"""Re-test the headline numbers that `00_derived/*.meta.json` sidecars claim.

A meta sidecar records what a builder measured. Nothing re-tests it, so when a
partner CSV is regenerated and its sidecar is not, the stale number keeps being
quoted — that is exactly how the fig-key dimension drifted out of step with the
IE40 pull (`FIG_KEY_PR00_AUDIT_20260827.md`).

Design note: checks are **declared, never guessed**. Sidecars legitimately mix
current-file measurements with historical context — `no_pr00_gap_cy2025_ranked`
carries both `remaining_pn` (31, the rows in the CSV) and `pn_count` (251, the
original 2026-08-01 measurement). A checker that assumed every count describes
the partner file would fire on the second one and be wrong. So each check below
names the meta key, the file, and the operation that should reproduce it.

Read-only. Exits non-zero when a claim no longer reproduces.

Usage:
    python 01_data/91_build/verify_derived_meta.py [--quiet]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parents[2] / "04_tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import DERIVED_DIR  # noqa: E402

# (meta file, meta key, partner file, operation, column)
#   rows  — number of rows in the partner file
#   sum   — sum of `column`
#   count_positive — rows where `column` > 0
CHECKS: list[tuple[str, str, str, str, str | None]] = [
    ("pn_supersession_map", "pn_count", "pn_supersession_map.csv", "rows", None),
    ("pn_supersession_map", "billed_on_old_pn_eur", "pn_supersession_map.csv",
     "sum", "billed_on_old_pn_eur"),
    ("supersession_billing_delta", "map_rows", "supersession_billing_delta.csv",
     "rows", None),
    ("supersession_billing_delta", "still_billing_old", "supersession_billing_delta.csv",
     "count_positive", "old_bill_eur_l12m"),
    ("supersession_billing_delta", "old_pn_eur_total", "supersession_billing_delta.csv",
     "sum", "old_bill_eur_l12m"),
    ("no_pr00_gap_cy2025_ranked", "remaining_pn", "no_pr00_gap_cy2025_ranked.csv",
     "rows", None),
    ("no_pr00_gap_cy2025_ranked", "remaining_eur", "no_pr00_gap_cy2025_ranked.csv",
     "sum", "cy2025_eur"),
    ("lubricant_sku_audit", "uncovered_pns", "lubricant_sku_audit_uncovered.csv",
     "rows", None),
    ("lubricant_sku_audit", "uncovered_eur", "lubricant_sku_audit_uncovered.csv",
     "sum", "eur"),
    ("fig_key_pr00_audit", "unexplained_drift", "fig_key_pr00_disagreements.csv",
     "rows", None),
]

TOLERANCE = 0.01  # euro rounding


def _load(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    skipped: list[str] = []
    passed = 0

    for meta_name, key, partner_name, op, column in CHECKS:
        meta_path = DERIVED_DIR / f"{meta_name}.meta.json"
        partner_path = DERIVED_DIR / partner_name
        label = f"{meta_name}.{key}"

        if not meta_path.exists() or not partner_path.exists():
            skipped.append(f"{label} — file absent (gitignored or not built here)")
            continue

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if key not in meta:
            failures.append(f"{label}: key missing from the sidecar")
            continue

        frame = _load(partner_path)
        if column and column not in frame.columns:
            failures.append(f"{label}: {partner_name} has no column '{column}'")
            continue

        if op == "rows":
            actual: float = float(len(frame))
        elif op == "sum":
            actual = float(frame[column].sum())
        elif op == "count_positive":
            actual = float((frame[column] > 0).sum())
        else:  # pragma: no cover
            failures.append(f"{label}: unknown operation '{op}'")
            continue

        claimed = float(meta[key])
        if abs(actual - claimed) > TOLERANCE:
            failures.append(
                f"{label}: sidecar says {claimed:,.2f}, {partner_name} gives "
                f"{actual:,.2f} ({op}{f' of {column}' if column else ''}) — "
                "rebuild the sidecar or re-check the data"
            )
        else:
            passed += 1
            if not args.quiet:
                print(f"  OK   {label:52} {actual:,.2f}")

    if not args.quiet:
        print(f"\nderived meta check — {passed} passed, {len(failures)} failed, "
              f"{len(skipped)} skipped")
        for item in skipped:
            print(f"  SKIP {item}")

    if failures:
        print(f"\nFAIL — {len(failures)} sidecar claim(s) no longer reproduce:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("\nOK — every declared sidecar claim reproduces from its data file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
