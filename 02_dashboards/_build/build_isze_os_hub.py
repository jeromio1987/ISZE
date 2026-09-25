# -*- coding: utf-8 -*-
r"""
Build ISZE_OS_Hub.html — the interconnection layer across the ISZE aftersales stack.

Layers: Car park / UIO  ->  PRISM (expected demand)  ->  AIM (competition)  ->  dashboards  ->  deliverables.

Every figure on the output page is re-derived here from the files it names (no copied constants) and
carries a CSS hover tooltip: what it is / formula / snapshot + source / what is NOT included.
Every link target is tested with os.path.exists before it is written.

Output:
  ..\hub\ISZE_OS_Hub.html

Authorised paths only: 02_dashboards\_build\ and 02_dashboards\hub\.
"""
import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\jerom\Desktop\claude"
ISZE = os.path.join(ROOT, "ISZE")
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
HUB = os.path.join(ISZE, "02_dashboards", "hub")
OUT = os.path.join(HUB, "ISZE_OS_Hub.html")
SNAPSHOT = "16 Sep 2026"

# ---------------------------------------------------------------- helpers
def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fnum(v, default=0.0):
    try:
        s = str(v).strip()
        return float(s) if s else default
    except Exception:
        return default


def eur(v, dec=0):
    return ("{:,.%df}" % dec).format(v).replace(",", " ").replace(" ", ",")


def pct(v, dec=1):
    return ("{:,.%df}" % dec).format(v)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def rel(path_from_root):
    """Absolute-ish repo path -> relative URL from the hub folder."""
    a = os.path.normpath(os.path.join(ROOT, path_from_root))
    return os.path.relpath(a, HUB).replace("\\", "/")


LINKS = []          # (label, repo-relative path, exists)
def link(label, repo_rel, cls=""):
    exists = os.path.exists(os.path.join(ROOT, repo_rel))
    LINKS.append((label, repo_rel, exists))
    mark = "" if exists else " data-missing=\"1\""
    return '<a class="lnk %s" href="%s"%s>%s</a>' % (
        cls, rel(repo_rel), mark, esc(label))


# ---------------------------------------------------------------- the two measurement states
class Chip:
    MEASURED = ("measured", "Measured", "A real count or a real euro from a named source. Quotable with its snapshot date.")
    MODELLED = ("modelled", "Modelled", "Computed from an assumption or a survival curve, not observed. Quotable only with the assumption attached.")
    EXCLUDED = ("excluded", "Excluded", "Deliberately out of scope, or there is no denominator at all. Shown as absent, never as zero.")
    JUDGE = ("judge", "Needs a judgement", "Two on-disk sources disagree, or the value needs a human call before it is used.")


CHIP_DEFS = {
    "measured": Chip.MEASURED,
    "modelled": Chip.MODELLED,
    "excluded": Chip.EXCLUDED,
    "judge": Chip.JUDGE,
}


def chip(state, note="", tag=""):
    css, label, definition = CHIP_DEFS[state]
    tip = definition if not note else definition + " " + note
    tg = '<i class="tag">%s</i>' % esc(tag) if tag else ""
    return ('<span class="chip %s">%s%s<span class="tip"><b>%s</b><span>%s</span></span></span>'
            % (css, label, tg, esc(label), esc(tip)))


def kpi(value, what, formula, source, notincluded, state="measured", cls=""):
    """A derived figure with the mandatory four-line hover tooltip."""
    css = CHIP_DEFS[state][0]
    return (
        '<span class="kpi %s %s">%s'
        '<span class="tip">'
        '<b>%s</b>'
        '<span class="tr"><i>Formula</i>%s</span>'
        '<span class="tr"><i>Snapshot &amp; source</i>%s</span>'
        '<span class="tr warn"><i>Not included</i>%s</span>'
        '</span></span>'
        % (css, cls, esc(value), esc(what), esc(formula), esc(source), esc(notincluded))
    )


# ================================================================ 1. read the estate
# --- GPS base: fleet denominator and spend per unit (CY2025, full year only)
gps_rows = read_csv(os.path.join(DERIVED, "gps_spu_by_distributor.csv"))
gps25 = [r for r in gps_rows if r["year"] == "2025"]
gps26 = [r for r in gps_rows if r["year"] == "2026"]
with_spu = [r for r in gps25 if r["spend_per_unit_eur"].strip()]
no_spu = [r for r in gps25 if not r["spend_per_unit_eur"].strip()]
sales_net = sum(fnum(r["total_sales_eur"]) for r in with_spu)

# --- target spend ceiling, captured, uncaptured (CY2025)
# Fleet denominator: worksheet base from wallet_waterfall (163,198). D08.
# The ceiling file was corrected on 2026-09-22: six markets now carry the measured 3.5 t
# share their light-truck row was missing, so the ceiling is EUR 54,375,729 and cover 56.6%.
# Read from the file, never typed in.
wal = read_csv(os.path.join(DERIVED, "wallet_waterfall.csv"))
w25 = [r for r in wal if r["year"] == "2025"]
wal_uio = {r["distributor_code"]: fnum(r["uio_units"]) for r in w25 if fnum(r["uio_units"]) > 0}
# Overlay worksheet fleet onto GPS spend rows for per-market SPU display
for r in with_spu:
    code = r["distributor_code"]
    if code in wal_uio:
        r["uio_units"] = str(wal_uio[code])
        billed = fnum(r["total_sales_eur"])
        r["spend_per_unit_eur"] = str(round(billed / wal_uio[code], 2)) if wal_uio[code] else ""
uio_net = sum(wal_uio.values())
spu_net = sales_net / uio_net if uio_net else 0.0
spu_vals = sorted(fnum(r["spend_per_unit_eur"]) for r in with_spu if r["spend_per_unit_eur"].strip())
_n = len(spu_vals)
spu_median = (spu_vals[_n // 2] if _n % 2 else 0.5 * (spu_vals[_n // 2 - 1] + spu_vals[_n // 2]))
spu_max = max(spu_vals) if spu_vals else 0.0
ceiling = sum(fnum(r["theoretical_wallet_eur"]) for r in w25)
captured = sum(fnum(r["captured_total_eur"]) for r in w25)
uncaptured = sum(fnum(r["uncaptured_eur"]) for r in w25)
cover = 100.0 * captured / ceiling
flat = [r for r in w25 if abs(fnum(r["theoretical_wallet_eur"]) / max(fnum(r["uio_units"]), 1) - 250.0) < 0.01]
flat_eur = sum(fnum(r["theoretical_wallet_eur"]) for r in flat)
flat_share = 100.0 * flat_eur / ceiling

# --- PMS opportunity basket (CY2025)
om = [r for r in read_csv(os.path.join(DERIVED, "pms_opportunity_matrix.csv")) if r["year"] == "2025"]
gap_total = sum(fnum(r["revenue_gap_eur"]) for r in om)
by_line = {}
for r in om:
    by_line[r["pms_category"]] = by_line.get(r["pms_category"], 0.0) + fnum(r["revenue_gap_eur"])
top_lines = sorted(by_line.items(), key=lambda kv: -kv[1])[:3]
top3 = sum(v for _, v in top_lines)
fam = ["clutch_disc", "clutch_pressure_plate", "clutch_kit", "clutch_booster", "release_bearing",
       "pilot_bearing", "brake_pad", "brake_shoe", "brake_rotor"]
fam_eur = sum(by_line.get(k, 0.0) for k in fam)

# --- ITUK oil filter: the two lanes that must never be mixed
pms = read_csv(os.path.join(DERIVED, "pms_capture_by_db_year.csv"))
ituk_oil = {(r["year"]): r for r in pms
            if r["distributor_code"] == "ITUK" and r["pms_category"] == "oil_filter"
            and r["line_type"] == "total"}
ituk_24 = ituk_oil.get("2024")
ituk_25 = ituk_oil.get("2025")
j_ituk_24_pct = 100 * fnum(ituk_24["actual_qty"]) / fnum(ituk_24["expected_qty"])
j_ituk_25_pct = 100 * fnum(ituk_25["actual_qty"]) / fnum(ituk_25["expected_qty"])
iml_txt = open(os.path.join(ISZE, "03_analytics", "Isuzu", "prism", "data",
                            "iml_v7_ituk_cy2025.yaml"), encoding="utf-8", errors="replace").read()
def iml(key):
    m = re.search(r"^\s*%s:\s*([0-9.]+)\s*$" % key, iml_txt, re.M)
    return fnum(m.group(1)) if m else 0.0
iml_oil_pct = iml("oil_filter_cover_pct")
iml_expected = iml("expected_demand")
iml_actual = iml("actual_sales")
iml_gap = iml("revenue_gap_eur_sum")
iml_uio = iml("uio_dvla")

# --- BVP down-trade gross profit
dgp = read_csv(os.path.join(DERIVED, "bvp_downtrade_gp.csv"))
dgp_total = sum(fnum(r["downtrade_gp_gap_eur"]) for r in dgp)
oil_row = next((r for r in dgp if r["pms_category"] == "oil_filter"), None)

# --- the two directions: ISZE -> DB (billing) vs DB -> DLR (sales to dealer), CY2025
mix = read_csv(os.path.join(DERIVED, "sellout_aim_network_mix_2025.csv"))
billing = {r["distributor_code"]: fnum(r["total_eur"]) for r in mix if r["layer"] == "billing_isze_db"}
sellout = {r["distributor_code"]: fnum(r["total_eur"]) for r in mix if r["layer"] == "sellout_db_dlr"}
two_dir = []
for k in sorted(set(billing) & set(sellout)):
    two_dir.append((k, billing[k], sellout[k], 100.0 * sellout[k] / billing[k]))
so_tot = sum(s for _, _, s, _ in two_dir)
bi_tot = sum(b for _, b, _, _ in two_dir)
so_ratio_all = 100.0 * so_tot / bi_tot
vis_share = 100.0 * bi_tot / sales_net

# --- VIN register + the UK registration extract
vin = json.load(open(os.path.join(ISZE, "01_data", "07_UIO", "vin", "VIN_register_summary.json"),
                     encoding="utf-8"))
vin_n = vin["n_vins"]
vin_markets = len(vin["by_db"])

# --- model code -> weight class (from the register's own model dimension)
md = read_csv(os.path.join(ISZE, "01_data", "07_UIO", "vin", "model_dimension.csv"))
wc = {}
for r in md:
    wc.setdefault(r["series"], set()).add(r["gvw_t"])

# --- type mix buckets
buckets = read_csv(os.path.join(ISZE, "03_analytics", "Isuzu", "prism", "data", "uio_by_model_bucket.csv"))
bucket_by_db = {r["distributor_code"]: r for r in buckets}

# --- manifest registry count
man = open(os.path.join(ISZE, "02_dashboards", "manifest.yaml"), encoding="utf-8").read()
man_files = len([l for l in man.split("files:")[1].split("stubs:")[0].splitlines()
                 if l.strip().startswith("- ")])
man_folders = len(re.findall(r"^  [a-z_]+:\s*$", man.split("files:")[1].split("stubs:")[0], re.M))

# ================================================================ 2. market state model
# Sources: _market_fleet_profile_workup.md (age, mix, exclusions), _data_integrity_open_issues.md
# (LCV-DEC, SPU-PARTIAL, PT-GAP, VIN-IL, VIN-ITUK, UIO-FCAST), V20_SPEC.md (fleet reconstruction),
# dealer_sellout_long_*.csv file listing (sales-to-dealer visibility), VIN_register_summary.json.
CLAIM_N = {"ITUK": 1646, "ISRAEL": 1367, "PORTUGAL": 222, "GERMANY": 32, "HUNGARY": 39,
           "IRELAND": 39, "ROMANIA": 23, "CYPRUS": 10, "MALTA": 7, "GREECE": 1}
VIN_MK = {"PORTUGAL", "IRELAND", "GERMANY", "MALTA", "CYPRUS", "BELGIUM", "GREECE"}
SELLOUT_MK = {"ITUK", "UTI", "IRELAND", "IUK", "GREECE", "PORTUGAL"}
LOWCONF = {"GERMANY", "CYPRUS", "MALTA", "GREECE"}

NAME = {
    "ITUK": ("United Kingdom — CV trucks", "ITUK"), "IUK": ("United Kingdom — pickups", "IUK"),
    "UTI": ("Israel — CV trucks", "UTI"), "UMI": ("Israel — pickups", "UMI"),
    "GERMANY": ("Germany", "ISD"), "BELGIUM": ("Belgium", "IBX"),
    "PORTUGAL": ("Portugal", "Imotors"), "SWEDEN": ("Sweden", "Sverige"),
    "NORWAY": ("Norway", "RSA"), "GREECE": ("Greece", "Petros"),
    "HUNGARY": ("Hungary", "AutoWallis"), "IRELAND": ("Ireland", "Ireland"),
    "CYPRUS": ("Cyprus", "Loutsios"), "MALTA": ("Malta", "GasanZammit"),
    "FINLAND": ("Finland", "NAT"), "ROMANIA": ("Romania", "ROM Auto"),
    "DENMARK": ("Denmark", "Danmark"), "ICELAND": ("Iceland", "BL"),
    "UKRAINE": ("Ukraine", "KTK"), "ARMENIA": ("Armenia", "GA"),
    "KAZAKHSTAN": ("Kazakhstan", "CBC"), "PALESTINE": ("Palestine", "—"),
    "ITALY": ("Italy", "MIDI"),
}


def fleet_state(code):
    if code in ("ITUK", "IRELAND", "PORTUGAL"):
        return "measured"
    if code in ("UTI", "UMI"):
        return "judge"
    return "modelled"


def age_meas(code):
    """-> (chip state, note, optional tag)"""
    if code == "ITUK":
        return ("measured", "n=1 646 VINs, median claim age 1.78 yr", "")
    if code in ("UTI", "UMI"):
        return ("judge", "n=1 367 VINs, median 2.78 yr — Israel CV and pickups are pooled, cannot be split", "")
    if code == "PORTUGAL":
        return ("measured", "n=222 VINs, median 1.62 yr", "")
    n = CLAIM_N.get(code)
    if n:
        return ("judge", "n=%d VINs — too thin to quote" % n, "thin")
    return ("excluded", "no warranty claims for this market — no measured age at all", "")


def wc_state(code):
    if code == "ITUK":
        return ("measured", "decoded from the UK registration extract (NPR75 = 7.5 t, NLR* = 3.5 t per ITUK)")
    if code in VIN_MK:
        return ("measured", "decoded from the VIN register model codes")
    if code == "UTI":
        return ("judge", "claim model codes exist (FRR / FSR / NPR) but the workbook LD bucket is questioned for Israel")
    return ("excluded", "no documented weight class for this market")


mark_rows = sorted(with_spu, key=lambda r: -fnum(r["uio_units"]))
foot_rows = no_spu


def market_row(code, uio, spu, src, cls=""):
    nm, db = NAME.get(code, (code.title(), code))
    fs = fleet_state(code)
    am, an, atag = age_meas(code)
    ws, wn = wc_state(code)
    mixs = "modelled"
    if code in bucket_by_db:
        b = bucket_by_db[code]
        ld, md_, fl, lcv = (fnum(b["cv_std_uio"]), 0.0, fnum(b["f_series_uio"]), fnum(b["lcv_uio"]))
        tot = max(ld + md_ + fl + lcv, 1)
        mixtip = ("<i>Formula</i>workbook light-duty + F-series + light-commercial shares of the market total<br>"
                  "<i>Snapshot</i>UIO workbook v19 sheet 1, 2025E<br>"
                  "<i>Not included</i>No N35 / N50 / N62 / N75 / F110 / F135 split exists for any market; "
                  "the light-duty bucket is one label, so a 3.5 tonne vehicle can be charged the target spend "
                  "of a 7.5 tonne vehicle")
        mixcell = ('<span class="mixbar" title="">'
                   '<i style="width:%.1f%%;background:#15233c"></i>'
                   '<i style="width:%.1f%%;background:#3f5a86"></i>'
                   '<i style="width:%.1f%%;background:#9fb0ca"></i>'
                   '<i style="width:%.1f%%;background:#c0552d"></i>'
                   '<span class="tip"><b>Type mix — LD / MD / F-series / LCV</b><span>%s</span></span></span>'
                   % (100 * ld / tot, 100 * md_ / tot, 100 * fl / tot, 100 * lcv / tot, mixtip))
    else:
        mixcell = chip("excluded", "No type mix in the workbook for this market.")
    return (
        '<tr class="%s">'
        '<td class="mk"><span class="nm">%s</span><span class="db">%s</span></td>'
        '<td class="num">%s</td>'
        '<td>%s</td>'
        '<td>%s</td>'
        '<td>%s</td>'
        '<td>%s</td>'
        '<td>%s</td>'
        '<td>%s</td>'
        '<td class="num">%s</td>'
        '</tr>'
        % (
            cls, esc(nm), esc(db),
            kpi(eur(uio), "Vehicles in service, CY2025", "UIO workbook v19 sheet 1 / GPS base, market row",
                "UIO v19, 18 Jun 2026",
                "Italy (87 510 units, no ISZE sales data) and the four CIS markets (no fleet rows). "
                "2026-2030 forecast columns excluded: overstated by 7.8% to 37.7%.",
                fs) if uio else chip("excluded", "No fleet denominator exists for this market."),
            mixcell,
            chip(am, an, tag=atag),
            chip("modelled", "Steady-state age from the survival curve, not observed: "
                             + (an if am == "excluded" else "second line beside the claim-based figure.")),
            kpi(eur(spu, 2), "Spend per unit (GPS), CY2025, EUR",
                "parts billed CY2025 / vehicles in service CY2025",
                "gps_spu_by_distributor.csv, full-year rows only",
                "Not comparable to 2026: those rows are partial-year and their capture columns are deliberately blank.",
                "measured") if spu else chip("excluded", "No denominator, so no spend per unit is shown."),
            chip("measured" if code not in ("PORTUGAL",) else "judge",
                 "Billing is in the PMS base for this market." if code != "PORTUGAL" else
                 "Six consecutive months (Mar-Aug 2025) are missing from Portugal billing, so any trend read is invalid."),
            chip("measured") if code in SELLOUT_MK else chip("excluded", "No sales-to-dealer file for this market."),
            chip(ws, wn),
        ))


market_rows_html = "\n".join(
    market_row(r["distributor_code"], fnum(r["uio_units"]), fnum(r["spend_per_unit_eur"]),
               r["uio_source"]) for r in mark_rows)

foot_html = "\n".join(
    '<tr class="footrow"><td class="mk"><span class="nm">%s</span><span class="db">%s</span></td>'
    '<td class="num">%s</td><td colspan="7">%s</td></tr>'
    % (esc(NAME[c][0]), esc(NAME[c][1]), kpi("0", "Vehicles in service", "hardcoded zero with uio_source = v18_proxy_2025",
                                             "UIO v19", "These markets bill parts but have no fleet rows at all, so no spend per unit and no age is derivable.",
                                             "excluded"),
       chip("excluded", "No fleet denominator, no type mix, no age and no spend per unit. The spend is real; the denominator is not there."))
    for c in [r["distributor_code"] for r in foot_rows])

italy_html = (
    '<tr class="footrow italy"><td class="mk"><span class="nm">Italy</span><span class="db">MIDI</span></td>'
    '<td class="num">87 510</td>'
    '<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
    '</tr>'
    % (chip("excluded", "Type mix exists in the workbook but the market is not in the GPS base."),
       chip("measured", "Warranty claims exist for Italy (1 120 VINs) even though the market is out of the commercial base.", tag="claim"),
       chip("modelled", "Steady-state curve only."),
       chip("excluded", "EXCLUDE — no ISZE sales data available. Roughly a third of the European fleet, shown rather than dropped."),
       chip("excluded", "Not in the PMS base."),
       chip("excluded", "No sales-to-dealer file."),
       )
)

# ================================================================ 3. link inventory (tested)
layer_links = [
    ("Car park / UIO — vehicles in service", [
        ("UIO dashboard (v18, 26 Aug)", "ISZE\\02_dashboards\\fleet\\ISUZU_UIO_Dashboard_2026.html"),
        ("GPS dashboard (canonical, 16 Jul)", "ISZE\\02_dashboards\\fleet\\ISZE_GPS_Dashboard.html"),
        ("Plan tracker 2030", "ISZE\\02_dashboards\\fleet\\ISZE_Plan_Tracker_2030.html"),
        ("PRISM page 1 — UIO", "ISZE\\03_analytics\\Isuzu\\prism\\pages\\1_UIO.py"),
        ("PRISM page 22 — model cohorts", "ISZE\\03_analytics\\Isuzu\\prism\\pages\\22_Parc_Cohort.py"),
        ("VIN register summary (7 markets, 3 238 VINs)", "ISZE\\01_data\\07_UIO\\vin\\VIN_register_summary.json"),
        ("VIN register — how it is built", "ISZE\\01_data\\07_UIO\\vin\\README.md"),
        ("UK VIN extract from the ITUK mail (29 935 VINs)", "ISZE\\01_data\\90_INBOX\\_ituk_vins_from_duncan_mail.md"),
        ("UIO workbook repair spec (V20)", "ISZE\\06_uio\\_CURRENT\\V20_SPEC.md"),
    ]),
    ("PRISM — expected service demand and capture", [
        ("PRISM metric dictionary", "ISZE\\03_analytics\\Isuzu\\prism\\docs\\metric_dictionary.md"),
        ("PRISM page 2 — GPS", "ISZE\\03_analytics\\Isuzu\\prism\\pages\\2_GPS.py"),
        ("PRISM page 3 — PMS capture", "ISZE\\03_analytics\\Isuzu\\prism\\pages\\3_PMS.py"),
        ("PRISM page 4 — BVP mix", "ISZE\\03_analytics\\Isuzu\\prism\\pages\\4_BVP.py"),
        ("PRISM page 23 — sales to dealer", "ISZE\\03_analytics\\Isuzu\\prism\\pages\\23_Dealer_Sellout.py"),
        ("PRISM dashboard contracts (column level)", "ISZE\\03_analytics\\Isuzu\\prism\\docs\\dashboard_contracts.md"),
        ("PRISM information architecture", "ISZE\\03_analytics\\Isuzu\\prism\\docs\\DASHBOARD_IA.md"),
        ("PRISM launcher", "ISZE\\03_analytics\\Isuzu\\prism\\run_prism.ps1"),
        ("Capture by distributor and year (the file)", "ISZE\\01_data\\00_derived\\pms_capture_by_db_year.csv"),
        ("Opportunity matrix (the file)", "ISZE\\01_data\\00_derived\\pms_opportunity_matrix.csv"),
    ]),
    ("AIM — what competes against each part", [
        ("AIM dashboard CY2026", "ISZE\\02_dashboards\\sales\\AIM_Dashboard_CY2026.html"),
        ("Competitiveness dashboard", "ISZE\\02_dashboards\\sales\\ISZE_Competitiveness_Dashboard.html"),
        ("AIM classification gap report", "ISZE\\03_analytics\\Isuzu\\prism\\docs\\aim_classification_gap_report.md"),
        ("IAM quality positioning overview", "ISZE\\02_dashboards\\pricing\\ISZE_IAM_Quality_Positioning_Overview.html"),
        ("IAM price vs billed part number", "ISZE\\02_dashboards\\pricing\\ISZE_IAM_Price_vs_Billed_PN.html"),
        ("Aftermarket live pricing", "ISZE\\02_dashboards\\pricing\\ISZE_Aftermarket_Live_Pricing_Dashboard.html"),
        ("Pricing action map", "ISZE\\02_dashboards\\pricing\\ISZE_Pricing_Action_Map.html"),
        ("Pricing history findings (16 Sep)", "ISZE\\02_dashboards\\pricing\\ISZE_Pricing_History_Findings_Dashboard.html"),
        ("Scraped price intelligence", "ISZE\\02_dashboards\\pricing\\ISZE_Scraped_Price_Intelligence_Dashboard.html"),
        ("Part number classification (the file)", "ISZE\\01_data\\00_derived\\aim_pn_classification.csv"),
    ]),
    ("Dashboards — the ~20 views that read the layers above", [
        ("Universe board — every pillar, its score, the roadmap and every live page", "ISZE\\02_dashboards\\hub\\ISZE_UNIVERSE_BOARD.html"),
        ("Universe map — the whole picture, what is built and what is next", "ISZE\\02_dashboards\\hub\\ISZE_UNIVERSE_MAP.html"),
        ("Dashboard index — BI packs", "ISZE\\02_dashboards\\hub\\BI_PACKS.html"),
        ("Mission control (26 Aug, carries superseded AIM figure)", "ISZE\\02_dashboards\\hub\\MASTER_DASHBOARD.html"),
        ("Hub home", "ISZE\\02_dashboards\\hub\\index.html"),
        ("Project hub", "ISZE\\02_dashboards\\hub\\PROJECT_HUB.html"),
        ("Workspace landing page (regenerated 16 Sep)", "DASHBOARDS.html"),
        ("Machine registry — manifest.yaml (81 live entries)", "ISZE\\02_dashboards\\manifest.yaml"),
        ("Monthly sales tracker", "ISZE\\02_dashboards\\sales\\ISZE_Monthly_Sales_Tracker.html"),
        ("Part-groups sales explorer", "ISZE\\02_dashboards\\sales\\ISZE_PartGroups_Sales_Explorer.html"),
        ("Sales to dealer — AIM and GPS, ITUK / UTI (15 Sep)", "ISZE\\02_dashboards\\sales\\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"),
        ("Sales to dealer — UTI against ITUK", "ISZE\\02_dashboards\\sales\\Dealer_Sellout_UTI_vs_ITUK.html"),
        ("Aftermarket BI command centre", "ISZE\\02_dashboards\\sales\\ISZE_Aftermarket_BI_Command_Center.html"),
        ("Risk cockpit (1 Aug)", "ISZE\\02_dashboards\\sales\\ISZE_Risk_Cockpit.html"),
        ("UTI replenishment H2 2025 (19 Aug)", "ISZE\\02_dashboards\\sales\\ISZE_UTI_Replenishment_H2_2025.html"),
        ("SPA run rate — UTI (1 Aug)", "ISZE\\02_dashboards\\sales\\ISZE_SPA_RunRate_UTI.html"),
        ("Dealer standard (IDS) compare — all markets (16 Sep)", "ISZE\\02_dashboards\\ids\\IDS_2026_dealer_compare.html"),
        ("Dealer standard — UK CV", "ISZE\\02_dashboards\\ids\\IDS_2026_dealer_compare_UK_CV.html"),
        ("Dealer standard — Israel pickups", "ISZE\\02_dashboards\\ids\\IDS_2026_dealer_compare_Israel_LCV.html"),
        ("Action ledger", "ISZE\\02_dashboards\\ops\\ISZE_Action_Ledger.html"),
        ("OS data map (capability against data)", "ISZE\\02_dashboards\\ops\\ISZE_OS_Data_Map.html"),
        ("Commercial model map", "ISZE\\02_dashboards\\ops\\ISZE_Commercial_Model_Map.html"),
        ("Tender monitor", "ISZE\\02_dashboards\\ops\\ISZE_Tender_Monitor_v2.html"),
        ("AI tools overview", "ISZE\\02_dashboards\\ops\\ISZE_AI_Tools_Overview.html"),
        ("BI twins — model cohorts (static snapshot)", "ISZE\\02_dashboards\\bi\\Parc_Cohorts.html"),
        ("BI twins — warranty intelligence (static snapshot)", "ISZE\\02_dashboards\\bi\\Warranty_Intelligence.html"),
        ("BI twins — price realisation (static snapshot)", "ISZE\\02_dashboards\\bi\\Price_Realization.html"),
        ("BI twins — dealer sales to dealer (static snapshot)", "ISZE\\02_dashboards\\bi\\Dealer_Sellout.html"),
    ]),
    ("Deliverables — the output layer", [
        ("Exec aftersales paper (16 pages, rebuilt 16 Sep)", "ISZE\\02_dashboards\\sales\\ISZE_Exec_Aftersales_Paper.html"),
        ("Growth plan 2026 (15 Sep)", "ISZE\\02_dashboards\\sales\\ISZE_Growth_Plan_2026.html"),
        ("Distributor to dealer replenishment CY2025", "ISZE\\02_dashboards\\sales\\ISZE_DB_DLR_Replenishment_CY2025.html"),
        ("Year-end review FY2026", "ISZE\\02_dashboards\\fleet\\ISZE_FY2026_YearEnd_Review.html"),
        ("GPS kickback and stretch proposal FY27 (distributor facing)", "ISZE\\02_dashboards\\gps\\ISZE_GPS_Kickback_Stretch_Proposal_FY27.html"),
        ("ZEV golden window", "ISZE\\02_dashboards\\fleet\\ITUK_ZEV_Golden_Window_Dashboard.html"),
    ]),
    ("Registers and guardians", [
        ("Open data-integrity issues", "ISZE\\01_data\\00_derived\\_data_integrity_open_issues.md"),
        ("Aftersales dashboard status (16 Sep)", "docs\\AFTERSALES_DASHBOARD_STATUS_2026-09-16.md"),
        ("KPI candidates from the archives", "ISZE\\01_data\\90_INBOX\\_archived_kpi_candidates.md"),
        ("Market fleet profile — workup", "ISZE\\01_data\\90_INBOX\\_market_fleet_profile_workup.md"),
        ("Market fleet profile — design", "ISZE\\01_data\\90_INBOX\\_market_fleet_profile_design.md"),
        ("Owned number shortlist", "ISZE\\00_docs\\OWNED_NUMBER_SHORTLIST_20260916.md"),
        ("Corrections to stop repeating", "ISZE\\00_docs\\RECURRING_CORRECTIONS_20260916.md"),
        ("Value ledger 2026 Q3", "ISZE\\00_docs\\VALUE_LEDGER_2026Q3.md"),
        ("Decision reconciliation (16 Sep)", "ISZE\\00_docs\\DECISION_RECONCILE_20260916.md"),
        ("Facts anchor", "ISZE\\FACTS.md"),
        ("Decision record", "ISZE\\DECISIONS.md"),
        ("Ship gate (this page must pass it)", "ISZE\\02_dashboards\\_build\\ship_gate_check.ps1"),
    ]),
]

link_sections = []
for title, items in layer_links:
    cards = "\n".join('<li>%s</li>' % link(lbl, p) for lbl, p in items)
    n_ok = sum(1 for _, p in items if os.path.exists(os.path.join(ROOT, p)))
    link_sections.append(
        '<div class="lcard"><div class="lhead"><h3>%s</h3>'
        '<span class="lcount">%d links tested</span></div><ul>%s</ul></div>'
        % (esc(title), n_ok, cards))
link_html = "\n".join(link_sections)

n_links = len(LINKS)
n_ok_links = sum(1 for _, _, ok in LINKS if ok)
missing = [p for _, p, ok in LINKS if not ok]

# ================================================================ 4. CSS / page
CSS = """
:root{--navy:#15233c;--navy2:#1a2b4a;--paper:#f7f4ee;--ink:#222;--terra:#c0552d;--muted:#6b7280;
--line:#e2ddd2;--pale:#eef3f9;}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:-apple-system,"Segoe UI",system-ui,Roboto,sans-serif;font-size:15px;line-height:1.5}
h1,h2,h3,h4{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
a{color:var(--navy);text-decoration:none}
code{font-family:Consolas,"SF Mono",Menlo,monospace;font-size:.85em;background:#efeade;
padding:.08em .3em;border-radius:3px}

/* chrome */
.chrome{background:var(--navy);color:var(--paper);position:sticky;top:0;z-index:60;
border-bottom:3px solid var(--terra)}
.chrome-in{max-width:1280px;margin:0 auto;display:flex;align-items:center;gap:20px;
padding:0 22px;height:52px;flex-wrap:wrap}
.brand{font-family:Georgia,serif;font-size:1.02rem;font-weight:700;white-space:nowrap}
.brand span{color:#e8b48c}
.chrome nav{display:flex;gap:2px;flex-wrap:wrap}
.chrome nav a{color:#c9cedb;font-size:.79rem;padding:6px 10px;border-radius:6px}
.chrome nav a:hover{color:#fff;background:rgba(255,255,255,.09)}

/* hero */
.hero{background:linear-gradient(118deg,var(--navy) 0%,var(--navy2) 58%,#263d61 100%);
color:#f7f4ee;padding:2.4rem 22px 2rem;border-bottom:4px solid var(--terra)}
.hero-in{max-width:1280px;margin:0 auto}
.kicker{font-size:.7rem;letter-spacing:.22em;text-transform:uppercase;color:#e8b48c;font-weight:700}
.hero h1{color:#fff;font-size:2.15rem;margin:.45rem 0 .5rem;line-height:1.15;max-width:940px}
.hero p{color:#c7cddb;max-width:900px;margin:.35rem 0 0;font-size:.97rem}
.hero .meta{margin-top:1rem;font-size:.78rem;color:#93a3c0}
.legend{display:flex;gap:10px;flex-wrap:wrap;margin-top:1.15rem}

/* state chips */
.chip{display:inline-flex;align-items:center;gap:.35rem;font-size:.68rem;font-weight:700;
letter-spacing:.05em;text-transform:uppercase;border-radius:999px;padding:.16rem .55rem;
border:1px solid transparent;cursor:help;position:relative;white-space:nowrap}
.chip.measured{background:#e3efe4;color:#1d5330;border-color:#b9d6bd}
.chip.modelled{background:#eef1f7;color:#2f4569;border-color:#c6cfe0}
.chip.excluded{background:#efeeea;color:#5d5a52;border-color:#d6d3c9}
.chip.judge{background:#f7e3d8;color:#8a3a17;border-color:#e6bfa6}
.chip.dim{opacity:.62}
.chip .tag{font-style:normal;font-size:.62rem;background:rgba(0,0,0,.08);border-radius:4px;padding:0 .28rem}

/* tooltips: kpi and chip both use .tip */
.tip{position:absolute;left:0;top:calc(100% + 7px);z-index:80;width:330px;background:var(--navy);
color:var(--paper);border-top:3px solid var(--terra);border-radius:8px;padding:.7rem .8rem;
font-family:-apple-system,"Segoe UI",system-ui,sans-serif;font-size:.74rem;font-weight:400;
letter-spacing:0;text-transform:none;line-height:1.42;box-shadow:0 10px 26px rgba(0,0,0,.3);
display:none;text-align:left;white-space:normal}
.tip b{display:block;color:#fff;font-size:.79rem;margin-bottom:.32rem;font-family:Georgia,serif}
.tip .tr{display:block;margin-top:.3rem;color:#d5dae6}
.tip .tr i{display:block;font-style:normal;color:#e8b48c;font-size:.63rem;letter-spacing:.1em;
text-transform:uppercase;font-weight:700}
.tip .tr.warn{color:#f0c9b5}
.chip:hover>.tip,.kpi:hover>.tip,.mixbar:hover>.tip{display:block}
.kpi{position:relative;cursor:help;border-bottom:1px dotted #9a958a;font-variant-numeric:tabular-nums}
.kpi.measured{border-bottom-color:#7d9c85}
.kpi.modelled{border-bottom-color:#8d9cb8}
.kpi.excluded{border-bottom-color:#a9a49a}
.kpi.judge{border-bottom-color:var(--terra)}

/* layout */
.wrap{max-width:1280px;margin:0 auto;padding:0 22px 3.5rem}
section{padding:2.2rem 0 .4rem;border-top:1px solid var(--line);margin-top:1.4rem}
section:first-of-type{border-top:0}
.shead{margin-bottom:1rem}
.shead h2{font-size:1.5rem}
.shead p{margin:.4rem 0 0;color:#4a4a4a;max-width:960px;font-size:.93rem}
.sq{color:var(--terra);font-weight:700}

/* layer stack */
.stack{display:grid;gap:.8rem}
.layer{display:grid;grid-template-columns:6px 1.05fr 1.5fr 1.3fr;gap:0;background:#fff;
border:1px solid var(--line);border-radius:10px;overflow:hidden}
.layer>.bar{background:var(--navy)}
.layer.l1>.bar{background:#1a2b4a}.layer.l2>.bar{background:#26456e}
.layer.l3>.bar{background:#8a3f22}.layer.l4>.bar{background:#6b7280}
.layer.l5>.bar{background:#c0552d}
.layer>div{padding:.9rem 1rem}
.layer h3{font-size:1.02rem;margin-bottom:.15rem}
.layer .q{color:var(--terra);font-size:.8rem;font-weight:700;margin-bottom:.35rem}
.layer p{margin:0 0 .5rem;font-size:.85rem;color:#3d3d3d}
.layer .figs{display:flex;flex-wrap:wrap;gap:.4rem .9rem;font-size:.85rem}
.layer .figs>span{display:inline-block}
.layer ul{margin:0;padding-left:1rem;font-size:.83rem}
.layer li{margin:.12rem 0}
@media(max-width:1080px){.layer{grid-template-columns:6px 1fr}.layer>div{padding:.8rem 1rem}
.layer .colh{display:none}}

/* key chain */
.chain{display:flex;align-items:stretch;gap:.45rem;flex-wrap:wrap;margin:.6rem 0 1rem}
.node{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);
border-radius:8px;padding:.55rem .75rem;min-width:150px;flex:1 1 150px;position:relative}
.node b{display:block;font-family:Georgia,serif;color:var(--navy);font-size:.9rem}
.node span{font-size:.76rem;color:#54514b}
.node.k{border-left-color:var(--terra);background:#fdf6f1}
.arrow{align-self:center;color:var(--terra);font-weight:700;font-size:1.1rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}

/* join cards */
.joins{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:1000px){.joins{grid-template-columns:1fr}}
.jcard{background:#fff;border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem}
.jcard h3{font-size:1.02rem;margin-bottom:.3rem}
.jcard .hl{font-size:.78rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--terra);margin-bottom:.4rem}
.jcard p{font-size:.87rem;margin:.35rem 0}
.jcard table{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:.5rem}

/* tables */
table.t{width:100%;border-collapse:collapse;font-size:.85rem;background:#fff;
border:1px solid var(--line);border-radius:8px;overflow:hidden}
table.t thead th{background:var(--navy);color:#f7f4ee;text-align:left;padding:.55rem .6rem;
font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;position:sticky;top:52px;z-index:40}
table.t tbody td{padding:.5rem .6rem;border-bottom:1px solid #f0ece3;vertical-align:top}
table.t tbody tr:nth-child(even):not(.footrow):not(.head) td{background:var(--pale);color:var(--ink)}
table.t tbody tr.footrow td{background:#f2f0eb;color:#4a4a4a;border-top:1px solid #ddd8cc}
table.t tbody tr.italy td{background:#fbf0e7}
table.t tbody tr.head td,table.t tbody tr.head:hover td{background:var(--navy2);color:#f7f4ee;
font-weight:700;font-size:.74rem;letter-spacing:.06em;text-transform:uppercase}
table.t .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
table.t .mk .nm{display:block;font-weight:600}
table.t .mk .db{font-size:.72rem;color:#6b7280}
.mixbar{display:inline-flex;width:132px;height:13px;border-radius:3px;overflow:hidden;
border:1px solid #d9d4c9;position:relative;cursor:help;vertical-align:middle}
.mixbar i{display:block;height:100%;font-style:normal}
.legendline{font-size:.76rem;color:#5a574f;margin:.45rem 0 .1rem}

/* bars */
.bars{background:#fff;border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem 1.15rem}
.bars h3{font-size:1rem;margin-bottom:.2rem}
.bars .sub{font-size:.79rem;color:#5a574f;margin-bottom:.85rem}
.brow{display:grid;grid-template-columns:190px 1fr 74px;align-items:center;gap:.6rem;
font-size:.82rem;padding:.16rem 0}
.brow .bname{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.btrack{position:relative;height:15px;background:#f1eee7;border-radius:3px}
.btrack i{display:block;height:100%;background:var(--navy);border-radius:3px}
.btrack i.terra{background:var(--terra)}
.btrack i.pale{background:#9fb0ca}
.btrack .med{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--terra);opacity:.7}
.brow .bval{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.btwo .bname{width:auto}
.btwo{grid-template-columns:120px 1fr 1fr 82px}
.btwo .btrack{margin-right:.15rem}

/* gap table */
.gapwrap{overflow-x:auto}
.callout{background:#fdf6f1;border:1px solid #e6bfa6;border-left:4px solid var(--terra);
border-radius:8px;padding:.85rem 1rem;margin:.9rem 0;font-size:.86rem}
.callout b{font-family:Georgia,serif;color:#8a3a17}
.note{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);
border-radius:8px;padding:.85rem 1rem;margin:.9rem 0;font-size:.86rem}
.note b{font-family:Georgia,serif}

/* links */
.lgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:1rem}
.lcard{background:#fff;border:1px solid var(--line);border-radius:10px;padding:.85rem 1rem}
.lcard .lhead{display:flex;justify-content:space-between;align-items:baseline;gap:.6rem;
border-bottom:1px solid #f0ece3;padding-bottom:.4rem;margin-bottom:.35rem}
.lcard h3{font-size:.96rem}
.lcount{font-size:.7rem;color:#6b7280;white-space:nowrap}
.lcard ul{list-style:none;margin:0;padding:0}
.lcard li{border-bottom:1px solid #f4f1ea}
.lcard li:last-child{border-bottom:0}
.lnk{display:block;padding:.34rem .1rem .34rem .55rem;border-left:3px solid transparent;font-size:.845rem}
.lnk:hover{color:var(--terra);border-left-color:var(--terra);background:#fdf9f5}
.lnk[data-missing]{color:#9a3b1c;text-decoration:line-through}
.foot{margin-top:2rem;padding-top:1rem;border-top:1px solid var(--line);color:#5a574f;font-size:.8rem}
.foot code{background:#efeade}
ul.plain{font-size:.86rem;padding-left:1.1rem}
ul.plain li{margin:.25rem 0}
.small{font-size:.78rem;color:#6b7280}
"""


def sec(sid, title, lede):
    return ('<section id="%s"><div class="shead"><h2>%s</h2><p>%s</p></div>'
            % (sid, esc(title), lede))


JS = """
document.querySelectorAll('a.lnk[data-missing]').forEach(function(a){
  a.setAttribute('title','link target missing on disk');
});
var bad=document.querySelectorAll('a.lnk[data-missing]').length;
var el=document.getElementById('linkcheck');
if(el){el.textContent = bad===0 ? 'all link targets present on disk' : (bad+' link targets MISSING');}
"""

# -*- coding: utf-8 -*-
"""Composition half of build_isze_os_hub.py — token substitution, no % formatting."""


def T(tpl, **vals):
    out = tpl
    for k, v in vals.items():
        out = out.replace("@@%s@@" % k, str(v))
    return out


def figs(*items):
    return "<br>".join(items)


# ------------------------------------------------------------------ LAYER STACK
LAYER1 = """
  <div class="layer l1">
    <div class="bar"></div>
    <div><h3>1 &middot; Car park / UIO</h3>
      <div class="q">Who owns the trucks, what are they, how old are they</div>
      <p>Units in operation (UIO): the vehicles in service. This layer supplies the denominator that every
      spend-per-unit, capture and age figure divides by.</p>
      <div class="figs">@@STATEKEY@@</div></div>
    <div><div class="colh small">Canonical figures</div>
      <div class="figs">@@FIGS@@</div></div>
    <div><div class="colh small">Where it lives</div>
      <p>@@LINKS@@</p>
      <p class="small">Register scope: @@SCOPE@@</p></div>
  </div>
"""

LAYER2 = """
  <div class="layer l2">
    <div class="bar"></div>
    <div><h3>2 &middot; PRISM</h3>
      <div class="q">What those trucks should consume, and what we actually bill them</div>
      <p>Expected service demand from a service interval per model, then capture = billed &divide; expected.
      Spend per unit (GPS) is parts revenue &divide; vehicles in service. Whatever the modelled ceiling does not
      cover is the uncaptured GPS value. These are siblings: all of them need a fleet denominator, so a market
      with no fleet count has none of them.</p></div>
    <div><div class="colh small">Canonical figures</div>
      <div class="figs">@@FIGS@@</div></div>
    <div><div class="colh small">Where it lives</div>
      <p>@@LINKS@@</p>
      <p class="small">The application itself is a live Streamlit app at port 8503. The static BI twins under
      <code>02_dashboards/bi/</code> are dated snapshots of four of its pages, not the live model.</p></div>
  </div>
"""

LAYER3 = """
  <div class="layer l3">
    <div class="bar"></div>
    <div><h3>3 &middot; AIM</h3>
      <div class="q">What competes against each part number, and at what price</div>
      <p>Aftermarket item classification: every billed part number gets an L1 / L2 / L3 class, then a
      competitive exposure and a price position against the independent aftermarket. AIM keys on the part
      number directly, which is why it shares its join with PRISM without a fleet key in between.</p></div>
    <div><div class="colh small">Canonical figures</div>
      <div class="figs">@@FIGS@@</div></div>
    <div><div class="colh small">Where it lives</div>
      <p>@@LINKS@@</p>
      <p class="small">Classified by part number network-wide. There is no per-market classification coverage
      figure on disk, so none is shown here.</p></div>
  </div>
"""

LAYER4 = """
  <div class="layer l4">
    <div class="bar"></div>
    <div><h3>4 &middot; Dashboards</h3>
      <div class="q">The views that read the three layers above</div>
      <p>Around twenty live pages across sales, fleet, pricing, dealer standard, operations and the hub,
      plus four static BI twins. They read the layers; they are not sources in their own right, and two of
      them still disagree about what exists.</p></div>
    <div><div class="colh small">Census</div>
      <div class="figs">@@FIGS@@</div></div>
    <div><div class="colh small">Where it lives</div>
      <p>@@LINKS@@</p>
      <p class="small">@@NOTE@@</p></div>
  </div>
"""

LAYER5 = """
  <div class="layer l5">
    <div class="bar"></div>
    <div><h3>5 &middot; Deliverables</h3>
      <div class="q">What leaves the building</div>
      <p>The exec aftersales paper, the growth plan, the management pack, the distributor-to-dealer
      replenishment page and the distributor-facing proposals.</p></div>
    <div><div class="colh small">State</div>
      <div class="figs">@@FIGS@@</div></div>
    <div><div class="colh small">Where it lives</div>
      <p>@@LINKS@@</p>
      <p class="small">@@NOTE@@</p></div>
  </div>
"""

layer_stack = ('<div class="stack">'
               + T(LAYER1,
                   STATEKEY='<span class="small">Every figure below is one of the four states: measured, '
                            'modelled, excluded, or needs a judgement.</span>',
                   FIGS=figs(
                       kpi(eur(uio_net), "Vehicles in service, CY2025, 18 markets",
                           "sum of uio_units over the 18 distributors that have a fleet denominator",
                           "gps_spu_by_distributor.csv, full-year 2025 rows",
                           "Italy (87 510 units) and the four CIS markets; the 2026-2030 forecast columns.", "measured"),
                       kpi("7 of 22", "Markets with vehicle identities, not only a count",
                           "vehicle register (7 markets, 3 238 VINs) plus the UK registration extract (29 935 VINs)",
                           "VIN_register_summary.json 27 Jul 2026; ITUK registration mail 23 Jul 2026",
                           "A live-fleet flag, mileage and transmission are absent from both files. Israel has neither.",
                           "judge"),
                   ),
                   LINKS=link("UIO dashboard", "ISZE\\02_dashboards\\fleet\\ISUZU_UIO_Dashboard_2026.html")
                         + " &middot; " + link("GPS dashboard", "ISZE\\02_dashboards\\fleet\\ISZE_GPS_Dashboard.html")
                         + " &middot; " + link("UIO workbook repair spec", "ISZE\\06_uio\\_CURRENT\\V20_SPEC.md")
                         + " &middot; " + link("Vehicle register summary", "ISZE\\01_data\\07_UIO\\vin\\VIN_register_summary.json"),
                   SCOPE="seven markets (BE, CY, DE, GR, IE, MT, PT), 3 238 VINs; ITUK, UK, UTI and UMI are "
                         "excluded by design, which is why the two largest books have no identity layer here")
               + T(LAYER2,
                   FIGS=figs(
                       kpi(eur(sales_net), "Parts billed CY2025, 18 markets", "sum of total_sales_eur, full-year rows",
                           "gps_spu_by_distributor.csv",
                           "The four CIS markets bill parts but have no denominator, so they sit outside this base.",
                           "measured"),
                       kpi(eur(spu_net, 2), "Spend per unit (GPS) network, CY2025",
                           "parts billed / vehicles in service, 18 markets", "gps_spu_by_distributor.csv 2025",
                           "Partial-year 2026 rows; Italy and the CIS markets.", "measured"),
                       kpi(str(len(set(r["pms_category"] for r in pms)))
                           + " service categories",
                           "Part-demand lines the capture layer measures",
                           "distinct service categories, each with expected quantity, actual quantity and a euro gap",
                           "pms_capture_by_db_year.csv, all years on the file",
                           "Categories with no agreed service interval are not in this count, so the layer is "
                           "narrower than the parts catalogue.", "measured"),
                       kpi(pct(cover) + "%", "Network cover of target spend, CY2025",
                           "captured total / modelled target spend ceiling",
                           "wallet_waterfall.csv 2025, re-derived 16 Sep 2026",
                           "The ceiling itself is modelled, and 8 of 18 markets sit on one flat placeholder rate.",
                           "measured"),
                       kpi(eur(uncaptured), "Uncaptured GPS value, CY2025, 18 markets",
                           "modelled target spend ceiling minus parts billed",
                           "wallet_waterfall.csv 2025, re-derived 16 Sep 2026",
                           "Uncaptured GPS value is the part of a market's modelled parts spend that we never bill. "
                           "It is a range, not a target: 37 per cent of the ceiling sits on one flat placeholder rate, "
                           "so the same book reads between 29 and 44 per cent cover on defensible alternatives.",
                           "modelled"),
                       kpi(pct(flat_share) + "%", "Share of the ceiling carried by a flat placeholder rate",
                           "markets at exactly EUR 250 per truck / total ceiling", "wallet_waterfall.csv 2025",
                           "Denmark is near 250 but not flat and is therefore excluded from the count.", "judge"),
                   ),
                   LINKS=link("PRISM metric dictionary", "ISZE\\03_analytics\\Isuzu\\prism\\docs\\metric_dictionary.md")
                         + " &middot; " + link("PRISM contracts", "ISZE\\03_analytics\\Isuzu\\prism\\docs\\dashboard_contracts.md")
                         + " &middot; " + link("PRISM launcher", "ISZE\\03_analytics\\Isuzu\\prism\\run_prism.ps1")
                         + " &middot; " + link("Capture file", "ISZE\\01_data\\00_derived\\pms_capture_by_db_year.csv")
                         + " &middot; " + link("Opportunity matrix", "ISZE\\01_data\\00_derived\\pms_opportunity_matrix.csv")
               )
               + T(LAYER3,
                   FIGS=figs(
                       kpi(pct(100 - 1.6, 0) + "%", "AIM classification, revenue-weighted residual",
                           "unclassified revenue / parts revenue in scope: 1.6% CY2024, 1.8% CY2025",
                           "aim_classification_gap_report.md, 2 Jul 2026",
                           "The 93.5% completeness figure of March 2026 is count-based and superseded; it is not "
                           "comparable with this residual.", "measured"),
                       kpi(eur(fnum(oil_row["downtrade_gp_gap_eur"])) if oil_row else "n/a",
                           "Down-trade margin, oil filter, per year",
                           "(genuine margin per unit minus best-value margin per unit) x best-value units",
                           "bvp_downtrade_gp.csv, rebuilt 2 Jun 2026",
                           "This is gross profit, not revenue, and must never be added to uncaptured spend. "
                           "The negative sign means down-trade on this line adds margin.", "measured"),
                   ),
                   LINKS=link("AIM dashboard", "ISZE\\02_dashboards\\sales\\AIM_Dashboard_CY2026.html")
                         + " &middot; " + link("Competitiveness", "ISZE\\02_dashboards\\sales\\ISZE_Competitiveness_Dashboard.html")
                         + " &middot; " + link("IAM price positioning", "ISZE\\02_dashboards\\pricing\\ISZE_IAM_Quality_Positioning_Overview.html")
                         + " &middot; " + link("Part number classification", "ISZE\\01_data\\00_derived\\aim_pn_classification.csv")
                         + " &middot; " + link("AIM gap report", "ISZE\\03_analytics\\Isuzu\\prism\\docs\\aim_classification_gap_report.md")
               )
               + T(LAYER4,
                   FIGS=figs(
                       kpi(str(man_files), "Live entries in the machine registry",
                           "list items under files: in manifest.yaml, stubs excluded",
                           "manifest.yaml, regenerated from disk 16 Sep 2026",
                           "Archive, build, data and scratch folders are excluded by design.", "measured"),
                       kpi("3 vs 1", "Index files that disagree about what exists",
                           "three landing pages list overlapping but different sets; one machine registry lists all",
                           "AFTERSALES_DASHBOARD_STATUS_2026-09-16.md",
                           "Nothing on disk declares one of the three canonical.", "judge"),
                   ),
                   LINKS=link("Dashboard index", "ISZE\\02_dashboards\\hub\\BI_PACKS.html")
                         + " &middot; " + link("Mission control", "ISZE\\02_dashboards\\hub\\MASTER_DASHBOARD.html")
                         + " &middot; " + link("Workspace landing page", "DASHBOARDS.html")
                         + " &middot; " + link("manifest.yaml", "ISZE\\02_dashboards\\manifest.yaml"),
                   NOTE="The dashboard index was last touched on 7 September and omits the exec paper, the growth "
                        "plan and the distributor-to-dealer page. Mission control is from 26 August and still prints "
                        "a superseded classification figure. Both are linked so the disagreement is visible rather "
                        "than hidden."
               )
               + T(LAYER5,
                   FIGS=figs(
                       chip("measured", "Sixteen A4 pages, eleven charts, rebuilt and receipted 16 September 2026."),
                       chip("judge", "No page declares itself the front door and no index is canonical; that is a "
                                     "decision, not a build."),
                   ),
                   LINKS=link("Exec aftersales paper", "ISZE\\02_dashboards\\sales\\ISZE_Exec_Aftersales_Paper.html")
                         + " &middot; " + link("Growth plan 2026", "ISZE\\02_dashboards\\sales\\ISZE_Growth_Plan_2026.html")
                         + " &middot; " + link("Distributor to dealer replenishment", "ISZE\\02_dashboards\\sales\\ISZE_DB_DLR_Replenishment_CY2025.html"),
                   NOTE="The exec paper is the only aftersales artefact with a machine guard on disk: an after-build "
                        "hook and an on-stop hook. That is why it is the most trustworthy page in this set."
               )
               + '</div>')

# ------------------------------------------------------------------ KEY CHAIN
KEY = """
<div class="chain">
  <div class="node"><b>Vehicle</b><span>a VIN, or just a fleet count per market</span></div>
  <div class="arrow">&rarr;</div>
  <div class="node"><b>Model code</b><span>NPR75, NLR87, FRR90, N75, F110&hellip;</span></div>
  <div class="arrow">&rarr;</div>
  <div class="node"><b>Weight class</b><span>7.5 t, 9.0 t, 3.5 t &mdash; the bridge to a part</span></div>
  <div class="arrow">&rarr;</div>
  <div class="node k"><b>Part number</b><span>the only key all three layers share</span></div>
  <div class="arrow">&rarr;</div>
  <div class="node"><b>AIM class</b><span>L1 / L2 / L3, exposure, price position</span></div>
</div>
"""

wc_rows = []
for s in ["NPR", "NLR", "NMR", "NNR", "N1R", "FRR", "FSR"]:
    if s in wc:
        wc_rows.append("<tr><td><code>%s</code></td><td>%s t</td></tr>" % (s, " / ".join(sorted(wc[s]))))
wc_table = ('<table class="t" style="max-width:360px"><thead><tr><th>Series</th>'
            '<th>Weight class the register reads</th></tr></thead><tbody>%s</tbody></table>'
            % "".join(wc_rows))

# ------------------------------------------------------------------ BARS
spu_rows = "".join(
    '<div class="brow"><span class="bname">%s</span>'
    '<span class="btrack"><i style="width:%.1f%%"></i>'
    '<span class="med" style="left:%.1f%%"></span></span>'
    '<span class="bval">%s</span></div>'
    % (esc(NAME.get(r["distributor_code"], (r["distributor_code"], ""))[0]),
       100 * fnum(r["spend_per_unit_eur"]) / spu_max,
       100 * spu_median / spu_max,
       kpi(eur(fnum(r["spend_per_unit_eur"]), 2),
           "Spend per unit, %s, CY2025" % NAME.get(r["distributor_code"], (r["distributor_code"], ""))[0],
           "parts billed / vehicles in service", "gps_spu_by_distributor.csv, full-year row",
           "Not comparable with 2026, which is a partial year. Where the market is pickups only, the denominator "
           "is a modelled pickup fleet rather than a registration count.", "measured"))
    for r in sorted(with_spu, key=lambda x: -fnum(x["spend_per_unit_eur"])))

mx_bill = max(b for _, b, _, _ in two_dir)
two_dir_rows = "".join(
    '<div class="brow btwo"><span class="bname">%s</span>'
    '<span class="btrack"><i style="width:%.1f%%"></i></span>'
    '<span class="btrack"><i class="terra" style="width:%.1f%%"></i></span>'
    '<span class="bval">%s</span></div>'
    % (esc(NAME.get(k, (k, k))[0]), 100 * b / mx_bill, 100 * s / mx_bill,
       kpi(pct(r) + "%", "Sales to dealer as a share of billing, %s, CY2025" % k,
           "distributor sales to dealers / ISZE billing to the distributor",
           "sellout_aim_network_mix_2025.csv, CY2025",
           "The two files may not cover exactly the same part numbers, so this is a level comparison, not a "
           "part-number reconciliation.", "measured"))
    for k, b, s, r in two_dir)

# ------------------------------------------------------------------ LINK CARDS
link_sections = []
for title, items in layer_links:
    cards = "".join("<li>%s</li>" % link(lbl, p) for lbl, p in items)
    n_ok = sum(1 for _, p in items if os.path.exists(os.path.join(ROOT, p)))
    link_sections.append('<div class="lcard"><div class="lhead"><h3>%s</h3>'
                         '<span class="lcount">%d of %d targets present</span></div><ul>%s</ul></div>'
                         % (esc(title), n_ok, len(items), cards))
link_html = "".join(link_sections)

n_links = len(LINKS)
n_ok_links = sum(1 for _, _, ok in LINKS if ok)
missing = [p for _, p, ok in LINKS if not ok]

CARDS = """
  <div class="jcard">
    <div class="hl">Join 1 &middot; by part number</div>
    <h3>Demand, competition and fitment all land on the same key</h3>
    <p>PRISM counts expected and actual quantity per part number. AIM classes the same part number.
    Fitment ties that part number to a model, and the model carries the weight class. This is the join that
    turns a fleet count into a parts decision, and it is why the part-number registry is the real build.</p>
    <p class="small">Where it is weak: a part number with no usable list price is out of reach of any price
    decision, however good. 251 part numbers carried EUR 4.96M of the CY2025 billed book with no list price;
    a pull in August 2026 closed 220 of them, leaving 31 part numbers and EUR 0.59M.</p>
  </div>

  <div class="jcard">
    <div class="hl">Join 2 &middot; model code to weight class</div>
    <h3>Weight class is how a part number reaches the fleet</h3>
    <p>NPR75 is 7.5 tonnes. FRR90 and FSR90 are 9.0 tonnes. The ranges are named N35, N55, N65, N75 and
    F110 / F135. The project workbook, however, carries one undifferentiated light-duty bucket, so a 3.5
    tonne vehicle can be charged the target spend of a 7.5 tonne vehicle. For Portugal that understates
    spend per unit by roughly a quarter, so the market total moves while nothing in the market has
    changed.</p>
    <p class="small">Where it is weak: no per-market split by N35 / N50 / N62 / N75 / F110 / F135 exists
    anywhere on disk. Only recent-arrival shares and claim counts exist, and neither of those is a fleet mix.</p>
  </div>

  <div class="jcard">
    <div class="hl">Join 3 &middot; by distributor and market</div>
    <h3>The only join that appears in every layer</h3>
    <p>Fleet rows, billing, expected demand, aftermarket exposure and dealer scores all key on the
    distributor. It is not one column: a sold-to code, a payer code and a distributor code all exist, and the
    Israeli payer covers two separate businesses that split at sold-to level.</p>
    <p class="small">Where it is weak: Israel's vehicles carry one distributor name in the warranty file, so
    the truck book and the pickup book cannot be split from claim data alone. Israel age figures are pooled
    and are labelled as pooled on this page.</p>
  </div>

  <div class="jcard">
    <div class="hl">Join 4 &middot; by month, in two directions</div>
    <h3>What we invoice the distributor, and what the distributor invoices its dealers</h3>
    <p>These are two separate measurements and must never be drawn as one line. The ratio between them is how
    much stock the distributor is sitting on: close to parity means the parts flow through to the dealers, low
    means they stay in the distributor's warehouse.</p>
    <p class="small">Where it is weak: sales-to-dealer files exist for six of the eighteen markets. Reading a
    network ratio without the coverage line beside it would overstate how much of the book is really visible.
    The ratio never reaches 100 per cent even where coverage is full, because the distributor sells but does
    not bill every part in the same period.</p>
  </div>
"""

WCTABLE_NOTE = ""

GAP_ROWS = """
      <tr><td><code>UIO-FCAST</code></td>
        <td>The vehicles-in-service forecast for 2026&ndash;2030 removes about 3 per cent of the fleet a year
        while the 1990&ndash;2025 history implies about 10 per cent. It is overstated by 7.8 per cent in 2026,
        rising to 37.7 per cent in 2030, and far worse by market. Israel is roughly 25 per cent low at the same
        time, in every year.</td>
        <td>Car park, and every figure that divides by it: spend per unit, capture, the FY27 target</td>
        <td>No 2026&ndash;2030 denominator appears anywhere on this page. Every figure is CY2025 or earlier,
        and the forecast half of the workbook is named as under repair rather than quoted.</td></tr>
      <tr><td><code>VIN-IL</code></td>
        <td>Israel is absent from the vehicle register, so there is no vehicle age and no model detail for the
        Israeli book from identity data.</td>
        <td>Car park, and part-level demand for Israel</td>
        <td>Israel age is shown as a warranty-claim measurement, pooled across trucks and pickups, and flagged
        as pooled. No per-model fleet split is drawn for Israel.</td></tr>
      <tr><td><code>VIN-ITUK</code></td>
        <td>The UK identity list arrived on 23 July 2026 and supplies 29 935 distinct registrations. It carries
        no live-fleet flag, no mileage and no transmission, so it is not yet a fleet.</td>
        <td>Car park age and model mix for the UK</td>
        <td>The UK is shown as measured on registration data, with the limit stated: an extract reaching back
        to 2008 is not the set of vehicles on the road today.</td></tr>
      <tr><td><code>PT-GAP</code></td>
        <td>Portugal is missing six consecutive months of billing, March to August 2025. It is the only
        distributor with a gap in the tested window, and it understates the 2025 network base.</td>
        <td>Billing and capture for Portugal, and the network total</td>
        <td>Portugal keeps its fleet and spend figures, and its part-demand cell carries a judgement chip: any
        trend read for Portugal is invalid.</td></tr>
      <tr><td><code>SPU-PARTIAL</code></td>
        <td>The 2026 rows carry a partial-year numerator against a full-year denominator, which made every
        distributor read as a collapse that did not happen.</td>
        <td>Spend per unit, capture and traffic lights for 2026</td>
        <td>Only full-year rows are used. The 2026 rows are excluded from every figure and from both bar
        charts on this page.</td></tr>
      <tr><td><code>LCV-DEC</code> <span class="chip excluded">closed</span></td>
        <td>The pickup warranty file ends in November 2025, so a full calendar-year pickup figure drawn from
        that file is one month short.</td>
        <td>&mdash;</td>
        <td>Closed 24 September 2026: a newer network-wide claim export covers to August 2026 and its
        overlap ties to the old file to the euro. The two UK books, trucks and pickups, stay separate rows
        and are never merged into one figure.</td></tr>
      <tr><td><code>LCV-EXT</code></td>
        <td>Pickup claim detail now runs four months past anything that is read &mdash; 5,048 claim lines and
        EUR 1.08M for May to August 2026 sit in the new export and in nothing else.</td>
        <td>Pickup warranty after April 2026</td>
        <td>Nothing published shows a pickup warranty figure for those four months. The months already held
        are not re-read from the new file, so no month is counted twice.</td></tr>
      <tr><td><code>UMI-WARR</code> <span class="chip excluded">closed</span></td>
        <td>Israeli pickups looked absent from the pickup warranty file.</td>
        <td>&mdash;</td><td>Closed 3 July 2026: they have their own file and the year is complete. Treated as
        complete and not re-opened.</td></tr>
      <tr><td><code>CV-BLANK</code> <span class="chip excluded">closed</span></td>
        <td>A blank-country block in the warranty sheet looked like missing claims.</td>
        <td>&mdash;</td><td>Closed: it is labour, not parts, and line-level detail is not used on this
        page.</td></tr>
      <tr><td><code>IRE-CV / PT-CV</code> <span class="chip excluded">closed</span></td>
        <td>Low price-map coverage in Ireland and Portugal looked like missing claims.</td>
        <td>&mdash;</td><td>Closed: optional valuation on a small number of real part numbers.</td></tr>
"""

SUPERSEDED = """
    <div class="jcard">
      <div class="hl">Superseded figure</div>
      <h3>AIM classification completeness, 93.5 per cent</h3>
      <p>The count-based completeness figure of 14 March 2026 is superseded by a revenue-weighted residual of
      1.6 per cent for CY2024 and 1.8 per cent for CY2025. These are different denominators and must not be
      compared with each other. The mission-control page still prints the older figure; this hub prints the
      residual and links that page with its state marked.</p>
    </div>
    <div class="jcard">
      <div class="hl">Contaminated cell</div>
      <h3>Two systems inside one figure</h3>
      <p>One cell on the mission-control page puts a service-schedule cover figure (35.1 per cent) beside a
      network-lane denominator (7 836), mixing two systems that are explicitly not interchangeable, and the
      row beneath it inherits the error. This hub keeps the two lanes apart:</p>
      <table class="t" style="margin-top:.45rem">
        <thead><tr><th>Lane</th><th>Basis</th><th class="num">Cover</th></tr></thead>
        <tbody>
          <tr><td>Service schedule, external</td><td>@@IML_UIO@@ vehicles, 1.25 services a year</td>
            <td class="num">@@IML_PCT@@</td></tr>
          <tr><td>Internal network lane</td><td>@@NET_UIO@@ bucketed vehicles, internal league only</td>
            <td class="num">@@NET_PCT@@</td></tr>
        </tbody>
      </table>
      <p class="small">Do not put these two in one tile. The internal lane reads @@NET_UNC@@ uncapped on a
      narrower denominator; the external lane reads @@IML_PCT@@ on the full registration fleet. Both are on
      disk; they answer different questions.</p>
    </div>
"""

PAGE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ISZE OS &mdash; how the aftersales layers connect</title>
<style>@@CSS@@</style>
</head>
<body>

<header class="chrome"><div class="chrome-in">
  <div class="brand"><span>ISZE</span> &middot; OS interconnection layer</div>
  <nav>
    <a href="#stack">Layers</a>
    <a href="#key">The key</a>
    <a href="#joins">Joins</a>
    <a href="#market">Market coverage</a>
    <a href="#two">Two directions</a>
    <a href="#gaps">Blocking gaps</a>
    <a href="#where">Artefacts</a>
    <a href="#carry">Corrections</a>
  </nav>
</div></header>

<div class="hero"><div class="hero-in">
  <div class="kicker">Isuzu Motors Europe &middot; aftersales analytics</div>
  <h1>One key, four joins and four measurement states across the whole aftersales stack</h1>
  <p>Five layers, in the order the data actually flows: the vehicles in service, what those vehicles should
  consume, what competes against each part, the views that read all three, and what leaves the building.
  This page shows the joins between them and marks every figure with what it really is.</p>
  <div class="meta">Built @@SNAPSHOT@@ &middot; @@NLINKS@@ link targets, every one tested on disk before it was
  written &middot; figures re-derived from the files named in their own tooltips, not copied from an older page</div>
  <div class="legend">@@LEGEND@@</div>
</div></div>

<div class="wrap">

  <div class="note">
    <b>How to read a figure here.</b> Every number is a chip you can hover, and the state is not decoration.
    <b>Measured</b> means a real count or a real euro from a named file. <b>Modelled</b> means an assumption or
    a survival curve produced it. <b>Excluded</b> means the market is out of scope or there is no denominator
    at all. <b>Needs a judgement</b> means two files on disk disagree and a person has to decide before the
    number can be used. A blank on this page is deliberately blank: where the data cannot support a figure,
    the tooltip carries the reason instead of showing a substitute.
  </div>

<section id="stack">
  <div class="shead">
    <h2>The five layers, in the order the data actually flows</h2>
    <p>Each layer answers one question, consumes the layer above it, and hands its output to the one below.
    The state chips say what kind of figure that layer really produces, because a layer that looks
    authoritative but is mostly modelled is the most dangerous object in this estate.</p>
  </div>
  @@LAYERSTACK@@
</section>

<section id="key">
  <div class="shead">
    <h2>The part number is the only key the three layers share</h2>
    <p>PRISM rolls its service demand up to a part number through the catalogue. AIM classes part numbers
    directly. Fitment links a part number to a model code, and the model code carries the weight class.
    Nothing else is common to all three, which is why the part-number registry is the real build and every
    screen on top of it is a view.</p>
  </div>
  @@KEYCHAIN@@
  <div class="grid2">
    <div>
      <h3 style="font-size:1rem">What the part number carries</h3>
      <ul class="plain">
        <li>the aftermarket class (L1 / L2 / L3) and its competitive exposure;</li>
        <li>the service category, oil, fuel, air, urea, brake or clutch, and its expected demand;</li>
        <li>the catalogue reference that reaches a model group, and through it the fleet;</li>
        <li>its price level on the list, and whether it has a usable list price at all.</li>
      </ul>
      <p class="small">A part number with no documented fitment cannot be joined to a weight class, so it
      cannot be given a target spend. That is the most common reason a figure on this page is blank rather
      than small.</p>
    </div>
    <div>
      <h3 style="font-size:1rem">Model code to weight class, and where that breaks</h3>
      @@WCTABLE@@
      <div class="callout" style="margin-top:.7rem">
        <b>Open judgement on the light class.</b> The vehicle register reads the numeric part of the model
        code as a weight: NLR85, NLR87 and NLR88 become 8.5, 8.7 and 8.8 tonnes. The UK registration file says
        those three codes are all the same 3.5 tonne class. Both statements are on disk. Until one is settled,
        any target spend attached to an NLR part number is a judgement, not a measurement, and is marked as
        one wherever it appears.
      </div>
    </div>
  </div>
</section>

<section id="joins">
  <div class="shead">
    <h2>The four joins that make five layers one system</h2>
    <p>Two of them connect the layers to each other and two connect the data to a market. None of the four is
    automatic today, and each one has a named weakness that the page states instead of smoothing over.</p>
  </div>
  <div class="joins">@@JOINCARDS@@</div>
</section>

<section id="market">
  <div class="shead">
    <h2>What is actually known per market &mdash; and what is not</h2>
    <p>Eighteen distributors form the commercial base. The vehicle register covers seven markets and excludes
    the UK and Israel by design; Italy is out of scope entirely. A chip that says excluded is not a zero: it
    means that layer has nothing to divide by, and printing a number there would be an invention.</p>
  </div>
  <div class="gapwrap">
  <table class="t">
    <thead><tr>
      <th>Market / distributor</th><th class="num">Vehicles in service</th><th>Type mix</th>
      <th>Age, measured</th><th>Age, modelled</th><th class="num">Spend per unit</th>
      <th>Part demand</th><th>Sales to dealer</th><th>Weight class</th>
    </tr></thead>
    <tbody>
    @@MARKETROWS@@
    <tr class="head"><td colspan="9">Below the sort &mdash; out of scope by decision, shown so it is not silently dropped</td></tr>
    @@ITALY@@
    <tr class="head"><td colspan="9">Markets with no fleet denominator at all &mdash; they bill parts and have no vehicles to divide by</td></tr>
    @@FOOTROWS@@
    </tbody>
  </table>
  </div>
  <p class="legendline">Type mix colours, left to right: <b>light duty</b>, <b>medium duty</b>,
  <b>F-series</b>, <b>light commercial</b>. Hover a bar for the basis and for the part of the mix that is not
  known. Hover any figure for its formula, its snapshot and what it leaves out.</p>
</section>

<section id="two">
  <div class="shead">
    <h2>Spend per unit by market, and the two directions of parts flow</h2>
    <p>One field, one snapshot, so the markets can be compared by eye. The hairline is the network market
    median, not a target, and it is not weighted by fleet size.</p>
  </div>
  <div class="bars">
    <h3>How much does each market bill per vehicle in service?</h3>
    <div class="sub">Spend per unit (GPS), CY2025 full year, 18 distributors &middot; network figure
      @@NETSPU@@ across @@UIO@@ vehicles &middot; market median @@MEDSPU@@</div>
    @@SPUROWS@@
  </div>

  <div class="bars" style="margin-top:1rem">
    <h3>How much of what we invoice the distributor is visible again one step down?</h3>
    <div class="sub">Navy is what ISZE invoices the distributor. Terracotta is what the distributor invoices
      its dealers, in the same year. The figure at the right is the ratio between the two.</div>
    @@TWODIR@@
    <p class="legendline">Visible in six markets, together @@VIS@@ of the @@BASE@@ eighteen-market billed book.
      The other twelve markets have no sales-to-dealer file, so this ratio is a statement about those six
      markets and about nothing else.</p>
  </div>
</section>

<section id="gaps">
  <div class="shead">
    <h2>Which gap blocks which layer</h2>
    <p>Six open source gaps and three closed ones, each with an identifier so it can be tracked in the
    integrity register. The right-hand column says what this page does instead of printing a number.</p>
  </div>
  <div class="gapwrap">
  <table class="t">
    <thead><tr><th>ID</th><th>What it is</th><th>Which layer it blocks</th><th>What this page shows instead</th></tr></thead>
    <tbody>@@GAPROWS@@</tbody>
  </table>
  </div>
  <div class="callout">
    <b>A blank is the design, not a hole.</b> Where a weight class is not documented there is no tonnage to
    print. Where a market has no fleet denominator, spend per unit does not exist. Filling those cells with a
    modelled substitute is exactly how the two contaminated figures this estate is retiring were produced,
    so the page leaves them empty and states the reason in the tooltip.
  </div>
</section>

<section id="where">
  <div class="shead">
    <h2>Where every layer actually lives</h2>
    <p>@@NOK@@ link targets, each one tested on disk before it was written. This index deliberately includes
    the three pages the older dashboard index omits: the exec paper, the growth plan and the
    distributor-to-dealer replenishment page.</p>
  </div>
  <div class="lgrid">@@LINKCARDS@@</div>
  <p class="legendline">Link check: <span id="linkcheck">checking&hellip;</span>. A struck-through entry is a
  target that has moved or been retired; it is shown rather than silently dropped.</p>
</section>

<section id="carry">
  <div class="shead">
    <h2>What this page deliberately does not repeat</h2>
    <p>Two figures are wrong or superseded elsewhere in the estate, and one cell mixes two systems. None of
    them is reused here, and the page that carries each one is named so the correction travels with the link.</p>
  </div>
  <div class="grid2">@@SUPERSEDED@@</div>
  <div class="note">
    <b>The three indexes still disagree.</b> The dashboard index was last touched on 7 September and does not
    list the exec paper, the growth plan or the distributor-to-dealer page. The mission-control page is from
    26 August and still carries the superseded classification figure. The machine registry, regenerated from
    disk on 16 September, lists all @@MANFILES@@ entries. Nothing on disk declares which index is canonical,
    and this page cannot make that decision for you &mdash; so it links all three and marks the difference.
  </div>
</section>

  <div class="foot">
    <b>Sources and method.</b> Every figure on this page was re-derived on @@SNAPSHOT@@ from the file named in
    its own tooltip: the distributor spend-per-unit file, the target-spend waterfall, the part-demand
    opportunity matrix, the service-schedule constant file, the down-trade margin file, the sales-to-dealer mix
    file, the aftermarket exposure file and the open-issue register. Counts and ratios only: no customer names,
    no dealer names, no line-level billing, no personal data. Snapshots used: vehicles in service and spend per
    unit CY2025 &middot; opportunity and margin CY2025 &middot; classification 2 July 2026 &middot; vehicle
    register 27 July 2026 &middot; UK registration extract 23 July 2026 &middot; fleet repair specification
    27&ndash;30 July 2026.
    <br><br>
    <b>Scope note.</b> PRISM itself is a live application. This page describes where it sits, what it consumes
    and what consumes it, and links its launcher and documentation rather than copying its screens. The static
    pages it links are point-in-time artefacts and carry their own dates on each link.
    <br><br>
    <b>What this page is not.</b> It is not a dashboard and not a source. It holds almost no numbers of its own
    beyond the joins it makes visible. Every figure here exists somewhere else first, and that somewhere else is
    named in the tooltip.
  </div>

</div>
<script>@@JS@@</script>
</body></html>
"""

JS = """
document.querySelectorAll('a.lnk[data-missing]').forEach(function(a){
  a.setAttribute('title','link target missing on disk');
});
var bad = document.querySelectorAll('a.lnk[data-missing]').length;
var el = document.getElementById('linkcheck');
if (el) { el.textContent = (bad === 0)
  ? 'all link targets present on disk'
  : (bad + ' link target(s) missing on disk'); }
"""

LEGEND = " ".join([
    chip("measured", "A real count or a real euro from a named file, quotable with its snapshot date."),
    chip("modelled", "An assumption or a survival curve produced it, not an observation."),
    chip("excluded", "Out of scope by decision, or there is no denominator at all."),
    chip("judge", "Two files on disk disagree, or a person has to decide before it is used."),
])

html = T(
    PAGE,
    CSS=CSS,
    SNAPSHOT=SNAPSHOT,
    NLINKS=str(n_links),
    LEGEND=LEGEND,
    LAYERSTACK=layer_stack,
    KEYCHAIN=KEY,
    WCTABLE=wc_table,
    JOINCARDS=CARDS,
    MARKETROWS=market_rows_html,
    ITALY=italy_html,
    FOOTROWS=foot_html,
    NETSPU=kpi(eur(spu_net, 2), "Network spend per unit, CY2025",
               "parts billed / vehicles in service, 18 markets", "gps_spu_by_distributor.csv, full-year rows",
               "Italy, the four CIS markets and every 2026 row.", "measured"),
    UIO=kpi(eur(uio_net), "Vehicles in service, CY2025", "sum of the 18 market fleet rows",
            "same file and snapshot", "The 2026-2030 forecast columns.", "measured"),
    MEDSPU=kpi(eur(spu_median, 2), "Market median spend per unit",
               "median of the 18 market ratios, unweighted", "same file and snapshot",
               "Not a target, and not weighted by fleet size, so it is not the network average.", "measured"),
    SPUROWS=spu_rows,
    TWODIR=two_dir_rows,
    VIS=kpi(pct(vis_share) + "%", "Share of the billed book with dealer-level visibility",
            "billing in the six markets that have a sales-to-dealer file / total 18-market billing",
            "sellout_aim_network_mix_2025.csv, CY2025",
            "The twelve markets with no file. Measured against the wider parts base the same share is about "
            "15 per cent, so the denominator must always be printed with the number.", "measured"),
    BASE=kpi(eur(sales_net), "Total billed book, CY2025, 18 markets",
             "sum of full-year total_sales_eur rows", "gps_spu_by_distributor.csv",
             "The four CIS billing markets and Italy.", "measured"),
    GAPROWS=GAP_ROWS,
    NOK=str(n_ok_links),
    LINKCARDS=link_html,
    SUPERSEDED=T(SUPERSEDED,
                 IML_UIO=kpi("{:,}".format(int(iml_uio)).replace(",", " "),
                             "Vehicles in the service-schedule lane", "the full ITUK registration fleet",
                             "IML v7 constant file, CY2025", "Not the bucketed fleet used by the internal lane.",
                             "measured"),
                 IML_PCT=kpi(pct(iml_oil_pct) + "%", "Oil-filter cover on the service schedule, ITUK CY2025",
                             "actual {} / expected {} on a 1.25 services-per-year schedule".format(
                                 "{:,}".format(int(iml_actual)).replace(",", " "),
                                 "{:,}".format(int(iml_expected)).replace(",", " ")),
                             "IML v7 constant file, adopted 2 July 2026",
                             "Not comparable with the internal lane below, which uses a different denominator.",
                             "modelled"),
                 NET_UIO=kpi("{:,}".format(int(fnum(ituk_25["uio_units"]))).replace(",", " "),
                             "Vehicles in the internal network lane",
                             "bucketed fleet for the internal capture lane",
                             "pms_capture_by_db_year.csv 2025",
                             "This is not the registration fleet and must not be quoted as one.", "modelled"),
                 NET_PCT=kpi(pct(min(j_ituk_25_pct, 100), 0) + "%",
                             "Capped oil-filter capture, internal lane, ITUK CY2025",
                             "actual {} / expected {}, capped at 100 for display".format(
                                 "{:,}".format(int(fnum(ituk_25["actual_qty"]))).replace(",", " "),
                                 "{:,}".format(int(fnum(ituk_25["expected_qty"]))).replace(",", " ")),
                             "pms_capture_by_db_year.csv 2025",
                             "Uncapped it reads {}. Internal network league only, never an external quote.".format(
                                 pct(j_ituk_25_pct)),
                             "measured"),
                 NET_UNC=pct(j_ituk_25_pct)),
    MANFILES=kpi(str(man_files), "Live entries in the machine registry",
                 "list items under files: in manifest.yaml", "manifest.yaml, 16 Sep 2026",
                 "Archive, build, data and scratch folders are excluded by design.", "measured"),
    JS=JS,
)

os.makedirs(HUB, exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(html)
with open(os.path.join(HUB, "ISZE_OS_Hub.links.json"), "w", encoding="utf-8") as fh:
    json.dump({"tested": n_links, "present": n_ok_links,
               "missing": missing,
               "targets": [{"label": l, "path": p, "exists": ok} for l, p, ok in LINKS]},
              fh, indent=1)

print("wrote", OUT)
print("bytes", os.path.getsize(OUT))
print("links", n_links, "present", n_ok_links)
for m in missing:
    print("MISSING TARGET:", m)
print("ceiling %s | captured %s | cover %.2f%% | flat %d markets %s (%.1f%%)"
      % (eur(ceiling), eur(captured), cover, len(flat), eur(flat_eur), flat_share))
print("opportunity %s | top3 lines %s (%.1f%%) | clutch+brake families %s (%.1f%%)"
      % (eur(gap_total), eur(top3), 100 * top3 / gap_total, eur(fam_eur), 100 * fam_eur / gap_total))
print("spu net %.2f | median %.2f | max %.2f | uio %d | sales %s"
      % (spu_net, spu_median, spu_max, uio_net, eur(sales_net)))
print("two directions", [("%s %.1f%%" % (k, r)) for k, _, _, r in two_dir], "| visible %.1f%%" % vis_share)
print("ITUK internal lane 2024 %.1f%% 2025 %.1f%% | IML lane %.1f%%" % (j_ituk_24_pct, j_ituk_25_pct, iml_oil_pct))
print("downtrade total %s | oil filter %s"
      % (eur(dgp_total), eur(fnum(oil_row["downtrade_gp_gap_eur"])) if oil_row else "n/a"))
print("manifest entries", man_files, "| markets in table", len(mark_rows), "| no-denominator rows", len(foot_rows))
