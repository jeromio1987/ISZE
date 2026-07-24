#!/usr/bin/env python3
"""Build UTI vs ITUK dealer sell-out comparison + static dashboard."""
from __future__ import annotations

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
    raise TypeError(type(obj))


def file_uti_sources() -> None:
    UTI_DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in [
        (DATA_ROOT / "Dealer_sellout" / "UTIPartSalesCY2024.xlsx", UTI_DIR / "UTIPartSales_2025-01.xlsx"),
        (DATA_ROOT / "Dealer_sellout" / "UTIPartSalesCY2025.xlsx", UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx"),
    ]:
        if src.exists():
            shutil.copy2(src, dst)


def billing_uti_2025() -> pd.DataFrame:
    if not SALES_PARQUET.exists():
        return pd.DataFrame(columns=["part_number", "billing_qty"])
    sales = pd.read_parquet(SALES_PARQUET)
    mapping = load_distributor_mapping(resolve_mapping_path())
    sales = apply_distributor_codes(sales, mapping)
    s = sales[(sales["distributor_code"] == "UTI") & (sales["year"] == 2025)].copy()
    s["part_number"] = s["part_number"].map(normalize_pn)
    s = s.dropna(subset=["part_number"])
    return s.groupby("part_number", as_index=False)["billed_qty"].sum().rename(
        columns={"billed_qty": "billing_qty"}
    )


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

    ituk_pn = attach_pn_master(
        aggregate_pn(load_ituk_dealer_sales(2025), "qty_year"), dim, desc, xref
    )

    uti_paths = [
        UTI_DIR / "UTIPartSales_2025-01.xlsx",
        UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx",
    ]
    uti_reports = []
    uti_ytd = pd.DataFrame()
    for p in uti_paths:
        if not p.exists():
            continue
        df, meta = load_uti_part_sales(p)
        uti_reports.append(meta)
        if meta.get("report_month") == 12 and meta.get("report_year") == 2025:
            uti_ytd = df

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
        lambda r: (r["uti_bvp"] / r["bill_bvp"]) if r["bill_bvp"] else None,
        axis=1,
    )
    pms_cmp["sellthrough_total"] = pms_cmp.apply(
        lambda r: (r["uti_total"] / r["bill_total"]) if r["bill_total"] else None,
        axis=1,
    )

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
    st_bvp = float(ff["sellthrough_bvp"].iloc[0] * 100) if len(ff) and ff["sellthrough_bvp"].iloc[0] else None

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
        "scope_note": (
            "UTI→dealer and ITUK→dealer are the demand signal (sell-out). "
            "line_type from bvp_pn_dimension; catalog pairs from genuine_bvp_crossref "
            "(pair_source catalog_* only). Billing = ISZE→UTI for sell-through checks."
        ),
        "bvp_genuine_integrity": bvp_check,
        "uti_reports": uti_reports,
        "summary": {
            "ituk_cy2025_dealer_qty": int(ituk_pn["qty"].sum()),
            "uti_cy2025_dealer_ytd_qty": int(uti_ytd_pn["qty"].sum()),
            "uti_cy2025_billing_qty": int(billing["billing_qty"].sum()),
            "fuel_filter_bvp_sellthrough_pct": st_bvp,
        },
        "pms_compare": pms_cmp.to_dict(orient="records"),
        "spot_checks": spot_checks[spot_cols].to_dict(orient="records"),
        "pn_overlap": overlap[
            ["part_number", "description", "ituk_dealer_cy25", "uti_dealer_ytd", "line_type"]
        ].to_dict(orient="records"),
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Dealer sell-out · UTI vs ITUK</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root {{ --red:#CC0E1E; --bg:#f4f5f7; --card:#fff; --text:#1a1a1a; --muted:#5a5a5a; --border:#e4e4e7; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI",Calibri,sans-serif; background:var(--bg); color:var(--text); }}
header {{ background:linear-gradient(135deg,var(--red),#9a0b17); color:#fff; padding:1.4rem 2rem; }}
header h1 {{ margin:0.2rem 0; font-size:1.5rem; }}
.badge {{ display:inline-block; margin-top:0.4rem; padding:0.2rem 0.55rem; background:rgba(0,0,0,0.25); border-radius:4px; font-size:0.72rem; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
section {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; }}
section h2 {{ margin:0 0 0.6rem; font-size:1.02rem; color:var(--red); border-bottom:3px solid var(--red); padding-bottom:0.25rem; }}
.muted {{ color:var(--muted); font-size:0.85rem; }}
.kpi-row {{ display:flex; flex-wrap:wrap; gap:0.55rem; }}
.kpi {{ flex:1 1 140px; background:var(--bg); border-left:4px solid var(--red); padding:0.6rem 0.8rem; border-radius:6px; }}
.kpi .val {{ font-size:1.25rem; font-weight:700; }}
.kpi .lbl {{ font-size:0.72rem; color:var(--muted); }}
.callout {{ padding:0.65rem 0.9rem; border-left:4px solid var(--red); background:#fff8f8; font-size:0.88rem; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
@media(max-width:800px){{ .grid2{{ grid-template-columns:1fr; }} }}
.tbl {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
.tbl th {{ background:var(--red); color:#fff; padding:0.4rem 0.5rem; text-align:left; }}
.tbl td {{ padding:0.35rem 0.5rem; border-bottom:1px solid var(--border); }}
footer {{ text-align:center; color:var(--muted); font-size:0.75rem; padding:1rem; }}
</style>
</head>
<body>
<header>
  <div style="font-weight:800;font-size:0.8rem;letter-spacing:0.08em;opacity:0.9">ISZE · Dealer sell-out</div>
  <h1>UTI vs ITUK — sell-out demand</h1>
  <span class="badge">Generated {generated}</span>
</header>
<div class="wrap">
  <p class="muted">{scope_note}</p>
  <div class="callout" id="bvpStatus"></div>
  <section><h2>Summary</h2><div class="kpi-row" id="kpis"></div></section>
  <div class="grid2">
    <section><h2>PMS sell-out (catalog taxonomy)</h2><canvas id="chartPms"></canvas></section>
    <section><h2>UTI billing vs dealer (BVP)</h2><canvas id="chartSellthrough"></canvas></section>
  </div>
  <section><h2>PMS genuine / BVP</h2><div id="pmsTable"></div></section>
  <section><h2>Spot checks (description + catalog pair)</h2><div id="spotTable"></div></section>
  <section><h2>Same PN — ITUK vs UTI demand</h2><div id="overlapTable"></div></section>
</div>
<footer>See Data/raw/dealer_sales/DEALER_SELL_OUT.md</footer>
<script>
const DATA = {data_json};
function fmt(n) {{ return n == null || n === '' ? '—' : Number(n).toLocaleString('en-GB'); }}
function pct(n) {{ return n == null ? '—' : Number(n).toFixed(1) + '%'; }}
const bvp = DATA.bvp_genuine_integrity || {{}};
document.getElementById('bvpStatus').textContent =
  'BVP/genuine integrity (dimension vs crossref): ' + (bvp.status || '?') +
  ' — xref mismatches: ' + (bvp.xref_genuine_not_dimension_genuine||0) + ' genuine, ' +
  (bvp.xref_bvp_not_dimension_bvp||0) + ' bvp.';
const s = DATA.summary;
document.getElementById('kpis').innerHTML = [
  ['ITUK sell-out CY25', s.ituk_cy2025_dealer_qty],
  ['UTI sell-out YTD', s.uti_cy2025_dealer_ytd_qty],
  ['UTI billing CY25', s.uti_cy2025_billing_qty],
  ['Fuel BVP sell-through', s.fuel_filter_bvp_sellthrough_pct != null ? s.fuel_filter_bvp_sellthrough_pct.toFixed(0)+'%' : '—'],
].map(([l,v]) => `<div class="kpi"><div class="val">${{fmt(v)}}</div><div class="lbl">${{l}}</div></div>`).join('');
const labels = DATA.pms_compare.map(r => r.category_label || r.pms_category);
new Chart(document.getElementById('chartPms'), {{
  type:'bar',
  data:{{ labels, datasets:[
    {{ label:'ITUK', data:DATA.pms_compare.map(r=>r.ituk_total), backgroundColor:'#CC0E1E' }},
    {{ label:'UTI YTD', data:DATA.pms_compare.map(r=>r.uti_total), backgroundColor:'#5a5a5a' }}
  ]}},
  options:{{ responsive:true, plugins:{{ legend:{{ position:'bottom' }} }} }}
}});
new Chart(document.getElementById('chartSellthrough'), {{
  type:'bar',
  data:{{ labels, datasets:[
    {{ label:'Bill BVP', data:DATA.pms_compare.map(r=>r.bill_bvp), backgroundColor:'#9a0b17' }},
    {{ label:'Dealer BVP', data:DATA.pms_compare.map(r=>r.uti_bvp), backgroundColor:'#64748b' }}
  ]}},
  options:{{ responsive:true, plugins:{{ legend:{{ position:'bottom' }} }} }}
}});
function table(rows, cols) {{
  const th = cols.map(c => `<th>${{c[0]}}</th>`).join('');
  const tr = rows.map(r => `<tr>${{cols.map(c => `<td>${{c[1](r)}}</td>`).join('')}}</tr>`).join('');
  return `<table class="tbl"><thead><tr>${{th}}</tr></thead><tbody>${{tr}}</tbody></table>`;
}}
document.getElementById('pmsTable').innerHTML = table(DATA.pms_compare, [
  ['Category', r => r.category_label],
  ['ITUK', r => fmt(r.ituk_total)],
  ['UTI', r => fmt(r.uti_total)],
  ['Bill BVP', r => fmt(r.bill_bvp)],
  ['DLR BVP', r => fmt(r.uti_bvp)],
  ['BVP ST%', r => r.sellthrough_bvp != null ? (r.sellthrough_bvp*100).toFixed(0)+'%' : '—'],
]);
document.getElementById('spotTable').innerHTML = table(DATA.spot_checks, [
  ['PN', r => r.part_number],
  ['Description', r => (r.description||'').slice(0,36)],
  ['Type', r => (r.line_type||'') + (r.line_type_ok===false?' ⚠':'')],
  ['Billing', r => fmt(r.uti_billing_qty)],
  ['Dealer', r => fmt(r.uti_dealer_ytd)],
  ['Cat.BVP', r => r.catalog_paired_bvp||'—'],
  ['Cat.DLR', r => fmt(r.catalog_paired_dealer_ytd)],
  ['Note', r => r.pair_note||''],
]);
document.getElementById('overlapTable').innerHTML = table(DATA.pn_overlap.slice(0,20), [
  ['PN', r => r.part_number],
  ['Description', r => (r.description||'').slice(0,32)],
  ['ITUK', r => fmt(r.ituk_dealer_cy25)],
  ['UTI', r => fmt(r.uti_dealer_ytd)],
]);
</script>
</body>
</html>
"""


def main() -> int:
    payload = build_payload()
    DASH_JSON.parent.mkdir(parents=True, exist_ok=True)
    DASH_JSON.write_text(
        json.dumps(payload, indent=2, default=_json_safe),
        encoding="utf-8",
    )
    DASH_HTML.write_text(
        HTML_TEMPLATE.format(
            generated=payload["generated"],
            scope_note=payload["scope_note"],
            data_json=json.dumps(payload, default=_json_safe),
        ),
        encoding="utf-8",
    )
    print(f"Wrote {DASH_JSON}")
    print(f"Wrote {DASH_HTML}")
    print(f"BVP integrity: {payload['bvp_genuine_integrity']}")
    print(f"Summary: {json.dumps(payload['summary'], indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
