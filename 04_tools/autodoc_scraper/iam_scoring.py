"""
ISZE - IAM Threat x Quality + Expected Loss scoring engine
===========================================================
Two layers of scoring:

LAYER 1 — Classification (legacy 2x2):
  - threat_score (0-100), quality_score (0-100), quadrant

LAYER 2 — Expected Loss (financial primary metric):
  - p_substitution (0-1) — sigmoid of price gap, quality alignment, multi-platform
  - eur_at_stake — Rev_CY2025 * ISZE_GP% * time_horizon
  - expected_loss = p_substitution * eur_at_stake
  - action_verdict — Defend / Match / Cede / Monitor

Apples-to-apples convention:
  Dealer-sell-to-workshop genuine = PR00 / (1-DB_GM) / (1-DLR_GM)
  AM retail = best_price_eur (cheapest competing site)
  Ratio = dealer_workshop / AM_retail. Ratio > 1 = dealer is more expensive.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).parent
DEFAULT_TIER_CSV = SCRIPT_DIR / "iam_brand_tiers.csv"

# SIMPLE MODEL — no weights, no sigmoid, no logarithms.
# Threat = price gap bucket mapped to 0-100. One observation, one number.
# Quality = brand tier mapped to 0-100 + OE bonus. One lookup.

PRICE_GAP_BUCKET_SCORE = {
    "<1.0":    0,    # Dealer cheaper, no threat
    "1.0-1.2": 20,   # Marginal gap
    "1.2-1.5": 40,   # Real gap
    "1.5-2.0": 60,   # Significant gap
    "2.0-3.0": 80,   # Large gap
    ">=3.0":   100,  # Extreme gap
}

TIER_SCORE = {4: 75, 3: 55, 2: 35, 1: 20}  # Base score; +25 if OE flag (capped 100)

QUADRANT_T = 50.0  # 2x2 threat split (= "real gap" threshold)
QUADRANT_Q = 50.0  # 2x2 quality split (= mainstream IAM threshold)


def load_brand_tiers(path: Path | None = None) -> pd.DataFrame:
    p = path or DEFAULT_TIER_CSV
    if not p.exists():
        raise FileNotFoundError(f"Brand tier table not found: {p}")
    tiers = pd.read_csv(p)
    tiers["brand_key"] = tiers["brand"].astype(str).str.upper().str.strip()
    tiers["tier"] = pd.to_numeric(tiers["tier"], errors="coerce").fillna(1).astype(int)
    tiers["oe_supplier"] = pd.to_numeric(tiers["oe_supplier"], errors="coerce").fillna(0).astype(int)
    return tiers


def _norm_brand(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.split("|")[0].strip()
    return s.upper()


def _coef_var(price_str: str | float) -> float | None:
    if not isinstance(price_str, str) or not price_str.strip():
        return None
    vals = []
    for part in price_str.split("|"):
        try:
            v = float(part.strip())
            if v >= 3:
                vals.append(v)
        except ValueError:
            pass
    if len(vals) < 2:
        return None
    arr = np.array(vals)
    if arr.mean() == 0:
        return None
    return float(arr.std() / arr.mean())


def _safe_log_norm(series: pd.Series) -> pd.Series:
    """log1p normalized to 0..100 across the series."""
    s = pd.to_numeric(series, errors="coerce").fillna(0).clip(lower=0)
    l = np.log1p(s)
    if l.max() == 0:
        return pd.Series(0, index=series.index)
    return (l / l.max() * 100).round(1)


def _is_scrape_error_value(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip()
    return bool(s) and s.lower() not in ("nan", "none")


def mask_scrape_error_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Null AM prices on scrape failures so they are not treated as IAM gaps.

    Distinct from Status=no_results (genuine empty catalogue). Error/timeout
    and a non-empty scrape_error column are masked; no_results is left as a gap.
    """
    out = df.copy()
    error_statuses = {"error", "timeout", "blocked_403", "scrape_error"}

    def _mask_key(key: str) -> None:
        err_col = f"{key}_scrape_error"
        st_col = f"{key}_status"
        mask = pd.Series(False, index=out.index)
        if err_col in out.columns:
            mask = mask | out[err_col].map(_is_scrape_error_value)
        if st_col in out.columns:
            mask = mask | out[st_col].astype(str).str.lower().isin(error_statuses)
        if not mask.any():
            return
        for suffix in ("_min_eur", "_min_native", "_premium"):
            col = f"{key}{suffix}"
            if col in out.columns:
                out.loc[mask, col] = np.nan

    keys = set()
    for col in out.columns:
        if col.endswith("_min_eur"):
            keys.add(col[: -len("_min_eur")])
        elif col.endswith("_status"):
            keys.add(col[: -len("_status")])
        elif col.endswith("_scrape_error"):
            keys.add(col[: -len("_scrape_error")])
    for key in keys:
        _mask_key(key)

    if "scrape_error" in out.columns or "Status" in out.columns:
        row_err = pd.Series(False, index=out.index)
        if "scrape_error" in out.columns:
            row_err = row_err | out["scrape_error"].map(_is_scrape_error_value)
        if "Status" in out.columns:
            row_err = row_err | out["Status"].astype(str).str.lower().isin(error_statuses)
        if row_err.any():
            for col in list(out.columns):
                if col.endswith("_min_eur") or col == "best_price_eur":
                    out.loc[row_err, col] = np.nan

    eur_cols = [c for c in out.columns if c.endswith("_min_eur")]
    if eur_cols:
        out["best_price_eur"] = out[eur_cols].min(axis=1)
    return out


def compute_scores(
    merged: pd.DataFrame,
    *,
    db_gm: float = 0.37,
    dlr_gm: float = 0.25,
    tier_path: Path | None = None,
) -> pd.DataFrame:
    """Add threat_score, quality_score, quadrant columns to merged df.

    Expects merged to have columns from autodoc_dashboard.load_all:
      PR00_EUR, Rev_CY2025_EUR,
      best_price_eur, best_site (preferred),
      AD_UK_min_eur, AD_UK_brand, AD_UK_status,
      KS_AM_min_eur, KS_AM_brand,
      KS_GEN_min_eur, KS_GEN_brand,
      MEK_min_eur, MEK_brand,
      Autodoc_ResultCount (if present), Autodoc_AllPrices_GBP (if present)
    """
    df = merged.copy()
    df = mask_scrape_error_prices(df)
    tiers = load_brand_tiers(tier_path)
    tier_lookup = dict(zip(tiers["brand_key"], tiers["tier"]))
    oe_lookup = dict(zip(tiers["brand_key"], tiers["oe_supplier"]))

    # --- Apples-to-apples genuine workshop price ---
    df["dealer_workshop_price"] = df["PR00_EUR"] / (1 - db_gm) / (1 - dlr_gm)

    # --- Pick primary threat brand: AD_UK_brand if present, else MEK, else KS_AM ---
    def pick_primary_brand(row):
        for col in ["AD_UK_brand", "MEK_brand", "KS_AM_brand"]:
            v = row.get(col)
            if isinstance(v, str) and v.strip():
                return _norm_brand(v)
        return ""
    df["primary_threat_brand"] = df.apply(pick_primary_brand, axis=1)

    # --- Best AM retail price (cheapest across all working sites) ---
    if "best_price_eur" not in df.columns:
        eur_cols = [c for c in df.columns if c.endswith("_min_eur")]
        if eur_cols:
            df["best_price_eur"] = df[eur_cols].min(axis=1)
        else:
            df["best_price_eur"] = np.nan

    # ── Price gap ratio (one observation) ──
    ratio = df["dealer_workshop_price"] / df["best_price_eur"].replace(0, np.nan)
    df["_ratio"] = ratio
    df["price_gap_bucket"] = ratio.apply(_gap_bucket)

    # THREAT SCORE = simple bucket lookup. No weights, no normalization.
    df["threat_score"] = df["price_gap_bucket"].map(PRICE_GAP_BUCKET_SCORE).fillna(0)

    # Informational sub-signals (NOT combined into threat — shown for context only)
    df["site_count"] = 0
    site_cols = [f"{k}_min_eur" for k in ["AD_UK","MEK","KS_AM","KS_GEN"] if f"{k}_min_eur" in df.columns]
    if site_cols:
        df["site_count"] = df[site_cols].notna().sum(axis=1)
    if "Autodoc_ResultCount" in df.columns:
        df["sku_count"] = pd.to_numeric(df["Autodoc_ResultCount"], errors="coerce").fillna(0).astype(int)
    else:
        df["sku_count"] = 0

    # QUALITY SCORE = tier + OE flag. No weighting.
    def quality(brand: str) -> float:
        if not brand:
            return float(TIER_SCORE[1])
        tier = tier_lookup.get(brand, 1)
        oe = oe_lookup.get(brand, 0)
        return float(min(100, TIER_SCORE.get(tier, TIER_SCORE[1]) + oe * 25))

    df["quality_score"] = df["primary_threat_brand"].apply(quality)
    df["brand_tier"] = df["primary_threat_brand"].map(tier_lookup).fillna(1).astype(int)
    df["brand_oe_flag"] = df["primary_threat_brand"].map(oe_lookup).fillna(0).astype(int)

    # ============================================================
    # Quadrant assignment
    # ============================================================
    def quadrant(row):
        t = row["threat_score"]
        q = row["quality_score"]
        if pd.isna(t) or pd.isna(q):
            return "No data"
        high_t = t >= QUADRANT_T
        high_q = q >= QUADRANT_Q
        if high_t and high_q:
            return "Dangerous"
        if high_t and not high_q:
            return "Nuisance"
        if not high_t and high_q:
            return "Watch"
        return "Ignore"
    df["quadrant"] = df.apply(quadrant, axis=1)

    return df


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """One-row-per-PN summary of the scoring."""
    cols = [
        "PN", "Description", "Rev_CY2025_EUR",
        "PR00_EUR", "dealer_workshop_price", "best_price_eur",
        "primary_threat_brand", "brand_tier", "brand_oe_flag",
        "price_gap_bucket", "threat_score", "quality_score",
        "site_count", "sku_count", "quadrant",
        "p_substitution", "eur_at_stake", "expected_loss", "action_verdict",
        "best_url" if "best_url" in df.columns else None,
    ]
    cols = [c for c in cols if c and c in df.columns]
    return df[cols].copy()


# ──────────────────────────────────────────────────────────────────
# LAYER 2 — Expected Loss model (primary financial metric)
# ──────────────────────────────────────────────────────────────────

DEFAULT_SUBSTITUTION_CSV = SCRIPT_DIR / "substitution_probability.csv"
DEFAULT_PMS_INTERVALS_CSV = SCRIPT_DIR / "pms_intervals.csv"


def load_pms_intervals(path: Path | None = None) -> pd.DataFrame:
    """Load PMS part categories with their annual replacement frequency."""
    p = path or DEFAULT_PMS_INTERVALS_CSV
    if not p.exists():
        raise FileNotFoundError(f"PMS intervals CSV not found: {p}")
    df = pd.read_csv(p)
    df["annual_freq"] = pd.to_numeric(df["annual_freq"], errors="coerce")
    return df


def classify_pms_category(description: str, intervals: pd.DataFrame | None = None) -> str | None:
    """Match a PN description to a PMS category. Returns None if breakdown / not PMS."""
    import re
    if not isinstance(description, str) or not description.strip():
        return None
    if intervals is None:
        intervals = load_pms_intervals()
    desc = description.lower()
    for _, row in intervals.iterrows():
        try:
            if re.search(row["description_regex"], desc, re.IGNORECASE):
                return row["pms_category"]
        except re.error:
            continue
    return None


def compute_lost_sales(
    scored: pd.DataFrame,
    *,
    uio_potential: float = 11900.0,
    isze_gp_pct: float = 0.35,
    horizon_years: float = 1.0,
) -> pd.DataFrame:
    """UIO-derived lost-sales calculation for PMS-eligible PNs.

    Methodology (matches your ITUK PMS Coverage Calculator):
        Potential annual demand = uio_potential × annual_freq
        Lost units = Potential demand × horizon - Actual units sold
        Lost revenue   = Lost units × PR00
        Lost ISZE GP   = Lost units × PR00 × ISZE GP%

    For non-PMS parts (no matching category), columns are NaN.
    The fallback expected_loss (substitution probability) stays in place
    for breakdown parts.
    """
    df = scored.copy()
    intervals = load_pms_intervals()

    # Map every PN to a PMS category (None if breakdown/unclassified)
    df["pms_category"] = df["Description"].apply(
        lambda d: classify_pms_category(d, intervals)
    )

    freq_lookup = dict(zip(intervals["pms_category"], intervals["annual_freq"]))
    df["annual_freq"] = df["pms_category"].map(freq_lookup)
    df["potential_demand"] = (df["annual_freq"] * uio_potential * horizon_years).round(0)

    # Actual units — prefer Qty_CY2025, fall back to Qty_CY2024
    qty_col = None
    for c in ("Qty_CY2025", "Qty_CY2024", "Qty_Last12M"):
        if c in df.columns:
            qty_col = c
            break
    if qty_col:
        df["actual_units"] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
    else:
        df["actual_units"] = 0

    df["lost_units"] = (df["potential_demand"] - df["actual_units"]).clip(lower=0)
    df["capture_rate"] = (df["actual_units"] / df["potential_demand"]).where(df["potential_demand"] > 0)
    df["lost_revenue_eur"] = (df["lost_units"] * pd.to_numeric(df["PR00_EUR"], errors="coerce")).round(0)
    df["lost_isze_gp_eur"] = (df["lost_revenue_eur"] * isze_gp_pct).round(0)

    # For non-PMS PNs, leave the columns NaN (don't pollute with zeros)
    non_pms = df["pms_category"].isna()
    for c in ("potential_demand", "lost_units", "capture_rate", "lost_revenue_eur", "lost_isze_gp_eur", "annual_freq"):
        df.loc[non_pms, c] = float("nan")

    return df


def load_substitution_table(path: Path | None = None) -> dict:
    """Load the substitution probability lookup table.

    Returns dict of {(bucket_label, tier): probability}.
    Bucket labels are strings: '<1.0', '1.0-1.2', '1.2-1.5', '1.5-2.0', '2.0-3.0', '>=3.0'.
    """
    p = path or DEFAULT_SUBSTITUTION_CSV
    if not p.exists():
        raise FileNotFoundError(f"Substitution table not found: {p}")
    df = pd.read_csv(p)
    table = {}
    for _, r in df.iterrows():
        bucket = str(r["price_gap_bucket"]).strip()
        for tier in (1, 2, 3, 4):
            col = f"tier_{tier}"
            if col in df.columns:
                table[(bucket, tier)] = float(r[col])
    return table


def _gap_bucket(ratio: float) -> str:
    """Bucketize a price gap ratio into the lookup table's bucket label."""
    if pd.isna(ratio) or ratio < 1.0:
        return "<1.0"
    if ratio < 1.2:
        return "1.0-1.2"
    if ratio < 1.5:
        return "1.2-1.5"
    if ratio < 2.0:
        return "1.5-2.0"
    if ratio < 3.0:
        return "2.0-3.0"
    return ">=3.0"


def compute_expected_loss(
    scored: pd.DataFrame,
    *,
    isze_gp_pct: float = 0.35,
    horizon_years: float = 1.0,
    sub_table_path: Path | None = None,
) -> pd.DataFrame:
    """Add p_substitution, eur_at_stake, expected_loss, action_verdict columns.

    SIMPLE MODEL — no sigmoid, no weights. Just a lookup table.

        For each PN:
          1. Compute ratio = DLR→WS price ÷ AM retail
          2. Bucket the ratio (<1.0, 1.0-1.2, 1.2-1.5, 1.5-2.0, 2.0-3.0, >=3.0)
          3. Look up P(substitution) = table[bucket][brand_tier]
          4. € at stake = Rev_CY2025 × ISZE GP × horizon
          5. Expected loss = P × €

    Action verdicts (dataset-relative thresholds):
      Defend  = EL ≥ 75th-percentile AND tier ≥ 3
      Match   = EL ≥ median           AND tier <  3
      Monitor = EL <  median          AND tier ≥ 3
      Cede    = EL <  median          AND tier <  3

    The substitution table is in substitution_probability.csv — edit it to
    refine the model. Every cell is an explicit, defensible judgment.
    """
    df = scored.copy()
    sub_table = load_substitution_table(sub_table_path)

    # Price gap ratio (simple division, no normalization)
    if "_ratio" in df.columns:
        ratio = df["_ratio"]
    else:
        ratio = df["dealer_workshop_price"] / df["best_price_eur"].replace(0, np.nan)

    # Bucket each ratio
    df["price_gap_bucket"] = ratio.apply(_gap_bucket)

    # Lookup P(substitution) from table
    def lookup_p(row):
        if pd.isna(row.get("best_price_eur")):
            return 0.0  # no AM presence = no risk
        tier = int(row.get("brand_tier", 1)) if pd.notna(row.get("brand_tier")) else 1
        bucket = row["price_gap_bucket"]
        return sub_table.get((bucket, tier), 0.0)
    df["p_substitution"] = df.apply(lookup_p, axis=1).round(3)

    # € at stake
    rev = pd.to_numeric(df["Rev_CY2025_EUR"], errors="coerce").fillna(0)
    df["eur_at_stake"] = (rev * isze_gp_pct * horizon_years).round(0)
    df["expected_loss"] = (df["p_substitution"] * df["eur_at_stake"]).round(0)

    # Action verdicts
    el_valid = df.loc[df["expected_loss"] > 0, "expected_loss"]
    if len(el_valid) >= 4:
        el_p75 = float(el_valid.quantile(0.75))
        el_p50 = float(el_valid.quantile(0.50))
    else:
        el_p75 = float(el_valid.max()) if len(el_valid) else 0.0
        el_p50 = float(el_valid.median()) if len(el_valid) else 0.0

    def verdict(row):
        el = row["expected_loss"]
        tier = int(row.get("brand_tier", 1)) if pd.notna(row.get("brand_tier")) else 1
        if el >= el_p75 and tier >= 3:
            return "Defend"
        if el >= el_p50 and tier < 3:
            return "Match"
        if el < el_p50 and tier >= 3 and el > 0:
            return "Monitor"
        return "Cede"
    df["action_verdict"] = df.apply(verdict, axis=1)

    return df


def brand_league(scored: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by primary_threat_brand for the league table."""
    if "primary_threat_brand" not in scored.columns:
        return pd.DataFrame()
    g = scored[scored["primary_threat_brand"] != ""].groupby("primary_threat_brand")
    league = pd.DataFrame({
        "pns_threatened":     g.size(),
        "rev_exposed_eur":    g["Rev_CY2025_EUR"].sum(),
        "expected_loss_eur":  g["expected_loss"].sum() if "expected_loss" in scored.columns else 0,
        "avg_price_gap":      g["_ratio"].mean() if "_ratio" in scored.columns else None,
        "tier":               g["brand_tier"].first() if "brand_tier" in scored.columns else 1,
        "oe_flag":            g["brand_oe_flag"].first() if "brand_oe_flag" in scored.columns else 0,
        "quality_score":      g["quality_score"].first() if "quality_score" in scored.columns else 30,
        "defend_count":       g["action_verdict"].apply(lambda s: (s == "Defend").sum()) if "action_verdict" in scored.columns else 0,
        "median_revenue":     g["Rev_CY2025_EUR"].median(),
    }).reset_index().rename(columns={"primary_threat_brand": "brand"})
    return league.sort_values("expected_loss_eur", ascending=False).reset_index(drop=True)


def category_concentration(scored: pd.DataFrame) -> pd.DataFrame:
    """Class × AIM_Category heatmap source data."""
    if "Class" not in scored.columns or "AIM_Category" not in scored.columns:
        return pd.DataFrame()
    g = scored.groupby(["Class", "AIM_Category"], dropna=False)
    out = pd.DataFrame({
        "pns":              g.size(),
        "rev_exposed_eur":  g["Rev_CY2025_EUR"].sum(),
        "expected_loss_eur":g["expected_loss"].sum() if "expected_loss" in scored.columns else 0,
        "avg_threat":       g["threat_score"].mean() if "threat_score" in scored.columns else 0,
        "defend_count":     g["action_verdict"].apply(lambda s: (s == "Defend").sum()) if "action_verdict" in scored.columns else 0,
    }).reset_index()
    return out


def data_quality_report(script_dir) -> pd.DataFrame:
    """Per-source freshness and coverage metrics."""
    from pathlib import Path
    sd = Path(script_dir)
    sources = [
        ("Autodoc UK",     "autodoc_results.csv",      "Autodoc_MinPrice_GBP"),
        ("Mekonomen",      "mekonomen_results.csv",    "MEK_AM_MinPrice_SEK"),
        ("KS Int'l (AM)",  "ks_results.csv",           "KS_AM_MinPrice_GBP"),
        ("KS Int'l (OEM)", "ks_results.csv",           "KS_GEN_MinPrice_GBP"),
        ("Autodoc EU",     "autodoc_eu_results.csv",   "Autodoc_MinPrice_EUR"),
        ("Autodoc DE",     "autodoc_de_results.csv",   "Autodoc_MinPrice_EUR"),
        ("Mister Auto",    "mister_auto_results.csv",  "MA_AM_MinPrice_EUR"),
        ("Oscaro",         "oscaro_results.csv",       "OSC_AM_MinPrice_EUR"),
    ]
    rows = []
    for label, fname, price_col in sources:
        p = sd / fname
        if not p.exists():
            rows.append({"source": label, "file": fname, "status": "missing",
                         "rows": 0, "hits": 0, "hit_rate": 0.0, "last_scrape": "—"})
            continue
        try:
            df = pd.read_csv(p, dtype={"PN": str}, low_memory=False)
        except Exception:
            rows.append({"source": label, "file": fname, "status": "corrupt",
                         "rows": 0, "hits": 0, "hit_rate": 0.0, "last_scrape": "—"})
            continue
        if "PN" not in df.columns:
            rows.append({"source": label, "file": fname, "status": "no header",
                         "rows": len(df), "hits": 0, "hit_rate": 0.0, "last_scrape": "—"})
            continue
        n = len(df)
        # Prefer authoritative Status column when available
        if "Status" in df.columns:
            hits = int((df["Status"].astype(str).str.lower() == "ok").sum())
        else:
            hits = int(df[price_col].notna().sum()) if price_col in df.columns else 0
        ts_max = "—"
        if "Scraped_At" in df.columns:
            ts = pd.to_datetime(df["Scraped_At"], errors="coerce").max()
            if pd.notna(ts):
                ts_max = ts.strftime("%Y-%m-%d %H:%M")
        rows.append({
            "source": label, "file": fname,
            "status": "ok" if hits > 0 else "no hits",
            "rows": n, "hits": hits,
            "hit_rate": round(hits / n * 100, 1) if n else 0.0,
            "last_scrape": ts_max,
        })
    return pd.DataFrame(rows)
