import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

FILES = ["02_dashboards/sales/ISZE_AIM_Classification_Paper.html",
         "02_dashboards/pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html",
         "02_dashboards/sales/aim_cy2026.data.js"]
for f in FILES:
    t = open(f, encoding="utf-8", errors="ignore").read()
    print("=" * 5, f)
    for m in re.finditer(r'.{70}NaN.{40}', t):
        s = " ".join(m.group(0).split())
        if "isNaN" in s:
            continue
        print("   ", s[:150])
