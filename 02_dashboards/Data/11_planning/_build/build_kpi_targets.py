"""Build ISZE_DB_KPI_Targets_FY2627_v1.xlsx — FY26/27 KPI targets per distributor.
Sources: KPI Master File april 2026.xlsx (currents = median of last 6 reported months,
parts/contracts/regs = trailing 12m); IMIT LCV forecast (LCV UIO Nov 2025 EU Study);
distributor_master_mapping.csv (countries). AIOS (Turkey) excluded — not an ISZE market.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

RED = "CC0E1E"
GREY = "F2F2F2"
def F(**k):
    k.setdefault("size", 10)
    return Font(name="Arial", **k)
BLUE = Font(name="Arial", size=10, color="0000FF")
THIN = Border(*[Side(style="thin", color="BFBFBF")] * 4)

wb = Workbook()

# ---------------- Assumptions sheet ----------------
ws = wb.create_sheet("Assumptions")
ws["A1"] = "ISZE DB KPI Targets FY26/27 — Assumptions & Target Logic"
ws["A1"].font = F(bold=True, size=13, color=RED)
ws["A3"] = "Named inputs (blue = change for scenarios)"
ws["A3"].font = F(bold=True)
inputs = [
    ("Parts price increase FY26/27", 0.04, "0.0%", "Jerome estimate 2026-06-11 — replace with actual PR00 uplift when known"),
    ("Fill rate standard", 0.95, "0%", "Network standard, all DBs"),
    ("Fill rate floor", 0.92, "0%", "Minimum acceptable"),
    ("BO intensity ceiling (lines / €100K DLR sales /mo)", 15, "0", "Best performers run 5–10 (MIDI 5.6, ITUK/IUK 10.2)"),
    ("Service contract attach (% of new regs)", 0.15, "0%", "Year-1 standard; mature programmes 25%+"),
    ("Warranty contract attach (% of new regs)", 0.12, "0%", "Where programme exists"),
]
r = 4
for name, val, fmt, note in inputs:
    ws.cell(r, 1, name).font = F()
    c = ws.cell(r, 2, val); c.font = BLUE; c.number_format = fmt
    c.fill = PatternFill("solid", start_color="FFFF00")
    ws.cell(r, 3, note).font = F(italic=True, size=9)
    r += 1
PRICE = "Assumptions!$B$4"

r += 1
ws.cell(r, 1, "Target logic per KPI").font = F(bold=True); r += 1
logic = [
    ("Fill rate", "Standard ≥95%, floor 92%. Current <85% → interim = half the gap closed FY26/27, full standard FY27/28. No macro adjustment."),
    ("MOS (days of stock)", "Band = order cycle (30d) + transit from Belgium PDC + safety (≈ transit + 15d). Class A ≤5d road: 60–75d. Class B 5–12d road/short-sea: 75–90d. Class C sea ≥3wk (IL, IS, MT, CY, PS): 90–120d. Trucks +15–30d assortment breadth. Above band = working capital waste, below = fill risk."),
    ("BO lines", "≤15 lines per €100K monthly DLR sales, or −10% YoY if already compliant. Normalized — absolute counts not comparable across DB sizes."),
    ("Parts sales DB→DLR", "Trailing 12m × (1 + price increase + macro modifier ±2pts). Aging parc caps downward macro pleas — weak new-vehicle market supports parts demand."),
    ("Campaigns", "Large DB ≥4/yr, mid ≥2, micro ≥1. Counted only if measurable offer. Free-text reporting in master file must stop."),
    ("Warranty contracts", "Attach % of new registrations where programme exists; else milestone = launch by Q3 FY26/27 + 5% attach H2."),
    ("Service contracts", "Attach % of new registrations; year-1 15%, mature 25%. Holders (UTI 26%) hold/stretch."),
    ("Registrations LCV", "IMIT forecast CY2026(E) as FY26/27 anchor (CY/FY offset noted). Source: LCV UIO (November 2025)_EU_Study_Imit.xlsx, RAW Data."),
    ("Registrations CV", "Trailing 12m ± market factor — NO IML CV forecast on disk; replace when IML CV plan received."),
    ("Reporting gate", "DBs dark ≥6 months (ISD, UMI, Petros, Loutsios; IMF since Sep 25): 3 consecutive complete months before numeric targets bind. N/D is not exemption."),
]
for k, v in logic:
    ws.cell(r, 1, k).font = F(bold=True)
    ws.cell(r, 2, v).font = F(size=9)
    ws.cell(r, 2).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    ws.row_dimensions[r].height = 28
    r += 1
ws.column_dimensions["A"].width = 38
ws.column_dimensions["B"].width = 16
ws.column_dimensions["C"].width = 60

# ---------------- Targets sheet ----------------
# row tuples: code, country, cls, status, fill_cur, fill_tgt, mos_cur, mos_lo, mos_hi,
# bo_cur, bo_tgt, parts12, mod, warr12, warr_tgt, svc12, svc_tgt, camp,
# lcv_trail, lcv26, lcv27, cv_trail, cv_tgt, note
# warr_tgt/svc_tgt: number, formula-marker tuple ("attach", pct, base_col) or text
D = [
    ("MIDI", "Multi (IT base: FR/CH/ES/IT/PL/RS)", "B + truck", "Active", 0.98, 0.97, 278, 105, 120, 180, 180, 34904000, 0.02, 128, 250, 769, ("att", 0.12, "lcv26+cv"), 4, 4378, 4540, 4615, 4065, 4100, "Interim MOS 180 FY26/27, band by FY28/29. 278d ≈ €9M tied up above band."),
    ("IUK", "United Kingdom (LCV)", "A", "Active", 0.93, 0.95, 71, 60, 75, 148, 130, 20366342, -0.02, None, "n/a (factory)", None, "Launch Q3", 4, 4256, 3020, 2520, None, None, "UK pickup BIK change: IMIT cuts regs −40%. Parts resilient (aging parc) → only −2pts."),
    ("ITUK", "United Kingdom (trucks)", "A + truck", "Active", 0.95, 0.96, 137, 90, 105, 120, 110, 14404505, -0.01, 206, ("att", 0.12, "cv"), 257, ("att", 0.15, "cv"), 4, None, None, None, 1913, 1950, "2 days from PDC, 137d stock — the MOS outlier. €1.5–2M working capital above band."),
    ("IBX (incl. Polska)", "Benelux + Poland", "A", "Active", 0.85, 0.90, 48, 60, 75, None, 75, 7747694, 0.00, None, "Launch Q3", 96, 100, 4, 990, 845, 845, None, None, "RAISE stock: 48d starves 85% fill. IMIT 845 = BE row only; PL/NL volumes unresolved in IMIT — verify. Parts = IBX 6.55M + PL 1.19M."),
    ("RSA", "Norway", "B", "Active", 0.96, 0.96, 110, 75, 90, 58, 45, 5152741, 0.00, 16, 25, None, "Launch Q3", 4, 607, 430, 355, None, None, "IMIT cuts Norway LCV −30% vs trailing."),
    ("ISD", "Germany", "A", "GATE", 0.98, 0.96, 126, 60, 75, 80, None, 4475521, 0.00, None, "Launch Q3", None, "Launch Q3", 4, 711, 1000, 1000, 30, None, "Dark since Jan 25. Parts figure = last trailing 12m, indicative only."),
    ("Imotors", "Portugal", "B", "Active", 0.795, 0.87, 96, 75, 90, 438, 305, 4047903, 0.02, 18, 55, 18, ("att", 0.10, "lcv26+cv"), 4, 700, 900, 900, 208, 220, "Fill 87 interim → 95 FY27/28. BO intensity 112/€100K = worst in network; end-state ≤60/mo. IMIT shows genuine growth (900 vs 692 CY25)."),
    ("UTI", "Israel (trucks)", "C + truck", "Active", 0.93, 0.95, 156, 135, 150, 199, 140, 3360454, 0.00, None, "Launch Q3", 271, ("att", 0.26, "cv"), 4, None, None, None, 1059, 1100, "3wk sea transit Antwerp–Haifa justifies C band — 156d nearly compliant. Svc attach 26% = network best; hold."),
    ("Isuzu Sverige", "Sweden", "B", "Active", 0.97, 0.97, 51, 60, 75, 63, 45, 3016144, -0.02, None, "Launch Q3", None, "Launch Q3", 4, 1529, 910, 925, None, None, "IMIT halves Sweden (EV transition). 51d MOS acceptable while fill ≥97."),
    ("Isuzu Ireland", "Ireland", "B", "Active", None, 0.95, 130, 75, 90, None, None, 2862584, 0.00, None, "Launch Q3", None, "Launch Q3", 3, 309, 430, 430, 111, 117, "Fill + BO not reported — report first, then standard applies."),
    ("WAE", "Hungary", "B", "Active", 0.69, 0.82, 100, 75, 90, 24, 18, 871455, 0.00, 8, 12, None, "Launch Q3", 2, 287, 370, 370, None, None, "100d stock + 74% fill = wrong parts on shelf → stock-mix audit. Fill 82 interim → 90 FY27/28."),
    ("IMF", "Finland", "B", "GATE", 0.89, 0.92, 33, 75, 90, 24, 18, 696062, 0.00, None, "Launch Q3", 3, "Launch Q3", 2, 108, 140, 140, None, None, "Stopped reporting Sep 25. 33d MOS is fill-risk thin — raise."),
    ("Isuzu Danmark", "Denmark", "A/B", "Active", None, 0.95, None, 60, 75, 5, 5, 560211, 0.00, None, "Launch Q3", None, "Launch Q3", 2, 104, 120, 120, None, None, "Fill + MOS not reported — report first."),
    ("GasanZammit", "Malta", "C", "Active", 0.86, 0.90, 117, 90, 105, None, None, 553873, 0.00, 0, "Launch Q3", 0, "Launch Q3", 2, 13, 75, 125, 48, 50, "Fill 90 interim → 93. Reports 13 LCV regs vs IMIT 75 shipped — reconcile regs vs shipments."),
    ("Petros Petropoulos", "Greece", "B", "GATE", 0.60, 0.80, 60, 75, 90, None, None, 515115, 0.00, 0, "Launch Q3", 0, "Launch Q3", 2, 333, 630, 630, 0, None, "Last reported fill 60% — worst in network. Gate first; interim 80."),
    ("Isuzu Rom Auto", "Romania", "B", "Active", 0.94, 0.95, 135, 75, 90, 4, 4, 394596, 0.00, None, "Launch Q3", None, "Launch Q3", 2, 176, 170, 170, None, None, "Trim stock 135 → band."),
    ("BL ehf", "Iceland", "C", "Active", 0.91, 0.95, 121, 90, 105, 19, 19, 195849, 0.00, 59, 60, 3, "—", 2, 79, 45, 45, None, None, "Warranty attach ~75% = network benchmark — showcase. IMIT 45 vs trailing 79 — verify IMIT row."),
    ("KIMA", "Palestine", "C", "Active", 0.91, 0.93, 30, 90, 105, 3, 5, 27798, 0.00, 0, "—", 0, "—", 1, 9, 20, 20, 0, None, "30d MOS with sea transit = stockout exposure, not efficiency. Raise."),
    ("UMI", "Israel (LCV)", "C", "GATE", None, None, 147, 105, 120, None, None, None, 0.00, None, "Gate", None, "Gate", 1, 453, 900, 1000, None, None, "Dark since Feb 25; parts 'internal only'. Gate before any target."),
    ("Loutsios Group", "Cyprus", "C", "GATE", None, None, None, 90, 105, None, None, None, 0.00, None, "Gate", None, "Gate", 1, None, 360, 400, None, None, "Zero KPI reporting while IMIT shows ~360 LCV/yr — blind on a real market."),
]

ws = wb.active
ws.title = "Targets FY26-27"
ws["A1"] = "ISZE DB KPI Targets FY26/27 (Apr 2026 – Mar 2027)"
ws["A1"].font = F(bold=True, size=13, color=RED)
ws["A2"] = "Currents: KPI Master File april 2026.xlsx (fill/MOS/BO = median last 6 reported months; € and counts = trailing 12m). LCV forecast: IMIT EU Study Nov 2025, CY2026(E)/CY2027(E). AIOS (Turkey) excluded — not an ISZE market."
ws["A2"].font = F(italic=True, size=9)

hdr2 = ["DB", "Country / market", "Supply class", "Status",
        "Fill cur", "Fill TARGET", "MOS cur (d)", "MOS band lo", "MOS band hi",
        "BO/mo cur", "BO/mo TARGET", "Parts 12m cur (€)", "Macro mod", "Parts TARGET (€)",
        "Warr 12m", "Warr TARGET", "Svc 12m", "Svc TARGET", "Camp TARGET",
        "LCV reg 12m", "LCV TGT (IMIT 26E)", "LCV ref (IMIT 27E)", "CV reg 12m", "CV TARGET", "Rationale"]
HR = 4
for c, h in enumerate(hdr2, 1):
    cell = ws.cell(HR, c, h)
    cell.font = F(bold=True, color="FFFFFF", size=9)
    cell.fill = PatternFill("solid", start_color=RED)
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
ws.row_dimensions[HR].height = 30

def put(r, c, v, fmt=None, blue=False):
    cell = ws.cell(r, c)
    if v is None:
        cell.value = "n/d"
        cell.font = F(color="999999", size=9)
    else:
        cell.value = v
        cell.font = BLUE if blue else F(size=9)
        if fmt:
            cell.number_format = fmt
    cell.border = THIN
    return cell

row = HR + 1
for d in D:
    (code, ctry, cls, status, fc, ft, mc, mlo, mhi, boc, bot, p12, mod,
     w12, wt, s12, st, camp, lcvt, l26, l27, cvt, cvtgt, note) = d
    put(row, 1, code).font = F(bold=True, size=9)
    put(row, 2, ctry)
    put(row, 3, cls)
    sc = put(row, 4, status)
    if status == "GATE":
        sc.font = F(bold=True, color=RED, size=9)
    put(row, 5, fc, "0%")
    put(row, 6, ft, "0%", blue=True)
    put(row, 7, mc, "0")
    put(row, 8, mlo, "0", blue=True)
    put(row, 9, mhi, "0", blue=True)
    put(row, 10, boc, "#,##0")
    put(row, 11, bot, "#,##0", blue=True)
    put(row, 12, p12, "#,##0")
    put(row, 13, mod, "0%", blue=True)
    if p12 is not None:
        c = ws.cell(row, 14, f"=L{row}*(1+{PRICE}+M{row})")
        c.font = F(size=9); c.number_format = "#,##0"; c.border = THIN
    else:
        put(row, 14, None)
    put(row, 15, w12, "#,##0")
    # warranty target
    if isinstance(wt, tuple):
        pct, base = wt[1], wt[2]
        ref = f"W{row}" if base == "cv" else f"(U{row}+W{row})"
        c = ws.cell(row, 16, f"=ROUND({pct}*{ref},0)")
        c.font = F(size=9); c.number_format = "#,##0"; c.border = THIN
    else:
        put(row, 16, wt, "#,##0", blue=isinstance(wt, (int, float)))
    put(row, 17, s12, "#,##0")
    if isinstance(st, tuple):
        pct, base = st[1], st[2]
        ref = f"W{row}" if base == "cv" else f"(U{row}+W{row})"
        c = ws.cell(row, 18, f"=ROUND({pct}*{ref},0)")
        c.font = F(size=9); c.number_format = "#,##0"; c.border = THIN
    else:
        put(row, 18, st, "#,##0", blue=isinstance(st, (int, float)))
    put(row, 19, camp, "0", blue=True)
    put(row, 20, lcvt, "#,##0")
    put(row, 21, l26, "#,##0", blue=True)
    put(row, 22, l27, "#,##0")
    put(row, 23, cvt, "#,##0")
    put(row, 24, cvtgt, "#,##0", blue=True)
    nc = put(row, 25, note)
    nc.alignment = Alignment(wrap_text=True, vertical="top")
    if row % 2 == 0:
        for c in range(1, 26):
            if ws.cell(row, c).fill.start_color.rgb in (None, "00000000"):
                ws.cell(row, c).fill = PatternFill("solid", start_color=GREY)
    row += 1

# totals
tr = row + 1
ws.cell(tr, 1, "NETWORK TOTAL (active + gate, ex-AIOS)").font = F(bold=True)
for col, fmt in ((12, "#,##0"), (14, "#,##0"), (20, "#,##0"), (21, "#,##0"), (22, "#,##0"), (23, "#,##0")):
    L = get_column_letter(col)
    c = ws.cell(tr, col, f"=SUM({L}{HR+1}:{L}{row-1})")
    c.font = F(bold=True); c.number_format = fmt

widths = [17, 26, 11, 7, 7, 8, 8, 8, 8, 8, 9, 13, 8, 13, 8, 10, 8, 10, 6, 9, 11, 11, 9, 9, 60]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "C5"

# ---------------- IMIT reference sheet ----------------
ws = wb.create_sheet("IMIT LCV forecast")
ws["A1"] = "IMIT LCV sales per country — source: LCV UIO (November 2025)_EU_Study_Imit.xlsx, sheet RAW Data"
ws["A1"].font = F(bold=True, size=11, color=RED)
ws["A2"] = "2025 = 11+1 annualised. (E) = IMIT estimate. Shipments, not registrations — reconcile before using as reg target where they diverge (Malta, Iceland)."
ws["A2"].font = F(italic=True, size=9)
imit = [
    ("Country", "CY2024", "CY2025 (11+1)", "CY2026(E)", "CY2027(E)", "CY2028(E)"),
    ("UK", 7013, 4280, 3020, 2520, 2520),
    ("Israel", 1712, 1831, 900, 1000, 930),
    ("Sweden", 1348, 1648, 910, 925, 880),
    ("Belgium (IBX, BE row)", 1358, 1186, 845, 845, 845),
    ("Germany", 1705, 1646, 1000, 1000, 1000),
    ("Portugal", 943, 692, 900, 900, 840),
    ("Greece", 803, 784, 630, 630, 630),
    ("Norway", 383, 624, 430, 355, 460),
    ("Ireland", 265, 507, 430, 430, 430),
    ("Hungary", 265, 453, 370, 370, 275),
    ("Cyprus", 294, 353, 360, 400, 360),
    ("Romania", 146, 164, 170, 170, 172),
    ("Finland", 174, 139, 140, 140, 155),
    ("Denmark", 161, 86, 120, 120, 135),
    ("Iceland", 72, 89, 45, 45, 92),
    ("Malta", 88, 81, 75, 125, 105),
    ("Palestine", 5, 59, 20, 20, 76),
    ("MIDI Europe", 6192, 3431, 4540, 4615, 4705),
    ("ISZE total", 16977, 15312, 10845, 10595, 10580),
]
for ri, rowv in enumerate(imit, 4):
    for ci, v in enumerate(rowv, 1):
        c = ws.cell(ri, ci, v)
        c.border = THIN
        if ri == 4:
            c.font = F(bold=True, color="FFFFFF", size=9)
            c.fill = PatternFill("solid", start_color=RED)
        else:
            c.font = F(size=9)
            if ci > 1:
                c.number_format = "#,##0"
ws.cell(4 + len(imit) - 1, 1).font = F(bold=True, size=9)
ws.column_dimensions["A"].width = 24
for col in "BCDEF":
    ws.column_dimensions[col].width = 13

out = r"C:\Users\jerom\Desktop\claude\ISZE\Data\planning\ISZE_DB_KPI_Targets_FY2627_v1.xlsx"
wb.save(out)
print("saved", out)
