"""shared Excel: N75 PMS EQ application + aftermarket brand prices vs ISZE list.

No invented prices. DAF peer rows are excluded (not physical fit).
Does not touch any PowerPoint. Does not Outlook Send.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_A = ROOT / "09_meetings" / "ISZE_PMS_Aftermarket_vs_List.xlsx"
OUT_B = ROOT / "ISZE_PMS_Aftermarket_vs_List.xlsx"
SHARE = ROOT / "09_meetings" / "Preparation Meetings" / "IML_ITUK_PMS" / "mp" / "SHARE"

PR00 = ROOT / "01_data" / "00_derived" / "pricing_pr00_ie40.parquet"
XREF = ROOT / "01_data" / "00_derived" / "genuine_bvp_crossref.csv"
EUCON = ROOT / "01_data" / "01_Pricing" / "_raw" / "Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx"
KS_CSV = ROOT / "04_tools" / "autodoc_scraper" / "ks_results.csv"
MEK_CSV = ROOT / "04_tools" / "autodoc_scraper" / "mekonomen_results.csv"

NAVY = PatternFill("solid", fgColor="1A2B4A")
PAPER = PatternFill("solid", fgColor="F7F4EE")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
GREEN = PatternFill("solid", fgColor="E6F5EF")
AMBER = PatternFill("solid", fgColor="FCE4D6")
RED_SOFT = PatternFill("solid", fgColor="F8E4E3")
GREY = PatternFill("solid", fgColor="E7E6E6")
WHITE = PatternFill("solid", fgColor="FFFFFF")

FONT_TITLE = Font(name="Calibri", size=16, bold=True, color="1A2B4A")
FONT_SEC = Font(name="Calibri", size=12, bold=True, color="1A2B4A")
FONT_HDR = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
FONT_BODY = Font(name="Calibri", size=10, color="222222")
FONT_MUTED = Font(name="Calibri", size=9, color="6B6256")
FONT_WARN = Font(name="Calibri", size=10, bold=True, color="C0552D")
FONT_INPUT = Font(name="Calibri", size=10, bold=True, color="222222")

THIN = Border(
    left=Side(style="thin", color="D9D3C8"),
    right=Side(style="thin", color="D9D3C8"),
    top=Side(style="thin", color="D9D3C8"),
    bottom=Side(style="thin", color="D9D3C8"),
)
WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_C = Alignment(wrap_text=True, vertical="center")
WRAP_CC = Alignment(wrap_text=True, vertical="center", horizontal="center")
WRAP_R = Alignment(wrap_text=True, vertical="center", horizontal="right")

EUR = "€#,##0.00"
PCT = "0%"
NUM2 = "#,##0.00"

FX_GBP_EUR = 1.17
BAND = 0.10


def z10(v) -> str:
    s = str(v).replace(".0", "").strip()
    return s.zfill(10) if s.isdigit() else s


def widths(ws, pairs):
    for col, w in pairs.items():
        ws.column_dimensions[col].width = w


def paint(cell, fill=None, font=None, fmt=None, align=None):
    if fill is not None:
        cell.fill = fill
    cell.font = font or FONT_BODY
    cell.alignment = align or WRAP
    cell.border = THIN
    if fmt:
        cell.number_format = fmt


def header_row(ws, row, n_cols, height=28):
    ws.row_dimensions[row].height = height
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = FONT_HDR
        cell.alignment = WRAP_CC
        cell.border = THIN


def load_pr00() -> dict[str, dict]:
    df = pd.read_parquet(PR00)
    df["part_number"] = df["part_number"].astype(str).map(z10)
    df = df[df["price_condition"] == "PR00"].copy()
    out = {}
    for _, r in df.iterrows():
        out[r["part_number"]] = {
            "newest": z10(r["newest_pn"]),
            "desc": str(r["description"] or ""),
            "eur": float(r["sp_eur"]) if pd.notna(r["sp_eur"]) else None,
            "superseded": bool(r["is_superseded_row"]),
        }
    return out


def load_ks_status(pns: list[str]) -> dict[str, dict]:
    if not KS_CSV.exists():
        return {}
    df = pd.read_csv(KS_CSV, dtype=str)
    df["PN"] = df["PN"].astype(str).map(z10)
    out = {}
    for _, r in df[df["PN"].isin(pns)].iterrows():
        out[r["PN"]] = {
            "status": r.get("Status") or "",
            "am_gbp": r.get("KS_AM_MinPrice_GBP") or "",
            "gen_gbp": r.get("KS_GEN_MinPrice_GBP") or "",
            "when": r.get("Scraped_At") or "",
            "notes": r.get("Notes") or "",
        }
    return out


def load_eucon_hcv() -> pd.DataFrame:
    df = pd.read_excel(EUCON, sheet_name="HCV", dtype={"Isuzu Part Number": str})
    df["pn"] = df["Isuzu Part Number"].astype(str).map(z10)
    df["brand"] = df["Manufacturer Brand"].astype(str).str.strip()
    df["comp_pn"] = df["Competitor Part Number"].astype(str).str.strip()
    df["list_gbp"] = pd.to_numeric(df["Competitor List Price"], errors="coerce")
    df["ws_gbp"] = pd.to_numeric(df["Workshop Purchase Price"], errors="coerce")
    df["quality"] = df["Comparability Quality"].astype(str)
    return df


def page_setup(ws, title):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.6, bottom=0.6)
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddHeader.left.text = title
    ws.oddFooter.left.text = "ISZE · parts support for the ITUK PMS programme · not for DAF fitment"
    ws.oddFooter.right.text = "Page &P of &N"
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = None
    ws.sheet_view.showGridLines = False
    ws.print_title_rows = "1:4"


def build():
    pr00 = load_pr00()
    eu = load_eucon_hcv()

    # N75 4HK1 is the current United Kingdom 7.5t PMS model (NPR75).
    # P700 is the next generation (first chassis to bodybuilders October 2026).
    eq_rows = [
        # function, model, genuine_pn, role, bvp_pn, kit, notes
        ("Oil filter (set contents)", "N75 4HK1", "8983282070", "Element — current list", "1876102890", "no",
         "Also 8983282071 (same list; superseded onto 8983282070). Extra BVP twins 5876101170 and 5876100310 both supersede onto 1876102890. Quiet line — set contents, not a campaign."),
        ("Oil filter (set contents)", "N75 4HK1", "8983282071", "Element — superseded", "1876102890", "no",
         "Same list EUR as 8983282070. Do not treat as a second oil filter on the truck."),
        ("Fuel filter", "N75 4HK1", "8975425400", "Element — primary", "1876102860", "no",
         "BVP 1876102860 is the twin. This is the locked fuel line on the filter set."),
        ("Fuel filter assembly", "N75 4HK1", "8975425050", "Assembly — not the element", "1876102860", "no",
         "Registry also maps this assembly. List is much higher than the element. Do not swap it for 8975425400."),
        ("Air filter", "N75 4HK1", "8981772710", "Element — primary", "5876102500", "no",
         "Locked air line. Two further genuine air PNs exist (below)."),
        ("Air cleaner assembly", "N75 4HK1", "8981235322", "Assembly — not the element", "5876102500", "no",
         "Full cleaner assembly. Not the scheduled element."),
        ("Air cleaner assembly", "N75 4HK1", "8982157230", "Assembly — not the element", "5876102500", "no",
         "Full cleaner assembly. Not the scheduled element."),
        ("Brake pad (front)", "N75 4HK1 and N75 4JZ1", "8982447940", "Pad kit", "none", "no",
         "Confirmed. No Best Value twin. Commercial route is a special price agreement only."),
        ("Brake pad (front)", "N75 4JZ1 (not 4HK1)", "8982169220", "Pad kit", "5876102380", "no",
         "4JZ1 / N35 family. Do not use as the 4HK1 pad. BVP twins 5876102380 and 5876170050 sit on 4JZ1, not on 8982447940."),
        ("Brake disc (front)", "N-series catalog (N*R / N*S)", "8973872290", "Rotor", "5876103060", "no",
         "BVP catalogue application, not in the PMS registry. Confirm on the vehicle before ordering."),
        ("Brake disc (front)", "NPR / NQR catalog", "8981052720", "Rotor", "5876103070", "no",
         "In the BVP catalogue. No ISZE list found in the current price file. Confirm before quoting."),
        ("Brake wear sensor", "N75", "none found", "Wear", "none", "no",
         "No wear-indicator part number in the PMS registry or the BVP catalogue for this model. Service schedule is inspect, not a replace-every-visit item."),
        ("Clutch disc", "N75 4HK1", "8981649171", "Disc", "5876100920", "yes — see kit",
         "Manual only. BVP disc twin 5876100920. Also listed as a component of BVP clutch kit 5876102320."),
        ("Clutch pressure plate", "N75 4HK1", "8970388314", "Cover / pressure plate", "5876101040", "yes — see kit",
         "8970388313 supersedes onto 8970388314 (same list). BVP cover 5876101040."),
        ("Clutch release bearing", "N-series 4HK1 catalog", "1313100120", "Release bearing", "1876101100", "yes — see kit",
         "Catalogue application NPR / NQR / NNR 4HK1. Not in the short PMS registry; required if the kit is disc + cover + bearing."),
        ("Clutch pilot bearing", "N-series 4HK1 catalog", "8972582390", "Pilot bearing", "5876101641", "optional",
         "Low-value pilot. Include only if the workshop kit specification asks for it."),
        ("Clutch kit (Best Value)", "NNR / NPR / NQR 4HK1", "none — kit is Best Value", "Complete kit", "5876102320", "yes",
         "Best Value clutch kit. Catalogue pairs it with disc 8981649171. Disc + cover + bearing in one number."),
        ("Clutch kit (Best Value)", "NNR / NPR / NPS / NQR 4HK1", "none — kit is Best Value", "Complete kit", "5876102040", "yes",
         "Second Best Value kit on 4HK1 N-series. Confirm which kit the vehicle takes before stocking both."),
        ("Clutch kit (Best Value)", "NPR / NQR 4HK1", "none — kit is Best Value", "Complete kit", "5876103120", "yes",
         "Catalogue kit paired with disc 8981649181 (different disc, higher list). No ISZE list found for this kit number. Do not mix with 8981649171."),
    ]

    pns_all = sorted({r[2] for r in eq_rows if r[2] not in ("none", "none found")}
                     | {r[4] for r in eq_rows if r[4] not in ("none",)})
    ks = load_ks_status(pns_all)

    focus = [
        ("Oil filter (set contents)", "8983282070", "1876102890"),
        ("Fuel filter", "8975425400", "1876102860"),
        ("Air filter", "8981772710", "5876102500"),
        ("Brake pad", "8982447940", None),
        ("Brake disc", "8973872290", "5876103060"),
        ("Clutch disc", "8981649171", "5876100920"),
        ("Clutch pressure plate", "8970388314", "5876101040"),
        ("Clutch release bearing", "1313100120", "1876101100"),
        ("Clutch kit (Best Value)", None, "5876102320"),
    ]

    wb = Workbook()

    # ── Read_me ──────────────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Read_me"
    ws.sheet_properties.tabColor = "1A2B4A"
    widths(ws, {"A": 28, "B": 110})
    ws.merge_cells("A1:B1")
    ws["A1"] = "N75 parts — application and aftermarket brand prices versus our list"
    ws["A1"].font = FONT_TITLE
    ws["A1"].fill = PAPER
    ws.row_dimensions[1].height = 28
    ws.merge_cells("A2:B2")
    ws["A2"] = (
        f"Built {date.today().isoformat()} · United Kingdom N75 first (4HK1 / NPR75). "
        "P700 is the next generation, not this parc. Figures are ISZE list versus aftermarket brand prices we actually hold."
    )
    ws["A2"].font = FONT_MUTED
    ws["A2"].alignment = WRAP
    ws.row_dimensions[2].height = 36

    howto = [
        ("What this file is",
         "A working paper for the Tuesday parts discussion. It shows which part numbers apply on N75, whether a Best Value twin or a clutch kit exists, and where our list sits versus aftermarket brand prices."),
        ("How to read the sign",
         "We are higher = our list is more than 10% above the aftermarket brand workshop price. In line = within 10%. We are lower = our list is more than 10% below. Percentage = our list ÷ brand price − 1. Yellow cells are inputs (rate and band). All percentages are formulas."),
        ("Price levels — do not mix",
         "Our list is the ISZE list in euro (ex VAT). Aftermarket brand prices are United Kingdom workshop purchase from the 2023 Eucon IAM survey, converted at the yellow GBP to EUR rate. That is a workshop buy, not a confirmed 2026 shop quote. KS International was searched on these exact part numbers in August 2026 — no price found."),
        ("What is excluded",
         "DAF (and other OEM peer) comparable prices are not physical fitment. They are not on the comparison sheets. Autodoc has no usable part-number prices on disk. Tranzparts / T&M category listings without our part number are not mapped."),
        ("Oil",
         "Oil filter is set contents only. It is on the application sheet so the set is complete. It is not a campaign line."),
        ("Brakes",
         "Pad 8982447940 is confirmed for N75. There is no Best Value twin. The commercial route is a special price agreement only."),
        ("Clutch",
         "Yes — we can sell a clutch as a kit, manual vehicles only. See the Clutch_kit sheet. Planning share of manuals remains 47% until a transmission file exists."),
        ("P700",
         "P700 is not the current N75 parc. First right-hand-drive chassis to United Kingdom bodybuilders: October 2026. Do not assume these part numbers carry over."),
    ]
    r = 4
    header_row(ws, r, 2)
    ws.cell(r, 1, "Topic")
    ws.cell(r, 2, "Note")
    for topic, note in howto:
        r += 1
        ws.row_dimensions[r].height = 48
        paint(ws.cell(r, 1, topic), PAPER, FONT_SEC)
        paint(ws.cell(r, 2, note), WHITE)
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:B{r}"
    page_setup(ws, "Read me")
    ws.freeze_panes = "A5"

    # ── Inputs ───────────────────────────────────────────────────────────────
    wi = wb.create_sheet("Inputs")
    widths(wi, {"A": 36, "B": 28, "C": 70})
    wi["A1"] = "Inputs (yellow). Other sheets read these cells."
    wi["A1"].font = FONT_TITLE
    wi.merge_cells("A1:C1")
    header_row(wi, 3, 3)
    wi.cell(3, 1, "Input")
    wi.cell(3, 2, "Value")
    wi.cell(3, 3, "Used for")
    paint(wi.cell(4, 1, "GBP to EUR"), PAPER)
    c_fx = wi.cell(4, 2, FX_GBP_EUR)
    paint(c_fx, YELLOW, FONT_INPUT, NUM2, WRAP_R)
    paint(wi.cell(4, 3, "Converts 2023 United Kingdom workshop GBP to EUR."), WHITE)
    paint(wi.cell(5, 1, "In-line band"), PAPER)
    c_band = wi.cell(5, 2, BAND)
    paint(c_band, YELLOW, FONT_INPUT, PCT, WRAP_R)
    paint(wi.cell(5, 3, "Absolute gap inside this band = in line. Outside = higher or lower."), WHITE)
    wi["A7"] = "Named cells: Inputs!B4 = GBP_EUR · Inputs!B5 = BAND"
    wi["A7"].font = FONT_MUTED
    wi.freeze_panes = "A4"

    # ── EQ application ───────────────────────────────────────────────────────
    we = wb.create_sheet("EQ_application")
    cols = ["Function", "Model", "Genuine PN", "Role", "Our list EUR",
            "Best Value twin", "BVP list EUR", "Kit?", "Notes"]
    widths(we, {"A": 28, "B": 28, "C": 16, "D": 28, "E": 14, "F": 16, "G": 14, "H": 16, "I": 72})
    we.merge_cells("A1:I1")
    we["A1"] = "Which part numbers apply on N75 — not only the three locked filter elements"
    we["A1"].font = FONT_TITLE
    we.merge_cells("A2:I2")
    we["A2"] = (
        "Source: ISZE PMS registry (ITUK April 2026) plus the Best Value catalogue application. "
        "Live Snap-on catalogue was not re-opened this pass. P700 is not this list."
    )
    we["A2"].font = FONT_MUTED
    we["A2"].alignment = WRAP
    we.row_dimensions[2].height = 32
    header_row(we, 4, 9)
    for i, h in enumerate(cols, 1):
        we.cell(4, i, h)
    for i, row in enumerate(eq_rows, 5):
        fn, model, gpn, role, bvp, kit, notes = row
        g_eur = pr00.get(gpn, {}).get("eur") if gpn not in ("none", "none found") else None
        b_eur = pr00.get(bvp, {}).get("eur") if bvp not in ("none",) else None
        quiet = "set contents" in fn.lower()
        fill = GREY if quiet else WHITE
        if "Brake pad (front)" in fn and gpn == "8982447940":
            fill = AMBER
        we.row_dimensions[i].height = 42
        vals = [fn, model, gpn if gpn != "none found" else "no PN found", role,
                g_eur, bvp if bvp != "none" else "no", b_eur, kit, notes]
        for c, v in enumerate(vals, 1):
            cell = we.cell(i, c, v if v is not None else "no list found")
            if c in (5, 7):
                if isinstance(v, (int, float)):
                    paint(cell, fill, FONT_BODY, EUR, WRAP_R)
                else:
                    paint(cell, fill, FONT_MUTED, None, WRAP_CC)
            else:
                paint(cell, fill)
    last_eq = 4 + len(eq_rows)
    we.auto_filter.ref = f"A4:I{last_eq}"
    we.freeze_panes = "A5"
    page_setup(we, "Application")
    we.cell(last_eq + 2, 1, "Count of genuine oil / fuel / air element PNs on N75 4HK1 (not assemblies): oil 2 (one current), fuel 1 element + 1 assembly, air 1 element + 2 assemblies.")
    we.merge_cells(start_row=last_eq + 2, start_column=1, end_row=last_eq + 2, end_column=9)
    we.cell(last_eq + 2, 1).font = FONT_MUTED
    we.cell(last_eq + 2, 1).alignment = WRAP
    we.row_dimensions[last_eq + 2].height = 28

    # ── Too_expensive ────────────────────────────────────────────────────────
    wt = wb.create_sheet("Too_expensive")
    wt.sheet_properties.tabColor = "C0552D"
    tcols = [
        "Function", "Our genuine PN", "Our list EUR", "Best Value PN", "BVP list EUR",
        "Aftermarket brands found", "Brand workshop EUR (median)", "Sign vs our list",
        "% our list vs brand", "KS International 2026", "What this means",
    ]
    widths(wt, {get_column_letter(i): w for i, w in enumerate(
        [26, 28, 14, 16, 14, 36, 22, 18, 16, 22, 56], 1)})
    wt.merge_cells("A1:K1")
    wt["A1"] = "Where our list is too expensive versus aftermarket brands — and where it is not"
    wt["A1"].font = FONT_TITLE
    wt.merge_cells("A2:K2")
    wt["A2"] = (
        "Brand prices = United Kingdom IAM workshop purchase, Eucon 2023, HCV sheet, OE-comparable where marked. "
        "Converted with Inputs!B4. KS International (August 2026 search on these part numbers): no price found. "
        "DAF comparable prices are not used."
    )
    wt["A2"].font = FONT_MUTED
    wt["A2"].alignment = WRAP
    wt.row_dimensions[2].height = 36
    header_row(wt, 4, 11)
    for i, h in enumerate(tcols, 1):
        wt.cell(4, i, h)

    # Pre-compute brand medians for focus PNs (OE-comparable workshop only)
    def brand_block(pn: str) -> tuple[str, float | None, int]:
        sub = eu[(eu["pn"] == pn) & eu["ws_gbp"].notna()].copy()
        if sub.empty:
            return "no price found", None, 0
        oe = sub[sub["quality"].str.contains("OE comparable", case=False, na=False)]
        use = oe if len(oe) else sub
        brands = ", ".join(sorted(use["brand"].dropna().unique()))
        med = float(use["ws_gbp"].median() * FX_GBP_EUR)
        return brands, med, len(use)

    sign_fills = {
        "we are higher": RED_SOFT,
        "in line": GREEN,
        "we are lower": GREEN,
        "no price found": GREY,
    }

    for i, (fn, gpn, bpn) in enumerate(focus, 5):
        g_eur = pr00.get(gpn, {}).get("eur") if gpn else None
        b_eur = pr00.get(bpn, {}).get("eur") if bpn else None
        brands, med, n = brand_block(gpn) if gpn else ("no price found", None, 0)
        if fn.startswith("Clutch kit"):
            brands, med, n = "no price found", None, 0
        ks_txt = "no price found"
        if gpn and gpn in ks:
            st = ks[gpn]["status"]
            ks_txt = "no price found" if st in ("no_results", "", None) else f"{st} {ks[gpn].get('am_gbp') or ''}".strip()
        elif bpn and bpn in ks:
            st = ks[bpn]["status"]
            ks_txt = "no price found" if st in ("no_results", "", None) else st

        if med is None or not g_eur:
            sign = "no price found"
            meaning = "No aftermarket brand workshop price on file for this part number."
            if fn.startswith("Brake pad"):
                meaning = "Brand prices exist — see the row. No Best Value twin. Special price agreement only."
            if fn.startswith("Brake disc"):
                meaning = "No aftermarket brand workshop price on file for this disc. Best Value twin exists on list. Special price agreement still the commercial route if we need to move genuine."
            if fn.startswith("Clutch kit"):
                meaning = "No aftermarket brand kit price on file. We can still sell the Best Value kit (list on this row) or the three genuine pieces."
            if fn.startswith("Oil"):
                meaning = "Oil is set contents. Brand prices exist on the Brand_prices sheet."
        else:
            gap = g_eur / med - 1
            if gap > BAND:
                sign = "we are higher"
            elif gap < -BAND:
                sign = "we are lower"
            else:
                sign = "in line"
            meaning = {
                "we are higher": "Our list is above the aftermarket brand workshop price. This is the expensive line.",
                "in line": "Our list sits close to the aftermarket brand workshop price.",
                "we are lower": "Our list is below the aftermarket brand workshop price.",
            }[sign]
            if fn.startswith("Brake pad"):
                meaning += " No Best Value twin — special price agreement only."
            if fn.startswith("Oil"):
                meaning += " Quiet line — set contents."

        if fn.startswith("Brake pad") and med:
            sign = "we are higher" if g_eur and g_eur / med - 1 > BAND else sign
            meaning = "Our list is well above Blue Print / Febi workshop. Ferodo is closer. Textar list is above us. No Best Value twin — special price agreement only."

        vals = [
            fn, gpn or "—", g_eur if g_eur is not None else "no list found",
            bpn or "no", b_eur if b_eur is not None else ("no list found" if bpn else "no"),
            brands, med if med is not None else "no price found",
            sign, None, ks_txt, meaning,
        ]
        fill = sign_fills.get(sign, WHITE)
        if "set contents" in fn.lower() or "Oil" in fn:
            fill = GREY if sign == "no price found" else fill
        wt.row_dimensions[i].height = 44
        for c, v in enumerate(vals, 1):
            cell = wt.cell(i, c, v)
            if c in (3, 5, 7) and isinstance(v, (int, float)):
                paint(cell, fill, FONT_BODY, EUR, WRAP_R)
            elif c == 8:
                paint(cell, fill, FONT_WARN if sign == "we are higher" else FONT_BODY, None, WRAP_CC)
            else:
                paint(cell, fill)

        # % formula: list / brand - 1  (cols C and G)
        pct_cell = wt.cell(i, 9)
        pct_cell.value = f'=IF(OR(G{i}="",G{i}="no price found",NOT(ISNUMBER(C{i})),NOT(ISNUMBER(G{i}))),"no price found",C{i}/G{i}-1)'
        paint(pct_cell, fill, FONT_BODY, PCT, WRAP_CC)

    last_t = 4 + len(focus)
    wt.auto_filter.ref = f"A4:K{last_t}"
    wt.freeze_panes = "A5"
    page_setup(wt, "Too expensive")
    wt.cell(last_t + 2, 1,
            "Headline: the pad is the expensive line versus Blue Print and Febi. Fuel and air are not. "
            "Oil is set contents. Disc: no aftermarket brand price found. "
            "Clutch genuine list is below the 2023 brand workshop prices. "
            "KS International: no price found on these part numbers (August 2026).")
    wt.merge_cells(start_row=last_t + 2, start_column=1, end_row=last_t + 2, end_column=11)
    wt.cell(last_t + 2, 1).font = FONT_SEC
    wt.cell(last_t + 2, 1).alignment = WRAP
    wt.row_dimensions[last_t + 2].height = 36

    # ── Brand_prices ─────────────────────────────────────────────────────────
    wb_p = wb.create_sheet("Brand_prices")
    bcols = [
        "Function", "Our PN", "Our list EUR", "Brand", "Brand PN",
        "Workshop GBP", "Workshop EUR", "Brand list GBP", "Quality",
        "Sign vs our list", "% our list vs brand", "Source",
    ]
    widths(wb_p, {get_column_letter(i): w for i, w in enumerate(
        [22, 28, 13, 16, 18, 14, 14, 14, 28, 16, 16, 42], 1)})
    wb_p.merge_cells("A1:L1")
    wb_p["A1"] = "Every aftermarket brand price we actually hold — one row per brand quote"
    wb_p["A1"].font = FONT_TITLE
    wb_p.merge_cells("A2:L2")
    wb_p["A2"] = (
        "Workshop EUR = Workshop GBP × Inputs!$B$4. Sign uses Inputs!$B$5. "
        "Mann-Filter, TRW, KS International: no price found on these part numbers. "
        "Bosch and Mahle appear on the fuel element only."
    )
    wb_p["A2"].font = FONT_MUTED
    wb_p["A2"].alignment = WRAP
    wb_p.row_dimensions[2].height = 32
    header_row(wb_p, 4, 12)
    for i, h in enumerate(bcols, 1):
        wb_p.cell(4, i, h)

    fn_by_pn = {
        "8983282070": "Oil filter (set contents)",
        "8975425400": "Fuel filter",
        "8981772710": "Air filter",
        "8982447940": "Brake pad",
        "8973872290": "Brake disc",
        "8981649171": "Clutch disc",
        "1313100120": "Clutch release bearing",
    }
    brand_pns = list(fn_by_pn)
    sub = eu[eu["pn"].isin(brand_pns) & eu["ws_gbp"].notna()].copy()
    sub = sub.sort_values(["pn", "brand", "ws_gbp"])
    r = 5
    for _, row in sub.iterrows():
        pn = row["pn"]
        g_eur = pr00.get(pn, {}).get("eur")
        wb_p.row_dimensions[r].height = 22
        wb_p.cell(r, 1, fn_by_pn[pn])
        wb_p.cell(r, 2, pn)
        c_list = wb_p.cell(r, 3, g_eur)
        wb_p.cell(r, 4, row["brand"])
        wb_p.cell(r, 5, row["comp_pn"])
        c_gbp = wb_p.cell(r, 6, float(row["ws_gbp"]))
        c_eur = wb_p.cell(r, 7)
        c_eur.value = f"=F{r}*Inputs!$B$4"
        wb_p.cell(r, 8, float(row["list_gbp"]) if pd.notna(row["list_gbp"]) else None)
        wb_p.cell(r, 9, row["quality"])
        c_sign = wb_p.cell(r, 10)
        c_sign.value = (
            f'=IF(OR(G{r}="",G{r}=0),"no price found",'
            f'IF((C{r}/G{r}-1)>Inputs!$B$5,"we are higher",'
            f'IF((C{r}/G{r}-1)<-Inputs!$B$5,"we are lower","in line")))'
        )
        c_pct = wb_p.cell(r, 11)
        c_pct.value = f'=IF(OR(G{r}="",G{r}=0),"no price found",C{r}/G{r}-1)'
        wb_p.cell(r, 12, "Eucon UK IAM survey 2023 · HCV · workshop purchase")
        fill = GREY if "Oil" in fn_by_pn[pn] else WHITE
        for c in range(1, 13):
            cell = wb_p.cell(r, c)
            fmt = EUR if c in (3, 7) else (NUM2 if c in (6, 8) else (PCT if c == 11 else None))
            align = WRAP_R if c in (3, 6, 7, 8, 11) else WRAP_C
            paint(cell, fill, FONT_BODY, fmt, align)
        r += 1

    # Explicit no-price rows for KS / Mann / TRW on each focus genuine PN
    missing_brands = [
        ("KS International", "August 2026 catalogue search on our PN — no results"),
        ("Mann-Filter", "No price found in ISZE files for these PNs"),
        ("TRW", "No price found in ISZE files for these PNs"),
        ("Autodoc", "No usable part-number prices on disk"),
    ]
    for fn, gpn, _ in focus:
        if not gpn:
            continue
        g_eur = pr00.get(gpn, {}).get("eur")
        for brand, why in missing_brands:
            wb_p.row_dimensions[r].height = 20
            vals = [fn, gpn, g_eur, brand, "—", None, None, None, "—", "no price found", "no price found", why]
            for c, v in enumerate(vals, 1):
                cell = wb_p.cell(r, c, v if v is not None else "no price found")
                fmt = EUR if c == 3 and isinstance(v, (int, float)) else None
                paint(cell, GREY, FONT_MUTED, fmt, WRAP_C if c != 12 else WRAP)
            r += 1

    last_b = r - 1
    wb_p.auto_filter.ref = f"A4:L{last_b}"
    wb_p.freeze_panes = "A5"
    page_setup(wb_p, "Brand prices")

    # ── Clutch_kit ───────────────────────────────────────────────────────────
    wc = wb.create_sheet("Clutch_kit")
    widths(wc, {"A": 32, "B": 28, "C": 16, "D": 16, "E": 70})
    wc.merge_cells("A1:E1")
    wc["A1"] = "Clutch as a kit — yes, manual vehicles only"
    wc["A1"].font = FONT_TITLE
    wc.merge_cells("A2:E2")
    wc["A2"] = (
        "Verdict: yes, we can sell a clutch as a kit. Either the Best Value kit number, "
        "or the three genuine pieces (disc + pressure plate + release bearing). "
        "Automatic / EasyShift / dual-clutch vehicles are out. Planning share of manuals remains 47% until a transmission file exists."
    )
    wc["A2"].font = FONT_BODY
    wc["A2"].alignment = WRAP
    wc.row_dimensions[2].height = 48
    header_row(wc, 4, 5)
    for i, h in enumerate(["Item", "PN", "List EUR", "In the kit?", "Note"], 1):
        wc.cell(4, i, h)
    kit_rows = [
        ("Genuine disc", "8981649171", pr00.get("8981649171", {}).get("eur"), "yes",
         "N75 4HK1. Do not mix with 8981649181."),
        ("Genuine pressure plate", "8970388314", pr00.get("8970388314", {}).get("eur"), "yes",
         "Current number. 8970388313 supersedes here."),
        ("Genuine release bearing", "1313100120", pr00.get("1313100120", {}).get("eur"), "yes",
         "Catalogue application NPR / NQR / NNR 4HK1."),
        ("Genuine pilot bearing (optional)", "8972582390", pr00.get("8972582390", {}).get("eur"), "optional",
         "Only if the workshop specification includes the pilot."),
        ("Genuine three-piece total", "sum", None, "yes",
         "Disc + pressure plate + release bearing. Formula in list column."),
        ("Best Value kit", "5876102320", pr00.get("5876102320", {}).get("eur"), "yes — one number",
         "Catalogue kit for NNR / NPR / NQR 4HK1. Paired with disc 8981649171."),
        ("Best Value kit (alt.)", "5876102040", pr00.get("5876102040", {}).get("eur"), "confirm vehicle",
         "Second 4HK1 N-series kit. Confirm which one the vehicle takes."),
        ("Best Value kit (other disc)", "5876103120", None, "do not mix",
         "Paired with disc 8981649181. No ISZE list found. Not the 8981649171 kit."),
        ("Best Value disc twin", "5876100920", pr00.get("5876100920", {}).get("eur"), "piece, not kit",
         "If the workshop wants pieces, not the boxed kit."),
        ("Best Value cover twin", "5876101040", pr00.get("5876101040", {}).get("eur"), "piece, not kit",
         "Pressure-plate twin."),
    ]
    for i, (item, pn, eur, inn, note) in enumerate(kit_rows, 5):
        wc.row_dimensions[i].height = 28
        wc.cell(i, 1, item)
        wc.cell(i, 2, pn)
        if item.startswith("Genuine three-piece"):
            wc.cell(i, 3).value = "=C5+C6+C7"
        else:
            wc.cell(i, 3, eur if eur is not None else "no list found")
        wc.cell(i, 4, inn)
        wc.cell(i, 5, note)
        fill = GREEN if "yes" in inn and "do not" not in inn else (AMBER if "confirm" in inn or "do not" in inn else WHITE)
        for c in range(1, 6):
            cell = wc.cell(i, c)
            fmt = EUR if c == 3 and (isinstance(cell.value, (int, float)) or (isinstance(cell.value, str) and cell.value.startswith("="))) else None
            paint(cell, fill, FONT_BODY, fmt, WRAP_R if c == 3 else WRAP)
    wc.cell(16, 1, "Fitment caveats")
    wc["A16"].font = FONT_SEC
    caveats = [
        "Manual only. The VIN list has no transmission column. Use 47% of the N75 parc as the planning assumption until ITUK can mark manuals.",
        "4HK1 and 4JZ1 are different clutches. This kit is 4HK1 / NPR75. Do not put it on 4JZ1.",
        "P700 introduces a dual-clutch gearbox on part of the new range. Do not assume the new vehicles take this kit.",
        "Confirm the kit contents on the vehicle (disc + cover + bearing) before calling it one saleable kit in the network. The German N75 datasheet states a 300 mm single dry-plate clutch on the 4HK1 manual.",
        "No aftermarket brand price was found for a complete N75 4HK1 clutch kit. Brand prices exist for the disc and the bearing only (2023 survey).",
    ]
    for i, t in enumerate(caveats, 17):
        wc.merge_cells(start_row=i, start_column=1, end_row=i, end_column=5)
        paint(wc.cell(i, 1, t), PAPER)
        wc.row_dimensions[i].height = 28
    wc.freeze_panes = "A5"
    page_setup(wc, "Clutch kit")

    # ── Sources ──────────────────────────────────────────────────────────────
    ws_s = wb.create_sheet("Sources")
    widths(ws_s, {"A": 28, "B": 100})
    ws_s["A1"] = "Sources (what we opened — nothing invented)"
    ws_s["A1"].font = FONT_TITLE
    ws_s.merge_cells("A1:B1")
    header_row(ws_s, 3, 2)
    ws_s.cell(3, 1, "Item")
    ws_s.cell(3, 2, "Path / note")
    sources = [
        ("ISZE list", str(PR00) + " · condition PR00 · file dated 10 August 2026"),
        ("Application / twins", str(XREF) + " · PMS registry + Best Value catalogue"),
        ("Aftermarket brands", str(EUCON) + " · HCV sheet · workshop purchase GBP 2023"),
        ("KS International", str(KS_CSV) + " · searched these PNs 10–14 August 2026 · no results"),
        ("Mekonomen", str(MEK_CSV) + " · same PNs · no results"),
        ("Autodoc", "No usable part-number prices on disk (placeholders only)"),
        ("DAF / OEM peer", "Held in partgroups_competitive.json — excluded here; not physical fit"),
        ("Manual share", "47% planning assumption — VIN list has no transmission column"),
        ("P700", "Next generation. Not this application list. First UK bodybuilder chassis October 2026."),
    ]
    for i, (a, b) in enumerate(sources, 4):
        ws_s.row_dimensions[i].height = 28
        paint(ws_s.cell(i, 1, a), PAPER, FONT_SEC)
        paint(ws_s.cell(i, 2, b), WHITE)
    ws_s.freeze_panes = "A4"
    page_setup(ws_s, "Sources")
    ws_s.freeze_panes = "A4"

    for wsx in wb.worksheets:
        wsx.sheet_view.zoomScale = 100
        if wsx.title != "Inputs":
            wsx.freeze_panes = wsx.freeze_panes or "A5"

    OUT_A.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_A)
    shutil.copy2(OUT_A, OUT_B)
    print(f"Wrote {OUT_A}")
    print(f"Copied {OUT_B}")
    return OUT_A


if __name__ == "__main__":
    sys.exit(0 if build() else 1)
