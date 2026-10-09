"""Build CLEAN tranche-1 proposal CSV from Shard A findings. Proposal only — no release."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SRC = ROOT / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_2026-10-07.csv"
FINDINGS = ROOT / "01_data/91_build/_aim_tranche1_findings_20261007.json"
OUT_CSV = ROOT / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_CLEAN_2026-10-07.csv"
OUT_SUM = ROOT / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_CLEAN_2026-10-07.summary.json"

MASTER_ROWS = 165_310
BASE_WITH_FAMILY = 21_045

HARD_HOLDS = {
    ("Repair parts > Gaskets / seals > Gasket set", "Transmission"),
    ("High value repair > Transmission parts > Transmission assembly", "Literature Marketing"),
    ("Competitive parts > Air system > Air valve", "Steering"),
}


def main() -> None:
    findings = json.loads(FINDINGS.read_text(encoding="utf-8"))
    exclude_keys = {
        (f["cat_path"], f["propose_aim_l1"]): {
            "n_expected": f["n"],
            "agree_share": f["agree_share"],
            "confidence": f["confidence"],
            "reasons": f["reasons"],
        }
        for f in findings["flags"]
    }

    df = pd.read_csv(SRC)
    n_before = len(df)

    mask_excl = df.apply(
        lambda r: (r["cat_path"], r["propose_aim_l1"]) in exclude_keys, axis=1
    )
    excluded = df[mask_excl]
    clean = df[~mask_excl].copy()

    excluded_paths = []
    for (cat_path, propose), meta in sorted(
        exclude_keys.items(), key=lambda x: -x[1]["n_expected"]
    ):
        n = int(
            ((excluded["cat_path"] == cat_path) & (excluded["propose_aim_l1"] == propose)).sum()
        )
        excluded_paths.append(
            {
                "cat_path": cat_path,
                "propose_aim_l1": propose,
                "n": n,
                "n_expected_from_findings": meta["n_expected"],
                "agree_share": meta["agree_share"],
                "confidence": meta["confidence"],
                "reasons": meta["reasons"],
                "hold_class": (
                    "hard_hold"
                    if (cat_path, propose) in HARD_HOLDS
                    else "thin_agreement_large_volume"
                ),
            }
        )

    n_after = len(clean)
    n_excluded = len(excluded)
    assert n_before == n_after + n_excluded
    assert n_excluded == findings["flagged_rows"], (n_excluded, findings["flagged_rows"])
    assert n_after == findings["unflagged_clean_rows"], (n_after, findings["unflagged_clean_rows"])

    by_conf = {k: int(v) for k, v in clean["confidence"].value_counts().to_dict().items()}
    top_l1 = {k: int(v) for k, v in clean["propose_aim_l1"].value_counts().head(20).to_dict().items()}

    with_family_if_applied = BASE_WITH_FAMILY + n_after
    with_family_pct = round(100.0 * with_family_if_applied / MASTER_ROWS, 2)
    without_family = MASTER_ROWS - with_family_if_applied

    clean.to_csv(OUT_CSV, index=False)

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source_proposal_csv": str(SRC),
        "findings_json": str(FINDINGS),
        "clean_proposal_csv": str(OUT_CSV),
        "apply": (
            "NO — proposal only. CLEAN subset for Jerome OK before any dated release. "
            "Does not write aim_master."
        ),
        "rows_before": n_before,
        "rows_after": n_after,
        "rows_excluded": n_excluded,
        "excluded_paths": excluded_paths,
        "hard_hold_rows": sum(p["n"] for p in excluded_paths if p["hold_class"] == "hard_hold"),
        "thin_agreement_large_volume_rows": sum(
            p["n"] for p in excluded_paths if p["hold_class"] == "thin_agreement_large_volume"
        ),
        "by_confidence_clean": by_conf,
        "top_propose_l1_clean": top_l1,
        "coverage_if_clean_applied": {
            "master_rows": MASTER_ROWS,
            "base_with_family": BASE_WITH_FAMILY,
            "base_with_family_pct": round(100.0 * BASE_WITH_FAMILY / MASTER_ROWS, 2),
            "clean_rows_added": n_after,
            "with_family_if_applied": with_family_if_applied,
            "with_family_pct_if_applied": with_family_pct,
            "without_family_if_applied": without_family,
            "note": "Projected only — CLEAN not applied to master.",
        },
        "notes": [
            "Excludes all 7 Shard A flagged cat_path×propose_aim_l1 pairs "
            "(3 hard holds + 4 thin-agreement 90–95% large-volume).",
            "Original tranche1 CSV untouched.",
            "Matches findings unflagged_clean_rows=38213.",
        ],
    }

    OUT_SUM.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("BEFORE", n_before)
    print("AFTER", n_after)
    print("EXCLUDED", n_excluded)
    print("COVERAGE", with_family_if_applied, "/", MASTER_ROWS, f"({with_family_pct}%)")
    for p in excluded_paths:
        print(
            f"  EXCL {p['n']:5d}  {p['hold_class']:28s}  "
            f"{p['cat_path']} -> {p['propose_aim_l1']}"
        )
    print("WROTE", OUT_CSV)
    print("WROTE", OUT_SUM)
    orig_n = len(pd.read_csv(SRC))
    assert orig_n == 49208
    print("ORIGINAL_UNCHANGED", orig_n)


if __name__ == "__main__":
    main()
