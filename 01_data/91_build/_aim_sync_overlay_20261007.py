#!/usr/bin/env python3
"""Sync release 2026-10-07 AIM labels into aim_pn_classification_20260920.csv.

Release + master already APPROVED/applied. This only finishes the overlay.
Never overwrites a non-blank overlay AIM label. EQ rows absent from overlay are appended.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
REL = DER / "_releases"
OVERLAY = DER / "aim_pn_classification_20260920.csv"
OUT = REL / "aim_pn_classification_release_2026-10-07.csv"
DESC = REL / "next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv"
EQ_MAP = REL / "aim_pn_classification_release_2026-10-07.eq_remap.csv"
SRC_DESC = "desc_proven_20261007"
SRC_EQ = "eq_hit_proven_20261007"
AIM_COLS = ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def add_source(cur: str, tag: str) -> str:
    cur = (cur or "").strip()
    if not cur:
        return tag
    return cur if tag in cur else f"{cur}|{tag}"


def main() -> int:
    if not OUT.is_file():
        print("STOP: release CSV missing", OUT)
        return 2
    if not OVERLAY.is_file():
        print("STOP: overlay missing", OVERLAY)
        return 2

    ts = datetime.now().strftime("%H%M%S")
    bak = DER / f"aim_pn_classification_20260920.csv.bak_pre_release_apply_20261007_{ts}"
    if bak.exists():
        print("STOP: backup already exists", bak.name)
        return 2

    raw = OVERLAY.read_bytes()
    crlf = b"\r\n" in raw[:5000]
    shutil.copy2(OVERLAY, bak)
    assert bak.read_bytes() == raw

    rel = pd.read_csv(OUT, dtype=str, keep_default_na=False)
    ov = pd.read_csv(OVERLAY, dtype=str, keep_default_na=False)
    for c in AIM_COLS + ("aim_source", "part_number"):
        if c not in ov.columns:
            print("STOP: overlay missing column", c)
            return 2

    opos = {pad(p): i for i, p in enumerate(ov["part_number"])}
    ridx = rel.set_index(rel["part_number"].map(pad), drop=False)

    desc = pd.read_csv(DESC, dtype=str, keep_default_na=False)
    filled = 0
    skipped_has_aim = 0
    missing_on_overlay = 0
    for pn in desc["part_number"].map(pad):
        i = opos.get(pn)
        if i is None:
            missing_on_overlay += 1
            continue
        r = ridx.loc[pn]
        if not r["aim_l1_fixed"]:
            continue
        if ov.at[i, "aim_l1_fixed"]:
            skipped_has_aim += 1
            continue
        ov.at[i, "aim_l1_fixed"] = r["aim_l1_fixed"]
        ov.at[i, "aim_l2_fixed"] = r["aim_l2_fixed"]
        ov.at[i, "aim_l3_fixed"] = r["aim_l3_fixed"]
        ov.at[i, "aim_source"] = add_source(ov.at[i, "aim_source"], SRC_DESC)
        filled += 1

    eq_map = pd.read_csv(EQ_MAP, dtype=str, keep_default_na=False)
    new_rows = []
    for pn in eq_map["part_number"].map(pad):
        if pn in opos:
            continue
        if pn not in ridx.index:
            continue
        r = ridx.loc[pn]
        if not r["aim_l1_fixed"]:
            continue
        row = {c: "" for c in ov.columns}
        row.update({
            "part_number": pn,
            "description_norm": r.get("description_norm", ""),
            "catalog_l1": r.get("catalog_l1", ""),
            "catalog_l2": r.get("catalog_l2", ""),
            "catalog_l3": r.get("catalog_l3", ""),
            "aim_l1_fixed": r["aim_l1_fixed"],
            "aim_l2_fixed": r["aim_l2_fixed"],
            "aim_l3_fixed": r["aim_l3_fixed"],
            "aim_source": SRC_EQ,
            "line_kind": "part",
        })
        new_rows.append(row)

    if new_rows:
        ov = pd.concat([ov, pd.DataFrame(new_rows, columns=list(ov.columns))], ignore_index=True)

    before_aim = int((pd.read_csv(bak, dtype=str, keep_default_na=False)["aim_l1_fixed"] != "").sum())
    after_aim = int((ov["aim_l1_fixed"] != "").sum())
    tmp = OVERLAY.with_suffix(".csv.tmp")
    tmp.write_bytes(
        ov.to_csv(index=False, lineterminator="\r\n" if crlf else "\n").encode("utf-8")
    )
    # verify tmp before replace
    chk = pd.read_csv(tmp, dtype=str, keep_default_na=False)
    assert len(chk) == len(ov)
    assert int((chk["aim_l1_fixed"] != "").sum()) == after_aim
    assert int(chk["aim_source"].str.contains(SRC_DESC, na=False).sum()) >= filled
    assert int(chk["aim_source"].str.contains(SRC_EQ, na=False).sum()) == len(new_rows)
    tmp.replace(OVERLAY)

    print(f"backup {bak.name}")
    print(f"DESC filled={filled} overlay_already_had_aim={skipped_has_aim} "
          f"desc_missing_on_overlay={missing_on_overlay}")
    print(f"EQ appended={len(new_rows)}")
    print(f"overlay aim nonblank {before_aim} -> {after_aim} rows={len(chk)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
