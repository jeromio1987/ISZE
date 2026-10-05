"""Capture a state file so before/after can be compared on the same build path, not on a mixed file."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BUILD = Path(__file__).resolve().parent
PRISM_DER = ROOT / "03_analytics" / "Isuzu" / "prism" / "evidence-app" / "data" / "derived"

DERIVED_SOURCES = [
    ("pms_capture_by_db_year.csv", DER),
    ("pms_summary_by_db.csv", DER),
    ("pms_tonnage_model.csv", DER),
    ("pms_opportunity_matrix.csv", PRISM_DER),
]


def main(tag: str) -> int:
    state: dict = {"tag": tag, "files": {}}
    for name, folder in DERIVED_SOURCES:
        p = folder / name
        if not p.is_file():
            state["files"][name] = None
            continue
        shutil.copy2(p, BUILD / f"_state_{tag}_{name}")
        df = pd.read_csv(p)
        entry = {"path": str(p), "rows": int(len(df)), "bytes": p.stat().st_size,
                 "mtime": pd.Timestamp(p.stat().st_mtime, unit="s").isoformat()}
        if "line_type" in df.columns:
            tot = df[df.line_type == "total"]
            entry["total_rows"] = int(len(tot))
            entry["expected_sum"] = round(float(tot.expected_qty.sum()), 4) if "expected_qty" in tot else None
            entry["gap_sum"] = round(float(tot.revenue_gap_eur.sum()), 4) if "revenue_gap_eur" in tot else None
            if "pms_category" in tot.columns:
                urea = tot[tot.pms_category == "urea_filter"]
                entry["urea_expected"] = round(float(urea.expected_qty.sum()), 4)
                entry["urea_gap"] = round(float(urea.revenue_gap_eur.sum()), 4)
                entry["per_cat_expected"] = {
                    k: round(float(v), 4)
                    for k, v in tot.groupby("pms_category").expected_qty.sum().items()
                }
        state["files"][name] = entry

    out = BUILD / f"_state_{tag}.json"
    out.write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(json.dumps(state["files"], indent=1)[:4000])
    print("written ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "x"))
