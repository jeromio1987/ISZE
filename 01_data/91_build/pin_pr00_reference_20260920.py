#!/usr/bin/env python3
"""Pin the pr00 copy-integrity reference to pr00_classification.csv as committed 20 Sep 2026.

Jerome's decision, 2 Oct 2026 (chat): the copy-integrity check (gate check
`pr00_copy_integrity`) measures a release's catalogue columns against the 20 Sep version of
pr00_classification.csv (git c813330f), not against today's file, because today's file
carries the 21 Sep regression (1,660 rows).

What this does (idempotent, never edits a release CSV):
  1. writes the exact bytes of c813330f:01_data/00_derived/pr00_classification.csv to
     _releases/pr00_classification_reference_20260920.csv (read-only), and a sidecar
     .meta.json with source commit, sha256, rows and the reason;
  2. re-measures copy integrity of the 2026-10-02 release against that pinned copy (same
     method as the release builder: padded key, (family, group, level3_type) ==
     (catalog_l1, catalog_l2, catalog_l3)) and rewrites the release meta's
     catalogue_verification_vs_pr00 block to name the pinned reference, its hash and the
     reason; today's-pr00 figure is kept beside it as information.

The gate (verify_aim_classification.py) re-hashes the pinned copy and re-measures the
figure itself; it does not take this script's number on trust.

    python pin_pr00_reference_20260920.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
PR00_TODAY = DER / "pr00_classification.csv"
SOURCE_COMMIT = "c813330f"
SOURCE_PATH = "01_data/00_derived/pr00_classification.csv"
REF = REL / "pr00_classification_reference_20260920.csv"
REF_META = REF.with_suffix(".meta.json")
RELEASE = REL / "aim_pn_classification_release_2026-10-02.csv"
RELEASE_META = RELEASE.with_suffix(".meta.json")
RELEASE_SHA = "0ac9137903a326430c68e4d619fa4f836a796a01d9d40f6f6f1183e7d4c52360"

REASON = (
    "Jerome decision 2026-10-02 (chat): copy integrity is measured against pr00_classification.csv "
    "as committed 20 Sep 2026 (git c813330f), not against today's file, because today's file "
    "carries the 21 Sep regression (1,660 rows). Pinned as a hash-recorded "
    "copy so the reference cannot move underneath the gate."
)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def integrity(pr00_text: str, release_path: Path) -> dict:
    pm = {}
    for r in csv.DictReader(io.StringIO(pr00_text)):
        k = pad(r.get("pn_norm") or "")
        if k:
            pm[k] = ((r.get("family") or "").strip(), (r.get("group") or "").strip(),
                     (r.get("level3_type") or "").strip())
    chk = ok = 0
    with release_path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            k = pad(r["part_number"])
            if k in pm:
                chk += 1
                ok += pm[k] == ((r["catalog_l1"] or "").strip(), (r["catalog_l2"] or "").strip(),
                                (r["catalog_l3"] or "").strip())
    return {"rows_checked": chk, "rows_matching": ok,
            "match_pct": round(100 * ok / chk, 4) if chk else None}


def main() -> int:
    blob = subprocess.run(["git", "-C", str(ISZE), "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
                          capture_output=True, check=True).stdout
    ref_sha = sha(blob)
    if REF.is_file():
        on_disk = sha(REF.read_bytes())
        if on_disk != ref_sha:
            raise SystemExit(f"{REF.name} exists with sha256 {on_disk}, git blob is {ref_sha}: refusing")
    else:
        REF.write_bytes(blob)
        os.chmod(REF, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    text = blob.decode("utf-8")
    ref_rows = sum(1 for _ in csv.DictReader(io.StringIO(text)))
    today_bytes = PR00_TODAY.read_bytes()

    REF_META.write_text(json.dumps({
        "file": REF.name,
        "sha256": ref_sha,
        "rows": ref_rows,
        "source_commit": SOURCE_COMMIT,
        "source_commit_full": subprocess.run(["git", "-C", str(ISZE), "rev-parse", SOURCE_COMMIT],
                                             capture_output=True, text=True, check=True).stdout.strip(),
        "source_path": SOURCE_PATH,
        "role": "reference for gate check pr00_copy_integrity",
        "decided_by": "Jerome",
        "decided_on": "2026-10-02",
        "reason": REASON,
        "not_used_today_file": {"file": str(PR00_TODAY), "sha256": sha(today_bytes)},
        "pinned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pinned_by": "01_data/91_build/pin_pr00_reference_20260920.py",
    }, indent=2), encoding="utf-8")

    if sha(RELEASE.read_bytes()) != RELEASE_SHA:
        raise SystemExit(f"{RELEASE.name} sha256 moved: refusing to amend its meta")
    ref_int = integrity(text, RELEASE)
    today_int = integrity(today_bytes.decode("utf-8"), RELEASE)

    meta = json.loads(RELEASE_META.read_text(encoding="utf-8"))
    meta["catalogue_verification_vs_pr00"] = {
        **ref_int,
        "reference_file": REF.name,
        "reference_sha256": ref_sha,
        "reference_source": f"git {SOURCE_COMMIT}:{SOURCE_PATH} (pr00 as committed 20 Sep 2026)",
        "reference_reason": REASON,
        "note": ("COPY-INTEGRITY ONLY, measured on THIS file: catalogue columns vs the pinned "
                 "20 Sep pr00 reference on the zero-padded key (method of "
                 "build_aim_classification_v2.py). The 9 lubricant 9-digit keys pad to their "
                 "10-digit twins and are counted. The single non-matching row is the deliberate "
                 "8980913940 air-filter catalogue fix. Does not prove correctness vs customs, "
                 "figures or part text."),
        "vs_pr00_today_information_only": {
            **today_int, "pr00_file": str(PR00_TODAY), "pr00_sha256": sha(today_bytes),
            "note": "today's pr00 carries the 21 Sep regression; not the gate reference "
                    "(Jerome 2026-10-02)"},
        "amended": {"on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "by": "01_data/91_build/pin_pr00_reference_20260920.py",
                    "previous_reference": "today's pr00_classification.csv (match 98.9921%)"},
    }
    RELEASE_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"reference {REF.name} sha256={ref_sha} rows={ref_rows}")
    print(f"release vs pinned reference: {ref_int}")
    print(f"release vs today's pr00 (information): {today_int}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
