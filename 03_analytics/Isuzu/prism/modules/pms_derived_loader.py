"""Map verified derived PMS capture CSV to the shape used by the PMS Streamlit page."""

from __future__ import annotations

import pandas as pd

from config import PMS_CAPTURE_BY_DB_CSV
from modules.pms_engine import CATEGORY_LABELS


def derived_capture_available() -> bool:
    return PMS_CAPTURE_BY_DB_CSV.exists()


def load_pms_capture_derived(
    year: int,
    distributor_codes: list[str] | None = None,
    line_type: str = "total",
) -> dict:
    """
    Build a pms_result-compatible dict from pms_capture_by_db_year.csv.

    Uses the same P1 build as verify_derived_pipeline (ITUK UIO overrides, scope filters).
    """
    if not PMS_CAPTURE_BY_DB_CSV.exists():
        raise FileNotFoundError(f"Missing derived file: {PMS_CAPTURE_BY_DB_CSV}")

    df = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
    df = df[(df["year"] == year) & (df["line_type"] == line_type)].copy()

    if distributor_codes:
        df = df[df["distributor_code"].isin(distributor_codes)]

    if df.empty:
        return _empty_result()

    rows = []
    for _, r in df.iterrows():
        cat = r["pms_category"]
        rows.append(
            {
                "category": cat,
                "category_label": r.get("category_label")
                or CATEGORY_LABELS.get(cat, cat),
                "distributor_code": r["distributor_code"],
                "actual_qty": float(r["actual_qty"]),
                "expected_qty": float(r["expected_qty"]),
                "capture_rate": float(r["capture_rate"]),
                "avg_sp_eur": float(r["avg_sp_eur"]),
                "revenue_gap_eur": float(r["revenue_gap_eur"]),
                "actual_rev_eur": float(r["actual_rev_eur"]),
                "uio_units": int(r.get("uio_units", 0) or 0),
                "uio_source": r.get("uio_source", ""),
                "scope": r.get("scope", ""),
            }
        )

    summary_df = pd.DataFrame(rows)
    if summary_df.empty:
        return _empty_result()

    if not distributor_codes or len(distributor_codes) != 1:
        summary_df = (
            summary_df.groupby(["category", "category_label"], as_index=False)
            .agg(
                actual_qty=("actual_qty", "sum"),
                expected_qty=("expected_qty", "sum"),
                actual_rev_eur=("actual_rev_eur", "sum"),
                revenue_gap_eur=("revenue_gap_eur", "sum"),
            )
        )
        summary_df["capture_rate"] = summary_df.apply(
            lambda row: row["actual_qty"] / row["expected_qty"]
            if row["expected_qty"] > 0
            else 0.0,
            axis=1,
        )
        summary_df["avg_sp_eur"] = summary_df.apply(
            lambda row: row["actual_rev_eur"] / row["actual_qty"]
            if row["actual_qty"] > 0
            else 0.0,
            axis=1,
        )

    summary_df = summary_df.sort_values("revenue_gap_eur", ascending=False).reset_index(
        drop=True
    )

    capture_rate_by_category = {
        row["category"]: row["capture_rate"] for _, row in summary_df.iterrows()
    }
    actual_by_category = {
        row["category"]: {
            "qty": row["actual_qty"],
            "revenue_eur": row["actual_rev_eur"],
        }
        for _, row in summary_df.iterrows()
    }
    expected_by_category = {
        row["category"]: {"qty": row["expected_qty"]} for _, row in summary_df.iterrows()
    }
    revenue_opportunity = {
        row["category"]: row["revenue_gap_eur"] for _, row in summary_df.iterrows()
    }

    total_actual_eur = float(summary_df["actual_rev_eur"].sum())
    total_opportunity_eur = float(summary_df["revenue_gap_eur"].sum())

    meta = {
        "source": "derived",
        "path": str(PMS_CAPTURE_BY_DB_CSV),
        "line_type": line_type,
    }
    if distributor_codes and len(distributor_codes) == 1:
        sub = df.iloc[0]
        meta["uio_units"] = int(sub.get("uio_units", 0) or 0)
        meta["uio_source"] = sub.get("uio_source", "")
        meta["scope"] = sub.get("scope", "")

    return {
        "actual_by_category": actual_by_category,
        "expected_by_category": expected_by_category,
        "capture_rate_by_category": capture_rate_by_category,
        "revenue_opportunity": revenue_opportunity,
        "total_actual_eur": total_actual_eur,
        "total_opportunity_eur": total_opportunity_eur,
        "summary_df": summary_df,
        "meta": meta,
    }


def _empty_result() -> dict:
    empty = pd.DataFrame(
        columns=[
            "category",
            "category_label",
            "actual_qty",
            "expected_qty",
            "capture_rate",
            "avg_sp_eur",
            "revenue_gap_eur",
            "actual_rev_eur",
        ]
    )
    return {
        "actual_by_category": {},
        "expected_by_category": {},
        "capture_rate_by_category": {},
        "revenue_opportunity": {},
        "total_actual_eur": 0.0,
        "total_opportunity_eur": 0.0,
        "summary_df": empty,
        "meta": {"source": "derived"},
    }
