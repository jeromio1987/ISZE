"""Build ISZE_DB_Leakage_Review_CY2025.html

Per-distributor leakage review. Four leaks, one row per distributor.
Three viewer toggles: period (CY2025 / FY2025 Apr-Mar), direction (ISZE->DB /
DB->dealer), warranty (included / excluded).

House rule isze-gaps-need-context.mdc: euro LEADS, units support. Every gap
carries service family + fleet denominator. A unit count is never a finding.

Anchor: CY2025 published demand capture (pms_capture_by_db_year.csv) for the
18-DB fleet base. The FY leg and the DB->dealer leg are derived and labelled.
No chart library, no CDN, no external request.

Run:  python 02_dashboards\\_build\\build_db_leakage_review.py
"""
from __future__ import annotations

import html
import io
import json
import os
import sys
from datetime import date

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
OUT_HTML = os.path.join(ROOT, r"02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html")
OUT_CMD = os.path.join(ROOT, r"02_dashboards\sales\OPEN_ISZE_DB_Leakage_Review.cmd")
D = os.path.join(ROOT, "01_data", "00_derived")
PRISM = os.path.join(ROOT, "03_analytics", "Isuzu", "prism")
SNAPSHOT = "16 September 2026"

if PRISM not in sys.path:
    sys.path.insert(0, PRISM)

# Measured annual distance, km/yr. Model default is a flat 20,000.
KM_MODEL = 20000.0
KM = {
    "IUK": dict(km=14494.0, label="14,494", src="N35 Grafter odometer intervals", note="9,006 mi median, 18,277 odometer intervals, 5,421 vehicles, 2018-2026"),
    "UTI": dict(km=51680.0, label="51,680", src="CV warranty odometer", note="already applied in the model as a 1.25 services/yr override"),
    "N35": dict(km=12165.0, label="12,165", src="CV warranty odometer", note="PROVISIONAL, all-market"),
    "N75": dict(km=35217.0, label="35,217", src="CV warranty odometer", note="PROVISIONAL, all-market"),
    "F": dict(km=45630.0, label="45,630", src="CV warranty odometer", note="PROVISIONAL, all-market"),
}
FAM_GROUPS = {
    "Oil Filter": "Filters", "Fuel Filter": "Filters", "Air Filter": "Filters",
    "Urea (AdBlue) Filter": "Filters", "Blower Unit Filter": "Filters",
    "Brake Pad": "Brakes", "Brake Shoe": "Brakes", "Brake Rotor": "Brakes",
    "Clutch Disc": "Clutch & bearings", "Clutch Pressure Plate": "Clutch & bearings",
    "Clutch Kit": "Clutch & bearings", "Release Bearing": "Clutch & bearings",
    "Pilot Bearing": "Clutch & bearings", "Clutch Booster": "Clutch & bearings",
}
GROUP_ORDER = ["Filters", "Brakes", "Clutch & bearings"]

DEALER_FILES = {
    "IUK": "dealer_sellout_long_IUK_CY2025.csv",
    "ITUK": "dealer_sellout_long_ITUK_CY2025.csv",
    "IRELAND": "dealer_sellout_long_IRELAND_CY2025.csv",
    "GREECE": "dealer_sellout_long_GREECE_CY2025.csv",
    "PORTUGAL": "dealer_sellout_long_PORTUGAL_CY2025.csv",
    "UTI": "dealer_sellout_long_UTI_CY2025.csv",
}
DEALER_FILES_2026 = {
    "IUK": "dealer_sellout_long_IUK_CY2026YTD.csv",
    "ITUK": "dealer_sellout_long_ITUK_CY2026YTD.csv",
    "IRELAND": "dealer_sellout_long_IRELAND_CY2026YTD.csv",
    "PORTUGAL": "dealer_sellout_long_PORTUGAL_CY2026YTD.csv",
    "UTI": "dealer_sellout_long_UTI_CY2026YTD.csv",
    "ROMANIA": "dealer_sellout_long_ROMANIA_CY2026YTD.csv",
}

CY = ("2025-01-01", "2025-12-31")
FY = ("2025-04-01", "2026-03-31")
FYMON = ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
         "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]


# ------------------------------------------------------------------ helpers
def norm_pn(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def n(v, d=0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return round(float(v), d)


# ------------------------------------------------------------------ load
print("loading published demand capture ...", flush=True)
pms = pd.read_csv(os.path.join(D, "pms_capture_by_db_year.csv"))
pms25 = pms[(pms.year == 2025) & (pms.line_type == "total")].copy()
pms25["fam_group"] = pms25.category_label.map(FAM_GROUPS).fillna("Other")

demand = pms25.groupby("distributor_code").agg(
    exp=("expected_qty", "sum"), act=("actual_qty", "sum"),
    gap=("revenue_gap_eur", "sum"), rev=("actual_rev_eur", "sum"),
    uio=("uio_units", "max")).reset_index()
demand["nb"] = (demand.exp - demand.act) / demand.exp * 100
demand["avg_sp"] = demand.apply(
    lambda r: (r.gap / (r.exp - r.act)) if (r.exp - r.act) > 1 else None, axis=1)

fam = pms25.groupby(["distributor_code", "category_label", "fam_group"]).agg(
    exp=("expected_qty", "sum"), act=("actual_qty", "sum"),
    gap=("revenue_gap_eur", "sum")).reset_index()
fam["cap"] = (fam.act / fam.exp * 100).round(1)
fam["avg_sp"] = fam.apply(
    lambda r: (r.gap / (r.exp - r.act)) if (r.exp - r.act) > 1 else None, axis=1)

FAMNET = pms25.groupby(["category_label", "fam_group"]).agg(
    exp=("expected_qty", "sum"), act=("actual_qty", "sum"),
    gap=("revenue_gap_eur", "sum")).reset_index()
FAMNET["cap"] = (FAMNET.act / FAMNET.exp * 100).round(1)
FAMNET["avg_sp"] = FAMNET.apply(
    lambda r: (r.gap / (r.exp - r.act)) if (r.exp - r.act) > 1 else None, axis=1)
FAMNET = FAMNET.sort_values("gap", ascending=False)

NETWORK = dict(
    exp=float(demand.exp.sum()), act=float(demand.act.sum()),
    gap=float(demand.gap.sum()), uio=float(demand.uio.sum()))
NETWORK["nb"] = (NETWORK["exp"] - NETWORK["act"]) / NETWORK["exp"] * 100
NETWORK["notbought"] = NETWORK["exp"] - NETWORK["act"]

print("tagging billing extract (one pass, ~90s) ...", flush=True)
from modules.pms_tagging import tag_pms_sales
from modules.pms_engine import CATEGORY_LABELS, PMS_PN_REGISTRY, _MULTI_MODEL

PN_CAT: dict[str, str] = {}
for _pn, _v in PMS_PN_REGISTRY.items():
    PN_CAT.setdefault(str(_pn).lstrip("0"), _v["category"])
for _pn, _maps in _MULTI_MODEL.items():
    PN_CAT.setdefault(str(_pn).lstrip("0"), _maps[0]["category"])

dim = pd.read_csv(os.path.join(D, "bvp_pn_dimension.csv"))
sf = pd.read_parquet(os.path.join(D, "sales_fact.parquet"))
ddim = pd.read_csv(os.path.join(D, "distributor_dimension.csv"))
sf["db"] = sf.sold_to_sap.map(dict(zip(ddim.sold_to_sap, ddim.distributor_code)))
sf["billing_date"] = pd.to_datetime(sf.billing_date)
sf["ym"] = sf.billing_date.dt.strftime("%Y-%m")
sf = sf[~sf.saty.isin(["CR", "RE"])].copy()

tag = tag_pms_sales(sf, dim, fill_catalog_pms=True)
tag = tag[tag.is_pms].copy()
if "pms_capture_eligible" in tag.columns:
    tag = tag[tag.pms_capture_eligible].copy()
tag["category_label"] = tag.pms_category.map(CATEGORY_LABELS).fillna(tag.pms_category)
print("  PMS-tagged billing lines:", len(tag), flush=True)

CNT = tag[tag.db.notna() & (tag.billing_date >= CY[0]) & (tag.billing_date <= CY[1])]
FNT = tag[tag.db.notna() & (tag.billing_date >= FY[0]) & (tag.billing_date <= FY[1])]

rat = (FNT.groupby(["db", "category_label"]).billed_qty.sum()
       / CNT.groupby(["db", "category_label"]).billed_qty.sum()).dropna()
rat = rat.clip(0.3, 1.6)
print("  FY/CY demand ratios: median",
      round(float(rat.median()), 3), "min",
      round(float(rat.min()), 3), "max",
      round(float(rat.max()), 3), flush=True)

mis = FNT.groupby("db").net_sales_value.sum() - CNT.groupby("db").net_sales_value.sum()
print("  FY vs CY billed EUR (all parts, 18 DBs):",
      round(float(CNT.net_sales_value.sum())), "->",
      round(float(FNT.net_sales_value.sum())), flush=True)

print("loading billing + warranty ...", flush=True)
gps = pd.read_csv(os.path.join(D, "gps_spu_by_distributor.csv"))
g25 = gps[gps.year == 2025].set_index("distributor_code")


# FY2025 billed straight off the billing extract, so markets without a GPS row
# still carry a billing column.
bill_fy_all = sf[sf.db.notna() & sf.billing_date.between(FY[0], FY[1])].groupby("db").net_sales_value.sum()
print("  CY2025 billed (published):",
      round(float(g25.total_sales_eur.sum())),
      "| warranty:", round(float(g25.warranty_parts_eur.sum())),
      "| FY2025 billed (local):", round(float(bill_fy_all.sum())), flush=True)

print("loading replenishment ...", flush=True)
rep = pd.read_csv(os.path.join(D, "replenishment_exceptions_cy2025.csv"))
bridge = pd.read_parquet(os.path.join(D, "replenishment_bridge.parquet"))
signals = ("leakage_high_sellthrough", "overstock_low_sellthrough", "overstock_no_sellout")
excfy = bridge[bridge.pipeline_signal.isin(signals) & bridge.year_month.isin(FYMON)].copy()
# Rank by sell-through where the line is a leakage signal, otherwise by billed
# quantity: a leakage line is urgent because dealers are selling it, an
# overstock line because we are sitting on it.
excfy["rank_key"] = [s if r.startswith("leakage") else b
                     for r, s, b in zip(excfy.pipeline_signal, excfy.sellout_qty, excfy.bill_qty)]
excfy = excfy.sort_values(["distributor_code", "pipeline_signal", "rank_key"],
                          ascending=[True, True, False])
excfy = excfy.groupby(["distributor_code", "pipeline_signal"]).head(100)

print("loading mix + exposure + no-price ...", flush=True)
mix = pd.read_csv(os.path.join(D, "mix_genuine_bvp_pms.csv"))
mix["bvp_eur"] = pd.to_numeric(mix.bvp_eur, errors="coerce")
mix["genuine_eur"] = pd.to_numeric(mix.genuine_eur, errors="coerce")
m25 = mix[mix.year == 2025].groupby("distributor_code").agg(
    bvp=("bvp_eur", "sum"), gen=("genuine_eur", "sum"))
m25["share"] = m25.bvp / (m25.bvp + m25.gen) * 100

pt = tag.copy()
pt["role"] = pt.pms_type.map({"genuine": "genuine", "bvp": "bvp"})
pt_cy = pt[pt.billing_date.between(CY[0], CY[1])].groupby(["db", "role"]).net_sales_value.sum().unstack(fill_value=0.0)
pt_fy = pt[pt.billing_date.between(FY[0], FY[1])].groupby(["db", "role"]).net_sales_value.sum().unstack(fill_value=0.0)


def share_of(d: pd.DataFrame) -> pd.Series:
    if d.empty or "bvp" not in d.columns:
        return pd.Series(dtype=float)
    tot = d.get("bvp", 0) + d.get("genuine", 0)
    return (d.get("bvp", 0) / tot * 100).replace([float("inf")], pd.NA)


mix_cy_calc = share_of(pt_cy)
mix_fy_calc = share_of(pt_fy)

aim = pd.read_csv(os.path.join(D, "aim_exposure_by_db_year.csv"))
a25 = aim[aim.year == 2025].set_index("distributor_code")

npr = pd.read_csv(os.path.join(D, "no_pr00_gap_cy2025_ranked.csv"), dtype={"part_number": str})
spdb = sf[sf.billing_date.between(CY[0], CY[1]) & sf.part_number.isin(set(npr.part_number))]
spdb = spdb.groupby("db").net_sales_value.sum()

npr["is_lube"] = npr.description.str.contains("Rim|Rimula|Tellus", case=False, na=False)
LUBE_EUR = float(npr.loc[npr.is_lube, "cy2025_eur"].sum())
NPR_TOTAL = float(npr.cy2025_eur.sum())

buckets = pd.read_csv(os.path.join(ROOT, r"03_analytics\Isuzu\prism\data\uio_by_model_bucket.csv")).set_index("distributor_code")
scope = ddim[ddim.network_role == "network_db"].groupby("distributor_code").scope.first()
region = ddim[ddim.network_role == "network_db"].groupby("distributor_code").region.first()
NETDBS = sorted(ddim.loc[ddim.network_role == "network_db", "distributor_code"].unique())

im = pd.read_excel(
    os.path.join(ROOT, r"01_data\08_Distributor\EU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx"),
    sheet_name=0)
# IMIT's own distributor names -> our network codes. Only these markets are in
# the IMIT extract; IUK is absent, which is why 14,494 km/yr comes from the
# N35 odometer work instead.
IMIT_NAME = {
    "ISUZU SALES DEUTSCHLAND - ISD": "GERMANY",
    "ISUZU BENELUX - BELGIUM": "BELGIUM",
    "A. LOUTSIOS & SONS": "CYPRUS",
    "ISUZU Danmark": "DENMARK",
    "Isuzu Motor Finland OY": "FINLAND",
    "PETROS PETROPOULOS": "GREECE",
    "WAE LTD.": "HUNGARY",
    "BL ehf.": "ICELAND",
    "Isuzu Ireland 2020 Unlimited Company": "IRELAND",
    "GASANZAMMIT MOTORS LIMITED": "MALTA",
    "RSA": "NORWAY",
    "IMOTORS LDA": "PORTUGAL",
    "ISUZU ROM AUTO SRL": "ROMANIA",
    "UMI": "UMI",
}
im["db"] = im.DistributorName.map(IMIT_NAME)
imit = im[im.db.notna()].set_index("db")["Average of Mileage per year"].round(0).to_dict()

dealer_qty = {}
dealer_files = {}
for _db, _f in {**DEALER_FILES, **DEALER_FILES_2026}.items():
    dealer_files.setdefault(_db, []).append(_f)
for db, files in dealer_files.items():
    frames = []
    for f in files:
        d = pd.read_csv(os.path.join(D, f), usecols=["period", "period_grain", "part_number", "qty"])
        d = d[d.period_grain == "month"].copy()
        d["month"] = d.period
        d["pn"] = norm_pn(d.part_number).str.lstrip("0")
        d["category_label"] = d.pn.map(PN_CAT).map(CATEGORY_LABELS).fillna("other")
        frames.append(d[["month", "pn", "category_label", "qty"]])
    d = pd.concat(frames, ignore_index=True).drop_duplicates(["month", "pn", "category_label"])
    key = db
    for pk, frame in (("cy", d[d.month.str.startswith("2025")]),
                      ("fy", d[d.month.isin(FYMON)])):
        if frame.empty:
            continue
        dealer_qty.setdefault(key, {})[pk] = frame.groupby("category_label").qty.sum().to_dict()
        dealer_qty[key][pk + "_total"] = float(frame.qty.sum())
        dealer_qty[key][pk + "_months"] = int(frame.month.nunique())


FYM_NEED = 11
DEALER_FY_MONTHS = {}
for _db in dealer_files:
    DEALER_FY_MONTHS[_db] = int(dealer_qty.get(_db, {}).get("fy_months") or 0)


def fy_months_of(db, months):
    return sorted({m for m in months if m in FYMON})


print("  dealer-file fiscal months:", DEALER_FY_MONTHS, flush=True)

ds = pd.read_csv(os.path.join(D, "dealer_sellout_gps_2025.csv"))
dealer_eur_cy = ds.groupby("distributor_code").total_eur.sum()

print("assembling payload ...", flush=True)
dbs = []
for db in NETDBS:
    dm = demand[demand.distributor_code == db]
    dm = dm.iloc[0] if len(dm) else None
    ux = buckets.loc[db] if db in buckets.index else None
    n75 = float(ux.cv_std_uio + ux.f_series_uio) if ux is not None else None
    lcv = float(ux.lcv_uio) if ux is not None else None
    if n75 is None:
        wc = "no fleet model"
    elif n75 > 0 and lcv > 0:
        wc = "truck + light"
    elif n75 > 0:
        wc = "truck class"
    else:
        wc = "light commercial"
    rec = dict(
        db=db,
        scope=str(scope.get(db)) if pd.notna(scope.get(db, None)) else None,
        region=str(region.get(db)) if pd.notna(region.get(db, None)) else None,
        uio=n(dm.uio) if dm is not None else None,
        n75=n(n75), lcv=n(lcv), wc=wc,
        imit=n(imit.get(db)),
        km=KM[db]["label"] if db in KM else None)
    if dm is not None:
        cy_gap = float(dm.gap)
        cy_exp = float(dm.exp)
        cy_act = float(dm.act)
        cy_nb = float(dm.nb)
        cy_cap = (1 - cy_nb / 100) * 100
        fams = []
        fy_gap = 0.0
        fy_exp = 0.0
        fy_act = 0.0
        for _, fr in fam[fam.distributor_code == db].iterrows():
            r = float(rat.get((db, fr.category_label), 1.0))
            f_act = float(fr.act) * r
            f_gap = max(float(fr.exp) - f_act, 0.0) * (float(fr.avg_sp) if pd.notna(fr.avg_sp) else 0.0)
            fams.append(dict(
                label=fr.category_label, group=fr.fam_group,
                gap=n(fr.gap), cap=n(fr.cap, 1), fy_gap=n(f_gap),
                act_qty=n(f_act), exp_qty=n(fr.exp)))
            fy_gap += f_gap
            fy_exp += float(fr.exp)
            fy_act += f_act
        rec["demand"] = dict(
            cy=dict(gap=n(cy_gap), exp=n(cy_exp), act=n(cy_act),
                    nb=n(cy_nb, 1), cap=n(cy_cap, 1)),
            fy=dict(gap=n(fy_gap), exp=n(fy_exp), act=n(fy_act),
                    nb=n((((fy_exp - fy_act) / fy_exp) * 100), 1) if fy_exp else None,
                    cap=n(((fy_act / fy_exp) * 100), 1) if fy_exp else None))
        rec["fam"] = fams
    else:
        rec["demand"] = dict(cy=None, fy=None)
        rec["fam"] = []

    dq = dealer_qty.get(db)
    dleg = dict(cy=None, fy=None)
    if dq and dq.get("cy"):
        rows, s_gap, s_act, s_exp = [], 0.0, 0.0, 0.0
        for _, fr in fam[fam.distributor_code == db].iterrows():
            got = float(dq["cy"].get(fr.category_label, 0.0))
            sp = float(fr.avg_sp) if pd.notna(fr.avg_sp) else 0.0
            g = max(float(fr.exp) - got, 0.0) * sp
            rows.append(dict(
                label=fr.category_label, got=n(got), exp_qty=n(fr.exp), gap=n(g),
                cap=n(((got / float(fr.exp)) * 100), 1) if fr.exp else None))
            s_gap += g
            s_act += got
            s_exp += float(fr.exp)
        dleg["cy"] = dict(
            gap=n(s_gap), act=n(s_act), exp=n(s_exp),
            cap=n(((s_act / s_exp) * 100), 1) if s_exp else None,
            nb=n((((s_exp - s_act) / s_exp) * 100), 1) if s_exp else None,
            months=dq.get("cy_months"), proj=False,
            eur=n(dealer_eur_cy.get(db)), fam=rows)
        fm = DEALER_FY_MONTHS.get(db, 0)
        if dq and dq.get("fy") and fm >= 9:
            scale = 12.0 / fm if fm < 12 else 1.0
            rows, s_gap, s_act, s_exp = [], 0.0, 0.0, 0.0
            for _, fr in fam[fam.distributor_code == db].iterrows():
                got = float(dq["fy"].get(fr.category_label, 0.0)) * scale
                sp = float(fr.avg_sp) if pd.notna(fr.avg_sp) else 0.0
                g = max(float(fr.exp) - got, 0.0) * sp
                rows.append(dict(
                    label=fr.category_label, got=n(got), exp_qty=n(fr.exp), gap=n(g),
                    cap=n(((got / float(fr.exp)) * 100), 1) if fr.exp else None))
                s_gap += g
                s_act += got
                s_exp += float(fr.exp)
            # A part-year fiscal window is annualised by the same ratio the
            # calendar-level euro figure carries, so the two legs are comparable.
            eur_fy = None
            if db in dealer_eur_cy.index and dq.get("cy_total"):
                eur_fy = n((float(dealer_eur_cy[db]) / float(dq["cy_total"])) * s_act)
            dleg["fy"] = dict(
                gap=n(s_gap), act=n(s_act), exp=n(s_exp),
                cap=n(((s_act / s_exp) * 100), 1) if s_exp else None,
                nb=n((((s_exp - s_act) / s_exp) * 100), 1) if s_exp else None,
                months=fm, proj=(fm < 12), eur=eur_fy, fam=rows)
    rec["dealer"] = dleg

    rr = rep[rep.distributor_code == db]
    rec["rep"] = dict(cy=None, fy=None)
    if len(rr):
        g = rr.groupby("pipeline_signal").bill_eur.sum()
        rec["rep"]["cy"] = dict(
            total=n(g.sum()),
            pull=n(g.get("leakage_high_sellthrough", 0)),
            over_low=n(g.get("overstock_low_sellthrough", 0)),
            over_none=n(g.get("overstock_no_sellout", 0)),
            nobill=n(g.get("leakage_no_bill", 0)),
            pns=int(rr.part_number.nunique()), rows=int(len(rr)))
        rf = excfy[excfy.distributor_code == db]
        if len(rf) and len(fy_months_of(db, rf.year_month.unique())) >= FYM_NEED:
            g = rf.groupby("pipeline_signal").bill_eur.sum()
            rec["rep"]["fy"] = dict(
                total=n(g.sum()),
                pull=n(g.get("leakage_high_sellthrough", 0)),
                over_low=n(g.get("overstock_low_sellthrough", 0)),
                over_none=n(g.get("overstock_no_sellout", 0)),
                nobill=n(g.get("leakage_no_bill", 0)),
                pns=int(rf.part_number.nunique()), rows=int(len(rf)))

    ms = float(m25.loc[db, "share"]) if db in m25.index else None
    mf = None
    if ms is not None and db in mix_cy_calc.index and db in mix_fy_calc.index:
        mf = ms + (float(mix_fy_calc[db]) - float(mix_cy_calc[db]))
    rec["mix"] = dict(cy=n(ms, 1), fy=n(mf, 1))

    if db in a25.index:
        rec["expo"] = dict(
            pct=n(float(a25.loc[db, "high_risk_rev_pct"]) * 100, 1),
            eur=n(float(a25.loc[db, "high_risk_rev_eur"])))
    else:
        rec["expo"] = None
    rec["np"] = dict(eur=n(spdb.get(db, 0)),
                     pns=int(npr.part_number.isin(set(sf.loc[sf.db == db, "part_number"])).sum()))

    wr = float(g25.loc[db, "warranty_parts_eur"]) if db in g25.index and pd.notna(g25.loc[db, "warranty_parts_eur"]) else None
    bcy = float(g25.loc[db, "total_sales_eur"]) if db in g25.index and pd.notna(g25.loc[db, "total_sales_eur"]) else None
    bfy = float(bill_fy_all.get(db)) if db in bill_fy_all.index else None
    rec["bill"] = dict(
        cy_inc=n(bcy), cy_exc=n(bcy - wr) if bcy is not None and wr is not None else None,
        fy_inc=n(bfy), fy_exc=n(bfy - wr) if bfy is not None and wr is not None else None,
        warr=n(wr))
    dbs.append(rec)

dbs.sort(key=lambda r: -(r["demand"]["cy"]["gap"] if r["demand"]["cy"] else -1))

NW = dict(
    exp=n(NETWORK["exp"]), act=n(NETWORK["act"]), gap=n(NETWORK["gap"]),
    nb=n(NETWORK["nb"], 1), notbought=n(NETWORK["notbought"]), uio=n(NETWORK["uio"]))
NW["rep_cy"] = n(sum(r["rep"]["cy"]["total"] for r in dbs if r["rep"]["cy"]))
NW["rep_cy_dbs"] = len([r for r in dbs if r["rep"]["cy"]])
NW["rep_fy"] = n(sum(r["rep"]["fy"]["total"] for r in dbs if r["rep"]["fy"]))
NW["rep_fy_dbs"] = len([r for r in dbs if r["rep"]["fy"]])
NW["pull_cy"] = n(sum(r["rep"]["cy"]["pull"] for r in dbs if r["rep"]["cy"]))
NW["pull_pn_cy"] = int(rep[rep.pipeline_signal == "leakage_high_sellthrough"].part_number.nunique())
NW["pull_pn_rows"] = int(len(rep[rep.pipeline_signal == "leakage_high_sellthrough"]))
NW["over_cy"] = n(sum(r["rep"]["cy"]["over_low"] + r["rep"]["cy"]["over_none"] for r in dbs if r["rep"]["cy"]))
NW["rep_rows_cy"] = int(len(rep))
NW["billed_cy"] = n(sum(r["bill"]["cy_inc"] or 0 for r in dbs))
NW["billed_fy"] = n(sum(r["bill"]["fy_inc"] or 0 for r in dbs))
NW["warr"] = n(sum(r["bill"]["warr"] or 0 for r in dbs))
NW["warr_pct"] = n((NW["warr"] / NW["billed_cy"] * 100), 1)
NW["dealer_cy"] = n(sum(r["dealer"]["cy"]["eur"] or 0 for r in dbs if r["dealer"]["cy"]))
NW["dealer_dbs"] = len([r for r in dbs if r["dealer"]["cy"]])
NW["np"] = n(NPR_TOTAL)
NW["np_pns"] = int(npr.part_number.nunique())
NW["np_lube"] = n(LUBE_EUR)
NW["np_lube_pct"] = n((LUBE_EUR / NPR_TOTAL) * 100, 1)
NW["np_top"] = n(float(npr.cy2025_eur.max()))
NW["np_top_pct"] = n((float(npr.cy2025_eur.max()) / NPR_TOTAL) * 100, 1)
NW["expo_max"] = n(max((r["expo"]["pct"] for r in dbs if r["expo"]), default=0), 1)
NW["expo_max_db"] = max((r for r in dbs if r["expo"]), key=lambda r: r["expo"]["pct"])["db"]
NW["mix_worst"] = max((r for r in dbs if r["mix"]["cy"]), key=lambda r: r["mix"]["cy"])["db"]
NW["mix_worst_v"] = max(r["mix"]["cy"] for r in dbs if r["mix"]["cy"])
NW["spu"] = n(NW["billed_cy"] / sum(r["uio"] or 0 for r in dbs))
NW["iuk_de"] = n(sum(r["demand"]["cy"]["gap"] for r in dbs if r["db"] in ("IUK", "GERMANY")))
NW["iuk_de_pct"] = n((NW["iuk_de"] / NW["gap"] * 100), 1)

# IUK mileage correction: the model's flat 20,000 km/yr against the measured
# N35 Grafter distance. Expected demand scales with the ratio; actual sales do not.
iuk = next(r for r in dbs if r["db"] == "IUK")
iuk_fam = fam[fam.distributor_code == "IUK"]
scale = KM["IUK"]["km"] / KM_MODEL
iuk_adj_exp = float(iuk_fam.exp.sum()) * scale
iuk_act = float(iuk_fam.act.sum())
iuk_sp = float(iuk_fam.gap.sum()) / (float(iuk_fam.exp.sum()) - iuk_act)
IUK_ADJ = dict(
    scale=n(scale, 3),
    exp=n(iuk_adj_exp), act=n(iuk_act),
    gap=n(max(iuk_adj_exp - iuk_act, 0) * iuk_sp),
    cap=n((iuk_act / iuk_adj_exp) * 100, 1),
    nb=n(((iuk_adj_exp - iuk_act) / iuk_adj_exp) * 100, 1),
    gap_now=n(float(iuk_fam.gap.sum())),
    cap_now=n((iuk_act / float(iuk_fam.exp.sum())) * 100, 1),
    cut=n(1 - (max(iuk_adj_exp - iuk_act, 0) * iuk_sp) / float(iuk_fam.gap.sum()), 3),
    km=KM["IUK"]["km"], km_model=KM_MODEL)
print("  IUK mileage correction:", IUK_ADJ, flush=True)

npr_sorted = npr.sort_values("cy2025_eur", ascending=False)
NPLIST = [
    dict(rank=int(r["rank"]), pn=str(r.part_number), desc=str(r.description),
         eur=n(r.cy2025_eur), reason=str(r.gap_reason).replace("_", " "),
         lube=bool(r.is_lube))
    for _, r in npr_sorted.iterrows()]

PAYLOAD = dict(
    meta=dict(snapshot=SNAPSHOT, built=date.today().isoformat(),
              cy=list(CY), fy=list(FY), km_model=KM_MODEL,
              n_dbs=len(dbs), n_fleet_dbs=int(len(demand)), anchor="CY2025"),
    nw=NW, dbs=dbs, noprice=NPLIST, groups=GROUP_ORDER)
FAMNET_JSON = [
    dict(label=r.category_label, group=r.fam_group,
         gap=n(r.gap, 0), cap=n(r.cap, 1), exp=n(r.exp), act=n(r.act),
         avg_sp=n(r.avg_sp, 2) if pd.notna(r.avg_sp) else None)
    for _, r in FAMNET.iterrows()]
print("payload dbs:", len(dbs), "| fam rows/IUK:", len(iuk_fam), flush=True)

# ------------------------------------------------------------------ render
def esc(s):
    return html.escape(s, quote=True)


E = "\u20ac"


def eur_py(v):
    if v is None:
        return "&mdash;"
    a = abs(v)
    if a >= 1000000.0:
        return f"{E}{v / 1000000.0:,.2f}M"
    if a >= 1000.0:
        return f"{E}{v / 1000.0:,.0f}k"
    return f"{E}{v:,.0f}"


def num_py(v):
    if v is None:
        return "&mdash;"
    return f"{v:,.0f}"


def one_py(v, s):
    if v is None:
        return "&mdash;"
    return f"{v:,.1f}{s}"


def tip_py(title, formula, src, excl, settings):
    return (f'<span class="tip"><b>{esc(title)}</b>'
            f'<span class="tr"><i>Formula</i>{formula}</span>'
            f'<span class="tr"><i>Snapshot &amp; source</i>{src}</span>'
            f'<span class="tr"><i>Settings that produced this figure</i>{settings}</span>'
            f'<span class="tr warn"><i>Not included</i>{excl}</span></span>')


CY_S = "Period CY2025 (Jan&ndash;Dec) &middot; Direction ISZE &rarr; DB &middot; Warranty included"


def tipg(t, f, s, e):
    return tip_py(t, f, s, e, CY_S)

h = []
# Ireland has no DB->dealer leg (no dealer-sales file), so the original builder
# raised TypeError at line 823 formatting the Ireland story card. Guard that one
# field. The value is unchanged wherever the leg exists, and no output number
# depends on it: all four comparison points are the distributor records, the
# network block, the family table and the no-price list.
IRELAND_DEALER_CAP = next((r["dealer"]["cy"]["cap"] for r in dbs
                           if r["db"] == "IRELAND" and r["dealer"]["cy"]), None)
h.append(__EXACT_C312__)
h.append(__FSTR_000__)
h.append(__EXACT_C327__)
h.append(__EXACT_C328__)
h.append(__FSTR_001__)
h.append(__EXACT_C332__)
h.append(__EXACT_C333__)
h.append(__FSTR_002__)
h.append(__FSTR_003__)
h.append(__FSTR_004__)
for x in NPLIST[:8]:
    h.append(__FSTR_005__)
h.append(__EXACT_C363__)
h.append(__FSTR_006__)
h.append(__FSTR_007__)
h.append(__FSTR_008__)
h.append(__EXACT_C399__ + SNAPSHOT + __EXACT_C400__ + json.dumps(PAYLOAD, default=str)
         + __EXACT_C401__ + json.dumps(IUK_ADJ)
         + __EXACT_C402__ + json.dumps(KM)
         + __EXACT_C403__ + json.dumps(FAMNET_JSON, default=str)
         + __EXACT_C405__)
JS = __EXACT_C406__
h.append("<script>" + JS + "</script></body></html>")

os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
with open(OUT_HTML, "w", encoding="utf-8") as fh:
    fh.write("\n".join(h))
with open(OUT_CMD, "w", encoding="ascii", newline="\r\n") as fh:
    fh.write('@echo off\nstart "" "%~dp0ISZE_DB_Leakage_Review_CY2025.html"\n')
print("WROTE", OUT_HTML, round(os.path.getsize(OUT_HTML) / 1024, 1), "KB")
print("WROTE", OUT_CMD)
print("charts: 6 | league rows:", len(dbs), "| no-price rows:", len(NPLIST))
