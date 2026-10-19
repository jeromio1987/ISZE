"""Independent check of the v6 numbers (dealer reaction and fiscal-year value) against what the page printed."""
import json, re, sys
import numpy as np, pandas as pd
from pathlib import Path
H = Path(__file__).parent
D = json.loads((H / "payload6.json").read_text(encoding="utf-8"))
sc = json.loads((H / "scen5.json").read_text())
cols = ["pn", "desc", "l1", "l2", "l3", "c", "bp0", "bp1", "p0", "p1", "p2", "nw", "pbi", "pcat", "cell", "src"]
P = pd.DataFrame(D["parts"], columns=cols); LN = pd.DataFrame(D["lines"], columns=["pi", "db", "k", "b", "q", "c0", "bits", "cat1"])
P["cp"] = (P.bp1 / P.bp0 - 1).clip(lower=0); S = sc["base"]; K = ["PR00", "UTI", "UMI", "OTH"]


def parse(v, cp):
    if v is None: return None
    s = str(v).strip().upper().replace(",", ".").replace("%", "")
    if s in ("", "S", "AUTO"): return None
    if s in ("H", "HOLD"): return 0.0
    return float(s) / 100


def val(key, k):
    d = S.get(key)
    if not d: return None
    return d[K[k]] if K[k] in d and d[K[k]] != "" else (d["ALL"] if "ALL" in d and d["ALL"] != "" else None)


fixed = np.full((len(P), 4), np.nan)
for i, r in P.iterrows():
    keys = ["p:" + r.pn, "f:%d" % r.cell, "c:%d" % r.pcat, "l3:%d" % r.l3, "l2:%d" % r.l2, "l1:%d" % r.l1]
    for k in range(4):
        v = None
        for key in keys:
            v = val(key, k)
            if v is not None: break
        p = parse(v, r.cp)
        if p is not None: fixed[i, k] = p
L = LN.copy(); L["cp"] = P.cp.to_numpy()[L.pi]; L["fm"] = fixed[L.pi.to_numpy(), L.k.to_numpy()]
L["hold"] = (L.bits & 32) > 0
target, ceil = 0.053, 0.05
base = L.b.sum(); free = L[~L.hold]; fx = free[free.fm.notna()]; au = free[free.fm.isna()]
F = (fx.b * fx.fm).sum(); B1 = (au.b * au.cp).sum(); s1 = (target * base - F) / B1
cap = au.cp * s1 > au.cp + ceil; capeur = (au.b[cap] * (au.cp[cap] + ceil)).sum(); unc = B1 - (au.b[cap] * au.cp[cap]).sum()
s2 = (target * base - F - capeur) / unc
mv = np.where(L.fm.notna(), L.fm, np.maximum(0, np.minimum(s2 * L.cp, L.cp + ceil))); mv = np.where(L.hold, 0.0, mv)
L["m"] = mv
out = {"x": float((L.b * L.m).sum())}
for name, e in (("central", -0.1584), ("stress", -0.81)):
    out["xa_" + name] = float((L.b * ((1 + L.m) * (1 + e * L.m) - 1)).sum())
cal = D["months"]["cal"]


def fy(iso, per_db):
    y, mo, d = int(iso[:4]), int(iso[5:7]) - 1, int(iso[8:10]); res = {}
    for i in range(36):
        yy = y + (mo + i) // 12; mn = (mo + i) % 12 + 1
        dim = pd.Period("%d-%02d" % (yy, mn)).days_in_month; w = (dim - d + 1) / dim if i == 0 else 1
        idx = cal.index(mn); v = sum(x * D["months"]["share"][str(k)][idx] for k, x in per_db.items() if str(k) in D["months"]["share"])
        f = "FY%d" % (yy + 1 if mn >= 4 else yy); res[f] = res.get(f, 0) + v * w
    return res


perdb = {int(k): float(v) for k, v in (L.assign(x=L.b * L.m).groupby("db").x.sum()).items()}
perdba = {int(k): float(v) for k, v in (L.assign(x=L.b * ((1 + L.m) * (1 + -0.1584 * L.m) - 1)).groupby("db").x.sum()).items()}
out["fy_20270101"] = fy("2027-01-01", perdb); out["fy_20270401"] = fy("2027-04-01", perdb); out["fyc_20270101"] = fy("2027-01-01", perdba)
page = json.loads(re.search(r"PAGEJSON:(\{.*?\})ENDJSON", (H.parent.parent / "_qa_sim_20261015" / "v6b.dom.txt").read_text(encoding="ascii", errors="ignore"), re.S).group(1))
ok = True
def chk(name, a, b):
    global ok
    d = abs(a - b); print("%-22s python %16.2f page %16.2f diff %.2f" % (name, a, b, d)); ok &= d < 1.0
chk("extra", out["x"], page["x"]); chk("after central", out["xa_central"], page["xa_central"]); chk("after stress", out["xa_stress"], page["xa_stress"])
chk("FY2027 from 1 Jan 2027", out["fy_20270101"]["FY2027"], page["fy1"]["FY2027"]); chk("FY2028 from 1 Jan 2027", out["fy_20270101"]["FY2028"], page["fy1"]["FY2028"])
chk("FY2028 from 1 Apr 2027", out["fy_20270401"]["FY2028"], page["fy2"]["FY2028"]); chk("FY2027 central 1 Jan", out["fyc_20270101"]["FY2027"], page["fyc1"]["FY2027"])
print("ALL OK" if ok else "MISMATCH")
