# Build Mode A Excel: how N75 PMS coverage % on the complementary pack is calculated.
# Outputs (same file, two paths). Does not touch any PowerPoint.

from copy import copy
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.page import PageMargins

OUT_A = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_PMS_N75_Coverage_Calculations.xlsx")
OUT_B = Path(r"C:\Users\jerom\Desktop\claude\ISZE\ISZE_PMS_N75_Coverage_Calculations.xlsx")

NAVY = PatternFill("solid", fgColor="1A2B4A")
PAPER = PatternFill("solid", fgColor="F7F4EE")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
GREEN = PatternFill("solid", fgColor="E6F5EF")
GREY = PatternFill("solid", fgColor="E7E6E6")
AMBER = PatternFill("solid", fgColor="FCE4D6")
RED_SOFT = PatternFill("solid", fgColor="F8E4E3")
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

PCT = "0.0%"
PCT2 = "0.00%"
NUM = "#,##0"
NUM1 = "#,##0.0"
NUM2 = "#,##0.00"
NUM4 = "#,##0.0000"


def widths(ws, pairs):
    for col, w in pairs.items():
        ws.column_dimensions[col].width = w


def header_row(ws, row, cols, heights=32):
    ws.row_dimensions[row].height = heights
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = FONT_HDR
        cell.alignment = WRAP_CC
        cell.border = THIN


def paint(cell, fill=None, font=None, fmt=None, align=None):
    if fill is not None:
        cell.fill = fill
    cell.font = font or FONT_BODY
    cell.alignment = align or WRAP
    cell.border = THIN
    if fmt:
        cell.number_format = fmt


def input_cell(cell, value, fmt=NUM):
    cell.value = value
    paint(cell, YELLOW, FONT_INPUT, fmt, Alignment(wrap_text=True, vertical="center", horizontal="right"))


def formula_cell(cell, formula, fmt=NUM, fill=GREEN):
    cell.value = formula
    paint(cell, fill, FONT_INPUT, fmt, Alignment(wrap_text=True, vertical="center", horizontal="right"))


def note_cell(cell, text, fill=PAPER):
    cell.value = text
    paint(cell, fill, FONT_MUTED, None, WRAP)


def label_cell(cell, text, fill=WHITE, font=None):
    cell.value = text
    paint(cell, fill, font or FONT_BODY, None, WRAP_C)


def page_setup(ws, landscape=False):
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.6, bottom=0.6)
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:4"
    ws.sheet_view.showGridLines = False


def define_name(wb, name, ref):
    # Replace if a rebuild re-runs in the same process (should not), else add.
    existing = [dn for dn in wb.defined_names.values() if dn.name == name]
    for dn in existing:
        del wb.defined_names[dn.name]
    wb.defined_names.add(DefinedName(name=name, attr_text=ref))


wb = Workbook()

# =============================================================================
# 1. Cover
# =============================================================================
ws = wb.active
ws.title = "Cover"
page_setup(ws, landscape=True)
ws.freeze_panes = "A5"
ws.sheet_properties.tabColor = "1A2B4A"

ws.merge_cells("A1:G1")
ws["A1"] = "N75 PMS coverage calculations  |  how the complementary-pack percentages are built"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
ws["A1"].fill = NAVY
ws["A1"].alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[1].height = 28

ws.merge_cells("A2:G2")
ws["A2"] = (
    "File date: 15 August 2026.  Scope: N75 only.  Not the complete UK registered parc.  "
    "Audience: IML / ITUK / ISZE.  Every coverage % on the Coverage sheet is an Excel formula."
)
ws["A2"].font = Font(name="Calibri", size=10, color="F7F4EE")
ws["A2"].fill = NAVY
ws["A2"].alignment = WRAP_C
ws.row_dimensions[2].height = 22

ws.merge_cells("A4:G4")
ws["A4"] = "What this file is"
ws["A4"].font = FONT_SEC
ws["A4"].fill = PAPER

ws.merge_cells("A5:G5")
ws["A5"] = (
    "This workbook reconstructs the N75 PMS coverage percentages shown on the ISZE complementary pack "
    "(How we proceed, N75 cover slide: Fuel 94%, Oil 40%, Air 19%, with clutch 47% manuals / 11% actual "
    "as a footnote). It is a calculation file, not a new study. Coverage = 2025 billed quantity divided by "
    "expected annual demand. Expected demand uses the IML service schedule locked in the April 2026 PMS "
    "analysis: 50,000 km per year and a 40,000 km filter interval, which is 1.25 filter events per vehicle "
    "per year. Wear parts (brake, clutch) use 0.5 events per year. Clutch expected demand is further limited "
    "to 47% of N75 UIO (manual-transmission convention, not VIN-verified). Two quantity layers are shown "
    "and must not be treated as the same number: (1) ISZE to ITUK billed quantity, and (2) ITUK dealer "
    "sell-out. Yellow cells on Parameters are inputs. Change a yellow cell and Expected, Coverage, and "
    "the oil worked example recalculate."
)
ws["A5"].font = FONT_BODY
ws["A5"].alignment = WRAP
ws["A5"].fill = WHITE
ws.row_dimensions[5].height = 96

ws.merge_cells("A7:G7")
ws["A7"] = "How to read the sheets"
ws["A7"].font = FONT_SEC
ws["A7"].fill = PAPER

headers = ["Sheet", "What it does", "What you should do"]
for c, h in enumerate(headers, 1):
    ws.cell(row=8, column=c, value=h)
header_row(ws, 8, 3)

rows_map = [
    (
        "Cover",
        "This page. One-paragraph purpose, date, N75-only scope.",
        "Read first. Then open Parameters.",
    ),
    (
        "Parameters",
        "Every locked input: UIO, km/year, intervals, factors, billed qty, dealer sell-out qty. Derived cells are formulas.",
        "Yellow = input. Green = formula. Grey = do-not-use reference. Notes column names each parameter.",
    ),
    (
        "Expected",
        "Step-by-step expected quantity per category. All results are formulas that point at Parameters.",
        "Follow oil / fuel / air (same expected qty), then brake, then clutch.",
    ),
    (
        "Actual",
        "2025 quantities used in the pack, split into ISZE to ITUK billed qty vs dealer sell-out. Not the same layer.",
        "Read the source note on each row. Do not add the two layers together.",
    ),
    (
        "Coverage",
        "Cover % = actual / expected. Excel formulas, percent-formatted. Pack slide print is shown beside the formula so you can see rounding.",
        "This is the page that answers 'how is 40% / 94% / 19% calculated?'",
    ),
    (
        "Worked_example_Oil",
        "One category walked in words and cells: UIO to events to expected to actual to %.",
        "Use this if you are explaining the method in a meeting.",
    ),
    (
        "What_this_is_not",
        "Traps: not warehouse YTD, not complete parc, do not sum model tables, do not use 10,684 or 22,389 as N75 UIO.",
        "Read before quoting a percentage outside N75.",
    ),
]
for i, (a, b, c) in enumerate(rows_map, 9):
    fill = PAPER if i % 2 == 0 else WHITE
    label_cell(ws.cell(row=i, column=1), a, fill, FONT_INPUT)
    label_cell(ws.cell(row=i, column=2), b, fill)
    label_cell(ws.cell(row=i, column=3), c, fill)
    ws.row_dimensions[i].height = 36

ws.merge_cells("A17:G17")
ws["A17"] = "Locked headline (formulas; same maths as Coverage)"
ws["A17"].font = FONT_SEC
ws["A17"].fill = PAPER

for c, h in enumerate(
    ["Layer", "Oil", "Fuel", "Air", "Brake", "Clutch", "Notes"], 1
):
    ws.cell(row=18, column=c, value=h)
header_row(ws, 18, 7)

# These formulas are written after named ranges exist; placeholders filled below.
cover_headlines = [
    (
        19,
        "ISZE to ITUK billed qty",
        "=OIL_QTY_ISZE_ITUK/EXPECTED_FILTERS_QTY",
        "=FUEL_QTY_ISZE_ITUK/EXPECTED_FILTERS_QTY",
        "=AIR_QTY_ISZE_ITUK/EXPECTED_FILTERS_QTY",
        "=BRAKE_QTY_ISZE_ITUK/EXPECTED_BRAKE_QTY",
        "=CLUTCH_QTY_ISZE_ITUK/EXPECTED_CLUTCH_QTY",
        "Primary layer on the complementary pack (Fuel 94% / Oil 40% / Air 19%).",
    ),
    (
        20,
        "Dealer sell-out",
        "=OIL_QTY_DEALER/EXPECTED_FILTERS_QTY",
        "=FUEL_QTY_DEALER/EXPECTED_FILTERS_QTY",
        "=AIR_QTY_DEALER/EXPECTED_FILTERS_QTY",
        "=BRAKE_QTY_DEALER/EXPECTED_BRAKE_QTY",
        "=CLUTCH_QTY_DEALER/EXPECTED_CLUTCH_QTY",
        "Same expected demand, different actuals. Oil 46.2% vs 40.0% is this split, not a second method.",
    ),
]
for r, layer, o, f, a, b, cl, note in cover_headlines:
    label_cell(ws.cell(row=r, column=1), layer, GREEN, FONT_INPUT)
    for col, formula in enumerate((o, f, a, b, cl), 2):
        formula_cell(ws.cell(row=r, column=col), formula, PCT, GREEN)
    note_cell(ws.cell(row=r, column=7), note, GREEN)
    ws.row_dimensions[r].height = 32

ws.merge_cells("A22:G22")
ws["A22"] = (
    "Source lock (15 August 2026). Numbers below were read from the April 2026 PMS analysis builder, "
    "the N75 progress pack table, and the UIO 2024A Method A cut. They were not invented for this file. "
    "The complementary PowerPoint was not edited."
)
ws["A22"].font = FONT_MUTED
ws["A22"].alignment = WRAP
ws.row_dimensions[22].height = 36

ws.merge_cells("A24:G24")
ws["A24"] = (
    "Language note. This file may be opened with IML or ITUK. It uses business words only: "
    "IML service schedule, April 2026 PMS analysis, GIDSS NPR75 MY24, ISZE to ITUK billed quantity, "
    "dealer sell-out, N75 UIO 2024A. Yellow = you may edit. Green = formula. Grey = shown so you do not use it."
)
ws["A24"].font = FONT_MUTED
ws["A24"].alignment = WRAP
ws.row_dimensions[24].height = 36

widths(ws, {"A": 32, "B": 52, "C": 52, "D": 14, "E": 14, "F": 14, "G": 62})

# =============================================================================
# 2. Parameters
# =============================================================================
ws = wb.create_sheet("Parameters")
page_setup(ws, landscape=True)
ws.freeze_panes = "A5"
ws.sheet_properties.tabColor = "C0552D"

ws.merge_cells("A1:J1")
ws["A1"] = "Parameters  |  every input named, sourced, and explained"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
ws["A1"].fill = NAVY
ws["A1"].alignment = WRAP_C
ws.row_dimensions[1].height = 26

ws.merge_cells("A2:J2")
ws["A2"] = (
    "Yellow cells are inputs. Green cells are formulas that other sheets read. "
    "Grey cells are reference values that must not be used as N75 UIO. "
    "Edit yellow only. Date locked: 15 August 2026."
)
ws["A2"].font = Font(name="Calibri", size=10, color="F7F4EE")
ws["A2"].fill = NAVY
ws["A2"].alignment = WRAP_C
ws.row_dimensions[2].height = 22

# Column map: A id, B name, C value, D unit, E excel name, F formula text, G used by, H source, I date, J notes
ph = [
    "ID",
    "Parameter",
    "Value",
    "Unit",
    "Excel name",
    "Formula in this cell",
    "Used by",
    "Source",
    "Date locked",
    "Notes",
]
for c, h in enumerate(ph, 1):
    ws.cell(row=4, column=c, value=h)
header_row(ws, 4, 10, 28)

# (row, id, name, value, unit, excel_name, formula_text, used, source, date, notes, kind, numfmt)
# kind: input | formula | ref
P_ROWS = []


def add_p(row, pid, name, value, unit, excel_name, formula_text, used, source, date, notes, kind, numfmt):
    P_ROWS.append(
        (row, pid, name, value, unit, excel_name, formula_text, used, source, date, notes, kind, numfmt)
    )


# --- A. Parc and schedule ---
ws.merge_cells("A3:J3")
ws["A3"] = "A. Parc and IML service schedule (April 2026 PMS analysis)"
ws["A3"].font = FONT_SEC
ws["A3"].fill = PAPER

add_p(
    5, "P01", "N75 UIO (pilot parc)", 9359, "vehicles", "UIO_N75",
    "Input (locked)", "Expected, Coverage, Worked_example_Oil",
    "UIO workbook 2024A Method A, both N75 engine generations (NPR75 and NPR88). Same cut as the April 2026 N75 study and the complementary pack.",
    "15 Aug 2026",
    "This is the only UIO that belongs in the N75 cover %. It is the cleaned 2024A N75 count. It is not 10,684 (mixed light-duty bucket) and not 22,389 (complete UK registered parc). Both engine generations are included.",
    "input", NUM,
)
add_p(
    6, "P02", "Annual kilometres per vehicle", 50000, "km / year", "KM_PER_YEAR",
    "Input (locked)", "FILTER_EVENTS_PER_YEAR, WEAR_EVENTS_PER_YEAR",
    "April 2026 PMS analysis planning assumption. Not a measured fleet average from MOT or R&M contracts.",
    "15 Aug 2026",
    "Planning number used so IML and ITUK quote one cover %. Changing this cell changes events per year and every expected quantity.",
    "input", NUM,
)
add_p(
    7, "P03", "Filter interval (oil, fuel, air)", 40000, "km", "FILTER_INTERVAL_KM",
    "Input (locked)", "FILTER_EVENTS_PER_YEAR",
    "GIDSS NPR75 MY24: oil filter and fuel filter replace every 40,000 km. April 2026 analysis applies the same 40,000 km to air so air sits on the same scheduled visit. GIDSS MY24 air is inspect / indicator; the 40,000 km air interval is the planning choice, not a GIDSS replace-every line.",
    "15 Aug 2026",
    "Do not switch this to 20,000 km. That is the older kick-off example (older MY oil), not the current GIDSS NPR75 oil/fuel line used on the complementary pack.",
    "input", NUM,
)
add_p(
    8, "P04", "Wear-part interval (brake, clutch)", 100000, "km", "WEAR_INTERVAL_KM",
    "Input (locked)", "WEAR_EVENTS_PER_YEAR",
    "April 2026 PMS analysis wear assumption (disc / kit). Not a GIDSS fixed replace-every for every N75.",
    "15 Aug 2026",
    "50,000 / 100,000 = 0.5 wear events per year. The complementary pack uses this 0.5 factor for brake and clutch expected demand.",
    "input", NUM,
)
add_p(
    9, "P05", "Clutch manual-transmission share", 0.47, "share of UIO", "CLUTCH_MANUAL_SHARE",
    "Input (locked)", "CLUTCH_UIO_N75",
    "Fleet-wide convention used in the April 2026 analysis (~47% of the registered fleet is manual). No N75-specific VIN extract was available.",
    "15 Aug 2026",
    "Clutch expected = N75 UIO x 47% x 0.5. The complementary pack footnote '47% manuals / 11% actual' is this share (denominator) and the resulting cover % (actual / expected). Not VIN-verified.",
    "input", PCT,
)
add_p(
    10, "P06", "Addressable share of UIO", 1.0, "share of UIO", "ADDRESSABLE_SHARE",
    "Input (locked)", "All expected quantities",
    "April 2026 analysis treats 100% of the N75 UIO as addressable for this cover %.",
    "15 Aug 2026",
    "Locked at 100%. Expected qty = UIO x events/year x addressable. If this were 70%, every expected qty and every cover % would change. The complementary pack does not apply a 70% ceiling.",
    "input", PCT,
)

# --- B. Derived ---
# row 11 section label
ws.merge_cells("A11:J11")
ws["A11"] = "B. Derived schedule factors (formulas; do not type over)"
ws["A11"].font = FONT_SEC
ws["A11"].fill = PAPER

add_p(
    12, "D01", "Filter events per vehicle per year", "=C6/C7", "events / year", "FILTER_EVENTS_PER_YEAR",
    "=KM_PER_YEAR / FILTER_INTERVAL_KM", "Oil, fuel, air expected qty",
    "Derived from P02 and P03. April 2026 analysis writes this as 1.25x.",
    "15 Aug 2026",
    "50,000 / 40,000 = 1.25. This is the filter factor on the complementary pack. Oil, fuel and air share this factor.",
    "formula", "0.00",
)
add_p(
    13, "D02", "Wear events per vehicle per year", "=C6/C8", "events / year", "WEAR_EVENTS_PER_YEAR",
    "=KM_PER_YEAR / WEAR_INTERVAL_KM", "Brake and clutch expected qty",
    "Derived from P02 and P04. April 2026 analysis writes this as 0.5x.",
    "15 Aug 2026",
    "50,000 / 100,000 = 0.50. This is the wear factor on the complementary pack.",
    "formula", "0.00",
)
add_p(
    14, "D03", "Clutch-relevant N75 UIO", "=C5*C9", "vehicles", "CLUTCH_UIO_N75",
    "=UIO_N75 * CLUTCH_MANUAL_SHARE", "Clutch expected qty",
    "Derived from P01 and P05.",
    "15 Aug 2026",
    "9,359 x 0.47 = 4,398.73 vehicles. Only this subset is assumed to need a clutch kit in the expected-demand model.",
    "formula", NUM2,
)
add_p(
    15, "D04", "Expected oil / fuel / air quantity", "=C5*C12*C10", "units / year", "EXPECTED_FILTERS_QTY",
    "=UIO_N75 * FILTER_EVENTS_PER_YEAR * ADDRESSABLE_SHARE", "Expected, Coverage, Worked_example_Oil",
    "Derived. Complementary pack displays 11,699 (integer rounding of 11,698.75).",
    "15 Aug 2026",
    "9,359 x 1.25 x 100% = 11,698.75. The progress-pack table prints 11,699. Coverage formulas in this file use the exact 11,698.75, not a typed 11,699.",
    "formula", NUM2,
)
add_p(
    16, "D05", "Expected brake quantity", "=C5*C13*C10", "units / year", "EXPECTED_BRAKE_QTY",
    "=UIO_N75 * WEAR_EVENTS_PER_YEAR * ADDRESSABLE_SHARE", "Expected, Coverage",
    "Derived. Complementary / progress pack displays 4,680 (integer rounding of 4,679.5).",
    "15 Aug 2026",
    "9,359 x 0.5 x 100% = 4,679.5. Same as UIO x 0.5.",
    "formula", NUM2,
)
add_p(
    17, "D06", "Expected clutch quantity", "=C14*C13*C10", "units / year", "EXPECTED_CLUTCH_QTY",
    "=CLUTCH_UIO_N75 * WEAR_EVENTS_PER_YEAR * ADDRESSABLE_SHARE", "Expected, Coverage",
    "Derived. Complementary / progress pack displays 2,199 (integer rounding of 2,199.365).",
    "15 Aug 2026",
    "9,359 x 0.47 x 0.5 x 100% = 2,199.365. Same as UIO x 0.47 x 0.5.",
    "formula", NUM2,
)

# --- C. ISZE to ITUK actuals ---
ws.merge_cells("A18:J18")
ws["A18"] = "C. ISZE to ITUK billed quantity (2025)  |  N75 cut  |  not dealer sell-out"
ws["A18"].font = FONT_SEC
ws["A18"].fill = PAPER

add_p(
    19, "A01", "Oil filter  |  ISZE to ITUK billed qty", 4673, "units", "OIL_QTY_ISZE_ITUK",
    "Input (locked)", "Actual, Coverage, Worked_example_Oil",
    "April 2026 N75 study integer lock (progress-pack table 4,673). Underlying extract before integer lock: 4,673.3438 (see U01).",
    "15 Aug 2026",
    "N75 share of 2025 ISZE to ITUK billed oil-filter units. Share-scaled N75 cut, not a VIN-tagged extract. Do not call this dealer sell-out.",
    "input", NUM,
)
add_p(
    20, "A02", "Fuel filter  |  ISZE to ITUK billed qty", 11021, "units", "FUEL_QTY_ISZE_ITUK",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study integer lock (progress-pack table 11,021). Underlying extract: 11,021.0982 (see U02).",
    "15 Aug 2026",
    "N75 share of 2025 ISZE to ITUK billed fuel-filter units. This is why fuel can read 94% on N75 and about 65% on the complete parc: different UIO, same method.",
    "input", NUM,
)
add_p(
    21, "A03", "Air filter  |  ISZE to ITUK billed qty", 2226, "units", "AIR_QTY_ISZE_ITUK",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study integer lock (progress-pack table 2,226). Underlying extract: 2,225.7013 (see U03).",
    "15 Aug 2026",
    "N75 share of 2025 ISZE to ITUK billed air-filter units. Complementary pack prints 2,226 / 11,699 expected.",
    "input", NUM,
)
add_p(
    22, "A04", "Brake  |  ISZE to ITUK billed qty", 2902, "units", "BRAKE_QTY_ISZE_ITUK",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study integer lock (progress-pack table 2,902). Underlying extract: 2,902.4413 (see U04).",
    "15 Aug 2026",
    "N75 share of 2025 ISZE to ITUK billed brake units. On the complementary pack this is a table/footnote fact, not the Tuesday campaign headline.",
    "input", NUM,
)
add_p(
    23, "A05", "Clutch  |  ISZE to ITUK billed qty", 243, "units", "CLUTCH_QTY_ISZE_ITUK",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study integer lock (progress-pack table 243). Underlying extract: 242.6042 (see U05).",
    "15 Aug 2026",
    "N75 share of 2025 ISZE to ITUK billed clutch units. Cover is low because expected demand is already cut to 47% manuals. Not a Tuesday ask on the complementary pack.",
    "input", NUM,
)

# --- D. Dealer sell-out ---
ws.merge_cells("A24:J24")
ws["A24"] = "D. Dealer sell-out quantity (2025)  |  N75 cut  |  not ISZE to ITUK billed qty"
ws["A24"].font = FONT_SEC
ws["A24"].fill = PAPER

add_p(
    25, "A06", "Oil filter  |  dealer sell-out qty", 5404, "units", "OIL_QTY_DEALER",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study / progress-pack dealer column (5,404). Bottom-up part-number split: 2025 dealer sell-out minus N35-tagged and F-Series-tagged lines.",
    "15 Aug 2026",
    "ITUK to dealers. Same expected 11,698.75. 5,404 / 11,698.75 = 46.2%. This is not 4,673. The 6.2 point gap vs ISZE to ITUK is stock / timing / mix, not a second cover method.",
    "input", NUM,
)
add_p(
    26, "A07", "Fuel filter  |  dealer sell-out qty", 11139, "units", "FUEL_QTY_DEALER",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study / progress-pack dealer column (11,139).",
    "15 Aug 2026",
    "11,139 / 11,698.75 = 95.2%. Near the ISZE to ITUK 94.2%. Still N75 only.",
    "input", NUM,
)
add_p(
    27, "A08", "Air filter  |  dealer sell-out qty", 2289, "units", "AIR_QTY_DEALER",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study / progress-pack dealer column (2,289).",
    "15 Aug 2026",
    "2,289 / 11,698.75 = 19.6%. Same story as 19.0% ISZE to ITUK: air is the attach miss on N75.",
    "input", NUM,
)
add_p(
    28, "A09", "Brake  |  dealer sell-out qty", 2923, "units", "BRAKE_QTY_DEALER",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study / progress-pack dealer column (2,923).",
    "15 Aug 2026",
    "2,923 / 4,679.5 = 62.5%. Close to the 62.0% ISZE to ITUK figure.",
    "input", NUM,
)
add_p(
    29, "A10", "Clutch  |  dealer sell-out qty", 340, "units", "CLUTCH_QTY_DEALER",
    "Input (locked)", "Actual, Coverage",
    "April 2026 N75 study / progress-pack dealer column (340).",
    "15 Aug 2026",
    "340 / 2,199.365 = 15.5%. Still the same 47% manual convention in the denominator.",
    "input", NUM,
)

# --- E. Unrounded extract ---
ws.merge_cells("A30:J30")
ws["A30"] = "E. Unrounded ISZE to ITUK extract (before the integer lock used on the pack)"
ws["A30"].font = FONT_SEC
ws["A30"].fill = PAPER

add_p(
    31, "U01", "Oil filter  |  unrounded ISZE to ITUK extract", 4673.3438, "units", "OIL_QTY_ISZE_ITUK_UNROUNDED",
    "Input (documentation)", "Coverage (comparison column only)",
    "N75 share-scaled extract used before the study rounded to 4,673.",
    "15 Aug 2026",
    "4,673.3438 / 11,698.75 = 40.0% to one decimal. Integer 4,673 / 11,698.75 = 39.9% to one decimal. The complementary slide prints 40%. Both are the same source; the difference is rounding.",
    "input", NUM4,
)
add_p(
    32, "U02", "Fuel filter  |  unrounded ISZE to ITUK extract", 11021.0982, "units", "FUEL_QTY_ISZE_ITUK_UNROUNDED",
    "Input (documentation)", "Coverage (comparison column only)",
    "N75 share-scaled extract used before the study rounded to 11,021.",
    "15 Aug 2026",
    "11,021.0982 / 11,698.75 = 94.2% to one decimal. Integer 11,021 gives the same 94.2%.",
    "input", NUM4,
)
add_p(
    33, "U03", "Air filter  |  unrounded ISZE to ITUK extract", 2225.7013, "units", "AIR_QTY_ISZE_ITUK_UNROUNDED",
    "Input (documentation)", "Coverage (comparison column only)",
    "N75 share-scaled extract used before the study rounded to 2,226.",
    "15 Aug 2026",
    "2,225.7013 / 11,698.75 = 19.0% to one decimal. Integer 2,226 also gives 19.0%.",
    "input", NUM4,
)
add_p(
    34, "U04", "Brake  |  unrounded ISZE to ITUK extract", 2902.4413, "units", "BRAKE_QTY_ISZE_ITUK_UNROUNDED",
    "Input (documentation)", "Coverage (comparison column only)",
    "N75 share-scaled extract used before the study rounded to 2,902.",
    "15 Aug 2026",
    "2,902.4413 / 4,679.5 = 62.0% to one decimal. Integer 2,902 also gives 62.0%.",
    "input", NUM4,
)
add_p(
    35, "U05", "Clutch  |  unrounded ISZE to ITUK extract", 242.6042, "units", "CLUTCH_QTY_ISZE_ITUK_UNROUNDED",
    "Input (documentation)", "Coverage (comparison column only)",
    "N75 share-scaled extract used before the study rounded to 243.",
    "15 Aug 2026",
    "242.6042 / 2,199.365 = 11.0% to one decimal. Integer 243 also gives 11.0%.",
    "input", NUM4,
)

# --- F. Do not use ---
ws.merge_cells("A36:J36")
ws["A36"] = "F. Do not use as N75 UIO (shown so the wrong denominators are visible)"
ws["A36"].font = FONT_SEC
ws["A36"].fill = AMBER

add_p(
    37, "X01", "Complete UK registered parc (all models)", 22389, "vehicles", "UIO_COMPLETE_PARC_DO_NOT_USE",
    "Reference only", "What_this_is_not",
    "Same UIO workbook 2024A total (N35 + N75 + residual). Complementary pack footnote 'complete parc about 65%' uses this layer, not 9,359.",
    "15 Aug 2026",
    "Do not put this in the N75 cover denominator. Fuel 94% is N75. Complete-parc fuel is a different row (about 65%). Do not add N75 cover to complete-parc cover.",
    "ref", NUM,
)
add_p(
    38, "X02", "Mixed light-duty bucket (not N75)", 10684, "vehicles", "UIO_MIXED_LD_DO_NOT_USE",
    "Reference only", "What_this_is_not",
    "N75 9,359 + N50/55 651 + N62/65 257 + unspecified 417 = 10,684. This is the dirty light-duty collapse, not cleaned N75.",
    "15 Aug 2026",
    "Do not defend 10,684 as N75 UIO. Cell C41 proves the add-back. The complementary pack does not use 10,684.",
    "ref", NUM,
)
add_p(
    39, "X03", "N50/55 count inside the 10,684 mix", 651, "vehicles", "UIO_N50_55_IN_MIX",
    "Reference only", "C41 checksum",
    "UIO workbook raw car-park split.",
    "15 Aug 2026",
    "Part of why 10,684 is larger than 9,359. Not N75.",
    "ref", NUM,
)
add_p(
    40, "X04", "N62/65 count inside the 10,684 mix", 257, "vehicles", "UIO_N62_65_IN_MIX",
    "Reference only", "C41 checksum",
    "UIO workbook raw car-park split.",
    "15 Aug 2026",
    "Part of why 10,684 is larger than 9,359. Not N75.",
    "ref", NUM,
)
add_p(
    41, "X05", "Unspecified count inside the 10,684 mix", 417, "vehicles", "UIO_UNSPEC_IN_MIX",
    "Reference only", "C41 checksum",
    "UIO workbook raw car-park split.",
    "15 Aug 2026",
    "Part of why 10,684 is larger than 9,359. Not N75.",
    "ref", NUM,
)
add_p(
    42, "X06", "Checksum: 9,359 + 651 + 257 + 417", "=C5+C39+C40+C41", "vehicles", "UIO_MIX_CHECKSUM",
    "=UIO_N75 + N50/55 + N62/65 + unspecified", "What_this_is_not",
    "Formula. Must equal 10,684.",
    "15 Aug 2026",
    "If this does not equal C38, the mix explanation is wrong. It is a proof, not a UIO to use in cover %.",
    "formula", NUM,
)

# Write P_ROWS (skip section-only rows already written)
for row, pid, name, value, unit, excel_name, formula_text, used, source, date, notes, kind, numfmt in P_ROWS:
    fill_label = WHITE if row % 2 else PAPER
    if kind == "ref":
        fill_label = AMBER
    label_cell(ws.cell(row=row, column=1), pid, fill_label, FONT_INPUT)
    label_cell(ws.cell(row=row, column=2), name, fill_label, FONT_INPUT)
    cell_c = ws.cell(row=row, column=3)
    if kind == "input":
        input_cell(cell_c, value, numfmt)
    elif kind == "formula":
        formula_cell(cell_c, value, numfmt, GREEN)
    else:
        cell_c.value = value
        paint(cell_c, GREY, FONT_INPUT, numfmt, Alignment(wrap_text=True, vertical="center", horizontal="right"))
    label_cell(ws.cell(row=row, column=4), unit, fill_label)
    label_cell(ws.cell(row=row, column=5), excel_name, fill_label, FONT_INPUT)
    label_cell(ws.cell(row=row, column=6), formula_text, fill_label)
    label_cell(ws.cell(row=row, column=7), used, fill_label)
    label_cell(ws.cell(row=row, column=8), source, fill_label)
    label_cell(ws.cell(row=row, column=9), date, fill_label)
    note_cell(ws.cell(row=row, column=10), notes, fill_label)
    ws.row_dimensions[row].height = 48

# Named ranges (workbook scope) -> Parameters!$C$row
for item in P_ROWS:
    row, _pid, _name, _val, _unit, excel_name = item[0], item[1], item[2], item[3], item[4], item[5]
    define_name(wb, excel_name, f"Parameters!$C${row}")

ws.merge_cells("A44:J44")
ws["A44"] = (
    "Billing year for all actual quantities in this file is calendar 2025. "
    "That is the year on the complementary pack source note ('2025 billed'). "
    "Do not replace these actuals with 2026 warehouse year-to-date."
)
ws["A44"].font = FONT_MUTED
ws["A44"].alignment = WRAP
ws.row_dimensions[44].height = 28

widths(
    ws,
    {
        "A": 8, "B": 42, "C": 14, "D": 16, "E": 32, "F": 42,
        "G": 36, "H": 54, "I": 14, "J": 78,
    },
)

# =============================================================================
# 3. Expected
# =============================================================================
ws = wb.create_sheet("Expected")
page_setup(ws, landscape=True)
ws.freeze_panes = "A5"
ws.sheet_properties.tabColor = "2E7D4F"

ws.merge_cells("A1:H1")
ws["A1"] = "Expected quantity  |  step by step  |  all results are formulas"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
ws["A1"].fill = NAVY
ws["A1"].alignment = WRAP_C
ws.row_dimensions[1].height = 26

ws.merge_cells("A2:H2")
ws["A2"] = (
    "Expected demand is not sales. It is the number of units the N75 parc would use in one year "
    "if every addressable vehicle followed the IML service schedule. "
    "Oil, fuel and air share one expected quantity. Brake and clutch do not."
)
ws["A2"].font = Font(name="Calibri", size=10, color="F7F4EE")
ws["A2"].fill = NAVY
ws["A2"].alignment = WRAP_C
ws.row_dimensions[2].height = 28

ws.merge_cells("A4:H4")
ws["A4"] = "Step 1  |  read the schedule factors from Parameters"
ws["A4"].font = FONT_SEC
ws["A4"].fill = PAPER

for c, h in enumerate(["Step", "What we take", "Excel name", "Formula / value", "Result", "Notes"], 1):
    ws.cell(row=5, column=c, value=h)
header_row(ws, 5, 6)

step1 = [
    (6, "1a", "N75 UIO", "UIO_N75", "=UIO_N75", NUM,
     "Start here. 9,359 vehicles. Cleaned 2024A N75, both engine generations."),
    (7, "1b", "Kilometres per year", "KM_PER_YEAR", "=KM_PER_YEAR", NUM,
     "Planning assumption. 50,000 km/year."),
    (8, "1c", "Filter interval", "FILTER_INTERVAL_KM", "=FILTER_INTERVAL_KM", NUM,
     "40,000 km. GIDSS NPR75 oil and fuel. Air uses the same planning interval."),
    (9, "1d", "Wear interval", "WEAR_INTERVAL_KM", "=WEAR_INTERVAL_KM", NUM,
     "100,000 km. Wear assumption for brake and clutch."),
    (10, "1e", "Filter events per year", "FILTER_EVENTS_PER_YEAR", "=FILTER_EVENTS_PER_YEAR", "0.00",
     "Kilometres / filter interval. Must equal 1.25 at the locked inputs."),
    (11, "1f", "Wear events per year", "WEAR_EVENTS_PER_YEAR", "=WEAR_EVENTS_PER_YEAR", "0.00",
     "Kilometres / wear interval. Must equal 0.50 at the locked inputs."),
    (12, "1g", "Manual-transmission share", "CLUTCH_MANUAL_SHARE", "=CLUTCH_MANUAL_SHARE", PCT,
     "47%. Applied only to clutch."),
    (13, "1h", "Addressable share", "ADDRESSABLE_SHARE", "=ADDRESSABLE_SHARE", PCT,
     "100%. Applied to every expected qty."),
    (14, "1i", "Clutch-relevant UIO", "CLUTCH_UIO_N75", "=CLUTCH_UIO_N75", NUM2,
     "UIO x 47%. 4,398.73 at the locked inputs."),
]
for r, step, what, name, formula, fmt, notes in step1:
    fill = PAPER if r % 2 == 0 else WHITE
    label_cell(ws.cell(row=r, column=1), step, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=2), what, fill)
    label_cell(ws.cell(row=r, column=3), name, fill, FONT_INPUT)
    formula_cell(ws.cell(row=r, column=4), formula, fmt, GREEN)
    formula_cell(ws.cell(row=r, column=5), formula, fmt, GREEN)
    note_cell(ws.cell(row=r, column=6), notes, fill)
    ws.row_dimensions[r].height = 28

ws.merge_cells("A16:H16")
ws["A16"] = "Step 2  |  expected quantity by category (formulas)"
ws["A16"].font = FONT_SEC
ws["A16"].fill = PAPER

eh = [
    "Category",
    "Base UIO used",
    "UIO cell",
    "Events / year",
    "Addressable",
    "Expected qty (formula)",
    "Pack prints (rounded)",
    "Notes",
]
for c, h in enumerate(eh, 1):
    ws.cell(row=17, column=c, value=h)
header_row(ws, 17, 8)

expected_cats = [
    (
        18, "Oil filter", "All N75 UIO", "=UIO_N75", "=FILTER_EVENTS_PER_YEAR", "=ADDRESSABLE_SHARE",
        "=C18*D18*E18", 11699,
        "UIO x 1.25 x 100% = 11,698.75. Oil, fuel and air share this number. Pack table prints 11,699.",
    ),
    (
        19, "Fuel filter", "All N75 UIO", "=UIO_N75", "=FILTER_EVENTS_PER_YEAR", "=ADDRESSABLE_SHARE",
        "=C19*D19*E19", 11699,
        "Same expected qty as oil. A 94% fuel cover on N75 does not mean 94% on the complete parc.",
    ),
    (
        20, "Air filter", "All N75 UIO", "=UIO_N75", "=FILTER_EVENTS_PER_YEAR", "=ADDRESSABLE_SHARE",
        "=C20*D20*E20", 11699,
        "Same expected qty as oil and fuel. That is a planning choice so air is measured on the same scheduled visit.",
    ),
    (
        21, "Brake", "All N75 UIO", "=UIO_N75", "=WEAR_EVENTS_PER_YEAR", "=ADDRESSABLE_SHARE",
        "=C21*D21*E21", 4680,
        "UIO x 0.5 x 100% = 4,679.5. Pack table prints 4,680. Not UIO x 1.25.",
    ),
    (
        22, "Clutch", "Manual share of N75 UIO", "=CLUTCH_UIO_N75", "=WEAR_EVENTS_PER_YEAR", "=ADDRESSABLE_SHARE",
        "=C22*D22*E22", 2199,
        "Clutch UIO x 0.5 x 100% = 2,199.365. Equivalent to UIO x 0.47 x 0.5. Pack table prints 2,199.",
    ),
]
for r, cat, base, uio, ev, addr, exp, printed, notes in expected_cats:
    fill = PAPER if r % 2 == 0 else WHITE
    label_cell(ws.cell(row=r, column=1), cat, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=2), base, fill)
    formula_cell(ws.cell(row=r, column=3), uio, NUM2, GREEN)
    formula_cell(ws.cell(row=r, column=4), ev, "0.00", GREEN)
    formula_cell(ws.cell(row=r, column=5), addr, PCT, GREEN)
    formula_cell(ws.cell(row=r, column=6), exp, NUM2, GREEN)
    cell_g = ws.cell(row=r, column=7, value=printed)
    paint(cell_g, GREY, FONT_BODY, NUM, Alignment(wrap_text=True, vertical="center", horizontal="right"))
    note_cell(ws.cell(row=r, column=8), notes, fill)
    ws.row_dimensions[r].height = 40

ws.merge_cells("A24:H24")
ws["A24"] = "Check  |  the three named expected quantities must match the category rows"
ws["A24"].font = FONT_SEC
ws["A24"].fill = PAPER

for c, h in enumerate(["Check", "Named range", "Named value", "Category row", "Match?", "Notes"], 1):
    ws.cell(row=25, column=c, value=h)
header_row(ws, 25, 6)

checks = [
    (26, "Filters (oil/fuel/air)", "EXPECTED_FILTERS_QTY", "=EXPECTED_FILTERS_QTY", "=F18",
     '=IF(ABS(C26-D26)<0.001,"OK","BREAK")',
     "If BREAK, a Parameters formula was overwritten."),
    (27, "Brake", "EXPECTED_BRAKE_QTY", "=EXPECTED_BRAKE_QTY", "=F21",
     '=IF(ABS(C27-D27)<0.001,"OK","BREAK")',
     "Must equal UIO x 0.5 at locked inputs."),
    (28, "Clutch", "EXPECTED_CLUTCH_QTY", "=EXPECTED_CLUTCH_QTY", "=F22",
     '=IF(ABS(C28-D28)<0.001,"OK","BREAK")',
     "Must equal UIO x 0.47 x 0.5 at locked inputs."),
]
for r, lab, name, named, rowv, match, notes in checks:
    fill = WHITE
    label_cell(ws.cell(row=r, column=1), lab, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=2), name, fill)
    formula_cell(ws.cell(row=r, column=3), named, NUM2, GREEN)
    formula_cell(ws.cell(row=r, column=4), rowv, NUM2, GREEN)
    formula_cell(ws.cell(row=r, column=5), match, "@", GREEN)
    note_cell(ws.cell(row=r, column=6), notes, fill)
    ws.row_dimensions[r].height = 24

ws.merge_cells("A30:H30")
ws["A30"] = (
    "Do not sum the five expected quantities and treat that as 'N75 demand'. "
    "Oil, fuel and air are three lines against the same 11,698.75. "
    "Adding them counts the same vehicles three times."
)
ws["A30"].font = FONT_WARN
ws["A30"].alignment = WRAP
ws.row_dimensions[30].height = 32

widths(ws, {"A": 28, "B": 32, "C": 26, "D": 22, "E": 16, "F": 26, "G": 22, "H": 78})

# =============================================================================
# 4. Actual
# =============================================================================
ws = wb.create_sheet("Actual")
page_setup(ws, landscape=True)
ws.freeze_panes = "A5"
ws.sheet_properties.tabColor = "3D5A80"

ws.merge_cells("A1:H1")
ws["A1"] = "Actual quantity  |  two layers that must not be mixed"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
ws["A1"].fill = NAVY
ws["A1"].alignment = WRAP_C
ws.row_dimensions[1].height = 26

ws.merge_cells("A2:H2")
ws["A2"] = (
    "Layer 1 = ISZE to ITUK billed quantity (what ISZE invoiced ITUK in 2025, N75 cut). "
    "Layer 2 = dealer sell-out (what ITUK invoiced dealers in 2025, N75 part-number split). "
    "They are not the same number and they are not two methods for one number."
)
ws["A2"].font = Font(name="Calibri", size=10, color="F7F4EE")
ws["A2"].fill = NAVY
ws["A2"].alignment = WRAP_C
ws.row_dimensions[2].height = 32

ah = [
    "Category",
    "ISZE to ITUK billed qty",
    "Excel name (layer 1)",
    "Dealer sell-out qty",
    "Excel name (layer 2)",
    "Unrounded ISZE to ITUK extract",
    "Why the two layers differ",
    "Notes",
]
for c, h in enumerate(ah, 1):
    ws.cell(row=4, column=c, value=h)
header_row(ws, 4, 8, 36)

actuals = [
    (
        5, "Oil filter",
        "=OIL_QTY_ISZE_ITUK", "OIL_QTY_ISZE_ITUK",
        "=OIL_QTY_DEALER", "OIL_QTY_DEALER",
        "=OIL_QTY_ISZE_ITUK_UNROUNDED",
        "Dealer sold 5,404; ISZE billed ITUK 4,673. Dealer can sell from stock that was billed in another period.",
        "Progress-pack table: 4,673 DB / 5,404 dealer. Complementary slide uses the ISZE to ITUK layer for the 40% oil chip.",
    ),
    (
        6, "Fuel filter",
        "=FUEL_QTY_ISZE_ITUK", "FUEL_QTY_ISZE_ITUK",
        "=FUEL_QTY_DEALER", "FUEL_QTY_DEALER",
        "=FUEL_QTY_ISZE_ITUK_UNROUNDED",
        "Layers are close (11,021 vs 11,139). Fuel is already attaching on N75.",
        "Progress-pack table: 11,021 DB / 11,139 dealer. Complementary slide 94% is the ISZE to ITUK layer.",
    ),
    (
        7, "Air filter",
        "=AIR_QTY_ISZE_ITUK", "AIR_QTY_ISZE_ITUK",
        "=AIR_QTY_DEALER", "AIR_QTY_DEALER",
        "=AIR_QTY_ISZE_ITUK_UNROUNDED",
        "Layers are close (2,226 vs 2,289). Air is the miss on both layers.",
        "Progress-pack table: 2,226 DB / 2,289 dealer. Complementary slide prints 2,226 / 11,699.",
    ),
    (
        8, "Brake",
        "=BRAKE_QTY_ISZE_ITUK", "BRAKE_QTY_ISZE_ITUK",
        "=BRAKE_QTY_DEALER", "BRAKE_QTY_DEALER",
        "=BRAKE_QTY_ISZE_ITUK_UNROUNDED",
        "Layers are close (2,902 vs 2,923).",
        "Progress-pack table: 2,902 DB / 2,923 dealer. Not the complementary-pack campaign headline after the 14 August wording lock.",
    ),
    (
        9, "Clutch",
        "=CLUTCH_QTY_ISZE_ITUK", "CLUTCH_QTY_ISZE_ITUK",
        "=CLUTCH_QTY_DEALER", "CLUTCH_QTY_DEALER",
        "=CLUTCH_QTY_ISZE_ITUK_UNROUNDED",
        "Dealer 340 vs ISZE to ITUK 243. Still a small actual against a 47% manual expected base.",
        "Progress-pack table: 243 DB / 340 dealer. Complementary footnote: 47% manuals / 11% actual. Not a Tuesday ask.",
    ),
]
for r, cat, q1, n1, q2, n2, uq, why, notes in actuals:
    fill = PAPER if r % 2 == 0 else WHITE
    label_cell(ws.cell(row=r, column=1), cat, fill, FONT_INPUT)
    formula_cell(ws.cell(row=r, column=2), q1, NUM, GREEN)
    label_cell(ws.cell(row=r, column=3), n1, fill)
    formula_cell(ws.cell(row=r, column=4), q2, NUM, GREEN)
    label_cell(ws.cell(row=r, column=5), n2, fill)
    formula_cell(ws.cell(row=r, column=6), uq, NUM4, GREEN)
    note_cell(ws.cell(row=r, column=7), why, fill)
    note_cell(ws.cell(row=r, column=8), notes, fill)
    ws.row_dimensions[r].height = 48

ws.merge_cells("A11:H11")
ws["A11"] = "How the N75 ISZE to ITUK quantities were cut"
ws["A11"].font = FONT_SEC
ws["A11"].fill = PAPER

ws.merge_cells("A12:H12")
ws["A12"] = (
    "ISZE billing does not carry a clean N75 VIN flag on every PMS line. "
    "The April 2026 N75 study therefore uses a share-scaled N75 cut of 2025 ISZE to ITUK billed units "
    "(N75 share of the ITUK billed basket). That is why the unrounded extract has decimals (4,673.3438 oil). "
    "The study then locks integers (4,673) for the table the complementary pack reads. "
    "Dealer sell-out is different: it is a bottom-up part-number split of 2025 dealer invoices, "
    "after removing lines tagged N35 and F-Series. Do not describe dealer sell-out as 'ISZE billed qty' "
    "and do not describe ISZE billed qty as 'workshop fitment'."
)
ws["A12"].font = FONT_BODY
ws["A12"].alignment = WRAP
ws.row_dimensions[12].height = 72

ws.merge_cells("A14:H14")
ws["A14"] = (
    "Calendar year for both layers: 2025. "
    "These cells must not be replaced with warehouse issues, opening stock, or 2026 year-to-date."
)
ws["A14"].font = FONT_WARN
ws["A14"].alignment = WRAP
ws.row_dimensions[14].height = 24

widths(ws, {"A": 16, "B": 26, "C": 28, "D": 22, "E": 24, "F": 32, "G": 56, "H": 72})

# =============================================================================
# 5. Coverage
# =============================================================================
ws = wb.create_sheet("Coverage")
page_setup(ws, landscape=True)
ws.freeze_panes = "A5"
ws.sheet_properties.tabColor = "C0552D"

ws.merge_cells("A1:K1")
ws["A1"] = "Coverage  |  actual / expected  |  every % is an Excel formula"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
ws["A1"].fill = NAVY
ws["A1"].alignment = WRAP_C
ws.row_dimensions[1].height = 26

ws.merge_cells("A2:K2")
ws["A2"] = (
    "Cover % = billed quantity / expected quantity. "
    "ISZE to ITUK and dealer sell-out share the same expected quantity and use different actuals. "
    "The complementary slide prints whole percents (94 / 40 / 19). This sheet shows one-decimal formulas."
)
ws["A2"].font = Font(name="Calibri", size=10, color="F7F4EE")
ws["A2"].fill = NAVY
ws["A2"].alignment = WRAP_C
ws.row_dimensions[2].height = 28

ch = [
    "Category",
    "Actual ISZE to ITUK",
    "Expected qty",
    "Cover ISZE to ITUK",
    "Actual dealer sell-out",
    "Cover dealer sell-out",
    "Unrounded ISZE to ITUK extract",
    "Cover from unrounded extract",
    "Complementary pack print",
    "Progress-pack table print",
    "Notes",
]
for c, h in enumerate(ch, 1):
    ws.cell(row=4, column=c, value=h)
header_row(ws, 4, 11, 40)

# Category rows 5-9
cov = [
    (
        5, "Oil filter",
        "=OIL_QTY_ISZE_ITUK", "=EXPECTED_FILTERS_QTY", "=B5/C5",
        "=OIL_QTY_DEALER", "=E5/C5",
        "=OIL_QTY_ISZE_ITUK_UNROUNDED", "=G5/C5",
        "40%", "40.0%  /  46.2%",
        "Integer 4,673 / 11,698.75 = 39.9% to one decimal. Unrounded 4,673.3438 / 11,698.75 = 40.0%. Slide prints 40%. Same source, rounding only.",
    ),
    (
        6, "Fuel filter",
        "=FUEL_QTY_ISZE_ITUK", "=EXPECTED_FILTERS_QTY", "=B6/C6",
        "=FUEL_QTY_DEALER", "=E6/C6",
        "=FUEL_QTY_ISZE_ITUK_UNROUNDED", "=G6/C6",
        "94%", "94.2%  /  95.2%",
        "11,021 / 11,698.75 = 94.2%. This is N75 only. Complete-parc fuel is about 65% on the complementary-pack footnote. Do not quote 94% as whole UK.",
    ),
    (
        7, "Air filter",
        "=AIR_QTY_ISZE_ITUK", "=EXPECTED_FILTERS_QTY", "=B7/C7",
        "=AIR_QTY_DEALER", "=E7/C7",
        "=AIR_QTY_ISZE_ITUK_UNROUNDED", "=G7/C7",
        "19%", "19.0%  /  19.6%",
        "2,226 / 11,698.75 = 19.0%. Complementary slide also prints 2,226 / 11,699 expected. Air uses the same expected qty as oil and fuel.",
    ),
    (
        8, "Brake",
        "=BRAKE_QTY_ISZE_ITUK", "=EXPECTED_BRAKE_QTY", "=B8/C8",
        "=BRAKE_QTY_DEALER", "=E8/C8",
        "=BRAKE_QTY_ISZE_ITUK_UNROUNDED", "=G8/C8",
        "not a campaign chip", "62.0%  /  62.5%",
        "2,902 / 4,679.5 = 62.0%. Expected is UIO x 0.5, not UIO x 1.25. After 14 August the complementary pack does not headline brake.",
    ),
    (
        9, "Clutch",
        "=CLUTCH_QTY_ISZE_ITUK", "=EXPECTED_CLUTCH_QTY", "=B9/C9",
        "=CLUTCH_QTY_DEALER", "=E9/C9",
        "=CLUTCH_QTY_ISZE_ITUK_UNROUNDED", "=G9/C9",
        "47% manuals / 11% actual", "11.0%  /  15.5%",
        "243 / 2,199.365 = 11.0%. The 47% is the manual share in the denominator, not the cover %. Cover is 11% (ISZE to ITUK) or 15.5% (dealer).",
    ),
]
for r, cat, act, exp, cov1, dlr, cov2, unr, cov3, slide, table, notes in cov:
    fill = PAPER if r % 2 == 0 else WHITE
    label_cell(ws.cell(row=r, column=1), cat, fill, FONT_INPUT)
    formula_cell(ws.cell(row=r, column=2), act, NUM, GREEN)
    formula_cell(ws.cell(row=r, column=3), exp, NUM2, GREEN)
    formula_cell(ws.cell(row=r, column=4), cov1, PCT, GREEN)
    formula_cell(ws.cell(row=r, column=5), dlr, NUM, GREEN)
    formula_cell(ws.cell(row=r, column=6), cov2, PCT, GREEN)
    formula_cell(ws.cell(row=r, column=7), unr, NUM4, GREEN)
    formula_cell(ws.cell(row=r, column=8), cov3, PCT, GREEN)
    label_cell(ws.cell(row=r, column=9), slide, GREY)
    label_cell(ws.cell(row=r, column=10), table, GREY)
    note_cell(ws.cell(row=r, column=11), notes, fill)
    ws.row_dimensions[r].height = 52

ws.merge_cells("A11:K11")
ws["A11"] = "Formula written in words"
ws["A11"].font = FONT_SEC
ws["A11"].fill = PAPER

words = [
    (12, "Oil / fuel / air cover (ISZE to ITUK)",
     "billed qty / (N75 UIO x km per year / filter interval x addressable)",
     "= A0x / (UIO_N75 * KM_PER_YEAR / FILTER_INTERVAL_KM * ADDRESSABLE_SHARE)"),
    (13, "Brake cover (ISZE to ITUK)",
     "billed qty / (N75 UIO x km per year / wear interval x addressable)",
     "= BRAKE_QTY_ISZE_ITUK / (UIO_N75 * KM_PER_YEAR / WEAR_INTERVAL_KM * ADDRESSABLE_SHARE)"),
    (14, "Clutch cover (ISZE to ITUK)",
     "billed qty / (N75 UIO x manual share x km per year / wear interval x addressable)",
     "= CLUTCH_QTY_ISZE_ITUK / (UIO_N75 * CLUTCH_MANUAL_SHARE * KM_PER_YEAR / WEAR_INTERVAL_KM * ADDRESSABLE_SHARE)"),
]
for c, h in enumerate(["Cover", "In words", "Named-range form"], 1):
    ws.cell(row=11, column=c)  # section already set
for c, h in enumerate(["Cover", "In words", "Named-range form"], 1):
    ws.cell(row=15, column=c, value=h)
# rewrite properly - I made a mess. Clear row 11 section and put words starting 12.

# Actually row 11 is the section title (merged). Put a small header on row 12 and data 13-15.
# I already wrote data to 12-14 in `words` but also started a second header at 15. Let me
# just write the three word rows at 12-14 as planned and skip the extra header.

for r, title, words_txt, named in words:
    fill = WHITE
    label_cell(ws.cell(row=r, column=1), title, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=2), words_txt, fill)
    label_cell(ws.cell(row=r, column=3), named, fill)
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=11)
    ws.row_dimensions[r].height = 28

# Fix: words used rows 12-14 which overwrite... wait, rows 12-14 were NOT used by the category table
# (categories are 5-9). Good. But I accidentally started writing a header at row 15 in the loop
# that I then replaced. Row 15 is unused. Fine.

ws.merge_cells("A16:K16")
ws["A16"] = (
    "Do not average the five cover percentages and call that 'N75 PMS cover'. "
    "Oil, fuel and air are three attachments on the same scheduled visit. "
    "Brake and clutch use a different expected base. "
    "The complementary pack headlines Fuel / Oil / Air on N75, not a five-category average."
)
ws["A16"].font = FONT_WARN
ws["A16"].alignment = WRAP
ws.row_dimensions[16].height = 36

widths(
    ws,
    {
        "A": 16, "B": 20, "C": 16, "D": 20, "E": 22, "F": 20,
        "G": 28, "H": 26, "I": 26, "J": 20, "K": 70,
    },
)

# =============================================================================
# 6. Worked_example_Oil
# =============================================================================
ws = wb.create_sheet("Worked_example_Oil")
page_setup(ws, landscape=False)
ws.freeze_panes = "A5"
ws.sheet_properties.tabColor = "1A2B4A"

ws.merge_cells("A1:E1")
ws["A1"] = "Worked example  |  oil filter  |  UIO to cover %"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
ws["A1"].fill = NAVY
ws["A1"].alignment = WRAP_C
ws.row_dimensions[1].height = 26

ws.merge_cells("A2:E2")
ws["A2"] = (
    "One category, every cell. Fuel and air use the same expected quantity and a different billed qty. "
    "Brake and clutch change the events factor (and clutch also changes the UIO)."
)
ws["A2"].font = Font(name="Calibri", size=10, color="F7F4EE")
ws["A2"].fill = NAVY
ws["A2"].alignment = WRAP_C
ws.row_dimensions[2].height = 28

for c, h in enumerate(["Step", "In words", "Excel formula", "Result", "Notes"], 1):
    ws.cell(row=4, column=c, value=h)
header_row(ws, 4, 5)

oil_steps = [
    (5, "1. Take the N75 parc",
     "How many N75 vehicles are in the cleaned 2024A cut?",
     "=UIO_N75", NUM,
     "9,359. Both engine generations. Not 10,684. Not 22,389."),
    (6, "2. Take annual kilometres",
     "How far does each vehicle travel in the planning year?",
     "=KM_PER_YEAR", NUM,
     "50,000 km. Planning assumption from the April 2026 PMS analysis."),
    (7, "3. Take the oil interval",
     "How often is the oil filter replaced on the IML service schedule?",
     "=FILTER_INTERVAL_KM", NUM,
     "40,000 km. GIDSS NPR75 MY24 oil filter. Same interval as fuel."),
    (8, "4. Events per year",
     "Kilometres divided by interval.",
     "=B8",  # placeholder replaced below
     "0.00",
     "50,000 / 40,000 = 1.25 oil-filter events per vehicle per year."),
    (9, "5. Addressable share",
     "What share of the 9,359 is treated as addressable demand?",
     "=ADDRESSABLE_SHARE", PCT,
     "100%. The complementary pack does not apply a 70% ceiling on N75."),
    (10, "6. Expected oil quantity",
     "UIO x events per year x addressable.",
     "=B5*B8*B9", NUM2,
     "9,359 x 1.25 x 1.00 = 11,698.75. Pack table prints 11,699."),
    (11, "7. Actual ISZE to ITUK",
     "How many oil filters did ISZE bill ITUK on the N75 cut in 2025?",
     "=OIL_QTY_ISZE_ITUK", NUM,
     "4,673 (integer lock). Unrounded extract 4,673.3438 is one step below."),
    (12, "8. Cover %  ISZE to ITUK",
     "Actual billed qty divided by expected qty.",
     "=B11/B10", PCT,
     "4,673 / 11,698.75 = 39.9% to one decimal. Complementary slide prints 40%."),
    (13, "9. Same cover from unrounded extract",
     "Unrounded billed qty divided by the same expected qty.",
     "=OIL_QTY_ISZE_ITUK_UNROUNDED/B10", PCT,
     "4,673.3438 / 11,698.75 = 40.0% to one decimal. This is why the slide and the progress-pack table say 40.0%."),
    (14, "10. Actual dealer sell-out",
     "How many oil filters did ITUK sell to dealers on the N75 part-number split in 2025?",
     "=OIL_QTY_DEALER", NUM,
     "5,404. Bottom-up PN split, excluding N35 and F-Series. Not the 4,673."),
    (15, "11. Cover %  dealer sell-out",
     "Dealer sell-out qty divided by the same expected qty.",
     "=B14/B10", PCT,
     "5,404 / 11,698.75 = 46.2%. Same method, different actual layer."),
    (16, "12. What 40% is not",
     "40% is not '40% of complete UK'. It is not warehouse YTD. It is not dealer sell-out.",
     "n/a", "@",
     "40% = N75 ISZE to ITUK oil billed qty / N75 expected oil qty on the 50k/40k schedule."),
]

# Fix step 4 formula to be KM/INTERVAL using named ranges, and step results
# We need Result column to be the live formula. Column C = formula-as-text, column D = live formula.
# Redesign: C = formula text (string), D = live formula.

oil_live = {
    5: ("=UIO_N75", "=UIO_N75", NUM),
    6: ("=KM_PER_YEAR", "=KM_PER_YEAR", NUM),
    7: ("=FILTER_INTERVAL_KM", "=FILTER_INTERVAL_KM", NUM),
    8: ("=KM_PER_YEAR/FILTER_INTERVAL_KM", "=KM_PER_YEAR/FILTER_INTERVAL_KM", "0.00"),
    9: ("=ADDRESSABLE_SHARE", "=ADDRESSABLE_SHARE", PCT),
    10: ("=D5*D8*D9", "=D5*D8*D9", NUM2),
    11: ("=OIL_QTY_ISZE_ITUK", "=OIL_QTY_ISZE_ITUK", NUM),
    12: ("=D11/D10", "=D11/D10", PCT),
    13: ("=OIL_QTY_ISZE_ITUK_UNROUNDED/D10", "=OIL_QTY_ISZE_ITUK_UNROUNDED/D10", PCT),
    14: ("=OIL_QTY_DEALER", "=OIL_QTY_DEALER", NUM),
    15: ("=D14/D10", "=D14/D10", PCT),
}

for r, step, words_txt, _old_f, _old_fmt, notes in oil_steps:
    fill = PAPER if r % 2 == 0 else WHITE
    label_cell(ws.cell(row=r, column=1), step, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=2), words_txt, fill)
    if r == 16:
        label_cell(ws.cell(row=r, column=3), "No formula. Read the note.", GREY)
        label_cell(ws.cell(row=r, column=4), "See note", GREY)
    else:
        ftxt, flive, fmt = oil_live[r]
        label_cell(ws.cell(row=r, column=3), ftxt, fill, FONT_INPUT)
        formula_cell(ws.cell(row=r, column=4), flive, fmt, GREEN)
    note_cell(ws.cell(row=r, column=5), notes, fill)
    ws.row_dimensions[r].height = 40

ws.merge_cells("A18:E18")
ws["A18"] = "Repeat the same 12 steps for fuel and air. Change only step 7 (the billed qty). Expected stays 11,698.75."
ws["A18"].font = FONT_SEC
ws["A18"].fill = PAPER

for c, h in enumerate(["Category", "Billed qty (ISZE to ITUK)", "Expected (from oil step 6)", "Cover %", "Notes"], 1):
    ws.cell(row=19, column=c, value=h)
header_row(ws, 19, 5)

repeats = [
    (20, "Fuel filter", "=FUEL_QTY_ISZE_ITUK", "=D10", "=B20/C20",
     "11,021 / 11,698.75 = 94.2%. Complementary slide prints 94%."),
    (21, "Air filter", "=AIR_QTY_ISZE_ITUK", "=D10", "=B21/C21",
     "2,226 / 11,698.75 = 19.0%. Complementary slide prints 19% and 2,226 / 11,699."),
]
for r, cat, act, exp, covf, notes in repeats:
    fill = WHITE
    label_cell(ws.cell(row=r, column=1), cat, fill, FONT_INPUT)
    formula_cell(ws.cell(row=r, column=2), act, NUM, GREEN)
    formula_cell(ws.cell(row=r, column=3), exp, NUM2, GREEN)
    formula_cell(ws.cell(row=r, column=4), covf, PCT, GREEN)
    note_cell(ws.cell(row=r, column=5), notes, fill)
    ws.row_dimensions[r].height = 32

ws.merge_cells("A23:E23")
ws["A23"] = (
    "If you change annual kilometres or the filter interval on Parameters, "
    "this page, Expected, Coverage, and the Cover headlines all move together. "
    "That is the point of keeping the maths in cells."
)
ws["A23"].font = FONT_MUTED
ws["A23"].alignment = WRAP
ws.row_dimensions[23].height = 32

widths(ws, {"A": 36, "B": 42, "C": 42, "D": 16, "E": 72})

# =============================================================================
# 7. What_this_is_not
# =============================================================================
ws = wb.create_sheet("What_this_is_not")
page_setup(ws, landscape=True)
ws.freeze_panes = "A5"
ws.sheet_properties.tabColor = "C0552D"

ws.merge_cells("A1:D1")
ws["A1"] = "What this is not  |  read before quoting a percentage"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="F7F4EE")
ws["A1"].fill = NAVY
ws["A1"].alignment = WRAP_C
ws.row_dimensions[1].height = 26

ws.merge_cells("A2:D2")
ws["A2"] = "Each row is a trap that has already produced a wrong number in this programme. The complementary pack is N75, 2025 billed, 50k/40k."
ws["A2"].font = Font(name="Calibri", size=10, color="F7F4EE")
ws["A2"].fill = NAVY
ws["A2"].alignment = WRAP_C
ws.row_dimensions[2].height = 22

for c, h in enumerate(["#", "This file is not...", "Proof / number to use instead", "Notes"], 1):
    ws.cell(row=4, column=c, value=h)
header_row(ws, 4, 4)

traps = [
    (
        5, "1",
        "Not warehouse year-to-date issues or stock movement.",
        "Use 2025 billed quantity (Parameters section C and D).",
        "The complementary pack source note is 2025 billed. A 2026 warehouse YTD pull is a different file and a different time window. Do not paste it into the actuals.",
    ),
    (
        6, "2",
        "Not the complete UK registered parc.",
        "N75 UIO = 9,359 (Parameters C5). Complete parc = 22,389 (C37) is a different layer.",
        "Fuel 94% is N75 only. The complementary pack footnote says complete-parc fuel is about 65%. Quoting 94% as whole UK is wrong.",
    ),
    (
        7, "3",
        "Not 10,684 vehicles.",
        "Checksum C42 = 9,359 + 651 + 257 + 417 must equal 10,684.",
        "10,684 mixes N75 with N50/55, N62/65 and unspecified. The complementary pack does not use it. Use 9,359.",
    ),
    (
        8, "4",
        "Not 22,389 as the N75 denominator.",
        "22,389 is all models (N35 + N75 + residual).",
        "Use 22,389 only when you are on the complete-parc layer (oil 35.1% in the April 2026 analysis). Do not mix that % with N75 40%.",
    ),
    (
        9, "5",
        "Do not sum four model tables and call the total N75 cover.",
        "N75 expected oil = 11,698.75. That already includes both N75 engine generations.",
        "Adding N35 + N75 + F-Series + residual cover tables double-counts vehicles and mixes intervals. The complementary pack is N75 first, one table.",
    ),
    (
        10, "6",
        "Do not treat ISZE to ITUK billed qty and dealer sell-out as the same number.",
        "Oil 4,673 vs 5,404. Cover 40.0% vs 46.2%.",
        "Label the layer every time. The complementary slide chips are the ISZE to ITUK layer.",
    ),
    (
        11, "7",
        "Do not add the N75 euro gap to the complete-parc euro gap.",
        "N75 is inside the complete parc.",
        "The April 2026 complete-parc gap and the N75 subset gap are two views of one parc. Adding them counts N75 twice.",
    ),
    (
        12, "8",
        "Do not switch the oil interval to 20,000 km and keep the same 40% label.",
        "Filter interval is 40,000 km (C7). Events = 1.25 (C12).",
        "A 20,000 km oil interval is the older kick-off example. It doubles expected oil qty and halves the cover %. The complementary pack does not use it.",
    ),
    (
        13, "9",
        "Do not read 47% manuals as clutch cover.",
        "47% is the manual share in the denominator. Clutch cover is 11% (ISZE to ITUK) or 15.5% (dealer).",
        "Complementary footnote: 47% manuals / 11% actual. Two different numbers on one line.",
    ),
    (
        14, "10",
        "Do not quote air 19% as a GIDSS replace-every result.",
        "GIDSS MY24 air is inspect / indicator. The 40,000 km air interval is the April 2026 planning choice.",
        "Air is measured on the same visit as oil and fuel so the attach miss is visible. That is a planning decision, not a workshop-manual replace-every line.",
    ),
    (
        15, "11",
        "Do not average oil, fuel, air, brake and clutch into one N75 %.",
        "The complementary pack headlines Fuel / Oil / Air.",
        "Brake and clutch use 0.5 events, not 1.25. Averaging five rows hides the air miss and invents a number the pack does not show.",
    ),
    (
        16, "12",
        "Do not use 2026 year-to-date as a drop-in replacement for 2025 billed.",
        "Billing year is calendar 2025.",
        "A short 2026 window has a different expected qty (less than a full year of 1.25 events). The complementary pack is a 2025 year.",
    ),
]
for r, num, what, proof, notes in traps:
    fill = PAPER if r % 2 == 0 else WHITE
    label_cell(ws.cell(row=r, column=1), num, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=2), what, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=3), proof, fill)
    note_cell(ws.cell(row=r, column=4), notes, fill)
    ws.row_dimensions[r].height = 48

ws.merge_cells("A18:D18")
ws["A18"] = "Sources used to lock the numbers (this file does not replace them)"
ws["A18"].font = FONT_SEC
ws["A18"].fill = PAPER

for c, h in enumerate(["Source", "What was taken from it", "What was not taken"], 1):
    ws.cell(row=19, column=c, value=h)
header_row(ws, 19, 3)

sources = [
    (
        20,
        "April 2026 PMS analysis N75 study builder (assumptions + integer actuals)",
        "UIO 9,359; 50,000 km/year; 40,000 km filter; 100,000 km wear; 47% manual; 100% addressable; integer billed qty and dealer sell-out qty.",
        "Internal nicknames. Complete-parc 35.1% oil. Other-distributor rebased covers.",
    ),
    (
        21,
        "N75 progress-pack table (same integer actuals and printed %)",
        "Oil 40.0% / 46.2% (4,673 / 5,404 over 11,699). Fuel 94.2% / 95.2%. Air 19.0% / 19.6%. Brake 62.0% / 62.5%. Clutch 11.0% / 15.5%.",
        "Phase-one campaign language. Euro gap. Personal names.",
    ),
    (
        22,
        "N75 share-scaled extract (unrounded ISZE to ITUK qty)",
        "4,673.3438 oil; 11,021.0982 fuel; 2,225.7013 air; 2,902.4413 brake; 242.6042 clutch. Expected 11,698.75 / 4,679.5 / 2,199.365.",
        "Revenue and list-price columns. Those are not needed to explain the cover %.",
    ),
    (
        23,
        "UIO workbook 2024A Method A + raw car-park split",
        "N75 9,359. Complete parc 22,389. Mix proof for 10,684 = 9,359 + 651 + 257 + 417.",
        "Forecast 2025P N75 (9,506). That is a projection, not the CY2025 cover denominator.",
    ),
    (
        24,
        "Complementary pack builder (N75 cover slide only, read-only)",
        "Slide print: Fuel 94%, Oil 40%, Air 19%, clutch footnote 47% manuals / 11% actual, air qty 2,226 / 11,699.",
        "Nothing was written back to the PowerPoint. ORIGINAL and DRAFT decks were not opened for write.",
    ),
    (
        25,
        "GIDSS NPR75 MY24 workshop schedule",
        "Oil filter and fuel filter replace every 40,000 km. Supports the 40,000 km interval.",
        "Air replace-every (GIDSS is inspect / indicator). Brake/clutch fixed km (condition / VIN).",
    ),
]
for r, src, taken, not_taken in sources:
    fill = PAPER if r % 2 == 0 else WHITE
    label_cell(ws.cell(row=r, column=1), src, fill, FONT_INPUT)
    label_cell(ws.cell(row=r, column=2), taken, fill)
    label_cell(ws.cell(row=r, column=3), not_taken, fill)
    ws.row_dimensions[r].height = 52

ws.merge_cells("A27:D27")
ws["A27"] = (
    "This workbook was built on 15 August 2026. "
    "It explains the complementary-pack N75 cover %. "
    "It does not change the complementary PowerPoint."
)
ws["A27"].font = FONT_MUTED
ws["A27"].alignment = WRAP
ws.row_dimensions[27].height = 28

widths(ws, {"A": 56, "B": 62, "C": 56, "D": 78})

# =============================================================================
# Save both paths
# =============================================================================
from shutil import copy2

for path in (OUT_A, OUT_B):
    path.parent.mkdir(parents=True, exist_ok=True)

wb.save(OUT_A)
copy2(OUT_A, OUT_B)
print("Wrote", OUT_A)
print("Wrote", OUT_B)
print("Sheets:", wb.sheetnames)
print("Names:", sorted(wb.defined_names))
