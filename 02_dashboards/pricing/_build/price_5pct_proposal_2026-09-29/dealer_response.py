"""Does dealer demand react to our list price? Measured on sales-to-dealer data.

Design: for each list change, compare dealer units per part number in the same calendar
months before and after, against the list change that part received, with family x event
(or market x family) fixed effects, so common shocks (fleet growth, season, FX) drop out.
Estimator: two-period Poisson with part fixed effects (binomial on the post share),
cluster-robust by part number. Placebo: the same list change against volume growth in
months before it took effect.

Run: python dealer_response.py   ->  dealer_price_response_2026-09-29.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from response_lib import (D, fe_logit, fe_wls, load_family, load_ituk_monthly, load_lists,
                          window_qty, z10)

OUT = Path(__file__).with_name("dealer_price_response_2026-09-29.json")
R = {"generated": "2026-09-29", "sources": {}}

lists, superseded, origin = load_lists()
cls, aim = load_family()


def est(d, xcols=("dlp",)):
    d = d[d.n > 0]
    b, se = fe_logit(d.share, d.n, d[list(xcols)].astype(float).to_numpy(), d.fe, d.pn)
    return {"n": int(len(d)), **{f"beta_{c}": round(float(bb), 4) for c, bb in zip(xcols, b)},
            **{f"se_{c}": round(float(s), 4) for c, s in zip(xcols, se)}}


# ------------------------------------------------------------------ 1. timing + invoice check
sf = pd.read_parquet(D / "sales_fact.parquet",
                     columns=["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value"])
sf = sf[(sf.billed_qty > 0) & (sf.net_sales_value > 0)].copy()
sf["pn"] = z10(sf.part_number)
sf["ym"] = sf.billing_date.dt.to_period("M")
it = sf[sf.sold_to_sap == 2575]


def asp(df, a, b):
    s = df[(df.ym >= pd.Period(a, "M")) & (df.ym <= pd.Period(b, "M"))]
    g = s.groupby("pn")[["net_sales_value", "billed_qty"]].sum()
    return g.net_sales_value / g.billed_qty


inv = {}
for ev, y0, y1, pre, post in [("April 2026", 2025, 2026, ("2025-04", "2026-02"), ("2026-04", "2026-08")),
                              ("January 2024", 2023, 2024, ("2023-02", "2023-12"), ("2024-03", "2024-12"))]:
    j = pd.DataFrame({"list": np.log(lists[y1] / lists[y0]),
                      "invoice": np.log(asp(it, *post) / asp(it, *pre))}).dropna()
    j = j[j.invoice.abs() < 0.5]
    inv[ev] = {"parts": int(len(j)), "median_list_change": round(float(j.list.median()), 4),
               "median_invoice_change": round(float(j.invoice.median()), 4),
               "correlation": round(float(j.corr().iloc[0, 1]), 3)}
R["invoice_check_ituk"] = inv

cd = pd.read_parquet(D / "pricing_revision_cd.parquet", columns=["part_number", "bp_jpy_new", "bp_jpy_current"])
cd["pn"] = z10(cd.part_number)
cd = cd[(cd.bp_jpy_current > 0) & (cd.bp_jpy_new > 0)].drop_duplicates("pn").set_index("pn")
q = sf[(sf.billing_date >= "2024-07-01") & (sf.billing_date < "2025-07-01")].groupby("pn").billed_qty.sum()
q = q.reindex(cd.index).fillna(0)
R["cy2026_cd_weighted_base_price_move"] = {
    "value": round(float((q * cd.bp_jpy_new).sum() / (q * cd.bp_jpy_current).sum() - 1), 4),
    "weights": "ISZE billed quantity 2024-07-01..2025-06-30, all customers",
    "parts_with_volume": int((q > 0).sum()),
    "source": "01_data/00_derived/pricing_revision_cd.parquet (PRICE CD 250912)"}

# ------------------------------------------------------------------ 2. UK network volume by month
m = load_ituk_monthly()
m["y"], m["mo"] = m.ym.dt.year, m.ym.dt.month
t = m.pivot_table(index="mo", columns="y", values="qty", aggfunc="sum")
R["ituk_dealer_units_by_month"] = {int(mo): {str(y): (None if pd.isna(v) else float(v)) for y, v in row.items()}
                                   for mo, row in t.iterrows()}


def yoy(mos, a, b):
    return round(float(t.loc[mos, a].sum() / t.loc[mos, b].sum() - 1), 4)


R["ituk_network_yoy"] = {"Jan-Feb 2026 vs 2025": yoy([1, 2], 2026, 2025),
                         "Mar 2026 vs 2025": yoy([3], 2026, 2025),
                         "Mar-Aug 2026 vs 2025": yoy([3, 4, 5, 6, 7, 8], 2026, 2025),
                         "Apr-Aug 2026 vs 2025": yoy([4, 5, 6, 7, 8], 2026, 2025),
                         "Apr-Aug 2025 vs 2024": yoy([4, 5, 6, 7, 8], 2025, 2024)}

# ------------------------------------------------------------------ 3. ITUK, three list changes
EVENTS = {
    "January 2024": (2023, 2024, ("2023-03", "2023-12"), ("2024-03", "2024-12"), None),
    "February 2025": (2024, 2025, ("2024-03", "2024-12"), ("2025-03", "2025-12"), ("2023-03", "2023-12")),
    "April 2026": (2025, 2026, ("2025-04", "2025-08"), ("2026-04", "2026-08"), ("2024-04", "2024-08")),
}
rows = []
for ev, (y0, y1, pre, post, pp) in EVENTS.items():
    q0, q1 = window_qty(m, *pre), window_qty(m, *post)
    pns = q0.index.union(q1.index)
    d = pd.DataFrame({"q_pre": q0.reindex(pns).fillna(0), "q_post": q1.reindex(pns).fillna(0)})
    d["q_pp"] = window_qty(m, *pp).reindex(pns).fillna(0) if pp else np.nan
    d["dlp"] = np.log(lists[y1].reindex(pns) / lists[y0].reindex(pns))
    d["event"] = ev
    rows.append(d.reset_index(names="pn"))
S = pd.concat(rows, ignore_index=True)
S["grp"] = cls.group.reindex(S.pn).fillna("unclassified").to_numpy()
S = S[(S.q_pre >= 3) & S.dlp.notna() & (S.dlp.abs() < 0.5)].copy()
S["n"], S["fe"] = S.q_pre + S.q_post, S.event + "|" + S.grp
S["share"] = S.q_post / S.n
S["superseded"] = S.pn.isin(superseded)

ituk = {"events": {}}
for ev, d in S.groupby("event", sort=False):
    within = d.groupby("grp").dlp.transform(lambda s: s - s.mean())
    pos = d[(d.q_pre > 0) & (d.q_post > 0)]
    b2, se2 = fe_wls(np.log(pos.q_post / pos.q_pre), pos.dlp.to_numpy()[:, None], pos.fe, pos.q_pre, pos.pn)
    ituk["events"][ev] = {"parts": int(len(d)),
                          "qty_weighted_list_change": round(float(np.average(d.dlp, weights=d.q_pre)), 4),
                          "median_list_change": round(float(d.dlp.median()), 4),
                          "within_family_spread_sd": round(float(within.std()), 4),
                          **est(d), "logdiff_beta": round(float(b2[0]), 4), "logdiff_se": round(float(se2[0]), 4)}
ituk["pooled"] = est(S)
ituk["pooled_excl_superseded"] = est(S[~S.superseded])
ituk["pooled_min10_units"] = est(S[S.q_pre >= 10])
plc = {}
for ev in ["February 2025", "April 2026"]:
    d = S[S.event == ev].copy()
    d["n"] = d.q_pp + d.q_pre
    d["share"] = d.q_pre / d.n
    plc[ev] = est(d)
ituk["placebo_previous_year_trend"] = plc
R["ituk_three_list_changes"] = ituk

# ------------------------------------------------------------------ 4. four markets, April 2026
def monthly(files):
    out = []
    for f in files:
        x = pd.read_csv(D / f, dtype={"part_number": str, "period": str})
        out.append(x[x.period_grain == "month"][["part_number", "period", "qty"]])
    x = pd.concat(out)
    x["pn"], x["ym"] = z10(x.part_number), pd.PeriodIndex(x.period, freq="M")
    return x.groupby(["pn", "ym"], as_index=False).qty.sum()


MK = {"ITUK (UK trucks)": (m, ("2025-04", "2025-08"), ("2026-04", "2026-08")),
      "IUK (UK D-Max)": (monthly(["dealer_sellout_long_IUK_CY2025.csv", "dealer_sellout_long_IUK_CY2026YTD.csv"]),
                         ("2025-04", "2025-07"), ("2026-04", "2026-07")),
      "Ireland": (monthly(["dealer_sellout_long_IRELAND_CY2025.csv", "dealer_sellout_long_IRELAND_CY2026YTD.csv"]),
                  ("2025-04", "2025-07"), ("2026-04", "2026-07")),
      "Portugal": (monthly(["dealer_sellout_long_PORTUGAL_CY2025.csv", "dealer_sellout_long_PORTUGAL_CY2026YTD.csv"]),
                   ("2025-04", "2025-08"), ("2026-04", "2026-08"))}
bvp = pd.read_csv(D / "genuine_bvp_crossref.csv", dtype=str)
has_bvp = set(z10(bvp.genuine_pn.dropna()))
pms = set(z10(bvp.dropna(subset=["pms_category"]).genuine_pn))
ks = pd.read_csv(D / "iam_ks_price_gap.csv", dtype={"pn": str})
eu = pd.read_csv(D / "eucon_price_gap.csv", dtype={"pn": str})
auto = pd.read_csv(D / "competitiveness_autodoc_risk.csv", dtype={"part_number": str})
comp = set(z10(ks.pn)) | set(z10(eu.pn)) | set(z10(auto.part_number))

frames, vol = [], {}
for name, (mm, pre, post) in MK.items():
    tot = lambda a, b: float(mm[(mm.ym >= pd.Period(a, "M")) & (mm.ym <= pd.Period(b, "M"))].qty.sum())
    vol[name] = {"window": f"{pre[0]}..{pre[1]} vs {post[0]}..{post[1]}", "units_before": tot(*pre),
                 "units_after": tot(*post), "change": round(tot(*post) / tot(*pre) - 1, 4),
                 "jan_feb_2026_vs_2025": round(tot("2026-01", "2026-02") / tot("2025-01", "2025-02") - 1, 4)}
    q0, q1 = window_qty(mm, *pre), window_qty(mm, *post)
    b0, b1 = window_qty(mm, "2025-01", "2025-02"), window_qty(mm, "2026-01", "2026-02")
    pns = q0.index.union(q1.index)
    d = pd.DataFrame({"q_pre": q0.reindex(pns).fillna(0), "q_post": q1.reindex(pns).fillna(0),
                      "b_pre": b0.reindex(pns).fillna(0), "b_post": b1.reindex(pns).fillna(0)})
    d["dlp"] = np.log(lists[2026].reindex(pns) / lists[2025].reindex(pns))
    d["market"] = name
    frames.append(d.reset_index(names="pn"))
A = pd.concat(frames, ignore_index=True)
A["grp"] = cls.group.reindex(A.pn).fillna("unclassified").to_numpy()
A = A[(A.q_pre >= 3) & A.dlp.notna() & (A.dlp.abs() < 0.5)].copy()
A["n"], A["share"], A["fe"] = A.q_pre + A.q_post, A.q_post / (A.q_pre + A.q_post), A.market + "|" + A.grp
A["superseded"] = A.pn.isin(superseded)
four = {"dealer_units": vol, "by_market": {}, "segments": {}}
for name, d in A.groupby("market", sort=False):
    four["by_market"][name] = {**est(d), "qty_weighted_list_change": round(float(np.average(d.dlp, weights=d.q_pre)), 4)}
four["pooled"] = est(A)
four["pooled_excl_superseded"] = est(A[~A.superseded])
four["pooled_min10_units"] = est(A[A.q_pre >= 10])
P = A.assign(n=A.b_pre + A.b_post, share=A.b_post / (A.b_pre + A.b_post))
four["placebo_jan_feb"] = est(P[P.n > 0])
A["pms"], A["has_bvp"], A["comp_ev"] = A.pn.isin(pms), A.pn.isin(has_bvp), A.pn.isin(comp)
labels = {"pms": "maintenance parts (filters, brakes, clutch)", "has_bvp": "parts with a cheaper Isuzu alternative",
          "comp_ev": "parts with a competitor price on file"}
for seg, lab in labels.items():
    A[f"dlp_x_{seg}"] = A.dlp * A[seg]
    r = est(A, ("dlp", f"dlp_x_{seg}"))
    four["segments"][lab] = {"share_of_parts": round(float(A[seg].mean()), 3),
                             "extra_response": r[f"beta_dlp_x_{seg}"], "extra_response_se": r[f"se_dlp_x_{seg}"]}
R["four_markets_april_2026"] = four

# ------------------------------------------------------------------ 5. scenario values for the proposal
pooled = four["pooled"]
lows = [v["beta_dlp"] - 1.96 * v["se_dlp"] for v in
        (four["pooled"], four["pooled_excl_superseded"], four["pooled_min10_units"])]
R["scenario_elasticities"] = {
    "none": 0.0,
    "central": pooled["beta_dlp"],
    "stress": round(float(min(lows)), 2),
    "note": ("central = four-market pooled estimate; stress = the lowest 95% lower bound across the three "
             "pooled specifications. Within-family response only: a family-wide move to the aftermarket is "
             "absorbed by the fixed effects and is not measured."),
}
R["sources"] = {
    "dealer_sales": "01_data/00_derived/dealer_sellout_long_{ITUK_CY2023,ITUK_CY2024,ITUK_network_CY2025,ITUK_CY2026YTD,"
                    "IUK_*,IRELAND_*,PORTUGAL_*}.csv, monthly network grain",
    "list_prices": "01_data/00_derived/pricing_pr00_ie40_{2023,2024,2025}.parquet (year-end snapshots) + "
                   "pricing_pr00_ie40.parquet (current, valid from 2026-03-13)",
    "billing": "01_data/00_derived/sales_fact.parquet, sold-to 2575 (ITUK)",
    "families": "01_data/00_derived/pr00_classification.csv (group)",
}
OUT.write_text(json.dumps(R, indent=2), encoding="utf-8")
print(json.dumps({k: R[k] for k in ["invoice_check_ituk", "cy2026_cd_weighted_base_price_move", "ituk_network_yoy",
                                    "scenario_elasticities"]}, indent=1))
print(json.dumps(R["ituk_three_list_changes"], indent=1))
print(json.dumps(R["four_markets_april_2026"], indent=1))
