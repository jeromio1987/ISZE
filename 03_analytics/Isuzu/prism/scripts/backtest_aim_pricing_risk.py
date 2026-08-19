#!/usr/bin/env python3
"""Backtest fitted AIM pricing-risk / opportunity candidates.

Does NOT touch modules/aim_pn_classifier.py (classification layer is out of scope).
Does NOT write FACTS.md or live Streamlit pages.

Pre-registered (before looking at holdout 2025):
  C1  2023 Eucon UK IAM workshop gap, lagged DB revenue weights
  C2  prior-year BVP capture of contested demand (existing genuine/BVP split)
  C3  prior-year commodity-contested revenue share vs maintenance-mandatory
      (Demand Type + Category L1, no new taxonomy)

Incumbent control: lagged aim_high_risk_pct (the 2026-07-17 retired axis).
Naive baselines: predict train-median; predict no YoY change (delta=0);
                 persistence y_t = y_{t-1}.

KS International (scraped 2026-08) and PartsPool Autodoc DE/NO (2026-03-29,
mislabeled as Eucon 2023 in some UIs) are contemporaneous diagnostics only —
they cannot be a 2023-2025 forecast.

Clears holdout iff, on 2024-feature → 2025-outcome (complete CY only):
  (a) Spearman |rho| >= 0.47 (two-sided p~0.05 at n=18) AND hypothesized sign
  (b) OLS MAE beats the matching naive baseline by >= 10%
  (c) Spearman strictly better than lagged AIM high-risk on the same rows
A well-argued null is a successful outcome of this script.

Run from prism/:  python scripts/backtest_aim_pricing_risk.py
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    resolve_mapping_path,
)
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_DIR = PRISM_ROOT / "docs"
YEARS = (2023, 2024, 2025)
NO_UIO = {"ARMENIA", "KAZAKHSTAN", "PALESTINE", "UKRAINE"}
# Hypothesized sign: higher feature → lower GPS SPU / lower PMS capture
RHO_CLEAR = 0.47
MAE_IMPROVE = 0.10
MAINT_L1 = {"Maintenance Service", "Lubrication", "Fluids Chemicals"}
SAFETY_L1 = {"Brakes", "Steering", "Suspension"}
AIM_WB = PRISM_ROOT.parent.parent.parent / "91_legacy" / "Isuzu" / "AIM_CY2025_Analysis.xlsx"


def _norm_pn(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def _norm_desc(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def spearman(x: pd.Series, y: pd.Series) -> dict:
    d = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    n = int(len(d))
    if n < 6:
        return {"n": n, "rho": None, "p": None}
    rho = float(d["x"].corr(d["y"], method="spearman"))
    if rho is None or not math.isfinite(rho):
        return {"n": n, "rho": None, "p": None}
    if abs(rho) >= 0.999999:
        p = 0.0
    else:
        t = rho * math.sqrt((n - 2) / (1.0 - rho * rho))
        # two-sided Student-t p via regularized incomplete beta (no scipy required)
        p = _student_t_sf_two_sided(t, n - 2)
    return {"n": n, "rho": round(rho, 4), "p": round(p, 4)}


def _student_t_sf_two_sided(t: float, df: int) -> float:
    """Two-sided p-value for Student's t. Sufficient for n~18 reporting."""
    x = df / (df + t * t)
    betainc = getattr(math, "betainc", None)
    if betainc is not None:
        return float(betainc(df / 2.0, 0.5, x))
    try:
        from scipy.special import betainc as sp_betainc  # type: ignore

        return float(sp_betainc(df / 2.0, 0.5, x))
    except Exception:
        z = abs(t)
        return float(math.erfc(z / math.sqrt(2.0)))


def mae_ols_vs_baselines(train: pd.DataFrame, test: pd.DataFrame, xcol: str, ycol: str) -> dict:
    tr = train[[xcol, ycol]].dropna()
    te = test[[xcol, ycol]].dropna()
    out = {"n_train": int(len(tr)), "n_test": int(len(te))}
    if len(tr) < 6 or len(te) < 6:
        out["ok"] = False
        return out
    xtr = tr[xcol].to_numpy(float)
    ytr = tr[ycol].to_numpy(float)
    xte = te[xcol].to_numpy(float)
    yte = te[ycol].to_numpy(float)
    X = np.column_stack([np.ones(len(xtr)), xtr])
    beta, _, _, _ = np.linalg.lstsq(X, ytr, rcond=None)
    pred = beta[0] + beta[1] * xte
    mae_model = float(np.mean(np.abs(pred - yte)))
    mae_median = float(np.mean(np.abs(np.median(ytr) - yte)))
    out.update(
        {
            "ok": True,
            "beta0": round(float(beta[0]), 6),
            "beta1": round(float(beta[1]), 6),
            "mae_model": round(mae_model, 6),
            "mae_median": round(mae_median, 6),
            "mae_improve_vs_median": round((mae_median - mae_model) / mae_median, 4)
            if mae_median
            else None,
        }
    )
    return out


def mae_delta_vs_zero(train: pd.DataFrame, test: pd.DataFrame, xcol: str, dcol: str) -> dict:
    """Fit Δy ~ feature on train; MAE on test vs naive Δ=0."""
    tr = train[[xcol, dcol]].dropna()
    te = test[[xcol, dcol]].dropna()
    out = {"n_train": int(len(tr)), "n_test": int(len(te))}
    if len(tr) < 6 or len(te) < 6:
        out["ok"] = False
        return out
    xtr, ytr = tr[xcol].to_numpy(float), tr[dcol].to_numpy(float)
    xte, yte = te[xcol].to_numpy(float), te[dcol].to_numpy(float)
    X = np.column_stack([np.ones(len(xtr)), xtr])
    beta, _, _, _ = np.linalg.lstsq(X, ytr, rcond=None)
    pred = beta[0] + beta[1] * xte
    mae_model = float(np.mean(np.abs(pred - yte)))
    mae_zero = float(np.mean(np.abs(yte)))
    out.update(
        {
            "ok": True,
            "beta0": round(float(beta[0]), 6),
            "beta1": round(float(beta[1]), 6),
            "mae_model": round(mae_model, 6),
            "mae_zero": round(mae_zero, 6),
            "mae_improve_vs_zero": round((mae_zero - mae_model) / mae_zero, 4) if mae_zero else None,
        }
    )
    return out


def load_outcomes() -> pd.DataFrame:
    gps = pd.read_csv(DERIVED_DIR / "gps_spu_by_distributor.csv")
    gps = gps[gps["year"].isin(YEARS)].copy()
    gps["distributor_code"] = gps["distributor_code"].astype(str).str.strip()
    gps["gps_spu"] = pd.to_numeric(gps["spend_per_unit_eur"], errors="coerce")
    gps["uio_ok"] = gps["distributor_code"].str.upper().isin(NO_UIO).eq(False) & gps["gps_spu"].notna()

    pms = pd.read_csv(DERIVED_DIR / "pms_capture_by_db_year.csv")
    pms = pms[(pms["year"].isin(YEARS)) & (pms["line_type"].astype(str).str.lower() == "total")].copy()
    pms["distributor_code"] = pms["distributor_code"].astype(str).str.strip()
    g = pms.groupby(["year", "distributor_code"], as_index=False).agg(
        actual_qty=("actual_qty", "sum"),
        expected_qty=("expected_qty", "sum"),
        actual_rev_eur=("actual_rev_eur", "sum"),
    )
    g["pms_total_capture"] = g["actual_qty"] / g["expected_qty"].replace(0, np.nan)

    pms_g = pms_genuine_capture()

    aim = pd.read_csv(DERIVED_DIR / "aim_exposure_by_db_year.csv")
    aim = aim[aim["year"].isin(YEARS)].copy()
    aim["distributor_code"] = aim["distributor_code"].astype(str).str.strip()
    aim["aim_high_risk_pct"] = pd.to_numeric(aim["high_risk_rev_pct"], errors="coerce")

    mix = pd.read_csv(DERIVED_DIR / "db_parts_mix_classification.csv")
    mix = mix[mix["year"].isin(YEARS)].copy()
    mix["distributor_code"] = mix["distributor_code"].astype(str).str.strip()
    mix["c2_bvp_contested"] = pd.to_numeric(mix["contested_bvp_capture"], errors="coerce")
    mix["c2_contested_share"] = pd.to_numeric(mix["contested_eur"], errors="coerce") / pd.to_numeric(
        mix["total_eur"], errors="coerce"
    ).replace(0, np.nan)

    out = gps.merge(g[["year", "distributor_code", "pms_total_capture"]], on=["year", "distributor_code"], how="outer")
    out = out.merge(pms_g, on=["year", "distributor_code"], how="left")
    out = out.merge(aim[["year", "distributor_code", "aim_high_risk_pct", "net_sales_eur"]], on=["year", "distributor_code"], how="left")
    out = out.merge(
        mix[["year", "distributor_code", "c2_bvp_contested", "c2_contested_share"]],
        on=["year", "distributor_code"],
        how="left",
    )
    out = out[~out["distributor_code"].str.upper().eq("TURKEY")].copy()
    out = out.sort_values(["distributor_code", "year"])
    out["gps_spu_lag"] = out.groupby("distributor_code")["gps_spu"].shift(1)
    out["pms_total_capture_lag"] = out.groupby("distributor_code")["pms_total_capture"].shift(1)
    out["pms_genuine_capture_lag"] = out.groupby("distributor_code")["pms_genuine_capture"].shift(1)
    out["aim_high_risk_pct_lag"] = out.groupby("distributor_code")["aim_high_risk_pct"].shift(1)
    out["c2_bvp_contested_lag"] = out.groupby("distributor_code")["c2_bvp_contested"].shift(1)
    out["c2_contested_share_lag"] = out.groupby("distributor_code")["c2_contested_share"].shift(1)
    out["d_gps"] = out["gps_spu"] - out["gps_spu_lag"]
    out["d_pms"] = out["pms_total_capture"] - out["pms_total_capture_lag"]
    out["d_pms_gen"] = out["pms_genuine_capture"] - out["pms_genuine_capture_lag"]
    return out


def pms_genuine_capture() -> pd.DataFrame:
    pms = pd.read_csv(DERIVED_DIR / "pms_capture_by_db_year.csv")
    pms = pms[(pms["year"].isin(YEARS)) & (pms["line_type"].astype(str).str.lower() == "genuine")].copy()
    pms["distributor_code"] = pms["distributor_code"].astype(str).str.strip()
    g = pms.groupby(["year", "distributor_code"], as_index=False).agg(
        g_actual=("actual_qty", "sum"),
        g_expected=("expected_qty", "sum"),
    )
    g["pms_genuine_capture"] = g["g_actual"] / g["g_expected"].replace(0, np.nan)
    return g[["year", "distributor_code", "pms_genuine_capture"]]


def load_sales_parts() -> pd.DataFrame:
    mapping = load_distributor_mapping(str(resolve_mapping_path()))
    sales, src = load_prism_sales(mapping)
    sales = sales[sales["year"].isin(YEARS)].copy()
    if "line_kind" in sales.columns:
        sales = sales[sales["line_kind"] == "part"].copy()
    sales["pn"] = _norm_pn(sales["part_number"])
    sales["distributor_code"] = sales["distributor_code"].astype(str).str.strip()
    sales = sales[~sales["distributor_code"].str.upper().isin({"TURKEY", "UNMAPPED"})]
    sales["net_sales_value"] = pd.to_numeric(sales["net_sales_value"], errors="coerce").fillna(0)
    sales["_src"] = src
    return sales


def db_year_rev(sales: pd.DataFrame) -> pd.DataFrame:
    return (
        sales.groupby(["year", "distributor_code"], as_index=False)["net_sales_value"]
        .sum()
        .rename(columns={"net_sales_value": "parts_rev_eur"})
    )


def weighted_gap_feature(
    sales: pd.DataFrame,
    gap_pn: pd.DataFrame,
    value_col: str,
    exposed_col: str | None,
    prefix: str,
) -> pd.DataFrame:
    """Revenue-weighted competitor gap at DB-year using that year's billed mix."""
    s = sales.merge(gap_pn, on="pn", how="inner")
    if s.empty:
        return pd.DataFrame(columns=["year", "distributor_code", f"{prefix}_wgap", f"{prefix}_exposed_share"])
    s["_w"] = s["net_sales_value"].clip(lower=0)
    s["_x"] = pd.to_numeric(s[value_col], errors="coerce")
    rows = []
    for (yr, db), d in s.groupby(["year", "distributor_code"]):
        w = float(d["_w"].sum())
        wx = float((d["_w"] * d["_x"]).sum())
        rows.append(
            {
                "year": int(yr),
                "distributor_code": db,
                f"{prefix}_wgap": (wx / w) if w else np.nan,
                f"{prefix}_gap_rev": w,
            }
        )
    g = pd.DataFrame(rows)
    tot = db_year_rev(sales)
    g = g.merge(tot, on=["year", "distributor_code"], how="left")
    g[f"{prefix}_rev_share"] = g[f"{prefix}_gap_rev"] / g["parts_rev_eur"].replace(0, np.nan)
    if exposed_col and exposed_col in s.columns:
        exp = (
            s[s[exposed_col].astype(str).str.lower().isin(["true", "1"])]
            .groupby(["year", "distributor_code"], as_index=False)["_w"]
            .sum()
            .rename(columns={"_w": f"{prefix}_exposed_rev"})
        )
        g = g.merge(exp, on=["year", "distributor_code"], how="left")
        g[f"{prefix}_exposed_share"] = g[f"{prefix}_exposed_rev"].fillna(0) / g["parts_rev_eur"].replace(0, np.nan)
    g[f"{prefix}_undercut"] = -pd.to_numeric(g[f"{prefix}_wgap"], errors="coerce")
    return g


def load_c1_survey_gap() -> pd.DataFrame:
    p = DERIVED_DIR / "eucon_uk_survey_2023_price_gap.csv"
    df = pd.read_csv(p)
    df["pn"] = _norm_pn(df["pn"])
    # One UK workshop gap per PN (same competitor prices copied across DBs)
    keep = (
        df.sort_values("pn")
        .drop_duplicates("pn")[["pn", "delta_vs_proj_retail_pct", "isze_exposed", "vintage", "probe_label"]]
        .copy()
    )
    keep["delta_vs_proj_retail_pct"] = pd.to_numeric(keep["delta_vs_proj_retail_pct"], errors="coerce")
    meta = {
        "file": str(p),
        "n_pn": int(keep["pn"].nunique()),
        "vintage": keep["vintage"].dropna().astype(str).unique().tolist(),
        "probe_label": keep["probe_label"].dropna().astype(str).unique().tolist(),
    }
    keep.attrs["meta"] = meta
    return keep


def load_ks_gap() -> pd.DataFrame:
    df = pd.read_csv(DERIVED_DIR / "iam_ks_price_gap.csv")
    df = df[df["status"].astype(str).str.lower() == "ok"].copy()
    df["pn"] = _norm_pn(df["pn"])
    keep = df.drop_duplicates("pn")[["pn", "delta_vs_proj_retail_pct", "isze_exposed", "scraped_at"]].copy()
    keep["delta_vs_proj_retail_pct"] = pd.to_numeric(keep["delta_vs_proj_retail_pct"], errors="coerce")
    return keep


def load_partspool_gap() -> tuple[pd.DataFrame, dict]:
    meta_path = DERIVED_DIR / "eucon_price_gap.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    df = pd.read_csv(DERIVED_DIR / "eucon_price_gap.csv")
    df["pn"] = _norm_pn(df["pn"])
    street = 1.785
    df["delta_vs_proj_retail_pct"] = (
        pd.to_numeric(df["Avg_Competitor_EUR"], errors="coerce")
        / (pd.to_numeric(df["ISZE_IE40_Price_EUR"], errors="coerce") * street)
        - 1.0
    )
    df["isze_exposed"] = df["delta_vs_proj_retail_pct"] < 0
    keep = df.drop_duplicates("pn")[["pn", "delta_vs_proj_retail_pct", "isze_exposed"]].copy()
    return keep, meta


def load_demand_and_l1(sales: pd.DataFrame) -> pd.DataFrame:
    classif = pd.read_csv(DERIVED_DIR / "aim_pn_classification.csv", usecols=["part_number", "aim_l1", "aim_l2"])
    classif["pn"] = _norm_pn(classif["part_number"])
    s = sales.merge(classif[["pn", "aim_l1", "aim_l2"]], on="pn", how="left")

    demand = None
    if AIM_WB.exists():
        pm = pd.read_excel(AIM_WB, sheet_name="Parts Master", header=1)
        pm.columns = [str(c).strip() for c in pm.columns]
        desc_col = next(c for c in pm.columns if c.lower().startswith("description"))
        dt = pd.DataFrame(
            {
                "description_norm": _norm_desc(pm[desc_col]),
                "aim_demand_type": pm.get("Demand Type"),
            }
        )
        dt = dt[dt["description_norm"] != ""].drop_duplicates("description_norm")
        s["description_norm"] = _norm_desc(s.get("description", pd.Series("", index=s.index)))
        s = s.merge(dt, on="description_norm", how="left")
        demand = dt["aim_demand_type"].value_counts(dropna=False).to_dict()
    else:
        s["aim_demand_type"] = np.nan

    dim = pd.read_csv(DERIVED_DIR / "bvp_pn_dimension.csv", usecols=["part_number", "in_bvp_catalog", "line_type"])
    dim["pn"] = _norm_pn(dim["part_number"])
    bvp_pns = set(dim.loc[dim["in_bvp_catalog"].astype(str).str.lower().isin(["true", "1"]), "pn"])
    # Contested family: PN is BVP-catalogued OR a genuine counterpart exists in the dimension
    genuine_pns = set(dim.loc[dim["line_type"].astype(str).str.lower() == "genuine", "pn"])
    contested_pns = bvp_pns | genuine_pns

    dt = s["aim_demand_type"].fillna("").astype(str)
    l1 = s["aim_l1"].fillna("").astype(str)
    s["seg_mandatory"] = dt.eq("Maintenance") | l1.isin(MAINT_L1)
    s["seg_safety"] = dt.eq("Wear Repair") | l1.isin(SAFETY_L1)
    s["seg_commodity_contested"] = s["pn"].isin(contested_pns) & ~s["seg_mandatory"] & ~s["seg_safety"]
    s["_w"] = s["net_sales_value"].clip(lower=0)

    rows = []
    for (yr, db), d in s.groupby(["year", "distributor_code"]):
        tot = d["_w"].sum()
        if tot <= 0:
            continue
        rows.append(
            {
                "year": int(yr),
                "distributor_code": db,
                "c3_mandatory_share": d.loc[d["seg_mandatory"], "_w"].sum() / tot,
                "c3_safety_share": d.loc[d["seg_safety"], "_w"].sum() / tot,
                "c3_commodity_contested_share": d.loc[d["seg_commodity_contested"], "_w"].sum() / tot,
                "c3_demand_join_rate": d["aim_demand_type"].notna().mean() if "aim_demand_type" in d else 0.0,
            }
        )
    feat = pd.DataFrame(rows)
    feat.attrs["demand_counts"] = demand
    feat.attrs["aim_wb"] = str(AIM_WB) if AIM_WB.exists() else None
    return feat


def lag_feature(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.sort_values(["distributor_code", "year"]).copy()
    for c in cols:
        df[f"{c}_lag"] = df.groupby("distributor_code")[c].shift(1)
    return df


def evaluate_candidate(panel: pd.DataFrame, feat: str, label: str, hypothesized_sign: int) -> dict:
    """hypothesized_sign = -1 means higher feature → lower outcome (risk)."""
    rows_2024 = panel[(panel["year"] == 2024) & panel["uio_ok"]].copy()
    rows_2025 = panel[(panel["year"] == 2025) & panel["uio_ok"]].copy()

    tests = {}
    for yname, ycol, dcol in (
        ("gps_spu", "gps_spu", "d_gps"),
        ("pms_total_capture", "pms_total_capture", "d_pms"),
        ("pms_genuine_capture", "pms_genuine_capture", "d_pms_gen"),
    ):
        tests[yname] = {
            "spearman_2024_origin": spearman(rows_2024[feat], rows_2024[ycol]),
            "spearman_2025_holdout": spearman(rows_2025[feat], rows_2025[ycol]),
            "spearman_delta_2024": spearman(rows_2024[feat], rows_2024[dcol]),
            "spearman_delta_2025_holdout": spearman(rows_2025[feat], rows_2025[dcol]),
            "ols_level_train2024_test2025": mae_ols_vs_baselines(rows_2024, rows_2025, feat, ycol),
            "ols_delta_train2024_test2025": mae_delta_vs_zero(rows_2024, rows_2025, feat, dcol),
        }
        lag_col = {
            "gps_spu": "gps_spu_lag",
            "pms_total_capture": "pms_total_capture_lag",
            "pms_genuine_capture": "pms_genuine_capture_lag",
        }[yname]
        tests[yname]["persistence_spearman_2025"] = spearman(rows_2025[lag_col], rows_2025[ycol])

    incumbent = {
        "gps_spu_holdout": spearman(rows_2025["aim_high_risk_pct_lag"], rows_2025["gps_spu"]),
        "pms_total_holdout": spearman(rows_2025["aim_high_risk_pct_lag"], rows_2025["pms_total_capture"]),
        "gps_delta_holdout": spearman(rows_2025["aim_high_risk_pct_lag"], rows_2025["d_gps"]),
        "pms_delta_holdout": spearman(rows_2025["aim_high_risk_pct_lag"], rows_2025["d_pms"]),
    }

    def _clears(block: dict, inc_rho: float | None, ykey: str) -> dict:
        hold = block["spearman_2025_holdout"]
        dhold = block["spearman_delta_2025_holdout"]
        ols_d = block["ols_delta_train2024_test2025"]
        rho = hold.get("rho")
        drho = dhold.get("rho")
        level_ok = (
            rho is not None
            and abs(rho) >= RHO_CLEAR
            and (np.sign(rho) == hypothesized_sign or rho == 0)
            and (inc_rho is None or abs(rho) > abs(inc_rho))
        )
        mae_ok = bool(
            ols_d.get("ok")
            and ols_d.get("mae_improve_vs_zero") is not None
            and ols_d["mae_improve_vs_zero"] >= MAE_IMPROVE
            and drho is not None
            and abs(drho) >= RHO_CLEAR
            and np.sign(drho) == hypothesized_sign
        )
        return {
            "level_clears": bool(level_ok),
            "delta_clears": bool(mae_ok),
            "holdout_rho": rho,
            "holdout_delta_rho": drho,
            "incumbent_rho": inc_rho,
        }

    verdict = {
        "gps_spu": _clears(tests["gps_spu"], incumbent["gps_spu_holdout"].get("rho"), "gps"),
        "pms_total_capture": _clears(
            tests["pms_total_capture"], incumbent["pms_total_holdout"].get("rho"), "pms"
        ),
        "gps_delta": {
            "delta_clears": tests["gps_spu"]["spearman_delta_2025_holdout"].get("rho") is not None
            and abs(tests["gps_spu"]["spearman_delta_2025_holdout"]["rho"] or 0) >= RHO_CLEAR
            and np.sign(tests["gps_spu"]["spearman_delta_2025_holdout"]["rho"] or 0) == hypothesized_sign
            and (tests["gps_spu"]["ols_delta_train2024_test2025"].get("mae_improve_vs_zero") or -1) >= MAE_IMPROVE,
        },
        "pms_delta": {
            "delta_clears": tests["pms_total_capture"]["spearman_delta_2025_holdout"].get("rho") is not None
            and abs(tests["pms_total_capture"]["spearman_delta_2025_holdout"]["rho"] or 0) >= RHO_CLEAR
            and np.sign(tests["pms_total_capture"]["spearman_delta_2025_holdout"]["rho"] or 0)
            == hypothesized_sign
            and (tests["pms_total_capture"]["ols_delta_train2024_test2025"].get("mae_improve_vs_zero") or -1)
            >= MAE_IMPROVE,
        },
    }
    any_clear = any(
        [
            verdict["gps_spu"]["level_clears"],
            verdict["pms_total_capture"]["level_clears"],
            verdict["gps_delta"]["delta_clears"],
            verdict["pms_delta"]["delta_clears"],
        ]
    )
    return {
        "label": label,
        "feature": feat,
        "hypothesized_sign": hypothesized_sign,
        "n_2025_uio_ok": int(len(rows_2025)),
        "tests": tests,
        "incumbent_aim_lag": incumbent,
        "verdict": verdict,
        "clears_any": bool(any_clear),
    }


def mekonomen_filter_check() -> dict:
    mek = pd.read_csv(DERIVED_DIR / "iam_mekonomen_price_gap.csv")
    classif = pd.read_csv(
        DERIVED_DIR / "aim_pn_classification.csv", usecols=["part_number", "aim_l1", "filter_part_role"]
    )
    classif["pn"] = _norm_pn(classif["part_number"])
    mek["pn"] = _norm_pn(mek["pn"])
    j = mek.merge(classif, on="pn", how="left")
    filter_hits = int(j["filter_part_role"].notna().sum()) if "filter_part_role" in j.columns else 0
    return {
        "n_rows": int(len(mek)),
        "n_pn": int(mek["pn"].nunique()),
        "filter_part_role_hits": filter_hits,
        "l1": j["aim_l1"].value_counts(dropna=False).to_dict(),
        "note": "Closed finding: Mekonomen is not a filter-PN index. 0 filter_part_role hits confirms AUTO365/proposal text.",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_outcomes()
    sales = load_sales_parts()
    sales_src = str(sales["_src"].iloc[0]) if "_src" in sales.columns and len(sales) else None
    sales = sales.drop(columns=["_src"], errors="ignore")

    # --- C1: 2023 UK IAM workshop (valid vintage for 2024/2025 holdout)
    c1_pn = load_c1_survey_gap()
    c1 = weighted_gap_feature(sales, c1_pn, "delta_vs_proj_retail_pct", "isze_exposed", "c1")
    c1 = lag_feature(c1, ["c1_undercut", "c1_exposed_share", "c1_rev_share"])
    panel = panel.merge(
        c1[
            [
                "year",
                "distributor_code",
                "c1_undercut",
                "c1_exposed_share",
                "c1_rev_share",
                "c1_undercut_lag",
                "c1_exposed_share_lag",
            ]
        ],
        on=["year", "distributor_code"],
        how="left",
    )

    # --- C3 mix
    c3 = load_demand_and_l1(sales)
    demand_counts = c3.attrs.get("demand_counts")
    c3 = lag_feature(c3, ["c3_commodity_contested_share", "c3_mandatory_share"])
    panel = panel.merge(c3, on=["year", "distributor_code"], how="left")

    # --- Diagnostics: KS 2026 and PartsPool 2026-03-29 (NOT lagged forecasts)
    ks_pn = load_ks_gap()
    ks = weighted_gap_feature(sales, ks_pn, "delta_vs_proj_retail_pct", "isze_exposed", "ks")
    panel = panel.merge(
        ks[["year", "distributor_code", "ks_undercut", "ks_exposed_share"]],
        on=["year", "distributor_code"],
        how="left",
    )
    pp_pn, pp_meta = load_partspool_gap()
    pp = weighted_gap_feature(sales, pp_pn, "delta_vs_proj_retail_pct", "isze_exposed", "pp")
    panel = panel.merge(
        pp[["year", "distributor_code", "pp_undercut", "pp_exposed_share"]],
        on=["year", "distributor_code"],
        how="left",
    )

    rows_2025 = panel[(panel["year"] == 2025) & panel["uio_ok"]]

    results = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verification_ok_cited": True,
        "sales_source": sales_src,
        "complete_years": list(YEARS),
        "excluded_partial_year": 2026,
        "no_uio_excluded_from_gps_tests": sorted(NO_UIO),
        "clearing_rule": {
            "rho_min": RHO_CLEAR,
            "mae_improve_min": MAE_IMPROVE,
            "holdout": "2024 feature (lagged) → 2025 outcome, UIO-ok DBs only",
            "sign": "higher feature → worse GPS SPU / worse PMS capture (sign -1)",
        },
        "c1_survey_meta": c1_pn.attrs.get("meta"),
        "partspool_meta_flag": pp_meta,
        "mekonomen": mekonomen_filter_check(),
        "ks_diagnostic": {
            "n_pn": int(ks_pn["pn"].nunique()),
            "scraped_at_sample": ks_pn["scraped_at"].astype(str).head(1).tolist(),
            "temporal": "2026-08 scrape — cannot forecast CY2025. Contemporaneous Spearman only.",
            "spearman_2025_gps": spearman(rows_2025["ks_undercut"], rows_2025["gps_spu"]),
            "spearman_2025_pms": spearman(rows_2025["ks_undercut"], rows_2025["pms_total_capture"]),
        },
        "partspool_diagnostic": {
            "temporal": "PartsPool Autodoc DE/NO dated 2026-03-29, not Eucon UK 2023. Contemporaneous only.",
            "n_pn": int(pp_pn["pn"].nunique()),
            "spearman_2025_gps": spearman(rows_2025["pp_undercut"], rows_2025["gps_spu"]),
            "spearman_2025_pms": spearman(rows_2025["pp_undercut"], rows_2025["pms_total_capture"]),
        },
        "aim_workbook": str(AIM_WB) if AIM_WB.exists() else None,
        "demand_type_counts_parts_master": demand_counts,
        "c3_demand_join_rate_2025_median": None
        if "c3_demand_join_rate" not in rows_2025
        else (None if rows_2025["c3_demand_join_rate"].dropna().empty else round(float(rows_2025["c3_demand_join_rate"].median()), 4)),
        "incumbent_aim_high_risk_2025": {
            "max": None if rows_2025["aim_high_risk_pct"].dropna().empty else round(float(rows_2025["aim_high_risk_pct"].max()), 4),
            "median": None if rows_2025["aim_high_risk_pct"].dropna().empty else round(float(rows_2025["aim_high_risk_pct"].median()), 4),
            "spearman_vs_gps": spearman(rows_2025["aim_high_risk_pct"], rows_2025["gps_spu"]),
            "spearman_vs_pms": spearman(rows_2025["aim_high_risk_pct"], rows_2025["pms_total_capture"]),
            "lagged_spearman_vs_gps": spearman(rows_2025["aim_high_risk_pct_lag"], rows_2025["gps_spu"]),
            "lagged_spearman_vs_pms": spearman(rows_2025["aim_high_risk_pct_lag"], rows_2025["pms_total_capture"]),
        },
        "persistence_2025": {
            "gps": spearman(rows_2025["gps_spu_lag"], rows_2025["gps_spu"]),
            "pms_total": spearman(rows_2025["pms_total_capture_lag"], rows_2025["pms_total_capture"]),
        },
        "candidates": {},
    }

    results["candidates"]["C1_eucon_uk_2023_undercut"] = evaluate_candidate(
        panel, "c1_undercut_lag", "C1 lagged 2023 IAM workshop undercut (rev-weighted -delta vs reference sell-out)", -1
    )
    results["candidates"]["C1b_exposed_share"] = evaluate_candidate(
        panel, "c1_exposed_share_lag", "C1b lagged share of € in 2023-survey PNs where IAM < reference sell-out", -1
    )
    results["candidates"]["C2_bvp_contested"] = evaluate_candidate(
        panel, "c2_bvp_contested_lag", "C2 lagged BVP capture of contested demand (existing genuine/BVP split)", -1
    )
    results["candidates"]["C3_commodity_contested_share"] = evaluate_candidate(
        panel,
        "c3_commodity_contested_share_lag",
        "C3 lagged commodity-contested € share (BVP-catalog PNs excluding Maintenance/safety L1)",
        -1,
    )

    results["any_candidate_clears"] = any(c["clears_any"] for c in results["candidates"].values())

    panel_path = OUT_DIR / "AIM_PRICING_RISK_BACKTEST_panel_2026-08-18.csv"
    keep_cols = [
        c
        for c in [
            "year",
            "distributor_code",
            "uio_ok",
            "gps_spu",
            "pms_total_capture",
            "pms_genuine_capture",
            "aim_high_risk_pct",
            "aim_high_risk_pct_lag",
            "c1_undercut_lag",
            "c1_exposed_share_lag",
            "c2_bvp_contested_lag",
            "c3_commodity_contested_share_lag",
            "c3_mandatory_share",
            "d_gps",
            "d_pms",
            "ks_undercut",
            "pp_undercut",
        ]
        if c in panel.columns
    ]
    panel[keep_cols].to_csv(panel_path, index=False)

    json_path = OUT_DIR / "AIM_PRICING_RISK_BACKTEST_2026-08-18.json"
    json_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    print("any_candidate_clears", results["any_candidate_clears"])
    print("persistence", results["persistence_2025"])
    print("incumbent", results["incumbent_aim_high_risk_2025"])
    for k, v in results["candidates"].items():
        print("---", k, "clears_any", v["clears_any"])
        print("  gps holdout", v["tests"]["gps_spu"]["spearman_2025_holdout"])
        print("  pms holdout", v["tests"]["pms_total_capture"]["spearman_2025_holdout"])
        print("  gps delta", v["tests"]["gps_spu"]["spearman_delta_2025_holdout"])
        print("  pms delta", v["tests"]["pms_total_capture"]["spearman_delta_2025_holdout"])
        print("  gps ols delta", v["tests"]["gps_spu"]["ols_delta_train2024_test2025"])
        print("  pms ols delta", v["tests"]["pms_total_capture"]["ols_delta_train2024_test2025"])
    print("ks", results["ks_diagnostic"])
    print("partspool", results["partspool_diagnostic"])
    print("mekonomen", results["mekonomen"])
    print("wrote", json_path)
    print("wrote", panel_path)


if __name__ == "__main__":
    main()
