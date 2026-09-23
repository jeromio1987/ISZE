"""Dry-run the builder against a COPY, so we can prove what it would change.

Points config.GPS_SPU_BY_DB_CSV at a temp copy, runs the (optionally patched)
script's main(), and diffs the result against the untouched original.

Usage:
    python _dryrun_builder.py <script_path> <output_csv>
"""
from __future__ import annotations

import csv
import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics/Isuzu/prism"
SRC = ROOT / "01_data/00_derived/gps_spu_by_distributor.csv"

script_path = Path(sys.argv[1])
out_csv = Path(sys.argv[2])
if not out_csv.exists():
    shutil.copy2(SRC, out_csv)

sys.path.insert(0, str(PRISM))
sys.path.insert(0, str(PRISM / "scripts"))
import config  # noqa: E402

config.GPS_SPU_BY_DB_CSV = out_csv

spec = importlib.util.spec_from_file_location("_builder_under_test", script_path)
mod = importlib.util.module_from_spec(spec)
sys.modules["_builder_under_test"] = mod
spec.loader.exec_module(mod)
# the script imported the name at module load; rebind the module-level constant too
mod.GPS_SPU_BY_DB_CSV = out_csv
mod.main()

orig = list(csv.DictReader(SRC.open(encoding="utf-8-sig", newline="")))
new = list(csv.DictReader(out_csv.open(encoding="utf-8-sig", newline="")))
print(f"rows: original={len(orig)} new={len(new)}")
oc = list(orig[0].keys())
nc = list(new[0].keys())
print(f"cols: original={len(oc)} new={len(nc)}")
if oc != nc:
    print(f"  only original: {set(oc) - set(nc)}")
    print(f"  only new:      {set(nc) - set(oc)}")

key = lambda r: (r["year"], r["distributor_code"])
om = {key(r): r for r in orig}
nm = {key(r): r for r in new}
print(f"  only original rows: {sorted(set(om) - set(nm))}")
print(f"  only new rows:      {sorted(set(nm) - set(om))}")

changed: dict[str, list[str]] = {}
for k in sorted(set(om) & set(nm)):
    for c in oc:
        if c not in nm[k]:
            continue
        a = (om[k].get(c) or "").strip()
        b = (nm[k].get(c) or "").strip()
        if a != b:
            changed.setdefault(c, []).append(f"{k[0]} {k[1]}: {a!r} -> {b!r}")
print("\ncolumns that differ:")
for c, items in changed.items():
    print(f"  {c}: {len(items)} rows")
    for i in items[:30]:
        print(f"     {i}")
    if len(items) > 30:
        print(f"     ... and {len(items) - 30} more")
if not changed:
    print("  (none)")
