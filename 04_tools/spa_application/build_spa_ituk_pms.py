r"""ITUK 2026 SPA (PMS basket) - optimizer, profit bridge and MD approval form.

Internal only. Built 2026-10-26 for Jerome, for approval by Yoshimoto san.

WHAT GOES IN
------------
ITUK's own proposal workbook (Duncan's "2026 ITUK SPA - PMS"): one row per part number
with ISZE's current price to ITUK, ITUK's proposed price, and the quantity ITUK commits
to over the SPA year. Its cells are links into Duncan's local file, so this reads the
cached values, not the formulas.

THE BASIS (same as the UTI build in build_spa_application.py, where it applies)
------------------------------------------------------------------------------
  * L12 window = the last 12 complete billed months in sales_fact (Sep 2025 - Aug 2026),
    sold-to 2575 (ITUK). Never 2574 (IUK).
  * L12 revenue = what we actually billed ITUK on that line, not list x qty. ITUK's billed
    price on this basket ran about 6% under current list in every quarter of the window.
  * Purchase cost = price-file FOB re-struck on the live vintage:
        purchase = FOB_file x (FX_file / FX_live) x (discount_live / discount_file)
    with FX_file 163.7 / discount 0.620 (what the price file sits on) and FX_live 178.5 /
    discount 0.673 (config.yaml, live from 2026-10-01). Thailand (T) discount is unchanged.
    L12 and SPA are costed on the same purchase price, so the comparison is like for like.
  * SPA price = ITUK's proposed price rounded to the cent (SAP holds cents).
  * Lines with no purchase cost in any price file are kept in the SPA (ITUK asked for them)
    but sit on their own sheet and are left out of every profit figure.

DECISIONS TAKEN WITH JEROME (2026-10-26)
----------------------------------------
  * Submit all lines as one basket; weak lines are shown openly, not repriced.
  * No IML / IMIT purchase cut is asked; 7% is shown as a what-if only.
  * Validity 1 Nov 2026 - 31 Oct 2027.
  * "Waterfall" = a profit bridge: L12 gross profit -> volume -> price -> SPA gross profit.

USAGE
-----
  python 04_tools/spa_application/build_spa_ituk_pms.py --basket <ITUK file.xlsx>
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd
import yaml
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import CharacterProperties, Paragraph, ParagraphProperties
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.paths import ISZE_ROOT  # noqa: E402

DERIVED = ISZE_ROOT / "01_data" / "00_derived"
PRICING_CONFIG = ISZE_ROOT / "03_analytics" / "isze_pricing" / "config.yaml"

SOLD_TO = 2575                      # ITUK. 2574 is IUK - never mix.
WINDOW = ("2025-09-01", "2026-08-31")
FX_FILE, DISC_FILE_J = 163.7, 0.620  # the vintage the price file is struck on

# ---------------------------------------------------------------- styles
NAVY, GREY, ORANGE, PURPLE, GREEN = "1F3864", "595959", "C55A11", "7030A0", "375623"
INPUT_BG, WHITE = "EBF3FB", "FFFFFF"
NUM = '#,##0.00;\\(#,##0.00\\);\\-'
EUR0 = '#,##0" €";-#,##0" €";"-"'
PCT = '0.0%'
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def fill(c):
    return PatternFill("solid", fgColor=c)


def font(color="000000", bold=False, size=10, italic=False):
    return Font(name="Arial", color=color, bold=bold, size=size, italic=italic)


def put(ws, ref, value, *, f=None, bg=None, fmt=None, wrap=False, align=None, border=False):
    c = ws[ref]
    c.value = value
    c.font = f or font()
    if bg:
        c.fill = fill(bg)
    if fmt:
        c.number_format = fmt
    if wrap or align:
        c.alignment = Alignment(wrap_text=wrap, horizontal=align, vertical="center")
    if border:
        c.border = BOX
    return c


def banner(ws, rng, text, bg, size=10):
    ws.merge_cells(rng)
    first = rng.split(":")[0]
    put(ws, first, text, f=font(WHITE, True, size), bg=bg, align="center")
    for row in ws[rng]:
        for c in row:
            c.fill = fill(bg)


def norm_pn(x) -> str | None:
    s = re.sub(r"\D", "", str(x or ""))
    return s.zfill(10) if s else None


# ---------------------------------------------------------------- data
def read_basket(path: Path) -> pd.DataFrame:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    head = [str(c.value or "").strip().lower() for c in ws[1]]
    need = {"part number": "pn_raw", "description": "desc", "current eur cost": "list_eur",
            "proposed ime cost eur": "itik_price", "proposed spa qty": "spa_qty"}
    idx = {}
    for name, key in need.items():
        if name not in head:
            raise SystemExit(f"ABORTED - basket has no '{name}' column")
        idx[key] = head.index(name)
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[idx["pn_raw"]] is None:
            continue
        rows.append({k: r[i] for k, i in idx.items()})
    df = pd.DataFrame(rows)
    df["pn"] = df["pn_raw"].map(norm_pn)
    if df["pn"].duplicated().any():
        raise SystemExit(f"ABORTED - duplicate part numbers: {df[df.pn.duplicated()].pn.tolist()}")
    if df[["list_eur", "itik_price", "spa_qty"]].isna().any().any():
        raise SystemExit("ABORTED - basket has empty price or quantity cells (external links not cached?)")
    df["spa_price"] = df["itik_price"].astype(float).round(2)
    df["spa_qty"] = df["spa_qty"].astype(float)
    return df


def read_cost(df: pd.DataFrame) -> pd.DataFrame:
    """Purchase cost per basket line, struck at the price-file vintage (FX 163.7, discount 0.620).

    Looked up in this order, and the route is written to cost_from:
      1. the price file, by part number;
      2. the price file, where the basket PN is the newest number of an older row;
      3. a sibling number (same first 9 digits, last digit differs) with the SAME selling
         price as the basket line - the same part under a new suffix;
      4. the yen base price in the 2026 pricing simulation:  FOB = BP_JPY / 163.7 x 0.620;
      5. the PR00 selling price x the price-class factor (FOB = SP x class factor), with the
         class taken from a sibling number. This is the price file's own identity.
    """
    lp = pd.read_parquet(DERIVED / "pricing_list_pn.parquet",
                         columns=["part_number", "newest_pn", "fob_eur", "sp_eur", "source", "price_class"])
    lp["pn"] = lp["part_number"].map(norm_pn)
    lp["npn"] = lp["newest_pn"].map(norm_pn)
    lpc = lp.dropna(subset=["fob_eur"])
    direct = lpc.drop_duplicates("pn", keep="last").set_index("pn")
    # A basket PN can be the newest number of an older price-file row (fog lamps, 2026-10).
    via_new = lpc.drop_duplicates("npn", keep="last").set_index("npn")
    lpc = lpc.assign(stem=lpc["pn"].str[:9])
    sim = pd.read_parquet(DERIVED / "pricing_sim_pr00_l12m.parquet",
                          columns=["part_number", "source", "price_class", "bp_jpy_2026"])
    sim["pn"] = sim["part_number"].map(norm_pn)
    sim = sim.dropna(subset=["bp_jpy_2026"]).drop_duplicates("pn", keep="last").set_index("pn")
    pr00 = pd.read_parquet(DERIVED / "pricing_pr00_ie40.parquet", columns=["part_number", "sp_eur"])
    pr00["pn"] = pr00["part_number"].map(norm_pn)
    pr00 = pr00.dropna(subset=["sp_eur"]).drop_duplicates("pn", keep="last").set_index("pn")
    cfg = yaml.safe_load(PRICING_CONFIG.read_text(encoding="utf-8"))["formula"]
    class_factor = cfg["class_factor"]
    file_disc = {"J": DISC_FILE_J, "T": float(cfg["source_discount"]["T"])}
    out = []
    for pn, list_eur in zip(df["pn"], df["list_eur"]):
        sib = lpc[(lpc["stem"] == pn[:9]) & (lpc["pn"] != pn)]
        if pn in direct.index:
            r = direct.loc[pn]
            out.append((r.fob_eur, r.source, r.sp_eur, "price file"))
        elif pn in via_new.index:
            r = via_new.loc[pn]
            out.append((r.fob_eur, r.source, r.sp_eur, f"price file via {r.part_number}"))
        elif len(same := sib[(sib["sp_eur"] - float(list_eur)).abs() < 0.005]):
            r = same.iloc[-1]
            out.append((r.fob_eur, r.source, r.sp_eur,
                        f"price file via {r.part_number} (same part, new suffix; same selling price)"))
        elif pn in sim.index:
            r = sim.loc[pn]
            src = str(r.source).strip()
            fob = round(float(r.bp_jpy_2026) / FX_FILE * file_disc.get(src, DISC_FILE_J), 2)
            out.append((fob, src, None, f"yen base price {int(r.bp_jpy_2026)} (2026 pricing simulation) / {FX_FILE} x {file_disc.get(src)}"))
        elif pn in pr00.index and len(sib) and str(sib.iloc[-1].price_class) in class_factor:
            k = str(sib.iloc[-1].price_class)
            sp = float(pr00.loc[pn].sp_eur)
            out.append((round(sp * float(class_factor[k]), 2), sib.iloc[-1].source, sp,
                        f"PR00 price {sp:.2f} x class {k} factor {class_factor[k]} (class from {sib.iloc[-1].part_number})"))
        else:
            out.append((None, None, None, "no purchase price in any price file"))
    df[["fob_file", "source", "sp_file", "cost_from"]] = pd.DataFrame(out, index=df.index)
    return df


def read_l12(df: pd.DataFrame) -> pd.DataFrame:
    sf = pd.read_parquet(DERIVED / "sales_fact.parquet",
                         columns=["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value"])
    if str(sf["billing_date"].max())[:10] < WINDOW[1]:
        raise SystemExit(f"ABORTED - sales_fact ends {sf['billing_date'].max()}, before the window end {WINDOW[1]}")
    sf = sf[(sf["sold_to_sap"] == SOLD_TO) & (sf["billing_date"] >= WINDOW[0]) & (sf["billing_date"] <= WINDOW[1])]
    sf["pn"] = sf["part_number"].map(norm_pn)
    # Billing under an older number of the same part counts toward that basket line: the
    # price file's supersession chain (same newest number) and same-stem suffix variants.
    # Without this the EGR cooler, DEF sensor, urea kit etc. show no L12 and their whole SPA
    # profit reads as gain (EUR 176K of ITUK billing in the 2026-10 basket).
    lp = pd.read_parquet(DERIVED / "pricing_list_pn.parquet", columns=["part_number", "newest_pn"])
    lp["pn"], lp["npn"] = lp["part_number"].map(norm_pn), lp["newest_pn"].map(norm_pn)
    basket = set(df["pn"])
    alias: dict[str, set] = {}
    for b in basket:
        news = set(lp.loc[lp["pn"] == b, "npn"]) | {b}
        olds = set(lp.loc[lp["npn"].isin(news), "pn"]) | set(lp.loc[lp["pn"].str[:9] == b[:9], "pn"])
        for o in olds - basket:
            alias.setdefault(o, set()).add(b)
    alias1 = {o: next(iter(bs)) for o, bs in alias.items() if len(bs) == 1}
    sf["billed_as"] = sf["pn"]
    sf["pn"] = sf["pn"].map(lambda p: alias1.get(p, p))
    old_nums = (sf[sf["pn"] != sf["billed_as"]].groupby("pn")["billed_as"]
                .apply(lambda x: ", ".join(sorted(set(x)))).rename("l12_also_billed_as"))
    g = sf.groupby("pn").agg(l12_qty=("billed_qty", "sum"), l12_rev=("net_sales_value", "sum")).reset_index()
    g = g.merge(old_nums, on="pn", how="left")
    df = df.merge(g, on="pn", how="left")
    df[["l12_qty", "l12_rev"]] = df[["l12_qty", "l12_rev"]].fillna(0.0)
    pc = pd.read_parquet(DERIVED / "parts_catalog_dimension.parquet", columns=["part_number", "pr00_group"])
    pc["pn"] = pc["part_number"].map(norm_pn)
    df = df.merge(pc.drop_duplicates("pn")[["pn", "pr00_group"]], on="pn", how="left")
    df["pr00_group"] = df["pr00_group"].fillna("Not classified")
    return df


# ---------------------------------------------------------------- workbook
def build(args) -> Path:
    cfg = yaml.safe_load(PRICING_CONFIG.read_text(encoding="utf-8"))["formula"]
    fx_live = float(cfg["fx_rate"])
    disc_j, disc_t = float(cfg["source_discount"]["J"]), float(cfg["source_discount"]["T"])

    df = read_l12(read_cost(read_basket(Path(args.basket))))
    costed = df[df["fob_file"].notna()].reset_index(drop=True)
    pending = df[df["fob_file"].isna()].reset_index(drop=True)
    n = len(costed)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ---------------- Assumptions
    wa = wb.create_sheet("Assumptions")
    wa.column_dimensions["A"].width = 4
    wa.column_dimensions["B"].width = 44
    wa.column_dimensions["C"].width = 22
    wa.column_dimensions["D"].width = 78
    banner(wa, "B1:D1", "SPA OPTIMIZER — ASSUMPTIONS  ·  ITUK 2026 SPA (PMS basket)", NAVY, 12)
    for col, t in zip("BCD", ("PARAMETER", "VALUE", "NOTES")):
        put(wa, f"{col}3", t, f=font(WHITE, True), bg=GREY)
    params = [
        (4, "IML / IMIT purchase price cut % (applied)", 0.0, PCT,
         "Base case: no cut asked of Japan. Change to test. Drives columns V–AB."),
        (5, "Minimum GM% floor (ISZE reference)", 0.25, PCT, "Reference only; highlights margin erosion."),
        (6, "What-if IML cut % (shown, not asked)", 0.07, PCT, "Standard ask used on the UTI SPA. Shown in the bridge and scenarios only."),
        (7, "FX JPY/EUR — live, used for cost", fx_live, "0.0", f"config.yaml fx_rate, live {cfg.get('fx_as_of')} to {cfg.get('fx_period_end')}."),
        (8, "FX JPY/EUR — price file vintage", FX_FILE, "0.0", "The vintage the price file FOB is struck on. Do not edit."),
        (9, "Japan purchase discount — live", disc_j, "0.000", "Effective 2026-01-05 (was 0.620)."),
        (10, "Japan purchase discount — price file vintage", DISC_FILE_J, "0.000", "Do not edit."),
        (11, "Thailand purchase discount (unchanged)", disc_t, "0.000", "IMIT; same in file and live, so no re-strike."),
    ]
    for r, label, v, fmt, note in params:
        put(wa, f"B{r}", label)
        put(wa, f"C{r}", v, f=font("0000FF"), bg=INPUT_BG, fmt=fmt, border=True)
        put(wa, f"D{r}", note, f=font(GREY, size=9), wrap=True)

    put(wa, "B13", "CUSTOMER & SPA CONTEXT", f=font(NAVY, True))
    ctx = [
        (14, "Customer / Distributor", "Isuzu Truck (UK) Ltd — ITUK"),
        (15, "Market", "United Kingdom"),
        (16, "SAP sold-to", str(SOLD_TO)),
        (17, "SPA reference", "ITUK 2026 SPA – PMS"),
        (18, "SPA valid from", "01-Nov-2026"),
        (19, "SPA valid to", "31-Oct-2027"),
        (20, "L12 baseline window", "01-Sep-2025 to 31-Aug-2026 (SAP billing)"),
        (21, "Prepared by", args.prepared_by),
        (22, "Basket source", Path(args.basket).name),
        (23, "Currency", "EUR (ITUK is billed in EUR)"),
    ]
    for r, label, v in ctx:
        put(wa, f"B{r}", label)
        put(wa, f"C{r}", v, f=font("0000FF"), bg=INPUT_BG, border=True)
        wa.merge_cells(f"C{r}:D{r}")

    # ---------------- SPA Optimizer
    wo = wb.create_sheet("SPA Optimizer")
    first, last = 6, 6 + n - 1
    tot = last + 2
    banner(wo, "A1:N1", f"SPA OPTIMIZER  ·  ITUK  ·  ISZE  ·  {n} costed lines", NAVY, 14)
    put(wo, "O2", "Blue cells = inputs  |  Black = formulas  |  Green = from Assumptions", f=font(GREY, size=9))
    groups = [("A4:B4", "PART INFO", GREY), ("C4:I4", "◀  L12 BASELINE — ACTUAL (SAP)  ▶", NAVY),
              ("J4:O4", "◀  SPA AS REQUESTED BY ITUK  ▶", ORANGE), ("P4:R4", "◀  DELTA vs L12  ▶", GREY),
              ("S4:U4", "◀  BREAK-EVEN  ▶", PURPLE), ("V4:AB4", "◀  ENTITY SHARING — IML / IMIT CUT  ▶", GREEN),
              ("AC4:AJ4", "◀  BASIS & BRIDGE  ▶", NAVY)]
    for rng, t, bg in groups:
        banner(wo, rng, t, bg)
    heads = ["P/N", "Description", "Purchase\nPrice (€)", "ISZE List\nto ITUK (€)", "L12\nQty", "L12\nRevenue (€)",
             "L12\nCost (€)", "L12\nProfit (€)", "L12\nGM%", "SPA\nPrice (€)", "SPA Qty\nCommitted", "SPA\nRevenue (€)",
             "Unit\nMargin (€)", "SPA\nProfit (€)", "SPA\nGM%", "Δ Revenue\n(€)", "Δ Profit\n(€)", "Status\n(no cut)",
             "Min Qty\n@ SPA Price", "Min Price\n@ SPA Qty", "Extra Qty\nNeeded", "IML\nCut %", "ISZE Cost\nw/ Cut (€)",
             "SPA Profit\nw/ Cut (€)", "Δ Profit\nw/ Cut (€)", "IML €\nSacrifice", "Req IML\nCut %", "Status\nw/ Cut",
             "Price-file\nFOB (€)", "Source", "L12 billed\n€/unit", "SPA disc.\nvs list", "SPA vs\nL12 billed",
             "Volume\neffect (€)", "Price\neffect (€)", "Part group"]
    widths = [13, 30, 11, 11, 8, 13, 13, 13, 8, 11, 10, 13, 10, 13, 8, 13, 13, 11, 11, 11, 10, 8, 11, 13, 13, 12, 9, 11,
              11, 7, 11, 9, 9, 13, 13, 20]
    for i, (h, w) in enumerate(zip(heads, widths), start=1):
        col = get_column_letter(i)
        put(wo, f"{col}5", h, f=font(WHITE, True, 9), bg=GREY, wrap=True, align="center")
        wo.column_dimensions[col].width = w
    wo.row_dimensions[5].height = 38

    fx_ratio = "(Assumptions!$C$8/Assumptions!$C$7)"
    for i, rec in costed.iterrows():
        r = first + i
        disc_ratio = f'IF(AD{r}="J",Assumptions!$C$9/Assumptions!$C$10,1)'
        vals = {
            "A": rec.pn, "B": rec.desc,
            "C": f"=ROUND(AC{r}*{fx_ratio}*{disc_ratio},4)",
            "D": float(rec.list_eur), "E": float(rec.l12_qty), "F": round(float(rec.l12_rev), 2),
            "G": f"=E{r}*C{r}", "H": f"=F{r}-G{r}", "I": f"=IFERROR(H{r}/F{r},0)",
            "J": float(rec.spa_price), "K": float(rec.spa_qty),
            "L": f"=J{r}*K{r}", "M": f"=J{r}-C{r}", "N": f"=M{r}*K{r}", "O": f"=IFERROR(N{r}/L{r},0)",
            "P": f"=L{r}-F{r}", "Q": f"=N{r}-H{r}", "R": f'=IF(Q{r}>=0,"▲ BETTER","▼ WORSE")',
            "S": f'=IFERROR(IF(J{r}-C{r}<=0,"BELOW COST",CEILING(H{r}/(J{r}-C{r}),1)),"N/A")',
            "T": f'=IFERROR(H{r}/K{r}+C{r},"N/A")', "U": f"=IFERROR(MAX(0,S{r}-K{r}),0)",
            "V": "=Assumptions!$C$4", "W": f"=C{r}*(1-Assumptions!$C$4)",
            "X": f"=(J{r}-W{r})*K{r}", "Y": f"=X{r}-H{r}", "Z": f"=C{r}*Assumptions!$C$4*K{r}",
            "AA": f'=IFERROR(MAX(0,1-(J{r}-H{r}/K{r})/C{r}),"N/A")',
            "AB": f'=IF(Y{r}>=0,"▲ BETTER","▼ WORSE")',
            "AC": float(rec.fob_file), "AD": str(rec.source),
            "AE": f"=IF(E{r}>0,F{r}/E{r},D{r})", "AF": f"=1-J{r}/D{r}", "AG": f"=J{r}/AE{r}-1",
            "AH": f"=(K{r}-E{r})*(AE{r}-C{r})", "AI": f"=(J{r}-AE{r})*K{r}", "AJ": rec.pr00_group,
        }
        for col, v in vals.items():
            is_input = col in ("A", "D", "E", "F", "J", "K", "AC", "AD")
            c = wo[f"{col}{r}"]
            c.value = v
            c.font = font("0000FF" if is_input else ("375623" if col == "V" else "000000"))
            if is_input:
                c.fill = fill(INPUT_BG)
            if col in ("I", "O", "V", "AA", "AF", "AG"):
                c.number_format = PCT
            elif col in ("E", "K", "S", "U"):
                c.number_format = "#,##0"
            elif col not in ("A", "B", "R", "AB", "AD", "AJ"):
                c.number_format = NUM
    rng = lambda col: f"{col}{first}:{col}{last}"  # noqa: E731
    put(wo, f"A{tot}", "TOTAL", f=font(WHITE, True), bg=NAVY)
    put(wo, f"B{tot}", f"{n} costed lines", f=font(WHITE, True), bg=NAVY)
    for col in ("E", "F", "G", "H", "K", "L", "N", "P", "Q", "X", "Y", "Z", "AH", "AI"):
        put(wo, f"{col}{tot}", f"=SUM({rng(col)})", f=font(WHITE, True), bg=NAVY,
            fmt="#,##0" if col in ("E", "K") else NUM)
    put(wo, f"I{tot}", f"=IFERROR(H{tot}/F{tot},0)", f=font(WHITE, True), bg=NAVY, fmt=PCT)
    put(wo, f"O{tot}", f"=IFERROR(N{tot}/L{tot},0)", f=font(WHITE, True), bg=NAVY, fmt=PCT)
    put(wo, f"R{tot}", f'=COUNTIF({rng("R")},"▲ BETTER")&" better"', f=font(WHITE, True), bg=NAVY)
    put(wo, f"AB{tot}", f'=COUNTIF({rng("AB")},"▲ BETTER")&" better"', f=font(WHITE, True), bg=NAVY)
    put(wo, f"AF{tot}", f"=1-L{tot}/SUMPRODUCT({rng('D')},{rng('K')})", f=font(WHITE, True), bg=NAVY, fmt=PCT)
    for col in ("C", "D", "J", "M", "S", "T", "U", "V", "W", "AA", "AC", "AD", "AE", "AG", "AJ"):
        wo[f"{col}{tot}"].fill = fill(NAVY)
    for col in ("R", "AB"):
        wo.conditional_formatting.add(rng(col), CellIsRule(operator="equal", formula=['"▼ WORSE"'],
                                                            font=Font(color="C00000", bold=True)))
        wo.conditional_formatting.add(rng(col), CellIsRule(operator="equal", formula=['"▲ BETTER"'],
                                                            font=Font(color="375623", bold=True)))
    wo.conditional_formatting.add(rng("O"), CellIsRule(operator="lessThan", formula=["Assumptions!$C$5"],
                                                       fill=fill("F8CBAD")))
    notes = tot + 2
    put(wo, f"A{notes}", "FORMULA NOTES", f=font(NAVY, True))
    for j, t in enumerate([
        "Purchase price (C) = price-file FOB × (163.7 / live FX) × (live discount / 0.620) for Japan parts; Thailand parts re-strike on FX only.",
        "L12 revenue (F) is what ITUK was actually billed (SAP, sold-to 2575, Sep 2025–Aug 2026), not list × qty. L12 cost uses today's purchase price so both sides compare like for like.",
        "SPA price (J) = ITUK's proposed price rounded to the cent. SPA qty (K) = ITUK's committed quantity for the SPA year.",
        "Volume effect (AH) = (SPA qty − L12 qty) × (L12 billed €/unit − purchase).  Price effect (AI) = (SPA price − L12 billed €/unit) × SPA qty.  AH + AI = Δ profit (Q).",
        "Min qty (S) = L12 profit ÷ SPA unit margin.  Min price (T) = L12 profit ÷ SPA qty + purchase.  Req IML cut (AA) = cut that would make the line profit-neutral.",
    ], start=1):
        put(wo, f"A{notes + j}", t, f=font(GREY, size=9))
    wo.freeze_panes = "C6"
    wo.auto_filter.ref = f"A5:AJ{last}"

    # ---------------- Lines pending cost
    wp = wb.create_sheet("Lines pending cost")
    banner(wp, "A1:J1", "LINES KEPT IN THE SPA BUT WITHOUT A PURCHASE PRICE — left out of all profit figures", ORANGE, 11)
    ph = ["P/N", "Description", "ISZE List\nto ITUK (€)", "SPA\nPrice (€)", "SPA\nQty", "SPA\nRevenue (€)",
          "L12\nQty", "L12\nRevenue (€)", "Why", "To do"]
    for i, (h, w) in enumerate(zip(ph, [13, 30, 11, 11, 9, 13, 9, 13, 34, 40]), start=1):
        col = get_column_letter(i)
        put(wp, f"{col}3", h, f=font(WHITE, True, 9), bg=GREY, wrap=True, align="center")
        wp.column_dimensions[col].width = w
    wp.row_dimensions[3].height = 30
    for i, rec in pending.iterrows():
        r = 4 + i
        row = [rec.pn, rec.desc, float(rec.list_eur), float(rec.spa_price), float(rec.spa_qty), f"=D{r}*E{r}",
               float(rec.l12_qty), round(float(rec.l12_rev), 2), rec.cost_from,
               "Get the purchase price from IML / IMIT before the SPA is loaded in SAP"]
        for j, v in enumerate(row, start=1):
            c = wp.cell(row=r, column=j, value=v)
            c.font = font()
            c.number_format = "#,##0" if j in (5, 7) else (NUM if j in (3, 4, 6, 8) else "General")
            c.alignment = Alignment(wrap_text=j >= 9, vertical="center")
    pend_tot = 4 + len(pending)
    put(wp, f"A{pend_tot}", "TOTAL", f=font(WHITE, True), bg=NAVY)
    for col in ("E", "F", "G", "H"):
        put(wp, f"{col}{pend_tot}", f"=SUM({col}4:{col}{pend_tot - 1})", f=font(WHITE, True), bg=NAVY,
            fmt="#,##0" if col in ("E", "G") else NUM)
    wp.freeze_panes = "A4"

    # ---------------- Profit Bridge (the waterfall)
    wbr = wb.create_sheet("Profit Bridge")
    banner(wbr, "A1:H1", "PROFIT BRIDGE — L12 gross profit to SPA gross profit (ISZE, EUR)", NAVY, 12)
    for col, w in zip("ABCDEFGH", (40, 16, 4, 14, 14, 14, 14, 14)):
        wbr.column_dimensions[col].width = w
    put(wbr, "A3", "Step", f=font(WHITE, True), bg=GREY)
    put(wbr, "B3", "€", f=font(WHITE, True), bg=GREY, align="center")
    O = "'SPA Optimizer'!"
    steps = [
        (4, "L12 gross profit (actual billing, today's cost)", f"={O}H{tot}"),
        (5, "Volume effect — ITUK commits more units", f"={O}AH{tot}"),
        (6, "Price effect — SPA price vs L12 billed price", f"={O}AI{tot}"),
        (7, "SPA gross profit — ISZE alone (no Japan cut)", f"={O}N{tot}"),
        (8, "What-if: Japan purchase cut (Assumptions C6)", f"=SUMPRODUCT({O}C{first}:C{last},{O}K{first}:K{last})*Assumptions!$C$6"),
        (9, "SPA gross profit — with what-if Japan cut", "=B7+B8"),
    ]
    for r, label, fml in steps:
        bold = r in (4, 7, 9)
        put(wbr, f"A{r}", label, f=font(bold=bold), border=True)
        put(wbr, f"B{r}", fml, f=font(bold=bold), fmt=EUR0, border=True)
    put(wbr, "A10", "Check: L12 + volume + price − SPA (must be 0)", f=font(GREY, size=9))
    put(wbr, "B10", "=ROUND(B4+B5+B6-B7,2)", f=font(GREY, size=9), fmt=NUM)

    # chart helper: invisible base + rise + fall + total
    put(wbr, "D3", "Bar", f=font(WHITE, True), bg=GREY)
    for col, t in zip("EFGH", ("Base", "Increase", "Decrease", "Total")):
        put(wbr, f"{col}3", t, f=font(WHITE, True), bg=GREY, align="center")
    chart_rows = [
        (4, "L12 profit", "=0", "=0", "=0", "=B4"),
        (5, "Volume", "=B4+MIN(0,B5)", "=MAX(0,B5)", "=MAX(0,-B5)", "=0"),
        (6, "Price", "=B4+B5+MIN(0,B6)", "=MAX(0,B6)", "=MAX(0,-B6)", "=0"),
        (7, "SPA profit", "=0", "=0", "=0", "=B7"),
        (8, "Japan cut (what-if)", "=B7+MIN(0,B8)", "=MAX(0,B8)", "=MAX(0,-B8)", "=0"),
        (9, "SPA + cut (what-if)", "=0", "=0", "=0", "=B9"),
    ]
    for r, lab, *cells in chart_rows:
        put(wbr, f"D{r}", lab, f=font(size=9))
        for col, v in zip("EFGH", cells):
            put(wbr, f"{col}{r}", v, f=font(size=9), fmt=EUR0)
    ch = BarChart()
    ch.type, ch.grouping, ch.overlap = "col", "stacked", 100
    ch.title = "ITUK SPA — gross profit bridge (EUR)"
    ch.y_axis.title = "EUR"
    ch.y_axis.numFmt = '#,##0'
    ch.y_axis.majorGridlines = None
    data = Reference(wbr, min_col=5, max_col=8, min_row=3, max_row=9)
    cats = Reference(wbr, min_col=4, min_row=4, max_row=9)
    ch.add_data(data, titles_from_data=True)
    ch.set_categories(cats)
    colors = [None, "70AD47", "C00000", NAVY]
    for s, col in zip(ch.series, colors):
        if col is None:
            s.graphicalProperties.noFill = True
            s.graphicalProperties.line.noFill = True
        else:
            s.graphicalProperties.solidFill = col
            s.graphicalProperties.line.solidFill = col
            s.dLbls = DataLabelList()
            s.dLbls.showVal = True
            s.dLbls.showSerName = False
            s.dLbls.showCatName = False
            s.dLbls.showLegendKey = False
            s.dLbls.showPercent = False
            s.dLbls.numFmt = '"-"#,##0;;' if col == "C00000" else '#,##0;-#,##0;'
            s.dLbls.txPr = RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=CharacterProperties(
                sz=900, b=True, solidFill="FFFFFF")), endParaRPr=CharacterProperties())])
    ch.legend = None
    ch.height, ch.width = 9.5, 22
    ch.gapWidth = 60
    wbr.add_chart(ch, "A13")

    # by part group
    g0 = 33
    put(wbr, f"A{g0}", "BY PART GROUP", f=font(NAVY, True))
    gh = ["Part group", "Lines", "", "L12 GP (€)", "SPA GP (€)", "Δ GP (€)", "SPA rev (€)", "SPA GM%"]
    for i, h in enumerate(gh):
        if h:
            put(wbr, f"{get_column_letter(i + 1)}{g0 + 1}", h, f=font(WHITE, True, 9), bg=GREY, align="center")
    # order by SPA revenue, largest first
    rev_by = (costed.spa_price * costed.spa_qty).groupby(costed.pr00_group).sum().sort_values(ascending=False)
    grp_order = rev_by.index.tolist()
    for j, grp in enumerate(grp_order):
        r = g0 + 2 + j
        gr = f"{O}$AJ${first}:$AJ${last}"
        put(wbr, f"A{r}", grp, f=font(size=9))
        put(wbr, f"B{r}", f'=COUNTIF({gr},A{r})', f=font(size=9), fmt="0")
        put(wbr, f"D{r}", f'=SUMIF({gr},A{r},{O}$H${first}:$H${last})', f=font(size=9), fmt=EUR0)
        put(wbr, f"E{r}", f'=SUMIF({gr},A{r},{O}$N${first}:$N${last})', f=font(size=9), fmt=EUR0)
        put(wbr, f"F{r}", f"=E{r}-D{r}", f=font(size=9), fmt=EUR0)
        put(wbr, f"G{r}", f'=SUMIF({gr},A{r},{O}$L${first}:$L${last})', f=font(size=9), fmt=EUR0)
        put(wbr, f"H{r}", f"=IFERROR(E{r}/G{r},0)", f=font(size=9), fmt=PCT)
    gl = g0 + 2 + len(grp_order)
    put(wbr, f"A{gl}", "TOTAL", f=font(WHITE, True), bg=NAVY)
    for col in "BDEFG":
        put(wbr, f"{col}{gl}", f"=SUM({col}{g0 + 2}:{col}{gl - 1})", f=font(WHITE, True), bg=NAVY,
            fmt="0" if col == "B" else EUR0)
    put(wbr, f"H{gl}", f"=IFERROR(E{gl}/G{gl},0)", f=font(WHITE, True), bg=NAVY, fmt=PCT)
    wbr.conditional_formatting.add(f"F{g0 + 2}:F{gl - 1}", CellIsRule(operator="lessThan", formula=["0"],
                                                                       font=Font(color="C00000")))

    # ---------------- Scenario Planner
    ws_ = wb.create_sheet("Scenario Planner")
    banner(ws_, "A1:G1", "SPA SCENARIO PLANNER — ITUK 2026 SPA (PMS basket)", NAVY, 12)
    for col, w in zip("ABCDEFG", (44, 12, 16, 16, 16, 16, 60)):
        ws_.column_dimensions[col].width = w
    sh = ["Scenario", "Lines", "SPA revenue (€)", "Gross profit (€)", "Δ GP vs L12 (€)", "Japan cut (€)", "Reading"]
    for i, h in enumerate(sh):
        put(ws_, f"{get_column_letter(i + 1)}3", h, f=font(WHITE, True, 9), bg=GREY, wrap=True, align="center")
    R, L, N_, H, K, C, J, E = (f"{O}{c}{first}:{c}{last}" for c in "RLNHKCJE")
    sc = [
        (4, "L12 baseline (actual)", f"={n}", f"={O}F{tot}", f"={O}H{tot}", "=0", "=0",
         "What ITUK bought from us on these lines in the last 12 months."),
        (5, "★ Full basket, no Japan cut (recommended)", f"={n}", f"={O}L{tot}", f"={O}N{tot}", "=D5-D4", "=0",
         "ITUK's proposal as sent, at the committed volume. ISZE carries the discount alone."),
        (6, "Partial — SPA only on lines that beat L12, rest at L12", f'=COUNTIF({R},"▲ BETTER")',
         f'=SUMIF({R},"▲ BETTER",{L})+SUMIF({R},"▼ WORSE",{O}F{first}:F{last})',
         f'=SUMIF({R},"▲ BETTER",{N_})+SUMIF({R},"▼ WORSE",{H})', "=D6-D4", "=0",
         "Better on paper, not chosen: brake pads, discs and filters, the core of the PMS campaign, would get no SPA."),
        (7, "Full basket + what-if Japan cut", f"={n}", f"={O}L{tot}", "='Profit Bridge'!B9", "=D7-D4",
         "='Profit Bridge'!B8", "Shown only. Not asked, because the basket already beats L12 without it."),
        (8, "Downside — ITUK only buys its L12 volume", f"={n}", f"=SUMPRODUCT({J},{E})",
         f"=SUMPRODUCT({J}-{C},{E})", "=D8-D4", "=0",
         "The risk: SPA prices are given but volume does not grow. This is the loss to protect against."),
    ]
    for r, *vals in sc:
        for i, v in enumerate(vals):
            col = get_column_letter(i + 1)
            fmt = None if col in ("A", "G") else ("0" if col == "B" else EUR0)
            put(ws_, f"{col}{r}", v, f=font(bold=r == 5), fmt=fmt, wrap=col == "G", border=True)
        ws_.row_dimensions[r].height = 30
    for r in range(4, 9):
        ws_[f"A{r}"].fill = fill("E2EFDA") if r == 5 else fill(WHITE)
    ws_.conditional_formatting.add("E4:E8", CellIsRule(operator="lessThan", formula=["0"], font=Font(color="C00000", bold=True)))
    put(ws_, "A10", "Break-even volume for the full basket (units, at SPA prices, no cut):", f=font(bold=True))
    put(ws_, "D10", f"={O}H{tot}/(({O}N{tot})/{O}K{tot})", fmt="#,##0")
    put(ws_, "E10", f"={O}K{tot}", fmt="#,##0")
    put(ws_, "F10", f"=D10/{O}E{tot}-1", fmt=PCT)
    put(ws_, "G10", "D = units needed at the average SPA unit margin to keep L12 profit · E = units committed · F = growth vs L12 needed",
        f=font(GREY, size=9), wrap=True)
    ws_.row_dimensions[10].height = 30

    # ---------------- Customer View (shareable with ITUK — no cost or margin)
    wcv = wb.create_sheet("Customer View")
    banner(wcv, "A1:H1", "ITUK 2026 SPA — PMS parts  ·  Special prices 1 Nov 2026 to 31 Oct 2027  ·  EUR", "C00000", 12)
    put(wcv, "A2", "Customer-safe. List price, SPA price, saving and committed quantity only. No ISZE cost or margin.",
        f=font(GREY, size=9, italic=True))
    ch_ = ["P/N", "Description", "Current price (€)", "SPA price (€)", "Saving / unit (€)", "Saving %",
           "Committed qty", "SPA value (€)"]
    for i, (h, w) in enumerate(zip(ch_, [13, 32, 13, 13, 13, 9, 12, 14]), start=1):
        col = get_column_letter(i)
        put(wcv, f"{col}4", h, f=font(WHITE, True, 9), bg=GREY, wrap=True, align="center")
        wcv.column_dimensions[col].width = w
    allrows = df.reset_index(drop=True)
    for i, rec in allrows.iterrows():
        r = 5 + i
        row = [rec.pn, rec.desc, float(rec.list_eur), float(rec.spa_price), f"=C{r}-D{r}", f"=IFERROR(E{r}/C{r},0)",
               float(rec.spa_qty), f"=D{r}*G{r}"]
        for j, v in enumerate(row, start=1):
            c = wcv.cell(row=r, column=j, value=v)
            c.font = font()
            c.number_format = {6: PCT, 7: "#,##0"}.get(j, NUM if j >= 3 else "General")
    cl = 5 + len(allrows)
    put(wcv, f"A{cl}", "TOTAL", f=font(WHITE, True), bg=NAVY)
    put(wcv, f"B{cl}", f"{len(allrows)} part numbers", f=font(WHITE, True), bg=NAVY)
    put(wcv, f"G{cl}", f"=SUM(G5:G{cl - 1})", f=font(WHITE, True), bg=NAVY, fmt="#,##0")
    put(wcv, f"H{cl}", f"=SUM(H5:H{cl - 1})", f=font(WHITE, True), bg=NAVY, fmt=NUM)
    put(wcv, f"F{cl}", f"=1-H{cl}/SUMPRODUCT(C5:C{cl - 1},G5:G{cl - 1})", f=font(WHITE, True), bg=NAVY, fmt=PCT)
    wcv.freeze_panes = "A5"

    # ---------------- MD Approval Request
    wmd = wb.create_sheet("MD Approval Request")
    for col, w in zip("ABCDEFGHIJKLM", (2, 20, 12, 14, 4, 12, 4, 20, 12, 14, 4, 18, 2)):
        wmd.column_dimensions[col].width = w
    put(wmd, "B1", "ISUZU MOTORS EUROPE NV", f=font(bold=True, size=14))
    put(wmd, "L1", "ISUZU", f=font(NAVY, True, 14), align="right")
    sig = [("B", "Applicant", args.prepared_by_name), ("E", "Manager", args.manager),
           ("H", "Director", "Masumi Hayakawa"), ("K", "Managing Director", "Norihiro Yoshimoto")]
    put(wmd, "B2", "Requested by", f=font(bold=True, size=9))
    put(wmd, "E2", "Approved by", f=font(bold=True, size=9))
    for col, role, name in sig:
        nxt = get_column_letter(openpyxl.utils.column_index_from_string(col) + 1)
        for rr in (3, 4, 5, 6):
            wmd.merge_cells(f"{col}{rr}:{nxt}{rr}")
        put(wmd, f"{col}3", role, f=font(WHITE, True, 9), bg=NAVY, align="center", border=True)
        put(wmd, f"{col}4", name, f=font(size=9), align="center", border=True)
        put(wmd, f"{col}5", "", border=True)
        put(wmd, f"{col}6", "Date:", f=font(size=9), border=True)
        wmd.row_dimensions[5].height = 34
    put(wmd, "B8", "Promotional Parts Price Change Request — SPA", f=font(bold=True, size=12))
    put(wmd, "B9", "PARTS CAMPAIGN · PMS (scheduled maintenance) · Phase 1 N75", f=font(size=10))
    put(wmd, "B11", "Customer", f=font(bold=True))
    put(wmd, "B12", "Name"); put(wmd, "C12", "=Assumptions!C14")
    put(wmd, "B13", "Country / Market"); put(wmd, "C13", "=Assumptions!C15")
    put(wmd, "H12", "Sold-to party"); put(wmd, "J12", "=Assumptions!C16")
    put(wmd, "H13", "SPA reference"); put(wmd, "J13", "=Assumptions!C17")
    put(wmd, "B14", "Validity"); put(wmd, "C14", '=Assumptions!C18&" to "&Assumptions!C19')
    put(wmd, "H14", "Repetition"); put(wmd, "J14", "No")

    put(wmd, "B16", "【Business impact】  (unit: €)", f=font(bold=True))
    for col, h in zip("BDFHIJL", ["", "L12 actual\n(SAP billing)", "SPA year 1\n(no Japan cut)", "Δ vs L12", "", "", "SPA with what-if\nJapan cut"]):
        if h:
            put(wmd, f"{col}17", h, f=font(WHITE, True, 9), bg=GREY, wrap=True, align="center", border=True)
    wmd.row_dimensions[17].height = 30
    imp = [
        (18, "Revenue", f"={O}F{tot}", f"={O}L{tot}", f"={O}L{tot}"),
        (19, "Purchase cost", f"={O}G{tot}", f"={O}L{tot}-{O}N{tot}", f"={O}L{tot}-'Profit Bridge'!B9"),
        (20, "Gross profit", f"={O}H{tot}", f"={O}N{tot}", "='Profit Bridge'!B9"),
        (21, "Gross margin %", f"={O}I{tot}", f"={O}O{tot}", "=IFERROR(L20/L18,0)"),
        (22, "Units", f"={O}E{tot}", f"={O}K{tot}", f"={O}K{tot}"),
    ]
    for r, lab, d, f_, l_ in imp:
        fmt = PCT if r == 21 else ("#,##0" if r == 22 else EUR0)
        put(wmd, f"B{r}", lab, f=font(bold=r == 20), border=True)
        put(wmd, f"D{r}", d, fmt=fmt, border=True, f=font(bold=r == 20))
        put(wmd, f"F{r}", f_, fmt=fmt, border=True, f=font(bold=r == 20))
        put(wmd, f"H{r}", f"=F{r}-D{r}", fmt=fmt, border=True, f=font(bold=r == 20))
        put(wmd, f"L{r}", l_, fmt=fmt, border=True, f=font(GREY))
    wmd.conditional_formatting.add("H18:H22", CellIsRule(operator="lessThan", formula=["0"], font=Font(color="C00000", bold=True)))

    put(wmd, "B24", "Background & justification", f=font(bold=True))
    just = (
        '="ITUK asks for SPA prices on "&TEXT(COUNTA(\'Customer View\'!A5:A' + str(cl - 1) + '),"0")'
        '&" part numbers for its PMS campaign (Phase 1 N75, go-live autumn 2026), at "&TEXT(\'Customer View\'!F' + str(cl) + ',"0.0%")'
        '&" average below current list, against a committed volume of "&TEXT(\'Customer View\'!G' + str(cl) + ',"#,##0")&" units."'
        '&CHAR(10)&"On the "&TEXT(' + str(n) + ',"0")&" lines we can cost, gross profit moves from "&TEXT(D20,"#,##0 €")&" to "&TEXT(F20,"#,##0 €")'
        '&" ("&TEXT(H20,"+#,##0 €;-#,##0 €")&") without any purchase-price support from Japan. Margin goes from "&TEXT(D21,"0.0%")&" to "&TEXT(F21,"0.0%")&"."'
        '&CHAR(10)&"The gain depends on ITUK reaching the committed volume: volume adds "&TEXT(\'Profit Bridge\'!B5,"#,##0 €")'
        '&", the lower price costs "&TEXT(-\'Profit Bridge\'!B6,"#,##0 €")&". If ITUK only buys its last-12-month volume, profit is "'
        '&TEXT(-\'Scenario Planner\'!E8,"#,##0 €")&" lower than today."'
    )
    wmd.merge_cells("B25:L29")
    put(wmd, "B25", just, wrap=True, f=font(size=9))
    wmd["B25"].alignment = Alignment(wrap_text=True, vertical="top")
    n_less = int(((costed.l12_qty > 0) & (costed.spa_qty < costed.l12_qty)).sum())
    put(wmd, "B31", "Points for the approver", f=font(bold=True))
    pts = [
        "1. No line falls under the 25% margin floor; the lowest SPA line margin is shown on the SPA Optimizer sheet (column O).",
        "2. Brakes, steering and filters earn less than today (brakes and filters are the core of the PMS campaign); the gain comes mainly from exhaust and lighting volume. See Profit Bridge, by part group.",
        f"3. {len(pending)} part numbers have no purchase price in our price files; they are in the SPA but not in these figures (sheet 'Lines pending cost').",
        f"4. On {n_less} lines ITUK commits fewer units than it bought in the last 12 months but still gets the SPA price (brake pads, king pins, fuel and air filters among them).",
        "5. Proposal: approve the full basket, review actual ITUK volume after 6 months, and stop the SPA price on lines where volume stays under L12.",
    ]
    for j, t in enumerate(pts):
        r = 32 + j
        wmd.merge_cells(f"B{r}:L{r}")
        put(wmd, f"B{r}", t, f=font(size=9), wrap=True)
        wmd.row_dimensions[r].height = 26
    put(wmd, "B38", "Comments from approver, if any", f=font(bold=True))
    wmd.merge_cells("B39:L42")
    for row in wmd["B39:L42"]:
        for c in row:
            c.border = BOX
    wmd.page_setup.orientation = "portrait"
    wmd.page_setup.fitToWidth, wmd.page_setup.fitToHeight = 1, 1
    wmd.sheet_properties.pageSetUpPr.fitToPage = True
    wmd.print_area = "A1:M43"
    wmd.page_margins = PageMargins(left=0.4, right=0.4, top=0.5, bottom=0.5)

    # ---------------- Health check on Assumptions (live)
    put(wa, "B26", "SPA HEALTH CHECK — read before sharing", f=font(NAVY, True))
    hc = [
        (27, "Δ gross profit vs L12 (no cut)", f"={O}Q{tot}", EUR0,
         f'=IF({O}Q{tot}>=0,"✔ Better than today without Japan support","✖ Worse than today — needs support or renegotiation")'),
        (28, "Δ gross profit if volume stays at L12", "='Scenario Planner'!E8", EUR0,
         '=IF(\'Scenario Planner\'!E8>=0,"✔ Safe even without volume growth","⚠ Depends on ITUK reaching committed volume")'),
        (29, "Lines better than L12 (no cut)", f'=COUNTIF({R},"▲ BETTER")', "0",
         f'=COUNTIF({R},"▲ BETTER")&" of {n} — weak lines kept, basket submitted whole"'),
        (30, "Lowest SPA line margin", f"=MIN({O}O{first}:O{last})", PCT,
         f'=IF(MIN({O}O{first}:O{last})>=Assumptions!C5,"✔ All lines above the floor","✖ Lines under the floor")'),
        (31, "Weighted SPA margin (L12)", f"={O}O{tot}", PCT, f'="L12: "&TEXT({O}I{tot},"0.0%")'),
        (32, "Committed units vs L12", f"={O}K{tot}/{O}E{tot}-1", PCT,
         f'=IF({O}K{tot}>={O}E{tot},"✔ Committed volume above L12","⚠ Below L12")'),
        (33, "Lines without purchase price", f"={len(pending)}", "0", '="See sheet Lines pending cost"'),
    ]
    for r, lab, v, fmt, status in hc:
        put(wa, f"B{r}", lab, border=True)
        put(wa, f"C{r}", v, fmt=fmt, border=True)
        put(wa, f"D{r}", status, border=True, f=font(size=9))

    # ---------------- How to Use
    wh = wb.create_sheet("How to Use", 0)
    wh.column_dimensions["A"].width = 26
    wh.column_dimensions["B"].width = 110
    banner(wh, "A1:B1", "ITUK 2026 SPA (PMS basket) — HOW TO READ THIS FILE", NAVY, 13)
    guide = [
        ("Assumptions", "ISZE internal. FX, purchase discount, Japan cut and the SPA health check."),
        ("SPA Optimizer", f"ISZE internal. Engine, one row per costed line ({n}). Blue = input, black = formula."),
        ("Lines pending cost", f"ISZE internal. {len(pending)} lines in the SPA with no purchase price; left out of profit."),
        ("Profit Bridge", "ISZE internal. The waterfall: L12 profit → volume → price → SPA profit, plus by part group."),
        ("Scenario Planner", "ISZE internal. Full basket (recommended), partial, what-if Japan cut, downside."),
        ("Customer View", "Shareable with ITUK. Prices and quantities only, no cost or margin."),
        ("MD Approval Request", "For Yoshimoto san. One page, prints to A4."),
        ("", ""),
        ("Basis", "L12 = SAP billing to ITUK (sold-to 2575), Sep 2025–Aug 2026. Cost = price-file FOB on the live FX "
                  f"{fx_live} and Japan discount {disc_j}. SPA prices = ITUK's proposal rounded to the cent."),
        ("Not in this file", "No IML / IMIT brief: no Japan support is asked for this SPA."),
    ]
    for j, (a, b) in enumerate(guide, start=3):
        put(wh, f"A{j}", a, f=font(bold=True))
        put(wh, f"B{j}", b, wrap=True)

    wb._sheets = [wb[s] for s in ("How to Use", "MD Approval Request", "Profit Bridge", "Scenario Planner",
                                    "SPA Optimizer", "Lines pending cost", "Assumptions", "Customer View")]
    wb.active = 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    # print copy for the PDF: only the approval page and the bridge are visible
    wbr.page_setup.orientation = "landscape"
    wbr.sheet_properties.pageSetUpPr.fitToPage = True
    wbr.page_setup.fitToWidth, wbr.page_setup.fitToHeight = 1, 0
    for w in wb.worksheets:
        if w.title not in ("MD Approval Request", "Profit Bridge"):
            w.sheet_state = "hidden"
    wb.save(out.with_name(out.stem + "_print.xlsx"))
    costed.to_pickle(out.with_suffix(".lines.pkl"))
    pending.to_pickle(out.with_suffix(".pending.pkl"))
    print(f"lines: {len(df)} | costed {n} | pending {len(pending)}")
    print(f"wrote {out}")
    return out


def main() -> int:
    stamp = date.today().strftime("%Y%m%d")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--basket", required=True)
    ap.add_argument("--out", default=str(ISZE_ROOT / "01_data" / "90_INBOX" / f"_spa_application_ITUK_PMS_{stamp}"
                                         / f"ISZE_SPA_ITUK_2026_PMS_{stamp}.xlsx"))
    ap.add_argument("--prepared-by", default="Jerome Van der Pluym")
    ap.add_argument("--prepared-by-name", default="Jerome Van der Pluym")
    ap.add_argument("--manager", default="Hadewijch Tibos")
    build(ap.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
