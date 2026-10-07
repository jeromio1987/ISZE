# -*- coding: utf-8 -*-
"""U26 / agent E -- read both coverage builds back from disk and write the
before/after table. Euros first, rows second, per market and family.

Outputs:
  _u26/E/before_after_20261006_vs_20261007.csv
  _u26/E/before_after_20261006_vs_20261007.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "01_data" / "00_derived"
OUT = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "E"


def load(tag: str):
    cov = pd.read_csv(D / f"market_data_gap_coverage_{tag}.csv", dtype={"part_number": str})
    emp = pd.read_csv(D / f"market_data_gap_empty_pns_{tag}.csv",
                      dtype={"part_number": str})
    return cov, emp


def main() -> int:
    rows = []
    for tag in ("20261006", "20261007"):
        cov, emp = load(tag)
        for market in ("UK", "PT"):
            for fam in ("brake_pad", "oil_filter"):
                c = cov[(cov["market"] == market) & (cov["pms_category"] == fam)]
                e = emp[(emp["market"] == market) & (emp["pms_category"] == fam)]
                rows.append({
                    "build": tag,
                    "market": market,
                    "family": fam,
                    "billed_eur_empty_numbers": round(
                        float(e["eur_all_billed_all_markets"].fillna(0).sum()), 2),
                    "empty_numbers": int(len(e)),
                    "numbers_with_a_row": int(c["part_number"].nunique()),
                    "ledger_rows": int(c["ledger_rows"].sum()),
                    "eligible_rows": int(c["eligible_count"].sum()),
                })
    df = pd.DataFrame(rows)
    out_csv = OUT / "before_after_20261006_vs_20261007.csv"
    df.sort_values(["market", "family", "build"]).to_csv(out_csv, index=False)

    summary = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": {
            "coverage_20261006": "01_data/00_derived/market_data_gap_coverage_20261006.csv",
            "coverage_20261007": "01_data/00_derived/market_data_gap_coverage_20261007.csv",
            "empty_20261006": "01_data/00_derived/market_data_gap_empty_pns_20261006.csv",
            "empty_20261007": "01_data/00_derived/market_data_gap_empty_pns_20261007.csv",
        },
        "per_build": df.to_dict(orient="records"),
    }
    for market in ("UK", "PT"):
        for tag in ("20261006", "20261007"):
            sub = df[(df["market"] == market) & (df["build"] == tag)]
            summary[f"{market}_{tag}"] = {
                "numbers_still_empty": int(sub["empty_numbers"].sum()),
                "billed_eur_of_empty_numbers": round(
                    float(sub["billed_eur_empty_numbers"].sum()), 2),
                "numbers_with_a_row": int(sub["numbers_with_a_row"].sum()),
                "ledger_rows_on_focus_numbers": int(sub["ledger_rows"].sum()),
                "eligible_rows": int(sub["eligible_rows"].sum()),
                "by_family": sub.to_dict(orient="records"),
            }
    out_json = OUT / "before_after_20261006_vs_20261007.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k.startswith(("UK", "PT"))},
                     indent=2))
    print("WROTE", out_csv)
    print("WROTE", out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
