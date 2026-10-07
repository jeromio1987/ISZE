#!/usr/bin/env python3
"""Finish approve + master sync for release 2026-10-07 already cut as PENDING_APPROVAL."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build")
REL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_releases")
OUT = REL / "aim_pn_classification_release_2026-10-07.csv"
META = OUT.with_suffix(".meta.json")
VERIFY = BUILD / "verify_aim_classification.py"


def main() -> int:
    # Re-run gate in candidate mode (house method for PENDING_APPROVAL)
    rc = os.system(f'python "{VERIFY}" --candidate --file "{OUT}"')
    print(f"gate exit {rc >> 8}")

    meta = json.loads(META.read_text(encoding="utf-8"))
    out_sha = meta["sha256"]
    ch = meta["changes_vs_base"]
    desc_filled = ch["desc_aim_filled"]
    desc_same = ch["desc_already_same"]
    eq_added = ch["rows_added"]
    eq_skipped = ch["eq_skipped"]
    cov_before = meta["coverage"]["aim_l1_fixed_nonblank_before"]
    cov_after = meta["coverage"]["aim_l1_fixed_nonblank_after"]

    # Load apply_approved from the builder
    spec = importlib.util.spec_from_file_location(
        "rel20261007", BUILD / "build_aim_classification_release_20261007.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    # DESC PNs for master: all with aim from release in change log D1 + already_same
    # Rebuild from release + proposal
    import pandas as pd

    def pad(k: str) -> str:
        k = (k or "").strip()
        return k.zfill(10) if k.isdigit() else k

    rel = pd.read_csv(OUT, dtype=str, keep_default_na=False)
    desc = pd.read_csv(
        REL / "next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv",
        dtype=str, keep_default_na=False,
    )
    raim = rel.set_index(rel["part_number"].map(pad))
    desc_for_master = []
    for _, r in desc.iterrows():
        pn = pad(r["part_number"])
        tgt = (r["propose_aim_l1"], r["propose_aim_l2"], r["propose_aim_l3"])
        cur = tuple(raim.at[pn, c] for c in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"))
        if cur == tgt:
            desc_for_master.append(pn)

    print(f"desc_for_master={len(desc_for_master)} (expect ~{desc_filled + desc_same})")
    return mod.apply_approved(
        out_sha, desc_for_master, eq_added, [], cov_before, cov_after,
        desc_filled_n=desc_filled, desc_same_n=desc_same, eq_skipped_n=eq_skipped,
        eng_gasket_pns=ch.get("preserved_engine_gasket_sets"),
    )


if __name__ == "__main__":
    sys.exit(main())
