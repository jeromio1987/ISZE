"""Snapshot urea capture per market/year before the AdBlue factor change.

Run before the edit; write to _urea_before.json. Same script run after the rebuild gives the
after-state, and _urea_compare.py prints the before/after table.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM_DER = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived"
BUILD = Path(__file__).resolve().parent


def find_capture() -> Path:
    for p in (DER / "pms_capture_by_db_year.csv", PRISM_DER / "pms_capture_by_db_year.csv"):
        if p.is_file():
            return p
    sys.exit("pms_capture_by_db_year.csv not found")


def main(tag: str) -> int:
    src = find_capture()
    cap = pd.read_csv(src)
    tot = cap[cap.line_type == "total"]
    urea = tot[tot.pms_category == "urea_filter"]

    out = {
        "source_file": str(src),
        "rows_total": int(len(cap)),
        "urea": {
            f"{r.distributor_code}|{int(r.year)}": {
                "expected_qty": round(float(r.expected_qty), 3),
                "actual_qty": round(float(r.actual_qty), 3),
                "capture": (round(float(r.capture_rate), 6) if pd.notna(r.capture_rate) else None),
                "gap_eur": round(float(r.revenue_gap_eur), 2),
            }
            for r in urea.itertuples()
        },
        "market_year_capture": {
            f"{r.distributor_code}|{int(r.year)}": round(float(r.capture_rate), 6)
            for r in tot.itertuples()
            if pd.notna(r.capture_rate)
        },
        "network_expected_urea": round(float(urea.expected_qty.sum()), 3),
        "network_gap_urea_eur": round(float(urea.revenue_gap_eur.sum()), 2),
        "network_expected_all": round(float(tot.expected_qty.sum()), 3),
        "network_gap_all_eur": round(float(tot.revenue_gap_eur.sum()), 2),
    }

    dest = BUILD / f"_urea_{tag}.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("source_file", "rows_total", "network_expected_urea",
                                          "network_gap_urea_eur", "network_expected_all",
                                          "network_gap_all_eur")}, indent=1))
    print("written ->", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "before"))
