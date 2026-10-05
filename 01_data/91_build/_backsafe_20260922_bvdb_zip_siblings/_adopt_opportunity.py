#!/usr/bin/env python3
"""Adopt the verified builder output as the live derived file and the pack copy.

Preconditions, all asserted rather than assumed:
  * every column the old file carried renders text-identically in the new one
  * the new file carries period_basis / coverage_note / gap_eur_like_for_like
  * every full-year row's gap_eur_like_for_like equals its revenue_gap_eur
"""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
LIVE = ROOT / "01_data" / "00_derived" / "pms_opportunity_matrix.csv"
PACK = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23" / "03_PMS" / \
    "pms_opportunity_matrix.csv"

tmp = Path(tempfile.gettempdir()) / "pms_opp_rebuild_preview.csv"


def replace_with_retry(src: Path, dst: Path) -> None:
    t = dst.with_suffix(dst.suffix + ".tmp")
    shutil.copy2(src, t)
    for attempt in range(6):
        try:
            t.replace(dst)
            return
        except PermissionError:
            time.sleep(0.4 * (attempt + 1))
    shutil.copyfile(t, dst)
    t.unlink(missing_ok=True)


def rows(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        return next(r), list(r)


print("rebuilding from the patched builder ...")
old_cols = pd.read_csv(LIVE).columns.tolist()
r = subprocess.run([sys.executable, "scripts/build_pms_opportunity_matrix.py",
                    "--out", str(tmp)], cwd=str(PRISM),
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.strip())
if r.returncode != 0:
    print(r.stderr[-2000:])
    sys.exit(1)

h_old, r_old = rows(LIVE)
h_new, r_new = rows(tmp)
keys = ["distributor_code", "pms_category", "year"]
old_by = {tuple(x[h_old.index(k)] for k in keys): x for x in r_old}
new_by = {tuple(x[h_new.index(k)] for k in keys): x for x in r_new}
assert set(old_by) == set(new_by), "row keys differ"

shared = [c for c in h_old if c in h_new]
mismatch = 0
for k, ro in old_by.items():
    rn = new_by[k]
    for c in shared:
        if ro[h_old.index(c)] != rn[h_new.index(c)]:
            mismatch += 1
print(f"old columns text-identical: {mismatch == 0}  (mismatched cells: {mismatch})")
assert mismatch == 0, "refusing to adopt: an old column changed"

for c in ("period_basis", "coverage_note", "gap_eur_like_for_like"):
    assert c in h_new, f"missing {c}"
df = pd.read_csv(tmp)
full = df[df["period_basis"] == "full_year"]
drift = (full["gap_eur_like_for_like"] - full["revenue_gap_eur"]).abs().max()
print(f"full-year rows: {len(full)}, max |l4l - gap|: {drift}")
assert drift <= 0.01, "refusing: a full-year row moved"
print(f"added columns: {[c for c in h_new if c not in h_old]}")

replace_with_retry(tmp, LIVE)
print(f"live derived file updated: {LIVE} ({LIVE.stat().st_size} bytes)")
replace_with_retry(LIVE, PACK)
print(f"pack copy updated:         {PACK} ({PACK.stat().st_size} bytes)")
print("\ntotals by year, printed gap vs like-for-like:")
g = df.groupby("year").agg(printed=("revenue_gap_eur", "sum"),
                           like_for_like=("gap_eur_like_for_like", "sum"),
                           basis=("period_basis", "first"))
print(g.round(0).to_string())
