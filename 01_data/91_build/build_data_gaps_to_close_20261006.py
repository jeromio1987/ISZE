"""
Build ISZE_Data_Gaps_To_Close_2026-10-06.xlsx  (filterable edition)

Uniformizes the data-integrity sources into two filterable lists:
  List 1 = data we are missing from outside ISZE
  List 2 = data we must fix or decide inside ISZE

Filtering: Excel AutoFilter on the header row of both sheets, so every column
(Region, Country, Distributor, Category, Priority, Status) gets a dropdown.
One row per country / distributor so a country filter returns a clean result.
A "By country" sheet counts open items per country with COUNTIFS.

Sources read 2026-10-06 (read-only):
  01_data/00_derived/_data_integrity_open_issues.md            (register, 2026-09-24)
  02_dashboards/ops/ISZE_Data_Integrity_Contacts.html          (2026-09-22)
  03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md
  09_meetings/*_Operating_Dashboard_*/DATA_INTEGRITY.md
  09_meetings/WARRANTY_DATA_ASKS_2026-08-18.md
  01_data/12_raw/dealer_sales/SELLOUT_COVERAGE_ASKS.md         (2026-09-03)
  00_docs/ISZE_OS_DATA_MAP.yaml  asks table
  09_meetings/PETROS_Sales_Review_2026/NOTES_MINUTES_2026-08-06.md
  01_data/14_dashboards/tender_data.json meta                  (2026-10-05)
  01_data/90_INBOX/_shimauchi_mileage_20261006/                (mail 2026-10-06 07:15)

No source file is modified. Writes one workbook.
"""

from __future__ import annotations

import calendar
import json
import math
import os
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("GAPS_OUT", ROOT / "01_data" / "11_planning" / "ISZE_Data_Gaps_To_Close_2026-10-06.xlsx"))

NAVY = "15233C"
TERRA = "C0552D"
PAPER = "F7F4EE"
ROW_ALT = "FAF8F4"
INK = "222222"
BAND = "EEF3F9"
HIGH_FILL = "FBE3DA"
MED_FILL = "FFF6E0"
LOW_FILL = "F1F1EE"

# Column layout shared by both list sheets.
# Country sits in column B so the country filter is the first thing he reaches.
HEADERS = [
    "#",
    "Country",
    "Region",
    "Distributor / scope",
    "Category",
    "What we are missing",
    "Who to ask",
    "Why it matters / what it blocks",
    "Priority",
    "Status",
    "Reference",
]
WIDTHS = [4, 30, 14, 22, 17, 46, 26, 56, 10, 20, 24]

# ---------------------------------------------------------------------------
# List 1 - supplied by someone outside ISZE
#   (region, country, distributor, category, what, who, why, priority, status, ref)
# ---------------------------------------------------------------------------
LIST1 = [
    ("UK", "United Kingdom", "ITUK (trucks)", "Fleet / parc",
     "UK vehicle records: chassis, model, registration date, and odometer if available",
     "Toshiaki Shimauchi, ISZJ, with Duncan Young (ITUK)",
     "Duncan's 29,935-chassis list carries no odometer column, so the UK distance cannot be measured from it. "
     "This is the swing that moves UK oil-filter cover by about 35 points.",
     "High", "Promised - follow up", "Vehicle data request 2026-10-06"),

    ("Israel", "Israel", "UTI", "Fleet / parc",
     "Israel chassis-number pack: chassis, model and registration date",
     "Toshiaki Shimauchi, ISZJ, or the UTI contact",
     "The vehicle register holds 3,238 chassis numbers in seven small markets and deliberately excludes Israel "
     "and the UK. Without it there is no vehicle age and no model mix for Israel.",
     "High", "Promised - follow up", "VIN-IL"),

    ("Network", "Network", "All markets", "Fleet / parc",
     "Transmission map (automatic vs manual) for N and F series",
     "Toshiaki Shimauchi, ISZJ",
     "No measured manual-versus-automatic split exists, so the clutch share stays at the assumed 47%. "
     "Promised alongside the mileage tables on 6 October.",
     "Medium", "Promised - follow up", "Vehicle data request 2026-10-06"),

    ("Network", "Network", "All markets", "Fleet / parc",
     "Gross-weight data per market",
     "Toshiaki Shimauchi, ISZJ",
     "Needed to weight the fleet by weight class instead of the current per-market assumptions.",
     "Medium", "Promised - follow up", "Vehicle data request 2026-10-06"),

    ("Israel", "Israel", "UMI", "Sales to dealer",
     "Monthly report: part number x month x quantity, same shape as Israel's UTI monthly report",
     "UMI parts contact",
     "UMI is the largest market still missing (about EUR 11.0M of billed parts) and the top ask on the coverage "
     "list. Never blend with UTI. A draft request exists and has not been sent.",
     "High", "Draft ready - not sent", "Coverage asks rank 1"),

    ("Israel", "Israel", "UTI", "Sales to dealer",
     "The six missing monthly files for 2025: February to July",
     "UTI order desk (sap4 job)",
     "The month detail exists for January 2025 and August to December 2025 only. The 2025 annual total is "
     "still complete and safe to use, because the December file carries a year-to-date column - but do not "
     "add the months together, the annual row sits in the same file. 2026 runs January to June, then stops.",
     "Medium", "Partly missing", "Coverage by month / hunt 2026-09-03"),

    ("UK", "United Kingdom", "IUK (pickup)", "Sales to dealer",
     "Invoice-level detail, or at least a date per line - the file carries month columns only",
     "Isuzu UK pickup distributor",
     "The IUK file is a pivot: part number, then one column per month. There is no invoice date, so no day "
     "or week level and no recut on a different month boundary. Ireland and Portugal do send an invoice "
     "date; IUK does not.",
     "Low", "Limitation - not requested", "Coverage by month / DEALER_SELL_OUT.md"),

    ("DACH", "Germany", "ISD", "Sales to dealer",
     "Part number x month x quantity",
     "Isuzu Sales Deutschland",
     "The largest remaining market after UMI (about EUR 8.0M of billed parts). There is no sales-to-dealer file "
     "of any kind for Germany today.",
     "High", "Open", "Coverage asks rank 2"),

    ("Benelux", "Belgium", "Belgium", "Sales to dealer",
     "Part number x month x quantity",
     "Belgium distributor",
     "About EUR 6.7M of billed parts and no file today.",
     "High", "Open", "Coverage asks rank 3"),

    ("Nordics", "Norway", "RSA", "Sales to dealer",
     "Part number x month x quantity",
     "RSA (Norway)",
     "About EUR 4.1M of billed parts and no file today.",
     "Medium", "Open", "Coverage asks rank 5"),

    ("Nordics", "Sweden", "Isuzu Sverige", "Sales to dealer",
     "Part number x month x quantity",
     "Isuzu Sverige",
     "About EUR 3.5M of billed parts and no file today.",
     "Medium", "Open", "Coverage asks rank 6"),

    ("CEE", "Hungary", "Hungary", "Sales to dealer",
     "Part number x month x quantity",
     "Hungary distributor",
     "About EUR 1.2M of billed parts and no file today.",
     "Medium", "Open", "Coverage asks rank 9"),

    ("South EU", "Cyprus", "Cyprus", "Sales to dealer",
     "Part number x month x quantity",
     "Cyprus distributor",
     "About EUR 1.2M of billed parts and no file today.",
     "Low", "Open", "Coverage asks rank 8"),

    ("Nordics", "Finland", "Finland", "Sales to dealer",
     "Part number x month x quantity",
     "Finland distributor",
     "About EUR 0.8M of billed parts and no file today.",
     "Low", "Open", "Coverage asks rank 10"),

    ("CEE", "Romania", "Rom Auto", "Sales to dealer",
     "A 2025 file (the 2026 months to August already arrived)",
     "Robert Petrache, Isuzu Rom Auto",
     "Romania answered on 17 September with 2026 only, so it has no full year and cannot enter the 2025 layer.",
     "Low", "Partly received", "Coverage asks rank 11"),

    ("CEE", "Ukraine", "Ukraine", "Sales to dealer",
     "Part number x month x quantity",
     "Ukraine distributor",
     "About EUR 2.7M of billed parts, but Ukraine sits outside the 18-market spend-per-truck base by design, "
     "so the value to the main model is limited.",
     "Low", "Open", "Coverage asks rank 7"),

    ("Network", "Network", "All markets", "Warranty",
     "Pickup claim export for September 2026 onward, in the same ExportClaimAssessment format",
     "Georg Fischer, Isuzu Motors Germany",
     "Claims to August 2026 have already arrived and only need wiring on our side, so do not ask for May again. "
     "September onward is the next real gap. Do not re-ask December 2025 either.",
     "Medium", "Draft ready - not sent", "LCV-EXT"),

    ("Network", "Network", "All markets", "Warranty",
     "Why the share of claim lines with a blank part number differs so much by market",
     "Rene Paul, Isuzu Motors Germany",
     "95% blank in Czechia against 23% in Israel, 23% in Germany and 17% in Portugal. Part-level rankings from "
     "claims are weakest in the German-owned markets.",
     "Low", "Standing contact", "WARR-SAMPLE"),

    ("Israel", "Israel", "UMI", "Order behaviour",
     "Stock-order cut-off weekday, plus local week definition and timezone",
     "UMI order desk",
     "Without the cut-off we cannot mark an order on time or late. Several stock orders in one week are allowed "
     "in Israel and must not be scored as bad.",
     "Medium", "You collect", "ORDER-CUTOFF"),

    ("Israel", "Israel", "UTI", "Order behaviour",
     "Stock-order cut-off weekday, plus local week definition and timezone",
     "UTI order desk",
     "Same as UMI. Needed before any on-time ranking covers Israel.",
     "Medium", "You collect", "ORDER-CUTOFF"),

    ("Network", "Network", "Other distributors", "Order behaviour",
     "Stock-order cut-off weekday for every distributor outside Israel",
     "Each distributor's order desk",
     "The on-time ranking cannot extend past Israel until these are collected.",
     "Low", "You collect", "ORDER-CUTOFF"),

    ("Network", "Network", "All markets", "Billing / system",
     "A billing extract carrying the SaTy column for April to June 2026",
     "SAP extract owner",
     "That quarter had no SaTy column, so credit and return lines are identified by sign only and an unknown "
     "positive-value amount for one quarter may be un-netted.",
     "Medium", "Next extract", "CR/RE-FY26"),

    ("Network", "Network", "All markets", "Service intervals",
     "Dealer repair-order lines, or a parts basket by part number for oil, air, fuel and brakes (optional)",
     "A distributor or dealer group with workshop data",
     "Claims can never supply service intervals - a consumable replaced at a scheduled service is not a defect. "
     "8 oil-filter lines out of 33,416 truck claim lines. Until this exists the air and brake factors stay provisional.",
     "Low", "Optional chase", "WARR-NO-MAINT"),
]

# ---------------------------------------------------------------------------
# List 2 - produced or decided inside ISZE
# ---------------------------------------------------------------------------
LIST2 = [
    ("Network", "Network", "All markets", "Warranty",
     "Wire the May to August 2026 pickup claims into the fiscal-year and monthly files, and rebuild the pages",
     "ISZE build",
     "Already extracted (5,048 claim lines, EUR 1,078,462; EUR 929,438 of it outside MIDI) but nothing published "
     "reads it yet.",
     "High", "Extracted - not wired", "LCV-EXT"),

    ("Network", "Network", "All markets", "Warranty",
     "Pick one conversion basis for the pickup claim file and apply it everywhere",
     "Jerome - decision",
     "The same file becomes euro three ways that disagree: a year-average rate in the main table, a flat 163.7 "
     "elsewhere, and raw dollar sums with no conversion in the monthly file.",
     "High", "Decision needed", "LCV-CURRENCY-RULE"),

    ("MIDI (outside book)", "France, Italy, Spain, Switzerland", "MIDI", "Warranty",
     "Confirm MIDI stays out of the ISZE warranty context, and make the filter explicit",
     "Jerome - decision",
     "MIDI is about a seventh of the pickup claim file (EUR 446,354) yet is not an ISZE spend-per-truck "
     "distributor. It is excluded by accident today, not by rule.",
     "Medium", "Decision needed", "MIDI-WARR"),

    ("Network", "Network", "All markets", "Spend per truck",
     "Rebuild the 2026 spend-per-truck rows from a dated extract, or drop 2026 from that file",
     "ISZE build",
     "The 2026 rows carry partial-year sales against a full-year maximum, which reads as a 43% collapse that did "
     "not happen (first half 2026 parts are actually up 12%).",
     "High", "Open", "SPU-PARTIAL"),

    ("Network", "Network", "All markets", "Fleet / parc",
     "Rebuild the 2026-2030 vehicles-in-service forecast",
     "UIO model owner",
     "A survival-curve mismatch at the 2025/2026 boundary makes 2026 9% too high, rising to 59% by 2030, while "
     "Israel is about 25% low. Every figure that divides spend by the fleet inherits this.",
     "High", "Do not quote until rebuilt", "UIO-FCAST"),

    ("Israel", "Israel", "UMI", "Verification",
     "Bring the UMI source files inside the green verification set - re-run the verifier",
     "ISZE build",
     "Four of UMI's main sources sit outside the green report, so the main numerator has never been through "
     "the verifier.",
     "Medium", "Open", "UMI check 10"),

    ("Greece", "Greece", "Petros", "Fleet / parc",
     "Ask the distributor to check the vehicles-in-service figure we model for them",
     "Jerome with Sales",
     "Agreed at the Greece review on 6 August: their fleet reads +5.1% and needs the Sales Department to confirm "
     "it, plus the mileage.",
     "Medium", "Open", "Petros minutes 2026-08-06"),

    ("Network", "Network", "Other markets", "Fleet / parc",
     "The same vehicles-in-service check for the remaining markets",
     "Jerome with Sales",
     "Same gap as Greece. No other market has had the model's fleet figure checked with the distributor.",
     "Low", "Open", "Petros minutes 2026-08-06"),

    ("Israel", "Israel", "UTI", "Sales to dealer",
     "Find or chase the missing monthly parts reports: February to July 2025, and July 2026",
     "ISZE - check the mailbox, then chase",
     "A hunt of Inbox, Sent and Archive on 3 September found them nowhere, so UTI's 2025 is not a complete year.",
     "Medium", "Open", "Sales-to-dealer hunt 2026-09-03"),

    ("Network", "Network", "All markets", "Service intervals",
     "Confirm the air-filter and brake factors, or keep them labelled provisional",
     "Jerome / IML confirmation",
     "Air filter 0.5 is provisional pending IML; brake pad and shoe 0.5 are described as an unsourced guess in "
     "their own note; brake rotor 0.25 is unconfirmed.",
     "Medium", "Open", "Integrity flag C"),

    ("Network", "Network", "All markets", "Requests not sent",
     "Send the claims request to Georg Fischer",
     "Jerome - send",
     "Written 18 August, still a draft. Every unsent draft keeps a gap waiting on nobody.",
     "High", "Draft ready - not sent", "WARRANTY_DATA_ASKS"),

    ("Israel", "Israel", "UMI", "Requests not sent",
     "Send the UMI sales-to-dealer request",
     "Jerome - send",
     "Written 25 August, still a draft. UMI is the top coverage gap at about EUR 11.0M of billed parts.",
     "High", "Draft ready - not sent", "Draft UMI 2026-08-25"),

    ("Network", "Network", "All markets", "Requests not sent",
     "Send the air-to-oil replacement ratio question to Japan",
     "Jerome - send",
     "Written 18 August to Suzuki san, still a draft. That one number replaces the provisional air factor.",
     "Medium", "Draft ready - not sent", "WARRANTY_DATA_ASKS"),

    ("Network", "Network", "All markets", "Requests not sent",
     "Send the interval cut-off question to Thailand",
     "Jerome - send",
     "Written 18 August to IMIT, still a draft. Without the cut-offs the pickup fleet cannot be weighted "
     "15,000 against 20,000 km.",
     "Medium", "Draft ready - not sent", "WARRANTY_DATA_ASKS"),

    ("Network", "Network", "All markets", "Tender",
     "Fill the missing tender fields and refresh the copy the dashboards read",
     "ISZE build",
     "The feed is live (last run 5 October, 654 opportunities) but 498 notices have no deadline, 612 no value, "
     "471 no lifecycle, and the copy the dashboards read is 32 days old.",
     "Medium", "Open", "Tender data 2026-10-05"),

    ("UK", "United Kingdom", "ITUK (trucks)", "Reconciliation",
     "Reconcile the pipeline against the older v9 sales file",
     "ISZE build",
     "ITUK reads 3.6% below the v9 sales file in the automatic audit.",
     "Low", "Open", "GPS integrity audit"),

    ("Ireland", "Ireland", "Ireland", "Reconciliation",
     "Reconcile the pipeline against the older v9 sales file",
     "ISZE build",
     "Ireland reads 2.2% below the v9 sales file in the automatic audit.",
     "Low", "Open", "GPS integrity audit"),

    ("Israel", "Israel", "UTI", "Reconciliation",
     "Reconcile the pipeline against the older v9 sales file",
     "ISZE build",
     "UTI reads 2.1% below the v9 sales file in the automatic audit.",
     "Low", "Open", "GPS integrity audit"),

    ("Israel", "Israel", "UMI", "Reconciliation",
     "Reconcile the pipeline against the older v9 sales file",
     "ISZE build",
     "UMI reads 2.0% below the v9 sales file in the automatic audit.",
     "Low", "Open", "GPS integrity audit"),

    ("Nordics", "Finland", "Finland", "Reconciliation",
     "Reconcile the pipeline against the older v9 sales file",
     "ISZE build",
     "Finland reads 2.8% below the v9 sales file in the automatic audit.",
     "Low", "Open", "GPS integrity audit"),

    ("Nordics", "Iceland", "Iceland", "Reconciliation",
     "Reconcile the pipeline against the older v9 sales file",
     "ISZE build",
     "Iceland reads 2.3% below the v9 sales file in the automatic audit.",
     "Low", "Open", "GPS integrity audit"),
]

# Country order for the summary sheet: his book first, then network, then outside.
SUMMARY_COUNTRIES = [
    ("United Kingdom", "UK"),
    ("Ireland", "Ireland"),
    ("Israel", "Israel"),
    ("Greece", "South EU"),
    ("Germany", "DACH"),
    ("Belgium", "Benelux"),
    ("Norway", "Nordics"),
    ("Sweden", "Nordics"),
    ("Finland", "Nordics"),
    ("Iceland", "Nordics"),
    ("Hungary", "CEE"),
    ("Romania", "CEE"),
    ("Ukraine", "CEE"),
    ("Cyprus", "South EU"),
    ("France, Italy, Spain, Switzerland", "MIDI (outside book)"),
    ("Network", "Network"),
]


def _thin():
    return Side(style="thin", color="D9D3C8")


def _title(ws, text, note, ncols, note_height=54):
    ws.sheet_view.showGridLines = False
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(row=1, column=1, value=text)
    c.font = Font(name="Georgia", size=15, bold=True, color=NAVY)
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 26

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    n = ws.cell(row=2, column=1, value=note)
    n.font = Font(name="Calibri", size=9.5, color="5D564B")
    n.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = note_height
    ws.row_dimensions[3].height = 6


def _header(ws, headers, row=4):
    th = _thin()
    for i, h in enumerate(headers, start=1):
        hc = ws.cell(row=row, column=i, value=h)
        hc.font = Font(name="Calibri", size=10.5, bold=True, color=PAPER)
        hc.fill = PatternFill("solid", fgColor=NAVY)
        hc.alignment = Alignment(wrap_text=True, vertical="center")
        hc.border = Border(bottom=th)
    ws.row_dimensions[row].height = 30


def _priority_fill(p):
    if p == "High":
        return HIGH_FILL
    if p == "Medium":
        return MED_FILL
    return LOW_FILL


def _write_rows(ws, rows, widths, start_row=5):
    """rows are (region, country, distributor, category, what, who, why, priority, status, ref).
    The sheet order is: #, Country, Region, Distributor, Category, What, Who, Why, Priority, Status, Ref.
    """
    th = _thin()
    r = start_row
    for idx, row in enumerate(rows, start=1):
        region, country, distributor, category, what, who, why, priority, status, ref = row
        cells = [idx, country, region, distributor, category, what, who, why, priority, status, ref]
        for i, val in enumerate(cells, start=1):
            dc = ws.cell(row=r, column=i, value=val)
            dc.font = Font(name="Calibri", size=10, color=INK)
            dc.alignment = Alignment(wrap_text=True, vertical="top")
            dc.border = Border(bottom=th)
            if idx % 2 == 0:
                dc.fill = PatternFill("solid", fgColor=ROW_ALT)
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="top")
        # Country and distributor tinted so they read as the filter keys.
        for c in (2, 3, 4):
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=BAND)
        # Priority cell: tinted and centred, so the colour reads at a glance.
        pc = ws.cell(row=r, column=9)
        pc.fill = PatternFill("solid", fgColor=_priority_fill(priority))
        pc.alignment = Alignment(horizontal="center", vertical="top")
        pc.font = Font(name="Calibri", size=10, bold=priority == "High", color=INK)

        # Row height from the longest wrapped cell, so print/PDF does not clip.
        lines = 1
        for i, val in enumerate(cells, start=1):
            text = str(val)
            chars_per_line = max(int(widths[i - 1] * 1.05), 8)
            wrapped = 0
            for para in text.split("\n"):
                wrapped += max(1, -(-len(para) // chars_per_line))
            lines = max(lines, wrapped)
        ws.row_dimensions[r].height = round(lines * 13.2 + 5, 1)
        r += 1
    return r - 1


def _finish(ws, widths, first_data_row, last_data_row, ncols):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    last_col = get_column_letter(ncols)
    # AutoFilter: dropdown on every column, which is the "filter by country" ask.
    ws.auto_filter.ref = f"A4:{last_col}{last_data_row}"
    ws.freeze_panes = f"C{first_data_row}"
    ws.print_title_rows = "4:4"
    ws.print_area = f"A1:{last_col}{last_data_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def _read_me(wb):
    ws = wb.active
    ws.title = "Read me"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 104

    ws.merge_cells("A1:B1")
    c = ws.cell(row=1, column=1, value="Data gaps - what we are missing, and who is on it")
    c.font = Font(name="Georgia", size=16, bold=True, color=NAVY)
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:B2")
    s = ws.cell(row=2, column=1, value=(
        "Two lists, built 6 October 2026 from every data-integrity source in the workspace. "
        "Pipeline checks are green: 164 pass, 1 warning, 0 fail."
    ))
    s.font = Font(name="Calibri", size=10, color="5D564B")
    s.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 30

    rows = [
        ("How to filter", "Click any cell in row 4 of either list, then Data > Filter (already switched on). "
                          "Every column gets a dropdown: Region, Country, Distributor, Category, Priority, Status. "
                          "To see one country, drop down Country and tick it."),
        ("Sheet 1 - Missing from others", "What has to come from outside ISZE. One row per country or distributor, "
                                          "so a country filter returns a clean result."),
        ("Sheet 2 - Ours to fix", "What we produce or decide ourselves. Nothing here waits on an external party."),
        ("Sheet 3 - Coverage by month", "Sales to dealer, market by market: which months we hold (X) and which "
                                        "are missing (pink), plus the grain and the time detail each source file "
                                        "carries. Read from the files, so it follows the data."),
        ("Sheet 4 - By country", "Count of open items per country, split external against internal, with a "
                                 "priority count. Live formulas, so it follows edits."),
        ("Priority", "High = changes a published number now. Medium = important, not blocking today. "
                     "Low = optional or long tail."),
        ("Category", "Sales to dealer, Warranty, Fleet / parc, Order behaviour, Spend per truck, Service intervals, "
                     "Billing / system, Verification, Reconciliation, Requests not sent, Tender."),
        ("Three things to know", "Sales to dealer already exists for eight markets - the rows below are what is "
                                 "still missing. UTI is missing six months of 2025 but its annual total is complete. "
                                 "Tender data is not missing: the feed is live, the quality inside it is the gap."),
        ("Source", "01_data/00_derived/_data_integrity_open_issues.md (24 Sep), the contact page (22 Sep), the PRISM "
                   "flag list (28 May), the per-country packs, the warranty asks (18 Aug), the sales-to-dealer "
                   "coverage list (3 Sep), the OS data map asks, the Petros minutes (6 Aug), the tender feed "
                   "(5 Oct) and this morning's Isuzu Japan mileage mail (6 Oct)."),
    ]
    r = 4
    for k, v in rows:
        kc = ws.cell(row=r, column=1, value=k)
        kc.font = Font(name="Calibri", size=10.5, bold=True, color=NAVY)
        kc.alignment = Alignment(vertical="top", wrap_text=True)
        vc = ws.cell(row=r, column=2, value=v)
        vc.font = Font(name="Calibri", size=10, color=INK)
        vc.alignment = Alignment(vertical="top", wrap_text=True)
        ws.row_dimensions[r].height = max(28, round((-(-len(v) // 100)) * 13.5 + 6, 1))
        r += 1
    ws.freeze_panes = "A4"
    return ws


def _read_coverage():
    """Read the derived sales-to-dealer long files and return market -> set of months present.

    Reading the files (not a hand-typed list) is what keeps this sheet honest: if a month
    arrives later, the grid follows.
    """
    import csv
    import glob

    market_months: dict[str, set] = {}
    market_files: dict[str, list] = {}
    for path in sorted(glob.glob(str(ROOT / "01_data" / "00_derived" / "dealer_sellout_long_*.csv"))):
        stem = Path(path).stem.replace("dealer_sellout_long_", "")
        key = stem.split("_CY")[0]
        months = market_months.setdefault(key, set())
        market_files.setdefault(key, []).append(stem)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                per = (row.get("period") or "").strip()
                if (row.get("period_grain") or "").strip() == "month" and len(per) == 7:
                    months.add(per)
    return market_months, market_files


# Display name, distributor, segment, what time detail the source carries.
COVERAGE_META = {
    "ITUK":         ("United Kingdom", "ITUK (trucks)", "CV",
                     "Month columns per part number, at dealer grain", "Month only - no invoice date"),
    "ITUK_network": ("United Kingdom", "ITUK (network grain file)", "CV",
                     "Month columns per part number, network total", "Month only - no invoice date"),
    "IUK":          ("United Kingdom", "IUK (pickup)", "LCV",
                     "Month columns per part number", "Month only - no invoice date"),
    "IRELAND":      ("Ireland", "Isuzu Ireland (Harris)", "LCV + CV",
                     "Line-level invoice/despatch rows", "InvoiceDate, OrderDate, DespatchDate"),
    "PORTUGAL":     ("Portugal", "I-Motors / Astara", "CV + LCV",
                     "Line-level rows with a date column", "Data da Fatura (invoice date)"),
    "GREECE":       ("Greece", "Petros (Petropoulos)", "LCV",
                     "Month columns per part number", "Month only - no invoice date"),
    "ROMANIA":      ("Romania", "Isuzu Rom Auto", "CV + LCV",
                     "One workbook per month, single sheet", "Period comes from the filename"),
    "UTI":          ("Israel", "UTI (Universal Trucks)", "CV",
                     "Month column plus a year-to-date column", "Month and YTD - no invoice date"),
}

COVERAGE_ORDER = ["ITUK", "ITUK_network", "IUK", "IRELAND", "PORTUGAL", "GREECE", "ROMANIA", "UTI"]


def _coverage(wb):
    market_months, market_files = _read_coverage()

    # Months shown: 2024-01 .. the latest month we hold, so the window follows the data.
    latest = max((m for s in market_months.values() for m in s), default="2026-08")
    end_y, end_m = int(latest[:4]), int(latest[5:7])
    months = []
    for y in range(2024, end_y + 1):
        for m in range(1, 13):
            tag = f"{y}-{m:02d}"
            if tag > latest:
                break
            months.append(tag)

    ws = wb.create_sheet("Coverage by month")
    ws.sheet_view.showGridLines = False

    headers = ["Market", "Distributor", "Segment"] + [
        f"{calendar.month_abbr[int(m[5:7])]}-{m[2:4]}" for m in months
    ] + [
        "Grain in file", "Time detail in file", "Source file(s)"
    ]
    ncols = len(headers)
    _title(
        ws,
        "Sales to dealer - which months we hold",
        "Read directly from the derived files on 6 October 2026, so it follows the data. X = month present. "
        "Pink = month absent. The 2024 columns are blank for markets whose first file is 2025 - that is not a gap, "
        "we never asked for 2024. Filter the Market or Distributor column with the dropdown in row 4.",
        ncols,
        note_height=44,
    )
    _header(ws, headers, row=4)

    th = _thin()
    r = 5
    for key in COVERAGE_ORDER:
        if key not in market_months:
            continue
        country, distributor, segment, grain, detail = COVERAGE_META.get(
            key, (key, key, "", "", "")
        )
        ws.cell(row=r, column=1, value=country).font = Font(name="Calibri", size=10, bold=True, color=NAVY)
        ws.cell(row=r, column=2, value=distributor).font = Font(name="Calibri", size=10, color=INK)
        ws.cell(row=r, column=3, value=segment).font = Font(name="Calibri", size=10, color=INK)
        present = market_months.get(key, set())
        for i, m in enumerate(months):
            cell = ws.cell(row=r, column=4 + i)
            if m in present:
                cell.value = "X"
                cell.font = Font(name="Calibri", size=9, bold=True, color="1F5C2E")
                cell.fill = PatternFill("solid", fgColor="E3F0E6")
            else:
                cell.fill = PatternFill("solid", fgColor="FBE3DA")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(bottom=th, left=Side(style="hair", color="E4DDD2"))
        c_grain = ws.cell(row=r, column=4 + len(months), value=grain)
        c_detail = ws.cell(row=r, column=5 + len(months), value=detail)
        files = sorted(set(market_files.get(key, [])))
        c_src = ws.cell(row=r, column=6 + len(months), value=", ".join(files))
        for c in (c_grain, c_detail, c_src):
            c.font = Font(name="Calibri", size=9, color=INK)
            c.alignment = Alignment(wrap_text=True, vertical="center")
        for cx in range(1, ncols + 1):
            cell = ws.cell(row=r, column=cx)
            if cell.border is None or not cell.border.bottom or cell.border.bottom.style is None:
                cell.border = Border(bottom=th)
        ws.row_dimensions[r].height = 30
        r += 1

    # Legend / notes under the grid.
    r += 1
    notes = [
        "UTI is the only market with month detail missing: February to July 2025, and July 2026 onward. "
        "Its 2025 annual total is still complete, because the December file carries a year-to-date column - "
        "and the annual row sits in the same file, so do not sum the months.",
        "Only Ireland and Portugal carry a real invoice date. IUK is a part-number pivot with one column per "
        "month, so there is no day or week level in it.",
        "Romania has no date inside the workbook either - the month is only knowable from the filename.",
        "Blank 2024 columns simply mean we never had a 2024 file for that market, not that it is missing.",
    ]
    for n in notes:
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
        nc = ws.cell(row=r, column=1, value=n)
        nc.font = Font(name="Calibri", size=9.5, color="5D564B")
        nc.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 26
        r += 1

    ws.column_dimensions["A"].width = 17
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 10
    for i in range(len(months)):
        ws.column_dimensions[get_column_letter(4 + i)].width = 5.2
    ws.column_dimensions[get_column_letter(4 + len(months))].width = 30
    ws.column_dimensions[get_column_letter(5 + len(months))].width = 30
    ws.column_dimensions[get_column_letter(6 + len(months))].width = 28

    last_col = get_column_letter(ncols)
    ws.auto_filter.ref = f"A4:{last_col}{4 + len(COVERAGE_ORDER) - 1}"
    ws.freeze_panes = f"D5"
    ws.print_title_rows = "4:4"
    ws.print_area = f"A1:{last_col}{r}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    return ws


def _summary(wb, n_ext: int, n_int: int):
    ws = wb.create_sheet("By country")
    _title(
        ws,
        "By country - how many open items",
        "Counts of the two lists by country. Live formulas, so they follow any edit. "
        "\"Network\" rows are asks that cover every market at once.",
        5,
        note_height=34,
    )
    _header(ws, ["Country", "Region", "Missing from others", "Ours to fix", "High priority"], row=4)
    ws.freeze_panes = "A5"

    ext_last = 4 + n_ext
    int_last = 4 + n_int
    r = 5
    for country, region in SUMMARY_COUNTRIES:
        ws.cell(row=r, column=1, value=country).font = Font(name="Calibri", size=10, bold=True, color=NAVY)
        ws.cell(row=r, column=2, value=region).font = Font(name="Calibri", size=10, color=INK)
        ws.cell(row=r, column=3, value=(
            f"=COUNTIF('1 Missing from others'!$B$5:$B${ext_last},$A{r})"
        ))
        ws.cell(row=r, column=4, value=(
            f"=COUNTIF('2 Ours to fix'!$B$5:$B${int_last},$A{r})"
        ))
        ws.cell(row=r, column=5, value=(
            f"=COUNTIFS('1 Missing from others'!$B$5:$B${ext_last},$A{r},"
            f"'1 Missing from others'!$I$5:$I${ext_last},\"High\")"
            f"+COUNTIFS('2 Ours to fix'!$B$5:$B${int_last},$A{r},'2 Ours to fix'!$I$5:$I${int_last},\"High\")"
        ))
        for cx in range(1, 6):
            cell = ws.cell(row=r, column=cx)
            cell.border = Border(bottom=_thin())
            cell.alignment = Alignment(vertical="center", wrap_text=True,
                                       horizontal="left" if cx <= 2 else "center")
            if cx >= 3:
                cell.font = Font(name="Calibri", size=11, bold=True, color=INK)
        ws.row_dimensions[r].height = 24
        r += 1

    # Total row
    ws.cell(row=r, column=1, value="Total").font = Font(name="Calibri", size=10.5, bold=True, color=PAPER)
    ws.cell(row=r, column=2, value="").font = Font(name="Calibri", size=10, color=PAPER)
    for cx in (1, 2):
        ws.cell(row=r, column=cx).fill = PatternFill("solid", fgColor=NAVY)
    for cx, col in ((3, "C"), (4, "D"), (5, "E")):
        tc = ws.cell(row=r, column=cx, value=f"=SUM({col}5:{col}{r - 1})")
        tc.font = Font(name="Calibri", size=11, bold=True, color=PAPER)
        tc.fill = PatternFill("solid", fgColor=NAVY)
        tc.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[r].height = 22

    for i, w in enumerate([34, 29, 19, 15, 14], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.print_area = f"A1:E{r}"
    ws.page_setup.orientation = "landscape"
    return ws


def main() -> None:
    wb = Workbook()

    note1 = (
        "Data we need from outside ISZE. One row per country or distributor. Filter any column with the dropdowns "
        "in row 4 - Country, Region, Distributor, Category, Priority, Status. Priority: High changes a published "
        "number now. Built 6 October 2026; pipeline checks green (164 pass, 1 warning, 0 fail)."
    )
    ws1 = wb.create_sheet("1 Missing from others")
    _title(ws1, "List 1 - Data we are missing from outside ISZE", note1, len(HEADERS))
    _header(ws1, HEADERS)
    last1 = _write_rows(ws1, LIST1, WIDTHS)
    _finish(ws1, WIDTHS, 5, last1, len(HEADERS))

    note2 = (
        "Ours to produce or decide. Nothing here waits on an external party. Same filters as List 1. "
        "The first rows are the ones that change a published number; the rest are wiring, a decision, or a "
        "request already written and not yet sent."
    )
    ws2 = wb.create_sheet("2 Ours to fix")
    _title(ws2, "List 2 - Data we must fix or decide inside ISZE", note2, len(HEADERS))
    _header(ws2, HEADERS)
    last2 = _write_rows(ws2, LIST2, WIDTHS)
    _finish(ws2, WIDTHS, 5, last2, len(HEADERS))

    _read_me(wb)
    _summary(wb, len(LIST1), len(LIST2))
    _coverage(wb)

    # Order the tabs: read me, list 1, list 2, coverage, by country.
    order = ["Read me", "1 Missing from others", "2 Ours to fix", "Coverage by month", "By country"]
    wb._sheets = [wb[n] for n in order]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT}")
    print(f"  List 1: {len(LIST1)} rows")
    print(f"  List 2: {len(LIST2)} rows")
    countries = sorted({r[1] for r in LIST1} | {r[1] for r in LIST2})
    print(f"  distinct countries: {len(countries)}")


if __name__ == "__main__":
    main()
