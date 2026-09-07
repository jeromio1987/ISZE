#!/usr/bin/env python3
"""
GPS & PMS V2 shadow lane — mileage × cohort × fitment expected demand.

Mode B only. Does NOT overwrite:
  - pms_capture_by_db_year.csv
  - gps_spu_by_distributor.csv
  - pms_capture_assumptions.yaml country_overrides (V1)

Outputs under 01_data/00_derived/ (and a short findings md).
See 00_docs/agent/GPS_PMS_V2_CONCEPT.md.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

PRISM_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM_ROOT))

from config import ISZE_ROOT  # noqa: E402
from modules.pms_capture_config import (  # noqa: E402
    BUCKET_SERVICES_PER_YEAR,
    BUCKET_SERVICES_PER_YEAR_OVERRIDES,
    CONSUMABLE_FACTOR,
    LCV_BUCKET_FACTOR_OVERRIDES,
    WEAR_FACTOR,
    load_uio_by_bucket,
)

DERIVED = ISZE_ROOT / "01_data" / "00_derived"
DIST_DIR = ISZE_ROOT / "01_data" / "08_Distributor"
VIN_PATH = ISZE_ROOT / "01_data" / "07_UIO" / "vin" / "VIN_register.csv"
CROSSREF = DERIVED / "genuine_bvp_crossref.csv"
EQHIT_EXTRACT = DERIVED / "eqhit_extract_priority_cy2025.csv"
PMS_V1 = DERIVED / "pms_capture_by_db_year.csv"
GPS_V1 = DERIVED / "gps_spu_by_distributor.csv"
CONFIG_PATH = PRISM_ROOT / "data" / "gps_pms_v2_config.yaml"

# Categories intentionally skipped in EQ-HIT pull (keep BVP).
EQHIT_SKIP_CATEGORIES = {"oil_filter"}
# Known UIO buckets only — unknown rows are coverage diagnostics, not demand zeros.
FITMENT_BUCKETS = ("cv_std", "f_series", "lcv")

MILEAGE_XLSX = DIST_DIR / "EU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx"

# EU Mileage CountryName → candidate VIN rows that roll into a reporting DB.
# LCV mileage only — never applied to CV buckets.
COUNTRY_TO_DB_LCV: dict[str, str] = {
    "BELGIUM": "BELGIUM",
    "NETHERLANDS": "BELGIUM",  # Benelux rollup
    "POLAND": "BELGIUM",
    "CYPRUS": "CYPRUS",
    "DENMARK": "DENMARK",
    "FINLAND": "FINLAND",
    "GERMANY": "GERMANY",
    "GREECE": "GREECE",
    "HUNGARY": "HUNGARY",
    "ICELAND": "ICELAND",
    "IRELAND": "IRELAND",
    "ISRAEL": "UMI",  # LCV only; UTI is CV
    "MALTA": "MALTA",
    "NORWAY": "NORWAY",
    "PORTUGL": "PORTUGAL",
    "ROMANIA": "ROMANIA",
    "SWEDEN": "SWEDEN",
    "U KING": "IUK",  # LCV UK; ITUK stays CV
}

MIDI_OR_OUT: set[str] = {
    "BOS HER",
    "CROATIA",
    "FRANCE",
    "ITALY",
    "MACEDON",
    "SERBIA",
    "SLOVENIA",
    "SPAIN",
    "SWITZLD",
    "AUSTRIA",
    "CZECH",
    "SLOVAKIA",
    "RUSSIA",
    "TURKEY",
    "PALESTINE",
}

VIN_DB_TO_CODE = {
    "PT": "PORTUGAL",
    "IE": "IRELAND",
    "DE": "GERMANY",
    "MT": "MALTA",
    "CY": "CYPRUS",
    "BE": "BELGIUM",
    "GR": "GREECE",
}

# BVP vehicle_model token → UIO bucket
def _bucket_from_vehicle_model(model: str) -> str | None:
    if not isinstance(model, str) or not model.strip():
        return None
    m = model.upper().replace(" ", "")
    # LCV / pickup family
    if any(tok in m for tok in ("TF*", "TBR", "TFR", "D-MAX", "DMAX", "MUX", "RT5", "RT8", "RG")):
        return "lcv"
    # F-series
    if any(tok in m for tok in ("F*S", "F*R", "FRR", "FSR", "FSS", "FTR", "FVR", "FV*", "FX*", "FY*", "EX*", "CX*", "CY*", "CV*")):
        # EX/CX often CV advanced / F-adjacent — treat as f_series when F present else cv_std
        if any(tok in m for tok in ("F*S", "F*R", "FRR", "FSR", "FSS", "FTR", "FVR", "FV*", "FX*", "FY*")):
            return "f_series"
        return "cv_std"
    # N-series CV
    if any(tok in m for tok in ("N*", "NHR", "NKR", "NPR", "NQR", "NPS", "NNR", "N*R", "N*S", "QKR")):
        return "cv_std"
    return None


def _load_config() -> dict:
    if CONFIG_PATH.is_file():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {}


def build_mileage_map() -> pd.DataFrame:
    if not MILEAGE_XLSX.is_file():
        raise FileNotFoundError(f"Missing mileage workbook: {MILEAGE_XLSX}")
    raw = pd.read_excel(MILEAGE_XLSX)
    raw.columns = [str(c).strip() for c in raw.columns]
    raw = raw.rename(
        columns={
            "CountryName": "country_name",
            "DistributorName": "distributor_name",
            "Count of VIN": "vin_count",
            "Average of Mileage per year": "annual_km_yr",
        }
    )
    raw["country_name"] = raw["country_name"].astype(str).str.strip()
    raw = raw[raw["country_name"].str.upper() != "GRAND TOTAL"]
    raw = raw[pd.to_numeric(raw["annual_km_yr"], errors="coerce").notna()]

    rows = []
    for _, r in raw.iterrows():
        ctry = str(r["country_name"]).strip()
        if ctry in MIDI_OR_OUT:
            status = "excluded_midi_or_out_of_18db"
            db = None
        else:
            db = COUNTRY_TO_DB_LCV.get(ctry)
            status = "mapped_lcv" if db else "unmapped"
        rows.append(
            {
                "country_name": ctry,
                "distributor_name": r.get("distributor_name"),
                "vin_count": int(r["vin_count"]) if pd.notna(r["vin_count"]) else 0,
                "annual_km_yr": float(r["annual_km_yr"]),
                "distributor_code": db,
                "scope": "LCV_warranty_sample",
                "map_status": status,
                "source_file": MILEAGE_XLSX.name,
            }
        )
    detail = pd.DataFrame(rows)

    # VIN-weighted rollup for Benelux etc.
    mapped = detail[detail["distributor_code"].notna()].copy()
    cfg = _load_config()
    lcv_iv = float(cfg.get("lcv_service_interval_km", 20000))
    parts = []
    for code, g in mapped.groupby("distributor_code"):
        vc = int(g["vin_count"].sum())
        km = float((g["vin_count"] * g["annual_km_yr"]).sum() / max(vc, 1))
        parts.append(
            {
                "distributor_code": code,
                "vin_count": vc,
                "annual_km_yr": round(km, 1),
                "source_countries": ",".join(sorted(g["country_name"].astype(str).unique())),
                "scope": "LCV_warranty_sample",
                "lcv_interval_km": lcv_iv,
                "svc_per_year_lcv": round(km / lcv_iv, 4),
                "note": "Do not apply to CV/N75 buckets",
            }
        )
    by_db = pd.DataFrame(parts).sort_values("distributor_code")
    detail_path = DERIVED / "eu_mileage_by_country_raw.csv"
    by_db_path = DERIVED / "eu_mileage_by_db_lcv.csv"
    detail.to_csv(detail_path, index=False)
    by_db.to_csv(by_db_path, index=False)
    return by_db


def build_cohort_weights(asof: date | None = None) -> pd.DataFrame:
    """Model-bucket shares + VIN age bands where available. SCR cutoffs flagged."""
    cfg = _load_config()
    intensity = cfg.get("cohort_intensity") or {}
    asof = asof or date(2025, 12, 31)
    buckets = load_uio_by_bucket()
    rows = []

    vin_ages: dict[str, dict[str, float]] = {}
    if VIN_PATH.is_file():
        vin = pd.read_csv(VIN_PATH, usecols=["db_code", "cohort_date"])
        vin["distributor_code"] = vin["db_code"].map(VIN_DB_TO_CODE)
        vin = vin[vin["distributor_code"].notna()]
        vin["cohort_date"] = pd.to_datetime(vin["cohort_date"], errors="coerce")
        vin = vin[vin["cohort_date"].notna()]
        vin["age_yr"] = (pd.Timestamp(asof) - vin["cohort_date"]).dt.days / 365.25
        for code, g in vin.groupby("distributor_code"):
            n = len(g)
            if n == 0:
                continue
            a0 = (g["age_yr"] <= 5).sum() / n
            a6 = ((g["age_yr"] > 5) & (g["age_yr"] <= 10)).sum() / n
            a11 = (g["age_yr"] > 10).sum() / n
            vin_ages[code] = {"age_0_5": a0, "age_6_10": a6, "age_11_plus": a11, "n_vin": n}

    for code, b in buckets.items():
        total = b["cv_std"] + b["f_series"] + b["lcv"]
        if total <= 0:
            continue
        ages = vin_ages.get(code)
        if ages:
            w = (
                ages["age_0_5"] * float(intensity.get("age_0_5", 1.05))
                + ages["age_6_10"] * float(intensity.get("age_6_10", 1.0))
                + ages["age_11_plus"] * float(intensity.get("age_11_plus", 0.9))
            )
            age_source = f"vin_register_n={int(ages['n_vin'])}"
        else:
            w = float(intensity.get("default_when_unknown", 1.0))
            age_source = "default_unknown_age"
            ages = {"age_0_5": None, "age_6_10": None, "age_11_plus": None, "n_vin": 0}

        rows.append(
            {
                "distributor_code": code,
                "cv_std_uio": b["cv_std"],
                "f_series_uio": b["f_series"],
                "lcv_uio": b["lcv"],
                "share_cv_std": round(b["cv_std"] / total, 4),
                "share_f_series": round(b["f_series"] / total, 4),
                "share_lcv": round(b["lcv"] / total, 4),
                "age_0_5_share": None if ages["age_0_5"] is None else round(ages["age_0_5"], 4),
                "age_6_10_share": None if ages["age_6_10"] is None else round(ages["age_6_10"], 4),
                "age_11_plus_share": None if ages["age_11_plus"] is None else round(ages["age_11_plus"], 4),
                "cohort_intensity": round(w, 4),
                "age_source": age_source,
                "scr_cutoffs_status": (cfg.get("scr_cutoffs") or {}).get("status", "need"),
                "scr_note": (cfg.get("scr_cutoffs") or {}).get("note", ""),
            }
        )
    out = pd.DataFrame(rows).sort_values("distributor_code")
    out.to_csv(DERIVED / "pms_v2_cohort_weights.csv", index=False)
    return out


def _bvp_fitment_rows() -> list[dict]:
    """Per PMS category × bucket from BVP crossref (baseline)."""
    if not CROSSREF.is_file():
        raise FileNotFoundError(CROSSREF)
    xref = pd.read_csv(CROSSREF, dtype=str)
    xref = xref[xref["pms_flag"].astype(str).str.lower().isin(["true", "1", "yes"])]
    xref = xref[xref["pms_category"].notna() & (xref["pms_category"].astype(str).str.strip() != "")]
    xref["bucket"] = xref["vehicle_model"].map(_bucket_from_vehicle_model)
    xref = xref[xref["bucket"].notna()]

    rows = []
    for cat, g in xref.groupby("pms_category"):
        counts = g["bucket"].value_counts()
        n = int(counts.sum())
        for bucket in FITMENT_BUCKETS:
            c = int(counts.get(bucket, 0))
            rows.append(
                {
                    "pms_category": cat,
                    "bucket": bucket,
                    "crossref_rows": c,
                    "fitment_share_of_category": round(c / n, 4) if n else 0.0,
                    "fitment_weight": 1.0 if c > 0 else 0.0,
                    "source": "bvp_crossref_vehicle_model",
                    "eq_hit_status": "bvp_only",
                    "eqhit_applicable_rows": 0,
                    "eqhit_unique_pns": 0,
                    "bvp_fitment_weight": 1.0 if c > 0 else 0.0,
                }
            )
    return rows


def _eqhit_category_bucket_counts() -> tuple[dict[str, dict[str, int]], dict[str, dict]]:
    """EQ-HIT extract → category→bucket applicable counts + per-category meta."""
    if not EQHIT_EXTRACT.is_file():
        return {}, {}
    ex = pd.read_csv(EQHIT_EXTRACT, dtype=str)
    if ex.empty:
        return {}, {}
    ex["pms_category"] = ex["pms_category"].astype(str).str.strip()
    ex["bucket"] = ex["bucket"].astype(str).str.strip().str.lower()
    ex["applicable"] = ex["applicable"].astype(str).str.lower()
    app = ex[ex["applicable"].isin(["true", "1", "yes"])].copy()
    app = app[~app["pms_category"].isin(EQHIT_SKIP_CATEGORIES)]
    # known buckets only for demand weights
    known = app[app["bucket"].isin(FITMENT_BUCKETS)]

    counts: dict[str, dict[str, int]] = {}
    meta: dict[str, dict] = {}
    for cat, g in known.groupby("pms_category"):
        bc = g["bucket"].value_counts().to_dict()
        counts[str(cat)] = {b: int(bc.get(b, 0)) for b in FITMENT_BUCKETS}
        # generation tags among LCV rows (Opt2 PN intensity later)
        lcv = g[g["bucket"] == "lcv"]
        gen = (
            lcv["lcv_generation"].astype(str).str.strip().str.lower().value_counts().to_dict()
            if "lcv_generation" in lcv.columns and not lcv.empty
            else {}
        )
        meta[str(cat)] = {
            "eqhit_applicable_rows": int(len(g)),
            "eqhit_unique_pns": int(g["part_number"].nunique()),
            "eqhit_unknown_bucket_rows": int(
                len(app[(app["pms_category"] == cat) & (~app["bucket"].isin(FITMENT_BUCKETS))])
            ),
            "lcv_gen_dmax_rt": int(gen.get("dmax_rt", 0)),
            "lcv_gen_dmax_rg": int(gen.get("dmax_rg", 0)),
            "lcv_gen_trooper": int(gen.get("trooper", 0)),
            "lcv_gen_unknown": int(gen.get("unknown", 0)),
            "extract_rows_total": int(len(ex[ex["pms_category"] == cat])),
        }
    return counts, meta


def build_fitment_weights() -> pd.DataFrame:
    """Per PMS category × bucket fitment.

    Baseline = BVP crossref. Categories present in EQ-HIT extract (applicable + known
    bucket) overwrite weights from extract seed-PN applicability. oil_filter stays BVP
    (pull skipped). Binary weight: 1.0 if ≥1 applicable row for that bucket else 0.0.
    """
    rows = _bvp_fitment_rows()
    by_key = {(r["pms_category"], r["bucket"]): r for r in rows}
    eq_counts, eq_meta = _eqhit_category_bucket_counts()

    for cat, bucket_counts in eq_counts.items():
        n = sum(bucket_counts.values())
        meta = eq_meta.get(cat) or {}
        for bucket in FITMENT_BUCKETS:
            c = int(bucket_counts.get(bucket, 0))
            key = (cat, bucket)
            base = by_key.get(key)
            bvp_w = float(base["fitment_weight"]) if base else 0.0
            bvp_rows = int(base["crossref_rows"]) if base else 0
            row = {
                "pms_category": cat,
                "bucket": bucket,
                "crossref_rows": c,  # EQ-HIT applicable rows for this bucket
                "fitment_share_of_category": round(c / n, 4) if n else 0.0,
                "fitment_weight": 1.0 if c > 0 else 0.0,
                "source": "eqhit_extract_priority_cy2025",
                "eq_hit_status": "extract_backed",
                "eqhit_applicable_rows": int(meta.get("eqhit_applicable_rows", 0)),
                "eqhit_unique_pns": int(meta.get("eqhit_unique_pns", 0)),
                "bvp_fitment_weight": bvp_w,
                "bvp_crossref_rows": bvp_rows,
                "weight_changed_vs_bvp": (1.0 if c > 0 else 0.0) != bvp_w,
            }
            by_key[key] = row

    # Mark remaining BVP-only cats that have no extract yet
    for r in by_key.values():
        if r.get("eq_hit_status") == "bvp_only" and r["pms_category"] in EQHIT_SKIP_CATEGORIES:
            r["eq_hit_status"] = "skipped_oil_filter"
        elif r.get("eq_hit_status") == "bvp_only" and r["pms_category"] not in eq_counts:
            r["eq_hit_status"] = "bvp_stub_no_extract"

    out = pd.DataFrame(list(by_key.values())).sort_values(["pms_category", "bucket"])
    out.to_csv(DERIVED / "pms_v2_fitment_weights.csv", index=False)

    # Coverage diagnostic (one row per extract category)
    cov_rows = []
    for cat, meta in sorted(eq_meta.items()):
        bc = eq_counts.get(cat) or {}
        cov_rows.append(
            {
                "pms_category": cat,
                "extract_rows_total": meta.get("extract_rows_total", 0),
                "eqhit_applicable_known_bucket": meta.get("eqhit_applicable_rows", 0),
                "eqhit_unique_pns": meta.get("eqhit_unique_pns", 0),
                "eqhit_unknown_bucket_rows": meta.get("eqhit_unknown_bucket_rows", 0),
                "rows_cv_std": bc.get("cv_std", 0),
                "rows_f_series": bc.get("f_series", 0),
                "rows_lcv": bc.get("lcv", 0),
                "lcv_gen_dmax_rt": meta.get("lcv_gen_dmax_rt", 0),
                "lcv_gen_dmax_rg": meta.get("lcv_gen_dmax_rg", 0),
                "lcv_gen_trooper": meta.get("lcv_gen_trooper", 0),
                "lcv_gen_unknown": meta.get("lcv_gen_unknown", 0),
                "fitment_source": "eqhit_extract",
                "note": "Seed-PN applicability — not full catalogue; oil skipped",
            }
        )
    # oil stub row
    cov_rows.append(
        {
            "pms_category": "oil_filter",
            "extract_rows_total": 0,
            "eqhit_applicable_known_bucket": 0,
            "eqhit_unique_pns": 0,
            "eqhit_unknown_bucket_rows": 0,
            "rows_cv_std": None,
            "rows_f_series": None,
            "rows_lcv": None,
            "lcv_gen_dmax_rt": None,
            "lcv_gen_dmax_rg": None,
            "lcv_gen_trooper": None,
            "lcv_gen_unknown": None,
            "fitment_source": "bvp_only_skipped_eqhit",
            "note": "Oil intentionally skipped in EQ-HIT pull; Opt1 oil lens stays BVP",
        }
    )
    pd.DataFrame(cov_rows).to_csv(DERIVED / "pms_v2_eqhit_fitment_coverage.csv", index=False)
    return out


def build_eqhit_category_gap_analysis(pms_v2: pd.DataFrame, fit: pd.DataFrame) -> pd.DataFrame:
    """CY2025 total-line gaps for EQ-HIT extract categories (contested capture lens)."""
    extract_cats = sorted(
        {
            str(c)
            for c in fit.loc[fit["eq_hit_status"] == "extract_backed", "pms_category"].unique()
        }
    )
    if not extract_cats:
        out = pd.DataFrame()
        out.to_csv(DERIVED / "pms_v2_eqhit_category_gap_cy2025.csv", index=False)
        return out

    tot = pms_v2[
        (pms_v2["year"] == 2025)
        & (pms_v2["line_type"] == "total")
        & (pms_v2["pms_category"].isin(extract_cats))
    ].copy()

    # Attach fitment flags (LCV / CV presence)
    fit_lcv = (
        fit[fit["bucket"] == "lcv"][["pms_category", "fitment_weight", "source", "bvp_fitment_weight"]]
        .rename(
            columns={
                "fitment_weight": "fitment_lcv",
                "source": "fitment_source",
                "bvp_fitment_weight": "bvp_fitment_lcv",
            }
        )
    )
    tot = tot.merge(fit_lcv, on="pms_category", how="left")

    rows = []
    for cat, g in tot.groupby("pms_category"):
        gap = g["revenue_gap_v2_eur"].fillna(0).sum()
        act = g["actual_qty"].sum()
        exp = g["expected_qty_v2"].sum()
        cap = (act / exp) if exp > 0 else None
        # worst DBs by capture (total)
        g2 = g.copy()
        g2["cap"] = g2.apply(
            lambda r: (r["actual_qty"] / r["expected_qty_v2"])
            if r["expected_qty_v2"] and r["expected_qty_v2"] > 0
            else None,
            axis=1,
        )
        low = g2.nsmallest(3, "cap", keep="all") if g2["cap"].notna().any() else g2.head(0)
        high_gap = g2.nlargest(3, "revenue_gap_v2_eur")
        rows.append(
            {
                "year": 2025,
                "pms_category": cat,
                "line_type": "total",
                "network_actual_qty": round(float(act), 2),
                "network_expected_qty_v2": round(float(exp), 2),
                "network_capture_v2": None if cap is None else round(float(cap), 4),
                "network_revenue_gap_v2_eur": round(float(gap), 2),
                "fitment_lcv": float(g["fitment_lcv"].iloc[0]) if "fitment_lcv" in g.columns else None,
                "bvp_fitment_lcv": float(g["bvp_fitment_lcv"].iloc[0])
                if "bvp_fitment_lcv" in g.columns
                else None,
                "fitment_source": g["fitment_source"].iloc[0] if "fitment_source" in g.columns else None,
                "lowest_capture_dbs": ";".join(
                    f"{r.distributor_code}:{r.cap:.3f}" for r in low.itertuples() if r.cap is not None
                ),
                "largest_gap_dbs": ";".join(
                    f"{r.distributor_code}:{r.revenue_gap_v2_eur:.0f}"
                    for r in high_gap.itertuples()
                    if pd.notna(r.revenue_gap_v2_eur)
                ),
            }
        )
    out = pd.DataFrame(rows).sort_values("network_revenue_gap_v2_eur", ascending=False)
    out.to_csv(DERIVED / "pms_v2_eqhit_category_gap_cy2025.csv", index=False)

    # DB × category contested matrix (extract cats only)
    mat = tot[
        [
            "distributor_code",
            "pms_category",
            "actual_qty",
            "expected_qty_v1",
            "expected_qty_v2",
            "capture_rate_v1",
            "capture_rate_v2",
            "revenue_gap_v2_eur",
            "fitment_lcv",
            "bvp_fitment_lcv",
            "fitment_source",
        ]
    ].copy()
    mat.to_csv(DERIVED / "pms_v2_eqhit_contested_by_db_cy2025.csv", index=False)
    return out


def _svc_buckets(distributor_code: str, mileage_by_db: pd.DataFrame) -> dict[str, float]:
    svc = {**BUCKET_SERVICES_PER_YEAR, **BUCKET_SERVICES_PER_YEAR_OVERRIDES.get(distributor_code, {})}
    # LCV mileage override only
    m = mileage_by_db[mileage_by_db["distributor_code"] == distributor_code]
    if not m.empty and float(m.iloc[0]["vin_count"]) > 0:
        svc["lcv"] = float(m.iloc[0]["svc_per_year_lcv"])
    return svc


def _fitment_for_cat(fit: pd.DataFrame, cat: str) -> dict[str, float]:
    sub = fit[fit["pms_category"] == cat]
    if sub.empty:
        return {"cv_std": 1.0, "f_series": 1.0, "lcv": 1.0}
    return {r["bucket"]: float(r["fitment_weight"]) for _, r in sub.iterrows()}


def expected_v2(
    distributor_code: str,
    buckets: dict[str, float],
    svc: dict[str, float],
    cohort_intensity: float,
    fit: pd.DataFrame,
    addr: float = 1.0,
) -> dict[str, float]:
    base_cv = buckets["cv_std"] * svc["cv_std"] * addr
    base_f = buckets["f_series"] * svc["f_series"] * addr
    base_l = buckets["lcv"] * svc["lcv"] * addr
    all_factors = {**CONSUMABLE_FACTOR, **WEAR_FACTOR}
    out: dict[str, float] = {}
    for cat, fac in all_factors.items():
        fac_l = LCV_BUCKET_FACTOR_OVERRIDES.get(cat, fac)
        fw = _fitment_for_cat(fit, cat)
        # If category has no crossref rows at all, keep weight 1.0 (don't zero demand)
        cat_rows = fit[fit["pms_category"] == cat]
        if cat_rows.empty or cat_rows["crossref_rows"].sum() == 0:
            fw = {"cv_std": 1.0, "f_series": 1.0, "lcv": 1.0}
        qty = (
            base_cv * fac * fw.get("cv_std", 1.0)
            + base_f * fac * fw.get("f_series", 1.0)
            + base_l * fac_l * fw.get("lcv", 1.0)
        ) * cohort_intensity
        out[cat] = qty
    return out


def build_pms_v2_capture(
    mileage_by_db: pd.DataFrame,
    cohorts: pd.DataFrame,
    fit: pd.DataFrame,
) -> pd.DataFrame:
    if not PMS_V1.is_file():
        raise FileNotFoundError(PMS_V1)
    v1 = pd.read_csv(PMS_V1)
    buckets_all = load_uio_by_bucket()
    cohort_map = cohorts.set_index("distributor_code")["cohort_intensity"].to_dict()

    rows = []
    for (year, dist, cat, line_type), g in v1.groupby(
        ["year", "distributor_code", "pms_category", "line_type"]
    ):
        r0 = g.iloc[0]
        b = buckets_all.get(dist)
        if not b:
            continue
        svc = _svc_buckets(dist, mileage_by_db)
        intensity = float(cohort_map.get(dist, 1.0))
        exp_map = expected_v2(dist, b, svc, intensity, fit)
        exp_v2 = float(exp_map.get(cat, 0.0))
        exp_v1 = float(r0["expected_qty"])
        actual = float(r0["actual_qty"])
        rev = float(r0["actual_rev_eur"]) if pd.notna(r0["actual_rev_eur"]) else 0.0
        avg_sp = float(r0["avg_sp_eur"]) if pd.notna(r0.get("avg_sp_eur")) else None
        cap_v2 = (actual / exp_v2) if exp_v2 > 0 else None
        gap_v2 = None
        if avg_sp is not None and exp_v2 > 0:
            gap_v2 = (exp_v2 - actual) * avg_sp
        rows.append(
            {
                "year": int(year),
                "distributor_code": dist,
                "pms_category": cat,
                "category_label": r0.get("category_label"),
                "line_type": line_type,
                "uio_units": r0.get("uio_units"),
                "expected_qty_v1": exp_v1,
                "expected_qty_v2": round(exp_v2, 2),
                "actual_qty": actual,
                "actual_rev_eur": rev,
                "capture_rate_v1": r0.get("capture_rate"),
                "capture_rate_v2": None if cap_v2 is None else round(cap_v2, 4),
                "avg_sp_eur": avg_sp,
                "revenue_gap_v2_eur": None if gap_v2 is None else round(gap_v2, 2),
                "svc_cv_std": svc["cv_std"],
                "svc_f_series": svc["f_series"],
                "svc_lcv": svc["lcv"],
                "cohort_intensity": intensity,
                "mileage_lcv_applied": dist in set(mileage_by_db["distributor_code"]),
                "scope": "v2_shadow_mileage_cohort_fitment",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(DERIVED / "pms_capture_by_db_year_v2_mileage.csv", index=False)
    return out


def build_gps_wallet_v2(pms_v2: pd.DataFrame) -> pd.DataFrame:
    """Wallet = sum expected_v2 * avg_sp for total line_type; index vs actual PMS EUR; classic GPS alongside."""
    tot = pms_v2[pms_v2["line_type"] == "total"].copy()
    parts = []
    for (year, dist), g in tot.groupby(["year", "distributor_code"]):
        w = 0.0
        for _, r in g.iterrows():
            sp = r["avg_sp_eur"]
            if pd.isna(sp):
                continue
            w += float(r["expected_qty_v2"]) * float(sp)
        actual = float(g["actual_rev_eur"].sum())
        exp_e = float(g["expected_qty_v2"].sum())
        act_e = float(g["actual_qty"].sum())
        parts.append(
            {
                "year": int(year),
                "distributor_code": dist,
                "wallet_eur": round(w, 2),
                "actual_pms_eur": round(actual, 2),
                "gps_index_vs_wallet": round(actual / w, 4) if w > 0 else None,
                "expected_events": round(exp_e, 2),
                "actual_events": round(act_e, 2),
                "pms_capture_events_v2": round(act_e / exp_e, 4) if exp_e > 0 else None,
            }
        )
    out = pd.DataFrame(parts)
    if GPS_V1.is_file():
        gps = pd.read_csv(GPS_V1)
        keep = [
            "year",
            "distributor_code",
            "total_sales_eur",
            "uio_units",
            "spend_per_unit_eur",
            "traffic_light",
        ]
        gps = gps[[c for c in keep if c in gps.columns]]
        out = out.merge(gps, on=["year", "distributor_code"], how="left")
        out = out.rename(
            columns={
                "spend_per_unit_eur": "gps_v1_spend_per_unit_eur",
                "total_sales_eur": "gps_v1_total_sales_eur",
                "traffic_light": "gps_v1_traffic_light",
            }
        )
    out.to_csv(DERIVED / "gps_wallet_v2_by_distributor.csv", index=False)
    return out


def write_findings(
    mileage: pd.DataFrame,
    cohorts: pd.DataFrame,
    pms_v2: pd.DataFrame,
    gps_v2: pd.DataFrame,
    skeleton: pd.DataFrame | None = None,
    sensitivity: pd.DataFrame | None = None,
    fit: pd.DataFrame | None = None,
    eqhit_gaps: pd.DataFrame | None = None,
) -> Path:
    y = 2025
    tot = pms_v2[(pms_v2["year"] == y) & (pms_v2["line_type"] == "total") & (pms_v2["pms_category"] == "oil_filter")]
    lines = [
        "# GPS / PMS V2 shadow — findings",
        "",
        f"**Built:** {date.today().isoformat()} · Mode B shadow · V1 untouched",
        "",
        "## Mileage layer (LCV)",
        "",
        f"DBs with LCV km mapped: **{len(mileage)}**",
        "",
    ]
    if not mileage.empty:
        top = mileage.sort_values("annual_km_yr", ascending=False).head(8)
        lines.append("| DB | km/yr | VIN n | svc/yr LCV |")
        lines.append("|----|------:|------:|-----------:|")
        for _, r in top.iterrows():
            lines.append(
                f"| {r['distributor_code']} | {r['annual_km_yr']:.0f} | {r['vin_count']} | {r['svc_per_year_lcv']:.3f} |"
            )
        lines.append("")
    vin_cohorts = cohorts[cohorts["age_source"].astype(str).str.startswith("vin_")]
    lines += [
        "## Cohorts",
        "",
        f"VIN age intensity available for **{len(vin_cohorts)}** DBs; others intensity=1.0.",
        "SCR cutoffs: **still need** from IMIT (15k vs 20k not applied).",
        "",
    ]

    # Solo progress (Ireland Opt2 / Portugal Opt3 / sensitivity)
    lines += ["## Solo progress (2026-09-05)", ""]
    if skeleton is not None and not skeleton.empty:
        ie = skeleton[skeleton["distributor_code"] == "IRELAND"]
        pt = skeleton[skeleton["distributor_code"] == "PORTUGAL"]
        opt2_on = skeleton[skeleton["opt2_enabled"].astype(str).str.lower().isin(["true", "1"])]
        if not ie.empty:
            r = ie.iloc[0]
            ie_on = str(r.get("opt2_enabled")).lower() in ("true", "1")
            lines.append(
                f"- **Ireland Opt2:** {'ON' if ie_on else 'OFF'} — "
                f"SIMI Trooper vs D-Max aggregate (RT/RG not separable; D-Max on RT col, RG=0). "
                f"Trooper UIO≈{r.get('subtype_trooper')}, D-Max/RT≈{r.get('subtype_dmax_rt')}."
            )
        if not pt.empty:
            r = pt.iloc[0]
            src = r.get("opt3_age_source") or "—"
            lines.append(
                f"- **Portugal Opt3:** {'ON' if str(r.get('opt3_enabled')).lower() in ('true', '1') else 'OFF'} — "
                f"share_age_le_10=**{r.get('share_age_le_10')}** (Matriculas preferred over VIN). Source: `{src}`."
            )
        lines.append(
            f"- **Opt2 enabled DBs:** {', '.join(sorted(opt2_on['distributor_code'].astype(str))) or 'none'}."
        )
    if sensitivity is not None and not sensitivity.empty:
        lines.append(
            f"- **Opt1 sensitivity:** `pms_v2_lcv_opt1_sensitivity.csv` — "
            f"method `{sensitivity.iloc[0].get('sensitivity_method')}` (±20% DB km); mid = current Opt1. "
            f"Network km P25/mean/P75 context: "
            f"{sensitivity.iloc[0].get('network_km_p25')} / "
            f"{sensitivity.iloc[0].get('network_km_mean')} / "
            f"{sensitivity.iloc[0].get('network_km_p75')}."
        )
    lines.append("")

    # EQ-HIT fitment overlay
    lines += ["## EQ-HIT fitment overlay (seed extract → V2 weights)", ""]
    if fit is not None and not fit.empty:
        backed = fit[fit["eq_hit_status"] == "extract_backed"]
        cats = sorted(backed["pms_category"].unique()) if not backed.empty else []
        flipped = (
            backed[backed["weight_changed_vs_bvp"] == True]
            if "weight_changed_vs_bvp" in backed.columns
            else backed.head(0)
        )
        lines.append(
            f"- Extract SSOT: `eqhit_extract_priority_cy2025.csv` wired into `pms_v2_fitment_weights.csv`."
        )
        lines.append(f"- Extract-backed categories: **{', '.join(cats) or 'none'}**.")
        lines.append("- Oil: **skipped** — Opt1 oil lens stays BVP (`eq_hit_status=skipped_oil_filter`).")
        lines.append(
            "- Scope caveat: weights = **seed-PN applicability** (37 PNs / 2311 rows), not full catalogue."
        )
        if flipped is not None and not flipped.empty:
            lines.append("- **BVP → EQ-HIT weight flips** (bucket binary changed):")
            for _, r in flipped.sort_values(["pms_category", "bucket"]).iterrows():
                lines.append(
                    f"  - `{r['pms_category']}` / `{r['bucket']}`: BVP={r.get('bvp_fitment_weight')} → "
                    f"EQ-HIT={r['fitment_weight']} (rows={r['crossref_rows']})"
                )
        cov_path = DERIVED / "pms_v2_eqhit_fitment_coverage.csv"
        if cov_path.is_file():
            lines.append(f"- Coverage detail: `{cov_path.name}`.")
    else:
        lines.append("- Fitment frame missing — re-run shadow builder.")
    if eqhit_gaps is not None and not eqhit_gaps.empty:
        lines += [
            "",
            f"## Contested capture — EQ-HIT categories CY{y} (total)",
            "",
            "| Category | capture V2 | EUR gap | LCV fitment | Lowest capture DBs |",
            "|----------|-----------:|--------:|:-----------:|--------------------|",
        ]
        for _, r in eqhit_gaps.head(10).iterrows():
            lines.append(
                f"| {r['pms_category']} | {r['network_capture_v2']} | "
                f"{r['network_revenue_gap_v2_eur']:.0f} | {r.get('fitment_lcv')} | "
                f"{r.get('lowest_capture_dbs') or '—'} |"
            )
    lines += [
        "",
        f"## Oil filter CY{y} — V1 vs V2 capture (total)",
        "",
        "| DB | capture V1 | capture V2 | expected V1 | expected V2 |",
        "|----|-----------:|-----------:|------------:|------------:|",
    ]
    for _, r in tot.sort_values("distributor_code").iterrows():
        lines.append(
            f"| {r['distributor_code']} | {r['capture_rate_v1']} | {r['capture_rate_v2']} | "
            f"{r['expected_qty_v1']} | {r['expected_qty_v2']} |"
        )
    # V1 vs V2 Opt1 movers (oil lens — primary mileage effect)
    movers = tot.copy()
    movers["delta_cap"] = pd.to_numeric(movers["capture_rate_v2"], errors="coerce") - pd.to_numeric(
        movers["capture_rate_v1"], errors="coerce"
    )
    lines += [
        "",
        f"## V1 → V2 Opt1 movers (oil_filter total CY{y}) — capture delta",
        "",
        "| Direction | DB | Δ capture | V1 | V2 |",
        "|-----------|----|----------:|---:|---:|",
    ]
    down = movers.nsmallest(5, "delta_cap")
    up = movers.nlargest(5, "delta_cap")
    for _, r in down.iterrows():
        lines.append(
            f"| down | {r['distributor_code']} | {r['delta_cap']:.4f} | "
            f"{r['capture_rate_v1']} | {r['capture_rate_v2']} |"
        )
    for _, r in up.iterrows():
        if r["distributor_code"] in set(down["distributor_code"]):
            continue
        lines.append(
            f"| up | {r['distributor_code']} | {r['delta_cap']:.4f} | "
            f"{r['capture_rate_v1']} | {r['capture_rate_v2']} |"
        )
    g25 = gps_v2[gps_v2["year"] == y].sort_values("gps_index_vs_wallet", ascending=True)
    lines += [
        "",
        f"## GPS wallet index CY{y} (actual PMS € / wallet) — lowest first",
        "",
        "| DB | index | wallet € | actual PMS € | V1 €/UIO |",
        "|----|------:|---------:|-------------:|---------:|",
    ]
    for _, r in g25.head(12).iterrows():
        spu = r.get("gps_v1_spend_per_unit_eur")
        spu_s = f"{spu:.0f}" if pd.notna(spu) else "—"
        idx = r.get("gps_index_vs_wallet")
        idx_s = f"{idx:.2f}" if pd.notna(idx) else "—"
        lines.append(
            f"| {r['distributor_code']} | {idx_s} | {r['wallet_eur']:.0f} | {r['actual_pms_eur']:.0f} | {spu_s} |"
        )
    lines += [
        "",
        "## Still stub / open",
        "",
        "- Categories without extract (clutch_kit, air_filter, clutch_booster, release_bearing, urea_filter, pilot_bearing): **BVP stub**.",
        "- Opt2 PN-level generation intensity: LCV generation tags still mostly `unknown` except partial `dmax_rt`/`dmax_rg`.",
        "- SCR cutoffs: need IMIT. V20 UIO not applied. No Mode A / V1 cutover.",
        "",
        "## Constraints",
        "",
        "- Do not quote V2 as the network KPI.",
        "- IML Model B ITUK headline unchanged.",
        "- Primary capture = **total** sales (not genuine-only).",
        "",
    ]
    path = DERIVED / "gps_pms_v2_findings.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _portugal_matriculas_shares() -> dict | None:
    """Cumulative Matriculas SUM 2005-2025 → RT vs RG shares (no Trooper)."""
    path = ISZE_ROOT / "01_data" / "07_UIO" / "Matriculas Isuzu SAP.xlsx"
    if not path.is_file():
        return None
    s = pd.read_excel(path, sheet_name="SUM", header=None)
    years = pd.to_numeric(s.iloc[3, 5:], errors="coerce")
    mask = years.notna() & (years >= 2005) & (years <= 2025)
    if not mask.any():
        return None

    def _sum_row(ri: int) -> float:
        vals = pd.to_numeric(s.iloc[ri, 5:], errors="coerce").fillna(0)
        return float(vals[mask.values].sum())

    rt56, rt88, rg = _sum_row(7), _sum_row(8), _sum_row(9)
    rt = rt56 + rt88
    denom = rt + rg
    if denom <= 0:
        return None
    return {
        "rt_regs": int(rt),
        "rg_regs": int(rg),
        "trooper_regs": 0,
        "share_rt": rt / denom,
        "share_rg": rg / denom,
        "share_trooper": 0.0,
        "source": "Matriculas_SUM_2005_2025_scaled_to_UIO",
    }


def _portugal_matriculas_age_share_le10(asof_year: int = 2025) -> dict | None:
    """Share of Matriculas LCV regs with age ≤10 at asof year-end (prefer over VIN).

    LCV rows on SUM: Rodeo / TF190 / RT56 / RT88 / RG (rows 5–9).
    Age lock: (asof_year - registration_year) ≤ 10 → year >= asof_year - 10.
    """
    path = ISZE_ROOT / "01_data" / "07_UIO" / "Matriculas Isuzu SAP.xlsx"
    if not path.is_file():
        return None
    s = pd.read_excel(path, sheet_name="SUM", header=None)
    years = pd.to_numeric(s.iloc[3, 5:], errors="coerce")
    lcv = None
    for ri in range(5, 10):
        vals = pd.to_numeric(s.iloc[ri, 5:], errors="coerce").fillna(0.0)
        lcv = vals if lcv is None else lcv + vals
    if lcv is None:
        return None
    y_min = asof_year - 10
    mask_all = years.notna() & (years >= 2005) & (years <= asof_year)
    mask_le10 = years.notna() & (years >= y_min) & (years <= asof_year)
    if not mask_all.any():
        return None
    tot = float(lcv[mask_all.values].sum())
    le10 = float(lcv[mask_le10.values].sum())
    if tot <= 0:
        return None
    return {
        "lcv_regs_total": int(tot),
        "lcv_regs_age_le_10": int(le10),
        "share_age_le_10": le10 / tot,
        "asof": f"{asof_year}-12-31",
        "year_floor": y_min,
        "source": "Matriculas_SUM_LCV_age_le10_prefer_over_VIN",
    }


def _ireland_simi_shares() -> dict | None:
    """SIMI isuzuregdata Sheet2 — Trooper vs D-Max aggregate (RT/RG not separable).

    Mapping:
      - Trooper line → Trooper
      - D max + LCV TFS → D-Max aggregate stored on subtype_dmax_rt; subtype_dmax_rg = 0
      - RT vs RG not in SIMI — do not invent a split
    """
    path = ISZE_ROOT / "01_data" / "07_UIO" / "isuzuregdata.xlsx"
    if not path.is_file():
        return None
    s = pd.read_excel(path, sheet_name="Sheet2", header=None)
    # Row labels col0; year sums col1+
    label_col = s.iloc[:, 0].astype(str).str.strip().str.lower()

    def _row_sum(label_sub: str) -> float:
        hits = s.index[label_col == label_sub.lower()]
        if len(hits) == 0:
            # fuzzy contains
            hits = s.index[label_col.str.contains(label_sub.lower(), na=False)]
        if len(hits) == 0:
            return 0.0
        vals = pd.to_numeric(s.iloc[hits[0], 1:], errors="coerce").fillna(0.0)
        return float(vals.sum())

    dmax = _row_sum("d max")  # Sheet2 label "D max"
    if dmax <= 0:
        dmax = _row_sum("d-max")
    tfs = _row_sum("lcv tfs")
    trooper = _row_sum("trooper")
    dmax_agg = dmax + tfs
    denom = dmax_agg + trooper
    if denom <= 0:
        return None
    return {
        "dmax_regs": int(dmax_agg),
        "trooper_regs": int(trooper),
        "tfs_regs": int(tfs),
        "rg_regs": 0,
        "share_dmax": dmax_agg / denom,
        "share_trooper": trooper / denom,
        "share_rt": dmax_agg / denom,  # aggregate parked on RT column
        "share_rg": 0.0,
        "mapping": "trooper_vs_dmax_aggregate__rt_rg_not_separable",
        "source": "SIMI_isuzuregdata_Sheet2_2010_2025_scaled_to_UIO",
    }


def build_uio_accuracy(buckets: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Rank A-D per DB for LCV UIO hover."""
    pt = _portugal_matriculas_shares()
    ie = _ireland_simi_shares()
    rows = []
    for code, b in sorted(buckets.items()):
        lcv = float(b.get("lcv", 0) or 0)
        if lcv <= 0:
            rows.append(
                {
                    "distributor_code": code,
                    "lcv_uio": 0.0,
                    "uio_accuracy_rank": "N/A",
                    "hover_text": "No LCV UIO in bucket — CV-only DB for V2 LCV panel",
                    "subtype_trooper": None,
                    "subtype_dmax_rt": None,
                    "subtype_dmax_rg": None,
                    "opt2_enabled": False,
                    "source_label": "n/a",
                }
            )
            continue
        if code == "PORTUGAL" and pt:
            rows.append(
                {
                    "distributor_code": code,
                    "lcv_uio": lcv,
                    "uio_accuracy_rank": "B",
                    "hover_text": (
                        f"Portugal LCV UIO {lcv:.0f} (v19). Matriculas RT+RG regs "
                        f"{pt['rt_regs']+pt['rg_regs']} used as shares only — "
                        f"Trooper=0; not rank A (no Trooper count)."
                    ),
                    "subtype_trooper": 0.0,
                    "subtype_dmax_rt": round(lcv * pt["share_rt"], 1),
                    "subtype_dmax_rg": round(lcv * pt["share_rg"], 1),
                    "opt2_enabled": True,
                    "source_label": pt["source"],
                }
            )
        elif code == "IRELAND" and ie:
            rows.append(
                {
                    "distributor_code": code,
                    "lcv_uio": lcv,
                    "uio_accuracy_rank": "B",
                    "hover_text": (
                        f"Ireland LCV UIO {lcv:.0f} (v19). SIMI Trooper={ie['trooper_regs']} / "
                        f"D-Max+TFS={ie['dmax_regs']} regs as shares — RT/RG not separable "
                        f"(D-Max aggregate on RT column, RG=0). Opt2 on. Not rank A."
                    ),
                    "subtype_trooper": round(lcv * ie["share_trooper"], 1),
                    "subtype_dmax_rt": round(lcv * ie["share_rt"], 1),
                    "subtype_dmax_rg": 0.0,
                    "opt2_enabled": True,
                    "source_label": ie["source"],
                }
            )
        elif code == "IRELAND":
            rows.append(
                {
                    "distributor_code": code,
                    "lcv_uio": lcv,
                    "uio_accuracy_rank": "B",
                    "hover_text": (
                        f"Ireland LCV UIO {lcv:.0f} (v19). SIMI isuzuregdata missing or "
                        "unparseable — Opt2 off."
                    ),
                    "subtype_trooper": None,
                    "subtype_dmax_rt": None,
                    "subtype_dmax_rg": None,
                    "opt2_enabled": False,
                    "source_label": "SIMI_isuzuregdata_missing",
                }
            )
        else:
            rows.append(
                {
                    "distributor_code": code,
                    "lcv_uio": lcv,
                    "uio_accuracy_rank": "C",
                    "hover_text": (
                        f"LCV UIO {lcv:.0f} from UIO v19 / IMIT shipment×survival. "
                        "No gov subtype (Trooper/RT/RG). Opt2 off."
                    ),
                    "subtype_trooper": None,
                    "subtype_dmax_rt": None,
                    "subtype_dmax_rg": None,
                    "opt2_enabled": False,
                    "source_label": "uio_v19_model",
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(DERIVED / "lcv_uio_accuracy_by_db.csv", index=False)
    return out


def build_lcv_opt_skeleton(
    mileage: pd.DataFrame,
    cohorts: pd.DataFrame,
    accuracy: pd.DataFrame,
    pms_v2: pd.DataFrame,
) -> pd.DataFrame:
    """Opt1 live; Opt2/Opt3 skeleton columns + enable flags (oil_filter total CY2025 lens)."""
    cfg = _load_config()
    lcv_iv = float(cfg.get("lcv_service_interval_km", 20000))
    gen_iv = cfg.get("generation_interval_km") or {}
    max_age = int(cfg.get("opt3_max_age_years", 10))
    buckets = load_uio_by_bucket()
    mile_map = mileage.set_index("distributor_code") if not mileage.empty else pd.DataFrame()
    cohort_map = cohorts.set_index("distributor_code") if not cohorts.empty else pd.DataFrame()
    acc_map = accuracy.set_index("distributor_code")
    pt_age = _portugal_matriculas_age_share_le10(asof_year=2025)

    # Opt1 oil filter expected from existing v2 capture (total, 2025)
    oil = pms_v2[
        (pms_v2["year"] == 2025)
        & (pms_v2["line_type"] == "total")
        & (pms_v2["pms_category"] == "oil_filter")
    ].set_index("distributor_code")

    rows = []
    for code, b in sorted(buckets.items()):
        lcv = float(b.get("lcv", 0) or 0)
        if lcv <= 0:
            continue
        acc = acc_map.loc[code] if code in acc_map.index else None
        svc_lcv = 1.0
        if code in mile_map.index:
            svc_lcv = float(mile_map.loc[code, "svc_per_year_lcv"])
        intensity = 1.0
        share_le_10 = None
        opt3_on = False
        opt3_age_source = None
        if code in cohort_map.index:
            intensity = float(cohort_map.loc[code, "cohort_intensity"])
            a0 = cohort_map.loc[code, "age_0_5_share"]
            a6 = cohort_map.loc[code, "age_6_10_share"]
            if pd.notna(a0) and pd.notna(a6):
                share_le_10 = float(a0) + float(a6)
                opt3_on = True
                opt3_age_source = "vin_cohort_proxy"

        # Portugal Opt3: prefer Matriculas first-registration year shares over VIN
        if code == "PORTUGAL" and pt_age is not None:
            share_le_10 = float(pt_age["share_age_le_10"])
            opt3_on = True
            opt3_age_source = pt_age["source"]

        opt1_exp = float(oil.loc[code, "expected_qty_v2"]) if code in oil.index else None
        actual = float(oil.loc[code, "actual_qty"]) if code in oil.index else None
        cap1 = float(oil.loc[code, "capture_rate_v2"]) if code in oil.index else None

        # Opt2
        opt2_on = bool(acc["opt2_enabled"]) if acc is not None else False
        trooper = acc["subtype_trooper"] if acc is not None else None
        rt = acc["subtype_dmax_rt"] if acc is not None else None
        rg = acc["subtype_dmax_rg"] if acc is not None else None
        opt2_exp = None
        if opt2_on and rt is not None and rg is not None:
            iv_rt = gen_iv.get("dmax_rt") or lcv_iv
            iv_rg = gen_iv.get("dmax_rg") or lcv_iv
            iv_tr = gen_iv.get("trooper") or iv_rt  # Jerome: Trooper = RT interval
            km = float(mile_map.loc[code, "annual_km_yr"]) if code in mile_map.index else lcv_iv
            svc_rt = km / float(iv_rt)
            svc_rg = km / float(iv_rg)
            svc_tr = km / float(iv_tr) if iv_tr else 0.0
            tr = float(trooper or 0)
            opt2_exp = (float(rt) * svc_rt + float(rg) * svc_rg + tr * svc_tr) * intensity

        opt3_exp = None
        if opt3_on and opt1_exp is not None and share_le_10 is not None:
            opt3_exp = opt1_exp * share_le_10

        rows.append(
            {
                "year": 2025,
                "distributor_code": code,
                "pms_category": "oil_filter",
                "line_type": "total",
                "lcv_uio": lcv,
                "uio_accuracy_rank": acc["uio_accuracy_rank"] if acc is not None else "C",
                "hover_text": acc["hover_text"] if acc is not None else "",
                "opt1_enabled": True,
                "expected_qty_opt1": None if opt1_exp is None else round(opt1_exp, 2),
                "capture_rate_opt1": cap1,
                "opt2_enabled": opt2_on,
                "subtype_trooper": trooper,
                "subtype_dmax_rt": rt,
                "subtype_dmax_rg": rg,
                "trooper_schedule_status": "same_as_rt_20k",
                "expected_qty_opt2": None if opt2_exp is None else round(opt2_exp, 2),
                "capture_rate_opt2": (
                    None
                    if opt2_exp is None or not opt2_exp or actual is None
                    else round(actual / opt2_exp, 4)
                ),
                "opt3_enabled": opt3_on,
                "opt3_max_age_years": max_age,
                "opt3_age_source": opt3_age_source,
                "share_age_le_10": None if share_le_10 is None else round(share_le_10, 4),
                "expected_qty_opt3": None if opt3_exp is None else round(opt3_exp, 2),
                "capture_rate_opt3": (
                    None
                    if opt3_exp is None or not opt3_exp or actual is None
                    else round(actual / opt3_exp, 4)
                ),
                "actual_qty": actual,
                "svc_per_year_lcv": round(svc_lcv, 4),
                "cohort_intensity": intensity,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(DERIVED / "pms_v2_lcv_opt_skeleton.csv", index=False)
    return out


def build_opt1_sensitivity(
    mileage: pd.DataFrame,
    skeleton: pd.DataFrame,
) -> pd.DataFrame:
    """Opt1 low/mid/high km bands (±20% around DB km). Mid = current Opt1.

    Also records network P25/mean/P75 of EU LCV mileage for context (not used as mid).
    """
    rows = []
    net_p25 = net_mean = net_p75 = None
    if not mileage.empty and "annual_km_yr" in mileage.columns:
        net_p25 = float(mileage["annual_km_yr"].quantile(0.25))
        net_mean = float(mileage["annual_km_yr"].mean())
        net_p75 = float(mileage["annual_km_yr"].quantile(0.75))
    mile_map = mileage.set_index("distributor_code") if not mileage.empty else pd.DataFrame()

    for _, r in skeleton.iterrows():
        code = r["distributor_code"]
        mid_exp = r.get("expected_qty_opt1")
        actual = r.get("actual_qty")
        if pd.isna(mid_exp):
            continue
        mid_exp_f = float(mid_exp)
        km_mid = None
        if code in mile_map.index:
            km_mid = float(mile_map.loc[code, "annual_km_yr"])
        # ±20% km → ±20% Opt1 expected (LCV intensity scales linearly with km)
        low_exp = mid_exp_f * 0.8
        high_exp = mid_exp_f * 1.2
        act = None if pd.isna(actual) else float(actual)

        def _cap(exp: float) -> float | None:
            if act is None or exp <= 0:
                return None
            return round(act / exp, 4)

        rows.append(
            {
                "year": 2025,
                "distributor_code": code,
                "pms_category": "oil_filter",
                "line_type": "total",
                "sensitivity_method": "db_annual_km_pm20pct",
                "km_mid": None if km_mid is None else round(km_mid, 1),
                "km_low": None if km_mid is None else round(km_mid * 0.8, 1),
                "km_high": None if km_mid is None else round(km_mid * 1.2, 1),
                "network_km_p25": None if net_p25 is None else round(net_p25, 1),
                "network_km_mean": None if net_mean is None else round(net_mean, 1),
                "network_km_p75": None if net_p75 is None else round(net_p75, 1),
                "expected_qty_opt1_mid": round(mid_exp_f, 2),
                "expected_qty_opt1_low": round(low_exp, 2),
                "expected_qty_opt1_high": round(high_exp, 2),
                "capture_rate_opt1_mid": _cap(mid_exp_f),
                "capture_rate_opt1_low": _cap(low_exp),
                "capture_rate_opt1_high": _cap(high_exp),
                "actual_qty": act,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(DERIVED / "pms_v2_lcv_opt1_sensitivity.csv", index=False)
    return out


def main() -> int:
    DERIVED.mkdir(parents=True, exist_ok=True)
    print("V2 shadow: mileage...")
    mileage = build_mileage_map()
    print(f"  {len(mileage)} DBs -> eu_mileage_by_db_lcv.csv")
    print("V2 shadow: cohorts...")
    cohorts = build_cohort_weights()
    print(f"  {len(cohorts)} DBs -> pms_v2_cohort_weights.csv")
    print("V2 shadow: fitment (BVP + EQ-HIT extract overlay)...")
    fit = build_fitment_weights()
    n_eq = int((fit["eq_hit_status"] == "extract_backed").sum()) if "eq_hit_status" in fit.columns else 0
    print(f"  {len(fit)} category x bucket rows ({n_eq} extract-backed) -> pms_v2_fitment_weights.csv")
    print("V2 shadow: PMS capture Opt1...")
    pms_v2 = build_pms_v2_capture(mileage, cohorts, fit)
    print(f"  {len(pms_v2)} rows -> pms_capture_by_db_year_v2_mileage.csv")
    print("V2 shadow: EQ-HIT category gap analysis...")
    eqhit_gaps = build_eqhit_category_gap_analysis(pms_v2, fit)
    print(f"  {len(eqhit_gaps)} extract categories -> pms_v2_eqhit_category_gap_cy2025.csv")
    print("V2 shadow: GPS wallet...")
    gps_v2 = build_gps_wallet_v2(pms_v2)
    print(f"  {len(gps_v2)} rows -> gps_wallet_v2_by_distributor.csv")
    print("V2 shadow: UIO accuracy ranks...")
    buckets = load_uio_by_bucket()
    accuracy = build_uio_accuracy(buckets)
    print(f"  {len(accuracy)} DBs -> lcv_uio_accuracy_by_db.csv")
    print("V2 shadow: Opt1/2/3 LCV skeleton...")
    skeleton = build_lcv_opt_skeleton(mileage, cohorts, accuracy, pms_v2)
    print(f"  {len(skeleton)} LCV DBs -> pms_v2_lcv_opt_skeleton.csv")
    print("V2 shadow: Opt1 sensitivity ±20% km...")
    sens = build_opt1_sensitivity(mileage, skeleton)
    print(f"  {len(sens)} DBs -> pms_v2_lcv_opt1_sensitivity.csv")
    findings = write_findings(
        mileage,
        cohorts,
        pms_v2,
        gps_v2,
        skeleton=skeleton,
        sensitivity=sens,
        fit=fit,
        eqhit_gaps=eqhit_gaps,
    )
    print(f"  findings -> {findings}")
    print("DONE - V1 files untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
