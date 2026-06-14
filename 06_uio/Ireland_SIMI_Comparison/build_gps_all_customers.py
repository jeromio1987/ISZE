"""
ISZE GPS — All Customers, recomputed under per-model wallet methodology.

Inputs:
  - v17 UIO (ISUZU_UIO_Overview_2026_v17.xlsx, sheet '1.UIO Overview')
  - Sales TSV (parts-only after TRANSPORT/FREIGHT/DUTY/PACKING strip)
  - Per-model GPS targets (gps_model_targets.csv):
      N 7.5T (CV LD)       EUR 1,120 / unit / year
      F-Series / CV MD     EUR 1,344 / unit / year
      LCV / D-Max          EUR 250 / unit / year

Notes:
  - v17 lumps N 3.5T into CV LD. This script applies EUR 1,120 to the whole
    CV LD bucket. To the extent N 3.5T units are inside the LD lump (a small
    share for most distributors), the wallet is slightly over-stated, so the
    resulting GPS% is slightly under-stated. Flagged in each sheet.
  - Segment-only scope: ITUK = CV only, IUK = LCV only, UTI = CV only,
    UMI = LCV only (per current ISZE distributor scoping).
  - Excluded entities: MIDI Europe (no ISZE direct sales / UIO not usable),
    Germany Service (internal), IML Internal, Russia, Forlog, Luxembourg,
    Netherlands (folded into Belgium).
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from pathlib import Path

V17_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Data\ISUZU_UIO_Overview_2026_v17.xlsx")
SALES_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\prism\data\sales_detailed_for_claude_full_fixed.tsv")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\UIO\Ireland_SIMI_Comparison\ISZE_GPS_AllCustomers_2026-05-28.xlsx")

T_N75 = 1120
T_FMD = 1344
T_LCV = 250
NON_PARTS = {"TRANSPORT", "FREIGHT", "DUTY", "PACKING"}
SALES_YEARS = [2022, 2023, 2024, 2025]

# v17 distributor label -> canonical distributor code
V17_DIST_TO_CODE = {
    "UTI": "UTI", "UMI": "UMI",
    "BL": "ICELAND", "RSA": "NORWAY",
    "Isuzu Sverige": "SWEDEN", "Isuzu Denmark": "DENMARK",
    "ITUK": "ITUK", "IUK": "IUK",
    "Isuzu Ireland": "IRELAND",
    "IBX": "BELGIUM",
    "ISD-Lang": "GERMANY",
    "Imotors": "PORTUGAL",
    "GasanZammit": "MALTA",
    "Nordic Auto.": "FINLAND",
    "AutoWallis": "HUNGARY",
    "Petros Petropoulos": "GREECE",
    "Isuzu Rom Auto": "ROMANIA",
    "Loutsios & Sons": "CYPRUS",
}

# Sales sold_to -> distributor code
SOLD_TO_TO_CODE = {
    "ISUZU TRUCK (UK) LIMITED": "ITUK",
    "ISUZU TRUCK UK LIMITED": "ITUK",
    "I.M. PARTS & SERVICE Limited": "IUK",
    "UNIVERSAL MOTORS ISRAEL LTD": "UMI",
    "UNIVERSAL TRUCKS ISRAEL LTD": "UTI",
    "ISUZU IRELAND": "IRELAND",
    "ISUZU BENELUX NV": "BELGIUM",
    "ISUZU SALES DEUTSCHLAND GMBH": "GERMANY",
    "XXX ISUZU SALES DEUTSCHLAND GMBH": "GERMANY",
    "Isuzu Motors Germany GmbH": "GERMANY_SERVICE",   # excluded
    "IMOTORS - Importacao e Comercio": "PORTUGAL",
    "ISUZU SVERIGE AB": "SWEDEN",
    "ISUZU MOTORS SWEDEN AB": "SWEDEN",
    "ISUZU DANMARK A/S": "DENMARK",
    "ISUZU ROM AUTO SRL": "ROMANIA",
    "RUTEBILEIERNES STANDARDISERING AS": "NORWAY",
    "PETROS PETROPOULOS S.A. (VEHICLE)": "GREECE",
    "PETROS PETROPOULOS S.A.": "GREECE",
    "LOUTSIOS A & SONS LTD": "CYPRUS",
    "Nordic Automotive trading oy.": "FINLAND",
    "GASANZAMMIT MOTORS LTD": "MALTA",
    "AW Distribution Kft.": "HUNGARY",
    "BL. EHF.": "ICELAND",
    "MIDI EUROPE S.R.L.": "MIDI_EXCLUDE",
    "ISUZU MOTORS LIMITED": "IML_EXCLUDE",
    "JSC ISUZU RUS": "RUSSIA_EXCLUDE",
    "Forlog NV": "FORLOG_EXCLUDE",
    "KOMTRANSKOMPLEKT LLC": "KZ_EXCLUDE",
    "Grand Avto LLC": "OTHER_EXCLUDE",
    "CBC-Trans LLP": "OTHER_EXCLUDE",
    "ANADOLU ISUZU OTOMOTIV": "OTHER_EXCLUDE",
    "KIMA LATEJARET AL MARKABAT CO": "OTHER_EXCLUDE",
}

EXCLUDED = {"GERMANY_SERVICE", "MIDI_EXCLUDE", "IML_EXCLUDE", "RUSSIA_EXCLUDE",
            "FORLOG_EXCLUDE", "KZ_EXCLUDE", "OTHER_EXCLUDE"}

SEGMENT_ONLY = {"ITUK": "CV", "IUK": "LCV", "UTI": "CV", "UMI": "LCV"}

# ---------- Load v17 UIO ----------
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

# UIO per (dist_code, year, segment_key)
# segment_key in {'LD','F','MD','LCV'}
uio = {}   # (dist, year, seg) -> units
for row in ws17.iter_rows(min_row=7, max_row=500, values_only=True):
    if not row[5]:
        continue
    v17_dist = str(row[5]).strip()
    if "MIDI" in v17_dist.upper():
        continue
    dist_code = V17_DIST_TO_CODE.get(v17_dist)
    if not dist_code:
        continue
    cv = (str(row[2]) if row[2] else "").strip()
    mdl = (str(row[3]) if row[3] else "").strip()
    if cv == "CV" and mdl == "LD":
        seg = "LD"
    elif mdl == "F-Series":
        seg = "F"
    elif cv == "CV" and mdl == "MD":
        seg = "MD"
    elif cv == "LCV":
        seg = "LCV"
    else:
        continue
    for y in SALES_YEARS:
        if y not in y2c:
            continue
        v = row[y2c[y]] or 0
        if v:
            uio[(dist_code, y, seg)] = uio.get((dist_code, y, seg), 0) + v

# Apply segment-only filter; fall back to 2024 proxy when year-specific UIO is missing
PROXY_YEAR = 2024

def _raw(dist, y, seg):
    v = uio.get((dist, y, seg), 0)
    if v == 0:
        v = uio.get((dist, PROXY_YEAR, seg), 0)
    return v

def get_uio(dist, y, seg):
    if dist in SEGMENT_ONLY:
        if SEGMENT_ONLY[dist] == "CV" and seg in ("LD", "F", "MD"):
            return _raw(dist, y, seg)
        if SEGMENT_ONLY[dist] == "LCV" and seg == "LCV":
            return _raw(dist, y, seg)
        return 0
    return _raw(dist, y, seg)

def wallet(dist, y):
    return (get_uio(dist, y, "LD") * T_N75
          + get_uio(dist, y, "F")  * T_FMD
          + get_uio(dist, y, "MD") * T_FMD
          + get_uio(dist, y, "LCV") * T_LCV)

# ---------- Sales (parts-only) ----------
sales = pd.read_csv(SALES_PATH, sep="\t", low_memory=False)
sales["net_sales_value"] = pd.to_numeric(sales["net_sales_value"], errors="coerce")
sales["year"] = pd.to_numeric(sales["year"], errors="coerce")
sales["part_upper"] = sales["part_number"].astype(str).str.upper().str.strip()
sales_parts = sales[~sales["part_upper"].isin(NON_PARTS)].copy()
sales_parts["dist_code"] = sales_parts["sold_to"].map(SOLD_TO_TO_CODE)

sales_by_dy = (
    sales_parts.dropna(subset=["dist_code"])
    .groupby(["dist_code", "year"])["net_sales_value"]
    .sum()
    .to_dict()
)

# Distributors in scope = (UIO present) ∪ (sales > 0) − excluded
all_dists = set(d for (d, _, _) in uio.keys())
all_dists |= set(d for (d, _) in sales_by_dy.keys() if d not in EXCLUDED)
all_dists -= EXCLUDED

# ---------- Build workbook ----------
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
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

def style_header(ws, row, n):
    for c in range(1, n + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = BLUE; cell.font = WHITE_BOLD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER

def autosize(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

def gps_fill(pct):
    if pct is None: return None
    if pct >= 1.00: return LIGHT_GREEN
    if pct >= 0.33: return LIGHT_AMBER
    return LIGHT_RED

# ---------- Sheet 1: Overview ----------
ws = wb.create_sheet("Overview")
ws["A1"] = "ISZE GPS — All Customers (per-model wallet methodology)"
ws["A1"].font = Font(bold=True, size=18, color="1F4E78")
ws.merge_cells("A1:G1")
ws["A2"] = "GPS% recomputed using ISZE GPS workbook maximum spend per vehicle (per-model). Parts-only net sales ÷ (UIO × per-model EUR target)."
ws["A2"].font = Font(size=12, italic=True, color="595959")
ws.merge_cells("A2:G2")

lines = [
    ("", ""),
    ("Date prepared", "2026-05-28"),
    ("Period", "2022 - 2025"),
    ("", ""),
    ("Methodology", ""),
    ("  UIO source", "v17 UIO Overview (current ISZE methodology — IML + scrap-adjusted)"),
    ("  Per-model targets", "N 7.5T = EUR 1,120/unit/yr  |  F-Series / CV MD = EUR 1,344/unit/yr  |  LCV / D-Max = EUR 250/unit/yr"),
    ("  Sales", "ISZE ERP net-sales export, parts-only (TRANSPORT / FREIGHT / DUTY / PACKING excluded)"),
    ("  Segment-only", "ITUK = CV only  |  IUK = LCV only  |  UTI = CV only  |  UMI = LCV only  (per current ISZE distributor scoping)"),
    ("  Excluded entities", "MIDI Europe, Germany Service (internal), IML, Russia, Forlog, Luxembourg, Netherlands (rolled into Belgium)"),
    ("", ""),
    ("Traffic-light thresholds", "≥100% GPS = green (healthy)  |  33 - 100% = amber (at risk)  |  <33% = red (critical)"),
    ("", ""),
    ("Caveat — v17 CV LD lump", "v17 does not split N 3.5T from N 7.5T inside CV LD. This script applies EUR 1,120 to the whole CV LD bucket. Where N 3.5T units exist inside the lump (LCV-wallet at EUR 250), the wallet is slightly over-stated and resulting GPS% slightly under-stated. Materially affects Ireland and Portugal more than other markets."),
    ("", ""),
    ("Sheets in this workbook", ""),
    ("  1. Overview", "this sheet"),
    ("  2. Ranking", "all distributors ranked by 2025 GPS%, with 4-year trend"),
    ("  3. Master_Table", "wide table: each distributor × year, sales / UIO / wallet / EUR per unit / GPS%"),
    ("  4. <one sheet per distributor>", "detail per distributor: UIO by segment, wallet composition, parts sales, GPS%"),
]
for i, (k, v) in enumerate(lines, 3):
    ws.cell(row=i, column=1, value=k).font = BOLD
    ws.cell(row=i, column=2, value=v).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=7)
autosize(ws, [30, 60, 18, 18, 18, 18, 18])

# ---------- Compute master table data ----------
rows = []
for dist in sorted(all_dists):
    for y in SALES_YEARS:
        ld = get_uio(dist, y, "LD")
        fs = get_uio(dist, y, "F")
        md = get_uio(dist, y, "MD")
        lcv = get_uio(dist, y, "LCV")
        total_uio = ld + fs + md + lcv
        wal = wallet(dist, y)
        sales_v = sales_by_dy.get((dist, y), 0.0)
        eu = sales_v / total_uio if total_uio else None
        gps = sales_v / wal if wal else None
        # 2024 UIO proxy if year-specific is zero but sales exist
        rows.append({
            "dist": dist, "year": y,
            "uio_ld": ld, "uio_f": fs, "uio_md": md, "uio_lcv": lcv,
            "uio_total": total_uio,
            "wallet": wal, "sales": sales_v,
            "eur_per_unit": eu, "gps_pct": gps,
        })

dfm = pd.DataFrame(rows)

# ---------- Sheet 2: Ranking (sorted by 2025 GPS%) ----------
ws = wb.create_sheet("Ranking")
ws["A1"] = "GPS Ranking — All Distributors"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:M1")
ws["A2"] = "Sorted by 2025 GPS%, descending. Coloured by traffic light per year."
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:M2")

hdr_row = ["Distributor", "Segment scope", "2022 €/unit", "2022 GPS%",
           "2023 €/unit", "2023 GPS%", "2024 €/unit", "2024 GPS%",
           "2025 €/unit", "2025 GPS%", "Avg UIO 2024", "2025 sales (€)"]
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=4, column=c, value=h)
style_header(ws, 4, len(hdr_row))

# Rank by 2025 GPS%
rank_2025 = (dfm[dfm["year"] == 2025]
             .sort_values("gps_pct", ascending=False, na_position="last")
             .reset_index(drop=True))

r = 5
for _, rr in rank_2025.iterrows():
    dist = rr["dist"]
    scope = SEGMENT_ONLY.get(dist, "CV + LCV")
    ws.cell(row=r, column=1, value=dist).font = BOLD
    ws.cell(row=r, column=2, value=scope).alignment = Alignment(horizontal="center")
    col = 3
    for y in SALES_YEARS:
        d_row = dfm[(dfm["dist"] == dist) & (dfm["year"] == y)].iloc[0]
        eu = d_row["eur_per_unit"]
        gps = d_row["gps_pct"]
        c1 = ws.cell(row=r, column=col, value=eu if eu is not None else None)
        c1.number_format = "€#,##0"
        c1.alignment = Alignment(horizontal="right")
        col += 1
        c2 = ws.cell(row=r, column=col, value=gps if gps is not None else None)
        c2.number_format = "0.0%"
        c2.alignment = Alignment(horizontal="right")
        c2.fill = gps_fill(gps) if gps is not None else None
        c2.font = BOLD
        col += 1
    # 2024 total UIO
    d24 = dfm[(dfm["dist"] == dist) & (dfm["year"] == 2024)].iloc[0]
    ws.cell(row=r, column=col, value=d24["uio_total"]).alignment = Alignment(horizontal="right")
    col += 1
    ws.cell(row=r, column=col, value=rr["sales"]).number_format = "#,##0"
    ws.cell(row=r, column=col).alignment = Alignment(horizontal="right")
    r += 1

autosize(ws, [22, 12, 12, 11, 12, 11, 12, 11, 12, 11, 14, 16])

# ---------- Sheet 3: Master Table ----------
ws = wb.create_sheet("Master_Table")
ws["A1"] = "Master Table — Distributor × Year"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:M1")

hdr_row = ["Distributor", "Year", "UIO CV LD", "UIO F", "UIO MD", "UIO LCV", "UIO total",
           "Wallet (€)", "Sales parts (€)", "€/unit", "GPS %"]
for c, h in enumerate(hdr_row, 1):
    ws.cell(row=3, column=c, value=h)
style_header(ws, 3, len(hdr_row))

r = 4
for dist in sorted(all_dists):
    for y in SALES_YEARS:
        rr = dfm[(dfm["dist"] == dist) & (dfm["year"] == y)].iloc[0]
        ws.cell(row=r, column=1, value=dist).font = BOLD
        ws.cell(row=r, column=2, value=y).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=3, value=rr["uio_ld"])
        ws.cell(row=r, column=4, value=rr["uio_f"])
        ws.cell(row=r, column=5, value=rr["uio_md"])
        ws.cell(row=r, column=6, value=rr["uio_lcv"])
        ws.cell(row=r, column=7, value=rr["uio_total"]).font = BOLD
        ws.cell(row=r, column=8, value=rr["wallet"]).number_format = "#,##0"
        ws.cell(row=r, column=9, value=rr["sales"]).number_format = "#,##0"
        if rr["eur_per_unit"] is not None:
            c = ws.cell(row=r, column=10, value=rr["eur_per_unit"])
            c.number_format = "€#,##0"
        if rr["gps_pct"] is not None:
            c = ws.cell(row=r, column=11, value=rr["gps_pct"])
            c.number_format = "0.0%"
            c.fill = gps_fill(rr["gps_pct"])
            c.font = BOLD
        for cc in range(3, 12):
            ws.cell(row=r, column=cc).alignment = Alignment(horizontal="right")
        r += 1

autosize(ws, [22, 8, 11, 9, 9, 10, 10, 14, 14, 11, 10])

# ---------- One sheet per distributor ----------
for dist in sorted(all_dists):
    ws = wb.create_sheet(dist[:31])
    ws["A1"] = f"{dist} — GPS Detail"
    ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
    ws.merge_cells("A1:G1")
    scope = SEGMENT_ONLY.get(dist, "CV + LCV (lumped)")
    ws["A2"] = f"Segment scope: {scope}  |  Targets: N7.5T €1,120  |  F/MD €1,344  |  LCV €250"
    ws["A2"].font = ITALIC_GREY
    ws.merge_cells("A2:G2")

    # UIO block
    hdr = ["Year", "UIO CV LD", "UIO F-Series", "UIO CV MD", "UIO LCV", "UIO total"]
    for c, h in enumerate(hdr, 1):
        ws.cell(row=4, column=c, value=h)
    style_header(ws, 4, len(hdr))
    r = 5
    for y in SALES_YEARS:
        rr = dfm[(dfm["dist"] == dist) & (dfm["year"] == y)].iloc[0]
        ws.cell(row=r, column=1, value=y).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=2, value=rr["uio_ld"]).alignment = Alignment(horizontal="right")
        ws.cell(row=r, column=3, value=rr["uio_f"]).alignment = Alignment(horizontal="right")
        ws.cell(row=r, column=4, value=rr["uio_md"]).alignment = Alignment(horizontal="right")
        ws.cell(row=r, column=5, value=rr["uio_lcv"]).alignment = Alignment(horizontal="right")
        c = ws.cell(row=r, column=6, value=rr["uio_total"])
        c.font = BOLD; c.alignment = Alignment(horizontal="right")
        r += 1
    r += 1

    # Wallet composition
    ws.cell(row=r, column=1, value="Max wallet composition (UIO × target)").font = BOLD
    ws.cell(row=r, column=1).fill = YELLOW
    r += 1
    hdr2 = ["Year", "CV LD @ €1,120", "F-Series @ €1,344", "CV MD @ €1,344", "LCV @ €250", "TOTAL wallet (€)"]
    for c, h in enumerate(hdr2, 1):
        ws.cell(row=r, column=c, value=h)
    style_header(ws, r, len(hdr2))
    r += 1
    for y in SALES_YEARS:
        rr = dfm[(dfm["dist"] == dist) & (dfm["year"] == y)].iloc[0]
        ws.cell(row=r, column=1, value=y).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=2, value=rr["uio_ld"] * T_N75).number_format = "#,##0"
        ws.cell(row=r, column=3, value=rr["uio_f"] * T_FMD).number_format = "#,##0"
        ws.cell(row=r, column=4, value=rr["uio_md"] * T_FMD).number_format = "#,##0"
        ws.cell(row=r, column=5, value=rr["uio_lcv"] * T_LCV).number_format = "#,##0"
        c = ws.cell(row=r, column=6, value=rr["wallet"])
        c.number_format = "#,##0"
        c.font = BOLD
        c.fill = LIGHT_GREEN
        for cc in range(2, 7):
            ws.cell(row=r, column=cc).alignment = Alignment(horizontal="right")
        r += 1
    r += 1

    # GPS headline
    ws.cell(row=r, column=1, value="GPS headline").font = BOLD
    ws.cell(row=r, column=1).fill = YELLOW
    r += 1
    hdr3 = ["Year", "Sales parts-only (€)", "Wallet (€)", "€/unit", "GPS %", "Status"]
    for c, h in enumerate(hdr3, 1):
        ws.cell(row=r, column=c, value=h)
    style_header(ws, r, len(hdr3))
    r += 1
    for y in SALES_YEARS:
        rr = dfm[(dfm["dist"] == dist) & (dfm["year"] == y)].iloc[0]
        ws.cell(row=r, column=1, value=y).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=2, value=rr["sales"]).number_format = "#,##0"
        ws.cell(row=r, column=3, value=rr["wallet"]).number_format = "#,##0"
        if rr["eur_per_unit"] is not None:
            c = ws.cell(row=r, column=4, value=rr["eur_per_unit"]); c.number_format = "€#,##0"
        if rr["gps_pct"] is not None:
            c = ws.cell(row=r, column=5, value=rr["gps_pct"])
            c.number_format = "0.0%"
            c.fill = gps_fill(rr["gps_pct"])
            c.font = BOLD
            status = "HEALTHY" if rr["gps_pct"] >= 1.0 else ("AT RISK" if rr["gps_pct"] >= 0.33 else "CRITICAL")
            sc = ws.cell(row=r, column=6, value=status)
            sc.fill = gps_fill(rr["gps_pct"])
            sc.alignment = Alignment(horizontal="center")
            sc.font = BOLD
        for cc in range(2, 7):
            ws.cell(row=r, column=cc).alignment = Alignment(horizontal="right")
        r += 1

    autosize(ws, [20, 18, 18, 18, 18, 14])

# Save
wb.save(OUT)
print(f"WROTE: {OUT}")
print(f"Distributors in scope: {len(all_dists)}")
print()
print("Ranked by 2025 GPS%:")
print(f"{'Distributor':<18}{'Scope':<10}{'2022':>10}{'2023':>10}{'2024':>10}{'2025':>10}{'UIO 2024':>10}")
for _, rr in rank_2025.iterrows():
    dist = rr["dist"]
    scope = SEGMENT_ONLY.get(dist, "TOTAL")
    def pct_str(y, dist=dist):
        v = dfm[(dfm['dist']==dist)&(dfm['year']==y)].iloc[0]['gps_pct']
        if v is None or pd.isna(v):
            return "n/a"
        return f"{v*100:.1f}%"
    uio_2024 = dfm[(dfm['dist']==dist)&(dfm['year']==2024)].iloc[0]['uio_total']
    print(f"{dist:<18}{scope:<10}{pct_str(2022):>10}{pct_str(2023):>10}{pct_str(2024):>10}{pct_str(2025):>10}{uio_2024:>10}")
