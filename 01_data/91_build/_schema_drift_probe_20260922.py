"""Read-only probe: which tracked derived files lost columns or rows vs git HEAD?

Part 3 of the 2026-09-22 schema-guard task. Writes nothing except its own stdout + a CSV.
"""
from __future__ import annotations

import csv
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = REPO / "01_data" / "91_build" / "_schema_drift_probe_20260922.csv"

# High-value derived files worth inspecting. Kept to workbooks the pipeline publishes.
CANDIDATES = [
    "01_data/00_derived/gps_spu_by_distributor.csv",
    "01_data/00_derived/lost_sales_model.csv",
    "01_data/00_derived/nseries_tonnage_evolution.csv",
    "01_data/00_derived/epc_decode_nseries_banded.csv",
    "01_data/00_derived/pms_capture_by_db_year.csv",
    "01_data/00_derived/pms_summary_by_db.csv",
    "01_data/00_derived/pms_opportunity_matrix.csv",
    "01_data/00_derived/capture_recovery_model.csv",
    "01_data/00_derived/bvp_pn_dimension.csv",
    "01_data/00_derived/genuine_bvp_crossref.csv",
    "01_data/00_derived/parts_catalog_dimension.csv",
    "01_data/00_derived/bvp_addressable_basket.csv",
    "01_data/00_derived/network_percentile.csv",
    "01_data/00_derived/uio_by_market_type_year.csv",
    "01_data/00_derived/vehicle_family_bands.csv",
    "01_data/00_derived/pms_tonnage_model.csv",
    "01_data/00_derived/tonnage_capable_part_numbers.csv",
    "01_data/00_derived/pms_capture_by_family.csv",
    "01_data/00_derived/ituk_pms_pn_audit.csv",
    "01_data/00_derived/sales_by_db_fig_key_year.csv",
    "01_data/00_derived/aim_gps_matrix.csv",
    "01_data/00_derived/aim_exposure_by_db_year.csv",
    "01_data/00_derived/aim_bvp_family_risk.csv",
    "01_data/00_derived/lost_sales_market.csv",
    "01_data/00_derived/lost_sales_pn_action.csv",
    "01_data/00_derived/lost_sales_competitor_coverage.csv",
    "01_data/00_derived/lost_sales_competitor_pn.csv",
    "01_data/00_derived/vor_profile.csv",
    "01_data/00_derived/vor_airfreight_risk.csv",
    "01_data/00_derived/vor_seasonality.csv",
    "01_data/00_derived/capture_trajectory.csv",
    "01_data/00_derived/part_lifecycle.csv",
    "01_data/00_derived/revenue_concentration.csv",
    "01_data/00_derived/revenue_waterfall.csv",
    "01_data/00_derived/price_premium.csv",
    "01_data/00_derived/basket_correlation.csv",
    "01_data/00_derived/substitution_timeline.csv",
    "01_data/00_derived/substitution_by_db_year.csv",
    "01_data/00_derived/substitution_by_pair_year.csv",
    "01_data/00_derived/db_benchmark_mix.csv",
    "01_data/00_derived/db_benchmark_mix_group.csv",
    "01_data/00_derived/db_benchmark_mix_subgroup.csv",
    "01_data/00_derived/mix_genuine_bvp_by_family.csv",
    "01_data/00_derived/mix_genuine_bvp_pms.csv",
    "01_data/00_derived/gps_spu_by_family.csv",
    "01_data/00_derived/gps_spu_pms.csv",
    "01_data/00_derived/pr00_classification.csv",
    "01_data/00_derived/sales_by_db_fig_key_year.csv",
    "01_data/00_derived/metrics_snapshot.json",
]


def git_show(rel: str) -> str | None:
    r = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout if r.returncode == 0 else None


def csv_header_and_rows(text: str) -> tuple[list[str], int]:
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return [], 0
    n = sum(1 for _ in reader)
    return header, n


def main() -> int:
    rows_out = []
    print(f"{'file':58} {'rows HEAD->disk':>18}  lost columns")
    print("-" * 110)
    for rel in CANDIDATES:
        path = REPO / rel
        name = Path(rel).name
        if not path.exists():
            rows_out.append({"file": name, "status": "absent_on_disk",
                             "rows_head": "", "rows_disk": "", "lost_columns": ""})
            print(f"{name:58} {'ABSENT':>18}  -")
            continue
        head_text = git_show(rel)
        if head_text is None:
            rows_out.append({"file": name, "status": "untracked_or_no_head",
                             "rows_head": "", "rows_disk": "", "lost_columns": ""})
            print(f"{name:58} {'UNTRACKED':>18}  -")
            continue

        disk_text = path.read_text(encoding="utf-8", errors="replace")
        if not name.endswith(".csv"):
            rows_out.append({"file": name, "status": "not_csv",
                             "rows_head": "", "rows_disk": "", "lost_columns": ""})
            print(f"{name:58} {'(json - see separate)':>18}  -")
            continue

        hh, hn = csv_header_and_rows(head_text)
        dh, dn = csv_header_and_rows(disk_text)
        lost = [c for c in hh if c not in dh]
        added = [c for c in dh if c not in hh]
        status = "OK"
        if lost:
            status = "COLUMN_LOST"
        elif dn < hn:
            status = "ROWS_SHRANK"
        rows_out.append({
            "file": name, "status": status,
            "rows_head": hn, "rows_disk": dn,
            "lost_columns": "|".join(lost),
            "added_columns": "|".join(added),
        })
        flag = "" if status == "OK" else f"   <== {status}"
        print(f"{name:58} {f'{hn} -> {dn}':>18}  {lost}{flag}")

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "status", "rows_head", "rows_disk",
                                          "lost_columns", "added_columns"], extrasaction="ignore")
        w.writeheader()
        for r in rows_out:
            w.writerow(r)
    print()
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
