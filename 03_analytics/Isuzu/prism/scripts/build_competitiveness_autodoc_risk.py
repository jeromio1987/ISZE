#!/usr/bin/env python3
"""Class C / Autodoc substitution risk: competitor price < 75% of PR00 list."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import AUTODOC_SCRAPER_DIR, DERIVED_DIR  # noqa: E402

OUT_CSV = DERIVED_DIR / "competitiveness_autodoc_risk.csv"
AUTODOC_CANDIDATES = [
    AUTODOC_SCRAPER_DIR / "autodoc_results.csv",
    AUTODOC_SCRAPER_DIR / "_HANDOFF_BUNDLE" / "autodoc_results.csv",
]
THRESHOLD = 0.75
GBP_EUR = 1.17


def _resolve_autodoc() -> Path | None:
    for p in AUTODOC_CANDIDATES:
        if p.is_file():
            return p
    return None


def main() -> int:
    src = _resolve_autodoc()
    if not src:
        print("autodoc_results.csv not found", flush=True)
        return 1

    df = pd.read_csv(src, dtype=str)
    df["pn"] = df["PN"].astype(str).str.strip().str.lstrip("0")
    pr00 = pd.to_numeric(df.get("PR00_EUR"), errors="coerce")
    ad_min_gbp = pd.to_numeric(df.get("Autodoc_MinPrice_GBP"), errors="coerce")
    ad_min_eur = ad_min_gbp * GBP_EUR
    df["pr00_eur"] = pr00
    df["autodoc_min_eur"] = ad_min_eur
    df["ratio"] = np.where(pr00 > 0, ad_min_eur / pr00, np.nan)
    df["class_c_substitution"] = (df["ratio"] < THRESHOLD) & df["ratio"].notna()
    df["aim_class"] = df.get("Class", "")
    df["aim_category"] = df.get("AIM_Category", "")

    out = df[
        df["class_c_substitution"]
        & df["Autodoc_ResultCount"].fillna("0").astype(str).str.isdigit()
    ].copy()
    out = out.sort_values("ratio")
    cols = [
        "pn",
        "Description",
        "pr00_eur",
        "autodoc_min_eur",
        "ratio",
        "aim_class",
        "aim_category",
        "Rev_CY2025_EUR",
        "Autodoc_CheapestBrand",
    ]
    cols = [c for c in cols if c in out.columns]
    out = out[cols].rename(columns={"pn": "part_number", "Description": "description"})

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"  -> {len(out):,} Class-C Autodoc flags -> {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
