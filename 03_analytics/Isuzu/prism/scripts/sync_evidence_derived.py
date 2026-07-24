#!/usr/bin/env python3
"""Copy Data/derived feeds into evidence-app/data/derived for portable SQL paths."""
from __future__ import annotations

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
    "tender_pipeline.csv",
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


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in NEEDED:
        src = DERIVED_DIR / name
        if src.exists():
            shutil.copy2(src, DEST / name)
            copied += 1
    print(f"sync_evidence_derived: {copied} files -> {DEST}", flush=True)

    rel = "data/derived"
    for sql in SOURCES.glob("*.sql"):
        text = sql.read_text(encoding="utf-8")
        new = _ABS_DERIVED_RE.sub(lambda m: f"{m.group(1)}('{rel}/{m.group(2)}')", text)
        if new != text:
            sql.write_text(new, encoding="utf-8")
    print("sync_evidence_derived: SQL paths -> data/derived/", flush=True)


if __name__ == "__main__":
    main()
