"""
GPS Refinement Maturity Matrix v2 — populated with safe defaults.

Pre-fill strategy:
  - Axis A (UIO): hard values from current ISZE methodology / v17 Data Sources.
  - Axis B (Sales): 0 for all (default: only ISZE→distributor visible) except
    ITUK=1 (confirmed sales-out via Niguri file).
  - Axis C (PMS): 0 for all except ITUK=1 (Apr 2026 PMS study confirmed).
  - Axis D (Pricing): 0 for all by default; ITUK=2 (BVP + competitive PR00 work
    documented). Mark all as GUESS unless confirmed.
  - Axis E (Warranty): 1 for all (warranty parts flagged in SAP for every
    sold_to, but not consistently excluded from GPS).

Confidence labels per cell:
  CONFIRMED — sourced from v17 Data Sources or directly confirmed
  GUESS     — inferred from typical distributor relationships
  DEFAULT   — safe baseline (lowest plausible value until owner confirms)

Targets are one step above current (where realistic). Owner overrides any cell.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\UIO\Ireland_SIMI_Comparison\ISZE_GPS_DataMaturity_Matrix_2026-05-28.xlsx")

# Per-distributor pre-fill.
# Tuple: (code, country, scope, A_cur, A_conf, B_cur, B_conf, C_cur, C_conf, D_cur, D_conf, E_cur, E_conf,
#         A_tgt, B_tgt, C_tgt, D_tgt, E_tgt)
D = [
    ("ITUK",     "United Kingdom",   "CV (N-series + F-Series)",
        2, "CONFIRMED",  1, "CONFIRMED",  1, "CONFIRMED",  2, "CONFIRMED",  1, "DEFAULT",
        2, 2, 2, 3, 2),
    ("IUK",      "United Kingdom",   "LCV (D-Max)",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    1, "GUESS",      1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("UTI",      "Israel",            "CV trucks (LD + MD)",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("UMI",      "Israel",            "LCV (D-Max)",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("IRELAND",  "Ireland",           "CV + LCV",
        2, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("BELGIUM",  "Belgium (Benelux)", "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("GERMANY",  "Germany",           "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("PORTUGAL", "Portugal + Azores", "CV (LD + F-Series) + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("SWEDEN",   "Sweden",            "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("NORWAY",   "Norway",            "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("DENMARK",  "Denmark",           "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("FINLAND",  "Finland",           "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("ICELAND",  "Iceland",           "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("GREECE",   "Greece",            "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("CYPRUS",   "Cyprus",            "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("MALTA",    "Malta",             "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("ROMANIA",  "Romania",           "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
    ("HUNGARY",  "Hungary",           "CV + LCV",
        1, "CONFIRMED",  0, "DEFAULT",    0, "DEFAULT",    0, "DEFAULT",    1, "DEFAULT",
        2, 1, 1, 2, 2),
]

wb = openpyxl.Workbook()
wb.remove(wb.active)

BLUE = PatternFill("solid", fgColor="1F4E78")
NAVY = PatternFill("solid", fgColor="2E75B6")
GREY = PatternFill("solid", fgColor="D9D9D9")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
ORANGE = PatternFill("solid", fgColor="FCE4D6")
RED0 = PatternFill("solid", fgColor="F8CBAD")
AMBER = PatternFill("solid", fgColor="FFEB9C")
GREEN = PatternFill("solid", fgColor="E2EFDA")
GREEN3 = PatternFill("solid", fgColor="C6EFCE")
WHITE_BOLD = Font(bold=True, color="FFFFFF")
BOLD = Font(bold=True)
ITALIC_GREY = Font(italic=True, color="595959")
ITALIC_RED = Font(italic=True, color="C00000")
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

LEVEL_FILL = {0: RED0, 1: AMBER, 2: GREEN, 3: GREEN3}
CONF_FONT = {
    "CONFIRMED": Font(bold=True, color="2E7D32"),
    "GUESS": Font(italic=True, color="E65100"),
    "DEFAULT": Font(italic=True, color="595959"),
}

def style_header(ws, row, n):
    for c in range(1, n + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = BLUE; cell.font = WHITE_BOLD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER

def autosize(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

# ============================================================
# Sheet 1: Framework
# ============================================================
ws = wb.create_sheet("Framework")
ws["A1"] = "GPS Refinement Maturity Matrix"
ws["A1"].font = Font(bold=True, size=18, color="1F4E78")
ws.merge_cells("A1:F1")
ws["A2"] = "Five-axis assessment of how refined the GPS calculation can become for each distributor. Pre-filled with safe defaults; owner reviews and adjusts."
ws["A2"].font = Font(size=12, italic=True, color="595959")
ws.merge_cells("A2:F2")

lines = [
    ("", ""),
    ("Date prepared", "2026-05-28"),
    ("Period", "Current state of GPS calculation inputs across the ISZE distributor network"),
    ("", ""),
    ("Five axes", ""),
    ("  A — UIO denominator", "Where the units-in-operation count comes from. Max = 3 (per-VIN cohort)."),
    ("  B — Sales numerator", "Whose sales we see. Max = 2 (per-VIN parts attribution; dealer-to-end-customer deliberately excluded)."),
    ("  C — PMS / maintenance", "Service-interval and workshop visibility. Max = 3 (full workshop integration)."),
    ("  D — Pricing / competitive", "Aftermarket pricing visibility per market. Max = 3 (full competitive PR00 mapping)."),
    ("  E — Warranty / goodwill", "Warranty parts cleanly excluded from sales numerator. Max = 2 (audit trail)."),
    ("", ""),
    ("Maximum total score", "3 + 2 + 3 + 3 + 2 = 13"),
    ("", ""),
    ("Confidence labels on pre-filled cells", ""),
    ("  CONFIRMED", "Sourced from current ISZE documentation or directly confirmed (green)"),
    ("  GUESS", "Inferred from typical distributor-network behaviour (orange italic) — owner must vet"),
    ("  DEFAULT", "Safe baseline (lowest plausible value until owner confirms) (grey italic)"),
    ("", ""),
    ("How to use", "Open Maturity_Matrix sheet. For each cell with confidence = GUESS or DEFAULT, replace the level with the actual value if known. Targets (one step up from current by default) can be adjusted upward where ambition is higher."),
    ("", ""),
    ("Workbook contents", ""),
    ("  1. Framework", "this sheet"),
    ("  2. Axis_Definitions", "scoring scale 0-3 per axis with examples"),
    ("  3. Maturity_Matrix", "main grid: 18 distributors × 5 axes (current + target + gap)"),
    ("  4. Refinement_Checklist", "per-distributor action list (one row per axis)"),
    ("  5. Scoreboard", "summary counts by axis and total"),
]
for i, (k, v) in enumerate(lines, 4):
    ws.cell(row=i, column=1, value=k).font = BOLD
    ws.cell(row=i, column=2, value=v).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=6)
autosize(ws, [32, 60, 18, 18, 18, 18])

# ============================================================
# Sheet 2: Axis definitions
# ============================================================
ws = wb.create_sheet("Axis_Definitions")
ws["A1"] = "Axis Definitions — Scoring Scale"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:E1")

r = 3
axes = [
    ("A — UIO Denominator Quality", "Where the units-in-operation number comes from.", [
        (0, "IML shipment records, lumped CV LD (no model split)", "Distributors with no scrap-adj logic"),
        (1, "IML shipment records, per-model split (N3.5T / N7.5T / F / MD / LCV)", "Current standard for most ISZE distributors"),
        (2, "National registration authority — SMMT, SIMI, KBA, Bilstatistik, etc. — true regs per model", "ITUK (SMMT), Ireland (SIMI from 2026)"),
        (3, "Per-VIN fleet register with age cohorts", "Workshop or distributor-system level — rare today"),
    ]),
    ("B — Sales Numerator Depth", "Whose parts sales we see in the calculation.", [
        (0, "ISZE → distributor only (wholesale-in, current SAP export)", "Default for all distributors today"),
        (1, "+ Distributor → dealer (distributor sell-out from their warehouse)", "ITUK confirmed (Niguri sales-out file)"),
        (2, "+ Per-VIN parts attribution (which truck VIN consumed which part)", "Requires workshop integration"),
        (None, "(Dealer → end-customer / retail sell-through level deliberately excluded — unreachable.)", ""),
    ]),
    ("C — PMS / Maintenance Data Access", "Visibility of service-interval and workshop behaviour.", [
        (0, "None — no PMS data shared", "Default for most distributors"),
        (1, "One-off PMS data exchange", "ITUK shared Apr 2026 PMS study"),
        (2, "Recurring PMS data feed", "Monthly/quarterly extracts from distributor"),
        (3, "Full workshop system integration (PMS captured per VIN automatically)", "Aspiration"),
    ]),
    ("D — Pricing / Competitive Data", "Aftermarket pricing visibility for that market.", [
        (0, "None — no aftermarket pricing visibility", "Default"),
        (1, "Anecdotal — competitor parts cited but unstructured", ""),
        (2, "TecDoc / Eucon coverage — structured competitive PNs and pricing", "Multiple ISZE markets covered by TecDoc"),
        (3, "Full competitive PR00 mapping with our genuine pricing benchmarked", "ITUK BVP work, ISZE master competitive parts file"),
    ]),
    ("E — Warranty / Goodwill Cleanliness", "Whether warranty parts are properly excluded from sales numerator.", [
        (0, "Warranty / goodwill blended into total sales (numerator inflated)", ""),
        (1, "Warranty flagged in SAP but not consistently excluded from GPS calc", "Current state across the network"),
        (2, "Warranty excluded with full audit trail per distributor", "Target — clean numerator"),
    ]),
]

for axis_name, axis_desc, levels in axes:
    ws.cell(row=r, column=1, value=axis_name).font = Font(bold=True, size=12, color="1F4E78")
    ws.cell(row=r, column=2, value=axis_desc).font = ITALIC_GREY
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    r += 1
    ws.cell(row=r, column=1, value="Level").font = BOLD
    ws.cell(row=r, column=2, value="What it means").font = BOLD
    ws.cell(row=r, column=3, value="Example / Note").font = BOLD
    for c in range(1, 6):
        ws.cell(row=r, column=c).fill = GREY
        ws.cell(row=r, column=c).border = BORDER
    r += 1
    for lvl, desc, ex in levels:
        if lvl is None:
            ws.cell(row=r, column=1, value="—").alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=2, value=desc).font = ITALIC_GREY
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        else:
            c1 = ws.cell(row=r, column=1, value=lvl)
            c1.font = BOLD; c1.fill = LEVEL_FILL[lvl]
            c1.alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=2, value=desc).alignment = Alignment(wrap_text=True, vertical="top")
            ws.cell(row=r, column=3, value=ex).alignment = Alignment(wrap_text=True, vertical="top")
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        ws.row_dimensions[r].height = 28
        r += 1
    r += 1

autosize(ws, [8, 42, 32, 20, 20])

# ============================================================
# Sheet 3: Maturity_Matrix (POPULATED)
# ============================================================
ws = wb.create_sheet("Maturity_Matrix")
ws["A1"] = "Maturity Matrix — All Distributors"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:T1")
ws["A2"] = "All cells pre-filled. Confidence: CONFIRMED (green) | GUESS (orange) | DEFAULT (grey). Owner adjusts any cell."
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:T2")

hdr = [
    "Distributor", "Country", "Scope",
    "A — UIO cur", "A conf", "A target",
    "B — Sales cur", "B conf", "B target",
    "C — PMS cur", "C conf", "C target",
    "D — Pricing cur", "D conf", "D target",
    "E — Warranty cur", "E conf", "E target",
    "Total current", "Total target",
]
for c, h in enumerate(hdr, 1):
    ws.cell(row=4, column=c, value=h)
style_header(ws, 4, len(hdr))
ws.row_dimensions[4].height = 36

def put_level(ws, r, c, lvl):
    cell = ws.cell(row=r, column=c, value=lvl)
    cell.fill = LEVEL_FILL[lvl]
    cell.alignment = Alignment(horizontal="center")
    cell.font = BOLD
    cell.border = BORDER

def put_conf(ws, r, c, conf):
    cell = ws.cell(row=r, column=c, value=conf)
    cell.font = CONF_FONT[conf]
    cell.alignment = Alignment(horizontal="center")
    cell.border = BORDER

def put_target(ws, r, c, tgt):
    cell = ws.cell(row=r, column=c, value=tgt)
    cell.fill = LEVEL_FILL[tgt]
    cell.alignment = Alignment(horizontal="center")
    cell.font = BOLD
    cell.border = BORDER

r = 5
for row in D:
    (code, country, scope,
     a_cur, a_conf, b_cur, b_conf, c_cur, c_conf, d_cur, d_conf, e_cur, e_conf,
     a_tgt, b_tgt, c_tgt, d_tgt, e_tgt) = row

    ws.cell(row=r, column=1, value=code).font = BOLD
    ws.cell(row=r, column=2, value=country)
    ws.cell(row=r, column=3, value=scope).font = ITALIC_GREY
    ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="center")
    for cc in range(1, 4):
        ws.cell(row=r, column=cc).border = BORDER

    put_level(ws, r, 4, a_cur)
    put_conf(ws, r, 5, a_conf)
    put_target(ws, r, 6, a_tgt)

    put_level(ws, r, 7, b_cur)
    put_conf(ws, r, 8, b_conf)
    put_target(ws, r, 9, b_tgt)

    put_level(ws, r, 10, c_cur)
    put_conf(ws, r, 11, c_conf)
    put_target(ws, r, 12, c_tgt)

    put_level(ws, r, 13, d_cur)
    put_conf(ws, r, 14, d_conf)
    put_target(ws, r, 15, d_tgt)

    put_level(ws, r, 16, e_cur)
    put_conf(ws, r, 17, e_conf)
    put_target(ws, r, 18, e_tgt)

    tot_cur = a_cur + b_cur + c_cur + d_cur + e_cur
    tot_tgt = a_tgt + b_tgt + c_tgt + d_tgt + e_tgt
    c1 = ws.cell(row=r, column=19, value=tot_cur)
    c1.font = BOLD; c1.alignment = Alignment(horizontal="center"); c1.border = BORDER
    c1.fill = NAVY; c1.font = Font(bold=True, color="FFFFFF")
    c2 = ws.cell(row=r, column=20, value=tot_tgt)
    c2.font = BOLD; c2.alignment = Alignment(horizontal="center"); c2.border = BORDER
    c2.fill = NAVY; c2.font = Font(bold=True, color="FFFFFF")

    ws.row_dimensions[r].height = 22
    r += 1

# Footer note
r += 1
ws.cell(row=r, column=1, value="Pre-fill rationale (per axis)").font = BOLD
r += 1
notes = [
    "Axis A — pre-filled from current ISZE methodology. Two distributors at A=2 (ITUK via SMMT, Ireland via SIMI from 2026). All others at A=1 (IML per-model split is the current standard).",
    "Axis B — defaulted to 0 (ISZE → distributor only) for everyone except ITUK=1 (sales-to-dealer via Niguri file is confirmed). All B values for distributors other than ITUK need owner confirmation: which distributors do share their sell-out?",
    "Axis C — defaulted to 0 except ITUK=1 (Apr 2026 PMS study). Owner to confirm whether any other distributor has shared PMS data.",
    "Axis D — defaulted to 0 for most markets; ITUK=2 (BVP + competitive PR00 work exists). IUK=1 marked GUESS. Owner to confirm TecDoc/Eucon coverage per market.",
    "Axis E — set to 1 for all distributors on the assumption warranty parts are flagged in SAP for every sold_to. Owner confirmed warranty data can be provided for all distributors — moving to E=2 is the ambition.",
]
for n in notes:
    ws.cell(row=r, column=1, value="• " + n).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=20)
    ws.row_dimensions[r].height = 30
    r += 1

autosize(ws, [12, 18, 24,
              8, 10, 8,
              9, 10, 8,
              8, 10, 8,
              9, 10, 8,
              9, 10, 8,
              10, 10])

# ============================================================
# Sheet 4: Refinement_Checklist
# ============================================================
ws = wb.create_sheet("Refinement_Checklist")
ws["A1"] = "Refinement Checklist — Action per Distributor per Axis"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:F1")

hdr_row = ["Distributor", "Axis", "Current → Target", "Action needed", "Data owner", "Status"]
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=4, column=c, value=h)
style_header(ws, 4, len(hdr_row))

axis_owners = {
    "A — UIO denominator": "ISZE Data team / national reg authority",
    "B — Sales numerator": "Distributor",
    "C — PMS data": "Distributor (workshop/DMS)",
    "D — Pricing data": "ISZE Pricing / TecDoc / Eucon",
    "E — Warranty data": "ISZE Finance / SAP team",
}

def action_text(code, axis_letter, cur, tgt):
    """Concrete action statement based on level transition."""
    if cur == tgt:
        return "Already at target — maintain."
    if axis_letter == "A":
        if cur == 0 and tgt >= 1:
            return "Apply per-model split (N3.5T / N7.5T / F / MD / LCV) to IML records for this distributor."
        if cur == 1 and tgt >= 2:
            return f"Identify and ingest {code}'s national vehicle registration authority data (SMMT/SIMI/KBA/etc.) with per-model granularity."
        if cur == 2 and tgt == 3:
            return "Move to per-VIN fleet register — requires DMS/workshop integration."
    if axis_letter == "B":
        if cur == 0 and tgt >= 1:
            return f"Request distributor sell-out (distributor → dealer) from {code}. Establish data-sharing cadence."
        if cur == 1 and tgt == 2:
            return "Integrate per-VIN parts attribution from workshop/DMS systems."
    if axis_letter == "C":
        if cur == 0 and tgt >= 1:
            return f"Request a one-off PMS study from {code} (similar to ITUK Apr 2026)."
        if cur == 1 and tgt >= 2:
            return f"Convert ITUK-style one-off PMS exchange into recurring quarterly feed for {code}."
        if cur == 2 and tgt == 3:
            return "Workshop / DMS integration for automated PMS capture."
    if axis_letter == "D":
        if cur == 0 and tgt >= 1:
            return f"Document competitor parts cited anecdotally in this market."
        if cur == 1 and tgt >= 2:
            return f"Procure TecDoc / Eucon coverage for {code}'s market."
        if cur == 2 and tgt == 3:
            return "Build competitive PR00 mapping vs ISZE genuine pricing."
    if axis_letter == "E":
        if cur == 0 and tgt >= 1:
            return f"Confirm warranty parts are flagged in SAP for {code}'s sold_to."
        if cur == 1 and tgt == 2:
            return f"Exclude warranty parts consistently from {code} GPS calc; document audit trail."
    return "—"

r = 5
for row in D:
    (code, country, scope,
     a_cur, a_conf, b_cur, b_conf, c_cur, c_conf, d_cur, d_conf, e_cur, e_conf,
     a_tgt, b_tgt, c_tgt, d_tgt, e_tgt) = row

    # Group header
    ws.cell(row=r, column=1, value=f"{code} — {country}").font = Font(bold=True, color="FFFFFF")
    ws.cell(row=r, column=1).fill = NAVY
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    r += 1

    axis_rows = [
        ("A — UIO denominator", a_cur, a_tgt, axis_owners["A — UIO denominator"]),
        ("B — Sales numerator", b_cur, b_tgt, axis_owners["B — Sales numerator"]),
        ("C — PMS data",        c_cur, c_tgt, axis_owners["C — PMS data"]),
        ("D — Pricing data",    d_cur, d_tgt, axis_owners["D — Pricing data"]),
        ("E — Warranty data",   e_cur, e_tgt, axis_owners["E — Warranty data"]),
    ]
    for axis, cur, tgt, owner in axis_rows:
        ws.cell(row=r, column=1, value="")
        ws.cell(row=r, column=2, value=axis).font = BOLD
        transition = f"{cur} → {tgt}"
        c3 = ws.cell(row=r, column=3, value=transition)
        c3.alignment = Alignment(horizontal="center")
        c3.font = BOLD
        if cur == tgt:
            c3.fill = GREEN
        else:
            c3.fill = AMBER
        ws.cell(row=r, column=4, value=action_text(code, axis[0], cur, tgt)).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row=r, column=5, value=owner).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row=r, column=6, value="").alignment = Alignment(horizontal="center")
        for cc in range(1, 7):
            ws.cell(row=r, column=cc).border = BORDER
        ws.row_dimensions[r].height = 38
        r += 1
    r += 1

autosize(ws, [16, 22, 14, 55, 28, 14])

# ============================================================
# Sheet 5: Scoreboard
# ============================================================
ws = wb.create_sheet("Scoreboard")
ws["A1"] = "Scoreboard — Current vs Target by Axis"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:H1")

# Per-axis counts
from collections import Counter
def axis_counts(idx, max_lvl):
    cur = Counter([row[idx] for row in D])
    tgt = Counter([row[13 + ["A","B","C","D","E"].index(name)] for row in D])
    return cur, tgt

axis_info = [
    ("A — UIO denominator", 3, 3),
    ("B — Sales numerator", 2, 5),
    ("C — PMS data",        3, 7),
    ("D — Pricing data",    3, 9),
    ("E — Warranty data",   2, 11),
]

target_idx_map = {"A": 13, "B": 14, "C": 15, "D": 16, "E": 17}

hdr = ["Axis", "Max", "Distributors at level 0", "Level 1", "Level 2", "Level 3", "Current total", "Target total"]
for c, h in enumerate(hdr, 1):
    ws.cell(row=3, column=c, value=h)
style_header(ws, 3, len(hdr))

r = 4
for axis_label, max_lvl, cur_col in axis_info:
    letter = axis_label[0]
    cur_vals = [row[cur_col] for row in D]
    tgt_vals = [row[target_idx_map[letter]] for row in D]
    cur_counter = Counter(cur_vals)
    ws.cell(row=r, column=1, value=axis_label).font = BOLD
    ws.cell(row=r, column=2, value=max_lvl).alignment = Alignment(horizontal="center")
    for lvl in range(4):
        cell = ws.cell(row=r, column=3 + lvl, value=cur_counter.get(lvl, 0))
        cell.alignment = Alignment(horizontal="center")
        if lvl <= max_lvl:
            cell.fill = LEVEL_FILL[lvl]
            if cur_counter.get(lvl, 0) > 0:
                cell.font = BOLD
        else:
            cell.fill = GREY
            cell.value = "—"
    ws.cell(row=r, column=7, value=sum(cur_vals)).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=7).font = BOLD
    ws.cell(row=r, column=8, value=sum(tgt_vals)).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=8).font = BOLD
    ws.cell(row=r, column=8).fill = GREEN
    r += 1

# Total row
ws.cell(row=r, column=1, value="ALL AXES TOTAL").font = BOLD
ws.cell(row=r, column=2, value="13").alignment = Alignment(horizontal="center")
ws.cell(row=r, column=2).font = BOLD
total_cur = sum(row[3] + row[5] + row[7] + row[9] + row[11] for row in D)
total_tgt = sum(row[13] + row[14] + row[15] + row[16] + row[17] for row in D)
for cc in range(3, 7):
    ws.cell(row=r, column=cc, value="").fill = GREY
c7 = ws.cell(row=r, column=7, value=total_cur); c7.font = WHITE_BOLD; c7.fill = NAVY
c7.alignment = Alignment(horizontal="center")
c8 = ws.cell(row=r, column=8, value=total_tgt); c8.font = WHITE_BOLD; c8.fill = NAVY
c8.alignment = Alignment(horizontal="center")
r += 2

# Top movers (distributors with highest gap)
ws.cell(row=r, column=1, value="Largest gap (Current → Target) by distributor").font = BOLD
r += 1
hdr2 = ["Rank", "Distributor", "Current total", "Target total", "Gap"]
for c, h in enumerate(hdr2, 1):
    ws.cell(row=r, column=c, value=h)
style_header(ws, r, len(hdr2))
r += 1

gap_list = []
for row in D:
    cur = row[3] + row[5] + row[7] + row[9] + row[11]
    tgt = row[13] + row[14] + row[15] + row[16] + row[17]
    gap_list.append((row[0], cur, tgt, tgt - cur))
gap_list.sort(key=lambda x: -x[3])
for i, (code, cur, tgt, gap) in enumerate(gap_list, 1):
    ws.cell(row=r, column=1, value=i).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=2, value=code).font = BOLD
    ws.cell(row=r, column=3, value=cur).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=4, value=tgt).alignment = Alignment(horizontal="center")
    c = ws.cell(row=r, column=5, value=gap)
    c.alignment = Alignment(horizontal="center")
    c.font = BOLD
    if gap >= 6:
        c.fill = RED0
    elif gap >= 4:
        c.fill = AMBER
    else:
        c.fill = GREEN
    r += 1

autosize(ws, [22, 12, 12, 10, 10, 10, 14, 14])

wb.save(OUT)
print(f"WROTE: {OUT}")
print(f"Sheets: {[s.title for s in wb.worksheets]}")
print(f"Distributors: {len(D)}")
print()
print(f"Total current score across network: {total_cur} / {len(D)*13}")
print(f"Total target score across network:  {total_tgt} / {len(D)*13}")
print(f"Total gap (refinement potential):   {total_tgt - total_cur}")
print()
print("Top 5 gap distributors (most to gain):")
for code, cur, tgt, gap in gap_list[:5]:
    print(f"  {code:<12} cur={cur:>2}  tgt={tgt:>2}  gap={gap:>2}")
