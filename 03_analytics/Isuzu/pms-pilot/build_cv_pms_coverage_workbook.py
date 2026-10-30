"""Build the simple CV PMS coverage workbook: truck customers by country, FY2025 and FY2026.

Agreed standard = the PMS coverage model (network lane): pieces needed = vehicles in service x km a year / replacement
interval km for the whole fleet (N-series split N35 / N75, F-series, D-Max), against everything billed. 20,000 km a year,
UTI N-series 50,000 km; ITUK brakes 100,000 km. Isuzu Truck UK's IML service schedule (Model B, decision 2026-07-02) is
shown as a fixed reference for IML / ITUK use. FY billed is rebuilt from sales_fact.parquet with the model's own part
list and tagging; FY2026 pieces needed equal the model's CY2025 expected demand (same UIO year).

Tabs: Overview per country, Customer one-pager, PMS coverage (expandable group > part > part number),
Ranking, Part numbers, Assumptions, UIO, Calculation. Earlier versions are in git history.

Run:  python build_cv_pms_coverage_workbook.py [output.xlsx]   then recalculate before reading values.
Rebuild notes: pms_capture_supplement.csv is not in git (part type read from the description for those parts);
SAP sold-to 92 is mapped to I Motors Portugal; brake disc includes ABS sensor rings, as in the PMS model.
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
OUT = Path(__file__).resolve().parent / (sys.argv[1] if len(sys.argv) > 1 else "ISZE_CV_PMS_Coverage_standard_2026-10-30.xlsx")

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
    ("FY2026", "FY", "2025-04-01", "2026-04-01", 12, 2025, "Rebuilt from billing", None),
    ("FY2025", "FY", "2024-04-01", "2025-04-01", 12, 2024, "Rebuilt from billing", None),
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

# ======================= workbook (simple version) =======================
from openpyxl.worksheet.properties import Outline  # noqa: E402

GROUPS = {"Filters": ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter"],
          "Brakes": ["brake_pad", "brake_shoe", "brake_rotor"],
          "Clutch": ["clutch_kit", "clutch_disc", "clutch_pressure_plate", "release_bearing", "pilot_bearing", "clutch_booster"]}
GROUP_OF = {c: g for g, cs in GROUPS.items() for c in cs}
UIO_YEAR = {"FY2025": 2024, "FY2026": 2025}
SVC_KM = {"N35": 20_000, "N75": 40_000, "F": 30_000, "L": 20_000}
GEN_KM = 20_000
# Inside the agreed PMS network model, UTI's N-series runs 50,000 km a year (confirmed). Nothing else deviates.
KM_N = {"UTI": (50_000, "50,000 km a year, confirmed by Jerome 2026-07-10 (IML CV study) — in the PMS model")}
NAME_TO_CODE = {NAMES.get(c, c): c for c in cust_order}
PER = ["FY2025", "FY2026"]
PLIST = '"FY2025,FY2026"'
MODEL_B = [("Oil filter", "35.1%", 140_602), ("Fuel filter", "65.1%", 127_440), ("Air filter", "13.2%", 736_037),
           ("Clutch", "7.8%", 392_559), ("Brake", "35.3%", 641_833)]

wb = Workbook()
rd = wb.active
rd.title = "Read me"

# ---------- Lists (hidden helper) ----------
wls = wb.create_sheet("Lists")
wls["A1"] = "All"
for i, c in enumerate(cust_order):
    wls.cell(row=2 + i, column=1, value=country[c])
    wls.cell(row=1 + i, column=2, value=NAMES.get(c, c))
    wls.cell(row=1 + i, column=3, value=c)
wls["D1"] = "All"
for i, (_, lab) in enumerate(CATS.items()):
    wls.cell(row=2 + i, column=4, value=lab)
NC = len(cust_order)
COUNTRY_LIST = f"Lists!$A$1:$A${NC + 1}"
CUST_LIST = f"Lists!$B$1:$B${NC}"
PART_LIST = f"Lists!$D$1:$D${len(CATS) + 1}"
wls.sheet_state = "hidden"
wls.freeze_panes = "A2"
wls.column_dimensions["B"].width = 30

# ---------- Assumptions (km) ----------
wa = wb.create_sheet("Assumptions")
text(wa, 1, 1, "Assumptions — the agreed PMS coverage standard, in kilometres", TITLE)
text(wa, 2, 1, "Parts needed a year = vehicles in service × km driven a year ÷ replacement interval km — for the whole fleet: N-series and F-series trucks AND D-Max. "
               "Coverage = everything billed ÷ that need. Blue cells are inputs.")
header(wa, 4, ["General", "Value", "Based on"], [44, 14, 110], freeze=False, filt=False)
gen_rows = [("Km driven a year per vehicle — all customers", GEN_KM, "PMS coverage model (network standard). Not measured. Only exception: UTI N-series 50,000 km (table below)."),
            ("Service interval N35 (NLR, 3.5 t, RZ4E)", SVC_KM["N35"], "Isuzu service schedule GIDSS N_MY24 (NLR87) / Duncan deck slide 14"),
            ("Service interval N75 (NPR, 7.5 t, 4HK1)", SVC_KM["N75"], "Isuzu service schedule GIDSS N_MY24 (NPR75) / Duncan deck slide 14"),
            ("Service interval F-series", SVC_KM["F"], "Isuzu Truck UK service book — provisional"),
            ("Service interval D-Max", SVC_KM["L"], "D-Max owner's handbook (20,000 km / 24 months)")]
for i, (a_, b_, c_) in enumerate(gen_rows):
    put(wa, 5 + i, 1, a_, BOLD if i == 0 else BLACK)
    put(wa, 5 + i, 2, b_, BLUE, PCS, IN_FILL)
    put(wa, 5 + i, 3, c_)

CK0 = 13
text(wa, CK0 - 2, 1, "Km driven a year per vehicle, per customer", BIG)
header(wa, CK0 - 1, ["Customer", "Customer code", "Country", "N35 share of N-series", "Km a year — N-series", "Km a year — F-series", "Km a year — D-Max", "Based on"],
       freeze=False, filt=False)
for i, c in enumerate(cust_order):
    rr_ = CK0 + i
    v = float(visits.get((c, "n_series_truck"), 0.5))
    share = 0.0 if c == "UTI" else max(0.0, round(v / 0.5 - 1, 4))
    put(wa, rr_, 1, NAMES.get(c, c), BOLD if c in KM_N else BLACK)
    put(wa, rr_, 2, c)
    put(wa, rr_, 3, country[c])
    put(wa, rr_, 4, share, BLUE, PCT, IN_FILL)
    if c in KM_N:
        put(wa, rr_, 5, KM_N[c][0], BLUE, PCS, IN_FILL)
    else:
        put(wa, rr_, 5, "=$B$5", GREEN, PCS)
    put(wa, rr_, 6, "=$B$5", GREEN, PCS)
    put(wa, rr_, 7, "=$B$5", GREEN, PCS)
    note = (KM_N[c][1] + "; F-series and D-Max 20,000 km.") if c in KM_N else "20,000 km a year (PMS model, not measured)."
    note += f" N35 share {share:.0%} (PMS model; an N35 is serviced every 20,000 km, an N75 every 40,000 km)."
    if c == "ITUK":
        note += " For IML / ITUK use the IML service schedule (Model B) figures below, not this row."
    put(wa, rr_, 8, note)
CK1 = CK0 + NC - 1
for col, w in zip("ABCDEFGHI", [44, 14, 14, 11, 12, 12, 12, 12, 100]):
    wa.column_dimensions[col].width = w

PI0 = CK1 + 4
text(wa, PI0 - 2, 1, "Replacement interval per part (km)", BIG)
header(wa, PI0 - 1, ["Part", "Part code", "Group", "N35 km", "N75 km", "F-series km", "D-Max km", "Every … N75 services", "Based on"], freeze=False, filt=False)
ibasis = {"oil_filter": "Every service — Isuzu GIDSS.", "fuel_filter": "Every service — Isuzu GIDSS.",
          "air_filter": "Every 2nd service — PMS model, provisional.", "blower_filter": "Every service — PMS model (Jerome 2026-07-26).",
          "urea_filter": "Isuzu GIDSS: 200,000 km N-series (NPR75), 80,000 km F-series (4HK1-TCH).",
          "brake_pad": "Every 2nd service (D-Max 50,000 km) — PMS model, not confirmed by IML.",
          "brake_shoe": "Every 2nd service — PMS model, not confirmed by IML.", "brake_rotor": "Every 2nd pad change — PMS model, provisional."}
non_ituk = rates.drop("ITUK", level=0, errors="ignore")
lcv_rates = pubfam[(pubfam.family == "light_vehicle") & (pubfam.distributor_code != "ITUK")].groupby("pms_category").category_factor.agg(lambda x: x.mode().iloc[0])
for i, (cat, lab) in enumerate(CATS.items()):
    rr_ = PI0 + i
    fN = non_ituk.xs((cat, "n_series_truck"), level=(1, 2)).mode().iloc[0]
    fF = non_ituk.xs((cat, "heavy_truck"), level=(1, 2)).mode().iloc[0]
    fL = float(lcv_rates.get(cat, fN))
    put(wa, rr_, 1, lab)
    put(wa, rr_, 2, cat)
    put(wa, rr_, 3, GROUP_OF[cat])
    put(wa, rr_, 4, round(SVC_KM["N35"] / fN), BLUE, PCS, IN_FILL)
    put(wa, rr_, 5, round(SVC_KM["N75"] / fN), BLUE, PCS, IN_FILL)
    put(wa, rr_, 6, round(SVC_KM["F"] / fF), BLUE, PCS, IN_FILL)
    put(wa, rr_, 7, round(SVC_KM["L"] / fL), BLUE, PCS, IN_FILL)
    put(wa, rr_, 8, f"=E{rr_}/$B$7", fmt="0.0")
    put(wa, rr_, 9, ibasis.get(cat, "PMS model assumption, not confirmed by IML."))
PI1 = PI0 + len(CATS) - 1

OI0 = PI1 + 4
text(wa, OI0 - 2, 1, "Customer-specific replacement intervals (in the PMS model)", BIG)
header(wa, OI0 - 1, ["Customer", "Key", "Part code", "N35 km", "N75 km", "F-series km", "D-Max km", "", "Based on"], freeze=False, filt=False)
OVR = [("ITUK", "brake_pad", 50_000, 100_000, 75_000, None, "IML market-research slide 2026-07-14: brakes every 100,000 km on N75, front and rear together (in the PMS model)."),
       ("ITUK", "brake_shoe", 50_000, 100_000, 75_000, None, "Same IML slide (in the PMS model).")]
for i, (c, cat, a_, b_, f_, l_, src_) in enumerate(OVR):
    rr_ = OI0 + i
    put(wa, rr_, 1, NAMES.get(c, c))
    put(wa, rr_, 2, f"{c}|{cat}")
    put(wa, rr_, 3, cat)
    for j, v_ in enumerate((a_, b_, f_, l_)):
        put(wa, rr_, 4 + j, v_, BLUE, PCS, IN_FILL)
    put(wa, rr_, 9, src_)
OI1 = OI0 + len(OVR) - 1

MB0 = OI1 + 4
text(wa, MB0 - 2, 1, "Isuzu Truck UK — IML service schedule (Model B), the agreed standard for IML / ITUK (decision 2 Jul 2026)", BIG)
header(wa, MB0 - 1, ["Category (CY2025, ISZE → ITUK)", "Cover", "Gap €", "", "", "", "", "", "Basis"], freeze=False, filt=False)
for i, (lab, cov, gap) in enumerate(MODEL_B):
    rr_ = MB0 + i
    put(wa, rr_, 1, lab)
    put(wa, rr_, 2, cov)
    put(wa, rr_, 3, gap, fmt=EUR)
put(wa, MB0, 9, "UIO 22,389 (full DVLA, Mar 2026) · 50,000 km a year for all ITUK trucks · oil, fuel, air filter every 40,000 km (1.25 a year) · "
                "clutch and brake 0.5 a year · 100% addressable · own part scope (v7 workbook). Total gap €2,038,471, weighted cover 35.9%.")
put(wa, MB0 + 1, 9, "Source: FACTS.md §1 / iml_v7_ituk_cy2025.yaml. Fixed figures — not recalculated in this file. Use these with IML and ITUK; "
                    "use the rest of this file for comparing customers.")
MB1 = MB0 + len(MODEL_B) - 1
put(wa, MB1 + 1, 1, "Total (5 categories)", BOLD)
put(wa, MB1 + 1, 2, "35.9%", BOLD)
put(wa, MB1 + 1, 3, 2_038_471, BOLD, EUR)

NT0 = MB1 + 4
text(wa, NT0, 1, "Not used, on purpose", BIG)
for i, t in enumerate([
        "• Isuzu GIDSS 'or every 12 months, whichever comes first': not applied — km only, as in the PMS model.",
        "• Odometer readings from warranty claims: not used (they show km driven, not whether a filter was changed).",
        "• Example: oil filter N75 every 40,000 km at 20,000 km a year → 0.5 filters a truck a year; D-Max every 20,000 km → 1.0 a year."]):
    text(wa, NT0 + 1 + i, 1, t)
wa.freeze_panes = "A4"
A = "Assumptions!"

# ---------- UIO ----------
wu = wb.create_sheet("UIO")
text(wu, 1, 1, "Vehicles in service (UIO) per customer", TITLE)
text(wu, 2, 1, "Source: Isuzu UIO Overview 2026 (by market and model type). FY2025 uses the 2024 count, FY2026 the 2025 count. Blue = input.")
header(wu, 4, ["Key", "Customer", "Country", "UIO year", "N-series trucks", "F-series trucks", "Trucks total", "D-Max", "Truck share of fleet"],
       [16, 28, 15, 9, 12, 12, 12, 12, 11])
r = 5
for c in cust_order:
    for y in (2024, 2025):
        p = piv.loc[(c, y)] if (c, y) in piv.index else None
        put(wu, r, 1, f"{c}|{y}")
        put(wu, r, 2, NAMES.get(c, c))
        put(wu, r, 3, country[c])
        put(wu, r, 4, y)
        put(wu, r, 5, float(p.LD + p.MD) if p is not None else 0, BLUE, PCS, IN_FILL)
        put(wu, r, 6, float(p["F-Series"]) if p is not None else 0, BLUE, PCS, IN_FILL)
        put(wu, r, 7, f"=E{r}+F{r}", fmt=PCS)
        put(wu, r, 8, float(p.LCV) if p is not None else 0, BLUE, PCS, IN_FILL)
        put(wu, r, 9, f"=IFERROR(G{r}/(G{r}+H{r}),0)", fmt=PCT)
        r += 1
U1 = r - 1


def uio(col, key_expr):
    return f"INDEX(UIO!${col}$5:${col}${U1},MATCH({key_expr},UIO!$A$5:$A${U1},0))"


# ---------- Calculation (one row per customer x FY x part) ----------
wc = wb.create_sheet("Calculation")
text(wc, 1, 1, "Calculation — PMS need vs billed, per customer, FY and part (whole fleet: trucks and D-Max)", TITLE)
text(wc, 2, 1, "Pieces needed = N-series × (N35 share × km ÷ interval N35 + N75 share × km ÷ interval N75) + F-series × km ÷ interval F + D-Max × km ÷ interval D-Max. "
               "Billed = every PMS part billed to the customer. This is the PMS coverage model's method.")
ccols = ["Key", "Customer code", "Customer", "Country", "FY", "Part", "Part code", "Group", "N-series trucks", "F-series trucks", "D-Max",
         "N35 share", "Km N-series", "Km F-series", "Km D-Max", "Interval N35", "Interval N75", "Interval F", "Pieces needed",
         "Interval D-Max", "Billed pieces (all)", "Billed pieces counted", "Average price €",
         "Expected €", "Coverage %", "Gap €", "Genuine €", "BVP €", "BVP share of €", "Genuine € with no BVP", "No-BVP share of genuine €",
         "Action", "Rank helper"]
header(wc, 4, ccols, [24, 10, 26, 13, 8, 20, 18, 9, 9, 9, 9, 8, 9, 9, 9, 9, 9, 9, 10, 9, 10, 10, 9, 11, 9, 11, 11, 11, 9, 11, 9, 30, 9])
asp_p = {}
for (d, k, c_, f_), (q_, e_) in agg.items():
    a0 = asp_p.setdefault((d, k, c_), [0.0, 0.0])
    a0[0] += q_
    a0[1] += e_
r = 5
RKS = "Ranking!"


def ivl(model_col, ovr_col, r):
    gen = f"INDEX({A}${model_col}${PI0}:${model_col}${PI1},MATCH(G{r},{A}$B${PI0}:$B${PI1},0))"
    ov = f"INDEX({A}${ovr_col}${OI0}:${ovr_col}${OI1},MATCH(B{r}&\"|\"&G{r},{A}$B${OI0}:$B${OI1},0))"
    return f"IFERROR(IF(N({ov})>0,{ov},{gen}),{gen})"


for c in cust_order:
    for k in PER:
        for cat, lab in CATS.items():
            allq = asp_p.get((c, k, cat), (0.0, 0.0))[0]
            q_, e_ = asp_p.get((c, k, cat), (0.0, 0.0))
            asp = e_ / q_ if q_ > 0 else asp_cust.get((c, cat), asp_net.get(cat))
            mx = mix.get((c, k, cat), dict(gen_eur=0, bvp_eur=0, nobvp_eur=0))
            key = f'B{r}&"|"&{UIO_YEAR[k]}'
            ck = f"MATCH(B{r},{A}$B${CK0}:$B${CK1},0)"
            put(wc, r, 1, f"{c}|{k}|{cat}")
            put(wc, r, 2, c)
            put(wc, r, 3, NAMES.get(c, c))
            put(wc, r, 4, country[c])
            put(wc, r, 5, k)
            put(wc, r, 6, lab)
            put(wc, r, 7, cat)
            put(wc, r, 8, GROUP_OF[cat])
            put(wc, r, 9, "=" + uio("E", key), GREEN, PCS)
            put(wc, r, 10, "=" + uio("F", key), GREEN, PCS)
            put(wc, r, 11, "=" + uio("H", key), GREEN, PCS)
            put(wc, r, 12, f"=INDEX({A}$D${CK0}:$D${CK1},{ck})", GREEN, PCT)
            put(wc, r, 13, f"=INDEX({A}$E${CK0}:$E${CK1},{ck})", GREEN, PCS)
            put(wc, r, 14, f"=INDEX({A}$F${CK0}:$F${CK1},{ck})", GREEN, PCS)
            put(wc, r, 15, f"=INDEX({A}$G${CK0}:$G${CK1},{ck})", GREEN, PCS)
            put(wc, r, 16, "=" + ivl("D", "D", r), GREEN, PCS)
            put(wc, r, 17, "=" + ivl("E", "E", r), GREEN, PCS)
            put(wc, r, 18, "=" + ivl("F", "F", r), GREEN, PCS)
            put(wc, r, 19, f"=I{r}*(L{r}*M{r}/P{r}+(1-L{r})*M{r}/Q{r})+J{r}*N{r}/R{r}+K{r}*O{r}/T{r}", fmt=PCS)
            put(wc, r, 20, "=" + ivl("G", "G", r), GREEN, PCS)
            put(wc, r, 21, allq, BLUE, PCS, IN_FILL)
            put(wc, r, 22, f"=U{r}", fmt=PCS)
            put(wc, r, 23, round(float(asp), 4) if asp else None, BLUE, EUR2, IN_FILL)
            put(wc, r, 24, f"=S{r}*N(W{r})", fmt=EUR)
            put(wc, r, 25, f'=IF(S{r}>0,V{r}/S{r},"")', fmt=PCT)
            put(wc, r, 26, f"=MAX(0,S{r}-V{r})*N(W{r})", fmt=EUR)
            put(wc, r, 27, float(mx["gen_eur"]), BLUE, EUR, IN_FILL)
            put(wc, r, 28, float(mx["bvp_eur"]), BLUE, EUR, IN_FILL)
            put(wc, r, 29, f'=IF(AA{r}+AB{r}>0,AB{r}/(AA{r}+AB{r}),"")', fmt=PCT)
            put(wc, r, 30, float(mx["nobvp_eur"]), BLUE, EUR, IN_FILL)
            put(wc, r, 31, f'=IF(AA{r}>0,AD{r}/AA{r},"")', fmt=PCT)
            put(wc, r, 32, action(f"X{r}", f"Y{r}", f"AA{r}", f"AB{r}", f"AC{r}", f"AE{r}"))
            put(wc, r, 33, f'=IF(AND(E{r}={RKS}$B$3,OR({RKS}$B$4="All",{RKS}$B$4=D{r}),OR({RKS}$D$4="All",{RKS}$D$4=F{r})),Z{r}+ROW()/1000000,-1)',
                fmt="0.00", fill=GREY)
            r += 1
C1 = r - 1
C = "Calculation!"
wc.conditional_formatting.add(f"Y5:Y{C1}", ColorScaleRule(**RED_GREEN))
wc.cell(row=4, column=23).comment = Comment("Billed € ÷ billed pieces for this customer, part and FY (whole customer); if nothing billed, the customer's average "
                                            "for the part, else the network average.", "ISZE")
ACTION_NOTE = ("Small: expected under €1,000. Covered: coverage 80%+. Hardly billed: billed under 3% of expected € — check the km interval first. "
               "Develop BVP: half or more of genuine € is on parts with no BVP. Push existing BVP / price: BVP exists but under 20% of €. "
               "Otherwise BVP already sells: look at price and availability.")
wc.cell(row=4, column=32).comment = Comment(ACTION_NOTE, "ISZE")


def km_line(code_ref):
    ck = f"MATCH({code_ref},{A}$B${CK0}:$B${CK1},0)"
    return ('"Agreed standard (PMS coverage model). Km a year: N-series "&TEXT(INDEX(' + f"{A}$E${CK0}:$E${CK1},{ck}" + '),"#,##0")&" · F-series "&TEXT(INDEX('
            + f"{A}$F${CK0}:$F${CK1},{ck}" + '),"#,##0")&" · D-Max "&TEXT(INDEX(' + f"{A}$G${CK0}:$G${CK1},{ck}"
            + '),"#,##0")&" — "&INDEX(' + f"{A}$H${CK0}:$H${CK1},{ck}" + ')')


# ---------- Part numbers ----------
wl = wb.create_sheet("Part numbers")
text(wl, 1, 1, "PMS part numbers billed to the truck customers — per customer, FY2025 and FY2026", TITLE)
text(wl, 2, 1, "Genuine and BVP, credit notes and returns removed. Whole customer (trucks and D-Max). Use the filters; the totals row follows them.")
lcols = ["Part number", "Description", "Part", "Group", "Genuine / BVP", "BVP alternative?", "BVP / genuine partner", "Fits", "Country", "Customer", "Check",
         "FY2025 pieces", "FY2025 €", "FY2026 pieces", "FY2026 €", "FY2026 average price €", "Tree: pieces", "Tree: €"]
header(wl, 5, lcols, [13, 32, 20, 9, 16, 11, 24, 22, 13, 26, 30, 10, 12, 10, 12, 11, 10, 11])
g2b, b2g = {}, {}
for r_ in cx.itertuples():
    g2b.setdefault(norm(r_.genuine_pn), set()).add(r_.bvp_pn)
    b2g.setdefault(norm(r_.bvp_pn), set()).add(r_.genuine_pn)
per_ = {k_: (st_, en_) for k_, _t, st_, en_, *_ in PERIODS}
lx = s[s.distributor_code.isin(cv_codes) & (s.bd >= per_["FY2025"][0]) & (s.bd < per_["FY2026"][1])].copy()
lx["fy"] = "FY2025"
lx.loc[lx.bd >= per_["FY2026"][0], "fy"] = "FY2026"
lg = lx.groupby(["pn", "distributor_code", "fy"]).agg(pcs=("billed_qty", "sum"), eur=("net_sales_value", "sum")).unstack("fy").fillna(0)
pn_txt = s.groupby("pn").part_number.first()
pn26 = lx[lx.fy == "FY2026"].groupby("pn").net_sales_value.sum()
pn_all = lx.groupby("pn").net_sales_value.sum()
famlab = {**FAMILIES, "light_vehicle": "Pickup (D-Max)", "shared_across_families": "Fits more than one family", "unattributed": "No vehicle reference"}


def kind_of(pn):
    raw = str(pn_txt.get(pn, pn))
    if pn in bvp_set:
        return raw, "BVP", "Is BVP", ", ".join(sorted(b2g.get(pn, [])))
    if raw[:4] in ("5876", "1876"):
        return raw, "BVP number, not in catalogue", "Is BVP", ""
    prt = sorted(g2b.get(pn, []))
    return raw, "Genuine", "Yes" if prt else "No", ", ".join(prt)


order_pn = sorted(lg.index.get_level_values(0).unique(), key=lambda p: (-pn26.get(p, 0.0), -pn_all.get(p, 0.0)))
TS = "'PMS coverage'!"
r = 6
for pn in order_pn:
    raw, kind, alt, partner = kind_of(pn)
    sub = lg.loc[pn]
    for d in sorted(sub.index, key=lambda d: -sub.loc[d][("eur", "FY2026")] if ("eur", "FY2026") in sub.columns else 0):
        row = sub.loc[d]
        put(wl, r, 1, raw)
        put(wl, r, 2, desc.get(pn, ""))
        put(wl, r, 3, CATS.get(PNCAT.get(pn), PNCAT.get(pn)))
        put(wl, r, 4, GROUP_OF.get(PNCAT.get(pn), ""))
        put(wl, r, 5, kind)
        put(wl, r, 6, alt)
        put(wl, r, 7, partner)
        put(wl, r, 8, famlab.get(pn_fam.get(pn) or pn_res.get(pn), "Fits more than one family"))
        put(wl, r, 9, country[d])
        put(wl, r, 10, NAMES.get(d, d))
        put(wl, r, 11, part_check(desc.get(pn, "")))
        for j, f_ in enumerate(PER):
            put(wl, r, 12 + 2 * j, float(row.get(("pcs", f_), 0.0)), BLUE, PCS)
            put(wl, r, 13 + 2 * j, float(row.get(("eur", f_), 0.0)), BLUE, EUR)
        put(wl, r, 16, f'=IF(N{r}>0,O{r}/N{r},"")', fmt=EUR2)
        sel = f'OR({TS}$B$3="All",{TS}$B$3=I{r})'
        put(wl, r, 17, f'=IF({sel},IF({TS}$B$4="FY2025",L{r},N{r}),0)', fmt=PCS, fill=GREY)
        put(wl, r, 18, f'=IF({sel},IF({TS}$B$4="FY2025",M{r},O{r}),0)', fmt=EUR, fill=GREY)
        r += 1
L1 = r - 1
text(wl, 4, 11, "Total of visible rows", BOLD)
for ci in range(12, 16):
    col = get_column_letter(ci)
    put(wl, 4, ci, f"=SUBTOTAL(9,{col}6:{col}{L1})", BOLD, PCS if ci % 2 == 0 else EUR, SUB_FILL)
wl.auto_filter.ref = f"A5:P{L1}"
wl.freeze_panes = "B6"
wl.conditional_formatting.add(f"F6:F{L1}", FormulaRule(formula=['$F6="No"'], **DEVELOP))
wl.conditional_formatting.add(f"K6:K{L1}", FormulaRule(formula=['$K6<>""'], fill=PatternFill("solid", fgColor="FCE4D6")))
PL = "'Part numbers'!"

# ---------- PMS coverage tree ----------
wt = wb.create_sheet("PMS coverage")
text(wt, 1, 1, "PMS coverage — group › part › part number (click + / − on the left, or the 1 2 3 buttons top left)", TITLE)
TC = selector(wt, 3, 1, "Country", "All", COUNTRY_LIST)
TP = selector(wt, 4, 1, "FY", "FY2026", PLIST)
text(wt, 3, 4, "Coverage = everything billed ÷ pieces the whole fleet needs (trucks and D-Max, Assumptions tab).", NOTE)
put(wt, 5, 1, f'=IF($B$3="All","Agreed standard (PMS coverage model): whole fleet — trucks and D-Max — at 20,000 km a year (UTI N-series 50,000). For IML / ITUK use the IML service schedule (Model B) — see Assumptions.",'
              + km_line(f'INDEX(Lists!$C$1:$C${NC},MATCH($B$3,Lists!$A$2:$A${NC + 1},0))') + ")", Font(name=F, size=10, bold=True, color="C00000"), box=False)
TH = 7
header(wt, TH, ["Group › part › part number", "Part number", "Description", "Genuine / BVP", "BVP alternative?", "Pieces needed (trucks + D-Max)",
                "Billed pieces", "Coverage %", "Billed €", "Share of part €", "Gap €", "Check"],
       [34, 13, 32, 16, 11, 12, 11, 10, 13, 9, 13, 30], freeze=False, filt=False)
wt.freeze_panes = f"B{TH + 1}"
wt.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=False)
ccrit = 'IF($B$3="All","*",$B$3)'
r = TH + 1
grp_rows = []
for gname, gcats in GROUPS.items():
    gr = r
    grp_rows.append(gr)
    put(wt, gr, 1, gname, BIG, fill=SUB_FILL)
    r += 1
    trs = []
    for cat in gcats:
        tr = r
        trs.append(tr)
        crit = f'{C}$E$5:$E${C1},$B$4,{C}$G$5:$G${C1},"{cat}",{C}$D$5:$D${C1},{ccrit}'
        put(wt, tr, 1, "   " + CATS[cat], BOLD)
        put(wt, tr, 6, f"=SUMIFS({C}$S$5:$S${C1},{crit})", GREEN, PCS)
        put(wt, tr, 7, f"=SUMIFS({C}$V$5:$V${C1},{crit})", GREEN, PCS)
        put(wt, tr, 8, f'=IF(F{tr}>0,G{tr}/F{tr},"")', fmt=PCT)
        put(wt, tr, 11, f"=SUMIFS({C}$Z$5:$Z${C1},{crit})", GREEN, EUR)
        wt.row_dimensions[tr].outline_level = 1
        r += 1
        first = r
        for pn in order_pn:
            if PNCAT.get(pn) != cat:
                continue
            raw, kind, alt, _p = kind_of(pn)
            put(wt, r, 1, "      " + raw)
            put(wt, r, 2, raw)
            put(wt, r, 3, desc.get(pn, ""))
            put(wt, r, 4, kind)
            put(wt, r, 5, alt)
            put(wt, r, 7, f"=SUMPRODUCT(--({PL}$A$6:$A${L1}=B{r}),{PL}$Q$6:$Q${L1})", fmt=PCS)
            put(wt, r, 9, f"=SUMPRODUCT(--({PL}$A$6:$A${L1}=B{r}),{PL}$R$6:$R${L1})", fmt=EUR)
            put(wt, r, 10, f'=IF(I{tr}>0,I{r}/I{tr},"")', fmt=PCT)
            put(wt, r, 12, part_check(desc.get(pn, "")))
            wt.row_dimensions[r].outline_level = 2
            wt.row_dimensions[r].hidden = True
            r += 1
        put(wt, tr, 9, f"=SUM(I{first}:I{r - 1})" if r > first else 0, BOLD, EUR)
    put(wt, gr, 9, "=" + "+".join(f"I{t}" for t in trs), BIG, EUR, SUB_FILL)
    put(wt, gr, 11, "=" + "+".join(f"K{t}" for t in trs), BIG, EUR, SUB_FILL)
    for cc_ in (2, 3, 4, 5, 6, 7, 8, 10, 12):
        put(wt, gr, cc_, None, fill=SUB_FILL)
    for t in trs:
        put(wt, t, 10, f'=IF(I{gr}>0,I{t}/I{gr},"")', fmt=PCT)
T1 = r - 1
put(wt, r + 1, 1, "All PMS parts", BIG, fill=SUB_FILL)
put(wt, r + 1, 9, "=" + "+".join(f"I{g}" for g in grp_rows), BIG, EUR, SUB_FILL)
put(wt, r + 1, 11, "=" + "+".join(f"K{g}" for g in grp_rows), BIG, EUR, SUB_FILL)
wt.conditional_formatting.add(f"H{TH + 1}:H{T1}", ColorScaleRule(**RED_GREEN))
wt.conditional_formatting.add(f"E{TH + 1}:E{T1}", FormulaRule(formula=[f'$E{TH + 1}="No"'], **DEVELOP))

# ---------- Overview per country ----------
wo = wb.create_sheet("Overview per country")
text(wo, 1, 1, "PMS coverage per country — all parts", TITLE)
OP = selector(wo, 3, 1, "FY", "FY2026", PLIST)
text(wo, 4, 1, "Agreed standard (PMS coverage model): whole fleet — trucks and D-Max — at 20,000 km a year (UTI N-series 50,000). For IML / ITUK use the IML service schedule (Model B) — see Assumptions.", Font(name=F, size=10, bold=True, color="C00000"))
cats = list(CATS.items())
header(wo, 6, ["Country", "Customer", "Trucks + D-Max in service"] + [lab for _, lab in cats] + ["Expected €", "Gap €"],
       [15, 28, 11] + [10] * len(cats) + [13, 13], freeze=False, filt=False)
wo.freeze_panes = "C7"
r = 7
for c in cust_order:
    put(wo, r, 1, country[c])
    put(wo, r, 2, NAMES.get(c, c))
    put(wo, r, 3, "=" + uio("G", f'"{c}|"&IF({OP}="FY2025",2024,2025)') + "+" + uio("H", f'"{c}|"&IF({OP}="FY2025",2024,2025)'), GREEN, PCS)
    for j, (cat, lab) in enumerate(cats):
        crit = f'{C}$B$5:$B${C1},"{c}",{C}$E$5:$E${C1},{OP},{C}$G$5:$G${C1},"{cat}"'
        put(wo, r, 4 + j, f'=IFERROR(SUMIFS({C}$V$5:$V${C1},{crit})/SUMIFS({C}$S$5:$S${C1},{crit}),"")', GREEN, PCT)
    critc = f'{C}$B$5:$B${C1},"{c}",{C}$E$5:$E${C1},{OP}'
    put(wo, r, 4 + len(cats), f"=SUMIFS({C}$X$5:$X${C1},{critc})", GREEN, EUR)
    put(wo, r, 5 + len(cats), f"=SUMIFS({C}$Z$5:$Z${C1},{critc})", GREEN, EUR)
    r += 1
put(wo, r, 1, "All customers", BOLD, fill=SUB_FILL)
put(wo, r, 2, "", BOLD, fill=SUB_FILL)
put(wo, r, 3, f"=SUM(C7:C{r - 1})", BOLD, PCS, SUB_FILL)
for j, (cat, lab) in enumerate(cats):
    crit = f'{C}$E$5:$E${C1},{OP},{C}$G$5:$G${C1},"{cat}"'
    put(wo, r, 4 + j, f'=IFERROR(SUMIFS({C}$V$5:$V${C1},{crit})/SUMIFS({C}$S$5:$S${C1},{crit}),"")', BOLD, PCT, SUB_FILL)
for cc_ in (4 + len(cats), 5 + len(cats)):
    col = get_column_letter(cc_)
    put(wo, r, cc_, f"=SUM({col}7:{col}{r - 1})", BOLD, EUR, SUB_FILL)
wo.conditional_formatting.add(f"D7:{get_column_letter(3 + len(cats))}{r}", ColorScaleRule(**RED_GREEN))
for row in wo.iter_rows(min_row=7, max_row=r, min_col=3, max_col=5 + len(cats)):
    for cell in row:
        cell.alignment = Alignment(horizontal="right", wrap_text=True)
text(wo, r + 2, 1, "Above 100% is possible: parts also go to vehicles outside the truck count (for mixed customers, pickups using the same part).", NOTE)

# ---------- Customer one-pager ----------
w1 = wb.create_sheet("Customer one-pager")
text(w1, 1, 1, "Customer one-pager — PMS coverage, gap and BVP", TITLE)
CU = selector(w1, 3, 1, "Customer", NAMES["ITUK"], CUST_LIST)
PP = selector(w1, 4, 1, "FY", "FY2026", PLIST)
CODE = f"INDEX(Lists!$C$1:$C${NC},MATCH({CU},{CUST_LIST},0))"
text(w1, 3, 4, "Country", BOLD)
put(w1, 3, 5, f"=INDEX(Lists!$A$2:$A${NC + 1},MATCH({CU},{CUST_LIST},0))", GREEN)
text(w1, 4, 4, "Trucks + D-Max in service", BOLD)
put(w1, 4, 5, "=" + uio("G", f'{CODE}&"|"&IF({PP}="FY2025",2024,2025)') + "+" + uio("H", f'{CODE}&"|"&IF({PP}="FY2025",2024,2025)'), GREEN, PCS)
text(w1, 3, 7, "Truck share of fleet", BOLD)
put(w1, 3, 8, "=" + uio("I", f'{CODE}&"|"&IF({PP}="FY2025",2024,2025)'), GREEN, PCT)
put(w1, 5, 1, "=" + km_line(CODE), Font(name=F, size=10, bold=True, color="C00000"), box=False)
header(w1, 7, ["Part", "Pieces needed", "Billed pieces", "Coverage %", "Gap €", "Expected €", "Genuine €", "BVP €", "BVP share of €",
               "Genuine € with no BVP", "No-BVP share", "Action"], [24, 12, 12, 10, 12, 12, 12, 12, 10, 12, 10, 36], freeze=False, filt=False)
w1.column_dimensions["B"].width = 28
w1.column_dimensions["G"].width = 20
for i, (cat, lab) in enumerate(cats):
    r = 8 + i
    mt = f'MATCH({CODE}&"|"&{PP}&"|"&"{cat}",{C}$A$5:$A${C1},0)'
    g = lambda col, mt=mt: f"INDEX({C}${col}$5:${col}${C1},{mt})"  # noqa: E731
    put(w1, r, 1, lab)
    put(w1, r, 2, f"={g('S')}", GREEN, PCS)
    put(w1, r, 3, f"={g('V')}", GREEN, PCS)
    put(w1, r, 4, f'=IF(B{r}>0,C{r}/B{r},"")', fmt=PCT)
    put(w1, r, 5, f"={g('Z')}", GREEN, EUR)
    put(w1, r, 6, f"={g('X')}", GREEN, EUR)
    put(w1, r, 7, f"={g('AA')}", GREEN, EUR)
    put(w1, r, 8, f"={g('AB')}", GREEN, EUR)
    put(w1, r, 9, f'=IF(G{r}+H{r}>0,H{r}/(G{r}+H{r}),"")', fmt=PCT)
    put(w1, r, 10, f"={g('AD')}", GREEN, EUR)
    put(w1, r, 11, f'=IF(G{r}>0,J{r}/G{r},"")', fmt=PCT)
    put(w1, r, 12, f"={g('AF')}", GREEN)
T_ = 8 + len(cats)
put(w1, T_, 1, "All PMS parts (€)", BOLD, fill=SUB_FILL)
for ci in range(2, 13):
    col = get_column_letter(ci)
    if col in "EFGHJ":
        put(w1, T_, ci, f"=SUM({col}8:{col}{T_ - 1})", BOLD, EUR, SUB_FILL)
    elif col == "I":
        put(w1, T_, ci, f'=IF(G{T_}+H{T_}>0,H{T_}/(G{T_}+H{T_}),"")', BOLD, PCT, SUB_FILL)
    elif col == "K":
        put(w1, T_, ci, f'=IF(G{T_}>0,J{T_}/G{T_},"")', BOLD, PCT, SUB_FILL)
    else:
        put(w1, T_, ci, "", BOLD, fill=SUB_FILL)
w1.conditional_formatting.add(f"D8:D{T_ - 1}", ColorScaleRule(**RED_GREEN))
w1.conditional_formatting.add(f"L8:L{T_ - 1}", FormulaRule(formula=['$L8="Develop BVP"'], **DEVELOP))
w1.cell(row=7, column=12).comment = Comment(ACTION_NOTE, "ISZE")
TB = T_ + 3
text(w1, TB, 1, "Top 10 genuine PMS parts with no BVP alternative (this customer and FY)", BIG)
header(w1, TB + 1, ["#", "Part", "Part number", "Description", "Fits", "Billed pieces", "Billed €", "Average price €"], freeze=False, filt=False)
NB0 = 1
wls["F1"] = "key"
rows_nb = []
for _, x in nobvp[nobvp.period.isin(PER) & (nobvp["rank"] <= 10)].iterrows():
    rows_nb.append((f"{NAMES.get(x.distributor_code, x.distributor_code)}|{x.period}|{int(x['rank'])}", CATS.get(x["cat"], x["cat"]),
                    str(pn_txt.get(x.pn, x.pn)), x.desc, famlab.get(x.fam, "No vehicle reference"), float(x.pcs), float(x.eur)))
for i, rw in enumerate(rows_nb):
    for j, v in enumerate(rw):
        wls.cell(row=2 + i, column=6 + j, value=v)
NBL = 1 + len(rows_nb)
for k in range(1, 11):
    r = TB + 1 + k
    mt = f'MATCH({CU}&"|"&{PP}&"|"&{k},Lists!$F$2:$F${NBL},0)'
    put(w1, r, 1, k)
    for col, src, fmt in [(2, "G", None), (3, "H", None), (4, "I", None), (5, "J", None), (6, "K", PCS), (7, "L", EUR)]:
        put(w1, r, col, f'=IFERROR(INDEX(Lists!${src}$2:${src}${NBL},{mt}),"")', fmt=fmt)
    put(w1, r, 8, f'=IFERROR(G{r}/F{r},"")', fmt=EUR2)
w1.column_dimensions["D"].width = 30
w1.freeze_panes = "A7"

# ---------- Ranking ----------
wk2 = wb.create_sheet("Ranking")
text(wk2, 1, 1, "Ranking — customer × part by gap €", TITLE)
selector(wk2, 3, 1, "FY", "FY2026", PLIST)
selector(wk2, 4, 1, "Country", "All", COUNTRY_LIST)
selector(wk2, 4, 3, "Part", "All", PART_LIST)
text(wk2, 5, 1, "Top 40 by gap €. " + "Agreed standard (PMS coverage model): whole fleet — trucks and D-Max — at 20,000 km a year (UTI N-series 50,000). For IML / ITUK use the IML service schedule (Model B) — see Assumptions.",
     Font(name=F, size=10, bold=True, color="C00000"))
header(wk2, 7, ["Rank", "Country", "Customer", "Part", "Pieces needed", "Coverage %", "Gap €", "Genuine €", "BVP €", "BVP share of €",
                "Genuine € with no BVP", "Action"], [11, 15, 28, 22, 11, 10, 12, 12, 12, 10, 12, 36], freeze=False, filt=False)
wk2.freeze_panes = "A8"
wk2.cell(row=7, column=12).comment = Comment(ACTION_NOTE, "ISZE")
SORT = f"{C}$AG$5:$AG${C1}"
for k in range(1, 41):
    r = 7 + k
    m = f"MATCH(LARGE({SORT},{k}),{SORT},0)"
    ok = f"LARGE({SORT},{k})>0"
    put(wk2, r, 1, f'=IF({ok},{k},"")')
    for col, src, fmt in [(2, "D", None), (3, "C", None), (4, "F", None), (5, "S", PCS), (6, "Y", PCT), (7, "Z", EUR),
                          (8, "AA", EUR), (9, "AB", EUR), (10, "AC", PCT), (11, "AD", EUR), (12, "AF", None)]:
        put(wk2, r, col, f'=IF({ok},INDEX({C}${src}$5:${src}${C1},{m}),"")', fmt=fmt)
wk2.conditional_formatting.add("F8:F47", ColorScaleRule(**RED_GREEN))
wk2.conditional_formatting.add("L8:L47", FormulaRule(formula=['$L8="Develop BVP"'], **DEVELOP))

# ---------- Read me ----------
rd.column_dimensions["A"].width = 26
rd.column_dimensions["B"].width = 120
lines = [
    ("PMS coverage — customers with trucks (whole fleet)", None),
    ("", None),
    ("What it shows", "How many PMS parts the vehicles in service need a year (trucks and D-Max, from the km they drive), against everything ISZE billed. Per country, customer, part and part number. FY2025 and FY2026."),
    ("Tabs", "Overview per country — all countries × all parts, coverage % and gap €.\n"
             "Customer one-pager — pick a customer: coverage, gap €, genuine vs BVP per part, action, top 10 genuine parts with no BVP.\n"
             "PMS coverage — expandable: Filters › Oil filter › part number. Pick a country (or All) and the FY.\n"
             "Ranking — biggest gaps first, filter by FY, country and part.\n"
             "Part numbers — every PMS part number billed, per customer, with genuine/BVP and its BVP partner.\n"
             "Assumptions — the km per customer and truck model, the replacement interval per part, and what each number is based on.\n"
             "UIO and Calculation — the inputs and the arithmetic."),
    ("Formula", "Pieces needed = vehicles × km a year ÷ replacement interval km, for N-series (split N35 / N75), F-series and D-Max.  Coverage = everything billed ÷ pieces needed.  "
                "Gap € = missing pieces × the average price billed."),
    ("Standard", "The agreed PMS coverage standard (the PMS coverage model, network lane): 20,000 km a year for every vehicle, UTI N-series 50,000 km (confirmed); "
                 "intervals from the Isuzu GIDSS service schedule where it exists, otherwise the model's assumption; Isuzu Truck UK brakes every 100,000 km. "
                 "FY2026 pieces needed are exactly the model's figures. Full list with sources on the Assumptions tab.\n"
                 "Isuzu Truck UK with IML / ITUK: use the IML service schedule (Model B, agreed 2 Jul 2026): oil filter 35.1%, gap €2.04M (CY2025) — on the Assumptions tab. "
                 "That standard uses 22,389 trucks at 50,000 km a year and its own part scope, so it differs from this file's ITUK row."),
    ("Billed", "ISZE parts billing, genuine + BVP, credit notes and returns removed — everything billed per customer, because the need includes D-Max. "
               "FY figures are rebuilt from the billing with the model's own part list."),
    ("Actions", ACTION_NOTE),
    ("Watch out", "• Brake, clutch and air-filter intervals are provisional, not confirmed by IML — use gap € to rank, not to quote.\n"
                  "• Isuzu Truck UK with IML / ITUK: use the IML service schedule (Model B) figures on the Assumptions tab, not this file's ITUK row.\n"
                  "• The PMS part list contains some non-wear parts (return springs, ABS sensor rings counted as brake discs) — marked 'Check' on Part numbers.\n"
                  "• Small truck fleets (Benelux, Greece, Cyprus) give unstable percentages.\n"
                  "• SAP customer 92 is I Motors Portugal; it was missing from the customer mapping in git and is included here."),
    ("Built", f"2026-10-30 by 03_analytics/Isuzu/pms-pilot/build_cv_pms_coverage_workbook.py, ISZE billing up to {last:%d %b %Y}."),
]
for i, (k, v) in enumerate(lines, 1):
    a_ = rd.cell(row=i, column=1, value=k)
    a_.font = TITLE if i == 1 else BOLD
    a_.alignment = Alignment(vertical="top")
    if v:
        b_ = rd.cell(row=i, column=2, value=v)
        b_.font = BLACK
        b_.alignment = Alignment(wrap_text=True, vertical="top")
        rd.row_dimensions[i].height = 15 * (v.count("\n") + 1 + len(v) // 130)

rd.freeze_panes = "A2"
order = ["Read me", "Overview per country", "Customer one-pager", "PMS coverage", "Ranking", "Part numbers", "Assumptions", "UIO", "Calculation", "Lists"]
wb._sheets = [wb[n] for n in order]
for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
    if ws.title != "Lists" and (ws.column_dimensions["B"].width or 0) < 28:
        ws.column_dimensions["B"].width = 28
for ws, r0, r1, c1 in ((wk2, 8, 47, 12), (w1, 8, T_, 12), (w1, TB + 2, TB + 11, 8)):
    for row in ws.iter_rows(min_row=r0, max_row=r1, min_col=1, max_col=c1):
        for cell in row:
            if cell.value is not None:
                cell.alignment = Alignment(wrap_text=True, vertical="center")
wb.active = 1
wb.save(OUT)
print(OUT, "| billing to", last.date())
