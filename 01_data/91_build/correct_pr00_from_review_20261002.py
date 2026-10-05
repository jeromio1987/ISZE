#!/usr/bin/env python3
"""Correct pr00 classification per the 21 Sep vs 20 Sep part-by-part review (Jerome's go, 2 Oct 2026).

Input review: 01_data/91_build/pr00_21sep_review_2026-10-02/pr00_21sep_review_per_part.csv (1,661 parts).
  verdict keep_20sep  -> family/group/level3_type <- approved release 2026-10-02 catalog_l1/l2/l3
                         (same values as settle_classification_from_release_20261002.py)
  verdict keep_21sep  -> current value kept (no change)
  verdict neither     -> the review's proposed_family/group/level3_type
Then parts_catalog_dimension.csv/.parquet pr00_* are set to the corrected pr00 triple
(same mechanics as the settle script). No other column, row or row order moves.

Not touched: the approved release, RELEASES.json, the gate. The 2 keep_21sep + 40 neither
differences vs the release are written as a proposal for the NEXT release (not applied).

pr00 has no review/note column, so the parts still to check are marked in the change log
(note = "to check").

Fail closed: input hashes must be the bytes measured on 2 Oct; byte-exact csv round-trip;
timestamped backups first; verification after write.
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
REL_DIR = DER / "_releases"
sys.path.insert(0, str(ISZE / "04_tools" / "_shared"))
from classification_paths import approved_release  # noqa: E402

REVIEW = ISZE / "01_data" / "91_build" / "pr00_21sep_review_2026-10-02" / "pr00_21sep_review_per_part.csv"
PR00 = DER / "pr00_classification.csv"
PCD = DER / "parts_catalog_dimension.csv"
PCD_PQ = DER / "parts_catalog_dimension.parquet"
EXPECT = {
    PR00: "f1e481919a32fbd74efd5ca2e6fd832f112a5eb6c70c4977b6f287c8e5c52f80",
    PCD: "02aecf7add3d8f8c699ac523084ce84e8f0b95e1e5fcd9b0eeb796ee3b0aa6ed",
    PCD_PQ: "8cd58b8fa13c87fc38423d45fb92ba0d0662aa2f10b7e8cd934a65956910ad4d",
}
LOG = REL_DIR / "pr00_correction_2026-10-02.changes.csv"
META = REL_DIR / "pr00_correction_2026-10-02.meta.json"
PROPOSAL = REL_DIR / "next_release_proposal_2026-10-02.csv"
# Jerome's brief names these as the low-confidence proposals to check. The review CSV rates
# PLATE; SKID,RAD "low" and ELEMENT KIT; PCV "medium" (reading of PCV not EPC-confirmed).
TO_CHECK = {"8983941570", "8983941544", "8981065790", "8980023462"}


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
    rel_path, entry = approved_release()
    if entry["release_id"] != "2026-10-02":
        raise SystemExit(f"approved release is {entry['release_id']}, expected 2026-10-02")
    for p, h in EXPECT.items():
        if sha(p) != h:
            raise SystemExit(f"{p.name} sha256 {sha(p)[:12]} != measured {h[:12]}: refusing")
    rel_sha_before = sha(rel_path)
    reg = REL_DIR / "RELEASES.json"
    reg_sha_before = sha(reg)

    rel = pd.read_csv(rel_path, dtype=str, keep_default_na=False,
                      usecols=["part_number", "catalog_l1", "catalog_l2", "catalog_l3"])
    rel["k"] = rel.part_number.map(pad)
    tri = {k: (a, b, c) for k, a, b, c in zip(rel.k, rel.catalog_l1, rel.catalog_l2, rel.catalog_l3)}

    rv = pd.read_csv(REVIEW, dtype=str, keep_default_na=False)
    rv["k"] = rv.part_number.map(pad)
    if rv.k.duplicated().any():
        raise SystemExit("review has duplicate parts")
    counts = rv.verdict.value_counts().to_dict()
    if counts != {"keep_20sep": 1619, "neither": 40, "keep_21sep": 2}:
        raise SystemExit(f"unexpected verdict counts {counts}")
    target, verdict_of, conf_of, desc_of = {}, {}, {}, {}
    for r in rv.itertuples(index=False):
        verdict_of[r.k], conf_of[r.k], desc_of[r.k] = r.verdict, r.confidence, r.description
        if r.verdict == "keep_20sep":
            if (r.sep20_family, r.sep20_group, r.sep20_level3_type) != tri.get(r.k):
                raise SystemExit(f"{r.k}: review 20 Sep value != release")
            target[r.k] = tri[r.k]
        elif r.verdict == "neither":
            target[r.k] = (r.proposed_family, r.proposed_group, r.proposed_level3_type)
        # keep_21sep: no target -> unchanged
    if not TO_CHECK <= {k for k, v in verdict_of.items() if v == "neither"}:
        raise SystemExit("to-check parts are not all 'neither'")

    before = {p: sha(p) for p in (PR00, PCD, PCD_PQ)}
    log = []

    def note(k):
        return "to check" if k in TO_CHECK else ""

    # ---- pr00
    rows, nl = read_csv_exact(PR00)
    h = rows[0]
    ik, i1, i2, i3 = (h.index(c) for c in ("pn_norm", "family", "group", "level3_type"))
    pr_new, n_pr, n_pr_by = {}, 0, {}
    cur21 = {}
    for r in rows[1:]:
        k = pad(r[ik])
        if k in verdict_of:
            cur21[k] = (r[i1], r[i2], r[i3])
        if k in target and (r[i1], r[i2], r[i3]) != target[k]:
            for col, i, v in (("family", i1, target[k][0]), ("group", i2, target[k][1]),
                              ("level3_type", i3, target[k][2])):
                if r[i] != v:
                    log.append({"file": PR00.name, "part_number": r[ik], "column": col,
                                "before": r[i], "after": v, "reason": verdict_of[k],
                                "confidence": conf_of[k], "note": note(k)})
            r[i1], r[i2], r[i3] = target[k]
            n_pr += 1
            n_pr_by[verdict_of[k]] = n_pr_by.get(verdict_of[k], 0) + 1
        pr_new[k] = (r[i1], r[i2], r[i3])
    if set(cur21) != set(verdict_of):
        raise SystemExit("not every review part is in pr00")

    # ---- dimension csv
    prows, pnl = read_csv_exact(PCD)
    ph = prows[0]
    jk, j1, j2, j3 = (ph.index(c) for c in ("part_number", "pr00_family", "pr00_group", "pr00_level3_type"))
    n_pcd, pcd_new = 0, {}
    for r in prows[1:]:
        k = pad(r[jk])
        if k in pr_new:
            if (r[j1], r[j2], r[j3]) != pr_new[k]:
                for col, i, v in (("pr00_family", j1, pr_new[k][0]), ("pr00_group", j2, pr_new[k][1]),
                                  ("pr00_level3_type", j3, pr_new[k][2])):
                    if r[i] != v:
                        log.append({"file": PCD.name, "part_number": r[jk], "column": col,
                                    "before": r[i], "after": v, "reason": verdict_of.get(k, ""),
                                    "confidence": conf_of.get(k, ""), "note": note(k)})
                r[j1], r[j2], r[j3] = pr_new[k]
                n_pcd += 1
            pcd_new[r[jk]] = pr_new[k]

    # ---- parquet twin
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

    # ---- backups (timestamped), then write
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = f".bak_pre_pr00_correction_{ts}"
    for p in (PR00, PCD, PCD_PQ):
        b = Path(str(p) + bak)
        if b.exists():
            raise SystemExit(f"{b.name} exists")
        b.write_bytes(p.read_bytes())
        if sha(b) != before[p]:
            raise SystemExit(f"backup {b.name} hash mismatch")
    write_csv(PR00, rows, nl)
    write_csv(PCD, prows, pnl)
    pq.to_parquet(PCD_PQ, index=False)
    with LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "part_number", "column", "before", "after",
                                          "reason", "confidence", "note"])
        w.writeheader()
        w.writerows(log)

    # ---- next-release proposal: corrected pr00 vs release, on the review parts
    prop = []
    for r in rv.itertuples(index=False):
        if r.verdict == "keep_20sep":
            continue
        rl = tri.get(r.k, ("", "", ""))
        nw = pr_new[r.k]
        prop.append({"part_number": r.k, "description": r.description, "fig_key": r.fig_key,
                     "verdict": r.verdict, "confidence": r.confidence,
                     "release_family": rl[0], "release_group": rl[1], "release_level3_type": rl[2],
                     "proposed_family": nw[0], "proposed_group": nw[1], "proposed_level3_type": nw[2],
                     "in_release": r.k in tri, "note": note(r.k), "l12m_eur": r.l12m_eur,
                     "status": "PROPOSED - not applied to any release; Jerome approves"})
    with PROPOSAL.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prop[0].keys()))
        w.writeheader()
        w.writerows(prop)

    # ---- verify
    chk = pd.read_csv(PR00, dtype=str, keep_default_na=False)
    chk["k"] = chk.pn_norm.map(pad)
    after = {k: (a, b, c) for k, a, b, c in zip(chk.k, chk.family, chk.group, chk.level3_type)}
    v_target = sum(1 for k, t in target.items() if after[k] != t)
    v_keep21 = sum(1 for k, v in verdict_of.items() if v == "keep_21sep" and after[k] != cur21[k])
    v_vs_rel = sorted(k for k in after if k in tri and after[k] != tri[k])
    v_vs_rel_ok = set(v_vs_rel) == {p["part_number"] for p in prop if p["in_release"]
                                      and (p["proposed_family"], p["proposed_group"], p["proposed_level3_type"])
                                      != (p["release_family"], p["release_group"], p["release_level3_type"])}
    # rows outside the review untouched
    old = pd.read_csv(Path(str(PR00) + bak), dtype=str, keep_default_na=False)
    old["k"] = old.pn_norm.map(pad)
    outside = (old.k.values == chk.k.values).all() and int(
        ((old.drop(columns="k").values != chk.drop(columns="k").values).any(axis=1)
         & ~chk.k.isin(target.keys()).values).sum()) == 0
    pcdc = pd.read_csv(PCD, dtype=str, keep_default_na=False)
    pcd_vs_pr = sum(1 for k, a, b, c in zip(pcdc.part_number.map(pad), pcdc.pr00_family,
                                            pcdc.pr00_group, pcdc.pr00_level3_type)
                    if k in after and (a, b, c) != after[k])
    pq2 = pd.read_parquet(PCD_PQ)
    pq_vs_csv = int((pq2[["pr00_family", "pr00_group", "pr00_level3_type"]].fillna("").astype(str).values
                     != pcdc[["pr00_family", "pr00_group", "pr00_level3_type"]].values).any(axis=1).sum())
    rel_untouched = sha(rel_path) == rel_sha_before and sha(reg) == reg_sha_before

    rec = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "by": "01_data/91_build/correct_pr00_from_review_20261002.py",
        "decision": "Jerome 2026-10-02: correct pr00 per the 21 Sep review (keep 20 Sep on 1,619; keep 21 Sep on 2; proposed value on 40)",
        "review": {"file": str(REVIEW.relative_to(ISZE)), "sha256": sha(REVIEW), "verdicts": counts},
        "release": {"id": entry["release_id"], "sha256": entry["sha256"], "untouched": rel_untouched},
        "pr00_rows_changed_by_verdict": n_pr_by,
        "rows_changed": {PR00.name: n_pr, PCD.name: n_pcd, PCD_PQ.name + " (cells)": n_pq},
        "cells_changed_logged": len(log),
        "to_check": sorted(TO_CHECK),
        "to_check_basis": "named in Jerome's brief; review CSV confidence: PLATE; SKID,RAD = low (2), ELEMENT KIT; PCV = medium (2)",
        "next_release_proposal": {"file": str(PROPOSAL.relative_to(ISZE)), "rows": len(prop),
                                  "differ_from_release": len(v_vs_rel), "applied": False},
        "verify": {"target_mismatch_after": v_target, "keep_21sep_changed": v_keep21,
                   "pr00_vs_release_diff_equals_proposal": v_vs_rel_ok,
                   "rows_outside_review_unchanged": bool(outside),
                   "pcd_vs_pr00_mismatch": pcd_vs_pr, "parquet_vs_csv_rows_differing": pq_vs_csv},
        "sha256_before": {p.name: h for p, h in before.items()},
        "sha256_after": {p.name: sha(p) for p in (PR00, PCD, PCD_PQ)},
        "backups": [p.name + bak for p in (PR00, PCD, PCD_PQ)],
    }
    META.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec, indent=2))
    ok = (v_target == 0 and v_keep21 == 0 and v_vs_rel_ok and outside and pcd_vs_pr == 0
          and pq_vs_csv == 0 and rel_untouched)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
