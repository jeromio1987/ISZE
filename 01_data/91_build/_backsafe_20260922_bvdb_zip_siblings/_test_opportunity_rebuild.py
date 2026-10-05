#!/usr/bin/env python3
"""Does a rebuild of pms_opportunity_matrix.csv reproduce the existing file exactly?

Compares only the columns the old file carries, per year, and reports the largest
numeric difference and any text differences. 2023-2025 must be exact; 2026 must also
be exact because revenue_gap_eur is computed the same way and the new like-for-like
column is an ADDITION, not a change.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
LIVE = ROOT / "01_data" / "00_derived" / "pms_opportunity_matrix.csv"

tmp = Path(tempfile.gettempdir()) / "pms_opp_rebuild_preview.csv"
r = subprocess.run([sys.executable, "scripts/build_pms_opportunity_matrix.py",
                    "--out", str(tmp), "--compare-to", str(LIVE)],
                   cwd=str(PRISM), capture_output=True, text=True, encoding="utf-8")
print(r.stdout)
if r.stderr.strip():
    print("stderr:", r.stderr[-2500:])
print("builder exit code:", r.returncode)

old = pd.read_csv(LIVE)
new = pd.read_csv(tmp)
keep = ["distributor_code", "pms_category", "year"]
shared = [c for c in old.columns if c in new.columns]
print(f"\nold cols {len(old.columns)}  new cols {len(new.columns)}  "
      f"added: {[c for c in new.columns if c not in old.columns]}")

m = old.merge(new, on=keep, how="inner", suffixes=("_old", "_new"))
print(f"matched rows: {len(m)} of {len(old)}")
fails = []
for yr in sorted(old["year"].unique()):
    sub = m[m["year"] == yr]
    worst, worst_c = 0.0, ""
    for c in shared:
        if c in keep:
            continue
        a, b = sub[f"{c}_old"], sub[f"{c}_new"]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            d = (a.astype(float) - b.astype(float)).abs().max()
            if d > worst:
                worst, worst_c = float(d), c
        else:
            n = int((a.astype(str) != b.astype(str)).sum())
            if n:
                fails.append(f"{yr} {c}: {n} text rows differ")
    status = "EXACT" if worst == 0 else f"max diff {worst:.6f} on {worst_c}"
    print(f"   {yr}: {status}")
    if worst > 0.01:
        fails.append(f"{yr}: numeric drift {worst:.6f} on {worst_c}")

print("\nRESULT:", "FAIL" if fails else "rebuild reproduces every existing column exactly")
for f in fails:
    print("   -", f)
sys.exit(1 if fails else 0)
