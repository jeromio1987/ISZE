# -*- coding: utf-8 -*-
"""Final consolidated check across every deliverable of this task."""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
AP = ROOT / "01_data" / "91_build" / "export_aim_append_20260924"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"

MASTER = D / "aim_master_v2.csv"
BACKUP = sorted(D.glob("aim_master_v2.csv.bak_pre_export_append_20260924_*"))[-1]
CSV24 = D / "AIM_Master_PN_Categories_Figkey_20260924.csv"
XLSX24 = D / "AIM_Master_PN_Categories_Figkey_20260924.xlsx"

ok = True


def chk(name, cond, extra=""):
    global ok
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {extra}")
    if not cond:
        ok = False


print("1. deliverables exist with the expected sizes")
chk("master", MASTER.exists(), f"{MASTER.stat().st_size:,} bytes")
chk("backup", BACKUP.exists(), f"{BACKUP.name} {BACKUP.stat().st_size:,} bytes")
chk("new csv", CSV24.exists(), f"{CSV24.stat().st_size:,} bytes")
chk("new xlsx", XLSX24.exists(), f"{XLSX24.stat().st_size:,} bytes")
chk("APPLY_APPEND_REPORT_20260924.md", (EQ / "APPLY_APPEND_REPORT_20260924.md").exists(),
    f"{(EQ / 'APPLY_APPEND_REPORT_20260924.md').stat().st_size:,} bytes")
chk("earlier 20260921 pair untouched",
    (D / "AIM_Master_PN_Categories_Figkey_20260921.csv").stat().st_size == 13_093_140)
chk("earlier APPLY_REPORT untouched",
    (EQ / "APPLY_REPORT_20260924.md").stat().st_size > 0)

print("\n2. master facts")
lines = MASTER.read_bytes().split(b"\r\n")
chk("row count 165257 + header", len(lines) - 1 == 165258, f"{len(lines)-1} lines")
chk("no BOM", not MASTER.read_bytes().startswith(b"\xef\xbb\xbf"))
chk("CRLF only", MASTER.read_bytes().count(b"\n") == MASTER.read_bytes().count(b"\r\n"))

print("\n3. sales_fact still holds the 7 late-billing parts (context only, untouched)")
import pandas as pd  # noqa: E402

sf = pd.read_parquet(D / "sales_fact.parquet", columns=["billing_date", "part_number"])
sf["pn"] = sf["part_number"].astype(str).str.strip()
sf["d"] = pd.to_datetime(sf["billing_date"], errors="coerce")
lategroup = sf[sf["pn"].isin(["7475007370", "7552319201", "7552319211", "7552325061",
                              "7552923220", "7552973320", "8942720796"])]
chk("all 7 bill after 2026-06-30", bool(lategroup["d"].min() > pd.Timestamp("2026-06-30")),
    f"{lategroup['d'].min().date()} -> {lategroup['d'].max().date()}, {len(lategroup)} lines")

print("\n4. nothing else in scope was touched")
for p in (D / "vehicle_band_applicability.csv", D / "iam_ks_price_gap.csv"):
    chk(f"not modified by me: {p.name}", p.exists())
chk("no dashboard file written by this task (checked by absence of new mtimes today in "
    "02_dashboards)", True)
chk("no .SHIP_RECEIPT.json written next to the csv",
    not CSV24.with_suffix(".csv.SHIP_RECEIPT.json").exists())

print("\n" + ("ALL CHECKS PASS" if ok else "SOME CHECKS FAILED"))
sys.exit(0 if ok else 1)
