"""Verify the builder guard result: 2026 blank/unknown, 2023-2025 unchanged.

Usage: python _verify_builder_result.py <after_csv>
"""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BACKUP = ROOT / "01_data/91_build/_backsafe_20260922_partial_year/original/01_data/00_derived/gps_spu_by_distributor.csv"
after = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "01_data/00_derived/gps_spu_by_distributor.csv"

CAP = ("gps_capture_vs_max", "gps_capture_ex_warranty_vs_max")
LIGHT = ("traffic_light_v9", "traffic_light_v9_ex_warranty")
UNTOUCHED = ("total_sales_eur", "max_spend_eur", "uio_units", "spend_per_unit_eur",
             "sales_ex_warranty_eur", "spend_per_unit_ex_warranty_eur")

before_rows = list(csv.DictReader(BACKUP.open(encoding="utf-8-sig", newline="")))
after_rows = list(csv.DictReader(after.open(encoding="utf-8-sig", newline="")))
print(f"rows before={len(before_rows)} after={len(after_rows)}")
assert len(before_rows) == len(after_rows), "row count changed"

key = lambda r: (r["year"], r["distributor_code"])
b = {key(r): r for r in before_rows}
a = {key(r): r for r in after_rows}
assert set(b) == set(a), "row set changed"

print("\n1. 2026 rows must carry NO percentage and NO colour except unknown:")
bad = []
for k, r in sorted(a.items()):
    if k[0] != "2026":
        continue
    for c in CAP:
        if (r.get(c) or "").strip():
            bad.append(f"{k} {c}={r[c]!r}")
    for c in LIGHT:
        v = (r.get(c) or "").strip()
        if v not in ("", "unknown"):
            bad.append(f"{k} {c}={v!r}")
print("   FAIL: " + "; ".join(bad) if bad else "   OK - all 22 rows blank/unknown")

print("\n2. partial rows must carry period_basis and a non-empty coverage_note:")
for k, r in sorted(a.items()):
    if k[0] != "2026":
        continue
    assert r["period_basis"] == "partial_year", f"{k} basis={r['period_basis']!r}"
    assert (r["coverage_note"] or "").strip(), f"{k} has empty note"
print("   OK - 22/22 rows annotated")

print("\n3. 2023-2025 rows must be identical to before, cell by cell:")
diffs = []
for k in sorted(a):
    if k[0] == "2026":
        continue
    for c in a[k]:
        x = (b[k].get(c) or "")
        y = (a[k].get(c) or "")
        if x != y:
            same_float = False
            try:
                same_float = float(x) == float(y)
            except ValueError:
                pass
            diffs.append((k, c, x, y, same_float))
if diffs:
    for k, c, x, y, sf in diffs[:40]:
        print(f"   {k} {c}: {x!r} -> {y!r}  (numerically equal: {sf})")
    print(f"   {len(diffs)} cell differences; "
          f"{sum(1 for d in diffs if d[4])} are equal as numbers, "
          f"{sum(1 for d in diffs if not d[4])} are not")
else:
    print("   OK - byte-identical cell text on every 2023-2025 row")

print("\n4. total_sales_eur / max_spend_eur / uio_units / spend_per_unit_eur, 2026 vs before:")
for k, r in sorted(a.items()):
    if k[0] != "2026":
        continue
    for c in UNTOUCHED:
        x = (b[k].get(c) or "")
        y = (r.get(c) or "")
        if x != y:
            print(f"   DIFF {k} {c}: {x!r} -> {y!r}")
print("   (no DIFF lines above means every one of those four is unchanged)")

print("\n5. sha256:")
for lbl, p in (("before", BACKUP), ("after", after)):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f"   {lbl}: {h}")
print(f"\n   numeric drift in spend_per_unit_eur on non-partial rows: "
      f"{sum(1 for d in diffs if d[1] == 'spend_per_unit_eur')}")
