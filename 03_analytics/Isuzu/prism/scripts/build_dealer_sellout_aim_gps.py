#!/usr/bin/env python3
"""
DB→DLR sales to dealer (second layer): network AIM + GPS-style proxy for every wired DB.

Native loaders: ITUK (dealer pivot), UTI (PartSales YTD).
Canonical long CSVs: any `dealer_sellout_long_<DB>_CY{year}.csv` (IRELAND, IUK, GREECE, …).

Sales-to-dealer files are qty-only. "ISZE-denominated value" = qty × median CY ISZE→DB unit
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
    ISZE_ROOT,
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
DIST_ORDER = ("ITUK", "UTI", "IRELAND", "IUK", "GREECE")
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
    """Format ISZE-denominated proxy (€ scale from billing ASP, not dealer invoice)."""
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
    kpi_items = []
    for dist in dists:
        bb = b_by.get(dist) or {}
        kpi_items.append((f"{dist} sales to dealer qty", _fmt(bb.get("qty"))))
        kpi_items.append((f"{dist} BVP % of proxy", _pct(bb.get("bvp_pct"))))
    kpis = "".join(
        f'<div class="kpi"><div class="val">{_e(v)}</div><div class="lbl">{_e(l)}</div></div>'
        for l, v in kpi_items
    )

    chart_json = json.dumps(
        _clean_nans(
            {
                "aim_mix": mix,
                "pms_compare": payload.get("pms_compare", [])[:12],
                "distributors": list(dists),
            }
        ),
        allow_nan=False,
    )
    dist_label = " · ".join(dists)

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Sales to dealer · mix · CY{YEAR}</title>
<script>/*INLINE_CHART_JS*/</script>
<style>
:root {{ --red:#CC0E1E; --bg:#f4f5f7; --card:#fff; --text:#1a1a1a; --muted:#5a5a5a; --border:#e4e4e7; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",Calibri,sans-serif; background:var(--bg); color:var(--text); }}
header {{ background:linear-gradient(135deg,var(--red),#9a0b17); color:#fff; padding:1.4rem 2rem; }}
header h1 {{ margin:0.2rem 0; font-size:1.45rem; }}
.badge {{ display:inline-block; margin-top:0.4rem; padding:0.2rem 0.55rem; background:rgba(0,0,0,0.25); border-radius:4px; font-size:0.72rem; }}
.wrap {{ max-width:1400px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
section {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; overflow-x:auto; }}
section h2 {{ margin:0 0 0.6rem; font-size:1.02rem; color:var(--red); border-bottom:3px solid var(--red); padding-bottom:0.25rem; }}
section h3 {{ font-size:0.9rem; margin:0.5rem 0; color:var(--muted); }}
.callout {{ padding:0.65rem 0.9rem; border-left:4px solid var(--red); background:#fff8f8; font-size:0.88rem; margin-bottom:1rem; }}
.kpi-row {{ display:flex; flex-wrap:wrap; gap:0.55rem; }}
.kpi {{ flex:1 1 140px; background:var(--bg); border-left:4px solid var(--red); padding:0.6rem 0.8rem; border-radius:6px; }}
.kpi .val {{ font-size:1.05rem; font-weight:700; }}
.kpi .lbl {{ font-size:0.72rem; color:var(--muted); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
.gridN {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1rem; }}
@media(max-width:900px){{ .grid2{{ grid-template-columns:1fr; }} }}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.74rem; }}
.tbl th {{ background:var(--red); color:#fff; padding:0.35rem 0.45rem; text-align:left; white-space:nowrap; }}
.tbl td {{ padding:0.3rem 0.45rem; border-bottom:1px solid var(--border); }}
.tbl tr.bill td {{ background:#f0f4ff; }}
.muted {{ color:var(--muted); font-size:0.85rem; }}
</style>
</head>
<body>
<header>
  <div style="font-weight:800;font-size:0.8rem;letter-spacing:0.08em;opacity:0.9">ISZE · billed vs sales to dealer · mix / GPS proxy</div>
  <h1>BVP &amp; genuine — sales to dealer — {_e(dist_label)} (CY{YEAR})</h1>
  <span class="badge">Generated {payload.get("generated", "")}</span>
</header>
<div class="wrap">
  <div class="callout">{_e(payload.get("scope_note", ""))}<br/><strong>{_e(proxy_note)}</strong></div>
  <section><h2>Network summary</h2><div class="kpi-row">{kpis}</div></section>
  <div class="grid2">
    <section><h2>AIM mix by network</h2><canvas id="chartMix" height="260"></canvas></section>
    <section><h2>PMS — BVP qty (sales to dealer)</h2><canvas id="chartPms" height="260"></canvas></section>
  </div>
  <section><h2>AIM comparison (sales to dealer qty vs billed, ISZE-denom. proxy)</h2>
    <p class="muted">We billed vs their sales to dealer. Difference is stock movement (year total only — do not add the months). IUK is pickup, ITUK is truck, Ireland is Ireland. BVP / genuine % on sales-to-dealer rows use the ISZE billed unit price as a mix proxy, not their invoice.</p>
    {_tbl(["Network","Layer","Qty (reported)","ISZE-denom. / invoice","BVP %","Contested gen. %","Genuine-only %","BVP capture","Per truck"],
          [[_e(r["label"]),_e(r["layer"]),_fmt(r.get("qty_year")),
            _isze_denom(r.get("total_eur")) if r.get("layer")=="sellout_db_dlr" else _invoice_eur(r.get("total_eur")),
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
<script type="application/json" id="chart-data">{chart_json}</script>
<script>
function initCharts() {{
  if (typeof Chart === 'undefined') return;
  const D = JSON.parse(document.getElementById('chart-data').textContent);
  const mix = D.aim_mix || [];
  const sell = mix.filter(r => r.layer === 'sellout_db_dlr');
  const dists = D.distributors || sell.map(r => r.distributor_code);
  const palette = ['#CC0E1E','#9a0b17','#b45309','#1d4ed8','#0f766e','#7c3aed','#be123c'];
  new Chart(document.getElementById('chartMix'), {{
    type: 'bar',
    data: {{
      labels: sell.map(r => r.distributor_code),
      datasets: [
        {{ label: 'BVP %', data: sell.map(r => (r.bvp_pct||0)*100), backgroundColor: '#CC0E1E' }},
        {{ label: 'Contested genuine %', data: sell.map(r => (r.genuine_contested_pct||0)*100), backgroundColor: '#64748b' }},
        {{ label: 'Genuine-only %', data: sell.map(r => (r.genuine_only_pct||0)*100), backgroundColor: '#cbd5e1' }},
      ],
    }},
    options: {{ responsive: true, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, max: 100 }} }} }},
  }});
  const pms = D.pms_compare || [];
  new Chart(document.getElementById('chartPms'), {{
    type: 'bar',
    data: {{
      labels: pms.map(r => r.category_label || r.pms_category),
      datasets: dists.map((d, i) => ({{
        label: d + ' BVP',
        data: pms.map(r => r[d + '_sellout_db_dlr_bvp_qty'] || 0),
        backgroundColor: palette[i % palette.length],
      }})),
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }},
  }});
}}
document.addEventListener('DOMContentLoaded', initCharts);
window.addEventListener('load', initCharts);
</script>
</body>
</html>"""
    chart_path = ISZE_ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
    chart_js = chart_path.read_text(encoding="utf-8")
    return html_out.replace("/*INLINE_CHART_JS*/", chart_js)


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
            print(f"warn: no sales-to-dealer rows for {dist}")
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
            aim_summary(sell, f"{dist} sales to dealer", dist, "sellout_db_dlr")
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
            f"Billed vs sales to dealer, calendar {YEAR}. Networks: {', '.join(DISTS)}. "
            "ITUK from their dealer file. UTI from PartSales. "
            "Ireland / IUK / Greece from the year-total sales-to-dealer file (months are not added). "
            "IUK is pickup, ITUK is truck, Ireland is Ireland. Mix buckets: BVP / genuine with a BVP alt / genuine only."
        ),
        "valuation_note": (
            "Sales to dealer is pieces only. Euro on that layer is pieces × our billed unit price for that distributor and part — a mix proxy, not their invoice. "
            "Difference vs what we billed is stock movement. Parts with no billed price keep the pieces and show €0 on the proxy. "
            "Billed rows use the invoice euro."
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

    print(f"ok: {OUT_HTML}")
    print(f"ok: {OUT_JSON}")
    print(f"ok: {OUT_MIX} ({len(mix_rows)} mix rows)")
    print(f"ok: {OUT_ENTITY_MIX} ({len(entity_mix)} entities)")
    print(f"ok: {OUT_ENTITY_GPS}")


if __name__ == "__main__":
    main()
