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
h.append('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>Aftermarket opportunity diagnostics &mdash; CY2025</title>\n<style>\n:root{--navy:#15233c;--navy2:#1a2b4a;--paper:#f7f4ee;--ink:#222;--terra:#c0552d;\n--muted:#6b6256;--line:#e5e0d6;--blue:#2b4a78;--grey:#8b8578;--paper2:#f2ede2}\n*{box-sizing:border-box}\nhtml{-webkit-text-size-adjust:100%}\nbody{margin:0;background:var(--paper);color:var(--ink);\nfont-family:-apple-system,"Segoe UI",system-ui,sans-serif;font-size:14px;line-height:1.5;overflow-x:hidden}\nh1,h2,h3{font-family:Georgia,\'Times New Roman\',serif;margin:0}\n.wrap{max-width:1280px;margin:0 auto;padding:0 18px 3rem}\n.hero{background:var(--navy);color:var(--paper);padding:2rem 0 1.6rem;border-bottom:4px solid var(--terra)}\n.hero .in{max-width:1280px;margin:0 auto;padding:0 18px}\n.hero .kick{font-size:.68rem;letter-spacing:.2em;text-transform:uppercase;color:#e8b48c}\n.hero h1{font-size:1.9rem;margin:.3rem 0 .45rem;line-height:1.15}\n.hero p{margin:0;color:#c9cedb;max-width:940px;font-size:.9rem}\n.hstats{display:flex;gap:2rem;flex-wrap:wrap;margin-top:1.1rem}\n.hstat .v{font-family:Georgia,serif;font-size:1.6rem;color:#fff;font-variant-numeric:tabular-nums}\n.hstat .l{font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;color:#aeb9cf;max-width:210px}\nsection{padding:1.7rem 0 .4rem;border-top:1px solid var(--line);margin-top:1.1rem}\nsection:first-of-type{border-top:0}\nh2{font-size:1.32rem;color:var(--navy);margin-bottom:.25rem}\n.shead p{color:#454545;font-size:.89rem;margin:.25rem 0 .9rem;max-width:960px}\n.tgl{position:sticky;top:0;z-index:40;background:#fff;border:1px solid var(--line);\nborder-radius:9px;padding:.6rem .85rem;display:flex;gap:1.3rem;flex-wrap:wrap;align-items:center;\nmargin:.9rem 0 .5rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}\n.tgl .grp{display:flex;align-items:center;gap:.35rem;flex-wrap:wrap}\n.tgl .gl{font-size:.64rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:700}\n.tgl button{font:inherit;font-size:.79rem;padding:.24rem .65rem;border:1px solid var(--line);\nbackground:#fbf9f5;border-radius:6px;cursor:pointer;color:var(--ink)}\n.tgl button.on{background:var(--navy);color:#fff;border-color:var(--navy)}\n.tgl button:focus-visible{outline:2px solid var(--terra);outline-offset:1px}\n#avail{background:#fdf6f1;border:1px solid #e6bfa6;border-left:4px solid var(--terra);\nborder-radius:8px;padding:.6rem .8rem;margin:.1rem 0 .9rem;font-size:.82rem;display:none}\n#avail.show{display:block}\n#avail ul{margin:.3rem 0 0;padding-left:1.1rem}\ntable{width:100%;border-collapse:collapse;background:#fff;font-size:.82rem}\nth,td{padding:.42rem .55rem;text-align:right;border-bottom:1px solid #f0ece4;\nfont-variant-numeric:tabular-nums}\nth{background:var(--navy);color:var(--paper);font-weight:600;font-size:.68rem;\ntext-transform:uppercase;letter-spacing:.03em;text-align:right;white-space:nowrap}\nth:first-child,td:first-child{text-align:left}\ntbody tr:hover{background:#fdf9f5}\ntr.tot td{font-weight:700;background:var(--paper2);border-top:2px solid var(--navy)}\ntd.null{color:#a9a49a;font-style:italic;font-size:.76rem}\n.chip{display:inline-block;font-size:.6rem;padding:.03rem .32rem;border-radius:999px;\nborder:1px solid #cbc4b4;color:var(--muted);margin-left:.28rem;vertical-align:middle;white-space:nowrap}\n.chip.terra{border-color:#dcae94;color:#8a3a17}\n.chip.blue{border-color:#a9bcd6;color:var(--blue)}\n.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;-webkit-overflow-scrolling:touch}\n.note{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);\nborder-radius:8px;padding:.75rem .9rem;margin:.8rem 0;font-size:.83rem}\n.callout{background:#fdf6f1;border:1px solid #e6bfa6;border-left:4px solid var(--terra);\nborder-radius:8px;padding:.75rem .9rem;margin:.8rem 0;font-size:.83rem}\n.callout b{font-family:Georgia,serif;color:#8a3a17}\n.g2{display:grid;grid-template-columns:1fr 1fr;gap:.9rem}\n.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.9rem}\n.dbfocus{background:#fff;border:1px solid var(--line);border-radius:9px;padding:.9rem 1rem}\n.dbfocus h3{font-size:1.02rem;color:var(--navy);margin-bottom:.15rem}\n.dbfocus .tagline{font-size:.76rem;color:var(--terra);font-weight:700;margin-bottom:.45rem}\n.dbfocus ul{margin:.35rem 0 0;padding-left:1.05rem;font-size:.82rem}\n.dbfocus li{margin:.14rem 0}\n.small{font-size:.75rem;color:var(--muted)}\n.basis{display:flex;flex-wrap:wrap;gap:.45rem .9rem;margin:.85rem 0 0;font-size:.68rem;letter-spacing:.04em;text-transform:uppercase}\n.basis span{padding:.18rem .45rem;border:1px solid #4a5568;border-radius:4px;background:rgba(255,255,255,.06);color:#d0d7e4}\n.basis span b{color:#e8b48c;font-weight:600;margin-right:.28rem}\n.hero-note{margin:.75rem 0 0;padding:.55rem .65rem;border:1px solid #4a5568;border-radius:6px;background:rgba(255,255,255,.05);font-size:.82rem;color:#d8dee9}\n.early-caveat{margin:.9rem 0 0}\n.kpi{position:relative;cursor:help;border-bottom:1px dotted #9a958a}\n.tip{display:none;position:absolute;left:0;top:118%;z-index:60;width:320px;background:var(--navy);\ncolor:var(--paper);border-radius:7px;padding:.55rem .65rem;font-size:.73rem;line-height:1.4;\nbox-shadow:0 6px 18px rgba(0,0,0,.28);text-align:left;font-weight:400;white-space:normal}\n.kpi:hover .tip,.kpi:focus .tip{display:block}\ntd:last-child .tip{left:auto;right:0}\n.tip i{display:block;color:#e8b48c;font-style:normal;font-size:.63rem;text-transform:uppercase;\nletter-spacing:.05em;margin-bottom:.04rem}\n.tip .tr{display:block;margin-top:.3rem}\n.tip .tr.warn{color:#f0c9b5}\n.tip b{font-family:Georgia,serif;font-size:.78rem;display:block;margin-bottom:.15rem}\n/* charts */\n.chart{background:#fff;border:1px solid var(--line);border-radius:9px;padding:.9rem 1rem 1rem;position:relative}\n.chart h3{font-size:1rem;color:var(--navy);line-height:1.25}\n.chart .cq{font-size:.8rem;color:#454545;margin:.2rem 0 .7rem}\n.chart .unit{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}\n.legend{display:flex;gap:.9rem;flex-wrap:wrap;margin:.35rem 0 .7rem;font-size:.74rem;color:#3c3c3c}\n.legend span i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:.28rem}\n.axis{display:grid;grid-template-columns:repeat(5,1fr);font-size:.65rem;color:var(--muted);\nborder-bottom:1px solid var(--line);margin-bottom:.35rem;padding-bottom:.15rem}\n.axis span{text-align:left}\n.axis span:last-child{text-align:right}\n.rows{position:relative}\n.grid{position:absolute;inset:0;pointer-events:none}\n.grid i{position:absolute;top:0;bottom:0;width:1px;background:#f0ece4}\n.brow{position:relative;display:grid;grid-template-columns:132px minmax(70px,1fr) 74px;\ngap:.45rem;align-items:center;margin:.2rem 0;z-index:1}\n.brow .bl{font-size:.77rem;overflow-wrap:anywhere}\n.brow .bv{font-size:.75rem;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}\n.track{height:14px;background:#efeade;border-radius:3px;display:flex;overflow:hidden}\n.track span{height:100%;display:block}\n.track.plain span{border-radius:3px}\n.gsg .brow{grid-template-columns:120px minmax(70px,1fr) 74px}\n@media(max-width:900px){\n.g2,.g3{grid-template-columns:1fr}\n.brow{grid-template-columns:104px minmax(50px,1fr) 66px}\n.gsg .brow{grid-template-columns:104px minmax(50px,1fr) 66px}\n.hero h1{font-size:1.5rem}\n.tip{width:min(300px,86vw)}\ntd:last-child .tip{left:auto;right:0}\n}\n@media(max-width:460px){\n.brow{grid-template-columns:88px minmax(38px,1fr) 60px}\n.gsg .brow{grid-template-columns:88px minmax(38px,1fr) 60px}\n.brow .bl{font-size:.72rem}\n.brow .bv{font-size:.7rem}\n.axis{grid-template-columns:repeat(3,1fr)}\n.axis span:nth-child(4){display:none}\ntable{font-size:.76rem}\n}\n</style></head><body>')
h.append(f'<div class="hero"><div class="in">\n<div class="kick">ISZE &middot; aftersales &middot; per distributor</div>\n<h1>Aftermarket opportunity diagnostics &mdash; CY2025</h1>\n<p>Where measured and modelled gaps appear in the aftermarket: four separate diagnostics,\nread per distributor with euro, service family and fleet context. Unit counts support the\nreading; they are never the headline finding. The period, direction and warranty controls\nbelow change every figure; each states the settings that produced it.</p>\n<p class="hero-note"><b>These diagnostics use different bases and are not additive.</b> Do not\nsum them into one network loss figure.</p>\n<div class="hstats">\n<div class="hstat"><div class="v" id="hero-nb">{one_py(NW['nb'], '%')}</div>\n<div class="l">Diagnostic 1 &middot; modelled unbought share</div></div>\n<div class="hstat"><div class="v" id="hero-cap">{one_py(((NW['act'] / NW['exp']) * 100), '%')}</div>\n<div class="l">Diagnostic 1 &middot; modelled capture rate</div></div>\n<div class="hstat"><div class="v" id="hero-billed">{eur_py(NW['billed_cy'])}</div>\n<div class="l">Observed &middot; parts billed, warranty included</div></div>\n<div class="hstat"><div class="v" id="hero-rep">{eur_py(NW['rep_cy'])}</div>\n<div class="l">Diagnostic 2 &middot; replenishment, {NW['rep_cy_dbs']} distributors</div></div>\n</div>\n<div class="basis">\n<span><b>Observed</b> Parts billed through 30 June 2026</span>\n<span><b>Modelled</b> Target spend / service demand where shown</span>\n<span><b>Fleet</b> Historical fleet basis only</span>\n<span><b>Sales to dealer</b> Five distributors only where used</span>\n</div>\n<p class="small" style="color:#aeb9cf;margin-top:.7rem">Supporting detail: the model expects\n{num_py(NW['exp'])} service-part units across {len(FAMNET)} filter, brake and clutch families on\n{num_py(NW['uio'])} vehicles in service; {num_py(NW['notbought'])} units were not bought in any form.\nPer-distributor euro gaps appear in the league table, not as one network total here.</p>\n</div></div>')
h.append('<div class="wrap">')
h.append('<div class="callout early-caveat"><b>Read these before the detail below.</b>\n<ul style="margin:.35rem 0 0;padding-left:1.15rem">\n<li><b>Distributor purchases are stocking decisions.</b> What we bill to a distributor is\nwhat they chose to buy, not proof that demand was lost.</li>\n<li><b>A modelled gap is not automatically bankable.</b> Target spend / service demand is a\nceiling from intervals and fleet, not observed lost orders.</li>\n<li><b>The four diagnostics are non-additive.</b> Modelled demand gap, replenishment\nexceptions, competitive mix, and no usable price answer different questions &mdash; never sum\nthem into one recovery number.</li>\n</ul></div>')
h.append('<div class="tgl">\n<div class="grp"><span class="gl">Period</span>\n<button class="on" data-t="period" data-v="cy">Calendar 2025</button>\n<button data-t="period" data-v="fy">Fiscal 2025 (Apr&ndash;Mar)</button></div>\n<div class="grp"><span class="gl">Direction</span>\n<button class="on" data-t="dir" data-v="db">ISZE &rarr; DB</button>\n<button data-t="dir" data-v="dealer">DB &rarr; dealer</button></div>\n<div class="grp"><span class="gl">Warranty</span>\n<button class="on" data-t="warr" data-v="inc">Included</button>\n<button data-t="warr" data-v="exc">Excluded</button></div>\n</div>\n<div id="avail"></div>')
h.append(f'<section><div class="shead">\n<h2>The distributor diagnostic league</h2>\n<p>One row per distributor, four separate diagnostics side by side &mdash; never summed.\nDiagnostic 1 is modelled target spend / service demand; Diagnostic 2 is replenishment (sales-to-dealer\nfile, five distributors only); Diagnostic 3 is competitive-parts share; Diagnostic 4 is parts billed\nwith no usable price. {len(dbs)} distributors bill parts; {int(len(demand))} have a modelled fleet\nbase, so the four CIS markets carry mix and price readings but no Diagnostic 1 gap. Euro leads\nevery column where the basis allows it.</p>\n</div>')
h.append('<div class="chart" id="c1">\n<h3>Where does the modelled Diagnostic 1 gap sit, and in which service families?</h3>\n<div class="cq">Per-distributor modelled gap by service family (target spend minus parts bought).\nEvery bar is euro. Unit counts are not shown; they are not the finding. Not one network total.</div>\n<div class="legend"><span><i style="background:#2b4a78"></i>Filters</span>\n<span><i style="background:#c0552d"></i>Brakes</span>\n<span><i style="background:#7a8fa8"></i>Clutch and bearings</span></div>\n<div class="axis" id="c1-axis"></div>\n<div class="rows" id="c1-rows"></div>\n</div>')
h.append('<div class="scroll" style="margin-top:.9rem"><table id="league"><thead><tr>\n<th>Distributor</th><th id="lg-demand">Diagnostic 1 gap</th><th>Unbought</th>\n<th>Fleet (UIO)</th><th>Weight class</th><th>Replenishment</th>\n<th>Competitive share</th><th>Exposed revenue</th><th>No usable price</th>\n<th id="lg-bill">Billed to distributor</th></tr></thead>\n<tbody id="league-tbody"></tbody>\n<tfoot id="league-foot"></tfoot></table></div>\n<p class="small">Competitive share is the share of the service-part euro going to Competitive parts\n(not a unit share). Exposed revenue is the high-risk share of net sales from the aftermarket\nexposure model. Fleet is the vehicles-in-service base the demand model divides into; the four CIS\nmarkets have no modelled fleet base, which is why their demand columns are blank rather than zero.</p>\n</section>')
h.append(f'<section><div class="shead">\n<h2>Diagnostic 2 &mdash; parts billed that never reached a dealer</h2>\n<p>The money splits into two problems that need opposite responses. Under-ordering means the parts\n<b>are</b> selling through to dealers and the distributor is simply not reordering enough. Genuine\noverstock means the parts are sitting still. Merging the two produces the wrong instruction.</p></div>\n<div class="chart" id="c2">\n<h3>Which distributors are under-ordering, and which are sitting on genuine overstock?</h3>\n<div class="cq">Value of exception lines at the distributor, calendar 2025. Five distributors have a\nsales-to-dealer file; the other thirteen cannot be measured this way.</div>\n<div class="legend"><span><i style="background:#2b4a78"></i>Under-ordering &mdash; selling through, reorder shortfall</span>\n<span><i style="background:#c0552d"></i>Genuine overstock &mdash; low or no sales to dealer</span></div>\n<div class="axis" id="c2-axis"></div>\n<div class="rows gsg" id="c2-rows"></div>\n</div>\n<div class="note"><b>Under-ordering is the bigger number:</b> {eur_py(NW['pull_cy'])} across\n{NW['pull_pn_cy']} part numbers is selling through to dealers faster than the distributor reorders.\n{eur_py(NW['over_cy'])} is genuinely sitting as overstock. A further 377 part numbers show dealer\ndemand with no billing at all &mdash; that is not stock, it is demand we never invoiced.</div>\n</section>')
h.append(f'<section><div class="shead">\n<h2>Diagnostic 3 &mdash; bought, but not from us</h2>\n<p>The aftermarket shows up as <b>mix</b>, not as lost revenue on exposed part numbers. Direct\nexposure is low everywhere &mdash; the worst market is {NW['expo_max_db']} at\n{one_py(NW['expo_max'], '%')} of net sales. What actually moves is the share of the service-part euro\nthat goes to Competitive parts rather than genuine.</p></div>\n<div class="chart" id="c3">\n<h3>Where have Competitive parts taken share of the service euro, and are we losing revenue on exposed part numbers?</h3>\n<div class="cq">Two different questions on one axis: what the distributor chooses to stock (share),\nand what the aftermarket takes on part numbers where an alternative exists (exposure).</div>\n<div class="legend"><span><i style="background:#2b4a78"></i>Competitive-parts share of the service euro</span>\n<span><i style="background:#c0552d"></i>Direct aftermarket exposure, % of net sales</span></div>\n<div class="axis" id="c3-axis"></div>\n<div class="rows gsg" id="c3-rows"></div>\n</div>\n<div class="callout"><b>The response follows the mix reading, not the exposure reading.</b>\nBecause exposed revenue is 0.2% to {one_py(NW['expo_max'], '%')} of net sales, the aftermarket is not\ncurrently taking revenue on part numbers where we list an alternative. It is shifting what the\ndistributor chooses to stock &mdash; which is a pricing, availability and counter-positioning\nproblem, not a lost-sale recovery problem.</div>\n</section>')
h.append(f'<section><div class="shead">\n<h2>Diagnostic 4 &mdash; parts we bill that have no usable price</h2>\n<p>{NW['np_pns']} part numbers worth {eur_py(NW['np'])} in CY2025 are either absent from the price\nlist or present with no usable price. This is mainly a <b>lubricants</b> gap, not a parts one: one\nlubricant oil alone is {one_py(NW['np_top_pct'], '%')} of the whole gap. The fix is a price-list\nentry, not a project.</p></div>\n<div class="chart" id="c4">\n<h3>Which part numbers sell without a usable price, and what are they worth?</h3>\n<div class="cq">Top ten part numbers by CY2025 billed value, with the remaining twenty-one grouped.</div>\n<div class="legend"><span><i style="background:#c0552d"></i>Lubricants</span>\n<span><i style="background:#2b4a78"></i>Parts</span></div>\n<div class="axis" id="c4-axis"></div>\n<div class="rows gsg" id="c4-rows"></div>\n</div>\n<div class="scroll" style="margin-top:.9rem"><table><thead><tr><th>#</th><th>Part number</th>\n<th>Description</th><th>CY2025 value</th><th>Cause</th><th>Billed to</th></tr></thead><tbody>')
for x in NPLIST[:8]:
    h.append(f'<tr><td>{x['rank']}</td><td>{esc(x['pn'])}</td>\n<td style="text-align:left">{esc(x['desc'])}</td>\n<td class="kpi">{eur_py(x['eur'])}{tipg('No usable price, CY2025', 'billed value of the part number in CY2025 where the price file carries no usable price', 'no_pr00_gap_cy2025_ranked.csv (price check 2026-08-11), CY2025 value from sales_fact.parquet', 'Only 31 part numbers remain after the August 2026 SAP price pull return closed 220. Shipments billed through a pricing path outside the standard selling-price route.')}</td>\n<td class="small" style="text-align:left">{esc(x['reason'])}</td>\n<td class="small" style="text-align:left">{('Israel' if bool(x['lube']) else 'Israel and Greece')}</td></tr>')
h.append('</tbody></table></div>\n<p class="small">Attribution: the seven lubricant part numbers bill to Israel (Universal Motors\nIsrael); the service cabs and the remaining parts bill mainly to Israel, with Greece for one\nback-door handle. Calendar 2025 only &mdash; this file carries no period tag.</p>\n</section>')
h.append(f'<section><div class="shead"><h2>Three distributors that carry the story</h2>\n<p>One is the largest Diagnostic 1 gap and partly a measurement artefact. One is the worst rate on a\nlarge book. One is above 100% and is not a gap at all. ITUK uses a separate external standard\nbelow &mdash; do not blend with IUK or UMI.</p></div>\n<div class="g3">\n<div class="dbfocus"><h3>IUK &mdash; the largest Diagnostic 1 gap, and part of it is our own measurement</h3>\n<div class="tagline">{eur_py(iuk["demand"]["cy"]["gap"])} &middot; {one_py(iuk["demand"]["cy"]["nb"], "%")} unbought</div>\n<ul><li>{num_py(iuk["uio"])} light commercial vehicles in service, no trucks</li>\n<li>{eur_py(iuk["demand"]["cy"]["gap"])} across the filter, brake and clutch families in CY2025</li>\n<li><b>This number is inflated by our own assumption.</b> The model applies a flat\n{num_py(KM_MODEL)} km/yr while IUK\'s measured N35 Grafter fleet averages\n<b>{KM["IUK"]["label"]} km/yr</b>. At measured distance the gap is {eur_py(IUK_ADJ["gap"])} &mdash; a\n{one_py((IUK_ADJ["cut"] * 100), "%")} smaller gap, with capture of {one_py(IUK_ADJ["cap"], "%")}.\nThe {one_py(IUK_ADJ["cap_now"], "%")} capture reading at flat 20,000 km/yr is outdated for IUK and\nshould not headline a visit.</li></ul></div>\n<div class="dbfocus"><h3>Germany &mdash; the worst rate on a large book</h3>\n<div class="tagline">{eur_py(next(r for r in dbs if r["db"] == "GERMANY")["demand"]["cy"]["gap"])} &middot; 86.1% unbought</div>\n<ul><li>13,780 vehicles in service, mixed light and truck class</li>\n<li>Second largest Diagnostic 1 gap and the worst rate of any large book</li>\n<li>Competitive-parts share 26.4%, so this is not a substitution story &mdash; the parts are simply\nnot being bought from us or from anyone else we can see</li>\n<li>The market\'s own measured distance would settle it the way Israel\'s 51,680 was settled</li></ul></div>\n<div class="dbfocus"><h3>Ireland &mdash; above 100%, and not a gap</h3>\n<div class="tagline">{one_py(next(r for r in dbs if r["db"] == "IRELAND")["demand"]["cy"]["nb"], "%")} unbought &mdash; i.e. more bought than expected</div>\n<ul><li>The only distributor above 100% of modelled expected demand</li>\n<li>Either a genuinely exceptional market or a denominator set too low</li>\n<li>Both readings are possible and they need opposite responses, so Ireland is\n<b>unresolved</b> and should not be quoted as either a strength or a weakness</li>\n<li>Its dealer-side reading is {one_py(IRELAND_DEALER_CAP, "%")}\nof expected demand reached dealers, which is the highest capture in the network</li></ul></div>\n</div>\n<div class="note"><b>ITUK external standard (IML schedule basis):</b> 22,389 trucks in service;\n35.1% oil-filter cover; {eur_py(2038000.0)} modelled gap across five service categories. Use these\nfigures when ITUK appears externally &mdash; not the IUK N35 fleet base or Israel UMI numbers.</div>\n<div class="chart" id="c5" style="margin-top:.9rem">\n<h3>How much of IUK\'s Diagnostic 1 gap is a measurement artefact?</h3>\n<div class="cq">The same fleet, the same actual sales, two distances. The distance assumption, not\nthe market, moves the number.</div>\n<div class="axis" id="c5-axis"></div>\n<div class="rows gsg" id="c5-rows"></div>\n<p class="small" id="c5-note"></p>\n</div>\n<div class="chart" id="c6" style="margin-top:.9rem">\n<h3>Which service families carry the modelled Diagnostic 1 gap?</h3>\n<div class="cq">All eighteen distributors with a fleet model, calendar 2025. Per-family euro gap and\ncapture rate &mdash; not one network total. A large family with a small rate stands out from a\nlarge family nearly covered.</div>\n<div class="axis" id="c6-axis"></div>\n<div class="rows gsg" id="c6-rows"></div>\n</div>\n</section>')
h.append(f'<section><div class="shead"><h2>What to do first</h2>\n<p>Five items, each tied to a distributor and to a number on this page.</p></div>\n<div class="note"><ol style="margin:.2rem 0;padding-left:1.2rem">\n<li><b>IUK</b> &mdash; re-baseline the distance before the visit: at the measured\n{KM["IUK"]["label"]} km/yr the gap is {eur_py(IUK_ADJ["gap"])}, not {eur_py(IUK_ADJ["gap_now"])}.\nActing on the uncorrected number buys the wrong conversation.</li>\n<li><b>Germany</b> &mdash; commission the market\'s own annual distance the way Israel\'s 51,680 was\nconfirmed, then re-read 86.1% unbought on 13,780 vehicles.</li>\n<li><b>IUK and UTI</b> &mdash; split {eur_py((sum(r["rep"]["cy"]["total"] for r in dbs if r["db"] == "IUK") + sum(r["rep"]["cy"]["total"] for r in dbs if r["db"] == "UTI")))}:\nthe under-ordering portion needs a reorder conversation, the overstock portion a stop-order instruction.</li>\n<li><b>UMI</b> &mdash; one lubricant price-list entry closes {eur_py(NW["np_top"])} of the\n{eur_py(NW["np"])} no-usable-price gap; lubricants together are {one_py(NW["np_lube_pct"], "%")} of it.</li>\n<li><b>Ireland</b> &mdash; resolve the above-100% reading before it is quoted either way.</li>\n</ol></div></section>')
h.append(f'<section><div class="shead"><h2>What this page does not claim</h2></div>\n<div class="note"><ul style="margin:.2rem 0;padding-left:1.2rem">\n<li><b>The demand side is modelled.</b> The service-demand model applies one flat\n{num_py(KM_MODEL)} km/yr annual distance and is being corrected per weight class using measured\nvalues (IUK {KM['IUK']['label']}, Israel 51,680, N35/N75/F-series provisional). Per-distributor\n<i>direction</i> is solid; absolute levels move when that lands, and IUK\'s moves most.</li>\n<li><b>The fiscal-year leg is derived, not published.</b> The capture file on disk carries calendar\nyears only. Fiscal 2025 (April 2025 &ndash; March 2026) is produced by applying the fiscal-to-calendar\nratio of PMS-tagged billing lines, per distributor and per family, to the published calendar actuals.\nThe expected-demand model itself has no period dimension, so expected demand is the same annual\nfigure in both periods. Treat the fiscal leg as a directional recut.</li>\n<li><b>The replenishment figure is a five-distributor number, not a network one.</b> Only five\ndistributors have a sales-to-dealer file. Under fiscal 2025 it drops to four, because the bridge file\nhas no dealer-sales evidence for Greece before August 2025.</li>\n<li><b>Every modelled figure is marked modelled.</b> Diagnostic 1 gaps are per-distributor ceilings\nfrom service intervals and fleet counts, not observed lost orders and not one additive network\ntotal.</li>\n<li><b>Warranty parts cannot be split by service family on this page.</b> The warranty claim extract\nmatches the service-family part-number registry on only seven part numbers (EUR 1,174 of 2025\nclaims), so the warranty-excluded view corrects the billing leg exactly per distributor but cannot\nre-cut the demand gap by family. The effect on Diagnostic 1 is small.</li>\n<li><b>Competitive-parts share is measured on the service-part euro</b> and excludes part numbers\nwhere no alternative is listed, which is why it reads far higher than the exposure column.</li>\n<li><b>No forward fleet figure appears.</b> The 2026&ndash;2030 vehicles-in-service projection is\noverstated pending correction, so nothing on this page depends on it.</li>\n</ul></div></section>')
h.append('<p class="small" style="margin-top:1.4rem;padding-top:.8rem;border-top:1px solid var(--line)">\nSources: pms_capture_by_db_year.csv &middot; replenishment_exceptions_cy2025.csv &middot;\nreplenishment_bridge.parquet &middot; mix_genuine_bvp_pms.csv &middot; aim_exposure_by_db_year.csv\n&middot; no_pr00_gap_cy2025_ranked.csv &middot; dealer_sellout_gps_2025.csv &middot;\ndealer_sellout_long_*.csv &middot; gps_spu_by_distributor.csv &middot; sales_fact.parquet &middot;\ndistributor_dimension.csv &middot; uio_by_model_bucket.csv &middot; n35 mileages all.xlsx &middot;\nEU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx. Snapshot ' + SNAPSHOT + '.</p>\n</div>\n<script>\nvar DATA = ' + json.dumps(PAYLOAD, default=str)
         + ';\nvar IUK_ADJ = ' + json.dumps(IUK_ADJ)
         + ';\nvar KM = ' + json.dumps(KM)
         + ';\nvar FAMNET = ' + json.dumps(FAMNET_JSON, default=str)
         + ";\nvar ST = {period:'cy', dir:'db', warr:'inc'};\nvar NPLIST = DATA.noprice;\nvar LOADED = false;\n</script>")
JS = '\nfunction eur(v){ if(v===null||v===undefined||v===\'\'||isNaN(v)) return \'\\u2014\';\n  v=+v; var a=Math.abs(v);\n  if(a>=1e6) return \'\\u20AC\'+(v/1e6).toFixed(2)+\'M\';\n  if(a>=1e3) return \'\\u20AC\'+Math.round(v/1e3)+\'k\';\n  return \'\\u20AC\'+Math.round(v); }\nfunction eur2(v){ if(v===null||v===undefined||isNaN(v)) return \'\\u2014\';\n  v=+v; var a=Math.abs(v);\n  if(a>=1e6) return \'\\u20AC\'+(v/1e6).toFixed(2)+\'M\';\n  if(a>=1e3) return \'\\u20AC\'+(v/1e3).toFixed(0)+\'k\';\n  return \'\\u20AC\'+Math.round(v); }\nfunction num(v){ return (v===null||v===undefined||isNaN(v))?\'\\u2014\':Math.round(v).toLocaleString(\'en-GB\'); }\nfunction one(v,s){ return (v===null||v===undefined||isNaN(v))?\'\\u2014\':(+v).toFixed(1)+(s||\'\'); }\nfunction esc(s){ return String(s).replace(/&/g,\'&amp;\').replace(/</g,\'&lt;\').replace(/>/g,\'&gt;\'); }\nfunction cfg(){ return \'Period \'+(ST.period===\'cy\'?\'CY2025 (Jan\\u2013Dec)\':\'FY2025 (Apr\\u2013Mar)\')\n  +\' \\u00b7 Direction \'+(ST.dir===\'db\'?\'ISZE \\u2192 DB\':\'DB \\u2192 dealer\')\n  +\' \\u00b7 Warranty \'+(ST.warr===\'inc\'?\'included\':\'excluded\'); }\nfunction tip(t,f,s,e){ return \'<span class="tip"><b>\'+t+\'</b><span class="tr"><i>Formula</i>\'+f\n  +\'</span><span class="tr"><i>Snapshot &amp; source</i>\'+s\n  +\'</span><span class="tr"><i>Settings that produced this figure</i>\'+cfg()\n  +\'</span><span class="tr warn"><i>Not included</i>\'+e+\'</span></span>\'; }\nfunction g(id){ return document.getElementById(id); }\nvar $ = g;\n\n// ---------- period/direction aware getters ----------\nfunction demand(r){ if(!r) return null; return r.demand[ST.period]; }\nfunction dealerLeg(r){ if(!r||!r.dealer) return null; return r.dealer[ST.period]; }\nfunction repOf(r){ if(!r||!r.rep) return null; return r.rep[ST.period]; }\nfunction mixOf(r){ if(!r) return null; return r.mix[ST.period]; }\nfunction billOf(r){\n  if(!r) return null;\n  var k = ST.period+\'_\'+(ST.warr===\'inc\'?\'inc\':\'exc\');\n  var v = r.bill[k];\n  return (v===null||v===undefined)?null:v;\n}\nfunction billNote(r){\n  if(!r) return \'\';\n  var k = ST.period+\'_\'+(ST.warr===\'inc\'?\'inc\':\'exc\');\n  if(r.bill[k]===null||r.bill[k]===undefined){\n    if(ST.warr===\'exc\') return \'no warranty data for this market \\u2014 unavailable, not zero\';\n    return \'no billing extract for this market in this period\';\n  }\n  return \'\';\n}\n// the gap column is demand-side when direction is ISZE->DB, dealer-side otherwise\nfunction gapOf(r){\n  if(ST.dir===\'db\'){ var d=demand(r); return d?d.gap:null; }\n  var t=dealerLeg(r); return t?t.gap:null;\n}\nfunction gapReason(r){\n  if(gapOf(r)!==null) return \'\';\n  if(ST.dir===\'dealer\'){\n    if(!r.dealer||!r.dealer.cy) return \'no sales-to-dealer file for this distributor\';\n    if(ST.period===\'fy\'&&!r.dealer.fy) return \'dealer file covers only 8 of 11 fiscal months \\u2014 excluded, not annualised\';\n    return \'no sales-to-dealer file for this distributor\';\n  }\n  return \'not in the modelled fleet base (bills parts but has no vehicles-in-service model)\';\n}\nfunction unboughtOf(r){\n  if(ST.dir===\'db\'){ var d=demand(r); return d?d.nb:null; }\n  var t=dealerLeg(r); return t?t.nb:null;\n}\nfunction capOf(r){\n  if(ST.dir===\'db\'){ var d=demand(r); return d?d.cap:null; }\n  var t=dealerLeg(r); return t?t.cap:null;\n}\n\n// ---------- charts ----------\nvar GROUPC={ \'Filters\':\'#2b4a78\',\'Brakes\':\'#c0552d\',\'Clutch & bearings\':\'#7a8fa8\' };\nfunction chart1(){\n  var rows=DATA.dbs.filter(function(r){ return demand(r)&&demand(r).gap>0; })\n    .sort(function(a,b){ return demand(b).gap-demand(a).gap; });\n  if(!rows.length){ g(\'c1-rows\').innerHTML=\'<p class="small">No demand gap under these settings.</p>\'; return; }\n  var mx=demand(rows[0]).gap;\n  var ticks=\'\'; for(var i=0;i<=4;i++){ ticks+=\'<span>\'+eur2(mx*i/4)+\'</span>\'; }\n  g(\'c1-axis\').innerHTML=ticks;\n  var grid=\'\'; for(var i=0;i<=4;i++){ grid+=\'<i style="left:\'+(i*25)+\'%"></i>\'; }\n  var out=\'<div class="grid">\'+grid+\'</div>\';\n  rows.forEach(function(r){\n    var d=demand(r), fams=r.fam.slice().sort(function(a,b){ return (b.gap||0)-(a.gap||0); });\n    var segs=\'\';\n    DATA.groups.forEach(function(gr){\n      var v=0;\n      fams.forEach(function(f){ if(f.group===gr){ v+=Math.max(0,(ST.period===\'fy\'?(f.fy_gap||0):(f.gap||0))); } });\n      if(v>0){ segs+=\'<span style="width:\'+(v/mx*100)+\'%;background:\'+GROUPC[gr]+\'"></span>\'; }\n    });\n    out+=\'<div class="brow"><div class="bl">\'+esc(r.db)+\'</div>\'\n      +\'<div class="track">\'+segs+\'</div>\'\n      +\'<div class="bv kpi">\'+eur2(d.gap)+tip(\'Diagnostic 1 gap, \'+esc(r.db),\n        \'expected service demand minus quantity bought (genuine or Competitive), valued at the observed average selling price per service family\',\n        \'pms_capture_by_db_year.csv, modelled; fleet \'+num(r.uio)+\' vehicles in service, \'+esc(r.wc)\n          + (ST.period===\'fy\'?\'. Fiscal leg derived from the fiscal-to-calendar ratio of service-part billing lines, per distributor and per family\':\'\')\n          + (r.db===\'IUK\'?\'. IUK expects \'+num(d.exp)+\' service-part units against \'+num(d.act)+\' bought at the flat 20,000 km/yr model distance; the measured distance is 14,494 km/yr\':\'\')\n          + (r.db===\'IRELAND\'?\'. Ireland exceeds 100% of modelled expected demand, which is unresolved, not a strength\':\'\'),\n        \'Service families with no agreed interval are outside the model, so this layer is narrower than the parts catalogue. The ceiling itself is modelled, not observed lost orders. Under fiscal the expected-demand ceiling is unchanged because the model has no period dimension.\')\n      +\'</div></div>\';\n  });\n  g(\'c1-rows\').innerHTML=out;\n}\nfunction chart2(){\n  var rows=DATA.dbs.filter(function(r){ return repOf(r)&&repOf(r).total>0; })\n    .sort(function(a,b){ return repOf(b).total-repOf(a).total; });\n  if(!rows.length){ g(\'c2-rows\').innerHTML=\'<p class="small">No distributor-level replenishment evidence under these settings.</p>\'; return; }\n  var mx=0; rows.forEach(function(r){ mx=Math.max(mx,repOf(r).pull||0,repOf(r).over_low||0,repOf(r).over_none||0); });\n  var t=\'\'; for(var i=0;i<=4;i++){ t+=\'<span>\'+eur2(mx*i/4)+\'</span>\'; } g(\'c2-axis\').innerHTML=t;\n  var grid=\'\'; for(var i=0;i<=4;i++){ grid+=\'<i style="left:\'+(i*25)+\'%"></i>\'; }\n  var out=\'<div class="grid">\'+grid+\'</div>\';\n  rows.forEach(function(r){\n    var rp=repOf(r), over=(rp.over_low||0)+(rp.over_none||0);\n    out+=\'<div class="brow"><div class="bl">\'+esc(r.db)+\'</div>\'\n      +\'<div><div class="track plain" title=""><span style="width:\'+((rp.pull||0)/mx*100)+\'%;background:#2b4a78"></span></div>\'\n      +\'<div class="track plain" style="margin-top:3px"><span style="width:\'+(over/mx*100)+\'%;background:#c0552d"></span></div></div>\'\n      +\'<div class="bv kpi">\'+eur2(rp.total)+tip(\'Replenishment exceptions, \'+esc(r.db),\n        \'value of exception part numbers billed to the distributor that did not show up proportionally in sales to its dealers, at billed value\',\n        \'replenishment_exceptions_cy2025.csv (calendar 2025) and replenishment_bridge.parquet for fiscal; ranking capped at the top 100 part numbers per signal\',\n        \'Thirteen of eighteen distributors have no sales-to-dealer file and cannot be measured. Under-ordering and overstock are different problems and are not added into one instruction.\')\n      +\'</div></div>\';\n  });\n  g(\'c2-rows\').innerHTML=out;\n}\nfunction chart3(){\n  var rows=DATA.dbs.filter(function(r){ return mixOf(r)!==null&&r.expo; })\n    .sort(function(a,b){ return mixOf(b)-mixOf(a); });\n  var mx=Math.max.apply(null,rows.map(function(r){ return mixOf(r); }));\n  var t=\'\'; for(var i=0;i<=4;i++){ t+=\'<span>\'+(Math.round(mx*i/4*10)/10)+\'%</span>\'; } g(\'c3-axis\').innerHTML=t;\n  var grid=\'\'; for(var i=0;i<=4;i++){ grid+=\'<i style="left:\'+(i*25)+\'%"></i>\'; }\n  var out=\'<div class="grid">\'+grid+\'</div>\';\n  rows.forEach(function(r){\n    var sh=mixOf(r), ex=r.expo.pct;\n    out+=\'<div class="brow"><div class="bl">\'+esc(r.db)+\'</div>\'\n      +\'<div><div class="track plain"><span style="width:\'+(sh/mx*100)+\'%;background:#2b4a78"></span></div>\'\n      +\'<div class="track plain" style="margin-top:3px"><span style="width:\'+(ex/mx*100)+\'%;background:#c0552d;min-width:2px"></span></div></div>\'\n      +\'<div class="bv kpi">\'+one(sh,\'%\')+tip(\'Competitive-parts share, \'+esc(r.db),\n        \'Competitive-parts euro divided by total service-part euro (genuine plus Competitive), service families only\',\n        \'mix_genuine_bvp_pms.csv, calendar 2025, snapshot \'+DATA.meta.snapshot,\n        \'Part numbers where no alternative is listed, so this is not the whole parts book. Fiscal leg is a period recut. Exposed revenue is \'+eur(r.expo.eur)+\' of net sales, \'+one(ex,\'%\')+\'.\')\n      +\'</div></div>\';\n  });\n  g(\'c3-rows\').innerHTML=out;\n}\nfunction chart4(){\n  var top=NPLIST.slice(0,10), rest=NPLIST.slice(10);\n  var mx=top[0].eur, rows=top.slice();\n  var restv=0; rest.forEach(function(x){ restv+=x.eur; });\n  if(restv>0) rows=rows.concat([{rank:0,pn:\'Other \'+(rest.length)+\' part numbers\',desc:\'\',eur:restv,lube:false,other:true}]);\n  var t=\'\'; for(var i=0;i<=4;i++){ t+=\'<span>\'+eur2(mx*i/4)+\'</span>\'; } g(\'c4-axis\').innerHTML=t;\n  var grid=\'\'; for(var i=0;i<=4;i++){ grid+=\'<i style="left:\'+(i*25)+\'%"></i>\'; }\n  var out=\'<div class="grid">\'+grid+\'</div>\';\n  rows.forEach(function(x){\n    var lb=x.other?esc(x.pn):(esc(x.pn)+\' <span class="small">\'+esc((x.desc||\'\').slice(0,22))+\'</span>\');\n    out+=\'<div class="brow"><div class="bl">\'+lb+\'</div>\'\n      +\'<div class="track plain"><span style="width:\'+(x.eur/mx*100)+\'%;background:\'+(x.lube?\'#c0552d\':\'#2b4a78\')+\'"></span></div>\'\n      +\'<div class="bv kpi">\'+eur2(x.eur)+tip(\'No usable price, \'+(x.other?\'grouped remainder\':esc(x.pn)),\n        \'billed value in CY2025 where the price file carries no usable price. \'+(x.other?\'Sum of \'+rest.length+\' part numbers below the top ten.\':\'Cause: \'+esc(x.desc?x.desc:\'\')+\'.\'),\n        \'no_pr00_gap_cy2025_ranked.csv (price check 2026-08-11, value from sales_fact.parquet CY2025)\',\n        \'Part numbers closed by the August 2026 SAP price pull return are not in this list. Billed value is not the same as lost margin.\')\n      +\'</div></div>\';\n  });\n  g(\'c4-rows\').innerHTML=out;\n}\nfunction chart5(){\n  var now=IUK_ADJ.gap_now, adj=IUK_ADJ.gap;\n  var mx=Math.max(now,adj);\n  var t=\'\'; for(var i=0;i<=4;i++){ t+=\'<span>\'+eur2(mx*i/4)+\'</span>\'; } g(\'c5-axis\').innerHTML=t;\n  var rows=[[\'Model distance \'+num(IUK_ADJ.km_model)+\' km/yr\',now,\'#2b4a78\',\n             \'IUK, the model as it stands, \'+num(IUK_ADJ.km_model)+\' km/yr flat assumption\'],\n            [\'Measured distance \'+num(IUK_ADJ.km)+\' km/yr\',adj,\'#c0552d\',\n             \'IUK, re-baselined to the measured N35 Grafter distance\']];\n  var out=\'\';\n  rows.forEach(function(r){\n    out+=\'<div class="brow"><div class="bl">\'+esc(r[0])+\'</div>\'\n      +\'<div class="track plain"><span style="width:\'+(r[1]/mx*100)+\'%;background:\'+r[2]+\'"></span></div>\'\n      +\'<div class="bv kpi">\'+eur2(r[1])+tip(esc(r[3]),\n        \'expected demand scaled by measured distance divided by model distance (\'+IUK_ADJ.scale.toFixed(3)+\'), minus actual bought, at the observed average selling price per family\',\n        \'n35 mileages all.xlsx, median of odometer deltas between readings over elapsed time, 18,277 intervals on 5,421 vehicles 2018-2026\',\n        \'Derived from odometer deltas, not the workbook annual mileage column, which divides by a shrinking vehicle age. N35 Grafter only, so the correction is applied to IUK as a whole.\')\n      +\'</div></div>\';\n  });\n  g(\'c5-rows\').innerHTML=out;\n  g(\'c5-note\').innerHTML=\'At \'+num(IUK_ADJ.km_model)+\' km/yr the flat model reads \'\n    +one(IUK_ADJ.cap_now,\'%\')+\' capture (outdated for IUK \\u2014 do not headline a visit). At the measured \'\n    +num(IUK_ADJ.km)+\' km/yr it reads \'+one(IUK_ADJ.cap,\'%\')+\' and the gap falls from \'\n    +eur2(IUK_ADJ.gap_now)+\' to \'+eur2(IUK_ADJ.gap)\n    +\' \\u2014 \'+(IUK_ADJ.cut*100).toFixed(0)+\'% of the flat-model gap was our own distance assumption. \'\n    +\'Israel is the one market already corrected inside the model, at 51,680 km/yr.\';\n}\nfunction chart6(){\n  var rows=FAMNET.slice().sort(function(a,b){ return (b.gap||0)-(a.gap||0); });\n  var mx=rows[0].gap;\n  var t=\'\'; for(var i=0;i<=4;i++){ t+=\'<span>\'+eur2(mx*i/4)+\'</span>\'; } g(\'c6-axis\').innerHTML=t;\n  var grid=\'\'; for(var i=0;i<=4;i++){ grid+=\'<i style="left:\'+(i*25)+\'%"></i>\'; }\n  var out=\'<div class="grid">\'+grid+\'</div>\';\n  rows.forEach(function(f){\n    out+=\'<div class="brow"><div class="bl">\'+esc(f.label)+\'</div>\'\n      +\'<div class="track plain"><span style="width:\'+(f.gap/mx*100)+\'%;background:\'+(GROUPC[f.group]||\'#8b8578\')+\'"></span></div>\'\n      +\'<div class="bv kpi">\'+eur2(f.gap)+tip(\'Diagnostic 1 gap, \'+esc(f.label),\n        \'expected demand minus bought, at the observed average selling price for this family\',\n        \'pms_capture_by_db_year.csv, 18 distributors, calendar 2025; snapshot \'+DATA.meta.snapshot,\n        \'This family bought \'+one(f.cap,\'%\')+\' of expected demand (\'+num(f.act)+\' of \'+num(f.exp)+\' units \\u2014 units shown only because the family is named). Modelled, not observed lost orders.\')\n      +\'</div></div>\';\n  });\n  g(\'c6-rows\').innerHTML=out;\n}\n\n// ---------- league table ----------\nfunction renderLeague(){\n  var tb=g(\'league-tbody\'), out=\'\';\n  var mx=0;\n  DATA.dbs.forEach(function(x){ var v=gapOf(x); if(v!==null&&v>mx) mx=v; });\n  DATA.dbs.forEach(function(r){\n    var gv=gapOf(r), nb=unboughtOf(r), bv=billOf(r);\n    var pct=(gv!==null&&mx)?Math.min(100,gv/mx*100):0;\n    var chips=\'\';\n    if(nb!==null&&nb<0) chips+=\'<span class="chip terra">above 100% \\u2014 unresolved</span>\';\n    if(r.db===\'IUK\') chips+=\'<span class="chip">mileage-inflated</span>\';\n    if(!r.demand.cy) chips+=\'<span class="chip blue">no fleet model</span>\';\n    out+=\'<tr><td><b>\'+esc(r.db)+\'</b>\'+chips+\'</td>\';\n    if(gv===null){\n      out+=\'<td class="null">\'+esc(gapReason(r))+\'</td><td class="null">\'+esc(gapReason(r))+\'</td>\';\n    } else {\n      out+=\'<td class="kpi">\'+eur2(gv)+tip((ST.dir===\'db\'?\'Diagnostic 1 gap, \':\'Diagnostic 1 gap at the dealer, \')+esc(r.db),\n        ST.dir===\'db\'\n          ? \'expected service demand minus quantity the distributor bought from ISZE, valued at the observed average selling price per service family\'\n          : \'expected service demand minus quantity the distributor sold on to its dealers, valued at the observed average selling price per service family\',\n        (ST.dir===\'db\' ? \'pms_capture_by_db_year.csv, modelled\' : \'monthly sales-to-dealer file for this distributor\')\n          + \', fleet \'+num(r.uio)+\' vehicles in service\'\n          + (ST.dir===\'dealer\'&&r.dealer&&r.dealer[ST.period]&&r.dealer[ST.period].proj\n             ? \'; only \'+r.dealer[ST.period].months+\' of 12 fiscal months are on file, so the observed run-rate is scaled to twelve and the figure is derived\' : \'\'),\n        ST.dir===\'db\'\n          ? \'Service families with no agreed service interval. A modelled ceiling, not observed lost orders. Fiscal leg is a derived recut.\'\n          : \'Excludes anything the dealer bought elsewhere. Only six of the twenty-two distributors have this file, so the twelve largest blank cells are structural, not zero.\')\n        +\'</td>\'\n        +\'<td class="kpi">\'+one(nb,\'%\')+tip(\'Not bought, share of expected demand, \'+esc(r.db),\n          \'one minus captured quantity divided by expected quantity\',\n          \'same source as the value column\',\n          \'A negative figure means more was bought than the model expected \\u2014 an unresolved reading, not a strength. Ireland reads 102.7% in calendar 2025.\')\n        +\'</td>\';\n    }\n    out+=\'<td>\'+num(r.uio)+\'</td><td class="small" style="text-align:left">\'+esc(r.wc)\n      +(r.n75?(\'<br><span class="small">\'+num(r.n75)+\' truck class / \'+num(r.lcv||0)+\' light</span>\'):\'\')\n      +(r.imit?(\'<br><span class="small">measured \'+num(r.imit)+\' km/yr</span>\'):\'\')\n      +\'</td>\';\n    var rp=repOf(r);\n    out+=\'<td class="kpi">\'+(rp?eur2(rp.total):\'<span class="null">no sales-to-dealer file</span>\')\n      +(rp?tip(\'Replenishment exceptions, \'+esc(r.db),\n        \'value of exception part numbers at billed value, capped at the top 100 part numbers per signal\',\n        ST.period===\'cy\'?\'replenishment_exceptions_cy2025.csv\':\'replenishment_bridge.parquet, fiscal months Apr 2025 \\u2013 Mar 2026\',\n        \'Only five distributors have a sales-to-dealer file, and under fiscal only four. Not a network figure.\'):\'\')\n      +\'</td>\';\n    var mv=mixOf(r);\n    out+=\'<td class="kpi">\'+(mv===null?\'<span class="null">not measured</span>\':one(mv,\'%\'))\n      +(mv===null?\'\':tip(\'Competitive-parts share, \'+esc(r.db),\n        \'Competitive-parts euro divided by total service-part euro, service families only\',\n        \'mix_genuine_bvp_pms.csv, calendar 2025\'+(ST.period===\'fy\'?\' with a period recut from tagged billing\':\'\'),\n        \'Part numbers with no listed alternative, so this is not the whole parts book.\'))\n      +\'</td>\';\n    out+=\'<td class="kpi">\'+(r.expo?one(r.expo.pct,\'%\'):\'\\u2014\')\n      +(r.expo?tip(\'Direct aftermarket exposure, \'+esc(r.db),\n        \'high-risk revenue divided by net sales\',\n        \'aim_exposure_by_db_year.csv, calendar 2025; \'+eur(r.expo.eur)+\' of net sales\',\n        \'Only part numbers with a matched alternative. A narrow slice, which is why it reads low everywhere.\'):\'\')\n      +\'</td>\';\n    out+=\'<td class="kpi">\'+(r.np&&r.np.eur?eur2(r.np.eur):\'\\u2014\')\n      +(r.np&&r.np.eur?tip(\'No usable price, \'+esc(r.db),\n        \'CY2025 billed value of part numbers the price file cannot price\',\n        \'no_pr00_gap_cy2025_ranked.csv with CY2025 value from sales_fact.parquet\',\n        \'Calendar 2025 only \\u2014 this file carries no period tag, so it does not move with the period control.\'):\'\')\n      +\'</td>\';\n    out+=\'<td class="kpi">\'+(bv===null?\'<span class="null">\'+esc(billNote(r))+\'</span>\':eur2(bv))\n      +(bv===null?\'\':tip((ST.dir===\'db\'?\'Billed to \':\'Sales to dealer from \')+esc(r.db),\n        ST.dir===\'db\'\n          ? \'net parts sales to this distributor, less warranty parts where warranty is excluded\'\n          : \'value the distributor invoiced on to its dealers\',\n        ST.dir===\'db\' ? \'gps_spu_by_distributor.csv (calendar 2025) and sales_fact.parquet (fiscal window); warranty split from the same GPS file\'\n                      : \'dealer_sellout_gps_2025.csv, calendar 2025 only\'\n                      + (r.dealer&&r.dealer[ST.period]&&r.dealer[ST.period].proj?\'; fiscal value derived at the distributor\\u2019s own euro per unit\':\'\'),\n        ST.warr===\'exc\'\n          ? \'Warranty parts, which are \'+(r.bill.warr?eur(r.bill.warr):\'n/a\')+\' at this distributor. Credit notes are already netted out.\'\n          : \'Nothing excluded. Credit notes are already netted out.\'))\n      +\'</td></tr>\';\n  });\n  tb.innerHTML=out;\n  var nwd={gap:0,exp:0,act:0,bill:0,bill_n:0,rep:0,rep_dbs:0,mix_max:null,gv_max:0};\n  DATA.dbs.forEach(function(r){\n    var v=gapOf(r);\n    if(v!==null){ nwd.gap+=v; nwd.exp+=(demand(r)?demand(r).exp:0); nwd.act+=(demand(r)?demand(r).act:0); }\n    var b=billOf(r); if(b!==null){ nwd.bill+=b; nwd.bill_n++; }\n    var rp=repOf(r); if(rp){ nwd.rep+=rp.total; nwd.rep_dbs++; }\n    var mv=mixOf(r); if(mv!==null&&(nwd.mix_max===null||mv>nwd.mix_max)) nwd.mix_max=mv;\n    if(r.expo&&r.expo.pct>nwd.gv_max) nwd.gv_max=r.expo.pct;\n  });\n  var nbn=(ST.dir===\'db\'&&nwd.exp>0)?one((nwd.exp-nwd.act)/nwd.exp*100,\'%\'):\'\\u2014\';\n  var f=\'<tr class="tot"><td>Network \\u00b7 \'+DATA.dbs.length+\' distributors</td>\'\n    +\'<td class="small" style="text-align:left">Per distributor only \\u2014 not summed</td><td>\'+nbn+\'</td>\'\n    +\'<td>\'+num(DATA.nw.uio)+\'</td><td class="small" style="text-align:left">light and truck class, mixed</td>\'\n    +\'<td>\'+(nwd.rep?eur2(nwd.rep)+\' <span class="small">(\'+nwd.rep_dbs+\' DBs)</span>\':\'\\u2014\')+\'</td>\'\n    +\'<td>\'+(nwd.mix_max===null?\'\\u2014\':\'max \'+one(nwd.mix_max,\'%\'))+\'</td>\'\n    +\'<td>\'+one(nwd.gv_max,\'%\')+\' max</td>\'\n    +\'<td>\'+eur2(DATA.nw.np)+\'</td><td>\'+(nwd.bill?eur2(nwd.bill):\'\\u2014\')+\'</td></tr>\';\n  g(\'league-foot\').innerHTML=f;\n  g(\'lg-demand\').textContent = ST.dir===\'db\'?\'Diagnostic 1 gap\':\'Diagnostic 1 gap at dealer\';\n  g(\'lg-bill\').textContent = ST.dir===\'db\'?\'Billed to distributor\':\'Sales to dealer\';\n}\n\n// ---------- availability + hero ----------\nfunction renderAvail(){\n  var items=[];\n  if(ST.dir===\'dealer\'){\n    items.push(\'<b>Sixteen of the twenty-two distributors have no sales-to-dealer file</b>, so their value columns are blank with the reason, never a zero and never a copy of the other direction. Six have one: IUK, UTI, ITUK, Ireland, Greece and Portugal.\');\n    var proj=[];\n    DATA.dbs.forEach(function(r){ var t=r.dealer&&r.dealer[ST.period];\n      if(t&&t.proj) proj.push(r.db+\' (\'+t.months+\' of 11 fiscal months on file)\'); });\n    if(ST.period===\'fy\'&&proj.length) items.push(\'<b>Two dealer files do not cover the fiscal window:</b> \'+proj.join(\' and \')+\'. Their value is the observed run-rate scaled to the window, marked derived, not counted. Greece is absent altogether under fiscal because its file starts in August 2025.\');\n  }\n  if(ST.period===\'fy\'){\n    items.push(\'<b>Fiscal 2025 is April 2025 to March 2026. No source covers 2026-03</b>, so a complete fiscal window is the eleven months April 2025 to February 2026. March 2026 is in neither the calendar nor the fiscal cut on this page.\');\n    items.push(\'<b>The demand gap under fiscal is a derived recut.</b> The demand-capture file on disk carries calendar years only, so the fiscal-to-calendar ratio of service-part billing lines, per distributor and per family, is applied to the published calendar actuals. The expected-demand model has no period dimension, so the ceiling is the same annual figure in both periods &mdash; only the bought quantity moves.\');\n    items.push(\'<b>The no-usable-price column stays on calendar 2025</b> under fiscal, because that file carries no period tag.\');\n    items.push(\'<b>Greece has no replenishment figure under fiscal</b>, and UTI\\\'s fiscal replenishment covers ten of the eleven months. Greece is excluded rather than annualised; UTI is shown because it is ten of eleven.\');\n  }\n  if(ST.warr===\'exc\') items.push(\'<b>Warranty is priced out of the billing column</b> (\'+eur2(DATA.nw.warr)+\' network-wide, \'+one(DATA.nw.warr_pct,\'%\')+\' of parts billed in CY2025). The four CIS markets \\u2014 Ukraine, Armenia, Kazakhstan and Palestine \\u2014 have no warranty data and show <i>unavailable, not zero</i>. Other figures do not move with this control: the demand gap covers parts that were never bought, so warranty claims against parts that were bought cannot be netted out of it. The warranty claim extract matches the service-family registry on only seven part numbers, which is why.\');\n  var el=g(\'avail\');\n  if(!items.length){ el.className=\'\'; el.innerHTML=\'\'; return; }\n  el.className=\'show\';\n  el.innerHTML=\'<b>What these settings cannot show.</b><ul><li>\'+items.join(\'</li><li>\')+\'</li></ul>\';\n}\nfunction renderHero(){\n  var billed=0, n=0, nwarr=0;\n  DATA.dbs.forEach(function(r){ var b=billOf(r); if(b!==null){ billed+=b; n++; } else if(ST.warr===\'exc\') nwarr++; });\n  g(\'hero-billed\').textContent = eur2(billed);\n  g(\'hero-billed\').nextElementSibling.textContent = ST.dir===\'dealer\'\n    ? \'Observed \\u00b7 sales to dealer, \'+DATA.nw.dealer_dbs+\' distributors\'\n    : \'Observed \\u00b7 parts billed, \'+(ST.warr===\'inc\'?\'warranty included\':\'warranty excluded\')+\', \'+n+\' of \'+DATA.dbs.length+\' distributors\';\n  if(ST.dir===\'db\'&&ST.period===\'cy\'){\n    g(\'hero-nb\').textContent=one(DATA.nw.nb,\'%\');\n    g(\'hero-nb\').nextElementSibling.textContent=\'Diagnostic 1 \\u00b7 modelled unbought share\';\n  } else {\n    var nbSum=0, nbN=0;\n    DATA.dbs.forEach(function(r){ var u=unboughtOf(r); if(u!==null){ nbSum+=u; nbN++; } });\n    g(\'hero-nb\').textContent=nbN?one(nbSum/nbN,\'%\'):\'\\u2014\';\n    g(\'hero-nb\').nextElementSibling.textContent=ST.dir===\'dealer\'\n      ? \'Diagnostic 1 \\u00b7 average unbought at dealer\'\n      : \'Diagnostic 1 \\u00b7 modelled unbought share (derived recut)\';\n  }\n  var cap=0, cn=0;\n  DATA.dbs.forEach(function(r){ var c=capOf(r); if(c!==null){ cap+=c; cn++; } });\n  $(\'hero-cap\').textContent = cn ? one(cap/cn,\'%\') : \'\\u2014\';\n  $(\'hero-cap\').nextElementSibling.textContent = ST.dir===\'dealer\'\n    ? \'Diagnostic 1 \\u00b7 average capture reached dealers\'+ (cn<22?\' \\u2014 \'+cn+\' of \'+DATA.dbs.length+\' distributors\':\'\')\n    : \'Diagnostic 1 \\u00b7 modelled capture rate\'+ (cn<22?\' \\u2014 \'+cn+\' of \'+DATA.dbs.length+\' distributors\':\'\');\n  var rp=0, dn=0; DATA.dbs.forEach(function(r){ var x=repOf(r); if(x){ rp+=x.total; dn++; } });\n  g(\'hero-rep\').textContent = eur2(rp);\n  g(\'hero-rep\').nextElementSibling.textContent = dn?(\'Diagnostic 2 \\u00b7 replenishment, \'+dn+\' distributors\'):\'Diagnostic 2 \\u00b7 no replenishment evidence under these settings\';\n}\nfunction renderAll(){ renderAvail(); renderHero(); renderLeague(); chart1(); chart2(); chart3(); chart4(); chart5(); chart6(); }\ndocument.querySelectorAll(\'.tgl button\').forEach(function(b){\n  b.addEventListener(\'click\', function(){\n    var t=b.getAttribute(\'data-t\'), v=b.getAttribute(\'data-v\');\n    document.querySelectorAll(\'.tgl button[data-t="\'+t+\'"]\').forEach(function(o){ o.classList.remove(\'on\'); o.setAttribute(\'aria-pressed\',\'false\'); });\n    b.classList.add(\'on\'); b.setAttribute(\'aria-pressed\',\'true\');\n    ST[t]=v; renderAll();\n  });\n});\ndocument.querySelectorAll(\'.tgl button\').forEach(function(b){ b.setAttribute(\'aria-pressed\', b.classList.contains(\'on\')?\'true\':\'false\'); });\nrenderAll();\n'
h.append("<script>" + JS + "</script></body></html>")

os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
with open(OUT_HTML, "w", encoding="utf-8") as fh:
    fh.write("\n".join(h))
with open(OUT_CMD, "w", encoding="ascii", newline="\r\n") as fh:
    fh.write('@echo off\nstart "" "%~dp0ISZE_DB_Leakage_Review_CY2025.html"\n')
print("WROTE", OUT_HTML, round(os.path.getsize(OUT_HTML) / 1024, 1), "KB")
print("WROTE", OUT_CMD)
print("charts: 6 | league rows:", len(dbs), "| no-price rows:", len(NPLIST))
