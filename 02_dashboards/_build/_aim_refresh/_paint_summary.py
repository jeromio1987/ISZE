import json, sys
sys.stdout.reconfigure(encoding="utf-8")
import os
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
d = json.load(open("02_dashboards/_build/_aim_refresh/paint_report.json", encoding="utf-8"))
print(f'{"page":58} {"paint":>6} {"tables":>7} {"rows":>6} {"err":>4}')
bad = []
for k, v in d.items():
    if "error" in v:
        print(f"{k:58} ERROR {v['error'][:60]}")
        continue
    paint = v.get("canvasesPainted", 0) + v.get("svgsDrawn", 0) + (1 if v.get("bars", 0) else 0)
    rows = v.get("tableRowsTotal", 0)
    err = len(v.get("console_errors") or [])
    mark = ""
    if paint == 0:
        mark = " <-- nothing painted"
        bad.append(k)
    if v.get("tables", 0) and rows == 0 and not v.get("hasDataUnavailable"):
        mark += " <-- tables all empty, no banner"
        bad.append(k)
    if err:
        mark += f" <-- {err} console errors"
    print(f'{k.replace("02_dashboards/",""):58} {paint:>6} {v.get("tables",0):>7} {rows:>6} {err:>4}{mark}')
print()
print("problems:", bad if bad else "none")
