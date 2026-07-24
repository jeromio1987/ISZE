#!/usr/bin/env python3
"""
DB→DLR sell-out: full AIM analysis ITUK vs UTI at network level (no dealer grain).

Sell-out files are qty-only. "ISZE-denominated value" = qty × median CY2025 ISZE→DB unit
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
    load_ituk_dealer_sales,
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
UIO = {"ITUK": 22_389.0, "UTI": 10_668.0}
DISTS = ("ITUK", "UTI")

OUT_MIX = DERIVED_DIR / "sellout_aim_network_mix_2025.csv"
OUT_PMS = DERIVED_DIR / "sellout_aim_by_pms_2025.csv"
OUT_SUB = DERIVED_DIR / "sellout_aim_by_subgroup_2025.csv"
OUT_AIM_L1 = DERIVED_DIR / "sellout_aim_by_aim_l1_2025.csv"
OUT_TOP = DERIVED_DIR / "sellout_aim_top_pn_2025.csv"
OUT_JSON = DASHBOARDS_JSON_DIR / "dealer_sellout_aim_gps.json"
OUT_HTML = DASHBOARDS_DIR / "sales" / "Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"
BILL_MIX = DERIVED_DIR / "db_parts_mix_classification.csv"

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
    if dist == "ITUK":
        raw = load_ituk_dealer_sales(YEAR)
        if raw.empty:
            return pd.DataFrame(columns=["part_number", "qty_year"])
        return raw.groupby("part_number", as_index=False)["qty_year"].sum()
    path = UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx"
    df, _ = load_uti_part_sales(path if path.exists() else None)
    if df.empty:
        return pd.DataFrame(columns=["part_number", "qty_year"])
    return aggregate_pn(df, "qty_ytd").rename(columns={"qty": "qty_year"})


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
        "proxy_spend_per_truck": total / UIO[dist] if layer == "sellout_db_dlr" and dist in UIO else None,
        "sellout_spu_eur": total / UIO[dist] if layer == "sellout_db_dlr" and dist in UIO else None,
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
    return sorted(out, key=lambda r: -(r.get("ITUK_sellout_db_dlr_bvp_qty", 0) or 0))


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

    pms_rows = []
    for r in payload.get("pms_compare", []):
        pms_rows.append(
            [
                _e(r.get("category_label") or r.get("pms_category")),
                _fmt(r.get("ITUK_sellout_db_dlr_bvp_qty")),
                _fmt(
                    (r.get("ITUK_sellout_db_dlr_genuine_contested_qty") or 0)
                    + (r.get("ITUK_sellout_db_dlr_genuine_only_qty") or 0)
                ),
                _pct(r.get("ITUK_sellout_bvp_share")),
                _fmt(r.get("UTI_sellout_db_dlr_bvp_qty")),
                _fmt(
                    (r.get("UTI_sellout_db_dlr_genuine_contested_qty") or 0)
                    + (r.get("UTI_sellout_db_dlr_genuine_only_qty") or 0)
                ),
                _pct(r.get("UTI_sellout_bvp_share")),
                f"{r.get('uti_vs_ituk_bvp_share_pp'):+.1f} pp"
                if r.get("uti_vs_ituk_bvp_share_pp") is not None
                else "—",
            ]
        )
    pms_tbl = _tbl(
        [
            "PMS category",
            "ITUK BVP qty",
            "ITUK genuine qty",
            "ITUK BVP share",
            "UTI BVP qty",
            "UTI genuine qty",
            "UTI BVP share",
            "UTI−ITUK BVP pp",
        ],
        pms_rows,
    )

    sub_rows = []
    for r in payload.get("subgroup_compare", [])[:30]:
        sub_rows.append(
            [
                _e(r.get("subgroup_label") or _report_subgroup_label(r.get("product_subgroup"))),
                _isze_denom(r.get("ITUK_sellout_eur")),
                _isze_denom(r.get("UTI_sellout_eur")),
                _pct(r.get("ITUK_bvp_share")),
                _pct(r.get("UTI_bvp_share")),
            ]
        )
    sub_tbl = _tbl(
        [
            "Taxonomy bucket",
            "ITUK ISZE-denom. (proxy)",
            "UTI ISZE-denom. (proxy)",
            "ITUK BVP %",
            "UTI BVP %",
        ],
        sub_rows,
    )

    aim_l1_rows = []
    for r in payload.get("aim_l1_compare", [])[:20]:
        aim_l1_rows.append(
            [
                _e(r.get("aim_l1_label") or _aim_l1_label(r.get("aim_l1"))),
                _e(r.get("aim_l2") or "—"),
                _isze_denom(r.get("ITUK_sellout_eur")),
                _isze_denom(r.get("UTI_sellout_eur")),
                _pct(r.get("ITUK_bvp_share")),
                _pct(r.get("UTI_bvp_share")),
            ]
        )
    aim_l1_tbl = _tbl(
        [
            "AIM Category L1",
            "AIM L2 (mode)",
            "ITUK ISZE-denom. (proxy)",
            "UTI ISZE-denom. (proxy)",
            "ITUK BVP %",
            "UTI BVP %",
        ],
        aim_l1_rows,
    )

    def top_tbl(side: dict, dist: str) -> str:
        rows = []
        for r in side.get(dist, [])[:20]:
            rows.append(
                [
                    _e(r.get("part_number")),
                    _e((r.get("description") or "")[:40]),
                    _e(r.get("pms_category") or "—"),
                    _e(r.get("aim_l1") or "—"),
                    _e(r.get("filter_part_role") or "—"),
                    _fmt(r.get("qty_year")),
                    _isze_denom(r.get("valued_eur")),
                ]
            )
        return _tbl(
            ["PN", "Description", "PMS", "AIM L1", "Filter role", "Qty", "ISZE-denom. (proxy)"],
            rows,
        )

    bvp_top = (
        "<div class='grid2'>"
        f"<div><h3>ITUK — top BVP</h3>{top_tbl(payload.get('top_bvp', {}), 'ITUK')}</div>"
        f"<div><h3>UTI — top BVP</h3>{top_tbl(payload.get('top_bvp', {}), 'UTI')}</div>"
        "</div>"
    )
    gen_top = (
        "<div class='grid2'>"
        f"<div><h3>ITUK — top contested genuine</h3>{top_tbl(payload.get('top_genuine_contested', {}), 'ITUK')}</div>"
        f"<div><h3>UTI — top contested genuine</h3>{top_tbl(payload.get('top_genuine_contested', {}), 'UTI')}</div>"
        "</div>"
    )

    b = payload.get("benchmarks", {})
    kpis = "".join(
        f'<div class="kpi"><div class="val">{_e(v)}</div><div class="lbl">{_e(l)}</div></div>'
        for l, v in [
            ("ITUK sell-out qty", _fmt(b.get("ituk_qty"))),
            ("UTI sell-out qty", _fmt(b.get("uti_qty"))),
            ("ITUK ISZE-denom. (proxy)", _isze_denom(b.get("ituk_eur"))),
            ("UTI ISZE-denom. (proxy)", _isze_denom(b.get("uti_eur"))),
            ("ITUK BVP % of proxy", _pct(b.get("ituk_bvp_pct"))),
            ("UTI BVP % of proxy", _pct(b.get("uti_bvp_pct"))),
            ("ITUK qty w/o ISZE price", _pct(b.get("ituk_qty_no_price_pct"))),
            ("UTI qty w/o ISZE price", _pct(b.get("uti_qty_no_price_pct"))),
        ]
    )

    chart_json = json.dumps(
        _clean_nans(
            {
                "aim_mix": mix,
                "pms_compare": payload.get("pms_compare", [])[:12],
            }
        ),
        allow_nan=False,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Sell-out AIM · ITUK vs UTI 2025</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" defer></script>
<style>
:root {{ --red:#CC0E1E; --bg:#f4f5f7; --card:#fff; --text:#1a1a1a; --muted:#5a5a5a; --border:#e4e4e7; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",Calibri,sans-serif; background:var(--bg); color:var(--text); }}
header {{ background:linear-gradient(135deg,var(--red),#9a0b17); color:#fff; padding:1.4rem 2rem; }}
header h1 {{ margin:0.2rem 0; font-size:1.45rem; }}
.badge {{ display:inline-block; margin-top:0.4rem; padding:0.2rem 0.55rem; background:rgba(0,0,0,0.25); border-radius:4px; font-size:0.72rem; }}
.wrap {{ max-width:1240px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
section {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; }}
section h2 {{ margin:0 0 0.6rem; font-size:1.02rem; color:var(--red); border-bottom:3px solid var(--red); padding-bottom:0.25rem; }}
section h3 {{ font-size:0.9rem; margin:0.5rem 0; color:var(--muted); }}
.callout {{ padding:0.65rem 0.9rem; border-left:4px solid var(--red); background:#fff8f8; font-size:0.88rem; margin-bottom:1rem; }}
.kpi-row {{ display:flex; flex-wrap:wrap; gap:0.55rem; }}
.kpi {{ flex:1 1 150px; background:var(--bg); border-left:4px solid var(--red); padding:0.6rem 0.8rem; border-radius:6px; }}
.kpi .val {{ font-size:1.15rem; font-weight:700; }}
.kpi .lbl {{ font-size:0.72rem; color:var(--muted); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
@media(max-width:900px){{ .grid2{{ grid-template-columns:1fr; }} }}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.78rem; }}
.tbl th {{ background:var(--red); color:#fff; padding:0.35rem 0.45rem; text-align:left; }}
.tbl td {{ padding:0.3rem 0.45rem; border-bottom:1px solid var(--border); }}
.tbl tr.bill td {{ background:#f0f4ff; }}
.muted {{ color:var(--muted); font-size:0.85rem; }}
</style>
</head>
<body>
<header>
  <div style="font-weight:800;font-size:0.8rem;letter-spacing:0.08em;opacity:0.9">ISZE · DB→DLR · Network AIM</div>
  <h1>BVP &amp; Genuine sell-out — ITUK vs UTI (CY2025)</h1>
  <span class="badge">Generated {payload.get("generated", "")}</span>
</header>
<div class="wrap">
  <div class="callout">{_e(payload.get("scope_note", ""))}<br/><strong>{_e(proxy_note)}</strong></div>
  <section><h2>Network summary</h2><div class="kpi-row">{kpis}</div></section>
  <div class="grid2">
    <section><h2>AIM mix by network</h2><canvas id="chartMix" height="260"></canvas></section>
    <section><h2>PMS — BVP qty (sell-out)</h2><canvas id="chartPms" height="260"></canvas></section>
  </div>
  <section><h2>AIM comparison (sell-out qty vs ISZE-denom. proxy vs billing)</h2>
    <p class="muted">No dealer breakdown — ITUK dealer file aggregated to network. BVP / genuine % on sell-out rows use ISZE-denominated proxy only (not qty-only mix).</p>
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
  Rebuild: prism/scripts/build_dealer_sellout_aim_gps.py · Data/derived/sellout_aim_*
</footer>
<script type="application/json" id="chart-data">{chart_json}</script>
<script>
function initCharts() {{
  if (typeof Chart === 'undefined') return;
  const D = JSON.parse(document.getElementById('chart-data').textContent);
  const mix = D.aim_mix || [];
  const sell = mix.filter(r => r.layer === 'sellout_db_dlr');
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
      datasets: [
        {{ label: 'ITUK BVP', data: pms.map(r => r.ITUK_sellout_db_dlr_bvp_qty||0), backgroundColor: '#CC0E1E' }},
        {{ label: 'UTI BVP', data: pms.map(r => r.UTI_sellout_db_dlr_bvp_qty||0), backgroundColor: '#9a0b17' }},
      ],
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }},
  }});
}}
document.addEventListener('DOMContentLoaded', initCharts);
window.addEventListener('load', initCharts);
</script>
</body>
</html>"""


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
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
            aim_summary(sell, f"{dist} sell-out (network)", dist, "sellout_db_dlr")
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
        sub_cmp.sort(key=lambda r: -(r.get("ITUK_sellout_eur") or 0))
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
        aim_l1_cmp.sort(key=lambda r: -(r.get("ITUK_sellout_eur") or 0))
    aim_l1_long.to_csv(OUT_AIM_L1, index=False)

    top_rows = []
    for dist in DISTS:
        for bucket, data in (("bvp", top_bvp[dist]), ("genuine_contested", top_gen[dist])):
            for r in data:
                top_rows.append({**r, "distributor_code": dist, "aim_bucket": bucket})
    pd.DataFrame(top_rows).to_csv(OUT_TOP, index=False)

    pd.DataFrame(mix_rows).to_csv(OUT_MIX, index=False)

    ituk_so = next(r for r in mix_rows if r["distributor_code"] == "ITUK" and r["layer"] == "sellout_db_dlr")
    uti_so = next(r for r in mix_rows if r["distributor_code"] == "UTI" and r["layer"] == "sellout_db_dlr")

    payload = {
        "generated": str(date.today()),
        "scope_note": (
            "Network-level DB→DLR sell-out CY2025. ITUK dealer pivot summed to one network. "
            "AIM buckets: bvp | genuine_contested (catalog pair exists) | genuine_only."
        ),
        "valuation_note": (
            "Sell-out reports are quantity only — no dealer EUR. ISZE-denominated value = "
            "reported qty × median CY2025 ISZE→DB unit price per PN (proxy for mix; not sell-out revenue). "
            "PNs with no billing price contribute qty but €0 to proxy totals. Billing rows use actual invoice EUR and GPS."
        ),
        "benchmarks": {
            "ituk_qty": ituk_so["qty_year"],
            "uti_qty": uti_so["qty_year"],
            "ituk_eur": ituk_so["total_eur"],
            "uti_eur": uti_so["total_eur"],
            "ituk_bvp_pct": ituk_so["bvp_pct"],
            "uti_bvp_pct": uti_so["bvp_pct"],
            "ituk_qty_no_price_pct": ituk_so.get("qty_without_isze_price_pct"),
            "uti_qty_no_price_pct": uti_so.get("qty_without_isze_price_pct"),
        },
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
    print(f"ok: {OUT_MIX} ({len(mix_rows)} mix rows)")


if __name__ == "__main__":
    main()
