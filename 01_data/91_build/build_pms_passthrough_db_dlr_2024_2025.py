#!/usr/bin/env python3
"""
PMS pass-through / volume response: ISZE→DB price move 2024→2025 vs sales-to-dealer qty.

Honest scope (internal):
  - Volume = distributor sales to dealer qty (never claim dealer invoice price).
  - Price axis = upstream ISZE→DB median ASP and/or PR00 IE40 list.
    Dealer-facing invoice price is absent → PRICE pass-through is BLOCKED;
    VOLUME response vs upstream price is still useful where ≥2 CY exist.
  - Do NOT quote price_volume_elasticity.csv (that is ISZE→DB stocking).
  - UTI ≠ UMI; IUK ≠ ITUK ≠ IRELAND.

New dated outputs only (does not overwrite price_elasticity_db_dlr_*):
  01_data/00_derived/pms_passthrough_db_dlr_2024_2025.csv
  01_data/00_derived/pms_passthrough_coverage_inventory_2026-09-22.csv
  01_data/90_INBOX/PMS_PASSTHROUGH_DB_TO_DEALER_2024_2025.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ISZE_ROOT = Path(__file__).resolve().parents[2]
PRISM = ISZE_ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))

from config import (  # noqa: E402
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import load_uti_part_sales, normalize_pn  # noqa: E402

OUT_CSV = DERIVED_DIR / "pms_passthrough_db_dlr_2024_2025.csv"
OUT_INV = DERIVED_DIR / "pms_passthrough_coverage_inventory_2026-09-22.csv"
OUT_MD = ISZE_ROOT / "01_data" / "90_INBOX" / "PMS_PASSTHROUGH_DB_TO_DEALER_2024_2025.md"

MIN_QTY = 5
MIN_PNS_CAT = 5
MIN_PNS_ADEQUATE = 12
MIN_ABS_DLNP = 0.005  # ~0.5% — below this, price barely moved; β unstable
MIN_PRICE_MOVERS = 3  # PNs with |dlnp| >= MIN_ABS_DLNP needed for a β row
WINSOR = 0.02
Y0, Y1 = 2024, 2025

# Long CSVs under 00_derived — preferred path for inventory + YoY.
SELLOUT_SPECS: list[dict] = [
    {
        "distributor_code": "ITUK",
        "note": "ITUK_not_IUK",
        "files": {
            2023: "dealer_sellout_long_ITUK_CY2023.csv",
            2024: "dealer_sellout_long_ITUK_CY2024.csv",
            2025: "dealer_sellout_long_ITUK_network_CY2025.csv",  # network grain = CY2024
            2026: "dealer_sellout_long_ITUK_CY2026YTD.csv",
        },
        "prefer_grain": "network_pn",
        "yoy_pair": (2024, 2025),
    },
    {
        "distributor_code": "UTI",
        "note": "UTI_only_not_UMI",
        "files": {
            2025: "dealer_sellout_long_UTI_CY2025.csv",
            2026: "dealer_sellout_long_UTI_CY2026YTD.csv",
        },
        "prefer_grain": "network_pn",
        "yoy_pair": None,  # misnamed CY2024 xlsx is Jan-2025
        "uti_verify": True,
    },
    {
        "distributor_code": "IUK",
        "note": "IUK_not_ITUK_not_IRELAND",
        "files": {
            2025: "dealer_sellout_long_IUK_CY2025.csv",
            2026: "dealer_sellout_long_IUK_CY2026YTD.csv",
        },
        "prefer_grain": "network_pn",
        "yoy_pair": None,
    },
    {
        "distributor_code": "IRELAND",
        "note": "IRELAND_not_IUK_not_ITUK",
        "files": {
            2025: "dealer_sellout_long_IRELAND_CY2025.csv",
            2026: "dealer_sellout_long_IRELAND_CY2026YTD.csv",
        },
        "prefer_grain": "network_pn",
        "yoy_pair": None,
    },
    {
        "distributor_code": "GREECE",
        "note": "GREECE_Petros_network_pn",
        "files": {2025: "dealer_sellout_long_GREECE_CY2025.csv"},
        "prefer_grain": "network_pn",
        "yoy_pair": None,
    },
    {
        "distributor_code": "PORTUGAL",
        "note": "PORTUGAL_network_pn",
        "files": {
            2025: "dealer_sellout_long_PORTUGAL_CY2025.csv",
            2026: "dealer_sellout_long_PORTUGAL_CY2026YTD.csv",
        },
        "prefer_grain": "network_pn",
        "yoy_pair": None,
    },
    {
        "distributor_code": "ROMANIA",
        "note": "ROMANIA_partial_only",
        "files": {2026: "dealer_sellout_long_ROMANIA_CY2026YTD.csv"},
        "prefer_grain": "network_pn",
        "yoy_pair": None,
    },
]


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def _wls_beta(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[float, float, float]:
    W = np.sqrt(np.clip(w, 1e-12, None))
    X = np.column_stack([np.ones_like(x), x]) * W[:, None]
    Y = y * W
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ coef
    dof = max(len(x) - 2, 1)
    sigma2 = float(resid @ resid) / dof
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
        se_b = float(np.sqrt(sigma2 * XtX_inv[1, 1]))
    except np.linalg.LinAlgError:
        se_b = float("nan")
    ss_tot = float(((Y - Y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else 0.0
    return float(coef[1]), se_b, r2


def pms_category_map() -> dict[str, str]:
    """PN → PMS service family only (genuine_bvp_crossref.pms_category)."""
    xref = pd.read_csv(
        GENUINE_BVP_CROSSREF_CSV,
        dtype={"genuine_pn": str, "bvp_pn": str, "pms_category": str},
    )
    cat_map: dict[str, str] = {}
    for col in ("genuine_pn", "bvp_pn"):
        if col not in xref.columns or "pms_category" not in xref.columns:
            continue
        sub = xref.dropna(subset=[col, "pms_category"])
        sub = sub[sub["pms_category"].astype(str).str.strip() != ""]
        cat_map.update(dict(zip(_norm(sub[col]), sub["pms_category"].astype(str))))
    return cat_map


def load_year_qty(path: Path, prefer_grain: str | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["part_number", "qty", "source_file", "grain", "flags"])
    df = pd.read_csv(path, dtype={"part_number": str, "part_number_raw": str})
    if "period_grain" in df.columns:
        year_rows = df[df["period_grain"].astype(str) == "year"].copy()
        if year_rows.empty:
            # monthly-only / ytd: sum months (do NOT group by flags — all-NaN keys drop rows)
            m = df[df["period_grain"].astype(str).isin(["month", "ytd"])].copy()
            if m.empty:
                year_rows = df.copy()
            else:
                year_rows = m.groupby("part_number", as_index=False).agg(
                    qty=("qty", "sum"),
                    **{
                        c: (c, "first")
                        for c in ("source_file", "grain")
                        if c in m.columns
                    },
                )
        df = year_rows
    df["part_number"] = df["part_number"].map(normalize_pn)
    df = df.dropna(subset=["part_number"])
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0.0)
    if prefer_grain and "grain" in df.columns:
        g = df[df["grain"].astype(str) == prefer_grain]
        if not g.empty:
            df = g
    # Always collapse to one row per PN (dealer_pn → network sum)
    agg: dict = {"qty": ("qty", "sum")}
    for c in ("source_file", "grain"):
        if c in df.columns:
            agg[c] = (c, "first")
    # Column named flags collides with DataFrame.flags — only keep if present, never groupby on it
    if "flags" in df.columns:
        agg["row_flags"] = ("flags", "first")
    df = df.groupby("part_number", as_index=False).agg(**agg)
    if "grain" in df.columns and (df["grain"].astype(str) == "dealer_pn").any():
        df["grain"] = "network_pn_summed"
    df = df[df["qty"] > 0]
    if "row_flags" in df.columns:
        df["qty_only"] = df["row_flags"].astype(str).str.contains("qty_only", na=False)
    else:
        df["qty_only"] = True  # no dealer price columns in long CSVs
    return df


def verify_uti_xlsx() -> dict:
    out: dict = {}
    base = ISZE_ROOT / "01_data" / "05_Dealer_sellout"
    for label, name in (("labelled_CY2024", "UTIPartSalesCY2024.xlsx"), ("labelled_CY2025", "UTIPartSalesCY2025.xlsx")):
        p = base / name
        if not p.exists():
            out[label] = {"exists": False, "path": str(p)}
            continue
        _, meta = load_uti_part_sales(p)
        out[label] = {
            "exists": True,
            "path": str(p),
            "report_month": meta.get("report_month"),
            "report_year": meta.get("report_year"),
            "unique_pn": meta.get("unique_pn"),
            "is_full_cy2024": False
            if label == "labelled_CY2024"
            else (meta.get("report_year") == 2025 and meta.get("report_month") == 12),
        }
    # Explicit honesty
    cy24 = out.get("labelled_CY2024", {})
    if cy24.get("exists") and cy24.get("report_year") == 2025 and cy24.get("report_month") == 1:
        out["cy2024_file_verdict"] = (
            "UTIPartSalesCY2024.xlsx is report 1/2025 (Jan-2025 YTD), NOT calendar 2024 — YoY blocked."
        )
    else:
        out["cy2024_file_verdict"] = str(cy24)
    return out


def inventory_rows(uti_meta: dict) -> list[dict]:
    rows = []
    for spec in SELLOUT_SPECS:
        db = spec["distributor_code"]
        years_present = []
        year_detail = []
        has_dealer_price = False
        qty_only = True
        sources = []
        for yr, fname in sorted(spec["files"].items()):
            path = DERIVED_DIR / fname
            if not path.exists():
                year_detail.append({"year": yr, "file": fname, "exists": False})
                continue
            g = load_year_qty(path, spec.get("prefer_grain"))
            # also peek raw for unit-price columns (avoid DataFrame.flags collision)
            raw = pd.read_csv(path, nrows=0)
            price_cols = [
                c
                for c in raw.columns
                if c.lower() != "flags"
                and any(k in c.lower() for k in ("price", "eur", "value", "asp", "invoice"))
            ]
            if price_cols:
                has_dealer_price = True
                qty_only = False
            years_present.append(yr)
            sources.append(fname)
            year_detail.append(
                {
                    "year": yr,
                    "file": fname,
                    "exists": True,
                    "n_pn": int(g["part_number"].nunique()) if not g.empty else 0,
                    "qty": float(g["qty"].sum()) if not g.empty else 0.0,
                    "partial": "YTD" in fname or "partial" in fname.lower(),
                }
            )
        full_cy = [y for y in years_present if y in (2023, 2024, 2025) and not any(
            d.get("year") == y and d.get("partial") for d in year_detail
        )]
        # 2026 always partial in these files
        full_cy = [y for y in years_present if y <= 2025]
        yoy_possible = False
        yoy_reason = ""
        pair = spec.get("yoy_pair")
        if pair and pair[0] in years_present and pair[1] in years_present:
            yoy_possible = True
            yoy_reason = f"sales_to_dealer qty for CY{pair[0]} and CY{pair[1]} both present (network grain)."
        elif db == "UTI":
            yoy_possible = False
            yoy_reason = uti_meta.get("cy2024_file_verdict", "no second full CY of sales-to-dealer")
        else:
            yoy_possible = False
            yoy_reason = (
                f"only calendar years present among long CSVs: {years_present}; "
                "need ≥2 full CY for arc volume response."
            )

        can_price_passthrough = False
        price_passthru_note = (
            "BLOCKED: long CSVs are qty-only — no dealer invoice / DB→DLR unit price. "
            "Upstream ISZE→DB ASP / PR00 can still be joined for volume response."
        )
        if has_dealer_price:
            can_price_passthrough = True
            price_passthru_note = "dealer unit price columns present in long CSV"

        rows.append(
            {
                "distributor_code": db,
                "entity_note": spec.get("note", ""),
                "years_present": "|".join(str(y) for y in years_present),
                "full_cy_years": "|".join(str(y) for y in full_cy),
                "n_full_cy": len(full_cy),
                "yoy_2024_2025_possible": "Y" if yoy_possible else "N",
                "yoy_reason": yoy_reason,
                "dealer_invoice_price_present": "Y" if has_dealer_price else "N",
                "qty_only": "Y" if qty_only else "N",
                "price_passthrough_status": "POSSIBLE" if can_price_passthrough else "BLOCKED",
                "price_passthrough_note": price_passthru_note,
                "pass_through_conversation": (
                    "YES — volume response vs upstream price (ITUK)"
                    if yoy_possible
                    else "NO for arc; single-year proxy only"
                    if 2025 in years_present
                    else "NO — insufficient coverage"
                ),
                "source_files": "|".join(sources),
                "year_detail_json": str(year_detail),
            }
        )
    return rows


def load_asp(years: list[int], dists: list[str]) -> pd.DataFrame:
    if not SALES_FACT_PARQUET.exists():
        return pd.DataFrame()
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    if "line_kind" in sales.columns:
        sales = sales[sales["line_kind"] == "part"]
    sales = sales[sales["year"].isin(years) & sales["distributor_code"].isin(dists)].copy()
    sales["part_number"] = sales["part_number"].map(normalize_pn)
    sales = sales.dropna(subset=["part_number"])
    sales = sales[sales["billed_qty"] > 0]
    sales["asp_eur"] = sales["net_sales_value"] / sales["billed_qty"]
    sales = sales[sales["asp_eur"] > 0]
    return (
        sales.groupby(["distributor_code", "year", "part_number"], as_index=False)
        .agg(asp_eur=("asp_eur", "median"), billed_qty=("billed_qty", "sum"))
    )


def load_pr00(years: list[int]) -> pd.DataFrame:
    frames = []
    for y in years:
        p = DERIVED_DIR / f"pricing_pr00_ie40_{y}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df["part_number"] = df["Material"].map(normalize_pn)
        df["pr00_eur"] = pd.to_numeric(df["Price_EUR"], errors="coerce")
        df["year"] = y
        df = df.dropna(subset=["part_number"])
        df = df[df["pr00_eur"] > 0]
        frames.append(df[["part_number", "year", "pr00_eur"]].drop_duplicates("part_number", keep="first"))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_yoy_panel(db: str, y0: int, y1: int, f0: str, f1: str, prefer_grain: str) -> pd.DataFrame:
    q0 = load_year_qty(DERIVED_DIR / f0, prefer_grain).rename(columns={"qty": "qty_0"})
    q1 = load_year_qty(DERIVED_DIR / f1, prefer_grain).rename(columns={"qty": "qty_1"})
    m = q0[["part_number", "qty_0"]].merge(q1[["part_number", "qty_1"]], on="part_number", how="inner")
    m["distributor_code"] = db
    return m


def yoy_family_rows(
    panel: pd.DataFrame,
    cat_map: dict[str, str],
    asp: pd.DataFrame,
    pr00: pd.DataFrame,
    db: str,
    entity_note: str,
) -> list[dict]:
    """Arc β: dln(sales_to_dealer qty) ~ dln(upstream ASP or PR00) within PMS family."""
    p = panel.copy()
    p["_pn"] = _norm(p["part_number"])
    p["pms_family"] = p["_pn"].map(cat_map)
    p = p.dropna(subset=["pms_family"])
    p = p[(p["qty_0"] >= MIN_QTY) & (p["qty_1"] >= MIN_QTY)]
    if p.empty:
        return []

    asp0 = asp[(asp["distributor_code"] == db) & (asp["year"] == Y0)][["part_number", "asp_eur"]].rename(
        columns={"asp_eur": "asp_0"}
    )
    asp1 = asp[(asp["distributor_code"] == db) & (asp["year"] == Y1)][["part_number", "asp_eur"]].rename(
        columns={"asp_eur": "asp_1"}
    )
    p = p.merge(asp0, on="part_number", how="left").merge(asp1, on="part_number", how="left")

    pr0 = pr00[pr00["year"] == Y0][["part_number", "pr00_eur"]].rename(columns={"pr00_eur": "pr00_0"})
    pr1 = pr00[pr00["year"] == Y1][["part_number", "pr00_eur"]].rename(columns={"pr00_eur": "pr00_1"})
    p = p.merge(pr0, on="part_number", how="left").merge(pr1, on="part_number", how="left")

    p["dlnq"] = np.log(p["qty_1"] / p["qty_0"])
    p["qty_pct"] = (p["qty_1"] / p["qty_0"] - 1.0) * 100.0
    p["dlnp_asp"] = np.where(
        (p["asp_0"] > 0) & (p["asp_1"] > 0),
        np.log(p["asp_1"] / p["asp_0"]),
        np.nan,
    )
    p["dlnp_pr00"] = np.where(
        (p["pr00_0"] > 0) & (p["pr00_1"] > 0),
        np.log(p["pr00_1"] / p["pr00_0"]),
        np.nan,
    )
    p["w"] = 0.5 * (p["qty_0"] + p["qty_1"])

    rows: list[dict] = []

    def volume_summary(fam: str, g: pd.DataFrame) -> dict:
        tot0 = float(g["qty_0"].sum())
        tot1 = float(g["qty_1"].sum())
        agg_pct = (tot1 / tot0 - 1.0) * 100.0 if tot0 > 0 else float("nan")
        return {
            "distributor_code": db,
            "entity_note": entity_note,
            "grain": "network_pn_pms_family",
            "pms_family": fam,
            "measure_kind": "volume_yoy_summary",
            "method": "sales_to_dealer_qty_yoy",
            "n_pns": int(len(g)),
            "n_pairs": int(len(g)),
            "sales_to_dealer_qty_y0": round(tot0, 1),
            "sales_to_dealer_qty_y1": round(tot1, 1),
            "median_qty_pct_chg": round(float(g["qty_pct"].median()), 2),
            # Aggregate % on summed qty — not mean of PN % (tiny bases explode)
            "wtd_qty_pct_chg": round(agg_pct, 2),
            "median_dlnp_pct": "",
            "beta": "",
            "se_beta": "",
            "r2": "",
            "low_power": len(g) < MIN_PNS_ADEQUATE,
            "price_axis": "n/a — volume only",
            "volume_axis": f"sales_to_dealer qty CY{Y0}→CY{Y1}",
            "dealer_invoice_price": "ABSENT",
            "reading": "family qty move dealer-side; price response not claimed here",
            "caveat": (
                "Qty-only files. wtd_qty_pct_chg = (sum qty 2025 / sum qty 2024 − 1). "
                "Useful for direction of dealer-facing volume; not pass-through."
            ),
        }

    def emit(fam: str, g: pd.DataFrame, price_col: str, price_label: str, method: str) -> None:
        gg = g.dropna(subset=[price_col, "dlnq"]).copy()
        gg = gg[np.isfinite(gg[price_col]) & np.isfinite(gg["dlnq"])]
        if len(gg) < MIN_PNS_CAT:
            return
        n_movers = int((gg[price_col].abs() >= MIN_ABS_DLNP).sum())
        med_dp = float(gg[price_col].median()) * 100.0
        std_dp = float(gg[price_col].std())
        if n_movers < MIN_PRICE_MOVERS or std_dp < MIN_ABS_DLNP:
            rows.append(
                {
                    "distributor_code": db,
                    "entity_note": entity_note,
                    "grain": "network_pn_pms_family",
                    "pms_family": fam,
                    "measure_kind": "volume_only",
                    "method": method + "_insufficient_price_move",
                    "n_pns": int(len(gg)),
                    "n_pairs": int(len(gg)),
                    "sales_to_dealer_qty_y0": round(float(gg["qty_0"].sum()), 1),
                    "sales_to_dealer_qty_y1": round(float(gg["qty_1"].sum()), 1),
                    "median_qty_pct_chg": round(float(gg["qty_pct"].median()), 2),
                    "wtd_qty_pct_chg": round(
                        float(np.average(gg["qty_pct"], weights=gg["w"])), 2
                    ),
                    "median_dlnp_pct": round(med_dp, 3),
                    "beta": "",
                    "se_beta": "",
                    "r2": "",
                    "low_power": True,
                    "price_axis": price_label,
                    "volume_axis": f"sales_to_dealer qty CY{Y0}→CY{Y1}",
                    "dealer_invoice_price": "ABSENT",
                    "reading": (
                        f"upstream price barely moved "
                        f"(median ΔP {med_dp:.2f}%, movers |ΔlnP|≥{MIN_ABS_DLNP}: {n_movers}); "
                        "β not estimated"
                    ),
                    "caveat": (
                        "Not dealer price pass-through. No DB→DLR invoice. "
                        "Too little upstream price variation for a stable volume-response β."
                    ),
                }
            )
            return
        for col in (price_col, "dlnq"):
            lo, hi = gg[col].quantile([WINSOR, 1 - WINSOR])
            gg[col] = gg[col].clip(lo, hi)
        beta, se, r2 = _wls_beta(gg[price_col].to_numpy(), gg["dlnq"].to_numpy(), gg["w"].to_numpy())
        n = len(gg)
        low = n < MIN_PNS_ADEQUATE
        # discard numerically absurd β (near-zero price denom leftovers)
        if abs(beta) > 50 or (se == se and se > 20):
            rows.append(
                {
                    "distributor_code": db,
                    "entity_note": entity_note,
                    "grain": "network_pn_pms_family",
                    "pms_family": fam,
                    "measure_kind": "unstable_beta",
                    "method": method + "_unstable",
                    "n_pns": n,
                    "n_pairs": n,
                    "sales_to_dealer_qty_y0": round(float(gg["qty_0"].sum()), 1),
                    "sales_to_dealer_qty_y1": round(float(gg["qty_1"].sum()), 1),
                    "median_qty_pct_chg": round(float(gg["qty_pct"].median()), 2),
                    "wtd_qty_pct_chg": round(float(np.average(gg["qty_pct"], weights=gg["w"])), 2),
                    "median_dlnp_pct": round(med_dp, 3),
                    "beta": round(beta, 3),
                    "se_beta": round(se, 3) if se == se else "",
                    "r2": round(r2, 3),
                    "low_power": True,
                    "price_axis": price_label,
                    "volume_axis": f"sales_to_dealer qty CY{Y0}→CY{Y1}",
                    "dealer_invoice_price": "ABSENT",
                    "reading": "β numerically unstable — do not use in conversation",
                    "caveat": "Small price moves inflate |β|. Prefer volume_yoy_summary rows.",
                }
            )
            return
        if beta < -0.5:
            reading = "volume fell when upstream price rose (contestable / sensitive signal)"
        elif beta < 0:
            reading = "weak negative volume response to upstream price"
        else:
            reading = "no negative volume response (mix/fleet/stocking confound likely)"
        rows.append(
            {
                "distributor_code": db,
                "entity_note": entity_note,
                "grain": "network_pn_pms_family",
                "pms_family": fam,
                "measure_kind": "volume_response_vs_upstream",
                "method": method,
                "n_pns": n,
                "n_pairs": n,
                "sales_to_dealer_qty_y0": round(float(gg["qty_0"].sum()), 1),
                "sales_to_dealer_qty_y1": round(float(gg["qty_1"].sum()), 1),
                "median_qty_pct_chg": round(float(gg["qty_pct"].median()), 2),
                "wtd_qty_pct_chg": round(float(np.average(gg["qty_pct"], weights=gg["w"])), 2),
                "median_dlnp_pct": round(med_dp, 3),
                "beta": round(beta, 3),
                "se_beta": round(se, 3) if se == se else "",
                "r2": round(r2, 3),
                "low_power": low,
                "price_axis": price_label,
                "volume_axis": f"sales_to_dealer qty CY{Y0}→CY{Y1}",
                "dealer_invoice_price": "ABSENT",
                "reading": reading,
                "caveat": (
                    "NOT dealer price elasticity / NOT ISZE→DB stocking elasticity. "
                    "β is dln(sales_to_dealer qty) / dln(upstream price). "
                    "Dealer invoice price absent → PRICE pass-through blocked. "
                    f"{'LOW_POWER n<' + str(MIN_PNS_ADEQUATE) if low else 'n_ok'}; "
                    "no demand-shock controls; fleet mix uncontrolled."
                ),
            }
        )

    for fam, g in p.groupby("pms_family"):
        if len(g) >= 3:
            rows.append(volume_summary(fam, g))
        emit(
            fam,
            g,
            "dlnp_asp",
            f"ISZE→DB median ASP CY{Y0}→CY{Y1} (billing; upstream — NOT dealer invoice)",
            "yoy_arc_dlnq_dlnp_asp",
        )
        emit(
            fam,
            g,
            "dlnp_pr00",
            f"PR00 IE40 list SP CY{Y0}→CY{Y1} (list — NOT dealer invoice)",
            "yoy_arc_dlnq_dlnp_pr00",
        )

    # All-PMS pooled
    rows.append(volume_summary("(all_pms)", p))
    emit(
        "(all_pms)",
        p,
        "dlnp_asp",
        f"ISZE→DB median ASP CY{Y0}→CY{Y1} (billing; upstream — NOT dealer invoice)",
        "yoy_arc_dlnq_dlnp_asp",
    )
    emit(
        "(all_pms)",
        p,
        "dlnp_pr00",
        f"PR00 IE40 list SP CY{Y0}→CY{Y1} (list — NOT dealer invoice)",
        "yoy_arc_dlnq_dlnp_pr00",
    )
    return rows


def proxy_cross_section_pms(
    db: str,
    entity_note: str,
    year: int,
    fname: str,
    prefer_grain: str,
    cat_map: dict[str, str],
    asp: pd.DataFrame,
) -> list[dict]:
    """Single-year proxy — BLOCKED for arc elasticity; level association only."""
    q = load_year_qty(DERIVED_DIR / fname, prefer_grain)
    if q.empty:
        return []
    a = asp[(asp["distributor_code"] == db) & (asp["year"] == year)][["part_number", "asp_eur"]]
    m = q.merge(a, on="part_number", how="inner")
    m["_pn"] = _norm(m["part_number"])
    m["pms_family"] = m["_pn"].map(cat_map)
    m = m.dropna(subset=["pms_family"])
    m = m[(m["qty"] >= MIN_QTY) & (m["asp_eur"] > 0)]
    rows = []
    for fam, g in m.groupby("pms_family"):
        gg = g.copy()
        n = len(gg)
        if n < MIN_PNS_CAT or float(gg["asp_eur"].std()) == 0:
            continue
        gg["lnq"] = np.log(gg["qty"])
        gg["lnp"] = np.log(gg["asp_eur"])
        for col in ("lnq", "lnp"):
            lo, hi = gg[col].quantile([WINSOR, 1 - WINSOR])
            gg[col] = gg[col].clip(lo, hi)
        beta, se, r2 = _wls_beta(gg["lnp"].to_numpy(), gg["lnq"].to_numpy(), gg["qty"].to_numpy())
        low = n < MIN_PNS_ADEQUATE
        rows.append(
            {
                "distributor_code": db,
                "entity_note": entity_note,
                "grain": "network_pn_pms_family",
                "pms_family": fam,
                "measure_kind": "proxy_blocked_arc",
                "method": "cross_section_lnq_lnp_asp",
                "n_pns": n,
                "n_pairs": n,
                "sales_to_dealer_qty_y0": "",
                "sales_to_dealer_qty_y1": round(float(gg["qty"].sum()), 1),
                "median_qty_pct_chg": "",
                "wtd_qty_pct_chg": "",
                "median_dlnp_pct": "",
                "beta": round(beta, 3),
                "se_beta": round(se, 3) if se == se else "",
                "r2": round(r2, 3),
                "low_power": low,
                "price_axis": f"ISZE→DB median ASP CY{year} (upstream — NOT dealer invoice)",
                "volume_axis": f"sales_to_dealer qty CY{year}",
                "dealer_invoice_price": "ABSENT",
                "reading": (
                    "level association only — NOT arc elasticity; YoY blocked for this DB"
                ),
                "caveat": (
                    "BLOCKED for pass-through / arc conversation. Single-year cross-section; "
                    "ASP is ISZE→DB not DB→DLR; part size confound. "
                    f"{'LOW_POWER n<' + str(MIN_PNS_ADEQUATE) if low else 'n_ok'}"
                ),
            }
        )
    return rows


def blocked_stub(db: str, entity_note: str, inv: dict, reason: str) -> dict:
    return {
        "distributor_code": db,
        "entity_note": entity_note,
        "grain": "network_pn",
        "pms_family": "(all_pms)",
        "measure_kind": "blocked",
        "method": "yoy_arc_passthrough",
        "n_pns": 0,
        "n_pairs": 0,
        "sales_to_dealer_qty_y0": "",
        "sales_to_dealer_qty_y1": "",
        "median_qty_pct_chg": "",
        "wtd_qty_pct_chg": "",
        "median_dlnp_pct": "",
        "beta": "",
        "se_beta": "",
        "r2": "",
        "low_power": True,
        "price_axis": "would need dealer invoice across ≥2 CY for PRICE pass-through; ASP/PR00 for volume response",
        "volume_axis": "sales_to_dealer qty YoY (need ≥2 full CY)",
        "dealer_invoice_price": "ABSENT",
        "reading": "insufficient_years_or_mislabelled_source",
        "caveat": reason + f" Inventory: years={inv.get('years_present')}.",
    }


def write_md(inv: pd.DataFrame, out: pd.DataFrame, uti_meta: dict) -> None:
    yoy = out[out["measure_kind"] == "volume_response_vs_upstream"]
    vol = out[out["measure_kind"] == "volume_yoy_summary"]
    blocked = out[out["measure_kind"] == "blocked"]
    proxy = out[out["measure_kind"] == "proxy_blocked_arc"]
    vol_only = out[out["measure_kind"] == "volume_only"]
    unstable = out[out["measure_kind"] == "unstable_beta"]
    lines = [
        "# PMS pass-through — sales to dealer vs upstream price (2024→2025)",
        "",
        "**As of:** 2026-09-22  ",
        "**Outputs:**  ",
        f"- `{OUT_CSV.relative_to(ISZE_ROOT).as_posix()}`  ",
        f"- `{OUT_INV.relative_to(ISZE_ROOT).as_posix()}`  ",
        "**Builder:** `01_data/91_build/build_pms_passthrough_db_dlr_2024_2025.py`  ",
        "",
        "Does **not** overwrite `price_elasticity_db_dlr_*.csv` or `price_volume_elasticity.csv`.",
        "",
        "---",
        "",
        "## Verdict",
        "",
        "**Only ITUK** has two full calendar years of sales-to-dealer qty (CY2024 + network CY2025), "
        "so only ITUK can support a **volume-response** conversation when ISZE→DB price moved. "
        "Every long CSV is **qty-only** — dealer invoice price is absent — so **price pass-through "
        "to the dealer invoice is BLOCKED** everywhere.",
        "",
        "On ITUK PMS parts, **upstream ASP / PR00 barely moved 2024→2025** for most families "
        "(median ΔP near 0%). That means a stable volume-response β is mostly not identifiable; "
        "the useful number is the **dealer-facing qty YoY by family**. Where β is shown, treat it "
        "as directional and low-powered — never as dealer elasticity, and never as "
        "`price_volume_elasticity.csv` (that file is ISZE→DB stocking only).",
        "",
        "**UTI:** the file named `UTIPartSalesCY2024.xlsx` is report "
        f"**{uti_meta.get('labelled_CY2024', {}).get('report_month')}/"
        f"{uti_meta.get('labelled_CY2024', {}).get('report_year')}** "
        "(Jan-2025 YTD), not calendar 2024. YoY blocked.",
        "",
        "Entity rules: UTI ≠ UMI; IUK ≠ ITUK ≠ IRELAND.",
        "",
        "---",
        "",
        "## Coverage",
        "",
        "| DB | Years present | YoY 2024→2025 | Dealer invoice price | Pass-through conversation |",
        "|----|---------------|---------------|----------------------|---------------------------|",
    ]
    for _, r in inv.iterrows():
        lines.append(
            f"| {r['distributor_code']} | {r['years_present']} | {r['yoy_2024_2025_possible']} | "
            f"{r['dealer_invoice_price_present']} | {r['pass_through_conversation']} |"
        )
    lines.extend(
        [
            "",
            "---",
            "",
            "## Axes",
            "",
            "| Axis | What we use | Honesty |",
            "|------|-------------|---------|",
            "| **Volume** | Sales to dealer qty (ITUK Duncan network CY2024 + CY2025) | True DB→dealer volume |",
            "| **Price (upstream)** | Median ISZE→DB ASP from billing, and/or PR00 IE40 list | Not dealer invoice |",
            "| **Dealer invoice** | — | **ABSENT** → PRICE pass-through blocked |",
            "",
            "PMS families come from `genuine_bvp_crossref.csv` (`pms_category`).",
            "",
            "---",
            "",
            "## ITUK PMS — sales-to-dealer qty YoY (primary usable table)",
            "",
        ]
    )
    if vol.empty:
        lines.append("_No volume summary rows._")
    else:
        show = vol.sort_values("pms_family")
        lines.append("| Family | n PNs | Qty 2024 | Qty 2025 | Median PN qty % | Aggregate qty % |")
        lines.append("|--------|------:|---------:|---------:|----------------:|----------------:|")
        for _, r in show.iterrows():
            lines.append(
                f"| {r['pms_family']} | {r['n_pns']} | {r['sales_to_dealer_qty_y0']} | "
                f"{r['sales_to_dealer_qty_y1']} | {r['median_qty_pct_chg']} | {r['wtd_qty_pct_chg']} |"
            )
        lines.append("")
        lines.append(
            "Aggregate qty % = (family sum 2025 ÷ family sum 2024 − 1). "
            "Median is across PNs and can disagree when mix shifts."
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Computable family betas (ITUK, only if upstream price moved enough)",
            "",
        ]
    )
    if yoy.empty:
        lines.append(
            "_No stable β cleared the price-move gate "
            f"(need ≥{MIN_PRICE_MOVERS} PNs with |ΔlnP|≥{MIN_ABS_DLNP}). "
            f"Volume-only / insufficient-price-move rows: **{len(vol_only)}**; "
            f"unstable discarded: **{len(unstable)}**._"
        )
    else:
        show = yoy.sort_values(["method", "pms_family"])
        lines.append(
            "| Family | Method | n PNs | Median upstream ΔP % | β (dlnQ/dlnP) | SE | Qty % (wtd) | Low power |"
        )
        lines.append("|--------|--------|------:|---------------------:|--------------:|---:|------------:|:---------:|")
        for _, r in show.iterrows():
            lines.append(
                f"| {r['pms_family']} | {r['method']} | {r['n_pns']} | {r['median_dlnp_pct']} | "
                f"{r['beta']} | {r['se_beta']} | {r['wtd_qty_pct_chg']} | {r['low_power']} |"
            )
        lines.append("")
        lines.append(
            "Caveat on every β: upstream price axis, sales-to-dealer volume axis, "
            "no dealer invoice, small n on several families, no fleet/demand controls."
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Stub / proxy counts",
            "",
            f"- Blocked arc / dealer-invoice stubs: **{len(blocked)}**",
            f"- Single-year proxy (blocked arc): **{len(proxy)}** rows",
            f"- Volume YoY summaries (ITUK PMS): **{len(vol)}**",
            f"- Volume-only (insufficient upstream price move): **{len(vol_only)}**",
            f"- Unstable β discarded: **{len(unstable)}**",
            f"- Stable volume-response vs upstream: **{len(yoy)}**",
            "",
            "---",
            "",
            "## Rebuild",
            "",
            "```powershell",
            "cd $env:ISZE_ROOT",
            "python 01_data/91_build/build_pms_passthrough_db_dlr_2024_2025.py",
            "```",
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    cat_map = pms_category_map()
    print(f"PMS PN map size={len(cat_map)}")

    uti_meta = verify_uti_xlsx()
    print("UTI verify:", uti_meta.get("cy2024_file_verdict"))

    inv_rows = inventory_rows(uti_meta)
    inv = pd.DataFrame(inv_rows)
    OUT_INV.parent.mkdir(parents=True, exist_ok=True)
    inv.to_csv(OUT_INV, index=False)
    print(f"wrote {OUT_INV} rows={len(inv)}")

    dists = [s["distributor_code"] for s in SELLOUT_SPECS]
    asp = load_asp([Y0, Y1], dists)
    pr00 = load_pr00([Y0, Y1])
    print(f"asp rows={len(asp)} pr00 rows={len(pr00)}")

    out_rows: list[dict] = []

    for spec in SELLOUT_SPECS:
        db = spec["distributor_code"]
        note = spec.get("note", "")
        inv_row = next(r for r in inv_rows if r["distributor_code"] == db)
        pair = spec.get("yoy_pair")

        if pair and inv_row["yoy_2024_2025_possible"] == "Y":
            y0, y1 = pair
            f0 = spec["files"][y0]
            f1 = spec["files"][y1]
            panel = build_yoy_panel(db, y0, y1, f0, f1, spec.get("prefer_grain", "network_pn"))
            print(f"{db} YoY panel PNs={len(panel)}")
            out_rows.extend(yoy_family_rows(panel, cat_map, asp, pr00, db, note))
            # also mark price pass-through blocked stub
            out_rows.append(
                {
                    "distributor_code": db,
                    "entity_note": note,
                    "grain": "network_pn",
                    "pms_family": "(all)",
                    "measure_kind": "blocked",
                    "method": "dealer_invoice_price_passthrough",
                    "n_pns": int(panel["part_number"].nunique()) if not panel.empty else 0,
                    "n_pairs": 0,
                    "sales_to_dealer_qty_y0": round(float(panel["qty_0"].sum()), 1) if not panel.empty else "",
                    "sales_to_dealer_qty_y1": round(float(panel["qty_1"].sum()), 1) if not panel.empty else "",
                    "median_qty_pct_chg": "",
                    "wtd_qty_pct_chg": "",
                    "median_dlnp_pct": "",
                    "beta": "",
                    "se_beta": "",
                    "r2": "",
                    "low_power": True,
                    "price_axis": "dealer invoice / DB→DLR unit price",
                    "volume_axis": f"sales_to_dealer qty CY{y0}→CY{y1} (available)",
                    "dealer_invoice_price": "ABSENT",
                    "reading": "PRICE_passthrough_blocked_qty_only_files",
                    "caveat": (
                        "Volume response vs upstream ASP/PR00 is computed separately. "
                        "Do not read those betas as dealer invoice pass-through."
                    ),
                }
            )
        else:
            out_rows.append(
                blocked_stub(db, note, inv_row, inv_row.get("yoy_reason", "YoY blocked"))
            )
            # single-year proxy if CY2025 exists
            if 2025 in spec["files"] and (DERIVED_DIR / spec["files"][2025]).exists():
                out_rows.extend(
                    proxy_cross_section_pms(
                        db,
                        note,
                        2025,
                        spec["files"][2025],
                        spec.get("prefer_grain", "network_pn"),
                        cat_map,
                        asp,
                    )
                )

    out = pd.DataFrame(out_rows)
    cols = [
        "distributor_code",
        "entity_note",
        "grain",
        "pms_family",
        "measure_kind",
        "method",
        "n_pns",
        "n_pairs",
        "sales_to_dealer_qty_y0",
        "sales_to_dealer_qty_y1",
        "median_qty_pct_chg",
        "wtd_qty_pct_chg",
        "median_dlnp_pct",
        "beta",
        "se_beta",
        "r2",
        "low_power",
        "price_axis",
        "volume_axis",
        "dealer_invoice_price",
        "reading",
        "caveat",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = ""
    out = out[cols]
    out["_sb"] = pd.to_numeric(out["beta"], errors="coerce")
    out = out.sort_values(
        ["measure_kind", "distributor_code", "method", "pms_family", "_sb"],
        ascending=[True, True, True, True, True],
    ).drop(columns="_sb")
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} rows={len(out)}")
    print(out.groupby(["measure_kind", "method"]).size().to_string())

    write_md(inv, out, uti_meta)
    print(f"wrote {OUT_MD}")

    # Console summary for parent agent
    print("\n=== COVERAGE ===")
    print(
        inv[
            ["distributor_code", "years_present", "yoy_2024_2025_possible", "pass_through_conversation"]
        ].to_string(index=False)
    )
    vol = out[out["measure_kind"] == "volume_yoy_summary"]
    if not vol.empty:
        print("\n=== ITUK PMS QTY YoY ===")
        print(
            vol[["pms_family", "n_pns", "sales_to_dealer_qty_y0", "sales_to_dealer_qty_y1", "wtd_qty_pct_chg"]]
            .to_string(index=False)
        )
    yoy = out[out["measure_kind"] == "volume_response_vs_upstream"]
    if not yoy.empty:
        print("\n=== STABLE FAMILY BETAS ===")
        print(
            yoy[
                ["pms_family", "method", "n_pns", "median_dlnp_pct", "beta", "se_beta", "wtd_qty_pct_chg", "low_power"]
            ].to_string(index=False)
        )
    else:
        print("\n=== STABLE FAMILY BETAS === none (upstream price barely moved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
