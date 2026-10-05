#!/usr/bin/env python3
"""Copy Data/derived feeds into evidence-app/data/derived for portable SQL paths.

Tender is the exception. The evidence-app tender page used to read a copy of the
flattened Data/derived/tender_pipeline.csv (last built 29 May 2026); that table
is superseded and its counts (400 actionable, 352 R&M) disagree with the live
feed (281 and 279). This script therefore does not copy it any more. It writes
``tender_feed.csv`` inside evidence-app instead, produced by PRISM's own feed
reader, so the app and the PRISM tender page show the same numbers.

The old table and its builder are both kept on disk.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR  # noqa: E402

EVIDENCE = PRISM_ROOT / "evidence-app"
DEST = EVIDENCE / "data" / "derived"
SOURCES = EVIDENCE / "sources" / "prism"

# Name of the tender file written into the app. The source SQL points here.
TENDER_CSV = "tender_feed.csv"

NEEDED = [
    "gps_spu_by_distributor.csv",
    "pms_capture_by_db_year.csv",
    "sales_fact.parquet",
    "bvp_pn_dimension.csv",
    "demand_classification.csv",
    "vor_airfreight_risk.csv",
    "ituk_pms_pn_audit.csv",
    "db_aftersales_risk.csv",
    "bvp_downtrade_gp.csv",
    # "tender_pipeline.csv" deliberately removed - superseded, see module docstring.
    "substitution_by_db_year.csv",
    "vor_profile.csv",
    "aim_exposure_by_db_year.csv",
    "db_parts_mix_classification.csv",
    "db_parts_mix_classification.parquet",
    "eucon_price_gap.csv",
    "_aim_gap_top50.csv",
    "aim_bvp_family_risk.csv",
    "aim_gap_suggestions_20260522.csv",
    "basket_correlation.csv",
    "network_percentile.csv",
    "part_lifecycle.csv",
    "vor_seasonality.csv",
    "substitution_timeline.csv",
    "mix_genuine_bvp_by_family.csv",
    "revenue_waterfall.csv",
    "revenue_concentration.csv",
    "capture_recovery_model.csv",
    "pms_opportunity_matrix.csv",
    "pms_summary_by_db.csv",
    "_gps_integrity_audit_rows.csv",
    "price_premium.csv",
    "vor_willingness_to_pay.csv",
]

_ABS_DERIVED_RE = re.compile(
    r"(read_csv_auto|read_parquet)\('(?:[A-Za-z]:/)?(?:[^']*/)?(?:Data|01_data)/derived/([^']+)'\)"
)


def write_tender_feed() -> dict:
    """Flatten the live tender feed into the app.

    The rows and columns come from ``modules.tender_feed``, the one reader of
    ``01_data/14_dashboards/tender_data.json``. Nothing here re-parses the JSON
    or re-derives what counts as actionable, so the app cannot drift from the
    PRISM tender page.
    """
    from modules.tender_feed import coverage as feed_coverage
    from modules.tender_feed import feed_generated_at, load_feed

    df, meta = load_feed()
    drop = [c for c in ("notices", "aftersales_evidence", "score_drivers") if c in df.columns]
    df = df.drop(columns=drop)
    out = DEST / TENDER_CSV
    df.to_csv(out, index=False, encoding="utf-8", lineterminator="\n")
    cov = feed_coverage(df)
    return {
        "file": TENDER_CSV,
        "source": "01_data/14_dashboards/tender_data.json",
        "generated_at": feed_generated_at(meta),
        "rows": int(len(df)),
        "actionable": int(df["actionable"].sum()),
        "rm_contract": int(df["rm_contract"].sum()),
        "coverage": cov,
    }


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in NEEDED:
        src = DERIVED_DIR / name
        if src.exists():
            shutil.copy2(src, DEST / name)
            copied += 1

    stats = write_tender_feed()
    # Written without BOM; the page reads it, the JSON beside it is for the report.
    (DEST / "tender_feed.meta.json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"sync_evidence_derived: {copied} files -> {DEST}", flush=True)
    print(f"sync_evidence_derived: tender -> {stats['file']} "
          f"({stats['rows']} rows, {stats['actionable']} actionable, "
          f"{stats['rm_contract']} R&M, feed {stats['generated_at']})", flush=True)

    rel = "data/derived"
    for sql in SOURCES.glob("*.sql"):
        text = sql.read_text(encoding="utf-8")
        new = _ABS_DERIVED_RE.sub(lambda m: f"{m.group(1)}('{rel}/{m.group(2)}')", text)
        if new != text:
            sql.write_text(new, encoding="utf-8")
    print("sync_evidence_derived: SQL paths -> data/derived/", flush=True)


if __name__ == "__main__":
    main()
