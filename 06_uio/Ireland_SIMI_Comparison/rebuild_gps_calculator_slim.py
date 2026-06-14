"""
Slim rebuild of ISZE_GPS_Calculator.xlsx.

Five tabs only:
  1. Instructions   — methodology, references v17 externally for UIO
  2. Assumptions    — per-model wallets, GPS targets per DB
  3. GPS_Results    — wide table, DB names, 2022-2025
  4. GPS_Ranking    — sorted by 2025 GPS%
  5. Data_Maturity  — 5-axis data model + axis defs + actions (consolidated)

Dropped: Shipment Data, UIO Calculation, GPS Model, Dashboard
         (UIO redundant with v17; old single-VP methodology superseded)

Mirrors only to Master Dashboard copy (B) and Tools master (C).
File A (Isuzu/Divers) and File D (gps_dashboard test) skipped per instruction.
"""
import openpyxl
import pandas as pd
import shutil
from pathlib import Path
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from collections import Counter

MASTER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Tools\isze-tools-github\isze-tools-github\tools\ISZE_GPS_Calculator.xlsx")
PUBLISHED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Master Dashboard\Divers\ISZE_GPS_Calculator.xlsx")
# SKIPPED (obsolete duplicates):
#   C:\Users\jerom\Desktop\claude\ISZE\Isuzu\Divers\ISZE_GPS_Calculator.xlsx
#   C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\gps_dashboard\ISZE_GPS_Dashboard_2024_test.xlsx

V17_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Data\ISUZU_UIO_Overview_2026_v17.xlsx")
SALES_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\prism\data\sales_detailed_for_claude_full_fixed.tsv")

T_N75 = 1120
T_FMD = 1344
T_LCV = 250
NON_PARTS = {"TRANSPORT", "FREIGHT", "DUTY", "PACKING"}
SALES_YEARS = [2022, 2023, 2024, 2025]
PROXY_YEAR = 2024

# Distributor codes mapped to DB short names + country
DB_INFO = {
    "ITUK":     {"db": "ITUK",                  "country": "United Kingdom",  "scope": "CV"},
    "IUK":      {"db": "IUK",                   "country": "United Kingdom",  "scope": "LCV"},
    "UTI":      {"db": "UTI",                   "country": "Israel",          "scope": "CV"},
    "UMI":      {"db": "UMI",                   "country": "Israel",          "scope": "LCV"},
    "IRELAND":  {"db": "Isuzu Ireland",         "country": "Ireland",         "scope": "CV+LCV"},
    "BELGIUM":  {"db": "IBX",                   "country": "Belgium (Benelux)","scope": "CV+LCV"},
    "GERMANY":  {"db": "ISD-Lang",              "country": "Germany",         "scope": "CV+LCV"},
    "PORTUGAL": {"db": "Imotors",               "country": "Portugal + Azores","scope": "CV+LCV"},
    "SWEDEN":   {"db": "Isuzu Sverige",         "country": "Sweden",          "scope": "CV+LCV"},
    "NORWAY":   {"db": "RSA",                   "country": "Norway",          "scope": "CV+LCV"},
    "DENMARK":  {"db": "Isuzu Denmark",         "country": "Denmark",         "scope": "CV+LCV"},
    "FINLAND":  {"db": "Nordic Auto",           "country": "Finland",         "scope": "CV+LCV"},
    "ICELAND":  {"db": "BL",                    "country": "Iceland",         "scope": "CV+LCV"},
    "GREECE":   {"db": "Petros Petropoulos",    "country": "Greece",          "scope": "CV+LCV"},
    "CYPRUS":   {"db": "Loutsios & Sons",       "country": "Cyprus",          "scope": "CV+LCV"},
    "MALTA":    {"db": "GasanZammit",           "country": "Malta",           "scope": "CV+LCV"},
    "ROMANIA":  {"db": "Isuzu Rom Auto",        "country": "Romania",         "scope": "CV+LCV"},
    "HUNGARY":  {"db": "AutoWallis",            "country": "Hungary",         "scope": "CV+LCV"},
}

V17_DIST_TO_CODE = {
    "UTI":"UTI","UMI":"UMI","BL":"ICELAND","RSA":"NORWAY",
    "Isuzu Sverige":"SWEDEN","Isuzu Denmark":"DENMARK",
    "ITUK":"ITUK","IUK":"IUK","Isuzu Ireland":"IRELAND",
    "IBX":"BELGIUM","ISD-Lang":"GERMANY","Imotors":"PORTUGAL",
    "GasanZammit":"MALTA","Nordic Auto.":"FINLAND","AutoWallis":"HUNGARY",
    "Petros Petropoulos":"GREECE","Isuzu Rom Auto":"ROMANIA","Loutsios & Sons":"CYPRUS",
}
SOLD_TO_TO_CODE = {
    "ISUZU TRUCK (UK) LIMITED":"ITUK","ISUZU TRUCK UK LIMITED":"ITUK",
    "I.M. PARTS & SERVICE Limited":"IUK",
    "UNIVERSAL MOTORS ISRAEL LTD":"UMI","UNIVERSAL TRUCKS ISRAEL LTD":"UTI",
    "ISUZU IRELAND":"IRELAND","ISUZU BENELUX NV":"BELGIUM",
    "ISUZU SALES DEUTSCHLAND GMBH":"GERMANY",
    "XXX ISUZU SALES DEUTSCHLAND GMBH":"GERMANY",
    "Isuzu Motors Germany GmbH":"EXCLUDE",
    "IMOTORS - Importacao e Comercio":"PORTUGAL",
    "ISUZU SVERIGE AB":"SWEDEN","ISUZU MOTORS SWEDEN AB":"SWEDEN",
    "ISUZU DANMARK A/S":"DENMARK","ISUZU ROM AUTO SRL":"ROMANIA",
    "RUTEBILEIERNES STANDARDISERING AS":"NORWAY",
    "PETROS PETROPOULOS S.A. (VEHICLE)":"GREECE",
    "PETROS PETROPOULOS S.A.":"GREECE",
    "LOUTSIOS A & SONS LTD":"CYPRUS",
    "Nordic Automotive trading oy.":"FINLAND",
    "GASANZAMMIT MOTORS LTD":"MALTA",
    "AW Distribution Kft.":"HUNGARY","BL. EHF.":"ICELAND",
}
SEGMENT_ONLY = {"ITUK":"CV","IUK":"LCV","UTI":"CV","UMI":"LCV"}

# ---------- Load v17 UIO ----------
wb17 = openpyxl.load_workbook(V17_PATH, read_only=True, data_only=True)
ws17 = wb17["1.UIO Overview"]
hdr17 = list(ws17.iter_rows(min_row=6, max_row=6, values_only=True))[0]
y2c = {}
for i, h in enumerate(hdr17):
    try:
        y = int(str(h).replace("E","").replace("F","").strip())
        y2c[y] = i
    except: pass

uio = {}
for row in ws17.iter_rows(min_row=7, max_row=500, values_only=True):
    if not row[5]: continue
    v17_dist = str(row[5]).strip()
    if "MIDI" in v17_dist.upper(): continue
    code = V17_DIST_TO_CODE.get(v17_dist)
    if not code: continue
    cv = (str(row[2]) if row[2] else "").strip()
    mdl = (str(row[3]) if row[3] else "").strip()
    if cv == "CV" and mdl == "LD": seg = "LD"
    elif mdl == "F-Series": seg = "F"
    elif cv == "CV" and mdl == "MD": seg = "MD"
    elif cv == "LCV": seg = "LCV"
    else: continue
    for y in SALES_YEARS:
        if y not in y2c: continue
        v = row[y2c[y]] or 0
        if v: uio[(code,y,seg)] = uio.get((code,y,seg),0) + v

def _raw(d,y,s):
    v = uio.get((d,y,s),0)
    if v == 0: v = uio.get((d,PROXY_YEAR,s),0)
    return v

def get_uio(d,y,s):
    if d in SEGMENT_ONLY:
        if SEGMENT_ONLY[d]=="CV" and s in ("LD","F","MD"): return _raw(d,y,s)
        if SEGMENT_ONLY[d]=="LCV" and s=="LCV": return _raw(d,y,s)
        return 0
    return _raw(d,y,s)

def wallet(d,y):
    return (get_uio(d,y,"LD")*T_N75 + get_uio(d,y,"F")*T_FMD
          + get_uio(d,y,"MD")*T_FMD + get_uio(d,y,"LCV")*T_LCV)

# ---------- Sales (parts only) ----------
sales = pd.read_csv(SALES_PATH, sep="\t", low_memory=False)
sales["net_sales_value"] = pd.to_numeric(sales["net_sales_value"], errors="coerce")
sales["year"] = pd.to_numeric(sales["year"], errors="coerce")
sales["part_upper"] = sales["part_number"].astype(str).str.upper().str.strip()
sales_parts = sales[~sales["part_upper"].isin(NON_PARTS)].copy()
sales_parts["dist_code"] = sales_parts["sold_to"].map(SOLD_TO_TO_CODE)
sales_by_dy = (sales_parts.dropna(subset=["dist_code"])
               .groupby(["dist_code","year"])["net_sales_value"].sum().to_dict())

all_dists = sorted(set(d for (d,_,_) in uio.keys()) - {"EXCLUDE"})

rows = []
for d in all_dists:
    for y in SALES_YEARS:
        ld = get_uio(d,y,"LD"); f = get_uio(d,y,"F")
        md = get_uio(d,y,"MD"); lcv = get_uio(d,y,"LCV")
        total = ld+f+md+lcv
        wal = wallet(d,y)
        sv = sales_by_dy.get((d,y),0.0)
        eu = sv/total if total else None
        gps = sv/wal if wal else None
        rows.append((d, DB_INFO[d]["db"], DB_INFO[d]["country"], y, ld,f,md,lcv,total,wal,sv,eu,gps))
dfm = pd.DataFrame(rows, columns=["code","db","country","year","ld","f","md","lcv","total","wallet","sales","eu","gps"])

# ---------- Maturity matrix ----------
MATURITY = [
    ("ITUK",2,"CONFIRMED",1,"CONFIRMED",1,"CONFIRMED",2,"CONFIRMED",1,"DEFAULT", 2,2,2,3,2),
    ("IUK", 1,"CONFIRMED",0,"DEFAULT",  0,"DEFAULT",  1,"GUESS",    1,"DEFAULT", 2,1,1,2,2),
    ("UTI", 1,"CONFIRMED",0,"DEFAULT",  0,"DEFAULT",  0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("UMI", 1,"CONFIRMED",0,"DEFAULT",  0,"DEFAULT",  0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("IRELAND",2,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("BELGIUM",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("GERMANY",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("PORTUGAL",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT",0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("SWEDEN",1,"CONFIRMED",0,"DEFAULT", 0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("NORWAY",1,"CONFIRMED",0,"DEFAULT", 0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("DENMARK",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("FINLAND",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("ICELAND",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("GREECE",1,"CONFIRMED",0,"DEFAULT", 0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("CYPRUS",1,"CONFIRMED",0,"DEFAULT", 0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("MALTA", 1,"CONFIRMED",0,"DEFAULT", 0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("ROMANIA",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
    ("HUNGARY",1,"CONFIRMED",0,"DEFAULT",0,"DEFAULT", 0,"DEFAULT",  1,"DEFAULT", 2,1,1,2,2),
]

# ============================================================
# Build slim workbook from scratch (drop obsolete tabs)
# ============================================================
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
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
LEVEL_FILL = {0:RED0, 1:AMBER, 2:GREEN, 3:GREEN3}
CONF_FONT = {"CONFIRMED":Font(bold=True, color="2E7D32"),
             "GUESS":Font(italic=True, color="E65100"),
             "DEFAULT":Font(italic=True, color="595959")}

def style_header(ws,row,n):
    for c in range(1,n+1):
        cell = ws.cell(row=row, column=c)
        cell.fill = BLUE; cell.font = WHITE_BOLD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER

def autosize(ws,widths):
    for i,w in enumerate(widths,1):
        ws.column_dimensions[get_column_letter(i)].width = w

def gps_fill(p):
    if p is None: return None
    if p >= 1.0: return GREEN3
    if p >= 0.33: return AMBER
    return RED0

# ----------- 1. Instructions -----------
ws = wb.create_sheet("Instructions")
ws["A1"] = "ISZE GENUINE PARTS SHARE (GPS) CALCULATOR"
ws["A1"].font = Font(bold=True, size=18, color="1F4E78")
ws.merge_cells("A1:F1")
ws["A2"] = "Estimates genuine parts share per DB. Per-model wallet methodology. UIO sourced externally from current ISZE methodology (v17)."
ws["A2"].font = Font(size=12, italic=True, color="595959")
ws.merge_cells("A2:F2")

lines = [
    ("",""),
    ("Date prepared","2026-05-28"),
    ("",""),
    ("HOW THE CALCULATION WORKS",""),
    ("","GPS % = Actual parts net sales ÷ Theoretical maximum parts wallet"),
    ("","Maximum wallet = Σ (UIO segment × per-model EUR target)"),
    ("","Sales numerator: parts-only (TRANSPORT / FREIGHT / DUTY / PACKING line items excluded)"),
    ("","UIO denominator: current ISZE methodology (ISUZU_UIO_Overview_2026_v17.xlsx, sheet '1.UIO Overview')"),
    ("",""),
    ("PER-MODEL MAXIMUM WALLET",""),
    ("  N 7.5T (N75 / N50 / N62)","EUR 1,120 / vehicle / year"),
    ("  F-Series / CV MD","EUR 1,344 / vehicle / year"),
    ("  LCV / D-Max","EUR 250 / vehicle / year"),
    ("  N 3.5T (NLR / N35 family)","EUR 250 / vehicle / year  (mapped to LCV wallet)"),
    ("",""),
    ("GPS TRAFFIC-LIGHT THRESHOLDS",""),
    ("  Healthy (green)","≥ 100% GPS"),
    ("  At risk (amber)","33 - 100% GPS"),
    ("  Critical (red)","< 33% GPS"),
    ("",""),
    ("UIO REFERENCE",""),
    ("","UIO is NOT recalculated inside this workbook. It is taken directly from the current ISZE methodology in ISUZU_UIO_Overview_2026_v17.xlsx (sheet '1.UIO Overview'). When v18 or later is published, this file is refreshed."),
    ("","Survival curves applied in v17: scrap-adjusted (CV — 8 markets including BE, CY, DE, DK, GR, IE, MT, PT), IML CV-developed (other markets), IMIT 12-yr (all LCV)."),
    ("",""),
    ("WORKBOOK CONTENTS",""),
    ("  1. Instructions","this sheet"),
    ("  2. Assumptions","per-model wallets, GPS targets per DB, methodology parameters"),
    ("  3. GPS_Results","wide table: each DB × year, UIO segments / wallet / sales / €/unit / GPS%"),
    ("  4. GPS_Ranking","DBs sorted by 2025 GPS%, with 4-year trend"),
    ("  5. Data_Maturity","5-axis data model per DB: where we are, where we could go, what to refine"),
]
for i,(k,v) in enumerate(lines,4):
    ws.cell(row=i, column=1, value=k).font = BOLD
    ws.cell(row=i, column=2, value=v).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=6)
autosize(ws, [30,60,18,18,18,18])

# ----------- 2. Assumptions -----------
ws = wb.create_sheet("Assumptions")
ws["A1"] = "ASSUMPTIONS"
ws["A1"].font = Font(bold=True, size=16, color="1F4E78")
ws.merge_cells("A1:F1")
ws["A2"] = "Per-model maximum wallet (= 100% GPS) and GPS targets per DB."
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:F2")

# Per-model wallet block
r = 4
ws.cell(row=r, column=1, value="A. PER-MODEL MAXIMUM WALLET").font = Font(bold=True, color="1F4E78", size=12)
r += 2
hdr = ["Model group","Models included","Max wallet (€/veh/yr)","Source"]
for c,h in enumerate(hdr,1): ws.cell(row=r, column=c, value=h)
style_header(ws, r, len(hdr))
r += 1
wallet_data = [
    ("N 7.5T", "N75 / N50 / N62 / N65 / NPR7x / NPR8x / NQR", 1120, "ISZE GPS workbook"),
    ("F-Series / CV MD", "F110/120 / F135 / F150/180 / FRR / FSR", 1344, "ISZE GPS workbook"),
    ("LCV / D-Max", "D-Max pickup, all LCV variants", 250, "ISZE GPS workbook"),
    ("N 3.5T", "NLR / NMR / NNR / NPR (3.5T) / N35", 250, "ISZE GPS workbook (mapped to LCV wallet)"),
]
for label, models, eur, src in wallet_data:
    ws.cell(row=r, column=1, value=label).font = BOLD
    ws.cell(row=r, column=2, value=models)
    c = ws.cell(row=r, column=3, value=eur); c.number_format = "€#,##0"
    c.alignment = Alignment(horizontal="right"); c.font = BOLD
    ws.cell(row=r, column=4, value=src).font = ITALIC_GREY
    for cc in range(1,5): ws.cell(row=r, column=cc).border = BORDER
    r += 1
r += 2

# GPS targets per DB
ws.cell(row=r, column=1, value="B. GPS TARGETS PER DB").font = Font(bold=True, color="1F4E78", size=12)
r += 2
hdr = ["DB","Country","Scope","FY2026 target","FY2028 stretch","Notes"]
for c,h in enumerate(hdr,1): ws.cell(row=r, column=c, value=h)
style_header(ws, r, len(hdr))
r += 1
ws.cell(row=r-1, column=1, value="(Targets to be provided by GPS owner — table left blank.)").font = ITALIC_GREY
ws.merge_cells(start_row=r-1, start_column=1, end_row=r-1, end_column=6)
for code in [d[0] for d in MATURITY]:
    info = DB_INFO[code]
    ws.cell(row=r, column=1, value=info["db"]).font = BOLD
    ws.cell(row=r, column=2, value=info["country"])
    ws.cell(row=r, column=3, value=info["scope"]).alignment = Alignment(horizontal="center")
    # FY2026 target — blank, owner to fill
    cell = ws.cell(row=r, column=4); cell.fill = YELLOW
    cell.alignment = Alignment(horizontal="right")
    # FY2028 stretch — blank, owner to fill
    cell = ws.cell(row=r, column=5); cell.fill = YELLOW
    cell.alignment = Alignment(horizontal="right")
    # Notes — blank, owner to fill
    cell = ws.cell(row=r, column=6); cell.fill = YELLOW
    for cc in range(1,7): ws.cell(row=r, column=cc).border = BORDER
    r += 1
r += 2

# Sales scope rule
ws.cell(row=r, column=1, value="C. SALES NUMERATOR SCOPE").font = Font(bold=True, color="1F4E78", size=12)
r += 2
notes = [
    "Source: ISZE ERP net-sales export (parts billed to sold_to = each DB's legal entity).",
    "Parts-only: TRANSPORT / FREIGHT / DUTY / PACKING line items excluded (~1-2% of total).",
    "Segment-only scope: ITUK and UTI = CV only; IUK and UMI = LCV only. All other DBs = total CV + LCV.",
    "UIO proxy: when year-specific UIO is missing (e.g. ITUK 2025), the 2024 UIO is used as proxy.",
]
for n in notes:
    ws.cell(row=r, column=1, value="• " + n).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 22
    r += 1

autosize(ws, [20,28,12,15,15,42])

# ----------- 3. GPS_Results -----------
ws = wb.create_sheet("GPS_Results")
ws["A1"] = "Full GPS results — all DBs × 2022-2025"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:K1")

hdr = ["Distributor","Year","CV LD","F","MD","LCV","Total UIO","Wallet (€)","Sales (€)","€/unit","GPS%"]
for c,h in enumerate(hdr,1): ws.cell(row=3, column=c, value=h)
style_header(ws, 3, len(hdr))

r = 4
dbs_in_order = [d[0] for d in MATURITY]
for code in dbs_in_order:
    db_name = DB_INFO[code]["db"]
    db_rows = dfm[dfm["code"]==code].sort_values("year")
    first = True
    for _, dr in db_rows.iterrows():
        if first:
            cell = ws.cell(row=r, column=1, value=db_name); cell.font = BOLD
            first = False
        ws.cell(row=r, column=2, value=int(dr["year"])).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=3, value=int(dr["ld"]))
        ws.cell(row=r, column=4, value=int(dr["f"]))
        ws.cell(row=r, column=5, value=int(dr["md"]))
        ws.cell(row=r, column=6, value=int(dr["lcv"]))
        c = ws.cell(row=r, column=7, value=int(dr["total"])); c.font = BOLD
        ws.cell(row=r, column=8, value=dr["wallet"]).number_format = "#,##0"
        ws.cell(row=r, column=9, value=dr["sales"]).number_format = "#,##0"
        if dr["eu"] is not None:
            c = ws.cell(row=r, column=10, value=dr["eu"]); c.number_format = "€#,##0"
        if dr["gps"] is not None:
            c = ws.cell(row=r, column=11, value=dr["gps"])
            c.number_format = "0.0%"; c.fill = gps_fill(dr["gps"]); c.font = BOLD
        for cc in range(3,12): ws.cell(row=r, column=cc).alignment = Alignment(horizontal="right")
        for cc in range(1,12): ws.cell(row=r, column=cc).border = BORDER
        r += 1
autosize(ws, [22,8,9,7,7,9,11,14,14,10,10])

# ----------- 4. GPS_Ranking -----------
ws = wb.create_sheet("GPS_Ranking")
ws["A1"] = "GPS Ranking — sorted by 2025 GPS%"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:L1")

hdr = ["DB","Country","Scope","2022 €/unit","2022 GPS%","2023 €/unit","2023 GPS%","2024 €/unit","2024 GPS%","2025 €/unit","2025 GPS%","UIO 2024"]
for c,h in enumerate(hdr,1): ws.cell(row=3, column=c, value=h)
style_header(ws, 3, len(hdr))

rank = (dfm[dfm["year"]==2025].sort_values("gps", ascending=False, na_position="last").reset_index(drop=True))
r = 4
for _, rr in rank.iterrows():
    code = rr["code"]
    info = DB_INFO[code]
    ws.cell(row=r, column=1, value=info["db"]).font = BOLD
    ws.cell(row=r, column=2, value=info["country"])
    ws.cell(row=r, column=3, value=info["scope"]).alignment = Alignment(horizontal="center")
    col = 4
    for y in SALES_YEARS:
        rec = dfm[(dfm["code"]==code) & (dfm["year"]==y)].iloc[0]
        if rec["eu"] is not None:
            c1 = ws.cell(row=r, column=col, value=rec["eu"]); c1.number_format = "€#,##0"
            c1.alignment = Alignment(horizontal="right")
        col += 1
        if rec["gps"] is not None:
            c2 = ws.cell(row=r, column=col, value=rec["gps"])
            c2.number_format = "0.0%"; c2.fill = gps_fill(rec["gps"]); c2.font = BOLD
            c2.alignment = Alignment(horizontal="right")
        col += 1
    d24 = dfm[(dfm["code"]==code) & (dfm["year"]==2024)].iloc[0]
    ws.cell(row=r, column=col, value=int(d24["total"])).alignment = Alignment(horizontal="right")
    for cc in range(1, 13): ws.cell(row=r, column=cc).border = BORDER
    r += 1
autosize(ws, [20,22,10,11,10,11,10,11,10,11,10,11])

# ----------- 5. Data_Maturity -----------
ws = wb.create_sheet("Data_Maturity")
ws["A1"] = "Data Maturity Model — Per DB"
ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
ws.merge_cells("A1:T1")
ws["A2"] = "Five axes 0-3 (B & E max 2). CONFIRMED (green) | GUESS (orange) | DEFAULT (grey). Cells with DEFAULT or GUESS need owner confirmation."
ws["A2"].font = ITALIC_GREY
ws.merge_cells("A2:T2")

# Axis legend at top
r = 4
ws.cell(row=r, column=1, value="AXIS DEFINITIONS").font = Font(bold=True, color="1F4E78", size=11)
r += 1
axes_def = [
    ("A", "UIO denominator", "0=IML lumped | 1=IML per-model | 2=National reg authority (SMMT/SIMI/KBA) | 3=Per-VIN cohort"),
    ("B", "Sales numerator",  "0=ISZE → DB only | 1=+ DB → dealer sell-out | 2=+ per-VIN parts attribution"),
    ("C", "PMS / maintenance","0=none | 1=one-off PMS exchange | 2=recurring feed | 3=workshop integration"),
    ("D", "Pricing / competitive","0=none | 1=anecdotal | 2=TecDoc/Eucon | 3=full PR00 mapping"),
    ("E", "Warranty / goodwill","0=blended | 1=flagged in SAP | 2=excluded with audit trail"),
]
for ax, name, scale in axes_def:
    ws.cell(row=r, column=1, value=ax).font = BOLD
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=2, value=name).font = BOLD
    ws.cell(row=r, column=3, value=scale).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=20)
    ws.row_dimensions[r].height = 24
    r += 1
r += 1

# Matrix grid
ws.cell(row=r, column=1, value="MATURITY GRID").font = Font(bold=True, color="1F4E78", size=11)
r += 1
hdr = ["DB","Country","Scope",
       "A cur","A cf","A tgt", "B cur","B cf","B tgt",
       "C cur","C cf","C tgt", "D cur","D cf","D tgt",
       "E cur","E cf","E tgt", "Cur tot","Tgt tot"]
for c,h in enumerate(hdr,1): ws.cell(row=r, column=c, value=h)
style_header(ws, r, len(hdr))
ws.row_dimensions[r].height = 30
matrix_header_row = r
r += 1

def pl(r,c,lvl):
    cell = ws.cell(row=r, column=c, value=lvl)
    cell.fill = LEVEL_FILL[lvl]; cell.font = BOLD
    cell.alignment = Alignment(horizontal="center"); cell.border = BORDER

def pc(r,c,cf):
    cell = ws.cell(row=r, column=c, value=cf)
    cell.font = CONF_FONT[cf]; cell.alignment = Alignment(horizontal="center"); cell.border = BORDER

for row in MATURITY:
    code = row[0]
    info = DB_INFO[code]
    (a_c,a_cf,b_c,b_cf,c_c,c_cf,d_c,d_cf,e_c,e_cf,a_t,b_t,c_t,d_t,e_t) = row[1:]
    ws.cell(row=r, column=1, value=info["db"]).font = BOLD
    ws.cell(row=r, column=2, value=info["country"])
    ws.cell(row=r, column=3, value=info["scope"])
    for cc in range(1,4): ws.cell(row=r, column=cc).border = BORDER
    pl(r,4,a_c); pc(r,5,a_cf); pl(r,6,a_t)
    pl(r,7,b_c); pc(r,8,b_cf); pl(r,9,b_t)
    pl(r,10,c_c); pc(r,11,c_cf); pl(r,12,c_t)
    pl(r,13,d_c); pc(r,14,d_cf); pl(r,15,d_t)
    pl(r,16,e_c); pc(r,17,e_cf); pl(r,18,e_t)
    cv = a_c+b_c+c_c+d_c+e_c
    tv = a_t+b_t+c_t+d_t+e_t
    c1 = ws.cell(row=r, column=19, value=cv); c1.fill = NAVY; c1.font = WHITE_BOLD
    c1.alignment = Alignment(horizontal="center"); c1.border = BORDER
    c2 = ws.cell(row=r, column=20, value=tv); c2.fill = NAVY; c2.font = WHITE_BOLD
    c2.alignment = Alignment(horizontal="center"); c2.border = BORDER
    r += 1
r += 2

# Scoreboard summary
ws.cell(row=r, column=1, value="SCOREBOARD").font = Font(bold=True, color="1F4E78", size=11)
r += 1
hdr = ["Axis","Max","L0","L1","L2","L3","Cur","Tgt"]
for c,h in enumerate(hdr,1): ws.cell(row=r, column=c, value=h)
style_header(ws, r, len(hdr))
r += 1

axis_summary = [("A — UIO",1,3),("B — Sales",2,2),("C — PMS",3,3),("D — Pricing",4,3),("E — Warranty",5,2)]
total_cur = 0; total_tgt = 0
for name, idx, mx in axis_summary:
    # idx: 1=a, 2=b, 3=c, 4=d, 5=e
    cur_col = {1:1, 2:3, 3:5, 4:7, 5:9}[idx]   # index into row[1:] (1-based after code)
    tgt_col = {1:11, 2:12, 3:13, 4:14, 5:15}[idx]
    cur_vals = [m[cur_col] for m in MATURITY]
    tgt_vals = [m[tgt_col] for m in MATURITY]
    cnt = Counter(cur_vals)
    ws.cell(row=r, column=1, value=name).font = BOLD
    ws.cell(row=r, column=2, value=mx).alignment = Alignment(horizontal="center")
    for lvl in range(4):
        cell = ws.cell(row=r, column=3+lvl, value=cnt.get(lvl,0) if lvl <= mx else "—")
        cell.alignment = Alignment(horizontal="center")
        cell.fill = LEVEL_FILL[lvl] if lvl <= mx else GREY
    cv = sum(cur_vals); tv = sum(tgt_vals)
    total_cur += cv; total_tgt += tv
    c1 = ws.cell(row=r, column=7, value=cv); c1.font = BOLD; c1.alignment = Alignment(horizontal="center")
    c2 = ws.cell(row=r, column=8, value=tv); c2.font = BOLD; c2.fill = GREEN; c2.alignment = Alignment(horizontal="center")
    r += 1
ws.cell(row=r, column=1, value="TOTAL").font = BOLD
ws.cell(row=r, column=2, value=13).alignment = Alignment(horizontal="center")
for cc in range(3,7): ws.cell(row=r, column=cc, value="").fill = GREY
c1 = ws.cell(row=r, column=7, value=total_cur); c1.font = WHITE_BOLD; c1.fill = NAVY
c1.alignment = Alignment(horizontal="center")
c2 = ws.cell(row=r, column=8, value=total_tgt); c2.font = WHITE_BOLD; c2.fill = NAVY
c2.alignment = Alignment(horizontal="center")
r += 2

# Refinement actions
ws.cell(row=r, column=1, value="REFINEMENT ACTIONS").font = Font(bold=True, color="1F4E78", size=11)
r += 1
hdr = ["DB","Axis","Cur → Tgt","Action","Owner"]
for c,h in enumerate(hdr,1): ws.cell(row=r, column=c, value=h)
style_header(ws, r, len(hdr))
r += 1

axis_owners = {"A":"ISZE Data / reg authority","B":"DB","C":"DB (workshop/DMS)","D":"ISZE Pricing / TecDoc","E":"ISZE Finance / SAP"}
def action_for(code, axis, cur, tgt):
    if cur == tgt: return "Already at target."
    if axis == "A":
        if cur == 1 and tgt == 2: return f"Ingest national reg authority data for {code}'s market."
        if cur == 2 and tgt == 3: return "Move to per-VIN fleet register."
    if axis == "B":
        if cur == 0 and tgt == 1: return f"Request distributor sell-out from {code}."
        if cur == 1 and tgt == 2: return "Per-VIN parts attribution from workshop."
    if axis == "C":
        if cur == 0 and tgt == 1: return f"Request one-off PMS study from {code}."
        if cur == 1 and tgt == 2: return f"Convert one-off to recurring PMS feed for {code}."
    if axis == "D":
        if cur == 0 and tgt == 2: return f"Procure TecDoc/Eucon coverage for {code}'s market."
        if cur == 1 and tgt == 2: return f"Procure TecDoc/Eucon coverage for {code}'s market."
        if cur == 2 and tgt == 3: return "Build competitive PR00 mapping."
    if axis == "E":
        if cur == 1 and tgt == 2: return f"Exclude warranty consistently from {code} GPS; document audit trail."
    return "—"

for row in MATURITY:
    code = row[0]
    db = DB_INFO[code]["db"]
    actions_per_db = [
        ("A", row[1], row[11]),
        ("B", row[3], row[12]),
        ("C", row[5], row[13]),
        ("D", row[7], row[14]),
        ("E", row[9], row[15]),
    ]
    actions_with_gap = [(ax,c,t) for ax,c,t in actions_per_db if c != t]
    if not actions_with_gap:
        continue
    first = True
    for ax, cur, tgt in actions_with_gap:
        ws.cell(row=r, column=1, value=db if first else "").font = BOLD
        first = False
        ws.cell(row=r, column=2, value=ax).alignment = Alignment(horizontal="center")
        c3 = ws.cell(row=r, column=3, value=f"{cur} → {tgt}")
        c3.alignment = Alignment(horizontal="center"); c3.font = BOLD; c3.fill = AMBER
        ws.cell(row=r, column=4, value=action_for(code, ax, cur, tgt)).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row=r, column=5, value=axis_owners[ax])
        for cc in range(1,6): ws.cell(row=r, column=cc).border = BORDER
        ws.row_dimensions[r].height = 22
        r += 1

autosize(ws, [18,18,12,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,10,10])

# Save master + published mirror
wb.save(MASTER)
print(f"Saved master: {MASTER}")
shutil.copy(MASTER, PUBLISHED)
print(f"Mirrored to published: {PUBLISHED}")

# Confirm
wb2 = openpyxl.load_workbook(MASTER)
print(f"\nFinal sheets ({len(wb2.sheetnames)}): {wb2.sheetnames}")
print(f"\nSkipped (not updated):")
print(f"  - Isuzu/Divers/ISZE_GPS_Calculator.xlsx (obsolete duplicate)")
print(f"  - gps_dashboard/ISZE_GPS_Dashboard_2024_test.xlsx (different file, obsolete test export)")
