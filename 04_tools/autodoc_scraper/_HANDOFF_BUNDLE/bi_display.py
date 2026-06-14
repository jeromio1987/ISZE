"""
BI presentation layer — slim tables, readable labels (no raw dicts / wide dumps).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from pms_validation import format_capture_pct
except ImportError:
    def format_capture_pct(v) -> str:  # type: ignore
        try:
            f = float(v)
            if pd.isna(f):
                return "—"
            return f"{f * 100:.1f}%"
        except (TypeError, ValueError):
            return "—"


def data_mode_banner(mode_df: pd.DataFrame) -> str:
    """Human-readable PRISM / engine data source line."""
    if mode_df is None or mode_df.empty:
        return ""
    row = mode_df.iloc[0]
    mode = str(row.get("mode", ""))
    file = str(row.get("file", ""))
    note = str(row.get("scope_note", ""))
    fname = Path(file).name if file else ""
    parts = [p for p in (f"**{mode}**" if mode else "", f"`{fname}`" if fname else "", note) if p]
    return " · ".join(parts)


def _pick_rename(df: pd.DataFrame, spec: list[tuple[str, str]]) -> pd.DataFrame:
    cols = [c for c, _ in spec if c in df.columns]
    if not cols:
        return df
    out = df[cols].copy()
    return out.rename(columns=dict(spec))


def format_v3_preview(df: pd.DataFrame, max_rows: int = 20) -> pd.DataFrame:
    cols = [
        c
        for c in (
            "PN",
            "Description",
            "AIM_Category",
            "AIM_DemandType",
            "PR00_EUR",
            "Qty_CY2025",
        )
        if c in df.columns
    ]
    return df[cols].head(max_rows) if cols else df.head(max_rows)


def format_sheet_preview(df: pd.DataFrame, max_cols: int = 6, max_rows: int = 20) -> pd.DataFrame:
    """Raw Excel sheet — first columns only (audit tab, not analysis)."""
    if df.empty:
        return df
    return df.iloc[:max_rows, : min(max_cols, df.shape[1])]


def format_scrape_compact(df: pd.DataFrame, max_rows: int = 25) -> pd.DataFrame:
    """Competitor tab — fixed width, no extra scrape columns."""
    cols = [
        c
        for c in (
            "PN",
            "Description",
            "pms_category",
            "AIM_Category",
            "AD_UK__Autodoc_MinPrice_GBP",
            "KS__KS_AM_MinPrice_GBP",
            "MEK__MEK_AM_MinPrice_SEK",
        )
        if c in df.columns
    ]
    rename = {
        "pms_category": "PMS cat.",
        "AIM_Category": "AIM cat.",
        "AD_UK__Autodoc_MinPrice_GBP": "AD UK £",
        "KS__KS_AM_MinPrice_GBP": "KS £",
        "MEK__MEK_AM_MinPrice_SEK": "MEK SEK",
    }
    if not cols:
        return df.head(max_rows)
    out = df[cols].head(max_rows).rename(columns=rename)
    return out


def format_brand_league_scrape(df: pd.DataFrame) -> pd.DataFrame:
    spec = [
        ("brand", "Brand"),
        ("pns_present", "PNs"),
        ("avg_price_eur", "Avg AM (€)"),
        ("categories", "Categories"),
    ]
    return _pick_rename(df, spec).head(15)


def format_category_table(df: pd.DataFrame) -> pd.DataFrame:
    spec = [
        ("category", "Category"),
        ("potential_units", "Potential"),
        ("actual_units", "Actual"),
        ("capture_rate", "Capture %"),
        ("lost_isze_gp", "Lost GP (€)"),
        ("lost_units", "Lost units"),
    ]
    out = _pick_rename(df, spec)
    if "Capture %" in out.columns:
        out["Capture %"] = (pd.to_numeric(out["Capture %"], errors="coerce") * 100).round(1)
    for c in ("Potential units", "Actual units", "Lost units", "Over-capture", "PNs"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").round(0)
    if "Lost GP (€)" in out.columns:
        out["Lost GP (€)"] = pd.to_numeric(out["Lost GP (€)"], errors="coerce").round(0)
    return out


def format_prism_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Executive view: one row per distributor, ≤7 columns (fits one screen)."""
    if df.empty:
        return df
    work = df.copy()
    if "overall_capture_rate" in work.columns:
        work["capture_pct"] = (pd.to_numeric(work["overall_capture_rate"], errors="coerce") * 100).round(1)
    spec: list[tuple[str, str]] = [
        ("distributor", "Distributor"),
        ("uio_scope", "UIO"),
        ("total_potential", "Expected"),
        ("total_actual", "Actual"),
        ("capture_pct", "Capture %"),
        ("total_lost_gp", "Lost GP (€)"),
    ]
    # Scope only if not uniform (saves a column)
    if "prism_scope" in work.columns and work["prism_scope"].nunique(dropna=True) > 1:
        spec.append(("prism_scope", "Scope"))
    out = _pick_rename(work, spec)
    sort_col = "Lost GP (€)" if "Lost GP (€)" in out.columns else out.columns[0]
    return out.sort_values(sort_col, ascending=False, na_position="last")


def format_prism_detail(df: pd.DataFrame) -> pd.DataFrame:
    """Category × distributor — only when drilling down."""
    if df.empty:
        return df
    work = df.copy()
    if "capture_rate" in work.columns:
        work["capture_pct"] = (pd.to_numeric(work["capture_rate"], errors="coerce") * 100).round(1)
    spec = [
        ("distributor", "Distributor"),
        ("category", "Category"),
        ("potential_units", "Expected"),
        ("actual_units", "Actual"),
        ("capture_pct", "Capture %"),
        ("lost_isze_gp", "Lost GP (€)"),
    ]
    out = _pick_rename(work, spec)
    if "Lost GP (€)" in out.columns:
        out = out.sort_values("Lost GP (€)", ascending=False, na_position="last")
    return out


def format_model_detail(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    if "capture_rate" in work.columns:
        work["capture_pct"] = (pd.to_numeric(work["capture_rate"], errors="coerce") * 100).round(1)
    spec = [
        ("model", "Model"),
        ("category", "Category"),
        ("potential_units", "Potential"),
        ("actual_units", "Actual"),
        ("capture_pct", "Capture %"),
        ("lost_isze_gp", "Lost GP (€)"),
    ]
    out = _pick_rename(work, spec)
    if "Lost GP (€)" in out.columns:
        return out.sort_values("Lost GP (€)", ascending=False, na_position="last")
    return out


def format_model_summary(df: pd.DataFrame) -> pd.DataFrame:
    spec = [
        ("model", "Model"),
        ("tonnage_class", "Class"),
        ("car_park_uio", "Car park UIO"),
        ("model_share", "Share %"),
        ("recommended_km_yr", "Rec. km/yr"),
        ("potential_units", "Potential"),
        ("actual_units", "Actual"),
        ("capture_rate", "Capture %"),
        ("lost_isze_gp", "Lost GP (€)"),
    ]
    out = _pick_rename(df, spec)
    if "Share %" in out.columns:
        out["Share %"] = (pd.to_numeric(out["Share %"], errors="coerce") * 100).round(1)
    if "Capture %" in out.columns:
        out["Capture %"] = (pd.to_numeric(out["Capture %"], errors="coerce") * 100).round(1)
    return out


def format_pn_table(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """≤6 columns — fits laptop width without horizontal scroll."""
    default = [
        "PN",
        "Description",
        "category",
        "actual_units",
        "allocated_lost_gp",
        "competitor_min_price_eur",
    ]
    use = [c for c in (columns or default) if c in df.columns]
    out = df[use].copy()
    rename = {
        "category": "Category",
        "PR00_EUR": "PR00 (€)",
        "actual_units": "Actual qty",
        "allocated_lost_gp": "Lost GP (€)",
        "competitor_min_price_eur": "AM min (€)",
        "competitor_brand": "AM brand",
    }
    return out.rename(columns={k: v for k, v in rename.items() if k in out.columns})


def format_scrape_table(df: pd.DataFrame, front_cols: list[str] | None = None) -> pd.DataFrame:
    return format_scrape_compact(df)
