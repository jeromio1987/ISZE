"""Shared loaders and builders for strategic dashboard contracts (1–15)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import stats

from config import (
    BVP_PN_DIMENSION_CSV,
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    GPS_SPU_BY_DB_CSV,
    PMS_CAPTURE_BY_DB_CSV,
    PRISM_DATA_DIR,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.bvp_analytics import ensure_part_number, normalize_pn_value, tag_sales_with_dimension
from modules.data_prep import load_distributor_mapping
from modules.sales_loader import load_prism_sales
from modules.saty_mapping import is_backorder, is_vor_urgent, saty_to_order_type

# Country centroids for contract 11 (approximate capitals / geographic centres)
COUNTRY_CENTROIDS: dict[str, tuple[float, float]] = {
    "Armenia": (40.18, 44.51),
    "Belgium": (50.85, 4.35),
    "Cyprus": (35.17, 33.36),
    "Denmark": (56.26, 9.50),
    "Finland": (60.17, 24.94),
    "Germany": (51.17, 10.45),
    "Greece": (39.07, 21.82),
    "Hungary": (47.16, 19.50),
    "Iceland": (64.96, -19.02),
    "Ireland": (53.35, -7.95),
    "Israel": (31.05, 34.85),
    "Italy": (41.87, 12.57),
    "Malta": (35.94, 14.38),
    "Kazakhstan": (48.02, 66.92),
    "Netherlands": (52.13, 5.29),
    "Norway": (60.47, 8.47),
    "Palestine": (31.95, 35.23),
    "Poland": (51.92, 19.15),
    "Portugal": (39.40, -8.22),
    "Romania": (45.94, 24.97),
    "Spain": (40.46, -3.75),
    "Ukraine": (48.38, 31.17),
    "Sweden": (60.13, 18.64),
    "Switzerland": (46.82, 8.23),
    "Turkey": (39.93, 32.86),
    "United Kingdom": (54.00, -2.00),
}

REGION_TERRITORY: dict[str, str] = {
    "UK/IE": "UK & Ireland",
    "Benelux": "Benelux",
    "Nordics": "Nordics",
    "CEE": "Central & Eastern Europe",
    "Med": "Mediterranean",
    "MENA": "Middle East & Africa",
    "DACH": "DACH",
}


def weight_class_for_family(family: str) -> str:
    fam = (family or "").lower()
    if any(k in fam for k in ("filter", "wiper", "gasket", "seal")):
        return "light"
    if any(k in fam for k in ("clutch", "engine", "transmission", "turbo", "exhaust")):
        return "heavy"
    return "medium"


def gini_coefficient(revenues: np.ndarray) -> float:
    s = np.asarray(revenues, dtype=float)
    s = s[s > 0]
    n = len(s)
    if n == 0:
        return 0.0
    s = np.sort(s)
    cumsum = np.sum((np.arange(1, n + 1)) * s)
    total = s.sum()
    if total <= 0:
        return 0.0
    return float((2 * cumsum) / (n * total) - (n + 1) / n)


def load_sales_mapped() -> pd.DataFrame:
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df, _ = load_prism_sales(df_map)
    df = ensure_part_number(df)
    if "saty" in df.columns:
        df["order_type"] = df["saty"].map(saty_to_order_type)
        df["is_vor_urgent"] = df["saty"].map(is_vor_urgent)
        df["is_backorder"] = df["saty"].map(is_backorder)
    else:
        df["order_type"] = "other"
        df["is_vor_urgent"] = False
        df["is_backorder"] = False
    return df


def load_sales_tagged() -> pd.DataFrame:
    df = load_sales_mapped()
    dim = pd.read_csv(BVP_PN_DIMENSION_CSV)
    return tag_sales_with_dimension(df, dim)


def attach_dimension_left(df: pd.DataFrame) -> pd.DataFrame:
    dim = pd.read_csv(BVP_PN_DIMENSION_CSV).drop_duplicates("part_number")
    dim["_pn"] = dim["part_number"].map(normalize_pn_value)
    out = ensure_part_number(df.copy())
    out["_pn"] = out["part_number"].map(normalize_pn_value)
    cols = ["_pn", "product_family", "line_type", "pms_category", "pms_flag"]
    return out.merge(dim[cols], on="_pn", how="left").drop(columns=["_pn"], errors="ignore")


# ── Contract 1 ──────────────────────────────────────────────────────────────

def build_vor_airfreight_risk() -> pd.DataFrame:
    df = load_sales_tagged()
    df = df[df["line_type"].isin(["genuine", "bvp"])].copy()
    df["weight_class"] = df["product_family"].map(weight_class_for_family)

    rows = []
    for (dist, fam, year), g in df.groupby(
        ["distributor_code", "product_family", "year"], dropna=False
    ):
        if pd.isna(fam) or not str(fam).strip():
            continue
        total = len(g)
        vor_g = g[g["is_vor_urgent"]]
        bo_g = g[g["is_backorder"]]
        vor_n = len(vor_g)
        vor_pct = vor_n / total if total else 0.0
        bo_rate = len(bo_g) / total if total else 0.0
        rows.append(
            {
                "distributor_code": dist,
                "product_family": fam,
                "year": int(year),
                "vor_line_count": vor_n,
                "total_line_count": total,
                "vor_pct": round(vor_pct, 4),
                "vor_revenue_eur": round(float(vor_g["net_sales_value"].sum()), 2),
                "backorder_rate": round(bo_rate, 4),
                "weight_class": g["weight_class"].mode().iloc[0]
                if not g["weight_class"].mode().empty
                else "medium",
                "airfreight_risk_score": round(vor_pct * bo_rate, 4),
            }
        )
    return pd.DataFrame(rows)


# ── Contract 6 ──────────────────────────────────────────────────────────────

def build_vor_seasonality() -> pd.DataFrame:
    df = load_sales_mapped()
    df = df.dropna(subset=["billing_date"]).copy()
    df["week_of_year"] = df["billing_date"].dt.isocalendar().week.fillna(0).astype(int)
    rows = []
    for (dist, year, week), g in df.groupby(
        ["distributor_code", "year", "week_of_year"], dropna=False
    ):
        total = len(g)
        vor_n = int(g["is_vor_urgent"].sum())
        rows.append(
            {
                "distributor_code": dist,
                "year": int(year),
                "week_of_year": int(week),
                "vor_count": vor_n,
                "total_order_count": total,
                "vor_pct": round(vor_n / total, 4) if total else 0.0,
            }
        )
    return pd.DataFrame(rows)


# ── Contract 12 ─────────────────────────────────────────────────────────────

def build_vor_profile() -> pd.DataFrame:
    df = load_sales_mapped()
    grp = (
        df.groupby(["distributor_code", "year", "order_type"], dropna=False)
        .agg(line_count=("part_number", "count"), revenue_eur=("net_sales_value", "sum"))
        .reset_index()
    )
    totals = (
        df.groupby(["distributor_code", "year"])
        .size()
        .rename("total_lines")
        .reset_index()
    )
    out = grp.merge(totals, on=["distributor_code", "year"])
    out["pct_of_total_lines"] = out["line_count"] / out["total_lines"].replace(0, np.nan)
    net = (
        out.groupby(["year", "order_type"])["pct_of_total_lines"]
        .mean()
        .rename("network_avg_pct")
        .reset_index()
    )
    out = out.merge(net, on=["year", "order_type"], how="left")
    out["vs_network_pp"] = out["pct_of_total_lines"] - out["network_avg_pct"]
    out["revenue_eur"] = out["revenue_eur"].round(2)
    return out.drop(columns=["total_lines"])


# ── Contract 7 ──────────────────────────────────────────────────────────────

def build_capture_trajectory(
    pms: pd.DataFrame | None = None,
    *,
    is_partial_year: Callable[[int], bool] | None = None,
) -> pd.DataFrame:
    """Capture-rate trend per distributor × PMS category (Contract 7).

    Fits slope / R² / ``alert_declining`` on **complete billing years only**.
    A partial current year is a fraction of annual demand and reads as a cliff
    if included — measured 2026-07-17: 35 declining alerts with the partial
    year in, 6 with it out (29/35 artifacts; 0 real declines hidden). See
    ``docs/EARLY_WARNING_DESIGN.md`` finding 1 and ``modules/year_coverage.py``.

    Partial-year actuals are still emitted (``is_projected=False``) so charts
    can show the truncated year; they do not enter the regression. Contract
    gate is unchanged: ``slope < -0.05`` and ``r2 > 0.5``.
    """
    from modules.year_coverage import is_partial as _default_is_partial

    if is_partial_year is None:
        is_partial_year = _default_is_partial
    if pms is None:
        pms = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)

    hist = pms[pms["line_type"] == "total"].copy()
    hist["year"] = hist["year"].astype(int)
    rows = []
    for (dist, cat), g in hist.groupby(["distributor_code", "pms_category"]):
        g = g.sort_values("year")
        fit = g[~g["year"].map(lambda y: bool(is_partial_year(int(y))))]
        slope = intercept = r2 = float("nan")
        alert = False
        can_project = False
        if len(fit) >= 2:
            years = fit["year"].astype(float).values
            caps = fit["capture_rate"].astype(float).values
            if np.isfinite(caps).all() and float(np.nanmax(caps)) > 0:
                slope, intercept, r, _, _ = stats.linregress(years, caps)
                r2 = float(r) ** 2
                alert = bool(slope < -0.05 and r2 > 0.5)
                can_project = True

        slope_out = round(float(slope), 4) if np.isfinite(slope) else np.nan
        r2_out = round(float(r2), 4) if np.isfinite(r2) else np.nan

        for _, r0 in g.iterrows():
            rows.append(
                {
                    "distributor_code": dist,
                    "pms_category": cat,
                    "year": int(r0["year"]),
                    "capture_rate": round(float(r0["capture_rate"]), 4),
                    "is_projected": False,
                    "trend_slope_pp_per_year": slope_out,
                    "trend_r2": r2_out,
                    "alert_declining": alert,
                }
            )
        if can_project:
            for py in (2026, 2027):
                pred = float(np.clip(intercept + slope * py, 0.0, 1.05))
                rows.append(
                    {
                        "distributor_code": dist,
                        "pms_category": cat,
                        "year": py,
                        "capture_rate": round(pred, 4),
                        "is_projected": True,
                        "trend_slope_pp_per_year": slope_out,
                        "trend_r2": r2_out,
                        "alert_declining": alert,
                    }
                )
    return pd.DataFrame(rows)


# ── Contract 9 ──────────────────────────────────────────────────────────────

def _lifecycle_stage(row) -> str:
    if row["line_type"] == "genuine" and row.get("has_bvp_equivalent") and row["last_billing_year"] <= 2023:
        return "zombie"
    cagr = row.get("cagr_2yr")
    if pd.isna(cagr):
        return "mature"
    if row["first_billing_year"] >= 2024 and cagr > 0:
        return "emerging"
    if cagr > 0.15:
        return "growing"
    if cagr < -0.10:
        return "declining"
    if abs(cagr) <= 0.15:
        return "mature"
    return "mature"


def build_part_lifecycle() -> pd.DataFrame:
    df = attach_dimension_left(load_sales_mapped())
    df = df[df["line_type"].isin(["genuine", "bvp"])].copy()
    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype=str)
    genuine_with_bvp = set(xref["genuine_pn"].dropna().astype(str))

    rows = []
    for (pn, lt), g in df.groupby(["part_number", "line_type"]):
        by_year = g.groupby("year").agg(
            qty=("billed_qty", "sum"), rev=("net_sales_value", "sum")
        )
        if by_year.empty:
            continue
        peak_year = int(by_year["qty"].idxmax())
        first_y = int(by_year.index.min())
        last_y = int(by_year.index.max())
        cagr = np.nan
        yrs = sorted(by_year.index.astype(int))
        if len(yrs) >= 4:
            q1 = by_year.loc[yrs[0], "qty"] + by_year.loc[yrs[1], "qty"]
            q2 = by_year.loc[yrs[-2], "qty"] + by_year.loc[yrs[-1], "qty"]
            if q1 > 0 and q2 > 0:
                cagr = (q2 / q1) ** 0.5 - 1
        fam = g["product_family"].dropna().iloc[0] if g["product_family"].notna().any() else ""
        pms_cat = g["pms_category"].dropna().iloc[0] if g["pms_category"].notna().any() else None
        has_bvp = lt == "genuine" and pn in genuine_with_bvp
        rec = {
            "part_number": pn,
            "line_type": lt,
            "product_family": fam,
            "pms_category": pms_cat,
            "first_billing_year": first_y,
            "peak_billing_year": peak_year,
            "last_billing_year": last_y,
            "total_revenue_eur": round(float(g["net_sales_value"].sum()), 2),
            "cagr_2yr": round(float(cagr), 4) if pd.notna(cagr) else np.nan,
            "has_bvp_equivalent": has_bvp,
        }
        rec["lifecycle_stage"] = _lifecycle_stage(rec)
        rows.append(rec)
    return pd.DataFrame(rows)


# ── Contract 14 ─────────────────────────────────────────────────────────────

def build_revenue_concentration() -> pd.DataFrame:
    df = attach_dimension_left(load_sales_mapped())
    df = df[df["line_type"].isin(["genuine", "bvp"])].copy()
    rows = []
    for line_type in ("genuine", "bvp"):
        sub = df[df["line_type"] == line_type]
        for (dist, year), g in sub.groupby(["distributor_code", "year"]):
            pn_rev = (
                g.groupby("part_number")["net_sales_value"]
                .sum()
                .astype(float)
            )
            pn_rev = pn_rev[pn_rev > 0]
            if pn_rev.empty:
                continue
            total_rev = pn_rev.sum()
            top1 = pn_rev.max() / total_rev
            top10 = pn_rev.nlargest(min(10, len(pn_rev))).sum() / total_rev
            rows.append(
                {
                    "distributor_code": dist,
                    "year": int(year),
                    "line_type": line_type,
                    "gini_coefficient": round(gini_coefficient(pn_rev.values), 4),
                    "top10_rev_share": round(float(top10), 4),
                    "top1_rev_share": round(float(top1), 4),
                    "total_pns_billed": int(len(pn_rev)),
                    "total_revenue_eur": round(float(total_rev), 2),
                }
            )
    # total = genuine + bvp combined per PN
    for (dist, year), g in df.groupby(["distributor_code", "year"]):
        pn_rev = g.groupby("part_number")["net_sales_value"].sum().astype(float)
        pn_rev = pn_rev[pn_rev > 0]
        if pn_rev.empty:
            continue
        total_rev = pn_rev.sum()
        rows.append(
            {
                "distributor_code": dist,
                "year": int(year),
                "line_type": "total",
                "gini_coefficient": round(gini_coefficient(pn_rev.values), 4),
                "top10_rev_share": round(float(pn_rev.nlargest(min(10, len(pn_rev))).sum() / total_rev), 4),
                "top1_rev_share": round(float(pn_rev.max() / total_rev), 4),
                "total_pns_billed": int(len(pn_rev)),
                "total_revenue_eur": round(float(total_rev), 2),
            }
        )
    return pd.DataFrame(rows)


# ── Contract 5 ──────────────────────────────────────────────────────────────

def build_revenue_waterfall() -> pd.DataFrame:
    df = load_sales_tagged()
    gen = df[df["line_type"] == "genuine"].copy()
    agg = (
        gen.groupby(["distributor_code", "product_family", "year"])
        .agg(qty=("billed_qty", "sum"), rev=("net_sales_value", "sum"))
        .reset_index()
    )
    agg["asp"] = np.where(agg["qty"] > 0, agg["rev"] / agg["qty"], np.nan)
    rows = []
    for (dist, fam), g in agg.groupby(["distributor_code", "product_family"]):
        if pd.isna(fam) or not str(fam).strip():
            continue
        for y_from, y_to in ((2023, 2024), (2024, 2025)):
            a = g[g["year"] == y_from]
            b = g[g["year"] == y_to]
            if a.empty or b.empty:
                continue
            qa, ra = float(a["qty"].iloc[0]), float(a["rev"].iloc[0])
            qb, rb = float(b["qty"].iloc[0]), float(b["rev"].iloc[0])
            if ra <= 0 or rb <= 0:
                continue
            asp_a = ra / qa if qa else 0
            asp_b = rb / qb if qb else 0
            d_vol = (qb - qa) * asp_a
            d_price = (asp_b - asp_a) * qb
            d_tot = rb - ra
            d_mix = d_tot - d_vol - d_price
            rows.append(
                {
                    "distributor_code": dist,
                    "year_from": y_from,
                    "year_to": y_to,
                    "product_family": fam,
                    "delta_volume_eur": round(d_vol, 2),
                    "delta_price_eur": round(d_price, 2),
                    "delta_mix_eur": round(d_mix, 2),
                    "revenue_base_eur": round(ra, 2),
                    "revenue_end_eur": round(rb, 2),
                    "total_delta_eur": round(d_tot, 2),
                }
            )
    return pd.DataFrame(rows)


# ── Contract 13 ─────────────────────────────────────────────────────────────

def build_price_premium() -> pd.DataFrame:
    df = load_sales_tagged()
    df = df[df["pms_category"].notna() & (df["pms_category"] != "")]
    rows = []
    for (dist, cat, year), g in df.groupby(["distributor_code", "pms_category", "year"]):
        gen = g[g["line_type"] == "genuine"]
        bvp = g[g["line_type"] == "bvp"]
        g_units = int(gen["billed_qty"].sum())
        b_units = int(bvp["billed_qty"].sum())
        if g_units == 0 or b_units == 0:
            continue
        def _pn_asp(x: pd.DataFrame) -> float:
            q = x["billed_qty"].sum()
            return float(x["net_sales_value"].sum() / max(q, 1))

        gen_asp = gen.groupby("part_number", group_keys=False).apply(_pn_asp, include_groups=False)
        bvp_asp = bvp.groupby("part_number", group_keys=False).apply(_pn_asp, include_groups=False)
        g_asp = float(gen_asp.mean())
        b_asp = float(bvp_asp.mean())
        if b_asp <= 0:
            continue
        rows.append(
            {
                "distributor_code": dist,
                "pms_category": cat,
                "year": int(year),
                "genuine_asp_eur": round(g_asp, 2),
                "bvp_asp_eur": round(b_asp, 2),
                "price_premium_pct": round((g_asp - b_asp) / b_asp, 4),
                "genuine_unit_share": round(g_units / (g_units + b_units), 4),
                "genuine_units": g_units,
                "bvp_units": b_units,
                "n_genuine_pns": int(gen["part_number"].nunique()),
                "n_bvp_pns": int(bvp["part_number"].nunique()),
            }
        )
    return pd.DataFrame(rows)


# ── Contract 8 ─────────────────────────────────────────────────────────────

def build_basket_correlation() -> pd.DataFrame:
    df = load_sales_tagged()
    df = df[df["pms_category"].notna() & (df["pms_category"] != "")]
    df["billing_month"] = df["billing_date"].dt.to_period("M").astype(str)
    rows = []
    for (dist, year), g in df.groupby(["distributor_code", "year"]):
        monthly = (
            g.groupby(["billing_month", "pms_category"])["billed_qty"]
            .sum()
            .unstack(fill_value=0)
        )
        cats = sorted(monthly.columns.tolist())
        for i, ca in enumerate(cats):
            for cb in cats[i + 1 :]:
                a = monthly[ca].values.astype(float)
                b = monthly[cb].values.astype(float)
                co = int(((a > 0) & (b > 0)).sum())
                total_m = len(a)
                if co < 3:
                    continue
                r, p = stats.pearsonr(a, b)
                rows.append(
                    {
                        "distributor_code": dist,
                        "year": int(year),
                        "pms_cat_a": ca,
                        "pms_cat_b": cb,
                        "correlation": round(float(r), 4),
                        "co_order_months": co,
                        "total_months": total_m,
                        "p_value": round(float(p), 6),
                    }
                )
    return pd.DataFrame(rows)


# ── Contract 2 ──────────────────────────────────────────────────────────────

def build_substitution_timeline() -> pd.DataFrame:
    df = load_sales_tagged()
    df = df[df["line_type"].isin(["genuine", "bvp"])].copy()
    bvp_first = (
        df[df["line_type"] == "bvp"]
        .groupby(["product_family", "distributor_code"])["year"]
        .min()
        .rename("bvp_first_billing_year")
    )
    rows = []
    for (fam, dist, year), g in df.groupby(
        ["product_family", "distributor_code", "year"], dropna=False
    ):
        if pd.isna(fam):
            continue
        gen_u = int(g.loc[g["line_type"] == "genuine", "billed_qty"].sum())
        bvp_u = int(g.loc[g["line_type"] == "bvp", "billed_qty"].sum())
        denom = gen_u + bvp_u
        share = gen_u / denom if denom > 0 else np.nan
        key = (fam, dist)
        bfy = bvp_first.get(key, np.nan)
        ysi = int(year - bfy) if pd.notna(bfy) else np.nan
        pre = np.nan
        if pd.notna(bfy) and int(year) == int(bfy) - 1:
            pre = share
        elif pd.notna(bfy):
            prev = df[
                (df["product_family"] == fam)
                & (df["distributor_code"] == dist)
                & (df["year"] == int(bfy) - 1)
            ]
            if not prev.empty:
                gu = int(prev.loc[prev["line_type"] == "genuine", "billed_qty"].sum())
                bu = int(prev.loc[prev["line_type"] == "bvp", "billed_qty"].sum())
                pre = gu / (gu + bu) if (gu + bu) > 0 else np.nan
        rows.append(
            {
                "product_family": fam,
                "distributor_code": dist,
                "year": int(year),
                "genuine_units": gen_u,
                "bvp_units": bvp_u,
                "genuine_unit_share": round(float(share), 4) if pd.notna(share) else np.nan,
                "bvp_first_billing_year": int(bfy) if pd.notna(bfy) else np.nan,
                "years_since_bvp_entry": int(ysi) if pd.notna(ysi) else np.nan,
                "pre_entry_genuine_share": round(float(pre), 4) if pd.notna(pre) else np.nan,
            }
        )
    return pd.DataFrame(rows)


# ── Contract 11 ─────────────────────────────────────────────────────────────

def build_distributor_geo() -> pd.DataFrame:
    gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
    latest = gps.sort_values("year").groupby("distributor_code").tail(1)
    rows = []
    for _, r in latest.iterrows():
        country = str(r.get("country", "")).strip()
        region = str(r.get("region", "")).strip()
        lat, lon = COUNTRY_CENTROIDS.get(country, (np.nan, np.nan))
        rows.append(
            {
                "distributor_code": r["distributor_code"],
                "country": country,
                "lat": lat,
                "lon": lon,
                "territory_label": REGION_TERRITORY.get(region, region or country),
            }
        )
    return pd.DataFrame(rows)


# ── Contract 15 ─────────────────────────────────────────────────────────────

def build_capture_recovery_model(price_premium: pd.DataFrame | None = None) -> pd.DataFrame:
    pms = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
    tot = pms[pms["line_type"] == "total"].copy()
    latest_year = int(tot["year"].max())
    tot = tot[tot["year"] == latest_year]
    bvp = pms[(pms["line_type"] == "bvp") & (pms["year"] == latest_year)]
    bvp_share = (
        bvp.groupby(["distributor_code", "pms_category"])
        .agg(bvp_qty=("actual_qty", "sum"))
        .reset_index()
    )
    if price_premium is None:
        pp_path = DERIVED_DIR / "price_premium.csv"
        price_premium = pd.read_csv(pp_path) if pp_path.exists() else pd.DataFrame()
    pp_latest = (
        price_premium[price_premium["year"] == latest_year]
        if not price_premium.empty and "year" in price_premium.columns
        else pd.DataFrame()
    )
    dim = pd.read_csv(BVP_PN_DIMENSION_CSV)
    gen_cats = set(
        dim.loc[(dim["line_type"] == "genuine") & dim["pms_category"].notna(), "pms_category"]
    )

    rows = []
    for _, r in tot.iterrows():
        dist, cat = r["distributor_code"], r["pms_category"]
        exp_q = float(r["expected_qty"])
        act_q = float(r["actual_qty"])
        gap = int(max(exp_q - act_q, 0))
        bs = bvp_share[
            (bvp_share["distributor_code"] == dist) & (bvp_share["pms_category"] == cat)
        ]
        bvp_u = float(bs["bvp_qty"].iloc[0]) if not bs.empty else 0.0
        total_u = act_q if act_q > 0 else 1.0
        bvp_unit_share = bvp_u / (bvp_u + max(act_q - bvp_u, 0)) if (bvp_u + act_q) > 0 else 0.0
        pp = pp_latest[
            (pp_latest["distributor_code"] == dist) & (pp_latest["pms_category"] == cat)
        ]
        g_asp = float(pp["genuine_asp_eur"].iloc[0]) if not pp.empty else float(r.get("avg_sp_eur", 0))
        b_asp = float(pp["bvp_asp_eur"].iloc[0]) if not pp.empty else g_asp * 0.85
        if bvp_u > 0 and bvp_unit_share > 0.05:
            gap_type = "substitution"
        elif cat not in gen_cats and exp_q > 0:
            gap_type = "catalog_gap"
        else:
            gap_type = "under_service"
        rows.append(
            {
                "distributor_code": dist,
                "pms_category": cat,
                "year": latest_year,
                "capture_rate_actual": round(float(r["capture_rate"]), 4),
                "expected_qty": int(round(exp_q)),
                "actual_qty": int(round(act_q)),
                "avg_sp_genuine_eur": round(g_asp, 2),
                "avg_sp_bvp_eur": round(b_asp, 2),
                "bvp_unit_share": round(bvp_unit_share, 4),
                "gap_units": gap,
                "gap_type": gap_type,
                "gap_revenue_at_genuine": round(gap * g_asp, 2),
            }
        )
    return pd.DataFrame(rows)
