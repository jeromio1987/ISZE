import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
import os
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

def embedded_meta(html, marker="AIMRP"):
    t = open(html, encoding="utf-8", errors="ignore").read()
    # find the largest embedded json block
    best = None
    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', t, re.S):
        s = m.group(1)
        if '"meta"' in s and '"rows"' in s:
            if best is None or len(s) > len(best):
                best = s
    if best is None:
        return None, len(t)
    d = json.loads(best)
    return d.get("meta"), len(t)

for html in ["02_dashboards/pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html",
             "02_dashboards/pricing/_build/_aim_refresh/before/pricing__ISZE_AIM_Repertoire_Map_2026-09-17.html"]:
    if not os.path.exists(html):
        print("missing", html); continue
    meta, n = embedded_meta(html)
    print("=" * 6, html, f"{n:,}")
    if meta:
        r = meta.get("repertoire", {})
        c = meta.get("checks", {})
        print("   built:", meta.get("built"))
        print("   tree_rows:", r.get("tree_rows"), "tree_pns:", r.get("tree_part_numbers"),
              "L1:", r.get("tree_l1"), "L3:", r.get("tree_l3"))
        print("   billed pns:", r.get("billed_part_numbers"), "billed_in_tree:", r.get("billed_in_tree"),
              "classified_not_billed:", r.get("classified_not_billed"))
        print("   checks:", json.dumps(c))
