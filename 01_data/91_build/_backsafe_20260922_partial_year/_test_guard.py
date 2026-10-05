"""Prove the two safety properties of the patched builder:
  1. _assert_no_capture_on_partial_rows REFUSES a partial row carrying a percentage
     or a colour.
  2. _is_partial_row prefers the row's own period_basis and falls back to
     year_coverage.is_partial.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics/Isuzu/prism"
sys.path.insert(0, str(PRISM))

spec = importlib.util.spec_from_file_location(
    "enrich_guard", PRISM / "scripts/enrich_gps_spu_v9.py"
)
m = importlib.util.module_from_spec(spec)
sys.modules["enrich_guard"] = m
spec.loader.exec_module(m)

fails = []

# 1. refusal on a percentage
df = pd.DataFrame(
    [
        {"year": 2026, "distributor_code": "IUK", "period_basis": "partial_year",
         "gps_capture_vs_max": 0.3289, "traffic_light_v9": "unknown",
         "gps_capture_ex_warranty_vs_max": None, "traffic_light_v9_ex_warranty": None},
    ]
)
try:
    m._assert_no_capture_on_partial_rows(df)
    fails.append("did NOT refuse a partial row carrying gps_capture_vs_max")
except SystemExit as e:
    print(f"1a. refused capture %: {e}")

# 2. refusal on a colour
df2 = df.copy()
df2["gps_capture_vs_max"] = None
df2["traffic_light_v9"] = "red"
try:
    m._assert_no_capture_on_partial_rows(df2)
    fails.append("did NOT refuse a partial row carrying a traffic_light_v9 colour")
except SystemExit as e:
    print(f"1b. refused colour:    {e}")

# 3. refusal on the ex-warranty pair
df3 = df.copy()
df3["gps_capture_vs_max"] = None
df3["traffic_light_v9"] = "unknown"
df3["gps_capture_ex_warranty_vs_max"] = 0.2
try:
    m._assert_no_capture_on_partial_rows(df3)
    fails.append("did NOT refuse gps_capture_ex_warranty_vs_max")
except SystemExit as e:
    print(f"1c. refused ex-warr cap: {e}")

# 4. clean partial row passes
df4 = df3.copy()
df4["gps_capture_ex_warranty_vs_max"] = None
try:
    m._assert_no_capture_on_partial_rows(df4)
    print("1d. clean partial row passes (correct)")
except SystemExit as e:
    fails.append(f"refused a clean partial row: {e}")

# 5. full-year row is not constrained
df5 = df.copy()
df5["period_basis"] = "full_year"
try:
    m._assert_no_capture_on_partial_rows(df5)
    print("1e. full-year row with a capture % passes (correct)")
except SystemExit as e:
    fails.append(f"refused a full-year row: {e}")

# 6. _is_partial_row: own basis wins
row_partial = pd.Series({"year": 2025, "period_basis": "partial_year"})
row_full = pd.Series({"year": 2026, "period_basis": "full_year"})
row_none25 = pd.Series({"year": 2025})
row_none26 = pd.Series({"year": 2026})
checks = [
    ("own basis partial_year (year 2025) -> True", m._is_partial_row(row_partial), True),
    ("own basis full_year (year 2026) -> False", m._is_partial_row(row_full), False),
    ("no basis, year 2025 -> False", m._is_partial_row(row_none25), False),
    ("no basis, year 2026 -> True", m._is_partial_row(row_none26), True),
]
for label, got, want in checks:
    ok = got == want
    print(f"2. {label}: got={got} want={want} {'OK' if ok else 'FAIL'}")
    if not ok:
        fails.append(label)

print()
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
    raise SystemExit(1)
print("all guard properties hold")
