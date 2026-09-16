"""Shared Tier A dashboard shell — navy/terra ISZE house style (Mode B).

Cloned from ISZE_OS_Data_Map.html + UTI replenishment H2 patterns.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
AIM_TOP_PN = DERIVED / "sellout_aim_top_pn_2025.csv"
CHART_JS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"

DB_ORDER = ("ITUK", "UTI", "IRELAND", "IUK", "GREECE")

TIER_A_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:15px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}
.hero{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:42px 28px 28px}
.hero-inner{max-width:1180px;margin:0 auto}
.brand{font-family:Georgia,serif;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#c9d4e6;margin-bottom:14px}
.hero h1{color:#fff;font-size:34px;line-height:1.12;margin:0 0 12px;font-weight:400}
.hero .rule{width:64px;height:3px;background:#c0552d;margin:0 0 16px}
.hero .lead{max-width:760px;font-size:15.5px;color:#d5dce8;margin:0 0 22px}
.hero-kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.hk{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);padding:14px 16px;position:relative;cursor:help}
.hk .v{font-size:28px;font-weight:700;letter-spacing:-.5px;color:#fff}
.hk .v.sm{font-size:20px;line-height:1.2}
.hk .l{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#aeb9cb;margin-top:4px}
.hk .n{font-size:12px;color:#9aa8bd;margin-top:6px;line-height:1.35}
.hk .tip{display:none;position:absolute;left:0;top:calc(100% + 8px);width:min(320px,70vw);
  background:#15233c;color:#f7f4ee;border-top:3px solid #c0552d;padding:12px 14px;
  font-size:12.5px;line-height:1.45;z-index:50;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.hk:hover .tip,.hk:focus-within .tip{display:block}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;max-width:1180px;margin:0 auto;padding:16px 28px;background:#f7f4ee;border-bottom:1px solid #d9d3c8;position:sticky;top:0;z-index:20}
.toolbar label{font-size:13px;color:#6b6256}
.toolbar input,.toolbar select{padding:7px 10px;font:inherit;font-size:13px;border:1px solid #d9d3c8;background:#fff}
.filters{display:flex;flex-wrap:wrap;gap:8px}
.filters button{appearance:none;border:1px solid #d9d3c8;background:#fff;color:#222;padding:7px 12px;font:inherit;font-size:13px;cursor:pointer}
.filters button.on{background:#15233c;color:#f7f4ee;border-color:#15233c}
.filters button:hover{border-color:#c0552d}
.wrap{max-width:1180px;margin:0 auto;padding:28px 28px 80px}
h2{font-size:22px;margin:8px 0 8px;padding-bottom:8px;border-bottom:2px solid #1a2b4a}
h2 .no{color:#c0552d}
.lead{color:#6b6256;margin:0 0 18px;max-width:820px}
.callout{border-left:3px solid #c0552d;background:#fff;padding:14px 16px;margin:0 0 20px;font-size:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.card{background:#fff;border:1px solid #d9d3c8;padding:18px 18px 14px}
.card h3{font-size:15px;margin:0 0 6px;font-family:Georgia,serif}
.card .cap{font-size:12.5px;color:#6b6256;margin:0 0 12px}
.chart-wrap{position:relative;width:100%;min-height:280px;height:300px}
.chart-wrap canvas{display:block;width:100%!important;min-height:280px}
.fallback-bars{display:flex;flex-direction:column;gap:6px;padding:4px 0}
.fb-row{display:grid;grid-template-columns:minmax(60px,28%) 1fr minmax(56px,18%);gap:8px;align-items:center;font-size:12px}
.fb-lb{color:#52514e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fb-track{background:#eceae4;height:18px;border-radius:2px;overflow:hidden}
.fb-bar{height:100%;min-width:2px;border-radius:2px}
.fb-val{text-align:right;font-variant-numeric:tabular-nums;color:#222}
.chart-status{margin-top:12px;padding:10px 14px;font-size:12px;color:#8a3030;background:#f8e4dc;border-left:3px solid #c0552d;display:none}
.chart-status.show{display:block}
table.matrix{width:100%;border-collapse:collapse;font-size:13px;background:#fff}
.matrix thead th{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;position:sticky;top:56px;z-index:6;cursor:pointer;user-select:none}
.matrix thead th.num,.matrix td.num{text-align:right;font-variant-numeric:tabular-nums}
.matrix td{padding:8px 10px;border-bottom:1px solid #e8e4dc;color:#222;vertical-align:top}
.matrix tbody tr:nth-child(even) td{background:#faf8f4;color:#222}
.matrix tbody tr.is-hide{display:none}
.matrix tbody tr:hover td{background:#eef3f9}
.table-scroll{overflow-x:auto;margin-bottom:8px;-webkit-overflow-scrolling:touch}
.matrix th[data-key="bucket"],.matrix td.bucket{min-width:200px;white-space:nowrap}
.tabs{display:flex;gap:0;max-width:1180px;margin:0 auto;padding:0 28px;background:#f7f4ee;border-bottom:1px solid #d9d3c8;position:sticky;top:0;z-index:25}
.tabs button{appearance:none;border:0;background:transparent;padding:14px 20px;font:inherit;font-size:14px;color:#6b6256;cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-1px}
.tabs button.active{color:#1a2b4a;font-weight:600;border-bottom-color:#c0552d}
.tabs button:hover{color:#1a2b4a}
.panel{display:none}
.panel.active{display:block}
.monday-list{margin:0;padding:0;list-style:none}
.monday-list li{background:#fff;border:1px solid #d9d3c8;border-left:3px solid #c0552d;padding:10px 14px;margin-bottom:8px;font-size:14px}
.pill{display:inline-block;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;padding:2px 8px;font-weight:700;white-space:nowrap}
.pill.leak{background:#f8e4dc;color:#8a3030}
.pill.over{background:#eceae4;color:#444}
.pill.bal{background:#e4f5ee;color:#1d6b4f}
.pill.act{background:#dcecfc;color:#1a4a7a}
.pill.hold{background:#eceae4;color:#666}
.pill.aim{background:#eef3f9;color:#1a2b4a;font-size:10px;text-transform:none;letter-spacing:0;font-weight:600}
.row-count{font-size:13px;color:#6b6256;margin-left:auto}
.foot{margin-top:40px;padding-top:14px;border-top:1px solid #d9d3c8;font-size:11.5px;color:#6b6256;line-height:1.65}
@media(max-width:900px){.hero-kpis,.grid2{grid-template-columns:1fr}.hero h1{font-size:26px}.wrap,.hero,.toolbar,.tabs{padding-left:16px;padding-right:16px}}
@media print{.tabs,.toolbar .filters{display:none}.panel{display:block!important}}
"""


def json_embed(obj: Any) -> str:
    """JSON safe for <script> embedding — no NaN/Infinity (breaks JSON.parse)."""

    def _clean(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (float, np.floating)):
            if math.isnan(v) or math.isinf(v):
                return None
            return float(v)
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.bool_, bool)):
            return bool(v)
        if isinstance(v, dict):
            return {str(k): _clean(val) for k, val in v.items()}
        if isinstance(v, (list, tuple)):
            return [_clean(x) for x in v]
        if pd.isna(v):
            return None
        return v

    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


def load_chart_js() -> str:
    if CHART_JS.is_file():
        raw = CHART_JS.read_text(encoding="utf-8", errors="ignore")
        # Prevent accidental </script> break if ever present in bundle
        return raw.replace("</script>", "<\\/script>")
    return ""


TIER_A_CHART_JS = """
const _chartErrors=[];
function reportChartError(id, err){
  const msg=(id||'chart')+': '+(err&&err.message?err.message:String(err));
  _chartErrors.push(msg);
  console.error(msg, err);
  const el=document.getElementById('chartStatus');
  if(el){ el.textContent='Chart init: '+_chartErrors.join(' · '); el.classList.add('show'); }
}
function renderFallbackBars(wrap, labels, values, color, fmt){
  if(!wrap) return;
  const f=fmt||((v)=>String(v));
  const nums=values.map(v=>Math.max(Number(v)||0,0));
  const max=Math.max(...nums,1);
  wrap.innerHTML='<div class="fallback-bars">'+labels.map((lb,i)=>{
    const v=nums[i]||0;
    const pct=Math.max(2,Math.round(100*v/max));
    return '<div class="fb-row"><span class="fb-lb">'+esc(lb)+'</span><div class="fb-track"><div class="fb-bar" style="width:'+pct+'%;background:'+(color||'#c0552d')+'"></div></div><span class="fb-val">'+f(v)+'</span></div>';
  }).join('')+'</div>';
}
function safeChart(store, key, canvasId, config, fallback){
  const canvas=document.getElementById(canvasId);
  const wrap=canvas?canvas.closest('.chart-wrap'):null;
  if(!canvas){ reportChartError(key, new Error('missing #'+canvasId)); return null; }
  if(typeof Chart==='undefined'){
    if(wrap&&fallback) fallback(wrap);
    reportChartError(key, new Error('Chart.js not loaded'));
    return null;
  }
  try{
    if(store[key]){ store[key].destroy(); delete store[key]; }
    const inst=new Chart(canvas, config);
    store[key]=inst;
    return inst;
  }catch(e){
    if(wrap&&fallback) fallback(wrap);
    reportChartError(key, e);
    return null;
  }
}
"""


def norm_pn_scalar(value: Any) -> str:
    s = str(value or "").strip().lstrip("0")
    return s or ""


def load_aim_by_pn() -> dict[str, dict[str, str]]:
    """PN → AIM L1 / subgroup / PMS category (network sell-out taxonomy)."""
    if not AIM_TOP_PN.is_file():
        return {}
    df = pd.read_csv(AIM_TOP_PN, dtype=str, low_memory=False)
    out: dict[str, dict[str, str]] = {}
    for _, r in df.iterrows():
        pn = norm_pn_scalar(r.get("part_number"))
        if not pn or pn in out:
            continue
        out[pn] = {
            "aim_l1": str(r.get("aim_l1") or "").strip(),
            "subgroup": str(r.get("product_subgroup") or r.get("report_subgroup") or "").strip(),
            "pms": str(r.get("pms_category") or "").strip(),
        }
    return out


def aim_chip(pn: str, aim_map: dict[str, dict[str, str]], fallback: str = "") -> str:
    if fallback and fallback.startswith("AIM:"):
        return fallback.replace("AIM:", "").strip()
    hit = aim_map.get(norm_pn_scalar(pn), {})
    if hit.get("aim_l1") and hit["aim_l1"] != "Unknown":
        return hit["aim_l1"]
    if hit.get("subgroup"):
        return hit["subgroup"]
    if hit.get("pms"):
        return hit["pms"]
    return fallback or "—"


def signal_pill_class(signal: str) -> str:
    s = (signal or "").lower()
    if "leakage" in s:
        return "leak"
    if "overstock" in s:
        return "over"
    if "balanced" in s:
        return "bal"
    return "act"


def action_pill_class(action: str) -> str:
    a = (action or "").upper()
    if "LEAKAGE" in a:
        return "leak"
    if "HOLD" in a:
        return "hold"
    return "act"


def safe_float(v: Any, ndigits: int | None = 2) -> float | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, ndigits) if ndigits is not None else f


TIER_A_TABLE_JS = """
function fmtInt(n){if(n==null||n==='')return '—';return Math.round(Number(n)).toLocaleString('en-GB');}
function fmtNum(n,d){if(n==null||n==='')return '—';return Number(n).toFixed(d==null?2:d);}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');}
function pill(cls,txt){return '<span class="pill '+cls+'">'+esc(txt)+'</span>';}
let sortKey='qty_gap', sortDir=-1;
function sortRows(rows,key){
  if(sortKey===key) sortDir=-sortDir; else {sortKey=key; sortDir=(key==='pn'||key==='db'||key==='signal'||key==='action')?1:-1;}
  document.querySelectorAll('.matrix thead th').forEach(th=>{
    th.textContent=th.dataset.label+(sortKey===th.dataset.key?(sortDir>0?' ▲':' ▼'):'');
  });
  renderTable();
}
function bindSort(){document.querySelectorAll('.matrix thead th[data-key]').forEach(th=>{
  th.dataset.label=th.textContent; th.onclick=()=>sortRows(filtered(), th.dataset.key);
});}
function cmp(a,b,key){
  const va=a[key], vb=b[key];
  if(key==='pn'||key==='db'||key==='signal'||key==='action'||key==='aim'||key==='bucket'){
    return String(va||'').localeCompare(String(vb||''));
  }
  return (Number(va)||0)-(Number(vb)||0);
}
function fmtEur(n){if(n==null||n==='')return '—';return '€'+Math.round(Number(n)).toLocaleString('en-GB');}
function bindTabs(){
  document.querySelectorAll('.tabs button[data-tab]').forEach(btn=>{
    btn.onclick=()=>{
      document.querySelectorAll('.tabs button').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-selected','false');});
      document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
      btn.classList.add('active'); btn.setAttribute('aria-selected','true');
      const id='panel-'+btn.dataset.tab;
      const p=document.getElementById(id); if(p) p.classList.add('active');
      window.dispatchEvent(new CustomEvent('bi-tab',{detail:{tab:btn.dataset.tab}}));
    };
  });
}
const CHART_COLORS={leak:'#c0552d',over:'#15233c',bal:'#1d9e75',ink:'#52514e',grid:'#e1e0d9',blue:'#2a78d6'};
function chartDefaults(){
  return {responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{color:CHART_COLORS.ink}}}};
}
"""
