# -*- coding: utf-8 -*-
"""Read-only: is `eur` identical to `l12m_billed_eur`, and what did the 44 bill in the master window?"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
pns = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]

same = diff = 0
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        a = (r.get("l12m_billed_eur") or "").strip()
        b = (r.get("eur") or "").strip()
        if a == b:
            same += 1
        else:
            diff += 1
print(f"eur == l12m_billed_eur: {same} rows equal, {diff} rows differ")

sf = pd.read_parquet(
    D / "sales_fact.parquet",
    columns=["billing_date", "part_number", "net_sales_value"],
)
sf["pn"] = sf["part_number"].astype(str).str.strip()
sf["d"] = pd.to_datetime(sf["billing_date"], errors="coerce")
win = sf[(sf["d"] >= "2025-01-01") & (sf["d"] <= "2026-06-30")]
tot = win.groupby("pn")["net_sales_value"].sum()
print("\nbilled in the master's own window (2025-01-01..2026-06-30), for the 44 that billed:")
hit = {p: float(tot.get(p, 0.0)) for p in pns if p in tot.index}
for p, v in sorted(hit.items(), key=lambda x: -x[1]):
    print(f"   {p}  EUR {v:,.2f}")
print("count with any billing:", len(hit), "of 44")

# cross-check: an existing master row's l12m value against this recomputation
probe = "7553261410"
print(f"\nrecompute check on a master row outside the 44: 8981560940 -> ")
rec = float(tot.get("8981560940", 0.0))
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["part_number"] == "8981560940":
            print("   master l12m_billed_eur:", r["l12m_billed_eur"], "| recomputed:", round(rec, 2))
            break
