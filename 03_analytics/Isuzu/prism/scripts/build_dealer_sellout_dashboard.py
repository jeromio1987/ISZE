#!/usr/bin/env python3
"""Build UTI vs ITUK dealer sell-out comparison + static dashboard."""
from __future__ import annotations

import html
import json
import math
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import (  # noqa: E402
    DASHBOARDS_DIR,
    DASHBOARDS_JSON_DIR,
    DATA_ROOT,
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)

UIO_FALLBACK = {"ITUK": 22_389.0, "UTI": 10_336.0}
from modules.data_prep import (  # noqa: E402
    _get_fiscal_year,
    apply_distributor_codes,
    load_distributor_mapping,
)
from modules.dealer_sales_loader import (  # noqa: E402
    MONTHS,
    UTI_DIR,
    aggregate_pn,
    load_ituk_dealer_sales,
    load_uti_part_sales,
    normalize_pn,
)
from modules.dealer_sellout_analytics import (  # noqa: E402
    add_sellthrough_columns,
    attach_pn_master,
    load_dimension_and_xref,
    verify_bvp_genuine_integrity,
)

DASH_JSON = DASHBOARDS_JSON_DIR / "dealer_sellout_compare.json"
DASH_HTML = DASHBOARDS_DIR / "sales" / "Dealer_Sellout_UTI_vs_ITUK.html"
SALES_PARQUET = SALES_FACT_PARQUET

PMS_LABELS = {
    "oil_filter": "Oil filter",
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "urea_filter": "Urea filter",
    "brake_pad": "Brake pad",
    "brake_shoe": "Brake shoe",
    "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate",
    "clutch_kit": "Clutch kit",
}


def _json_safe(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if hasattr(obj, "item"):
        try:
            return _json_safe(obj.item())
        except (ValueError, AttributeError, TypeError):
            pass
    raise TypeError(type(obj))


def _json_clean(obj):
    if isinstance(obj, dict):
        return {k: _json_clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_clean(v) for v in obj]
    if isinstance(obj, (str, bool, bytes)):
        return obj
    try:
        if obj is not None and pd.isna(obj):
            return None
    except (ValueError, TypeError):
        pass
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if hasattr(obj, "item") and not isinstance(obj, (bytes, bytearray)):
        try:
            return _json_clean(obj.item())
        except (ValueError, AttributeError, TypeError):
            return None
    return obj


def file_uti_sources() -> None:
    """Seed missing UTI files from the old Data/ drop. Never overwrite monthly snapshots."""
    UTI_DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in [
        (DATA_ROOT / "Dealer_sellout" / "UTIPartSalesCY2024.xlsx", UTI_DIR / "UTIPartSales_2025-01.xlsx"),
        (DATA_ROOT / "Dealer_sellout" / "UTIPartSalesCY2025.xlsx", UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx"),
    ]:
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)


def _load_sales() -> pd.DataFrame:
    if not SALES_PARQUET.exists():
        return pd.DataFrame()
    sales = pd.read_parquet(SALES_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    if "billing_date" in sales.columns:
        dt = pd.to_datetime(sales["billing_date"], errors="coerce")
        if "year" not in sales.columns:
            sales["year"] = dt.dt.year
        if "month" not in sales.columns:
            sales["month"] = dt.dt.month
    if "fiscal_year" not in sales.columns:
        sales["fiscal_year"] = sales.apply(_get_fiscal_year, axis=1)
    if "line_kind" in sales.columns:
        sales = sales[sales["line_kind"] == "part"]
    return sales


def billing_pn(dist: str, *, year: int | None = None, fiscal_year: int | None = None) -> pd.DataFrame:
    sales = _load_sales()
    empty = pd.DataFrame(columns=["part_number", "billing_qty"])
    if sales.empty:
        return empty
    s = sales[sales["distributor_code"] == dist].copy()
    if year is not None:
        s = s[s["year"] == year]
    if fiscal_year is not None:
        s = s[s["fiscal_year"] == fiscal_year]
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    return s.groupby("part_number", as_index=False)["billed_qty"].sum().rename(
        columns={"billed_qty": "billing_qty"}
    )


def billing_uti_2025() -> pd.DataFrame:
    return billing_pn("UTI", year=2025)


def load_uti_monthlies() -> tuple[pd.DataFrame, list[dict]]:
    """One row per PN × calendar month from qty Month (not the YTD column)."""
    reports = []
    parts = []
    for p in sorted(UTI_DIR.glob("UTIPartSales_*.xlsx")):
        df, meta = load_uti_part_sales(p)
        reports.append(meta)
        if df.empty or meta.get("report_month") is None or meta.get("report_year") is None:
            continue
        tmp = df[["part_number", "qty_month"]].copy()
        tmp["year"] = int(meta["report_year"])
        tmp["month"] = int(meta["report_month"])
        tmp["qty"] = pd.to_numeric(tmp["qty_month"], errors="coerce").fillna(0)
        parts.append(tmp[["part_number", "year", "month", "qty"]])
    if not parts:
        return pd.DataFrame(columns=["part_number", "year", "month", "qty"]), reports
    return pd.concat(parts, ignore_index=True), reports


def duncan_ituk_months(year: int) -> pd.DataFrame:
    path = DERIVED_DIR / f"dealer_sellout_long_ITUK_CY{year}YTD.csv"
    if year == 2025:
        path = DERIVED_DIR / "dealer_sellout_long_ITUK_network_CY2025.csv"
    if not path.exists():
        alt = DERIVED_DIR / f"dealer_sellout_long_ITUK_CY{year}.csv"
        path = alt if alt.exists() else path
    if not path.exists():
        return pd.DataFrame(columns=["part_number", "year", "month", "qty"])
    df = pd.read_csv(path, dtype={"part_number": str}, low_memory=False)
    if "period_grain" in df.columns:
        df = df[df["period_grain"].astype(str).str.lower() == "month"]
    df = df.copy()
    df["part_number"] = df["part_number"].map(normalize_pn)
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    per = df["period"].astype(str)
    df["year"] = pd.to_numeric(per.str.slice(0, 4), errors="coerce")
    df["month"] = pd.to_numeric(per.str.slice(5, 7), errors="coerce")
    df = df.dropna(subset=["part_number", "year", "month"])
    return df[["part_number", "year", "month", "qty"]]


def ituk_dealer_months() -> pd.DataFrame:
    raw = load_ituk_dealer_sales(2025)
    if raw.empty:
        return pd.DataFrame(columns=["part_number", "year", "month", "qty"])
    rows = []
    for i, name in enumerate(MONTHS, start=1):
        if name not in raw.columns:
            continue
        tmp = raw[["part_number", name]].copy()
        tmp["qty"] = pd.to_numeric(tmp[name], errors="coerce").fillna(0)
        tmp["year"] = 2025
        tmp["month"] = i
        rows.append(tmp[["part_number", "year", "month", "qty"]])
    if not rows:
        return pd.DataFrame(columns=["part_number", "year", "month", "qty"])
    return pd.concat(rows, ignore_index=True)


def filter_months(df: pd.DataFrame, pairs: list[tuple[int, int]]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["part_number", "qty"])
    want = {(int(y), int(m)) for y, m in pairs}
    mask = [
        (int(y), int(m)) in want
        for y, m in zip(df["year"].tolist(), df["month"].tolist())
    ]
    m = df.loc[mask]
    if m.empty:
        return pd.DataFrame(columns=["part_number", "qty"])
    return m.groupby("part_number", as_index=False)["qty"].sum()


def load_uio() -> dict[str, float]:
    out = dict(UIO_FALLBACK)
    if GPS_SPU_BY_DB_CSV.exists():
        gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
        sub = gps[(gps["year"] == 2025) & (gps["distributor_code"].isin(("ITUK", "UTI")))]
        for _, r in sub.iterrows():
            u = float(r["uio_units"]) if pd.notna(r.get("uio_units")) else 0.0
            if u > 0:
                out[str(r["distributor_code"])] = u
    return out


def enrich_pms(pms: pd.DataFrame, uio: dict[str, float]) -> pd.DataFrame:
    out = pms.copy()
    ituk_u = uio.get("ITUK") or 0.0
    uti_u = uio.get("UTI") or 0.0
    for side, u in (("ituk", ituk_u), ("uti", uti_u)):
        tot_col = f"{side}_total"
        bvp_col = f"{side}_bvp"
        tot = (
            pd.to_numeric(out[tot_col], errors="coerce").fillna(0)
            if tot_col in out.columns
            else pd.Series(0.0, index=out.index)
        )
        bvp = (
            pd.to_numeric(out[bvp_col], errors="coerce").fillna(0)
            if bvp_col in out.columns
            else pd.Series(0.0, index=out.index)
        )
        out[f"{side}_per_truck"] = (tot / u) if u else None
        share = pd.Series(index=out.index, dtype="float64")
        mask = tot > 0
        share.loc[mask] = bvp.loc[mask] / tot.loc[mask]
        out[f"{side}_bvp_share"] = share
    if "uti_bvp" in out.columns and "bill_bvp" in out.columns:
        st_num = pd.to_numeric(out["uti_bvp"], errors="coerce")
        st_den = pd.to_numeric(out["bill_bvp"], errors="coerce")
        st = pd.Series(index=out.index, dtype="float64")
        mask = st_den > 0
        st.loc[mask] = st_num.loc[mask] / st_den.loc[mask]
        out["sellthrough_bvp"] = st
    elif "sellthrough_bvp" not in out.columns:
        out["sellthrough_bvp"] = pd.Series(index=out.index, dtype="float64")
    return out


def pms_from_qty(ituk_pn: pd.DataFrame, uti_pn: pd.DataFrame, dim, desc, xref, prefix_bill=None) -> pd.DataFrame:
    ituk_cat = pivot_catalog(catalog_pms_summary(attach_pn_master(ituk_pn, dim, desc, xref), "qty"), "ituk")
    uti_cat = pivot_catalog(catalog_pms_summary(attach_pn_master(uti_pn, dim, desc, xref), "qty"), "uti")
    pms = ituk_cat.merge(uti_cat, on="pms_category", how="outer").fillna(0)
    pms["category_label"] = pms["pms_category"].map(PMS_LABELS).fillna(pms["pms_category"])
    return pms


def catalog_pms_summary(pn_df: pd.DataFrame, qty_col: str) -> pd.DataFrame:
    p = pn_df[pn_df["pms_category"].notna() & (pn_df["pms_category"] != "")]
    if p.empty:
        return pd.DataFrame(columns=["pms_category", "line_type", "qty"])
    return p.groupby(["pms_category", "line_type"], as_index=False)[qty_col].sum().rename(
        columns={qty_col: "qty"}
    )


def pivot_catalog(summary: pd.DataFrame, prefix: str) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    w = summary.pivot_table(
        index="pms_category", columns="line_type", values="qty", aggfunc="sum", fill_value=0
    ).reset_index()
    w.columns.name = None
    rename = {lt: f"{prefix}_{lt}" for lt in ("genuine", "bvp") if lt in w.columns}
    w = w.rename(columns=rename)
    for lt in ("genuine", "bvp"):
        col = f"{prefix}_{lt}"
        if col not in w.columns:
            w[col] = 0
    w[f"{prefix}_total"] = w[f"{prefix}_genuine"] + w[f"{prefix}_bvp"]
    return w


def build_payload() -> dict:
    file_uti_sources()
    dim, xref, desc = load_dimension_and_xref()
    bvp_check = verify_bvp_genuine_integrity(dim, xref)
    uio = load_uio()

    ituk_pn = attach_pn_master(
        aggregate_pn(load_ituk_dealer_sales(2025), "qty_year"), dim, desc, xref
    )

    uti_monthlies, uti_reports = load_uti_monthlies()
    uti_ytd = pd.DataFrame()
    for p in sorted(UTI_DIR.glob("UTIPartSales_*.xlsx")):
        df, meta = load_uti_part_sales(p)
        if meta.get("report_month") == 12 and meta.get("report_year") == 2025:
            uti_ytd = df
            break
    uti_ytd_pn = attach_pn_master(
        aggregate_pn(uti_ytd, "qty_ytd").rename(columns={"qty_ytd": "qty"}), dim, desc, xref
    )
    billing = attach_pn_master(billing_uti_2025(), dim, desc, xref)

    ituk_cat = pivot_catalog(catalog_pms_summary(ituk_pn, "qty"), "ituk")
    uti_cat = pivot_catalog(catalog_pms_summary(uti_ytd_pn, "qty"), "uti")
    bill_cat = pivot_catalog(
        catalog_pms_summary(billing.assign(qty=billing["billing_qty"]), "qty"), "bill"
    )

    pms_cmp = ituk_cat.merge(uti_cat, on="pms_category", how="outer", suffixes=("_ituk", "_uti"))
    pms_cmp = pms_cmp.merge(bill_cat, on="pms_category", how="outer").fillna(0)
    pms_cmp["category_label"] = pms_cmp["pms_category"].map(PMS_LABELS).fillna(pms_cmp["pms_category"])
    pms_cmp["uti_vs_ituk_pct"] = pms_cmp.apply(
        lambda r: (r["uti_total"] / r["ituk_total"] * 100) if r["ituk_total"] else None,
        axis=1,
    )
    pms_cmp["sellthrough_bvp"] = pms_cmp.apply(
        lambda r: (float(r["uti_bvp"]) / float(r["bill_bvp"])) if float(r.get("bill_bvp") or 0) else None,
        axis=1,
    )
    pms_cmp["sellthrough_total"] = pms_cmp.apply(
        lambda r: (float(r["uti_total"]) / float(r["bill_total"])) if float(r.get("bill_total") or 0) else None,
        axis=1,
    )
    pms_cmp = enrich_pms(pms_cmp, uio)

    fy26_pairs = [(2026, 4), (2026, 5), (2026, 6)]
    uti_fy26 = filter_months(uti_monthlies, fy26_pairs)
    ituk_fy26 = filter_months(duncan_ituk_months(2026), fy26_pairs)
    pms_fy26 = pd.DataFrame()
    if not uti_fy26.empty or not ituk_fy26.empty:
        pms_fy26 = ituk_fy26.merge(uti_fy26, on="part_number", how="outer", suffixes=("_ituk", "_uti"))
        # rebuild via catalog
        ituk_fy26_pn = attach_pn_master(ituk_fy26.rename(columns={"qty": "qty"}) if "qty" in ituk_fy26.columns else ituk_fy26, dim, desc, xref)
        uti_fy26_pn = attach_pn_master(uti_fy26, dim, desc, xref)
        ituk_c = pivot_catalog(catalog_pms_summary(ituk_fy26_pn, "qty"), "ituk")
        uti_c = pivot_catalog(catalog_pms_summary(uti_fy26_pn, "qty"), "uti")
        pms_fy26 = ituk_c.merge(uti_c, on="pms_category", how="outer").fillna(0)
        pms_fy26["category_label"] = pms_fy26["pms_category"].map(PMS_LABELS).fillna(pms_fy26["pms_category"])
        pms_fy26 = enrich_pms(pms_fy26, uio)

    sales = _load_sales()
    fy_bill = {}
    for fy in (2025, 2026):
        fy_bill[fy] = {}
        for dist in ("ITUK", "UTI"):
            sub = sales[(sales["distributor_code"] == dist) & (sales["fiscal_year"] == fy)] if not sales.empty else pd.DataFrame()
            fy_bill[fy][dist] = {
                "qty": float(sub["billed_qty"].sum()) if not sub.empty else 0.0,
                "eur": float(sub["net_sales_value"].sum()) if not sub.empty and "net_sales_value" in sub.columns else 0.0,
            }

    ituk_apr_dec = filter_months(
        ituk_dealer_months(),
        [(2025, m) for m in range(4, 13)],
    )
    ituk_q1_26 = filter_months(duncan_ituk_months(2026), [(2026, 1), (2026, 2), (2026, 3)])
    ituk_fy25_qty = float(ituk_apr_dec["qty"].sum()) + float(ituk_q1_26["qty"].sum())
    uti_fy25_have = filter_months(
        uti_monthlies,
        [(2025, m) for m in (8, 9, 10, 11, 12)] + [(2026, 1), (2026, 2), (2026, 3)],
    )
    uti_fy25_have_qty = float(uti_fy25_have["qty"].sum()) if not uti_fy25_have.empty else 0.0

    audit = billing[["part_number", "billing_qty"]].rename(columns={"billing_qty": "uti_billing_qty"})
    audit = audit.merge(
        uti_ytd_pn[["part_number", "qty"]].rename(columns={"qty": "uti_dealer_ytd"}),
        on="part_number",
        how="outer",
    )
    audit = audit.merge(
        ituk_pn[["part_number", "qty"]].rename(columns={"qty": "ituk_dealer_cy25"}),
        on="part_number",
        how="outer",
    )
    audit = attach_pn_master(audit, dim, desc, xref)
    for c in ("uti_billing_qty", "uti_dealer_ytd", "ituk_dealer_cy25"):
        audit[c] = pd.to_numeric(audit[c], errors="coerce").fillna(0)
    audit = add_sellthrough_columns(audit, uti_ytd_pn.set_index("part_number")["qty"].to_dict())
    audit = audit.sort_values("uti_billing_qty", ascending=False)

    spot_checks = pd.concat(
        [
            audit[
                (audit["pms_category"] == "fuel_filter")
                & (audit["uti_billing_qty"] + audit["uti_dealer_ytd"] > 0)
            ].head(15),
            audit[
                (audit["line_type"] == "genuine")
                & (audit["catalog_paired_bvp"].astype(str).str.len() > 0)
                & (audit["uti_dealer_ytd"] == 0)
                & (audit["catalog_paired_dealer_ytd"] > 0)
            ].head(10),
            audit[audit["line_type_ok"] == False].head(10),  # noqa: E712
            audit[(audit["gap_flag"] == "billing_no_dealer") & (audit["uti_billing_qty"] >= 200)].head(10),
        ]
    ).drop_duplicates(subset=["part_number"])

    overlap = audit[(audit["ituk_dealer_cy25"] > 0) & (audit["uti_dealer_ytd"] > 0)].nlargest(
        25, "ituk_dealer_cy25"
    )

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    pms_cmp.to_csv(DERIVED_DIR / "dealer_sellout_pms_compare.csv", index=False)
    audit.to_csv(DERIVED_DIR / "dealer_sellout_pn_audit.csv", index=False)
    spot_checks.to_csv(DERIVED_DIR / "dealer_sellout_spot_checks.csv", index=False)
    overlap.to_csv(DERIVED_DIR / "dealer_sellout_pn_overlap.csv", index=False)
    uti_ytd_pn.to_csv(DERIVED_DIR / "dealer_sellout_uti_ytd_by_pn.csv", index=False)
    ituk_pn.to_csv(DERIVED_DIR / "dealer_sellout_ituk_cy2025_by_pn.csv", index=False)

    ff = pms_cmp[pms_cmp["pms_category"] == "fuel_filter"]
    st_bvp = None
    if len(ff):
        v = ff["sellthrough_bvp"].iloc[0]
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            st_bvp = float(v) * 100

    ituk_u = uio.get("ITUK") or 0
    uti_u = uio.get("UTI") or 0
    ituk_qty = float(ituk_pn["qty"].sum())
    uti_qty = float(uti_ytd_pn["qty"].sum())
    ituk_bvp_share = (
        float(ituk_pn.loc[ituk_pn["line_type"] == "bvp", "qty"].sum()) / ituk_qty
        if ituk_qty and "line_type" in ituk_pn.columns
        else None
    )
    uti_bvp_share = (
        float(uti_ytd_pn.loc[uti_ytd_pn["line_type"] == "bvp", "qty"].sum()) / uti_qty
        if uti_qty and "line_type" in uti_ytd_pn.columns
        else None
    )

    spot_cols = [
        "part_number",
        "description",
        "line_type",
        "expected_line_type",
        "line_type_ok",
        "pms_category",
        "uti_billing_qty",
        "uti_dealer_ytd",
        "catalog_paired_bvp",
        "catalog_paired_dealer_ytd",
        "catalog_pair_source",
        "sellthrough_same_pn",
        "pair_note",
    ]

    return {
        "generated": date.today().isoformat(),
        "uio": uio,
        "scope_note": (
            "CY2025 sell-out is apples: ITUK Jan–Dec dealer file and UTI Dec report qty Year (calendar Jan–Dec). "
            "Not a YTD stub. ISZE FY = Apr–Mar (FY2025 = Apr 2025–Mar 2026). "
            "Headline comparison is per truck because parc differs (ITUK vs UTI). "
            "FY2025 billing is a full 12 months. FY sell-out for UTI Apr–Jul 2025 is missing — not invented. "
            "FY2026 YTD sell-out = Apr–Jun 2026 (3 of 12) on both sides."
        ),
        "bvp_genuine_integrity": bvp_check,
        "uti_reports": uti_reports,
        "summary": {
            "ituk_cy2025_dealer_qty": int(ituk_qty),
            "uti_cy2025_dealer_qty": int(uti_qty),
            "uti_cy2025_billing_qty": int(billing["billing_qty"].sum()),
            "ituk_per_truck": (ituk_qty / ituk_u) if ituk_u else None,
            "uti_per_truck": (uti_qty / uti_u) if uti_u else None,
            "ituk_bvp_share": ituk_bvp_share,
            "uti_bvp_share": uti_bvp_share,
            "ituk_uio": ituk_u,
            "uti_uio": uti_u,
            "fuel_filter_bvp_sellthrough_pct": st_bvp,
            "ituk_fy2025_billing_qty": fy_bill[2025]["ITUK"]["qty"],
            "uti_fy2025_billing_qty": fy_bill[2025]["UTI"]["qty"],
            "ituk_fy2026_billing_qty": fy_bill[2026]["ITUK"]["qty"],
            "uti_fy2026_billing_qty": fy_bill[2026]["UTI"]["qty"],
            "ituk_fy2025_sellout_qty": ituk_fy25_qty,
            "uti_fy2025_sellout_qty_incomplete": uti_fy25_have_qty,
            "uti_fy2025_months_missing": "Apr–Jul 2025",
            "ituk_fy2026_ytd_sellout_qty": float(ituk_fy26["qty"].sum()) if not ituk_fy26.empty else 0.0,
            "uti_fy2026_ytd_sellout_qty": float(uti_fy26["qty"].sum()) if not uti_fy26.empty else 0.0,
        },
        "pms_compare": pms_cmp.to_dict(orient="records"),
        "pms_fy2026_ytd": pms_fy26.to_dict(orient="records") if not pms_fy26.empty else [],
        "spot_checks": spot_checks[spot_cols].to_dict(orient="records"),
        "pn_overlap": overlap[
            ["part_number", "description", "ituk_dealer_cy25", "uti_dealer_ytd", "line_type"]
        ].to_dict(orient="records"),
    }


def _e(text: object) -> str:
    if text is None:
        return ""
    if isinstance(text, float) and (math.isnan(text) or math.isinf(text)):
        return "—"
    s = str(text)
    if s.lower() == "nan":
        return "—"
    return html.escape(s)


def _num(n: object) -> float:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return v


def _fmt(n: object) -> str:
    if n is None or n == "":
        return "—"
    try:
        v = float(n)
    except (TypeError, ValueError):
        return "—" if str(n).lower() == "nan" else _e(n)
    if math.isnan(v) or math.isinf(v):
        return "—"
    return f"{v:,.0f}"


def _pct(n: object) -> str:
    if n is None or n == "":
        return "—"
    try:
        v = float(n)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(v) or math.isinf(v):
        return "—"
    return f"{v * 100:.0f}%" if abs(v) <= 1.5 else f"{v:.0f}%"


def _per(n: object) -> str:
    if n is None or n == "":
        return "—"
    try:
        v = float(n)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(v) or math.isinf(v):
        return "—"
    return f"{v:.2f}"


def _tbl(headers: list[str], rows: list[list[str]]) -> str:
    h = "<table class='tbl'><thead><tr>" + "".join(f"<th>{_e(x)}</th>" for x in headers) + "</tr></thead><tbody>"
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return h + body + "</tbody></table>"


def _num0(n: object) -> float:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return v


def _grouped_bars(rows: list[dict], a_key: str, b_key: str) -> str:
    max_q = 0.0
    for r in rows:
        for k in (a_key, b_key):
            max_q = max(max_q, _num0(r.get(k)))
    if max_q <= 0:
        max_q = 1.0
    parts = []
    for r in rows:
        lab = r.get("category_label") or r.get("pms_category") or ""
        a = _num0(r.get(a_key))
        b = _num0(r.get(b_key))
        parts.append(
            f'<div class="bar-row bar-pair"><span class="bar-lab">{_e(lab)}</span>'
            f'<div class="mini-stack">'
            f'<div class="mini" title="ITUK {_per(a)}"><div class="bar-seg" style="width:{100*a/max_q:.1f}%;background:#c0552d"></div></div>'
            f'<div class="mini" title="UTI {_per(b)}"><div class="bar-seg" style="width:{100*b/max_q:.1f}%;background:#15233c"></div></div>'
            f"</div></div>"
        )
    return "".join(parts)


def build_html(payload: dict) -> str:
    s = payload.get("summary") or {}
    bvp = payload.get("bvp_genuine_integrity") or {}
    pms = payload.get("pms_compare") or []
    pms_fy = payload.get("pms_fy2026_ytd") or []
    spots = payload.get("spot_checks") or []
    overlap = (payload.get("pn_overlap") or [])[:20]
    fuel = s.get("fuel_filter_bvp_sellthrough_pct")
    fuel_s = f"{fuel:.0f}%" if isinstance(fuel, (int, float)) and not math.isnan(fuel) else "—"
    kpis = [
        (
            "ITUK per truck CY2025",
            _per(s.get("ituk_per_truck")),
            f"Dealer qty ÷ UIO { _fmt(s.get('ituk_uio')) } trucks (V19). Not raw volume vs UTI.",
        ),
        (
            "UTI per truck CY2025",
            _per(s.get("uti_per_truck")),
            f"Dealer qty ÷ UIO { _fmt(s.get('uti_uio')) } trucks (V19). Same calendar year as ITUK.",
        ),
        (
            "ITUK BVP mix CY2025",
            _pct(s.get("ituk_bvp_share")),
            "BVP share of dealer qty. Mix, not park size.",
        ),
        (
            "UTI BVP mix CY2025",
            _pct(s.get("uti_bvp_share")),
            "BVP share of dealer qty. Mix, not park size.",
        ),
        (
            "Fuel BVP sell-through",
            fuel_s,
            "UTI dealer BVP ÷ UTI billed BVP on fuel filters. CY2025 both sides.",
        ),
        (
            "FY2025 bill qty ITUK / UTI",
            f"{_fmt(s.get('ituk_fy2025_billing_qty'))} / {_fmt(s.get('uti_fy2025_billing_qty'))}",
            "ISZE FY Apr 2025–Mar 2026. Full 12 months of ISZE→DB billing.",
        ),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="val">{_e(v)}</div><div class="lbl">{_e(l)}</div><div class="tip">{_e(tip)}</div></div>'
        for l, v, tip in kpis
    )
    pms_bars = _grouped_bars(pms, "ituk_per_truck", "uti_per_truck")
    mix_bars = _grouped_bars(
        [r for r in pms if (r.get("ituk_total") or 0) or (r.get("uti_total") or 0)],
        "ituk_bvp_share",
        "uti_bvp_share",
    )
    fy_bars = _grouped_bars(pms_fy, "ituk_per_truck", "uti_per_truck") if pms_fy else "<p class='muted'>No Apr–Jun 2026 sell-out months.</p>"
    pms_tbl = _tbl(
        ["Category", "ITUK / truck", "UTI / truck", "ITUK BVP %", "UTI BVP %", "BVP ST%"],
        [
            [
                _e(r.get("category_label")),
                _per(r.get("ituk_per_truck")),
                _per(r.get("uti_per_truck")),
                _pct(r.get("ituk_bvp_share")),
                _pct(r.get("uti_bvp_share")),
                _pct(r.get("sellthrough_bvp")),
            ]
            for r in pms
        ],
    )
    fy_tbl = _tbl(
        ["Category", "ITUK / truck", "UTI / truck", "ITUK BVP %", "UTI BVP %"],
        [
            [
                _e(r.get("category_label")),
                _per(r.get("ituk_per_truck")),
                _per(r.get("uti_per_truck")),
                _pct(r.get("ituk_bvp_share")),
                _pct(r.get("uti_bvp_share")),
            ]
            for r in pms_fy
        ],
    ) if pms_fy else ""
    spot_tbl = _tbl(
        ["PN", "Description", "Type", "Billing", "Dealer", "Cat.BVP", "Cat.DLR", "Note"],
        [
            [
                _e(r.get("part_number")),
                _e((r.get("description") or "")[:36]),
                (_e(r.get("line_type")) or "—") + (" ⚠" if r.get("line_type_ok") is False else ""),
                _fmt(r.get("uti_billing_qty")),
                _fmt(r.get("uti_dealer_ytd")),
                _e(r.get("catalog_paired_bvp") or "—"),
                _fmt(r.get("catalog_paired_dealer_ytd")),
                _e(r.get("pair_note") or ""),
            ]
            for r in spots
        ],
    )
    overlap_tbl = _tbl(
        ["PN", "Description", "ITUK / truck", "UTI / truck"],
        [
            [
                _e(r.get("part_number")),
                _e((r.get("description") or "")[:32]),
                _per((r.get("ituk_dealer_cy25") or 0) / (s.get("ituk_uio") or 1)),
                _per((r.get("uti_dealer_ytd") or 0) / (s.get("uti_uio") or 1)),
            ]
            for r in overlap
        ],
    )
    bvp_line = (
        f"BVP/genuine integrity (dimension vs crossref): {_e(bvp.get('status'))} — "
        f"xref mismatches: {bvp.get('xref_genuine_not_dimension_genuine') or 0} genuine, "
        f"{bvp.get('xref_bvp_not_dimension_bvp') or 0} bvp."
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Dealer sell-out · UTI vs ITUK (both CV) · per truck</title>
<style>
:root {{ --navy:#15233c; --terra:#c0552d; --paper:#f7f4ee; --ink:#222; --muted:#5a5a5a; --border:#d9d3c8; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",Calibri,sans-serif; background:var(--paper); color:var(--ink); }}
header {{ background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%); color:#f7f4ee; padding:1.4rem 2rem; }}
header h1 {{ margin:0.2rem 0; font-size:1.5rem; font-family:Georgia,serif; color:#fff; font-weight:400; }}
.badge {{ display:inline-block; margin-top:0.4rem; padding:0.2rem 0.55rem; background:rgba(0,0,0,0.25); border-radius:4px; font-size:0.72rem; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
section {{ background:#fff; border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; }}
section h2 {{ margin:0 0 0.6rem; font-size:1.02rem; font-family:Georgia,serif; color:var(--navy); border-bottom:3px solid var(--terra); padding-bottom:0.25rem; }}
.muted {{ color:var(--muted); font-size:0.85rem; }}
.kpi-row {{ display:flex; flex-wrap:wrap; gap:0.55rem; }}
.kpi {{ flex:1 1 160px; background:#fff; border-left:4px solid var(--terra); padding:0.6rem 0.8rem; border-radius:6px; position:relative; cursor:help; color:var(--ink); }}
.kpi .val {{ font-size:1.15rem; font-weight:700; color:var(--navy); }}
.kpi .lbl {{ font-size:0.72rem; color:var(--muted); }}
.kpi .tip {{ display:none; position:absolute; left:0; top:calc(100% + 6px); z-index:8; width:min(280px,70vw); background:#15233c; color:#f7f4ee; padding:10px 12px; font-size:12px; border-top:3px solid #c0552d; }}
.kpi:hover .tip {{ display:block; }}
.callout {{ padding:0.65rem 0.9rem; border-left:4px solid var(--terra); background:#fff; font-size:0.88rem; color:var(--ink); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
@media(max-width:800px){{ .grid2{{ grid-template-columns:1fr; }} }}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
.tbl th {{ background:#15233c; color:#f7f4ee; padding:0.4rem 0.5rem; text-align:left; }}
.tbl td {{ padding:0.35rem 0.5rem; border-bottom:1px solid var(--border); color:#222; }}
.bar-pair {{ display:flex; align-items:center; gap:8px; margin:8px 0; }}
.bar-lab {{ width:130px; font-size:12px; flex-shrink:0; color:#222; }}
.mini-stack {{ flex:1; }}
.mini {{ height:9px; background:#e8e4dc; margin:2px 0; border-radius:2px; overflow:hidden; display:flex; }}
.bar-seg {{ height:100%; }}
.legend {{ font-size:12px; margin-bottom:8px; color:#222; }}
.legend i {{ display:inline-block; width:10px; height:10px; margin:0 4px 0 10px; }}
footer {{ text-align:center; color:var(--muted); font-size:0.75rem; padding:1rem; }}
</style>
</head>
<body>
<header>
  <div style="font-weight:800;font-size:0.8rem;letter-spacing:0.08em;opacity:0.9">ISZE · Dealer sell-out</div>
  <h1>UTI vs ITUK — per truck, not raw qty (both CV)</h1>
  <p style="max-width:48rem;opacity:0.95">Parc is different. Compare intensity (qty ÷ UIO) and BVP mix. CY2025 is Jan–Dec on both sides.</p>
  <span class="badge">Generated {payload.get("generated")}</span>
</header>
<div class="wrap">
  <p class="muted">{_e(payload.get("scope_note"))}</p>
  <div class="callout">{bvp_line}</div>
  <section><h2>CY2025 — apples (Jan–Dec both) · per truck</h2><div class="kpi-row">{kpi_html}</div></section>
  <div class="grid2">
    <section><h2>PMS sell-out per truck</h2>
      <p class="muted">Grouped bars, same scale. Terracotta = ITUK · Navy = UTI. CY2025.</p>
      <div class="legend"><i style="background:#c0552d"></i>ITUK / truck <i style="background:#15233c"></i>UTI / truck</div>
      {pms_bars}</section>
    <section><h2>BVP mix % by PMS</h2>
      <p class="muted">Share of that category that is BVP. Independent of park size.</p>
      <div class="legend"><i style="background:#c0552d"></i>ITUK BVP % <i style="background:#15233c"></i>UTI BVP %</div>
      {mix_bars}</section>
  </div>
  <section><h2>PMS per truck + BVP mix</h2>{pms_tbl}</section>
  <section><h2>Fiscal years (ISZE FY = Apr–Mar)</h2>
    <p class="muted">FY2025 billing is complete (Apr 2025–Mar 2026). ITUK FY2025 sell-out uses dealer Apr–Dec 2025 plus Duncan Jan–Mar 2026. UTI FY2025 sell-out is <strong>not</strong> shown as a full year — Apr–Jul 2025 monthly files are missing and not invented. FY2026 YTD below is Apr–Jun 2026 (3 of 12) on both networks.</p>
    <div class="kpi-row">
      <div class="kpi"><div class="val">{_fmt(s.get("ituk_fy2025_billing_qty"))}</div><div class="lbl">ITUK FY2025 bill qty</div><div class="tip">ISZE→ITUK billed qty Apr 2025–Mar 2026. Full year.</div></div>
      <div class="kpi"><div class="val">{_fmt(s.get("uti_fy2025_billing_qty"))}</div><div class="lbl">UTI FY2025 bill qty</div><div class="tip">ISZE→UTI billed qty Apr 2025–Mar 2026. Full year.</div></div>
      <div class="kpi"><div class="val">{_fmt(s.get("ituk_fy2025_sellout_qty"))}</div><div class="lbl">ITUK FY2025 sell-out qty</div><div class="tip">Dealer Apr–Dec 2025 + Duncan network Jan–Mar 2026. Grain mix on Q1.</div></div>
      <div class="kpi"><div class="val">incomplete</div><div class="lbl">UTI FY2025 sell-out</div><div class="tip">Missing Apr–Jul 2025. Have Aug–Dec 2025 + Jan–Mar 2026 only ({_fmt(s.get("uti_fy2025_sellout_qty_incomplete"))} qty in those months). Not a full-year number.</div></div>
      <div class="kpi"><div class="val">{_per((s.get("ituk_fy2026_ytd_sellout_qty") or 0)/(s.get("ituk_uio") or 1))}</div><div class="lbl">ITUK FY2026 YTD / truck</div><div class="tip">Apr–Jun 2026 Duncan network ÷ UIO. 3 of 12 months.</div></div>
      <div class="kpi"><div class="val">{_per((s.get("uti_fy2026_ytd_sellout_qty") or 0)/(s.get("uti_uio") or 1))}</div><div class="lbl">UTI FY2026 YTD / truck</div><div class="tip">Apr–Jun 2026 PartSales months ÷ UIO. 3 of 12 months.</div></div>
    </div>
  </section>
  <section><h2>FY2026 YTD sell-out per truck (Apr–Jun 2026)</h2>
    <p class="muted">Same three months on both sides. Partial fiscal year.</p>
    {fy_bars}{fy_tbl}
  </section>
  <section><h2>Spot checks (description + catalog pair)</h2>{spot_tbl}</section>
  <section><h2>Same PN — demand per truck</h2>{overlap_tbl}</section>
</div>
<footer>See 01_data/12_raw/dealer_sales/ITUK/SOURCE.md</footer>
</body>
</html>"""


def main() -> int:
    payload = _json_clean(build_payload())
    DASH_JSON.parent.mkdir(parents=True, exist_ok=True)
    DASH_JSON.write_text(
        json.dumps(payload, indent=2, default=_json_safe, allow_nan=False),
        encoding="utf-8",
    )
    DASH_HTML.write_text(build_html(payload), encoding="utf-8")
    cmd = DASH_HTML.with_name("OPEN_Dealer_Sellout_UTI_vs_ITUK.cmd")
    cmd.write_text(
        '@echo off\r\nstart "" "%~dp0Dealer_Sellout_UTI_vs_ITUK.html"\r\n',
        encoding="utf-8",
    )
    print(f"Wrote {DASH_JSON}")
    print(f"Wrote {DASH_HTML}")
    print(f"BVP integrity: {payload['bvp_genuine_integrity']}")
    print(f"Summary: {json.dumps(payload['summary'], indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
