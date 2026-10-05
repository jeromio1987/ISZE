# -*- coding: utf-8 -*-
"""Read-only evidence: master + classified workbook paths for the 44 descriptions."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"

not_in_master = [
    l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()
]

# description + fig per PN from the tiering file
info: dict[str, dict] = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in not_in_master:
            info[r["pn"]] = r

PLACEHOLDER = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review"}


def master_path(r: dict) -> tuple[str, str, str]:
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


print("=" * 100)
print("A. master paths for ENGINE ASM")
print("=" * 100)
master_by_pn: dict[str, dict] = {}
by_desc: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
by_fig: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    master_hdr = rd.fieldnames
    for r in rd:
        master_by_pn[r["part_number"]] = r
        by_desc[(r.get("description") or "").strip()].append(master_path(r))
        fk = (r.get("fig_key") or "").strip()
        if fk:
            by_fig[fk].append(master_path(r))

print("master has ENGINE ASM rows:", len(by_desc.get("ENGINE ASM", [])))
for k, n in Counter(by_desc.get("ENGINE ASM", [])).most_common(15):
    print("  ", k, "x", n)

for d in ("HEAD ASM; CYL", "PLATE ASM; PRESSURE,CLU", "SPRING ASM; LEAF,FRT", "TANK; FUEL"):
    print(f"\nmaster desc {d!r}: rows={len(by_desc.get(d, []))}")
    for k, n in Counter(by_desc.get(d, [])).most_common(10):
        print("  ", k, "x", n)

# ---- classified workbook: ENGINE ASM ----
print()
print("=" * 100)
print("B. classified workbook — ENGINE ASM content")
print("=" * 100)
eng_rows = []
eng_all = []
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        dn = (r.get("description_norm") or "").strip()
        if "ENGINE ASM" in dn.upper():
            eng_rows.append(r)
        if (r.get("catalog_l3") or "").strip() == "Engine assembly":
            eng_all.append(r)
print("classified rows with ENGINE ASM in description_norm:", len(eng_rows))
for k, n in Counter(
    (r.get("description_norm"), r.get("catalog_l1"), r.get("catalog_l2"), r.get("catalog_l3")) for r in eng_rows
).most_common(20):
    print("  ", k, "x", n)
print("\nclassified rows with catalog_l3 == 'Engine assembly':", len(eng_all))
for k, n in Counter(
    (r.get("catalog_l1"), r.get("catalog_l2"), r.get("catalog_l3")) for r in eng_all
).most_common(20):
    print("  ", k, "x", n)
print("\nof the catalog leaf, the aim_l3_fixed values:")
for k, n in Counter(
    (r.get("aim_l1_fixed"), r.get("aim_l2_fixed"), r.get("aim_l3_fixed")) for r in eng_all
).most_common(20):
    print("  ", k, "x", n)
print("\nof the catalog leaf, description_norm top values:")
for k, n in Counter((r.get("description_norm") or "") for r in eng_all).most_common(15):
    print("  ", repr(k), "x", n)
