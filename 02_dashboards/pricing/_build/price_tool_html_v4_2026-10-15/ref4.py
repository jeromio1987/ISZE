"""Independent pandas version of the v4 scenario (pad kits held, steering units fixed at +5%, shop-far hold ticked)."""
import json
import numpy as np, pandas as pd
from pathlib import Path
H = Path(__file__).parent
D = json.loads((H / "payload4.json").read_text(encoding="utf-8"))
P = pd.DataFrame(D["parts"], columns=["pn", "desc", "l1", "l2", "l3", "c", "bp0", "bp1", "p0", "p1", "p2", "nw", "pbi"])
LN = pd.DataFrame(D["lines"], columns=["pi", "db", "k", "b", "q", "c0", "bits"])
P["cp"] = (P.bp1 / P.bp0 - 1).clip(lower=0)
steer = [i for i, t in enumerate(D["l3"]) if t[1] == "Steering Unit"][0]
padpart = P.pn.isin(D["pad_parts"]) | P.l3.isin(D["pad_l3"])
steerpart = P.l3.eq(steer) & ~padpart
fixed_move = np.where(padpart, 0.0, np.where(steerpart, 0.05, np.nan))   # nan = auto


def run(target, mask, ceil=0.05):
    L = LN.copy()
    L["cp"] = P.cp.to_numpy()[L.pi]; L["fm"] = fixed_move[L.pi]
    L["hold"] = (L.bits & mask) > 0
    base = L.b.sum(); free = L[~L.hold]
    fx = free[free.fm.notna()]; auto = free[free.fm.isna()]
    F = (fx.b * fx.fm).sum(); B1 = (auto.b * auto.cp).sum()
    s1 = (target * base - F) / B1
    cap = auto.cp * s1 > auto.cp + ceil
    capeur = (auto.b[cap] * (auto.cp[cap] + ceil)).sum(); unc = B1 - (auto.b[cap] * auto.cp[cap]).sum()
    s2 = (target * base - F - capeur) / unc
    mv = np.where(L.fm.notna(), L.fm, np.maximum(0, np.minimum(s2 * L.cp, L.cp + ceil))); mv = np.where(L.hold, 0.0, mv)
    ex = L.b * mv
    return {"extra": round(float(ex.sum()), 2), "held": round(float(L.b[L.hold].sum()), 2), "steer": round(float(ex[P.l3.to_numpy()[L.pi] == steer].sum()), 2), "s2": round(float(s2), 6)}


ref = {"start_5.3": run(0.053, 32), "start_nomask_5.3": run(0.053, 0), "start_all_5.0": run(0.05, 63)}
js = json.loads((H / "js4.json").read_text()); ok = True
for k, v in ref.items():
    d = abs(v["extra"] - js[k]["extra"]); print(k, "python", v, "| js", js[k], "| diff extra %.2f" % d)
    ok &= d < 1 and abs(v["s2"] - js[k]["s2"]) < 1e-5 and abs(v["held"] - js[k]["held"]) < 0.01 and abs(v["steer"] - js[k]["steer"]) < 1
print("ALL OK" if ok else "MISMATCH")
