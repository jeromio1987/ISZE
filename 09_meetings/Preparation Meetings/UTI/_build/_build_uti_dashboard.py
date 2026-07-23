#!/usr/bin/env python3
"""
Build UTI meeting dashboards (internal + UTI-facing).
Metrics: GPS wallet %, attach rates, filter mix, genuine/BVP split, warranty overlay.
CY + FY from sales_fact; warranty from Final_Complete_Warranty_Pricing_2026.xlsx.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ISZE = Path(__file__).resolve().parents[4]
PRISM = ISZE / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
ROOT = ISZE
OUT = Path(__file__).resolve().parent.parent
WARR_PATH = ISZE / "Data" / "Final_Complete_Warranty_Pricing_2026.xlsx"

from config import (  # noqa: E402
    DERIVED_DIR,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.bvp_analytics import ensure_part_number, normalize_pn_value  # noqa: E402
from modules.data_prep import (  # noqa: E402
    load_distributor_mapping,
    load_uio_detail_from_excel,
    get_distributor_metadata,
)
from modules.gps_engine import (  # noqa: E402
    calculate_model_weighted_gps,
    calculate_model_weighted_multiyear_trends,
    calculate_sales_by_distributor,
)
from modules.sales_loader import load_prism_sales  # noqa: E402

DERIVED = DERIVED_DIR
CV_MAP = {
    "ITUK": "ITUK",
    "UTI": "UTI",
    "IRELAND": "IRELAND",
    "ISD": "GERMANY",
    "PORTUGAL": "PORTUGAL",
    "CYPRUS": "CYPRUS",
    "GREECE": "GREECE",
    "MALTA": "MALTA",
}


def norm_pn(v) -> str:
    return normalize_pn_value(v) if v is not None else ""


def load_warranty_claims() -> pd.DataFrame:
    """CV 2025 warranty claims by distributor × PN (qty, EUR)."""
    if not WARR_PATH.exists():
        return pd.DataFrame(columns=["distributor_code", "part_number", "qty", "value_eur", "year"])

    import openpyxl

    prices: dict[str, float] = {}
    wb = openpyxl.load_workbook(WARR_PATH, read_only=True, data_only=True)
    ws_p = wb["Pricing_Data"]
    hdr = list(ws_p.iter_rows(min_row=1, max_row=1, values_only=True))[0]
    pn_i = hdr.index("P/N")
    price_i = hdr.index("Price")
    for row in ws_p.iter_rows(min_row=2, max_row=ws_p.max_row, values_only=True):
        pn = norm_pn(row[pn_i])
        if pn and row[price_i] is not None:
            try:
                prices[pn] = float(row[price_i])
            except (TypeError, ValueError):
                pass

    ws = wb["Raw_CV_Warranty"]
    hdr = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
    idx = {h: i for i, h in enumerate(hdr)}
    rows = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        bill = str(row[idx["BILLYMD"]]) if row[idx["BILLYMD"]] else ""
        m = re.match(r"(\d{4})", bill)
        if not m:
            continue
        yr = int(m.group(1))
        dst = str(row[idx["DST_Name"]]).strip() if row[idx["DST_Name"]] else ""
        code = CV_MAP.get(dst)
        if not code:
            continue
        for pn_col, q_col in [("PARTNBR", "QTY1"), ("PARTNBR2", "QTY2")]:
            pn = norm_pn(row[idx[pn_col]])
            if not pn:
                continue
            try:
                qty = float(row[idx[q_col]] or 0)
            except (TypeError, ValueError):
                qty = 0
            if qty <= 0:
                continue
            price = prices.get(pn, 0.0)
            rows.append(
                {
                    "distributor_code": code,
                    "part_number": pn,
                    "qty": qty,
                    "value_eur": qty * price,
                    "year": yr,
                }
            )
    wb.close()
    return pd.DataFrame(rows)


def classify_sales(sales: pd.DataFrame, xref: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    bvp = set(xref["bvp_pn"].map(norm_pn))
    gen = set(xref["genuine_pn"].map(norm_pn))
    bvp_catalog = set(dim.loc[dim["line_type"] == "bvp", "part_number"].map(norm_pn))

    def bucket(pn: str) -> str:
        if pn in bvp:
            return "bvp"
        if pn in gen:
            return "genuine_pair"
        if pn in bvp_catalog:
            return "bvp"
        return "genuine_other"

    s = ensure_part_number(sales)
    s["bucket"] = s["part_number"].map(bucket)
    pn_cat = dim.set_index(dim["part_number"].map(norm_pn))["pms_category"].to_dict()
    s["pms_category"] = s["part_number"].map(lambda p: pn_cat.get(p, "") or "")
    return s


def period_agg(s: pd.DataFrame, year_col: str, year: int, dist: str | None = None) -> dict:
    d = s[s[year_col] == year]
    if dist:
        d = d[d["distributor_code"] == dist]
    if d.empty:
        return {}
    tot = float(d["net_sales_value"].sum())
    wear = d[d["pms_category"].isin(("oil_filter", "fuel_filter", "air_filter", "brake_pad", "clutch_kit"))]
    wear_e = float(wear["net_sales_value"].sum())
    bvp_e = float(d.loc[d["bucket"] == "bvp", "net_sales_value"].sum())
    gen_pair = float(d.loc[d["bucket"] == "genuine_pair", "net_sales_value"].sum())
    gen_other = float(d.loc[d["bucket"] == "genuine_other", "net_sales_value"].sum())
    return {
        "total_eur": round(tot),
        "genuine_eur": round(gen_pair + gen_other),
        "genuine_pair_eur": round(gen_pair),
        "genuine_other_eur": round(gen_other),
        "bvp_eur": round(bvp_e),
        "wear_eur": round(wear_e),
        "wear_pct": round(100 * wear_e / tot, 1) if tot else 0,
        "non_wear_eur": round(tot - wear_e),
    }


def attach_rates(s: pd.DataFrame, year_col: str, year: int, dist: str, uio: int) -> dict:
    if uio <= 0:
        return {}
    d = s[(s[year_col] == year) & (s["distributor_code"] == dist)]
    out = {}
    for cat in ("oil_filter", "fuel_filter", "air_filter", "brake_pad"):
        q = float(d.loc[d["pms_category"] == cat, "billed_qty"].sum())
        out[cat] = round(q / uio, 2)
    return out


def filter_mix(s: pd.DataFrame, year_col: str, year: int, dist: str) -> dict:
    bvp = set(pd.read_csv(DERIVED / "genuine_bvp_crossref.csv", dtype=str)["bvp_pn"].map(norm_pn))
    gen = set(pd.read_csv(DERIVED / "genuine_bvp_crossref.csv", dtype=str)["genuine_pn"].map(norm_pn))

    def xr(pn: str) -> str:
        if pn in bvp:
            return "bvp"
        if pn in gen:
            return "genuine"
        return "other"

    d = s[(s[year_col] == year) & (s["distributor_code"] == dist)]
    d = d[d["pms_category"].isin(("oil_filter", "fuel_filter", "air_filter", "brake_pad"))]
    out = {}
    for cat in ("oil_filter", "fuel_filter", "air_filter", "brake_pad"):
        g = d[d["pms_category"] == cat]
        tq = float(g["billed_qty"].sum())
        if tq < 1:
            continue
        gq = float(g[g["part_number"].map(xr) == "genuine"]["billed_qty"].sum())
        out[cat] = round(100 * gq / tq)
    return out


def build_payload() -> dict:
    xref = pd.read_csv(DERIVED / "genuine_bvp_crossref.csv", dtype=str)
    dim = pd.read_csv(DERIVED / "bvp_pn_dimension.csv", dtype=str)
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    sales = classify_sales(sales, xref, dim)
    if "fiscal_year" not in sales.columns:
        sales["fiscal_year"] = sales["year"]

    df_uio = load_uio_detail_from_excel(str(resolve_uio_path()))
    df_meta = get_distributor_metadata(df_map)

    gps_cy = calculate_model_weighted_multiyear_trends(
        sales, df_uio, df_meta, year_type="calendar"
    )
    gps_fy = calculate_model_weighted_multiyear_trends(
        sales, df_uio, df_meta, year_type="fiscal"
    )

    warr = load_warranty_claims()

    cy_years = sorted(int(y) for y in sales["year"].dropna().unique())
    fy_years = sorted(int(y) for y in sales["fiscal_year"].dropna().unique())

    dists_focus = ["UTI", "ITUK", "BELGIUM", "FINLAND", "PORTUGAL", "IRELAND"]

    def gps_table(df_gps: pd.DataFrame, yr: int) -> list[dict]:
        g = df_gps[df_gps["year_value"] == yr].copy()
        g = g[g["gps_pct"].notna()].sort_values("gps_pct", ascending=False)
        return [
            {
                "code": r["distributor_code"],
                "gps_pct": round(float(r["gps_pct"]), 1),
                "spu": round(float(r["spend_per_unit_eur"]), 0),
                "uio": int(float(r["uio_units"])),
                "sales": round(float(r["total_sales_eur"]), 0),
                "wallet": round(float(r["target_wallet_eur"]), 0),
            }
            for _, r in g.iterrows()
        ]

    payload: dict = {
        "generated": date.today().isoformat(),
        "cy_years": cy_years,
        "fy_years": fy_years,
        "warranty_note": (
            "Billing (sales_fact) has no WARRANTY text rows in CY exports. "
            "Warranty = CV claims file (qty × PR00 price), separate from distributor purchase billing. "
            "Do not add warranty EUR to billing EUR — show side by side."
        ),
        "gps_ranking": {
            "cy": {str(y): gps_table(gps_cy, y) for y in cy_years},
            "fy": {str(y): gps_table(gps_fy, y) for y in fy_years if y in fy_years},
        },
        "distributors": {},
    }

    for dist in dists_focus:
        rec: dict = {"code": dist}
        rec["sales_cy"] = {str(y): period_agg(sales, "year", y, dist) for y in cy_years}
        rec["sales_fy"] = {str(y): period_agg(sales, "fiscal_year", y, dist) for y in fy_years}
        rec["filter_mix_cy"] = {str(y): filter_mix(sales, "year", y, dist) for y in cy_years}
        rec["filter_mix_fy"] = {str(y): filter_mix(sales, "fiscal_year", y, dist) for y in fy_years}
        rec["attach_cy"] = {}
        rec["attach_fy"] = {}
        for y in cy_years:
            row = gps_cy[(gps_cy["distributor_code"] == dist) & (gps_cy["year_value"] == y)]
            uio = int(float(row["uio_units"].iloc[0])) if len(row) else 0
            rec["attach_cy"][str(y)] = attach_rates(sales, "year", y, dist, uio)
        for y in fy_years:
            row = gps_fy[(gps_fy["distributor_code"] == dist) & (gps_fy["year_value"] == y)]
            uio = int(float(row["uio_units"].iloc[0])) if len(row) else 0
            rec["attach_fy"][str(y)] = attach_rates(sales, "fiscal_year", y, dist, uio)
        if not warr.empty:
            wd = warr[warr["distributor_code"] == dist]
            rec["warranty"] = {
                str(y): {
                    "total_eur": round(float(wd.loc[wd["year"] == y, "value_eur"].sum())),
                    "total_qty": round(float(wd.loc[wd["year"] == y, "qty"].sum())),
                    "top_pns": (
                        wd[wd["year"] == y]
                        .groupby("part_number")
                        .agg(qty=("qty", "sum"), eur=("value_eur", "sum"))
                        .reset_index()
                        .sort_values("eur", ascending=False)
                        .head(15)
                        .assign(
                            part_number=lambda x: x["part_number"],
                            qty=lambda x: x["qty"].round(0).astype(int),
                            eur=lambda x: x["eur"].round(0).astype(int),
                        )
                        .to_dict(orient="records")
                    ),
                }
                for y in sorted(wd["year"].unique())
            }
        # NOx PN billing vs warranty
        nox = "8983528481"
        rec["nox"] = {}
        for y in cy_years:
            b = sales[
                (sales["distributor_code"] == dist)
                & (sales["year"] == y)
                & (sales["part_number"] == nox)
            ]
            bill_q = float(b["billed_qty"].sum())
            bill_e = float(b["net_sales_value"].sum())
            wq = 0.0
            we = 0.0
            if not warr.empty:
                w = warr[
                    (warr["distributor_code"] == dist)
                    & (warr["year"] == y)
                    & (warr["part_number"] == nox)
                ]
                wq = float(w["qty"].sum())
                we = float(w["value_eur"].sum())
            rec["nox"][str(y)] = {
                "billing_qty": int(bill_q),
                "billing_eur": round(bill_e),
                "warranty_qty": int(wq),
                "warranty_eur": round(we),
                "warranty_share_pct": round(100 * wq / (bill_q + wq), 1) if (bill_q + wq) else 0,
            }
        payload["distributors"][dist] = rec

    # UTI uplift (CY2025)
    s25 = sales[(sales["year"] == 2025) & (sales["distributor_code"] == "UTI")]
    bvp = set(xref["bvp_pn"].map(norm_pn))
    gen = set(xref["genuine_pn"].map(norm_pn))

    def xr(pn: str) -> str:
        if pn in bvp:
            return "bvp"
        if pn in gen:
            return "genuine"
        return "o"

    net = sales[(sales["year"] == 2025)].copy()
    net["xr"] = net["part_number"].map(xr)
    uplifts = {}
    for cat in ("fuel_filter", "air_filter"):
        g = net[(net["pms_category"] == cat) & (net["xr"].isin(["genuine", "bvp"]))]
        gq = float(g.loc[g["xr"] == "genuine", "billed_qty"].sum())
        ge = float(g.loc[g["xr"] == "genuine", "net_sales_value"].sum())
        gen_p = ge / gq if gq else 0
        u = s25[(s25["pms_category"] == cat) & (s25["part_number"].map(xr) == "bvp")]
        bq = float(u["billed_qty"].sum())
        be = float(u["net_sales_value"].sum())
        bvp_p = be / bq if bq else 0
        uplifts[cat] = int(bq * (gen_p - bvp_p))
    payload["uti_uplift_ex_oil"] = uplifts.get("fuel_filter", 0) + uplifts.get("air_filter", 0)

    return payload


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__TITLE__</title>
<script src="assets/chart.umd.min.js"></script>
<style>
__CSS__
</style>
</head>
<body>
<header>
  <div class="brand">ISUZU · ISZE</div>
  <h1>__H1__</h1>
  <p>__SUB__</p>
  <span class="badge">__BADGE__</span>
</header>
<div class="controls wrap">
  <label>Period <select id="periodType"><option value="cy">Calendar year (CY)</option><option value="fy">Fiscal year (FY Apr–Mar)</option></select></label>
  <label>Year <select id="yearSel"></select></label>
  <label>Distributor <select id="distSel"></select></label>
  __EXTRA_CTRL__
</div>
<div class="wrap" id="app"></div>
<footer>Generated __GEN__ · Billing: sales_fact · GPS wallet: model targets × UIO v17 · Warranty: CV claims file</footer>
<script>
const DATA = __JSON__;
const INTERNAL = __INTERNAL__;
let charts = [];

const CSS = document.querySelector('style').textContent;

function fmtE(n) { return n == null || isNaN(n) ? '—' : '€' + Number(n).toLocaleString('en-GB', {maximumFractionDigits:0}); }
function fmtPct(n) { return n == null || isNaN(n) ? '—' : Number(n).toFixed(0) + '%'; }

function destroyCharts() { charts.forEach(c => c.destroy()); charts = []; }

function yearOptions() {
  const pt = document.getElementById('periodType').value;
  return pt === 'fy' ? DATA.fy_years : DATA.cy_years;
}

function refreshYearSelect() {
  const sel = document.getElementById('yearSel');
  const yrs = yearOptions();
  sel.innerHTML = yrs.map(y => `<option value="${y}">${y}</option>`).join('');
  sel.value = yrs[yrs.length - 1];
}

function distList() { return Object.keys(DATA.distributors); }

function render() {
  destroyCharts();
  const pt = document.getElementById('periodType').value;
  const yr = document.getElementById('yearSel').value;
  const dist = document.getElementById('distSel').value;
  const d = DATA.distributors[dist];
  const salesKey = pt === 'fy' ? 'sales_fy' : 'sales_cy';
  const sales = d[salesKey][yr] || {};
  const gpsRank = (DATA.gps_ranking[pt] || DATA.gps_ranking.cy)[yr] || [];
  const utiRank = gpsRank.findIndex(r => r.code === dist) + 1;
  const gpsRow = gpsRank.find(r => r.code === dist) || {};
  const attachKey = pt === 'fy' ? 'attach_fy' : 'attach_cy';
  const mixKey = pt === 'fy' ? 'filter_mix_fy' : 'filter_mix_cy';
  const attach = (d[attachKey] || {})[yr] || {};
  const mix = (d[mixKey] || {})[yr] || {};
  const warr = (d.warranty || {})[yr];
  const nox = (d.nox || {})[yr] || {};

  let html = '';

  html += `<section><h2>Storyline</h2><div class="callout ok">
    <strong>Lead with wallet capture (GPS %)</strong>, not filter mix alone.
    UTI wallet capture is in the same band as ITUK (~low-20s % of model max wallet) while
    spend/vehicle is high — the gap is breadth (aftermarket), not price.
    Filter mix (€${(DATA.uti_uplift_ex_oil||0).toLocaleString()} fuel+air) is a small, provable first win inside that.
  </div></section>`;

  html += `<section><h2>KPIs — ${dist} · ${pt.toUpperCase()}${yr}</h2><div class="kpi-row">
    <div class="kpi"><div class="val">${fmtE(sales.total_eur)}</div><div class="lbl">Parts billing (net)</div></div>
    <div class="kpi"><div class="val">${fmtPct(sales.genuine_eur && sales.total_eur ? 100*sales.genuine_eur/sales.total_eur : null)}</div><div class="lbl">Genuine (incl. OE non-catalogue)</div></div>
    <div class="kpi"><div class="val">${fmtPct(sales.bvp_eur && sales.total_eur ? 100*sales.bvp_eur/sales.total_eur : null)}</div><div class="lbl">BVP-catalogue EUR</div></div>
    <div class="kpi"><div class="val">${fmtPct(gpsRow.gps_pct)}</div><div class="lbl">GPS % of target wallet</div></div>
    <div class="kpi"><div class="val">${fmtE(gpsRow.spu)}</div><div class="lbl">Spend / vehicle</div></div>
    <div class="kpi"><div class="val">#${utiRank || '—'}</div><div class="lbl">Wallet capture rank (network)</div></div>
  </div></section>`;

  html += `<section><h2>GPS wallet capture — network ranking</h2>
    <p class="muted">GPS % = parts billing ÷ Σ(UIO × max €/vehicle by model). Directional — denominator is ISZE max wallet, not measured aftermarket.</p>
    <canvas id="chartGps" height="120"></canvas>
    <table class="tbl"><tr><th>#</th><th>Market</th><th>GPS %</th><th>€/veh</th><th>UIO</th><th>Billing</th><th>Target wallet</th></tr>`;
  gpsRank.slice(0, 18).forEach((r, i) => {
    const hi = r.code === dist ? ' class="hi"' : '';
    html += `<tr${hi}><td>${i+1}</td><td>${r.code}</td><td>${fmtPct(r.gps_pct)}</td><td>${fmtE(r.spu)}</td><td>${r.uio.toLocaleString()}</td><td>${fmtE(r.sales)}</td><td>${fmtE(r.wallet)}</td></tr>`;
  });
  html += `</table></section>`;

  html += `<section><h2>Genuine parts billing vs warranty claims</h2>
    <p class="muted">${DATA.warranty_note}</p>
    <div class="grid2">
      <div><h3>Billing (distributor purchases)</h3>
        <table class="tbl"><tr><th>Bucket</th><th>EUR</th></tr>
        <tr><td>Genuine (crossref pairs)</td><td>${fmtE(sales.genuine_pair_eur)}</td></tr>
        <tr><td>Genuine (other OE)</td><td>${fmtE(sales.genuine_other_eur)}</td></tr>
        <tr><td>BVP catalogue</td><td>${fmtE(sales.bvp_eur)}</td></tr>
        <tr><td><strong>Total</strong></td><td><strong>${fmtE(sales.total_eur)}</strong></td></tr>
        </table></div>
      <div><h3>Warranty claims (CV file)</h3>`;
  if (warr) {
    html += `<p><strong>${fmtE(warr.total_eur)}</strong> · ${warr.total_qty.toLocaleString()} units (claims, not billing)</p>
      <table class="tbl"><tr><th>PN</th><th>Qty</th><th>EUR</th></tr>`;
    (warr.top_pns || []).slice(0, 8).forEach(p => {
      html += `<tr><td>${p.part_number}</td><td>${p.qty}</td><td>${fmtE(p.eur)}</td></tr>`;
    });
    html += `</table>`;
  } else {
    html += `<p class="muted">No warranty rows for this market/year in CV extract.</p>`;
  }
  html += `</div></div>`;
  if (nox.billing_qty !== undefined) {
    html += `<div class="callout warn"><strong>NOx 8983528481</strong> — Billing ${nox.billing_qty} units (${fmtE(nox.billing_eur)}) vs warranty claims ${nox.warranty_qty} units (${fmtE(nox.warranty_eur)}) · ~${nox.warranty_share_pct}% of combined volume on warranty (indicative).</div>`;
  }
  html += `</section>`;

  html += `<section><h2>PMS attach rates (units / vehicle / year)</h2>
    <p class="muted">Model-free: filter &amp; brake quantities ÷ UIO. Oil ~0.5/veh everywhere → many oil changes not on ISZE filter.</p>
    <canvas id="chartAttach" height="100"></canvas></section>`;

  html += `<section><h2>Filter genuine % (contestable catalogue)</h2>
    <canvas id="chartMix" height="100"></canvas>
    <p class="muted">UTI vs ITUK benchmark for fuel/air — see ITUK tab.</p></section>`;

  if (INTERNAL) {
    html += `<section class="internal"><h2>Internal — do not share</h2>
      <ul>
        <li>Do not quote €221K capture, 87% BVP overall, oil 76% genuine, AIM €</li>
        <li>FY incomplete for FY2025 (missing Jan–Mar 2026 billing)</li>
        <li>Dimension line_type fixed 2026-06-02 — classify from crossref</li>
      </ul></section>`;
  }

  document.getElementById('app').innerHTML = html;

  const labels = gpsRank.slice(0, 12).map(r => r.code);
  const gpsVals = gpsRank.slice(0, 12).map(r => r.gps_pct);
  charts.push(new Chart(document.getElementById('chartGps'), {
    type: 'bar',
    data: { labels, datasets: [{ label: 'GPS %', data: gpsVals, backgroundColor: labels.map(l => l === dist ? '#CC0E1E' : '#DC606E') }] },
    options: { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { max: 100, ticks: { callback: v => v + '%' } } } }
  }));

  const cats = ['oil_filter','fuel_filter','air_filter','brake_pad'];
  const labels2 = ['Oil','Fuel','Air','Brake pad'];
  charts.push(new Chart(document.getElementById('chartAttach'), {
    type: 'bar',
    data: {
      labels: labels2,
      datasets: [
        { label: dist, data: cats.map(c => attach[c] || 0), backgroundColor: '#CC0E1E' },
        { label: 'ITUK', data: cats.map(c => ((DATA.distributors.ITUK[attachKey]||{})[yr]||{})[c] || 0), backgroundColor: '#5a5a5a' }
      ]
    },
    options: { scales: { y: { beginAtZero: true, title: { display: true, text: 'units / vehicle' } } } }
  }));

  const itukMix = ((DATA.distributors.ITUK[mixKey]||{})[yr]||{});
  charts.push(new Chart(document.getElementById('chartMix'), {
    type: 'bar',
    data: {
      labels: labels2,
      datasets: [
        { label: 'UTI genuine %', data: cats.map(c => mix[c] != null ? mix[c] : 0), backgroundColor: '#CC0E1E' },
        { label: 'ITUK genuine %', data: cats.map(c => itukMix[c] != null ? itukMix[c] : 0), backgroundColor: '#5a5a5a' }
      ]
    },
    options: { scales: { y: { max: 100, ticks: { callback: v => v + '%' } } } }
  }));
}

document.getElementById('periodType').addEventListener('change', () => { refreshYearSelect(); render(); });
document.getElementById('yearSel').addEventListener('change', render);
document.getElementById('distSel').addEventListener('change', render);

(function init() {
  const ds = document.getElementById('distSel');
  distList().forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; if (c === 'UTI') o.selected = true; ds.appendChild(o); });
  refreshYearSelect();
  render();
})();
</script>
</body>
</html>"""

SHARED_CSS = """
:root { --red:#CC0E1E; --red-l:#DC606E; --bg:#f4f5f7; --card:#fff; --text:#1a1a1a; --muted:#5a5a5a; --border:#e4e4e7; }
* { box-sizing:border-box; }
body { margin:0; font-family:"Segoe UI",Calibri,sans-serif; background:var(--bg); color:var(--text); }
header { background:linear-gradient(135deg,var(--red),#9a0b17); color:#fff; padding:1.5rem 2rem; }
header h1 { margin:0.2rem 0; font-size:1.6rem; }
.brand { font-weight:800; font-size:0.8rem; letter-spacing:0.08em; opacity:0.9; }
.badge { display:inline-block; margin-top:0.5rem; padding:0.2rem 0.6rem; background:rgba(0,0,0,0.25); border-radius:4px; font-size:0.72rem; text-transform:uppercase; }
.controls { background:var(--card); border-bottom:1px solid var(--border); padding:0.75rem 1.25rem; display:flex; flex-wrap:wrap; gap:1rem; align-items:center; }
.controls label { font-size:0.85rem; font-weight:600; }
.controls select { margin-left:0.35rem; padding:0.35rem 0.5rem; }
.wrap { max-width:1200px; margin:0 auto; padding:1rem 1.25rem 2rem; }
section { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1.1rem 1.3rem; margin-bottom:1rem; }
section h2 { margin:0 0 0.75rem; font-size:1.05rem; color:var(--red); border-bottom:3px solid var(--red); padding-bottom:0.3rem; }
section h3 { margin:0 0 0.5rem; font-size:0.95rem; }
.muted { color:var(--muted); font-size:0.85rem; }
.kpi-row { display:flex; flex-wrap:wrap; gap:0.6rem; }
.kpi { flex:1 1 120px; background:var(--bg); border-left:4px solid var(--red); padding:0.65rem 0.85rem; border-radius:6px; }
.kpi .val { font-size:1.35rem; font-weight:700; }
.kpi .lbl { font-size:0.72rem; color:var(--muted); }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:1rem; }
@media(max-width:800px){ .grid2{ grid-template-columns:1fr; } }
.tbl { width:100%; border-collapse:collapse; font-size:0.85rem; margin-top:0.5rem; }
.tbl th { background:var(--red); color:#fff; padding:0.45rem 0.55rem; text-align:left; }
.tbl td { padding:0.4rem 0.55rem; border-bottom:1px solid var(--border); }
.tbl tr.hi td { background:#fff5f5; font-weight:600; }
.callout { padding:0.7rem 1rem; border-left:4px solid var(--red); background:#fff8f8; margin:0.5rem 0; font-size:0.9rem; }
.callout.ok { border-color:#0d7a4a; background:#f0fdf4; }
.callout.warn { border-color:#b45309; background:#fffbeb; }
section.internal { background:#1a1a1a; color:#f4f4f5; }
section.internal h2 { color:#fbbf24; border-color:#fbbf24; }
footer { text-align:center; color:var(--muted); font-size:0.75rem; padding:1rem; }
"""


def write_html(path: Path, title: str, h1: str, sub: str, badge: str, payload: dict, internal: bool) -> None:
    html = (
        HTML_TEMPLATE.replace("__CSS__", SHARED_CSS)
        .replace("__TITLE__", title)
        .replace("__H1__", h1)
        .replace("__SUB__", sub)
        .replace("__BADGE__", badge)
        .replace("__GEN__", payload["generated"])
        .replace("__JSON__", json.dumps(payload, indent=None))
        .replace("__INTERNAL__", "true" if internal else "false")
        .replace("__EXTRA_CTRL__", "")
    )
    path.write_text(html, encoding="utf-8")


def main() -> None:
    print("Building metrics payload …")
    payload = build_payload()
    write_html(
        OUT / "UTI_Dashboard_Show.html",
        "UTI Dashboard",
        "UTI · GPS, capture & parts analytics",
        "Interactive view for the meeting · toggle CY/FY and distributor",
        "For UTI meeting",
        payload,
        internal=False,
    )
    write_html(
        OUT / "UTI_Dashboard_Internal.html",
        "UTI Dashboard INTERNAL",
        "UTI · full analytics (internal)",
        "Same data + caveats · pair with UTI_Dashboard_Show.html",
        "Internal only",
        payload,
        internal=True,
    )
    # refresh lightweight show doc
    import subprocess

    subprocess.run(
        [sys.executable, str(OUT / "_build" / "_build_uti_meeting_html.py")],
        check=False,
    )
    print("Done:")
    print(f"  {OUT / 'UTI_Dashboard_Show.html'}")
    print(f"  {OUT / 'UTI_Dashboard_Internal.html'}")


if __name__ == "__main__":
    main()
