"""Build the Excellence Partner ROI model (Excel, live formulas).

Reads derived files only:
  _build/order_mix_fy2026.csv                      FY2026 billed + stock orders (SOR) per distributor
  01_data/00_derived/wallet_waterfall.csv          modelled uncaptured wallet 2025 (ceiling, not a forecast)
  09_meetings/.../ANALYSE ... (cost basis)         discount levels, scope (CIS out)

Output: Excellence_Partner_ROI_Model_2026-10-09.xlsx
Run from the ISZE root:  python 09_meetings/Excellence_Partner_Program_2026/_build/build_roi_model.py
then recalculate with the xlsx skill's recalc.py.
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOT = HERE.parents[2]
OUT = PACK / "Excellence_Partner_ROI_Model_2026-10-09.xlsx"

F = "Arial"
BLUE = Font(name=F, size=10, color="0000FF")
BLACK = Font(name=F, size=10)
GREEN = Font(name=F, size=10, color="008000")
BOLD = Font(name=F, size=10, bold=True)
TITLE = Font(name=F, size=14, bold=True)
HDR = Font(name=F, size=10, bold=True, color="FFFFFF")
HFILL = PatternFill("solid", start_color="24282C")
YELLOW = PatternFill("solid", start_color="FFFF00")
GREY = PatternFill("solid", start_color="F2F2F2")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
EUR = '€#,##0;(€#,##0);-'
PCT = '0.0%;(0.0%);-'
PCT2 = '0.00%;(0.00%);-'
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()


def hdr(ws, row, labels, col=1):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=t)
        c.font, c.fill, c.border = HDR, HFILL, BOX
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")


def put(ws, ref, value, font=BLACK, fmt=None, fill=None, note=None, wrap=False):
    c = ws[ref]
    c.value = value
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if note:
        c.comment = Comment(note, "Claude")
    if wrap:
        c.alignment = WRAP
    return c


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


# ------------------------------------------------------------------ data
o = pd.read_csv(HERE / "order_mix_fy2026.csv", index_col=0)
w = pd.read_csv(ROOT / "01_data/00_derived/wallet_waterfall.csv")
w25 = w[w.year == 2025].set_index("distributor_code").uncaptured_eur

# Rebate credit lines ("Rebate Material") booked FY2026 (1 Apr 2025 - 31 Mar 2026), per distributor.
_sf = pd.read_parquet(ROOT / "01_data/00_derived/sales_fact.parquet")
_sf["billing_date"] = pd.to_datetime(_sf["billing_date"])
_dim = pd.read_csv(ROOT / "01_data/00_derived/distributor_dimension.csv")
_map = dict(zip(_dim.sold_to_sap, _dim.distributor_code.fillna(_dim.network_role)))
_rb = _sf[(_sf.part_number.astype(str).str.upper() == "REBATE")
          & (_sf.billing_date >= "2025-04-01") & (_sf.billing_date < "2026-04-01")]
REBATE = _rb.assign(db=_rb.sold_to_sap.map(_map)).groupby("db").net_sales_value.sum().abs().round(0).to_dict()

LABEL = {
    "ITUK": "Isuzu Truck UK", "IUK": "Isuzu UK pickup", "UTI": "UTI (Israel trucks)", "UMI": "UMI (Israel light commercial)",
    "GERMANY": "Germany", "BELGIUM": "Benelux", "PORTUGAL": "Portugal", "NORWAY": "Norway", "SWEDEN": "Sweden",
    "IRELAND": "Ireland", "GREECE": "Greece", "CYPRUS": "Cyprus", "HUNGARY": "Hungary", "FINLAND": "Finland",
    "MALTA": "Malta", "ROMANIA": "Romania", "DENMARK": "Denmark", "ICELAND": "Iceland", "PALESTINE": "Palestine",
}
ORDER = list(LABEL)
KICK = {"IUK", "UTI", "UMI", "GERMANY", "BELGIUM", "PORTUGAL", "SWEDEN", "NORWAY", "IRELAND"}
STD_TODAY = {
    "ITUK": "Per dealer, 2025 only", "IUK": "Network total", "IRELAND": "Network total", "UTI": "Network total",
    "PORTUGAL": "Network total", "GREECE": "Network total", "ROMANIA": "Network total (2026)",
}
# Illustrative participation plan: 0 = not in, 1 = level 1 (-2.5%), 2 = level 2 (-5%).
Y1 = {"ITUK", "IUK", "UTI", "IRELAND", "PORTUGAL", "GREECE", "ROMANIA"}
Y2_L2 = {"ITUK", "IUK", "PORTUGAL"}
Y2 = Y1 | {"GERMANY", "BELGIUM", "SWEDEN", "NORWAY", "UMI", "HUNGARY"}
Y3_L2 = Y2_L2 | {"IRELAND", "UTI", "GERMANY"}


def lvl(code, inset, l2set):
    return 0 if code not in inset else (2 if code in l2set else 1)


# ------------------------------------------------------------------ Inputs
wi = wb.active
wi.title = "Inputs"
put(wi, "A1", "Inputs — change blue cells; yellow cells still need a real number", TITLE)
hdr(wi, 3, ["Lever", "Value", "Unit / source / note"])
rows = [
    (4, "Discount, level 1 (stock orders)", 0.025, PCT, "Proposal in the deck: 2.5% on stock orders (SaTy SOR)", None),
    (5, "Discount, level 2 (stock orders)", 0.05, PCT, "Proposal in the deck: 5% on stock orders", None),
    (6, "Gross margin on billed parts", 0.468, PCT,
     "INDICATIVE. SAP cost vs billed, Q1 FY2027 (Apr–Jun 2026), 01_data/00_derived/q1fy2027_export_with_saty.csv. One quarter; SAP cost not complete for every line.", None),
    (7, "Programme running cost per year, extra cash (€)", 0, EUR,
     "Jerome 9 Oct 2026: no running cost. Built and run by Jerome, Bart Symons and AI. Internal time is NOT costed; management may ask.", None),
    (8, "One-off build cost in year 1, extra cash (€)", 0, EUR,
     "Same: built in-house with AI. Change if an external developer, licences or hosting are needed.", None),
    (9, "Other benefits per year at full ramp (€)", 0, EUR,
     "Left at zero on purpose. Air-freight saving from rush orders moving to stock orders is excluded (Jerome 9 Oct 2026: look at stock orders only); it stays an unpriced upside.", None),
    (10, "Price-revision value per year (€)", 682000, EUR,
     "Midpoint of +5% option: €638k (forecast weights) to €726k (last-12-months). DECISION_MEMO_PRICE_ADJUSTMENT_20260916 via Universe term sheet §2.", None),
    (11, "In-scope billed FY2026 (€)", "=Distributors!C24", EUR, "Link. 19 distributors, CIS markets excluded.", None),
    (12, "Growth of participants vs FY2026 baseline, as planned", 0.05, PCT,
     "Reviewed FY2027 business plan €34.9M (excl. MIDI/IMG) vs €33.2M billed FY2026 = about +5%. Used for the growth-based designs.", None),
    (13, "Hybrid design: flat discount level 1", 0.01, PCT, "Design choice, not a proposal yet.", None),
    (14, "Hybrid design: flat discount level 2", 0.02, PCT, "Design choice, not a proposal yet.", None),
    (15, "Hybrid design: growth bonus level 1 (on stock orders above FY2026)", 0.05, PCT, "Design choice, not a proposal yet.", None),
    (16, "Hybrid design: growth bonus level 2 (on stock orders above FY2026)", 0.10, PCT, "Design choice, not a proposal yet.", None),
]
for r, lab, val, fmt, note, fill in rows:
    put(wi, f"A{r}", lab)
    is_formula = isinstance(val, str) and val.startswith("=")
    put(wi, f"B{r}", val, GREEN if is_formula else BLUE, fmt, fill)
    put(wi, f"C{r}", note, BLACK, wrap=True)
hdr(wi, 17, ["Ramp-up of benefits", "Share of full effect", "Why"])
for r, lab, v, n in [(18, "Year 1 = FY2028 (Apr 2027 – Mar 2028)", 0.25, "Data and tools need time; first discount only after a clean first quarter."),
                     (19, "Year 2 = FY2029", 0.6, "Assumption."), (20, "Year 3 = FY2030", 1.0, "Assumption.")]:
    put(wi, f"A{r}", lab)
    put(wi, f"B{r}", v, BLUE, PCT)
    put(wi, f"C{r}", n, wrap=True)
hdr(wi, 22, ["Benefit scenario", "Extra sales vs plan, % of participants' billed", "Share of price-revision value that better data explains", "Note"])
scen = [("Low", 0.005, 0.0, "Data arrives, hardly changes decisions."),
        ("Base", 0.015, 0.05, "ASSUMPTION. No measured uplift exists anywhere in the workspace; see Evidence."),
        ("High", 0.03, 0.10, "Optimistic, still inside normal yearly movement of a distributor (Evidence).")]
for i, (nme, u, p, n) in enumerate(scen):
    r = 23 + i
    put(wi, f"A{r}", nme, BOLD)
    put(wi, f"B{r}", u, BLUE, PCT, YELLOW)
    put(wi, f"C{r}", p, BLUE, PCT, YELLOW)
    put(wi, f"D{r}", n, wrap=True)
hdr(wi, 29, ["Design choices", "Value", "Rate on stock orders", "Note"])
put(wi, "A30", "Design shown on Plan_ROI (1 deck flat · 2 growth only · 3 hybrid · 4 tiered)")
put(wi, "B30", 3, BLUE, "0", YELLOW)
put(wi, "A31", "Spread of yearly stock-order growth between distributors (σ)")
put(wi, "B31", 0.138, BLUE, PCT)
put(wi, "D31", "Observed FY2026 vs FY2025 spread of billing growth, 12 larger distributors (Evidence sheet). Luck decides much of a tier.", wrap=True)
put(wi, "A32", "Tiered design 4: rate on ALL stock orders, by the distributor's own growth in stock orders", BOLD)
for r, lab, thr, rate in [(33, "Tier 1: growth below", 0.0, 0.01), (34, "Tier 2: growth below", 0.05, 0.02),
                          (35, "Tier 3: growth below", 0.10, 0.035)]:
    put(wi, f"A{r}", lab)
    put(wi, f"B{r}", thr, BLUE, PCT)
    put(wi, f"C{r}", rate, BLUE, PCT)
put(wi, "A36", "Tier 4: growth above the tier-3 limit")
put(wi, "C36", 0.05, BLUE, PCT)
put(wi, "A37", "Expected rate on stock orders if growth is as planned, with the spread above", BOLD)
mu, sg = "$B$12", "$B$31"
put(wi, "B37", f"=C33*NORMDIST(B33,{mu},{sg},TRUE)+C34*(NORMDIST(B34,{mu},{sg},TRUE)-NORMDIST(B33,{mu},{sg},TRUE))"
    f"+C35*(NORMDIST(B35,{mu},{sg},TRUE)-NORMDIST(B34,{mu},{sg},TRUE))+C36*(1-NORMDIST(B35,{mu},{sg},TRUE))", BLACK, PCT2)
put(wi, "D33", "Tier limits and rates are design choices to test in the pilot, not proposals.", wrap=True)
put(wi, "A27", "Colour code: blue = typed input · black = formula · green = link to another sheet · yellow = key assumption or missing number.", BLACK)
widths(wi, {"A": 58, "B": 22, "C": 60, "D": 50})
for r in range(4, 17):
    wi.row_dimensions[r].height = 30
wi.row_dimensions[31].height = 30
wi.row_dimensions[22].height = 45

# ------------------------------------------------------------------ Distributors
wd = wb.create_sheet("Distributors")
put(wd, "A1", "Distributors in scope (19, CIS excluded) and the illustrative participation plan", TITLE)
put(wd, "A2", "Levels: 0 = not in · 1 = level 1 (-2.5%) · 2 = level 2 (-5%). Years: FY2028, FY2029, FY2030. Plan is illustrative; edit the blue level cells.", BLACK)
hdr(wd, 4, ["Code", "Distributor", "Billed FY2026 (€)", "Stock orders FY2026 (€)", "Stock-order share", "Kickback today",
            "Sales to dealer today", "Uncaptured wallet 2025 (€, modelled ceiling)", "Level Y1", "Level Y2", "Level Y3",
            "Billed of participants Y1 (€)", "Y2 (€)", "Y3 (€)", "Discount cost Y1 (€)", "Y2 (€)", "Y3 (€)",
            "Rebate credits booked FY2026 (€)", "Rebate as % of billed"])
for i, code in enumerate(ORDER):
    r = 5 + i
    put(wd, f"A{r}", code, BLUE)
    put(wd, f"B{r}", LABEL[code], BLUE)
    put(wd, f"C{r}", int(o.loc[code, "fy2026_billed_eur"]), BLUE, EUR)
    put(wd, f"D{r}", int(o.loc[code, "SOR_eur"]), BLUE, EUR)
    put(wd, f"E{r}", f"=IFERROR(D{r}/C{r},0)", BLACK, PCT)
    put(wd, f"F{r}", "yes" if code in KICK else "no", BLUE)
    put(wd, f"G{r}", STD_TODAY.get(code, "nothing on file"), BLUE)
    put(wd, f"H{r}", int(w25.get(code, 0)), BLUE, EUR)
    put(wd, f"I{r}", lvl(code, Y1, set()), BLUE, "0", YELLOW)
    put(wd, f"J{r}", lvl(code, Y2, Y2_L2), BLUE, "0", YELLOW)
    put(wd, f"K{r}", 1, BLUE, "0", YELLOW)
    if code in Y3_L2:
        wd[f"K{r}"].value = 2
    for col, lv in zip("LMN", "IJK"):
        put(wd, f"{col}{r}", f"=IF({lv}{r}>0,C{r},0)", BLACK, EUR)
    for col, lv in zip("OPQ", "IJK"):
        put(wd, f"{col}{r}", f"=D{r}*IF({lv}{r}=1,Inputs!$B$4,IF({lv}{r}=2,Inputs!$B$5,0))", BLACK, EUR)
    put(wd, f"R{r}", int(REBATE.get(code, 0)), BLUE, EUR)
    put(wd, f"S{r}", f"=IFERROR(R{r}/C{r},0)", BLACK, PCT)
put(wd, "A24", "Total", BOLD)
put(wd, "S24", "=IFERROR(R24/C24,0)", BOLD, PCT)
for col in "CDHLMNOPQR":
    put(wd, f"{col}24", f"=SUM({col}5:{col}23)", BOLD, EUR)
put(wd, "E24", "=IFERROR(D24/C24,0)", BOLD, PCT)
put(wd, "A26", "Sources: billed and stock orders = sales_fact.parquet, FY2026 (1 Apr 2025 – 31 Mar 2026), credit notes, transport and rebates excluded, via _build/order_mix_and_discount_cost.py. "
    "Uncaptured wallet = wallet_waterfall.csv, 2025 — a ceiling built on target spend per truck, NOT recoverable sales (FACTS.md). Kickback list = 01_data/91_build/build_gps_kickback_proposal.py. "
    "Sales to dealer today = register in 01_data/DATA_MANIFEST.md §05. Rebate credits = billing lines 'Rebate Material', FY2026, sales_fact.parquet: kickback and other incentives mixed (ITUK includes the €30k defence-programme credit). The workbook with the incentive sheet (budget_per_DB_reviewed_24042026.xlsx) is not in the workspace.", BLACK, wrap=True)
wd.merge_cells("A26:S26")
wd.row_dimensions[26].height = 55
widths(wd, {"A": 12, "B": 28, "C": 16, "D": 16, "E": 11, "F": 10, "G": 22, "H": 20, "I": 8, "J": 8, "K": 8,
            "L": 16, "M": 14, "N": 14, "O": 16, "P": 14, "Q": 14, "R": 18, "S": 12})
wd.row_dimensions[4].height = 58
wd.freeze_panes = "C5"

# ------------------------------------------------------------------ Plan ROI
wp = wb.create_sheet("Plan_ROI")
put(wp, "A1", "Plan: cost, benefit and net result per year for the design chosen on Inputs B30", TITLE)
hdr(wp, 3, ["", "Year 1 FY2028", "Year 2 FY2029", "Year 3 FY2030", "3-year total"])
cols = ["B", "C", "D"]
dist_bill = dict(zip(cols, "LMN"))
dist_cost = dict(zip(cols, "OPQ"))
lvl_col = dict(zip(cols, "IJK"))
ramp_row = dict(zip(cols, (18, 19, 20)))

labels = {4: "Participating distributors", 5: "Billed of participants, FY2026 base (€)", 6: "Discount cost, chosen design (€)",
          7: "Programme running cost (€)", 8: "One-off build cost (€)", 9: "Total cost (€)",
          10: "Discount cost as % of participants' billed", 11: "Margin on an extra € billed, after the discount", 12: "Ramp-up"}
for r, t in labels.items():
    put(wp, f"A{r}", t, BOLD if r == 9 else BLACK)
for c in cols:
    put(wp, f"{c}4", f'=COUNTIF(Distributors!{lvl_col[c]}5:{lvl_col[c]}23,">0")', GREEN, "0")
    put(wp, f"{c}5", f"=Distributors!{dist_bill[c]}24", GREEN, EUR)
    put(wp, f"{c}6", f"=INDEX(Design_variants!{c}$10:{c}$13,Inputs!$B$30)", GREEN, EUR)
    put(wp, f"{c}7", "=Inputs!$B$7", GREEN, EUR)
    put(wp, f"{c}8", "=Inputs!$B$8" if c == "B" else 0, GREEN if c == "B" else BLACK, EUR)
    put(wp, f"{c}9", f"=SUM({c}6:{c}8)", BOLD, EUR)
    put(wp, f"{c}10", f"=IFERROR({c}6/{c}5,0)", BLACK, PCT2)
    put(wp, f"{c}11", f"=Inputs!$B$6-{c}10", BLACK, PCT)
    put(wp, f"{c}12", f"=Inputs!$B${ramp_row[c]}", GREEN, PCT)
for r in (6, 7, 8, 9):
    put(wp, f"E{r}", f"=SUM(B{r}:D{r})", BOLD if r == 9 else BLACK, EUR)

blocks = {}
start = 14
for k, nme in enumerate(["Low", "Base", "High"]):
    r0 = start + k * 8
    blocks[nme] = r0
    put(wp, f"A{r0}", f"Scenario {nme}", BOLD, fill=GREY)
    for c in "BCDE":
        wp[f"{c}{r0}"].fill = GREY
    names = ["Extra sales vs plan (€)", "Margin on extra sales, after discount (€)", "Price-decision benefit (€)",
             "Other benefits (€)", "Total benefit (€)", "Net result (€)"]
    for j, t in enumerate(names):
        put(wp, f"A{r0 + 1 + j}", t, BOLD if j >= 4 else BLACK)
    srow = 23 + k
    for c in cols:
        put(wp, f"{c}{r0+1}", f"=Inputs!$B${srow}*{c}$12*{c}$5", BLACK, EUR)
        put(wp, f"{c}{r0+2}", f"={c}{r0+1}*{c}$11", BLACK, EUR)
        put(wp, f"{c}{r0+3}", f"=Inputs!$C${srow}*Inputs!$B$10*{c}$12*IFERROR({c}$5/Inputs!$B$11,0)", BLACK, EUR)
        put(wp, f"{c}{r0+4}", f"=Inputs!$B$9*{c}$12", BLACK, EUR)
        put(wp, f"{c}{r0+5}", f"=SUM({c}{r0+2}:{c}{r0+4})", BOLD, EUR)
        put(wp, f"{c}{r0+6}", f"={c}{r0+5}-{c}$9", BOLD, EUR)
    for j in range(1, 7):
        put(wp, f"E{r0+j}", f"=SUM(B{r0+j}:D{r0+j})", BOLD if j >= 5 else BLACK, EUR)
    put(wp, f"A{r0+7}", "Return on cost over 3 years (net ÷ cost)", BLACK)
    put(wp, f"E{r0+7}", f"=IFERROR(E{r0+6}/E$9,0)", BOLD, PCT)

be = 40
put(wp, f"A{be}", "Break-even", BOLD, fill=GREY)
for c in "BCDE":
    wp[f"{c}{be}"].fill = GREY
put(wp, f"A{be+1}", "Extra sales needed to cover the year's cost, if extra sales were the only benefit (€)")
put(wp, f"A{be+2}", "… as % of participants' billed")
put(wp, f"A{be+3}", "… as % of participants' modelled uncaptured wallet (ceiling)")
for c in cols:
    put(wp, f"{c}{be+1}", f"=IFERROR({c}9/{c}11,0)", BLACK, EUR)
    put(wp, f"{c}{be+2}", f"=IFERROR({c}{be+1}/{c}5,0)", BOLD, PCT)
    put(wp, f"{c}{be+3}", f"=IFERROR({c}{be+1}/SUMPRODUCT(Distributors!$H$5:$H$23*(Distributors!{lvl_col[c]}$5:{lvl_col[c]}$23>0)),0)", BLACK, PCT)
put(wp, f"A{be+5}", "Reading: extra sales must come on top of the plan (about +5% already) and must be caused by the programme. The break-even ignores ramp-up and the price-decision channel on purpose.", BLACK, wrap=True)
wp.merge_cells(f"A{be+5}:E{be+5}")
wp.row_dimensions[be + 5].height = 40
widths(wp, {"A": 70, "B": 17, "C": 17, "D": 17, "E": 17})

# ------------------------------------------------------------------ Variants
wv = wb.create_sheet("Design_variants")
put(wv, "A1", "Four ways to pay for the same participants — cost, result and break-even", TITLE)
hdr(wv, 3, ["Per year", "Year 1 FY2028", "Year 2 FY2029", "Year 3 FY2030", "3-year total"])
put(wv, "A4", "Billed of participants, FY2026 base (€)")
put(wv, "A5", "Stock orders of level-1 participants (€)")
put(wv, "A6", "Stock orders of level-2 participants (€)")
put(wv, "A7", "Stock orders of all participants (€)")
put(wv, "A8", "Ramp-up of benefits")
for c, bc, lc in zip("BCD", "LMN", "IJK"):
    put(wv, f"{c}4", f"=Distributors!{bc}24", GREEN, EUR)
    put(wv, f"{c}5", f"=SUMPRODUCT(Distributors!$D$5:$D$23*(Distributors!{lc}$5:{lc}$23=1))", GREEN, EUR)
    put(wv, f"{c}6", f"=SUMPRODUCT(Distributors!$D$5:$D$23*(Distributors!{lc}$5:{lc}$23=2))", GREEN, EUR)
    put(wv, f"{c}7", f"={c}5+{c}6", BLACK, EUR)
put(wv, "B8", "=Inputs!$B$18", GREEN, PCT)
put(wv, "C8", "=Inputs!$B$19", GREEN, PCT)
put(wv, "D8", "=Inputs!$B$20", GREEN, PCT)
hdr(wv, 9, ["Discount cost per year (€)", "Year 1", "Year 2", "Year 3", "3-year total"])
names = ["1  Deck: flat on all stock orders", "2  Growth only: on stock orders above FY2026",
         "3  Hybrid: small flat + bonus on growth", "4  Tiered: rate on all stock orders by own growth"]
for k, nme in enumerate(names):
    put(wv, f"A{10+k}", nme)
for c in "BCD":
    put(wv, f"{c}10", f"={c}5*Inputs!$B$4+{c}6*Inputs!$B$5", BLACK, EUR)
    put(wv, f"{c}11", f"=({c}5*Inputs!$B$4+{c}6*Inputs!$B$5)*Inputs!$B$12", BLACK, EUR)
    put(wv, f"{c}12", f"={c}5*Inputs!$B$13+{c}6*Inputs!$B$14+({c}5*Inputs!$B$15+{c}6*Inputs!$B$16)*Inputs!$B$12", BLACK, EUR)
    put(wv, f"{c}13", f"={c}7*Inputs!$B$37", BLACK, EUR)
for r in range(10, 14):
    put(wv, f"E{r}", f"=SUM(B{r}:D{r})", BOLD, EUR)
hdr(wv, 15, ["Total cost per year, incl. running and build (€)", "Year 1", "Year 2", "Year 3", "3-year total"])
for k, nme in enumerate(names):
    r = 16 + k
    put(wv, f"A{r}", nme)
    put(wv, f"B{r}", f"=B{10+k}+Inputs!$B$7+Inputs!$B$8", BLACK, EUR)
    put(wv, f"C{r}", f"=C{10+k}+Inputs!$B$7", BLACK, EUR)
    put(wv, f"D{r}", f"=D{10+k}+Inputs!$B$7", BLACK, EUR)
    put(wv, f"E{r}", f"=SUM(B{r}:D{r})", BOLD, EUR)
hdr(wv, 21, ["Result by design, 3 years (€)", "3-year cost", "Net, Low", "Net, Base", "Net, High", "Break-even extra sales, year 3 (% of billed)", "Reward for a participant whose stock orders stay flat"])
flat = ["Full discount (-2.5% / -5%)", "None", "Small flat part only", "Tier 1 rate only"]
for k, nme in enumerate(names):
    r = 22 + k
    put(wv, f"A{r}", nme)
    put(wv, f"B{r}", f"=E{16+k}", BLACK, EUR)
    for col, srow in zip("CDE", (23, 24, 25)):
        put(wv, f"{col}{r}",
            f"=Inputs!$B${srow}*SUMPRODUCT($B$8:$D$8,$B$4:$D$4*Inputs!$B$6-B{10+k}:D{10+k})"
            f"+Inputs!$C${srow}*Inputs!$B$10*SUMPRODUCT($B$8:$D$8,$B$4:$D$4)/Inputs!$B$11"
            f"+Inputs!$B$9*SUM($B$8:$D$8)-$B{r}", BOLD, EUR)
    put(wv, f"F{r}", f"=IFERROR(D{16+k}/($D$4*Inputs!$B$6-D{10+k}),0)", BOLD, PCT)
    put(wv, f"G{r}", flat[k], BLACK, wrap=True)
put(wv, "A27", "What each design does for the real goal (more distributors taking part):", BOLD)
put(wv, "A28", "1 is the strongest hook but pays mostly for volume that was coming anyway. 2 almost always pays back but gives a flat or shrinking distributor no reason to send data. "
    "3 keeps a visible reward for taking part and links the larger part to growth, paid only on the increase. "
    "4 is progressive in the usual sense (higher rate for higher growth) but pays on ALL stock orders, and with a normal yearly spread of about 14% between distributors, a large part of who lands in which tier is luck, so it pays out on noise. "
    "Designs 2 to 4 assume stock orders grow at the planned rate (Inputs B12).", BLACK, wrap=True)
wv.merge_cells("A28:G28")
wv.row_dimensions[28].height = 85
widths(wv, {"A": 62, "B": 18, "C": 18, "D": 18, "E": 18, "F": 24, "G": 30})
wv.row_dimensions[21].height = 45

# ------------------------------------------------------------------ Sensitivity
wsn = wb.create_sheet("Sensitivity")
put(wsn, "A1", "Net result per year at full ramp (year-3 participants), extra sales as the only benefit", TITLE)
put(wsn, "A2", "Rows: extra sales beyond plan as % of participants' billed. Negative = the programme costs more than it earns.", BLACK)
hdr(wsn, 4, ["Extra sales vs plan", "1 Deck", "2 Growth only", "3 Hybrid", "4 Tiered"])
for i, u in enumerate([0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]):
    r = 5 + i
    put(wsn, f"A{r}", u, BLUE, PCT)
    for k, c in enumerate("BCDE"):
        put(wsn, f"{c}{r}", f"=$A{r}*(Design_variants!$D$4*Inputs!$B$6-Design_variants!$D${10+k})-Design_variants!$D${16+k}", BLACK, EUR)
put(wsn, "A15", "Break-even per design is on Design_variants. Read the sign: no colours on purpose.", BLACK)
widths(wsn, {"A": 24, "B": 18, "C": 18, "D": 18, "E": 18})

# ------------------------------------------------------------------ Evidence
we = wb.create_sheet("Evidence")
put(we, "A1", "What the data can and cannot say about the benefit", TITLE)
hdr(we, 3, ["Observation", "Number", "Source / reading"])
ev = [
    ("Median year-on-year change in billing of the 12 larger distributors, FY2025 vs FY2024", 0.085, PCT, "gps_clean_all_fy_v2.csv; distributors above €300k in each year, Israel excluded (UTI/UMI split)"),
    ("Same, FY2026 vs FY2025", 0.011, PCT, "same"),
    ("Spread (standard deviation) of year-on-year change, FY2025", 0.255, PCT, "A distributor moves ±14% to ±25% in a normal year, so a +1.5% effect cannot be seen in one year per distributor"),
    ("Spread (standard deviation) of year-on-year change, FY2026", 0.138, PCT, "same"),
    ("Average yearly growth FY2024→FY2026, distributors that send sales to dealer today (5)", 0.044, PCT, "IUK, ITUK, Ireland, Portugal, Greece (not Romania: no history). NOT evidence that sending data lifts sales; groups differ in size and markets"),
    ("Average yearly growth FY2024→FY2026, the other larger distributors (7)", 0.102, PCT, "same"),
    ("ITUK oil-filter capture 2024 → 2025", "56% → 79%", None, "FACTS.md §1b. Capture can move 20+ points in a year without a programme; one category only"),
    ("Network billed vs modelled target wallet 2025", "€30.8M vs €54.4M", None, "wallet_waterfall.csv. Ceiling, not recoverable sales"),
    ("Price-decision value if +5% price revision goes through", "€638k–€726k", None, "Universe €300k term sheet §2. Price reaction can only be measured distributor→dealer and needs two years of data (DECISIONS 11 Aug 2026)"),
    ("Parts billed ≥20% below reference price, PMS, 2025", "8.4% = €558,851", None, "Universe 3.0 §3.4. Deliberate discounts, not an error to recover"),
]
for i, (a, b, fmt, c) in enumerate(ev):
    r = 4 + i
    put(we, f"A{r}", a, wrap=True)
    put(we, f"B{r}", b, BLUE, fmt)
    put(we, f"C{r}", c, wrap=True)
put(we, "A16", "Reading for management", BOLD)
put(we, "A17", "1) No uplift from sharing data has been measured here, so every benefit line is an assumption and says so. "
    "2) Normal yearly movement is larger than the effect we hope for, so one year of results cannot prove it. "
    "3) The credible route is a measured pilot: a few distributors in the programme, comparable distributors outside it, same months, same measure, decided in advance. "
    "4) Until then, ask for approval of the cost ceiling and of the pilot, not of a return.", BLACK, wrap=True)
we.merge_cells("A17:C17")
we.row_dimensions[17].height = 90
widths(we, {"A": 70, "B": 20, "C": 80})
for r in range(4, 14):
    we.row_dimensions[r].height = 32

# ------------------------------------------------------------------ Summary (first)
ws = wb.create_sheet("Summary", 0)
put(ws, "A1", "Excellence Partner Program — return on investment, model v2", TITLE)
put(ws, "A2", "Internal draft · 9 October 2026 · euros · stock orders only · no extra running cost · edit Inputs and Distributors, the rest recalculates", BLACK)
hdr(ws, 4, ["Design (same participants, 3 years)", "3-year cost", "Net result, Low", "Net result, Base", "Net result, High", "Extra sales needed to break even in year 3 (% of billed)"])
for k, nme in enumerate(names):
    r = 5 + k
    put(ws, f"A{r}", nme)
    for col, src in zip("BCDEF", "BCDEF"):
        put(ws, f"{col}{r}", f"=Design_variants!{src}{22+k}", GREEN, PCT if col == "F" else EUR)
put(ws, "A9", "Low / Base / High are my assumptions for extra sales (0.5% / 1.5% / 3% of participants' billed) and price-decision value; no measured uplift exists. See Evidence.", BLACK, wrap=True)
ws.merge_cells("A9:F9")
ws.row_dimensions[9].height = 30
hdr(ws, 11, ["What the discount is worth next to the incentives already paid", "", "", "", "", ""])
put(ws, "A12", "Rebate credits already booked in FY2026, all distributors in scope (€)")
put(ws, "B12", "=Distributors!R24", GREEN, EUR)
put(ws, "A13", "… as % of their billed")
put(ws, "B13", "=Distributors!S24", GREEN, PCT)
put(ws, "A14", "Year-3 discount, deck design (€)")
put(ws, "B14", "=Design_variants!D10", GREEN, EUR)
put(ws, "A15", "… times the rebates paid today")
put(ws, "B15", "=IFERROR(B14/B12,0)", BOLD, '0.0"x"')
put(ws, "A16", "Year-3 discount, hybrid design (€)")
put(ws, "B16", "=Design_variants!D12", GREEN, EUR)
put(ws, "A17", "… times the rebates paid today")
put(ws, "B17", "=IFERROR(B16/B12,0)", BOLD, '0.0"x"')
hdr(ws, 19, ["Still open before this goes to management", "", "", "", "", ""])
miss = [
    "A defendable benefit. No measured uplift exists; Low/Base/High are assumptions. A pilot with comparable distributors outside the programme gives the first measurement.",
    "Share of the rebates that is tied to sales-to-dealer data today. Universe papers say 20% of the incentive; not confirmed. The incentive sheet (budget_per_DB_reviewed_24042026.xlsx) is not in the workspace.",
    "Internal time of Jerome and Bart Symons is not costed (no extra cash). Management may want it shown.",
    "Excluded on purpose: air-freight saving from rush orders moving to stock orders (stock orders only).",
]
for i, t in enumerate(miss):
    put(ws, f"A{20+i}", f"{i+1}. {t}", BLACK, wrap=True)
    ws.merge_cells(f"A{20+i}:F{20+i}")
    ws.row_dimensions[20 + i].height = 32
put(ws, "A25", "Sheets: Inputs · Distributors (plan per distributor) · Plan_ROI (detail for the design chosen on Inputs B30) · Design_variants · Sensitivity · Evidence.", BLACK)
widths(ws, {"A": 66, "B": 18, "C": 18, "D": 18, "E": 18, "F": 26})
ws.row_dimensions[4].height = 45

for sh in wb.worksheets:
    sh.sheet_view.showGridLines = False
    sh.page_setup.orientation = "landscape"
    sh.page_setup.fitToWidth = 1
    sh.page_setup.fitToHeight = 0
    sh.sheet_properties.pageSetUpPr.fitToPage = True
    if sh.title != "Distributors":
        for col in "BCDE":
            if (sh.column_dimensions[col].width or 0) < 28:
                sh.column_dimensions[col].width = 28
        sh.freeze_panes = "B4" if sh.title not in ("Summary",) else "B5"
wb.save(OUT)
print(OUT)
