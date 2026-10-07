#!/usr/bin/env python3
"""Approve PENDING release 2026-10-07 (Jerome GO) and sync aim_master_v2.

House sequence after the cut:
  1. Re-run verify_aim_classification.py --candidate --file <release>
  2. Stamp RELEASES.json APPROVED / SUPERSEDED
  3. Backup + fill/append aim_master_v2 (+ overlay AIM cols)
  4. Prove 2026-10-04 engine gasket sets + hard holds on master
  5. Write _aim_apply_proven_20261007.md

Does not re-cut the release file.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build")
REL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases")
OUT = REL / "aim_pn_classification_release_2026-10-07.csv"
META = OUT.with_suffix(".meta.json")
GATE = OUT.with_suffix(".gate.json")
VERIFY = BUILD / "verify_aim_classification.py"


def main() -> int:
    if not OUT.is_file() or not META.is_file():
        print("STOP: release or meta missing; cut first with build_aim_classification_release_20261007.py")
        return 2

    # 1) candidate gate (house method)
    rc = subprocess.call(
        [sys.executable, str(VERIFY), "--candidate", "--file", str(OUT)],
    )
    print(f"candidate gate exit {rc}")
    if rc != 0:
        print("STOP: candidate gate did not pass; master untouched")
        return rc

    # 2–5) reuse apply_approved from the builder module
    spec = importlib.util.spec_from_file_location(
        "build_20261007", BUILD / "build_aim_classification_release_20261007.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    import json
    meta = json.loads(META.read_text(encoding="utf-8"))
    out_sha = meta["sha256"]
    got = mod.sha(OUT)
    if got != out_sha:
        print(f"STOP: release sha {got} != meta {out_sha}")
        return 1

    ch = meta["changes_vs_base"]
    desc_filled_n = ch["desc_aim_filled"]
    desc_same_n = ch["desc_already_same"]
    eq_added = ch["rows_added"]
    eq_skipped_n = ch["eq_skipped"]
    cov_before = meta["coverage"]["aim_l1_fixed_nonblank_before"]
    cov_after = meta["coverage"]["aim_l1_fixed_nonblank_after"]

    # DESC master sync targets = filled + already-same (from changes log + proposal)
    import pandas as pd
    changes = pd.read_csv(REL / "aim_pn_classification_release_2026-10-07.changes.csv",
                          dtype=str, keep_default_na=False)
    desc_from_log = sorted({
        r for r in changes.loc[changes.change_group == "D1_desc_proven", "part_number"]
    })
    # already-same: on DESC propose and release, not in change log for AIM
    desc = pd.read_csv(
        REL / "next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv",
        dtype=str, keep_default_na=False,
    )
    rel = pd.read_csv(OUT, dtype=str, keep_default_na=False,
                      usecols=["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
    rmap = rel.set_index("part_number")
    already_same = []
    for _, r in desc.iterrows():
        pn = mod.pad(r["part_number"])
        if pn not in rmap.index:
            continue
        cur = (rmap.at[pn, "aim_l1_fixed"], rmap.at[pn, "aim_l2_fixed"], rmap.at[pn, "aim_l3_fixed"])
        tgt = (r["propose_aim_l1"], r["propose_aim_l2"], r["propose_aim_l3"])
        if cur == tgt and pn not in set(desc_from_log):
            already_same.append(pn)
    desc_for_master = sorted(set(desc_from_log) | set(already_same))

    # engine gasket PNs from 2026-10-04 change log
    chg04 = pd.read_csv(REL / "aim_pn_classification_release_2026-10-04.changes.csv",
                        dtype=str, keep_default_na=False)
    eng_gasket_pns = sorted({
        mod.pad(r["part_number"]) for _, r in chg04.iterrows()
        if r["change_group"] == "D2_engine_gasket_sets" and r["column"] == "aim_l1_fixed"
    })

    print(f"desc_for_master={len(desc_for_master)} (log {len(desc_from_log)} + same {len(already_same)})")
    print(f"eq_added={len(eq_added)} eng_gasket_check={len(eng_gasket_pns)}")

    return mod.apply_approved(
        out_sha, desc_for_master, eq_added, [], cov_before, cov_after,
        desc_filled_n=desc_filled_n, desc_same_n=desc_same_n,
        eq_skipped_n=eq_skipped_n, eng_gasket_pns=eng_gasket_pns,
    )


if __name__ == "__main__":
    sys.exit(main())
