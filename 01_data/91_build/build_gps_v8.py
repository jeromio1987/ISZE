import json, openpyxl, sys
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = r"C:\Users\jerom\Desktop\claude\ISZE\Data\ISZE_GPS_Calculator_v8.xlsx"

BLUE = Font(name="Arial", size=10, color="0000FF")
BLACK = Font(name="Arial", size=10)
BOLD = Font(name="Arial", size=10, bold=True)
H1 = Font(name="Arial", size=13, bold=True, color="CC0E1E")
SMALL = Font(name="Arial", size=8, italic=True, color="808080")
HDR = Font(name="Arial", size=9, bold=True, color="FFFFFF")
HDRFILL = PatternFill("solid", start_color="CC0E1E")
YELLOW = PatternFill("solid", start_color="FFFF00")
GREEN = Font(name="Arial", size=10, color="008000")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

# ---- source data
# Rate Table (from v7): db, scope, cv, fmd, lcv, note
rates = [
    ("ITUK", "CV only (N+F+MD)", 1120, 1344, 0, "IC account. D-Max via IUK separately."),
    ("IUK", "LCV only (D-Max)", 0, 0, 250, "IC account. D-Max only."),
    ("UMI", "LCV only (D-Max)", 0, 0, 250, "IC account. Israel LCV."),
    ("UTI", "CV only (N+MD+F)", 1120, 1344, 0, "IC account. Israel CV trucks."),
    ("BELGIUM", "CV + LCV", 1120, 1344, 250, "IBX. Standard rate."),
    ("GERMANY", "CV + LCV", 1120, 1344, 250, "ISD. Standard rate."),
    ("PORTUGAL", "CV + LCV", 1120, 1344, 250, "Imotors. Standard rate."),
    ("IRELAND", "CV + LCV", 1120, 1344, 250, "Isuzu Ireland. Standard rate."),
    ("NORWAY", "LCV only", 0, 0, 250, "RSA. Standard rate."),
    ("SWEDEN", "LCV only", 0, 0, 250, "Isuzu Sverige. Standard rate."),
    ("DENMARK", "LCV only", 0, 0, 250, "Isuzu Denmark. Standard rate."),
    ("FINLAND", "LCV only", 0, 0, 250, "NAT. Standard rate."),
    ("ICELAND", "LCV only", 0, 0, 250, "BL. Standard rate."),
    ("MALTA", "CV + LCV", 1120, 1344, 250, "GasanZammit. Standard rate."),
    ("CYPRUS", "CV + LCV", 1120, 1344, 250, "Loutsios & Sons. Standard rate."),
    ("GREECE", "CV + LCV", 1120, 1344, 250, "Petros Petropoulos. Standard rate."),
    ("HUNGARY", "LCV only", 0, 0, 250, "AutoWallis. Standard rate."),
    ("ROMANIA", "LCV only", 0, 0, 250, "Isuzu Rom Auto. Standard rate."),
]
# 2025 baseline (v7 GPS_ex_Warranty): db, scope, uio25, wallet25, sales25_incl
base = [
    ("ITUK", "CV (N/F-Series)", 23989, 27270432, 5769867.82),
    ("IUK", "LCV (D-Max)", 47783, 11945750, 6221920.41),
    ("UMI", "LCV (D-Max)", 18542, 4635500, 3388801.28),
    ("UTI", "CV (N-Series)", 10336, 12534368, 3402116.94),
    ("GERMANY", "CV + LCV", 13780, 4089680, 2577765.90),
    ("BELGIUM", "CV + LCV", 9594, 2497904, 2143951.90),
    ("IRELAND", "CV + LCV", 2161, 1276868, 1213660.33),
    ("NORWAY", "CV + LCV", 7929, 1982250, 1438472.63),
    ("SWEDEN", "CV + LCV", 8443, 2110750, 1289481.04),
    ("DENMARK", "CV + LCV", 851, 212500, 150218.49),
    ("FINLAND", "CV + LCV", 1204, 301000, 285912.53),
    ("ICELAND", "CV + LCV", 406, 101500, 87259.89),
    ("CYPRUS", "CV + LCV", 2308, 753610, 429512.03),
    ("GREECE", "CV + LCV", 3742, 967690, 528390.82),
    ("MALTA", "CV + LCV", 1040, 471410, 206502.27),
    ("ROMANIA", "CV + LCV", 1071, 267750, 177276.35),
    ("HUNGARY", "CV + LCV", 3734, 933500, 330030.58),
    ("PORTUGAL", "CV + LCV", 7208, 4015506, 1712790.96),
]
# CY2025 warranty parts EUR per DB = CV (Warranty_CV_2025.xlsx, qty×price: ITUK/UTI sheets + Sheet4 country pivot)
#   + LCV (Warranty_LCV_2025.xlsx ExportClaimAssessment split by DistributorName × Sheet2 ISZE price; 99.8% pieces priced).
# Full per-DB CV/LCV breakdown + caveats: Data\Warranty_CY2025_by_DB.md (2026-06-12).
warranty = {
    "ITUK": 374426.05,     # CV only
    "IUK": 1054394.91,     # LCV (D-Max) — PM-sensor campaign + steering/brake/engine
    "UMI": 0.0,            # GAP: Israel LCV absent from warranty file — NOT a true zero
    "UTI": 255967.77,      # CV only
    "GERMANY": 259675.49,  # CV 5,593 + LCV 254,082 (ISD)
    "BELGIUM": 74676.85,   # LCV (IBX Belgium)
    "IRELAND": 34856.81,   # CV 3,908* + LCV 30,949   (*CV truck price-map, 82% priced = lower bound)
    "NORWAY": 290712.10,   # LCV (RSA)
    "SWEDEN": 189618.40,   # LCV
    "DENMARK": 9115.46,    # LCV
    "FINLAND": 48676.09,   # LCV
    "ICELAND": 7034.63,    # LCV
    "CYPRUS": 28040.72,    # CV 406 + LCV 27,634
    "GREECE": 56158.68,    # CV 1,450 + LCV 54,708
    "MALTA": 18218.85,     # CV 1,470 + LCV 16,749
    "ROMANIA": 19377.31,   # LCV
    "HUNGARY": 77433.66,   # LCV
    "PORTUGAL": 130587.94, # CV 28,836* + LCV 101,752  (*CV truck price-map, 52% priced = lower bound)
}
# FY2026 UIO from ISUZU_UIO_Overview_2026_v17.xlsx (1.UIO Overview 2026F + ITUK projection)
uio26 = {
    "ITUK": (23210, 963, 0), "IUK": (0, 0, 44923), "UMI": (0, 0, 17016), "UTI": (5887, 4583, 0),
    "GERMANY": (784, 0, 12338), "BELGIUM": (145, 0, 9338), "IRELAND": (1332, 131, 2145),
    "NORWAY": (0, 0, 7419), "SWEDEN": (0, 0, 8778), "DENMARK": (1, 0, 902), "FINLAND": (0, 0, 1194),
    "ICELAND": (0, 0, 419), "CYPRUS": (227, 5, 2328), "GREECE": (56, 5, 4106), "MALTA": (260, 0, 788),
    "ROMANIA": (0, 0, 1159), "HUNGARY": (0, 0, 3643), "PORTUGAL": (2963, 371, 5762),
}
hist = [r for r in json.load(open(r"C:\Users\jerom\Desktop\claude\ISZE\Data\_build\gps_results.json", encoding="utf-8-sig"))
        if r["db"] != "Distributor" and isinstance(r["year"], int)]

wb = openpyxl.Workbook()

# ============ Sheet 1: Rate Table
ws = wb.active; ws.title = "Rate Table"; ws.sheet_view.showGridLines = False
ws["A1"] = "SPEND RATE TABLE — €/unit/yr per distributor (blue = input, adjustable)"; ws["A1"].font = H1
ws["A2"] = "Theoretical annual genuine-parts wallet per vehicle. Source: ISZE standard (gps_model_targets); carried from v7."; ws["A2"].font = SMALL
hdrs = ["Distributor", "Scope", "CV LD (N-series) €/unit/yr", "CV MD / F-Series €/unit/yr", "LCV (D-Max) €/unit/yr", "Notes"]
for j, h in enumerate(hdrs, 1):
    c = ws.cell(4, j, h); c.font = HDR; c.fill = HDRFILL; c.border = BORDER
    c.alignment = Alignment(wrap_text=True, vertical="center")
for i, (db, scope, cv, fmd, lcv, note) in enumerate(rates):
    r = 5 + i
    ws.cell(r, 1, db).font = BOLD
    ws.cell(r, 2, scope).font = BLACK
    for j, v in ((3, cv), (4, fmd), (5, lcv)):
        c = ws.cell(r, j, v); c.font = BLUE; c.border = BORDER; c.number_format = "€#,##0"
    ws.cell(r, 6, note).font = SMALL
for j, w in enumerate([13, 20, 14, 14, 14, 40], 1):
    ws.column_dimensions[get_column_letter(j)].width = w
RATE_ROW = {db: 5 + i for i, (db, *_rest) in enumerate(rates)}

# ============ Sheet 2: GPS_Results_2022_2025 (history, values)
ws = wb.create_sheet("GPS_History_2022_2025"); ws.sheet_view.showGridLines = False
ws["A1"] = "GPS RESULTS 2022–2025 — per-model wallet basis (carried from v7 GPS_Results_2026; sales incl. warranty)"; ws["A1"].font = H1
hdrs = ["Distributor", "Year", "UIO CV LD", "UIO F", "UIO MD", "UIO LCV", "Total UIO", "Wallet (€)", "Sales parts (€)", "€/unit", "GPS %"]
for j, h in enumerate(hdrs, 1):
    c = ws.cell(3, j, h); c.font = HDR; c.fill = HDRFILL; c.border = BORDER
for i, row in enumerate(hist):
    r = 4 + i
    vals = [row["db"], row["year"], row["uio_cv_ld"], row["uio_f"], row["uio_md"], row["uio_lcv"],
            row["uio_total"], row["wallet"], row["sales"], row["spu"], row["gps"]]
    for j, v in enumerate(vals, 1):
        c = ws.cell(r, j, v); c.font = BLACK
        if j in (8, 9): c.number_format = "€#,##0"
        if j == 10: c.number_format = "€#,##0"
        if j == 11: c.number_format = "0.0%"
for j, w in enumerate([13, 7, 10, 8, 8, 9, 10, 13, 13, 9, 8], 1):
    ws.column_dimensions[get_column_letter(j)].width = w

# ============ Sheet 3: GPS_2025_Warranty
ws = wb.create_sheet("GPS_2025_Warranty"); ws.sheet_view.showGridLines = False
ws["A1"] = "GPS 2025 — WITH & WITHOUT WARRANTY"; ws["A1"].font = H1
ws["A2"] = "Warranty (blue) = CY2025 warranty parts value, qty × ISZE price (EUR). CV from Warranty_CV_2025.xlsx (ITUK/UTI sheets + Sheet4 country pivot); LCV now split per distributor from Warranty_LCV_2025.xlsx ExportClaimAssessment × Sheet2 price (99.8% of pieces priced). Per-DB breakdown + caveats: Data\\Warranty_CY2025_by_DB.md. Exceptions: UMI (Israel LCV) absent from file = 0 (gap, not true zero); Ireland/Portugal CV = truck price-map lower bound."; ws["A2"].font = SMALL
ws["A3"] = "VERIFIED 2026-06-11: ERP net sales contain NO separate warranty document type (SaTy in sales_fact = SOR/VOR/RUSH/PRD only) — warranty-consumed parts are embedded in normal orders. Claim-file values are at claim price basis; ISZE-net equivalent is lower (≈ ×0.74 if ITUK GP34%/FX applies) — adjust the blue field if you want the net-level correction."; ws["A3"].font = SMALL
hdrs = ["Distributor", "Scope", "UIO 2025", "Wallet (€)", "VP Sales incl. Warranty (€)", "Warranty Parts (€) [INPUT]",
        "VP Sales ex. Warranty (€)", "GPS % incl.", "GPS % ex.", "Delta (pp)"]
for j, h in enumerate(hdrs, 1):
    c = ws.cell(4, j, h); c.font = HDR; c.fill = HDRFILL; c.border = BORDER
    c.alignment = Alignment(wrap_text=True, vertical="center")
for i, (db, scope, uio, wallet, sales) in enumerate(base):
    r = 5 + i
    ws.cell(r, 1, db).font = BOLD
    ws.cell(r, 2, scope).font = BLACK
    ws.cell(r, 3, uio).number_format = "#,##0"
    ws.cell(r, 4, wallet).number_format = "€#,##0"
    ws.cell(r, 5, sales).number_format = "€#,##0"
    cw = ws.cell(r, 6, warranty.get(db, 0)); cw.font = BLUE; cw.border = BORDER; cw.number_format = "€#,##0"
    ws.cell(r, 7, f"=E{r}-F{r}").number_format = "€#,##0"
    ws.cell(r, 8, f"=E{r}/D{r}").number_format = "0.0%"
    ws.cell(r, 9, f"=G{r}/D{r}").number_format = "0.0%"
    ws.cell(r, 10, f"=(H{r}-I{r})*100").number_format = "0.00"
    for j in range(3, 11):
        if j != 6: ws.cell(r, j).font = BLACK
tr = 5 + len(base)
ws.cell(tr, 1, "TOTAL").font = BOLD
for col, letter in ((3, "C"), (4, "D"), (5, "E"), (6, "F"), (7, "G")):
    c = ws.cell(tr, col, f"=SUM({letter}5:{letter}{tr-1})"); c.font = BOLD
    c.number_format = "#,##0" if col == 3 else "€#,##0"
ws.cell(tr, 8, f"=E{tr}/D{tr}").font = BOLD; ws.cell(tr, 8).number_format = "0.0%"
ws.cell(tr, 9, f"=G{tr}/D{tr}").font = BOLD; ws.cell(tr, 9).number_format = "0.0%"
ws.cell(tr, 10, f"=(H{tr}-I{tr})*100").font = BOLD; ws.cell(tr, 10).number_format = "0.00"
ws.cell(tr+2, 1, "Note: LCV warranty now split per distributor (2026-06-12) — IUK €1.05M, Norway €291K, Sweden €190K, Hungary €77K, Belgium €75K, etc. Still 0: UMI (Israel LCV absent from warranty file — true value unknown, so UMI ex-warranty GPS remains overstated).").font = SMALL
for j, w in enumerate([13, 17, 9, 13, 15, 14, 15, 9, 9, 9], 1):
    ws.column_dimensions[get_column_letter(j)].width = w
BASE_ROW = {db: 5 + i for i, (db, *_r) in enumerate(base)}

# ============ Sheet 4: Projection_FY2026
ws = wb.create_sheet("Projection_FY2026"); ws.sheet_view.showGridLines = False
ws["A1"] = "FY2026 PROJECTION — GPS uplift scenario (variable)"; ws["A1"].font = H1
ws["A2"] = "UIO FY2026: ISUZU_UIO_Overview_2026_v17.xlsx (2026F; ITUK from UIO projection: LD 23,210 / F+MD 963). Rates: Rate Table (adjustable). Baseline GPS: 2025 from GPS_2025_Warranty."; ws["A2"].font = SMALL
ws["A4"] = "GPS uplift vs 2025 (pp) — adjustable:"; ws["A4"].font = BOLD
up = ws.cell(4, 4, 0.01); up.font = BLUE; up.fill = YELLOW; up.border = BORDER; up.number_format = "0.0%"
UP = "$D$4"
hdrs = ["Distributor", "UIO CV LD 26", "UIO F/MD 26", "UIO LCV 26", "Wallet FY26 (€)",
        "GPS 2025 incl. warr", "GPS FY26 proj (= +uplift)", "Proj. Sales FY26 (€)",
        "Sales 2025 (€)", "Δ vs 2025 (€)",
        "GPS 2025 ex. warr", "GPS FY26 proj ex. warr", "Proj. Sales FY26 ex. warr (€)"]
for j, h in enumerate(hdrs, 1):
    c = ws.cell(6, j, h); c.font = HDR; c.fill = HDRFILL; c.border = BORDER
    c.alignment = Alignment(wrap_text=True, vertical="center")
r0 = 7
for i, (db, scope, uio, wallet, sales) in enumerate(base):
    r = r0 + i
    ld, fmd, lcv = uio26[db]
    rr = RATE_ROW[db]; br = BASE_ROW[db]
    ws.cell(r, 1, db).font = BOLD
    for j, v in ((2, ld), (3, fmd), (4, lcv)):
        c = ws.cell(r, j, v); c.font = BLUE; c.number_format = "#,##0"
    c = ws.cell(r, 5, f"='Rate Table'!C{rr}*B{r}+'Rate Table'!D{rr}*C{r}+'Rate Table'!E{rr}*D{r}"); c.font = GREEN; c.number_format = "€#,##0"
    c = ws.cell(r, 6, f"=GPS_2025_Warranty!H{br}"); c.font = GREEN; c.number_format = "0.0%"
    ws.cell(r, 7, f"=F{r}+{UP}").number_format = "0.0%"
    ws.cell(r, 8, f"=G{r}*E{r}").number_format = "€#,##0"
    c = ws.cell(r, 9, f"=GPS_2025_Warranty!E{br}"); c.font = GREEN; c.number_format = "€#,##0"
    ws.cell(r, 10, f"=H{r}-I{r}").number_format = "€#,##0;(€#,##0);-"
    c = ws.cell(r, 11, f"=GPS_2025_Warranty!I{br}"); c.font = GREEN; c.number_format = "0.0%"
    ws.cell(r, 12, f"=K{r}+{UP}").number_format = "0.0%"
    ws.cell(r, 13, f"=L{r}*E{r}").number_format = "€#,##0"
tr = r0 + len(base)
ws.cell(tr, 1, "TOTAL").font = BOLD
for col in (2, 3, 4, 5, 8, 9, 10, 13):
    letter = get_column_letter(col)
    c = ws.cell(tr, col, f"=SUM({letter}{r0}:{letter}{tr-1})"); c.font = BOLD
    c.number_format = "#,##0" if col in (2, 3, 4) else "€#,##0"
ws.cell(tr, 6, f"=I{tr}/E{tr}").font = BOLD; ws.cell(tr, 6).number_format = "0.0%"
ws.cell(tr, 7, f"=H{tr}/E{tr}").font = BOLD; ws.cell(tr, 7).number_format = "0.0%"

# ITUK vs BP block
b = tr + 3
ws.cell(b, 1, "ITUK — FY2026 LANDING vs BUSINESS PLAN").font = H1
items = [
    ("ITUK BP FY2026 retail sales (£)", 13129200, "blue", "ITUK BUSINESSPLAN.xlsx Dashboard"),
    ("ITUK gross profit on parts", 0.34, "blue", "FY2025 actual per Target Study"),
    ("GBP/EUR (IML rate)", 1.12, "blue", "Per Target Study"),
    ("BP-implied ISZE→ITUK sales (€)", 6974170.05, "blue", "Target Study plan row 2026"),
    ("Our FY26 projected ISZE→ITUK sales (€) @ uplift", f"=H{r0}", "formula", "From projection table (ITUK row, incl. warranty)"),
    ("Gap to BP (€)", f"=B{b+5}-B{b+4}", "formula", "Negative = we land below BP"),
    ("GPS needed to hit BP", f"=B{b+4}/E{r0}", "pct", "BP-implied ISZE sales ÷ FY26 wallet"),
    ("GPS uplift needed vs 2025 (pp)", f"=(B{b+7}-F{r0})*100", "num2", "Compare with the uplift input D4"),
]
for i, (label, val, kind, note) in enumerate(items):
    r = b + 1 + i
    ws.cell(r, 1, label).font = BLACK
    c = ws.cell(r, 2, val)
    c.border = BORDER
    if kind == "blue": c.font = BLUE
    else: c.font = BLACK
    if kind == "pct": c.number_format = "0.0%"
    elif kind == "num2": c.number_format = "0.00"
    elif isinstance(val, float) and val < 2: c.number_format = "0.0%" if val != 1.12 else "0.00"
    else: c.number_format = "#,##0"
    ws.cell(r, 4, note).font = SMALL
for j, w in enumerate([26, 12, 11, 11, 13, 11, 11, 13, 13, 12, 11, 11, 14], 1):
    ws.column_dimensions[get_column_letter(j)].width = w

# ITUK N35 sensitivity block (study UIO splits: 2025 N35 11,444 / N75+rest 10,747 / F+MD 877; FY26 12,345 / 10,865 / 963)
s = b + 11
ws.cell(s, 1, "ITUK — N35 SPEND/UNIT SENSITIVITY (study UIO basis)").font = H1
ws.cell(s+1, 1, "Set the N35 rate to €295.68 to mirror ITUK's Target Study assumption (£400 retail × GP34% × 1.12). Other N-series and F/MD stay adjustable.").font = SMALL
sens = [
    ("N35 rate (€/unit/yr)", 1120, True),
    ("N75 + other LD rate (€/unit/yr)", 1120, True),
    ("F/MD rate (€/unit/yr)", 1344, True),
]
for i, (label, val, blue) in enumerate(sens):
    r = s + 2 + i
    ws.cell(r, 1, label).font = BLACK
    c = ws.cell(r, 2, val); c.font = BLUE; c.border = BORDER; c.number_format = "€#,##0"
r1, r2_, r3 = s+2, s+3, s+4
calc = [
    ("Wallet 2025 (€) — N35 11,444 / rest 10,747 / F+MD 877", f"=11444*B{r1}+10747*B{r2_}+877*B{r3}", "€#,##0"),
    ("GPS 2025 on this wallet (sales €5,769,868 incl. warr)", f"=5769867.82/B{s+5}", "0.0%"),
    ("Wallet FY2026 (€) — N35 12,345 / rest 10,865 / F+MD 963", f"=12345*B{r1}+10865*B{r2_}+963*B{r3}", "€#,##0"),
    ("GPS FY26 proj (= 2025 + uplift D4)", f"=B{s+6}+{UP}", "0.0%"),
    ("Projected ISZE→ITUK FY26 (€)", f"=B{s+8}*B{s+7}", "€#,##0"),
    ("Gap to BP-implied €6,974,170", f"=B{s+9}-6974170.05", "€#,##0;(€#,##0);-"),
    ("GPS needed for BP on this wallet", f"=6974170.05/B{s+7}", "0.0%"),
    ("Uplift needed vs 2025 (pp)", f"=(B{s+11}-B{s+6})*100", "0.00"),
]
for i, (label, formula, fmt) in enumerate(calc):
    r = s + 5 + i
    ws.cell(r, 1, label).font = BLACK
    c = ws.cell(r, 2, formula); c.font = BLACK; c.border = BORDER; c.number_format = fmt

wb.save(OUT)
print("saved", OUT)

# Warranty wired per-DB (CV+LCV, qty×price) — see Data\Warranty_CY2025_by_DB.md
print(f"Warranty parts wired (CV+LCV, all {len(warranty)} DBs): EUR {sum(warranty.values()):,.0f}")
print("  UMI LCV = 0 (Israel absent from LCV file); Ireland/Portugal CV = price-map lower bound")
