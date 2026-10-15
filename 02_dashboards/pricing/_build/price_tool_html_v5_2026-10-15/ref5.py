"""Independent pandas version of the v5 scenarios: settings chain part > PMS cell > PMS category > L3 > L2 > L1,
category holds where capture is under 45%, single market x category holds."""
import json
import numpy as np, pandas as pd
from pathlib import Path
H = Path(__file__).parent
D = json.loads((H / "payload5.json").read_text(encoding="utf-8"))
sc = json.loads((H / "scen5.json").read_text())
cols = ["pn", "desc", "l1", "l2", "l3", "c", "bp0", "bp1", "p0", "p1", "p2", "nw", "pbi", "pcat", "cell", "src"]
P = pd.DataFrame(D["parts"], columns=cols)
LN = pd.DataFrame(D["lines"], columns=["pi", "db", "k", "b", "q", "c0", "bits", "cat1"])
P["cp"] = (P.bp1 / P.bp0 - 1).clip(lower=0)
ncat = len(D["pms"]["cats"]); K = ["PR00", "UTI", "UMI", "OTH"]


def val(S, key, k):
    d = S.get(key)
    if not d: return None
    if k in d and d[k] != "": return d[k]
    if "ALL" in d and d["ALL"] != "": return d["ALL"]
    return None


def parse(v, cp):
    if v is None: return None
    s = str(v).strip().upper().replace(",", ".").replace("%", "")
    if s in ("", "S", "AUTO"): return None
    if s in ("H", "HOLD"): return 0.0
    if s[0] == "B":
        rest = s[2:].replace("+", "").strip(); pts = float(rest) if rest else 0.0
        return max(0.0, cp + pts / 100)
    return float(s) / 100


def run(S, ph, target, mask, ceil=0.05):
    fixed = np.full((len(P), 4), np.nan)
    for i, r in P.iterrows():
        keys = ["p:" + r.pn, "f:%d" % r.cell, "c:%d" % r.pcat, "l3:%d" % r.l3, "l2:%d" % r.l2, "l1:%d" % r.l1]
        for k in range(4):
            v = None
            for key in keys:
                v = val(S, key, K[k])
                if v is not None: break
            p = parse(v, r.cp)
            if p is not None: fixed[i, k] = p
    L = LN.copy()
    L["cp"] = P.cp.to_numpy()[L.pi]; L["fm"] = fixed[L.pi.to_numpy(), L.k.to_numpy()]
    hold = (L.bits & mask) > 0
    cat0 = L.cat1.to_numpy() - 1
    catset = {int(k) for k in ph["cat"]}; cellset = {int(k) for k in ph["cell"]}
    hold |= ((L.bits & 64) > 0) & np.isin(cat0, list(catset)) & (L.cat1 > 0)
    hold |= (L.cat1 > 0) & np.isin(L.db.to_numpy() * ncat + cat0, list(cellset))
    L["hold"] = hold
    base = L.b.sum(); free = L[~L.hold]; fx = free[free.fm.notna()]; au = free[free.fm.isna()]
    F = (fx.b * fx.fm).sum(); B1 = (au.b * au.cp).sum(); s1 = (target * base - F) / B1
    cap = au.cp * s1 > au.cp + ceil; capeur = (au.b[cap] * (au.cp[cap] + ceil)).sum(); unc = B1 - (au.b[cap] * au.cp[cap]).sum()
    s2 = (target * base - F - capeur) / unc
    mv = np.where(L.fm.notna(), L.fm, np.maximum(0, np.minimum(s2 * L.cp, L.cp + ceil))); mv = np.where(L.hold, 0.0, mv)
    ex = L.b * mv; pmsm = (L.cat1 > 0).to_numpy()
    return {"extra": round(float(ex.sum()), 2), "held": round(float(L.b[L.hold].sum()), 2), "pms_extra": round(float(ex[pmsm].sum()), 2), "pms_billed": round(float(L.b[pmsm].sum()), 2), "s2": round(float(s2), 6)}


empty = {"cat": {}, "cell": {}}
ref = {"start": run(sc["base"], empty, 0.053, 32), "pms": run(sc["S2"], sc["ph2"], 0.053, 32), "pms_nomask": run(sc["S2"], sc["ph2"], 0.05, 0)}
js = json.loads((H / "js5.json").read_text()); ok = True
for k, v in ref.items():
    d = abs(v["extra"] - js[k]["extra"]); print(k, "python", v, "\n      js    ", js[k], "| diff extra %.2f" % d)
    ok &= d < 1 and abs(v["s2"] - js[k]["s2"]) < 1e-5 and abs(v["held"] - js[k]["held"]) < 0.01 and abs(v["pms_extra"] - js[k]["pms_extra"]) < 1
print("ALL OK" if ok else "MISMATCH")
