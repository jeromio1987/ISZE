"""Unwrap the CDP dump into a clean decode result file, and report what it actually holds.

The CDP response wraps the page's JSON string in {result:{type,value}}. This extracts the inner
array, writes it as clean JSON, and prints the shape so the numbers can be quoted with evidence.
"""

import json
from pathlib import Path

RAW = Path(r"C:\Users\jerom\.cursor\browser-logs\cdp-response-Runtime.evaluate-2026-09-19T05-13-22-081Z.json")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\epc_decode_batch1_20260919.json")

raw = json.loads(RAW.read_text(encoding="utf-8"))
inner = raw["result"]["value"]
records = json.loads(inner) if isinstance(inner, str) else inner
if isinstance(records, dict):
    records = records.get("result", records)

OUT.write_text(json.dumps(records, indent=1), encoding="utf-8")

# Honest shape report.
n = len(records)
errors = [r for r in records if r.get("error")]
found = [r for r in records if r.get("found")]
zero = [r for r in records if r.get("found") is False]
with_fam = [r for r in found if r.get("families")]
no_fam = [r for r in found if not r.get("families")]

fams: dict[str, int] = {}
for r in found:
    for f in r.get("families", []):
        fams[f] = fams.get(f, 0) + 1

print(f"wrote {OUT}")
print(f"  records              : {n}")
print(f"  errors               : {len(errors)}")
print(f"  found                : {len(found)}")
print(f"  explicitly zero hits : {len(zero)}")
print(f"  found with family    : {len(with_fam)}")
print(f"  found but no family  : {len(no_fam)}")
print()
print("  families seen (count of part numbers touching each):")
for f, c in sorted(fams.items(), key=lambda kv: -kv[1]):
    print(f"    {f:34s} {c}")

# Which of the batch's part numbers carry only light-vehicle fitment vs truck fitment.
LIGHT = ("PASSENGER VEHICLE PICK UP", "PASSENGER VEHICLE SUV")
TRUCK = ("TRUCKS N", "TRUCKS F&G", "TRUCKS C&E", "TRUCKS 810")
light_only = [r["pn"] for r in found
              if r.get("families") and all(f in LIGHT for f in r["families"])]
truck_any = [r["pn"] for r in found
             if any(f in TRUCK for f in (r.get("families") or []))]
print()
print(f"  light-vehicle only   : {len(light_only)} part numbers")
print(f"  any truck fitment    : {len(truck_any)} part numbers")
