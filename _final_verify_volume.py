# -*- coding: utf-8 -*-
"""Final verification after the Tier A volume run."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(__file__).resolve().parent


def run(script: Path, args=None):
    p = subprocess.run([sys.executable, str(script), *(args or [])], cwd=str(R),
                       capture_output=True, text=True, errors="replace")
    return p.returncode, (p.stdout + p.stderr)


checks = [
    ("parsers selftest", "04_tools/delegation/parsers/price_parsers.py", ["--selftest"]),
    ("offline probe", "04_tools/delegation/parsers/run_probe.py", None),
    ("bridge", "04_tools/price_ledger/build_scraped_observations.py", ["--emit"]),
    ("ledger", "04_tools/price_ledger/build_price_ledger.py", None),
    ("verbatim check", "04_tools/price_ledger/verify_scraped_observations.py", None),
    ("additive check", "04_tools/price_ledger/check_loader_additive.py", None),
    ("crossref grading", "04_tools/aftermarket_intelligence/grade_crossref_edges.py", None),
    ("price movement", "04_tools/aftermarket_intelligence/build_price_movement.py", None),
    ("tender join", "04_tools/aftermarket_intelligence/build_tender_price_context.py", None),
]

print("=" * 74)
print("FINAL VERIFICATION")
print("=" * 74)
fails = []
for label, rel, args in checks:
    rc, out = run(R / rel, args)
    print(f"{'PASS' if rc == 0 else 'FAIL'}  {label}")
    if rc:
        fails.append(label)
        for ln in out.strip().splitlines()[-5:]:
            print(f"        {ln[:118]}")

m = json.loads((R / "01_data/00_derived/price_observations.meta.json").read_text(encoding="utf-8"))
print(f"\n{'='*74}\nRESULT\n{'='*74}")
print(f"ledger rows          : {m['rows']:,}")
print(f"part numbers observed: {m['isuzu_part_numbers_with_observation']:,}")

web = {k: v for k, v in m["rows_by_loader"].items()
       if k in {"amayama", "ks", "omega", "geparden", "mekster", "tungen", "autoline"}}
print(f"web-sourced rows     : {sum(web.values()):,}  {web}")
print(f"price types          : {m['rows_by_price_type']}")

d = pd.read_parquet(R / "01_data/00_derived/price_observations.parquet")
scraped = d[d["loader"].isin(web)]
print(f"\nscraped part numbers : {scraped['part_no'].nunique()}")
print(f"sources              : {sorted(scraped['source'].unique())}")

pm = R / "04_tools/aftermarket_intelligence/state/price_movement.csv"
if pm.exists():
    mv = pd.read_csv(pm)
    print(f"\nmovement pairs watched: {len(mv)}")
    if len(mv):
        print(mv[["part_no", "source", "first_price", "last_price", "change_pct"]].to_string(index=False))

print()
if fails:
    print(f"FAILURES: {fails}")
    raise SystemExit(1)
print("ALL CHECKS PASS")
