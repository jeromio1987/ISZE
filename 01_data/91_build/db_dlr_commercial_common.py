"""Shared loaders for DB→DLR commercial stack (replenishment, revision queue, elasticity)."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ISZE_ROOT = Path(__file__).resolve().parents[2]
PRISM = ISZE_ROOT / "03_analytics" / "Isuzu" / "prism"
DERIVED = ISZE_ROOT / "01_data" / "00_derived"
RAW_DEALER = ISZE_ROOT / "01_data" / "12_raw" / "dealer_sales"
KS_RESULTS = ISZE_ROOT / "04_tools" / "autodoc_scraper" / "ks_results.csv"
KS_RAW_DIR = ISZE_ROOT / "01_data" / "01_Pricing" / "_raw"
SIM_PARQUET = DERIVED / "pricing_sim_pr00_l12m.parquet"

# Chat / UI: sales to dealer and %GM. Code field names stay.
# STREET_FACTOR is a markup gross-up (list × 1.40 × 1.275). Do not brief Jerome in this factor.
STREET_FACTOR = 1.785
GBP_EUR = 1.17  # diagnostic only; label in meta

NETWORK_DBS = ("ITUK", "UTI", "IRELAND", "IUK", "GREECE")
SELL_NETWORK_MONTHLY_COLS = (
    "distributor_code",
    "part_number",
    "year_month",
    "sellout_qty",
    "grain",
    "dealer_name",
)
SELL_NETWORK_ANNUAL_COLS = ("distributor_code", "part_number", "sellout_qty")


def _empty_sell_network_monthly(db: str) -> pd.DataFrame:
    return pd.DataFrame(columns=list(SELL_NETWORK_MONTHLY_COLS)).assign(distributor_code=db)


def _empty_sell_network_annual(db: str) -> pd.DataFrame:
    return pd.DataFrame(columns=list(SELL_NETWORK_ANNUAL_COLS)).assign(distributor_code=db)
YEAR = 2025

MONTH_NAME_TO_NUM = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def _ensure_prism() -> None:
    p = str(PRISM)
    if p not in sys.path:
        sys.path.insert(0, p)


def norm_pn(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def normalize_pn_scalar(value: Any) -> str | None:
    _ensure_prism()
    from modules.dealer_sales_loader import normalize_pn  # noqa: WPS433

    return normalize_pn(value)


def year_month(year: int, month: int) -> str:
    return f"{int(year):04d}-{int(month):02d}"


def load_category_map() -> dict[str, str]:
    _ensure_prism()
    from config import AIM_PN_CLASSIFICATION_CSV, GENUINE_BVP_CROSSREF_CSV  # noqa: WPS433

    cat_map: dict[str, str] = {}
    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    for col in ("genuine_pn", "bvp_pn"):
        if col not in xref.columns or "pms_category" not in xref.columns:
            continue
        sub = xref.dropna(subset=[col, "pms_category"])
        cat_map.update(dict(zip(norm_pn(sub[col]), sub["pms_category"].astype(str))))
    if AIM_PN_CLASSIFICATION_CSV.exists():
        aim = pd.read_csv(AIM_PN_CLASSIFICATION_CSV, usecols=["part_number", "aim_l1"], dtype=str)
        for pn, l1 in zip(norm_pn(aim["part_number"]), aim["aim_l1"]):
            cat_map.setdefault(pn, f"AIM: {l1}" if pd.notna(l1) else "AIM: Unclassified")
    return cat_map


def load_billing_monthly(dbs: tuple[str, ...] = NETWORK_DBS, year: int = YEAR) -> pd.DataFrame:
    _ensure_prism()
    from config import SALES_FACT_PARQUET  # noqa: WPS433

    dim_path = DERIVED / "distributor_dimension.csv"
    if not SALES_FACT_PARQUET.exists() or not dim_path.exists():
        return pd.DataFrame()
    sf = pd.read_parquet(
        SALES_FACT_PARQUET,
        columns=["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value", "year", "saty"],
    )
    dim = pd.read_csv(dim_path)
    dim = dim[dim["network_role"].astype(str) == "network_db"][
        ["sold_to_sap", "distributor_code"]
    ].dropna(subset=["distributor_code"])
    dim["sold_to_sap"] = pd.to_numeric(dim["sold_to_sap"], errors="coerce")
    sf["sold_to_sap"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    sf = sf.merge(dim, on="sold_to_sap", how="inner")
    sf = sf[sf["distributor_code"].isin(dbs)].copy()
    if "saty" in sf.columns:
        is_cr_re = sf["saty"].astype(str).str.strip().str.upper().isin(["CR", "RE"])
        sf = sf[(sf["net_sales_value"].fillna(0) >= 0) & ~is_cr_re]
    sf["billing_date"] = pd.to_datetime(sf["billing_date"], errors="coerce")
    sf = sf.dropna(subset=["billing_date"])
    sf = sf[sf["year"] == year]
    sf["part_number"] = sf["part_number"].map(normalize_pn_scalar)
    sf = sf.dropna(subset=["part_number"])
    sf["billed_qty"] = pd.to_numeric(sf["billed_qty"], errors="coerce").fillna(0)
    sf = sf[sf["billed_qty"] != 0]
    sf["year_month"] = sf["billing_date"].dt.to_period("M").astype(str)
    return (
        sf.groupby(["distributor_code", "part_number", "year_month"], as_index=False)
        .agg(bill_qty=("billed_qty", "sum"), bill_eur=("net_sales_value", "sum"))
    )


def load_sellout_long_monthly(db: str, year: int = YEAR) -> pd.DataFrame:
    """Network PN × year_month from canonical long CSV."""
    paths = [
        DERIVED / f"dealer_sellout_long_{db}_CY{year}.csv",
        DERIVED / f"dealer_sellout_long_{db}_CY{year}YTD.csv",
    ]
    path = next((p for p in paths if p.exists()), None)
    if path is None:
        return pd.DataFrame()
    df = pd.read_csv(path, dtype={"part_number": str}, low_memory=False)
    if df.empty or "qty" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    if "year" in df.columns:
        df = df[pd.to_numeric(df["year"], errors="coerce") == year]
    df["part_number"] = df["part_number"].map(normalize_pn_scalar)
    df = df.dropna(subset=["part_number"])
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    if "period" in df.columns:
        df["year_month"] = df["period"].astype(str).str.strip()
        df = df[df["year_month"].str.match(r"^\d{4}-\d{2}$", na=False)]
    else:
        return pd.DataFrame()
    return (
        df.groupby(["part_number", "year_month"], as_index=False)["qty"]
        .sum()
        .rename(columns={"qty": "sellout_qty"})
        .assign(distributor_code=db, grain="network_pn", dealer_name="")
    )


def load_ituk_sellout_monthly(year: int = YEAR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (network_monthly, dealer_monthly)."""
    _ensure_prism()
    from modules.dealer_sales_loader import load_ituk_dealer_sales, MONTHS  # noqa: WPS433

    raw = load_ituk_dealer_sales(year)
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame()
    month_cols = [c for c in raw.columns if c in MONTHS]
    if not month_cols:
        return pd.DataFrame(), pd.DataFrame()
    raw["part_number"] = raw["part_number"].map(normalize_pn_scalar)
    raw = raw.dropna(subset=["part_number"])
    dealer_rows = []
    for mname in month_cols:
        mnum = MONTH_NAME_TO_NUM[mname]
        ym = year_month(year, mnum)
        chunk = raw[["dealer_name", "part_number", mname]].copy()
        chunk = chunk.rename(columns={mname: "sellout_qty"})
        chunk["sellout_qty"] = pd.to_numeric(chunk["sellout_qty"], errors="coerce").fillna(0)
        chunk = chunk[chunk["sellout_qty"] > 0]
        chunk["year_month"] = ym
        dealer_rows.append(chunk)
    dealer = pd.concat(dealer_rows, ignore_index=True)
    dealer["distributor_code"] = "ITUK"
    dealer["grain"] = "dealer_pn"
    network = (
        dealer.groupby(["distributor_code", "part_number", "year_month"], as_index=False)["sellout_qty"]
        .sum()
        .assign(grain="network_pn", dealer_name="")
    )
    return network, dealer


def load_uti_sellout_monthly() -> pd.DataFrame:
    """Stack UTI PartSales monthly snapshots → network PN × year_month."""
    _ensure_prism()
    from modules.dealer_sales_loader import load_uti_part_sales  # noqa: WPS433

    uti_dir = RAW_DEALER / "UTI"
    if not uti_dir.is_dir():
        return pd.DataFrame()
    rows = []
    for path in sorted(uti_dir.glob("UTIPartSales_*.xlsx")):
        df, meta = load_uti_part_sales(path)
        if df.empty or meta.get("report_year") is None or meta.get("report_month") is None:
            continue
        ym = year_month(int(meta["report_year"]), int(meta["report_month"]))
        chunk = df[["part_number", "qty_month"]].copy()
        chunk["part_number"] = chunk["part_number"].map(normalize_pn_scalar)
        chunk = chunk.dropna(subset=["part_number"])
        chunk["sellout_qty"] = pd.to_numeric(chunk["qty_month"], errors="coerce").fillna(0)
        chunk = chunk[chunk["sellout_qty"] > 0]
        chunk["year_month"] = ym
        rows.append(chunk[["part_number", "year_month", "sellout_qty"]])
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out = (
        out.groupby(["part_number", "year_month"], as_index=False)["sellout_qty"]
        .sum()
        .assign(distributor_code="UTI", grain="network_pn", dealer_name="")
    )
    return out


def load_sellout_network_monthly(db: str, year: int = YEAR) -> pd.DataFrame:
    if db == "ITUK":
        net, _ = load_ituk_sellout_monthly(year)
        if not net.empty:
            return net
    elif db == "UTI":
        out = load_uti_sellout_monthly()
        if not out.empty:
            return out
    out = load_sellout_long_monthly(db, year)
    return out if not out.empty else _empty_sell_network_monthly(db)


def load_sellout_network_annual(db: str, year: int = YEAR) -> pd.DataFrame:
    _ensure_prism()
    from modules.dealer_sales_loader import (  # noqa: WPS433
        aggregate_pn,
        load_ituk_dealer_sales,
        load_sellout_long_pn,
        load_uti_part_sales,
    )
    from config import DERIVED_DIR  # noqa: WPS433

    if db == "ITUK":
        raw = load_ituk_dealer_sales(year)
        if raw.empty:
            g = load_sellout_long_pn(db, year, DERIVED_DIR).rename(columns={"qty_year": "sellout_qty"})
        else:
            g = aggregate_pn(raw, "qty_year").rename(columns={"qty": "sellout_qty"})
    elif db == "UTI":
        path = RAW_DEALER / "UTI" / "UTIPartSales_2025-12_YTD.xlsx"
        uti, _ = load_uti_part_sales(path if path.exists() else None)
        if uti.empty:
            g = load_sellout_long_pn(db, year, DERIVED_DIR).rename(columns={"qty_year": "sellout_qty"})
        else:
            g = uti.groupby("part_number", as_index=False)["qty_ytd"].sum().rename(columns={"qty_ytd": "sellout_qty"})
    else:
        g = load_sellout_long_pn(db, year, DERIVED_DIR).rename(columns={"qty_year": "sellout_qty"})
    if g.empty:
        return _empty_sell_network_annual(db)
    g["part_number"] = g["part_number"].map(normalize_pn_scalar)
    g = g.dropna(subset=["part_number"])
    g["sellout_qty"] = pd.to_numeric(g["sellout_qty"], errors="coerce").fillna(0)
    g = g[g["sellout_qty"] > 0]
    return g.assign(distributor_code=db)


def load_billing_annual(dbs: tuple[str, ...] = NETWORK_DBS, year: int = YEAR) -> pd.DataFrame:
    m = load_billing_monthly(dbs, year)
    if m.empty:
        return m
    return (
        m.groupby(["distributor_code", "part_number"], as_index=False)
        .agg(bill_qty=("bill_qty", "sum"), bill_eur=("bill_eur", "sum"))
    )


def classify_pipeline(bill_qty: float, sellout_qty: float) -> str:
    """Warehouse timing, not lost sales.

    Sales to dealer above our bill = destock (they already had pieces).
    Sales to dealer below our bill = restock. Code names stay for existing files.
    """
    if bill_qty <= 0 and sellout_qty > 0:
        return "leakage_no_bill"
    if sellout_qty <= 0 and bill_qty > 0:
        return "overstock_no_sellout"
    if bill_qty <= 0:
        return "no_activity"
    ratio = sellout_qty / bill_qty
    if ratio >= 1.25:
        return "leakage_high_sellthrough"
    if ratio <= 0.65:
        return "overstock_low_sellthrough"
    return "balanced"


def load_sim_sp() -> pd.DataFrame:
    if not SIM_PARQUET.exists():
        return pd.DataFrame()
    sim = pd.read_parquet(SIM_PARQUET)
    sim["part_number"] = sim["part_number"].map(normalize_pn_scalar)
    sim = sim.dropna(subset=["part_number"])
    for c in ("sp_eur_2025", "sp_eur_2026"):
        sim[c] = pd.to_numeric(sim[c], errors="coerce")
    sim = sim[(sim["sp_eur_2025"] > 0) & (sim["sp_eur_2026"] > 0)]
    sim = sim.drop_duplicates("part_number", keep="first")
    sim["planned_sp_pct_chg_2025_2026"] = (sim["sp_eur_2026"] / sim["sp_eur_2025"] - 1.0) * 100.0
    return sim[
        ["part_number", "sp_eur_2025", "sp_eur_2026", "planned_sp_pct_chg_2025_2026", "qty_l12m"]
    ]


def _load_pr00_lookup() -> dict[str, float]:
    pr_path = DERIVED / "pricing_pr00_ie40.parquet"
    if not pr_path.exists():
        return {}
    pr = pd.read_parquet(pr_path, columns=["part_number", "sp_eur"])
    pr["pn"] = pr["part_number"].map(normalize_pn_scalar)
    pr["sp_eur"] = pd.to_numeric(pr["sp_eur"], errors="coerce")
    pr = pr.dropna(subset=["pn", "sp_eur"])
    pr = pr[pr["sp_eur"] > 0].sort_values("sp_eur", ascending=False).drop_duplicates("pn")
    return dict(zip(pr["pn"], pr["sp_eur"]))


def load_ks_pn_index() -> pd.DataFrame:
    """KS + IAM crawl union — widened beyond legacy ks_results.csv (~148)."""
    import re

    pr_map = _load_pr00_lookup()
    parts: list[pd.DataFrame] = []

    if KS_RESULTS.exists():
        ks = pd.read_csv(KS_RESULTS, dtype=str)
        ks["part_number"] = ks["PN"].map(normalize_pn_scalar)
        ks = ks.dropna(subset=["part_number"])
        ks["pr00_eur"] = pd.to_numeric(ks.get("PR00_EUR"), errors="coerce")
        for col in ("KS_AM_MinPrice_GBP", "KS_GEN_MinPrice_GBP"):
            if col in ks.columns:
                ks[col] = pd.to_numeric(ks[col], errors="coerce")
        ks["shop_gbp"] = ks[["KS_AM_MinPrice_GBP", "KS_GEN_MinPrice_GBP"]].min(axis=1)
        ks["ks_source"] = "ks_results_legacy"
        parts.append(ks)

    # KS catalog crawls — OEM PNs on page × min AM/genuine GBP price
    if KS_RAW_DIR.is_dir():
        for path in sorted(KS_RAW_DIR.glob("ks_catalog*.csv")):
            df = pd.read_csv(path, dtype=str, low_memory=False)
            if "oem_on_page" not in df.columns:
                continue
            price_col = "price_ex_vat_gbp" if "price_ex_vat_gbp" in df.columns else None
            line_col = "line" if "line" in df.columns else None
            rows = []
            for _, r in df.iterrows():
                oems = re.findall(r"\d{8,12}", str(r.get("oem_on_page") or ""))
                if not oems:
                    continue
                gbp = pd.to_numeric(r.get(price_col), errors="coerce") if price_col else np.nan
                if pd.isna(gbp) or gbp <= 0:
                    continue
                line = str(r.get(line_col) or "").lower()
                for pn_raw in oems:
                    pn = normalize_pn_scalar(pn_raw)
                    if not pn:
                        continue
                    rows.append({"part_number": pn, "shop_gbp": gbp, "ks_line": line, "ks_source": path.name})
            if rows:
                parts.append(pd.DataFrame(rows))

    # IAM live quotes (non-KS shops) — min EUR per ISZE PN
    live = KS_RAW_DIR / "iam_sku_live_quotes_20260818.csv"
    if live.exists():
        iq = pd.read_csv(live, dtype=str)
        iq = iq[iq.get("keep", "").astype(str).str.startswith("yes", na=False)]
        iq["part_number"] = iq["isze_pn"].map(normalize_pn_scalar)
        iq["shop_eur"] = pd.to_numeric(iq.get("price_eur_exvat_est"), errors="coerce")
        iq = iq.dropna(subset=["part_number", "shop_eur"])
        iq = iq[iq["shop_eur"] > 0]
        if not iq.empty:
            g = iq.groupby("part_number", as_index=False)["shop_eur"].min()
            g["shop_gbp"] = g["shop_eur"] / GBP_EUR
            g["ks_source"] = "iam_live_quotes"
            parts.append(g)

    # Inbox PMS PN-search products (durable copy under _raw if present)
    for prod_path in (
        KS_RAW_DIR / "ks_pms_products_20260819.csv",
        ISZE_ROOT
        / "02_dashboards"
        / "Data"
        / "90_INBOX"
        / "ks_pms_scan_20260819"
        / "products.csv",
    ):
        if not prod_path.exists():
            continue
        prod = pd.read_csv(prod_path, dtype=str)
        if "pn" not in prod.columns:
            continue
        prod["part_number"] = prod["pn"].map(normalize_pn_scalar)
        gen = pd.to_numeric(prod.get("gen_gbp"), errors="coerce")
        iam = pd.to_numeric(prod.get("iam_gbp"), errors="coerce")
        prod["shop_gbp"] = pd.concat([gen, iam], axis=1).min(axis=1)
        prod = prod.dropna(subset=["part_number", "shop_gbp"])
        prod = prod[prod["shop_gbp"] > 0]
        if not prod.empty:
            g = prod.groupby("part_number", as_index=False)["shop_gbp"].min()
            g["ks_source"] = "ks_pms_products_20260819"
            parts.append(g)
        break

    # Inbox compare file — matched ISZE/ITUK PNs with KS GBP
    for cmp_path in (
        KS_RAW_DIR / "ks_aftermarket_price_compare_20260819.csv",
        ISZE_ROOT
        / "02_dashboards"
        / "Data"
        / "90_INBOX"
        / "ks_pms_scan_20260819"
        / "ks_aftermarket_price_compare_20260819.csv",
    ):
        if not cmp_path.exists():
            continue
        cmp = pd.read_csv(cmp_path, dtype=str)
        if "matched_isze_ituk_pn" not in cmp.columns:
            continue
        cmp["part_number"] = cmp["matched_isze_ituk_pn"].map(normalize_pn_scalar)
        cmp["shop_gbp"] = pd.to_numeric(cmp.get("ks_gbp_exvat"), errors="coerce")
        cmp = cmp.dropna(subset=["part_number", "shop_gbp"])
        cmp = cmp[cmp["shop_gbp"] > 0]
        if not cmp.empty:
            g = cmp.groupby("part_number", as_index=False)["shop_gbp"].min()
            g["ks_source"] = "ks_aftermarket_compare_20260819"
            parts.append(g)
        break

    if not parts:
        return pd.DataFrame()

    raw = pd.concat(parts, ignore_index=True)
    raw["part_number"] = raw["part_number"].map(normalize_pn_scalar)
    raw = raw.dropna(subset=["part_number"])
    raw["shop_gbp"] = pd.to_numeric(raw.get("shop_gbp"), errors="coerce")
    raw["shop_eur"] = pd.to_numeric(raw.get("shop_eur"), errors="coerce")
    raw.loc[raw["shop_eur"].isna() & raw["shop_gbp"].notna(), "shop_eur"] = raw["shop_gbp"] * GBP_EUR

    agg = (
        raw.groupby("part_number", as_index=False)
        .agg(
            shop_gbp=("shop_gbp", "min"),
            shop_eur=("shop_eur", "min"),
            ks_source=("ks_source", lambda s: "|".join(sorted(set(s.astype(str))))[:200]),
        )
    )
    agg["pr00_eur"] = agg["part_number"].map(pr_map)
    agg["reference_sellout_eur"] = agg["pr00_eur"] * STREET_FACTOR
    agg["ks_price_index"] = np.where(
        agg["reference_sellout_eur"] > 0,
        agg["shop_eur"] / agg["reference_sellout_eur"],
        np.nan,
    )
    agg["ks_has_quote"] = agg["shop_gbp"].notna() & (agg["shop_gbp"] > 0)
    agg["ks_status"] = "crawl_union_20260825"
    return agg[
        [
            "part_number",
            "pr00_eur",
            "reference_sellout_eur",
            "shop_gbp",
            "shop_eur",
            "ks_price_index",
            "ks_has_quote",
            "ks_status",
            "ks_source",
        ]
    ]
