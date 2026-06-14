#!/usr/bin/env python3
"""Build UTI meeting HTML (internal + external) from verified crossref + billing."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[3] / "Projects" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))

from config import resolve_mapping_path  # noqa: E402
from modules.bvp_analytics import ensure_part_number, normalize_pn_value  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent
DERIVED = Path(__file__).resolve().parents[3] / "Data" / "derived"


def load_data() -> dict:
    xref = pd.read_csv(DERIVED / "genuine_bvp_crossref.csv", dtype=str)
    dim = pd.read_csv(DERIVED / "bvp_pn_dimension.csv", dtype=str)
    gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
    pn_cat = dim.set_index(dim["part_number"].map(normalize_pn_value))["pms_category"].to_dict()

    bvp = set(xref["bvp_pn"].map(normalize_pn_value))
    gen = set(xref["genuine_pn"].map(normalize_pn_value))

    def classify(pn: str) -> str:
        if pn in bvp:
            return "bvp"
        if pn in gen:
            return "genuine"
        return "other"

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    s = ensure_part_number(sales)
    s25 = s[s["year"] == 2025].copy()
    s25["xr"] = s25["part_number"].map(classify)
    s25["cat"] = s25["part_number"].map(
        lambda p: pn_cat.get(p, "") if pd.notna(pn_cat.get(p, "")) else ""
    )

    contest = bvp | gen
    metrics: dict = {"generated": date.today().isoformat(), "year": 2025}

    for dist in ("UTI", "ITUK"):
        d = s25[s25["distributor_code"] == dist]
        tot = float(d["net_sales_value"].sum())
        bvp_e = float(d.loc[d["xr"] == "bvp", "net_sales_value"].sum())
        metrics[dist] = {
            "total_eur": round(tot),
            "bvp_pct": round(100 * bvp_e / tot, 1) if tot else 0,
            "non_bvp_pct": round(100 * (tot - bvp_e) / tot, 1) if tot else 0,
        }
        c = d[d["part_number"].isin(contest) & d["xr"].isin(["genuine", "bvp"])]
        tq = float(c["billed_qty"].sum())
        bq = float(c.loc[c["xr"] == "bvp", "billed_qty"].sum())
        metrics[dist]["contestable_bvp_pct"] = round(100 * bq / tq, 1) if tq else 0

        filters = {}
        for cat in ("fuel_filter", "air_filter", "oil_filter", "brake_pad"):
            g = c[c["cat"] == cat]
            if g.empty:
                continue
            tq_f = float(g["billed_qty"].sum())
            gq = float(g.loc[g["xr"] == "genuine", "billed_qty"].sum())
            bq_f = float(g.loc[g["xr"] == "bvp", "billed_qty"].sum())
            be = float(g.loc[g["xr"] == "bvp", "net_sales_value"].sum())
            ge = float(g.loc[g["xr"] == "genuine", "net_sales_value"].sum())
            filters[cat] = {
                "genuine_pct": round(100 * gq / tq_f) if tq_f else 0,
                "bvp_units": int(bq_f),
                "bvp_eur_per_unit": round(be / bq_f, 2) if bq_f else 0,
                "genuine_eur_per_unit": round(ge / gq, 2) if gq else 0,
            }
        metrics[dist]["filters"] = filters

    # Network genuine prices for uplift
    net = s25[s25["part_number"].isin(contest) & s25["xr"].isin(["genuine", "bvp"])]
    uplifts = {}
    for cat in ("fuel_filter", "air_filter"):
        g = net[net["cat"] == cat]
        bq_n = float(g.loc[g["xr"] == "bvp", "billed_qty"].sum())
        be_n = float(g.loc[g["xr"] == "bvp", "net_sales_value"].sum())
        gq_n = float(g.loc[g["xr"] == "genuine", "billed_qty"].sum())
        ge_n = float(g.loc[g["xr"] == "genuine", "net_sales_value"].sum())
        gen_p = ge_n / gq_n if gq_n else 0
        bvp_p = be_n / bq_n if bq_n else 0
        u = s25[(s25["distributor_code"] == "UTI") & (s25["cat"] == cat) & (s25["xr"] == "bvp")]
        bq_u = float(u["billed_qty"].sum())
        be_u = float(u["net_sales_value"].sum())
        bvp_u = be_u / bq_u if bq_u else 0
        uplifts[cat] = {
            "network_genuine_eur": round(gen_p, 2),
            "network_bvp_eur": round(bvp_p, 2),
            "uti_bvp_units": int(bq_u),
            "uti_bvp_eur": round(bvp_u, 2),
            "revenue_uplift_eur": round(bq_u * (gen_p - bvp_u)),
        }

    oil_u = s25[(s25["distributor_code"] == "UTI") & (s25["cat"] == "oil_filter") & (s25["xr"] == "bvp")]
    bq_o = float(oil_u["billed_qty"].sum())
    be_o = float(oil_u["net_sales_value"].sum())
    g_o = net[(net["cat"] == "oil_filter") & (net["xr"] == "genuine")]
    gq_o = float(g_o["billed_qty"].sum())
    ge_o = float(g_o["net_sales_value"].sum())
    gen_o = ge_o / gq_o if gq_o else 0
    bvp_o = be_o / bq_o if bq_o else 0
    uplifts["oil_filter"] = {
        "uti_bvp_units": int(bq_o),
        "network_genuine_eur": round(gen_o, 2),
        "uti_bvp_eur": round(bvp_o, 2),
        "revenue_if_converted_eur": round(bq_o * (gen_o - bvp_o)),
    }

    metrics["uplifts"] = uplifts
    metrics["uplift_total_ex_oil"] = uplifts["fuel_filter"]["revenue_uplift_eur"] + uplifts["air_filter"]["revenue_uplift_eur"]

    gu = gps[gps["distributor_code"] == "UTI"].sort_values("year")
    metrics["gps_ut"] = [
        {
            "year": int(r["year"]),
            "spu": round(float(r["spend_per_unit_eur"])),
            "sales": round(float(r["total_sales_eur"])),
            "uio": int(float(r["uio_units"])),
        }
        for _, r in gu.iterrows()
    ]

    g25 = gps[gps["year"] == 2025].sort_values("spend_per_unit_eur", ascending=False)
    metrics["spu_rank_2025"] = [
        {"code": r["distributor_code"], "spu": round(float(r["spend_per_unit_eur"]))}
        for _, r in g25.head(8).iterrows()
    ]

    return metrics


CSS = """
:root {
  --red: #CC0E1E;
  --red-light: #DC606E;
  --bg: #f7f7f8;
  --card: #fff;
  --text: #1a1a1a;
  --muted: #5a5a5a;
  --border: #e4e4e7;
  --ok: #0d7a4a;
  --warn: #b45309;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", Calibri, system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.45;
}
header {
  background: linear-gradient(135deg, var(--red) 0%, #9a0b17 100%);
  color: #fff;
  padding: 1.75rem 2rem 1.5rem;
}
header h1 { margin: 0 0 0.35rem; font-size: 1.75rem; font-weight: 700; }
header p { margin: 0; opacity: 0.92; font-size: 0.95rem; }
.badge {
  display: inline-block;
  margin-top: 0.75rem;
  padding: 0.2rem 0.65rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.badge.ext { background: rgba(255,255,255,0.2); }
.badge.int { background: #1a1a1a; color: #fbbf24; }
.wrap { max-width: 1100px; margin: 0 auto; padding: 1.5rem 1.25rem 3rem; }
nav.toc {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}
nav.toc a { color: var(--red); text-decoration: none; margin-right: 1rem; font-size: 0.9rem; }
section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
}
section h2 {
  margin: 0 0 1rem;
  font-size: 1.15rem;
  color: var(--red);
  border-bottom: 3px solid var(--red);
  padding-bottom: 0.35rem;
}
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 800px) { .grid2 { grid-template-columns: 1fr; } }
.kpi-row { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; }
.kpi {
  flex: 1 1 140px;
  background: var(--bg);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  border-left: 4px solid var(--red);
}
.kpi .val { font-size: 1.5rem; font-weight: 700; }
.kpi .lbl { font-size: 0.8rem; color: var(--muted); }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th { background: var(--red); color: #fff; text-align: left; padding: 0.55rem 0.65rem; }
td { padding: 0.5rem 0.65rem; border-bottom: 1px solid var(--border); }
tr:nth-child(even) td { background: #fafafa; }
.bar-chart { margin: 0.5rem 0; }
.bar-row { display: flex; align-items: center; gap: 0.5rem; margin: 0.35rem 0; font-size: 0.85rem; }
.bar-label { width: 110px; flex-shrink: 0; color: var(--muted); }
.bar-track { flex: 1; height: 22px; background: #eee; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--red); border-radius: 4px; }
.bar-fill.alt { background: var(--red-light); }
.bar-fill.good { background: var(--ok); }
.bar-val { width: 52px; text-align: right; font-weight: 600; }
.callout {
  background: #fff8f8;
  border-left: 4px solid var(--red);
  padding: 0.75rem 1rem;
  margin: 0.75rem 0;
  font-size: 0.92rem;
}
.callout.warn { background: #fffbeb; border-color: var(--warn); }
.callout.ok { background: #f0fdf4; border-color: var(--ok); }
.internal-only {
  background: #1a1a1a;
  color: #f4f4f5;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin: 1rem 0;
  font-size: 0.88rem;
}
.internal-only h3 { color: #fbbf24; margin-top: 0; font-size: 0.95rem; }
.internal-only ul { margin: 0.5rem 0 0; padding-left: 1.2rem; }
footer {
  text-align: center;
  color: var(--muted);
  font-size: 0.8rem;
  padding: 1rem;
}
.steps { counter-reset: step; list-style: none; padding: 0; margin: 0; }
.steps li {
  position: relative;
  padding: 0.65rem 0 0.65rem 2.5rem;
  border-bottom: 1px dashed var(--border);
}
.steps li::before {
  counter-increment: step;
  content: counter(step);
  position: absolute;
  left: 0;
  top: 0.55rem;
  width: 1.6rem;
  height: 1.6rem;
  background: var(--red);
  color: #fff;
  border-radius: 50%;
  font-size: 0.8rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
@media print {
  body { background: #fff; }
  section { break-inside: avoid; box-shadow: none; }
  nav.toc { display: none; }
}
"""


def bar_rows(items: list[tuple[str, float, str]], max_val: float = 100) -> str:
    html = '<div class="bar-chart">'
    for label, val, cls in items:
        w = min(100, (val / max_val * 100) if max_val else 0)
        html += (
            f'<div class="bar-row"><span class="bar-label">{label}</span>'
            f'<div class="bar-track"><div class="bar-fill {cls}" style="width:{w:.1f}%"></div></div>'
            f'<span class="bar-val">{val:.0f}%</span></div>'
        )
    html += "</div>"
    return html


def render_external(m: dict) -> str:
    uti = m["UTI"]
    ituk = m["ITUK"]
    fu = m["uplifts"]["fuel_filter"]
    au = m["uplifts"]["air_filter"]
    ou = m["uplifts"]["oil_filter"]
    filt = uti["filters"]
    itf = ituk["filters"]

    filter_bars_uti = bar_rows(
        [
            ("Fuel", filt["fuel_filter"]["genuine_pct"], ""),
            ("Air", filt["air_filter"]["genuine_pct"], ""),
            ("Oil", filt["oil_filter"]["genuine_pct"], ""),
            ("Brake pad", filt["brake_pad"]["genuine_pct"], "good"),
        ]
    )
    filter_bars_ituk = bar_rows(
        [
            ("Fuel", itf["fuel_filter"]["genuine_pct"], "good"),
            ("Air", itf["air_filter"]["genuine_pct"], "good"),
            ("Oil", itf["oil_filter"]["genuine_pct"], "good"),
            ("Brake pad", itf["brake_pad"]["genuine_pct"], "good"),
        ]
    )

    gps_bars = ""
    for row in m["gps_ut"]:
        w = row["spu"] / 350 * 100
        gps_bars += (
            f'<div class="bar-row"><span class="bar-label">{row["year"]}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{w:.0f}%"></div></div>'
            f'<span class="bar-val">€{row["spu"]}</span></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ISZE – UTI Meeting · June 2026</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div style="font-weight:800;font-size:0.85rem;letter-spacing:0.08em">ISUZU · ISZE</div>
  <h1>UTI Meeting · Parts, UIO &amp; Genuine Parts Share</h1>
  <p>June 2026 · CY2025 billing &amp; FY27 year-to-date context</p>
  <span class="badge ext">For discussion with UTI</span>
</header>
<div class="wrap">
  <section id="story">
    <h2>How the topics connect</h2>
    <ol class="steps">
      <li><strong>Market softness</strong> — FY27 YTD sales below budget and prior year; May order intake improved.</li>
      <li><strong>SPA flexibility</strong> — 53-line basket; 6-month option; NOx line to align on warranty volume first.</li>
      <li><strong>Filter mix vs peers</strong> — UTI buys filters as BVP where ITUK buys genuine; ~€{m['uplift_total_ex_oil']:,} revenue upside on fuel + air (excl. oil).</li>
      <li><strong>UIO confirmation</strong> — Active parc 31/12/2025 needed to size capture and spend per vehicle.</li>
    </ol>
  </section>

  <section id="bp">
    <h2>BP FY27 — where the year stands (Apr–May)</h2>
    <table>
      <tr><th></th><th>Apr</th><th>May</th><th>YTD</th></tr>
      <tr><td>Sales (€K)</td><td>211</td><td>191</td><td>402</td></tr>
      <tr><td>Budget (€K)</td><td>247</td><td>235</td><td>482</td></tr>
      <tr><td>vs Budget</td><td>−14%</td><td>−19%</td><td><strong>−17%</strong></td></tr>
      <tr><td>vs Prior year</td><td>−28%</td><td>−33%</td><td><strong>−31%</strong></td></tr>
      <tr><td>Order intake (€K)</td><td>182</td><td>238</td><td>420</td></tr>
    </table>
    <div class="callout ok">May order intake (€238K) was above April (€182K) — worth confirming whether the pipeline is recovering.</div>
  </section>

  <section id="account">
    <h2>UTI parts account — overall vs filter mix</h2>
    <div class="kpi-row">
      <div class="kpi"><div class="val">€{uti['total_eur']:,}</div><div class="lbl">Parts sales CY2025</div></div>
      <div class="kpi"><div class="val">{uti['non_bvp_pct']:.0f}%</div><div class="lbl">Non–BVP-catalogue spend (mostly OE genuine)</div></div>
      <div class="kpi"><div class="val">{uti['bvp_pct']:.0f}%</div><div class="lbl">BVP-catalogue part numbers</div></div>
      <div class="kpi"><div class="val">{uti['contestable_bvp_pct']:.0f}%</div><div class="lbl">BVP share where a BVP alternative exists</div></div>
    </div>
    <div class="callout">
      <strong>UTI is a genuine-dominant account.</strong> The commercial conversation is about
      <em>filters inside the BVP offer</em> — not about “UTI not buying genuine” overall.
    </div>
  </section>

  <section id="filters">
    <h2>Filters — UTI vs ITUK (genuine share by units, CY2025)</h2>
    <div class="grid2">
      <div>
        <p style="margin-top:0;font-weight:600">UTI</p>
        {filter_bars_uti}
      </div>
      <div>
        <p style="margin-top:0;font-weight:600">ITUK (peer)</p>
        {filter_bars_ituk}
      </div>
    </div>
    <table style="margin-top:1rem">
      <tr><th>Category</th><th>UTI genuine</th><th>ITUK genuine</th></tr>
      <tr><td>Fuel filter</td><td>{filt['fuel_filter']['genuine_pct']}%</td><td>{itf['fuel_filter']['genuine_pct']}%</td></tr>
      <tr><td>Air filter</td><td>{filt['air_filter']['genuine_pct']}%</td><td>{itf['air_filter']['genuine_pct']}%</td></tr>
      <tr><td>Oil filter</td><td>{filt['oil_filter']['genuine_pct']}%</td><td>{itf['oil_filter']['genuine_pct']}%</td></tr>
      <tr><td>Brake pad</td><td>{filt['brake_pad']['genuine_pct']}%</td><td>{itf['brake_pad']['genuine_pct']}%</td></tr>
    </table>
    <div class="callout">
      <strong>Opportunity (revenue, CY2025 run-rate):</strong>
      Fuel filter ~€{fu['revenue_uplift_eur']:,} + Air filter ~€{au['revenue_uplift_eur']:,}
      ≈ <strong>€{m['uplift_total_ex_oil']:,}/yr</strong> if UTI BVP filter volumes moved to network genuine pricing.<br/>
      <strong>Exclude oil filter</strong> — genuine element is lower unit price (~€{ou['network_genuine_eur']}/u vs UTI BVP ~€{ou['uti_bvp_eur']}/u); converting would reduce revenue ~€{abs(ou['revenue_if_converted_eur']):,}.
    </div>
  </section>

  <section id="gps">
    <h2>GPS — parts spend per vehicle (UTI)</h2>
    <div class="bar-chart">{gps_bars}</div>
    <p style="font-size:0.88rem;color:var(--muted)">
      Spend per unit = parts sales ÷ UIO. 2025 uses prior-year UIO proxy (~{m['gps_ut'][-1]['uio']:,} units) — treat YoY as indicative until parc is confirmed.
    </p>
  </section>

  <section id="uio">
    <h2>UIO — what we need from UTI</h2>
    <ul>
      <li>Active parc as of <strong>31/12/2025</strong> — operating vehicles only</li>
      <li>N- and F-series, by tonnage if possible</li>
      <li>Source (registration, internal records, estimate) and any scrap / de-registration rate</li>
      <li>Our model starting point: <strong>N 6,444 + F 4,809</strong> (shipment × survival curve) — we want to reconcile with your view</li>
    </ul>
  </section>

  <section id="spa">
    <h2>SPA — lines to align</h2>
    <ul>
      <li>53-part basket — flexibility: 6-month term; line-by-line or total</li>
      <li><strong>NOx sensor 8983528481</strong> — largest line; reconcile warranty vs retail volume before fixing programme price</li>
      <li>EGR cooler / valve — genuine-only; programme defends against parallel imports</li>
    </ul>
  </section>

  <section id="next">
    <h2>Proposed next steps</h2>
    <ul>
      <li><strong>UIO</strong> — UTI data by beginning of next week</li>
      <li><strong>SPA</strong> — confirm straightforward lines; joint NOx warranty review; agree term structure</li>
      <li><strong>GPS / filters</strong> — confirm category volumes; discuss fuel &amp; air genuine mix vs ITUK benchmark</li>
    </ul>
  </section>
</div>
<footer>ISZE internal · Generated {m['generated']} · Sources: billing CY2025, BVP catalog cross-reference</footer>
</body>
</html>"""


def render_internal(m: dict) -> str:
    ext_path = "UTI_Meeting_Show_UTI.html"
    data_json = json.dumps(m, indent=2)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>UTI Meeting — INTERNAL prep</title>
<style>{CSS}</style>
</head>
<body>
<header style="background:linear-gradient(135deg,#1a1a1a,#333)">
  <div style="font-weight:800;font-size:0.85rem;letter-spacing:0.08em;color:#fbbf24">INTERNAL ONLY</div>
  <h1>UTI Meeting prep · data audit &amp; sparring</h1>
  <p>Pair with <a href="{ext_path}" style="color:#fca5a5">{ext_path}</a> for the UTI-facing view · Generated {m['generated']}</p>
  <span class="badge int">Do not share</span>
</header>
<div class="wrap">
  <nav class="toc">
    <strong>Sections:</strong>
    <a href="#audit">Audit</a>
    <a href="#safe">Safe numbers</a>
    <a href="#dead">Do not quote</a>
    <a href="#ask">Questions</a>
    <a href="#aim">AIM</a>
    <a href="#raw">Raw metrics JSON</a>
  </nav>

  <section id="audit">
    <h2>Data audit (2026-06-02)</h2>
    <div class="internal-only">
      <h3>Bug fixed in pipeline</h3>
      <ul>
        <li><code>bvp_dimension.py</code> tagged all <code>PMS_PN_REGISTRY</code> PNs as <code>genuine</code>, ignoring <code>type: bvp</code>.</li>
        <li>Example: <code>1876102890</code> (3,793 UTI oil-filter units) → fake “76% genuine oil” narrative.</li>
        <li>Fix: registry <code>type</code> respected; P0/P2 rebuilt. <strong>Still classify from <code>genuine_bvp_crossref.csv</code> for meetings.</strong></li>
      </ul>
    </div>
    <div class="callout warn">
      <strong>Three metrics — never conflate:</strong><br/>
      (1) Overall billing: UTI {m['UTI']['non_bvp_pct']}% non-BVP-catalogue / {m['UTI']['bvp_pct']}% BVP-catalogue<br/>
      (2) Contestable basket: UTI {m['UTI']['contestable_bvp_pct']}% BVP units vs ITUK {m['ITUK']['contestable_bvp_pct']}%<br/>
      (3) <code>mix_genuine_bvp_pms.csv</code> = substitution only — not overall genuine share
    </div>
  </section>

  <section id="safe">
    <h2>Safe to show UTI (in external HTML)</h2>
    <ul>
      <li>Filter table UTI vs ITUK (crossref + billing)</li>
      <li>Revenue uplift fuel + air ≈ €{m['uplift_total_ex_oil']:,} (excl. oil)</li>
      <li>GPS €/vehicle 2023–25, BP FY27 Apr–May table</li>
      <li>Brake pads already ~{m['UTI']['filters']['brake_pad']['genuine_pct']}% genuine — not a gap</li>
      <li>UIO ask + SPA NOx park</li>
    </ul>
    <p>External file: <strong><a href="{ext_path}">{ext_path}</a></strong> · Deck backup: <code>UTI_Meeting_June2026.pptx</code></p>
  </section>

  <section id="dead">
    <h2>Do not quote (deprecated / wrong)</h2>
    <table>
      <tr><th>Claim</th><th>Why wrong</th></tr>
      <tr><td>“UTI 87% BVP overall”</td><td>Inverted contestable rate; overall is ~{m['UTI']['non_bvp_pct']}% non-BVP</td></tr>
      <tr><td>“0% genuine filters” / “oil 76% genuine”</td><td>Dimension bug; oil stable ~100% BVP</td></tr>
      <tr><td>€221K capture gap</td><td>N75-only + soft brake intervals</td></tr>
      <tr><td>€45K GP from bvp_downtrade_gp</td><td>Built on broken dimension unless re-derived</td></tr>
      <tr><td>ITUK “86% genuine” benchmark</td><td>Never valid</td></tr>
      <tr><td>AIM € at risk</td><td>No external AM feed; ~€11K network noise</td></tr>
    </table>
  </section>

  <section id="ask">
    <h2>Questions to ask UTI</h2>
    <ul>
      <li>Active parc 31/12/2025 — N/F split, source, scrap rate</li>
      <li>FY27 softness drivers; is May intake recovery real?</li>
      <li>SPA: line vs total; 6-month OK? NOx warranty volume split</li>
      <li>Real brake pad interval &amp; annual km on 7.5t urban (model assumes ~80k — too slack)</li>
      <li>Will you join FY27 GPS exercise? Category sales outside ISZE billing?</li>
    </ul>
  </section>

  <section id="aim">
    <h2>AIM &amp; capture model (internal)</h2>
    <ul>
      <li>Verify report: 3 fails — ITUK oil capture &gt;100%, capture cap rows</li>
      <li>Demand/capture model = filters only (23 BVP categories unmodelled — see BVP_FINDING.md)</li>
      <li>Lead meeting with filter mix + €{m['uplift_total_ex_oil']:,} revenue story, not AIM</li>
    </ul>
  </section>

  <section id="raw">
    <h2>Computed metrics (reproducible)</h2>
    <pre style="background:#f4f4f5;padding:1rem;border-radius:8px;overflow:auto;font-size:0.75rem">{data_json}</pre>
    <p style="font-size:0.85rem;color:var(--muted)">Rebuild: <code>python _build/_build_uti_meeting_html.py</code></p>
  </section>
</div>
<footer>ISZE internal · Not for UTI distribution</footer>
</body>
</html>"""


def main() -> None:
    print("Loading sales + crossref …")
    m = load_data()
    ext = OUT_DIR / "UTI_Meeting_Show_UTI.html"
    intr = OUT_DIR / "UTI_Meeting_Internal.html"
    ext.write_text(render_external(m), encoding="utf-8")
    intr.write_text(render_internal(m), encoding="utf-8")
    print(f"Wrote {ext}")
    print(f"Wrote {intr}")
    print(f"Uplift total (ex oil): EUR {m['uplift_total_ex_oil']:,}")


if __name__ == "__main__":
    main()
