import re
BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\\"
checks = {
    "02_ISZE_Leakage_Cockpit.html": ["getElementById('mod-" ],
    "03_Warranty_Commercial_Review.html": ["getElementById('sec'", "getElementById('sec"],
    "07_ISZE_Pricing_Revision_AIM_Source.html": ['id="payload"', "cb-db", "cb-l1", "cb-l2", "cb-net"],
}
for fn, pats in checks.items():
    t = open(BASE + fn, encoding="utf-8", newline="").read()
    print("==", fn)
    for p in pats:
        print("   ", repr(p), "->", t.count(p))
    for m in re.finditer(r"getElementById\([^)]{0,60}\)", t):
        s = m.group(0).replace("\n", " ")
        if "mod-" in s or "'sec'" in s or "cb-" in s:
            print("     ctx:", s)
