"""Independent Python reference of the v2 line model, written from the payload with pandas (not a port of the JS)."""
import json
import numpy as np, pandas as pd
from pathlib import Path
H = Path(__file__).parent
D = json.loads((H / "payload2.json").read_text(encoding="utf-8"))
P = pd.DataFrame(D["parts"], columns=["pn", "desc", "l1", "l2", "l3", "c", "bp0", "bp1", "p0", "p1", "p2", "nw", "pbi"])
LN = pd.DataFrame(D["lines"], columns=["pi", "db", "k", "b", "q", "c0", "bits"])
P["cp"] = P.c.clip(lower=0)
pads = set(D["pad_parts"]); padl3 = set(D["pad_l3"])
held_part = P.pn.isin(pads) | P.l3.isin(padl3)          # setting 0 on every list


def run(target, mask, ceil=0.05):
    L = LN.copy()
    L["cp"] = P.cp.to_numpy()[L.pi]
    L["fixed"] = held_part.to_numpy()[L.pi]               # part-level setting 0 -> fixed move 0
    L["hold"] = (L.bits & mask) > 0
    base = L.b.sum()
    free = L[~L.hold]
    auto = free[~free.fixed]
    B1 = (auto.b * auto.cp).sum()
    s1 = (target * base - 0.0) / B1
    cap = auto.cp * s1 > auto.cp + ceil
    capeur = (auto.b[cap] * (auto.cp[cap] + ceil)).sum()
    unc = B1 - (auto.b[cap] * auto.cp[cap]).sum()
    s2 = (target * base - capeur) / unc
    mv = np.where(L.fixed, 0.0, np.maximum(0, np.minimum(s2 * L.cp, L.cp + ceil)))
    mv = np.where(L.hold, 0.0, mv)
    extra = (L.b * mv).sum()
    return {"extra": round(extra, 2), "held": round(L.b[L.hold].sum(), 2), "inc": round(extra / base, 6), "s2": round(s2, 6)}


ref = {"noholds_5.3": run(0.053, 0), "allholds_5.3": run(0.053, 31), "service_5.0": run(0.05, 1), "lost_5.0": run(0.05, 16)}
js = json.loads((H / "js_results.json").read_text())
ok = True
for k, v in ref.items():
    d = abs(v["extra"] - js[k]["extra"])
    print(k, "python", v, "\n      js    ", js[k], "| diff extra EUR %.2f" % d)
    ok &= d < 1 and abs(v["s2"] - js[k]["s2"]) < 1e-5 and abs(v["held"] - js[k]["held"]) < 0.01
print("ALL OK" if ok else "MISMATCH")
