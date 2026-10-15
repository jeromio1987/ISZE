"""Read-only look: PMS service categories inside the price revision base, and what a filter split and a tonnage split would rest on."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PROP = ISZE / "02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29"
sys.path.insert(0, str(PROP))
from evidence_lib import load_base, attach_evidence, FILTER_WORDS
H = Path(__file__).parent
D = json.loads((H / "payload4.json").read_text(encoding="utf-8"))
P = pd.DataFrame(D["parts"], columns=["pn", "desc", "l1", "l2", "l3", "c", "bp0", "bp1", "p0", "p1", "p2", "nw", "pbi"])
P["cp"] = (P.bp1 / P.bp0 - 1).clip(lower=0)
LN = pd.DataFrame(D["lines"], columns=["pi", "db", "k", "b", "q", "c0", "bits"])
print("FILTER_WORDS:", FILTER_WORDS)
L = load_base(); L = L[L.movable].copy()
E = attach_evidence(L.copy())
cat = E.groupby("pn").service_category.agg(lambda s: s.dropna().iloc[0] if s.notna().any() else None)
bill = E.groupby("pn").net_sales_value.sum()
P["cat"] = P.pn.map(cat); P["bill"] = P.pn.map(bill)
# start-state moves per part (price list free move) from the v4 recipe: pads and steering fixed, shop-far hold (bit 32)
steer = [i for i, t in enumerate(D["l3"]) if t[1] == "Steering Unit"][0]
padpart = P.pn.isin(D["pad_parts"]) | P.l3.isin(D["pad_l3"]); steerpart = P.l3.eq(steer) & ~padpart
fm = np.where(padpart, 0.0, np.where(steerpart, 0.05, np.nan))
L2 = LN.copy(); L2["cp"] = P.cp.to_numpy()[L2.pi]; L2["fm"] = fm[L2.pi]; L2["hold"] = (L2.bits & 32) > 0
base = L2.b.sum(); free = L2[~L2.hold]; fx = free[free.fm.notna()]; au = free[free.fm.isna()]
F = (fx.b * fx.fm).sum(); B1 = (au.b * au.cp).sum(); s1 = (0.053 * base - F) / B1
cap = au.cp * s1 > au.cp + 0.05; capeur = (au.b[cap] * (au.cp[cap] + 0.05)).sum(); unc = B1 - (au.b[cap] * au.cp[cap]).sum()
s2 = (0.053 * base - F - capeur) / unc
mv = np.where(L2.fm.notna(), L2.fm, np.maximum(0, np.minimum(s2 * L2.cp, L2.cp + 0.05))); mv = np.where(L2.hold, 0.0, mv)
L2["x"] = L2.b * mv
P["x"] = L2.groupby("pi").x.sum().reindex(range(len(P))).fillna(0).to_numpy()
P["b"] = L2.groupby("pi").b.sum().reindex(range(len(P))).fillna(0).to_numpy()
print("start-state scale", round(s2, 4), "book extra", round(P.x.sum()), "billed", round(P.b.sum()))
pm = P[P.cat.notna()]
print("\nPMS parts: %d of %d parts, EUR %.0f of %.0f billed (%.1f%%); extra EUR %.0f = %.2f%%" % (len(pm), len(P), pm.b.sum(), P.b.sum(), 100 * pm.b.sum() / P.b.sum(), pm.x.sum(), 100 * pm.x.sum() / pm.b.sum()))
g = pm.groupby("cat").apply(lambda d: pd.Series({"parts": len(d), "billed": d.b.sum(), "extra": d.x.sum(), "move": d.x.sum() / d.b.sum(), "own_step_w": (d.b * d.cp).sum() / d.b.sum(), "parts_at_0": int((d.cp <= 0).sum())}), include_groups=False).sort_values("billed", ascending=False)
pd.set_option("display.width", 200); print(g.round(4).to_string())
nonpms = P[P.cat.isna()]
print("\nnot in PMS: billed %.0f, move %.2f%%" % (nonpms.b.sum(), 100 * nonpms.x.sum() / nonpms.b.sum()))
flt = pm[pm.cat.str.contains("ilter", case=False, na=False)]
print("\nfilter categories:", sorted(flt.cat.unique()))
print(flt.groupby("cat").apply(lambda d: pd.Series({"parts": len(d), "billed": d.b.sum(), "move": d.x.sum() / d.b.sum(), "own_step": (d.b * d.cp).sum() / d.b.sum(), "min_step": d.cp.min(), "max_step": d.cp.max()}), include_groups=False).round(4).to_string())
P.to_pickle(H / "_pms_parts.pkl")
# tonnage side
for f in ["vehicle_band_applicability.csv", "vehicle_family_bands.csv"]:
    p = ISZE / "01_data/00_derived" / f
    if p.exists():
        t = pd.read_csv(p, dtype=str, nrows=3); print("\n", f, list(t.columns)); print(t.to_string(index=False)[:700])
    else:
        print("\nmissing", f)
