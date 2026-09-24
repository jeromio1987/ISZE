import json, re, sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
B = "02_dashboards/_build/_aim_refresh/before/"


def meta(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    best = None
    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', t, re.S):
        s = m.group(1)
        if '"meta"' in s and '"rows"' in s and (best is None or len(s) > len(best)):
            best = s
    d = json.loads(best)
    return d["meta"]


for label, p in [("AFTER", "02_dashboards/pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html"),
                 ("BEFORE", B + "pricing__ISZE_AIM_Repertoire_Map_2026-09-17.html")]:
    m = meta(p)
    print("=" * 5, label)
    print("   l1 list      :", m["l1"])
    print("   residual_l1  :", m["residual_l1"])
    print("   unclassified_l1:", m.get("unclassified_l1"))
    print("   no_l3        :", m.get("no_l3"))
    missing = [x for x in m["residual_l1"] if x not in m["l1"]]
    print("   residual not in l1 ->", missing)
