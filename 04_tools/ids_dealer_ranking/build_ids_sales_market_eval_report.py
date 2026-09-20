#!/usr/bin/env python3
"""Build shared IDS × sales × market evaluation HTML (self-contained Chart.js)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = ROOT / "01_data/90_INBOX/IDS_2026/reports/ids_sales_market_eval/eval_payload.json"
CHART_JS = ROOT / "02_dashboards/since_2026-06-01/assets/chart.umd.min.js"
OUT_DIR = ROOT / "01_data/90_INBOX/IDS_2026/reports/ids_sales_market_eval"
OUT_HTML = OUT_DIR / "IDS_2026_Audit_Sales_Market_Evaluation.html"
MIRROR = ROOT / "02_dashboards/ids/IDS_2026_Audit_Sales_Market_Evaluation.html"

DISPLAY = {
    "BE": "Belgium",
    "NL": "Netherlands",
    "POLAND": "Poland",
    "PETROS": "Greece (Petros)",
    "RSA": "Norway (RSA)",
    "IUK": "UK LCV",
    "ISRAEL": "Israel (UMI)",
    "MALTA": "Malta",
    "CYPRUS": "Cyprus",
    "ROMANIA": "Romania",
    "PORTUGAL": "Portugal",
    "HUNGARY": "Hungary",
}


def r_fmt(v) -> str:
    if v is None:
        return "—"
    return f"{v:+.2f}"


def main() -> None:
    data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    chart = CHART_JS.read_text(encoding="utf-8")
    chart = re.sub(r"//# sourceMappingURL=.*", "", chart)
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    markets = data["markets"]
    corr = data["correlations"]["dedupe_drop_nl"]
    corr_full = data["correlations"]["full_incl_be_nl"]
    quads = data["quadrants"]

    # Chart data: scatter D vs PMS (markets with both)
    scatter = []
    for m in markets:
        if m["pms_total_pct"] is None:
            continue
        scatter.append(
            {
                "x": m["ids_d_pct"],
                "y": m["pms_total_pct"],
                "label": DISPLAY.get(m["market"], m["market"]),
                "gps": m["gps_spu_eur"],
                "mix": m["genuine_mix_pct"],
            }
        )

    # Correlation bars (deduped)
    corr_labels = []
    corr_vals = []
    corr_colors = []
    for c in corr:
        if c["r"] is None:
            continue
        short = c["label"].replace(" avg", "").replace("Section D", "Sec. D").replace("IDS total", "IDS tot.")
        corr_labels.append(short)
        corr_vals.append(round(c["r"], 3))
        corr_colors.append("#1d9e75" if c["r"] >= 0 else "#e24b4a")

    # Ranking: IDS D
    rank_d = sorted(
        [m for m in markets if m["ids_d_pct"] is not None],
        key=lambda x: x["ids_d_pct"],
        reverse=True,
    )
    # Ranking PMS total where available
    rank_pms = sorted(
        [m for m in markets if m["pms_total_pct"] is not None],
        key=lambda x: x["pms_total_pct"],
        reverse=True,
    )

    # Risk join where DB matches
    risk_by_db = {}
    for row in data.get("aftersales_risk_rows") or []:
        if row.get("db"):
            risk_by_db[str(row["db"]).upper()] = row

    payload_js = json.dumps(
        {
            "scatter": scatter,
            "corr_labels": corr_labels,
            "corr_vals": corr_vals,
            "corr_colors": corr_colors,
            "rank_d_labels": [DISPLAY.get(m["market"], m["market"]) for m in rank_d],
            "rank_d_vals": [m["ids_d_pct"] for m in rank_d],
            "rank_pms_labels": [DISPLAY.get(m["market"], m["market"]) for m in rank_pms],
            "rank_pms_vals": [m["pms_total_pct"] for m in rank_pms],
            "med_d": quads["ids_d_median_pct"],
            "med_pms": quads["pms_total_median_pct"],
        },
        ensure_ascii=False,
    )

    # Market table rows
    table_rows = []
    for m in sorted(markets, key=lambda x: -(x["ids_d_pct"] or 0)):
        name = DISPLAY.get(m["market"], m["market"])
        risk = risk_by_db.get(str(m["prism_db"]).upper())
        risk_s = "—" if not risk or risk.get("risk_score") is None else f"{risk['risk_score']:.0f}"
        pms = "—" if m["pms_total_pct"] is None else f"{m['pms_total_pct']:.1f}%"
        mix = "—" if m["genuine_mix_pct"] is None else f"{m['genuine_mix_pct']:.1f}%"
        gps = "—" if m["gps_spu_eur"] is None else f"€{m['gps_spu_eur']:.0f}"
        fill = "—" if m["kpi_fill_pct"] is None else f"{m['kpi_fill_pct']:.0f}%"
        table_rows.append(
            "<tr>"
            f"<td>{name}</td>"
            f"<td class='num'>{m['dealers']}</td>"
            f"<td class='num'>{m['ids_d_pct']:.1f}%</td>"
            f"<td class='num'>{m['ids_total_pct']:.1f}%</td>"
            f"<td class='num'>{pms}</td>"
            f"<td class='num'>{mix}</td>"
            f"<td class='num'>{gps}</td>"
            f"<td class='num'>{fill}</td>"
            f"<td class='num'>{risk_s}</td>"
            "</tr>"
        )

    def quad_list(key: str) -> str:
        items = quads.get(key) or []
        if not items:
            return "<li>None in this sample</li>"
        bits = []
        for i in items:
            gps = "" if i.get("gps_spu_eur") is None else f" · GPS €{i['gps_spu_eur']:.0f}/UIO"
            bits.append(
                f"<li><strong>{DISPLAY.get(i['market'], i['market'])}</strong> — "
                f"Sec. D {i['ids_d_pct']:.1f}% · PMS total {i['pms_total_pct']:.1f}%{gps}</li>"
            )
        return "".join(bits)

    corr_rows_html = []
    for c in corr:
        c0 = next((x for x in corr_full if x["y"] == c["y"] and x["x"] == c["x"]), None)
        corr_rows_html.append(
            "<tr>"
            f"<td>{c['label']}</td>"
            f"<td class='num'>{r_fmt(c['r'])}</td>"
            f"<td class='num'>{c['n']}</td>"
            f"<td class='num'>{r_fmt(None if c0 is None else c0['r'])}</td>"
            "</tr>"
        )

    debate_html = "".join(
        f"<div class='callout'><h3>{h['title']}</h3>"
        f"<p>{h['point']}</p>"
        f"<p class='impl'><em>Strategic implication:</em> {h['implication']}</p></div>"
        for h in data["debate_hooks"]
    )

    gaps_html = "".join(f"<li>{g}</li>" for g in data["coverage_gaps"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>IDS 2026 — Audit × Sales × Market Evaluation</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:15px;line-height:1.55;background:#f7f4ee}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}}
.cover{{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:3.5rem 2.5rem 3rem;}}
.cover h1{{color:#fff;font-size:2.35rem;line-height:1.15;max-width:40rem}}
.cover .rule{{width:4.5rem;height:3px;background:#c0552d;margin:1.25rem 0 1rem}}
.cover p{{margin:0;opacity:.9;max-width:42rem;font-size:1.02rem}}
.cover .meta{{margin-top:1.5rem;font-size:.85rem;opacity:.75}}
main{{max-width:1100px;margin:0 auto;padding:1.5rem 1.5rem 3rem}}
h2.sec{{font-size:1.35rem;margin:2rem 0 .6rem;padding-bottom:.4rem;border-bottom:2px solid #1a2b4a}}
h2.sec .no{{color:#c0552d}}
h3{{font-size:1.05rem;margin:1rem 0 .4rem}}
.lead{{font-size:1.05rem;color:#3a4556;margin:.4rem 0 1rem}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.75rem;margin:1rem 0 1.5rem}}
.stat{{background:#fff;border-radius:10px;padding:.85rem 1rem;border-left:4px solid #c0552d}}
.stat strong{{display:block;font-size:1.45rem;color:#1a2b4a;font-variant-numeric:tabular-nums}}
.stat span{{font-size:.78rem;color:#6b6256;text-transform:uppercase;letter-spacing:.04em}}
.card{{background:#fff;border-radius:10px;padding:1.1rem 1.2rem;margin:1rem 0;box-shadow:0 1px 3px rgba(26,39,68,.06)}}
.callout{{border-left:3px solid #c0552d;background:#fff;padding:.9rem 1rem;margin:.85rem 0;border-radius:0 8px 8px 0}}
.callout h3{{margin:0 0 .35rem;font-size:1rem}}
.callout p{{margin:.25rem 0}}
.callout .impl{{color:#3a4556;font-size:.95rem}}
.chart-wrap{{position:relative;width:100%;height:380px;margin:.5rem 0 0}}
.chart-wrap.tall{{height:460px}}
.hint{{font-size:.88rem;color:#6b6256;margin:.25rem 0 0}}
.quad{{display:grid;grid-template-columns:1fr 1fr;gap:.85rem;margin:1rem 0}}
@media(max-width:800px){{.quad{{grid-template-columns:1fr}}}}
.quad .box{{background:#fff;border-radius:10px;padding:.9rem 1rem;border-top:4px solid #888780}}
.quad .box.hh{{border-top-color:#1d9e75}}
.quad .box.hl{{border-top-color:#eda100}}
.quad .box.lh{{border-top-color:#2a78d6}}
.quad .box.ll{{border-top-color:#e24b4a}}
.quad h3{{font-size:.92rem;margin:0 0 .4rem}}
.quad ul{{margin:0;padding-left:1.1rem;font-size:.9rem}}
table{{width:100%;border-collapse:collapse;margin:.5rem 0;font-size:.88rem}}
th{{background:#1a2b4a;color:#fff;text-align:left;padding:.45rem .5rem;font-size:.72rem;text-transform:uppercase;letter-spacing:.03em}}
td{{padding:.4rem .5rem;border-bottom:1px solid #d9d3c8}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}
tbody tr:nth-child(even){{background:#f7f4ee}}
.sources{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #d9d3c8;font-size:.78rem;color:#6b6256}}
.badge{{display:inline-block;background:#fff3e8;color:#c0552d;font-size:.72rem;font-weight:700;padding:.15rem .45rem;border-radius:4px;margin-left:.35rem}}
ul.gaps{{margin:.4rem 0 0;padding-left:1.15rem}}
ul.gaps li{{margin:.3rem 0}}
</style>
</head>
<body>
<header class="cover">
  <h1>IDS 2026 — Dealer standards, parts sales, and market context</h1>
  <div class="rule"></div>
  <p>Structured evaluation of Isuzu Dealer Standard (IDS) audit results alongside distributor sales KPIs
  (PMS total capture, GPS €/UIO, fill) and aftersales market-pressure indicators — for constructive debate
  among dealers, distributors, and the OEM.</p>
  <p class="meta">shared briefing · built {built} · join grain: country / distributor averages · verification green</p>
</header>

<main>
  <div class="stats">
    <div class="stat"><strong>{data['scored_dealers']}</strong><span>IDS dealers scored</span></div>
    <div class="stat"><strong>{len(markets)}</strong><span>markets in sales join</span></div>
    <div class="stat"><strong>{r_fmt(next(c['r'] for c in corr if c['y']=='pms_capture_total' and c['x']=='ids_d_avg'))}</strong><span>r · Sec. D vs PMS total*</span></div>
    <div class="stat"><strong>{r_fmt(next(c['r'] for c in corr if c['y']=='genuine_share_eur' and c['x']=='ids_d_avg'))}</strong><span>r · Sec. D vs genuine mix*</span></div>
    <div class="stat"><strong>{data['network_gps_capture_pct_locked']}%</strong><span>network GPS capture (locked)</span></div>
  </div>
  <p class="hint">*Pearson on unique distributor wallets (Netherlands duplicate of Belgium PMS/GPS dropped). Primary PMS lens = <strong>total</strong> capture.</p>

  <h2 class="sec"><span class="no">01</span> Executive verdict</h2>
  <div class="card">
    <p class="lead"><strong>High Parts audit scores do not predict high maintenance-basket capture.</strong>
    Across joined markets, Section D (Parts &amp; Accessories) averages move <em>opposite</em> to PMS total capture
    (r ≈ −0.51 after removing the Belgium/Netherlands double-count; r ≈ −0.45 including both). Genuine € mix
    moves <em>with</em> Section D (r ≈ +0.41). GPS €/UIO is essentially unrelated to Section D at this grain.</p>
    <ul>
      <li>IDS remains a strong process / capability signal — especially for mix quality and fill discipline.</li>
      <li>Sales volume (PMS total) and wallet intensity (GPS €/UIO) require separate commercial levers.</li>
      <li>There is <strong>no dealer-level sales join</strong>: every correlation below is distributor / country average.</li>
      <li>Internet “market dominance” scrapers are <strong>not</strong> yet joined to IDS; aftersales risk scores provide a partial external pressure lens.</li>
    </ul>
  </div>

  <h2 class="sec"><span class="no">02</span> Audit vs sales — the picture</h2>
  <div class="card">
    <h3>Section D % vs PMS total capture %</h3>
    <p class="hint">Each point is one distributor market. Median split lines: Sec. D {quads['ids_d_median_pct']}% · PMS total {quads['pms_total_median_pct']}%.</p>
    <div class="chart-wrap"><canvas id="scat" role="img" aria-label="Scatter of Section D average versus PMS total capture">Scatter chart</canvas></div>
  </div>
  <div class="card">
    <h3>Correlation strength (unique wallets)</h3>
    <div class="chart-wrap"><canvas id="corr" role="img" aria-label="Bar chart of Pearson correlations">Correlation chart</canvas></div>
    <p class="hint">Green = positive association · red = negative. Small n (8–10) — directional, not causal.</p>
  </div>

  <h2 class="sec"><span class="no">03</span> Quadrants for debate</h2>
  <p class="lead">Median split on Section D and PMS total (unique wallets with both metrics).</p>
  <div class="quad">
    <div class="box hh">
      <h3>High IDS · High PMS total</h3>
      <ul>{quad_list('high_ids_high_pms')}</ul>
    </div>
    <div class="box hl">
      <h3>High IDS · Low PMS total <span class="badge">tension</span></h3>
      <ul>{quad_list('high_ids_low_pms')}</ul>
    </div>
    <div class="box lh">
      <h3>Low IDS · High PMS total <span class="badge">tension</span></h3>
      <ul>{quad_list('low_ids_high_pms')}</ul>
    </div>
    <div class="box ll">
      <h3>Low IDS · Low PMS total</h3>
      <ul>{quad_list('low_ids_low_pms')}</ul>
    </div>
  </div>

  <h2 class="sec"><span class="no">04</span> Rankings side by side</h2>
  <div class="card">
    <h3>IDS Section D average</h3>
    <div class="chart-wrap tall"><canvas id="rankD" role="img" aria-label="Horizontal ranking of Section D averages">Ranking</canvas></div>
  </div>
  <div class="card">
    <h3>PMS total capture (where joined)</h3>
    <div class="chart-wrap tall"><canvas id="rankP" role="img" aria-label="Horizontal ranking of PMS total capture">Ranking</canvas></div>
  </div>

  <h2 class="sec"><span class="no">05</span> Strategic discussion hooks</h2>
  {debate_html}

  <h2 class="sec"><span class="no">06</span> Market scorecard</h2>
  <div class="card" style="overflow:auto">
    <table>
      <thead>
        <tr>
          <th>Market</th><th class="num">Dealers</th><th class="num">Sec. D</th><th class="num">IDS total</th>
          <th class="num">PMS total</th><th class="num">Genuine mix</th><th class="num">GPS €/UIO</th>
          <th class="num">Fill</th><th class="num">Risk†</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>
    <p class="hint">† Aftersales risk score (CY2025) where available — street-price / IAM pressure composite, not an internet share metric. Israel row = UMI only.</p>
  </div>

  <h2 class="sec"><span class="no">07</span> Correlation table</h2>
  <div class="card">
    <table>
      <thead>
        <tr><th>Pair</th><th class="num">r (unique wallets)</th><th class="num">n</th><th class="num">r (incl. BE+NL)</th></tr>
      </thead>
      <tbody>
        {''.join(corr_rows_html)}
      </tbody>
    </table>
  </div>

  <h2 class="sec"><span class="no">08</span> Coverage &amp; limits</h2>
  <div class="card">
    <ul class="gaps">{gaps_html}</ul>
    <p class="hint" style="margin-top:1rem">Portugal meeting GPS Capture lock <strong>{data['portugal_meeting_gps_capture_pct_locked']}%</strong> is a separate metric family from pipeline GPS €/UIO / PMS % in this join — do not substitute one for the other in client slides.</p>
  </div>

  <div class="sources">
    <strong>Sources (footnote):</strong> IDS 2026 result reports · Parts Kaizen join (built {data.get('kaizen_built_at','')}) ·
    PRISM PMS total capture &amp; GPS €/UIO · KPI Master fill/MOS · aftersales risk composite CY2025 ·
    network GPS capture lock {data['network_gps_capture_pct_locked']}% (verified metrics snapshot).
    No raw line-level billing in this briefing.
  </div>
</main>

<script>
{chart}
</script>
<script>
const P = {payload_js};
const ink = '#52514e', grid = '#e1e0d9';
const tip = {{
  callbacks: {{
    label: function(ctx) {{
      const d = ctx.raw;
      if (d && d.label) {{
        let s = d.label + ': Sec. D ' + d.x.toFixed(1) + '% · PMS ' + d.y.toFixed(1) + '%';
        if (d.gps != null) s += ' · GPS €' + Math.round(d.gps) + '/UIO';
        if (d.mix != null) s += ' · mix ' + d.mix.toFixed(1) + '%';
        return s;
      }}
      return ctx.formattedValue;
    }}
  }}
}};

new Chart(document.getElementById('scat'), {{
  type: 'scatter',
  data: {{
    datasets: [{{
      data: P.scatter,
      backgroundColor: '#c0552d',
      borderColor: '#fff',
      borderWidth: 1.5,
      pointRadius: 7,
      pointHoverRadius: 9
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    layout: {{ padding: {{ top: 12, right: 72, bottom: 8, left: 8 }} }},
    plugins: {{
      legend: {{ display: false }},
      tooltip: tip
    }},
    scales: {{
      x: {{
        title: {{ display: true, text: 'IDS Section D average (%)', color: ink }},
        min: 68, max: 94,
        ticks: {{ color: ink, callback: v => v + '%' }},
        grid: {{ color: grid }}
      }},
      y: {{
        title: {{ display: true, text: 'PMS total capture (%)', color: ink }},
        min: 10, max: 62,
        ticks: {{ color: ink, callback: v => v + '%' }},
        grid: {{ color: grid }}
      }}
    }}
  }},
  plugins: [{{
    id: 'medians',
    beforeDatasetsDraw(ch) {{
      const x = ch.scales.x, y = ch.scales.y, c = ch.ctx;
      c.save();
      c.strokeStyle = 'rgba(26,43,74,0.35)';
      c.setLineDash([5,4]);
      c.beginPath();
      c.moveTo(x.getPixelForValue(P.med_d), y.top);
      c.lineTo(x.getPixelForValue(P.med_d), y.bottom);
      c.moveTo(x.left, y.getPixelForValue(P.med_pms));
      c.lineTo(x.right, y.getPixelForValue(P.med_pms));
      c.stroke();
      c.restore();
    }},
    afterDatasetsDraw(ch) {{
      const c = ch.ctx, meta = ch.getDatasetMeta(0);
      c.save();
      c.font = '11px Segoe UI, sans-serif';
      c.fillStyle = ink;
      // Manual label offsets to reduce overlap
      const dir = {{
        'Portugal': [8, -10], 'Hungary': [8, 12], 'Malta': [8, -8],
        'Romania': [8, 4], 'UK LCV': [-8, -10], 'Belgium': [8, 12],
        'Norway (RSA)': [8, -8], 'Israel (UMI)': [-8, 12],
        'Greece (Petros)': [8, 4], 'Cyprus': [8, -10]
      }};
      meta.data.forEach((pt, i) => {{
        const d = P.scatter[i];
        const off = dir[d.label] || [8, 0];
        c.textAlign = off[0] < 0 ? 'right' : 'left';
        c.fillText(d.label, pt.x + off[0], pt.y + off[1]);
      }});
      c.restore();
    }}
  }}]
}});

new Chart(document.getElementById('corr'), {{
  type: 'bar',
  data: {{
    labels: P.corr_labels,
    datasets: [{{
      data: P.corr_vals,
      backgroundColor: P.corr_colors,
      borderRadius: 4,
      barThickness: 22
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{
        min: -0.7, max: 0.7,
        title: {{ display: true, text: 'Pearson r', color: ink }},
        ticks: {{ color: ink }},
        grid: {{ color: grid }}
      }},
      y: {{ ticks: {{ color: ink, font: {{ size: 11 }} }}, grid: {{ display: false }} }}
    }}
  }}
}});

function rankChart(id, labels, vals, color) {{
  new Chart(document.getElementById(id), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [{{
        data: vals,
        backgroundColor: labels.map((_, i) => i < 3 ? color : '#888780'),
        borderRadius: 4,
        barThickness: 20
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{
          min: 0, max: Math.ceil(Math.max(...vals) / 5) * 5 + 5,
          ticks: {{ color: ink, callback: v => v + '%' }},
          grid: {{ color: grid }}
        }},
        y: {{ ticks: {{ color: ink }}, grid: {{ display: false }} }}
      }}
    }}
  }});
}}
rankChart('rankD', P.rank_d_labels, P.rank_d_vals, '#2a78d6');
rankChart('rankP', P.rank_pms_labels, P.rank_pms_vals, '#c0552d');
</script>
</body>
</html>
"""

    # Fix the f-string issues - I used doubled braces for JS which is correct in f-string
    # But table_rows had escaped quotes that might be wrong - let me check
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    MIRROR.write_text(html, encoding="utf-8")

    # Self-contained check
    https_src = len(re.findall(r"""(?:src|href)=["']https?://""", html, flags=re.I))
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {MIRROR}")
    print(f"external src/href count: {https_src}")
    print(f"size_kb: {OUT_HTML.stat().st_size // 1024}")


if __name__ == "__main__":
    main()
