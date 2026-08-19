"""P5.1 — monthly demand series by DB × AIM L1 category (deterministic, no model).

Reads  : sales_fact.parquet, distributor_dimension.csv, aim_pn_classification.csv
Writes : 01_data/00_derived/demand_series.parquet (+ .meta.json)

Spec   : 00_docs/P5_FORECAST_BUILD_PLAN.md § Phase 5.1
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import DERIVED_DIR, ISZE_ROOT  # noqa: E402

BUILDER_VERSION = "p5.1-v1"
OUT_PARQUET = DERIVED_DIR / "demand_series.parquet"
OUT_META = DERIVED_DIR / "demand_series.meta.json"

SALES_SRC = DERIVED_DIR / "sales_fact.parquet"
DIM_SRC = DERIVED_DIR / "distributor_dimension.csv"
AIM_SRC = DERIVED_DIR / "aim_pn_classification.csv"

# Mirror prism/modules/sales_loader.py — non-part placeholder PNs
NON_PART_PNS = {
    "TRANSPORT",
    "REBATE",
    "LATEPAYMENTINTEREST",
    "LATE PAYMENT INTEREST",
    "DISRACK01",
    "5874123810",
    "5874123811",
    "5874123812",
}

EXCLUDED_CODES = {
    "GERMANY_SERVICE",
    "MIDI",
    "IML_INTERNAL",
}


def _load_sales() -> pd.DataFrame:
    cols = ["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value", "saty"]
    sf = pd.read_parquet(SALES_SRC, columns=cols)
    sf["billing_date"] = pd.to_datetime(sf["billing_date"], errors="coerce")
    sf = sf.dropna(subset=["billing_date"])

    dim = pd.read_csv(DIM_SRC)
    dim = dim[dim["network_role"].astype(str) == "network_db"][
        ["sold_to_sap", "distributor_code"]
    ].dropna(subset=["distributor_code"])
    dim["sold_to_sap"] = pd.to_numeric(dim["sold_to_sap"], errors="coerce")
    sf["sold_to_sap"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    sf = sf.merge(dim, on="sold_to_sap", how="inner")
    sf = sf.rename(columns={"distributor_code": "db_code"})
    sf = sf[~sf["db_code"].isin(EXCLUDED_CODES)]

    pn = sf["part_number"].astype(str).str.strip().str.upper()
    sf = sf[~pn.isin(NON_PART_PNS)]

    saty = sf["saty"].astype(str).str.strip().str.upper() if "saty" in sf.columns else ""
    is_cr_re = saty.isin(["CR", "RE"]) if isinstance(saty, pd.Series) else False
    sf = sf[(sf["net_sales_value"].fillna(0) >= 0) & ~is_cr_re]

    sf["billed_qty"] = pd.to_numeric(sf["billed_qty"], errors="coerce").fillna(0)
    sf = sf[sf["billed_qty"] != 0]

    sf["pn"] = pn
    sf["year_month"] = sf["billing_date"].dt.to_period("M").astype(str)
    return sf


def _load_categories() -> pd.Series:
    aim = pd.read_csv(AIM_SRC, usecols=["part_number", "aim_l1"], dtype=str)
    aim["pn"] = aim["part_number"].astype(str).str.strip().str.upper()
    return aim.drop_duplicates("pn").set_index("pn")["aim_l1"]


def build() -> tuple[pd.DataFrame, dict]:
    sf = _load_sales()
    cats = _load_categories()
    sf["category"] = sf["pn"].map(cats).fillna("UNCLASSIFIED")

    agg = (
        sf.groupby(["db_code", "category", "year_month"], as_index=False)
        .agg(
            units_sold=("part_number", "size"),
            revenue=("net_sales_value", "sum"),
        )
    )
    agg["revenue"] = agg["revenue"].round(2)

    series_stats = (
        agg[agg["units_sold"] > 0]
        .groupby(["db_code", "category"], as_index=False)
        .agg(
            first_seen=("year_month", "min"),
            last_seen=("year_month", "max"),
            nonzero_months=("year_month", "nunique"),
        )
    )
    series_stats["sparse_flag"] = series_stats["nonzero_months"] < 3

    out = agg.merge(
        series_stats.drop(columns=["nonzero_months"]),
        on=["db_code", "category"],
        how="left",
    )
    produced = datetime.now(timezone.utc)
    out["produced_at"] = produced.isoformat(timespec="seconds")
    out["builder_version"] = BUILDER_VERSION

    meta = {
        "generated_at": produced.isoformat(timespec="seconds"),
        "builder_version": BUILDER_VERSION,
        "rows": int(len(out)),
        "series": int(out[["db_code", "category"]].drop_duplicates().shape[0]),
        "distributors": int(out["db_code"].nunique()),
        "categories": int(out["category"].nunique()),
        "months": sorted(out["year_month"].unique().tolist()),
        "billing_window": {
            "from": sf["billing_date"].min().date().isoformat(),
            "to": sf["billing_date"].max().date().isoformat(),
        },
        "sparse_series": int(out.drop_duplicates(["db_code", "category"])["sparse_flag"].sum()),
        "filter_rules": [
            "network_db sold_to only (distributor_dimension)",
            f"exclude distributor codes: {sorted(EXCLUDED_CODES)}",
            f"exclude non-part PNs: {sorted(NON_PART_PNS)}",
            "exclude CR/RE SaTy and negative net_sales_value",
            "exclude billed_qty == 0",
            "category = aim_l1 from aim_pn_classification; missing → UNCLASSIFIED",
            "units_sold = billing line count per month (not qty sum)",
            "sparse_flag = series has < 3 months with units_sold > 0",
        ],
        "sales_fact_path": str(SALES_SRC.relative_to(ISZE_ROOT)),
        "aim_classification_path": str(AIM_SRC.relative_to(ISZE_ROOT)),
        "phase": "5.1 — no forecast model yet",
    }
    return out, meta


def main() -> int:
    if not SALES_SRC.is_file():
        print(f"MISSING: {SALES_SRC}", file=sys.stderr)
        return 1
    out, meta = build()
    if out.empty:
        print("no demand_series rows", file=sys.stderr)
        return 1

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PARQUET, index=False)
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"wrote {OUT_PARQUET} ({len(out):,} rows)")
    print(
        f"series={meta['series']:,}  dbs={meta['distributors']}  "
        f"sparse={meta['sparse_series']:,}  months={meta['months'][0]}..{meta['months'][-1]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
