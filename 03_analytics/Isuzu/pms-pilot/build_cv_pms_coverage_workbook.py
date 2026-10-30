"""Build the CV PMS coverage workbook: every customer with a truck fleet, by country, FY and calendar year.

Expected PMS demand is a live Excel formula on UIO:
    expected pieces = trucks in service (UIO) x km a year / replacement interval km x months / 12
    (N-series split N35 / N75 by the N35 share; inputs on 'Km assumptions', set to reproduce the model's factors)
Billed pieces / euros are pasted values. Coverage, gap, ranking and the customer one-pager are formulas.

Billed source per period
    CY2024, CY2025  published PMS coverage model (pms_capture_by_family.csv, pms_capture_by_db_year.csv)
    FY periods      rebuilt here from sales_fact.parquet with the model's own part list
                    (pms_family_part_number_map.csv), its own part tagging (modules.pms_tagging), and the
                    model's family table (vehicle_family_bands.csv). The 'Check vs model' sheet compares the
                    rebuild with the published calendar years.

Rebuild notes (things the git copy is missing that the model on Jerome's PC has):
    * prism/data/pms_capture_supplement.csv is not in git: categories for its part numbers come from the
      part description instead (see CAT_RULES).
    * SAP sold-to 92 (I Motors Portugal) is not in the git sold-to mapping: mapped to PORTUGAL here.
    * The model counts every 'ROTOR; ...' and 'DRUM; BRK' part as a brake disc, ABS sensor rings included.
      Mirrored here so the totals tie; flagged in the Read me.

Run:  python build_cv_pms_coverage_workbook.py [output.xlsx]
Then recalculate (LibreOffice / Excel) before reading values.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[3]
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
PDATA = PRISM / "data"
sys.path.insert(0, str(PRISM))
OUT = Path(__file__).resolve().parent / (sys.argv[1] if len(sys.argv) > 1 else "ISZE_CV_PMS_Coverage_by_Customer_2026-10-30_v4.xlsx")

MIN_CV_UIO = 10  # Denmark has 1 truck in service: left out
UIO_YEARS = [2024, 2025, 2026]
FAMILIES = {"n_series_truck": "N-series truck", "heavy_truck": "Heavy truck (F-series)"}
CATS = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "blower_filter": "Cabin (blower) filter", "urea_filter": "AdBlue filter",
    "brake_pad": "Brake pad", "brake_shoe": "Brake shoe", "brake_rotor": "Brake disc (rotor)",
    "clutch_kit": "Clutch kit", "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate", "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing", "clutch_booster": "Clutch booster",
}
NAMES = {
    "ITUK": "Isuzu Truck UK", "UTI": "UTI (Universal Trucks Israel)", "PORTUGAL": "I Motors Portugal",
    "IRELAND": "Isuzu Ireland", "GERMANY": "Isuzu Sales Deutschland", "BELGIUM": "Isuzu Benelux",
    "MALTA": "Gasan Zammit Motors", "CYPRUS": "Loutsios & Sons", "GREECE": "Petros Petropoulos",
}
# description -> category, for model part numbers the git copy cannot tag (first match wins)
CAT_RULES = [
    ("urea_filter", r"DEF|UREA"), ("blower_filter", r"BLOWER"),
    ("oil_filter", r"OIL FILTER|FILTER; OIL|ELEMENT; OIL"), ("fuel_filter", r"FUEL"),
    ("air_filter", r"ACL|AIR CLEANER|FILTER; AIR"), ("brake_rotor", r"ROTOR|DISC; BRK|DRUM"),
    ("brake_pad", r"PAD"), ("brake_shoe", r"SHOE|LINING"), ("clutch_pressure_plate", r"PRESSURE"),
    ("clutch_disc", r"DISC; ?CLUTCH"), ("release_bearing", r"RELEASE"), ("pilot_bearing", r"PILOT"),
    ("clutch_booster", r"BOOSTER"), ("clutch_kit", r"CLUTCH"),
]
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# ---------- styles ----------
F = "Arial"
H_FILL = PatternFill("solid", fgColor="1F3864")
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")
IN_FILL = PatternFill("solid", fgColor="FFF2CC")
SEL_FILL = PatternFill("solid", fgColor="FFFF00")
GREY = PatternFill("solid", fgColor="EDEDED")
BLUE = Font(name=F, size=10, color="0000FF")
GREEN = Font(name=F, size=10, color="008000")
BLACK = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
BIG = Font(name=F, size=12, bold=True)
NOTE = Font(name=F, size=9, italic=True)
HFONT = Font(name=F, size=10, bold=True, color="FFFFFF")
TITLE = Font(name=F, size=14, bold=True, color="1F3864")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
EUR = '€#,##0;(€#,##0);"-"'
EUR2 = '€#,##0.00;(€#,##0.00);"-"'
PCS = '#,##0;(#,##0);"-"'
PCS1 = '#,##0.0;(#,##0.0);"-"'
PCT = '0.0%;(0.0%);"-"'
RATE = "0.00"
RED_GREEN = dict(start_type="num", start_value=0, start_color="F8696B", mid_type="num", mid_value=0.5,
                 mid_color="FFEB84", end_type="num", end_value=1, end_color="63BE7B")
DEVELOP = dict(fill=PatternFill("solid", fgColor="F8CBAD"), font=Font(name=F, bold=True))


def header(ws, row, cols, widths=None, freeze=True, filt=True, start_col=1):
    for i, c in enumerate(cols):
        cell = ws.cell(row=row, column=start_col + i, value=c)
        cell.font, cell.fill, cell.border = HFONT, H_FILL, BOX
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[row].height = 45
    if widths:
        for i, w in enumerate(widths):
            ws.column_dimensions[get_column_letter(start_col + i)].width = w
    if freeze:
        ws.freeze_panes = ws.cell(row=row + 1, column=1)
    if filt:
        ws.auto_filter.ref = f"A{row}:{get_column_letter(len(cols))}{row}"


def put(ws, r, c, v, font=BLACK, fmt=None, fill=None, box=True):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font
    if box:
        cell.border = BOX
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
    return cell


def text(ws, r, c, v, font=BLACK):
    return put(ws, r, c, v, font, box=False)


def selector(ws, r, c, label, default, options_formula):
    text(ws, r, c, label, BOLD)
    cell = put(ws, r, c + 1, default, BLUE, None, SEL_FILL)
    dv = DataValidation(type="list", formula1=options_formula, allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(cell.coordinate)
    return f"${get_column_letter(c + 1)}${r}"


def action(exp_eur, cov, gen, bvp, bvp_share, nobvp_share):
    # billed under 3% of expected € reads as a demand-assumption problem before it reads as a market gap
    return (f'=IF({exp_eur}<1000,"Small",IF(N({cov})>=0.8,"Covered",IF({gen}+{bvp}=0,"Nothing billed — check range",'
            f'IF({gen}+{bvp}<0.03*{exp_eur},"Hardly billed — check demand assumption",'
            f'IF(N({nobvp_share})>=0.5,"Develop BVP",IF(N({bvp_share})<0.2,"Push existing BVP / price",'
            f'"BVP selling — check price & availability"))))))')


# ---------- data: UIO ----------
uio = pd.read_csv(DER / "uio_by_market_type_year.csv")
uio = uio[uio.year.isin(UIO_YEARS)]
uio_basis = uio.groupby(["distributor_code", "year"]).basis.first()
piv = uio.pivot_table(index=["distributor_code", "year"], columns="model_type", values="uio_units", aggfunc="sum", fill_value=0)
for c in ["LD", "MD", "F-Series", "LCV"]:
    if c not in piv:
        piv[c] = 0
piv["cv"] = piv.LD + piv.MD + piv["F-Series"]
cv_codes = sorted(piv[piv.cv >= MIN_CV_UIO].reset_index().query("year == 2025").distributor_code.unique())

dbm = pd.read_csv(PDATA / "distributor_master_mapping.csv").drop_duplicates("distributor_code").set_index("distributor_code")
country = {c: dbm.country.get(c, c.title()) for c in cv_codes}
cust_order = sorted(cv_codes, key=lambda c: (country[c], c))

pubfam = pd.read_csv(DER / "pms_capture_by_family.csv")
pubtot = pd.read_csv(DER / "pms_capture_by_db_year.csv")
_n35p = ROOT / "01_data" / "15_gpt_safe" / "gpt_pack_2026-09-20" / "07_uio_ld_n35_share.csv"  # measured N35 share, for the notes only
n35_file = pd.read_csv(_n35p) if _n35p.is_file() else None
visits = pubfam[pubfam.family.isin(FAMILIES) & (pubfam.year == 2025)].groupby(["distributor_code", "family"]).visits_per_year.first()
rates = pubfam[pubfam.family.isin(FAMILIES)].groupby(["distributor_code", "pms_category", "family"]).category_factor.first()

# ---------- data: billing rebuild ----------
from config import resolve_mapping_path  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.pms_tagging import tag_pms_sales  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

sales, _ = load_prism_sales(load_distributor_mapping(str(resolve_mapping_path())))
sales["pn"] = sales.part_number.map(norm)
sap = sales.sold_to_sap.astype(str).str.replace(r"\.0$", "", regex=True)
sales.loc[sap == "92", "distributor_code"] = "PORTUGAL"  # I Motors Portugal; not in the git sold-to mapping
dim = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype={"part_number": str})
tagged = tag_pms_sales(sales.copy(), dim, fill_catalog_pms=True)
tagged["pn"] = tagged.part_number.map(norm)
tagcat = tagged[tagged.is_pms.fillna(False)].groupby("pn").pms_category.agg(lambda s: s.mode().iloc[0])
pnmap = pd.read_csv(DER / "pms_family_part_number_map.csv", dtype=str)
pnmap["pn"] = pnmap.pn.map(norm)
desc = sales.groupby("pn").description.first()


def _cat(p):
    if p in tagcat.index:
        return tagcat[p]
    d = str(desc.get(p, "")).upper()
    for c, rx in CAT_RULES:
        if re.search(rx, d):
            return c
    return None


PNCAT = {p: _cat(p) for p in pnmap.pn}
# brake discs, drums and ABS sensor rings (the model counts the rings); not crank / cam / speed sensor rotors
for p in sales[sales.description.astype(str).str.upper().str.contains(r"^ROTOR; ?(?:DISC|SENSOR\s*$)|^DRUM; ?BRK", regex=True)].pn.unique():
    PNCAT.setdefault(p, "brake_rotor")
PNCAT = {k: v for k, v in PNCAT.items() if v}
CATSRC = {p: "PMS model tagging" if p in tagcat.index else "Part description" for p in PNCAT}
NOT_WEAR = r"SPRING|^PIN;|SCREW|BOLT|^NUT;|GASKET|BRACKET|HOSE|CLIP KIT|BLOCK; SHIFT|CRANK|CAM ANGLE|SPEED SENSOR|ROTOR; GEN|VAC PUMP"


def part_check(d):
    d = str(d).upper()
    if re.match(r"ROTOR; ?SENSOR\s*$", d):
        return "ABS sensor ring — counted as brake disc by the model"
    if re.search(NOT_WEAR, d):
        return "Not a wear part — check"
    return ""

bands = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str)
bands["pn"] = bands.pn.map(norm)
pn_fam = dict(zip(bands.pn, bands.family.where(bands.resolution == "single_family")))
pn_res = dict(zip(bands.pn, bands.resolution.replace({"no_vehicle_reference": "unattributed"})))

cx = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str)
bvp_set = {norm(p) for p in set(dim[dim.line_type == "bvp"].part_number) | set(cx.bvp_pn)}
paired_genuine = {norm(p) for p in cx.genuine_pn}

s = sales[sales.pn.isin(PNCAT) & ~sales.is_credit_note.fillna(False).astype(bool)].copy()
s["cat"] = s.pn.map(PNCAT)
s["family"] = s.pn.map(pn_fam).fillna(s.pn.map(pn_res)).fillna("shared_across_families")
s["is_bvp"] = s.pn.isin(bvp_set)
s["no_bvp"] = ~s.is_bvp & ~s.pn.isin(paired_genuine) & ~s.part_number.astype(str).str[:4].isin(["5876", "1876"])
s["bd"] = pd.to_datetime(s.billing_date)
last = s.bd.max()
ytd_end = last.normalize() if last.is_month_end else (last.replace(day=1) - pd.Timedelta(days=1)).normalize()
ytd_months = (ytd_end.year - 2026) * 12 + ytd_end.month - 3

PERIODS = [  # key, type, start, end (exclusive), months, uio_year, billed source, published year
    ("FY2027 YTD", "FY", "2026-04-01", (ytd_end + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), ytd_months, 2025, "Rebuilt from billing", None),
    ("FY2026", "FY", "2025-04-01", "2026-04-01", 12, 2025, "Rebuilt from billing", None),
    ("FY2025", "FY", "2024-04-01", "2025-04-01", 12, 2024, "Rebuilt from billing", None),
    ("CY2025", "Calendar", "2025-01-01", "2026-01-01", 12, 2025, "PMS coverage model (published)", 2025),
    ("CY2024", "Calendar", "2024-01-01", "2025-01-01", 12, 2024, "PMS coverage model (published)", 2024),
]
PKEYS = [p[0] for p in PERIODS]

agg = {}      # (dist, period, cat, family) -> (pcs, eur)
mix = {}      # (dist, period, cat) -> genuine / BVP / no-BVP euros
nobvp_rows = []
for key, _t, st, en, _m, _uy, _src, pub_year in PERIODS:
    x = s[(s.bd >= st) & (s.bd < en) & s.distributor_code.isin(cv_codes)]
    g = x.groupby(["distributor_code", "cat", "family"]).agg(pcs=("billed_qty", "sum"), eur=("net_sales_value", "sum"))
    for (d, c, f), r in g.iterrows():
        agg[(d, key, c, f)] = (float(r.pcs), float(r.eur))
    m = x.assign(ge=x.net_sales_value.where(~x.is_bvp, 0), be=x.net_sales_value.where(x.is_bvp, 0),
                 ne=x.net_sales_value.where(x.no_bvp, 0)).groupby(["distributor_code", "cat"])[["ge", "be", "ne"]].sum()
    for (d, c), r in m.iterrows():
        mix[(d, key, c)] = dict(gen_eur=r["ge"], bvp_eur=r["be"], nobvp_eur=r["ne"])
    if pub_year is not None:  # calendar periods: the published model wins
        for k in [k for k in agg if k[1] == key]:
            agg.pop(k)
        for (d, f, c), r in pubfam[(pubfam.year == pub_year) & pubfam.distributor_code.isin(cv_codes)].set_index(
                ["distributor_code", "family", "pms_category"]).iterrows():
            agg[(d, key, c, f)] = (float(r.billed_units), float(r.billed_eur))
        t = pubtot[(pubtot.year == pub_year) & pubtot.distributor_code.isin(cv_codes)]
        for (d, c), grp in t.groupby(["distributor_code", "pms_category"]):
            ne = mix.get((d, key, c), {}).get("nobvp_eur", 0.0)
            mix[(d, key, c)] = dict(gen_eur=grp[grp.line_type == "genuine"].actual_rev_eur.sum(),
                                    bvp_eur=grp[grp.line_type == "bvp"].actual_rev_eur.sum(), nobvp_eur=ne)
    nb = x[x.no_bvp].groupby(["distributor_code", "cat", "pn"]).agg(desc=("description", "first"), pcs=("billed_qty", "sum"),
                                                                    eur=("net_sales_value", "sum"), fam=("family", "first")).reset_index()
    nb["period"] = key
    nobvp_rows.append(nb)
nobvp = pd.concat(nobvp_rows, ignore_index=True)
nobvp = nobvp[nobvp.eur > 0].sort_values(["distributor_code", "period", "eur"], ascending=[True, True, False])
nobvp["rank"] = nobvp.groupby(["distributor_code", "period"]).cumcount() + 1

# fallback average price per customer x part (all periods), then network
allp = s[s.distributor_code.isin(cv_codes)].groupby(["distributor_code", "cat"]).agg(e=("net_sales_value", "sum"), q=("billed_qty", "sum"))
asp_cust = (allp.e / allp.q.where(allp.q > 0)).dropna().to_dict()
nw = s.groupby("cat").agg(e=("net_sales_value", "sum"), q=("billed_qty", "sum"))
asp_net = (nw.e / nw.q.where(nw.q > 0)).dropna().to_dict()

# check vs model (calendar years, rebuilt vs published, customer x part)
chk = []
for y in (2024, 2025):
    xr = s[(s.bd.dt.year == y) & s.distributor_code.isin(cv_codes)].groupby(["distributor_code", "cat"]).net_sales_value.sum()
    xp = pubtot[(pubtot.year == y) & (pubtot.line_type == "total") & pubtot.distributor_code.isin(cv_codes)].set_index(
        ["distributor_code", "pms_category"]).actual_rev_eur
    both = pd.concat([xr.rename("rebuilt"), xp.rename("published")], axis=1).fillna(0)
    both.index.names = ["dist", "cat"]
    chk.append(both.reset_index().assign(year=y))
chk = pd.concat(chk, ignore_index=True)

# ======================= workbook =======================
wb = Workbook()
rd = wb.active
rd.title = "Read me"

# ----- Periods -----
wp = wb.create_sheet("Periods")
text(wp, 1, 1, "Periods — inputs", TITLE)
text(wp, 2, 1, "Months scales expected demand (YTD = part of a year). UIO year = which fleet count is used. Blue = input.")
header(wp, 4, ["Period", "Type", "From", "To", "Months", "UIO year used", "Billed figures from", "Note"],
       [13, 10, 12, 12, 8, 10, 30, 90], filt=False)
pnotes = {"FY2027 YTD": f"Billing up to {ytd_end:%d %b %Y}. UIO 2025 (last actual); 2026 is a forecast — type 2026 in 'UIO year used' to switch.",
          "FY2026": "1 Apr 2025 – 31 Mar 2026. UIO 2025 (fleet at the start of the period).",
          "FY2025": "1 Apr 2024 – 31 Mar 2025. UIO 2024.",
          "CY2025": "Same billed figures as the ISZE PMS coverage model.",
          "CY2024": "Same billed figures as the PMS coverage model; that model uses the 2025 fleet for 2024, this file the 2024 fleet."}
for i, (key, typ, st, en, mo, uy, src, _py) in enumerate(PERIODS):
    r = 5 + i
    put(wp, r, 1, key, BOLD)
    put(wp, r, 2, typ)
    put(wp, r, 3, st)
    put(wp, r, 4, (pd.Timestamp(en) - pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    put(wp, r, 5, mo, BLUE, None, IN_FILL)
    put(wp, r, 6, uy, BLUE, None, IN_FILL)
    put(wp, r, 7, src)
    put(wp, r, 8, pnotes[key])
P_LAST = 4 + len(PERIODS)
PERIOD_LIST = '"' + ",".join(PKEYS) + '"'
MONTHS = f"INDEX(Periods!$E$5:$E${P_LAST},MATCH({{p}},Periods!$A$5:$A${P_LAST},0))"
UIOY = f"INDEX(Periods!$F$5:$F${P_LAST},MATCH({{p}},Periods!$A$5:$A${P_LAST},0))"

# ----- UIO -----
wu = wb.create_sheet("UIO")
text(wu, 1, 1, "Trucks in service (UIO) by customer and year — inputs", TITLE)
text(wu, 2, 1, "Blue = input. Source: Isuzu UIO Overview 2026 (by market and model type). 2026 is a forecast. Km driven and the N35 share are on 'Km assumptions'.")
header(wu, 4, ["Key", "Customer code", "Customer", "Country", "UIO year", "Basis", "N-series light duty (LD)", "N-series medium duty (MD)",
               "N-series trucks total", "Heavy truck F-series", "Trucks total (CV)", "Pickup / LCV (info)", "Truck share of fleet"],
       [16, 12, 30, 15, 8, 9, 13, 13, 13, 13, 13, 13, 11])
r = 5
for c in cust_order:
    for y in UIO_YEARS:
        p = piv.loc[(c, y)] if (c, y) in piv.index else None
        put(wu, r, 1, f'=B{r}&"|"&E{r}')
        put(wu, r, 2, c)
        put(wu, r, 3, NAMES.get(c, c))
        put(wu, r, 4, country[c])
        put(wu, r, 5, y)
        put(wu, r, 6, uio_basis.get((c, y), ""))
        for col, k in [(7, "LD"), (8, "MD"), (10, "F-Series"), (12, "LCV")]:
            put(wu, r, col, float(p[k]) if p is not None else 0, BLUE, PCS1, IN_FILL)
        put(wu, r, 9, f"=G{r}+H{r}", fmt=PCS1)
        put(wu, r, 11, f"=I{r}+J{r}", fmt=PCS1)
        put(wu, r, 13, f"=IFERROR(K{r}/(K{r}+L{r}),0)", fmt=PCT)
        r += 1
U_LAST = r - 1
text(wu, r + 1, 1, "Denmark (1 truck in service) and pickup-only customers are not in this file.", NOTE)


def uio_look(col, code_ref, period_ref):
    return f'SUMIFS(UIO!${col}$5:${col}${U_LAST},UIO!$A$5:$A${U_LAST},{code_ref}&"|"&{UIOY.format(p=period_ref)})'


# ----- Km assumptions -----
# Every assumption per truck model (N35 / N75 / F-series), with its source, side by side:
#   PMS model      what the published PMS coverage model uses (20,000 km flat; UTI 50,000)
#   Market-stated  a figure the market / IML gave us (ITUK N75 50,000, ITUK N35 11,576 mi, UTI 50,000)
#   Measured       warranty-claim odometers per market and model (only where the market has 30+ claim VINs)
# 'Per model' (default) takes market-stated, else measured, else the 20,000 km default.
# Replacements a truck a year = N35 share x km N35 / interval N35 + (1 - N35 share) x km N75 / interval N75 (N-series);
#                               km F / interval F (F-series). Part interval = service interval / model factor.
SVC_KM = {"N35": 20_000, "N75": 40_000, "F": 30_000}
MIN_VINS = 30
WARRANTY_MARKET = {"ITUK": "UK", "UTI": "ISRAEL", "PORTUGAL": "PORTUGAL", "IRELAND": "IRELAND", "GERMANY": "GERMANY",
                   "CYPRUS": "CYPRUS", "MALTA": "MALTA", "GREECE": "GREECE", "BELGIUM": None}
STATED = {  # (customer, model) -> (km, source)
    ("ITUK", "N75"): (50_000, "ITUK via IML market-research slide 2026-07-14; used in the IML deck for all ITUK trucks"),
    ("ITUK", "N35"): (18_630, "ITUK trip report Apr 2026: N35 11,576 miles a year (MOT-date recalc)"),
    ("UTI", "N75"): (50_000, "Confirmed by Jerome 2026-07-10 (IML CV study); odometers agree (51,680)"),
}
warr = pd.read_csv(DER / "warranty_cv_km_age_by_market.csv").set_index("market")
wr = wb.create_sheet("Km assumptions")
KM = "'Km assumptions'!"
text(wr, 1, 1, "Kilometre assumptions per truck model — inputs and sources", TITLE)
MB = selector(wr, 3, 1, "Mileage basis", "Per model", '"Per model,PMS model,Market-stated,Measured"')
IB = selector(wr, 4, 1, "Interval basis", "Per model", '"Per model,PMS model"')
text(wr, 3, 4, "Per model = market-stated km where a market gave one, else measured odometers (30+ claim VINs), else 20,000 km. "
               "PMS model = exactly the published PMS coverage model (20,000 km flat; UTI 50,000).", NOTE)
text(wr, 4, 4, "Per model = also the market-specific service intervals (Israel N75 oil and fuel filter every 22,500 km, Isuzu GIDSS). "
               "PMS model = the model's intervals only.", NOTE)
MBK = f"{KM}{MB}"
IBK = f"{KM}{IB}"
header(wr, 6, ["Factory service interval", "Km", "Source"], [34, 14, 60], freeze=False, filt=False)
svc_rows = {}
for i, (lab, k, src) in enumerate([("N35 (NLR, 3.5 t) — RZ4E", "N35", "Isuzu service schedule (GIDSS N_MY24 p6-8) / Duncan deck slide 14"),
                                   ("N75 (NPR, 7.5 t) — 4HK1", "N75", "Isuzu service schedule (GIDSS N_MY24) / Duncan deck slide 14"),
                                   ("F-series", "F", "Isuzu Truck UK service book — provisional")]):
    rr_ = 7 + i
    put(wr, rr_, 1, lab)
    put(wr, rr_, 2, SVC_KM[k], BLUE, PCS, IN_FILL)
    put(wr, rr_, 3, src)
    svc_rows[k] = rr_

CB0 = 13
ccols = ["Customer code", "Customer", "Country", "N35 share — PMS model", "N35 share — UIO file", "N35 share used"]
for m_ in ("N35", "N75", "F-series"):
    ccols += [f"{m_} km — PMS model", f"{m_} km — market-stated", f"{m_} km — measured", f"{m_} km USED", f"{m_} source used"]
ccols += ["Warranty claim VINs (sample)", "Sources and notes"]
header(wr, CB0 - 1, ccols, freeze=False, filt=False)
share_file = {r_.distributor_code: (float(r_.n35_share), r_.basis) for r_ in n35_file.itertuples()} if n35_file is not None else {}
cust_note = {}
for i, c in enumerate(cust_order):
    rr_ = CB0 + i
    v = float(visits.get((c, "n_series_truck"), 0.5))
    share_model = 0.0 if c == "UTI" else max(0.0, round(v / 0.5 - 1, 4))
    sf = share_file.get(c, (share_model, "PMS model"))
    wm = WARRANTY_MARKET.get(c)
    wrow = warr.loc[wm] if wm in warr.index else None
    vins = int(wrow.vins_cv_claims) if wrow is not None else 0
    put(wr, rr_, 1, c)
    put(wr, rr_, 2, NAMES.get(c, c))
    put(wr, rr_, 3, country[c])
    put(wr, rr_, 4, share_model, BLUE, PCT, IN_FILL)
    put(wr, rr_, 5, sf[0], BLUE, PCT, IN_FILL)
    put(wr, rr_, 6, f'=IF({MB}="PMS model",D{rr_},E{rr_})', fmt=PCT)
    notes = [f"N35 share in UIO file: {sf[0]:.1%} ({sf[1]})."]
    col = 7
    for m_, wcol in (("N35", "km_yr_N35"), ("N75", "km_yr_N75"), ("F", "km_yr_F")):
        pms = 50_000 if (c == "UTI" and m_ != "F") else 20_000
        st = STATED.get((c, m_))
        meas = float(wrow[wcol]) if wrow is not None and pd.notna(wrow[wcol]) else None
        meas_ok = meas is not None and vins >= MIN_VINS
        a, b, cc, u = (get_column_letter(col + k) for k in range(4))
        put(wr, rr_, col, pms, BLUE, PCS, IN_FILL)
        put(wr, rr_, col + 1, st[0] if st else None, BLUE, PCS, IN_FILL)
        put(wr, rr_, col + 2, round(meas) if meas_ok else None, BLUE, PCS, IN_FILL)
        put(wr, rr_, col + 3, f'=IF({MB}="PMS model",{a}{rr_},IF({MB}="Market-stated",IF(N({b}{rr_})>0,{b}{rr_},{a}{rr_}),'
                              f'IF({MB}="Measured",IF(N({cc}{rr_})>0,{cc}{rr_},{a}{rr_}),'
                              f'IF(N({b}{rr_})>0,{b}{rr_},IF(N({cc}{rr_})>0,{cc}{rr_},{a}{rr_})))))', BOLD, PCS)
        put(wr, rr_, col + 4, f'=IF({MB}="PMS model","PMS model",IF(AND(N({b}{rr_})>0,{u}{rr_}={b}{rr_}),"Market-stated",'
                              f'IF(AND(N({cc}{rr_})>0,{u}{rr_}={cc}{rr_}),"Measured odometers","No data — PMS model value")))')
        if st:
            notes.append(f"{m_} stated: {st[1]}.")
        if meas is not None and not meas_ok:
            notes.append(f"{m_} measured {meas:,.0f} km but only {vins} claim VINs — not used.")
        col += 5
    if c == "ITUK":
        notes.append("Warranty odometers UK: N35 12,891, N75 35,478, F 27,242 km (vehicles with claims, under 28 months old). "
                     "Mileage question to Duncan Young drafted, not sent.")
    if c == "UTI":
        notes.append("Israel has no N35 trucks.")
    if wm is None:
        notes.append("No warranty mileage for this market.")
    put(wr, rr_, col, vins, fmt=PCS)
    put(wr, rr_, col + 1, " ".join(notes))
    cust_note[c] = " ".join(notes)
CB1 = CB0 + len(cust_order) - 1
for i, w in enumerate([12, 26, 14, 9, 9, 9] + [10, 10, 10, 11, 16] * 3 + [10, 120], 1):
    wr.column_dimensions[get_column_letter(i)].width = w
wr.column_dimensions["A"].width = 30
wr.column_dimensions["B"].width = 28
KMCOL = {"N35": "J", "N75": "O", "F": "T"}
SRCCOL = {"N35": "K", "N75": "P", "F": "U"}

PB0 = CB1 + 4
header(wr, PB0 - 1, ["Part code", "Part", "Replacement interval km — N35", "Replacement interval km — N75", "Replacement interval km — F-series",
                     "Replaced every … N75 services (info)", "Source / note"], freeze=False, filt=False)
rnotes = {"oil_filter": "Every service (GIDSS).", "fuel_filter": "Every service (GIDSS).",
          "air_filter": "Every 2nd service — provisional, waiting for IML confirmation.",
          "urea_filter": "GIDSS: 200,000 km N-series (NPR75), 80,000 km F-series 4HK1-TCH.",
          "brake_rotor": "About every 2nd pad change — provisional, not confirmed by IML.",
          "brake_pad": "Every 2nd service — not confirmed by IML.", "brake_shoe": "Every 2nd service — not confirmed by IML.",
          "blower_filter": "Every service (Jerome 2026-07-26)."}
non_ituk = rates.drop("ITUK", level=0, errors="ignore")
for i, (cat, lab) in enumerate(CATS.items()):
    rr_ = PB0 + i
    fN = non_ituk.xs((cat, "n_series_truck"), level=(1, 2)).mode().iloc[0]
    fF = non_ituk.xs((cat, "heavy_truck"), level=(1, 2)).mode().iloc[0]
    put(wr, rr_, 1, cat)
    put(wr, rr_, 2, lab)
    put(wr, rr_, 3, round(SVC_KM["N35"] / fN), BLUE, PCS, IN_FILL)
    put(wr, rr_, 4, round(SVC_KM["N75"] / fN), BLUE, PCS, IN_FILL)
    put(wr, rr_, 5, round(SVC_KM["F"] / fF), BLUE, PCS, IN_FILL)
    put(wr, rr_, 6, f"=D{rr_}/$B${svc_rows['N75']}", fmt="0.0")
    put(wr, rr_, 7, rnotes.get(cat, "Not confirmed by IML."))
PB1 = PB0 + len(CATS) - 1

OB0 = PB1 + 4
text(wr, OB0 - 2, 1, "Customer-specific replacement intervals (replace the general interval above for that customer)", BIG)
header(wr, OB0 - 1, ["Key", "Customer code", "Part code", "Interval km — N35", "Interval km — N75", "Interval km — F-series", "Applies under", "Source"],
       freeze=False, filt=False)
OVR = []
for cat in ("brake_pad", "brake_shoe"):
    iN, iF = rates.get(("ITUK", cat, "n_series_truck")), rates.get(("ITUK", cat, "heavy_truck"))
    OVR.append(("ITUK", cat, round(SVC_KM["N35"] / iN), round(SVC_KM["N75"] / iN), round(SVC_KM["F"] / iF), "Both",
                "IML market-research slide 2026-07-14: 100,000 km, front and rear together (Isuzu Truck UK only, O-licence inspections)."))
for cat in ("oil_filter", "fuel_filter"):
    OVR.append(("UTI", cat, None, 22_500, None, "Per model",
                "Isuzu GIDSS N_MY24 'Engine oil (Israel)': NPR75 / 4HK1 every 22,500 km in Israel. Not in the PMS model."))
for i, (c, cat, a, b, cc, ap, src) in enumerate(OVR):
    rr_ = OB0 + i
    put(wr, rr_, 1, f'=B{rr_}&"|"&C{rr_}')
    put(wr, rr_, 2, c)
    put(wr, rr_, 3, cat)
    put(wr, rr_, 4, a, BLUE, PCS, IN_FILL)
    put(wr, rr_, 5, b, BLUE, PCS, IN_FILL)
    put(wr, rr_, 6, cc, BLUE, PCS, IN_FILL)
    put(wr, rr_, 7, ap)
    put(wr, rr_, 8, src)
OB1 = OB0 + len(OVR) + 3  # room for extra rows typed in by hand
for rr_ in range(OB0 + len(OVR), OB1 + 1):
    put(wr, rr_, 1, f'=IF(B{rr_}="","",B{rr_}&"|"&C{rr_})')
    for cc_ in range(2, 9):
        put(wr, rr_, cc_, None, BLUE, PCS if 4 <= cc_ <= 6 else None, IN_FILL)
text(wr, OB1 + 2, 1, "Example: oil filter N75 = 40,000 km at 20,000 km a year → 0.5 filters a truck a year; at 50,000 km a year → 1.25. "
                     "N35 intervals are half the N75 ones because an N35 is serviced every 20,000 km.", NOTE)
wr.freeze_panes = "A6"


def km_cust(col, code_ref):
    return f"INDEX({KM}${col}${CB0}:${col}${CB1},MATCH({code_ref},{KM}$A${CB0}:$A${CB1},0))"


def km_int(model, r):
    gcol = {"N35": "C", "N75": "D", "F": "E"}[model]
    ocol = {"N35": "D", "N75": "E", "F": "F"}[model]
    gen = f"INDEX({KM}${gcol}${PB0}:${gcol}${PB1},MATCH(F{r},{KM}$A${PB0}:$A${PB1},0))"
    key = f'A{r}&"|"&F{r}'
    ov = f"INDEX({KM}${ocol}${OB0}:${ocol}${OB1},MATCH({key},{KM}$A${OB0}:$A${OB1},0))"
    ap = f"INDEX({KM}$G${OB0}:$G${OB1},MATCH({key},{KM}$A${OB0}:$A${OB1},0))"
    return f'IF(IFERROR(AND(N({ov})>0,OR({ap}="Both",{IBK}="Per model")),FALSE),{ov},{gen})'


# ----- Detail by truck family -----
wd = wb.create_sheet("Detail by truck family")
text(wd, 1, 1, "Expected PMS demand from UIO vs billed — by customer, period, part and truck family", TITLE)
text(wd, 2, 1, "Expected pieces = UIO × replacements a truck a year × months ÷ 12. N-series: N35 share × km N35 ÷ interval N35 + (1 − N35 share) × km N75 ÷ interval N75. "
               "F-series: km ÷ interval. Km and intervals from 'Km assumptions' (basis chosen there). Billed = parts that fit only this truck family.")
header(wd, 4, ["Customer code", "Customer", "Country", "Period", "Part", "Part code", "Truck family", "Family code", "UIO (trucks)",
               "N35 share", "Km a year — N35", "Interval km — N35", "Km a year — N75 / F-series", "Interval km — N75 / F-series",
               "Replacements a truck a year", "Months", "Expected pieces", "Average price €", "Expected €",
               "Billed pieces (this family only)", "Billed €", "Coverage % (pieces)", "Gap €"],
       [11, 28, 13, 11, 20, 18, 20, 14, 10, 8, 10, 10, 10, 10, 11, 8, 11, 10, 12, 12, 12, 10, 12])
r = 5
for c in cust_order:
    for key in PKEYS:
        for cat, lab in CATS.items():
            for fk, fl in FAMILIES.items():
                pcs, eur = agg.get((c, key, cat, fk), (0.0, 0.0))
                asp = eur / pcs if pcs > 0 else asp_cust.get((c, cat), asp_net.get(cat))
                ns = fk == "n_series_truck"
                put(wd, r, 1, c)
                put(wd, r, 2, NAMES.get(c, c))
                put(wd, r, 3, country[c])
                put(wd, r, 4, key)
                put(wd, r, 5, lab)
                put(wd, r, 6, cat)
                put(wd, r, 7, fl)
                put(wd, r, 8, fk)
                put(wd, r, 9, "=" + uio_look("I" if ns else "J", f"A{r}", f"D{r}"), GREEN, PCS1)
                if ns:
                    put(wd, r, 10, "=" + km_cust("F", f"A{r}"), GREEN, PCT)
                    put(wd, r, 11, "=" + km_cust(KMCOL["N35"], f"A{r}"), GREEN, PCS)
                    put(wd, r, 12, "=" + km_int("N35", r), GREEN, PCS)
                    put(wd, r, 13, "=" + km_cust(KMCOL["N75"], f"A{r}"), GREEN, PCS)
                    put(wd, r, 14, "=" + km_int("N75", r), GREEN, PCS)
                    put(wd, r, 15, f"=J{r}*K{r}/L{r}+(1-J{r})*M{r}/N{r}", fmt="0.000")
                else:
                    put(wd, r, 10, 0, fmt=PCT)
                    put(wd, r, 11, "")
                    put(wd, r, 12, "")
                    put(wd, r, 13, "=" + km_cust(KMCOL["F"], f"A{r}"), GREEN, PCS)
                    put(wd, r, 14, "=" + km_int("F", r), GREEN, PCS)
                    put(wd, r, 15, f"=M{r}/N{r}", fmt="0.000")
                put(wd, r, 16, "=" + MONTHS.format(p=f"D{r}"), GREEN)
                put(wd, r, 17, f"=I{r}*O{r}*P{r}/12", fmt=PCS1)
                put(wd, r, 18, round(float(asp), 4) if asp else None, BLUE, EUR2, IN_FILL)
                put(wd, r, 19, f"=Q{r}*N(R{r})", fmt=EUR)
                put(wd, r, 20, pcs, BLUE, PCS, IN_FILL)
                put(wd, r, 21, eur, BLUE, EUR, IN_FILL)
                put(wd, r, 22, f'=IF(Q{r}>0,T{r}/Q{r},"")', fmt=PCT)
                put(wd, r, 23, f"=MAX(0,Q{r}-T{r})*N(R{r})", fmt=EUR)
                r += 1
D_LAST = r - 1
wd.cell(row=4, column=18).comment = Comment("Billed € ÷ billed pieces for this customer, part, family and period; if nothing billed, this customer's "
                                            "average for the part over all periods, else the network average.", "ISZE")
D = "'Detail by truck family'!"


def km_text(code_ref):
    """'18,630 (Market-stated) / 50,000 (Market-stated) / 27,242 (Measured odometers)' for one customer (live)."""
    return '&" / "&'.join(f'TEXT({km_cust(KMCOL[m_], code_ref)},"#,##0")&" ("&{km_cust(SRCCOL[m_], code_ref)}&")"' for m_ in ("N35", "N75", "F"))


def assumptions_line(code_ref):
    """One readable line naming the km and sources used for a customer (live)."""
    parts = []
    for m_ in ("N35", "N75", "F"):
        parts.append(f'"{m_ if m_ != "F" else "F-series"} "&TEXT({km_cust(KMCOL[m_], code_ref)},"#,##0")&" km ("&{km_cust(SRCCOL[m_], code_ref)}&")"')
    return ('="Assumptions: km a year per truck — "&' + '&" · "&'.join(parts)
            + f'&" · N35 share "&TEXT({km_cust("F", code_ref)},"0%")&" · mileage basis "&{MBK}&", interval basis "&{IBK}&" (see Km assumptions)"')


# ----- Ranking sheet is referenced by the coverage helper columns: create it now, fill later -----
wk2 = wb.create_sheet("Ranking")
RK = "Ranking!"

# ----- Coverage by customer (engine for overview, ranking, one-pager) -----
wc = wb.create_sheet("Coverage by customer")
text(wc, 1, 1, "PMS coverage by customer, period and part — trucks only", TITLE)
text(wc, 2, 1, "LOW = only truck-only parts. HIGH = also parts shared with other vehicles and parts with no vehicle reference. "
               "Genuine / BVP columns are the whole customer (trucks and pickups). Grey columns drive the Ranking sheet.")
header(wc, 4, ["Key", "Customer code", "Customer", "Country", "Period", "Part", "Part code", "Truck share of fleet",
               "Expected pieces (trucks)", "Expected € (trucks)", "Billed pieces — truck-only parts", "Billed pieces — shared parts",
               "Billed pieces — no vehicle reference", "Billed € — truck-only parts", "Billed € — shared + no reference",
               "Coverage % LOW", "Coverage % HIGH", "Average price €", "Gap € LOW", "Gap € HIGH",
               "Genuine € (customer)", "BVP € (customer)", "BVP share of €", "Genuine € with no BVP alternative", "No-BVP share of genuine €",
               "Action (Ranking view)", "Ranking: coverage (chosen view)", "Ranking: gap € (chosen view)", "Ranking: sort value",
               "Billed pieces (AUTO view)", "Gap € (AUTO view)"],
       [26, 11, 28, 13, 11, 20, 18, 9, 11, 12, 11, 11, 11, 12, 12, 9, 9, 9, 12, 12, 12, 12, 9, 12, 9, 30, 10, 12, 12, 12, 12])
r = 5
for c in cust_order:
    for key in PKEYS:
        for cat, lab in CATS.items():
            sh = agg.get((c, key, cat, "shared_across_families"), (0.0, 0.0))
            un = agg.get((c, key, cat, "unattributed"), (0.0, 0.0))
            mx = mix.get((c, key, cat), dict(gen_eur=0, bvp_eur=0, nobvp_eur=0))
            crit = f"{D}$A$5:$A${D_LAST},B{r},{D}$D$5:$D${D_LAST},E{r},{D}$F$5:$F${D_LAST},G{r}"
            hi = f'OR({RK}$D$3="HIGH",AND({RK}$D$3="AUTO",H{r}>=0.9))'
            put(wc, r, 1, f'=B{r}&"|"&E{r}&"|"&G{r}')
            put(wc, r, 2, c)
            put(wc, r, 3, NAMES.get(c, c))
            put(wc, r, 4, country[c])
            put(wc, r, 5, key)
            put(wc, r, 6, lab)
            put(wc, r, 7, cat)
            put(wc, r, 8, "=" + uio_look("M", f"B{r}", f"E{r}"), GREEN, PCT)
            put(wc, r, 9, f"=SUMIFS({D}$Q$5:$Q${D_LAST},{crit})", GREEN, PCS)
            put(wc, r, 10, f"=SUMIFS({D}$S$5:$S${D_LAST},{crit})", GREEN, EUR)
            put(wc, r, 11, f"=SUMIFS({D}$T$5:$T${D_LAST},{crit})", GREEN, PCS)
            put(wc, r, 12, sh[0], BLUE, PCS, IN_FILL)
            put(wc, r, 13, un[0], BLUE, PCS, IN_FILL)
            put(wc, r, 14, f"=SUMIFS({D}$U$5:$U${D_LAST},{crit})", GREEN, EUR)
            put(wc, r, 15, sh[1] + un[1], BLUE, EUR, IN_FILL)
            put(wc, r, 16, f'=IF(I{r}>0,K{r}/I{r},"")', fmt=PCT)
            put(wc, r, 17, f'=IF(I{r}>0,(K{r}+L{r}+M{r})/I{r},"")', fmt=PCT)
            put(wc, r, 18, f'=IF(I{r}>0,J{r}/I{r},"")', fmt=EUR2)
            put(wc, r, 19, f"=MAX(0,I{r}-K{r})*N(R{r})", fmt=EUR)
            put(wc, r, 20, f"=MAX(0,I{r}-K{r}-L{r}-M{r})*N(R{r})", fmt=EUR)
            put(wc, r, 21, float(mx["gen_eur"]), BLUE, EUR, IN_FILL)
            put(wc, r, 22, float(mx["bvp_eur"]), BLUE, EUR, IN_FILL)
            put(wc, r, 23, f'=IF(U{r}+V{r}>0,V{r}/(U{r}+V{r}),"")', fmt=PCT)
            put(wc, r, 24, float(mx["nobvp_eur"]), BLUE, EUR, IN_FILL)
            put(wc, r, 25, f'=IF(U{r}>0,X{r}/U{r},"")', fmt=PCT)
            put(wc, r, 26, action(f"J{r}", f"AA{r}", f"U{r}", f"V{r}", f"W{r}", f"Y{r}"))
            put(wc, r, 27, f"=IF({hi},Q{r},P{r})", fmt=PCT, fill=GREY)
            put(wc, r, 28, f"=IF({hi},T{r},S{r})", fmt=EUR, fill=GREY)
            put(wc, r, 29, f'=IF(AND(E{r}={RK}$B$3,OR({RK}$B$4="All",{RK}$B$4=C{r}),OR({RK}$D$4="All",{RK}$D$4=F{r})),AB{r}+ROW()/1000000,-1)',
                fmt="0.00", fill=GREY)
            put(wc, r, 30, f"=IF(H{r}>=0.9,K{r}+L{r}+M{r},K{r})", fmt=PCS)
            put(wc, r, 31, f"=IF(H{r}>=0.9,T{r},S{r})", fmt=EUR)
            r += 1
C_LAST = r - 1
wc.conditional_formatting.add(f"P5:Q{C_LAST}", ColorScaleRule(**RED_GREEN))
wc.cell(row=4, column=24).comment = Comment("Genuine PMS part numbers billed that have no BVP partner in the BVP catalogue cross-reference. Whole customer.", "ISZE")
ACTION_NOTE = ("Small: expected under €1,000. Covered: coverage 80%+. Hardly billed: billed under 3% of expected € — check the km interval first. "
               "Develop BVP: half or more of genuine € is on parts with no BVP. "
               "Push existing BVP / price: BVP exists but under 20% of €. Otherwise BVP already sells: look at price and availability.")
wc.cell(row=4, column=26).comment = Comment(ACTION_NOTE + " Uses the view chosen on the Ranking sheet.", "ISZE")
C = "'Coverage by customer'!"

# ----- No-BVP list -----
wn = wb.create_sheet("Genuine no BVP")
text(wn, 1, 1, "Genuine PMS parts with no BVP alternative — by customer and period (truck customers, whole customer)", TITLE)
text(wn, 2, 1, "No BVP = genuine part number not paired with a BVP part in the BVP catalogue cross-reference. "
               "Part numbers that look like BVP numbers (5876… / 1876…) are left out.")
header(wn, 4, ["Key", "Country", "Customer", "Period", "Rank in customer & period", "Part", "Part number", "Description", "Fits",
               "Billed pieces", "Billed €", "Average price €"], [24, 13, 28, 11, 9, 20, 13, 32, 22, 11, 12, 11])
famlab = {**FAMILIES, "light_vehicle": "Pickup (D-Max)", "shared_across_families": "Fits more than one family", "unattributed": "No vehicle reference"}
r = 5
for _, x in nobvp.iterrows():
    put(wn, r, 1, f'=C{r}&"|"&D{r}&"|"&E{r}')
    put(wn, r, 2, country[x.distributor_code])
    put(wn, r, 3, NAMES.get(x.distributor_code, x.distributor_code))
    put(wn, r, 4, x.period)
    put(wn, r, 5, int(x["rank"]))
    put(wn, r, 6, CATS.get(x["cat"], x["cat"]))
    put(wn, r, 7, x.pn)
    put(wn, r, 8, x.desc)
    put(wn, r, 9, famlab.get(x.fam, "No vehicle reference"))
    put(wn, r, 10, float(x.pcs), BLUE, PCS)
    put(wn, r, 11, float(x.eur), BLUE, EUR)
    put(wn, r, 12, f'=IF(J{r}>0,K{r}/J{r},"")', fmt=EUR2)
    r += 1
N_LAST = r - 1
NB = "'Genuine no BVP'!"

# ----- Check vs model -----
wk = wb.create_sheet("Check vs model")
text(wk, 1, 1, "Check: billed € rebuilt from billing vs the published PMS coverage model (calendar years)", TITLE)
text(wk, 2, 1, "FY figures use the rebuild. Where the rebuild matches the model on calendar years, the FY figures can be trusted to the same degree. "
               "Red = more than 5% and €1,000 off.")
header(wk, 4, ["Year", "Country", "Customer", "Part", "Rebuilt €", "Model €", "Difference €", "Difference %"], [7, 13, 28, 20, 12, 12, 12, 11])
r = 5
for _, x in chk.sort_values(["year", "dist", "cat"]).iterrows():
    if x.dist not in country or x["cat"] not in CATS:
        continue
    put(wk, r, 1, int(x.year))
    put(wk, r, 2, country[x.dist])
    put(wk, r, 3, NAMES.get(x.dist, x.dist))
    put(wk, r, 4, CATS[x["cat"]])
    put(wk, r, 5, float(x.rebuilt), BLUE, EUR)
    put(wk, r, 6, float(x.published), BLUE, EUR)
    put(wk, r, 7, f"=E{r}-F{r}", fmt=EUR)
    put(wk, r, 8, f'=IF(F{r}<>0,G{r}/F{r},"")', fmt=PCT)
    r += 1
K_LAST = r - 1
for i, y in enumerate((2024, 2025)):
    rr_ = K_LAST + 2 + i
    put(wk, rr_, 3, f"Total {y}", BOLD)
    put(wk, rr_, 5, f"=SUMIFS(E5:E{K_LAST},A5:A{K_LAST},{y})", BOLD, EUR)
    put(wk, rr_, 6, f"=SUMIFS(F5:F{K_LAST},A5:A{K_LAST},{y})", BOLD, EUR)
    put(wk, rr_, 7, f"=E{rr_}-F{rr_}", BOLD, EUR)
    put(wk, rr_, 8, f'=IF(F{rr_}<>0,G{rr_}/F{rr_},"")', BOLD, PCT)
wk.conditional_formatting.add(f"H5:H{K_LAST}", FormulaRule(formula=["AND(ISNUMBER(H5),ABS(H5)>0.05,ABS(G5)>1000)"],
                                                           fill=PatternFill("solid", fgColor="F8CBAD")))

cats = list(CATS.items())

# ----- Overview by country -----
wo = wb.create_sheet("Overview by country")
text(wo, 1, 1, "PMS coverage — trucks, by country and customer", TITLE)
OP = selector(wo, 3, 1, "Period", "FY2026", PERIOD_LIST)
OV = selector(wo, 3, 3, "Coverage view", "AUTO", '"AUTO,LOW,HIGH"')
put(wo, 5, 1, f"=\"Assumptions: mileage basis \"&{MBK}&\", interval basis \"&{IBK}&\" — km per customer and truck model in the last column and on 'Km assumptions'.\"", Font(name=F, size=10, bold=True, color="C00000"), box=False)
text(wo, 4, 1, "LOW = truck-only parts. HIGH = also shared parts and parts with no vehicle reference. AUTO = HIGH where trucks are 90%+ of the fleet, LOW elsewhere.", NOTE)
header(wo, 6, ["Country", "Customer", "Trucks in service (UIO)", "Truck share of fleet"] + [lab for _, lab in cats] + ["All PMS — expected €", "All PMS — gap €",
                                                                                                         "Km a year used — N35 / N75 / F-series (source)"],
       [15, 28, 11, 10] + [10] * len(cats) + [13, 13, 46], freeze=False, filt=False)
wo.freeze_panes = "C7"
r = 7
for c in cust_order:
    put(wo, r, 1, country[c])
    put(wo, r, 2, NAMES.get(c, c))
    put(wo, r, 3, "=" + uio_look("K", f'"{c}"', OP), GREEN, PCS)
    put(wo, r, 4, "=" + uio_look("M", f'"{c}"', OP), GREEN, PCT)
    hi = f'OR({OV}="HIGH",AND({OV}="AUTO",$D{r}>=0.9))'
    for j, (cat, lab) in enumerate(cats):
        crit = f'{C}$B$5:$B${C_LAST},"{c}",{C}$E$5:$E${C_LAST},{OP},{C}$G$5:$G${C_LAST},"{cat}"'
        exp = f"SUMIFS({C}$I$5:$I${C_LAST},{crit})"
        lo = f"SUMIFS({C}$K$5:$K${C_LAST},{crit})"
        hv = f"(SUMIFS({C}$K$5:$K${C_LAST},{crit})+SUMIFS({C}$L$5:$L${C_LAST},{crit})+SUMIFS({C}$M$5:$M${C_LAST},{crit}))"
        put(wo, r, 5 + j, f'=IF({exp}>0,IF({hi},{hv},{lo})/{exp},"")', GREEN, PCT)
    critc = f'{C}$B$5:$B${C_LAST},"{c}",{C}$E$5:$E${C_LAST},{OP}'
    put(wo, r, 5 + len(cats), f"=SUMIFS({C}$J$5:$J${C_LAST},{critc})", GREEN, EUR)
    put(wo, r, 6 + len(cats), f"=IF({hi},SUMIFS({C}$T$5:$T${C_LAST},{critc}),SUMIFS({C}$S$5:$S${C_LAST},{critc}))", GREEN, EUR)
    put(wo, r, 7 + len(cats), "=" + km_text(f'"{c}"'), GREEN)
    r += 1
O_LAST = r - 1
put(wo, r, 1, "All truck customers", BOLD)
put(wo, r, 2, "", BOLD)
put(wo, r, 3, f"=SUM(C7:C{O_LAST})", BOLD, PCS)
put(wo, r, 4, "", BOLD)
for j, (cat, lab) in enumerate(cats):
    crit = f'{C}$E$5:$E${C_LAST},{OP},{C}$G$5:$G${C_LAST},"{cat}"'
    exp = f"SUMIFS({C}$I$5:$I${C_LAST},{crit})"
    terms = []
    for i, c in enumerate(cust_order):
        ci = f'{C}$B$5:$B${C_LAST},"{c}",{crit}'
        lo = f"SUMIFS({C}$K$5:$K${C_LAST},{ci})"
        hv = f"SUMIFS({C}$K$5:$K${C_LAST},{ci})+SUMIFS({C}$L$5:$L${C_LAST},{ci})+SUMIFS({C}$M$5:$M${C_LAST},{ci})"
        terms.append(f'IF(OR({OV}="HIGH",AND({OV}="AUTO",$D{7 + i}>=0.9)),{hv},{lo})')
    put(wo, r, 5 + j, f'=IF({exp}>0,({"+".join(terms)})/{exp},"")', BOLD, PCT)
ecol, gcol = get_column_letter(5 + len(cats)), get_column_letter(6 + len(cats))
put(wo, r, 5 + len(cats), f"=SUM({ecol}7:{ecol}{O_LAST})", BOLD, EUR)
put(wo, r, 6 + len(cats), f"=SUM({gcol}7:{gcol}{O_LAST})", BOLD, EUR)
for cc in range(1, 7 + len(cats)):
    wo.cell(row=r, column=cc).fill = SUB_FILL
for row in wo.iter_rows(min_row=7, max_row=r, min_col=3, max_col=7 + len(cats)):
    for cell in row:
        cell.alignment = Alignment(wrap_text=True, horizontal="right")
wo.conditional_formatting.add(f"E7:{get_column_letter(4 + len(cats))}{r}", ColorScaleRule(**RED_GREEN))
text(wo, r + 2, 1, "Coverage above 100% is possible: billed parts also go to vehicles outside the truck UIO (for mixed customers, pickups using shared parts). "
                   "FY2027 YTD expected demand is scaled to the months billed.", NOTE)

# ----- Ranking (filled) -----
text(wk2, 1, 1, "Opportunity ranking — customer × part by gap €", TITLE)
RP = selector(wk2, 3, 1, "Period", "FY2026", PERIOD_LIST)
selector(wk2, 3, 3, "Coverage view", "AUTO", '"AUTO,LOW,HIGH"')
wk2["Z1"] = "All"
for i, c in enumerate(cust_order):
    wk2.cell(row=2 + i, column=26, value=NAMES.get(c, c))
wk2["AA1"] = "All"
for i, (_, lab) in enumerate(cats):
    wk2.cell(row=2 + i, column=27, value=lab)
wk2.column_dimensions["Z"].hidden = True
wk2.column_dimensions["AA"].hidden = True
selector(wk2, 4, 1, "Customer", "All", f"$Z$1:$Z${1 + len(cust_order)}")
selector(wk2, 4, 3, "Part", "All", f"$AA$1:$AA${1 + len(cats)}")
put(wk2, 6, 1, f"=\"Assumptions: mileage basis \"&{MBK}&\", interval basis \"&{IBK}&\" — km per customer and truck model in the last column and on 'Km assumptions'.\"", Font(name=F, size=10, bold=True, color="C00000"), box=False)
text(wk2, 5, 1, "Top 60 by gap € for the chosen period, view and filters. Genuine / BVP € are the whole customer (trucks and pickups).", NOTE)
header(wk2, 7, ["Rank", "Country", "Customer", "Part", "Trucks in service (UIO)", "Expected € (trucks)", "Coverage %", "Gap €",
                "Genuine €", "BVP €", "BVP share of €", "Genuine € with no BVP", "No-BVP share of genuine €", "Action",
                "Km a year used — N35 / N75 / F-series (source)"],
       [7, 15, 28, 22, 11, 12, 10, 12, 12, 12, 10, 12, 10, 36, 46], freeze=False, filt=False)
wk2.freeze_panes = "A8"
wk2.cell(row=7, column=14).comment = Comment(ACTION_NOTE, "ISZE")
SORT = f"{C}$AC$5:$AC${C_LAST}"
for k in range(1, 61):
    r = 7 + k
    m = f"MATCH(LARGE({SORT},{k}),{SORT},0)"
    ok = f"LARGE({SORT},{k})>0"
    put(wk2, r, 1, f'=IF({ok},{k},"")')
    for col, src, fmt in [(2, "D", None), (3, "C", None), (4, "F", None), (6, "J", EUR), (7, "AA", PCT), (8, "AB", EUR),
                          (9, "U", EUR), (10, "V", EUR), (11, "W", PCT), (12, "X", EUR), (13, "Y", PCT), (14, "Z", None)]:
        put(wk2, r, col, f'=IF({ok},INDEX({C}${src}$5:${src}${C_LAST},{m}),"")', fmt=fmt)
    put(wk2, r, 15, f'=IF({ok},' + km_text(f"INDEX({C}$B$5:$B${C_LAST},{m})") + ',"")', fmt=None)
    put(wk2, r, 5, f'=IF({ok},SUMIFS(UIO!$K$5:$K${U_LAST},UIO!$A$5:$A${U_LAST},INDEX({C}$B$5:$B${C_LAST},{m})&"|"&{UIOY.format(p=RP)}),"")', fmt=PCS)
wk2.conditional_formatting.add("G8:G67", ColorScaleRule(**RED_GREEN))
wk2.conditional_formatting.add("N8:N67", FormulaRule(formula=['$N8="Develop BVP"'], **DEVELOP))
text(wk2, 69, 1, "Sum of gap € in the top 60", BOLD)
put(wk2, 69, 8, "=SUM(H8:H67)", BOLD, EUR)

# ----- Customer one-pager -----
w1 = wb.create_sheet("Customer one-pager")
text(w1, 1, 1, "Customer one-pager — PMS coverage, gap and BVP", TITLE)
for i, c in enumerate(cust_order):
    w1.cell(row=1 + i, column=26, value=NAMES.get(c, c))
    w1.cell(row=1 + i, column=27, value=c)
w1.column_dimensions["Z"].hidden = True
w1.column_dimensions["AA"].hidden = True
NC = len(cust_order)
CU = selector(w1, 3, 1, "Customer", NAMES["ITUK"], f"$Z$1:$Z${NC}")
PP = selector(w1, 4, 1, "Period", "FY2026", PERIOD_LIST)
VV = selector(w1, 5, 1, "Coverage view", "AUTO", '"AUTO,LOW,HIGH"')
CODE = f"INDEX($AA$1:$AA${NC},MATCH({CU},$Z$1:$Z${NC},0))"
text(w1, 3, 4, "Country", BOLD)
put(w1, 3, 5, f'=INDEX(UIO!$D$5:$D${U_LAST},MATCH({CODE}&"|"&{UIOY.format(p=PP)},UIO!$A$5:$A${U_LAST},0))', GREEN)
text(w1, 4, 4, "Trucks in service (UIO)", BOLD)
put(w1, 4, 5, "=" + uio_look("K", CODE, PP), GREEN, PCS)
text(w1, 5, 4, "Pickups (info)", BOLD)
put(w1, 5, 5, "=" + uio_look("L", CODE, PP), GREEN, PCS)
text(w1, 3, 7, "Truck share of fleet", BOLD)
put(w1, 3, 8, "=" + uio_look("M", CODE, PP), GREEN, PCT)
text(w1, 4, 7, "View used", BOLD)
put(w1, 4, 8, f'=IF(OR({VV}="HIGH",AND({VV}="AUTO",$H$3>=0.9)),"HIGH","LOW")', GREEN)
text(w1, 5, 7, "Months in period", BOLD)
put(w1, 5, 8, "=" + MONTHS.format(p=PP), GREEN)
put(w1, 6, 1, assumptions_line(CODE), Font(name=F, size=10, bold=True, color="C00000"), box=False)
header(w1, 7, ["Part", "Expected pieces", "Billed pieces", "Coverage %", "Gap €", "Expected €", "Genuine €", "BVP €", "BVP share of €",
               "Genuine € with no BVP", "No-BVP share", "Action"],
       [24, 12, 12, 10, 12, 12, 12, 12, 10, 12, 10, 36], freeze=False, filt=False)
w1.row_dimensions[7].height = 32
HI1 = '$H$4="HIGH"'
for i, (cat, lab) in enumerate(cats):
    r = 8 + i
    mt = f'MATCH({CODE}&"|"&{PP}&"|"&"{cat}",{C}$A$5:$A${C_LAST},0)'
    g = lambda col, mt=mt: f"INDEX({C}${col}$5:${col}${C_LAST},{mt})"  # noqa: E731
    put(w1, r, 1, lab)
    put(w1, r, 2, f"={g('I')}", GREEN, PCS)
    put(w1, r, 3, f"=IF({HI1},{g('K')}+{g('L')}+{g('M')},{g('K')})", GREEN, PCS)
    put(w1, r, 4, f'=IF(B{r}>0,C{r}/B{r},"")', fmt=PCT)
    put(w1, r, 5, f"=IF({HI1},{g('T')},{g('S')})", GREEN, EUR)
    put(w1, r, 6, f"={g('J')}", GREEN, EUR)
    put(w1, r, 7, f"={g('U')}", GREEN, EUR)
    put(w1, r, 8, f"={g('V')}", GREEN, EUR)
    put(w1, r, 9, f'=IF(G{r}+H{r}>0,H{r}/(G{r}+H{r}),"")', fmt=PCT)
    put(w1, r, 10, f"={g('X')}", GREEN, EUR)
    put(w1, r, 11, f'=IF(G{r}>0,J{r}/G{r},"")', fmt=PCT)
    put(w1, r, 12, action(f"F{r}", f"D{r}", f"G{r}", f"H{r}", f"I{r}", f"K{r}"))
T1 = 8 + len(cats)
put(w1, T1, 1, "All PMS parts (€)", BOLD)
for ci in (2, 3, 4, 12):
    put(w1, T1, ci, "", BOLD)
for ci, col in ((5, "E"), (6, "F"), (7, "G"), (8, "H"), (10, "J")):
    put(w1, T1, ci, f"=SUM({col}8:{col}{T1 - 1})", BOLD, EUR)
put(w1, T1, 9, f'=IF(G{T1}+H{T1}>0,H{T1}/(G{T1}+H{T1}),"")', BOLD, PCT)
put(w1, T1, 11, f'=IF(G{T1}>0,J{T1}/G{T1},"")', BOLD, PCT)
for cc in range(1, 13):
    w1.cell(row=T1, column=cc).fill = SUB_FILL
w1.conditional_formatting.add(f"D8:D{T1 - 1}", ColorScaleRule(**RED_GREEN))
w1.conditional_formatting.add(f"L8:L{T1 - 1}", FormulaRule(formula=['$L8="Develop BVP"'], **DEVELOP))
w1.cell(row=7, column=12).comment = Comment(ACTION_NOTE, "ISZE")
text(w1, T1 + 1, 1, "Coverage is on pieces per part; pieces of different parts are not added up. Genuine / BVP € = whole customer (trucks and pickups).", NOTE)
TB = T1 + 3
text(w1, TB, 1, "Top 10 genuine PMS parts with no BVP alternative (this customer and period)", BIG)
header(w1, TB + 1, ["#", "Part", "Part number", "Description", "Fits", "Billed pieces", "Billed €", "Average price €"],
       freeze=False, filt=False)
w1.row_dimensions[TB + 1].height = 30
for k in range(1, 11):
    r = TB + 1 + k
    mt = f'MATCH({CU}&"|"&{PP}&"|"&{k},{NB}$A$5:$A${N_LAST},0)'
    put(w1, r, 1, k)
    for col, src, fmt in [(2, "F", None), (3, "G", None), (4, "H", None), (5, "I", None), (6, "J", PCS), (7, "K", EUR), (8, "L", EUR2)]:
        put(w1, r, col, f'=IFERROR(INDEX({NB}${src}$5:${src}${N_LAST},{mt}),"")', fmt=fmt)
w1.column_dimensions["D"].width = 30
w1.freeze_panes = "A7"

# ----- PMS parts list (part number x customer, FY) -----
wl = wb.create_sheet("PMS parts list")
text(wl, 1, 1, "PMS parts list — every PMS part number billed to the truck customers, by customer and FY", TITLE)
text(wl, 2, 1, "Genuine and BVP, credit notes and returns removed. Use the filters; the totals row adds up only the visible rows. "
               "Whole customer (trucks and pickups). BVP partner = paired part in the BVP catalogue cross-reference.")
FYS = ["FY2025", "FY2026", "FY2027 YTD"]
lcols = ["Part number", "Description", "Part", "Genuine / BVP", "BVP alternative?", "Partner part number(s)", "Fits", "Country", "Customer",
         "Part type from", "Check"]
for f_ in FYS:
    lcols += [f"{f_} pieces", f"{f_} €"]
lcols += ["FY2026 average price €"]
header(wl, 5, lcols, [13, 32, 20, 16, 12, 24, 22, 13, 28, 16, 30] + [10, 12] * len(FYS) + [11])
g2b, b2g = {}, {}
for r_ in cx.itertuples():
    g2b.setdefault(norm(r_.genuine_pn), set()).add(r_.bvp_pn)
    b2g.setdefault(norm(r_.bvp_pn), set()).add(r_.genuine_pn)
per = {k: (st, en) for k, _t, st, en, *_ in PERIODS}
lx = s[s.distributor_code.isin(cv_codes) & (s.bd >= per["FY2025"][0]) & (s.bd < per["FY2027 YTD"][1])].copy()
lx["fy"] = None
for f_ in FYS:
    lx.loc[(lx.bd >= per[f_][0]) & (lx.bd < per[f_][1]), "fy"] = f_
lg = lx.groupby(["pn", "distributor_code", "fy"]).agg(pcs=("billed_qty", "sum"), eur=("net_sales_value", "sum")).unstack("fy")
pn_txt = s.groupby("pn").part_number.first()
r = 6
pn_tot = lg[[c for c in lg.columns if c[0] == "eur"]].sum(axis=1).groupby(level=0).sum()
lg = lg.assign(_t=lg.index.get_level_values(0).map(pn_tot), _r=lg[[c for c in lg.columns if c[0] == "eur"]].sum(axis=1))
lg = lg.sort_values(["_t", "_r"], ascending=False)
for (pn, d), row in lg.iterrows():
    cat = PNCAT.get(pn)
    raw = str(pn_txt.get(pn, pn))
    if pn in bvp_set:
        kind, alt, partner = "BVP", "Is BVP", ", ".join(sorted(b2g.get(pn, [])))
    elif raw[:4] in ("5876", "1876"):
        kind, alt, partner = "BVP number, not in catalogue", "Is BVP", ""
    else:
        prt = sorted(g2b.get(pn, []))
        kind, alt, partner = "Genuine", "Yes" if prt else "No", ", ".join(prt)
    put(wl, r, 1, raw)
    put(wl, r, 2, desc.get(pn, ""))
    put(wl, r, 3, CATS.get(cat, cat))
    put(wl, r, 4, kind)
    put(wl, r, 5, alt)
    put(wl, r, 6, partner)
    put(wl, r, 7, famlab.get(pn_fam.get(pn) or pn_res.get(pn), "Fits more than one family"))
    put(wl, r, 8, country[d])
    put(wl, r, 9, NAMES.get(d, d))
    put(wl, r, 10, CATSRC.get(pn, ""))
    put(wl, r, 11, part_check(desc.get(pn, "")))
    for i, f_ in enumerate(FYS):
        q = row.get(("pcs", f_))
        e = row.get(("eur", f_))
        put(wl, r, 12 + 2 * i, float(q) if pd.notna(q) else 0.0, BLUE, PCS)
        put(wl, r, 13 + 2 * i, float(e) if pd.notna(e) else 0.0, BLUE, EUR)
    put(wl, r, 18, f'=IF(N{r}>0,O{r}/N{r},"")', fmt=EUR2)
    r += 1
L_LAST = r - 1
text(wl, 4, 11, "Total of visible rows", BOLD)
for ci in range(12, 18):
    col = get_column_letter(ci)
    put(wl, 4, ci, f"=SUBTOTAL(9,{col}6:{col}{L_LAST})", BOLD, PCS if ci % 2 == 0 else EUR, SUB_FILL)
wr.freeze_panes = "A4"
wl.auto_filter.ref = f"A5:{get_column_letter(len(lcols))}{L_LAST}"
wl.freeze_panes = "B6"
wl.conditional_formatting.add(f"E6:E{L_LAST}", FormulaRule(formula=['$E6="No"'], **DEVELOP))
wl.conditional_formatting.add(f"K6:K{L_LAST}", FormulaRule(formula=['$K6<>""'], fill=PatternFill("solid", fgColor="FCE4D6")))
wl.cell(row=5, column=10).comment = Comment("PMS model tagging = the part type the PMS coverage model gives this part. Part description = "
                                            "the model's part list has it, but its part type is in a file not available here, so it was read from the description.", "ISZE")

# ----- PMS tree: group -> part -> part number, expandable (Excel outline) -----
from openpyxl.worksheet.properties import Outline  # noqa: E402

GROUPS = {"Filters": ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter"],
          "Brakes": ["brake_pad", "brake_shoe", "brake_rotor"],
          "Clutch": ["clutch_kit", "clutch_disc", "clutch_pressure_plate", "release_bearing", "pilot_bearing", "clutch_booster"]}
wt = wb.create_sheet("PMS tree")
text(wt, 1, 1, "PMS tree — group › part › part number (click + / − on the left, or the 1 2 3 buttons at the top left)", TITLE)
wt["Z1"] = "All"
for i, c in enumerate(cust_order):
    wt.cell(row=2 + i, column=26, value=NAMES.get(c, c))
for i, f_ in enumerate(FYS):
    wt.cell(row=1 + i, column=27, value=f_)
wt.column_dimensions["Z"].hidden = True
wt.column_dimensions["AA"].hidden = True
TC = selector(wt, 3, 1, "Customer", "All", f"$Z$1:$Z${1 + len(cust_order)}")
TP = selector(wt, 4, 1, "Period (FY)", "FY2026", f"$AA$1:$AA${len(FYS)}")
text(wt, 3, 4, "Level 1 = group, 2 = part, 3 = part numbers. Billed = whole customer (trucks and pickups), genuine + BVP. "
               "Expected / coverage / gap = trucks only, AUTO view (HIGH for 90%+ truck fleets, LOW otherwise).", NOTE)
put(wt, 5, 1, f"=\"Assumptions: mileage basis \"&{MBK}&\", interval basis \"&{IBK}&\" — km per customer and truck model on 'Km assumptions'.\"", BOLD, box=False)
TH = 7
header(wt, TH, ["Group › part › part number", "Part number", "Description", "Genuine / BVP", "BVP alternative?", "Billed pieces", "Billed €",
                "Share of part €", "Expected pieces (trucks)", "Coverage % (trucks)", "Gap € (trucks)", "Check"],
       [34, 13, 32, 16, 11, 11, 13, 9, 12, 10, 13, 30], freeze=False, filt=False)
wt.freeze_panes = f"B{TH + 1}"
wt.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=False)

# helper columns on the parts list: the tree's chosen customer and FY, per row
PL = "'PMS parts list'!"
TT = "'PMS tree'!"
put(wl, 5, 19, "Tree: pieces (chosen)", HFONT, fill=H_FILL)
put(wl, 5, 20, "Tree: € (chosen)", HFONT, fill=H_FILL)
for rr_ in range(6, L_LAST + 1):
    sel = f'AND(OR({TT}$B$3="All",{TT}$B$3=I{rr_}),1)'
    idx = f'MATCH({TT}$B$4,{TT}$AA$1:$AA${len(FYS)},0)'
    put(wl, rr_, 19, f"=IF({sel},CHOOSE({idx},L{rr_},N{rr_},P{rr_}),0)", fmt=PCS, fill=GREY)
    put(wl, rr_, 20, f"=IF({sel},CHOOSE({idx},M{rr_},O{rr_},Q{rr_}),0)", fmt=EUR, fill=GREY)
wl.column_dimensions["S"].width = 11
wl.column_dimensions["T"].width = 12

pn_fy26 = lx[lx.fy == "FY2026"].groupby("pn").net_sales_value.sum()
pn_rows = sorted(pn_tot.items(), key=lambda kv: (-pn_fy26.get(kv[0], 0.0), -kv[1]))
cust_crit = f'IF($B$3="All","*",$B$3)'
r = TH + 1
grp_rows = []
GREY_BOLD = Font(name=F, size=10, bold=True)
for gname, gcats in GROUPS.items():
    gr = r
    grp_rows.append(gr)
    put(wt, gr, 1, gname, BIG, fill=SUB_FILL)
    type_rows = []
    r += 1
    for cat in gcats:
        tr = r
        type_rows.append(tr)
        put(wt, tr, 1, "   " + CATS[cat], GREY_BOLD)
        crit = f'{C}$E$5:$E${C_LAST},$B$4,{C}$G$5:$G${C_LAST},"{cat}",{C}$C$5:$C${C_LAST},{cust_crit}'
        put(wt, tr, 9, f"=SUMIFS({C}$I$5:$I${C_LAST},{crit})", GREEN, PCS)
        put(wt, tr, 10, f'=IF(I{tr}>0,SUMIFS({C}$AD$5:$AD${C_LAST},{crit})/I{tr},"")', GREEN, PCT)
        put(wt, tr, 11, f"=SUMIFS({C}$AE$5:$AE${C_LAST},{crit})", GREEN, EUR)
        wt.row_dimensions[tr].outline_level = 1
        r += 1
        first = r
        for pn, _t in pn_rows:
            if PNCAT.get(pn) != cat:
                continue
            raw = str(pn_txt.get(pn, pn))
            if pn in bvp_set:
                kind, alt = "BVP", "Is BVP"
            elif raw[:4] in ("5876", "1876"):
                kind, alt = "BVP number, not in catalogue", "Is BVP"
            else:
                kind, alt = "Genuine", "Yes" if g2b.get(pn) else "No"
            put(wt, r, 1, "      " + raw)
            put(wt, r, 2, raw)
            put(wt, r, 3, desc.get(pn, ""))
            put(wt, r, 4, kind)
            put(wt, r, 5, alt)
            put(wt, r, 6, f'=SUMPRODUCT(--({PL}$A$6:$A${L_LAST}=B{r}),{PL}$S$6:$S${L_LAST})', fmt=PCS)
            put(wt, r, 7, f'=SUMPRODUCT(--({PL}$A$6:$A${L_LAST}=B{r}),{PL}$T$6:$T${L_LAST})', fmt=EUR)
            put(wt, r, 8, f'=IF(G{tr}>0,G{r}/G{tr},"")', fmt=PCT)
            put(wt, r, 12, part_check(desc.get(pn, "")))
            wt.row_dimensions[r].outline_level = 2
            wt.row_dimensions[r].hidden = True
            r += 1
        last_pn = r - 1
        if last_pn >= first:
            put(wt, tr, 6, f"=SUM(F{first}:F{last_pn})", GREY_BOLD, PCS)
            put(wt, tr, 7, f"=SUM(G{first}:G{last_pn})", GREY_BOLD, EUR)
        else:
            put(wt, tr, 6, 0, GREY_BOLD, PCS)
            put(wt, tr, 7, 0, GREY_BOLD, EUR)
        put(wt, tr, 8, f'=IF(G{gr}>0,G{tr}/G{gr},"")', fmt=PCT)
    put(wt, gr, 6, "=" + "+".join(f"F{t}" for t in type_rows), BIG, PCS, SUB_FILL)
    put(wt, gr, 7, "=" + "+".join(f"G{t}" for t in type_rows), BIG, EUR, SUB_FILL)
    put(wt, gr, 11, "=" + "+".join(f"K{t}" for t in type_rows), BIG, EUR, SUB_FILL)
    for cc_ in (2, 3, 4, 5, 8, 9, 10, 12):
        put(wt, gr, cc_, None, fill=SUB_FILL)
T_LAST = r - 1
put(wt, r + 1, 1, "All PMS parts", BIG, fill=SUB_FILL)
put(wt, r + 1, 7, "=" + "+".join(f"G{g}" for g in grp_rows), BIG, EUR, SUB_FILL)
put(wt, r + 1, 11, "=" + "+".join(f"K{g}" for g in grp_rows), BIG, EUR, SUB_FILL)
wt.conditional_formatting.add(f"J{TH + 1}:J{T_LAST}", ColorScaleRule(**RED_GREEN))
wt.conditional_formatting.add(f"E{TH + 1}:E{T_LAST}", FormulaRule(formula=[f'$E{TH + 1}="No"'], **DEVELOP))

# ----- sheet order -----
order = ["Read me", "Km assumptions", "Customer one-pager", "PMS tree", "Ranking", "Overview by country", "Coverage by customer", "Detail by truck family",
         "PMS parts list", "Genuine no BVP", "UIO", "Periods", "Check vs model"]
wb._sheets = [wb[n] for n in order]

# per-model km actually used under the default 'Per model' basis, for the Read me (the sheet itself is live)
def _default_km(c, m_):
    st = STATED.get((c, m_))
    if st:
        return st[0], "market-stated: " + st[1]
    wm = WARRANTY_MARKET.get(c)
    if wm in warr.index and warr.loc[wm].vins_cv_claims >= MIN_VINS:
        v_ = warr.loc[wm][{"N35": "km_yr_N35", "N75": "km_yr_N75", "F": "km_yr_F"}[m_]]
        if pd.notna(v_):
            return round(v_), f"measured, warranty odometers {wm} ({int(warr.loc[wm].vins_cv_claims)} claim VINs)"
    return (50_000 if c == "UTI" and m_ != "F" else 20_000), "default (not measured)"


assump_lines = []
for c in cust_order:
    bits = []
    for m_, lab_ in (("N35", "N35"), ("N75", "N75"), ("F", "F-series")):
        km_, src_ = _default_km(c, m_)
        bits.append(f"{lab_} {km_:,} km ({src_})")
    sh_ = share_file.get(c, (0, ""))[0]
    assump_lines.append(f"• {NAMES.get(c, c)}: " + "; ".join(bits) + f"; N35 share {sh_:.0%}.")

# ----- Read me -----
rd.column_dimensions["A"].width = 30
rd.column_dimensions["B"].width = 120
lines = [
    ("PMS coverage — truck (CV) customers by country, FY and calendar year", None),
    ("", None),
    ("What this is", "Expected PMS parts demand from trucks in service (UIO), against what ISZE billed, per customer, part and period. "
                     "Every expected figure is a live formula on the UIO, Km assumptions and Periods sheets."),
    ("Customers", "Every ISZE customer with trucks in service (N-series or F-series): " + ", ".join(f"{NAMES.get(c, c)} ({country[c]})" for c in cust_order)
                  + ". Denmark (1 truck) and pickup-only customers are not included."),
    ("ASSUMPTIONS (read first)", "Every expected figure rests on km assumptions PER TRUCK MODEL (N35 3.5 t, N75 7.5 t, F-series), chosen on 'Km assumptions'. "
                                 "Default = 'Per model': the market-stated figure where a market gave one, else measured warranty odometers (markets with 30+ claim VINs), "
                                 "else 20,000 km. Set both selectors on 'Km assumptions' to 'PMS model' to get exactly the published PMS coverage model.\n"
                                 "Km a year per truck under the default:\n" + "\n".join(assump_lines) + "\n"
                                 "Service intervals: N35 every 20,000 km, N75 every 40,000 km (Isuzu GIDSS), F-series 30,000 km (provisional). "
                                 "Israel N75 oil and fuel filter every 22,500 km (Isuzu GIDSS 'Engine oil (Israel)') — used under interval basis 'Per model', not in the PMS model. "
                                 "Isuzu Truck UK brake pads and shoes every 100,000 km on N75 (IML market-research slide 2026-07-14).\n"
                                 "Isuzu Truck UK: the 50,000 km a year that the IML deck uses is ITUK's figure for its N-series and was applied to all ITUK trucks, N35 included. "
                                 "It is not an N35 figure: the Apr 2026 trip report gives N35 11,576 miles (≈18,630 km) a year, warranty odometers give N35 12,891 and N75 35,478 km. "
                                 "The question to ITUK for a measured split is drafted, not sent.\n"
                                 "Every tool sheet shows the km and source used in red at the top or in its last column."),
    ("Formula", "Expected pieces = UIO (trucks) × km driven a year ÷ replacement interval km × months ÷ 12. N-series is split into N35 and N75 by the N35 share "
                "(an N35 is serviced every 20,000 km, an N75 every 40,000 km).   Coverage % = billed pieces ÷ expected pieces.   "
                "Gap € = (expected − billed pieces) × average billed price, never below zero."),
    ("Periods", f"FY2027 YTD (Apr 2026 – {ytd_end:%b %Y}, {ytd_months} months), FY2026 (Apr 2025 – Mar 2026), FY2025 (Apr 2024 – Mar 2025), CY2025, CY2024. "
                "Default everywhere is FY2026."),
    ("Tools", "Customer one-pager — pick customer, period and view: coverage, gap €, genuine vs BVP per part, action, and the top 10 genuine parts with no BVP.\n"
              "PMS tree — group › part › part number, expandable with + / −; pick customer and FY.\n"
              "Ranking — top 60 customer × part by gap €; filter by period, view, customer and part; action per line.\n"
              "Overview by country — all truck customers × all parts for one period.\n"
              "PMS parts list — every PMS part number billed, per customer and FY, with genuine/BVP and its BVP partner; filter and the totals follow.\n"
              "Km assumptions — km driven a year per customer, N35 share, and replacement interval in km per part (N35 / N75 / F-series). Change any km and the whole file follows."),
    ("Action labels", "Develop BVP: coverage under 80% and half or more of genuine € is on parts with no BVP alternative.  "
                      "Push existing BVP / price: BVP exists but is under 20% of €.  BVP selling — check price & availability: BVP already sells, coverage still low.  "
                      "Covered: 80%+.  Small: expected under €1,000.  Hardly billed — check demand assumption: billed under 3% of expected €; "
                      "the km interval is more likely wrong than the market gap is real (e.g. clutch booster, release bearing)."),
    ("Billed", "ISZE parts billing, genuine + BVP, credit notes and returns removed. Calendar years = the ISZE PMS coverage model figures. "
               "FY = rebuilt from the same billing with the model's own part list; 'Check vs model' compares the rebuild with the model on calendar years."),
    ("LOW / HIGH / AUTO", "Parts that fit more than one vehicle family, or have no vehicle reference, cannot be split between trucks and pickups. "
                          "LOW counts only truck-only parts; HIGH adds the shared and unreferenced parts. AUTO = HIGH for customers with 90%+ trucks "
                          "(Isuzu Truck UK, UTI), LOW for the rest."),
    ("Colours", "Blue on light yellow = input (change it and the file recalculates). Bright yellow = drop-down selector. Black = formula. Green = formula from another sheet."),
    ("Caveats", "1) Replacement intervals in km for air filter, brake pads, brake shoes, brake disc and all clutch parts (incl. booster and bearings) are provisional, not confirmed by IML — use gap € to rank, not to quote. "
                "Measured odometers come from warranty claims: young trucks (under 28 months) that had a claim, not a fleet survey. Benelux, Germany, Greece, Cyprus and Malta have no usable measurement and stay on 20,000 km.\n"
                "2) Isuzu Truck UK coverage here differs from the IML headline, which uses its own part scope. Do not use this file's Isuzu Truck UK figures with IML.\n"
                "3) Clutch disc and pressure plate are often replaced as a clutch kit, so their own coverage looks lower than reality.\n"
                "4) Some parts in the model's PMS part list are not wear parts (return springs, shim & clip kits, clutch shift blocks, ABS sensor rings) — the PMS parts list marks them under 'Check'. Brake disc follows the PMS model and includes ABS sensor rings ('ROTOR; SENSOR') and brake drums — overstates brake disc billed "
                "(Isuzu Truck UK about €87k in 2025).\n"
                "5) UTI's expected demand is driven by 50,000 km a year (confirmed) and, under the per-model interval basis, oil and fuel filters every 22,500 km. Check before quoting.\n"
                "6) Small truck fleets (Benelux, Greece, Cyprus) give unstable percentages.\n"
                "7) SAP customer 92 is I Motors Portugal (about €1.07M billed in 2025); it was missing from the customer mapping in git and is added in the FY figures."),
    ("Built", "2026-10-30 by 03_analytics/Isuzu/pms-pilot/build_cv_pms_coverage_workbook.py from the verified PMS files (data check green 2026-09-24) "
              f"and ISZE billing up to {last:%d %b %Y}."),
]
for i, (k, v) in enumerate(lines, 1):
    a_ = rd.cell(row=i, column=1, value=k)
    a_.font = TITLE if i == 1 else BOLD
    a_.alignment = Alignment(vertical="top")
    if v:
        b_ = rd.cell(row=i, column=2, value=v)
        b_.font = BLACK
        b_.alignment = Alignment(wrap_text=True, vertical="top")
        rd.row_dimensions[i].height = min(409, 15 * (v.count("\n") + 1 + len(v) // 130))
rd.freeze_panes = "A2"

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
    if (ws.column_dimensions["B"].width or 0) < 28:
        ws.column_dimensions["B"].width = 28
for ws, r0, r1, c1 in ((wk2, 8, 67, 15), (w1, 8, T1, 12), (w1, TB + 2, TB + 11, 8)):
    for row in ws.iter_rows(min_row=r0, max_row=r1, min_col=1, max_col=c1):
        for cell in row:
            if cell.value is not None:
                cell.alignment = Alignment(wrap_text=True, vertical="center")
w1.column_dimensions["G"].width = 20
wk2.column_dimensions["A"].width = 11
wb.active = 1
wb.save(OUT)
print(OUT, "| billing to", last.date(), "| FY2027 YTD months", ytd_months)
