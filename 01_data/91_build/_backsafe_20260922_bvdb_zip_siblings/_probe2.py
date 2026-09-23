#!/usr/bin/env python3
"""READ-ONLY: raw bytes of the sibling files, the pms capture output, and the
declared schema in verification_fixtures.yaml."""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

print("=" * 100)
print("RAW BYTE SHAPE (does any cell contain a comma/newline that needs quoting?)")
print("=" * 100)
for n in ("gps_spu_by_family.csv", "gps_spu_pms.csv", "aim_gps_matrix.csv",
          "gps_spu_by_distributor.csv", "pms_capture_by_db_year.csv"):
    p = DER / n
    raw = p.read_bytes()
    txt = raw.decode("utf-8-sig")
    lines = txt.splitlines()
    quoted = [ln for ln in lines if '"' in ln]
    print(f"{n}")
    print(f"   lines={len(lines)} quoted_lines={len(quoted)} "
          f"ends_with_newline={raw.endswith(b'\\n')} has_crlf={b'\\r\\n' in raw} "
          f"bom={raw[:3] == b'\\xef\\xbb\\xbf'}")

print()
print("=" * 100)
print("pms_capture_by_db_year.csv — actual_qty / expected_qty per year (is the denominator part-year?)")
print("=" * 100)
cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
print("columns:", list(cap.columns))
c = cap[cap["line_type"] == "total"]
print(c.groupby("year").agg(expected_qty=("expected_qty", "sum"),
                            actual_qty=("actual_qty", "sum"),
                            capture=("capture_rate", "mean")
                            if "capture_rate" in c.columns else
                            ("expected_qty", "size")).to_string())
print("\nrow counts by year (line_type=total):")
print(c.groupby("year").size().to_string())

print()
print("=" * 100)
print("verification_fixtures.yaml -> schema_required")
print("=" * 100)
fx = yaml.safe_load((ROOT / "03_analytics" / "Isuzu" / "prism" / "data" /
                     "verification_fixtures.yaml").read_text(encoding="utf-8"))
sr = (fx.get("schema_required") or {})
print("keys:", list(sr.keys()))
for f in sr.get("files") or []:
    print(" ", f)

print()
print("=" * 100)
print("Which checks does the verifier run, and does any read the sibling files' values?")
print("=" * 100)
src = (ROOT / "03_analytics" / "Isuzu" / "prism" / "scripts" /
       "verify_derived_pipeline.py").read_text(encoding="utf-8")
for n in ("gps_spu_by_family", "gps_spu_pms", "spu_eur", "aim_gps_matrix"):
    hits = [i + 1 for i, ln in enumerate(src.splitlines()) if n in ln]
    print(f"  {n}: lines {hits}")
