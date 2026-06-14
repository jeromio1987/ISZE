"""Slim tables for ISZE IAM Lookup Lab (autodoc_dashboard.py)."""
from __future__ import annotations

import pandas as pd

from bi_display import _pick_rename


def format_brand_league(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    spec = [
        ("brand", "Brand"),
        ("tier", "Tier"),
        ("pns_threatened", "PNs"),
        ("expected_loss_eur", "Expected loss (€)"),
        ("rev_exposed_eur", "Rev exposed (€)"),
        ("avg_price_gap", "DLR÷AM"),
    ]
    out = _pick_rename(df, spec)
    if "Expected loss (€)" in out.columns:
        out = out.sort_values("Expected loss (€)", ascending=False, na_position="last")
    return out.head(top_n)


def format_iam_pn(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    work = df.copy()
    if "expected_loss" in work.columns:
        work = work.sort_values("expected_loss", ascending=False, na_position="last")
    spec = [
        ("PN", "PN"),
        ("Description", "Description"),
        ("quadrant", "Quadrant"),
        ("primary_threat_brand", "Threat brand"),
        ("expected_loss", "Expected loss (€)"),
        ("action_verdict", "Action"),
        ("best_price_eur", "AM price (€)"),
        ("PR00_EUR", "PR00 (€)"),
    ]
    return _pick_rename(work, spec).head(top_n)


def format_category_concentration(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    spec = [
        ("AIM_Category", "Category"),
        ("Class", "Class"),
        ("pns", "PNs"),
        ("expected_loss_eur", "Expected loss (€)"),
    ]
    out = _pick_rename(df, spec)
    if "Expected loss (€)" in out.columns:
        out = out.sort_values("Expected loss (€)", ascending=False, na_position="last")
    return out.head(top_n)


def format_pms_category_iam(df: pd.DataFrame) -> pd.DataFrame:
    """PMS tab inside IAM app — shorter than engine view."""
    work = df.copy()
    if "capture_rate" in work.columns:
        work["capture_pct"] = (work["capture_rate"] * 100).round(1)
    elif "capture_rate_pct" in work.columns:
        work["capture_pct"] = work["capture_rate_pct"]
    spec = [
        ("pms_category", "Category"),
        ("lost_gp", "Lost GP (€)"),
        ("capture_pct", "Capture %"),
        ("actual", "Actual"),
        ("potential", "Potential"),
        ("pns", "PNs"),
    ]
    return _pick_rename(work, spec)


def format_pms_pn_iam(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    work = df.copy()
    if "capture_rate_pct" not in work.columns and "capture_rate" in work.columns:
        work["capture_rate_pct"] = (pd.to_numeric(work["capture_rate"], errors="coerce") * 100).round(1)
    spec = [
        ("PN", "PN"),
        ("Description", "Description"),
        ("pms_category", "Category"),
        ("lost_isze_gp_eur", "Lost GP (€)"),
        ("capture_rate_pct", "Capture %"),
        ("primary_threat_brand", "Threat brand"),
        ("best_price_eur", "AM (€)"),
    ]
    return _pick_rename(work.head(top_n) if len(work) > top_n else work, spec)
