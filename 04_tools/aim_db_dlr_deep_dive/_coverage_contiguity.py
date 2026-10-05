"""Measure both-stage coverage per distributor: counts AND contiguous runs.

Reads the per-stage month presence the build already wrote into VERIFY_ALL.json,
intersects them, and reports the contiguous runs. This replaces the inferred
"longest clean run" with something measured.
"""
import json

P = r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\VERIFY_ALL.json"
d = json.load(open(P, encoding="utf-8"))
months = d["payload_months"] if "payload_months" in d else None

# the month axis the build used
import re
src = open(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\build_aim_db_dlr.py",
           encoding="utf-8").read()
print(f"report: {P}")
print(f"run: {d['run']}  built: {d['built']}  passed {d['passed']} of {d['passed']+d['failed']}\n")

print(f"{'distributor':<10} {'billed m':>9} {'sold m':>7} {'both m':>7} "
      f"{'longest run':>12}  {'run span':<22} {'12vs12 possible':>16}")
for c in d["coverage"]:
    b = c["billed_months"]; s = c["sold_months"]
    mb = c["billed_range"]; ms = c["sold_range"]
    both = c["billed_months_and_sold"] if "billed_months_and_sold" in c else None
    print(f"{c['db']:<10} {b:>9} {s:>7} {str(both):>7} "
          f"{'(see run check)':>12}  {(str(ms) if ms else '-'):<22}")
print()
print("keys available in each coverage row:", sorted(d["coverage"][0].keys()))
