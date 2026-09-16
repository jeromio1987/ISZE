# Extend the N75 coverage workbook: both layers first-class, fuel+air focus.
# Does not touch PowerPoint. Same two output paths.

from pathlib import Path
from shutil import copy2

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.page import PageMargins

SRC = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_PMS_N75_Coverage_Calculations.xlsx")
OUT_A = SRC
OUT_B = Path(r"C:\Users\jerom\Desktop\claude\ISZE\ISZE_PMS_N75_Coverage_Calculations.xlsx")

NAVY = PatternFill("solid", fgColor="1A2B4A")
PAPER = PatternFill("solid", fgColor="F7F4EE")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
GREEN = PatternFill("solid", fgColor="E6F5EF")
GREY = PatternFill("solid", fgColor="E7E6E6")
AMBER = PatternFill("solid", fgColor="FCE4D6")
WHITE = PatternFill("solid", fgColor="FFFFFF")

FONT_TITLE = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
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
PCT, NUM, NUM2 = "0.0%", "#,##0", "#,##0.00"


def paint(cell, fill=None, font=None, fmt=None, align=None):
    if fill is not None:
        cell.fill = fill
    cell.font = font or FONT_BODY
    cell.alignment = align or WRAP
    cell.border = THIN
    if fmt:
        cell.number_format = fmt


def header_row(ws, row, cols, h=32):
    ws.row_dimensions[row].height = h
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = FONT_HDR
        cell.alignment = WRAP_CC
        cell.border = THIN


def label(cell, text, fill=WHITE, font=None):
    cell.value = text
    paint(cell, fill, font or FONT_BODY, None, WRAP_C)


def note(cell, text, fill=PAPER):
    cell.value = text
    paint(cell, fill, FONT_MUTED, None, WRAP)


def formula(cell, f, fmt=NUM, fill=GREEN):
    cell.value = f
    paint(cell, fill, FONT_INPUT, fmt, Alignment(wrap_text=True, vertical="center", horizontal="right"))


def title_bar(ws, text, merge, subtitle=None, submerge=None):
    a, b = merge.split(":")
    ws.merge_cells(merge)
    ws[a] = text
    ws[a].font = FONT_TITLE
    ws[a].fill = NAVY
    ws[a].alignment = WRAP_C
    ws.row_dimensions[1].height = 26
    if subtitle:
        ws.merge_cells(submerge)
        c = submerge.split(":")[0]
        ws[c] = subtitle
        ws[c].font = Font(name="Calibri", size=10, color="F7F4EE")
        ws[c].fill = NAVY
        ws[c].alignment = WRAP_C
        ws.row_dimensions[2].height = 32


def page_setup(ws, landscape=True):
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.6, bottom=0.6)
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.freeze_panes = "A5"
    ws.sheet_view.showGridLines = False


def widths(ws, pairs):
    for col, w in pairs.items():
        ws.column_dimensions[col].width = w


wb = load_workbook(SRC)

# ---------------------------------------------------------------------------
# Cover: both layers, fuel+air focus
# ---------------------------------------------------------------------------
ws = wb["Cover"]
ws["A5"] = (
    "This workbook shows how the N75 PMS coverage percentages are calculated on two layers, "
    "same part-number basket, same period (calendar 2025, 1 January to 31 December). "
    "Layer 1 = ISZE to ITUK billed quantity (what ISZE invoiced ITUK). "
    "Layer 2 = ITUK to dealer quantity (what ITUK invoiced dealers). "
    "They are not the same number. Coverage = actual quantity / expected annual demand. "
    "Expected demand uses the IML service schedule from the April 2026 PMS analysis: "
    "9,359 N75 vehicles, 50,000 km per year, 40,000 km filter interval (1.25 events per year). "
    "Fuel and air are the campaign focus. Oil is kept as a calculation row and is labelled "
    "not an ISZE campaign item. Yellow cells on Parameters are inputs. Every coverage % is an Excel formula. "
    "File date: 15 August 2026. N75 only. The complementary PowerPoint was not edited."
)
ws["A5"].alignment = WRAP
ws.row_dimensions[5].height = 110

# Reorder headline chips: Fuel, Air, Oil (not campaign), then wear
ws["A17"] = "Locked headline (formulas)  |  both layers  |  fuel and air are the campaign focus"
ws["B18"] = "Fuel"
ws["C18"] = "Air"
ws["D18"] = "Oil (not an ISZE campaign item)"
ws["E18"] = "Brake"
ws["F18"] = "Clutch"
ws["A19"] = "1. ISZE to ITUK"
ws["B19"] = "=FUEL_QTY_ISZE_ITUK/EXPECTED_FILTERS_QTY"
ws["C19"] = "=AIR_QTY_ISZE_ITUK/EXPECTED_FILTERS_QTY"
ws["D19"] = "=OIL_QTY_ISZE_ITUK/EXPECTED_FILTERS_QTY"
ws["E19"] = "=BRAKE_QTY_ISZE_ITUK/EXPECTED_BRAKE_QTY"
ws["F19"] = "=CLUTCH_QTY_ISZE_ITUK/EXPECTED_CLUTCH_QTY"
ws["G19"] = "ITUK billing account 2575. N75 cut. Calendar 2025. Fuel 94% and air 19% are this layer on the complementary pack."
ws["A20"] = "2. ITUK to dealer"
ws["B20"] = "=FUEL_QTY_DEALER/EXPECTED_FILTERS_QTY"
ws["C20"] = "=AIR_QTY_DEALER/EXPECTED_FILTERS_QTY"
ws["D20"] = "=OIL_QTY_DEALER/EXPECTED_FILTERS_QTY"
ws["E20"] = "=BRAKE_QTY_DEALER/EXPECTED_BRAKE_QTY"
ws["F20"] = "=CLUTCH_QTY_DEALER/EXPECTED_CLUTCH_QTY"
ws["G20"] = "Same expected demand, different actuals. Fuel 95.2% and air 19.6% are this layer. Not ISZE invoices."

for r in (19, 20):
    for col in range(2, 7):
        formula(ws.cell(row=r, column=col), ws.cell(row=r, column=col).value, PCT, GREEN)
    paint(ws.cell(row=r, column=1), GREEN, FONT_INPUT, None, WRAP_C)
    note(ws.cell(row=r, column=7), ws.cell(row=r, column=7).value, GREEN)
    ws.row_dimensions[r].height = 40
paint(ws["D18"], AMBER, FONT_HDR, None, WRAP_CC)
ws["D18"].fill = AMBER
ws["D18"].font = Font(name="Calibri", size=10, bold=True, color="222222")

# sheet map: add new sheets
# find the map rows and append
ws["A26"] = "Open Both_layers first for the two-layer table. Then Worked_example_Fuel and Worked_example_Air."
ws["A26"].font = FONT_SEC
ws.merge_cells("A26:G26")

# ---------------------------------------------------------------------------
# Parameters: period + campaign note + IUK rejection
# ---------------------------------------------------------------------------
ps = wb["Parameters"]
ps.merge_cells("A46:J46")
ps["A46"] = "G. Period and layer labels (locked)"
ps["A46"].font = FONT_SEC
ps["A46"].fill = PAPER

ps["A47"] = "P07"
ps["B47"] = "Quantity period"
ps["C47"] = "calendar 2025"
paint(ps["C47"], YELLOW, FONT_INPUT, None, WRAP_C)
ps["D47"] = "1 Jan 2025 to 31 Dec 2025"
ps["E47"] = "QTY_PERIOD"
ps["F47"] = "Input (locked text)"
ps["G47"] = "Actual, Both_layers, worked examples"
ps["H47"] = "April 2026 N75 study and complementary pack source note (2025 billed)."
ps["I47"] = "15 Aug 2026"
ps["J47"] = (
    "Both layers use this same window. Do not write CY as a slogan. "
    "Do not replace with 2026 year-to-date or warehouse issues."
)
for c in range(1, 11):
    if c != 3:
        paint(ps.cell(row=47, column=c), PAPER, FONT_BODY if c != 2 else FONT_INPUT, None, WRAP)
ps.row_dimensions[47].height = 40

ps.merge_cells("A49:J49")
ps["A49"] = (
    "Layer 1 source: ISZE invoices to ITUK, billing account 2575, N75 share-scaled cut, calendar 2025. "
    "Layer 2 source: ITUK invoices to dealers, N75 part-number split (exclude N35 and F-Series), calendar 2025, "
    "from the April 2026 N75 study (progress-pack dealer column). "
    "The file dealer_sellout_long_IUK_CY2025.csv was opened and rejected for this pack: it is IUK D-Max LCV, not ITUK trucks. "
    "IUK is not ITUK. Campaign PNs on that IUK file are zero."
)
ps["A49"].font = FONT_MUTED
ps["A49"].alignment = WRAP
ps.row_dimensions[49].height = 48

# oil parameter notes: not campaign
for row, hint in ((19, "OIL  |  not an ISZE campaign item. Kept so the 40% complementary-pack chip can be rebuilt."),
                  (25, "OIL  |  not an ISZE campaign item. Dealer layer of the same oil basket.")):
    old = ps.cell(row=row, column=2).value or ""
    if "not an ISZE campaign" not in old:
        ps.cell(row=row, column=2).value = old.replace("Oil filter", "Oil filter (not an ISZE campaign item)")
    note_old = ps.cell(row=row, column=10).value or ""
    if "not an ISZE campaign" not in note_old:
        ps.cell(row=row, column=10).value = hint + " " + note_old

# ---------------------------------------------------------------------------
# Actual: rename dealer column language
# ---------------------------------------------------------------------------
act = wb["Actual"]
act["A1"] = "Actual quantity  |  two layers  |  same basket  |  calendar 2025"
if act["A2"].value:
    act["A2"] = (
        "Layer 1 = ISZE to ITUK billed quantity (ITUK billing account 2575, N75 cut). "
        "Layer 2 = ITUK to dealer quantity (N75 part-number split). "
        "Period for both: calendar 2025 (1 January to 31 December). "
        "Do not mix the two layers. Oil is in this table as a calculation row, not an ISZE campaign item."
    )
    act["A2"].alignment = WRAP
    act.row_dimensions[2].height = 40
act["B4"] = "ISZE to ITUK qty"
act["D4"] = "ITUK to dealer qty"
act["A5"] = "Oil filter (not an ISZE campaign item)"

# ---------------------------------------------------------------------------
# Coverage: campaign flag + dealer label
# ---------------------------------------------------------------------------
cov = wb["Coverage"]
cov["A1"] = "Coverage  |  both layers  |  actual / expected  |  every % is a formula"
cov["E4"] = "Actual ITUK to dealer"
cov["F4"] = "Cover ITUK to dealer"
cov["A5"] = "Oil filter (not an ISZE campaign item)"
# add campaign column L
cov["L4"] = "Campaign?"
paint(cov["L4"], NAVY, FONT_HDR, None, WRAP_CC)
flags = {5: "No  |  not an ISZE campaign item", 6: "Yes  |  fuel is in the campaign",
         7: "Yes  |  air is in the campaign", 8: "No  |  not headlined", 9: "No  |  footnote only"}
for r, txt in flags.items():
    fill = AMBER if r == 5 else (GREEN if r in (6, 7) else GREY)
    label(cov.cell(row=r, column=12), txt, fill, FONT_INPUT)
cov.column_dimensions["L"].width = 32

# ---------------------------------------------------------------------------
# Both_layers (new, place after Cover)
# ---------------------------------------------------------------------------
if "Both_layers" in wb.sheetnames:
    del wb["Both_layers"]
bl = wb.create_sheet("Both_layers", 1)
page_setup(bl, True)
bl.sheet_properties.tabColor = "C0552D"
title_bar(
    bl,
    "Both layers  |  N75  |  calendar 2025  |  fuel and air are the focus",
    "A1:H1",
    "Layer 1 = ISZE to ITUK (billing account 2575).  Layer 2 = ITUK to dealer.  Same expected qty.  Oil is not an ISZE campaign item.",
    "A2:H2",
)

bl.merge_cells("A4:H4")
bl["A4"] = "The table the complementary-pack percentages come from. Every cover % is an Excel formula pointing at Parameters."
bl["A4"].font = FONT_SEC
bl["A4"].fill = PAPER

headers = [
    "Category",
    "Campaign?",
    "Expected qty",
    "ISZE to ITUK qty",
    "Cover ISZE to ITUK",
    "ITUK to dealer qty",
    "Cover ITUK to dealer",
    "Notes",
]
for c, h in enumerate(headers, 1):
    bl.cell(row=5, column=c, value=h)
header_row(bl, 5, 8, 36)

rows = [
    (
        6, "Fuel filter", "Yes  |  campaign focus",
        "=EXPECTED_FILTERS_QTY", "=FUEL_QTY_ISZE_ITUK", "=D6/C6",
        "=FUEL_QTY_DEALER", "=F6/C6",
        "11,021 / 11,698.75 on layer 1. 11,139 / 11,698.75 on layer 2. Complementary slide prints 94% (layer 1, whole percent).",
        GREEN,
    ),
    (
        7, "Air filter", "Yes  |  campaign focus",
        "=EXPECTED_FILTERS_QTY", "=AIR_QTY_ISZE_ITUK", "=D7/C7",
        "=AIR_QTY_DEALER", "=F7/C7",
        "2,226 / 11,698.75 on layer 1. 2,289 / 11,698.75 on layer 2. Complementary slide prints 19% and 2,226 / 11,699 (layer 1).",
        GREEN,
    ),
    (
        8, "Oil filter", "No  |  not an ISZE campaign item",
        "=EXPECTED_FILTERS_QTY", "=OIL_QTY_ISZE_ITUK", "=D8/C8",
        "=OIL_QTY_DEALER", "=F8/C8",
        "Kept so the complementary-pack 40% oil chip can be rebuilt. Same method as fuel and air. Not a campaign line.",
        AMBER,
    ),
    (
        9, "Brake", "No  |  not headlined",
        "=EXPECTED_BRAKE_QTY", "=BRAKE_QTY_ISZE_ITUK", "=D9/C9",
        "=BRAKE_QTY_DEALER", "=F9/C9",
        "Expected is UIO x 0.5, not UIO x 1.25. In the file for completeness.",
        GREY,
    ),
    (
        10, "Clutch", "No  |  footnote only",
        "=EXPECTED_CLUTCH_QTY", "=CLUTCH_QTY_ISZE_ITUK", "=D10/C10",
        "=CLUTCH_QTY_DEALER", "=F10/C10",
        "Expected is UIO x 47% manuals x 0.5. 47% is the denominator share, not the cover %.",
        GREY,
    ),
]
for r, cat, camp, exp, q1, c1, q2, c2, notes, fill in rows:
    label(bl.cell(row=r, column=1), cat, fill, FONT_INPUT)
    label(bl.cell(row=r, column=2), camp, fill, FONT_INPUT)
    formula(bl.cell(row=r, column=3), exp, NUM2, GREEN)
    formula(bl.cell(row=r, column=4), q1, NUM, GREEN)
    formula(bl.cell(row=r, column=5), c1, PCT, GREEN)
    formula(bl.cell(row=r, column=6), q2, NUM, GREEN)
    formula(bl.cell(row=r, column=7), c2, PCT, GREEN)
    note(bl.cell(row=r, column=8), notes, fill)
    bl.row_dimensions[r].height = 44

bl.merge_cells("A12:H12")
bl["A12"] = "How the two layers were locked (same period, same N75 basket)"
bl["A12"].font = FONT_SEC
bl["A12"].fill = PAPER

for c, h in enumerate(["Layer", "What it is", "Period", "Source used", "Source opened and not used"], 1):
    bl.cell(row=13, column=c, value=h)
header_row(bl, 13, 5, 28)

label(bl["A14"], "1. ISZE to ITUK", GREEN, FONT_INPUT)
label(bl["B14"], "ISZE invoices to ITUK. N75 share-scaled cut of the 2025 billed basket. Billing account 2575.", GREEN)
label(bl["C14"], "calendar 2025", GREEN)
label(bl["D14"], "April 2026 N75 study integer lock (4,673 / 11,021 / 2,226 / 2,902 / 243) plus the unrounded extract on Parameters.", GREEN)
label(bl["E14"], "Raw line-level billing files are not in this workbook. Account 2575 is the ITUK invoice account, written here as a source key only.", GREEN)
bl.row_dimensions[14].height = 52

label(bl["A15"], "2. ITUK to dealer", GREEN, FONT_INPUT)
label(bl["B15"], "ITUK invoices to dealers. N75 part-number split (exclude N35 and F-Series).", GREEN)
label(bl["C15"], "calendar 2025", GREEN)
label(bl["D15"], "April 2026 N75 study / progress-pack dealer column (5,404 / 11,139 / 2,289 / 2,923 / 340).", GREEN)
label(bl["E15"], "dealer_sellout_long_IUK_CY2025.csv is IUK D-Max LCV, not ITUK trucks. Campaign PNs on that file are zero. IUK is not ITUK.", GREEN)
bl.row_dimensions[15].height = 52

bl.merge_cells("A17:H17")
bl["A17"] = (
    "Do not add layer 1 and layer 2. Do not call oil a campaign item. "
    "Do not quote fuel 94% as complete UK. Do not use the IUK D-Max file as ITUK dealer sell-out."
)
bl["A17"].font = FONT_WARN
bl["A17"].alignment = WRAP
bl.row_dimensions[17].height = 28

widths(bl, {"A": 22, "B": 32, "C": 16, "D": 20, "E": 20, "F": 20, "G": 22, "H": 72})

# ---------------------------------------------------------------------------
# Worked examples: fuel and air, both layers
# ---------------------------------------------------------------------------
def worked_sheet(name, title, qty_isze, qty_dlr, slide_print, pack_print, extra_note, tab):
    if name in wb.sheetnames:
        del wb[name]
    w = wb.create_sheet(name)
    page_setup(w, False)
    w.sheet_properties.tabColor = tab
    title_bar(
        w, title, "A1:E1",
        "Same expected qty on both layers. Period = calendar 2025. Change Parameters and this page moves.",
        "A2:E2",
    )
    for c, h in enumerate(["Step", "In words", "Excel formula", "Result", "Notes"], 1):
        w.cell(row=4, column=c, value=h)
    header_row(w, 4, 5)

    steps = [
        (5, "1. N75 UIO", "Cleaned 2024A N75 parc, both engine generations.",
         "=UIO_N75", "=UIO_N75", NUM, "9,359. Not 10,684. Not 22,389."),
        (6, "2. Kilometres per year", "Planning kilometres on the IML service schedule.",
         "=KM_PER_YEAR", "=KM_PER_YEAR", NUM, "50,000 km. April 2026 PMS analysis."),
        (7, "3. Filter interval", "Oil / fuel / air planning interval.",
         "=FILTER_INTERVAL_KM", "=FILTER_INTERVAL_KM", NUM, "40,000 km. GIDSS NPR75 oil and fuel. Air uses the same planning interval."),
        (8, "4. Events per year", "Kilometres divided by interval.",
         "=KM_PER_YEAR/FILTER_INTERVAL_KM", "=KM_PER_YEAR/FILTER_INTERVAL_KM", "0.00",
         "50,000 / 40,000 = 1.25."),
        (9, "5. Addressable share", "Share of UIO treated as demand.",
         "=ADDRESSABLE_SHARE", "=ADDRESSABLE_SHARE", PCT, "100%."),
        (10, "6. Expected quantity", "UIO x events x addressable. Shared by oil, fuel and air.",
         "=D5*D8*D9", "=D5*D8*D9", NUM2, "9,359 x 1.25 = 11,698.75. Pack table prints 11,699."),
        (11, "7a. Layer 1 actual  |  ISZE to ITUK",
         "Calendar 2025 billed qty on this category, N75 cut, billing account 2575.",
         f"={qty_isze}", f"={qty_isze}", NUM,
         "Layer 1 only. Not ITUK to dealer."),
        (12, "8a. Layer 1 cover %", "ISZE to ITUK qty / expected qty.",
         "=D11/D10", "=D11/D10", PCT,
         f"Complementary slide prints {slide_print} (layer 1, whole percent). Progress-pack table prints {pack_print}."),
        (13, "7b. Layer 2 actual  |  ITUK to dealer",
         "Calendar 2025 ITUK invoices to dealers, same N75 basket.",
         f"={qty_dlr}", f"={qty_dlr}", NUM,
         "Layer 2 only. Same expected qty as step 6. Not ISZE invoices."),
        (14, "8b. Layer 2 cover %", "ITUK to dealer qty / the same expected qty.",
         "=D13/D10", "=D13/D10", PCT,
         "If this % and 8a differ, that is stock / timing / mix between the two layers, not a second method."),
    ]
    for r, step, words, ftxt, flive, fmt, notes in steps:
        fill = PAPER if r % 2 == 0 else WHITE
        if r in (11, 12):
            fill = GREEN
        if r in (13, 14):
            fill = PAPER
        label(w.cell(row=r, column=1), step, fill, FONT_INPUT)
        label(w.cell(row=r, column=2), words, fill)
        label(w.cell(row=r, column=3), ftxt, fill, FONT_INPUT)
        formula(w.cell(row=r, column=4), flive, fmt, GREEN)
        note(w.cell(row=r, column=5), notes, fill)
        w.row_dimensions[r].height = 36

    w.merge_cells("A16:E16")
    w["A16"] = extra_note
    w["A16"].font = FONT_MUTED
    w["A16"].alignment = WRAP
    w.row_dimensions[16].height = 40
    widths(w, {"A": 40, "B": 48, "C": 36, "D": 14, "E": 72})
    return w


worked_sheet(
    "Worked_example_Fuel",
    "Worked example  |  fuel  |  both layers",
    "FUEL_QTY_ISZE_ITUK",
    "FUEL_QTY_DEALER",
    "94%",
    "94.2% / 95.2%",
    "Fuel 94% is N75 only. Complete-parc fuel is about 65% on the complementary-pack footnote. Do not quote 94% as whole UK. Period is calendar 2025 on both layers.",
    "2E7D4F",
)
worked_sheet(
    "Worked_example_Air",
    "Worked example  |  air  |  both layers",
    "AIR_QTY_ISZE_ITUK",
    "AIR_QTY_DEALER",
    "19%",
    "19.0% / 19.6%",
    "Air uses the same expected 11,698.75 as fuel. GIDSS MY24 air is inspect / indicator; the 40,000 km interval is the April 2026 planning choice so air is measured on the same visit. Period is calendar 2025 on both layers.",
    "C0552D",
)

# Relabel oil worked example
wo = wb["Worked_example_Oil"]
wo["A1"] = "Worked example  |  oil  |  not an ISZE campaign item  |  both layers"
if wo["A2"].value:
    wo["A2"] = (
        "Oil is in this file so the complementary-pack 40% chip can be rebuilt. "
        "It is not an ISZE campaign item. Fuel and air are the campaign walkthroughs."
    )

# What_this_is_not: add IUK trap + oil campaign trap
wt = wb["What_this_is_not"]
# find last used row
last = 16
for r in range(4, 40):
    if wt.cell(row=r, column=1).value:
        last = r
r1, r2 = last + 2, last + 3
label(wt.cell(row=r1, column=1), "13", PAPER, FONT_INPUT)
label(wt.cell(row=r1, column=2), "Not the IUK D-Max dealer file.", PAPER, FONT_INPUT)
label(wt.cell(row=r1, column=3), "Use the April 2026 N75 study ITUK-to-dealer column.", PAPER)
note(wt.cell(row=r1, column=4),
     "dealer_sellout_long_IUK_CY2025.csv is IUK LCV D-Max. IUK is not ITUK. Campaign PNs on that file are zero. Do not use it as ITUK to dealer.",
     PAPER)
wt.row_dimensions[r1].height = 44
label(wt.cell(row=r2, column=1), "14", AMBER, FONT_INPUT)
label(wt.cell(row=r2, column=2), "Oil is not an ISZE campaign item.", AMBER, FONT_INPUT)
label(wt.cell(row=r2, column=3), "Use fuel and air on Both_layers and the two worked-example sheets.", AMBER)
note(wt.cell(row=r2, column=4),
     "Oil stays in the file as a calculation row so 40% can be rebuilt. Do not present oil as a campaign line.",
     AMBER)
wt.row_dimensions[r2].height = 44

# Sheet order
order = [
    "Cover",
    "Both_layers",
    "Parameters",
    "Expected",
    "Actual",
    "Coverage",
    "Worked_example_Fuel",
    "Worked_example_Air",
    "Worked_example_Oil",
    "What_this_is_not",
]
for i, name in enumerate(order):
    wb.move_sheet(name, offset=i - wb.sheetnames.index(name))

wb.save(OUT_A)
copy2(OUT_A, OUT_B)
print("sheets", wb.sheetnames)
print("Wrote", OUT_A, OUT_A.stat().st_size)
print("Wrote", OUT_B, OUT_B.stat().st_size)
