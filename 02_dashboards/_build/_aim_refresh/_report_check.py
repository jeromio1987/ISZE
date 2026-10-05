import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
t = open("02_dashboards/_build/AIM_DASHBOARD_REFRESH_20260924.md", encoding="utf-8").read()
paths = re.findall(r"C:\\Users\\jerom\\[^\s`]+SHIP_RECEIPT\.json", t)
print("receipt paths listed in the report:", len(paths))
missing = []
for p in paths:
    ok = os.path.exists(p)
    if not ok:
        missing.append(p)
    print(("  OK   " if ok else "  GONE ") + os.path.basename(p))
print()
print("missing:", missing if missing else "none")
