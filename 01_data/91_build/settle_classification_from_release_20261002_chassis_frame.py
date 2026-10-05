#!/usr/bin/env python3
"""Settle the pricing-critical catalogue columns from the APPROVED release 2026-10-02-chassis-frame.

Jerome's go of 2 Oct 2026 (approval 2 + go-live): pr00 and the dimension made to agree with the
newly approved release where they differ (expected: the 2 wrong-in-both parts 5878305371 and
9443730060; decision (1) changes no catalogue value). Same method as the 2026-10-02 settle below.
Keys in the release but not in pr00 (the 3 rows the release added) are NOT added to pr00.

Original docstring of the 2026-10-02 settle:

Jerome's decision, 2 Oct 2026 (PR #10 merge): the pricing-critical classification files are
SETTLED from the approved 2026-10-02 release rather than merged side against side.

What it changes, and only that:
  pr00_classification.csv            family / group / level3_type  <- release catalog_l1/l2/l3
  parts_catalog_dimension.csv/.parquet  pr00_family / pr00_group / pr00_level3_type
                                     <- the settled pr00 triple (the dimension's pr00_* columns
                                        are a copy of pr00; checked equal before the change)
Keys not in the release are left as they are. No other column, row or row order moves.

Not touched: sellout_aim_top_pn_2025.csv. Its aim_l1/aim_l2 come from the sellout builder's
workbook taxonomy, not from the release; settling it means re-running that builder against the
release (which also rebuilds its sibling aggregates and page), and that builder is one of the
PR #10 source divergences still open.

Fail closed: the release must be APPROVED and hash-equal to the register; the inputs must be
the bytes measured on 2 Oct (sha256 below); a byte-exact round-trip of each file is proved
before writing; backups .bak_pre_release_settle_20261002 are written first; a change log CSV
lists every changed cell.

    python settle_classification_from_release_20261002.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
sys.path.insert(0, str(ISZE / "04_tools" / "_shared"))
from classification_paths import approved_release  # noqa: E402

PR00 = DER / "pr00_classification.csv"
PCD = DER / "parts_catalog_dimension.csv"
PCD_PQ = DER / "parts_catalog_dimension.parquet"
EXPECT = {
    PR00: "cf4bc400fa3ddcff8248b1c812bb79ef15ed652d662de02f11cd2193d927546f",
}
BAK = ".bak_pre_release_settle_20261002_chassis_frame"
LOG = DER / "_releases" / "settle_from_release_2026-10-02-chassis-frame.changes.csv"
REC = DER / "_releases" / "settle_from_release_2026-10-02-chassis-frame.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def read_csv_exact(p: Path):
    raw = p.read_bytes()
    text = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in text[:5000] else "\n"
    rows = list(csv.reader(io.StringIO(text, newline="")))
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=nl).writerows(rows)
    if buf.getvalue().encode("utf-8") != raw:
        raise SystemExit(f"{p.name}: csv round-trip is not byte-exact; refusing to rewrite")
    return rows, nl


def write_csv(p: Path, rows, nl):
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=nl).writerows(rows)
    p.write_bytes(buf.getvalue().encode("utf-8"))


def main() -> int:
    rel_path, entry = approved_release()  # raises unless APPROVED + hash ok
    if entry["release_id"] != "2026-10-02-chassis-frame":
        raise SystemExit(f"approved release is {entry['release_id']}, expected 2026-10-02-chassis-frame")
    for p, h in EXPECT.items():
        if sha(p) != h:
            raise SystemExit(f"{p.name} sha256 {sha(p)[:12]} != measured {h[:12]}: refusing")
    for p in (PR00, PCD, PCD_PQ):
        if Path(str(p) + BAK).exists():
            raise SystemExit(f"backup {p.name}{BAK} exists: already settled? refusing")

    rel = pd.read_csv(rel_path, dtype=str, keep_default_na=False,
                      usecols=["part_number", "catalog_l1", "catalog_l2", "catalog_l3"])
    rel["k"] = rel.part_number.map(pad)
    # both lubricant key forms pad to the same key and carry the same catalogue triple; check
    dup = rel[rel.k.duplicated(keep=False)]
    if dup.groupby("k")[["catalog_l1", "catalog_l2", "catalog_l3"]].nunique().max().max() > 1:
        raise SystemExit("release key forms disagree on the catalogue triple")
    tri = {k: (a, b, c) for k, a, b, c in zip(rel.k, rel.catalog_l1, rel.catalog_l2, rel.catalog_l3)}

    before = {p: sha(p) for p in (PR00, PCD, PCD_PQ)}
    log = []

    # ---- pr00
    rows, nl = read_csv_exact(PR00)
    h = rows[0]
    ik, i1, i2, i3 = (h.index(c) for c in ("pn_norm", "family", "group", "level3_type"))
    pr_new = {}
    n_pr = 0
    for r in rows[1:]:
        k = pad(r[ik])
        if k in tri and (r[i1], r[i2], r[i3]) != tri[k]:
            for col, i, v in (("family", i1, tri[k][0]), ("group", i2, tri[k][1]),
                              ("level3_type", i3, tri[k][2])):
                if r[i] != v:
                    log.append({"file": PR00.name, "part_number": r[ik], "column": col,
                                "before": r[i], "after": v})
            r[i1], r[i2], r[i3] = tri[k]
            n_pr += 1
        pr_new[k] = (r[i1], r[i2], r[i3])

    # ---- parts_catalog_dimension.csv: pr00_* is a copy of pr00; prove, then copy the settled triple
    prows, pnl = read_csv_exact(PCD)
    ph = prows[0]
    jk, j1, j2, j3 = (ph.index(c) for c in ("part_number", "pr00_family", "pr00_group",
                                             "pr00_level3_type"))
    old_pr = {pad(r[ik]): None for r in rows[1:]}
    n_pcd = 0
    pcd_new = {}
    for r in prows[1:]:
        k = pad(r[jk])
        if k in pr_new:
            if (r[j1], r[j2], r[j3]) != pr_new[k]:
                for col, i, v in (("pr00_family", j1, pr_new[k][0]), ("pr00_group", j2, pr_new[k][1]),
                                  ("pr00_level3_type", j3, pr_new[k][2])):
                    if r[i] != v:
                        log.append({"file": PCD.name, "part_number": r[jk], "column": col,
                                    "before": r[i], "after": v})
                r[j1], r[j2], r[j3] = pr_new[k]
                n_pcd += 1
            pcd_new[r[jk]] = pr_new[k]
    del old_pr

    # ---- parquet twin: same keys, same three columns
    pq = pd.read_parquet(PCD_PQ)
    if len(pq) != len(prows) - 1:
        raise SystemExit(f"parquet rows {len(pq)} != csv rows {len(prows) - 1}")
    pk = pq["part_number"].astype(str)
    n_pq = 0
    for col, pos in (("pr00_family", 0), ("pr00_group", 1), ("pr00_level3_type", 2)):
        newv = pk.map(lambda s: pcd_new[s][pos] if s in pcd_new else None)
        cur = pq[col]
        mask = newv.notna() & (cur.fillna("").astype(str) != newv.fillna(""))
        n_pq += int(mask.sum())
        pq.loc[mask, col] = newv[mask]

    # ---- write (backups first)
    for p in (PR00, PCD, PCD_PQ):
        Path(str(p) + BAK).write_bytes(p.read_bytes())
    write_csv(PR00, rows, nl)
    write_csv(PCD, prows, pnl)
    pq.to_parquet(PCD_PQ, index=False)
    with LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "part_number", "column", "before", "after"])
        w.writeheader()
        w.writerows(log)

    # ---- verify
    chk = pd.read_csv(PR00, dtype=str, keep_default_na=False)
    chk["k"] = chk.pn_norm.map(pad)
    mism = sum(1 for k, a, b, c in zip(chk.k, chk.family, chk.group, chk.level3_type)
               if k in tri and (a, b, c) != tri[k])
    pcdc = pd.read_csv(PCD, dtype=str, keep_default_na=False)
    pcd_vs_pr = sum(1 for k, a, b, c in zip(pcdc.part_number.map(pad), pcdc.pr00_family,
                                            pcdc.pr00_group, pcdc.pr00_level3_type)
                    if k in pr_new and (a, b, c) != pr_new[k])
    pq2 = pd.read_parquet(PCD_PQ)
    pq_vs_csv = int((pq2[["pr00_family", "pr00_group", "pr00_level3_type"]].fillna("").astype(str).values
                     != pcdc[["pr00_family", "pr00_group", "pr00_level3_type"]].values).any(axis=1).sum())
    rec = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "by": "01_data/91_build/settle_classification_from_release_20261002_chassis_frame.py",
        "decision": "Jerome 2026-10-02 (approval 2 + go-live): pr00 / parts_catalog_dimension made to agree with the approved 2026-10-02-chassis-frame release where they differ",
        "release": {"id": entry["release_id"], "sha256": entry["sha256"], "path": str(rel_path)},
        "rows_changed": {PR00.name: n_pr, PCD.name: n_pcd, PCD_PQ.name + " (cells)": n_pq},
        "cells_changed_logged": len(log),
        "verify": {"pr00_vs_release_mismatch_after": mism, "pcd_vs_settled_pr00_mismatch": pcd_vs_pr,
                   "parquet_vs_csv_rows_differing": pq_vs_csv},
        "sha256_before": {p.name: h for p, h in before.items()},
        "sha256_after": {p.name: sha(p) for p in (PR00, PCD, PCD_PQ)},
        "backups": [p.name + BAK for p in (PR00, PCD, PCD_PQ)],
        "not_settled": {"sellout_aim_top_pn_2025.csv": "labels come from the sellout builder's workbook taxonomy; needs that builder re-run against the release (open PR #10 source divergence)"},
    }
    REC.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec, indent=2))
    return 0 if (mism == 0 and pcd_vs_pr == 0 and pq_vs_csv == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
