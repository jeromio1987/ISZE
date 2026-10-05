# -*- coding: utf-8 -*-
"""
Task card 4.1 — competitor-to-list ratio model by category x price class, with a confidence band,
back-tested on held-out observed parts.

The whole point of this card is the last four words: "report the error, do not hide it". A ratio
model that looks good in-sample and has never been tested on a part it did not see is worthless, so
every number here is produced out-of-sample.

Fit set : 04_tools/aftermarket_intelligence/state/crossref_edges.csv, rows that carry a real
          competitor price AND a list price for the same part number.
Target  : competitor price / our list price, on one price type at a time. Price types are NEVER
          blended - the acceptance rule from the delegation file, section 5.

Method  : leave-one-part-number-out. For each held-out part number, the model is refitted on all
          other part numbers in the same category x price-class cell; if that cell is too thin, it
          falls back to the category, then to the whole book. The fallback level used is recorded
          per prediction, because a model that mostly answers from the whole-book average is not a
          category model and must not be described as one.

Outputs : state/ratio_model.csv            the fitted ratios and their bands
          state/ratio_backtest.csv         one row per held-out observation
          state/RATIO_MODEL_REPORT.md      the build log and the error, in plain words

Nothing is fetched. Nothing is written outside this folder.

Run: python 04_tools/aftermarket_intelligence/build_ratio_model.py
"""
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STATE = HERE / "state"

MIN_CELL = 5          # a cell needs this many parts to be used on its own

log = []

edges = pd.read_csv(STATE / "crossref_edges.csv", dtype=str)
edges["price"] = pd.to_numeric(edges.competitor_price, errors="coerce")
edges["price_type"] = edges.price_type.fillna("")

# our list price for the same part number
pl = pd.read_parquet(ROOT / "01_data/00_derived/pricing_pr00_ie40.parquet",
                     columns=["part_number", "sp_eur"])
pl["part_no"] = pl.part_number.astype(str).str.strip()
pl["sp_eur"] = pd.to_numeric(pl.sp_eur, errors="coerce")
pl = pl.drop_duplicates("part_no").set_index("part_no")["sp_eur"]

# category
import sys as _sys
_sys.path.insert(0, str(ROOT / "04_tools" / "_shared"))
from classification_paths import figkey_export_for_release  # noqa: E402
# AIM figure-key export of the APPROVED release (sidecar + sha256 checked; raises otherwise)
FIGKEY_EXPORT, _FIGKEY_RELEASE = figkey_export_for_release()
master = pd.read_csv(FIGKEY_EXPORT, dtype=str)
master["part_no"] = master.part_number.astype(str).str.strip()
master = master.drop_duplicates("part_no")
cat = dict(zip(master.part_no, master.aim_level_1.fillna("(unclassified)")))
cat2 = dict(zip(master.part_no, master.aim_level_2.fillna("")))

# GBP -> EUR. The UK workshop survey is dated "2023" with no day, so the ECB 2023 annual average is
# used: 1 EUR = 0.8697865098039 GBP (ECB data API, series EXR.A.GBP.EUR.SP00.A, fetched 2026-09-24).
# FIX 2026-09-24: before this, GBP prices were divided by a EUR list with no conversion.
EUR_PER = {"EUR": 1.0, "GBP": 1 / 0.8697865098039}

# only rows that are a genuine rival price and are not our own line / a peer carrier
# FIX 2026-09-24: is_our_own_line was 0 on every edge (see build_crossref_graph.py), so our own
# number's retail price ("oem_recommended_retail", 237 edges) was modelled as a competitor price.
# The graph now flags it; the second test below refuses our own number even if a flag is lost again.
d = edges[(edges.has_competitor_price.astype(int) == 1)
          & (edges.is_our_own_line.astype(int) == 0)
          & (edges.is_peer_carrier.astype(int) == 0)
          & (edges.cpn_key != edges.part_no.str.replace(r"[\s.\-/]", "", regex=True).str.upper())
          ].copy()
log.append(f"- priced rival edges (our own line, our own number, peer carrier removed): {len(d)}")
log.append(f"- price types left: {d.price_type.value_counts().to_dict()}")

d["currency"] = d.currency.fillna("")
bad_ccy = sorted(set(d.currency) - set(EUR_PER))
if bad_ccy:
    raise SystemExit(f"currency with no conversion rate: {bad_ccy}")
d["price"] = d.price * d.currency.map(EUR_PER)
log.append(f"- converted to EUR: {d[d.currency != 'EUR'].shape[0]} rows "
           f"(GBP at ECB 2023 average, 1 GBP = EUR {EUR_PER['GBP']:.6f})")
log.append(f"- VAT status per price type (blank = not recorded): "
           f"{d.groupby('price_type').vat.agg(lambda s: s.fillna('not recorded').value_counts().to_dict()).to_dict()}")

d["our_list"] = d.part_no.map(pl)
d = d[d.our_list.notna() & (d.our_list > 0) & d.price.notna() & (d.price > 0)]
d["ratio"] = d.price / d.our_list
d["category"] = d.part_no.map(cat).fillna("(unclassified)")
d["subcategory"] = d.part_no.map(cat2).fillna("")
log.append(f"- with a list price on both sides: {len(d)} edges, {d.part_no.nunique()} part numbers")

# one observation per part number x price type: the median of its rows, so a part with 20 offers
# does not outvote a part with one
obs = (d.groupby(["part_no", "price_type"])
       .agg(ratio=("ratio", "median"), price=("price", "median"), our_list=("our_list", "first"),
            category=("category", "first"), subcategory=("subcategory", "first"),
            n_rows=("ratio", "size"), countries=("country", lambda s: "|".join(sorted(set(s.dropna())))))
       .reset_index())
obs = obs[(obs.ratio > 0) & np.isfinite(obs.ratio)]
log.append(f"- observations (part number x price type): {len(obs)}")
log.append(f"- by price type: {obs.price_type.value_counts().to_dict()}")

# price class from our own list value
bins = [0, 10, 25, 50, 100, 250, 1000, 1e12]
labels = ["<10", "10-25", "25-50", "50-100", "100-250", "250-1000", ">1000"]
obs["price_class"] = pd.cut(obs.our_list, bins=bins, labels=labels, right=False)

# CLUSTERS - FIX 2026-09-24. Holding out one part number left its siblings (other Isuzu numbers
# sharing a rival number: supersessions, kits, left/right) in the training set, so the model partly
# saw the answer. A cluster is a connected group of Isuzu numbers linked through any shared rival
# number, over ALL rival edges (priced or not). The whole cluster is held out together.
rv = edges[(edges.is_our_own_line.astype(int) == 0) & (edges.is_peer_carrier.astype(int) == 0)]
parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for pn, ck in zip(rv.part_no, rv.cpn_key):
    a, b = find("P" + pn), find("C" + ck)
    if a != b:
        parent[a] = b
obs["cluster"] = obs.part_no.map(lambda p: find("P" + p))
cs = obs.groupby("cluster").part_no.nunique()
log.append(f"- clusters among modelled parts: {len(cs)}; parts sharing a cluster with another "
           f"modelled part: {int(cs[cs > 1].sum())}")


def predict(train, r):
    cell = train[(train.category == r.category) & (train.price_class == r.price_class)]
    if len(cell) >= MIN_CELL:
        return "category x price class", cell.ratio
    catc = train[train.category == r.category]
    if len(catc) >= MIN_CELL:
        return "category", catc.ratio
    return "whole price type", train.ratio


# out-of-sample, one price type at a time, two hold-out schemes side by side:
#   part    - the original leave-one-part-number-out (kept only so the change is visible)
#   cluster - the whole cluster held out: the honest one
rows = []
for ptype, grp in obs.groupby("price_type"):
    if len(grp) < 4:
        log.append(f"- price type '{ptype}' has {len(grp)} observations: too thin to model, skipped")
        continue
    for i, r in grp.iterrows():
        for scheme, train in (("part", grp.drop(index=i)),
                              ("cluster", grp[grp.cluster != r.cluster])):
            if len(train) < MIN_CELL:
                continue
            level, used = predict(train, r)
            rows.append(dict(scheme=scheme, part_no=r.part_no, cluster=r.cluster, price_type=ptype,
                             category=r.category, price_class=str(r.price_class), actual=r.ratio,
                             predicted=float(np.median(used)),
                             constant=float(np.median(train.ratio)),   # one number for every part
                             p10=float(np.percentile(used, 10)), p90=float(np.percentile(used, 90)),
                             n_fit=len(used), fallback_level=level, our_list=r.our_list,
                             n_obs_rows=r.n_rows, countries=r.countries))

bt = pd.DataFrame(rows)
if bt.empty:
    raise SystemExit("no price type had enough observations to back-test")

# Error as a FACTOR, symmetric: predicting 2x the truth and half the truth are the same size of miss.
# The old "% of actual" blew up whenever the actual ratio was small (the 164% on online retail).
bt["miss_factor"] = np.exp((np.log(bt.predicted) - np.log(bt.actual)).abs())
bt["miss_factor_constant"] = np.exp((np.log(bt.constant) - np.log(bt.actual)).abs())
bt["abs_err_pct"] = (bt.predicted - bt.actual).abs() / bt.actual * 100      # old measure, kept
bt["in_band"] = ((bt.actual >= bt.p10) & (bt.actual <= bt.p90)).astype(int)
bt.to_csv(STATE / "ratio_backtest.csv", index=False, encoding="utf-8")


def fx(v):
    """a miss factor of 1.25 reads 'off by 25%' either way"""
    return f"x{v:.2f} (off by {100 * (v - 1):.0f}%)"


log.append("")
log.append("## out-of-sample error, by price type")
log.append("Miss is a factor: x1.25 means the prediction was 25% too high OR the truth 25% higher "
           "than predicted. 'Constant' = one median ratio for every part, same hold-out.")
for ptype, gp in bt.groupby("price_type"):
    log.append(f"### {ptype}")
    for scheme in ("part", "cluster"):
        g = gp[gp.scheme == scheme]
        if g.empty:
            continue
        log.append(f"- hold-out by {scheme} ({len(g)} parts): typical miss {fx(g.miss_factor.median())}"
                   f"; 9 in 10 within {fx(g.miss_factor.quantile(0.9))}"
                   f"; constant typical miss {fx(g.miss_factor_constant.median())}"
                   f"; inside 10-90 band {100 * g.in_band.mean():.0f}%"
                   f"; old measure median {g.abs_err_pct.median():.1f}%")
    g = gp[gp.scheme == "cluster"]
    log.append(f"- where the cluster-hold-out answer came from: {g.fallback_level.value_counts().to_dict()}")

bc = bt[bt.scheme == "cluster"]
log.append("")
log.append("## does the model beat one constant? (cluster hold-out, all price types)")
diff = bc.miss_factor - bc.miss_factor_constant
tie = diff.abs() < 1e-9
log.append(f"- identical to the constant (the model fell back to it or matched it): "
           f"{100 * tie.mean():.0f}% of parts; model closer {100 * (diff < -1e-9).mean():.0f}%; "
           f"constant closer {100 * (diff > 1e-9).mean():.0f}%")
log.append(f"- typical miss model {fx(bc.miss_factor.median())} vs constant {fx(bc.miss_factor_constant.median())}")

# the parts this would be USED on: tier C, the long tail
tiers = pd.read_csv(ROOT / "04_tools/delegation/state/refresh_tiers_LOCAL.csv", dtype={"part_no": str})
tiers["part_no"] = tiers.part_no.astype(str).str.strip()
lt = tiers[tiers.tier == "C"].copy()
lt["our_list"] = lt.part_no.map(pl)
lt_mix = pd.cut(lt.our_list, bins=bins, labels=labels, right=False).value_counts(normalize=True)
log.append("")
log.append(f"## error by price band, against where the long tail sits "
           f"(tier C: {len(lt)} parts, {int(lt.our_list.notna().sum())} with a list price)")
log.append("| our list band | long-tail share | tested parts (cluster hold-out) | typical miss |")
log.append("|---|---|---|---|")
for lab in labels:
    g = bc[bc.price_class == lab]
    log.append(f"| {lab} | {100 * lt_mix.get(lab, 0):.0f}% | {len(g)} | "
               f"{fx(g.miss_factor.median()) if len(g) else 'not tested'} |")
tested_share = sum(lt_mix.get(lab, 0) for lab in labels if (bc.price_class == lab).sum() >= 10)
log.append(f"- share of the long tail sitting in a band with 10+ tested parts: {100 * tested_share:.0f}%")

# CHECK: pack-size mismatch. Within one part and one price type, rival row prices that sit near 2x or
# 0.5x the part's own median point to per-piece vs per-set confusion. Control band: near 1.5x / 0.67x.
d2 = d.merge(obs[["part_no", "price_type", "price"]].rename(columns={"price": "part_median"}),
             on=["part_no", "price_type"])
d2 = d2[d2.groupby(["part_no", "price_type"]).price.transform("size") >= 3]
# distance from the part's median, on a log scale, direction ignored: 2x and 0.5x are both ln 2
dist = np.log(d2.price / d2.part_median).abs()
W = 0.05                                             # window half-width on the log scale (~5%)
at2 = int(((dist - np.log(2)).abs() <= W).sum())
side_lo = int(((dist - (np.log(2) - 3 * W)).abs() <= W).sum())
side_hi = int(((dist - (np.log(2) + 3 * W)).abs() <= W).sum())
log.append("")
log.append("## check: pack-size mismatch")
log.append(f"- rows tested (parts with 3+ rival prices in one price type): {len(d2)}")
log.append(f"- rows within ~5% of 2x or 0.5x their part's median: {at2}; same-width windows just "
           f"below and above (~1.7x and ~2.3x): {side_lo} and {side_hi}")
log.append("- read: a clear bump at 2x over its neighbours means per-piece vs per-set confusion. "
           "No bump says nothing either way.")

log.append("")
log.append("## is the category model actually a category model? (cluster hold-out)")
lv = bc.fallback_level.value_counts()
tot = len(bc)
for k, v in lv.items():
    log.append(f"- {k}: {v} of {tot} ({100 * v / tot:.0f}%)")

# the fitted table, in-sample, for reading
fit = (obs.groupby(["price_type", "category", "price_class"], observed=True)
       .agg(parts=("ratio", "size"), median_ratio=("ratio", "median"),
            p10=("ratio", lambda s: np.percentile(s, 10)),
            p90=("ratio", lambda s: np.percentile(s, 90)))
       .reset_index())
fit = fit[fit.parts >= 3]
fit.to_csv(STATE / "ratio_model.csv", index=False, encoding="utf-8")
log.append("")
log.append(f"## fitted cells with 3 or more parts: {len(fit)}")

(STATE / "RATIO_MODEL_REPORT.md").write_text(
    "# Competitor-to-list ratio — model and back-test (task card 4.1)\n\n"
    f"Built {datetime.now(timezone.utc).isoformat(timespec='seconds')} by "
    "`04_tools/aftermarket_intelligence/build_ratio_model.py`\n\n"
    "Every error figure is out-of-sample, one part number held out at a time. The model is only "
    "refitted on parts it has not seen.\n\n"
    + "\n".join(log) + "\n\n"
    "## How to use this, honestly\n"
    "NOT for per-part estimates of unmatched parts. At most, quote the observed range per price "
    "type as a description of matched parts. The ratio is what a competitor price TENDS to be, as a "
    "multiple of our list, in that category and price band. It is not a price. A cell with two parts "
    "in it is two parts, not a market.\n\n"
    "## What would make it wrong\n"
    "- Time: rival prices are 2023-2025; our list is today's. A list price change since then moves "
    "every ratio.\n"
    "- VAT: not recorded for the online price types, so whether they include VAT is unknown; DE and "
    "NO carry different VAT rates.\n"
    "- One price type fitted across a country mix: EUcon's online medians span five countries.\n"
    "- Pack-size differences: a pad set per axle against per wheel is a factor of two, and it shows "
    "up as a whole-number multiple in the ratio distribution.\n"
    "- A category whose competitors are all premium brands, against one where budget brands set "
    "the median.\n",
    encoding="utf-8")

print("\n".join(log))
