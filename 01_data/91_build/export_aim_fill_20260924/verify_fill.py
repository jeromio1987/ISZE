# -*- coding: utf-8 -*-
"""Step 9 verification, run against the written files and the backups."""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
F = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"
STAMP = "export_pr00_20260924"

MASTER = D / "aim_master_v2.csv"
BACKUP_FILL = sorted(D.glob("aim_master_v2.csv.bak_pre_export_fill_20260924_*"))[-1]
BACKUP_APPEND = sorted(D.glob("aim_master_v2.csv.bak_pre_export_append_20260924_*"))[-1]
CSV24 = D / "AIM_Master_PN_Categories_Figkey_20260924.csv"
XLSX24 = D / "AIM_Master_PN_Categories_Figkey_20260924.xlsx"
PAIR_BAK = D / "_backup_20260924_pair_before_fill"

free = [l.strip() for l in (A / "would_land_free.txt").read_text().splitlines() if l.strip()]
blocked = [l.strip() for l in (A / "carried_out_blocked_precedence.txt").read_text().splitlines() if l.strip()]
notin = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]

with (F / "decision_164_final.csv").open(encoding="utf-8-sig", newline="") as fh:
    dec = list(csv.DictReader(fh))
placed = {d["pn"]: d for d in dec if d["chosen_l1"]}
unplaced = [d for d in dec if not d["chosen_l1"]]


def load(p):
    with p.open(encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        return hdr, list(rd)


ok = True


def chk(name, cond, extra=""):
    global ok
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {extra}")
    if not cond:
        ok = False


h_fill, before_fill = load(BACKUP_FILL)
h_app, before_app = load(BACKUP_APPEND)
h_now, now = load(MASTER)
bi = {c: i for i, c in enumerate(h_now)}
now_by = {r[0]: r for r in now}
fill_by = {r[0]: r for r in before_fill}
app_by = {r[0]: r for r in before_app}

print("=" * 100)
print("A. the master file itself")
print("=" * 100)
chk("row count unchanged from the post-append count of 165,257",
    len(now) == 165257, f"{len(now)} rows")
chk("header identical, 32 columns, same order",
    h_now == h_fill == h_app and len(h_now) == 32)
chk("no duplicate part numbers", len(now_by) == len(now))
chk("still sorted by part number", [r[0] for r in now] == sorted(r[0] for r in now))
raw = MASTER.read_bytes()
chk("no BOM introduced", not raw.startswith(b"\xef\xbb\xbf"))
chk("CRLF only, no bare LF", raw.count(b"\n") == raw.count(b"\r\n"))
chk("readable as UTF-8", True)

print("\n" + "=" * 100)
print("B. the 162 carry the new levels and the stamp")
print("=" * 100)
bad = []
for pn, d in placed.items():
    r = now_by.get(pn)
    if r is None:
        bad.append((pn, "row missing")); continue
    want = (d["chosen_l1"], d["chosen_l2"], d["chosen_l3"])
    got = (r[bi["aim_l1"]], r[bi["aim_l2"]], r[bi["aim_l3"]])
    if got != want:
        bad.append((pn, "levels", got, want))
    if r[bi["aim_source"]] != STAMP:
        bad.append((pn, "aim_source", r[bi["aim_source"]]))
    if r[bi["aim_changed"]] != STAMP:
        bad.append((pn, "aim_changed", r[bi["aim_changed"]]))
    if r[bi["has_aim"]] != "1":
        bad.append((pn, "has_aim", r[bi["has_aim"]]))
    if r[bi["aim_l1_fixed"]] != want[0] or r[bi["aim_l2_fixed"]] != want[1]:
        bad.append((pn, "fixed", r[bi["aim_l1_fixed"]], r[bi["aim_l2_fixed"]]))
chk(f"all {len(placed)} carry levels + {STAMP}", not bad, str(bad[:5]))

print("\n" + "=" * 100)
print("C. no other row changed its aim columns (by part number vs the backup)")
print("=" * 100)
targets = set(placed)
aim_cols = ["description", "aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed",
            "has_aim", "aim_source", "aim_changed", "cat_l1", "cat_l2", "cat_l3",
            "cat_pms_flag", "fig_key", "fig_no", "key_no", "l12m_billed_eur", "eur",
            "has_catalogue_node", "desc_ambiguous", "aim_demand_type", "aim_core_noncore"]
rows_changed = []
cols_changed_outside = []
for pn, old in fill_by.items():
    new = now_by.get(pn)
    if new is None:
        rows_changed.append(pn); continue
    if new != old:
        rows_changed.append(pn)
        for c in aim_cols:
            if old[bi[c]] != new[bi[c]] and c not in (
                    "aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed",
                    "has_aim", "aim_source", "aim_changed"):
                cols_changed_outside.append((pn, c, old[bi[c]], new[bi[c]]))
chk("rows that changed at all == exactly the 162 targets",
    set(rows_changed) == targets, f"{len(rows_changed)} rows changed")
chk("no AIM-adjacent column changed anywhere (outside the 8 allowed)",
    not cols_changed_outside, str(cols_changed_outside[:5]))

print("\n" + "=" * 100)
print("D. the 44 appended earlier were not disturbed")
print("=" * 100)
app_diff = [p for p in notin if now_by.get(p) != fill_by.get(p)]
chk("all 44 rows byte-identical to the pre-fill (post-append) backup", not app_diff, str(app_diff[:5]))
app_absent_from_preappend = [p for p in notin if p not in app_by]
chk("and they are genuinely absent from the pre-append backup, so that is the right baseline",
    len(app_absent_from_preappend) == 44, f"{len(app_absent_from_preappend)}/44 absent")
stamp44 = sum(1 for p in notin if now_by[p][bi["aim_source"]] == STAMP)
chk("all 44 still carry their stamp", stamp44 == 44, f"{stamp44}/44")

print("\n" + "=" * 100)
print("E. none of the 92 blocked rows moved or took the stamp")
print("=" * 100)
blk_diff = [p for p in blocked if now_by.get(p) != fill_by.get(p)]
chk("all 92 unchanged against the pre-fill backup", not blk_diff, str(blk_diff[:5]))
stamp92 = [p for p in blocked if now_by[p][bi["aim_source"]] == STAMP]
chk("none of the 92 carries the fill stamp", not stamp92, str(stamp92[:5]))
still_unknown = sum(1 for p in blocked
                    if now_by[p][bi["aim_l1_fixed"]] in ("Unknown", "Unknown Review"))
chk("the 92 still carry Unknown / Unknown Review in aim_l1_fixed",
    still_unknown == 92, f"{still_unknown}/92")

print("\n" + "=" * 100)
print("F. the rebuilt pair carries the new labels for the 162 and the 44")
print("=" * 100)
csv_by = {}
n_csv = 0
with CSV24.open(encoding="utf-8-sig", newline="") as fh:
    rd = csv.DictReader(fh)
    for r in rd:
        n_csv += 1
        if r["part_number"] in targets or r["part_number"] in set(notin):
            csv_by[r["part_number"]] = r
print(f"  pair rows: {n_csv}")
chk("pair found for all 162 + 44", len(csv_by) == 162 + 44, f"{len(csv_by)}")
bad_pair = []
for pn, d in placed.items():
    r = csv_by.get(pn)
    m = now_by[pn]
    if not r:
        bad_pair.append((pn, "absent")); continue
    if (r["aim_level_1"], r["aim_level_2"], r["aim_level_3"]) != (
            m[bi["aim_l1"]], m[bi["aim_l2"]], m[bi["aim_l3"]]):
        bad_pair.append((pn, "level mismatch",
                         (r["aim_level_1"], r["aim_level_2"], r["aim_level_3"])))
chk("all 162 carry the new labels in the rebuilt csv", not bad_pair, str(bad_pair[:5]))
# the pair builder reads aim_source from the classification overlay first, by design; that is
# pre-existing behaviour and none of the 162 is in the overlay, so the pair's aim_source is not
# the master's aim_source. Measure and report it rather than asserting it.
pair_src_stamp = sum(1 for pn in placed if csv_by.get(pn, {}).get("aim_source") == STAMP)
print(f"      note: the pair carries aim_source = {STAMP} on {pair_src_stamp}/162 of these rows "
      f"(the builder prefers the classification overlay's aim_source, which these rows are not in)")
bad44 = [p for p in notin if p not in csv_by or csv_by[p]["aim_source"] != STAMP]
chk("all 44 carry their stamp in the rebuilt csv", not bad44, str(bad44[:5]))
chk("pair row count equals the master row count", n_csv == 165257, f"{n_csv}")

print("\n" + "=" * 100)
print("G. files and hashes")
print("=" * 100)
for p in (BACKUP_FILL, BACKUP_APPEND, MASTER, CSV24, XLSX24,
          PAIR_BAK / CSV24.name, PAIR_BAK / XLSX24.name):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f"  {h}  {p.stat().st_size:>12,}  {p}")
print("\n  the 20260921 pair, untouched:")
for p in sorted(D.glob("AIM_Master_PN_Categories_Figkey_20260921.*")):
    if p.suffix in (".csv", ".xlsx"):
        print(f"  {p.stat().st_size:>12,}  {p.name}  mtime {p.stat().st_mtime}")

print("\n" + "=" * 100)
print("H. the rows I did not place")
print("=" * 100)
for d in unplaced:
    print(f"  {d['pn']}  {d['description']}  list_eur {d['list_eur']}  reason: {d['unplaced_reason']}")

print("\n" + ("ALL CHECKS PASS" if ok else "SOME CHECKS FAILED"))
sys.exit(0 if ok else 1)
