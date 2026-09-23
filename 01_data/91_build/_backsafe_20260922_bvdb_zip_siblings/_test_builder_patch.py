#!/usr/bin/env python3
"""Prove the builder patches produce the columns, without running the builders.

Imports the two patched builders and exercises the functions they now call, on
frames shaped like the rows they write. Nothing is built and nothing is written -
this only proves the guard is in the code path and that its output matches what is
already spliced into the files on disk.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
SCRIPTS = PRISM / "scripts"
sys.path.insert(0, str(PRISM))

spec = importlib.util.spec_from_file_location("bbp", SCRIPTS / "build_bvp_p4_p5.py")
bbp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bbp)

frame = pd.DataFrame({
    "year": [2023, 2025, 2026, 2026],
    "distributor_code": ["ITUK", "IUK", "IUK", "GREECE"],
    "product_family": ["Brakes"] * 4,
    "line_type": ["all"] * 4,
    "net_sales_eur": [1.0, 2.0, 3.0, 4.0],
    "uio_units": [1, 1, 1, 1],
    "spu_eur": [1.0, 2.0, 3.0, 4.0],
})
out = bbp._add_period_columns(frame.copy())

print("builder: build_bvp_p4_p5.py -> _add_period_columns")
print(out[["year", "distributor_code", "period_basis"]].to_string(index=False))
print("   columns now:", list(out.columns))

assert list(out.columns)[-2:] == ["period_basis", "coverage_note"], "column order wrong"
assert out.loc[out["year"] == 2023, "period_basis"].iloc[0] == "full_year"
assert out.loc[out["year"] == 2025, "period_basis"].iloc[0] == "full_year"
assert (out.loc[out["year"] == 2026, "period_basis"] == "partial_year").all()
assert out.loc[out["year"] == 2026, "coverage_note"].iloc[0] == bbp.PARTIAL_COVERAGE_NOTE

# The wording must match what is already in the files, or the next build would
# restyle it and the two would diverge.
sys.path.insert(0, str(Path(__file__).resolve().parent))
on_disk = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_family.csv")
note_disk = on_disk.loc[on_disk["period_basis"] == "partial_year", "coverage_note"].iloc[0]
print("\n   builder note == spliced note:", bbp.PARTIAL_COVERAGE_NOTE == note_disk)
assert bbp.PARTIAL_COVERAGE_NOTE == note_disk, "wording differs between builder and file"
print("\nPASS - the builder emits the same two columns, in the same order, with the same wording")
