#!/usr/bin/env python3
"""Cut AIM classification release 2026-10-15-revert from approved 2026-10-15.

Puts the 178 parts in revert_list_wrong_moves_2026-10-15.csv back on their
11 Oct labels. Does not touch any other part. Does not strip cells.

    python 01_data/91_build/build_aim_classification_release_revert_20261015.py
    python 01_data/91_build/build_aim_classification_release_revert_20261015.py --approve
    python 01_data/91_build/build_aim_classification_release_revert_20261015.py --sync
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"

RELEASE_ID = "2026-10-15-revert"
BASE_ID = "2026-10-15"
OCT11_ID = "2026-10-11"
RUN_DATE = "2026-10-15"

BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
OCT11 = REL / f"aim_pn_classification_release_{OCT11_ID}.csv"
OUT = REL / f"aim_pn_classification_release_{RELEASE_ID}.csv"
OUT_CHANGES = REL / f"aim_pn_classification_release_{RELEASE_ID}.changes.csv"
OUT_META = REL / f"aim_pn_classification_release_{RELEASE_ID}.meta.json"
REGISTER = REL / "RELEASES.json"
REVERT = REL / "revert_list_wrong_moves_2026-10-15.csv"
BASE_META = REL / f"aim_pn_classification_release_{BASE_ID}.meta.json"
PR00_REF = REL / "pr00_classification_reference_20260920.csv"
MASTER = DER / "aim_master_v2.csv"
LIVE = DER / "aim_pn_classification_20260920.csv"
MASTER_11 = DER / "aim_master_v2.csv.bak_pre_padkit_wronglabel_20261015_133755"
LIVE_11 = DER / "aim_pn_classification_20260920.csv.bak_pre_padkit_wronglabel_20261015_133755"

AIM4 = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed", "aim_source"]
REVERT_COLS = {
    "aim_l1_fixed": "revert_to_aim_l1",
    "aim_l2_fixed": "revert_to_aim_l2",
    "aim_l3_fixed": "revert_to_aim_l3",
    "aim_source": "revert_to_aim_source",
}
MASTER_COLS = [
    "aim_l1_fixed",
    "aim_l2_fixed",
    "aim_l3",
    "has_aim",
    "aim_changed",
    "aim_source",
]
LIVE_COLS = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed", "aim_source"]

JEROME_GO = (
    "Yes, write the fix brief: revert the 26 wrong groups to their 11 Oct labels, "
    "keep the other 76, refresh the Power BI file and rewrite the Bart draft."
)
SUPERSEDE_NOTE = (
    "26 wrong move groups, 178 parts, put back on their 11 Oct labels; "
    "other moves and pad kits kept"
)
EXPECT_BASE_SHA = "cd7ac827199751ddb55bc3b7a864724184877ab652ed86824016b8fc36b02571"
EXPECT_REVERT_SHA = "18d487d10d84aab1ecb94bb59675ef04488f407ed99fba24eaac5a1d584966ec"
EXPECT_PR00_SHA = "98e64b5bdaef73819cf954ce96241f1a9b49d8fbd998d02700ae8494028bea34"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(p: Path, tag: str) -> Path:
    b = p.with_name(p.name + f".bak_{tag}_{STAMP}")
    shutil.copy2(p, b)
    return b


def read_csv(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def catalogue_integrity(df: pd.DataFrame) -> tuple[dict, list[str]]:
    """Same comparison as build_aim_classification_release_20261015.py.

    Strips only the copies used for the PR00 comparison. Does not change df.
    """
    text = PR00_REF.read_text(encoding="utf-8")
    pm = {}
    for r in csv.DictReader(io.StringIO(text)):
        k = (r.get("pn_norm") or "").strip()
        k = k.zfill(10) if k.isdigit() else k
        if k:
            pm[k] = (
                (r.get("family") or "").strip(),
                (r.get("group") or "").strip(),
                (r.get("level3_type") or "").strip(),
            )
    chk = ok = 0
    miss = []
    for pn, a, b_, c in zip(df["part_number"], df["catalog_l1"], df["catalog_l2"], df["catalog_l3"]):
        k = str(pn).strip()
        k = k.zfill(10) if k.isdigit() else k
        if k in pm:
            chk += 1
            if pm[k] == (a.strip(), b_.strip(), c.strip()):
                ok += 1
            else:
                miss.append(pn)
    return (
        {
            "rows_checked": chk,
            "rows_matching": ok,
            "match_pct": round(100 * ok / chk, 4) if chk else None,
        },
        miss,
    )


def load_revert() -> pd.DataFrame:
    rev = read_csv(REVERT)
    if not rev.part_number.is_unique:
        raise SystemExit("revert list part_number is not unique")
    if len(rev) != 178:
        raise SystemExit(f"revert list has {len(rev)} parts, expected 178")
    groups = rev.groupby(["description_key", "revert_to_aim_l3"]).ngroups
    if groups != 26:
        raise SystemExit(f"revert list has {groups} groups, expected 26")
    return rev


def apply_revert(base: pd.DataFrame, rev: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    rel = base.copy()
    by_pn = rev.set_index("part_number", drop=False)
    missing = [pn for pn in rev.part_number if not (rel.part_number == pn).any()]
    if missing:
        raise SystemExit(f"revert parts missing from base: {missing[:10]}")
    change_rows: list[dict] = []
    for pn in rev.part_number:
        rows = rel.index[rel.part_number == pn]
        if len(rows) != 1:
            raise SystemExit(f"part {pn} matched {len(rows)} base rows")
        i = int(rows[0])
        src = by_pn.loc[pn]
        for col, src_col in REVERT_COLS.items():
            new = src[src_col]
            old = rel.at[i, col]
            if old != new:
                change_rows.append(
                    {"part_number": pn, "column": col, "before": old, "after": new}
                )
            rel.at[i, col] = new
    return rel, change_rows


def step2_numbers(rel: pd.DataFrame, before: pd.DataFrame, rev: pd.DataFrame) -> dict:
    pns = set(rev.part_number)
    changed_cells = 0
    changed_outside = []
    for col in rel.columns:
        ne = rel[col] != before[col]
        n = int(ne.sum())
        if col in AIM4:
            bad_pn = sorted(set(rel.loc[ne, "part_number"]) - pns)
            if bad_pn:
                changed_outside.append((col, bad_pn[:5]))
            changed_cells += n
        elif n:
            changed_outside.append((col, n))
    if changed_outside:
        raise SystemExit(f"cells changed outside the 178 / four AIM columns: {changed_outside[:8]}")

    oct11 = read_csv(OCT11)
    if len(oct11) != len(rel) or set(oct11.part_number) != set(rel.part_number):
        raise SystemExit("11 Oct release is not the same part set as this cut")
    m = rel.merge(oct11[ ["part_number", *AIM4] ], on="part_number", suffixes=("", "_11"))
    if len(m) != len(rel):
        raise SystemExit("11 Oct merge changed the row count")
    differ = pd.Series(False, index=m.index)
    for col in AIM4:
        differ = differ | (m[col] != m[col + "_11"])
    reverted = m.part_number.isin(pns)
    reverted_still_differ = int((reverted & differ).sum())
    n_differ = int(differ.sum())

    desc = pd.Series("", index=rel.index)
    for col in ("description", "description_norm"):
        if col in rel.columns:
            desc = desc.where(desc.ne(""), rel[col])
            desc = desc.mask(rel[col].str.contains("PAD; TRIM", regex=False), rel[col])
    pad_trim_on_brakes = int(
        (rel.aim_l1_fixed.eq("Brakes") & desc.str.contains("PAD; TRIM", regex=False)).sum()
    )
    l3 = {
        name: int(rel.aim_l3_fixed.eq(name).sum())
        for name in (
            "Brake Pad Kit",
            "Sector Shaft",
            "Cylinder Liner",
            "Brake Pad",
            "Release Bearing",
            "Oil Pipe",
        )
    }
    return {
        "rows": int(len(rel)),
        "cells_changed": changed_cells,
        "reverted_still_differ_from_11_oct": reverted_still_differ,
        "parts_differ_from_11_oct": n_differ,
        "l3": l3,
        "pad_trim_on_brakes": pad_trim_on_brakes,
    }


def assert_step2(nums: dict) -> None:
    expect_l3 = {
        "Brake Pad Kit": 142,
        "Sector Shaft": 3,
        "Cylinder Liner": 727,
        "Brake Pad": 18,
        "Release Bearing": 149,
        "Oil Pipe": 143,
    }
    problems = []
    if nums["rows"] != 165055:
        problems.append(f"rows {nums['rows']}")
    if nums["cells_changed"] != 711:
        problems.append(f"cells_changed {nums['cells_changed']}")
    if nums["reverted_still_differ_from_11_oct"] != 0:
        problems.append(f"178 not equal to 11 Oct: {nums['reverted_still_differ_from_11_oct']}")
    if nums["parts_differ_from_11_oct"] != 872:
        problems.append(f"parts differ from 11 Oct {nums['parts_differ_from_11_oct']}")
    if nums["l3"] != expect_l3:
        problems.append(f"l3 {nums['l3']}")
    if nums["pad_trim_on_brakes"] != 0:
        problems.append(f"PAD; TRIM on Brakes {nums['pad_trim_on_brakes']}")
    if problems:
        raise SystemExit("step 2 check failed: " + "; ".join(problems))


def build_pending() -> None:
    base_sha = sha256(BASE)
    revert_sha = sha256(REVERT)
    if base_sha != EXPECT_BASE_SHA:
        raise SystemExit(f"base sha mismatch {base_sha}")
    if revert_sha != EXPECT_REVERT_SHA:
        raise SystemExit(f"revert list sha mismatch {revert_sha}")
    if sha256(PR00_REF) != EXPECT_PR00_SHA:
        raise SystemExit("pr00 reference sha mismatch")

    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    if any(c.get("release_id") == RELEASE_ID for c in reg["candidates"]):
        raise SystemExit(f"{RELEASE_ID} already in RELEASES.json — stop")
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    if base_entry.get("status") != "APPROVED":
        raise SystemExit(f"base status is {base_entry.get('status')}, expected APPROVED")
    if base_entry.get("sha256") != base_sha:
        raise SystemExit("RELEASES.json base sha does not match the base file")

    before = read_csv(BASE)
    rev = load_revert()
    rel, change_rows = apply_revert(before, rev)
    if list(rel.columns) != list(before.columns):
        raise SystemExit("column order changed")
    nums = step2_numbers(rel, before, rev)
    assert_step2(nums)

    rel.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n")
    disk = read_csv(OUT)
    if list(disk.columns) != list(before.columns) or len(disk) != len(before):
        raise SystemExit("written release does not match base shape")
    if not disk["part_number"].equals(before["part_number"]):
        raise SystemExit("written release row order changed")
    disk_nums = step2_numbers(disk, before, rev)
    assert_step2(disk_nums)

    changes = pd.DataFrame(change_rows, columns=["part_number", "column", "before", "after"])
    if len(changes) != 711:
        raise SystemExit(f"changes.csv has {len(changes)} rows, expected 711")
    changes.to_csv(OUT_CHANGES, index=False, encoding="utf-8", lineterminator="\n")
    out_sha = sha256(OUT)

    ref_int, ref_miss = catalogue_integrity(disk)
    base_int, base_miss = catalogue_integrity(before)
    if set(ref_miss) != set(base_miss):
        raise SystemExit("catalogue miss set changed; catalogue columns were touched")
    base_meta = json.loads(BASE_META.read_text(encoding="utf-8"))
    base_cat = base_meta["catalogue_verification_vs_pr00"]
    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_aim_classification_release_revert_20261015.py",
        "release_id": RELEASE_ID,
        "status": "PENDING_APPROVAL",
        "base_release": BASE_ID,
        "base_sha256": base_sha,
        "sha256": out_sha,
        "rows": int(len(disk)),
        "jerome_go": JEROME_GO,
        "revert_list": "01_data/00_derived/_releases/revert_list_wrong_moves_2026-10-15.csv",
        "revert_list_sha256": revert_sha,
        "counts": {"parts": 178, "groups": 26},
        "change_log": OUT_CHANGES.name,
        "change_log_rows": int(len(changes)),
        "aim_label_vocabulary": {"new_aim_labels": []},
        "catalogue_verification_vs_pr00": {
            **ref_int,
            "reference_file": PR00_REF.name,
            "reference_sha256": EXPECT_PR00_SHA,
            "non_matching_parts": len(ref_miss),
            "base_release_non_matching_parts": len(base_miss),
            "note": "COPY-INTEGRITY ONLY. This release did not change catalogue columns.",
            "reference_reason": base_cat.get("reference_reason"),
            "reference_source": base_cat.get("reference_source"),
        },
        "consumer_contract": base_meta["consumer_contract"],
        "purpose": base_meta["purpose"],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    others_before = [c for c in reg["candidates"] if c.get("release_id") != BASE_ID]
    bak = backup(REGISTER, "pre_revert_20261015")
    reg["candidates"].append(
        {
            "release_id": RELEASE_ID,
            "path": OUT.name,
            "sha256": out_sha,
            "status": "PENDING_APPROVAL",
            "rows": int(len(disk)),
            "rows_note": "data rows, header excluded",
            "base_release": BASE_ID,
            "source": (
                "release 2026-10-15 with 178 parts from 26 wrong move groups "
                "put back on their 11 Oct labels; other moves and pad kits kept"
            ),
            "recommendation": JEROME_GO,
            "notes": (
                f"Change log {OUT_CHANGES.name}. 711 AIM cells. "
                "No new AIM labels. counts parts 178 groups 26."
            ),
        }
    )
    others_after = [
        c for c in reg["candidates"]
        if c.get("release_id") not in (RELEASE_ID, BASE_ID)
    ]
    if others_after != others_before:
        raise SystemExit("register update would change an entry other than the new release")
    REGISTER.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "status": "PENDING_APPROVAL",
        "release_id": RELEASE_ID,
        "sha256": out_sha,
        "backup_register": str(bak),
        "check": disk_nums,
        "catalogue_match_pct": ref_int["match_pct"],
    }, indent=2))


def approve() -> None:
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    out_sha = sha256(OUT)
    meta = json.loads(OUT_META.read_text(encoding="utf-8"))
    if meta.get("sha256") != out_sha:
        raise SystemExit("meta sha256 does not match the release file")
    snapshot = json.loads(json.dumps(reg))
    found_new = found_base = False
    for c in reg["candidates"]:
        rid = c.get("release_id")
        if rid == RELEASE_ID:
            if c.get("sha256") != out_sha:
                raise SystemExit("register sha256 does not match the release file")
            c["status"] = "APPROVED"
            c["approved_by"] = "Jerome"
            c["approved_on"] = RUN_DATE
            c["approved_note"] = JEROME_GO
            found_new = True
        elif rid == BASE_ID:
            c["status"] = "SUPERSEDED"
            c["superseded_by"] = RELEASE_ID
            c["superseded_on"] = RUN_DATE
            c["superseded_note"] = SUPERSEDE_NOTE
            found_base = True
    if not found_new or not found_base:
        raise SystemExit(f"register entries missing new={found_new} base={found_base}")
    for before, after in zip(snapshot["candidates"], reg["candidates"]):
        rid = before.get("release_id")
        if rid in (RELEASE_ID, BASE_ID):
            continue
        if before != after:
            raise SystemExit(f"refusing to change register entry {rid}")
    approved = [c["release_id"] for c in reg["candidates"] if c.get("status") == "APPROVED"]
    if approved != [RELEASE_ID]:
        raise SystemExit(f"APPROVED entries are {approved}")
    backup(REGISTER, "pre_approve_revert_20261015")
    REGISTER.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    meta["status"] = "APPROVED"
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if sha256(OUT) != out_sha:
        raise SystemExit("approve rewrote the release csv")
    print(json.dumps({"ok": True, "status": "APPROVED", "release_id": RELEASE_ID, "sha256": out_sha}, indent=2))


def _copy_columns(dst: pd.DataFrame, src: pd.DataFrame, pns: set[str], cols: list[str], label: str) -> int:
    if dst.part_number.duplicated().any() or src.part_number.duplicated().any():
        raise SystemExit(f"{label} part_number is not unique")
    src_idx = src.set_index("part_number", drop=False)
    missing = sorted(pns - set(src_idx.index))
    if missing:
        raise SystemExit(f"{label} 11 Oct backup missing {missing[:5]}")
    hit = dst.part_number.isin(pns)
    if int(hit.sum()) != 178:
        raise SystemExit(f"{label} matched {int(hit.sum())} rows, expected 178")
    for col in cols:
        if col not in dst.columns or col not in src.columns:
            raise SystemExit(f"{label} missing column {col}")
        dst.loc[hit, col] = dst.loc[hit, "part_number"].map(src_idx[col])
    return int(hit.sum())


def _frame_equal(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return False
    return all(a[c].equals(b[c]) for c in a.columns)


def sync_master_overlay() -> None:
    rev = load_revert()
    pns = set(rev.part_number)
    bak_m = backup(MASTER, "pre_revert")
    bak_l = backup(LIVE, "pre_revert")

    master = read_csv(MASTER)
    live = read_csv(LIVE)
    master_before = master.copy()
    live_before = live.copy()
    master_11 = read_csv(MASTER_11)
    live_11 = read_csv(LIVE_11)
    if len(master) != 165422:
        raise SystemExit(f"master rows {len(master)}")
    if len(live) != 165019:
        raise SystemExit(f"overlay rows {len(live)}")

    _copy_columns(master, master_11, pns, MASTER_COLS, "master")
    _copy_columns(live, live_11, pns, LIVE_COLS, "overlay")

    for df, before, label in (
        (master, master_before, "master"),
        (live, live_before, "overlay"),
    ):
        other = ~df.part_number.isin(pns)
        if not _frame_equal(df.loc[other].reset_index(drop=True), before.loc[other].reset_index(drop=True)):
            raise SystemExit(f"{label}: a row outside the 178 changed")
        touched = df.part_number.isin(pns)
        src = master_11 if label == "master" else live_11
        cols = MASTER_COLS if label == "master" else LIVE_COLS
        got = df.loc[touched, ["part_number", *cols]].sort_values("part_number")
        exp = src.loc[src.part_number.isin(pns), ["part_number", *cols]].sort_values("part_number")
        if not _frame_equal(got.reset_index(drop=True), exp.reset_index(drop=True)):
            raise SystemExit(f"{label}: the 178 do not equal the 11 Oct backup")

    master.to_csv(MASTER, index=False, encoding="utf-8", lineterminator="\n")
    live.to_csv(LIVE, index=False, encoding="utf-8", lineterminator="\n")
    master_d = read_csv(MASTER)
    live_d = read_csv(LIVE)
    if len(master_d) != 165422 or len(live_d) != 165019:
        raise SystemExit("row count changed on write")
    if not _frame_equal(master_d, master) or not _frame_equal(live_d, live):
        raise SystemExit("csv round-trip changed a cell")

    rel = read_csv(OUT).drop_duplicates("part_number").set_index("part_number")
    m_idx = master_d.drop_duplicates("part_number").set_index("part_number")
    l_idx = live_d.drop_duplicates("part_number").set_index("part_number")
    bad = []
    for pn in sorted(pns):
        rt = (rel.at[pn, "aim_l1_fixed"], rel.at[pn, "aim_l2_fixed"], rel.at[pn, "aim_l3_fixed"])
        mt = (m_idx.at[pn, "aim_l1_fixed"], m_idx.at[pn, "aim_l2_fixed"], m_idx.at[pn, "aim_l3"])
        lt = (l_idx.at[pn, "aim_l1_fixed"], l_idx.at[pn, "aim_l2_fixed"], l_idx.at[pn, "aim_l3_fixed"])
        if not (rt == mt == lt):
            bad.append((pn, rt, mt, lt))
    if bad:
        raise SystemExit(f"labels disagree across release, master, overlay: {bad[:5]}")

    print(json.dumps({
        "ok": True,
        "synced_parts": 178,
        "master_rows": 165422,
        "overlay_rows": 165019,
        "backup_master": str(bak_m),
        "backup_live": str(bak_l),
    }, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--sync", action="store_true")
    args = ap.parse_args()
    if args.approve and args.sync:
        raise SystemExit("pass one of --approve or --sync")
    if args.approve:
        approve()
    elif args.sync:
        sync_master_overlay()
    else:
        build_pending()


if __name__ == "__main__":
    main()
