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
    (7, "Programme running cost per year (€)", 100000, EUR,
     "PLACEHOLDER = Universe 3.0 recommended route (€100k). Replace with real internal time, IMG support, training, award.", YELLOW),
    (8, "One-off build cost in year 1 (€)", 0, EUR,
     "NOT KNOWN. Network developer to estimate intake channel, checks, SAP condition, quarterly report. Leave 0 = result is too favourable.", YELLOW),
    (9, "Other benefits per year at full ramp (€)", 0, EUR,
     "Fill in only what can be defended, e.g. air-freight saved when rush orders move to stock orders. No data in workspace yet.", YELLOW),
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
put(wi, "A27", "Colour code: blue = typed input · black = formula · green = link to another sheet · yellow = key assumption or missing number.", BLACK)
widths(wi, {"A": 58, "B": 22, "C": 60, "D": 50})
for r in range(4, 17):
    wi.row_dimensions[r].height = 30
wi.row_dimensions[22].height = 45

# ------------------------------------------------------------------ Distributors
wd = wb.create_sheet("Distributors")
put(wd, "A1", "Distributors in scope (19, CIS excluded) and the illustrative participation plan", TITLE)
put(wd, "A2", "Levels: 0 = not in · 1 = level 1 (-2.5%) · 2 = level 2 (-5%). Years: FY2028, FY2029, FY2030. Plan is illustrative; edit the blue level cells.", BLACK)
hdr(wd, 4, ["Code", "Distributor", "Billed FY2026 (€)", "Stock orders FY2026 (€)", "Stock-order share", "Kickback today",
            "Sales to dealer today", "Uncaptured wallet 2025 (€, modelled ceiling)", "Level Y1", "Level Y2", "Level Y3",
            "Billed of participants Y1 (€)", "Y2 (€)", "Y3 (€)", "Discount cost Y1 (€)", "Y2 (€)", "Y3 (€)"])
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
put(wd, "A24", "Total", BOLD)
for col in "CDHLMNOPQ":
    put(wd, f"{col}24", f"=SUM({col}5:{col}23)", BOLD, EUR)
put(wd, "E24", "=IFERROR(D24/C24,0)", BOLD, PCT)
put(wd, "A26", "Sources: billed and stock orders = sales_fact.parquet, FY2026 (1 Apr 2025 – 31 Mar 2026), credit notes, transport and rebates excluded, via _build/order_mix_and_discount_cost.py. "
    "Uncaptured wallet = wallet_waterfall.csv, 2025 — a ceiling built on target spend per truck, NOT recoverable sales (FACTS.md). Kickback list = 01_data/91_build/build_gps_kickback_proposal.py. "
    "Sales to dealer today = register in 01_data/DATA_MANIFEST.md §05.", BLACK, wrap=True)
wd.merge_cells("A26:Q26")
wd.row_dimensions[26].height = 55
widths(wd, {"A": 12, "B": 28, "C": 16, "D": 16, "E": 11, "F": 10, "G": 22, "H": 20, "I": 8, "J": 8, "K": 8,
            "L": 16, "M": 14, "N": 14, "O": 16, "P": 14, "Q": 14})
wd.row_dimensions[4].height = 58
wd.freeze_panes = "C5"

# ------------------------------------------------------------------ Plan ROI
wp = wb.create_sheet("Plan_ROI")
put(wp, "A1", "Plan: cost, benefit and net result per year (deck design: flat discount on all stock orders)", TITLE)
hdr(wp, 3, ["", "Year 1 FY2028", "Year 2 FY2029", "Year 3 FY2030", "3-year total"])
cols = ["B", "C", "D"]
dist_bill = dict(zip(cols, "LMN"))
dist_cost = dict(zip(cols, "OPQ"))
lvl_col = dict(zip(cols, "IJK"))
ramp_row = dict(zip(cols, (18, 19, 20)))

labels = {4: "Participating distributors", 5: "Billed of participants, FY2026 base (€)", 6: "Discount cost (€)",
          7: "Programme running cost (€)", 8: "One-off build cost (€)", 9: "Total cost (€)",
          10: "Discount cost as % of participants' billed", 11: "Margin on an extra € billed, after the discount", 12: "Ramp-up"}
for r, t in labels.items():
    put(wp, f"A{r}", t, BOLD if r == 9 else BLACK)
for c in cols:
    put(wp, f"{c}4", f'=COUNTIF(Distributors!{lvl_col[c]}5:{lvl_col[c]}23,">0")', GREEN, "0")
    put(wp, f"{c}5", f"=Distributors!{dist_bill[c]}24", GREEN, EUR)
    put(wp, f"{c}6", f"=Distributors!{dist_cost[c]}24", GREEN, EUR)
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
put(wv, "A1", "Same participants (Year 3), three ways to pay — which design earns its money back", TITLE)
hdr(wv, 3, ["", "V1 Deck: flat on all stock orders", "V2 Growth only: on stock orders above FY2026", "V3 Hybrid: small flat + growth bonus"])
put(wv, "A4", "Stock orders of level-1 participants (€)")
put(wv, "A5", "Stock orders of level-2 participants (€)")
put(wv, "A6", "Billed of participants (€)")
put(wv, "B4", "=SUMPRODUCT(Distributors!$D$5:$D$23*(Distributors!$K$5:$K$23=1))", GREEN, EUR)
put(wv, "B5", "=SUMPRODUCT(Distributors!$D$5:$D$23*(Distributors!$K$5:$K$23=2))", GREEN, EUR)
put(wv, "B6", "=Distributors!N24", GREEN, EUR)
for c in "CD":
    for r in (4, 5, 6):
        put(wv, f"{c}{r}", f"=$B{r}", BLACK, EUR)
put(wv, "A8", "Discount cost per year (€)")
put(wv, "B8", "=B4*Inputs!$B$4+B5*Inputs!$B$5", BLACK, EUR)
put(wv, "C8", "=(C4*Inputs!$B$4+C5*Inputs!$B$5)*Inputs!$B$12", BLACK, EUR)
put(wv, "D8", "=D4*Inputs!$B$13+D5*Inputs!$B$14+(D4*Inputs!$B$15+D5*Inputs!$B$16)*Inputs!$B$12", BLACK, EUR)
put(wv, "A9", "Programme running cost per year (€)")
put(wv, "A10", "Total cost per year (€)")
put(wv, "A11", "Discount cost as % of participants' billed")
put(wv, "A12", "Margin on an extra € billed, after the discount")
put(wv, "A13", "Extra sales needed to break even (growth as only benefit, €)")
put(wv, "A14", "… as % of participants' billed")
put(wv, "A15", "Reward for a participant whose stock orders stay flat")
for c in "BCD":
    put(wv, f"{c}9", "=Inputs!$B$7", GREEN, EUR)
    put(wv, f"{c}10", f"={c}8+{c}9", BOLD, EUR)
    put(wv, f"{c}11", f"=IFERROR({c}8/{c}6,0)", BLACK, PCT2)
    put(wv, f"{c}12", f"=Inputs!$B$6-{c}11", BLACK, PCT)
    put(wv, f"{c}13", f"=IFERROR({c}10/{c}12,0)", BLACK, EUR)
    put(wv, f"{c}14", f"=IFERROR({c}13/{c}6,0)", BOLD, PCT)
put(wv, "B15", "Full discount (-2.5% / -5%)", BLACK, wrap=True)
put(wv, "C15", "None", BLACK)
put(wv, "D15", "Small flat part only", BLACK, wrap=True)
put(wv, "A17", "What each design does for the real goal (more distributors taking part):", BOLD)
put(wv, "A18", "V1 is the strongest hook for participation but pays mostly for volume that was coming anyway. "
    "V2 almost always pays back but gives a flat or shrinking distributor no reason to send data. "
    "V3 keeps a visible reward for taking part and links the bigger part to growth. Growth cost in V2 and V3 assumes stock orders grow at the planned rate (Inputs B12).", BLACK, wrap=True)
wv.merge_cells("A18:D18")
wv.row_dimensions[18].height = 60
widths(wv, {"A": 62, "B": 28, "C": 28, "D": 28})
wv.row_dimensions[3].height = 45

# ------------------------------------------------------------------ Sensitivity
wsn = wb.create_sheet("Sensitivity")
put(wsn, "A1", "Net result per year at full ramp (Year 3 participants), growth as the only benefit", TITLE)
put(wsn, "A2", "Rows: extra sales beyond plan as % of participants' billed. Negative = the programme costs more than it earns.", BLACK)
hdr(wsn, 4, ["Extra sales vs plan", "V1 Deck", "V2 Growth only", "V3 Hybrid"])
for i, u in enumerate([0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]):
    r = 5 + i
    put(wsn, f"A{r}", u, BLUE, PCT)
    for c in "BCD":
        put(wsn, f"{c}{r}", f"=$A{r}*Design_variants!{c}$6*Design_variants!{c}$12-Design_variants!{c}$10", BLACK, EUR)
put(wsn, "A15", "Cell colours are not used on purpose: read the sign. The break-even row for each design is on Design_variants.", BLACK)
widths(wsn, {"A": 24, "B": 18, "C": 18, "D": 18})

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
put(ws, "A1", "Excellence Partner Program — return on investment, first model", TITLE)
put(ws, "A2", "Internal draft · 9 October 2026 · euros per fiscal year · edit Inputs and Distributors, everything else recalculates", BLACK)
hdr(ws, 4, ["", "Low", "Base", "High"])
rowsS = [
    (5, "3-year cost (€)", "=Plan_ROI!E9", "=Plan_ROI!E9", "=Plan_ROI!E9", EUR),
    (6, "3-year benefit (€)", f"=Plan_ROI!E{blocks['Low']+5}", f"=Plan_ROI!E{blocks['Base']+5}", f"=Plan_ROI!E{blocks['High']+5}", EUR),
    (7, "3-year net result (€)", f"=Plan_ROI!E{blocks['Low']+6}", f"=Plan_ROI!E{blocks['Base']+6}", f"=Plan_ROI!E{blocks['High']+6}", EUR),
    (8, "Return on cost (net ÷ cost)", f"=Plan_ROI!E{blocks['Low']+7}", f"=Plan_ROI!E{blocks['Base']+7}", f"=Plan_ROI!E{blocks['High']+7}", PCT),
]
for r, lab, a, b, c, fmt in rowsS:
    put(ws, f"A{r}", lab, BOLD if r in (7, 8) else BLACK)
    for col, f in zip("BCD", (a, b, c)):
        put(ws, f"{col}{r}", f, GREEN, fmt)
put(ws, "A9", "Verdict on these assumptions")
for col in "BCD":
    put(ws, f"{col}9", f'=IF({col}7>0,"pays back","does not pay back")', BOLD)
hdr(ws, 11, ["Break-even, deck design (year 3, full ramp)", "", "", ""])
put(ws, "A12", "Extra sales beyond plan needed, as % of participants' billed")
put(ws, "B12", f"=Plan_ROI!D{be+2}", GREEN, PCT)
put(ws, "A13", "… with the growth-only design (V2)")
put(ws, "B13", "=Design_variants!C14", GREEN, PCT)
put(ws, "A14", "… with the hybrid design (V3)")
put(ws, "B14", "=Design_variants!D14", GREEN, PCT)
put(ws, "A15", "Year-3 discount cost, deck design (€)")
put(ws, "B15", "=Plan_ROI!D6", GREEN, EUR)
hdr(ws, 17, ["What is missing before this can go to management", "", "", ""])
miss = [
    "Real running cost and one-off build cost (yellow cells on Inputs): network developer, IMG support, training, award.",
    "A defendable benefit. No measured uplift exists; the three scenarios are assumptions. A pilot with comparable distributors outside the programme would produce the first measurement.",
    "Air freight and handling cost of rush and VOR orders, to value the move to stock orders. Not in the workspace.",
    "Kickback size per distributor, to see what is already paid for the same data.",
]
for i, t in enumerate(miss):
    put(ws, f"A{18+i}", f"{i+1}. {t}", BLACK, wrap=True)
    ws.merge_cells(f"A{18+i}:D{18+i}")
    ws.row_dimensions[18 + i].height = 32
put(ws, "A23", "Sheets: Inputs · Distributors (plan per distributor) · Plan_ROI (cost, benefit, net) · Design_variants · Sensitivity · Evidence.", BLACK)
widths(ws, {"A": 72, "B": 18, "C": 18, "D": 18})

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
