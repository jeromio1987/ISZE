"""Audit parts_catalog_dimension.fig_key against the current SAP IE40 PR00 extract.

Read-only. Answers two questions the fig-key V2 roadmap item leaves open:

  1. How many catalogue PNs still have a blank ``fig_key`` that the SAP
     ``fig_no`` / ``key_no`` columns could fill today?
  2. Where both sides carry a figure, do they agree? Disagreement means the
     dimension was built from an older IE40 pull than the one on disk.

``fig_key`` is the composite ``<fig_no>-<key_no>`` (e.g. ``130-006``).

Supersession is ruled out explicitly: a PN whose catalogue figure matches its
``newest_pn`` figure is counted as explained, not as drift.

Writes a JSON summary + the disagreeing rows as CSV next to the other derived
audits. It does NOT rebuild the dimension — that is
``prism/scripts/build_pr00_classification.py`` +
``build_fig_key_dimension.py`` followed by ``run_pipeline_and_verify.ps1``.

Usage:
    python 01_data/91_build/audit_fig_key_vs_pr00.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parents[2] / "04_tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import DERIVED_DIR  # noqa: E402

CATALOGUE = DERIVED_DIR / "parts_catalog_dimension.parquet"
PR00 = DERIVED_DIR / "pricing_pr00_ie40.parquet"
OUT_JSON = DERIVED_DIR / "fig_key_pr00_audit.json"
OUT_CSV = DERIVED_DIR / "fig_key_pr00_disagreements.csv"


def _filled(series: pd.Series) -> pd.Series:
    """True where the value is a real string, not NaN / blank / literal 'nan'."""
    text = series.astype(str).str.strip()
    return (series.notna() & (text != "") & (text.str.lower() != "nan")).astype(bool)


def main() -> int:
    pr00 = pd.read_parquet(PR00)
    catalogue = pd.read_parquet(CATALOGUE)

    pr00["pn"] = pr00["part_number"].astype(str).str.strip()
    pr00["newest"] = pr00["newest_pn"].astype(str).str.strip()
    pr00["sap_fig_key"] = (
        pr00["fig_no"].astype(str).str.strip() + "-" + pr00["key_no"].astype(str).str.strip()
    )
    catalogue["pn"] = catalogue["part_number"].astype(str).str.strip()
    catalogue["fk"] = catalogue["fig_key"].astype(str).str.strip()
    catalogue["has_fig_key"] = _filled(catalogue["fig_key"])

    sap = pr00.loc[
        _filled(pr00["fig_no"]) & _filled(pr00["key_no"]),
        ["pn", "newest", "sap_fig_key", "is_superseded_row", "source_file"],
    ]
    joined = sap.merge(
        catalogue[["pn", "fk", "has_fig_key", "classification_source"]], on="pn", how="inner"
    )

    # 1 — fillable blanks
    blank_total = int((~catalogue["has_fig_key"]).sum())
    fillable = joined.loc[~joined["has_fig_key"]]

    # 2 — disagreements, with the supersession route ruled out
    both = joined.loc[joined["has_fig_key"]].copy()
    disagree = both.loc[both["fk"] != both["sap_fig_key"]].copy()
    newest_fig_key = sap.set_index("pn")["sap_fig_key"]
    disagree["newest_sap_fig_key"] = disagree["newest"].map(newest_fig_key)
    disagree["explained_by_supersession"] = disagree["fk"] == disagree["newest_sap_fig_key"]
    drift = disagree.loc[~disagree["explained_by_supersession"]]

    coverage_now = float(catalogue["has_fig_key"].mean())
    coverage_after = float(
        (int(catalogue["has_fig_key"].sum()) + len(fillable)) / len(catalogue)
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "catalogue": CATALOGUE.name,
            "catalogue_pns": int(len(catalogue)),
            "pr00": PR00.name,
            "pr00_source_files": sorted(pr00["source_file"].dropna().unique().tolist()),
            "pr00_pns_with_figure": int(len(sap)),
        },
        "fillable_blanks": {
            "catalogue_fig_key_blank": blank_total,
            "fillable_from_sap": int(len(fillable)),
            "not_fillable": blank_total - int(len(fillable)),
            "coverage_now_pct": round(coverage_now * 100, 2),
            "coverage_after_fill_pct": round(coverage_after * 100, 2),
        },
        "disagreements": {
            "compared": int(len(both)),
            "agree": int(len(both) - len(disagree)),
            "agree_pct": round((1 - len(disagree) / len(both)) * 100, 2) if len(both) else None,
            "disagree": int(len(disagree)),
            "explained_by_supersession": int(disagree["explained_by_supersession"].sum()),
            "unexplained_drift": int(len(drift)),
            "drift_on_non_superseded_pns": int((~drift["is_superseded_row"].astype(bool)).sum()),
            "drift_by_classification_source": drift["classification_source"]
            .value_counts()
            .to_dict(),
        },
        "note": (
            "Drift means the dimension predates the IE40 pull on disk. Fix by re-running "
            "build_pr00_classification.py + build_fig_key_dimension.py, then "
            "run_pipeline_and_verify.ps1 — not by editing the CSV."
        ),
    }

    OUT_JSON.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    drift[
        ["pn", "fk", "sap_fig_key", "is_superseded_row", "classification_source"]
    ].rename(columns={"pn": "part_number", "fk": "catalogue_fig_key"}).to_csv(
        OUT_CSV, index=False
    )

    print(json.dumps(summary, indent=1))
    print(f"\nwrote {OUT_JSON}\nwrote {OUT_CSV}  ({len(drift):,} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
