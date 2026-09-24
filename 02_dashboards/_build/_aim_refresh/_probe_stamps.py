import csv, collections, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
D = "01_data/00_derived/"

for name in ["AIM_Master_PN_Categories_Figkey_20260921.csv",
             "AIM_Master_PN_Categories_Figkey_20260924.csv",
             "aim_master_v2.csv",
             "aim_pn_classification_20260920.csv"]:
    p = D + name
    r = csv.DictReader(open(p, encoding="utf-8-sig", newline=""))
    cols = r.fieldnames
    stamp = collections.Counter()
    lines = collections.Counter()
    n = 0
    for row in r:
        n += 1
        stamp[(row.get("aim_source") or "").strip()] += 1
        if "line_kind" in cols:
            lines[(row.get("line_kind") or "").strip()] += 1
    print("=" * 6, name, "rows", n, "sha", hashlib.sha256(open(p, "rb").read()).hexdigest()[:12])
    print("   aim_source with export_aim_eq:", sum(v for k, v in stamp.items() if "export_aim_eq_20260924" in k))
    print("   top aim_source:", stamp.most_common(6))
    if lines:
        print("   line_kind:", lines.most_common(8))
