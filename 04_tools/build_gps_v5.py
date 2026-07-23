#!/usr/bin/env python3
"""
build_gps_v5.py — ISZE GPS v5 unified workbook
v2: class-weighted max spend from UIO v19; Option A re-solved
"""
import sys, shutil, csv
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from collections import defaultdict
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as gcl
from openpyxl.workbook.defined_name import DefinedName

BASE      = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
KOSHA_DIR = BASE / "14_dashboards" / "kosha"
SRC_V4A   = KOSHA_DIR / "ISZE_GPS_Kosha_v4a.xlsx"
SRC_V4B   = KOSHA_DIR / "ISZE_GPS_Kosha_v4b.xlsx"
SRC_TMPL  = BASE / "ISZE_GPS_Kosha_v4_merged_template (1).xlsx"
UIO_FILE  = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx")
WARR_CSV  = BASE / "00_derived" / "distributor_warranty_expense_fiscal.csv"
OUT       = BASE / "ISZE_GPS_v5.xlsx"
ARCHIVE   = KOSHA_DIR / "_archive"

DARK="1A2B4A"; MID="2C4A7C"; LIGHT="4A7AB5"; ACCENT="E87920"
GBG="C6EFCE"; GFG="276221"; ABG="FFEB9C"; AFG="9C6500"; RBG="FFC7CE"; RFG="9C0006"
WHITE="FFFFFF"; LGR="F5F5F5"; MGR="D9D9D9"; DGR="808080"
TOGGLE = "Dashboard!$C$2"

# UIO v19 → GPS DB name map
UIO_NAME = {
    "UTI":"UTI","UMI":"UMI","BL":"BL Iceland","RSA":"RSA",
    "Isuzu Sverige":"Sverige","Isuzu Denmark":"Danmark",
    "ITUK":"ITUK","IUK":"IUK","Isuzu Ireland":"Ireland","IBX":"IBX",
    "ISD-Lang":"ISD","Imotors":"Imotors","GasanZammit":"GasanZammit",
    "Nordic Auto.":"Nordic FI","AutoWallis":"AutoWallis",
    "Petros Petropoulos":"Greece","Isuzu Rom Auto":"ROM Auto",
    "Loutsios & Sons":"Loutsios","MIDI Europe":"MIDI",
}
BUILD_DIR = BASE / "91_build"
sys.path.insert(0, str(BUILD_DIR))
from gps_v9_loaders import build_gps_uio_package, max_spend_from_buckets, RATE_N35, RATE_N75, RATE_FMD
# Class rates (€/UIO/yr) — network DBs (ex-ITUK)
CLASS_RATE = {"LD":739, "F-Series":887, "MD":887, "LCV":250}
ITUK_CLASS_RATE = {"N35": int(RATE_N35), "N75_LD": int(RATE_N75), "F_MD": int(RATE_FMD)}
# Keep max spend from v4a source for bespoke wallets only
KEEP_MAX = {"Ireland", "MIDI"}
# Projected market caps for KEEP_MAX DBs (from v4a observation text)
PROJ_CAP = {
    "Ireland": {2027: 2102000, 2028: 2308000, 2029: 2519000, 2030: 2735000},
    "MIDI":    {2027: 1296000, 2028: 1296000, 2029: 1296000, 2030: 1296000},
}
# BP network totals read LIVE from PL Plan row 186 (VP parts / vehicle parts), cols G-J = FY2027-2030.
# Was hardcoded 2029:42_560_000 / 2030:48_270_000 (pre-revision); IML row 186 withdrew that to
# 41_530_410 / 46_385_705 -- the EUR 2.91M phantom uplift. Read live so it cannot drift again.
_PLAN_186 = BASE / "11_planning" / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"
def _load_bp_row186(plan=_PLAN_186):
    _wb = openpyxl.load_workbook(plan, data_only=True)
    _ws = _wb["IX study"]
    return {yr: float(_ws.cell(186, c).value) for yr, c in {2027: 7, 2028: 8, 2029: 9, 2030: 10}.items()}
BP   = _load_bp_row186()
CIS_P= {2027: 1700000, 2028: 1800000, 2029: 1900000, 2030: 2000000}

# v5 workbook DB name → GPS v9 / reviewed BP code (load_bp_fy27.py)
V5_TO_GPS = {
    "ITUK": "ITUK", "IUK": "IUK", "UTI": "UTI", "UMI": "UMI",
    "ISD": "GERMANY", "RSA": "NORWAY", "Sverige": "SWEDEN", "IBX": "BELGIUM",
    "Imotors": "PORTUGAL", "Ireland": "IRELAND", "Greece": "GREECE",
    "AutoWallis": "HUNGARY", "ROM Auto": "ROMANIA", "Loutsios": "CYPRUS",
    "GasanZammit": "MALTA", "Nordic FI": "FINLAND", "Danmark": "DENMARK",
    "BL Iceland": "ICELAND",
}

def F(h): return PatternFill("solid", fgColor=h)
def Fn(bold=False, color="000000", size=9, italic=False):
    return Font(bold=bold, color=color, size=size, italic=italic, name="Calibri")
def Al(h="left", v="center", wrap=False): return Alignment(horizontal=h, vertical=v, wrap_text=wrap)
def Br(c=MGR):
    s = Side(style="thin", color=c)
    return Border(left=s, right=s, top=s, bottom=s)

def hdr(ws, r, c, txt, bg=MID, span=1):
    if span > 1:
        ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c+span-1)
    cell = ws.cell(r, c, txt)
    cell.font = Fn(bold=True, color=WHITE, size=9)
    cell.fill = F(bg); cell.alignment = Al("center", wrap=True); cell.border = Br(WHITE)
    ws.row_dimensions[r].height = max(ws.row_dimensions[r].height or 0, 28)

def title_row(ws, r, txt, cols=12, bg=DARK):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
    c = ws.cell(r, 1, txt)
    c.font = Fn(bold=True, color=WHITE, size=12); c.fill = F(bg); c.alignment = Al("left")
    ws.row_dimensions[r].height = 30

def note_row(ws, r, txt, cols=12):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
    c = ws.cell(r, 1, txt)
    c.font = Fn(italic=True, color=DGR, size=8); ws.row_dimensions[r].height = 13

def dc(ws, r, c, val, fmt=None, bold=False, bg=None, align="right", italic=False):
    cell = ws.cell(r, c, val); cell.font = Fn(bold=bold, size=9, italic=italic)
    cell.alignment = Al(align); cell.border = Br()
    if bg: cell.fill = F(bg)
    if fmt: cell.number_format = fmt
    return cell

def lc(ws, r, c, txt, bold=False, bg=None, italic=False):
    cell = ws.cell(r, c, txt); cell.font = Fn(bold=bold, size=9, italic=italic)
    cell.alignment = Al("left"); cell.border = Br()
    if bg: cell.fill = F(bg)
    return cell

def traffic(ws, col, r1, r2):
    rng = f"{col}{r1}:{col}{r2}"
    ws.conditional_formatting.add(rng, CellIsRule("lessThan",["0.85"],fill=F(GBG),font=Fn(color=GFG)))
    ws.conditional_formatting.add(rng, CellIsRule("between",["0.85","1.0"],fill=F(ABG),font=Fn(color=AFG)))
    ws.conditional_formatting.add(rng, CellIsRule("greaterThanOrEqual",["1.0"],fill=F(RBG),font=Fn(color=RFG,bold=True)))

def safe_float(v, d=0.0):
    if v is None: return d
    if isinstance(v,(int,float)): return float(v)
    s=str(v).replace("%","").replace(",",".").strip()
    try: return float(s)/100 if "%" in str(v) else float(s)
    except: return d

def safe_int(v, d=0):
    if v is None: return d
    if isinstance(v, (int, float)): return int(round(v))
    try: return int(float(str(v).replace(",", "").strip()))
    except: return d

def ituk_bucket_total(buckets: dict) -> float:
    return buckets.get("N35", 0) + buckets.get("N75_LD", 0) + buckets.get("F_MD", 0)

# ── UIO & WARRANTY READERS ────────────────────────────────────────────────────
def read_uio_classes():
    """Return {gps_db: {year: {class_type: uio_count}}} from UIO v19."""
    wb = openpyxl.load_workbook(UIO_FILE, data_only=True)
    ws = wb["1.UIO Overview"]

    # Find year columns (row 6): 2024, 2025E, 2026F, 2027F, 2028F, 2029F, 2030F
    year_col = {}
    for c in range(1, 60):
        v = str(ws.cell(6,c).value or "").strip()
        if v == "2024":     year_col[2024] = c
        elif "2025" in v:   year_col[2025] = c
        elif v == "2026F":  year_col[2026] = c
        elif v == "2027F":  year_col[2027] = c
        elif v == "2028F":  year_col[2028] = c
        elif v == "2029F":  year_col[2029] = c
        elif v == "2030F":  year_col[2030] = c

    # Aggregate: {gps_db: {year: {type: count}}}
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for r in range(7, 200):
        uio_name = str(ws.cell(r,6).value or "").strip()
        if not uio_name: continue
        gps_db = UIO_NAME.get(uio_name)
        if not gps_db: continue
        cls_type = str(ws.cell(r,4).value or "").strip()
        if cls_type not in CLASS_RATE: continue
        for yr, col in year_col.items():
            v = ws.cell(r, col).value
            n = safe_int(v, 0)
            data[gps_db][yr][cls_type] += n

    wb.close()
    return data

def read_warranty():
    """Return {db: {fy24: €, fy25: €, fy26: €}} from warranty CSV."""
    warr = {}
    with open(WARR_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            warr[row["db"]] = {
                2024: float(row.get("warr_FY2024",0) or 0),
                2025: float(row.get("warr_FY2025",0) or 0),
                2026: float(row.get("warr_FY2026",0) or 0),
            }
    return warr

def compute_max_spend(uio_data, src_max, keep_max):
    """
    Returns {db: {year: max_spend}} using class-weighted rates.
    DBs in keep_max use src_max values unchanged.
    uio_data: from read_uio_classes()
    src_max:  {db: {year: max_spend}} from v4a source
    """
    result = {}
    for db in src_max:
        result[db] = {}
        for yr, ms_src in src_max[db].items():
            if db in keep_max:
                result[db][yr] = ms_src
            else:
                classes = uio_data.get(db, {}).get(yr, {})
                total_uio = sum(classes.values())
                if total_uio == 0:
                    # no v19 data → fall back to source
                    result[db][yr] = ms_src
                else:
                    ms_new = sum(n * CLASS_RATE[t] for t, n in classes.items())
                    result[db][yr] = ms_new
    return result

# ── SOURCE READERS ────────────────────────────────────────────────────────────
def read_actuals(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["GPS Actuals FY2024-26"]
    rows = []
    for r in range(4, 100):
        db = ws.cell(r,1).value
        if db is None: break
        if str(db).startswith("TOTAL"): continue
        rows.append({
            "db":       str(db).strip(),
            "fy24_bill": safe_float(ws.cell(r,2).value),
            "fy24_max":  safe_float(ws.cell(r,3).value),
            "fy25_bill": safe_float(ws.cell(r,5).value),
            "fy25_max":  safe_float(ws.cell(r,6).value),
            "fy26_bill": safe_float(ws.cell(r,8).value),
            "fy26_max":  safe_float(ws.cell(r,9).value),
            "uio_fy26":  int(ws.cell(r,12).value or 0),
            "notes":     ws.cell(r,14).value or "",
            "driver":    str(ws.cell(r,13).value or ""),  # old "rate" field
        })
    wb.close()
    return rows

def read_proj_cis(path):
    """Return only CIS rows from projection tab."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["GPS Projection FY2027-30"]
    cis = []
    UIO_DBS = {"ITUK","IUK","UTI","UMI","ISD","RSA","Sverige","IBX","Imotors",
               "Ireland","Greece","AutoWallis","ROM Auto","Loutsios","GasanZammit",
               "Nordic FI","Danmark","BL Iceland","MIDI"}
    EXCL = {"ANADOLU ISUZU OTOMOTIV"}
    none_streak = 0
    for r in range(11, 120):
        v = ws.cell(r,1).value
        if v is None:
            none_streak += 1
            if none_streak > 3: break
            continue
        none_streak = 0
        db = str(v).strip()
        if not db or db.startswith("  "): continue
        if any(db.startswith(p) for p in ("TOTAL","IML Kosha")): break
        if db.startswith("CIS") or db in EXCL or db in UIO_DBS: continue
        cis.append({"db":db,
            "fy27":safe_float(ws.cell(r,5).value),
            "fy28":safe_float(ws.cell(r,8).value),
            "fy29":safe_float(ws.cell(r,11).value),
            "fy30":safe_float(ws.cell(r,14).value)})
    wb.close()
    return cis

def read_gap(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Kosha Gap"]
    data = {}
    for r in range(4, 25):
        k = ws.cell(r,1).value
        if k: data[str(k).strip()] = [ws.cell(r,c).value for c in range(2,8)]
    wb.close()
    return data

def read_db_uio(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["DB Class UIO Input"]
    rows = []
    for r in range(5,300):
        db = ws.cell(r,1).value
        if not db: break
        rows.append({"db":db,"year":ws.cell(r,2).value,
                     "n35":ws.cell(r,3).value or 0,"n75":ws.cell(r,4).value or 0,
                     "mdf":ws.cell(r,5).value or 0,"lcv":ws.cell(r,6).value or 0,
                     "dmax":ws.cell(r,7).value or 0,"total":ws.cell(r,8).value or 0})
    wb.close()
    return rows

# ── OPTION A SOLVER ───────────────────────────────────────────────────────────
def solve_option_a(dbs_order, net_base, grs_base, max_cap, warr_avg, bp, cis):
    """
    Re-solve Option A for one projection year.
    Returns {db: {"net_pct", "grs_pct", "net_rev", "grs_rev", "cap", "warr_avg"}}
    net_base / grs_base: {db: base%}
    max_cap:   {db: market_cap_€}
    warr_avg:  {db: avg_warranty_€}
    """
    # Net solve: X = (BP - CIS - SW - Σ(eff×base)) / Σeff
    net_sum_eff  = sum(max(max_cap[d] - warr_avg.get(d,0), 0) for d in dbs_order)
    net_sum_base = sum(max(max_cap[d]-warr_avg.get(d,0),0) * net_base.get(d,0) for d in dbs_order)
    sw           = sum(warr_avg.get(d,0) for d in dbs_order)
    x_net = (bp - cis - sw - net_sum_base) / net_sum_eff if net_sum_eff else 0

    # Gross solve: X = (BP - CIS - Σ(cap×base)) / Σcap
    grs_sum_cap  = sum(max_cap[d] for d in dbs_order)
    grs_sum_base = sum(max_cap[d] * grs_base.get(d,0) for d in dbs_order)
    x_grs = (bp - cis - grs_sum_base) / grs_sum_cap if grs_sum_cap else 0

    result = {}
    for d in dbs_order:
        cap  = max_cap[d]
        warr = warr_avg.get(d, 0)
        eff  = max(cap - warr, 0)

        net_req = net_base.get(d, 0) + x_net
        grs_req = grs_base.get(d, 0) + x_grs
        infeas_net = net_req > 1.0
        infeas_grs = grs_req > 1.0
        net_req = min(net_req, 1.0)
        grs_req = min(grs_req, 1.0)

        net_rev = eff * net_req + warr   # gross toward BP in net mode
        grs_rev = cap * grs_req          # gross billing in gross mode

        result[d] = {
            "net_pct": net_req, "grs_pct": grs_req,
            "net_rev": net_rev, "grs_rev": grs_rev,
            "infeas_net": infeas_net, "infeas_grs": infeas_grs,
            "cap": cap, "warr": warr,
        }
    return result, x_net, x_grs


def _load_reviewed_bp_fy27() -> dict[str, float]:
    """Reviewed per-DB BP FY27 — single source: 91_build/load_bp_fy27.py."""
    sys.path.insert(0, str(BUILD_DIR))
    from load_bp_fy27 import load_bp_fy27_reviewed, VP_NETWORK_TOTAL_EUR  # noqa: WPS433

    bp = load_bp_fy27_reviewed(write_json=True)
    return bp, VP_NETWORK_TOTAL_EUR


def apply_reviewed_bp_fy27(
    proj_2027: dict,
    dbs_order: list[str],
    cap_yr: dict[str, float],
    warr_avg: dict[str, float],
    bp_reviewed: dict[str, float],
    net_base: dict[str, float],
    grs_base: dict[str, float],
) -> tuple[int, int]:
    """
    Replace FY27 Option-A revenue split with bottom-up reviewed BP per DB.
    Returns (infeasible_net_count, infeasible_grs_count).
    """
    imp_n = imp_g = 0
    for db in dbs_order:
        if db == "MIDI":
            continue
        gps = V5_TO_GPS.get(db)
        if not gps or gps not in bp_reviewed:
            continue
        target = float(bp_reviewed[gps])
        cap = cap_yr[db]
        warr = warr_avg.get(db, 0)
        eff = max(cap - warr, 0)
        net_req = (target - warr) / eff if eff else 0.0
        grs_req = target / cap if cap else 0.0
        infeas_net = net_req > 1.0
        infeas_grs = grs_req > 1.0
        if infeas_net:
            imp_n += 1
        if infeas_grs:
            imp_g += 1
        proj_2027[db] = {
            "net_pct": min(net_req, 1.0),
            "grs_pct": min(grs_req, 1.0),
            "net_rev": target,
            "grs_rev": target,
            "infeas_net": infeas_net,
            "infeas_grs": infeas_grs,
            "cap": cap,
            "warr": warr,
            "base_net": net_base.get(db, 0),
            "base_grs": grs_base.get(db, 0),
        }
    return imp_n, imp_g


def build_bp_reviewed_tab(wb, dbs_order, bp_reviewed, solver_fy27, reviewed_network_eur):
    """Audit tab: reviewed BP FY27 per DB vs prior Option-A split."""
    ws = wb.create_sheet("BP FY27 Reviewed")
    ws.sheet_properties.tabColor = ACCENT
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 48

    title_row(ws, 1, "  BP FY27 — Reviewed budget per DB (24 Apr 2026)", cols=5)
    note_row(
        ws,
        2,
        "Source: 11_planning/budget_per_DB_reviewed_24042026.xlsx · Incentive FY27 + VP turnover. "
        f"Network €{reviewed_network_eur/1e6:.2f}M. FY27 projection tab uses reviewed € (not Kosha Option-A split).",
        cols=5,
    )
    hdr(ws, 4, 1, "Distributor")
    hdr(ws, 4, 2, "Option A\nFY27 €")
    hdr(ws, 4, 3, "Reviewed\nFY27 €")
    hdr(ws, 4, 4, "Δ €")
    hdr(ws, 4, 5, "GPS code / note")

    r = 5
    tot_solver = tot_rev = 0.0
    for db in dbs_order:
        gps = V5_TO_GPS.get(db, "—")
        solver_e = solver_fy27.get(db, {}).get("net_rev") if solver_fy27 else None
        rev_e = bp_reviewed.get(gps) if gps in bp_reviewed else None
        if solver_e:
            tot_solver += solver_e
        if rev_e:
            tot_rev += rev_e
        bg = LGR if (r - 5) % 2 else None
        lc(ws, r, 1, db, bg=bg)
        if solver_e is not None:
            dc(ws, r, 2, solver_e, "€#,##0", bg=bg)
        else:
            dc(ws, r, 2, "—", bg=bg)
        if rev_e is not None:
            dc(ws, r, 3, rev_e, "€#,##0", bold=True, bg=bg)
            delta = rev_e - (solver_e or 0)
            dc(ws, r, 4, delta, "€#,##0", bg=bg)
        else:
            dc(ws, r, 3, "—", bg=bg)
            dc(ws, r, 4, "—", bg=bg)
        note = gps if gps != "—" else ("non-GPS channel" if db == "MIDI" else "no reviewed row")
        lc(ws, r, 5, note, italic=True, bg=bg)
        r += 1

    ws.row_dimensions[r].height = 18
    for c in range(1, 6):
        ws.cell(r, c).fill = F(DARK)
        ws.cell(r, c).border = Br()
    lc(ws, r, 1, "TOTAL (mapped DBs)", bold=True)
    ws.cell(r, 1).font = Fn(bold=True, color=WHITE, size=9)
    dc(ws, r, 2, tot_solver, "€#,##0", bold=True)
    ws.cell(r, 2).font = Fn(bold=True, color=WHITE, size=9)
    dc(ws, r, 3, tot_rev, "€#,##0", bold=True)
    ws.cell(r, 3).font = Fn(bold=True, color=WHITE, size=9)
    dc(ws, r, 4, tot_rev - tot_solver, "€#,##0", bold=True)
    ws.cell(r, 4).font = Fn(bold=True, color=WHITE, size=9)
    return ws

# ── TAB 1: Dashboard ──────────────────────────────────────────────────────────
def build_dashboard(wb):
    ws = wb.create_sheet("Dashboard")
    ws.sheet_properties.tabColor = DARK
    ws.sheet_view.showGridLines = False
    for col, w in {"A":2,"B":24,"C":14,"D":14,"E":14,"F":14,"G":14,"H":14,"I":14}.items():
        ws.column_dimensions[col].width = w

    title_row(ws, 1, "  ISZE  ·  GPS Performance Dashboard  ·  FY2024–FY2030", cols=9)
    ws.row_dimensions[2].height = 34
    ws.cell(2,2,"GPS Mode →").font = Fn(bold=True, size=10); ws.cell(2,2).alignment = Al("right")
    tog = ws.cell(2,3,"Net")
    tog.font=Fn(bold=True,size=12,color=DARK); tog.fill=F(ACCENT); tog.alignment=Al("center"); tog.border=Br(DARK)
    dv = DataValidation(type="list",formula1='"Net,Gross"',allow_blank=False,showDropDown=False)
    dv.sqref="C2"; ws.add_data_validation(dv)
    ws.cell(2,4,"← select Net or Gross").font=Fn(italic=True,size=9,color=DGR); ws.cell(2,4).alignment=Al("left")
    ws.row_dimensions[3].height = 8

    ws.merge_cells("B4:I4")
    ws.cell(4,2,"  Network Summary").font=Fn(bold=True,color=WHITE,size=10)
    ws.cell(4,2).fill=F(MID); ws.row_dimensions[4].height=20

    ws.row_dimensions[5].height = 28
    for c,txt in [(2,"Metric"),(3,"FY2024\nActual"),(4,"FY2025\nActual"),(5,"FY2026\nActual"),
                  (6,"FY2027\nProjection"),(7,"FY2028\nProjection"),(8,"FY2029\nProjection"),(9,"FY2030\nProjection")]:
        hdr(ws,5,c,txt)

    for r,label,fmt,bold in [
        (6,"Network GPS% / Revenue → BP","0.0%",True),
        (7,"Total Revenue → BP (€)","€#,##0",False),
        (8,"IML Kosha BP (€)","€#,##0",False),
        (9,"Gap vs BP (€)","€#,##0;[Red](€#,##0)",True),
        (10,"Uplift X required",'0.00"pp"',False),
        (11,"DBs exceeding cap","@",False),
    ]:
        ws.row_dimensions[r].height = 18
        lc(ws,r,2,label,bold=bold)
        for c in range(3,10):
            cell=ws.cell(r,c,"…"); cell.number_format=fmt
            cell.font=Fn(bold=bold,size=9); cell.alignment=Al("center"); cell.border=Br()

    ws.row_dimensions[12].height = 8
    ws.merge_cells("B13:I13")
    ws.cell(13,2,"  Distributor GPS%  ·  FY2024 / FY2025 / FY2026  ·  Green <85%  ·  Amber 85–100%  ·  Red ≥100%")
    ws.cell(13,2).font=Fn(bold=True,color=WHITE,size=10); ws.cell(13,2).fill=F(MID); ws.row_dimensions[13].height=20

    ws.row_dimensions[14].height = 28
    for c,txt in [(2,"Distributor"),(3,"FY2024\nGPS%"),(4,"FY2025\nGPS%"),(5,"FY2026\nGPS%"),(6,"UIO FY26"),(7,"€/UIO")]:
        hdr(ws,14,c,txt)
    return ws

# ── TAB 2: GPS Actuals FY24-26 ────────────────────────────────────────────────
# Hidden col map: M=Net24% N=Net24Bill O=Grs24% P=Grs24Bill Q=FY24Max
#                 R=Net25% S=Net25Bill T=Grs25% U=Grs25Bill V=FY25Max
#                 W=Net26% X=Net26Bill Y=Grs26% Z=Grs26Bill
#                 AA=NetBase% AB=GrsBase%
def build_actuals(wb, net_rows, grs_rows, new_max, uio_data):
    ws = wb.create_sheet("GPS Actuals FY24-26")
    ws.sheet_properties.tabColor = MID
    ws.sheet_view.showGridLines = False
    g = {r["db"]:r for r in grs_rows}

    for col,w in {"A":20,"B":9,"C":9,"D":9,"E":13,"F":9,"G":13,"H":9,"I":13,"J":13,"K":9,"L":28}.items():
        ws.column_dimensions[col].width = w
    for col in ["M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","AA","AB"]:
        ws.column_dimensions[col].width = 1; ws.column_dimensions[col].hidden = True

    title_row(ws,1,"  ISZE  ·  GPS Capture Rate  ·  FY2024–FY2026 Actuals  ·  Max spend = UIO v19 × class rates",cols=12)
    note_row(ws,2,"Net = billing ex-warranty ÷ max spend.  Gross = total billing ÷ max spend.  Max spend recomputed from UIO v19 class breakdown (LD €739 · F/MD €887 · LCV €250).  Green <85%  ·  Amber 85–100%  ·  Red ≥100%",cols=12)

    ws.row_dimensions[3].height = 28
    for c,txt in [(1,"Distributor"),(2,"UIO\nFY26"),(3,"Rate\n€/UIO"),(4,"FY24\nGPS%"),(5,"FY24\nBill €"),
                  (6,"FY25\nGPS%"),(7,"FY25\nBill €"),(8,"FY26\nGPS%"),(9,"FY26\nBill €"),
                  (10,"FY26\nMax Spend"),(11,"GPS Base\n(avg25+26)"),(12,"Notes")]:
        hdr(ws,3,c,txt)

    for i, nr in enumerate(net_rows):
        r = 4+i; ws.row_dimensions[r].height = 16
        db = nr["db"]; gr = g.get(db, nr)
        bg = LGR if i%2 else None

        # Updated max spend from v19
        ms24 = new_max.get(db,{}).get(2024, nr["fy24_max"])
        ms25 = new_max.get(db,{}).get(2025, nr["fy25_max"])
        ms26 = new_max.get(db,{}).get(2026, nr["fy26_max"])

        # Recompute GPS% from billing / new max spend
        n24p = nr["fy24_bill"]/ms24 if ms24 else 0
        g24p = gr["fy24_bill"]/ms24 if ms24 else 0
        n25p = nr["fy25_bill"]/ms25 if ms25 else 0
        g25p = gr["fy25_bill"]/ms25 if ms25 else 0
        n26p = nr["fy26_bill"]/ms26 if ms26 else 0
        g26p = gr["fy26_bill"]/ms26 if ms26 else 0
        n_base = (n25p+n26p)/2; g_base = (g25p+g26p)/2

        # UIO from v19 2026F (or source fallback)
        uio26_classes = uio_data.get(db,{}).get(2026,{})
        uio26 = sum(uio26_classes.values()) or nr["uio_fy26"]
        rate26 = round(ms26/uio26) if uio26 else 0

        lc(ws,r,1,db,bg=bg)
        dc(ws,r,2,uio26,"#,##0",bg=bg)
        dc(ws,r,3,rate26,"€#,##0",bg=bg)
        dc(ws,r,10,ms26,"€#,##0",bg=bg)
        lc(ws,r,12,nr["notes"],italic=True)

        # Toggle display formulas
        for col_d,nc,gc_,fmt in [
            (4,"M","O","0.0%"),(5,"N","P","€#,##0"),
            (6,"R","T","0.0%"),(7,"S","U","€#,##0"),
            (8,"W","Y","0.0%"),(9,"X","Z","€#,##0"),
            (11,"AA","AB","0.0%"),
        ]:
            cell=ws.cell(r,col_d,f'=IF({TOGGLE}="Net",{nc}{r},{gc_}{r})')
            cell.number_format=fmt; cell.font=Fn(bold=(col_d==8),size=9)
            cell.alignment=Al("center" if "%"in fmt else "right"); cell.border=Br()
            if bg and col_d in (4,6,8,11): cell.fill=F(bg)

        # Hidden raw data — billing unchanged, GPS% recomputed from new max spend
        raw=[(13,n24p),(14,nr["fy24_bill"]),(15,g24p),(16,gr["fy24_bill"]),(17,ms24),
             (18,n25p),(19,nr["fy25_bill"]),(20,g25p),(21,gr["fy25_bill"]),(22,ms25),
             (23,n26p),(24,nr["fy26_bill"]),(25,g26p),(26,gr["fy26_bill"]),
             (27,n_base),(28,g_base)]
        for c_,v in raw:
            cell=ws.cell(r,c_,v or 0)
            cell.number_format="0.00%" if c_ in (13,15,18,20,23,25,27,28) else "#,##0"

    # Total row
    n=len(net_rows); R=4+n; r1,r2=4,4+n-1
    ws.row_dimensions[R].height=18
    for c in range(1,13): ws.cell(R,c).fill=F(DARK); ws.cell(R,c).border=Br()
    ws.cell(R,1,"TOTAL — UIO Distributors").font=Fn(bold=True,color=WHITE,size=9)
    ws.cell(R,1).alignment=Al("left")

    for col_d,nb,gb,mx,fmt in [
        (4,"N","P","Q","0.0%"),(5,"N","P","Q","€#,##0"),
        (6,"S","U","V","0.0%"),(7,"S","U","V","€#,##0"),
        (8,"X","Z",None,"0.0%"),(9,"X","Z",None,"€#,##0"),
        (11,"AA","AB",None,"0.0%"),
    ]:
        if fmt=="0.0%":
            f=(f'=IF({TOGGLE}="Net",SUM({nb}{r1}:{nb}{r2})/SUM({mx}{r1}:{mx}{r2}),SUM({gb}{r1}:{gb}{r2})/SUM({mx}{r1}:{mx}{r2}))'
               if mx else
               f'=IF({TOGGLE}="Net",SUM(X{r1}:X{r2})/SUM(J{r1}:J{r2}),SUM(Z{r1}:Z{r2})/SUM(J{r1}:J{r2}))')
        else:
            f=(f'=IF({TOGGLE}="Net",SUM({nb}{r1}:{nb}{r2}),SUM({gb}{r1}:{gb}{r2}))'
               if mx else
               f'=IF({TOGGLE}="Net",SUM(X{r1}:X{r2}),SUM(Z{r1}:Z{r2}))')
        cell=ws.cell(R,col_d,f); cell.number_format=fmt
        cell.font=Fn(bold=True,color=WHITE,size=9)
        cell.alignment=Al("center" if "%"in fmt else "right"); cell.border=Br()

    ws.cell(R,10,f"=SUM(J{r1}:J{r2})").number_format="€#,##0"
    ws.cell(R,10).font=Fn(bold=True,color=WHITE,size=9); ws.cell(R,10).alignment=Al("right"); ws.cell(R,10).border=Br()

    for col in ["D","F","H"]: traffic(ws,col,4,4+n-1)

    LR=R+2; ws.row_dimensions[LR].height=14
    ws.cell(LR,1,"Legend:").font=Fn(bold=True,size=8)
    for c,bg,fg,txt in [(2,GBG,GFG,"< 85%"),(3,ABG,AFG,"85–100%"),(4,RBG,RFG,"≥ 100%")]:
        cell=ws.cell(LR,c,txt); cell.fill=F(bg); cell.font=Fn(size=8,color=fg,bold=True)
        cell.alignment=Al("center"); cell.border=Br()

    return ws, R

# ── TAB 3: GPS Projection FY27-30 ─────────────────────────────────────────────
def build_projection(wb, dbs_order, proj_results, cis_rows):
    ws = wb.create_sheet("GPS Projection FY27-30")
    ws.sheet_properties.tabColor = MID
    ws.sheet_view.showGridLines = False

    for col,w in {"A":18,"B":18,"C":9,"D":9,"E":13,"F":9,"G":13,"H":9,"I":13,"J":9,"K":13}.items():
        ws.column_dimensions[col].width = w
    for col in ["L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","AA","AB","AC"]:
        ws.column_dimensions[col].width=1; ws.column_dimensions[col].hidden=True

    title_row(ws,1,"  ISZE  ·  GPS Projection FY2027–FY2030  ·  FY27 reviewed BP per DB · FY28–30 Option A",cols=11)
    note_row(ws,2,"FY27: bottom-up reviewed budget (24 Apr 2026) per distributor — tab 'BP FY27 Reviewed'.  "
              "FY28–30: uniform Option A uplift X.  Net: effective cap; Gross: full market cap.",cols=11)

    ws.row_dimensions[3].height=28
    for c,txt in [(1,"Distributor"),(2,"Driver"),(3,"GPS Base\n(avg25+26)"),
                  (4,"FY27\nGPS%"),(5,"FY27\nRev → BP €"),
                  (6,"FY28\nGPS%"),(7,"FY28\nRev → BP €"),
                  (8,"FY29\nGPS%"),(9,"FY29\nRev → BP €"),
                  (10,"FY30\nGPS%"),(11,"FY30\nRev → BP €")]:
        hdr(ws,3,c,txt)

    for i,db in enumerate(dbs_order):
        r=4+i; ws.row_dimensions[r].height=16
        bg=LGR if i%2 else None
        lc(ws,r,1,db,bg=bg)

        r27=proj_results[2027][db]; r28=proj_results[2028][db]
        r29=proj_results[2029][db]; r30=proj_results[2030][db]

        # Hidden base (net/gross)
        net_b=(r27["net_pct"]-0)  # base is in the individual year's stored value
        # Actually base pct = from hidden cols AA/AB in actuals tab
        # Store as static hidden values
        n_base=r27.get("base_net",r27["net_pct"]); g_base=r27.get("base_grs",r27["grs_pct"])
        # Actually we'll store base separately — use the pre-computed value passed in
        ws.cell(r,12,n_base).number_format="0.00%"  # hidden L
        ws.cell(r,13,g_base).number_format="0.00%"  # hidden M

        cell=ws.cell(r,3,f'=IF({TOGGLE}="Net",L{r},M{r})')
        cell.number_format="0.0%"; cell.font=Fn(size=9); cell.alignment=Al("center"); cell.border=Br()
        if bg: cell.fill=F(bg)

        for col_d,yr_data,np_c,nr_c,gp_c,gr_c in [
            (4,r27,"N","O","P","Q"),(6,r28,"R","S","T","U"),
            (8,r29,"V","W","X","Y"),(10,r30,"Z","AA","AB","AC"),
        ]:
            cp=ws.cell(r,col_d,f'=IF({TOGGLE}="Net",{np_c}{r},{gp_c}{r})')
            cp.number_format="0.0%"; cp.font=Fn(size=9); cp.alignment=Al("center"); cp.border=Br()
            if bg: cp.fill=F(bg)
            cr_=ws.cell(r,col_d+1,f'=IF({TOGGLE}="Net",{nr_c}{r},{gr_c}{r})')
            cr_.number_format="€#,##0"; cr_.font=Fn(size=9); cr_.alignment=Al("right"); cr_.border=Br()

            # Infeasibility marker
            if yr_data["infeas_net"] or yr_data["infeas_grs"]:
                note_txt="⚠ >100%" if yr_data["infeas_net"] else "⚠ Grs >100%"
                cp.fill=F(RBG); cp.font=Fn(size=9,color=RFG,bold=True)

            # Hidden data
            offset={"N":14,"O":15,"P":16,"Q":17,"R":18,"S":19,"T":20,"U":21,
                    "V":22,"W":23,"X":24,"Y":25,"Z":26,"AA":27,"AB":28,"AC":29}
            for hcol,val in [(np_c,yr_data["net_pct"]),(nr_c,yr_data["net_rev"]),
                             (gp_c,yr_data["grs_pct"]),(gr_c,yr_data["grs_rev"])]:
                cell=ws.cell(r,offset[hcol],val or 0)
                cell.number_format="0.00%" if hcol in(np_c,gp_c) else "#,##0"

    n=len(dbs_order); R_NET=4+n
    ws.row_dimensions[R_NET].height=18
    for c in range(1,12): ws.cell(R_NET,c).fill=F(DARK); ws.cell(R_NET,c).border=Br()
    ws.cell(R_NET,1,"TOTAL — UIO Distributors").font=Fn(bold=True,color=WHITE,size=9)
    ws.cell(R_NET,1).alignment=Al("left")
    r1,r2=4,4+n-1
    for col_d,nr_,gr_ in [(5,"O","Q"),(7,"S","U"),(9,"W","Y"),(11,"AA","AC")]:
        f=f'=IF({TOGGLE}="Net",SUM({nr_}{r1}:{nr_}{r2}),SUM({gr_}{r1}:{gr_}{r2}))'
        cell=ws.cell(R_NET,col_d,f)
        cell.number_format="€#,##0"; cell.font=Fn(bold=True,color=WHITE,size=9)
        cell.alignment=Al("right"); cell.border=Br()
    for col_d in [4,6,8,10]:
        ws.cell(R_NET,col_d,"—").font=Fn(bold=True,color=WHITE,size=9)
        ws.cell(R_NET,col_d).alignment=Al("center"); ws.cell(R_NET,col_d).border=Br()

    # CIS
    R_CIS=R_NET+1; ws.row_dimensions[R_CIS].height=16
    ws.merge_cells(f"A{R_CIS}:C{R_CIS}")
    ws.cell(R_CIS,1,"CIS & Non-UIO Distributors").font=Fn(bold=True,color=WHITE,size=9)
    ws.cell(R_CIS,1).fill=F(LIGHT); ws.cell(R_CIS,1).alignment=Al("left"); ws.cell(R_CIS,1).border=Br()

    for j,nc in enumerate(cis_rows):
        r=R_CIS+1+j; ws.row_dimensions[r].height=15
        bg=LGR if j%2 else None
        lc(ws,r,1,nc["db"],italic=True,bg=bg); lc(ws,r,2,"CIS — no UIO",italic=True,bg=bg); lc(ws,r,3,"N/A",italic=True,bg=bg)
        for col_d,fy in [(5,"fy27"),(7,"fy28"),(9,"fy29"),(11,"fy30")]:
            dc(ws,r,col_d,nc[fy],"€#,##0",bg=bg)
            cell_d=ws.cell(r,col_d-1,"—"); cell_d.alignment=Al("center"); cell_d.border=Br()
            if bg: cell_d.fill=F(bg)

    n_cis=len(cis_rows); R_GRAND=R_CIS+1+n_cis
    ws.row_dimensions[R_GRAND].height=18
    cis_r1=R_CIS+1; cis_r2=R_CIS+n_cis
    for c in range(1,12): ws.cell(R_GRAND,c).fill=F(DARK); ws.cell(R_GRAND,c).border=Br()
    ws.cell(R_GRAND,1,"GRAND TOTAL (UIO + CIS)").font=Fn(bold=True,color=WHITE,size=9)
    ws.cell(R_GRAND,1).alignment=Al("left")
    for col_d in [5,7,9,11]:
        f=f"={gcl(col_d)}{R_NET}+SUM({gcl(col_d)}{cis_r1}:{gcl(col_d)}{cis_r2})"
        cell=ws.cell(R_GRAND,col_d,f)
        cell.number_format="€#,##0"; cell.font=Fn(bold=True,color=WHITE,size=9)
        cell.alignment=Al("right"); cell.border=Br()
    for col_d in [4,6,8,10]:
        ws.cell(R_GRAND,col_d,"—").font=Fn(bold=True,color=WHITE,size=9)
        ws.cell(R_GRAND,col_d).alignment=Al("center"); ws.cell(R_GRAND,col_d).border=Br()

    # X / impossible summary rows
    R_X=R_GRAND+2; ws.row_dimensions[R_X].height=13
    ws.cell(R_X,1,"Uplift X").font=Fn(italic=True,size=8,color=DGR); ws.cell(R_X,1).alignment=Al("left")
    R_IMP=R_X+1; ws.row_dimensions[R_IMP].height=13
    ws.cell(R_IMP,1,"DBs >100%").font=Fn(italic=True,size=8,color=RFG); ws.cell(R_IMP,1).alignment=Al("left")
    for col_d,gap_col in [(4,"C"),(6,"D"),(8,"E"),(10,"F")]:
        cx=ws.cell(R_X,col_d,f"='Kosha Gap'!{gap_col}14")
        cx.number_format='0.00"pp"'; cx.font=Fn(italic=True,size=8,color=DGR)
        cx.alignment=Al("center"); cx.border=Br()
        ci=ws.cell(R_IMP,col_d,f"='Kosha Gap'!{gap_col}17")
        ci.font=Fn(italic=True,size=8,color=RFG); ci.alignment=Al("center"); ci.border=Br()

    for col in ["D","F","H","J"]: traffic(ws,col,4,4+n-1)
    return ws, R_NET, R_GRAND, R_X, R_IMP

# ── TAB 4: Kosha Gap ──────────────────────────────────────────────────────────
def build_kosha_gap(wb, net_gap, grs_gap, x_net, x_grs, imp_net, imp_grs, net_proj_results, grs_proj_results,
                    bp_fy27_reviewed_eur=None, fy27_per_db_bp=False):
    ws = wb.create_sheet("Kosha Gap")
    ws.sheet_properties.tabColor = ACCENT
    ws.sheet_view.showGridLines = False
    for col,w in {"A":40,"B":14,"C":14,"D":14,"E":14,"F":14,"G":22}.items():
        ws.column_dimensions[col].width = w
    for col in ["H","I","J","K","L","M","N","O","P","Q"]:
        ws.column_dimensions[col].width=1; ws.column_dimensions[col].hidden=True

    title_row(ws,1,"  ISZE  ·  GPS vs IML Kosha BP Targets  ·  Summary  ·  Re-solved with UIO v19",cols=7)
    note_row(ws,2,"⚠ INTERNAL.  Net: billing ex-warranty + warranty credited toward BP.  Gross: gross billing.  X values re-solved with class-weighted market caps.  Toggle on Dashboard·C2.",cols=7)

    ws.row_dimensions[3].height=28
    for c,txt in [(1,"Metric"),(2,"FY2026\nActual"),(3,"FY2027"),(4,"FY2028"),(5,"FY2029"),(6,"FY2030"),(7,"Note")]:
        hdr(ws,3,c,txt,bg=ACCENT); ws.cell(3,c).font=Fn(bold=True,color=DARK,size=9)

    # Revenue / BP rows from source (same in net/gross — revenue numerics identical)
    fys=["fy26","fy27","fy28","fy29","fy30"]; cols=[2,3,4,5,6]
    REV_KEY=next((k for k in net_gap if "UIO DBs" in k),None)
    CIS_KEY=next((k for k in net_gap if "CIS" in k and "GPS Revenue" in k),None)
    TOT_KEY=next((k for k in net_gap if k=="TOTAL GPS Revenue (€)"),None)
    BP_KEY =next((k for k in net_gap if "Kosha BP" in k),None)
    GAP_KEY=next((k for k in net_gap if "Gap: GPS" in k),None)
    GAPP_K =next((k for k in net_gap if "Gap %" in k),None)
    X_KEY  =next((k for k in net_gap if "Uplift X" in k),None)
    IMP_KEY=next((k for k in net_gap if "DBs requiring" in k),None)
    CAGR_G =next((k for k in net_gap if "CAGR GPS" in k),None)
    CAGR_B =next((k for k in net_gap if "CAGR IML" in k),None)
    IMP_DB =next((k for k in net_gap if "Distributors with" in k),None)

    def to_dict(lst):
        return dict(zip(fys,lst[:5])) if lst else {}

    def write_row(r,label,vals,fmt,bold=False,bg=None):
        ws.row_dimensions[r].height=16; lc(ws,r,1,label,bold=bold,bg=bg)
        for ci,fy in zip(cols,fys):
            v=vals.get(fy); cell=ws.cell(r,ci,v if v is not None else "—")
            if isinstance(v,(int,float)): cell.number_format=fmt
            cell.font=Fn(bold=bold,size=9); cell.alignment=Al("right"); cell.border=Br()
            if bg: cell.fill=F(bg)

    def write_toggle(r,label,nv,gv,fmt,bold=False):
        ws.row_dimensions[r].height=16; lc(ws,r,1,label)
        for idx,(ci,fy) in enumerate(zip(cols,fys)):
            n_val=nv.get(fy); g_val=gv.get(fy)
            hcn=idx+8; hcg=idx+13
            if n_val is not None: ws.cell(r,hcn,n_val).number_format=fmt
            if g_val is not None: ws.cell(r,hcg,g_val).number_format=fmt
            if n_val==g_val or (n_val is None and g_val is None):
                cell=ws.cell(r,ci,n_val if n_val is not None else "—")
                if isinstance(n_val,(int,float)): cell.number_format=fmt
            else:
                cell=ws.cell(r,ci,f'=IF({TOGGLE}="Net",{gcl(hcn)}{r},{gcl(hcg)}{r})')
                cell.number_format=fmt
            cell.font=Fn(bold=bold,size=9); cell.alignment=Al("right"); cell.border=Br()

    # Compute projected revenue totals from newly solved results
    def proj_rev(proj_r, mode):
        """Sum of all DB revenues for a year in given mode."""
        return sum(v[f"{mode}_rev"] for v in proj_r.values())

    # Re-build revenue toward BP from new solve
    cis_vals = to_dict(net_gap.get(CIS_KEY) if CIS_KEY else [None]*5)
    # FY26 actuals from source (unchanged billing)
    rev_uio = to_dict(net_gap.get(REV_KEY) if REV_KEY else [None]*5)
    bp_vals  = to_dict(net_gap.get(BP_KEY) if BP_KEY else [None]*5)
    if bp_fy27_reviewed_eur is not None:
        bp_vals["fy27"] = bp_fy27_reviewed_eur
    # FY28-30 BP target from LIVE PL Plan row 186 (BP global), not the stale v4a gap snapshot baked
    # in at v4a build time, so the displayed target matches the live figure the uplift solve targets
    # (otherwise Gap shows a phantom -EUR2.91M when v4a predates the FY29/30 downward revision).
    for _bp_fy, _bp_yr in (("fy28", 2028), ("fy29", 2029), ("fy30", 2030)):
        if BP.get(_bp_yr) is not None:
            bp_vals[_bp_fy] = BP[_bp_yr]
    cagr_g   = to_dict(net_gap.get(CAGR_G) if CAGR_G else [None]*5)
    cagr_b   = to_dict(net_gap.get(CAGR_B) if CAGR_B else [None]*5)

    # Override projection years with new solve results
    for yr_int,yr_key in [(2027,"fy27"),(2028,"fy28"),(2029,"fy29"),(2030,"fy30")]:
        rev_uio[yr_key] = proj_rev(net_proj_results[yr_int],"net")

    rev_tot = {fy: (rev_uio.get(fy,0) or 0) + (cis_vals.get(fy,0) or 0) for fy in fys}
    gap_vals = {fy: (rev_tot.get(fy,0) or 0) - (bp_vals.get(fy,0) or 0) for fy in fys}
    gapp_vals= {fy: gap_vals[fy]/(bp_vals.get(fy,1) or 1) for fy in fys}

    # X values (already x100 from solver); FY27 may use per-DB reviewed BP instead of Option A
    net_x_d = {"fy26":None,"fy27":x_net[2027]*100 if x_net.get(2027) is not None else None,"fy28":x_net[2028]*100,
                "fy29":x_net[2029]*100,"fy30":x_net[2030]*100}
    grs_x_d = {"fy26":None,"fy27":x_grs[2027]*100 if x_grs.get(2027) is not None else None,"fy28":x_grs[2028]*100,
                "fy29":x_grs[2029]*100,"fy30":x_grs[2030]*100}
    net_i_d  = {"fy26":imp_net.get(2026,0),"fy27":imp_net[2027],"fy28":imp_net[2028],
                "fy29":imp_net[2029],"fy30":imp_net[2030]}
    grs_i_d  = {"fy26":imp_grs.get(2026,0),"fy27":imp_grs[2027],"fy28":imp_grs[2028],
                "fy29":imp_grs[2029],"fy30":imp_grs[2030]}

    SBG="EBF0FA"
    write_row(4,"Revenue toward BP — UIO DBs (€)",rev_uio,"€#,##0")
    write_row(5,"GPS Revenue — CIS / Other (€)",cis_vals,"€#,##0")
    write_row(6,"TOTAL GPS Revenue (€)",rev_tot,"€#,##0",bold=True,bg=SBG)
    ws.row_dimensions[7].height=5
    write_row(8,"BP Target (€)",bp_vals,"€#,##0",bold=True,bg=SBG)
    ws.cell(8,7,"FY27: reviewed per-DB (24 Apr 2026). FY28–30: Kosha network row." if fy27_per_db_bp else "")
    ws.cell(8,7).font=Fn(size=8,italic=True,color=DGR)
    ws.row_dimensions[9].height=5; ws.row_dimensions[10].height=5
    write_row(11,"Gap: GPS Revenue − BP Target (€)",gap_vals,"€#,##0;[Red](€#,##0)",bold=True)
    write_row(12,"Gap as % of BP Target",gapp_vals,"0.0%;[Red](0.0%)")
    ws.row_dimensions[13].height=5
    write_toggle(14,"Required Uplift X — Option A (pp)",net_x_d,grs_x_d,'0.00"pp"')
    if fy27_per_db_bp:
        ws.cell(14,3,"per-DB BP")
        ws.cell(14,3).font=Fn(size=9,italic=True,color=DGR)
        ws.cell(14,7,"FY27 uses reviewed € per DB — no single uniform X. See 'BP FY27 Reviewed'.")
        ws.cell(14,7).font=Fn(size=8,italic=True,color=DGR)
    write_row(15,"CAGR GPS Revenue from FY2026",cagr_g,"0.0%")
    write_row(16,"CAGR IML BP Target from FY2026",cagr_b,"0.0%")
    write_toggle(17,"DBs requiring GPS% > 100% (impossible)",net_i_d,grs_i_d,"@")

    for ci in cols:
        cell=ws.cell(11,ci); v=gap_vals.get(fys[ci-2])
        if isinstance(v,(int,float)):
            if v>0: cell.fill=F(GBG); cell.font=Fn(bold=True,color=GFG,size=9)
            elif v<0: cell.fill=F(RBG); cell.font=Fn(bold=True,color=RFG,size=9)
    return ws

# ── TAB 5: DB Rates ───────────────────────────────────────────────────────────
def build_db_rates(wb, uio_data, ituk_uio=None):
    ws = wb.create_sheet("DB Rates")
    ws.sheet_properties.tabColor = MGR
    ws.sheet_view.showGridLines = False
    for col,w in {"A":18,"B":12,"C":40,"D":9,"E":9,"F":9,"G":9,"H":9,"I":12,"J":12}.items():
        ws.column_dimensions[col].width = w

    title_row(ws,1,"  ISZE  ·  Vehicle Class Wallet Rates  &  Distributor UIO v19 Breakdown",cols=10)
    note_row(ws,2,"Network: LD €739 · F/MD €887 · LCV €250.  ITUK: N35 €296 · N75/LD €739 · F/MD €887 (DVLA car park + UIO v19 projection).",cols=10)

    cls_rates=[
        {"class":"N35 Grafter","rate":296,"note":"£400 retail × (1−34% GP) × 1.12 FX.  ITUK N35 only (DVLA car park)."},
        {"class":"N75 / LD CV","rate":739,"note":"£1,000 retail × (1−34% GP) × 1.12 FX.  Network-wide LD CV rate (replaces legacy €1,120)."},
        {"class":"F-series / MD","rate":887,"note":"£1,200 retail × (1−34% GP) × 1.12 FX.  F-series & MD/F trucks (replaces legacy €1,344)."},
        {"class":"LCV / D-Max","rate":250,"note":"Jerome confirmed 30-Jun-2026 as ISZE standard wallet rate."},
        {"class":"D-Max (standalone)","rate":None,"note":"NOT SET independently.  Uses €250 LCV proxy.  Confirm when validated."},
    ]

    ws.row_dimensions[3].height=8
    ws.merge_cells("A4:J4"); ws.cell(4,1,"  § 1 — Vehicle Class Wallet Rates (€/UIO/yr)").font=Fn(bold=True,color=WHITE,size=10)
    ws.cell(4,1).fill=F(MID); ws.cell(4,1).alignment=Al("left"); ws.row_dimensions[4].height=20
    ws.row_dimensions[5].height=28
    for c,txt in [(1,"Vehicle Class"),(2,"€/UIO/yr"),(3,"Source & Confidence")]: hdr(ws,5,c,txt)
    for i,cr in enumerate(cls_rates):
        r=6+i; ws.row_dimensions[r].height=16; bg=LGR if i%2 else None
        lc(ws,r,1,cr["class"],bg=bg); dc(ws,r,2,cr["rate"],"€#,##0",bg=bg)
        lc(ws,r,3,cr["note"],italic=True,bg=bg)

    R2=6+len(cls_rates)+2
    ws.merge_cells(f"A{R2}:J{R2}")
    ws.cell(R2,1,"  § 2 — Distributor UIO by Vehicle Class  (from UIO v19  ·  FY2026F)").font=Fn(bold=True,color=WHITE,size=10)
    ws.cell(R2,1).fill=F(MID); ws.cell(R2,1).alignment=Al("left"); ws.row_dimensions[R2].height=20

    HR=R2+1; ws.row_dimensions[HR].height=28
    for c,txt in [(1,"Distributor"),(2,"CV LD\nUIO"),(3,"F-Series\nUIO"),(4,"MD\nUIO"),
                  (5,"LCV\nUIO"),(6,"Total\nUIO"),(7,"Max Spend €\n(class-wtd)"),(8,"€/UIO\n(wtd)"),(9,"Source")]:
        hdr(ws,HR,c,txt)

    GPS_DBS = ["ITUK","IUK","UTI","UMI","ISD","RSA","Sverige","IBX","Imotors",
               "Ireland","Greece","AutoWallis","ROM Auto","Loutsios","GasanZammit",
               "Nordic FI","Danmark","BL Iceland","MIDI"]

    for i,db in enumerate(GPS_DBS):
        r=HR+1+i; ws.row_dimensions[r].height=15
        bg=LGR if i%2 else None
        if db == "ITUK" and ituk_uio:
            cls26 = ituk_uio.get(2026, {})
            n35 = int(round(cls26.get("N35", 0)))
            n75 = int(round(cls26.get("N75_LD", 0)))
            fmd = int(round(cls26.get("F_MD", 0)))
            ld, fs, md, lcv = n35, n75, fmd, 0
            total = n35 + n75 + fmd
            ms = max_spend_from_buckets(cls26, "ITUK")
            source = "DVLA car park + UIO v19 projection"
        else:
            cls26=uio_data.get(db,{}).get(2026,{})
            ld=cls26.get("LD",0); fs=cls26.get("F-Series",0); md=cls26.get("MD",0); lcv=cls26.get("LCV",0)
            total=ld+fs+md+lcv
            ms=ld*739+fs*887+md*887+lcv*250
            source="UIO v19 2026F" if total>0 else ("SIMI hybrid" if db=="Ireland" else "—")
        rate=round(ms/total) if total else 0
        lc(ws,r,1,db,bg=bg)
        for c_,v in [(2,ld),(3,fs),(4,md),(5,lcv),(6,total)]:
            dc(ws,r,c_,v,"#,##0",bg=bg)
        dc(ws,r,7,ms or None,"€#,##0",bg=bg)
        dc(ws,r,8,rate or None,"€#,##0",bg=bg)
        lc(ws,r,9,source,italic=True,bg=bg)

    return ws

# ── TAB 6: Method ─────────────────────────────────────────────────────────────
def build_method(wb):
    ws = wb.create_sheet("Method & Assumptions")
    ws.sheet_properties.tabColor = MGR
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width=3; ws.column_dimensions["B"].width=28; ws.column_dimensions["C"].width=62
    title_row(ws,1,"  ISZE GPS v5  ·  Method, Sources & Assumptions",cols=3)

    sections=[
        ("§ 1 — GPS Scope & Toggle",[
            ("Scope","ISZE → Distributor billing only.  Excludes transport, rebates, credit notes, Shell Rimula Israel."),
            ("Net mode","GPS% = (gross billing − warranty avg) ÷ max spend.  Warranty from distributor_warranty_expense_fiscal.csv (Σ avg €4.2M/yr)."),
            ("Gross mode","GPS% = gross billing ÷ max spend.  Warranty not deducted."),
            ("Toggle","Dashboard · C2 dropdown (Net / Gross).  Named range GPS_MODE."),
        ]),
        ("§ 2 — Max Spend Rates (UIO v19, class-weighted)",[
            ("N35 Grafter","€296/UIO/yr.  ITUK only (DVLA car park, N35 class)."),
            ("N75 / LD CV","€739/UIO/yr.  Network-wide LD CV rate (replaces legacy €1,120)."),
            ("F-series / MD","€887/UIO/yr.  F-series & MD/F trucks (replaces legacy €1,344)."),
            ("LCV / D-Max","€250/UIO/yr  (Jerome confirmed 30-Jun-2026)."),
            ("ITUK","N35/N75/F buckets from DVLA car park + UIO v19 projection.  Rates €296 / €739 / €887 via gps_v9_loaders (not generic CV LD)."),
            ("Ireland","SIMI hybrid wallet (€1.9M FY26, growing per UIO v19) — overrides flat rate."),
            ("MIDI","Flat €14/UIO — indirect channel, kept from v4a."),
        ]),
        ("§ 3 — Data Sources",[
            ("SAP billing","GPS-eligible ISZE → DB billing.  FY2024, FY2025, FY2026 actuals.  Values unchanged from v4a/v4b."),
            ("UIO","ISUZU_UIO_Overview_2026.xlsx  v19 (_CURRENT).  Class breakdown (CV LD/F/MD, LCV) per DB, years 2024–2030F."),
            ("Warranty",r"01_data\00_derived\distributor_warranty_expense_fiscal.csv  (fiscal Apr–Mar)."),
            ("Kosha BP","ISZE PL Plan row 186 (車両部品).  FY27 €35.28M reviewed per-DB (24 Apr 2026).  FY28–30 network totals unchanged until next review."),
            ("Reviewed BP FY27","11_planning/budget_per_DB_reviewed_24042026.xlsx · loader 91_build/load_bp_fy27.py · tab 'BP FY27 Reviewed'."),
        ]),
        ("§ 4 — Option A Math",[
            ("Logic","Uniform uplift X: Σ(eff_cap × (base% + X)) + warranty + CIS = Kosha BP."),
            ("Net X","X = (BP − CIS − Σwarr_avg − Σ(eff_cap × base%)) / Σeff_cap.  eff_cap = class_max − warr_avg."),
            ("Gross X","X = (BP − CIS − Σ(class_max × base%)) / Σclass_max."),
            ("Infeasibility","req% > 100% → capped at 100%.  DB flagged ⚠.  Total revenue falls short of BP when DBs are capped."),
        ]),
        ("§ 5 — Change Log",[
            ("v5.4  2026-07-03","ITUK max spend from N35 €296 / N75 €739 / F €887 buckets (gps_v9_loaders).  Fixes N35 priced at LD €739 (~€18M → ~€13M FY27 wallet)."),
            ("v5.3  2026-07-03","FY27 projection uses reviewed bottom-up BP per DB (budget_per_DB_reviewed_24042026.xlsx).  New tab 'BP FY27 Reviewed'.  FY28–30 remain Option A.  See 91_build/GPS_FILE_LINEAGE.md."),
            ("v5.2  2026-06-30","Class-weighted max spend from UIO v19 (LD €739 · F/MD €887 · LCV €250).  Option A re-solved.  Imotors GPS% corrected from ~81% to ~49% FY26."),
            ("v5.1  2026-06-30","Initial 6-tab merge of GPS_Kosha_v4a, v4b, merged_template, GPS_Calculator_v10."),
            ("v4a/v4b  2026-06-19","Net/gross split; BP from PL Plan row 186; UTI UIO v19.  Generator: build_gps_kosha_v4.py."),
        ]),
    ]
    r=3
    for sec_t,items in sections:
        ws.row_dimensions[r].height=8; r+=1
        ws.merge_cells(f"A{r}:C{r}")
        ws.cell(r,1,f"  {sec_t}").font=Fn(bold=True,color=WHITE,size=10)
        ws.cell(r,1).fill=F(MID); ws.cell(r,1).alignment=Al("left"); ws.row_dimensions[r].height=20; r+=1
        for label,content in items:
            ws.row_dimensions[r].height=max(16,len(content)//70*13+14)
            lc(ws,r,2,label,bold=True); ws.cell(r,2).border=Br()
            cell=ws.cell(r,3,content); cell.font=Fn(size=9); cell.alignment=Al("left",wrap=True); cell.border=Br()
            r+=1
    return ws

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("Reading source files...")
    net_act   = read_actuals(SRC_V4A)
    grs_act   = read_actuals(SRC_V4B)
    cis_rows  = read_proj_cis(SRC_V4A)
    net_gap   = read_gap(SRC_V4A)
    grs_gap   = read_gap(SRC_V4B)
    uio_data  = read_uio_classes()
    warr      = read_warranty()

    print("Loading ITUK DVLA / projection buckets (gps_v9)...")
    gps_pkg = build_gps_uio_package()
    ituk_uio = gps_pkg["distributors"]["ITUK"]["uio"]
    ituk_ms = gps_pkg["distributors"]["ITUK"]["max_spend"]

    print(f"  Actuals: {len(net_act)} DBs  |  CIS: {len(cis_rows)}  |  UIO DBs mapped: {len(uio_data)}")
    print(f"  ITUK FY26 max spend: €{ituk_ms.get(2026, 0):,.0f}  |  FY27: €{ituk_ms.get(2027, 0):,.0f}")

    # Build source max spend dict from v4a
    dbs_order = [r["db"] for r in net_act]
    src_max = {}
    for r in net_act:
        db=r["db"]
        src_max[db]={2024:r["fy24_max"],2025:r["fy25_max"],2026:r["fy26_max"]}
        # Add projection years from PROJ_CAP or UIO v19
        for yr in [2027,2028,2029,2030]:
            if db in PROJ_CAP:
                src_max[db][yr]=PROJ_CAP[db][yr]
            else:
                src_max[db][yr]=0  # will be filled by compute_max_spend

    # Compute new class-weighted max spend
    # For projection years of non-KEEP DBs, compute from UIO v19
    new_max = {}
    for db in dbs_order:
        new_max[db] = {}
        for yr in [2024,2025,2026,2027,2028,2029,2030]:
            if db == "ITUK":
                if yr == 2024:
                    new_max[db][yr] = src_max[db].get(2024) or ituk_ms.get(2025, 0)
                elif yr in ituk_ms:
                    new_max[db][yr] = ituk_ms[yr]
                else:
                    new_max[db][yr] = src_max[db].get(yr, 0)
            elif db in KEEP_MAX:
                new_max[db][yr] = src_max[db].get(yr, 0)
                if yr >= 2027 and db in PROJ_CAP:
                    new_max[db][yr] = PROJ_CAP[db][yr]
            else:
                classes = uio_data.get(db,{}).get(yr,{})
                total_uio = sum(classes.values())
                if total_uio > 0:
                    new_max[db][yr] = sum(n*CLASS_RATE[t] for t,n in classes.items())
                else:
                    new_max[db][yr] = src_max[db].get(yr, 0)

    # Compute warranty avg per DB (avg FY25+FY26)
    warr_avg = {db: (warr.get(db,{}).get(2025,0)+warr.get(db,{}).get(2026,0))/2
                for db in dbs_order}

    # Recompute GPS% base from new max spend
    g_act = {r["db"]:r for r in grs_act}
    net_base = {}; grs_base = {}
    for nr in net_act:
        db=nr["db"]; gr=g_act.get(db,nr)
        ms25=new_max[db][2025]; ms26=new_max[db][2026]
        n25=nr["fy25_bill"]/ms25 if ms25 else 0
        n26=nr["fy26_bill"]/ms26 if ms26 else 0
        g25=gr["fy25_bill"]/ms25 if ms25 else 0
        g26=gr["fy26_bill"]/ms26 if ms26 else 0
        net_base[db]=(n25+n26)/2; grs_base[db]=(g25+g26)/2

    # Run Option A for FY27-30
    proj_results_net = {}; proj_results_grs = {}
    x_net={}; x_grs={}; imp_net={}; imp_grs={}
    for yr in [2027,2028,2029,2030]:
        cap_yr = {db: new_max[db][yr] for db in dbs_order}
        bp_yr  = BP[yr]; cis_yr = CIS_P[yr]
        res, xn, xg = solve_option_a(dbs_order, net_base, grs_base, cap_yr, warr_avg, bp_yr, cis_yr)
        # Tag each result with base values for projection tab
        for db in dbs_order:
            res[db]["base_net"] = net_base[db]
            res[db]["base_grs"] = grs_base[db]
        proj_results_net[yr] = res
        x_net[yr]=xn; x_grs[yr]=xg
        imp_net[yr]=sum(1 for v in res.values() if v["infeas_net"])
        imp_grs[yr]=sum(1 for v in res.values() if v["infeas_grs"])

    print("\nLoading reviewed BP FY27...")
    bp_reviewed, reviewed_network = _load_reviewed_bp_fy27()
    BP[2027] = reviewed_network
    solver_fy27 = {db: dict(proj_results_net[2027][db]) for db in dbs_order}
    cap_yr_27 = {db: new_max[db][2027] for db in dbs_order}
    imp_n27, imp_g27 = apply_reviewed_bp_fy27(
        proj_results_net[2027], dbs_order, cap_yr_27, warr_avg, bp_reviewed, net_base, grs_base,
    )
    imp_net[2027] = imp_n27
    imp_grs[2027] = imp_g27
    x_net[2027] = None
    x_grs[2027] = None
    print(f"  Reviewed network FY27: €{reviewed_network/1e6:.2f}M  |  mapped DBs: {len(bp_reviewed)}")

    # Print summary
    x27n = f"{x_net[2027]*100:+.2f}pp" if x_net[2027] is not None else "per-DB BP"
    print(f"\n  Uplift X (net)  : FY27={x27n}  FY28={x_net[2028]*100:+.2f}pp  FY29={x_net[2029]*100:+.2f}pp  FY30={x_net[2030]*100:+.2f}pp")
    print(f"  Uplift X (grs)  : FY27={x27n}  FY28={x_grs[2028]*100:+.2f}pp  FY29={x_grs[2029]*100:+.2f}pp  FY30={x_grs[2030]*100:+.2f}pp")
    print(f"  Infeasible (net): FY29={imp_net[2029]} DB  FY30={imp_net[2030]} DB")

    # Key changes
    print("\n  Key max spend changes vs v4a:")
    for nr in net_act:
        db=nr["db"]
        old=nr["fy26_max"]; new=new_max[db][2026]
        if abs(new-old)/old > 0.01 if old else new>0:
            old_pct=nr["fy26_bill"]/old if old else 0
            new_pct=nr["fy26_bill"]/new if new else 0
            print(f"    {db:14s}  max {old/1e6:.2f}M→{new/1e6:.2f}M  GPS%26 net: {old_pct:.1%}→{new_pct:.1%}")

    print("\nBuilding workbook...")
    wb = Workbook(); wb.remove(wb.active)

    ws_dash  = build_dashboard(wb)
    ws_act, R_ACT = build_actuals(wb, net_act, grs_act, new_max, uio_data)
    ws_proj, R_PROJ, R_GRAND, R_X, R_IMP = build_projection(wb, dbs_order, proj_results_net, cis_rows)
    build_bp_reviewed_tab(wb, dbs_order, bp_reviewed, solver_fy27, reviewed_network)
    ws_gap   = build_kosha_gap(wb, net_gap, grs_gap, x_net, x_grs, imp_net, imp_grs, proj_results_net, proj_results_grs:={},
                               bp_fy27_reviewed_eur=reviewed_network, fy27_per_db_bp=True)
    ws_rates = build_db_rates(wb, uio_data, ituk_uio)
    ws_meth  = build_method(wb)

    print(f"  Tab refs: Actuals total {R_ACT}  |  Proj grand total {R_GRAND}")

    # Patch Dashboard
    act  = "'GPS Actuals FY24-26'"; proj = "'GPS Projection FY27-30'"; gap = "'Kosha Gap'"
    refs6=[(3,f"={act}!D{R_ACT}","0.0%"),(4,f"={act}!F{R_ACT}","0.0%"),(5,f"={act}!H{R_ACT}","0.0%"),
           (6,f"={proj}!E{R_GRAND}","€#,##0"),(7,f"={proj}!G{R_GRAND}","€#,##0"),
           (8,f"={proj}!I{R_GRAND}","€#,##0"),(9,f"={proj}!K{R_GRAND}","€#,##0")]
    ws_dash.cell(6,2).value="Network GPS% / Revenue → BP"
    for c,ref,fmt in refs6:
        cell=ws_dash.cell(6,c,ref); cell.number_format=fmt
        cell.font=Fn(bold=True,size=9); cell.alignment=Al("center"); cell.border=Br()
    for c,ref in [(3,f"={act}!E{R_ACT}"),(4,f"={act}!G{R_ACT}"),(5,f"={act}!I{R_ACT}"),
                  (6,f"={proj}!E{R_GRAND}"),(7,f"={proj}!G{R_GRAND}"),
                  (8,f"={proj}!I{R_GRAND}"),(9,f"={proj}!K{R_GRAND}")]:
        cell=ws_dash.cell(7,c,ref); cell.number_format="€#,##0"
        cell.font=Fn(size=9); cell.alignment=Al("center"); cell.border=Br()
    for c,ref in [(3,""),(4,""),(5,f"={gap}!B8"),(6,f"={gap}!C8"),(7,f"={gap}!D8"),(8,f"={gap}!E8"),(9,f"={gap}!F8")]:
        cell=ws_dash.cell(8,c,ref or "—"); cell.number_format="€#,##0"
        cell.font=Fn(size=9); cell.alignment=Al("center"); cell.border=Br()
    for c,ref in [(3,""),(4,""),(5,f"={gap}!B11"),(6,f"={gap}!C11"),(7,f"={gap}!D11"),(8,f"={gap}!E11"),(9,f"={gap}!F11")]:
        cell=ws_dash.cell(9,c,ref or "—"); cell.number_format="€#,##0;[Red](€#,##0)"
        cell.font=Fn(bold=True,size=9); cell.alignment=Al("center"); cell.border=Br()
    for c,ref in [(3,"—"),(4,"—"),(5,"—"),(6,f"={proj}!D{R_X}"),(7,f"={proj}!F{R_X}"),
                  (8,f"={proj}!H{R_X}"),(9,f"={proj}!J{R_X}")]:
        cell=ws_dash.cell(10,c,ref); cell.number_format='0.00"pp"'
        cell.font=Fn(italic=True,size=9,color=DGR); cell.alignment=Al("center"); cell.border=Br()
    for c,ref in [(3,"—"),(4,"—"),(5,"—"),(6,f"={proj}!D{R_IMP}"),(7,f"={proj}!F{R_IMP}"),
                  (8,f"={proj}!H{R_IMP}"),(9,f"={proj}!J{R_IMP}")]:
        cell=ws_dash.cell(11,c,ref)
        cell.font=Fn(italic=True,size=9,color=RFG); cell.alignment=Al("center"); cell.border=Br()

    n_dbs=len(net_act)
    for i,nr in enumerate(net_act):
        r=15+i; ws_dash.row_dimensions[r].height=16
        act_row=4+i; bg=LGR if i%2 else None
        lc(ws_dash,r,2,nr["db"],bg=bg)
        for col_d,col_l in [(3,"D"),(4,"F"),(5,"H")]:
            cell=ws_dash.cell(r,col_d,f"={act}!{col_l}{act_row}")
            cell.number_format="0.0%"; cell.font=Fn(size=9); cell.alignment=Al("center"); cell.border=Br()
            if bg: cell.fill=F(bg)
        if nr["db"] == "ITUK" and ituk_uio.get(2026):
            uio26 = int(round(ituk_bucket_total(ituk_uio[2026])))
        else:
            uio26 = sum(uio_data.get(nr["db"],{}).get(2026,{}).values()) or nr["uio_fy26"]
        ms26=new_max[nr["db"]][2026]; rate26=round(ms26/uio26) if uio26 else 0
        dc(ws_dash,r,6,uio26,"#,##0",bg=bg); dc(ws_dash,r,7,rate26,"€#,##0",bg=bg)

    for col in ["C","D","E"]: traffic(ws_dash,col,15,15+n_dbs-1)
    LR=15+n_dbs+1; ws_dash.row_dimensions[LR].height=14
    ws_dash.cell(LR,2,"Legend:").font=Fn(bold=True,size=8)
    for c,bg,fg,txt in [(3,GBG,GFG,"< 85%"),(4,ABG,AFG,"85–100%"),(5,RBG,RFG,"≥ 100%")]:
        cell=ws_dash.cell(LR,c,txt); cell.fill=F(bg); cell.font=Fn(size=8,color=fg,bold=True)
        cell.alignment=Al("center"); cell.border=Br()

    wb.defined_names["GPS_MODE"]=DefinedName("GPS_MODE",attr_text="Dashboard!$C$2")

    # Archive originals
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    for src in [SRC_V4A,SRC_V4B,SRC_TMPL]:
        dst=ARCHIVE/src.name
        if src.exists() and not dst.exists():
            shutil.copy2(src,dst); print(f"  Archived: {src.name}")

    wb.save(OUT)
    print(f"\n✓ Saved: {OUT}")

if __name__=="__main__":
    main()
