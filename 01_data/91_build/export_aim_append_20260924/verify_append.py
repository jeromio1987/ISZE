# -*- coding: utf-8 -*-
"""Step 11 — verify my own write, comparing the written master against the backup by part number."""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
OUTDIR = ROOT / "01_data" / "91_build" / "export_aim_append_20260924"
STAMP = "export_pr00_20260924"
MASTER = D / "aim_master_v2.csv"
BACKUP = sorted(D.glob("aim_master_v2.csv.bak_pre_export_append_20260924_*"))[-1]
CSV24 = D / "AIM_Master_PN_Categories_Figkey_20260924.csv"
XLSX24 = D / "AIM_Master_PN_Categories_Figkey_20260924.xlsx"

pns = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]
blocked = [l.strip() for l in (A / "carried_out_blocked_precedence.txt").read_text().splitlines() if l.strip()]
free = [l.strip() for l in (A / "would_land_free.txt").read_text().splitlines() if l.strip()]

print("=" * 100)
print("A. master wrote correctly?")
print("=" * 100)


def load(p):
    with p.open(encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        return hdr, list(rd)


h_before, before = load(BACKUP)
h_after, after = load(MASTER)
print(f"backup : {BACKUP.name}  {len(before)} rows  {len(h_before)} cols")
print(f"master : {MASTER.name}  {len(after)} rows  {len(h_after)} cols")
print(f"row count grew by exactly {len(pns)}: {len(after) - len(before) == len(pns)}")
print(f"header unchanged: {h_before == h_after}")

bi = {c: i for i, c in enumerate(h_before)}
after_by = {r[0]: r for r in after}
before_by = {r[0]: r for r in before}

missing = [p for p in pns if p not in after_by]
print(f"all 44 present after the write: {not missing}  {missing or ''}")

aim_cols = ["aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed", "aim_l3",
            "aim_source", "aim_changed", "has_aim", "cat_l1", "cat_l2", "cat_l3",
            "fig_key", "fig_no", "key_no", "l12m_billed_eur", "eur"]
diffs = []
for pn, old in before_by.items():
    new = after_by.get(pn)
    if new is None:
        diffs.append((pn, "row disappeared"))
    elif new != old:
        diffs.append((pn, "row content changed"))
print(f"pre-existing rows byte-identical (all {len(before)}): {not diffs}  {diffs[:5]}")

print("\n--- the new rows as written ---")
for pn in sorted(pns):
    r = after_by[pn]
    print(f"{pn:12} | {r[bi['description']][:30]:30} | {r[bi['aim_l1']]} > {r[bi['aim_l2']]} > {r[bi['aim_l3']]}"
          f" | src={r[bi['aim_source']]} | l1f={r[bi['aim_l1_fixed']]} | fig={r[bi['fig_key']] or '(blank)'}"
          f" fig_no={r[bi['fig_no']]} key_no={r[bi['key_no']]}")

stamp_ok = all(after_by[p][bi["aim_source"]] == STAMP for p in pns)
levels_ok = all(after_by[p][bi["aim_l1"]] and after_by[p][bi["aim_l2"]] and after_by[p][bi["aim_l3"]]
                for p in pns)
print(f"\nevery new row carries aim_source = {STAMP}: {stamp_ok}")
print(f"every new row carries all three AIM levels: {levels_ok}")

print("\n--- the 92 and the 164 untouched? ---")
bk = {p: before_by.get(p) for p in blocked}
af = {p: after_by.get(p) for p in blocked}
print(f"of the 92 blocked, on this master: {sum(1 for v in bk.values() if v)}")
print(f"none of the 92 changed: {all(bk[p] == af[p] for p in blocked)}")
print(f"none of the 92 carries my stamp: "
      f"{not any(after_by[p] and after_by[p][bi['aim_source']] and STAMP in after_by[p][bi['aim_source']] for p in blocked)}")
fr_b = {p: before_by.get(p) for p in free}
fr_a = {p: after_by.get(p) for p in free}
print(f"none of the 164 changed: {all(fr_b[p] == fr_a[p] for p in free)}")
print(f"none of the 164 carries my stamp: "
      f"{not any(after_by[p] and after_by[p][bi['aim_source']] and STAMP in after_by[p][bi['aim_source']] for p in free)}")

print("\n" + "=" * 100)
print("B. does the new CSV carry the new labels?")
print("=" * 100)
with CSV24.open(encoding="utf-8-sig", newline="") as fh:
    rd = csv.DictReader(fh)
    ci = rd.fieldnames
    csv_by = {}
    n = 0
    for r in rd:
        n += 1
        if r["part_number"] in set(pns):
            csv_by[r["part_number"]] = r
print(f"csv rows: {n}  cols: {len(ci)}")
print(f"of the 44 found in the new csv: {len(csv_by)}")
bad = []
for pn in pns:
    r = csv_by.get(pn)
    m = after_by[pn]
    if not r:
        bad.append((pn, "absent"))
        continue
    if (r["aim_level_1"], r["aim_level_2"], r["aim_level_3"]) != (
            m[bi["aim_l1"]], m[bi["aim_l2"]], m[bi["aim_l3"]]):
        bad.append((pn, "level mismatch", (r["aim_level_1"], r["aim_level_2"], r["aim_level_3"])))
    if r["aim_source"] != STAMP:
        bad.append((pn, "stamp mismatch", r["aim_source"]))
print(f"all 44 carry the new labels and stamp in the csv: {not bad}  {bad[:5]}")
print("\nsample from the new csv:")
for pn in ("8981422000", "7552319201", "8982703783", "8983989340", "5872210960"):
    r = csv_by[pn]
    print(f"  {pn} | {r['description']} | {r['aim_level_1']} > {r['aim_level_2']} > {r['aim_level_3']}"
          f" | fig {r['figure_key']} | label {r['figure_key_label']} | src {r['aim_source']}")

print("\n" + "=" * 100)
print("C. files")
print("=" * 100)
for p in (MASTER, BACKUP, CSV24, XLSX24):
    print(f"  {p}  {p.stat().st_size:>12,} bytes")
print("\nshas:")
for p in (BACKUP, MASTER, CSV24, XLSX24):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f"  {h}  {p.name}")

print("\n--- earlier dated pairs still present, untouched ---")
for f in sorted(D.glob("AIM_Master_PN_Categories_Figkey_2026092*")):
    print(f"  {f.name:<60} {f.stat().st_size:>12,} bytes")
