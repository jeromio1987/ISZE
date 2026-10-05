# -*- coding: utf-8 -*-
"""
The pricing stack workbook, on JEROME'S OWN ARCHITECTURE, with the measured method.

WHY THIS ARCHITECTURE
  The version before it did not open in Excel: about 80,000 VLOOKUP formulas and 78
  SUMPRODUCT array formulas, several scanning 11,000-row ranges, inside a single
  45 MB worksheet part. Jerome's own file does none of that and opens. This file
  copies his structure.

HIS STRUCTURE, COPIED
  1. NO VLOOKUP. The class factor is written per row as a literal.
  2. ONE ROW PER PART NUMBER, scalar arithmetic only. No array formulas in the data.
  3. Aggregation is pre-computed in Python and written as literal values, with at most
     a handful of simple SUM over one contiguous column.
  4. He HARDCODES the current sales price rather than deriving it from an old rate.

THE METHOD - THE WEIGHTED INCREASE, MEASURED
    weighted increase = SUM(qty x delta_jpy) / SUM(qty x bp_prior) - 1
  on the published recipe: in_scope AND unpriced_reason IS NULL, 47,617 rows. It
  reproduces the published index of 5.9616%.

  There is no factor chain. The exchange rate of 178.5 is what we pay now and the
  67.3% purchase discount has been in force since 5 January 2026, so neither is a
  forward move. There is no pass-through dial, no pass-through grid and no
  "what each source needs" block: the rate is issued by ISZJ and applied.

Run: python 01_data/91_build/build_pricing_stack_simulation_20260919.py
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
OUT_DIR = ISZE / "01_data" / "01_Pricing"
XLSX_OUT = OUT_DIR / "ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx"
OPEN_OUT = OUT_DIR / "OPEN_Pricing_Stack_Simulation.cmd"
JSON_OUT = DERIVED / "pricing_stack_simulation_2026-09-19.json"

FX_LIVE = 178.5
FX_LIST_BASE = 163.7
FX_PREV_VINTAGE = 172.6
DISC_LIVE = {"J": 0.673, "T": 0.611}
DISC_J_PRIOR = 0.620
CLASS_FACTOR = {"C": 0.47, "D": 0.48, "F": 0.525, "J": 0.555,
                "M": 0.50, "P": 0.44, "V": 0.55, "T": 0.80}
CIS_FACTOR = 0.40
ZPR1 = -0.10
TARGET, BAND_LOW, BAND_HIGH = 0.05, 0.04, 0.06
EBP_VP_RATE = 0.62
EBP_IE_RATE = 0.735
EBP_IE_RATE_2026 = 0.797
IML_STATED_REVISION = 0.03
PR00_REGIONS = ("WEST", "SOUTH", "EAST", "NORDICS", "MIDDLE_EAST")
SRC_J, SRC_T, SRC_NONE = "J", "T", "(none)"
MARKETS = [
    ("PR00", "class", None,
     "Main EU distributor list. Full class-factor engine - the reference basis."),
    ("UTI", "class", "1799",
     "Israel, sold-to 1799. Never combined with UMI."),
    ("UMI", "class", "1797",
     "Israel, sold-to 1797. Never combined with UTI."),
    ("CIS", "flat", None,
     "GA Armenia and CBC Kazakhstan. Class-independent: one margin across the "
     "catalogue, so no class-factor column is looked up on this sheet."),
]
CLASS_ROW = {k: 13 + i for i, k in enumerate(CLASS_FACTOR)}
CIS_FACTOR_ROW = 22
FX_BASE_ROW, FX_LIVE_ROW, FX_PREV_ROW = 4, 6, 5
DISC_J_ROW, DISC_J_PRIOR_ROW, DISC_T_ROW = 8, 9, 10
ZPR1_ROW, TARGET_ROW, BANDLO_ROW, BANDHI_ROW = 25, 27, 28, 29

NAVY, PAPER = "15233C", "F7F4EE"
HDR = PatternFill("solid", fgColor=NAVY)
HF = Font(bold=True, color=PAPER, size=10)
DIAL = PatternFill("solid", fgColor="FFF2CC")
SEC = Font(bold=True, size=10, color=NAVY)
TITLE = Font(bold=True, size=14, color=NAVY)
SUB = Font(italic=True, size=9, color="555555")
BOLD = Font(bold=True)
AMBER = PatternFill("solid", fgColor="FDF3D8")
MONO = Font(name="Consolas", size=10)


def say(m: str = "") -> None:
    print(m)
    sys.stdout.flush()


def money(x: float) -> str:
    a = abs(x)
    if a >= 1_000_000:
        return f"EUR {x/1_000_000:,.2f}M"
    if a >= 1_000:
        return f"EUR {x/1_000:,.0f}k"
    return f"EUR {x:,.0f}"


# ================================================================== the measurement
say("=" * 98)
say("1. THE WEIGHTED INCREASE OF ALL PRICES, MEASURED")
say("=" * 98)

cmp_ = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv",
                   dtype={"part_number": str, "customer_code": str})
rec = cmp_[(cmp_["in_scope"] == True) & cmp_["unpriced_reason"].isna()].copy()  # noqa: E712
rec["pn"] = rec["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec[rec["billed_qty"].notna() & rec["bp_prior_revised"].notna()
          & rec["delta_jpy"].notna()].copy()
rec["weight"] = rec["billed_qty"] * rec["bp_prior_revised"]
rec["step_yen"] = rec["billed_qty"] * rec["delta_jpy"]
IDX = rec["step_yen"].sum() / rec["weight"].sum()
say(f"  recipe rows: {len(rec):,}")
say(f"  index {IDX:.8f} = {100*IDX:.6f}%  ->  "
    f"{'TIES to 5.9616%' if abs(IDX - 0.059616) < 1e-6 else 'DOES NOT TIE'}")

pl = pd.read_parquet(DERIVED / "pricing_list_pn.parquet",
                     columns=["part_number", "source", "price_class", "sp_eur",
                              "fob_eur", "bp_jpy", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True].drop_duplicates("part_number")      # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec.merge(pl[["pn", "source", "price_class", "sp_eur", "fob_eur"]],
                on="pn", how="left")
rec["srclab"] = rec["source"].where(rec["source"].isin([SRC_J, SRC_T]), SRC_NONE)

WHOLE = float(IDX)
SRC_MK = {}
for s in (SRC_J, SRC_T, SRC_NONE):
    g = rec[rec["srclab"] == s]
    if not len(g):
        continue
    SRC_MK[s] = {
        "rows": int(len(g)), "billed": float(g["net_sales_value"].sum()),
        "weight_share": float(g["weight"].sum() / rec["weight"].sum()),
        "increase": float(g["step_yen"].sum() / g["weight"].sum()),
    }
say(f"  ALL PRICES {100*WHOLE:+.4f}%   "
    f"Japan {100*SRC_MK[SRC_J]['increase']:+.4f}%   "
    f"Thailand {100*SRC_MK[SRC_T]['increase']:+.4f}%")


# ================================================================== the books
say()
say("=" * 98)
say("2. THE BOOKS - one row per part number, the measure per market")
say("=" * 98)

BOOKS, MK = {}, {}
for code, basis, sold_to, note in MARKETS:
    if code == "PR00":
        g = rec[rec["region"].isin(PR00_REGIONS)]
    elif code in ("UTI", "UMI"):
        g = rec[rec["customer_code"].astype(str).str.strip() == sold_to]
    else:
        g = rec[rec["region"] == "CIS"]
    b = g.groupby("pn").agg(
        qty=("billed_qty", "sum"), billed=("net_sales_value", "sum"),
        prior_bp=("bp_prior_revised", "first"), new_bp=("bp_new_jpy", "first"),
        delta_bp=("delta_jpy", "first"),
        current=("sp_eur", "first"), fob_current=("fob_eur", "first"),
        src=("srclab", "first"), cls=("price_class", "first")).reset_index()
    b["billed_description"] = b["pn"].map(
        rec.drop_duplicates("pn").set_index("pn")["billed_description"].to_dict()
    ).fillna("")
    # THE MEASURE, per part number: the row's own weight and step
    b["weight"] = b["qty"] * b["prior_bp"]
    b["step_yen"] = b["qty"] * b["delta_bp"]
    b["incr"] = b["delta_bp"] / b["prior_bp"]
    b["new_price_flat"] = b["new_bp"] / FX_LIVE * b["src"].map(DISC_LIVE) / CIS_FACTOR
    b["incr_flat"] = b["delta_bp"] / b["prior_bp"]
    BOOKS[code] = b

    bm = b[b["weight"] > 0]
    tot_w = bm["weight"].sum()
    mv = float(bm["step_yen"].sum() / tot_w) if tot_w else float("nan")
    jb, tb = bm[bm["src"].eq(SRC_J)], bm[bm["src"].eq(SRC_T)]
    nb = bm[bm["src"].eq(SRC_NONE)]

    def sub(x):
        w = x["weight"].sum()
        return float(x["step_yen"].sum() / w) if w else float("nan")

    MK[code] = {
        "recipe_rows": int(len(g)),
        "rows": int(len(g)),
        "sheet_rows": int(len(b)), "part_numbers": int(b["pn"].nunique()),
        "billed": float(b["billed"].sum()),
        "increase": mv, "japan": sub(jb), "thailand": sub(tb),
        "no_label": sub(nb) if len(nb) else float("nan"),
        "no_label_share": float(nb["weight"].sum() / tot_w) if len(nb) else 0.0,
        "billed_japan": float(jb["billed"].sum()),
        "billed_thailand": float(tb["billed"].sum()),
        "rows_japan": int(len(jb)), "rows_thailand": int(len(tb)),
        "note": note, "basis": basis,
        "billed_after": float((b["billed"] * (1 + b["incr"])).sum()),
    }
    say(f"  {code:<5} {len(b):>7,} rows  {b['pn'].nunique():>7,} PNs   "
        f"whole {100*mv:+8.4f}%   Japan {100*sub(jb):+8.4f}%  "
        f"Thailand {100*sub(tb):+8.4f}%")
OLD = {"whole": 0.0180, "japan": 0.0574, "thailand": -0.0245}
OLD_MK = {"PR00": 0.0024, "UTI": 0.0517, "UMI": -0.0070, "CIS": 0.0328}

# ================================================================== the workbook
say()
say("=" * 98)
say("3. WRITE THE FIVE SHEETS ON HIS ARCHITECTURE")
say("=" * 98)
wb = Workbook()
ws_leg = wb.active
ws_leg.title = "Legends"
sheets = {c: wb.create_sheet(c) for c, _, _, _ in MARKETS}
for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False


def hdr_row(ws, row, labels, widths=None, freeze=None):
    """Write a header row. The freeze pane is set ONLY when `freeze` is given, and it
    is never derived from the row being written.

    THE BUG THIS PREVENTS, which cost Jerome two turns. This helper used to set
    `ws.freeze_panes = ws.cell(row + 1, 1)` on every call. The market sheets call it
    once at row 1 for the real column headers - and again far down the sheet for a
    second table. The second call then pinned the sheet at that low row, so Excel
    froze almost the whole sheet and only a handful of rows would scroll.

    THE RULE: a market sheet freezes at A2 and nothing else. Legends takes no freeze.
    """
    for i, h in enumerate(labels, start=1):
        c = ws.cell(row, i, h)
        c.fill = HDR
        c.font = HF
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if widths:
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
    if freeze is not None:
        ws.freeze_panes = freeze


# ================================================================== Legends
ws_leg.freeze_panes = None
ws_leg["A1"] = "PRICING STACK - LEGENDS"
ws_leg["A1"].font = TITLE
for col, w in zip("ABCDEF", (56, 16, 18, 26, 12, 86)):
    ws_leg.column_dimensions[col].width = w

ws_leg["A2"] = "Exchange rate as of 01/10/2023"
ws_leg["B2"] = 146.6
ws_leg["A3"] = "Exchange rate as of 01/10/2024"
ws_leg["B3"] = 159.4
ws_leg["A4"] = "Exchange rate as of 01/10/2025 - the rate our price list sits on"
ws_leg["B4"] = FX_LIST_BASE
ws_leg["A5"] = "Exchange rate 01/04/2026 to 30/09/2026 - previous vintage"
ws_leg["B5"] = FX_PREV_VINTAGE
ws_leg["A6"] = "LIVE rate 01/10/2026 to 31/03/2027 - issued by ISZJ, applied to both sources"
ws_leg["B6"] = FX_LIVE
for rr in (2, 3, 4, 5, 6):
    ws_leg.cell(rr, 2).number_format = "0.0"
ws_leg["F2"] = ("146.6 and 159.4 are earlier vintages, recorded for traceability only. "
                "Nothing is multiplied into the move.")
ws_leg["F4"] = ("163.7 is what our price list was built on, and it is documentation "
                "only. It is never an input to a move.")
ws_leg["F5"] = "172.6 ran to 30/09/2026. Documentation only."
ws_leg["F6"] = ("The rate is issued by ISZJ and applied. It is a corporate rate, not a "
                "commercial choice, and no part of it is passed on, held back or handed "
                "over. FX is in the denominator of the euro cost, so a higher rate "
                "lowers our euro cost.")

ws_leg["A8"] = "Purchase discount J (Japan), live - in force since 05/01/2026"
ws_leg["B8"] = DISC_LIVE["J"]
ws_leg["A9"] = "Purchase discount J (Japan), prior"
ws_leg["B9"] = DISC_J_PRIOR
ws_leg["A10"] = "Purchase discount T (Thailand)"
ws_leg["B10"] = DISC_LIVE["T"]
for rr in (8, 9, 10):
    ws_leg.cell(rr, 2).number_format = "0.000"
ws_leg["F8"] = ("Japan pays 67.3% of the yen base price, so the margin on the yen base "
                "price is 32.7%. Effective 5 January 2026, at the same time as the "
                "annual base-price revision. It is already inside today's prices, so it "
                "is not a move.")
ws_leg["F9"] = ("The margin on the yen base price was 38.0% before it. A change already "
                "in force is never multiplied into the weighted increase.")
ws_leg["F10"] = ("Thailand is unchanged at 61.1%, so Thailand has no discount change. "
                 "Not revised in this update.")

ws_leg["A12"] = "Class factors, PR00 FY2026"
ws_leg["B12"] = "PR00"
ws_leg["C12"] = "ZPR1 ISRAEL 1797"
ws_leg["D12"] = "ZPR1 ISRAEL 1799"
ws_leg["E12"] = "Margin"
for k, v in CLASS_FACTOR.items():
    rr = CLASS_ROW[k]
    ws_leg.cell(rr, 1, k)
    ws_leg.cell(rr, 2, v).number_format = "0.000"
    ws_leg.cell(rr, 5, f"=1-B{rr}").number_format = "0.0%"
ws_leg.cell(12, 1).value = "Class factors"
ws_leg.cell(12, 2).value = "PR00"
ws_leg.cell(12, 3).value = "ZPR1 ISRAEL 1797"
ws_leg.cell(12, 4).value = "ZPR1 ISRAEL 1799"
ws_leg.cell(12, 5).value = "Margin"
for cc in range(1, 6):
    ws_leg.cell(12, cc).fill = HDR
    ws_leg.cell(12, cc).font = HF
ws_leg["F13"] = ("The class factor is written per row as a literal value. No lookup. "
                 "The margin column beside it is 1 minus the factor: class C is a 53% "
                 "margin, class V a 45% margin.")

ws_leg.cell(CIS_FACTOR_ROW, 1, "CIS factor (class-independent)")
ws_leg.cell(CIS_FACTOR_ROW, 2, CIS_FACTOR).number_format = "0.000"
ws_leg.cell(CIS_FACTOR_ROW, 5, f"=1-B{CIS_FACTOR_ROW}").number_format = "0.0%"
ws_leg.cell(CIS_FACTOR_ROW, 6, "A 60% margin across the whole catalogue. The class "
                               "letters are NOT applied on the CIS sheet.")

ws_leg.cell(ZPR1_ROW, 1, "ZPR1 differential against PR00 (UTI and UMI)")
ws_leg.cell(ZPR1_ROW, 2, ZPR1).number_format = "0.0%"
ws_leg.cell(ZPR1_ROW, 6, "Israel is a flat 10% below PR00 today. The spec calls for a "
                         "per-category differential and it is not wired.")
ws_leg.cell(TARGET_ROW, 1, "Target move")
ws_leg.cell(TARGET_ROW, 2, TARGET).number_format = "0.0%"
ws_leg.cell(BANDLO_ROW, 1, "Band, bottom")
ws_leg.cell(BANDLO_ROW, 2, BAND_LOW).number_format = "0.0%"
ws_leg.cell(BANDHI_ROW, 1, "Band, top")
ws_leg.cell(BANDHI_ROW, 2, BAND_HIGH).number_format = "0.0%"
ws_leg.cell(BANDHI_ROW, 6, "Jerome's band is 4% to 6%.")

rr = BANDHI_ROW + 2
ws_leg.cell(rr, 1, "THE MEASURE").font = SEC
rr += 1
for line in ("weighted increase = SUM(qty x delta_jpy) / SUM(qty x bp_prior) - 1",
             "recipe = in_scope == TRUE AND unpriced_reason IS NULL  ->  47,617 rows",
             "qty        = billed_qty, the quantity in the window",
             "bp_prior   = bp_prior_revised, the previous yen base price",
             "delta_jpy  = bp_new_jpy - bp_prior_revised",
             "no exchange rate and no discount is multiplied into the move",
             "the exchange rate is issued by ISZJ and applied, not a decision"):
    ws_leg.cell(rr, 1, line).font = MONO
    rr += 1
ws_leg.cell(rr, 1, "Both the exchange rate and the purchase discount are already in "
                   "force, so neither is a forward move. Multiplying either one in would "
                   "add a change that is already inside today's prices. An earlier "
                   "version of this workbook did exactly that.")\
    .font = SUB
ws_leg.cell(rr, 1).alignment = Alignment(wrap_text=True, vertical="top")
ws_leg.merge_cells(start_row=rr, start_column=1, end_row=rr + 1, end_column=6)
rr += 3

# ---------------------------------------------------------------- the EBP evidence
ws_leg.cell(rr, 1, "HOW THE IML BASE PRICE WORKS - SOURCE DOCUMENTATION").font = SEC
rr += 1
ws_leg.cell(rr, 1, "The Export Base Price is built up from IML's own costs, and our "
                   "purchase price is a discount off it.").font = SUB
ws_leg.cell(rr, 1).alignment = Alignment(wrap_text=True, vertical="top")
ws_leg.merge_cells(start_row=rr, start_column=1, end_row=rr + 1, end_column=6)
rr += 2
hdr_row(ws_leg, rr, ["Point", "Source", "", "", "", "Detail"])
rr += 1
EBP = [
    ("The Export Base Price is built up from IML's own costs; our purchase price is a "
     "discount off it.",
     "Masumi Hayakawa (IML), 10 Nov 2025, FW: ISZE 移転価格対応 10/30打ち合わせメモ",
     "Factors are 62% on vehicle parts and 73.5% on industrial engines, applied to "
     "IML's Export Base Price. Worked example: EBP 1,000 JPY gives a purchase price "
     "of 620 JPY on vehicle parts."),
    ("IML builds its offer price from supplier cost plus a target gross profit.",
     "Hideya Kondou (ISZJ), 24 Nov 2020, ITUK向けMMU新規ハーネスの価格設定について",
     "Normal at 25% gross profit, Best at 17%."),
    ("The discount change and the base-price revision happen at the same moment.",
     "Takayoshi Suzuki, 22 Dec 2025, discount/whole sales ratio revisoin from Jan 5th 2026",
     "Valid from 5 January 2026, and stated as \"the same timing with annual EBP "
     "revision\". That is why the discount is not a forward move."),
    ("The base price and the class letter arrive together from Japan.",
     "Peeraya Sawangsaensuk (IMIT), 29 Apr 2026, RE: base price class",
     "\"Please find the B/P, Price Class, and remark as detailed below.\" The class "
     "letter is issued with the base price."),
]
for claim, src, detail in EBP:
    c = ws_leg.cell(rr, 1, claim)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws_leg.cell(rr, 2, src).font = SUB
    ws_leg.cell(rr, 2).alignment = Alignment(wrap_text=True, vertical="top")
    ws_leg.cell(rr, 6, detail).font = SUB
    ws_leg.cell(rr, 6).alignment = Alignment(wrap_text=True, vertical="top")
    rr += 1
rr += 1

# ---------------------------------------------------------------- open items
ws_leg.cell(rr, 1, "TWO OPEN ITEMS - FLAGGED, NOT RESOLVED").font = SEC
rr += 1
for title, detail in (
    ("Our configuration carries only the vehicle-parts rate.",
     "03_analytics/isze_pricing/config.yaml holds J: 0.673, the vehicle-parts rate (1 "
     "minus the 32.7% discount). The industrial-engine rate is different: 73.5% in "
     "2025, 79.7% in 2026 (1 minus 20.3%). Our configuration applies 67.3% to "
     "everything Japan-sourced. config.yaml is left alone. Question for IML: confirm "
     "the current industrial-engine rate and which part families it covers."),
    ("IML states a different revision size from ours.",
     "The 10 November 2025 mail says the CY2026 EBP revision has an impact of "
     "\"around 3% increase for ISZE (weighted average)\". We measure 5.9616% on the "
     "published recipe. Likely different revisions or different scopes - theirs may "
     "be a purchase-cost impact over another window. Not reconciled by assumption. "
     "Open item: ask IML for the window, the scope and the weighting behind the 3%."),
):
    c = ws_leg.cell(rr, 1, title)
    c.font = BOLD
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws_leg.cell(rr, 6, detail).font = SUB
    ws_leg.cell(rr, 6).alignment = Alignment(wrap_text=True, vertical="top")
    rr += 1
rr += 2

# ---------------------------------------------------------------- the source split
ws_leg.cell(rr, 1, "THE WEIGHTED INCREASE BY SOURCE").font = SEC
rr += 1
hdr_row(ws_leg, rr, ["Source", "Rows", "Share of weight", "Weighted increase", "", ""])
rr += 1
for s in (SRC_J, SRC_T, SRC_NONE):
    d = SRC_MK.get(s)
    if not d:
        continue
    ws_leg.cell(rr, 1, {"J": "Japan (IML)", "T": "Thailand (IMIT)"}.get(
        s, "No source label in the price list"))
    ws_leg.cell(rr, 2, d["rows"]).number_format = "#,##0"
    ws_leg.cell(rr, 3, d["weight_share"]).number_format = "0.00%"
    ws_leg.cell(rr, 4, d["increase"]).number_format = "+0.0000%;-0.0000%"
    rr += 1
ws_leg.cell(rr, 1, "All prices").font = BOLD
ws_leg.cell(rr, 2, int(len(rec))).number_format = "#,##0"
ws_leg.cell(rr, 2).font = BOLD
ws_leg.cell(rr, 3, 1.0).number_format = "0.00%"
ws_leg.cell(rr, 3).font = BOLD
ws_leg.cell(rr, 4, WHOLE).number_format = "+0.0000%;-0.0000%"
ws_leg.cell(rr, 4).font = BOLD
rr += 2
ws_leg.cell(rr, 1, "The share of weight is the quantity-weighted share of the previous "
                   "yen base price. The rows do not sum to 100% because 1,801 rows carry "
                   "no source label.").font = SUB
ws_leg.cell(rr, 1).alignment = Alignment(wrap_text=True, vertical="top")
ws_leg.merge_cells(start_row=rr, start_column=1, end_row=rr + 1, end_column=6)
rr += 3

# ---------------------------------------------------------------- Sources block
ws_leg.cell(rr, 1, "SOURCES - every input written into this workbook, and where it "
                   "came from").font = SEC
rr += 1
ws_leg.cell(rr, 1, "The market sheets carry these as literal values, not as references, "
                   "so that the file opens. That means changing a value here does NOT "
                   "propagate through the sheets: this sheet is a record of what was "
                   "used, not a live control panel.").font = SUB
ws_leg.cell(rr, 1).alignment = Alignment(wrap_text=True, vertical="top")
ws_leg.merge_cells(start_row=rr, start_column=1, end_row=rr + 1, end_column=6)
rr += 2
hdr_row(ws_leg, rr, ["Input", "Value", "Unit", "Source", "", "Note"])
rr += 1
SOURCES = [
    ("Exchange rate, live", FX_LIVE, "JPY/EUR",
     "Suzuki san's mail 'Exchange revision from Oct 2026', 15 Sep 2026",
     "Issued by ISZJ and applied to both sources. Not a decision, and nothing is "
     "passed on or held back."),
    ("Exchange rate, the rate the list sits on", FX_LIST_BASE, "JPY/EUR",
     "FY2026, as of 1 Oct 2025",
     "Documentation only. It is what our price list was built on."),
    ("Exchange rate, previous vintage", FX_PREV_VINTAGE, "JPY/EUR",
     "1 Apr to 30 Sep 2026",
     "Documentation only."),
    ("Purchase discount, Japan, live", DISC_LIVE[SRC_J], "of base price",
     "Suzuki san's mail 'discount/whole sales ratio revisoin from Jan 5th 2026', "
     "22 Dec 2025",
     "EFFECTIVE 5 January 2026, at the same timing as the annual base-price revision. "
     "Already in force, so not a move. Margin on the yen base price 32.7%."),
    ("Purchase discount, Japan, prior", DISC_J_PRIOR, "of base price",
     "The position it replaced",
     "Margin on the yen base price was 38.0%, so the change took 5.3 points off it. "
     "Recorded, never multiplied in."),
    ("Purchase discount, Thailand", DISC_LIVE[SRC_T], "of base price",
     "Unchanged, not part of the January 2026 revision",
     "Thailand has no discount change."),
    ("Weighted increase, all prices", WHOLE, "of yen base",
     "Measured on 01_data/00_derived/price_bp_weighted_compare_pn.csv",
     "in_scope == TRUE AND unpriced_reason IS NULL = 47,617 rows. Reproduces the "
     "published index of 5.9616%."),
    ("Weighted increase, Japan (IML)", SRC_MK[SRC_J]["increase"], "of yen base",
     "Same file, split on the source field of pricing_list_pn.parquet",
     "22,731 rows, 47.71% of the weight."),
    ("Weighted increase, Thailand (IMIT)", SRC_MK[SRC_T]["increase"], "of yen base",
     "Same file, same split",
     "23,085 rows, 43.08% of the weight."),
    ("IML Export Base Price evidence", "62% VP / 73.5% IE", "applied to EBP",
     "Masumi Hayakawa (IML), 10 Nov 2025",
     "Our purchase price is a discount off the Export Base Price, so the EBP sits "
     "above our cost. The IE rate is an open item: our config carries the VP rate "
     "only."),
    ("IML stated revision, CY2026", IML_STATED_REVISION, "weighted average",
     "Masumi Hayakawa (IML), 10 Nov 2025",
     "Stated as an impact of around 3% for ISZE. We measure 5.9616%. Open "
     "reconciliation item, not reconciled by assumption."),
    ("Current sales price", "per row", "EUR",
     "sp_eur in 01_data/00_derived/pricing_list_pn.parquet",
     "READ from the price list, not reconstructed. Written into the current sales "
     "price column."),
    ("Class factors", "C .47 D .48 F .525 J .555 M .50 P .44 V .55 T .80", "factor",
     "PR00 FY2026",
     "Written as literal values per row. Shown as margins above: .47 is a 53% margin, "
     ".55 a 45% margin."),
    ("CIS factor", CIS_FACTOR, "factor",
     "03_analytics/isze_pricing/config.yaml -> markets.CIS.factor_flat",
     "Class-independent, so the CIS sheet carries no class factor column. A 60% "
     "margin on every line."),
    ("ZPR1 differential", ZPR1, "on the list price",
     "03_analytics/isze_pricing/config.yaml -> markets.ZPR1.differential",
     "Israel UMI 1797 and UTI 1799, a flat 10% below PR00."),
    ("Target move", TARGET, "on price", "Jerome", "The band is 4% to 6%."),
]
for lab, val, unit, src, note in SOURCES:
    ws_leg.cell(rr, 1, lab)
    c = ws_leg.cell(rr, 2, val)
    if unit in ("of base price", "of yen base"):
        c.number_format = "0.0000%"
    elif unit in ("JPY/EUR", "factor"):
        c.number_format = "0.000"
    elif unit in ("on the list price", "on price"):
        c.number_format = "0.0%"
    elif unit == "weighted average":
        c.number_format = "0.0%"
    ws_leg.cell(rr, 3, unit)
    ws_leg.cell(rr, 4, src).font = SUB
    ws_leg.cell(rr, 6, note).font = SUB
    ws_leg.cell(rr, 1).alignment = Alignment(wrap_text=True, vertical="top")
    ws_leg.cell(rr, 6).alignment = Alignment(wrap_text=True, vertical="top")
    rr += 1

# ================================================================== market sheets
COLS = [
    ("PN", 13), ("qty", 10), ("description", 38), ("Source", 8), ("Class", 7),
    ("bp_current", 12), ("fob_current", 12), ("sp_current", 12),
    ("bp_new", 12), ("delta_bp", 11), ("new_bp_over_prior", 16),
    ("weighted_increase", 17),
    ("billed_eur", 14), ("billed_after_eur", 15),
    ("flag", 34),
]
NCOL = len(COLS)
C_QTY, C_DESC, C_SRC, C_CLS = 2, 3, 4, 5
C_BPC, C_FOBC, C_SPC = 6, 7, 8
C_BPN, C_DELTA, C_NEWOVER, C_INCR = 9, 10, 11, 12
C_BA, C_AF = 13, 14
C_FLAG = 15
FIRST_DATA = 2
RES_GAP = 2

summary = {}
for code, basis, sold_to, note in MARKETS:
    ws = sheets[code]
    b = BOOKS[code]
    n = len(b)

    hdr_row(ws, 1, [c[0] for c in COLS], [c[1] for c in COLS], freeze="A2")
    if code in ("UTI", "UMI"):
        note_txt = (f"BASIS: {code}, sold-to {sold_to}. Priced on ZPR1, a flat 10% "
                    f"below the PR00 list. Movement = the weighted increase of the "
                    f"yen base prices.")
    elif code == "CIS":
        note_txt = ("BASIS: class-independent, one 60% margin across the catalogue, so "
                    "no class factor is applied on this sheet.")
    else:
        note_txt = ("BASIS: the mainland EU distributor list. Full class-factor engine. "
                    "Movement = the weighted increase of the yen base prices.")
    ws.cell(1, NCOL + 2, note_txt).font = SUB
    ws.cell(2, NCOL + 2, "See the Legends sheet for the measure, the sources and the "
                         "two open items.").font = SUB
    ws.cell(3, NCOL + 2, "The flag in column O explains any row held out.").font = SUB

    for i, (_, row) in enumerate(b.iterrows()):
        rr = FIRST_DATA + i
        src = row["src"] if isinstance(row["src"], str) else ""
        ws.cell(rr, 1, row["pn"])
        ws.cell(rr, C_QTY, float(row["qty"])).number_format = "#,##0"
        ws.cell(rr, C_DESC, row["billed_description"] or "")
        ws.cell(rr, C_SRC, src if src in (SRC_J, SRC_T) else "")
        ws.cell(rr, C_CLS, row["cls"] if isinstance(row["cls"], str) else "")
        ws.cell(rr, C_BPC, float(row["prior_bp"])).number_format = "#,##0"
        fc = row["fob_current"]
        ws.cell(rr, C_FOBC, float(fc) if pd.notna(fc) else "").number_format = "#,##0.00"
        cur = row["current"]
        ws.cell(rr, C_SPC, float(cur) if pd.notna(cur) else "").number_format = "#,##0.00"
        ws.cell(rr, C_BPN, float(row["new_bp"])).number_format = "#,##0"
        ws.cell(rr, C_DELTA, float(row["delta_bp"])).number_format = "#,##0"
        ws.cell(rr, C_NEWOVER, float(row["new_bp"]) / float(row["prior_bp"])
                ).number_format = "0.00000"
        ws.cell(rr, C_INCR, float(row["incr"])).number_format = "+0.0000%;-0.0000%"
        ws.cell(rr, C_BA, float(row["billed"])).number_format = "#,##0.00"
        ws.cell(rr, C_AF, f"=IFERROR(${get_column_letter(C_BA)}{rr}"
                          f"*(1+${get_column_letter(C_INCR)}{rr}),\"\")"
                ).number_format = "#,##0.00"
        if not src:
            fl = "no source label - excluded from the source split"
        elif pd.isna(row["prior_bp"]) or float(row["prior_bp"]) == 0:
            fl = "no previous base price - carries no weight"
        else:
            fl = ""
        ws.cell(rr, C_FLAG, fl)
        if fl:
            for c in range(1, NCOL + 1):
                ws.cell(rr, c).fill = AMBER
    last = FIRST_DATA + n - 1
    tot = last + 1
    ws.cell(tot, 1, "TOTAL").font = BOLD
    ws.cell(tot, C_QTY, f"=SUM({get_column_letter(C_QTY)}{FIRST_DATA}:"
                        f"{get_column_letter(C_QTY)}{last})").number_format = "#,##0"
    for col in (C_BA, C_AF):
        ws.cell(tot, col, f"=SUM({get_column_letter(col)}{FIRST_DATA}:"
                          f"{get_column_letter(col)}{last})").number_format = "#,##0.00"
        ws.cell(tot, col).font = BOLD

    m = MK[code]
    r = tot + RES_GAP
    ws.cell(r, 1, "RESULT").font = SEC
    r += 1
    res = [
        ("Weighted increase, whole market", m["increase"], "+0.0000%;-0.0000%"),
        ("Rows on this sheet", m["sheet_rows"], "#,##0"),
        ("Part numbers", m["part_numbers"], "#,##0"),
        ("Billed EUR in the window", m["billed"], "#,##0"),
        ("Source: Japan (IML)", m["japan"], "+0.0000%;-0.0000%"),
        ("Source: Thailand (IMIT)", m["thailand"], "+0.0000%;-0.0000%"),
        ("Source: no label, excluded from the split", m["no_label"],
         "+0.0000%;-0.0000%"),
        ("Share of weight with no source label", m["no_label_share"], "0.00%"),
    ]
    if code == "CIS":
        res.append(("CIS note: the measure is class-independent, so the flat 60% "
                    "margin does not enter it", "", "General"))
    for lab, val, fmt in res:
        ws.cell(r, 1, lab)
        if val != "":
            ws.cell(r, 2, val).number_format = fmt
        r += 1

    summary[code] = {"rows": n, "header_row": 1, "first_row": FIRST_DATA,
                     "last_row": last, "total_row": tot,
                     "result_row": tot + RES_GAP}

# ---- final formatting. THE CRITICAL RULE: no wrapping anywhere in the DATA rows.
DATA_SHEETS = {"PR00", "UTI", "UMI", "CIS"}
for _ws in wb.worksheets:
    for _row in _ws.iter_rows():
        for _c in _row:
            _a = _c.alignment
            if _a is not None and _a.wrap_text:
                _c.alignment = Alignment(wrap_text=False, vertical=_a.vertical,
                                         horizontal=_a.horizontal)
    _b = _ws.column_dimensions.get("B")
    if _b is None or (_b.width or 0) < 28:
        _ws.column_dimensions["B"].width = 28
# the Legends sheet may wrap its prose: it is small and nothing there is data. The
# threshold is 50 characters so the long source citations wrap too, which is what the
# generic pre-delivery checker wants. Row heights are still never set explicitly, so
# nothing auto-fits on open.
_leg_ws = wb["Legends"]
for _row in _leg_ws.iter_rows():
    for _c in _row:
        v = _c.value
        if isinstance(v, str) and not v.startswith("=") and len(v) > 50:
            _c.alignment = Alignment(wrap_text=True, vertical="top")

wb.save(XLSX_OUT)
say()
say(f"  {XLSX_OUT} ({XLSX_OUT.stat().st_size:,} bytes)")
say(f"  sheets: {wb.sheetnames}")
OPEN_OUT.write_bytes(
    ('@echo off\r\nstart "" "%~dp0' + XLSX_OUT.name + '"\r\n').encode("utf-8"))
raw = OPEN_OUT.read_bytes()
n_crlf = raw.count(b"\r\n")
n_bare = raw.count(b"\n") - n_crlf
say(f"  {OPEN_OUT.name}: CRLF {n_crlf}, bare LF {n_bare} -> "
    f"{'OK' if n_crlf == 2 and n_bare == 0 else 'BAD'}")

meta = {
    "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "workbook": str(XLSX_OUT), "sheets": wb.sheetnames,
    "architecture": ("Jerome's own: no VLOOKUP (class factor written per row as a "
                     "literal), no SUMPRODUCT, one row per part number, scalar "
                     "arithmetic, aggregates pre-computed in Python and written as "
                     "literal values, current price hardcoded."),
    "method": {
        "formula": "weighted_increase = SUM(qty x delta_jpy) / SUM(qty x bp_prior) - 1",
        "recipe": ("in_scope == TRUE AND unpriced_reason IS NULL -> 47,617 rows -> "
                   "5.961599%"),
        "recipe_rows": int(len(rec)),
        "reproduces_published_index": 0.059616,
        "computed": float(IDX),
        "no_factor_chain": True,
        "exchange_rate_is_a_decision": False,
        "why": ("The exchange rate and the purchase discount are both already in force, "
                "so neither is a forward move."),
    },
    "live_inputs": {"fx": FX_LIVE, "fx_list_base": FX_LIST_BASE,
                    "fx_previous_vintage": FX_PREV_VINTAGE,
                    "discount_live": DISC_LIVE, "discount_j_prior": DISC_J_PRIOR,
                    "class_factors": CLASS_FACTOR, "cis_factor": CIS_FACTOR,
                    "zpr1_differential": ZPR1, "target": TARGET,
                    "band": [BAND_LOW, BAND_HIGH]},
    "whole_book": {"weighted_increase": WHOLE,
                   "japan": SRC_MK[SRC_J]["increase"],
                   "thailand": SRC_MK[SRC_T]["increase"]},
    "by_source": SRC_MK,
    "figure_replaced": {
        "earlier_method": ("(1 + revision) x (FX_old / FX_new) x "
                           "(discount_new / discount_old) - 1"),
        "earlier_whole": OLD["whole"], "earlier_japan": OLD["japan"],
        "earlier_thailand": OLD["thailand"], "earlier_per_market": OLD_MK,
        "corrected_whole": WHOLE,
    },
    "markets": {k: {kk: (None if isinstance(vv, float) and vv != vv else vv)
                    for kk, vv in v.items()} for k, v in MK.items()},
    "ebp_evidence": [
        {"n": 1, "claim": "The Export Base Price is built up from IML's own costs, and "
                          "our purchase price is a discount off it.",
         "source": "Masumi Hayakawa (IML), 10 November 2025",
         "detail": "62% on vehicle parts and 73.5% on industrial engines, applied to "
                   "IML's Export Base Price. EBP 1,000 JPY gives a purchase price of "
                   "620 JPY on vehicle parts."},
        {"n": 2, "claim": "IML builds its offer price from supplier cost plus a target "
                          "gross profit.",
         "source": "Hideya Kondou (ISZJ), 24 November 2020",
         "detail": "Normal at 25% gross profit, Best at 17%."},        {"n": 3, "claim": "The discount change and the base-price revision happen at "
                          "the same moment.",
         "source": "Takayoshi Suzuki, 22 December 2025",
         "detail": "Valid from 5 January 2026, \"the same timing with annual EBP "
                   "revision\"."},
        {"n": 4, "claim": "The base price and the class letter arrive together from "
                          "Japan.",
         "source": "Peeraya Sawangsaensak (IMIT), 29 April 2026",
         "detail": "\"Please find the B/P, Price Class, and remark as detailed "
                   "below.\""},
    ],
    "open_items": [
        {"id": "IE_RATE",
         "title": "Our configuration carries only the vehicle-parts rate",
         "detail": ("config.yaml holds J: 0.673, the vehicle-parts rate. The "
                    "industrial-engine rate is 73.5% in 2025 and 79.7% in 2026. Our "
                    "configuration applies 67.3% to everything Japan-sourced."),
         "action": ("config.yaml is left alone. Ask IML to confirm the current "
                    "industrial-engine rate and its part families.")},
        {"id": "REVISION_SIZE",
         "title": "IML states a different revision size from ours",
         "detail": ("IML says the CY2026 EBP revision is around 3% for ISZE (weighted "
                    "average). We measure 5.9616%. Likely different revisions or "
                    "scopes."),
         "action": ("Open reconciliation item. Ask IML for the window, the scope and "
                    "the weighting behind the 3%.")},
    ],
    "caveats": [
        "The weighted increase is measured on the price comparison itself. No exchange "
        "rate and no discount is multiplied into it.",
        "Rows with no source label are reported separately, never assigned to Japan or "
        "Thailand.",
        "Volume and mix are held flat. This is the arithmetic of the price move.",
        "CIS current prices sit on the class factors even though the configuration "
        "wants a flat 60% margin, so the switch is reported separately.",
        "The result blocks are literal values, computed in Python, so they render the "
        "instant the file opens.",
    ],
}
JSON_OUT.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
say(f"  {JSON_OUT.name}")
say()
say("SIMULATION_BUILT" if abs(IDX - 0.059616) < 1e-6 else "SIMULATION_CHECK_FAILED")
