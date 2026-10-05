# -*- coding: utf-8 -*-
"""Verification of the orphan append. Runs against the written files and the backup,
by part number, not by row position."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924"

MASTER = DER / "aim_master_v2.csv"
BACKUP = DER / "aim_master_v2.csv.bak_pre_orphan_append_20260924_170151"
PAIR_CSV = DER / "AIM_Master_PN_Categories_Figkey_20260924.csv"
PAIR_XLSX = DER / "AIM_Master_PN_Categories_Figkey_20260924.xlsx"
PAIR_BAK = DER / "_backup_20260924_pair_before_orphans"
CMD = DER / "OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_csv_rows(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as fh:
        rdr = csv.reader(fh)
        rows = list(rdr)
    return rows[0], rows[1:]


def s(v):
    return "" if v is None else str(v).strip()


results = {}

with (OUT / "decision_orphans.csv").open(encoding="utf-8-sig", newline="") as fh:
    dec = list(csv.DictReader(fh))
placed = [d for d in dec if s(d["place"]).lower() == "true"]
unplaced = [d for d in dec if s(d["place"]).lower() != "true"]
placed_pns = {s(d["pn"]) for d in placed}
print(f"decisions {len(dec)} | placed {len(placed)} | unplaced {len(unplaced)}")

hdr_b, data_b = load_csv_rows(BACKUP)
hdr_a, data_a = load_csv_rows(MASTER)
idx = {c: i for i, c in enumerate(hdr_a)}

results["header_identical"] = hdr_b == hdr_a
results["columns_identical"] = len(hdr_a) == len(hdr_b) == 32
results["row_count_before"] = len(data_b)
results["row_count_after"] = len(data_a)
results["row_count_plus_placed"] = len(data_a) == len(data_b) + len(placed)

by_b = {r[0]: r for r in data_b}
by_a = {r[0]: r for r in data_a}
missing = [p for p in by_b if p not in by_a]
changed = [p for p in by_b if p in by_a and by_a[p] != by_b[p]]
results["no_preexisting_row_lost"] = not missing
results["every_preexisting_row_identical"] = not changed
results["preexisting_rows_checked"] = len(by_b)

# new rows carry a real family and the right stamp
bad_new = []
for d in placed:
    r = by_a.get(s(d["pn"]))
    if r is None:
        bad_new.append((d["pn"], "no row"))
        continue
    got = (r[idx["aim_l1"]], r[idx["aim_l2"]], r[idx["aim_l3"]])
    want = (s(d["chosen_l1"]), s(d["chosen_l2"]), s(d["chosen_l3"]))
    if got != want:
        bad_new.append((d["pn"], f"levels {got} != {want}"))
    if r[idx["aim_l1_fixed"]] != s(d["chosen_l1"]) or r[idx["aim_l2_fixed"]] != s(d["chosen_l2"]):
        bad_new.append((d["pn"], "fixed levels differ"))
    if r[idx["aim_source"]] != s(d["stamp"]):
        bad_new.append((d["pn"], f"stamp {r[idx['aim_source']]!r} != {d['stamp']!r}"))
    if r[idx["has_aim"]] != "1":
        bad_new.append((d["pn"], f"has_aim={r[idx['has_aim']]!r}"))
    if r[idx["aim_changed"]] != s(d["stamp"]):
        bad_new.append((d["pn"], "aim_changed stamp differs"))
results["new_rows_carry_levels_and_stamp"] = not bad_new

# routes and stamps
from collections import Counter
results["routes"] = Counter(s(d["route"]) for d in placed)
results["stamps"] = Counter(s(d["stamp"]) for d in placed)

# sorted / dupes
results["sorted_ascending"] = [r[0] for r in data_a] == sorted(r[0] for r in data_a)
results["no_duplicate_part_numbers"] = len({r[0] for r in data_a}) == len(data_a)

# the guarded groups on this price list
with (EQ / "queue.csv").open(encoding="utf-8-sig", newline="") as fh:
    q_pns = {s(r["pn"]) for r in csv.DictReader(fh)}


def fam(v):
    v = s(v)
    if v and not v.lower().startswith("unknown"):
        return "real"
    if v.lower().startswith("unknown"):
        return "marker"
    return "blank"


marker_b = {p for p in q_pns if p in by_b and fam(by_b[p][idx["aim_l1"]]) == "marker"}
blank_b = {p for p in q_pns if p in by_b and fam(by_b[p][idx["aim_l1"]]) == "blank"}
marker_touched = [p for p in marker_b if by_a.get(p) != by_b[p]]
blank_touched = [p for p in blank_b if by_a.get(p) != by_b[p]]
results["marker_rows_on_queue"] = len(marker_b)
results["blank_rows_on_queue"] = len(blank_b)
results["marker_rows_untouched"] = not marker_touched
results["blank_rows_untouched"] = not blank_touched
results["no_new_stamp_on_marker_or_blank"] = not any(
    s(by_a[p][idx["aim_source"]]) in {s(d["stamp"]) for d in placed}
    for p in (marker_b | blank_b))


# open count on the price list, before and after, on the main table
def open_count(by):
    on = [p for p in q_pns if p in by]
    m = sum(1 for p in on if fam(by[p][idx["aim_l1"]]) == "marker")
    b = sum(1 for p in on if fam(by[p][idx["aim_l1"]]) == "blank")
    off = len(q_pns) - len(on)
    return {"fact": m, "no_wording": b, "no_row": off, "open": m + b + off,
            "on_master": len(on)}


results["open_before"] = open_count(by_b)
results["open_after"] = open_count(by_a)

# the rebuilt pair
pair_hdr, pair_rows = load_csv_rows(PAIR_CSV)
pair_pns = {r[0] for r in pair_rows}
pidx = {c: i for i, c in enumerate(pair_hdr)}
pair_ok = True
pair_detail = []
for d in placed:
    p = s(d["pn"])
    row = next((r for r in pair_rows if r[0] == p), None)
    if row is None:
        pair_ok = False
        pair_detail.append((p, "missing from CSV"))
        continue
    got = (row[pidx["aim_level_1"]], row[pidx["aim_level_2"]], row[pidx["aim_level_3"]])
    want = (s(d["chosen_l1"]), s(d["chosen_l2"]), s(d["chosen_l3"]))
    if got != want:
        pair_ok = False
        pair_detail.append((p, f"{got} != {want}"))
results["pair_csv_has_all_placed_with_families"] = pair_ok
results["pair_csv_detail"] = pair_detail
results["pair_csv_rows"] = len(pair_rows)

xl = pd.read_excel(PAIR_XLSX, sheet_name="AIM_PN", dtype=str)
xl["k"] = xl["part_number"].fillna("").str.strip()
xlset = set(xl["k"])
xl_missing = sorted(p for p in placed_pns if p not in xlset)
xl_ok = True
xl_detail = []
for d in placed:
    p = s(d["pn"])
    row = xl[xl["k"] == p]
    if row.empty:
        xl_ok = False
        xl_detail.append((p, "missing"))
        continue
    got = (s(row.iloc[0]["aim_level_1"]), s(row.iloc[0]["aim_level_2"]), s(row.iloc[0]["aim_level_3"]))
    if got != (s(d["chosen_l1"]), s(d["chosen_l2"]), s(d["chosen_l3"])):
        xl_ok = False
        xl_detail.append((p, str(got)))
results["pair_xlsx_has_all_placed_with_families"] = xl_ok
results["pair_xlsx_rows"] = len(xl)

# launcher
raw = CMD.read_bytes()
results["launcher_bytes"] = len(raw)
results["launcher_crlf"] = raw.count(b"\r\n") == 2 and b"\n" not in raw.replace(b"\r\n", b"")
results["launcher_points_at_20260924_xlsx"] = b"AIM_Master_PN_Categories_Figkey_20260924.xlsx" in raw
results["launcher_text"] = raw.decode("ascii", "replace")

# encoding / line endings of the master
mb = MASTER.read_bytes()
results["master_no_bom"] = not mb.startswith(b"\xef\xbb\xbf")
results["master_crlf_only"] = b"\n" not in mb.replace(b"\r\n", b"")
results["master_bytes"] = len(mb)
results["master_sha256"] = sha(MASTER)
results["backup_bytes"] = BACKUP.stat().st_size
results["backup_sha256"] = sha(BACKUP)
results["pair_csv_bytes"] = PAIR_CSV.stat().st_size
results["pair_csv_sha256"] = sha(PAIR_CSV)
results["pair_xlsx_bytes"] = PAIR_XLSX.stat().st_size
results["pair_xlsx_sha256"] = sha(PAIR_XLSX)
results["pair_backup_dir"] = str(PAIR_BAK)
results["pair_backup_files"] = sorted(p.name for p in PAIR_BAK.iterdir())

# unplaced detail
results["unplaced"] = [{"pn": s(d["pn"]), "description": s(d["description"]),
                        "fig_key": s(d["fig_key"]),
                        "classified_source": s(d["classified_source"]),
                        "note": s(d["classified_note"])} for d in unplaced]

print()
for k, v in results.items():
    if k in {"pair_csv_detail", "pair_xlsx_detail", "unplaced"}:
        continue
    print(f"{k:48} {v}")

(OUT / "verify_orphan_append.json").write_text(
    json.dumps(results, indent=2, default=str), encoding="utf-8")

fails = [k for k in ("header_identical", "columns_identical", "row_count_plus_placed",
                     "no_preexisting_row_lost", "every_preexisting_row_identical",
                     "new_rows_carry_levels_and_stamp", "sorted_ascending",
                     "no_duplicate_part_numbers", "marker_rows_untouched",
                     "blank_rows_untouched", "no_new_stamp_on_marker_or_blank",
                     "pair_csv_has_all_placed_with_families",
                     "pair_xlsx_has_all_placed_with_families",
                     "launcher_crlf", "launcher_points_at_20260924_xlsx",
                     "master_no_bom", "master_crlf_only") if not results[k]]
print()
print("VERIFY:", "ALL CHECKS PASS" if not fails else f"FAILED -> {fails}")
if bad_new:
    print("bad new rows:", bad_new[:10])
