#!/usr/bin/env python3
"""Cut AIM classification release 2026-10-15 from approved 2026-10-11.

Jerome 2026-10-15: "approve and do all changes, I want AIM to be as good as possible"

Applies:
  - 30 pad kits from next_release_proposal_pad_kits_2026-10-15.csv
  - every verdict=move row from next_release_proposal_wrong_labels_2026-10-15.csv

Does NOT invent new AIM labels. Decide rows stay untouched.
Does NOT touch catalogue columns. Does NOT rebuild the price revision tool.

    python 01_data/91_build/build_aim_classification_release_20261015.py
    python 01_data/91_build/build_aim_classification_release_20261015.py --approve
    python 01_data/91_build/build_aim_classification_release_20261015.py --sync
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

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
BUILD = ISZE / "01_data" / "91_build"

RELEASE_ID = "2026-10-15"
RELEASE_IDC = "20261015"
BASE_ID = "2026-10-11"
BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
OUT = REL / f"aim_pn_classification_release_{RELEASE_ID}.csv"
OUT_CHANGES = REL / f"aim_pn_classification_release_{RELEASE_ID}.changes.csv"
OUT_META = REL / f"aim_pn_classification_release_{RELEASE_ID}.meta.json"
REGISTER = REL / "RELEASES.json"
MASTER = DER / "aim_master_v2.csv"
LIVE = DER / "aim_pn_classification_20260920.csv"
PAD = REL / "next_release_proposal_pad_kits_2026-10-15.csv"
WRONG = REL / "next_release_proposal_wrong_labels_2026-10-15.csv"
PR00_REF = REL / "pr00_classification_reference_20260920.csv"
META_07 = REL / "aim_pn_classification_release_2026-10-07.meta.json"

AIM = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]
JEROME_GO = (
    "approve and do all changes, I want AIM to be as good as possible "
    "(2026-10-15 chat; pad kits + wrong-label moves; no new leaves)"
)
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

EXPECT_BASE_SHA = "d9b26b0124bacadcece437f665fc673e32b70d2087d78aa0884ea6615369f605"
EXPECT_PR00_SHA = "98e64b5bdaef73819cf954ce96241f1a9b49d8fbd998d02700ae8494028bea34"


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


def pad_key(s: str) -> str:
    s = (s or "").strip()
    return s.zfill(10) if s.isdigit() or (s and s.lstrip("0").isdigit()) or s.isdigit() else s.zfill(10) if s else s


def load_moves() -> pd.DataFrame:
    pad = pd.read_csv(PAD, dtype=str, keep_default_na=False)
    for c in pad.columns:
        pad[c] = pad[c].str.strip()
    pad["part_number"] = pad.part_number.str.zfill(10)
    pad["change_group"] = "padkit_" + pad.change_group.astype(str)
    pad["src_tag"] = f"padkit_{RELEASE_IDC}"
    pad["proposed_aim_l1"] = pad.proposed_aim_l1
    pad["proposed_aim_l2"] = pad.proposed_aim_l2
    pad["proposed_aim_l3"] = pad.proposed_aim_l3

    wr = pd.read_csv(WRONG, dtype=str, keep_default_na=False)
    for c in wr.columns:
        wr[c] = wr[c].str.strip()
    wr = wr[wr.verdict.eq("move")].copy()
    wr["part_number"] = wr.part_number.str.zfill(10)
    wr["change_group"] = "wronglabel_" + wr.group.astype(str)
    wr["src_tag"] = f"wronglabel_{RELEASE_IDC}"

    cols = [
        "part_number",
        "change_group",
        "src_tag",
        "proposed_aim_l1",
        "proposed_aim_l2",
        "proposed_aim_l3",
        "current_aim_l1",
        "current_aim_l2",
        "current_aim_l3",
    ]
    # pad uses current_aim_l1 etc already
    out = pd.concat([pad[cols], wr[cols]], ignore_index=True)
    assert out.part_number.is_unique, out.part_number[out.part_number.duplicated()].tolist()[:10]
    assert len(pad) == 30
    assert len(wr) == 1020, len(wr)
    return out


def catalogue_integrity(df: pd.DataFrame) -> tuple[dict, list[str]]:
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


def build_pending() -> dict:
    base_sha = sha256(BASE)
    assert base_sha == EXPECT_BASE_SHA, base_sha
    assert sha256(PR00_REF) == EXPECT_PR00_SHA

    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    if any(c.get("release_id") == RELEASE_ID for c in reg["candidates"]):
        raise SystemExit(f"{RELEASE_ID} already in RELEASES.json — stop")
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    assert base_entry["status"] == "APPROVED", base_entry["status"]
    assert base_entry["sha256"] == base_sha

    moves = load_moves()
    rel = pd.read_csv(BASE, dtype=str, keep_default_na=False)
    for c in rel.columns:
        rel[c] = rel[c].str.strip()
    assert len(rel) == 165055
    before = rel.copy()

    change_rows = []
    by_group: dict[str, int] = {}
    idx = rel.set_index(rel.part_number.str.zfill(10), drop=False)

    for r in moves.itertuples():
        pn = r.part_number
        if pn not in idx.index:
            raise SystemExit(f"part {pn} missing from base release")
        # handle duplicate index carefully — release part_numbers should be unique
        row_pos = rel.index[rel.part_number.str.zfill(10) == pn]
        assert len(row_pos) == 1, pn
        i = int(row_pos[0])
        tgt = (r.proposed_aim_l1, r.proposed_aim_l2, r.proposed_aim_l3)
        for col, val in zip(AIM, tgt):
            old = rel.at[i, col]
            if old != val:
                change_rows.append(
                    {
                        "part_number": pn,
                        "change_group": r.change_group,
                        "column": col,
                        "before": old,
                        "after": val,
                    }
                )
            rel.at[i, col] = val
        prev = rel.at[i, "aim_source"] if "aim_source" in rel.columns else ""
        tag = r.src_tag
        if tag not in str(prev):
            rel.at[i, "aim_source"] = (str(prev) + "|" + tag).lstrip("|")
        by_group[r.change_group] = by_group.get(r.change_group, 0) + 1

    # only AIM + aim_source may differ
    for c in rel.columns:
        if c in AIM or c == "aim_source":
            continue
        if not rel[c].equals(before[c]):
            raise SystemExit(f"non-AIM column changed: {c}")

    moved_mask = (rel[AIM] != before[AIM]).any(axis=1)
    moved_pns = set(rel.loc[moved_mask, "part_number"].str.zfill(10))
    expect_pns = set(moves.part_number)
    # some moves may already equal target (no cell change) — still tagged in source
    assert moved_pns <= expect_pns, sorted(moved_pns - expect_pns)[:10]

    # pad kit zero-check
    desc = rel.description_norm.str.upper()
    # also PR00 list for blank release descriptions — use proposal rule
    enq = pd.read_parquet(
        DER / "pricing_pn_enquiry.parquet",
        columns=["part_number", "description"],
    )
    enq["pn"] = enq.part_number.astype(str).str.strip().str.zfill(10)
    enq = enq.drop_duplicates("pn").set_index("pn")
    list_desc = rel.part_number.str.zfill(10).map(enq.description).fillna("").astype(str)
    pad_like = desc.str.startswith("PAD KIT") | (
        desc.eq("") & list_desc.str.upper().str.startswith("PAD KIT")
    )
    left = rel[pad_like & rel.aim_l3_fixed.ne("Brake Pad Kit")]
    assert left.empty, left.part_number.tolist()[:10]
    bpk_before = int(before.aim_l3_fixed.eq("Brake Pad Kit").sum())
    bpk_after = int(rel.aim_l3_fixed.eq("Brake Pad Kit").sum())
    assert bpk_before == 112 and bpk_after == 142, (bpk_before, bpk_after)

    # no new leaves
    leaves_before = set(zip(*(before[c] for c in AIM)))
    leaves_after = set(zip(*(rel[c] for c in AIM)))
    new_leaves = leaves_after - leaves_before
    assert not new_leaves, list(new_leaves)[:10]

    rel.to_csv(OUT, index=False, encoding="utf-8")
    changes_df = pd.DataFrame(change_rows)
    changes_df.to_csv(OUT_CHANGES, index=False, encoding="utf-8")
    out_sha = sha256(OUT)

    ref_int, ref_miss = catalogue_integrity(rel)
    base_int, base_miss = catalogue_integrity(before)
    # catalogue untouched → miss sets must match base
    assert set(ref_miss) == set(base_miss), (
        len(set(ref_miss) - set(base_miss)),
        len(set(base_miss) - set(ref_miss)),
    )

    meta07 = json.loads(META_07.read_text(encoding="utf-8"))
    consumer = meta07["consumer_contract"]
    purpose = meta07["purpose"]

    # distinct parts in changes
    ch_parts = changes_df.part_number.nunique() if len(changes_df) else 0

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_aim_classification_release_20261015.py",
        "release_id": RELEASE_ID,
        "status": "PENDING_APPROVAL",
        "base_release": BASE_ID,
        "base_sha256": base_sha,
        "sha256": out_sha,
        "rows": int(len(rel)),
        "built_by_note": "combined pad kits + wrong-label moves",
        "jerome_go": JEROME_GO,
        "counts": {k: int(v) for k, v in sorted(by_group.items())},
        "parts_in_proposals": int(len(moves)),
        "parts_with_aim_cell_change": int(ch_parts),
        "change_log": OUT_CHANGES.name,
        "change_log_rows": int(len(changes_df)),
        "zero_checks": {
            "pad_kits_outside_brake_pad_kit": 0,
            "new_aim_labels": 0,
            "catalogue_columns_changed": 0,
            "brake_pad_kit_before": bpk_before,
            "brake_pad_kit_after": bpk_after,
        },
        "aim_label_vocabulary": {
            "new_aim_labels": [],
            "note": "no new AIM triples; pad kits and wrong-label moves onto existing leaves only",
        },
        "catalogue_verification_vs_pr00": {
            **ref_int,
            "reference_file": PR00_REF.name,
            "reference_sha256": EXPECT_PR00_SHA,
            "non_matching_parts": len(ref_miss),
            "base_release_non_matching_parts": len(base_miss),
            "note": "COPY-INTEGRITY ONLY. This release did not change catalogue columns.",
        },
        "purpose": purpose,
        "consumer_contract": consumer,
        "decide_not_applied": {
            "note": (
                "wrong-label verdict=decide parts were not applied; "
                "no existing leaf fits and new labels are out of scope"
            ),
            "parts": int((pd.read_csv(WRONG, dtype=str).verdict == "decide").sum()),
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    backup(REGISTER, "pre_rel_20261015")
    reg["candidates"].append(
        {
            "release_id": RELEASE_ID,
            "path": OUT.name,
            "sha256": out_sha,
            "status": "PENDING_APPROVAL",
            "rows": int(len(rel)),
            "rows_note": "data rows, header excluded",
            "base_release": BASE_ID,
            "source": (
                f"release {BASE_ID} + pad kits (30) + wrong-label moves (1020); "
                "decide rows not applied"
            ),
            "recommendation": JEROME_GO,
            "notes": (
                f"Change log {OUT_CHANGES.name}. No new AIM labels. "
                f"Counts: {meta['counts']}"
            ),
        }
    )
    REGISTER.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "status": "PENDING_APPROVAL",
                "sha256": out_sha,
                "change_rows": len(changes_df),
                "change_parts": ch_parts,
                "counts": meta["counts"],
                "bpk": [bpk_before, bpk_after],
            },
            indent=2,
        )
    )
    return meta


def approve() -> None:
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    out_sha = sha256(OUT)
    meta = json.loads(OUT_META.read_text(encoding="utf-8"))
    assert meta["sha256"] == out_sha

    found = False
    for c in reg["candidates"]:
        if c.get("release_id") == BASE_ID and c.get("status") == "APPROVED":
            c["status"] = "SUPERSEDED"
            c["superseded_by"] = RELEASE_ID
            c["superseded_on"] = RELEASE_ID
            c["superseded_note"] = (
                "Superseded when Jerome approved the combined pad-kit + wrong-label "
                "release 2026-10-15."
            )
        if c.get("release_id") == RELEASE_ID:
            assert c.get("sha256") == out_sha, (c.get("sha256"), out_sha)
            c["status"] = "APPROVED"
            c["approved_by"] = "Jerome"
            c["approved_on"] = RELEASE_ID
            c["approved_note"] = JEROME_GO
            found = True
    assert found, "release entry missing"
    backup(REGISTER, "pre_approve_20261015")
    REGISTER.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")

    meta["status"] = "APPROVED"
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "status": "APPROVED", "sha256": out_sha}, indent=2))


def sync_master_overlay() -> None:
    moves = load_moves()
    pns = set(moves.part_number)
    by_pn = moves.set_index("part_number")

    bak_m = backup(MASTER, "pre_padkit_wronglabel")
    bak_l = backup(LIVE, "pre_padkit_wronglabel")

    master = pd.read_csv(MASTER, dtype=str, keep_default_na=False)
    for c in master.columns:
        master[c] = master[c].str.strip()
    live = pd.read_csv(LIVE, dtype=str, keep_default_na=False)
    for c in live.columns:
        live[c] = live[c].str.strip()

    m_before = master.copy()
    l_before = live.copy()
    mp = master.part_number.str.zfill(10)
    lp = live.part_number.str.zfill(10)

    for pn in pns:
        r = by_pn.loc[pn]
        tgt = (r.proposed_aim_l1, r.proposed_aim_l2, r.proposed_aim_l3)
        tag = r.src_tag
        mm = mp.eq(pn)
        if mm.any():
            master.loc[mm, "aim_l1_fixed"] = tgt[0]
            master.loc[mm, "aim_l2_fixed"] = tgt[1]
            if "aim_l3" in master.columns:
                master.loc[mm, "aim_l3"] = tgt[2]
            if "has_aim" in master.columns:
                master.loc[mm, "has_aim"] = "1"
            if "aim_changed" in master.columns:
                master.loc[mm, "aim_changed"] = "1"
            if "aim_source" in master.columns:
                prev = master.loc[mm, "aim_source"].fillna("").astype(str)
                master.loc[mm, "aim_source"] = [
                    (p + "|" + tag).lstrip("|") if tag not in p else p for p in prev
                ]
        lm = lp.eq(pn)
        if lm.any():
            live.loc[lm, "aim_l1_fixed"] = tgt[0]
            live.loc[lm, "aim_l2_fixed"] = tgt[1]
            live.loc[lm, "aim_l3_fixed"] = tgt[2]
            if "aim_source" in live.columns:
                prev = live.loc[lm, "aim_source"].fillna("").astype(str)
                live.loc[lm, "aim_source"] = [
                    (p + "|" + tag).lstrip("|") if tag not in p else p for p in prev
                ]

    assert len(master) == len(m_before)
    assert len(live) == len(l_before)

    # only touched pns may differ
    for df, before, key in (
        (master, m_before, mp),
        (live, l_before, lp),
    ):
        # compare all columns; allow diffs only on rows in pns
        for c in df.columns:
            if df[c].equals(before[c]):
                continue
            changed_rows = df.index[df[c] != before[c]]
            changed_pns = set(key.loc[changed_rows])
            if not changed_pns <= pns:
                raise SystemExit(
                    f"{c}: rows outside proposal changed: {sorted(changed_pns - pns)[:10]}"
                )

    master.to_csv(MASTER, index=False, encoding="utf-8")
    live.to_csv(LIVE, index=False, encoding="utf-8")

    # agreement check vs release
    rel = pd.read_csv(OUT, dtype=str, keep_default_na=False)
    rel["pn"] = rel.part_number.str.zfill(10)
    rmap = rel.drop_duplicates("pn").set_index("pn")
    master["pn"] = master.part_number.str.zfill(10)
    live["pn"] = live.part_number.str.zfill(10)
    bad = []
    for pn in pns:
        rt = (
            rmap.at[pn, "aim_l1_fixed"],
            rmap.at[pn, "aim_l2_fixed"],
            rmap.at[pn, "aim_l3_fixed"],
        )
        if pn in set(master.pn):
            mrow = master.loc[master.pn.eq(pn)].iloc[0]
            mt = (mrow.aim_l1_fixed, mrow.aim_l2_fixed, mrow.aim_l3)
            if mt != rt:
                bad.append(("master", pn, mt, rt))
        if pn in set(live.pn):
            lrow = live.loc[live.pn.eq(pn)].iloc[0]
            lt = (lrow.aim_l1_fixed, lrow.aim_l2_fixed, lrow.aim_l3_fixed)
            if lt != rt:
                bad.append(("live", pn, lt, rt))
    assert not bad, bad[:5]

    print(
        json.dumps(
            {
                "ok": True,
                "synced_parts": len(pns),
                "backup_master": str(bak_m),
                "backup_live": str(bak_l),
            },
            indent=2,
        )
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--sync", action="store_true")
    args = ap.parse_args()
    if args.approve:
        approve()
    elif args.sync:
        sync_master_overlay()
    else:
        build_pending()


if __name__ == "__main__":
    main()
