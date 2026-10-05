"""Chart forms gallery -- ten ways to present the same fictive aftersales move.

WHY THIS EXISTS
    Jerome (2026-09-19): the current charts plot a change in a rate (euro per
    vehicle), which is two steps away from anything he manages. He asked for ten
    different presentation forms of the same business situation, on fictive
    numbers, so he can pick the ones he wants applied to real data.

WHAT IT WRITES
    02_dashboards/_design/chart_gallery/ISZE_Chart_Forms_Gallery.html

CONTRACT
    * Self-contained: chart.umd.min.js inlined (no CDN), fictive data embedded as
      JSON in a <script type="application/json"> block. Opens from file://.
    * Every panel carries a FICTIVE badge, a business-question title, and an
      italic caption that states the form's strength AND its weakness.
    * No number in this file is real. All of it is invented for form comparison.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHARTJS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = HERE / "ISZE_Chart_Forms_Gallery.html"

# --------------------------------------------------------------------------
# FICTIVE DATA -- invented, internally consistent, one situation for all panels
# --------------------------------------------------------------------------
FAMILIES = [
    # name,               eur_ly,  eur_ty,  units_ly, units_ty
    ("Filtration",        372000, 298000, 124000, 106000),
    ("Braking",           244000, 198000,  24400,  18900),
    ("Service kits",      188000, 156000,  23500,  17800),
    ("Engine parts",      141000, 119000,   9400,   7600),
    ("Electrical",        109000,  78000,  27250,  11200),
    ("Driveline",          56000,  45000,   2800,   2500),
]

EUR_LY = sum(f[1] for f in FAMILIES)
EUR_TY = sum(f[2] for f in FAMILIES)
UNITS_LY = sum(f[3] for f in FAMILIES)
UNITS_TY = sum(f[4] for f in FAMILIES)
UIO_LY = 48876
UIO_TY = 47783
SPEND_PER_TRUCK = 4500  # fictive assumption, stated on the panel

# The euro move, decomposed. Four briefed steps net to -215,000 against a real
# billed move of -216,000. The 1,000 residual is disclosed in the panel kicker
# rather than drawn: at a 1.3M axis a 1,000 step is a quarter of a pixel, and a
# sub-pixel bar is a lie told quietly.
BRIDGE = [
    ("Last year billed", EUR_LY, "total"),
    ("Volume", -295000, "down"),
    ("Price", 38000, "up"),
    ("Mix", 12000, "up"),
    ("Fleet", 30000, "up"),
    ("This year billed", EUR_TY, "total"),
]

NET_MOVE = EUR_TY - EUR_LY
REF_RATE = EUR_TY / EUR_LY
AVG_MOVE_PCT = (REF_RATE - 1) * 100
NORMAL_BAND = 0.10


def build_payload() -> dict:
    families = []
    for name, eur_ly, eur_ty, u_ly, u_ty in FAMILIES:
        families.append(
            {
                "name": name,
                "eur_ly": eur_ly,
                "eur_ty": eur_ty,
                "diff": eur_ty - eur_ly,
                "units_ly": u_ly,
                "units_ty": u_ty,
                "units_diff": u_ty - u_ly,
                "units_pct": (u_ty / u_ly - 1) * 100,
                "index": eur_ty / eur_ly * 100,
                "expected_ty": round(eur_ly * REF_RATE),
            }
        )
    for f in families:
        f["deviation"] = f["eur_ty"] - f["expected_ty"]

    bridge_bars, cursor = [], 0
    for label, value, kind in BRIDGE:
        if kind == "total":
            bridge_bars.append({"label": label, "value": value, "start": 0, "end": value,
                                "kind": kind, "bar": [0, value]})
            cursor = value
        else:
            start, end = cursor, cursor + value
            bridge_bars.append({"label": label, "value": value, "start": start, "end": end,
                                "kind": kind, "bar": [start, end]})
            cursor = end

    return {
        "fictive": True,
        "label": "FICTIVE",
        "disclaimer": ("Every number on this page is invented to compare chart forms. "
                       "None of it is real ISZE or distributor data."),
        "scenario": "One fictive distributor, one fictive 12-month period, six service families.",
        "eur_ly": EUR_LY,
        "eur_ty": EUR_TY,
        "net_move": NET_MOVE,
        "avg_move_pct": AVG_MOVE_PCT,
        "units_ly": UNITS_LY,
        "units_ty": UNITS_TY,
        "uio_ly": UIO_LY,
        "uio_ty": UIO_TY,
        "uio_diff": UIO_TY - UIO_LY,
        "spend_per_truck": SPEND_PER_TRUCK,
        "net_trucks": abs(NET_MOVE) / SPEND_PER_TRUCK,
        "normal_band_pct": NORMAL_BAND * 100,
        "families": families,
        "families_by_ly": sorted(families, key=lambda f: -f["eur_ly"]),
        "bridge": bridge_bars,
    }


PAYLOAD = build_payload()

CSS = """
:root{
  --navy:#15233c; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#222; --muted:#6c7484; --line:#d9d3c7; --good:#2f6b5a; --bad:#a63a2a;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--paper);color:var(--ink);
  font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:14px;line-height:1.45}
.wrap{max-width:1500px;margin:0 auto;padding:26px 22px 60px}
header.masthead{border-bottom:3px solid var(--navy);padding-bottom:16px;margin-bottom:18px}
h1{font-family:Georgia,"Times New Roman",serif;font-size:30px;line-height:1.15;margin:0 0 8px;color:var(--navy)}
.sub{color:var(--muted);font-size:14px;margin:0 0 10px;max-width:1000px}
.fictive-banner{display:inline-block;background:var(--terra);color:#fff;font-weight:700;
  letter-spacing:.14em;font-size:12px;padding:4px 10px;border-radius:3px}
.fictive-banner + span{margin-left:10px}
.note{background:#fdf6ef;border-left:4px solid var(--terra);padding:9px 12px;margin:12px 0 0;
  font-size:13px;max-width:1150px}
nav.index{margin:18px 0 26px;padding:12px 14px;background:#fff;border:1px solid var(--line);border-radius:4px}
nav.index h2{font-family:Georgia,serif;font-size:14px;margin:0 0 8px;color:var(--navy)}
nav.index ol{margin:0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:6px 8px}
nav.index a{display:inline-block;text-decoration:none;color:var(--navy);background:var(--paper);
  border:1px solid var(--line);border-radius:3px;padding:4px 9px;font-size:12.5px}
nav.index a:hover{background:var(--navy);color:var(--paper);border-color:var(--navy)}
nav.index a b{color:var(--terra);margin-right:5px}
nav.index a:hover b{color:var(--paper)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media (max-width:1300px){ .grid{grid-template-columns:1fr} }
.panel{background:#fff;border:1px solid var(--line);border-radius:5px;padding:15px 16px 13px;
  display:flex;flex-direction:column;scroll-margin-top:14px}
.panel.wide{grid-column:1 / -1}
.p-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.p-title{font-family:Georgia,"Times New Roman",serif;font-size:17px;line-height:1.25;
  color:var(--navy);margin:0}
.p-title .n{color:var(--terra);font-weight:700;margin-right:7px}
.badge{background:#fdeee7;color:#8d3a18;border:1px solid var(--terra);font-size:10.5px;
  font-weight:700;letter-spacing:.12em;padding:2px 7px;border-radius:3px;white-space:nowrap}
.p-kicker{font-size:12px;color:var(--muted);margin:5px 0 10px}
.p-body{flex:1 1 auto;position:relative}
.chart-box{position:relative;height:296px}
.chart-box.tall{height:326px}
.p-cap{font-style:italic;font-size:12.5px;color:#4a5262;margin:10px 0 0;padding-top:8px;
  border-top:1px dotted var(--line)}
.p-cap b{font-style:normal;color:var(--navy)}
.truck-lead{display:flex;flex-wrap:wrap;gap:18px;align-items:baseline;margin:2px 0 10px}
.truck-big{font-family:Georgia,serif;font-size:40px;line-height:1;color:var(--terra)}
.truck-big small{font-size:15px;color:var(--navy)}
.truck-say{font-size:13px;color:#3b4457;max-width:440px}
.truck-grid{display:grid;grid-template-columns:repeat(auto-fill,24px);gap:3px;margin:4px 0 10px}
.truck-grid svg{display:block}
.legend-inline{font-size:12px;color:var(--muted);margin:2px 0 10px}
table.gal{width:100%;border-collapse:collapse;font-size:13px}
table.gal th{text-align:right;font-size:11.5px;letter-spacing:.04em;text-transform:uppercase;
  color:var(--navy);border-bottom:2px solid var(--navy);padding:6px 8px;background:var(--paper)}
table.gal th.l{text-align:left}
table.gal td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:right;vertical-align:middle}
table.gal td.l{text-align:left}
table.gal tr.total td{border-top:2px solid var(--navy);border-bottom:none;font-weight:700;color:var(--navy)}
.cellbar-wrap{display:flex;align-items:center;justify-content:flex-end;gap:8px}
.cellbar{height:11px;background:var(--terra);border-radius:2px;min-width:2px}
td.num{font-variant-numeric:tabular-nums}
.neg{color:var(--bad)}
.sm-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media (max-width:1100px){ .sm-grid{grid-template-columns:repeat(2,1fr)} }
.sm{border:1px solid var(--line);border-radius:4px;padding:8px 9px 6px;background:#fff}
.sm-title{font-family:Georgia,serif;font-size:13.5px;color:var(--navy);margin-bottom:2px}
.sm-chart{position:relative;height:132px}
.sm-foot{font-size:11px;color:#4a5262;margin-top:4px;line-height:1.35}
"""

APP_JS = r"""
(function () {
  var D = JSON.parse(document.getElementById('fictive-data').textContent);
  var NAVY = '#15233c', TERRA = '#c0552d', PAPER = '#f7f4ee', MUTED = '#8b93a3';
  var GOOD = '#2f6b5a', BAD = '#a63a2a', GRID = '#e6e0d4', INK = '#3b4457';
  var FONT = '"Segoe UI",Roboto,Helvetica,Arial,sans-serif';

  Chart.defaults.font.family = FONT;
  Chart.defaults.font.size = 12;
  Chart.defaults.color = INK;
  Chart.defaults.animation = false;
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.plugins.legend.labels.boxWidth = 10;
  Chart.defaults.plugins.legend.labels.boxHeight = 10;
  Chart.defaults.plugins.tooltip.backgroundColor = NAVY;
  Chart.defaults.plugins.tooltip.titleColor = PAPER;
  Chart.defaults.plugins.tooltip.bodyColor = PAPER;
  Chart.defaults.plugins.tooltip.padding = 8;

  function eurK(v) {
    var s = v < 0 ? '-' : '';
    var a = Math.abs(Math.round(v));
    if (a >= 1000000) { return s + '\u20AC' + (a / 1000000).toFixed(2) + 'M'; }
    return s + '\u20AC' + Math.round(a / 1000) + 'k';
  }
  function eurFull(v) {
    return (v < 0 ? '-\u20AC' : '\u20AC') + Math.abs(v).toLocaleString('en-GB');
  }
  function num(v) { return v.toLocaleString('en-GB'); }
  function pct(v) { return (v > 0 ? '+' : '') + v.toFixed(1) + '%'; }
  function sgn(v) {
    return (v > 0 ? '+' : v < 0 ? '-' : '') + '\u20AC' + Math.abs(Math.round(v)).toLocaleString('en-GB');
  }
  function byDiffAsc() {
    return D.families.slice().sort(function (a, b) { return a.diff - b.diff; });
  }

  var charts = [];
  var errors = [];
  window.__galleryCharts = charts;
  window.__galleryErrors = errors;

  // Each panel is built inside step(). If one panel throws, the rest of the page
  // still renders and the failure is recorded instead of killing the gallery.
  function step(name, fn) {
    try { fn(); }
    catch (e) { errors.push(name + ': ' + (e && e.message ? e.message : String(e))); }
  }
  function mk(id, cfg) {
    var el = document.getElementById(id);
    if (!el) { return null; }
    var c = new Chart(el.getContext('2d'), cfg);
    charts.push(c);
    return c;
  }

  /* --- reusable drawing helpers ----------------------------------------
     NOTE: the label settings live in this closure, NOT in chart.options.
     Chart.js resolves a function found under options into a call with a
     null-prototype context object, which then throws "Cannot convert object
     to primitive value" the moment the function does arithmetic on it. Keeping
     the config out of options avoids that trap entirely.

     Placement logic below is explicit about which side of the bar the text
     lands on, because a horizontal bar can grow left or right of its base:
     outside the bar tip if there is room, otherwise inside the bar in paper
     colour, otherwise nothing -- never paper-coloured text on white paper. */
  var tipSeq = 0;
  function hTipLabels(fmt, opts) {
    opts = opts || {};
    var dsi = opts.dataset === undefined ? 0 : opts.dataset;
    var colorFn = opts.colorFn || null;
    var flat = opts.color || INK;
    tipSeq += 1;
    return {
      id: 'hTips' + tipSeq,
      afterDatasetsDraw: function (chart) {
        var ctx = chart.ctx, area = chart.chartArea;
        var meta = chart.getDatasetMeta(dsi);
        if (!meta || !meta.data) { return; }
        ctx.save();
        ctx.font = '600 11px ' + FONT;
        ctx.textBaseline = 'middle';
        meta.data.forEach(function (el, i) {
          var raw = chart.data.datasets[dsi].data[i];
          if (raw === null || raw === undefined || Array.isArray(raw)) { return; }
          var txt = fmt(raw, i);
          if (!txt) { return; }
          var w = ctx.measureText(txt).width;
          var left = Math.min(el.x, el.base), right = Math.max(el.x, el.base);
          var growsRight = el.x >= el.base;
          var tipX = growsRight ? right : left;
          var ink = colorFn ? colorFn(raw, i) : flat;
          ctx.fillStyle = ink;
          if (growsRight) {
            if (tipX + 7 + w <= area.right - 1) {
              ctx.textAlign = 'left';
              ctx.fillText(txt, tipX + 7, el.y);
              return;
            }
          } else if (tipX - 7 - w >= area.left + 1) {
            ctx.textAlign = 'right';
            ctx.fillText(txt, tipX - 7, el.y);
            return;
          }
          // no room outside: put it inside the bar, if the bar is wide enough
          if (right - left > w + 22) {
            ctx.fillStyle = PAPER;
            if (growsRight) { ctx.textAlign = 'right'; ctx.fillText(txt, right - 9, el.y); }
            else { ctx.textAlign = 'left'; ctx.fillText(txt, left + 9, el.y); }
          }
        });
        ctx.restore();
      }
    };
  }
  // Vertical bars: value above the bar tip, dropping inside the bar when the
  // tip is too close to the top of the plot area to hold the text.
  function vTipLabels(fmt, size) {
    tipSeq += 1;
    return {
      id: 'vTips' + tipSeq,
      afterDatasetsDraw: function (chart) {
        var ctx = chart.ctx, area = chart.chartArea;
        var meta = chart.getDatasetMeta(0);
        if (!meta || !meta.data) { return; }
        ctx.save();
        ctx.font = '600 ' + (size || 11) + 'px ' + FONT;
        ctx.textAlign = 'center';
        meta.data.forEach(function (el, i) {
          var txt = fmt(chart.data.datasets[0].data[i], i);
          if (!txt) { return; }
          var h = (size || 11) + 4;
          if (el.y - 5 - h >= area.top) {
            ctx.fillStyle = INK; ctx.textBaseline = 'bottom';
            ctx.fillText(txt, el.x, el.y - 5);
          } else if (el.base - el.y > h + 12) {
            ctx.fillStyle = PAPER; ctx.textBaseline = 'top';
            ctx.fillText(txt, el.x, el.y + 5);
          }
        });
        ctx.restore();
      }
    };
  }
  function vLineAt(value, color, label) {
    return {
      id: 'vLineAt' + value,
      afterDatasetsDraw: function (chart) {
        var s = chart.scales.x, a = chart.chartArea, ctx = chart.ctx;
        if (!s) { return; }
        var x = s.getPixelForValue(value);
        if (x < a.left || x > a.right) { return; }
        ctx.save();
        ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([5, 4]);
        ctx.beginPath(); ctx.moveTo(x, a.top); ctx.lineTo(x, a.bottom); ctx.stroke();
        ctx.setLineDash([]);
        if (label) {
          ctx.font = '600 11px ' + FONT; ctx.fillStyle = color;
          ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
          ctx.fillText(label, x, a.top - 3);
        }
        ctx.restore();
      }
    };
  }
  function hCaptionPlugin(cfg) {
    // Puts the mini-panel's euro + unit line inside the canvas plot area, so the
    // reading travels with the panel even if the canvas is the only thing copied.
    return {
      id: 'hCap',
      afterDraw: function (chart) {
        var ctx = chart.ctx, a = chart.chartArea;
        ctx.save();
        ctx.font = '600 10.5px ' + FONT;
        ctx.fillStyle = cfg.color || INK;
        ctx.textAlign = 'center'; ctx.textBaseline = 'top';
        ctx.fillText(cfg.text, (a.left + a.right) / 2, a.top + 2);
        ctx.restore();
      }
    };
  }

  /* ---- 1. bridge / waterfall ------------------------------------------ */
  step('p1', function () { mk('c1', {
    type: 'bar',
    data: {
      labels: D.bridge.map(function (b) { return b.label; }),
      datasets: [{
        data: D.bridge.map(function (b) { return b.bar; }),
        backgroundColor: D.bridge.map(function (b) {
          if (b.kind === 'total') { return NAVY; }
          return b.value < 0 ? TERRA : '#3f7d68';
        }),
        borderWidth: 0, barPercentage: 0.6
      }]
    },
    options: {
      responsive: true,
      layout: { padding: { top: 26, right: 8 } },
      plugins: {
        legend: { display: false },
        hTip: { dataset: 0 },
        tooltip: { callbacks: { label: function (c) {
          var b = D.bridge[c.dataIndex];
          if (b.kind === 'total') { return b.label + ': ' + eurFull(b.value); }
          return b.label + ': ' + sgn(b.value) + '  (' + eurK(b.start) + ' \u2192 ' + eurK(b.end) + ')';
        } } }
      },
      scales: {
        x: { grid: { display: false }, border: { display: false },
             ticks: { color: NAVY, font: { size: 11, weight: '600' }, maxRotation: 0, autoSkip: false } },
        y: { beginAtZero: true, max: 1300000, grid: { color: GRID }, border: { display: false },
             ticks: { color: MUTED, callback: function (v) { return eurK(v); } } }
      }
    },
    plugins: [{
      id: 'bridgeSteps',
      afterDatasetsDraw: function (chart) {
        var ctx = chart.ctx, meta = chart.getDatasetMeta(0).data;
        var xs = chart.scales.x, ys = chart.scales.y;
        ctx.save();
        ctx.strokeStyle = '#b9b2a4';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        // the connector after bar i sits at the bar's trailing edge, at the
        // running total, and runs to the leading edge of the next bar
        for (var i = 0; i < D.bridge.length - 1; i++) {
          var runningEnd = D.bridge[i].end;
          var y = ys.getPixelForValue(runningEnd);
          var x1 = meta[i].x + (meta[i].width ? meta[i].width / 2 : 20);
          var x2 = meta[i + 1].x - (meta[i + 1].width ? meta[i + 1].width / 2 : 20);
          ctx.beginPath();
          ctx.moveTo(x1, y);
          ctx.lineTo(x2, y);
          ctx.stroke();
        }
        ctx.restore();
      }
    }, {
      id: 'bridgeTips',
      afterDatasetsDraw: function (chart) {
        var ctx = chart.ctx, area = chart.chartArea;
        ctx.save();
        ctx.font = '600 11px ' + FONT;
        ctx.fillStyle = INK; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
        chart.getDatasetMeta(0).data.forEach(function (el, i) {
          var b = D.bridge[i];
          var txt = b.kind === 'total'
            ? eurK(b.value)
            : (b.value > 0 ? '+' : '-') + '\u20AC' + Math.abs(Math.round(b.value / 1000)) + 'k';
          var y = Math.min(el.y, el.base) - 7;
          if (y - 11 < area.top) { return; }
          // skip a label that would run into a neighbouring one on the same row
          var w = ctx.measureText(txt).width;
          var prev = chart.getDatasetMeta(0).data[i - 1];
          if (prev && Math.abs(prev.x - el.x) < (w + ctx.measureText('+EUR000k').width) / 2 + 6) { return; }
          ctx.fillText(txt, el.x, y);
        });
        ctx.restore();
      }
    }]
  }); });

  /* ---- 2. two columns and a difference -------------------------------- */
  step('p2', function () {
    var fs = D.families_by_ly;
    mk('c2', {
      type: 'bar',
      data: {
        labels: fs.map(function (f) { return f.name; }),
        datasets: [
          { label: 'Last year', data: fs.map(function (f) { return f.eur_ly; }),
            backgroundColor: NAVY, borderWidth: 0, barPercentage: 0.82, categoryPercentage: 0.7 },
          { label: 'This year', data: fs.map(function (f) { return f.eur_ty; }),
            backgroundColor: TERRA, borderWidth: 0, barPercentage: 0.82, categoryPercentage: 0.7 }
        ]
      },
      options: {
        responsive: true,
        layout: { padding: { top: 26 } },
        plugins: {
          legend: { position: 'top', align: 'end', labels: { color: NAVY, padding: 12 } },
          tooltip: { callbacks: { label: function (c) { return c.dataset.label + ': ' + eurFull(c.parsed.y); } } }
        },
        scales: {
          x: { grid: { display: false }, border: { display: false },
               ticks: { color: NAVY, font: { size: 11, weight: '600' }, maxRotation: 0, autoSkip: false } },
          y: { beginAtZero: true, max: 430000, grid: { color: GRID }, border: { display: false },
               ticks: { color: MUTED, padding: 6, callback: function (v) { return eurK(v); } } }
        }
      },
      plugins: [{
        id: 'pairDiff',
        afterDatasetsDraw: function (chart) {
          var ctx = chart.ctx, area = chart.chartArea;
          var m0 = chart.getDatasetMeta(0), m1 = chart.getDatasetMeta(1);
          ctx.save();
          ctx.font = '700 11px ' + FONT;
          ctx.fillStyle = BAD; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
          m1.data.forEach(function (el, i) {
            // group centre: between the two columns, so the label can never sit
            // outside the plot area horizontally
            var cx = (m0.data[i].x + el.x) / 2;
            var top = Math.min(el.y, m0.data[i].y);
            if (cx > area.left && cx < area.right && top - 9 > area.top) {
              ctx.fillText(sgn(fs[i].diff), cx, top - 8);
            }
          });
          ctx.restore();
        }
      }]
    });
  });

  /* ---- 3. shortfall ranked -------------------------------------------- */
  step('p3', function () {
    var fs = byDiffAsc();
    mk('c3', {
      type: 'bar',
      data: { labels: fs.map(function (f) { return f.name; }),
              datasets: [{ data: fs.map(function (f) { return f.diff; }),
                           backgroundColor: TERRA, borderWidth: 0, barPercentage: 0.66 }] },
      options: {
        indexAxis: 'y', responsive: true,
        layout: { padding: { right: 74 } },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function (c) {
            var f = fs[c.dataIndex];
            return sgn(f.diff) + '  (' + eurK(f.eur_ly) + ' \u2192 ' + eurK(f.eur_ty) + ', ' + pct(f.units_pct) + ' units)';
          } } }
        },
        scales: {
          x: { min: -82000, max: 0, grid: { color: GRID }, border: { display: false },
               ticks: { color: MUTED, callback: function (v) { return v === 0 ? '\u20AC0' : eurK(v); } } },
          y: { grid: { display: false }, ticks: { color: NAVY, font: { weight: '600' } } }
        }
      },
      plugins: [hTipLabels(function (v) { return sgn(v); })]
    });
  });

  /* ---- 4. the gap in trucks' worth ------------------------------------ */
  step('p4', function () {
    var spend = D.spend_per_truck;
    var fs = byDiffAsc().map(function (f) {
      return { name: f.name, trucks: Math.abs(f.diff) / spend, diff: f.diff };
    });
    mk('c4', {
      type: 'bar',
      data: { labels: fs.map(function (f) { return f.name; }),
              datasets: [{ data: fs.map(function (f) { return +f.trucks.toFixed(2); }),
                           backgroundColor: NAVY, borderWidth: 0, barPercentage: 0.66 }] },
      options: {
        indexAxis: 'y', responsive: true,
        layout: { padding: { right: 84 } },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function (c) {
            var f = fs[c.dataIndex];
            return f.trucks.toFixed(1) + ' trucks\u2019 worth (' + sgn(f.diff) + ' at \u20AC' + num(spend) + ' per truck)';
          } } }
        },
        scales: {
          x: { beginAtZero: true, max: 18, grid: { color: GRID }, border: { display: false },
               ticks: { color: MUTED, callback: function (v) { return v + ' trk'; } } },
          y: { grid: { display: false }, ticks: { color: NAVY, font: { weight: '600' } } }
        }
      },
      plugins: [hTipLabels(function (v) { return v.toFixed(1) + ' trucks'; })]
    });
  });

  /* ---- 5. index, last year = 100 -------------------------------------- */
  step('p5', function () {
    var fs = D.families.slice().sort(function (a, b) { return b.index - a.index; });
    mk('c5', {
      type: 'bar',
      data: { labels: fs.map(function (f) { return f.name; }),
              datasets: [{ data: fs.map(function (f) { return +f.index.toFixed(1); }),
                           backgroundColor: TERRA, borderWidth: 0, barPercentage: 0.66 }] },
      options: {
        indexAxis: 'y', responsive: true,
        layout: { padding: { right: 54, top: 20 } },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function (c) {
            var f = fs[c.dataIndex];
            return 'index ' + f.index.toFixed(1) + '  (' + eurK(f.eur_ly) + ' \u2192 ' + eurK(f.eur_ty) + ')';
          } } }
        },
        scales: {
          x: { beginAtZero: true, max: 112, grid: { color: GRID }, border: { display: false },
               ticks: { color: MUTED, stepSize: 25 } },
          y: { grid: { display: false }, ticks: { color: NAVY, font: { weight: '600' } } }
        }
      },
      plugins: [hTipLabels(function (v) { return v.toFixed(1); },
                           { colorFn: function (v) { return v < 100 ? NAVY : INK; } }),
                vLineAt(100, NAVY, 'last year = 100')]
    });
  });

  /* ---- 6. dumbbell ----------------------------------------------------- */
  step('p6', function () {
    var fs = D.families_by_ly;
    var half = 2400; // half-height of a dot, in euro units, so the ends read round
    mk('c6', {
      type: 'bar',
      data: {
        labels: fs.map(function (f) { return f.name; }),
        datasets: [
          { label: 'Move', data: fs.map(function (f) { return [Math.min(f.eur_ly, f.eur_ty), Math.max(f.eur_ly, f.eur_ty)]; }),
            backgroundColor: '#c9c2b4', borderWidth: 0, grouped: false, barThickness: 3 },
          { label: 'Last year', data: fs.map(function (f) { return [f.eur_ly - half, f.eur_ly + half]; }),
            backgroundColor: NAVY, borderWidth: 0, grouped: false, barThickness: 13, borderRadius: 6 },
          { label: 'This year', data: fs.map(function (f) { return [f.eur_ty - half, f.eur_ty + half]; }),
            backgroundColor: TERRA, borderWidth: 0, grouped: false, barThickness: 13, borderRadius: 6 }
        ]
      },
      options: {
        indexAxis: 'y', responsive: true,
        layout: { padding: { right: 96, left: 8 } },
        plugins: {
          legend: { position: 'top', align: 'end', labels: { color: NAVY, padding: 12 } },
          tooltip: { callbacks: { label: function (c) {
            var f = fs[c.dataIndex];
            if (c.datasetIndex === 1) { return 'Last year: ' + eurFull(f.eur_ly); }
            if (c.datasetIndex === 2) { return 'This year: ' + eurFull(f.eur_ty); }
            return 'Move: ' + sgn(f.diff) + '  (' + pct((f.eur_ty / f.eur_ly - 1) * 100) + ')';
          } } }
        },
        scales: {
          x: { beginAtZero: true, max: 400000, grid: { color: GRID }, border: { display: false },
               ticks: { color: MUTED, callback: function (v) { return eurK(v); } } },
          y: { grid: { display: false }, ticks: { color: NAVY, font: { weight: '600' } } }
        }
      },
      plugins: [{
        id: 'dumbbellTip',
        afterDatasetsDraw: function (chart) {
          var ctx = chart.ctx, a = chart.chartArea;
          var mTY = chart.getDatasetMeta(2), mLY = chart.getDatasetMeta(1);
          ctx.save();
          ctx.font = '600 11px ' + FONT;
          ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
          mTY.data.forEach(function (el, i) {
            var x = Math.max(el.x, el.base) + 13;
            var txt = sgn(fs[i].diff) + '  (' + pct((fs[i].eur_ty / fs[i].eur_ly - 1) * 100) + ')';
            if (x + ctx.measureText(txt).width <= a.right) {
              ctx.fillStyle = BAD;
              ctx.fillText(txt, x, (el.y + mLY.data[i].y) / 2);
            }
          });
          ctx.restore();
        }
      }]
    });
  });

  /* ---- 7. bullet ------------------------------------------------------- */
  step('p7', function () {
    var fs = D.families_by_ly;
    var b = D.normal_band_pct / 100;
    mk('c7', {
      type: 'bar',
      data: {
        labels: fs.map(function (f) { return f.name; }),
        datasets: [
          { label: 'Assumed normal range (\u00B1' + D.normal_band_pct + '%)',
            data: fs.map(function (f) { return [f.eur_ly * (1 - b), f.eur_ly * (1 + b)]; }),
            backgroundColor: '#e8e2d6', borderWidth: 0, grouped: false, barThickness: 26, borderRadius: 2 },
          { label: 'This year',
            data: fs.map(function (f) { return f.eur_ty; }),
            backgroundColor: NAVY, borderWidth: 0, grouped: false, barThickness: 13, borderRadius: 2 },
          { label: 'Last year',
            data: fs.map(function (f) { return [f.eur_ly - 1300, f.eur_ly + 1300]; }),
            backgroundColor: TERRA, borderWidth: 0, grouped: false, barThickness: 30 }
        ]
      },
      options: {
        indexAxis: 'y', responsive: true,
        layout: { padding: { right: 106 } },
        plugins: {
          legend: { position: 'top', align: 'end', labels: { color: NAVY, padding: 12 } },
          tooltip: { callbacks: { label: function (c) {
            var f = fs[c.dataIndex];
            if (c.datasetIndex === 1) { return 'This year: ' + eurFull(f.eur_ty) + '  (' + pct((f.eur_ty / f.eur_ly - 1) * 100) + ')'; }
            if (c.datasetIndex === 2) { return 'Last year: ' + eurFull(f.eur_ly); }
            return 'Assumed normal range: ' + eurK(f.eur_ly * (1 - b)) + ' \u2013 ' + eurK(f.eur_ly * (1 + b));
          } } }
        },
        scales: {
          x: { beginAtZero: true, max: 400000, grid: { color: GRID }, border: { display: false },
               ticks: { color: MUTED, callback: function (v) { return eurK(v); } } },
          y: { grid: { display: false }, ticks: { color: NAVY, font: { weight: '600' } } }
        }
      },
      plugins: [{
        id: 'bulletTip',
        afterDatasetsDraw: function (chart) {
          var ctx = chart.ctx, a = chart.chartArea, meta = chart.getDatasetMeta(1);
          ctx.save();
          ctx.font = '600 11px ' + FONT;
          ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
          meta.data.forEach(function (el, i) {
            var f = fs[i];
            var txt = eurK(f.eur_ty) + '  ' + pct((f.eur_ty / f.eur_ly - 1) * 100);
            var x = Math.max(el.x, el.base) + 9;
            if (x + ctx.measureText(txt).width <= a.right) {
              ctx.fillStyle = (f.eur_ty < f.eur_ly * (1 - b)) ? BAD : INK;
              ctx.fillText(txt, x, el.y);
            }
          });
          ctx.restore();
        }
      }]
    });
  });

  /* ---- 8. small multiples --------------------------------------------- */
  step('p8', function () {
    var fs = D.families_by_ly;
    var host = document.getElementById('sm-grid');
    if (!host) { return; }
    fs.forEach(function (f) {
      var box = document.createElement('div');
      box.className = 'sm';
      var cid = 'sm-' + f.name.replace(/[^A-Za-z]/g, '');
      box.innerHTML =
        '<div class="sm-title">' + f.name + '</div>' +
        '<div class="sm-chart"><canvas id="' + cid + '"></canvas></div>' +
        '<div class="sm-foot"><b>' + eurK(f.eur_ty) + '</b> from ' + eurK(f.eur_ly) +
        ' \u00B7 ' + sgn(f.diff) + ' \u00B7 ' + num(f.units_ty) + ' units (' + pct(f.units_pct) + ')</div>';
      host.appendChild(box);
      var cv = box.querySelector('canvas');
      var c = new Chart(cv.getContext('2d'), {
        type: 'bar',
        data: { labels: ['Last year', 'This year'],
                datasets: [{ data: [f.eur_ly, f.eur_ty], backgroundColor: [NAVY, TERRA], borderWidth: 0, barPercentage: 0.7 }] },
        options: {
          responsive: true,
          layout: { padding: { top: 20 } },
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: function (ct) { return ct.label + ': ' + eurFull(ct.parsed.y); } } }
          },
          scales: {
            x: { grid: { display: false }, border: { display: false }, ticks: { color: INK, font: { size: 10.5 } } },
            y: { beginAtZero: true, max: 400000, grid: { color: GRID }, border: { display: false },
                 ticks: { color: MUTED, font: { size: 10 }, stepSize: 200000,
                          callback: function (v) { return v === 0 ? '0' : eurK(v); } } }
          }
        },
        plugins: [{
          id: 'smTip' + cid,
          afterDatasetsDraw: function (chart) {
            var ctx = chart.ctx, area = chart.chartArea;
            ctx.save();
            ctx.font = '600 10.5px ' + FONT;
            ctx.fillStyle = INK; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
            chart.getDatasetMeta(0).data.forEach(function (el, i) {
              var txt = eurK(chart.data.datasets[0].data[i]);
              if (el.y - 4 - 15 < area.top) { return; }
              ctx.fillText(txt, el.x, el.y - 4);
            });
            ctx.restore();
          }
        }]
      });
      charts.push(c);
    });
  });

  /* ---- 9. two-sided deviation from the distributor's own average ------ */
  step('p9', function () {
    var fs = D.families.slice().sort(function (a, b) { return b.deviation - a.deviation; });
    mk('c9', {
      type: 'bar',
      data: { labels: fs.map(function (f) { return f.name; }),
              datasets: [{ data: fs.map(function (f) { return f.deviation; }),
                           backgroundColor: fs.map(function (f) { return f.deviation < 0 ? BAD : GOOD; }),
                           borderWidth: 0, barPercentage: 0.66 }] },
      options: {
        indexAxis: 'y', responsive: true,
        layout: { padding: { left: 16, right: 66 } },
        plugins: {
          legend: { display: false },
          hTip: { dataset: 0 },
          tooltip: { callbacks: { label: function (c) {
            var f = fs[c.dataIndex];
            return sgn(f.deviation) + '  against the all-family average move of ' +
              D.avg_move_pct.toFixed(1) + '%';
          } } }
        },
        scales: {
          x: { min: -12000, max: 7000, grid: { color: GRID }, border: { display: false },
               ticks: { color: MUTED, callback: function (v) { return v === 0 ? 'average' : eurK(v); } } },
          y: { grid: { display: false }, ticks: { color: NAVY, font: { weight: '600' } } }
        }
      },
      plugins: [hTipLabels(function (v) { return sgn(v); }), {
        id: 'zeroLine',
        afterDatasetsDraw: function (chart) {
          var x = chart.scales.x.getPixelForValue(0), a = chart.chartArea, ctx = chart.ctx;
          ctx.save(); ctx.strokeStyle = NAVY; ctx.lineWidth = 1.5;
          ctx.beginPath(); ctx.moveTo(x, a.top); ctx.lineTo(x, a.bottom); ctx.stroke();
          ctx.restore();
        }
      }]
    });
  });

  /* ---- 10. table with in-cell bars ------------------------------------ */
  step('p10', function () {
    var host = document.getElementById('tbl-body');
    if (!host) { return; }
    var fs = D.families.slice().sort(function (a, b) { return b.eur_ty - a.eur_ty; });
    var max = fs[0].eur_ty;
    var html = '';
    fs.forEach(function (f, i) {
      var w = Math.max(2, Math.round(f.eur_ty / max * 100));
      html += '<tr>' +
        '<td class="num" style="color:#8b93a3">' + (i + 1) + '</td>' +
        '<td class="l">' + f.name + '</td>' +
        '<td class="num"><div class="cellbar-wrap"><span>' + num(f.eur_ty) + '</span><span class="cellbar" style="width:' + w + '%"></span></div></td>' +
        '<td class="num">' + num(f.eur_ly) + '</td>' +
        '<td class="num neg">' + sgn(f.diff) + '</td>' +
        '<td class="num">' + num(f.units_ty) + '</td>' +
        '<td class="num neg">' + pct(f.units_pct) + '</td>' +
        '</tr>';
    });
    html += '<tr class="total">' +
      '<td></td><td class="l">All six families</td>' +
      '<td class="num">' + num(D.eur_ty) + '</td>' +
      '<td class="num">' + num(D.eur_ly) + '</td>' +
      '<td class="num">' + sgn(D.net_move) + '</td>' +
      '<td class="num">' + num(D.units_ty) + '</td>' +
      '<td class="num">' + pct((D.units_ty / D.units_ly - 1) * 100) + '</td>' +
      '</tr>';
    host.innerHTML = html;
    var note = document.getElementById('tbl-note');
    if (note) {
      note.innerHTML = 'Bars are drawn against the largest single family in this table (' + num(max) +
        '), not against the total, so the six bars are comparable to each other.';
    }
  });

  window.__galleryReady = true;
  if (errors.length) {
    var box = document.getElementById('build-errors');
    if (box) {
      box.style.display = 'block';
      box.innerHTML = '<b>Panels that failed to draw on this render:</b><br>' + errors.join('<br>');
    }
  }
})();
"""

FICTIVE_BADGE = '<span class="badge">FICTIVE</span>'


def panel(n: int, title: str, kicker: str, body: str, caption: str, wide: bool = False) -> str:
    cls = "panel wide" if wide else "panel"
    return f"""  <section class="{cls}" id="p{n}">
    <div class="p-head">
      <h2 class="p-title"><span class="n">{n}</span>{title}</h2>
      {FICTIVE_BADGE}
    </div>
    <p class="p-kicker">{kicker}</p>
    <div class="p-body">
{body}
    </div>
    <p class="p-cap">{caption}</p>
  </section>
"""


def build_html() -> str:
    d = PAYLOAD
    chartjs = CHARTJS.read_text(encoding="utf-8")
    assert "sourceMappingURL" not in chartjs, "chart.umd.min.js carries a source map reference"

    tot_ly = f"{d['eur_ly']:,}"
    tot_ty = f"{d['eur_ty']:,}"
    net = f"{d['net_move']:,}"
    fake = sorted(d["families"], key=lambda f: -f["eur_ty"])

    glyph = ('<svg viewBox="0 0 26 14" width="24" height="13" aria-hidden="true">'
             '<path d="M1 2h14v7.5H1z" fill="#15233c"/>'
             '<path d="M15 4.6h4.1l3.4 3.6v1.3H15z" fill="#c0552d"/>'
             '<circle cx="5.6" cy="11.1" r="2" fill="#15233c"/>'
             '<circle cx="18.7" cy="11.1" r="2" fill="#15233c"/></svg>')
    truck_grid = "\n".join("        " + glyph for _ in range(48))

    panels = []

    panels.append(panel(
        1,
        "How did &euro;1.11M of billing turn into &euro;0.89M, and which step took the money out?",
        f"Billed &euro;{tot_ly} last year, &euro;{tot_ty} this year. The four middle bars decompose the &euro;{abs(d['net_move']):,} move; the dashed line is the running total after each step. "
        f"Volume &minus;&euro;295k, price +&euro;38k, mix +&euro;12k, fleet +&euro;30k &mdash; those four net to &euro;215k, so the step to the billed &euro;{tot_ty} carries a &euro;1k residual that is too small to draw at this scale.",
        """      <div class="chart-box tall"><canvas id="c1"></canvas></div>""",
        "<b>Strength:</b> it starts and ends on money that was actually billed, so every step has a size you can argue about. "
        "<b>Weakness:</b> the four middle bars are computed, not billed, and the &euro;1k they leave unexplained is disclosed in words, not shown. "
        "A positive Fleet step on a fleet that shrank by 1,093 trucks is a question this form raises and cannot answer.",
    ))

    panels.append(panel(
        2,
        "For each service family, what did we bill this year against last year, and how big is the difference?",
        "Two billed columns per family on one shared euro scale, with the difference printed above each pair.",
        """      <div class="chart-box tall"><canvas id="c2"></canvas></div>""",
        "<b>Strength:</b> only one derived number per family (the difference); the two columns are as billed, so nothing can be argued with. "
        "<b>Weakness:</b> twelve bars on one canvas at panel size &mdash; the eye reads the pairs, not the individual heights, so a &euro;6k move and a &euro;20k move look alike.",
    ))

    panels.append(panel(
        3,
        "How far short of last year is each family, in euros, worst first?",
        "One signed number per family, ranked. All six are below last year, so every bar points the same way.",
        """      <div class="chart-box"><canvas id="c3"></canvas></div>""",
        "<b>Strength:</b> ranks the euro damage in the order you would act on it, and nothing else competes for attention. "
        "<b>Weakness:</b> it hides size. Driveline&rsquo;s &euro;11k hole is a 19.6% loss of that family; Engine parts&rsquo; &euro;22k hole is 15.6%. Ranked by euros alone, the smaller family looks harmless.",
    ))

    panels.append(panel(
        4,
        "How many trucks&rsquo; worth of parts is the &euro;216k shortfall?",
        f"Same shortfall, counted in trucks. Assumed annual parts spend per truck <b>&euro;{d['spend_per_truck']:,}</b> (a fictive assumption, not a measured average). "
        f"Fleet in this fictive case: {d['uio_ly']:,} trucks last year, {d['uio_ty']:,} this year.",
        f"""      <div class="truck-lead">
        <div class="truck-big">{d['net_trucks']:.0f}<small> trucks&rsquo; worth</small></div>
        <div class="truck-say">&euro;{abs(d['net_move']):,} short of last year, at &euro;{d['spend_per_truck']:,} of parts a year per truck.
        One glyph below is one truck. At &euro;3,000 per truck the same gap is 72 trucks; at &euro;6,000 it is 36.</div>
      </div>
      <div class="truck-grid">
{truck_grid}
      </div>
      <div class="legend-inline">48 glyphs &times; &euro;{d['spend_per_truck']:,} = &euro;216,000. Below, the same gap split by family, still in trucks.</div>
      <div class="chart-box" style="height:236px"><canvas id="c4"></canvas></div>""",
        "<b>Strength:</b> an abstract euro gap becomes something countable in the yard, which is how the business actually feels a shortfall. "
        "<b>Weakness:</b> the whole panel rests on one invented number. Change &euro;4,500 and the headline moves &plusmn;50%, and it says nothing about which parts went missing.",
    ))

    panels.append(panel(
        5,
        "How big is each family&rsquo;s move, with last year set to 100?",
        "The same movement with no arithmetic needed. The dashed line is last year = 100.",
        """      <div class="chart-box"><canvas id="c5"></canvas></div>""",
        "<b>Strength:</b> the size of each move in one number, and it compares families fairly whatever their size. "
        "<b>Weakness:</b> it removes the money. Index 80 on the &euro;372k family and index 80 on the &euro;56k family look identical, yet the euro consequence differs by more than &euro;60k.",
    ))

    panels.append(panel(
        6,
        "Where did each family start, where did it finish, and how far did it travel?",
        "A dot for last year and a dot for this year, joined by the distance between them, in euros.",
        """      <div class="chart-box tall"><canvas id="c6"></canvas></div>""",
        "<b>Strength:</b> shows level and movement at the same time, so a small family with a long line is not mistaken for a quiet one. "
        "<b>Weakness:</b> two dots per family, and no reason given. A long line is not automatically the biggest euro loss &mdash; Driveline travels furthest relative to its own size and is the smallest hole on the page.",
    ))

    panels.append(panel(
        7,
        "Which families fell outside the normal year-on-year range?",
        f"The bar is this year&rsquo;s billed euro, the dark mark is last year, and the grey band is an assumed normal range of &plusmn;{d['normal_band_pct']:.0f}% around last year (fictive, not a measured tolerance).",
        """      <div class="chart-box tall"><canvas id="c7"></canvas></div>""",
        "<b>Strength:</b> answers &ldquo;how bad is bad&rdquo; in one look, by putting this year against both a reference and a range, so only real outliers draw the eye. "
        "<b>Weakness:</b> the band is a made-up tolerance. Widen it to &plusmn;25% and every family is normal, so the form is only as honest as the assumption behind it.",
    ))

    panels.append(panel(
        8,
        "Which families moved most, all seen on one common euro scale?",
        "Six mini panels, last year against this year, every one on the same &euro;0&ndash;&euro;400k axis so the heights can be compared across families.",
        """      <div class="sm-grid" id="sm-grid"></div>""",
        "<b>Strength:</b> a shared scale means the big movers stand out and no family can be made to look dramatic by its own axis. Each mini panel carries its own euro and unit line underneath. "
        "<b>Weakness:</b> small panels, so you read the shape rather than the value, and every family under &euro;60k is cramped against a &euro;400k ceiling.",
        wide=True,
    ))

    panels.append(panel(
        9,
        "Which families are out of line with this distributor&rsquo;s own average move, and in which direction?",
        f"Reference: the all-family average move of {d['avg_move_pct']:.1f}%, applied to each family&rsquo;s last-year billing. Right of the line is better than the distributor&rsquo;s own average, left is worse.",
        """      <div class="chart-box"><canvas id="c9"></canvas></div>""",
        "<b>Strength:</b> separates &ldquo;down like everything else&rdquo; from &ldquo;down in a way that is out of line&rdquo;, in euros, in both directions. "
        "<b>Weakness:</b> it measures against this distributor&rsquo;s own average, not against what was achievable. Electrical looks like the only real failure and still holds the &euro;9.8k flag, while Filtration&rsquo;s &euro;74k &mdash; the largest single loss &mdash; reads as normal.",
    ))

    panels.append(panel(
        10,
        "The ranked detail: billed this year, billed last year, the difference, and the units behind it.",
        "A plain table ranked by this year&rsquo;s billing. The bar inside the first euro column is proportionate to the largest family in the table.",
        """      <table class="gal">
        <thead>
          <tr>
            <th class="l" style="width:34px">#</th>
            <th class="l">Service family</th>
            <th>Billed this year (&euro;)</th>
            <th>Billed last year (&euro;)</th>
            <th>Difference (&euro;)</th>
            <th>Units this year</th>
            <th>Units vs last year</th>
          </tr>
        </thead>
        <tbody id="tbl-body"></tbody>
      </table>
      <p class="table-note" id="tbl-note"></p>""",
        "<b>Strength:</b> everything in one place, ranked, with units beside the euro so the money cannot be read on its own. Electrical lost 58.9% of its units but only 28.4% of its euro &mdash; the unit column is what exposes that. "
        "<b>Weakness:</b> a table asks to be read, not seen. There is no shape and no first-glance story, which is why in practice it travels with one of the forms above rather than alone.",
        wide=True,
    ))

    body = "\n".join(panels)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chart forms gallery &mdash; ten ways to present the same aftersales move (FICTIVE)</title>
<style>
{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <h1>Ten ways to present the same aftersales move</h1>
    <p class="sub">One fictive distributor, one fictive period, six service families, one movement. The numbers never change across the panels &mdash; only the form does.</p>
    <div><span class="fictive-banner">FICTIVE</span><span>All figures invented for form comparison. Not ISZE, not a distributor, not a market.</span></div>
    <p class="note"><b>Read it this way:</b> pick the forms that let you conclude something correct fastest, and say which ones you want on real numbers.
    Every panel states its own weakness underneath, because a form you cannot argue against is a form that will mislead you on the day the data is less tidy.</p>
    <p class="note" style="border-left-color:#15233c;background:#eef2f7"><b>The fictive situation:</b> billed <b>&euro;{tot_ly}</b> across six service families last year on {d['uio_ly']:,} trucks, and <b>&euro;{tot_ty}</b> this year on {d['uio_ty']:,} trucks &mdash; a move of <b>&euro;{net}</b>.
    Units behind the money: {d['units_ly']:,} last year, {d['units_ty']:,} this year. The decomposition used in panel 1 is volume &minus;&euro;295k, price +&euro;38k, mix +&euro;12k, fleet +&euro;30k.</p>
  </header>

  <nav class="index">
    <h2>The ten forms</h2>
    <ol>
      <li><a href="#p1"><b>1</b>Bridge / waterfall</a></li>
      <li><a href="#p2"><b>2</b>Two columns and a difference</a></li>
      <li><a href="#p3"><b>3</b>Shortfall in euros</a></li>
      <li><a href="#p4"><b>4</b>The gap in trucks&rsquo; worth</a></li>
      <li><a href="#p5"><b>5</b>Index, last year = 100</a></li>
      <li><a href="#p6"><b>6</b>Dumbbell / connected dot</a></li>
      <li><a href="#p7"><b>7</b>Bullet chart</a></li>
      <li><a href="#p8"><b>8</b>Small multiples</a></li>
      <li><a href="#p9"><b>9</b>Two-sided deviation</a></li>
      <li><a href="#p10"><b>10</b>Table with in-cell bars</a></li>
    </ol>
  </nav>

  <div class="grid">
{body}
  </div>
  <div id="build-errors" style="display:none;margin-top:18px;border-left:4px solid #a63a2a;background:#fdeee7;padding:10px 12px;font-size:13px"></div>
</div>

<script type="application/json" id="fictive-data">
{json.dumps(d, indent=1)}
</script>
<script>
{chartjs}
</script>
<script>
{APP_JS}
</script>
</body>
</html>
"""


def main() -> int:
    html = build_html()
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"  bytes: {OUT.stat().st_size:,}")
    print(f"  families: {len(FAMILIES)}  eur_ly={EUR_LY:,}  eur_ty={EUR_TY:,}  net={NET_MOVE:,}")
    print(f"  units: {UNITS_LY:,} -> {UNITS_TY:,}   uio: {UIO_LY:,} -> {UIO_TY:,}")
    print(f"  chart.js inlined: {CHARTJS.name} ({CHARTJS.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
