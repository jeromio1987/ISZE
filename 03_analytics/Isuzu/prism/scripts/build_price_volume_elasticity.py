#!/usr/bin/env python3
"""
Price-volume elasticity from natural experiments (IE40 list changes, FX).

For each PN x distributor with qty >= min in two consecutive years:
    dlnQ = ln(qty_t / qty_t-1),  dlnP = ln(price_t / price_t-1)
Pooled per category, qty-weighted least squares:  dlnQ = alpha + beta * dlnP
beta = arc elasticity estimate for the category.

HONEST LIMITS (also written into the output):
- annual prices, 23 distributors, 2 YoY transitions -> LOW statistical power;
  read beta as direction + rough magnitude, never as a precise elasticity
- avg realized price (net_sales_value / billed_qty) confounds mix & discounts
- demand shocks (supply gaps, campaigns) are not controlled
Categories below `min_pairs_per_category` are flagged low_power.

Output: Data/derived/price_volume_elasticity.csv
Run from prism/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    AIM_PN_CLASSIFICATION_CSV,
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    resolve_mapping_path,
)
from modules.data_prep import EXCLUDED_CODES, load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_CSV = DERIVED_DIR / "price_volume_elasticity.csv"
ASSUMPTIONS = PRISM_ROOT / "data" / "decision_model_assumptions.yaml"


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def _wls_beta(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[float, float, float]:
    """Weighted least squares y = a + b x. Returns (beta, se_beta, r2)."""
    W = np.sqrt(w)
    X = np.column_stack([np.ones_like(x), x]) * W[:, None]
    Y = y * W
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ coef
    dof = max(len(x) - 2, 1)
    sigma2 = float(resid @ resid) / dof
    XtX_inv = np.linalg.inv(X.T @ X)
    se_b = float(np.sqrt(sigma2 * XtX_inv[1, 1]))
    ss_tot = float(((Y - Y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else 0.0
    return float(coef[1]), se_b, r2


def main() -> int:
    cfg = yaml.safe_load(ASSUMPTIONS.read_text(encoding="utf-8"))["elasticity"]
    min_qty = int(cfg["min_qty_both_years"])
    min_pairs = int(cfg["min_pairs_per_category"])
    wins = float(cfg["winsorize_pct"])

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df, src = load_prism_sales(df_map)
    print(f"elasticity: {len(df):,} rows from {src}")
    df = df[~df["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    if "line_kind" in df.columns:
        df = df[df["line_kind"] == "part"]

    agg = (
        df.groupby(["part_number", "distributor_code", "year"])
        .agg(qty=("billed_qty", "sum"), rev=("net_sales_value", "sum"))
        .reset_index()
    )
    agg = agg[(agg["qty"] >= min_qty) & (agg["rev"] > 0)]
    agg["price"] = agg["rev"] / agg["qty"]

    nxt = agg.copy()
    nxt["year"] -= 1
    pairs = agg.merge(
        nxt,
        on=["part_number", "distributor_code", "year"],
        suffixes=("_t0", "_t1"),
    )
    pairs = pairs[(pairs["price_t0"] > 0) & (pairs["price_t1"] > 0)]
    pairs["dlnq"] = np.log(pairs["qty_t1"] / pairs["qty_t0"])
    pairs["dlnp"] = np.log(pairs["price_t1"] / pairs["price_t0"])

    for col in ("dlnq", "dlnp"):
        lo, hi = pairs[col].quantile([wins, 1 - wins])
        pairs[col] = pairs[col].clip(lo, hi)

    # category tags: PMS category (crossref) first, AIM L1 fallback
    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    cat_map: dict[str, str] = {}
    for col in ("genuine_pn", "bvp_pn"):
        sub = xref.dropna(subset=[col, "pms_category"])
        cat_map.update(dict(zip(_norm(sub[col]), sub["pms_category"])))
    aim = pd.read_csv(AIM_PN_CLASSIFICATION_CSV, usecols=["part_number", "aim_l1"], dtype=str)
    aim_map = dict(zip(_norm(aim["part_number"]), aim["aim_l1"]))

    pairs["_pn"] = _norm(pairs["part_number"])
    pairs["category"] = pairs["_pn"].map(cat_map)
    pairs.loc[pairs["category"].isna(), "category"] = (
        "AIM: " + pairs.loc[pairs["category"].isna(), "_pn"].map(aim_map).fillna("Unclassified")
    )
    print(f"elasticity: {len(pairs):,} YoY pairs across {pairs['category'].nunique()} categories")

    rows = []
    for cat, grp in pairs.groupby("category"):
        n = len(grp)
        if n < 5 or grp["dlnp"].std() == 0:
            continue
        beta, se, r2 = _wls_beta(
            grp["dlnp"].to_numpy(), grp["dlnq"].to_numpy(), grp["qty_t0"].to_numpy()
        )
        rows.append(
            {
                "category": cat,
                "n_pairs": n,
                "n_pns": grp["part_number"].nunique(),
                "median_dlnp_pct": round(float(grp["dlnp"].median()) * 100, 2),
                "beta_elasticity": round(beta, 2),
                "se_beta": round(se, 2),
                "r2": round(r2, 3),
                "low_power": n < min_pairs,
                "reading": (
                    "price-sensitive (contestable)" if beta < -0.5
                    else "weak response" if beta < 0
                    else "no negative price response (captive or confounded)"
                ),
                "method_note": (
                    "qty-weighted WLS on YoY log deltas 2023-2025; annual data, "
                    "LOW POWER — direction + rough magnitude only; realized avg "
                    "price confounds mix/discounts; demand shocks uncontrolled"
                ),
            }
        )

    out = pd.DataFrame(rows).sort_values("beta_elasticity")
    out.to_csv(OUT_CSV, index=False)
    strong = out[(~out["low_power"]) & (out["beta_elasticity"] < -0.5)]
    print(f"elasticity: {len(out)} categories -> {OUT_CSV.name}")
    for _, r in out[~out["low_power"]].head(6).iterrows():
        print(
            f"  {r['category']}: beta={r['beta_elasticity']} (se {r['se_beta']}, "
            f"n={r['n_pairs']}) -> {r['reading']}"
        )
    print(f"  categories flagged price-sensitive (adequate n): {len(strong)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
