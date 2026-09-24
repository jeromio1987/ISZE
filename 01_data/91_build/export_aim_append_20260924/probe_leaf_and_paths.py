# -*- coding: utf-8 -*-
"""Read-only: find the 'Engine assembly' leaf and derive evidence for the 44."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"

not_in_master = [
    l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()
]

# ---------------------------------------------------------------- classification
print("=" * 100)
print("STEP 5 — the 'Engine assembly' leaf in the classified workbook")
print("=" * 100)
cls_by_pn: dict[str, dict] = {}
cls_hdr = None
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    cls_hdr = rd.fieldnames
    for r in rd:
        cls_by_pn[r["part_number"]] = r

# any leaf containing 'engine assembly'
leaf_counter: Counter = Counter()
for r in cls_by_pn.values():
    for col in ("catalog_l3", "aim_l3_fixed", "workbook_l3"):
        v = (r.get(col) or "").strip()
        if "engine" in v.lower() and "assembl" in v.lower():
            leaf_counter[(col, r.get("catalog_l1", ""), r.get("catalog_l2", ""), v)] += 1
print("--- leaves matching 'engine*assembl*' ---")
for k, n in leaf_counter.most_common(40):
    print(f"{k}  x{n}")

# exact 'Engine assembly'
print("\n--- rows whose catalog_l3 is exactly 'Engine assembly' ---")
exact = [r for r in cls_by_pn.values() if (r.get("catalog_l3") or "").strip() == "Engine assembly"]
print("count:", len(exact))
pc = Counter((r.get("catalog_l1"), r.get("catalog_l2"), r.get("catalog_l3")) for r in exact)
for k, n in pc.most_common(10):
    print(f"  {k}  x{n}")

# ENGINE ASM rows anywhere in the classified workbook (description_norm)
print("\n--- classified rows whose description_norm == 'ENGINE ASM' ---")
eng = [r for r in cls_by_pn.values() if (r.get("description_norm") or "").strip() == "ENGINE ASM"]
print("count:", len(eng))
pc = Counter(
    (
        r.get("description_norm"),
        r.get("catalog_l1"),
        r.get("catalog_l2"),
        r.get("catalog_l3"),
        r.get("aim_l1_fixed"),
        r.get("aim_l2_fixed"),
        r.get("aim_l3_fixed"),
    )
    for r in eng
)
for k, n in pc.most_common(10):
    print(f"  {k}  x{n}")
print("sample pns:", [r["part_number"] for r in eng[:15]])

# ---------------------------------------------------------------- master
print()
print("=" * 100)
print("STEP 6 — description evidence on the master")
print("=" * 100)
master_by_pn: dict[str, dict] = {}
master_desc: dict[str, list] = defaultdict(list)
master_fig: dict[str, list] = defaultdict(list)
master_hdr = None
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    master_hdr = rd.fieldnames
    for r in rd:
        master_by_pn[r["part_number"]] = r
        dn = (r.get("description") or "").strip()
        master_desc[dn].append(r)
        fk = (r.get("fig_key") or "").strip()
        if fk:
            master_fig[fk].append(r)

PLACEHOLDER = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None"}


def full_path(r: dict) -> tuple[str, str, str]:
    """Resolve a master row the way the builder does not — plain columns for evidence."""
    l1 = (r.get("aim_l1") or "").strip()
    l2 = (r.get("aim_l2") or "").strip()
    l3 = (r.get("aim_l3") or "").strip()
    f1 = (r.get("aim_l1_fixed") or "").strip()
    f2 = (r.get("aim_l2_fixed") or "").strip()
    if f1 not in PLACEHOLDER:
        l1 = f1
    if f2 not in PLACEHOLDER:
        l2 = f2
    return l1, l2, l3


def cls_path(r: dict) -> tuple[str, str, str]:
    l1 = (r.get("aim_l1_fixed") or "").strip()
    l2 = (r.get("aim_l2_fixed") or "").strip()
    l3 = (r.get("aim_l3_fixed") or "").strip()
    if l1 in PLACEHOLDER:
        l1 = (r.get("workbook_l1") or "").strip()
    if l2 in PLACEHOLDER or not l2:
        l2 = (r.get("workbook_l2") or "").strip()
    if l3 in PLACEHOLDER or not l3:
        l3 = (r.get("workbook_l3") or "").strip()
    return l1, l2, l3


for pn in not_in_master:
    pass

# ---------------------------------------------------------------- per-PN evidence
print("\nper-PN evidence for the 44:")
for pn in not_in_master:
    # description from the tiering file is loaded elsewhere; use master description search
    print(f"\n{pn}")
