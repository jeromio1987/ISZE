"""
Load upgradeable data sources from sources.yaml.

Swap files on disk → update yaml paths → reload app. No code changes required.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

BUNDLE_DIR = Path(__file__).parent

PRISM_CAT_TO_DISPLAY = {
    "oil_filter": "Oil filter",
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "cabin_filter": "Cabin filter",
    "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Pressure plate",
    "release_bearing": "Release bearing",
    "brake_pad": "Brake pad (front)",
    "brake_pad_front": "Brake pad (front)",
    "brake_pad_rear": "Brake pad (rear)",
    "brake_disc_front": "Brake disc (front)",
    "brake_disc_rear": "Brake disc (rear)",
    "brake_lining": "Brake lining",
}


def load_sources_config(path: Path | None = None) -> dict[str, Any]:
    p = path or BUNDLE_DIR / "sources.yaml"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg["_config_path"] = str(p.resolve())
    return cfg


def _resolve_path(raw: str, base: Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return (base / p).resolve()


def resolve_paths(cfg: dict[str, Any]) -> dict[str, Path]:
    base = BUNDLE_DIR
    paths = cfg.get("paths") or {}
    out = {}
    for key, val in paths.items():
        if isinstance(val, str):
            out[key] = _resolve_path(val, base)
    out["config"] = Path(cfg.get("_config_path", BUNDLE_DIR / "sources.yaml"))
    return out


def sales_column_names(period_type: str, year: int) -> tuple[str | None, str | None]:
    """Return (qty_column, rev_column) on v3 PN_Price_Matrix for CY. FY not in v3 — use PRISM derived."""
    period_type = (period_type or "CY").upper()
    y = int(year)
    if period_type == "CY":
        return f"Qty_CY{y}", f"Rev_CY{y}_EUR"
    # FY columns not standard in v3; caller should use distributor sales or derived CSV
    return None, None


def load_fx_rates(cfg: dict[str, Any] | None = None) -> dict[str, float]:
    """FX from sources.yaml fx_rates block."""
    cfg = cfg or load_sources_config()
    fx = cfg.get("fx_rates") or {}
    return {
        "GBP_EUR": float(fx.get("GBP_EUR", 1.17)),
        "SEK_EUR": float(fx.get("SEK_EUR", 0.089)),
        "as_of": str(fx.get("as_of", "")),
    }


def normalize_pn(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)


def sanitize_scrape_frame(df: pd.DataFrame, price_floor: float = 3.0) -> pd.DataFrame:
    """Treat no-result sentinels (e.g. 2.0) as missing; respect Status=no_results."""
    if df.empty:
        return df
    out = df.copy()
    if "PN" in out.columns:
        out["PN"] = normalize_pn(out["PN"])
    bad = (
        out["Status"].astype(str).str.lower().isin(("no_results", "error", "timeout"))
        if "Status" in out.columns
        else pd.Series(False, index=out.index)
    )
    price_cols = [c for c in out.columns if "MinPrice" in c or "AllPrices" in c]
    for col in price_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out.loc[bad, col] = np.nan
        out.loc[out[col] < price_floor, col] = np.nan
    return out


def load_v3_pn_matrix(paths: dict[str, Path]) -> pd.DataFrame:
    fp = paths.get("v3_pn_matrix")
    if not fp or not fp.exists():
        return pd.DataFrame()
    sheet = "PN_Price_Matrix"
    cfg = load_sources_config()
    sheet = (cfg.get("paths") or {}).get("v3_sheet") or sheet
    df = pd.read_excel(fp, sheet_name=sheet, dtype={"PN": str})
    df["PN"] = normalize_pn(df["PN"])
    return df


def load_pms_parts_config(paths: dict[str, Path], cfg: dict[str, Any]) -> dict[str, Any]:
    """Load full pms_parts_config.yaml (parts + per-model mileage)."""
    rel = (cfg.get("paths") or {}).get("pms_parts_config") or "pms_parts_config.yaml"
    p = _resolve_path(rel, BUNDLE_DIR)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_pms_parts_from_yaml(paths: dict[str, Path], cfg: dict[str, Any]) -> pd.DataFrame | None:
    doc = load_pms_parts_config(paths, cfg)
    parts = doc.get("parts") or []
    if not parts:
        return None
    df = pd.DataFrame(parts)
    if "annual_freq" in df.columns and "parts_per_service" in df.columns:
        df["annual_pieces_per_vehicle"] = df["annual_freq"] * df["parts_per_service"]
    return df


def load_pms_model_mileage(paths: dict[str, Path], cfg: dict[str, Any]) -> pd.DataFrame:
    """Per-model annual mileage km from pms_parts_config.yaml models block."""
    doc = load_pms_parts_config(paths, cfg)
    default_km = float(doc.get("default_annual_mileage_km", 80_000))
    rows = doc.get("models") or []
    if not rows:
        return pd.DataFrame(columns=["model", "annual_mileage_km", "mileage_factor"])
    df = pd.DataFrame(rows)
    if "annual_mileage_km" not in df.columns:
        df["annual_mileage_km"] = default_km
    df["annual_mileage_km"] = pd.to_numeric(df["annual_mileage_km"], errors="coerce").fillna(default_km)
    df["mileage_factor"] = df["annual_mileage_km"] / default_km
    df["default_annual_mileage_km"] = default_km
    return df


def pms_intervals_for_model(
    base_intervals: pd.DataFrame,
    model_row: pd.Series,
) -> pd.DataFrame:
    """Scale category annual_freq by model mileage vs fleet default."""
    if base_intervals.empty:
        return base_intervals
    factor = float(model_row.get("mileage_factor", 1.0) or 1.0)
    if factor <= 0 or abs(factor - 1.0) < 1e-6:
        return base_intervals
    out = base_intervals.copy()
    for col in ("annual_freq", "annual_pieces_per_vehicle"):
        if col in out.columns:
            out[col] = out[col] * factor
    out["model_mileage_km"] = model_row.get("annual_mileage_km")
    out["mileage_factor"] = factor
    return out


def load_pms_capture_derived(
    paths: dict[str, Path],
    year: int,
    period_type: str = "CY",
    line_type: str = "total",
    distributor_codes: list[str] | None = None,
) -> pd.DataFrame:
    """
    Multi-DB PMS from PRISM derived pipeline (preferred when file exists).
    period_type CY uses calendar year column; FY uses same year index (ISZE FY label in UI).
    """
    fp = paths.get("pms_capture_by_db")
    if not fp or not fp.exists():
        return pd.DataFrame()

    df = pd.read_csv(fp)
    df = df[(df["year"] == int(year)) & (df["line_type"] == line_type)].copy()
    if distributor_codes:
        df = df[df["distributor_code"].isin(distributor_codes)]

    df["category"] = df["pms_category"].map(
        lambda c: PRISM_CAT_TO_DISPLAY.get(str(c), str(c).replace("_", " ").title())
    )
    df["distributor"] = df["distributor_code"]
    df["potential_units"] = df["expected_qty"]
    df["actual_units"] = df["actual_qty"]
    df["lost_units"] = (df["expected_qty"] - df["actual_qty"]).clip(lower=0)
    df["lost_revenue"] = df["revenue_gap_eur"]
    df["lost_isze_gp"] = df["revenue_gap_eur"]  # derived file gap is revenue; GP applied in engine if needed
    df["capture_rate"] = df["capture_rate"]
    df["uio_scope"] = df["uio_units"]
    if "scope" in df.columns:
        df["prism_scope"] = df["scope"]
    if "uio_source" in df.columns:
        df["prism_uio_source"] = df["uio_source"]

    def _prism_row_label(r: pd.Series) -> str:
        scope = r.get("prism_scope", r.get("scope", ""))
        usrc = r.get("prism_uio_source", r.get("uio_source", ""))
        return f"PRISM derived (scope={scope}, uio_source={usrc})"

    df["data_source"] = df.apply(_prism_row_label, axis=1)
    df["methodology_note"] = (
        "PRISM expected_qty uses pipeline scope (typically N75_only). "
        "Not comparable to ITUK tab PMS Calc whole-fleet potential_units."
    )
    return df


def _num_cell(val: Any) -> float | None:
    try:
        v = float(val)
        return v if pd.notna(v) else None
    except (TypeError, ValueError):
        return None


def parse_ituk_car_park_uio(
    uio_sheets: dict[str, pd.DataFrame],
    year: int = 2024,
    paths: dict[str, Path] | None = None,
) -> tuple[float | None, str]:
    """
    ITUK car park from v17 sheet 4 — Section G «Total ITUK», column «{year}A» (e.g. 2024A = 22,389).

    Workbook text cites SMMT via ITUK; PRISM CSV may tag uio_source (e.g. ituk_dvla_2026). Labels use file fields.
    """
    sheet_name = "4. ITUK UIO Projection"
    raw = uio_sheets.get(sheet_name)
    if raw is not None and not raw.empty:
        header_row = None
        for i in range(len(raw)):
            row = [str(c).strip() if pd.notna(c) else "" for c in raw.iloc[i]]
            if row[1] == "Model" and any("2024" in c or "A" in c for c in row[2:15]):
                header_row = i
                break
        if header_row is not None:
            headers = [str(c).strip() if pd.notna(c) else "" for c in raw.iloc[header_row]]
            col_idx = None
            y = int(year)
            for prefer in (f"{y}A", f"{y}P", str(y), f"CY{y}"):
                for j, h in enumerate(headers):
                    if h == prefer or h.startswith(prefer):
                        col_idx = j
                        break
                if col_idx is not None:
                    break
            if col_idx is None:
                for j, h in enumerate(headers):
                    if h.endswith("A") and h.replace("A", "").isdigit() and int(h.replace("A", "")) <= y:
                        col_idx = j
            if col_idx is not None:
                for i in range(header_row + 1, min(header_row + 25, len(raw))):
                    label = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
                    if label == "Total ITUK":
                        val = _num_cell(raw.iloc[i, col_idx])
                        if val is not None and val > 1000:
                            col_label = headers[col_idx] if col_idx < len(headers) else str(year)
                            return (
                                val,
                                f"ITUK — car park {col_label} (v17 sheet 4; workbook: SMMT via ITUK)",
                            )

    if paths:
        fp = paths.get("pms_capture_by_db")
        if fp and fp.exists():
            df = pd.read_csv(fp)
            sub = df[
                (df["distributor_code"].astype(str).str.upper() == "ITUK")
                & (df["year"] == int(year))
                & (df["line_type"] == "total")
            ]
            if not sub.empty:
                u = float(sub["uio_units"].iloc[0])
                src = str(sub["uio_source"].iloc[0]) if "uio_source" in sub.columns else "PRISM"
                sc = str(sub["scope"].iloc[0]) if "scope" in sub.columns else ""
                return (
                    u,
                    f"ITUK — car park via PRISM (uio_source={src}, scope={sc}, year={year})",
                )

    return None, ""


# Back-compat alias
parse_ituk_smmt_car_park = parse_ituk_car_park_uio

CANONICAL_ITUK_MODELS = frozenset(
    {"F110/120", "F135", "F150/180", "N35", "N50/55", "N62/65", "N75", "UNSPEC", "Total ITUK"}
)

TONNAGE_KM_RECOMMENDED: dict[str, int] = {
    "LCV": 45_000,
    "3.5t (N35)": 60_000,
    "5.5t (N50/55)": 70_000,
    "6.5t (N62/65)": 75_000,
    "7.5t (N75)": 80_000,
    "F-Series": 80_000,
    "MD": 70_000,
    "Other CV": 80_000,
    "Fleet total": 0,
}


def tonnage_class_for_model(model: str) -> str:
    m = model.upper()
    if "D-MAX" in m or "DMAX" in m or "LCV" in m or "GRAFTER" in m:
        return "LCV"
    if "N35" in m or "3.5" in m:
        return "3.5t (N35)"
    if "N50" in m or "N55" in m or "5.5" in m:
        return "5.5t (N50/55)"
    if "N62" in m or "N65" in m or "6.5" in m:
        return "6.5t (N62/65)"
    if "N75" in m or "7.5" in m or "NPR75" in m or "NPR88" in m:
        return "7.5t (N75)"
    if "F-" in m or "F SERIES" in m or m.startswith("F"):
        return "F-Series"
    if "MD" in m:
        return "MD"
    if "TOTAL" in m:
        return "Fleet total"
    return "Other CV"


def parse_ituk_models_car_park(
    uio_sheets: dict[str, pd.DataFrame],
    year: int = 2024,
) -> pd.DataFrame:
    """
    ITUK active car park by model — v17 sheet 4 Section G, column {year}A.
    """
    raw = uio_sheets.get("4. ITUK UIO Projection")
    if raw is None or raw.empty:
        return pd.DataFrame()

    header_row = None
    headers: list[str] = []
    for i in range(len(raw)):
        row = [str(c).strip() if pd.notna(c) else "" for c in raw.iloc[i]]
        if len(row) > 1 and row[1] == "Model" and f"{year}A" in row:
            header_row = i
            headers = row
            break
    if header_row is None:
        return pd.DataFrame()

    col = f"{year}A"
    if col not in headers:
        return pd.DataFrame()
    col_idx = headers.index(col)

    rows: list[dict[str, Any]] = []
    for i in range(header_row + 1, min(header_row + 25, len(raw))):
        model = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
        if model not in CANONICAL_ITUK_MODELS:
            continue
        uio = _num_cell(raw.iloc[i, col_idx])
        ton = tonnage_class_for_model(model)
        rows.append(
            {
                "model": model,
                "tonnage_class": ton,
                "car_park_uio": uio,
                "recommended_km_yr": TONNAGE_KM_RECOMMENDED.get(ton, 80_000),
                "uio_year": col,
                "source": "v17 sheet 4 §G (SMMT via ITUK per workbook)",
            }
        )

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.sort_values("car_park_uio", ascending=False, na_position="last")
    return df.drop_duplicates(subset=["model"], keep="first").reset_index(drop=True)


def parse_pms_calc_model_uio(pms_sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """N35 / N75 blocks from PMS Calc UIO Data (5-yr registration placeholders)."""
    raw = pms_sheets.get("UIO Data")
    if raw is None or raw.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    current = None
    reg = pot = None
    for i in range(len(raw)):
        c0 = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
        c1 = str(raw.iloc[i, 1]).strip() if pd.notna(raw.iloc[i, 1]) else ""
        if "N35 MODEL" in c0.upper() or "N35 MODEL" in c1.upper():
            current = "N35"
            reg = pot = None
        elif "N75 MODEL" in c0.upper() or "N75 MODEL" in c1.upper():
            current = "N75"
            reg = pot = None
        if not current:
            continue
        if "registered units" in c1.lower():
            reg = _num_cell(raw.iloc[i, 6]) if raw.shape[1] > 6 else None
        elif "potential units" in c1.lower():
            pot = _num_cell(raw.iloc[i, 6]) if raw.shape[1] > 6 else None
            rows.append(
                {
                    "model": current,
                    "pms_calc_5yr_registrations": reg,
                    "pms_calc_potential_uio": pot,
                    "source": "PMS Calc UIO Data (update from ITUK VIN)",
                }
            )
            current = None
            reg = pot = None
    return pd.DataFrame(rows)


def scrape_freshness(paths: dict[str, Path], script_dir: Path, max_age_days: int = 30) -> pd.DataFrame:
    """Oldest Scraped_At across bundle scraper CSVs."""
    rows = []
    for fname in ("autodoc_results.csv", "ks_results.csv", "mekonomen_results.csv"):
        for base in (script_dir, paths.get("scraper_dir") or script_dir):
            p = Path(base) / fname
            if not p.exists():
                continue
            try:
                df = pd.read_csv(p, usecols=["Scraped_At"], low_memory=False)
                if "Scraped_At" in df.columns and not df.empty:
                    ts = pd.to_datetime(df["Scraped_At"], errors="coerce").max()
                    if pd.notna(ts):
                        rows.append({"file": fname, "path": str(p), "latest_scrape": ts})
            except Exception:
                pass
            break
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out["age_days"] = (pd.Timestamp.now() - out["latest_scrape"]).dt.days
    out["stale"] = out["age_days"] > max_age_days
    return out


def _parse_margin_pct(series: pd.Series) -> pd.Series:
    """'45.0%' / 45 / '—' → fraction 0–1."""
    s = series.astype(str).str.strip().str.replace("%", "", regex=False)
    s = s.replace({"—": "", "nan": "", "None": ""})
    out = pd.to_numeric(s, errors="coerce")
    # Values > 1 are percent points (45 → 0.45)
    out = np.where(out > 1, out / 100.0, out)
    return pd.Series(out, index=series.index)


def load_ituk_pn_gp_table(paths: dict[str, Path], cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    """
    PN-level gross margin % from ITUK Parts Sales Classification workbook.

    Column «Margin %» = SAP price-class margin (same basis as your CY2025 classification work).
    """
    cfg = cfg or load_sources_config()
    path_keys = cfg.get("paths") or {}
    fp = paths.get("ituk_pn_margins")
    if not fp or not fp.exists():
        raw_path = path_keys.get("ituk_pn_margins")
        if raw_path:
            fp = _resolve_path(str(raw_path), BUNDLE_DIR)
    if not fp or not Path(fp).exists():
        return pd.DataFrame(columns=["PN", "gp_pct", "margin_tier", "price_class"])

    sheet = (path_keys.get("ituk_pn_margins_sheet") or "PARTS MASTER CY2025")
    try:
        df = pd.read_excel(fp, sheet_name=sheet, header=1, dtype={"PN": str})
    except Exception:
        return pd.DataFrame(columns=["PN", "gp_pct", "margin_tier", "price_class"])

    if "PN" not in df.columns:
        return pd.DataFrame(columns=["PN", "gp_pct", "margin_tier", "price_class"])

    margin_col = next((c for c in df.columns if str(c).strip().lower() in ("margin %", "margin%")), None)
    if margin_col is None:
        return pd.DataFrame(columns=["PN", "gp_pct", "margin_tier", "price_class"])

    out = pd.DataFrame()
    out["PN"] = normalize_pn(df["PN"])
    out["gp_pct"] = _parse_margin_pct(df[margin_col])
    if "Margin Tier" in df.columns:
        out["margin_tier"] = df["Margin Tier"]
    if "Price Class" in df.columns:
        out["price_class"] = df["Price Class"]
    out = out.dropna(subset=["PN"])
    out = out[out["gp_pct"].notna() & (out["gp_pct"] >= 0) & (out["gp_pct"] <= 1)]
    return out.drop_duplicates(subset=["PN"], keep="first")


def attach_gp_pct_to_pms(
    pms: pd.DataFrame,
    gp_table: pd.DataFrame,
    fallback_pct: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Add gp_pct column; return frame + match stats."""
    out = pms.copy()
    if "PN" in out.columns:
        out["PN"] = normalize_pn(out["PN"])
    fallback = float(fallback_pct)
    if gp_table is None or gp_table.empty:
        out["gp_pct"] = fallback
        return out, {"matched_pns": 0, "total_pns": len(out), "fallback_pct": fallback}

    g = gp_table[["PN", "gp_pct"]].copy()
    g["PN"] = normalize_pn(g["PN"])
    out = out.drop(columns=[c for c in ("gp_pct",) if c in out.columns], errors="ignore")
    out = out.merge(g, on="PN", how="left")
    matched = int(out["gp_pct"].notna().sum())
    out["gp_pct"] = pd.to_numeric(out["gp_pct"], errors="coerce").fillna(fallback)
    return out, {"matched_pns": matched, "total_pns": len(out), "fallback_pct": fallback}


def resolve_gp_policy(
    market_scope: str,
    pms: pd.DataFrame,
    paths: dict[str, Path],
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    ITUK scope: use PN margins from classification file (PR00-weighted effective %).
    Other scopes: flat fallback from yaml (Sales to Dealers file has qty only, no margin).
    """
    defaults = cfg.get("defaults") or {}
    fallback = float(defaults.get("isze_gp_pct", 0.35))
    meta: dict[str, Any] = {
        "fallback_pct": fallback,
        "source_label": f"Policy default {fallback * 100:.0f}%",
        "effective_gp_pct": fallback,
        "matched_pns": 0,
        "total_pns": len(pms),
    }

    if not str(market_scope).startswith("ITUK"):
        meta["note"] = (
            "Sales to Dealers_*.xlsx = quantities only (no cost/turnover). "
            "Pan-EU GP uses defaults.isze_gp_pct until billing+COGS export is wired."
        )
        out, stats = attach_gp_pct_to_pms(pms, pd.DataFrame(), fallback)
        meta.update(stats)
        return out, meta

    gp_table = load_ituk_pn_gp_table(paths, cfg)
    out, stats = attach_gp_pct_to_pms(pms, gp_table, fallback)
    meta.update(stats)

    fp = paths.get("ituk_pn_margins")
    fname = Path(fp).name if fp else "ITUK_Parts_Sales_Classification_CY2025.xlsx"
    if stats["matched_pns"] == 0:
        meta["source_label"] = f"Policy default {fallback * 100:.0f}% (margin file missing or no PN match)"
        meta["effective_gp_pct"] = fallback
        meta["note"] = (
            f"Expected margin file: {fname}. "
            "Sales to Dealers_ITUK = qty only — not cost/turnover."
        )
        return out, meta

    w = pd.to_numeric(out.get("PR00_EUR"), errors="coerce").fillna(0)
    gp = pd.to_numeric(out["gp_pct"], errors="coerce").fillna(fallback)
    effective = float((w * gp).sum() / w.sum()) if w.sum() > 0 else float(gp.mean())
    meta["effective_gp_pct"] = effective
    meta["source_label"] = (
        f"{fname} — {stats['matched_pns']}/{stats['total_pns']} PNs · "
        f"PR00-weighted GP {effective * 100:.1f}%"
    )
    meta["note"] = (
        "Margin % = SAP class margin from your classification workbook. "
        "Sales to Dealers_ITUK_CY*.xlsx still supplies actual **quantities** only."
    )
    return out, meta


def v17_name_to_db_code(name: str, aliases: dict[str, str]) -> str:
    s = str(name).strip()
    if s in aliases:
        return aliases[s]
    return s.upper().replace(" ", "_")[:20]


def load_ituk_dealer_sales(paths: dict[str, Path], cfg: dict[str, Any], year: int, period_type: str = "CY") -> pd.DataFrame:
    """Parse ITUK Sales to Dealers workbook → PN × qty for the year."""
    aliases = cfg.get("distributor_aliases") or {}
    db_code = aliases.get("ITUK", "ITUK")
    period = (period_type or "CY").upper()
    pattern = (cfg.get("paths") or {}).get("sales_to_dealers_pattern") or "Sales to Dealers_{db_code}_{period}{year}.xlsx"
    sales_dir = paths.get("sales_to_dealers_dir")
    if not sales_dir:
        return pd.DataFrame()

    fname = pattern.format(db_code=db_code, period=period, year=year)
    fp = sales_dir / fname
    if not fp.exists():
        # try without period in name
        alt = sales_dir / f"Sales to Dealers_{db_code}_CY{year}.xlsx"
        fp = alt if alt.exists() else fp
    if not fp.exists():
        return pd.DataFrame()

    raw = pd.read_excel(fp, sheet_name=0, header=None)
    header_row = None
    for i in range(min(20, len(raw))):
        row = [str(x).strip() if pd.notna(x) else "" for x in raw.iloc[i]]
        if row[0] == "Customer Name" and "Item Number" in row:
            header_row = i
            break
    if header_row is None:
        return pd.DataFrame()

    df = pd.read_excel(fp, sheet_name=0, header=header_row)
    if "Item Number" not in df.columns:
        return pd.DataFrame()

    def extract_pn(s: str) -> str | None:
        if not isinstance(s, str):
            return None
        token = s.strip().split()[0].split("-")[0]
        digits = re.sub(r"\D", "", token)
        return digits.zfill(10) if len(digits) >= 8 else None

    df = df.dropna(subset=["Item Number"])
    # Only calendar month columns — never sum PN or other fields (PN digits were summed as qty).
    month_cols = [
        c
        for c in df.columns
        if c
        in (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        )
    ]
    for c in month_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if month_cols:
        df["qty"] = df[month_cols].sum(axis=1)
    else:
        df["qty"] = 0
    df["PN"] = df["Item Number"].apply(extract_pn)
    df = df.dropna(subset=["PN"])
    # Per customer×PN row sanity cap (bad Excel cells)
    df.loc[df["qty"] > 100_000, "qty"] = pd.NA
    df["qty"] = df["qty"].fillna(0)

    out = df.groupby("PN", as_index=False)["qty"].sum()
    out["distributor_code"] = db_code
    out["period_type"] = period
    out["year"] = year
    out["data_source"] = str(fp.name)
    return out


def attach_actual_qty(
    pms_df: pd.DataFrame,
    v3: pd.DataFrame,
    qty_col: str | None,
    dist_sales: pd.DataFrame | None = None,
    distributor_code: str | None = None,
) -> pd.DataFrame:
    """Set actual_units on PN-level frame from distributor sales (preferred) or v3 column."""
    out = pms_df.copy()
    if "PN" in out.columns:
        out["PN"] = normalize_pn(out["PN"])
    if dist_sales is not None and not dist_sales.empty and "PN" in dist_sales.columns:
        out = out.drop(columns=[c for c in ("actual_units", "qty_actual") if c in out.columns], errors="ignore")
        sales = dist_sales[["PN", "qty"]].copy()
        sales["PN"] = normalize_pn(sales["PN"])
        out = out.merge(sales.rename(columns={"qty": "actual_units"}), on="PN", how="left")
        out["actual_units"] = pd.to_numeric(out["actual_units"], errors="coerce").fillna(0)
        out["actual_source"] = f"dealer sales ({distributor_code})"
    elif qty_col and qty_col in v3.columns:
        v3m = v3[["PN", qty_col]].copy()
        v3m["PN"] = normalize_pn(v3m["PN"])
        out = out.merge(v3m.rename(columns={qty_col: "actual_units"}), on="PN", how="left")
        out["actual_units"] = pd.to_numeric(out["actual_units"], errors="coerce").fillna(0)
        out["actual_source"] = f"v3 global ({qty_col})"
    else:
        out["actual_units"] = 0.0
        out["actual_source"] = "none"
    return out
