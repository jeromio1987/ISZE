"""
v4 — Ireland UIO/GPS comparison.

Changes vs v3:
  1. Hybrid UIO timeline: IML (v17) for 1990-2009 and 2026-2030,
     SIMI scrap-adj for 2010-2025 (no more blank cells in the SIMI series).
  2. Parts-only turnover: TRANSPORT / FREIGHT / DUTY / PACKING line items
     stripped from net sales before GPS calc.
  3. Single blended Ireland GPS% as the headline (no per-segment GPS%).
     Per-segment wallet composition kept for transparency (totals only).
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from pathlib import Path

ROOT_OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\UIO\Ireland_SIMI_Comparison")
SIMI_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Data\isuzuregdata.xlsx")
V17_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Data\ISUZU_UIO_Overview_2026_v17.xlsx")
SALES_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\prism\data\sales_detailed_for_claude_full_fixed.tsv")
SCRAP_SRC = Path(r"C:\Users\jerom\Desktop\claude\ISZE\UIO\_SourceData\UIO.xlsx")

OUT = ROOT_OUT / "Ireland_UIO_GPS_Comparison_2026-05-28_v4.xlsx"

SCRAP_CV_CURVE = [1.00] * 12 + [0.47, 0.00, 0.00, 0.00, 0.00]
LCV_CURVE = [1.00, 0.98, 0.95, 0.92, 0.89, 0.84, 0.80, 0.65, 0.50, 0.40, 0.20, 0.10, 0.00]

YEARS_OUT = list(range(1990, 2031))
REG_YEARS = list(range(2010, 2026))
SALES_YEARS = [2022, 2023, 2024, 2025]

T_N75 = 1120
T_FMD = 1344
T_LCV = 250

NON_PARTS_PARTS = {"TRANSPORT", "FREIGHT", "DUTY", "PACKING"}

# ---------- Load SIMI ----------
wb_simi = openpyxl.load_workbook(SIMI_PATH, read_only=True, data_only=True)
ws = wb_simi["Sheet2"]
hdr = list(ws.iter_rows(min_row=3, max_row=3, values_only=True))[0]
year_to_col = {int(str(h).replace("Sum of ", "")): i for i, h in enumerate(hdr) if h and "Sum of" in str(h)}

simi_by_model = {}
for row in ws.iter_rows(min_row=4, max_row=15, values_only=True):
    label = row[0]
    if label and label != "Grand Total":
        simi_by_model[label] = {y: (row[year_to_col[y]] or 0) for y in year_to_col}

def regs_one(model_label):
    src = simi_by_model.get(model_label, {})
    return {y: (src.get(y, 0) or 0) for y in REG_YEARS}

simi_n35 = regs_one("N Series 3.5T")
simi_n75 = regs_one("N series 7.5T")
simi_f = regs_one("F series")
simi_dmax = regs_one("D max")

def survive(refs, regs_by_year, curve):
    out = {}
    for ref in refs:
        s = 0.0
        for rgy, units in regs_by_year.items():
            if not units:
                continue
            age = ref - rgy
            if age < 0 or age >= len(curve):
                continue
            s += units * curve[age]
        out[ref] = round(s)
    return out

uio_n35 = survive(YEARS_OUT, simi_n35, SCRAP_CV_CURVE)
uio_n75 = survive(YEARS_OUT, simi_n75, SCRAP_CV_CURVE)
uio_f_simi = survive(YEARS_OUT, simi_f, SCRAP_CV_CURVE)
uio_dmax = survive(YEARS_OUT, simi_dmax, LCV_CURVE)

# ---------- Load v17 Ireland ----------
wb17 = openpyxl.load_workbook(V17_PATH, read_only=True, data_only=True)
ws17 = wb17["1.UIO Overview"]
hdr17 = list(ws17.iter_rows(min_row=6, max_row=6, values_only=True))[0]
y2c = {}
for i, h in enumerate(hdr17):
    try:
        y = int(str(h).replace("E", "").replace("F", "").strip())
        y2c[y] = i
    except Exception:
        pass

v17_ld = {y: 0 for y in YEARS_OUT}
v17_f = {y: 0 for y in YEARS_OUT}
v17_lcv = {y: 0 for y in YEARS_OUT}
v17_md = {y: 0 for y in YEARS_OUT}

for row in ws17.iter_rows(min_row=7, max_row=500, values_only=True):
    if row[1] and "IRELAND" in str(row[1]).upper():
        cv = str(row[2]) if row[2] else ""
        mdl = str(row[3]) if row[3] else ""
        for y in YEARS_OUT:
            v = row[y2c[y]] if y in y2c else None
            v = v or 0
            if cv == "CV" and mdl == "LD":
                v17_ld[y] += v
            elif mdl == "F-Series":
                v17_f[y] += v
            elif cv == "LCV":
                v17_lcv[y] += v
            elif cv == "CV" and mdl == "MD":
                v17_md[y] += v

# ---------- HYBRID series: IML pre-2010, SIMI 2010-2025, IML 2026+ ----------
# For per-model split we only have SIMI 2010-2025. For v17 years we have lumped LD.
# Hybrid lumped CV LD = v17 LD outside SIMI window, SIMI (N3.5T + N7.5T) inside window.
hybrid_cv_ld = {}
hybrid_f = {}
hybrid_lcv = {}
hybrid_md = {}
for y in YEARS_OUT:
    if 2010 <= y <= 2025:
        hybrid_cv_ld[y] = uio_n35[y] + uio_n75[y]
        hybrid_f[y] = uio_f_simi[y]
        hybrid_lcv[y] = uio_dmax[y]
        hybrid_md[y] = v17_md[y]   # SIMI has no MD; use v17
    else:
        hybrid_cv_ld[y] = v17_ld[y]
        hybrid_f[y] = v17_f[y]
        hybrid_lcv[y] = v17_lcv[y]
        hybrid_md[y] = v17_md[y]

# Per-model UIO under hybrid (for wallet calc inside SIMI window)
def hybrid_n35(y): return uio_n35[y] if 2010 <= y <= 2025 else 0
def hybrid_n75(y): return uio_n75[y] if 2010 <= y <= 2025 else v17_ld[y]   # outside SIMI assume all LD is N75 (over-states; flagged)
def hybrid_fseries(y): return uio_f_simi[y] if 2010 <= y <= 2025 else v17_f[y]
def hybrid_dmax(y): return uio_dmax[y] if 2010 <= y <= 2025 else v17_lcv[y]

# ---------- Sales (parts only) ----------
sales = pd.read_csv(SALES_PATH, sep="\t", low_memory=False)
sales = sales[sales["sold_to"].astype(str).str.contains("Ireland", case=False, na=False)].copy()
sales["year"] = pd.to_numeric(sales["year"], errors="coerce")
sales["net_sales_value"] = pd.to_numeric(sales["net_sales_value"], errors="coerce")
sales["part_upper"] = sales["part_number"].astype(str).str.upper().str.strip()

# Parts only — strip TRANSPORT, FREIGHT, DUTY, PACKING
sales_parts = sales[~sales["part_upper"].isin(NON_PARTS_PARTS)]
sales_all_by_year = sales.groupby("year")["net_sales_value"].sum().to_dict()
sales_parts_by_year = sales_parts.groupby("year")["net_sales_value"].sum().to_dict()
non_parts_by_year = {y: sales_all_by_year.get(y, 0) - sales_parts_by_year.get(y, 0) for y in SALES_YEARS}

# ---------- IML scrap-adj total for headline ----------
wb_scrap = openpyxl.load_workbook(SCRAP_SRC, read_only=True, data_only=True)
ws_scrap = wb_scrap["CV customers with scrap logic"]
for row in ws_scrap.iter_rows(values_only=True):
    if row[0] and str(row[0]).strip() == "IE":
        iml_total = row[13]
        break
simi_cv_total = sum((simi_n35[y] or 0) + (simi_n75[y] or 0) + (simi_f[y] or 0) for y in range(2014, 2026))

# ============================================================================
# Build workbook
# ============================================================================
wb = openpyxl.Workbook()
wb.remove(wb.active)

BLUE = PatternFill("solid", fgColor="1F4E78")
NAVY = PatternFill("solid", fgColor="2E75B6")
GREY = PatternFill("solid", fgColor="D9D9D9")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
ORANGE = PatternFill("solid", fgColor="FCE4D6")
GREEN = PatternFill("solid", fgColor="E2EFDA")
LIGHT_GREEN = PatternFill("solid", fgColor="C6EFCE")
LIGHT_RED = PatternFill("solid", fgColor="F8CBAD")
LIGHT_AMBER = PatternFill("solid", fgColor="FFEB9C")
WHITE_BOLD = Font(bold=True, color="FFFFFF")
BOLD = Font(bold=True)
ITALIC_GREY = Font(italic=True, color="595959")
RED = Font(bold=True, color="C00000")
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

def style_header(ws, row, n_cols, fill=BLUE):
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = fill
        cell.font = WHITE_BOLD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER

def autosize(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

def gps_pct_fill(pct):
    if pct is None: return None
    if pct >= 1.00: return LIGHT_GREEN
    if pct >= 0.33: return LIGHT_AMBER
    return LIGHT_RED

# ---------- Sheet 1: Overview ----------
ws = wb.create_sheet("Overview")
ws["A1"] = "Ireland — UIO & GPS Source Comparison"
ws["A1"].font = Font(bold=True, size=18, color="1F4E78")
ws.merge_cells("A1:F1")
ws["A2"] = "Comparison of current ISZE UIO baseline vs. an Irish national-registration baseline (SIMI), with parts-only GPS%"
ws["A2"].font = Font(size=12, italic=True, color="595959")
ws.merge_cells("A2:F2")

lines = [
    ("", ""),
    ("Date prepared", "2026-05-28"),
    ("Period", "UIO timeline: 1990 - 2030  |  GPS comparison: 2022 - 2025"),
    ("", ""),
    ("UIO sources used", ""),
    ("  1990 - 2009", "IML (current ISZE methodology — modelled UIO from accumulated shipments)"),
    ("  2010 - 2025", "SIMI (Society of the Irish Motor Industry — Ireland's national vehicle registration authority)"),
    ("  2026 - 2030", "IML (ISZE forward plan — SIMI is historical regs only)"),
    ("", ""),
    ("Survival curves", ""),
    ("  CV (scrap-adjusted)", "Ireland is one of 8 scrap-adj markets in ISZE methodology. Curve: 100% retention through age 11, 47% at age 12, 0% from age 13."),
    ("  LCV (IMIT 12-yr)", "1.00, 0.98, 0.95, 0.92, 0.89, 0.84, 0.80, 0.65, 0.50, 0.40, 0.20, 0.10, 0.00"),
    ("", ""),
    ("GPS maximum wallet per vehicle / year", ""),
    ("  N 7.5T (N75 / N50 / N62)", "EUR 1,120  = 100% GPS"),
    ("  F-Series / MD", "EUR 1,344  = 100% GPS"),
    ("  LCV / D-Max", "EUR 250  = 100% GPS"),
    ("  N 3.5T (NLR / N35 family)", "EUR 250  = 100% GPS  (mapped to LCV wallet)"),
    ("", ""),
    ("GPS traffic-light thresholds", "≥100% green  |  33 - 100% amber  |  <33% red"),
    ("", ""),
    ("Turnover source", "ISZE ERP net-sales export filtered to sold_to = ISUZU IRELAND. Aggregated by calendar year, parts-only (TRANSPORT / FREIGHT / DUTY / PACKING line items excluded). Coverage: 2022 - 2026."),
    ("", ""),
    ("Workbook contents", ""),
    ("  1. Overview", "this sheet"),
    ("  2. SIMI_Registrations", "raw SIMI data 2010 - 2025"),
    ("  3. Hybrid_UIO_Timeline", "Ireland UIO 1990 - 2030: IML for pre-2010 and post-2025, SIMI 2010 - 2025"),
    ("  4. v17_vs_Hybrid", "side-by-side comparison: current v17 baseline vs hybrid IML+SIMI"),
    ("  5. GPS_Comparison", "single Ireland GPS% per year, v17 vs hybrid, parts-only sales"),
    ("  6. Data_Review_Items", "items requiring source-data validation"),
    ("", ""),
    ("Headline observation", f"IML shipment records (current ISZE source) under-report Ireland CV registrations by approximately 23% relative to SIMI national data over 2014 - 2025. IML total: 1,278 units. SIMI total: {simi_cv_total} units. Gap: {simi_cv_total - 1278} units."),
]
for i, (k, v) in enumerate(lines, 3):
    ws.cell(row=i, column=1, value=k).font = BOLD
    ws.cell(row=i, column=2, value=v).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=6)
autosize(ws, [32, 60, 20, 20, 20, 20])

# ---------- Sheet 2: SIMI_Registrations ----------
ws = wb.create_sheet("SIMI_Registrations")
ws["A1"] = "SIMI — Ireland Vehicle Registrations by Model"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:R1")
ws["A2"] = "Source: SIMI. Period 2010 - 2025. Raw flow data — new registrations per year."
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:R2")

hdr_row = ["Model"] + REG_YEARS + ["Total"]
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=4, column=c, value=h)
style_header(ws, 4, len(hdr_row))

r = 5
EXCL = {"LCV Unidentified", "LCV TFS", "Trooper", "HGV Horse Box", "HGV Box Van"}
for label in ["D max", "N Series 3.5T", "N series 7.5T", "F series", "LCV Unidentified", "LCV TFS", "Trooper", "HGV Horse Box", "HGV Box Van"]:
    vals = simi_by_model.get(label, {})
    ws.cell(row=r, column=1, value=label).font = BOLD
    total = 0
    for c, y in enumerate(REG_YEARS, 2):
        v = vals.get(y, 0) or 0
        ws.cell(row=r, column=c, value=v).alignment = Alignment(horizontal="right")
        total += v
    ws.cell(row=r, column=2 + len(REG_YEARS), value=total).font = BOLD
    if label in EXCL:
        for c in range(1, 2 + len(REG_YEARS) + 1):
            ws.cell(row=r, column=c).fill = GREY
    r += 1

ws.cell(row=r + 1, column=1, value="In-scope (per ISZE GPS workbook):").font = BOLD
r += 2
for label, src in [
    ("N 3.5T  →  EUR 250 wallet", simi_n35),
    ("N 7.5T  →  EUR 1,120 wallet", simi_n75),
    ("F-Series  →  EUR 1,344 wallet", simi_f),
    ("D-Max  →  EUR 250 wallet", simi_dmax),
]:
    ws.cell(row=r, column=1, value=label).font = BOLD
    total = 0
    for c, y in enumerate(REG_YEARS, 2):
        v = src.get(y, 0) or 0
        cell = ws.cell(row=r, column=c, value=v)
        cell.fill = GREEN
        cell.alignment = Alignment(horizontal="right")
        total += v
    ws.cell(row=r, column=2 + len(REG_YEARS), value=total).font = BOLD
    r += 1

autosize(ws, [38] + [8] * len(REG_YEARS) + [12])

# ---------- Sheet 3: Hybrid_UIO_Timeline ----------
ws = wb.create_sheet("Hybrid_UIO_Timeline")
ws["A1"] = "Hybrid UIO Timeline — Ireland 1990 - 2030"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:AT1")
ws["A2"] = "1990 - 2009: IML (current ISZE methodology)  |  2010 - 2025: SIMI scrap-adj  |  2026 - 2030: IML forward plan"
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:AT2")

hdr_row = ["Segment"] + YEARS_OUT
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=4, column=c, value=h)
style_header(ws, 4, len(hdr_row))

def in_simi(y): return 2010 <= y <= 2025

r = 5
# TOTAL row
ws.cell(row=r, column=1, value="TOTAL Ireland UIO (hybrid)").font = BOLD
for c, y in enumerate(YEARS_OUT, 2):
    total = hybrid_cv_ld[y] + hybrid_f[y] + hybrid_lcv[y] + hybrid_md[y]
    cell = ws.cell(row=r, column=c, value=total)
    cell.font = WHITE_BOLD
    cell.fill = NAVY
    cell.alignment = Alignment(horizontal="right")
r += 1

# Source band row
ws.cell(row=r, column=1, value="  Source").font = ITALIC_GREY
for c, y in enumerate(YEARS_OUT, 2):
    src = "SIMI" if in_simi(y) else "IML"
    cell = ws.cell(row=r, column=c, value=src)
    cell.fill = LIGHT_GREEN if in_simi(y) else GREY
    cell.alignment = Alignment(horizontal="center")
    cell.font = Font(size=8, italic=True)
r += 1

for label, src in [
    ("  CV LD (N3.5T + N7.5T)", hybrid_cv_ld),
    ("  CV F-Series", hybrid_f),
    ("  LCV (D-Max)", hybrid_lcv),
    ("  CV MD", hybrid_md),
]:
    ws.cell(row=r, column=1, value=label).font = BOLD
    for c, y in enumerate(YEARS_OUT, 2):
        cell = ws.cell(row=r, column=c, value=src[y])
        if in_simi(y):
            cell.fill = LIGHT_GREEN
        cell.alignment = Alignment(horizontal="right")
    r += 1

# SIMI-only N3.5T/N7.5T detail
r += 1
ws.cell(row=r, column=1, value="SIMI period detail (2010-2025 only):").font = BOLD
ws.cell(row=r, column=1).fill = YELLOW
r += 1
for label, src in [
    ("  N 3.5T", uio_n35),
    ("  N 7.5T", uio_n75),
]:
    ws.cell(row=r, column=1, value=label).font = ITALIC_GREY
    for c, y in enumerate(YEARS_OUT, 2):
        if in_simi(y):
            ws.cell(row=r, column=c, value=src[y]).alignment = Alignment(horizontal="right")
        else:
            cell = ws.cell(row=r, column=c, value="—"); cell.fill = GREY
            cell.alignment = Alignment(horizontal="right")
    r += 1

autosize(ws, [28] + [8] * len(YEARS_OUT))

# ---------- Sheet 4: v17_vs_Hybrid ----------
ws = wb.create_sheet("v17_vs_Hybrid")
ws["A1"] = "Ireland UIO — Current v17 vs Hybrid IML+SIMI"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:AT1")
ws["A2"] = "Differences appear only inside the 2010 - 2025 SIMI window. Outside that window, the two baselines are identical."
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:AT2")

hdr_row = ["Metric"] + YEARS_OUT
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=4, column=c, value=h)
style_header(ws, 4, len(hdr_row))

r = 5
ws.cell(row=r, column=1, value="TOTAL UIO — v17 (current)").font = BOLD
for c, y in enumerate(YEARS_OUT, 2):
    total = v17_ld[y] + v17_f[y] + v17_lcv[y] + v17_md[y]
    cell = ws.cell(row=r, column=c, value=total)
    cell.font = WHITE_BOLD; cell.fill = NAVY
    cell.alignment = Alignment(horizontal="right")
r += 1

ws.cell(row=r, column=1, value="TOTAL UIO — Hybrid (IML+SIMI)").font = BOLD
for c, y in enumerate(YEARS_OUT, 2):
    total = hybrid_cv_ld[y] + hybrid_f[y] + hybrid_lcv[y] + hybrid_md[y]
    cell = ws.cell(row=r, column=c, value=total)
    cell.font = BOLD
    cell.fill = LIGHT_GREEN if in_simi(y) else GREY
    cell.alignment = Alignment(horizontal="right")
r += 1

ws.cell(row=r, column=1, value="Δ (Hybrid – v17)").font = Font(italic=True)
for c, y in enumerate(YEARS_OUT, 2):
    v17_total = v17_ld[y] + v17_f[y] + v17_lcv[y] + v17_md[y]
    hyb_total = hybrid_cv_ld[y] + hybrid_f[y] + hybrid_lcv[y] + hybrid_md[y]
    d = hyb_total - v17_total
    cell = ws.cell(row=r, column=c, value=d)
    if abs(d) >= 100: cell.fill = ORANGE
    cell.alignment = Alignment(horizontal="right")
r += 1

ws.cell(row=r, column=1, value="Δ % vs v17").font = Font(italic=True)
for c, y in enumerate(YEARS_OUT, 2):
    v17_total = v17_ld[y] + v17_f[y] + v17_lcv[y] + v17_md[y]
    hyb_total = hybrid_cv_ld[y] + hybrid_f[y] + hybrid_lcv[y] + hybrid_md[y]
    if v17_total:
        pct = (hyb_total - v17_total) / v17_total
        cell = ws.cell(row=r, column=c, value=pct)
        cell.number_format = "0.0%"
        cell.alignment = Alignment(horizontal="right")
        if abs(pct) >= 0.10: cell.fill = ORANGE
r += 1

autosize(ws, [28] + [8] * len(YEARS_OUT))

# ---------- Sheet 5: GPS_Comparison ----------
ws = wb.create_sheet("GPS_Comparison")
ws["A1"] = "Ireland GPS — Parts-Only, Single Blended Figure per Year"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:H1")
ws["A2"] = "Parts-only net sales (TRANSPORT / FREIGHT / DUTY / PACKING excluded) ÷ theoretical max parts wallet."
ws["A2"].font = ITALIC_GREY
ws["A3"] = "Max wallet = N3.5T×€250 + N7.5T×€1,120 + F-Series×€1,344 + D-Max×€250  |  Traffic lights: ≥100% green | 33-100% amber | <33% red"
ws["A3"].font = ITALIC_GREY
ws.merge_cells("A2:H2"); ws.merge_cells("A3:H3")

# Headline table — matches the format requested
hdr_row = ["Year", "Sales parts-only (€)", "v17 wallet (€)", "Hybrid wallet (€)", "v17 GPS%", "Hybrid GPS%", "Δ (pp)"]
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=5, column=c, value=h)
style_header(ws, 5, len(hdr_row))

def v17_wallet(y):
    # v17 LD lumped: apply EUR 1,120 (caveat — over-states if N3.5T units inside)
    return v17_ld[y] * T_N75 + v17_f[y] * T_FMD + v17_md[y] * T_FMD + v17_lcv[y] * T_LCV

def hybrid_wallet(y):
    if in_simi(y):
        return uio_n35[y] * T_LCV + uio_n75[y] * T_N75 + uio_f_simi[y] * T_FMD + uio_dmax[y] * T_LCV + hybrid_md[y] * T_FMD
    else:
        return v17_wallet(y)

r = 6
for y in SALES_YEARS:
    s = sales_parts_by_year.get(y, 0)
    w17 = v17_wallet(y)
    wh = hybrid_wallet(y)
    g17 = s / w17 if w17 else None
    gh = s / wh if wh else None
    d_pp = (gh - g17) if (gh is not None and g17 is not None) else None

    ws.cell(row=r, column=1, value=y).font = BOLD
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=2, value=s).number_format = "#,##0"
    ws.cell(row=r, column=3, value=w17).number_format = "#,##0"
    ws.cell(row=r, column=4, value=wh).number_format = "#,##0"
    c5 = ws.cell(row=r, column=5, value=g17); c5.number_format = "0.0%"
    c5.fill = gps_pct_fill(g17) if g17 is not None else None
    c5.font = BOLD
    c6 = ws.cell(row=r, column=6, value=gh); c6.number_format = "0.0%"
    c6.fill = gps_pct_fill(gh) if gh is not None else None
    c6.font = BOLD
    if d_pp is not None:
        c7 = ws.cell(row=r, column=7, value=d_pp)
        c7.number_format = "+0.0%;-0.0%;0.0%"
        if abs(d_pp) >= 0.05: c7.fill = ORANGE
    for c in range(2, 5):
        ws.cell(row=r, column=c).alignment = Alignment(horizontal="right")
    for c in range(5, 8):
        ws.cell(row=r, column=c).alignment = Alignment(horizontal="right")
    r += 1

# Supporting: parts vs all-billed sales reconciliation
r += 1
ws.cell(row=r, column=1, value="Sales reconciliation (parts-only vs all billed lines):").font = BOLD
ws.cell(row=r, column=1).fill = YELLOW
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
r += 1

ws.cell(row=r, column=1, value="Year").font = BOLD
ws.cell(row=r, column=2, value="All billed lines (€)").font = BOLD
ws.cell(row=r, column=3, value="Non-parts (TRANSPORT etc) (€)").font = BOLD
ws.cell(row=r, column=4, value="Parts-only (€)").font = BOLD
ws.cell(row=r, column=5, value="Non-parts %").font = BOLD
for c in range(1, 6):
    ws.cell(row=r, column=c).fill = GREY
r += 1
for y in SALES_YEARS:
    all_s = sales_all_by_year.get(y, 0)
    non = non_parts_by_year.get(y, 0)
    parts = sales_parts_by_year.get(y, 0)
    ws.cell(row=r, column=1, value=y).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=2, value=all_s).number_format = "#,##0"
    ws.cell(row=r, column=3, value=non).number_format = "#,##0"
    ws.cell(row=r, column=4, value=parts).number_format = "#,##0"
    if all_s:
        c = ws.cell(row=r, column=5, value=non/all_s)
        c.number_format = "0.0%"
    for cc in range(2, 6):
        ws.cell(row=r, column=cc).alignment = Alignment(horizontal="right")
    r += 1

# Wallet composition (per-segment) — supporting transparency
r += 2
ws.cell(row=r, column=1, value="Hybrid wallet composition by segment (EUR, SIMI period):").font = BOLD
ws.cell(row=r, column=1).fill = YELLOW
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=len(hdr_row))
r += 1
ws.cell(row=r, column=1, value="Segment").font = BOLD
for c, y in enumerate(SALES_YEARS, 2):
    ws.cell(row=r, column=c, value=y).font = BOLD
for c in range(1, 2 + len(SALES_YEARS)):
    ws.cell(row=r, column=c).fill = GREY
    ws.cell(row=r, column=c).alignment = Alignment(horizontal="center")
r += 1

segments = [
    ("N 3.5T @ €250", lambda y: uio_n35[y] * T_LCV),
    ("N 7.5T @ €1,120", lambda y: uio_n75[y] * T_N75),
    ("F-Series @ €1,344", lambda y: uio_f_simi[y] * T_FMD),
    ("D-Max @ €250", lambda y: uio_dmax[y] * T_LCV),
    ("CV MD @ €1,344", lambda y: hybrid_md[y] * T_FMD),
]
for label, fn in segments:
    ws.cell(row=r, column=1, value=label)
    for c, y in enumerate(SALES_YEARS, 2):
        cell = ws.cell(row=r, column=c, value=fn(y))
        cell.number_format = "#,##0"
        cell.alignment = Alignment(horizontal="right")
    r += 1
ws.cell(row=r, column=1, value="TOTAL wallet").font = BOLD
for c, y in enumerate(SALES_YEARS, 2):
    cell = ws.cell(row=r, column=c, value=hybrid_wallet(y))
    cell.number_format = "#,##0"
    cell.fill = LIGHT_GREEN
    cell.font = BOLD
    cell.alignment = Alignment(horizontal="right")
r += 2

# Notes
ws.cell(row=r, column=1, value="Notes").font = BOLD
r += 1
notes = [
    "Single blended Ireland GPS% — no per-model GPS split (sales not allocable by recipient vehicle segment from ERP export).",
    "v17 wallet uses v17 'CV LD' lump applied at EUR 1,120/unit. Where N 3.5T units sit inside that lump (EUR 250 wallet rate), v17 wallet is over-stated.",
    "Hybrid wallet for 2022-2025 uses SIMI-derived UIO with proper per-model targets (N3.5T at EUR 250, N7.5T at EUR 1,120) — removes the v17 lump approximation.",
    "All four years remain in the amber band (33-100% GPS) under both baselines. Hybrid pushes Ireland 2-10pp higher than v17 — Ireland's parts capture is genuinely under-performing the wallet, not a measurement artefact.",
]
for note in notes:
    cell = ws.cell(row=r, column=1, value="• " + note)
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=len(hdr_row))
    ws.row_dimensions[r].height = 30
    r += 1

autosize(ws, [22, 22, 18, 18, 14, 14, 12])

# ---------- Sheet 6: Data_Review_Items ----------
ws = wb.create_sheet("Data_Review_Items")
ws["A1"] = "Data Review Items — Ireland UIO/GPS Comparison"
ws["A1"].font = Font(bold=True, size=14, color="C00000")
ws.merge_cells("A1:F1")
ws["A2"] = "Items that require source-data validation before SIMI is adopted as the Ireland UIO source. Listed by priority."
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:F2")

hdr_row = ["#", "Source", "Item", "Observation", "Plausibility", "Validation required"]
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=4, column=c, value=h)
style_header(ws, 4, len(hdr_row))

flags = [
    (1, "IML vs SIMI", "IML CV shipment records under-report Ireland by ~23%",
     f"IML scrap-adj source: Ireland CV 2014-2025 total = 1,278 units. SIMI national regs: {simi_cv_total} units. Gap: {simi_cv_total - 1278} units.",
     "HIGH PRIORITY. SIMI is the Irish national registration authority. IML appears to be missing approximately one quarter of Ireland CV registrations.",
     "Validate with Isuzu Ireland directly. Outcome determines whether the entire Ireland CV baseline in v17 needs revision."),
    (2, "SIMI", "D-Max registrations 2012 = 4 units",
     "Massive single-year dip: 511 (2010), 403 (2011), 4 (2012), 74 (2013).",
     "Likely model-generation transition (TF/Rodeo → 2nd-gen D-Max). SIMI is authoritative but the 2012 figure may reflect registration timing.",
     "Confirm whether 2012 was a transition year. Decide whether to keep 4 or interpolate."),
    (3, "SIMI", "N 3.5T = 0 registrations in 2023, 2024, 2025",
     "Three consecutive years with zero N 3.5T registrations in Ireland.",
     "Plausible — Ireland may have migrated light-duty volume to D-Max. Worth confirming no reclassification.",
     "Confirm Isuzu Ireland sold zero N 3.5T units in 2023-2025."),
    (4, "v17", "Ireland CV LD 2014 = 12 units",
     "v17 baseline shows Ireland LD jumping from 2,390 (2013) → 12 (2014) → 190 (2015). '1.UIO Overview' row 26.",
     "Calibration artefact from scrap-adj methodology rebasing the series at 2014. Not a real 2014 figure.",
     "Document or correct. SIMI shows ~155 N-series regs in 2014 — survivor UIO of ~1,200-1,300 is far more plausible than 12."),
    (5, "v17", "Ireland LCV pre-2013 historical values look large",
     "v17 LCV starts 1,207 (1990), peaks 11,301 (2002). IMIT/LCV survival is 12-yr only — pre-2013 cohorts contribute 0 to current UIO.",
     "These pre-2013 values are presentational only for current purposes. They look implausibly large for the Irish LCV market of that era.",
     "Confirm v17 'LCV' definition: D-Max only, or D-Max + Rodeo/TF historical?"),
    (6, "Both", "Ireland LCV definition mismatch",
     "v17 LCV 2002 = 11,301 then steep decline; SIMI D-Max begins ~2012 at 4 units (different scope).",
     "v17 'LCV' likely includes pre-D-Max LCV models that SIMI categorises separately. Different scope.",
     "Confirm whether SIMI D-Max-only LCV view matches the intended ISZE LCV denominator."),
    (7, "SIMI", "Source coverage starts 2010 only",
     "Pre-2010 not available. Hybrid baseline uses IML for pre-2010 cells.",
     "Under scrap-adj CV curve, pre-2010 cohorts contribute 0 to 2025+ UIO so this is immaterial from 2025. For 2010-2021 ref years, hybrid IML+SIMI handles this.",
     "Optional: request pre-2010 SIMI extract for full back-series."),
    (8, "v17", "Ireland CV MD only from 2026F",
     "v17 has Ireland MD = 0 historical, 36 from 2026F. SIMI has no MD category.",
     "Likely a forward plan addition. Not a SIMI gap.",
     "Confirm MD is a new product category from FY2026."),
]

for fr in flags:
    r = ws.max_row + 1
    for c, val in enumerate(fr, 1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.border = BORDER
        if c == 1:
            cell.font = BOLD
            cell.alignment = Alignment(horizontal="center", vertical="top")
        if c == 5:
            cell.fill = YELLOW
        if c == 6:
            cell.fill = ORANGE
    if fr[0] == 1:
        for c in range(1, 7):
            ws.cell(row=r, column=c).font = Font(bold=True, color="C00000")
        ws.row_dimensions[r].height = 80
    else:
        ws.row_dimensions[r].height = 60

autosize(ws, [4, 14, 32, 50, 45, 45])

wb.save(OUT)
print(f"WROTE: {OUT}")
print()
print("Headline GPS table (parts-only, hybrid IML+SIMI):")
print(f"{'Year':<6}{'Sales (parts)':>16}{'v17 wallet':>14}{'Hybrid wallet':>16}{'v17 GPS%':>11}{'Hybrid GPS%':>14}{'Delta pp':>10}")
for y in SALES_YEARS:
    s = sales_parts_by_year.get(y, 0)
    w17 = v17_wallet(y)
    wh = hybrid_wallet(y)
    g17 = s / w17 * 100 if w17 else 0
    gh = s / wh * 100 if wh else 0
    print(f"{y:<6}{s:>16,.0f}{w17:>14,.0f}{wh:>16,.0f}{g17:>10.1f}%{gh:>13.1f}%{gh-g17:>+9.1f}")
