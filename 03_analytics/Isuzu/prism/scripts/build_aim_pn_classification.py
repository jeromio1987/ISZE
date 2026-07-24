#!/usr/bin/env python3
"""
Build aim_pn_classification.csv — PN → AIM L1/L2/L3 + catalog L1/L2/L3 + filter role.

Run after pr00_classification.csv exists (build_pr00_classification.py).
Optional: aim_gap_suggestions_*.csv for high-confidence gap fill.

  python scripts/build_aim_pn_classification.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import AIM_PN_CLASSIFICATION_CSV, DERIVED_DIR, SALES_FACT_PARQUET  # noqa: E402
from modules.aim_pn_classifier import build_aim_pn_classification  # noqa: E402
from modules.dealer_sales_loader import normalize_pn  # noqa: E402


def _collect_pns() -> tuple[pd.Series, pd.Series]:
    pns: set[str] = set()
    desc_map: dict[str, str] = {}

    if SALES_FACT_PARQUET.exists():
        sf = pd.read_parquet(SALES_FACT_PARQUET)
        if "line_kind" in sf.columns:
            sf = sf[sf["line_kind"] == "part"]
        sf = sf[["part_number", "description"]] if "description" in sf.columns else sf[["part_number"]]
        for _, r in sf.dropna(subset=["part_number"]).iterrows():
            pn = normalize_pn(r["part_number"])
            if pn:
                pns.add(pn)
                if pn not in desc_map and pd.notna(r.get("description")):
                    desc_map[pn] = str(r["description"])

    pr00 = DERIVED_DIR / "pr00_classification.csv"
    if pr00.exists():
        pr = pd.read_csv(pr00, dtype=str)
        for n in pr["pn_norm"].dropna():
            pn = normalize_pn(n.zfill(10) if str(n).isdigit() else n)
            if pn:
                pns.add(pn)

    ordered = sorted(pns)
    return pd.Series(ordered), pd.Series([desc_map.get(p, "") for p in ordered])


def main() -> int:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    pns, descs = _collect_pns()
    if pns.empty:
        print("ERROR: no part numbers found")
        return 1

    df = build_aim_pn_classification(pns, descs)
    df.to_csv(AIM_PN_CLASSIFICATION_CSV, index=False)

    has_aim = df["aim_l1"].notna() & (df["aim_l1"].astype(str).str.strip() != "")
    has_cat = df["catalog_l1"].notna() & (df["catalog_l1"].astype(str).str.strip() != "")
    roles = df["filter_part_role"].notna().sum()
    print(f"  -> {len(df):,} PNs -> {AIM_PN_CLASSIFICATION_CSV.name}")
    print(f"     aim_l1: {has_aim.sum():,} ({has_aim.mean()*100:.1f}%)")
    print(f"     catalog_l1: {has_cat.sum():,} ({has_cat.mean()*100:.1f}%)")
    print(f"     filter_part_role: {roles:,}")
    print("     sources:", df["aim_source"].value_counts().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
