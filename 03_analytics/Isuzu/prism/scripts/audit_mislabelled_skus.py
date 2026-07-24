#!/usr/bin/env python3
"""Flag likely mislabelled part descriptions (e.g. oil sold as 'Rim')."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, SALES_FACT_PARQUET  # noqa: E402

OUT_CSV = DERIVED_DIR / "mislabelled_sku_audit.csv"

OIL_PAT = re.compile(
    r"\b(15W40|10W40|5W30|CK4|CJ-4|ENGINE\s*OIL|MOTOR\s*OIL|LUBRICANT|SAE\s*\d)",
    re.I,
)
RIM_PAT = re.compile(r"\bRIM\b", re.I)
BRAKE_PAT = re.compile(r"\b(BRK|BRAKE|DISC\s*BRK|PAD\s*KIT)\b", re.I)


def main() -> int:
    if not SALES_FACT_PARQUET.exists():
        print("Run build_sales_fact_from_cy.py first", flush=True)
        return 1

    df = pd.read_parquet(SALES_FACT_PARQUET)
    df["desc_u"] = df["description"].fillna("").astype(str)
    df["rev"] = pd.to_numeric(df["net_sales_value"], errors="coerce").fillna(0)
    df["qty"] = pd.to_numeric(df["billed_qty"], errors="coerce").fillna(0)

    flags: list[dict] = []
    for _, r in df.groupby("part_number", as_index=False).agg(
        description=("description", "first"),
        rev=("rev", "sum"),
        qty=("qty", "sum"),
        lines=("part_number", "count"),
    ).iterrows():
        d = str(r["description"])
        du = d.upper()
        issue = None
        if RIM_PAT.search(du) and OIL_PAT.search(du):
            issue = "rim_keyword_but_oil_spec"
        elif RIM_PAT.search(du) and not re.search(r"\bWHEEL\b", du, re.I):
            if OIL_PAT.search(du):
                issue = "rim_keyword_but_oil_spec"
        if issue:
            flags.append(
                {
                    "part_number": r["part_number"],
                    "description": d,
                    "issue": issue,
                    "rev_eur": round(float(r["rev"]), 2),
                    "qty": round(float(r["qty"]), 1),
                    "lines": int(r["lines"]),
                }
            )

    out = pd.DataFrame(flags).sort_values("rev_eur", ascending=False)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"Mislabelled SKU candidates: {len(out):,} -> {OUT_CSV}")
    if not out.empty:
        print(out.head(15).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
