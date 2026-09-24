# -*- coding: utf-8 -*-
"""Verify the cab class end to end. Read only."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
B = D / "_backup_20260924_pair_before_cab_class"
MASTER = D / "aim_master_v2.csv"
PAIR_CSV = D / "AIM_Master_PN_Categories_Figkey_20260924.csv"
PAIR_XLSX = D / "AIM_Master_PN_Categories_Figkey_20260924.xlsx"
CMD24 = D / "OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd"
CMD21 = D / "OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"

STAMP = "cab_class_20260924"
L1, L2, L3 = "Accident & Body", "Complete Assembly", "Cab Assembly"
SET_COLS = ["aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed",
            "has_aim", "aim_source", "aim_changed"]
PLACED = ["7551847570", "7552044930", "7552612100", "7552625790", "7552824860",
          "7553142130", "7551847580", "7552060250", "7552349740", "7552427800",
          "7552641820", "7552650510", "7552825890", "8974877720", "8980115942",
          "8980115951", "8980425220", "8980554611", "8980554621"]
ADDED = "7553266960"

backups = sorted(D.glob("aim_master_v2.csv.bak_pre_cab_class_20260924_*"))
if len(backups) != 1:
    raise SystemExit(f"expected exactly one cab-class backup, found {len(backups)}")
BAK = backups[0]

results: list[tuple[str, bool, str]] = []


def rec(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------- (a) row count ----------
with MASTER.open(encoding="utf-8", newline="") as fh:
    after = list(csv.reader(fh))
with BAK.open(encoding="utf-8", newline="") as fh:
    before = list(csv.reader(fh))
hdr_after, data_after = after[0], after[1:]
hdr_before, data_before = before[0], before[1:]
idx = {c: i for i, c in enumerate(hdr_after)}
rec("a1_header_identical", hdr_after == hdr_before, f"{len(hdr_after)} cols")
rec("a2_row_count_plus_1", len(data_after) == len(data_before) + 1,
    f"{len(data_before)} -> {len(data_after)}")
rec("a3_no_duplicate_pn",
    len({r[0] for r in data_after}) == len(data_after))
rec("a4_sorted", [r[0] for r in data_after] == sorted(r[0] for r in data_after))

# ---------- (b) cell by cell ----------
by_before = {r[0]: r for r in data_before}
by_after = {r[0]: r for r in data_after}
placed_set = set(PLACED)
unexpected: list[str] = []
changed_by_col: dict[str, int] = {}
changed_rows: set[str] = set()
for pn, old in by_before.items():
    new = by_after.get(pn)
    if new is None:
        unexpected.append(f"{pn}: row disappeared")
        continue
    for i, (a, b) in enumerate(zip(old, new)):
        if a == b:
            continue
        changed_rows.add(pn)
        if pn in placed_set and hdr_after[i] in SET_COLS:
            changed_by_col[hdr_after[i]] = changed_by_col.get(hdr_after[i], 0) + 1
        else:
            unexpected.append(f"{pn}:{hdr_after[i]}: {a!r}->{b!r}")
rec("b1_only_intended_cells_changed",
    not unexpected and changed_rows == placed_set,
    f"{len(changed_rows)} rows, {sum(changed_by_col.values())} cells, "
    f"cols={changed_by_col}; unexpected={len(unexpected)}")
if unexpected:
    for u in unexpected[:10]:
        print("   ", u)

# ---------- (c) the class at all three levels ----------
bad3 = [p for p in PLACED
        if (by_after[p][idx["aim_l1"]], by_after[p][idx["aim_l2"]],
            by_after[p][idx["aim_l3"]]) != (L1, L2, L3)]
badfix = [p for p in PLACED
          if (by_after[p][idx["aim_l1_fixed"]], by_after[p][idx["aim_l2_fixed"]])
          != (L1, L2)]
badstamp = [p for p in PLACED if by_after[p][idx["aim_source"]] != STAMP]
rec("c1_all_placed_read_new_class", not bad3, f"{len(PLACED) - len(bad3)}/{len(PLACED)}")
rec("c2_all_placed_fixed_cols", not badfix, "")
rec("c3_all_placed_stamped", not badstamp, "")

# ---------- (d) the added part ----------
r = by_after.get(ADDED)
ok_d = bool(r) and r[idx["description"]] == "CAB ASM; SERVICE,W/ELECT" and \
    (r[idx["aim_l1"]], r[idx["aim_l2"]], r[idx["aim_l3"]]) == (L1, L2, L3) and \
    r[idx["aim_source"]] == STAMP and r[idx["has_aim"]] == "1"
rec("d1_added_row_exists_with_class", ok_d,
    f"{r[idx['description']]!r} {r[idx['aim_l1']]}|{r[idx['aim_l2']]}|{r[idx['aim_l3']]}"
    if r else "missing")

# ---------- (e) rebuilt pair shows it ----------
pair = pd.read_csv(PAIR_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig")
pair["k"] = pair.part_number.str.strip()
pk = pair.set_index("k")
rec("e1_pair_row_count", len(pair) == len(data_after),
    f"{len(pair)} rows")
sub = pk.reindex(PLACED + [ADDED])
ok_e = ((sub.aim_level_1 == L1) & (sub.aim_level_2 == L2) &
        (sub.aim_level_3 == L3)).all()
rec("e2_pair_csv_shows_class_on_all_20", bool(ok_e),
    f"{(sub.aim_level_3 == L3).sum()}/20 read {L3}")
xl = pd.read_excel(PAIR_XLSX, dtype=str, sheet_name="AIM_PN")
xl["k"] = xl.part_number.str.strip()
xs = xl.set_index("k").reindex(PLACED + [ADDED])
ok_x = ((xs.aim_level_1 == L1) & (xs.aim_level_2 == L2) &
        (xs.aim_level_3 == L3)).all()
rec("e3_pair_xlsx_shows_class_on_all_20", bool(ok_x),
    f"{(xs.aim_level_3 == L3).sum()}/20 read {L3}")

# ---------- (f) the 2026-09-21 pair unchanged ----------
ref21 = {
    "AIM_Master_PN_Categories_Figkey_20260921.csv":
        "bed9c4a266aa2851", "AIM_Master_PN_Categories_Figkey_20260921.xlsx":
        "8376812d5702a89f", "OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd":
        "c182b0e980d62fc5"}
bad21 = [n for n, h in ref21.items() if sha(D / n)[:16] != h]
rec("f1_20260921_pair_unchanged", not bad21, f"hashes match: {not bad21}")

# ---------- launcher ----------
cb = CMD24.read_bytes()
rec("g1_launcher_points_at_20260924_xlsx",
    b"20260924.xlsx" in cb and b"20260921" not in cb, f"{len(cb)} bytes")
rec("g2_launcher_is_crlf", cb.count(b"\r\n") == 2 and cb.count(b"\n") == 2, "")

# ---------- (g) open count on the IE40 price list ----------
q = pd.read_csv(EQ, dtype=str, keep_default_na=False)
pns = q.pn.str.strip().str.upper().unique()
cur = pk.reindex(pns)
v = cur.aim_level_1.fillna("")
blank = int((v == "").sum())
unk = int((v == "Unknown").sum())
rev = int((v == "Unknown Review").sum())
print()
print(f"open count on the IE40 price list ({len(pns)} part numbers):")
print(f"  blank {blank} + Unknown {unk} + Unknown Review {rev} = {blank + unk + rev}")
print(f"  before this change: 34 + 31 + 14 = 79")

# ---------- extra: what the class holds now ----------
cls = pair[(pair.aim_level_1 == L1) & (pair.aim_level_2 == L2) &
           (pair.aim_level_3 == L3)]
rec("h1_class_holds_20_rows", len(cls) == 20, f"{len(cls)} rows")
print()
print("the class, as it now stands:")
print(cls[["part_number", "description", "aim_level_3", "aim_source"]].to_string(index=False))

# ---------- gold: the master did not move during the write ----------
print()
print(f"master now: {MASTER.stat().st_size:,} bytes  sha256 {sha(MASTER)}")
print(f"backup    : {BAK.name}  {BAK.stat().st_size:,} bytes  sha256 {sha(BAK)}")
print()
failed = [n for n, ok, _ in results if not ok]
print(f"{len(results) - len(failed)}/{len(results)} checks passed")
if failed:
    print("FAILED:", failed)
json.dump(
    {"checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in results],
     "open_count": {"parts": int(len(pns)), "blank": blank, "unknown": unk,
                    "unknown_review": rev, "open": blank + unk + rev,
                    "before": 79},
     "master_sha256": sha(MASTER), "backup": BAK.name},
    open(ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" /
         "cab_class_verify.json", "w", encoding="utf-8"), indent=2)
sys.exit(1 if failed else 0)
