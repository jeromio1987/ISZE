"""
ISZE Competitive BI — engine (swappable brain).

Every constant is read from source sheets passed by bi_shell.py loaders.
See SPEC.md for the compute_view() contract.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).parent

# Description → PMS category (ITUK pilot basket). AIM_Category alone cannot split
# brake front/rear; patterns mirror ITUK_PMS_Analysis / PMS Coverage part names.
PN_TO_PMS_CATEGORY: list[tuple[str, str]] = [
    (r"oil filter|element[;,].*oil", "Oil filter"),
    (r"fuel filter|element.*fuel filter|element[;,].*fuel", "Fuel filter"),
    (r"air filter|air cleaner|filter[;,]\s*acl", "Air filter"),
    (r"cabin filter|blower unit", "Cabin filter"),
    (r"clutch kit|clutch.*disc", "Clutch disc"),
    (r"pressure plate", "Pressure plate"),
    (r"release bearing", "Release bearing"),
    (r"pad kit.*frt|pad.*caliper.*frt|pad.*disc.*brk.*frt", "Brake pad (front)"),
    (r"pad kit.*disc brk.*w/o shim", "Brake pad (front)"),
    (r"pad kit.*rr|pad.*disc.*brk.*rr", "Brake pad (rear)"),
    (r"rotor.*disc.*brk.*frt", "Brake disc (front)"),
    (r"rotor.*disc.*brk.*rr", "Brake disc (rear)"),
    (r"lining.*brk|brake lining", "Brake lining"),
]

# Defaults; overridden via sources.yaml fx_rates in compute_view / normalize_scraped_prices
GBP_EUR = 1.17
SEK_EUR = 0.089

ENGINE_METHODOLOGY_NOTE = (
    "ITUK tab: PMS Calc intervals × UIO (whole-fleet assumptions). "
    "All distributors tab: PRISM expected_qty (typically scope=N75_only). "
    "Do not compare potential_units across tabs."
)


def _num(val: Any) -> float | None:
    try:
        v = float(val)
        return v if pd.notna(v) else None
    except (TypeError, ValueError):
        return None


def parse_pms_assumptions(pms_sheets: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, float]]:
    """Read PMS part table + general parameters from PMS Calc Assumptions sheet."""
    raw = pms_sheets.get("Assumptions")
    defaults = {
        "annual_mileage_km": 80_000.0,
        "horizon_years": 5.0,
        "potential_uio_factor": 0.5,
        "base_year": 2024.0,
        "mileage_source": "default (80,000 km/yr — Assumptions sheet missing row)",
    }
    if raw is None or raw.empty:
        return pd.DataFrame(), defaults

    for i in range(len(raw)):
        label = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
        val = _num(raw.iloc[i, 1])
        if val is None:
            continue
        low = label.lower()
        if "annual mileage" in low:
            defaults["annual_mileage_km"] = val
            defaults["mileage_source"] = "PMS Calc Assumptions sheet"
        elif "uio horizon" in low:
            defaults["horizon_years"] = val
        elif "potential uio factor" in low:
            defaults["potential_uio_factor"] = val
        elif "base year" in low:
            defaults["base_year"] = val

    parts: list[dict[str, Any]] = []
    for i in range(len(raw)):
        name = raw.iloc[i, 0]
        if not isinstance(name, str) or not name.strip():
            continue
        if name.strip().lower() in ("part type / name", "legend:"):
            continue
        interval = _num(raw.iloc[i, 1])
        pcs = _num(raw.iloc[i, 2])
        freq = _num(raw.iloc[i, 3])
        if interval is None or pcs is None or freq is None:
            continue
        if interval < 1000:  # skip non-part rows
            continue
        parts.append(
            {
                "category": name.strip(),
                "interval_km": interval,
                "parts_per_service": pcs,
                "annual_freq": freq,
                "annual_pieces_per_vehicle": freq * pcs,
            }
        )

    return pd.DataFrame(parts), defaults


def parse_pms_coverage_uio(pms_sheets: dict[str, pd.DataFrame]) -> float | None:
    """ITUK pilot potential units from PMS Coverage sheet (Step 2)."""
    raw = pms_sheets.get("PMS Coverage")
    if raw is None or raw.empty:
        return None
    for i in range(len(raw)):
        pot = _num(raw.iloc[i, 3])
        if pot is not None and 5_000 < pot < 50_000:
            return pot
    return None


def parse_survival_rates(uio_sheets: dict[str, pd.DataFrame]) -> dict[str, dict[int, float]]:
    """Parse v17 sheet 3 survival tables."""
    raw = uio_sheets.get("3. UIO Calculation")
    out: dict[str, dict[int, float]] = {
        "CV_DEV": {},
        "CV_EMG": {},
        "LCV": {},
    }
    if raw is None or raw.empty:
        return out

    col_map: dict[str, int] = {}
    for i in range(min(8, len(raw))):
        row = raw.iloc[i]
        for j, cell in enumerate(row):
            s = str(cell) if pd.notna(cell) else ""
            if "CV" in s and "Developed" in s:
                col_map["CV_DEV"] = j
            elif "CV" in s and "Emerging" in s:
                col_map["CV_EMG"] = j
            elif "LCV" in s:
                col_map["LCV"] = j

    for i in range(len(raw)):
        age = _num(raw.iloc[i, 1])
        if age is None or age < 1 or age > 25:
            continue
        for key, j in col_map.items():
            rate = _num(raw.iloc[i, j])
            if rate is not None:
                out[key][int(age)] = rate
    return out


def load_uio_by_distributor(
    uio_sheets: dict[str, pd.DataFrame],
    survival: dict[str, dict[int, float]],
    base_year: int = 2024,
) -> pd.DataFrame:
    """Active UIO per distributor from v17 sheet 1 + survival sheet 3."""
    raw = uio_sheets.get("1.UIO Overview")
    if raw is None or raw.empty or len(raw) < 7:
        return pd.DataFrame(columns=["Distributor", "active_uio"])

    header_row = None
    for i in range(min(12, len(raw))):
        row = [str(c).strip() if pd.notna(c) else "" for c in raw.iloc[i]]
        if "Distributor" in row:
            header_row = i
            break
    if header_row is None:
        return pd.DataFrame(columns=["Distributor", "active_uio"])

    headers = [str(c).replace("\n", " ").strip() if pd.notna(c) else f"col_{j}" for j, c in enumerate(raw.iloc[header_row])]
    df = raw.iloc[header_row + 1 :].copy()
    df.columns = headers
    df = df.rename(columns={c: str(c).replace("\n", " ").strip() for c in df.columns})

    year_cols = [c for c in df.columns if str(c).isdigit()]
    if not year_cols:
        return pd.DataFrame(columns=["Distributor", "active_uio"])

    current_year = max(int(c) for c in year_cols)
    cv_col = "CV/ LCV" if "CV/ LCV" in df.columns else next((c for c in df.columns if "LCV" in c), "CV/ LCV")

    rows = []
    for _, r in df.iterrows():
        dist = str(r.get("Distributor", "")).strip()
        if not dist or dist.lower() == "nan":
            continue
        cv_lcv = str(r.get(cv_col, "CV")).strip().upper()
        surv = survival.get("LCV", {}) if cv_lcv == "LCV" else survival.get("CV_DEV", {})
        active = 0.0
        for yc in year_cols:
            v = _num(r.get(yc))
            if v is None or v <= 0:
                continue
            age = current_year - int(yc) + 1
            active += v * surv.get(age, 0.0)
        rows.append({"Distributor": dist, "active_uio": active})

    if not rows:
        return pd.DataFrame(columns=["Distributor", "active_uio"])
    return (
        pd.DataFrame(rows)
        .groupby("Distributor", as_index=False)["active_uio"]
        .sum()
        .sort_values("active_uio", ascending=False)
    )


def resolve_uio_scope(
    market_scope: str,
    distributor: str | None,
    uio_by_dist: pd.DataFrame,
    pms_sheets: dict[str, pd.DataFrame],
    pms_defaults: dict[str, float],
    *,
    ituk_uio_source: str = "pms_calc",
    uio_sheets: dict[str, pd.DataFrame] | None = None,
    paths: dict[str, Path] | None = None,
    sales_year: int = 2024,
    cfg: dict[str, Any] | None = None,
) -> tuple[float, str, float]:
    """
    Returns (uio_scope, scope_label, potential_factor_applied).
    uio_scope = vehicles used in potential demand (after horizon/factor where applicable).
    """
    factor = pms_defaults.get("potential_uio_factor", 0.5)
    horizon = pms_defaults.get("horizon_years", 5.0)

    if market_scope == "ITUK (PMS Calc pilot)":
        src = (ituk_uio_source or "pms_calc").lower().replace("-", "_")
        if src in ("smmt", "smmt_car_park", "smmt_2024", "prism_smmt", "smtt"):
            try:
                from sources_loader import parse_ituk_car_park_uio

                yaml_def = (cfg or {}).get("defaults") or {}
                smmt_year = int(yaml_def.get("ituk_smmt_car_park_year", 2024))
                val, label = parse_ituk_car_park_uio(uio_sheets or {}, smmt_year, paths)
                if val is not None:
                    return val, label, factor
            except ImportError:
                pass
            return 0.0, "ITUK — SMMT car park (sheet 4 not loaded)", factor
        if src in ("v17", "v17_survival", "survival", "v17 survival"):
            if not uio_by_dist.empty:
                match = uio_by_dist[uio_by_dist["Distributor"] == "ITUK"]
                raw_uio = float(match["active_uio"].sum()) if len(match) else 0.0
                return (
                    raw_uio,
                    "ITUK — v17 survival-adjusted (sheet 1 cohort math, not SMMT car park)",
                    factor,
                )
            return 0.0, "ITUK — v17 (no ITUK row)", factor
        pot = parse_pms_coverage_uio(pms_sheets)
        if pot is not None:
            return pot, "ITUK — PMS Coverage Step 2", factor
        if not uio_by_dist.empty:
            match = uio_by_dist[uio_by_dist["Distributor"] == "ITUK"]
            raw_uio = float(match["active_uio"].sum()) if len(match) else 0.0
            return raw_uio * factor, "ITUK — survival-adjusted × potential factor (fallback)", factor
        return 0.0, "ITUK", factor

    if market_scope == "Pan-European (all distributors)":
        raw = float(uio_by_dist["active_uio"].sum()) if not uio_by_dist.empty else 0.0
        return raw * factor, "Pan-EU — active UIO × potential factor", factor

    if distributor and not uio_by_dist.empty:
        match = uio_by_dist[uio_by_dist["Distributor"] == distributor]
        raw = float(match["active_uio"].sum()) if len(match) else 0.0
        return raw * factor, distributor, factor

    return 0.0, market_scope, factor


def classify_pms_category(description: str) -> str | None:
    if not isinstance(description, str):
        return None
    d = description.lower()
    for pattern, category in PN_TO_PMS_CATEGORY:
        if re.search(pattern, d, re.IGNORECASE):
            return category
    return None


def report_unmapped_pms_pns(v3: pd.DataFrame, pms_basket: str) -> pd.DataFrame:
    """PNs in basket with no description→PMS category (regex gap)."""
    if v3.empty or "Description" not in v3.columns:
        return pd.DataFrame()
    work = v3.copy()
    if pms_basket == "Maintenance (AIM_DemandType)":
        work = work[work["AIM_DemandType"] == "Maintenance"].copy()
    elif pms_basket == "Maintenance + Wear Repair (PMS pilot)":
        work = work[work["AIM_DemandType"].isin(["Maintenance", "Wear Repair"])].copy()
    work["pms_category"] = work["Description"].apply(classify_pms_category)
    miss = work[work["pms_category"].isna()].copy()
    cols = [c for c in ("PN", "Description", "AIM_DemandType", "AIM_Category", "Rev_CY2025_EUR") if c in miss.columns]
    return miss[cols].head(200) if cols else miss.head(200)


def normalize_scraped_prices(
    scraped: pd.DataFrame,
    fx: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Convert wide prefixed scraper merge into per-PN best AM price + brand."""
    if scraped.empty or "PN" not in scraped.columns:
        return pd.DataFrame()
    gbp_eur = float((fx or {}).get("GBP_EUR", GBP_EUR))
    sek_eur = float((fx or {}).get("SEK_EUR", SEK_EUR))

    def _clean_prices(s: Any, floor: float = 3.0) -> float | None:
        if not isinstance(s, str):
            return None
        vals = []
        for p in s.split("|"):
            try:
                v = float(p.strip())
                if v >= floor:
                    vals.append(v)
            except ValueError:
                pass
        return min(vals) if vals else None

    pn = scraped[["PN"]].copy()
    sources: list[pd.DataFrame] = []

    ad_all = "AD_UK__Autodoc_AllPrices_GBP"
    ad_min = "AD_UK__Autodoc_MinPrice_GBP"
    if ad_all in scraped.columns or ad_min in scraped.columns:
        df = pn.copy()
        if ad_all in scraped.columns:
            df["price"] = scraped[ad_all].apply(_clean_prices)
        else:
            df["price"] = pd.to_numeric(scraped[ad_min], errors="coerce")
            df.loc[df["price"] < 3, "price"] = None
        df["price_eur"] = df["price"] * gbp_eur
        df["brand"] = scraped.get("AD_UK__Autodoc_CheapestBrand")
        df["source"] = "AD_UK"
        sources.append(df)

    ks_am = "KS__KS_AM_MinPrice_GBP"
    if ks_am in scraped.columns:
        df = pn.copy()
        df["price"] = pd.to_numeric(scraped[ks_am], errors="coerce")
        df.loc[df["price"] < 3, "price"] = None
        df["price_eur"] = df["price"] * gbp_eur
        df["brand"] = scraped.get("KS__KS_AM_SKUs")
        df["source"] = "KS_AM"
        sources.append(df)

    ks_gen = "KS__KS_GEN_MinPrice_GBP"
    if ks_gen in scraped.columns:
        df = pn.copy()
        df["price"] = pd.to_numeric(scraped[ks_gen], errors="coerce")
        df.loc[df["price"] < 3, "price"] = None
        df["price_eur"] = df["price"] * gbp_eur
        df["brand"] = scraped.get("KS__KS_GEN_SKUs")
        df["source"] = "KS_GEN"
        sources.append(df)

    mek = "MEK__MEK_AM_MinPrice_SEK"
    if mek in scraped.columns:
        df = pn.copy()
        df["price"] = pd.to_numeric(scraped[mek], errors="coerce")
        df.loc[df["price"] < 3, "price"] = None
        df["price_eur"] = df["price"] * sek_eur
        df["brand"] = scraped.get("MEK__MEK_AM_Brands")
        df["source"] = "MEK"
        sources.append(df)

    if not sources:
        return pd.DataFrame()

    merged = sources[0]
    for s in sources[1:]:
        merged = pd.concat([merged, s], ignore_index=True)

    merged = merged.dropna(subset=["price_eur"])
    if merged.empty:
        return pd.DataFrame()

    idx = merged.groupby("PN")["price_eur"].idxmin()
    best = merged.loc[idx].copy()
    best = best.rename(
        columns={
            "price_eur": "competitor_min_price_eur",
            "brand": "competitor_brand",
            "source": "competitor_source",
        }
    )
    return best[["PN", "competitor_min_price_eur", "competitor_brand", "competitor_source"]]


def _resolve_pms_intervals(
    pms_sheets: dict[str, pd.DataFrame],
    cfg: dict[str, Any] | None = None,
    paths: dict[str, Path] | None = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """PMS parts table: yaml override first, else PMS Calc Assumptions sheet."""
    if cfg and paths:
        try:
            from sources_loader import load_pms_parts_from_yaml

            yaml_parts = load_pms_parts_from_yaml(paths, cfg)
            if yaml_parts is not None and not yaml_parts.empty:
                _, defaults = parse_pms_assumptions(pms_sheets)
                return yaml_parts, defaults
        except ImportError:
            pass
    return parse_pms_assumptions(pms_sheets)


def _effective_gp_pct(sub: pd.DataFrame, default_gp: float) -> float:
    """PR00-weighted GP% when pms rows carry gp_pct; else flat default."""
    if "gp_pct" not in sub.columns:
        return float(default_gp)
    w = pd.to_numeric(sub.get("PR00_EUR"), errors="coerce").fillna(0)
    gp = pd.to_numeric(sub["gp_pct"], errors="coerce").fillna(default_gp)
    if w.sum() > 0:
        return float((w * gp).sum() / w.sum())
    if gp.notna().any():
        return float(gp.mean())
    return float(default_gp)


def _category_aggregate(
    pms: pd.DataFrame,
    pms_intervals: pd.DataFrame,
    uio_scope: float,
    horizon: float,
    isze_gp_pct: float,
    qty_col: str,
) -> pd.DataFrame:
    cat_rows: list[dict[str, Any]] = []
    for _, cat_row in pms_intervals.iterrows():
        cat = cat_row["category"]
        sub = pms[pms["category"] == cat]
        if sub.empty:
            continue
        annual_pieces = float(cat_row["annual_pieces_per_vehicle"])
        potential_units = uio_scope * annual_pieces * horizon
        actual_units = float(sub["actual_units"].sum()) if "actual_units" in sub.columns else 0.0
        lost_units = max(potential_units - actual_units, 0.0)
        over_capture_units = max(actual_units - potential_units, 0.0)
        avg_pr00 = float(sub["PR00_EUR"].mean()) if "PR00_EUR" in sub.columns else 0.0
        lost_revenue = lost_units * avg_pr00
        cat_gp_pct = _effective_gp_pct(sub, isze_gp_pct)
        lost_isze_gp = lost_revenue * cat_gp_pct
        cat_rows.append(
            {
                "category": cat,
                "pns": len(sub),
                "annual_freq": cat_row["annual_freq"],
                "parts_per_service": cat_row["parts_per_service"],
                "annual_pieces_per_vehicle": annual_pieces,
                "uio_scope": uio_scope,
                "horizon_years": horizon,
                "potential_units": potential_units,
                "actual_units": actual_units,
                "lost_units": lost_units,
                "over_capture_units": over_capture_units,
                "capture_rate": (actual_units / potential_units) if potential_units > 0 else 0.0,
                "avg_pr00": avg_pr00,
                "gp_pct": cat_gp_pct,
                "lost_revenue": lost_revenue,
                "lost_isze_gp": lost_isze_gp,
            }
        )
    out = pd.DataFrame(cat_rows)
    if not out.empty:
        out = out.sort_values("lost_isze_gp", ascending=False)
    return out


def compute_pms_by_model(
    category_view: pd.DataFrame,
    uio_sheets: dict[str, pd.DataFrame],
    pms_sheets: dict[str, pd.DataFrame] | None = None,
    *,
    market_scope: str = "ITUK (PMS Calc pilot)",
    car_park_year: int = 2024,
) -> dict[str, pd.DataFrame]:
    """
    Allocate category-level PMS engine results to ITUK models by car-park UIO share.

    Until PN-level model mapping exists, actuals and potentials are proportional
    to v17 sheet 4 §G model mix (not N75-only PRISM scope).
    """
    try:
        from sources_loader import parse_ituk_models_car_park, parse_pms_calc_model_uio
    except ImportError:
        return {
            "PMS by model (summary)": pd.DataFrame(),
            "PMS by model (detail)": pd.DataFrame(),
            "ITUK car park by model": pd.DataFrame(),
        }

    models = parse_ituk_models_car_park(uio_sheets, year=car_park_year)
    pms_uio = parse_pms_calc_model_uio(pms_sheets or {}) if pms_sheets else pd.DataFrame()
    if not models.empty and not pms_uio.empty:
        models = models.merge(pms_uio, on="model", how="left")

    if models.empty:
        return {
            "PMS by model (summary)": pd.DataFrame(),
            "PMS by model (detail)": pd.DataFrame(),
            "ITUK car park by model": pd.DataFrame(),
            "PMS by model (note)": pd.DataFrame(
                [{"message": "No ITUK model rows in v17 sheet 4 §G."}]
            ),
        }

    fleet = models[~models["model"].isin(("Total ITUK",))].copy()
    fleet_uio = float(fleet["car_park_uio"].sum()) if "car_park_uio" in fleet.columns else 0.0
    if fleet_uio <= 0:
        fleet["model_share"] = 0.0
    else:
        fleet["model_share"] = fleet["car_park_uio"] / fleet_uio

    model_mileage = pd.DataFrame()
    try:
        from sources_loader import load_pms_model_mileage

        cfg_path = SCRIPT_DIR / "sources.yaml"
        if cfg_path.exists():
            import yaml

            with cfg_path.open(encoding="utf-8") as f:
                cfg_doc = yaml.safe_load(f) or {}
            from sources_loader import resolve_paths

            model_mileage = load_pms_model_mileage(resolve_paths(cfg_doc), cfg_doc)
            if not model_mileage.empty:
                fleet = fleet.merge(
                    model_mileage[["model", "annual_mileage_km", "mileage_factor", "tonnage_class"]],
                    on="model",
                    how="left",
                    suffixes=("", "_yaml"),
                )
                if "tonnage_class_yaml" in fleet.columns:
                    fleet["tonnage_class"] = fleet["tonnage_class"].fillna(fleet["tonnage_class_yaml"])
                    fleet = fleet.drop(columns=["tonnage_class_yaml"])
                fleet["mileage_factor"] = pd.to_numeric(
                    fleet.get("mileage_factor"), errors="coerce"
                ).fillna(1.0)
                fleet["annual_mileage_km"] = pd.to_numeric(
                    fleet.get("annual_mileage_km"), errors="coerce"
                ).fillna(fleet.get("recommended_km_yr", 80_000))
    except ImportError:
        pass

    alloc_note = (
        "Proportional allocation: category totals × (model car park UIO / fleet UIO), "
        "potentials scaled by per-model mileage from pms_parts_config.yaml. "
        "Replace with PN×model actuals when available. Not PRISM N75_only scope."
    )

    if category_view is None or category_view.empty:
        summary = fleet.copy()
        summary["allocation_method"] = alloc_note
        return {
            "PMS by model (summary)": summary,
            "PMS by model (detail)": pd.DataFrame(),
            "ITUK car park by model": models,
            "PMS by model (note)": pd.DataFrame([{"message": alloc_note}]),
        }

    if not market_scope.startswith("ITUK"):
        note = pd.DataFrame(
            [
                {
                    "message": (
                        "Model allocation shown for ITUK car park reference. "
                        "Switch sidebar scope to ITUK for aligned category totals."
                    )
                }
            ]
        )
        return {
            "PMS by model (summary)": fleet,
            "PMS by model (detail)": pd.DataFrame(),
            "ITUK car park by model": models,
            "PMS by model (note)": note,
        }

    detail_rows: list[dict[str, Any]] = []
    for _, mrow in fleet.iterrows():
        share = float(mrow["model_share"])
        mileage_factor = float(mrow.get("mileage_factor", 1.0) or 1.0)
        for _, crow in category_view.iterrows():
            pot = float(crow.get("potential_units", 0) or 0) * share * mileage_factor
            act = float(crow.get("actual_units", 0) or 0) * share
            lost = max(pot - act, 0.0) if pot > act else float(crow.get("lost_units", 0) or 0) * share
            detail_rows.append(
                {
                    "model": mrow["model"],
                    "tonnage_class": mrow.get("tonnage_class"),
                    "car_park_uio": mrow.get("car_park_uio"),
                    "model_share": share,
                    "recommended_km_yr": mrow.get("recommended_km_yr"),
                    "annual_mileage_km": mrow.get("annual_mileage_km"),
                    "mileage_factor": mileage_factor,
                    "category": crow.get("category"),
                    "potential_units": pot,
                    "actual_units": act,
                    "lost_units": lost,
                    "lost_isze_gp": float(crow.get("lost_isze_gp", 0) or 0) * share * mileage_factor,
                    "capture_rate": (act / pot) if pot > 0 else None,
                    "allocation_method": alloc_note,
                    "pms_calc_potential_uio": mrow.get("pms_calc_potential_uio"),
                }
            )

    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return {
            "PMS by model (summary)": fleet,
            "PMS by model (detail)": detail,
            "ITUK car park by model": models,
            "PMS by model (note)": pd.DataFrame([{"message": alloc_note}]),
        }

    summary = (
        detail.groupby(["model", "tonnage_class"], as_index=False)
        .agg(
            car_park_uio=("car_park_uio", "first"),
            model_share=("model_share", "first"),
            recommended_km_yr=("recommended_km_yr", "first"),
            potential_units=("potential_units", "sum"),
            actual_units=("actual_units", "sum"),
            lost_units=("lost_units", "sum"),
            lost_isze_gp=("lost_isze_gp", "sum"),
            categories=("category", "nunique"),
            allocation_method=("allocation_method", "first"),
        )
    )
    summary["capture_rate"] = summary["actual_units"] / summary["potential_units"].replace(0, np.nan)
    summary = summary.sort_values("lost_isze_gp", ascending=False)

    total_row = models[models["model"] == "Total ITUK"]
    if not total_row.empty:
        models = models.copy()
        models["pct_of_ituk_total"] = models["car_park_uio"] / float(
            total_row["car_park_uio"].iloc[0]
        )

    return {
        "PMS by model (summary)": summary,
        "PMS by model (detail)": detail.sort_values(["model", "lost_isze_gp"], ascending=[True, False]),
        "ITUK car park by model": models,
        "PMS by model (note)": pd.DataFrame([{"message": alloc_note}]),
    }


def compute_pms_all_distributors(
    v3: pd.DataFrame,
    uio_sheets: dict[str, pd.DataFrame],
    pms_sheets: dict[str, pd.DataFrame],
    *,
    period_type: str = "CY",
    sales_year: int = 2025,
    isze_gp_pct: float = 0.35,
    horizon_years: float = 1.0,
    pms_basket: str = "Maintenance + Wear Repair (PMS pilot)",
    cfg: dict[str, Any] | None = None,
    paths: dict[str, Path] | None = None,
    data_mode: str = "auto",
) -> dict[str, Any]:
    """
    PMS capture for all distributors.

    data_mode:
      - auto: use PRISM pms_capture_by_db_year.csv if present, else v17 UIO + v3 qty
      - prism: force PRISM derived file only
      - computed: force v17 survival UIO + v3 (global qty per DB — approximate)
    """
    cfg = cfg or {}
    paths = paths or {}
    period_type = (period_type or "CY").upper()
    year = int(sales_year)

    try:
        from sources_loader import (
            load_pms_capture_derived,
            load_ituk_dealer_sales,
            sales_column_names,
            attach_actual_qty,
            v17_name_to_db_code,
        )
    except ImportError:
        return {"error": pd.DataFrame([{"message": "sources_loader.py missing"}])}

    pms_intervals, pms_defaults = _resolve_pms_intervals(pms_sheets, cfg, paths)
    if pms_intervals.empty:
        return {"error": pd.DataFrame([{"message": "No PMS intervals (yaml or PMS Calc)."}])}

    prism_path = paths.get("pms_capture_by_db")
    use_prism = data_mode == "prism" or (
        data_mode == "auto" and prism_path is not None and prism_path.exists()
    )

    if use_prism:
        detail = load_pms_capture_derived(paths, year, period_type, line_type="total")
        if detail.empty:
            return {
                "error": pd.DataFrame(
                    [{"message": f"No rows in PRISM derived for year={year}. Re-run PRISM pipeline."}]
                )
            }
        detail["lost_isze_gp"] = detail["revenue_gap_eur"] * isze_gp_pct
        agg_spec: dict[str, Any] = {
            "uio_scope": ("uio_scope", "first"),
            "total_potential": ("potential_units", "sum"),
            "total_actual": ("actual_units", "sum"),
            "total_lost_gp": ("lost_isze_gp", "sum"),
            "categories": ("category", "nunique"),
            "data_source": ("data_source", "first"),
        }
        if "prism_scope" in detail.columns:
            agg_spec["prism_scope"] = ("prism_scope", "first")
        if "prism_uio_source" in detail.columns:
            agg_spec["prism_uio_source"] = ("prism_uio_source", "first")
        summary = detail.groupby("distributor", as_index=False).agg(**agg_spec)
        summary["overall_capture_rate"] = summary["total_actual"] / summary["total_potential"].replace(0, np.nan)
        summary["period_type"] = period_type
        summary["sales_year"] = year
        summary["methodology_note"] = detail["methodology_note"].iloc[0] if "methodology_note" in detail.columns else ""
        return {
            "PMS by distributor (detail)": detail,
            "PMS by distributor (summary)": summary.sort_values("total_lost_gp", ascending=False),
            "data_mode": pd.DataFrame(
                [
                    {
                        "mode": "PRISM derived",
                        "file": str(prism_path),
                        "scope_note": "Typically N75_only — not comparable to ITUK PMS Calc tab",
                    }
                ]
            ),
        }

    # ── Computed path: each v17 distributor with survival UIO ────────────────
    survival = parse_survival_rates(uio_sheets)
    base_year = int(pms_defaults.get("base_year", 2024))
    uio_by_dist = load_uio_by_distributor(uio_sheets, survival, base_year)
    factor = pms_defaults.get("potential_uio_factor", 0.5)
    aliases = cfg.get("distributor_aliases") or {}
    qty_col, _ = sales_column_names(period_type, year)

    work = v3.copy()
    for c in ("PR00_EUR", qty_col, f"Rev_CY{year}_EUR"):
        if c and c in work.columns:
            work[c] = pd.to_numeric(work[c], errors="coerce")
    work["category"] = work["Description"].apply(classify_pms_category)
    work = work[work["category"].isin(set(pms_intervals["category"]))].copy()
    if pms_basket == "Maintenance (AIM_DemandType)":
        work = work[work["AIM_DemandType"] == "Maintenance"].copy()
    elif pms_basket == "Maintenance + Wear Repair (PMS pilot)":
        work = work[work["AIM_DemandType"].isin(["Maintenance", "Wear Repair"])].copy()

    detail_rows: list[pd.DataFrame] = []
    for _, urow in uio_by_dist.iterrows():
        dist_name = str(urow["Distributor"])
        if not dist_name or dist_name.lower() == "nan" or dist_name.isdigit():
            continue
        db_code = v17_name_to_db_code(dist_name, aliases)
        uio_scope = float(urow["active_uio"]) * factor

        dist_sales = None
        if db_code == "ITUK":
            dist_sales = load_ituk_dealer_sales(paths, cfg, year, period_type)

        pms = attach_actual_qty(work, work, qty_col, dist_sales, db_code)
        cat = _category_aggregate(pms, pms_intervals, uio_scope, horizon_years, isze_gp_pct, qty_col or "")
        if cat.empty:
            continue
        cat["distributor"] = dist_name
        cat["distributor_code"] = db_code
        cat["data_source"] = (
            f"dealer sales ({dist_sales['data_source'].iloc[0]})"
            if dist_sales is not None and not dist_sales.empty
            else f"v3 global ({qty_col}) — same qty all DBs"
        )
        detail_rows.append(cat)

    if not detail_rows:
        return {"error": pd.DataFrame([{"message": "No distributor rows computed."}])}

    detail = pd.concat(detail_rows, ignore_index=True)
    detail = detail.rename(
        columns={
            "potential_units": "potential_units",
            "actual_units": "actual_units",
            "lost_units": "lost_units",
            "lost_isze_gp": "lost_isze_gp",
        }
    )
    summary = (
        detail.groupby("distributor", as_index=False)
        .agg(
            uio_scope=("uio_scope", "first"),
            total_potential=("potential_units", "sum"),
            total_actual=("actual_units", "sum"),
            total_lost_gp=("lost_isze_gp", "sum"),
            categories=("category", "nunique"),
            data_source=("data_source", "first"),
        )
    )
    summary["overall_capture_rate"] = summary["total_actual"] / summary["total_potential"].replace(0, np.nan)
    summary["period_type"] = period_type
    summary["sales_year"] = year

    return {
        "PMS by distributor (detail)": detail,
        "PMS by distributor (summary)": summary.sort_values("total_lost_gp", ascending=False),
        "data_mode": pd.DataFrame(
            [{"mode": "computed (v17 UIO)", "note": "Use PRISM derived for DB-specific actuals"}]
        ),
    }


def compute_view(
    v3: pd.DataFrame,
    uio_sheets: dict[str, pd.DataFrame],
    pms_sheets: dict[str, pd.DataFrame],
    scraped: pd.DataFrame,
    *,
    market_scope: str = "ITUK (PMS Calc pilot)",
    distributor: str | None = None,
    isze_gp_pct: float = 0.35,
    horizon_years: float | None = None,
    pms_basket: str = "Maintenance + Wear Repair (PMS pilot)",
    period_type: str = "CY",
    sales_year: int = 2025,
    cfg: dict[str, Any] | None = None,
    paths: dict[str, Path] | None = None,
    pms_data_mode: str = "auto",
    ituk_uio_source: str = "pms_calc",
) -> dict[str, Any]:
    """
    Build category / PN / brand views per SPEC.md.

    market_scope: ITUK (PMS Calc pilot) | Pan-European (all distributors) | <distributor name>
    period_type: CY (v3 columns) or FY (PRISM derived / dealer sales when available)
    """
    period_type = (period_type or "CY").upper()
    year = int(sales_year)
    pms_intervals, pms_defaults = _resolve_pms_intervals(pms_sheets, cfg, paths)
    if pms_intervals.empty:
        return {"error": pd.DataFrame([{"message": "Could not parse PMS Assumptions sheet."}])}

    horizon = horizon_years if horizon_years is not None else pms_defaults.get("horizon_years", 1.0)
    survival = parse_survival_rates(uio_sheets)
    uio_by_dist = load_uio_by_distributor(uio_sheets, survival, int(pms_defaults.get("base_year", 2024)))

    uio_scope, scope_label, _ = resolve_uio_scope(
        market_scope,
        distributor,
        uio_by_dist,
        pms_sheets,
        pms_defaults,
        ituk_uio_source=ituk_uio_source,
        uio_sheets=uio_sheets,
        paths=paths,
        sales_year=year,
        cfg=cfg,
    )

    if v3.empty:
        return {"error": pd.DataFrame([{"message": "v3 PN matrix empty or missing."}])}

    qty_col, rev_col = None, None
    actual_source = "none"
    try:
        from sources_loader import load_ituk_dealer_sales, sales_column_names, attach_actual_qty

        qty_col, rev_col = sales_column_names(period_type, year)
    except ImportError:
        qty_col, rev_col = f"Qty_CY{year}", f"Rev_CY{year}_EUR"

    work = v3.copy()
    for c in ("PR00_EUR", qty_col, rev_col):
        if c and c in work.columns:
            work[c] = pd.to_numeric(work[c], errors="coerce")

    work["category"] = work["Description"].apply(classify_pms_category)
    valid_cats = set(pms_intervals["category"].astype(str))
    work = work[work["category"].isin(valid_cats)].copy()

    if pms_basket == "Maintenance (AIM_DemandType)":
        work = work[work["AIM_DemandType"] == "Maintenance"].copy()
    elif pms_basket == "Maintenance + Wear Repair (PMS pilot)":
        work = work[work["AIM_DemandType"].isin(["Maintenance", "Wear Repair"])].copy()

    dist_sales = None
    if cfg and paths and market_scope.startswith("ITUK"):
        try:
            dist_sales = load_ituk_dealer_sales(paths, cfg, year, period_type)
        except Exception:
            pass
    pms = attach_actual_qty(work, work, qty_col, dist_sales, "ITUK") if qty_col else work.copy()
    if "actual_source" in pms.columns:
        actual_source = str(pms["actual_source"].iloc[0]) if len(pms) else actual_source

    gp_meta: dict[str, Any] = {}
    isze_gp_effective = isze_gp_pct
    try:
        from sources_loader import resolve_gp_policy

        pms, gp_meta = resolve_gp_policy(market_scope, pms, paths or {}, cfg or {})
        isze_gp_effective = float(gp_meta.get("effective_gp_pct", isze_gp_pct))
    except ImportError:
        pms["gp_pct"] = isze_gp_pct

    fx = {"GBP_EUR": GBP_EUR, "SEK_EUR": SEK_EUR}
    scraped_clean = scraped
    try:
        from sources_loader import load_fx_rates, sanitize_scrape_frame

        fx = load_fx_rates(cfg)
        scraped_clean = sanitize_scrape_frame(scraped)
    except ImportError:
        pass

    comp_prices = normalize_scraped_prices(scraped_clean, fx)
    category_view = _category_aggregate(
        pms, pms_intervals, uio_scope, horizon, isze_gp_effective, qty_col or "actual_units"
    )
    category_view["actual_data_source"] = actual_source
    if gp_meta:
        category_view["gp_source"] = gp_meta.get("source_label", "")
    category_view["period_type"] = period_type
    category_view["sales_year"] = year
    category_view["methodology_scope"] = "PMS Calc engine (whole-fleet intervals)"
    category_view["methodology_note"] = ENGINE_METHODOLOGY_NOTE

    # ── PN view ──────────────────────────────────────────────────────────────
    keep_cols = [
        c
        for c in [
            "PN",
            "Description",
            "category",
            "PR00_EUR",
            "actual_units",
            qty_col,
            rev_col,
            "AIM_Category",
            "AIM_Bucket",
            "AIM_DemandType",
            "Source",
            "Class",
            "actual_source",
        ]
        if c and c in pms.columns
    ]
    pn_view = pms[keep_cols].copy()
    if not category_view.empty:
        pn_view = pn_view.merge(
            category_view[
                ["category", "potential_units", "lost_units", "lost_isze_gp"]
            ].rename(
                columns={
                    "potential_units": "cat_potential_units",
                    "lost_units": "cat_lost_units",
                    "lost_isze_gp": "cat_lost_gp",
                }
            ),
            on="category",
            how="left",
        )
        alloc_col = "actual_units" if "actual_units" in pn_view.columns else qty_col
        if alloc_col and alloc_col in pn_view.columns:
            pn_view["sales_share_in_cat"] = pn_view.groupby("category")[alloc_col].transform(
                lambda s: s / s.sum() if s.sum() > 0 else 0.0
            )
        else:
            pn_view["sales_share_in_cat"] = 0.0
        pn_view["allocated_lost_units"] = (
            pn_view["cat_lost_units"] * pn_view["sales_share_in_cat"]
        ).round(0)
        pn_view["allocated_lost_gp"] = (
            pn_view["cat_lost_gp"] * pn_view["sales_share_in_cat"]
        ).round(0)

    if not comp_prices.empty:
        pn_view = pn_view.merge(comp_prices, on="PN", how="left")

    sort_col = "allocated_lost_gp" if "allocated_lost_gp" in pn_view.columns else (
        "actual_units" if "actual_units" in pn_view.columns else qty_col
    )
    pn_view = pn_view.sort_values(
        sort_col if sort_col and sort_col in pn_view.columns else "PN",
        ascending=False,
        na_position="last",
    )

    # ── Brand view ───────────────────────────────────────────────────────────
    brand_view = pd.DataFrame()
    if not comp_prices.empty and "competitor_brand" in comp_prices.columns:
        brands = comp_prices.dropna(subset=["competitor_brand"]).copy()
        brands["competitor_brand"] = brands["competitor_brand"].astype(str)
        if not pn_view.empty and "category" in pn_view.columns:
            brands = brands.merge(pn_view[["PN", "category"]], on="PN", how="left")
        brand_view = (
            brands.groupby("competitor_brand", as_index=False)
            .agg(
                pns_present=("PN", "nunique"),
                categories=("category", lambda s: ", ".join(sorted({x for x in s.dropna().astype(str) if x}))),
                avg_price_eur=("competitor_min_price_eur", "mean"),
                min_price_eur=("competitor_min_price_eur", "min"),
            )
            .rename(columns={"competitor_brand": "brand"})
            .sort_values("pns_present", ascending=False)
        )

    total_potential = float(category_view["potential_units"].sum()) if not category_view.empty else 0.0
    total_actual = float(category_view["actual_units"].sum()) if not category_view.empty else 0.0
    total_lost_units = float(category_view["lost_units"].sum()) if not category_view.empty else 0.0
    total_lost_gp = float(category_view["lost_isze_gp"].sum()) if not category_view.empty else 0.0

    summary_kpis = pd.DataFrame(
        [
            {
                "scope_label": scope_label,
                "total_uio": uio_scope,
                "pms_pns": len(pms),
                "horizon_years": horizon,
                "isze_gp_pct": isze_gp_effective,
                "gp_source": gp_meta.get("source_label", "") if gp_meta else "",
                "gp_matched_pns": gp_meta.get("matched_pns") if gp_meta else None,
                "annual_mileage_km": pms_defaults.get("annual_mileage_km"),
                "potential_uio_factor": pms_defaults.get("potential_uio_factor"),
                "total_potential_units": total_potential,
                "total_actual_units": total_actual,
                "total_lost_units": total_lost_units,
                "total_lost_gp": total_lost_gp,
                "overall_capture_rate": (total_actual / total_potential) if total_potential > 0 else None,
                "period_type": period_type,
                "sales_year": year,
                "actual_data_source": actual_source,
                "ituk_uio_source": ituk_uio_source if market_scope.startswith("ITUK") else None,
                "methodology_note": ENGINE_METHODOLOGY_NOTE,
                "annual_mileage_km": pms_defaults.get("annual_mileage_km"),
                "mileage_source": pms_defaults.get("mileage_source", "PMS Calc Assumptions"),
                "fx_GBP_EUR": fx.get("GBP_EUR"),
                "fx_SEK_EUR": fx.get("SEK_EUR"),
                "fx_as_of": fx.get("as_of", ""),
            }
        ]
    )

    unmapped = report_unmapped_pms_pns(v3, pms_basket)
    uio_distributors = uio_by_dist.copy()
    car_park_year = int((cfg or {}).get("defaults", {}).get("ituk_smmt_car_park_year", 2024))
    by_model = compute_pms_by_model(
        category_view,
        uio_sheets,
        pms_sheets,
        market_scope=market_scope,
        car_park_year=car_park_year,
    )
    multidb = compute_pms_all_distributors(
        v3,
        uio_sheets,
        pms_sheets,
        period_type=period_type,
        sales_year=year,
        isze_gp_pct=isze_gp_pct,
        horizon_years=horizon,
        pms_basket=pms_basket,
        cfg=cfg,
        paths=paths,
        data_mode=(pms_data_mode or "auto").split()[0],
    )

    try:
        from pms_validation import validate_engine_result

        validation = validate_engine_result(
            {
                "Summary KPIs": summary_kpis,
                "Category lost sales": category_view,
                "PN drill-down": pn_view,
            }
        )
    except ImportError:
        validation = pd.DataFrame()

    out = {
        "Summary KPIs": summary_kpis,
        "Validation": validation,
        "Category lost sales": category_view,
        "PN drill-down": pn_view,
        "Brand league": brand_view,
        "PMS intervals (from source)": pms_intervals,
        "UIO by distributor": uio_distributors,
        "Unmapped PMS PNs": unmapped,
        "Methodology": pd.DataFrame([{"note": ENGINE_METHODOLOGY_NOTE}]),
    }
    for k, v in multidb.items():
        if k not in out:
            out[k] = v
    for k, v in by_model.items():
        out[k] = v
    return out
