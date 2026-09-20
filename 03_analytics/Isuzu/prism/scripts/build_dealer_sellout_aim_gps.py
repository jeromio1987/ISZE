#!/usr/bin/env python3
"""
DB→DLR sell-out (second layer): network AIM + GPS-style proxy for every wired DB.

Native loaders: ITUK (dealer pivot), UTI (PartSales YTD).
Canonical long CSVs: any `dealer_sellout_long_<DB>_CY{year}.csv` (IRELAND, IUK, GREECE, …).

Sell-out files are qty-only. "ISZE-denominated value" = qty × median CY ISZE→DB unit
price for that distributor×PN — a proxy for mix/GPS-style views, NOT dealer invoice EUR.
"""
from __future__ import annotations

import html
import json
import math
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import (  # noqa: E402
    DASHBOARDS_DIR,
    DASHBOARDS_JSON_DIR,
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    GPS_SPU_BY_DB_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import (  # noqa: E402
    UTI_DIR,
    aggregate_pn,
    discover_sellout_long_dists,
    load_ituk_dealer_sales,
    load_sellout_long_pn,
    load_uti_part_sales,
    normalize_pn,
)
from modules.aim_pn_classifier import FILTER_SUBGROUPS, filter_subgroup_label  # noqa: E402
from modules.bvp_product_nav import subgroup_label  # noqa: E402
from modules.dealer_sellout_analytics import attach_pn_master, load_dimension_and_xref  # noqa: E402


def _report_subgroup_label(code: object, role: object = None) -> str:
    if code is None or (isinstance(code, float) and pd.isna(code)):
        return "(unclassified)"
    s = str(code).strip()
    if s == "(unclassified)":
        return s
    if s.startswith("pr00_"):
        return s[5:].replace("_", " ").title()
    if s.endswith("_asm"):
        return filter_subgroup_label(s.replace("_asm", ""), "assembly")
    if s.endswith("_kit"):
        return filter_subgroup_label(s.replace("_kit", ""), "kit")
    base = s.replace("_asm", "").replace("_kit", "")
    if base in FILTER_SUBGROUPS:
        return filter_subgroup_label(base, role or "element")
    return subgroup_label(s)


def _aim_l1_label(code: object) -> str:
    if code is None or (isinstance(code, float) and pd.isna(code)):
        return "(unclassified)"
    return str(code).strip()

YEAR = 2025
# Native Excel loaders always included; long-CSV DBs auto-discovered and merged.
NATIVE_DISTS = ("ITUK", "UTI")
# Display / sort order when present (others append alphabetically).
DIST_ORDER = ("ITUK", "UTI", "IRELAND", "IUK", "GREECE", "PORTUGAL", "ROMANIA")
CHANNEL = {
    "ITUK": "CV trucks",
    "UTI": "CV trucks",
    "IUK": "LCV pickups",
    "IRELAND": "CV+LCV",
    "GREECE": "CV+LCV",
    "PORTUGAL": "CV+LCV",
    "ROMANIA": "LCV pickups",
}
# ITUK DVLA / UTI fallback if GPS row missing; others from gps_spu_by_distributor.
UIO_FALLBACK = {"ITUK": 22_389.0, "UTI": 10_668.0}

OUT_MIX = DERIVED_DIR / f"sellout_aim_network_mix_{YEAR}.csv"
OUT_PMS = DERIVED_DIR / f"sellout_aim_by_pms_{YEAR}.csv"
OUT_SUB = DERIVED_DIR / f"sellout_aim_by_subgroup_{YEAR}.csv"
OUT_AIM_L1 = DERIVED_DIR / f"sellout_aim_by_aim_l1_{YEAR}.csv"
OUT_TOP = DERIVED_DIR / f"sellout_aim_top_pn_{YEAR}.csv"
OUT_ENTITY_MIX = DERIVED_DIR / f"dealer_sellout_aim_mix_{YEAR}.csv"
OUT_ENTITY_GPS = DERIVED_DIR / f"dealer_sellout_gps_{YEAR}.csv"
OUT_JSON = DASHBOARDS_JSON_DIR / "dealer_sellout_aim_gps.json"
# Keep stable path (hub links); content is multi-DB second layer.
OUT_HTML = DASHBOARDS_DIR / "sales" / "Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"
BILL_MIX = DERIVED_DIR / "db_parts_mix_classification.csv"

# Filled in main() after discovery.
DISTS: tuple[str, ...] = NATIVE_DISTS
UIO: dict[str, float] = dict(UIO_FALLBACK)


def resolve_dists() -> tuple[str, ...]:
    long_dists = discover_sellout_long_dists(DERIVED_DIR, YEAR)
    ordered = [d for d in DIST_ORDER if d in NATIVE_DISTS or d in long_dists]
    for d in sorted(set(NATIVE_DISTS) | set(long_dists)):
        if d not in ordered:
            ordered.append(d)
    return tuple(ordered)


def load_uio_map(dists: tuple[str, ...]) -> dict[str, float]:
    out = {k: v for k, v in UIO_FALLBACK.items() if k in dists}
    if GPS_SPU_BY_DB_CSV.exists():
        gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
        sub = gps[(gps["year"] == YEAR) & (gps["distributor_code"].isin(dists))]
        for _, r in sub.iterrows():
            u = float(r["uio_units"]) if pd.notna(r["uio_units"]) else 0.0
            if u > 0:
                out[str(r["distributor_code"])] = u
    return out


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


def _clean_nans(obj: object) -> object:
    if isinstance(obj, dict):
        return {k: _clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_nans(x) for x in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


def _e(text: object) -> str:
    return html.escape(str(text) if text is not None else "")


def _fmt(n: object) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return f"{float(n):,.0f}"


def _pct(n: object) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return f"{float(n) * 100:.1f}%"


def _isze_denom(n: object) -> str:
    """Format ISZE-denominated proxy (€ scale from billing ASP, not dealer sell-out)."""
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return f"€{_fmt(n)}"


def _invoice_eur(n: object) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "—"
    return f"€{_fmt(n)}"


def load_asp() -> pd.DataFrame:
    if not SALES_FACT_PARQUET.exists():
        return pd.DataFrame(columns=["distributor_code", "part_number", "asp_eur"])
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[(sales["year"] == YEAR) & (sales["distributor_code"].isin(DISTS))].copy()
    if "line_kind" in s.columns:
        s = s[s["line_kind"] == "part"]
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    s = s[s["billed_qty"] > 0]
    s["asp_eur"] = s["net_sales_value"] / s["billed_qty"]
    s = s[s["asp_eur"] > 0]
    return (
        s.groupby(["distributor_code", "part_number"], as_index=False)["asp_eur"]
        .median()
    )


def load_billing_pn(dist: str, asp: pd.DataFrame) -> pd.DataFrame:
    if not SALES_FACT_PARQUET.exists():
        return pd.DataFrame(columns=["part_number", "qty_year", "valued_eur"])
    sales = pd.read_parquet(SALES_FACT_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[
        (sales["year"] == YEAR) & (sales["distributor_code"] == dist)
    ].copy()
    if "line_kind" in s.columns:
        s = s[s["line_kind"] == "part"]
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    g = s.groupby("part_number", as_index=False)["billed_qty"].sum()
    g = g.rename(columns={"billed_qty": "qty_year"})
    a = asp[asp["distributor_code"] == dist][["part_number", "asp_eur"]]
    g = g.merge(a, on="part_number", how="left")
    g["valued_eur"] = g["qty_year"] * g["asp_eur"].fillna(0)
    return g


def load_sellout_pn(dist: str) -> pd.DataFrame:
    """Prefer canonical long CSV when present; else native ITUK/UTI Excel loaders."""
    long_df = load_sellout_long_pn(dist, YEAR, DERIVED_DIR)
    if not long_df.empty:
        return long_df
    if dist == "ITUK":
        raw = load_ituk_dealer_sales(YEAR)
        if raw.empty:
            return pd.DataFrame(columns=["part_number", "qty_year"])
        return raw.groupby("part_number", as_index=False)["qty_year"].sum()
    if dist == "UTI":
        path = UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx"
        df, _ = load_uti_part_sales(path if path.exists() else None)
        if df.empty:
            return pd.DataFrame(columns=["part_number", "qty_year"])
        return aggregate_pn(df, "qty_ytd").rename(columns={"qty": "qty_year"})
    return pd.DataFrame(columns=["part_number", "qty_year"])


def classify_pn(
    pn_df: pd.DataFrame, genuine_pns: set[str], bvp_pns: set[str]
) -> pd.DataFrame:
    pn = pn_df["part_number"].astype(str)
    bucket = pd.Series("genuine_only", index=pn_df.index)
    bucket.loc[pn.isin(genuine_pns)] = "genuine_contested"
    bucket.loc[pn.isin(bvp_pns)] = "bvp"
    out = pn_df.copy()
    out["aim_bucket"] = bucket
    return out


def aim_summary(valued: pd.DataFrame, label: str, dist: str, layer: str) -> dict:
    g = valued.groupby("aim_bucket", as_index=False).agg(
        qty_year=("qty_year", "sum"),
        valued_eur=("valued_eur", "sum"),
    )
    buckets = {r["aim_bucket"]: r for _, r in g.iterrows()}
    bvp = float(buckets.get("bvp", {}).get("valued_eur", 0) or 0)
    gen_c = float(buckets.get("genuine_contested", {}).get("valued_eur", 0) or 0)
    gen_o = float(buckets.get("genuine_only", {}).get("valued_eur", 0) or 0)
    total = bvp + gen_c + gen_o
    qty = float(valued["qty_year"].sum())
    unval_qty = float(valued.loc[valued["asp_eur"].isna(), "qty_year"].sum()) if "asp_eur" in valued.columns else 0.0
    contested = bvp + gen_c
    return {
        "label": label,
        "distributor_code": dist,
        "layer": layer,
        "qty_year": qty,
        "total_eur": total,
        "bvp_eur": bvp,
        "genuine_contested_eur": gen_c,
        "genuine_only_eur": gen_o,
        "bvp_pct": bvp / total if total else None,
        "genuine_contested_pct": gen_c / total if total else None,
        "genuine_only_pct": gen_o / total if total else None,
        "contested_bvp_capture": bvp / contested if contested else None,
        "bvp_qty": float(
            valued.loc[valued["aim_bucket"] == "bvp", "qty_year"].sum()
        ),
        "genuine_qty": float(
            valued.loc[valued["aim_bucket"].isin(["genuine_contested", "genuine_only"]), "qty_year"].sum()
        ),
        "qty_without_isze_price_pct": unval_qty / qty if qty else None,
        "proxy_spend_per_truck": (
            total / UIO[dist]
            if layer == "sellout_db_dlr" and dist in UIO and UIO[dist]
            else None
        ),
        "sellout_spu_eur": (
            total / UIO[dist]
            if layer == "sellout_db_dlr" and dist in UIO and UIO[dist]
            else None
        ),
        "uio_units": UIO.get(dist),
    }


def breakdown_table(
    valued: pd.DataFrame, group_col: str, dist: str, layer: str
) -> pd.DataFrame:
    v = valued.copy()
    v[group_col] = v[group_col].fillna("(unclassified)").replace("", "(unclassified)")
    rows = []
    for key, grp in v.groupby(group_col):
        for bucket in ("bvp", "genuine_contested", "genuine_only"):
            sub = grp[grp["aim_bucket"] == bucket]
            rows.append(
                {
                    "distributor_code": dist,
                    "layer": layer,
                    group_col: key,
                    "aim_bucket": bucket,
                    "qty": float(sub["qty_year"].sum()),
                    "eur": float(sub["valued_eur"].sum()),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    tot = out.groupby([group_col, "distributor_code", "layer"], as_index=False).agg(
        qty_total=("qty", "sum"),
        eur_total=("eur", "sum"),
    )
    out = out.merge(tot, on=[group_col, "distributor_code", "layer"])
    out["qty_share"] = out["qty"] / out["qty_total"].where(out["qty_total"] > 0)
    out["eur_share"] = out["eur"] / out["eur_total"].where(out["eur_total"] > 0)
    return out


def pms_pivot(pms_long: pd.DataFrame) -> list[dict]:
    if pms_long.empty:
        return []
    wide = []
    for cat, grp in pms_long.groupby("pms_category"):
        row = {"pms_category": cat, "category_label": PMS_LABELS.get(cat, cat)}
        for _, r in grp.iterrows():
            key = f"{r['distributor_code']}_{r['layer']}_{r['aim_bucket']}"
            row[f"{key}_qty"] = r["qty"]
            row[f"{key}_eur"] = r["eur"]
        wide.append(row)
    out = []
    for row in wide:
        for dist in DISTS:
            so_bvp = row.get(f"{dist}_sellout_db_dlr_bvp_qty", 0) or 0
            so_gen = (
                (row.get(f"{dist}_sellout_db_dlr_genuine_contested_qty", 0) or 0)
                + (row.get(f"{dist}_sellout_db_dlr_genuine_only_qty", 0) or 0)
            )
            so_tot = so_bvp + so_gen
            row[f"{dist}_sellout_bvp_share"] = so_bvp / so_tot if so_tot else None
        ituk = row.get("ITUK_sellout_bvp_share")
        uti = row.get("UTI_sellout_bvp_share")
        row["uti_vs_ituk_bvp_share_pp"] = (
            (uti - ituk) * 100 if ituk is not None and uti is not None else None
        )
        out.append(row)

    def _sort_key(r: dict) -> float:
        return -sum(r.get(f"{d}_sellout_db_dlr_bvp_qty", 0) or 0 for d in DISTS)

    return sorted(out, key=_sort_key)


def top_pn_table(valued: pd.DataFrame, dist: str, bucket: str, n: int = 25) -> list[dict]:
    sub = valued[valued["aim_bucket"] == bucket].copy()
    sub = sub.sort_values("qty_year", ascending=False).head(n)
    cols = [
        "part_number",
        "description",
        "line_type",
        "pms_category",
        "product_subgroup",
        "aim_l1",
        "aim_l2",
        "filter_part_role",
        "report_subgroup",
        "fig_key",
        "taxonomy_source",
        "qty_year",
        "valued_eur",
    ]
    for c in cols:
        if c not in sub.columns:
            sub[c] = ""
    return sub[cols].to_dict(orient="records")


def _tbl(headers: list[str], rows: list[list[str]], row_class: str = "") -> str:
    h = "<table class='tbl'><tr>" + "".join(f"<th>{_e(x)}</th>" for x in headers) + "</tr>"
    body = ""
    for row in rows:
        cls = f" class='{_e(row_class)}'" if row_class else ""
        body += "<tr" + cls + ">" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    return h + body + "</table>"


def _mix_bars_html(mix: list[dict]) -> str:
    sell = [r for r in mix if r.get("layer") == "sellout_db_dlr"]
    parts = []
    for r in sell:
        dist = r.get("distributor_code") or ""
        bvp = (r.get("bvp_pct") or 0) * 100
        gc = (r.get("genuine_contested_pct") or 0) * 100
        go = (r.get("genuine_only_pct") or 0) * 100
        parts.append(
            f'<div class="bar-row"><span class="bar-lab">{_e(dist)}</span>'
            f'<div class="bar-track" title="BVP {bvp:.0f}% / contested genuine {gc:.0f}% / genuine-only {go:.0f}%">'
            f'<div class="bar-seg" style="width:{bvp:.1f}%;background:#c0552d"></div>'
            f'<div class="bar-seg" style="width:{gc:.1f}%;background:#5a6d86"></div>'
            f'<div class="bar-seg" style="width:{go:.1f}%;background:#d9d3c8"></div>'
            f"</div></div>"
        )
    return "".join(parts) or "<p class='muted'>No sales-to-dealer mix rows.</p>"


def _pms_bars_html(pms: list[dict], dists: tuple[str, ...]) -> str:
    rows = list(pms)[:12]
    max_q = 1.0
    for r in rows:
        for d in dists:
            max_q = max(max_q, float(r.get(f"{d}_sellout_db_dlr_bvp_qty") or 0))
    palette = ["#c0552d", "#15233c", "#2b4a78", "#8a6500", "#0f766e", "#7c3aed"]
    legend = "".join(
        f'<span class="leg"><i style="background:{palette[i % len(palette)]}"></i>{_e(d)}</span>'
        for i, d in enumerate(dists)
    )
    body = []
    for r in rows:
        lab = r.get("category_label") or r.get("pms_category") or ""
        segs = []
        for i, d in enumerate(dists):
            q = float(r.get(f"{d}_sellout_db_dlr_bvp_qty") or 0)
            w = 100.0 * q / max_q if max_q else 0
            segs.append(
                f'<div class="mini"><div class="bar-seg" style="width:{w:.1f}%;background:{palette[i % len(palette)]}"></div></div>'
            )
        body.append(
            f'<div class="bar-row pms"><span class="bar-lab">{_e(lab)}</span><div class="mini-stack">{"".join(segs)}</div></div>'
        )
    return f'<div class="legend">{legend}</div>' + "".join(body)


def build_html(payload: dict) -> str:
    mix = payload["aim_mix_comparison"]
    proxy_note = payload.get("valuation_note", "")
    dists = tuple(payload.get("distributors") or DISTS)

    # PMS: BVP qty + share per network (compact multi-DB)
    pms_headers = ["PMS category"]
    for dist in dists:
        pms_headers.extend([f"{dist} BVP qty", f"{dist} BVP share"])
    pms_rows = []
    for r in payload.get("pms_compare", []):
        row = [_e(r.get("category_label") or r.get("pms_category"))]
        for dist in dists:
            bvp_q = r.get(f"{dist}_sellout_db_dlr_bvp_qty")
            gen_q = (r.get(f"{dist}_sellout_db_dlr_genuine_contested_qty") or 0) + (
                r.get(f"{dist}_sellout_db_dlr_genuine_only_qty") or 0
            )
            # show BVP qty; share already on row
            _ = gen_q
            row.append(_fmt(bvp_q))
            row.append(_pct(r.get(f"{dist}_sellout_bvp_share")))
        pms_rows.append(row)
    pms_tbl = _tbl(pms_headers, pms_rows)

    sub_headers = ["Taxonomy bucket"] + [f"{d} proxy €" for d in dists] + [f"{d} BVP %" for d in dists]
    sub_rows = []
    for r in payload.get("subgroup_compare", [])[:30]:
        row = [_e(r.get("subgroup_label") or _report_subgroup_label(r.get("product_subgroup")))]
        for dist in dists:
            row.append(_isze_denom(r.get(f"{dist}_sellout_eur")))
        for dist in dists:
            row.append(_pct(r.get(f"{dist}_bvp_share")))
        sub_rows.append(row)
    sub_tbl = _tbl(sub_headers, sub_rows)

    aim_headers = ["AIM Category L1", "AIM L2 (mode)"]
    aim_headers += [f"{d} proxy €" for d in dists] + [f"{d} BVP %" for d in dists]
    aim_l1_rows = []
    for r in payload.get("aim_l1_compare", [])[:20]:
        row = [
            _e(r.get("aim_l1_label") or _aim_l1_label(r.get("aim_l1"))),
            _e(r.get("aim_l2") or "—"),
        ]
        for dist in dists:
            row.append(_isze_denom(r.get(f"{dist}_sellout_eur")))
        for dist in dists:
            row.append(_pct(r.get(f"{dist}_bvp_share")))
        aim_l1_rows.append(row)
    aim_l1_tbl = _tbl(aim_headers, aim_l1_rows)

    def top_tbl(side: dict, dist: str) -> str:
        rows = []
        for r in side.get(dist, [])[:15]:
            rows.append(
                [
                    _e(r.get("part_number")),
                    _e((r.get("description") or "")[:40]),
                    _e(r.get("pms_category") or "—"),
                    _fmt(r.get("qty_year")),
                    _isze_denom(r.get("valued_eur")),
                ]
            )
        return _tbl(
            ["PN", "Description", "PMS", "Qty", "ISZE-denom. (proxy)"],
            rows,
        )

    top_blocks = []
    for dist in dists:
        top_blocks.append(
            f"<div><h3>{_e(dist)} — top BVP</h3>{top_tbl(payload.get('top_bvp', {}), dist)}</div>"
        )
    bvp_top = "<div class='gridN'>" + "".join(top_blocks) + "</div>"

    gen_blocks = []
    for dist in dists:
        gen_blocks.append(
            f"<div><h3>{_e(dist)} — top contested genuine</h3>"
            f"{top_tbl(payload.get('top_genuine_contested', {}), dist)}</div>"
        )
    gen_top = "<div class='gridN'>" + "".join(gen_blocks) + "</div>"

    b_by = payload.get("benchmarks_by_dist") or {}
    uti_row = next((r for r in mix if r.get("distributor_code") == "UTI" and r.get("layer") == "sellout_db_dlr"), None)
    iuk_row = next((r for r in mix if r.get("distributor_code") == "IUK" and r.get("layer") == "sellout_db_dlr"), None)
    kpi_bits = []
    if uti_row and iuk_row:
        kpi_bits.append(
            (
                "UTI BVP capture (CV trucks)",
                _pct(uti_row.get("contested_bvp_capture")),
                "BVP qty as a share of BVP + contested genuine on UTI sales to dealer. UTI is trucks. Compare to IUK as a tendency only.",
            )
        )
        kpi_bits.append(
            (
                "IUK BVP capture (LCV pickups)",
                _pct(iuk_row.get("contested_bvp_capture")),
                "Same formula on IUK sales to dealer. IUK is D-Max pickups, not trucks. Not like-for-like with UTI.",
            )
        )
    for dist in dists:
        bb = b_by.get(dist) or {}
        kpi_bits.append(
            (
                f"{dist} sales-to-dealer qty",
                _fmt(bb.get("qty")),
                f"Reported dealer demand qty CY{YEAR}. ITUK is dealer×PN SSOT; Duncan network companion is a separate mix row.",
            )
        )
        kpi_bits.append(
            (
                f"{dist} BVP % of proxy",
                _pct(bb.get("bvp_pct")),
                "BVP share of ISZE-denominated proxy (qty × median ISZE→DB price). Not dealer invoice €.",
            )
        )
    kpis = "".join(
        f'<div class="kpi"><div class="val">{_e(v)}</div><div class="lbl">{_e(l)}</div><div class="tip">{_e(tip)}</div></div>'
        for l, v, tip in kpi_bits
    )
    mix_bars = _mix_bars_html(mix)
    pms_bars = _pms_bars_html(payload.get("pms_compare", []), dists)
    dist_label = " · ".join(dists)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Sales to dealer AIM · UTI CV vs IUK LCV · CY{YEAR}</title>
<style>
:root {{ --navy:#15233c; --terra:#c0552d; --paper:#f7f4ee; --ink:#222; --muted:#5a5a5a; --border:#d9d3c8; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",Calibri,sans-serif; background:var(--paper); color:var(--ink); }}
header {{ background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%); color:#f7f4ee; padding:1.4rem 2rem; }}
header h1 {{ margin:0.2rem 0; font-size:1.55rem; font-family:Georgia,serif; color:#fff; font-weight:400; }}
.badge {{ display:inline-block; margin-top:0.4rem; padding:0.2rem 0.55rem; background:rgba(0,0,0,0.25); border-radius:4px; font-size:0.72rem; }}
.wrap {{ max-width:1400px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
section {{ background:#fff; border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; overflow-x:auto; }}
section h2 {{ margin:0 0 0.6rem; font-size:1.02rem; font-family:Georgia,serif; color:var(--navy); border-bottom:3px solid var(--terra); padding-bottom:0.25rem; }}
section h3 {{ font-size:0.9rem; margin:0.5rem 0; color:var(--muted); }}
.callout {{ padding:0.65rem 0.9rem; border-left:4px solid var(--terra); background:#fff; font-size:0.88rem; margin-bottom:1rem; color:var(--ink); }}
.kpi-row {{ display:flex; flex-wrap:wrap; gap:0.55rem; }}
.kpi {{ flex:1 1 140px; background:#fff; border-left:4px solid var(--terra); padding:0.6rem 0.8rem; border-radius:6px; position:relative; cursor:help; color:var(--ink); }}
.kpi .val {{ font-size:1.05rem; font-weight:700; color:var(--navy); }}
.kpi .lbl {{ font-size:0.72rem; color:var(--muted); }}
.basis-strip {{ display:flex; flex-wrap:wrap; gap:8px 18px; margin:10px 0 14px; padding:10px 14px; background:#eef3f9; border-left:4px solid #c0552d; font-size:12px; line-height:1.45; color:#222; }}
.basis-strip b {{ color:#15233c; letter-spacing:.04em; text-transform:uppercase; font-size:10px; margin-right:4px; }}
.kpi .tip {{ display:none; position:absolute; left:0; top:calc(100% + 6px); z-index:8; width:min(280px,70vw); background:#15233c; color:#f7f4ee; padding:10px 12px; font-size:12px; border-top:3px solid #c0552d; }}
.kpi:hover .tip {{ display:block; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
.gridN {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1rem; }}
@media(max-width:900px){{ .grid2{{ grid-template-columns:1fr; }} }}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.74rem; }}
.tbl th {{ background:#15233c; color:#f7f4ee; padding:0.35rem 0.45rem; text-align:left; white-space:nowrap; }}
.tbl td {{ padding:0.3rem 0.45rem; border-bottom:1px solid var(--border); color:var(--ink); }}
.tbl tr.bill td {{ background:#eef3f9; color:#222; }}
.muted {{ color:var(--muted); font-size:0.85rem; }}
.bar-row {{ display:flex; align-items:center; gap:8px; margin:7px 0; }}
.bar-lab {{ width:110px; font-size:12px; flex-shrink:0; color:var(--ink); }}
.bar-track {{ flex:1; display:flex; height:22px; background:#e8e4dc; border-radius:3px; overflow:hidden; }}
.bar-seg {{ height:100%; }}
.legend {{ display:flex; flex-wrap:wrap; gap:10px; font-size:12px; margin-bottom:8px; color:var(--ink); }}
.legend i {{ display:inline-block; width:10px; height:10px; margin-right:4px; }}
.mini-stack {{ flex:1; }}
.mini {{ height:8px; background:#e8e4dc; margin:2px 0; border-radius:2px; overflow:hidden; display:flex; }}
.bar-row.pms .bar-lab {{ width:130px; }}
</style>
</head>
<body>
<header>
  <div style="font-weight:800;font-size:0.8rem;letter-spacing:0.08em;opacity:0.9">ISZE · DB→DLR · Second layer (sales to dealer · AIM / GPS)</div>
  <h1>Sales to dealer — {_e(dist_label)} (CY{YEAR})</h1>
  <p style="max-width:52rem;font-size:0.92rem;opacity:0.95">UTI CV vs IUK LCV is a <strong>tendency</strong>, not the same vehicle market. IUK is pickups. UTI and ITUK are trucks.</p>
  <span class="badge">Generated {payload.get("generated", "")}</span>
</header>
<div class="wrap">
  <div class="basis-strip"><div><b>Observed</b> Sales to dealer CY{YEAR}</div><div><b>Scope</b> Listed distributors only — stocking, not final customer demand</div><div><b>Entities</b> ITUK ≠ IUK · UTI ≠ UMI</div></div>
  <div class="callout"><b>Scope:</b> Sales-to-dealer files for the listed distributors only — distributor stocking, not final customer demand. ITUK ≠ IUK. UTI ≠ UMI.<br/>{_e(payload.get("scope_note", ""))}<br/><strong>{_e(proxy_note)}</strong></div>
  <section><h2>Observed distributor subset — summary</h2><div class="kpi-row">{kpis}</div></section>
  <div class="grid2">
    <section><h2>AIM mix by distributor (observed subset)</h2>
      <div class="legend"><span class="leg"><i style="background:#c0552d"></i>BVP</span><span class="leg"><i style="background:#5a6d86"></i>Contested genuine</span><span class="leg"><i style="background:#d9d3c8"></i>Genuine-only</span></div>
      {mix_bars}</section>
    <section><h2>PMS — BVP qty (sales to dealer)</h2>{pms_bars}</section>
  </div>
  <section><h2>AIM comparison (sales-to-dealer qty vs ISZE-denom. proxy vs billing)</h2>
    <p class="muted">Observed subset (not the full ISZE network). ITUK dealer file is the SSOT. Duncan 4 Sep 2026 file is the network companion (Customer Name=All, thru Aug 2026). IUK / IRELAND / GREECE from canonical long CSVs. Never blend IUK↔ITUK or IRELAND↔IUK. BVP / genuine % on sell-out rows use ISZE-denominated proxy only.</p>
    {_tbl(["Distributor","Layer","Qty (reported)","ISZE-denom. / invoice","BVP %","Contested gen. %","Genuine-only %","BVP capture","Per vehicle"],
          [[_e(r["label"]),_e(r["layer"]),_fmt(r.get("qty_year")),
            _isze_denom(r.get("total_eur")) if r.get("layer") in ("sellout_db_dlr","sellout_duncan_network") else _invoice_eur(r.get("total_eur")),
            _pct(r.get("bvp_pct")),_pct(r.get("genuine_contested_pct")),_pct(r.get("genuine_only_pct")),
            _pct(r.get("contested_bvp_capture")),
            (_isze_denom(r.get("proxy_spend_per_truck"))+" proxy") if r.get("layer")=="sellout_db_dlr" else (_invoice_eur(r.get("billing_gps"))+" GPS invoice") if r.get("billing_gps") else "—"]
           for r in mix], "")}
  </section>
  <section><h2>What they order — PMS (catalog taxonomy)</h2>{pms_tbl}</section>
  <section><h2>What they order — taxonomy (PMS subgroup + PR00 family, top 30)</h2>{sub_tbl}</section>
  <section><h2>What they order — AIM Category L1 / L2 (workbook taxonomy, top 20)</h2>{aim_l1_tbl}</section>
  <section><h2>Top parts — BVP line</h2>{bvp_top}</section>
  <section><h2>Top parts — contested genuine</h2>{gen_top}</section>
</div>
<footer class="muted" style="text-align:center;padding:1rem;font-size:0.75rem">
  Rebuild: prism/scripts/build_dealer_sellout_aim_gps.py · 01_data/00_derived/sellout_aim_* · second layer
</footer>
</body>
</html>"""


def _entity_rows_from_network(mix_rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Network aggregate rows for dealer_sellout_aim_mix / gps (second-layer entity files)."""
    rows = []
    for r in mix_rows:
        if r.get("layer") != "sellout_db_dlr":
            continue
        dist = r["distributor_code"]
        entity = f"{dist} (network aggregate)"
        rows.append(
            {
                "entity": entity,
                "bvp_eur": r.get("bvp_eur"),
                "genuine_contested_eur": r.get("genuine_contested_eur"),
                "genuine_only_eur": r.get("genuine_only_eur"),
                "total_eur": r.get("total_eur"),
                "bvp_pct": r.get("bvp_pct"),
                "genuine_contested_pct": r.get("genuine_contested_pct"),
                "genuine_only_pct": r.get("genuine_only_pct"),
                "contested_bvp_capture": r.get("contested_bvp_capture"),
                "distributor_code": dist,
                "layer": "sellout_db_dlr",
                "year": YEAR,
                "qty_year": r.get("qty_year"),
                "qty_unvalued_share": r.get("qty_without_isze_price_pct"),
            }
        )
    mix_df = pd.DataFrame(rows)
    gps_df = mix_df.copy()
    if not gps_df.empty:
        gps_df["uio_units"] = gps_df["distributor_code"].map(UIO)
        gps_df["sellout_spu_eur"] = gps_df.apply(
            lambda x: (x["total_eur"] / x["uio_units"])
            if x.get("uio_units") and x["uio_units"]
            else None,
            axis=1,
        )
        gps_df["sellout_qty"] = gps_df["qty_year"]
        gps_df["share_of_network"] = 1.0
    return mix_df, gps_df


def _ituk_dealer_entity_rows(
    asp: pd.DataFrame,
    dim: pd.DataFrame,
    desc: pd.DataFrame,
    xref: pd.DataFrame,
    xref_g: set[str],
    xref_b: set[str],
) -> pd.DataFrame:
    """Rebuild ITUK dealer-grain AIM rows (keeps dealer grain in entity mix/gps)."""
    raw = load_ituk_dealer_sales(YEAR)
    if raw.empty:
        return pd.DataFrame()
    deal = attach_pn_master(raw, dim, desc, xref)
    deal = classify_pn(deal, xref_g, xref_b)
    a = asp[asp["distributor_code"] == "ITUK"][["part_number", "asp_eur"]]
    deal = deal.merge(a, on="part_number", how="left")
    deal["valued_eur"] = deal["qty_year"] * deal["asp_eur"].fillna(0)
    rows = []
    for dealer, grp in deal.groupby("dealer_name"):
        s = aim_summary(grp, str(dealer), "ITUK", "sellout_db_dlr")
        rows.append(
            {
                "entity": str(dealer),
                "bvp_eur": s["bvp_eur"],
                "genuine_contested_eur": s["genuine_contested_eur"],
                "genuine_only_eur": s["genuine_only_eur"],
                "total_eur": s["total_eur"],
                "bvp_pct": s["bvp_pct"],
                "genuine_contested_pct": s["genuine_contested_pct"],
                "genuine_only_pct": s["genuine_only_pct"],
                "contested_bvp_capture": s["contested_bvp_capture"],
                "distributor_code": "ITUK",
                "layer": "sellout_db_dlr",
                "year": YEAR,
                "qty_year": s["qty_year"],
                "qty_unvalued_share": s.get("qty_without_isze_price_pct"),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    global DISTS, UIO

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    DISTS = resolve_dists()
    UIO = load_uio_map(DISTS)
    print(f"dists: {DISTS}")
    print(f"uio: {UIO}")

    dim, xref, desc = load_dimension_and_xref()
    xref_g = set(xref["genuine_pn"].dropna().str.strip())
    xref_b = set(xref["bvp_pn"].dropna().str.strip())
    asp = load_asp()

    mix_rows: list[dict] = []
    pms_parts: list[pd.DataFrame] = []
    sub_parts: list[pd.DataFrame] = []
    aim_l1_parts: list[pd.DataFrame] = []
    top_bvp: dict[str, list] = {}
    top_gen: dict[str, list] = {}
    valued_by_dist: dict[str, pd.DataFrame] = {}

    for dist in DISTS:
        sell = load_sellout_pn(dist)
        if sell.empty:
            print(f"warn: no sell-out rows for {dist}")
            continue
        sell = attach_pn_master(sell, dim, desc, xref)
        sell["aim_l1_report"] = (
            sell["aim_l1"]
            .fillna(sell.get("catalog_l1"))
            .fillna("(unclassified)")
            .replace("", "(unclassified)")
        )
        sell = classify_pn(sell, xref_g, xref_b)
        a = asp[asp["distributor_code"] == dist][["part_number", "asp_eur"]]
        sell = sell.merge(a, on="part_number", how="left")
        sell["valued_eur"] = sell["qty_year"] * sell["asp_eur"].fillna(0)
        valued_by_dist[dist] = sell

        mix_rows.append(
            aim_summary(
                sell,
                f"{dist} sell-out ({CHANNEL.get(dist, 'network')})",
                dist,
                "sellout_db_dlr",
            )
        )

        bill = load_billing_pn(dist, asp)
        bill = attach_pn_master(bill, dim, desc, xref)
        bill = classify_pn(bill, xref_g, xref_b)
        bill["valued_eur"] = bill["qty_year"] * bill["asp_eur"].fillna(0)
        mix_rows.append(
            aim_summary(bill, f"{dist} billing (ISZE→DB)", dist, "billing_isze_db")
        )

        pms_parts.append(breakdown_table(sell, "pms_category", dist, "sellout_db_dlr"))
        sub_parts.append(breakdown_table(sell, "report_subgroup", dist, "sellout_db_dlr"))
        aim_l1_parts.append(breakdown_table(sell, "aim_l1_report", dist, "sellout_db_dlr"))
        top_bvp[dist] = top_pn_table(sell, dist, "bvp")
        top_gen[dist] = top_pn_table(sell, dist, "genuine_contested")

    net_path = DERIVED_DIR / f"dealer_sellout_long_ITUK_network_CY{YEAR}.csv"
    if net_path.exists():
        raw = pd.read_csv(net_path, dtype={"part_number": str}, low_memory=False)
        if "period_grain" in raw.columns:
            year_only = raw[raw["period_grain"].astype(str).str.lower() == "year"]
            if not year_only.empty:
                raw = year_only
        companion = (
            raw.groupby("part_number", as_index=False)["qty"]
            .sum()
            .rename(columns={"qty": "qty_year"})
        )
        companion["part_number"] = companion["part_number"].map(normalize_pn)
        companion = companion.dropna(subset=["part_number"])
        if not companion.empty:
            companion = attach_pn_master(companion, dim, desc, xref)
            companion = classify_pn(companion, xref_g, xref_b)
            a = asp[asp["distributor_code"] == "ITUK"][["part_number", "asp_eur"]]
            companion = companion.merge(a, on="part_number", how="left")
            companion["valued_eur"] = companion["qty_year"] * companion["asp_eur"].fillna(0)
            mix_rows.append(
                aim_summary(
                    companion,
                    "ITUK Duncan network companion (All dealers, PN×month thru Aug)",
                    "ITUK",
                    "sellout_duncan_network",
                )
            )
            print(f"duncan companion PNs={len(companion)} qty={companion['qty_year'].sum():,.0f}")

    # Keep DISTS aligned to what actually produced sell-out rows
    present = tuple(
        d
        for d in DISTS
        if any(r["distributor_code"] == d and r["layer"] == "sellout_db_dlr" for r in mix_rows)
    )
    if present:
        DISTS = present

    if BILL_MIX.exists():
        bm = pd.read_csv(BILL_MIX)
        for dist in DISTS:
            sub = bm[(bm["year"] == YEAR) & (bm["distributor_code"] == dist)]
            if sub.empty:
                continue
            r = sub.iloc[0]
            for row in mix_rows:
                if row["distributor_code"] == dist and row["layer"] == "billing_isze_db":
                    row["total_eur"] = float(r["total_eur"])
                    row["bvp_pct"] = float(r["bvp_pct"])
                    row["genuine_contested_pct"] = float(r["genuine_contested_pct"])
                    row["genuine_only_pct"] = float(r["genuine_only_pct"])
                    row["contested_bvp_capture"] = float(r["contested_bvp_capture"])

    if GPS_SPU_BY_DB_CSV.exists():
        gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
        gps = gps[(gps["year"] == YEAR) & (gps["distributor_code"].isin(DISTS))]
        for _, g in gps.iterrows():
            for row in mix_rows:
                if (
                    row["distributor_code"] == g["distributor_code"]
                    and row["layer"] == "billing_isze_db"
                ):
                    if pd.notna(g.get("spend_per_unit_eur")):
                        row["billing_gps"] = float(g["spend_per_unit_eur"])

    pms_long = pd.concat(pms_parts, ignore_index=True) if pms_parts else pd.DataFrame()
    pms_cmp = pms_pivot(pms_long)
    pms_long.to_csv(OUT_PMS, index=False)

    sub_long = pd.concat(sub_parts, ignore_index=True) if sub_parts else pd.DataFrame()
    sub_cmp = []
    if not sub_long.empty:
        for sg, grp in sub_long.groupby("report_subgroup"):
            row = {
                "product_subgroup": sg,
                "subgroup_label": _report_subgroup_label(sg),
            }
            for dist in DISTS:
                s = grp[(grp["distributor_code"] == dist) & (grp["aim_bucket"] == "bvp")]
                t = grp[grp["distributor_code"] == dist]
                eur = float(t["eur"].sum())
                bvp_e = float(s["eur"].sum())
                row[f"{dist}_sellout_eur"] = eur
                row[f"{dist}_bvp_share"] = bvp_e / eur if eur else None
            sub_cmp.append(row)
        sub_cmp.sort(
            key=lambda r: -sum(r.get(f"{d}_sellout_eur") or 0 for d in DISTS)
        )
    sub_long.to_csv(OUT_SUB, index=False)

    aim_l1_cmp: list[dict] = []
    aim_l1_long = pd.concat(aim_l1_parts, ignore_index=True) if aim_l1_parts else pd.DataFrame()
    if not aim_l1_long.empty:
        for l1, grp in aim_l1_long.groupby("aim_l1_report"):
            row = {"aim_l1": l1, "aim_l1_label": _aim_l1_label(l1)}
            l2_vals = []
            for dist in DISTS:
                sub = grp[grp["distributor_code"] == dist]
                bvp = sub[sub["aim_bucket"] == "bvp"]
                eur = float(sub["eur"].sum())
                row[f"{dist}_sellout_eur"] = eur
                row[f"{dist}_bvp_share"] = float(bvp["eur"].sum()) / eur if eur else None
                pn_sub = valued_by_dist.get(dist)
                if pn_sub is not None and "aim_l2" in pn_sub.columns:
                    l2s = pn_sub.loc[pn_sub["aim_l1_report"] == l1, "aim_l2"].dropna()
                    if not l2s.empty:
                        l2_vals.append(l2s.mode().iloc[0])
            row["aim_l2"] = l2_vals[0] if l2_vals else None
            aim_l1_cmp.append(row)
        aim_l1_cmp.sort(
            key=lambda r: -sum(r.get(f"{d}_sellout_eur") or 0 for d in DISTS)
        )
    aim_l1_long.to_csv(OUT_AIM_L1, index=False)

    top_rows = []
    for dist in DISTS:
        for bucket, data in (("bvp", top_bvp.get(dist, [])), ("genuine_contested", top_gen.get(dist, []))):
            for r in data:
                top_rows.append({**r, "distributor_code": dist, "aim_bucket": bucket})
    pd.DataFrame(top_rows).to_csv(OUT_TOP, index=False)

    pd.DataFrame(mix_rows).to_csv(OUT_MIX, index=False)

    # Entity-level second-layer CSVs: ITUK dealers + network aggregates for all DBs
    ituk_dealers = _ituk_dealer_entity_rows(asp, dim, desc, xref, xref_g, xref_b)
    net_mix, net_gps = _entity_rows_from_network(mix_rows)
    # Prefer dealer rows for ITUK; keep network row for others (and UTI)
    if not ituk_dealers.empty:
        other_net = net_mix[net_mix["distributor_code"] != "ITUK"]
        entity_mix = pd.concat([ituk_dealers, other_net], ignore_index=True)
    else:
        entity_mix = net_mix
    entity_mix.to_csv(OUT_ENTITY_MIX, index=False)

    if not ituk_dealers.empty:
        ituk_gps = ituk_dealers.copy()
        uio_ituk = UIO.get("ITUK")
        ituk_gps["uio_units"] = uio_ituk
        ituk_gps["sellout_spu_eur"] = (
            ituk_gps["total_eur"] / uio_ituk if uio_ituk else None
        )
        ituk_gps["sellout_qty"] = ituk_gps["qty_year"]
        tot_q = float(ituk_gps["qty_year"].sum()) or 1.0
        ituk_gps["share_of_network"] = ituk_gps["qty_year"] / tot_q
        other_gps = net_gps[net_gps["distributor_code"] != "ITUK"]
        entity_gps = pd.concat([ituk_gps, other_gps], ignore_index=True)
    else:
        entity_gps = net_gps
    entity_gps.to_csv(OUT_ENTITY_GPS, index=False)

    benchmarks_by_dist = {}
    for dist in DISTS:
        so = next(
            (
                r
                for r in mix_rows
                if r["distributor_code"] == dist and r["layer"] == "sellout_db_dlr"
            ),
            None,
        )
        if so:
            benchmarks_by_dist[dist] = {
                "qty": so["qty_year"],
                "eur": so["total_eur"],
                "bvp_pct": so["bvp_pct"],
                "qty_no_price_pct": so.get("qty_without_isze_price_pct"),
                "sellout_spu_eur": so.get("sellout_spu_eur"),
                "uio_units": so.get("uio_units"),
            }

    # Legacy ITUK/UTI keys kept for any old consumers
    legacy = {}
    if "ITUK" in benchmarks_by_dist:
        legacy.update(
            {
                "ituk_qty": benchmarks_by_dist["ITUK"]["qty"],
                "ituk_eur": benchmarks_by_dist["ITUK"]["eur"],
                "ituk_bvp_pct": benchmarks_by_dist["ITUK"]["bvp_pct"],
                "ituk_qty_no_price_pct": benchmarks_by_dist["ITUK"]["qty_no_price_pct"],
            }
        )
    if "UTI" in benchmarks_by_dist:
        legacy.update(
            {
                "uti_qty": benchmarks_by_dist["UTI"]["qty"],
                "uti_eur": benchmarks_by_dist["UTI"]["eur"],
                "uti_bvp_pct": benchmarks_by_dist["UTI"]["bvp_pct"],
                "uti_qty_no_price_pct": benchmarks_by_dist["UTI"]["qty_no_price_pct"],
            }
        )

    payload = {
        "generated": str(date.today()),
        "distributors": list(DISTS),
        "uio_units": dict(UIO),
        "scope_note": (
            f"Second layer (DB→DLR) CY{YEAR}. Networks: {', '.join(DISTS)}. "
            "UTI is CV trucks. IUK is LCV pickups — BVP capture vs UTI is a tendency, not like-for-like trucks. "
            "ITUK dealer×PN SSOT plus Duncan network companion (PN×month thru Aug 2026, Customer Name=All). "
            "IUK ≠ ITUK; IRELAND ≠ IUK. AIM buckets: bvp | genuine_contested | genuine_only."
        ),
        "valuation_note": (
            "Sell-out reports are quantity only — no dealer EUR. ISZE-denominated value = "
            f"reported qty × median CY{YEAR} ISZE→DB unit price per PN (proxy for mix; not sell-out revenue). "
            "IUK is qty-only by design (no EUR chase). PNs with no billing price contribute qty but €0 to proxy totals. "
            "Billing rows use actual invoice EUR and GPS."
        ),
        "benchmarks": legacy,
        "benchmarks_by_dist": benchmarks_by_dist,
        "aim_mix_comparison": mix_rows,
        "pms_compare": pms_cmp,
        "subgroup_compare": sub_cmp,
        "aim_l1_compare": aim_l1_cmp,
        "top_bvp": top_bvp,
        "top_genuine_contested": top_gen,
    }

    OUT_JSON.write_text(
        json.dumps(_clean_nans(payload), indent=2, default=str), encoding="utf-8"
    )
    OUT_HTML.write_text(build_html(payload), encoding="utf-8")
    cmd = OUT_HTML.with_name("OPEN_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.cmd")
    cmd.write_text(
        '@echo off\r\nstart "" "%~dp0Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"\r\n',
        encoding="utf-8",
    )

    print(f"ok: {OUT_HTML}")
    print(f"ok: {OUT_JSON}")
    print(f"ok: {OUT_MIX} ({len(mix_rows)} mix rows)")
    print(f"ok: {OUT_ENTITY_MIX} ({len(entity_mix)} entities)")
    print(f"ok: {OUT_ENTITY_GPS}")


if __name__ == "__main__":
    main()
