"""Append the `schema_required:` block to verification_fixtures.yaml.

This workspace cannot truncate-write verification_fixtures.yaml (OSError [Errno 22] Invalid
argument), so the text is appended with open(...,'a') and, where a rewrite is needed, written to a
temp file in the same directory and moved with os.replace().
"""
from __future__ import annotations

import os
from pathlib import Path

FX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\verification_fixtures.yaml")

BLOCK = """
# ---------------------------------------------------------------------------------------------
# Schema guard (added 2026-09-22).
#
# Compares the COLUMNS of the listed derived files against the list below. A column declared here
# and absent from the file is a FAIL, not a warn: unlike staleness (where some delay is
# deliberate), a vanished column is never deliberate and something downstream may already read
# it. Reason it exists: on 2026-09-21 another workstream regenerated gps_spu_by_distributor.csv
# and it silently lost period_basis and coverage_note. Every existing check reads values, so a
# missing column was invisible; it surfaced a day later only when build_lost_sales_model.py
# happened to name period_basis and raised KeyError "['period_basis'] not in index".
#
# Extra columns are reported in the check detail and never fail.
#
# `git_dir` is optional and only powers a second, best-effort arm: anything present in the
# committed version of the file but missing from the working copy is reported too. The declared
# list is the primary mechanism and does NOT need git.
# ---------------------------------------------------------------------------------------------
schema_required:
  # Workspace root, so the git arm can be run without the module guessing.
  repo_root: C:\\Users\\jerom\\Desktop\\claude\\ISZE
  files:
    # The file that lost its columns. Both annotation columns are declared because they are the
    # exact thing that went missing, and both are read by the lost-sales builder.
    - file: gps_spu_by_distributor.csv
      kind: csv
      git_dir: 01_data/00_derived
      required_columns:
        - year
        - distributor_code
        - total_sales_eur
        - uio_units
        - spend_per_unit_eur
        - max_spend_eur
        - gps_capture_vs_max
        - traffic_light_v9
        - period_basis
        - coverage_note

    - file: lost_sales_model.csv
      kind: csv
      git_dir: 01_data/00_derived
      required_columns:
        - distributor_code
        - year
        - pms_category
        - net_sales_eur
        - gap_type
        - gap_eur_at_genuine
        - theoretical_wallet_eur
        - ceiling_qualifier
        - ceilings_are_market_level
        - period_basis
        - gps_capture_vs_max
        - momentum_basis
        - is_partial_year
        - delta_total_eur
        - delta_volume_eur
        - delta_price_eur
        - delta_mix_eur
        - down_trade_verdict

    - file: nseries_tonnage_evolution.csv
      kind: csv
      git_dir: 01_data/00_derived
      required_columns:
        - family_scope
        - clock
        - period
        - distributor_code
        - lane
        - tonnage_band
        - membership
        - sums_to_n_series_total
        - billed_eur
        - units
        - comparable_to_previous

    - file: epc_decode_nseries_banded.csv
      kind: csv
      git_dir: 01_data/00_derived
      required_columns:
        - pn
        - in_n_series_family
        - series_all
        - series_unresolved
        - tonnage_band
        - band_status
        - band_reason
        - eur_2025
        - eur_2026

    # The ITUK / oil-filter and PMS capture lane. A column lost here moves published capture.
    - file: pms_capture_by_db_year.csv
      kind: csv
      git_dir: 01_data/00_derived
      required_columns:
        - year
        - distributor_code
        - pms_category
        - line_type
        - uio_units
        - expected_qty
        - actual_qty
        - capture_rate
        - revenue_gap_eur
        - revenue_gap_quotable

    # The published headline figures other packs quote. The keys of the `metrics` object, not
    # the document root (which is only as_of / generator / metrics).
    - file: metrics_snapshot.json
      kind: json
      key_path: metrics
      git_dir: 01_data/00_derived
      required_columns:
        - sales.parts_base_eur
        - sales.parts_base_data_through
        - sales_fact.rows
        - verify.pass
        - verify.fail
        - verify.generated
        - waterfall.network.wallet_eur_2025
        - waterfall.network.captured_eur_2025
        - waterfall.network.gps_pct_2025
        - ituk.oil_filter.uio_units
        - ituk.oil_filter.expected_qty

    # --- reported by Part 3 of the 2026-09-22 sweep as having shrunk; no column lost, but the
    # --- columns that carry the distinction are the ones worth guarding.
    - file: network_percentile.csv
      kind: csv
      git_dir: 01_data/00_derived
      required_columns:
        - distributor_code
        - year
        - metric
        - raw_value
        - percentile_rank
        - network_median
        - vs_median
        - n_distributors

    - file: bvp_pn_dimension.csv
      kind: csv
      git_dir: 01_data/00_derived
      required_columns:
        - part_number
        - line_type
        - pms_flag
      required_columns_optional: []
"""


def main() -> int:
    text = FX.read_text(encoding="utf-8")
    if "schema_required:" in text:
        print("schema_required already present - nothing appended")
        return 0
    # Append (not truncate) is the operation that works on this file.
    with FX.open("a", encoding="utf-8", newline="") as fh:
        fh.write(BLOCK)
    after = FX.read_text(encoding="utf-8")
    assert "schema_required:" in after, "append did not land"
    print(f"appended schema_required block; file now {len(after)} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
