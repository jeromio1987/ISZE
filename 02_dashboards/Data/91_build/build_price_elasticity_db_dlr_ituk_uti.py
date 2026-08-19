#!/usr/bin/env python3
"""
DB → DLR price/volume response — ITUK + UTI only.

Honest scope (Mode B):
  - Volume axis = distributor sell-out qty (true DB→DLR layer).
  - Price axis = upstream ISZE→DB median ASP (billing) and/or PR00 sim list SP.
    We do NOT observe dealer purchase invoices → never claim true DB→DLR price
    elasticity. Rows are measure_kind=proxy (or blocked).
  - Existing price_volume_elasticity.csv remains ISZE→DB stocking; do not conflate.
  - Israel = UTI only (never blend UMI). ITUK separate.

Data gate (2026-08-10):
  - ITUK: CY2025 dealer×PN only (no prior CY sell-out) → no YoY arc elasticity.
  - UTI: Dec-2025 YTD + Jan-2025 snapshot only. File named UTIPartSalesCY2024.xlsx
    is Jan-2025 YTD (not CY2024) → no YoY arc elasticity yet.

Outputs:
  01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv
  01_data/01_Pricing/PRICE_ELASTICITY_DB_DLR_ITUK_UTI.md
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
    AIM_PN_CLASSIFICATION_CSV,
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import (  # noqa: E402
    aggregate_pn,
    load_ituk_dealer_sales,
    load_uti_part_sales,
    normalize_pn,
)

OUT_CSV = DERIVED_DIR / "price_elasticity_db_dlr_ituk_uti.csv"
OUT_MD = ISZE_ROOT / "01_data" / "01_Pricing" / "PRICE_ELASTICITY_DB_DLR_ITUK_UTI.md"
SIM_PARQUET = DERIVED_DIR / "pricing_sim_pr00_l12m.parquet"

DISTS = ("ITUK", "UTI")
YEAR = 2025
MIN_QTY = 10
MIN_PNS_CAT = 8
MIN_PNS_ADEQUATE = 20
WINSOR = 0.02


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


def category_map() -> dict[str, str]:
    cat_map: dict[str, str] = {}
    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    for col in ("genuine_pn", "bvp_pn"):
        if col not in xref.columns or "pms_category" not in xref.columns:
            continue
        sub = xref.dropna(subset=[col, "pms_category"])
        cat_map.update(dict(zip(_norm(sub[col]), sub["pms_category"].astype(str))))
    if AIM_PN_CLASSIFICATION_CSV.exists():
        aim = pd.read_csv(AIM_PN_CLASSIFICATION_CSV, usecols=["part_number", "aim_l1"], dtype=str)
        for pn, l1 in zip(_norm(aim["part_number"]), aim["aim_l1"]):
            cat_map.setdefault(pn, f"AIM: {l1}" if pd.notna(l1) else "AIM: Unclassified")
    return cat_map


def load_sellout() -> tuple[pd.DataFrame, dict]:
    """Network-PN CY2025 sell-out for ITUK + UTI. Returns long + coverage meta."""
    meta: dict = {"ituk": {}, "uti": {}, "blocked_yoy": True}
    rows = []

    ituk = load_ituk_dealer_sales(YEAR)
    if not ituk.empty:
        g = aggregate_pn(ituk, "qty_year")
        g["distributor_code"] = "ITUK"
        g["grain"] = "network_pn"  # summed from dealer_pn
        g["source_file"] = str(ituk["data_source"].iloc[0]) if "data_source" in ituk.columns else ""
        g["n_dealers"] = ituk["dealer_name"].nunique()
        rows.append(g)
        meta["ituk"] = {
            "source": g["source_file"].iloc[0],
            "grain_raw": "dealer_pn",
            "n_dealers": int(ituk["dealer_name"].nunique()),
            "n_pn": int(g["part_number"].nunique()),
            "qty": float(g["qty"].sum()),
            "years": [YEAR],
        }
    else:
        meta["ituk"] = {"error": "no ITUK sell-out file"}

    uti_path = ISZE_ROOT / "01_data" / "12_raw" / "dealer_sales" / "UTI" / "UTIPartSales_2025-12_YTD.xlsx"
    uti, umeta = load_uti_part_sales(uti_path if uti_path.exists() else None)
    if not uti.empty:
        g = uti.groupby("part_number", as_index=False)["qty_ytd"].sum().rename(columns={"qty_ytd": "qty"})
        g["distributor_code"] = "UTI"
        g["grain"] = "network_pn"
        g["source_file"] = umeta.get("source_file", "")
        g["n_dealers"] = 0
        rows.append(g)
        # Misnamed CY2024 file check
        mis = ISZE_ROOT / "01_data" / "05_Dealer_sellout" / "UTIPartSalesCY2024.xlsx"
        mis_note = ""
        if mis.exists():
            _, m2 = load_uti_part_sales(mis)
            mis_note = (
                f"UTIPartSalesCY2024.xlsx is report {m2.get('report_month')}/{m2.get('report_year')} "
                f"(Jan YTD), NOT CY2024 — YoY blocked."
            )
        meta["uti"] = {
            "source": umeta.get("source_file"),
            "grain_raw": "network_pn",
            "n_dealers": 0,
            "n_pn": int(g["part_number"].nunique()),
            "qty": float(g["qty"].sum()),
            "years": [YEAR],
            "misnamed_cy2024_note": mis_note,
        }
    else:
        meta["uti"] = {"error": "no UTI sell-out file"}

    if not rows:
        return pd.DataFrame(), meta
    out = pd.concat(rows, ignore_index=True)
    out["part_number"] = out["part_number"].map(normalize_pn)
    out = out.dropna(subset=["part_number"])
    out = out[out["qty"] > 0]
    return out, meta


def load_asp_cy(year: int = YEAR) -> pd.DataFrame:
    if not SALES_FACT_PARQUET.exists():
        return pd.DataFrame(columns=["distributor_code", "part_number", "asp_eur", "billed_qty"])
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[(sales["year"] == year) & (sales["distributor_code"].isin(DISTS))].copy()
    if "line_kind" in s.columns:
        s = s[s["line_kind"] == "part"]
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    s = s[s["billed_qty"] > 0]
    s["asp_eur"] = s["net_sales_value"] / s["billed_qty"]
    s = s[s["asp_eur"] > 0]
    return (
        s.groupby(["distributor_code", "part_number"], as_index=False)
        .agg(asp_eur=("asp_eur", "median"), billed_qty=("billed_qty", "sum"))
    )


def load_sim_sp() -> pd.DataFrame:
    if not SIM_PARQUET.exists():
        return pd.DataFrame()
    sim = pd.read_parquet(SIM_PARQUET)
    sim["part_number"] = sim["part_number"].map(normalize_pn)
    sim = sim.dropna(subset=["part_number"])
    for c in ("sp_eur_2025", "sp_eur_2026"):
        sim[c] = pd.to_numeric(sim[c], errors="coerce")
    sim = sim[(sim["sp_eur_2025"] > 0) & (sim["sp_eur_2026"] > 0)]
    sim = sim.drop_duplicates("part_number", keep="first")
    sim["sp_pct_change_2025_2026"] = (sim["sp_eur_2026"] / sim["sp_eur_2025"] - 1.0) * 100.0
    sim["dlnp_list"] = np.log(sim["sp_eur_2026"] / sim["sp_eur_2025"])
    return sim[
        ["part_number", "sp_eur_2025", "sp_eur_2026", "sp_pct_change_2025_2026", "dlnp_list", "qty_l12m"]
    ]


def attach_category(df: pd.DataFrame, cat_map: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    out["_pn"] = _norm(out["part_number"])
    out["category"] = out["_pn"].map(cat_map).fillna("AIM: Unclassified")
    return out


def proxy_cross_section(panel: pd.DataFrame) -> list[dict]:
    """Category-level ln(sellout_qty) ~ ln(ISZE→DB ASP). Proxy only."""
    rows = []
    for (dist, cat), grp in panel.groupby(["distributor_code", "category"]):
        g = grp[(grp["qty"] >= MIN_QTY) & (grp["asp_eur"] > 0)].copy()
        n = len(g)
        if n < MIN_PNS_CAT or g["asp_eur"].std() == 0:
            continue
        g["lnq"] = np.log(g["qty"])
        g["lnp"] = np.log(g["asp_eur"])
        for col in ("lnq", "lnp"):
            lo, hi = g[col].quantile([WINSOR, 1 - WINSOR])
            g[col] = g[col].clip(lo, hi)
        beta, se, r2 = _wls_beta(
            g["lnp"].to_numpy(), g["lnq"].to_numpy(), g["qty"].to_numpy()
        )
        low = n < MIN_PNS_ADEQUATE
        rows.append(
            {
                "distributor_code": dist,
                "israel_note": "UTI_only_not_UMI" if dist == "UTI" else "",
                "grain": "network_pn_category",
                "category": cat,
                "measure_kind": "proxy",
                "method": "cross_section_lnq_lnp_asp",
                "n_pns": n,
                "n_pairs": n,
                "sellout_qty_total": round(float(g["qty"].sum()), 1),
                "median_price_eur": round(float(g["asp_eur"].median()), 4),
                "median_dlnp_pct": "",
                "beta": round(beta, 3),
                "se_beta": round(se, 3) if se == se else "",
                "r2": round(r2, 3),
                "low_power": low,
                "sellout_wtd_sp_pct_chg_2025_2026": "",
                "price_axis": "ISZE→DB median ASP CY2025 (billing; upstream pass-through proxy — NOT dealer invoice)",
                "volume_axis": "DB→DLR sell-out qty CY2025",
                "reading": (
                    "higher ASP ↔ lower sell-out qty (contestable / price-sensitive signal)"
                    if beta < -0.5
                    else "weak negative level association"
                    if beta < 0
                    else "no negative level association (size/mix confound likely)"
                ),
                "caveat": (
                    "PROXY not elasticity: single-year cross-section; ASP is ISZE→DB not DB→DLR; "
                    "part size/necessity confound; no demand-shock controls; "
                    f"{'LOW_POWER n<' + str(MIN_PNS_ADEQUATE) if low else 'n_ok'}"
                ),
            }
        )
    return rows


def proxy_list_exposure(panel: pd.DataFrame, sim: pd.DataFrame) -> list[dict]:
    """Sell-out-weighted planned list SP % change by category — exposure, not response."""
    if sim.empty:
        return []
    m = panel.merge(sim, on="part_number", how="inner")
    rows = []
    for (dist, cat), grp in m.groupby(["distributor_code", "category"]):
        g = grp[grp["qty"] >= MIN_QTY].copy()
        n = len(g)
        if n < MIN_PNS_CAT:
            continue
        w = g["qty"].to_numpy()
        wtd = float(np.average(g["sp_pct_change_2025_2026"], weights=w))
        rows.append(
            {
                "distributor_code": dist,
                "israel_note": "UTI_only_not_UMI" if dist == "UTI" else "",
                "grain": "network_pn_category",
                "category": cat,
                "measure_kind": "proxy",
                "method": "list_shock_exposure_2025_2026",
                "n_pns": n,
                "n_pairs": n,
                "sellout_qty_total": round(float(g["qty"].sum()), 1),
                "median_price_eur": round(float(g["sp_eur_2025"].median()), 4),
                "median_dlnp_pct": round(float(g["dlnp_list"].median()) * 100, 3),
                "beta": "",
                "se_beta": "",
                "r2": "",
                "low_power": n < MIN_PNS_ADEQUATE,
                "sellout_wtd_sp_pct_chg_2025_2026": round(wtd, 3),
                "price_axis": "PR00 sim list SP % change 2025→2026 (IE40 condition)",
                "volume_axis": "DB→DLR sell-out qty CY2025 (weight only — no 2026 sell-out yet)",
                "reading": "planned_list_exposure_not_response",
                "caveat": (
                    "PROXY exposure table only: no observed sell-out response to 2026 list; "
                    "do not feed into allocation as elasticity coefficient"
                ),
            }
        )
    return rows


def blocked_yoy_rows(meta: dict) -> list[dict]:
    rows = []
    for dist in DISTS:
        info = meta.get(dist.lower(), {})
        rows.append(
            {
                "distributor_code": dist,
                "israel_note": "UTI_only_not_UMI" if dist == "UTI" else "",
                "grain": "network_pn",
                "category": "(all)",
                "measure_kind": "blocked",
                "method": "yoy_arc_elasticity",
                "n_pns": info.get("n_pn", 0),
                "n_pairs": 0,
                "sellout_qty_total": info.get("qty", 0),
                "median_price_eur": "",
                "median_dlnp_pct": "",
                "beta": "",
                "se_beta": "",
                "r2": "",
                "low_power": True,
                "sellout_wtd_sp_pct_chg_2025_2026": "",
                "price_axis": "would need DB→DLR invoice or pass-through series across ≥2 CY",
                "volume_axis": "DB→DLR sell-out qty YoY (need ≥2 full CY)",
                "reading": "insufficient_sellout_years",
                "caveat": (
                    f"True arc elasticity blocked. Coverage: {info}. "
                    + (info.get("misnamed_cy2024_note") or "")
                ),
            }
        )
    return rows


def write_md(out: pd.DataFrame, meta: dict) -> None:
    proxy_cs = out[out["method"] == "cross_section_lnq_lnp_asp"]
    proxy_ex = out[out["method"] == "list_shock_exposure_2025_2026"]
    lines = [
        "# Price response DB→DLR — ITUK + UTI (Mode B method note)",
        "",
        "**As of:** 2026-08-10  ",
        "**Output:** `01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv`  ",
        "**Builder:** `01_data/91_build/build_price_elasticity_db_dlr_ituk_uti.py`  ",
        "**Constraint:** elasticity / response **only** at DB→DLR. Do **not** claim ISZE→DB elasticity.  ",
        "**Israel:** UTI only — never blend UMI.",
        "",
        "---",
        "",
        "## Verdict",
        "",
        "**True YoY arc elasticity is blocked** — only one full calendar year of sell-out "
        "(CY2025) for ITUK and UTI. The file labelled `UTIPartSalesCY2024.xlsx` under "
        "`01_data/05_Dealer_sellout/` is a **Jan-2025 YTD** snapshot (same family as "
        "`UTIPartSales_2025-01.xlsx`), not CY2024.",
        "",
        "Delivered rows are therefore **`measure_kind=proxy`** (plus `blocked` stub rows "
        "for the YoY method). Filename keeps `price_elasticity_*` for roadmap discoverability; "
        "read the `measure_kind` column.",
        "",
        "---",
        "",
        "## Axes",
        "",
        "| Axis | What we use | Honesty |",
        "|------|-------------|---------|",
        "| **Volume** | Sell-out qty CY2025 — ITUK summed dealer×PN → network PN; UTI network PN | True DB→DLR volume |",
        "| **Price (proxy A)** | Median ISZE→DB ASP from `sales_fact` CY2025 (qty×median unit price, same as DEALER_SELL_OUT valuation) | Upstream cost to DB — **not** dealer invoice |",
        "| **Price (proxy B)** | PR00 sim list SP % 2025→2026 (`pricing_sim_pr00_l12m`) | Planned list shock; sell-out used as **weight only** |",
        "",
        "No SAP pocket / waterfall. Talk in **%** for list moves. FY27 target remains **+3% weighted** (separate).",
        "",
        "---",
        "",
        "## Coverage",
        "",
        f"- **ITUK:** {meta.get('ituk')}",
        f"- **UTI:** {meta.get('uti')}",
        f"- Cross-section proxy categories: **{len(proxy_cs)}** rows "
        f"(ITUK {int((proxy_cs.distributor_code=='ITUK').sum())} / "
        f"UTI {int((proxy_cs.distributor_code=='UTI').sum())})",
        f"- List-exposure proxy categories: **{len(proxy_ex)}** rows",
        "",
        "### Gates",
        "",
        f"- Drop PN with sell-out qty < **{MIN_QTY}**",
        f"- Category needs ≥ **{MIN_PNS_CAT}** PNs to emit; `low_power` if n < **{MIN_PNS_ADEQUATE}**",
        f"- Winsorize log levels at **{WINSOR:.0%}** / **{1-WINSOR:.0%}** for cross-section",
        "",
        "---",
        "",
        "## Methods in the CSV",
        "",
        "| method | measure_kind | Meaning |",
        "|--------|--------------|---------|",
        "| `yoy_arc_elasticity` | `blocked` | Would be real arc β from YoY lnQ/lnP — insufficient years |",
        "| `cross_section_lnq_lnp_asp` | `proxy` | Category WLS: ln(sell-out qty) ~ ln(ASP). Level association, confounded |",
        "| `list_shock_exposure_2025_2026` | `proxy` | Sell-out-weighted mean planned SP % change — **not** a response β |",
        "",
        "---",
        "",
        "## vs existing `price_volume_elasticity.csv`",
        "",
        "That file is **ISZE→DB stocking** (billing qty × realized ASP across distributors). "
        "It must **not** be labelled DB→DLR or end-market elasticity. This new CSV is the "
        "sell-out-side track for ITUK/UTI only.",
        "",
        "---",
        "",
        "## Engine / allocation plug-in",
        "",
        "**Not wired into `isze_pricing` allocation.** Safe optional path later:",
        "",
        "1. Keep `allocation.target = 0.03` (+3% weighted) unchanged.",
        "2. Do **not** multiply deltas by `beta` until `measure_kind=elasticity` exists with adequate n.",
        "3. Optional: join `list_shock_exposure_*` rows as a **weight/exposure** diagnostic "
        "in run notes; or gate soft warnings when a category’s cross-section `beta < -0.5` "
        "and `low_power=False` — still not a coefficient in the solver.",
        "4. Config hook (suggested, not implemented): "
        "`paths.db_dlr_response: 01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv`.",
        "",
        "Action-map consumer left untouched this pass (proxies too weak to move ceilings).",
        "",
        "---",
        "",
        "## Rebuild",
        "",
        "```powershell",
        "cd $env:ISZE_ROOT",
        "python 01_data/91_build/build_price_elasticity_db_dlr_ituk_uti.py",
        "```",
        "",
        "### Unblock true elasticity",
        "",
        "- File full-CY sell-out for ITUK and/or UTI for a second year (CY2024 or CY2026).",
        "- Prefer dealer invoice / DB→DLR unit price if available; else keep ASP as labeled pass-through proxy.",
        "- Re-run builder; rows with `measure_kind=elasticity` will appear only when YoY pairs clear gates.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    cat_map = category_map()
    sell, meta = load_sellout()
    if sell.empty:
        print("ERROR: no sell-out loaded")
        return 1
    asp = load_asp_cy(YEAR)
    sim = load_sim_sp()
    print(
        f"sellout rows={len(sell)} asp rows={len(asp)} sim pns={len(sim)} "
        f"ITUK qty={meta.get('ituk',{}).get('qty')} UTI qty={meta.get('uti',{}).get('qty')}"
    )

    panel = sell.merge(asp, on=["distributor_code", "part_number"], how="left")
    panel = attach_category(panel, cat_map)

    rows: list[dict] = []
    rows.extend(blocked_yoy_rows(meta))
    rows.extend(proxy_cross_section(panel))
    rows.extend(proxy_list_exposure(panel, sim))

    out = pd.DataFrame(rows)
    # Stable column order
    cols = [
        "distributor_code",
        "israel_note",
        "grain",
        "category",
        "measure_kind",
        "method",
        "n_pns",
        "n_pairs",
        "sellout_qty_total",
        "median_price_eur",
        "median_dlnp_pct",
        "beta",
        "se_beta",
        "r2",
        "low_power",
        "sellout_wtd_sp_pct_chg_2025_2026",
        "price_axis",
        "volume_axis",
        "reading",
        "caveat",
    ]
    out = out[cols]
    # Sort: blocked first, then by dist, method, beta
    out["_sort_beta"] = pd.to_numeric(out["beta"], errors="coerce")
    out = out.sort_values(
        ["measure_kind", "distributor_code", "method", "_sort_beta"],
        ascending=[True, True, True, True],
    ).drop(columns="_sort_beta")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    write_md(out, meta)
    print(f"wrote {OUT_CSV} rows={len(out)}")
    print(f"wrote {OUT_MD}")
    print(out.groupby(["measure_kind", "method", "distributor_code"]).size().to_string())
    strong = out[
        (out["method"] == "cross_section_lnq_lnp_asp")
        & (out["low_power"] == False)  # noqa: E712
        & (pd.to_numeric(out["beta"], errors="coerce") < -0.5)
    ]
    print(f"proxy cross-section price-sensitive (adequate n): {len(strong)}")
    if len(strong):
        print(strong[["distributor_code", "category", "n_pns", "beta", "se_beta", "r2"]].head(12).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
