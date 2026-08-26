#!/usr/bin/env python3
"""Aftermarket BI Command Center — unified director dashboard (Mode B).

Build-time SSR: hero KPIs, SVG/CSS charts, static tables — visible with JS disabled.
Reads  : revision_exception_queue, replenishment_*, revision_book_b_top_review
Writes : 02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html
         02_dashboards/sales/OPEN_Aftermarket_BI_Command_Center.cmd
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import aftermarket_bi_data as BI  # noqa: E402
import render_ssr_charts as SSR  # noqa: E402
import tier_a_dashboard_common as T  # noqa: E402

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
OUT_HTML = ISZE / "02_dashboards" / "sales" / "ISZE_Aftermarket_BI_Command_Center.html"
OUT_CMD = ISZE / "02_dashboards" / "sales" / "OPEN_Aftermarket_BI_Command_Center.cmd"

DEFAULT_DB = "IUK"

EXTRA_CSS = SSR.SSR_CHART_CSS + """
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px}
@media(max-width:900px){.grid3{grid-template-columns:1fr}}
.heatmap td,.heatmap th{text-align:center;min-width:72px}
.heatmap td.hot{background:#f8e4dc;color:#8a3030;font-weight:600}
.heatmap td.warm{background:#fff3d6;color:#8a6500}
.heatmap td.cool{background:#eef3f9;color:#1a2b4a}
.heatmap td.zero{color:#aaa}
.heatmap th.rowhead{text-align:left;min-width:180px;background:#15233c;color:#f7f4ee}
.db-select-wrap{display:flex;align-items:center;gap:10px;margin:0 0 18px}
.db-select-wrap select{padding:8px 12px;font:inherit;border:1px solid #d9d3c8;background:#fff}
.section-label{font-family:Georgia,serif;font-size:13px;color:#6b6256;text-transform:uppercase;letter-spacing:.08em;margin:24px 0 10px}
.boot-error{background:#f8e4dc;border-left:3px solid #8a3030;padding:14px 18px;margin:16px 28px;font-size:14px}
.db-panel{display:none}
.db-panel.active{display:block}
#panel-db.active .db-panel.active{display:block}
.ssr-fallback{min-height:120px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:16px}
@media(max-width:1100px){.grid4{grid-template-columns:1fr 1fr}}
@media(max-width:700px){.grid4,.grid3{grid-template-columns:1fr}}
"""

INTERACT_JS = r"""
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');}
function fmtInt(n){if(n==null||n==='')return '—';return Math.round(Number(n)).toLocaleString('en-GB');}
function fmtEur(n){if(n==null||n==='')return '—';return '€'+Math.round(Number(n)).toLocaleString('en-GB');}
function cmp(a,b,key){
  const va=a[key], vb=b[key];
  if(['pn','db','signal','action','aim','bucket','aim_l2'].includes(key))
    return String(va||'').localeCompare(String(vb||''));
  return (Number(va)||0)-(Number(vb)||0);
}

document.querySelectorAll('.tabs button[data-tab]').forEach(btn=>{
  btn.onclick=()=>{
    document.querySelectorAll('.tabs button').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-selected','false');});
    document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
    btn.classList.add('active'); btn.setAttribute('aria-selected','true');
    const p=document.getElementById('panel-'+btn.dataset.tab); if(p) p.classList.add('active');
  };
});

const dbSel=document.getElementById('dbTabSelect');
if(dbSel){
  dbSel.onchange=()=>{
    document.querySelectorAll('.db-panel').forEach(p=>{
      p.classList.toggle('active', p.dataset.db===dbSel.value);
    });
  };
}

function filterTable(tblId, countId, filters){
  const tb=document.querySelector('#'+tblId+' tbody'); if(!tb) return;
  let shown=0;
  tb.querySelectorAll('tr').forEach(tr=>{
    let ok=true;
    for(const [key,val] of Object.entries(filters)){
      if(!val) continue;
      const cell=tr.dataset[key]||'';
      if(key==='pn'||key==='pnDrill'){
        if(!cell.includes(val)) ok=false;
      } else if(cell!==val) ok=false;
    }
    tr.classList.toggle('is-hide', !ok);
    if(ok) shown++;
  });
  const rc=document.getElementById(countId);
  if(rc) rc.textContent=shown+' shown';
}

['fPn','fDb'].forEach(id=>{
  const el=document.getElementById(id);
  if(!el) return;
  el.addEventListener('input',()=>filterTable('networkTbl','networkRowCount',{
    pn:(document.getElementById('fPn')||{}).value||'',
    db:(document.getElementById('fDb')||{}).value||''
  }));
});
const fDrill=document.getElementById('fPnDrill');
if(fDrill) fDrill.addEventListener('input',()=>filterTable('tbl','drillRowCount',{pnDrill:fDrill.value||''}));

let networkSortKey='gap_eur', networkSortDir=-1;
document.querySelectorAll('#networkTbl thead th[data-key]').forEach(th=>{
  th.dataset.label=th.textContent;
  th.onclick=()=>{
    if(networkSortKey===th.dataset.key) networkSortDir=-networkSortDir;
    else {networkSortKey=th.dataset.key; networkSortDir=(th.dataset.key==='pn'||th.dataset.key==='db')?1:-1;}
    const tb=document.querySelector('#networkTbl tbody');
    const rows=[...tb.querySelectorAll('tr:not(.is-hide)')];
    rows.sort((a,b)=>{
      const va=a.dataset[networkSortKey], vb=b.dataset[networkSortKey];
      if(['pn','db','aim','aim_l2','signal','action'].includes(networkSortKey))
        return networkSortDir*String(va||'').localeCompare(String(vb||''));
      return networkSortDir*((Number(va)||0)-(Number(vb)||0));
    });
    rows.forEach(r=>tb.appendChild(r));
  };
});

let drillSortKey='gap_eur', drillSortDir=-1;
document.querySelectorAll('#tbl thead th[data-key]').forEach(th=>{
  th.dataset.label=th.textContent;
  th.onclick=()=>{
    if(drillSortKey===th.dataset.key) drillSortDir=-drillSortDir;
    else {drillSortKey=th.dataset.key; drillSortDir=(drillSortKey==='pn'||drillSortKey==='db')?1:-1;}
    const tb=document.querySelector('#tbl tbody');
    const rows=[...tb.querySelectorAll('tr:not(.is-hide)')];
    rows.sort((a,b)=>{
      const va=a.dataset[drillSortKey], vb=b.dataset[drillSortKey];
      if(['pn','db','signal','action','aim'].includes(drillSortKey))
        return drillSortDir*String(va||'').localeCompare(String(vb||''));
      return drillSortDir*((Number(va)||0)-(Number(vb)||0));
    });
    rows.forEach(r=>tb.appendChild(r));
  };
});
"""


def _hero_html(hero: dict) -> str:
    h = hero or {}
    chips = [
        (SSR.fmt_eur_compact(h.get("total_gap_eur")), "Network € leakage", "Qty gap × reference sell-out €",
         "Sum of positive (sell-out − bill) × ref sell-out across five DBs. CY2025."),
        (SSR.fmt_eur_compact(h.get("total_overstock_eur")), "Overstock €", "Bill qty &gt; sell-out · ref €",
         "Inventory risk where ISZE bill exceeds dealer sell-out, valued at reference sell-out."),
        (SSR.fmt_int(h.get("pn_count")), "PNs in queue", "Revision exception register",
         "Distinct PN×DB rows in revision_exception_queue.csv."),
        (SSR.fmt_int(h.get("db_count")), "DBs with sell-out", "ITUK · UTI · IRELAND · IUK · GREECE",
         "Five-network cut. UTI≠UMI · IUK≠ITUK · IRELAND≠IUK."),
        (SSR.fmt_eur_compact(h.get("book_b_weighted_eur")), "Book B weighted €", "Provisional forecast weights",
         "Sum of forecast_weight_eur from book_b_bucket_summary — no alloc run."),
        (SSR.fmt_int(h.get("iam_undercut_count")), "IAM undercut PNs", "KS index &lt; 1 vs ref sell-out",
         "Peer shop below our reference sell-out — guardrail review list."),
        (SSR.fmt_eur_compact(h.get("high_list_exposure_eur")), "High list exposure €", "Category list % ≥ 5",
         "€ gap on PNs flagged for high planned-list exposure."),
        (SSR.fmt_eur_compact(h.get("book_b_blocked_eur")), "Ambition blocked €", "Growth bucket × guardrail",
         "Book B growth/carryover bucket rows with HOLD / leakage / IAM / list guardrails."),
    ]
    return SSR.hero_kpis(chips)


def _network_callout(hero: dict) -> str:
    h = hero or {}
    st = round(float(h.get("network_sell_through") or 0) * 100)
    return (
        f"<strong>Biggest money leak:</strong> {SSR.esc(h.get('biggest_db', '—'))} · PN "
        f"<strong>{SSR.esc(h.get('biggest_pn', '—'))}</strong> · ~{SSR.fmt_eur(h.get('biggest_pn_gap_eur'))} gap "
        f"({SSR.fmt_int(h.get('biggest_pn_qty_gap'))} units) · network total {SSR.fmt_eur(h.get('total_gap_eur'))} "
        f"· sell-through {st}%."
    )


def _network_table_rows(rows: list[dict]) -> str:
    parts = []
    for r in rows:
        parts.append(
            f'<tr data-pn="{SSR.esc(r.get("pn",""))}" data-db="{SSR.esc(r.get("db",""))}" '
            f'data-aim="{SSR.esc(r.get("aim",""))}" data-aim_l2="{SSR.esc(r.get("aim_l2",""))}" '
            f'data-bill_eur="{r.get("bill_eur") or 0}" data-sellout_eur="{r.get("sellout_eur") or 0}" '
            f'data-gap_eur="{r.get("gap_eur") or 0}" data-signal="{SSR.esc(r.get("signal",""))}" '
            f'data-action="{SSR.esc(r.get("action",""))}">'
            f'<td>{SSR.esc(r.get("pn"))}</td><td>{SSR.esc(r.get("db"))}</td>'
            f'<td>{SSR.pill("aim", r.get("aim") or "—")}</td><td>{SSR.esc(r.get("aim_l2") or "—")}</td>'
            f'<td class="num">{SSR.fmt_eur(r.get("bill_eur"))}</td>'
            f'<td class="num">{SSR.fmt_eur(r.get("sellout_eur"))}</td>'
            f'<td class="num">{SSR.fmt_eur(r.get("gap_eur"))}</td>'
            f'<td>{SSR.pill(r.get("signal_class","act"), r.get("signal") or "")}</td>'
            f'<td>{SSR.pill(r.get("action_class","act"), r.get("action") or "")}</td></tr>'
        )
    return "".join(parts)


def _drill_table_rows(rows: list[dict]) -> str:
    parts = []
    for r in rows:
        ks = r.get("ks_index")
        unit = r.get("unit_eur")
        parts.append(
            f'<tr data-pn="{SSR.esc(r.get("pn",""))}" data-db="{SSR.esc(r.get("db",""))}" '
            f'data-gap_eur="{r.get("gap_eur") or 0}" data-qty_gap="{r.get("qty_gap") or 0}" '
            f'data-signal="{SSR.esc(r.get("signal",""))}" data-action="{SSR.esc(r.get("action",""))}" '
            f'data-aim="{SSR.esc(r.get("aim",""))}" data-bill_qty="{r.get("bill_qty") or 0}" '
            f'data-sellout_qty="{r.get("sellout_qty") or 0}" data-unit_eur="{unit or ""}" '
            f'data-ks_index="{ks or ""}">'
            f'<td>{SSR.esc(r.get("pn"))}</td><td>{SSR.esc(r.get("db"))}</td>'
            f'<td class="num">{SSR.fmt_eur(r.get("gap_eur"))}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("qty_gap"))}</td>'
            f'<td>{SSR.pill(r.get("signal_class","act"), r.get("signal") or "")}</td>'
            f'<td>{SSR.pill(r.get("action_class","act"), r.get("action") or "")}</td>'
            f'<td>{SSR.pill("aim", r.get("aim") or "—")}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("bill_qty"))}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("sellout_qty"))}</td>'
            f'<td class="num">{SSR.fmt_num(unit) if unit is not None else "—"}</td>'
            f'<td class="num">{SSR.fmt_num(ks) if ks is not None else "—"}</td></tr>'
        )
    return "".join(parts)


def _db_panel_html(db: str, panel: dict, ituk_dealers: list[dict], default: bool) -> str:
    active = " active" if default else ""
    top15 = sorted(panel.get("top15") or [], key=lambda x: float(x.get("gap_eur") or 0), reverse=True)[:15]
    aim_mix = panel.get("aim_mix") or []
    monday = panel.get("monday_fix") or []

    monday_html = "".join(
        f'<li><strong>{i+1}. {SSR.esc(r.get("pn"))}</strong> · {SSR.fmt_eur(r.get("gap_eur"))} · '
        f'{SSR.fmt_int(r.get("qty_gap"))} units · {SSR.esc(r.get("action") or r.get("signal") or "")}</li>'
        for i, r in enumerate(monday)
    ) or "<li>No leakage rows for this DB.</li>"

    split_bars = SSR.vertical_bar_svg(
        [{"db": "Leakage €", "gap_eur": panel.get("leakage_eur")}, {"db": "Overstock €", "gap_eur": panel.get("overstock_eur")}],
        label_key="db", value_key="gap_eur", color=SSR.COLORS["leak"],
    )
    pipe_donut = SSR.pipeline_donut_svg(
        {
            "leakage": panel.get("leakage_eur") or 0,
            "overstock": panel.get("overstock_eur") or 0,
            "balanced": panel.get("balanced_eur") or 0,
        }
    )
    top_bars = SSR.horizontal_bar_rows(top15, label_key="pn", value_key="gap_eur", color=SSR.COLORS["leak"], reverse=True, max_items=10)
    aim_bars = SSR.aim_family_bars(aim_mix, max_items=10)

    ituk_block = ""
    if db == "ITUK" and ituk_dealers:
        dealer_rows = "".join(
            f'<tr><td>{SSR.esc(d.get("dealer"))}</td><td class="num">{SSR.fmt_eur(d.get("gap_eur"))}</td>'
            f'<td class="num">{SSR.fmt_int(d.get("sellout_qty"))}</td><td class="num">{SSR.fmt_eur(d.get("bill_eur"))}</td></tr>'
            for d in ituk_dealers
        )
        ituk_block = f"""
  <div id="itukDealerBox">
    <h3>ITUK · top 10 dealers by € gap</h3>
    <p class="cap">Dealer grain from replenishment_bridge_ituk_dealer · CY2025</p>
    {SSR.so_what("Rank dealers by € gap before PN-level pricing — workshop behaviour shows here first.")}
    <div class="table-scroll"><table class="matrix" id="itukDealerTbl"><thead><tr>
      <th>Dealer</th><th class="num">€ gap</th><th class="num">Sell-out qty</th><th class="num">Bill €</th>
    </tr></thead><tbody>{dealer_rows}</tbody></table></div>
  </div>"""

    return f"""
<div class="db-panel{active}" data-db="{SSR.esc(db)}" id="db-panel-{SSR.esc(db)}">
  <div class="callout db-headline">
    <strong>{SSR.esc(db)}</strong> · leakage {SSR.fmt_eur(panel.get('leakage_eur'))} · overstock {SSR.fmt_eur(panel.get('overstock_eur'))}
    · {SSR.fmt_int(panel.get('leakage_pn'))} leakage PNs · {SSR.fmt_int(panel.get('overstock_pn'))} overstock PNs.
  </div>
  <div class="grid3" id="db-split">
    <div class="card"><h3>Pipeline donut · € split</h3><p class="cap">Leakage vs overstock vs balanced</p><div class="ssr-fallback">{pipe_donut}</div></div>
    <div class="card"><h3>Top 10 leakage PNs</h3><p class="cap">By € gap in selected DB</p><div class="ssr-fallback">{top_bars}</div></div>
    <div class="card"><h3>AIM L1 families · € gap</h3><p class="cap">Leakage € by AIM family</p><div class="ssr-fallback">{aim_bars}</div></div>
  </div>
  <div class="grid2">
    <div class="card"><h3>Leakage vs overstock €</h3><p class="cap">Selected DB · vertical bars</p><div class="ssr-fallback">{split_bars}</div></div>
    <div class="card"><h3>Register counts</h3><p class="cap">{SSR.fmt_int(panel.get('leakage_pn'))} leakage PNs · {SSR.fmt_int(panel.get('overstock_pn'))} overstock PNs</p>
      <ul class="monday-list"><li>Leakage € {SSR.fmt_eur(panel.get('leakage_eur'))}</li><li>Overstock € {SSR.fmt_eur(panel.get('overstock_eur'))}</li></ul>
    </div>
  </div>
  {ituk_block}
  <h3>What to fix Monday</h3>
  <p class="cap">Ranked by € gap · top 12 leakage PNs</p>
  <ul class="monday-list">{monday_html}</ul>
</div>"""


def _pricing_html(payload: dict) -> str:
    bb = payload.get("book_b") or {}
    blocked = bb.get("conflict_blocked_eur") or 0
    n = bb.get("conflict_count") or 0
    hero = payload.get("hero") or {}
    bullets = SSR.bullet_chart_dual(
        [
            {
                "label": "Book B weighted ambition",
                "actual_eur": hero.get("book_b_weighted_eur") or 0,
                "blocked_eur": blocked,
            },
            {
                "label": "Guardrail-blocked growth rows",
                "actual_eur": blocked,
                "blocked_eur": blocked,
            },
        ]
    )
    conflict_callout = (
        f"<strong>{SSR.fmt_int(n)}</strong> rows · <strong>{SSR.fmt_eur(blocked)}</strong> "
        "weighted ambition blocked by guardrails (HOLD / REVIEW_LEAKAGE / IAM / list exposure)."
    )
    conflict_summary = "".join(
        f'<li><strong>{SSR.esc(c.get("action"))}</strong> · {SSR.fmt_int(c.get("count"))} rows · '
        f'{SSR.fmt_eur(c.get("blocked_eur"))} blocked €</li>'
        for c in (bb.get("conflict_summary") or [])
    )
    heatmap = SSR.heatmap_table(bb.get("heatmap") or [])

    ba = bb.get("bucket_action") or []
    buckets = list(dict.fromkeys(x.get("bucket") for x in ba))[:10]
    actions = list(dict.fromkeys(x.get("action") for x in ba))
    stacked_parts = ['<div class="bar-rows ssr-chart">']
    palette = ["#c0552d", "#15233c", "#2a78d6", "#1d9e75", "#eda100", "#8a3030"]
    for b in buckets:
        total = sum(int(x.get("count") or 0) for x in ba if x.get("bucket") == b) or 1
        lbl = b[:22] + "…" if len(b) > 22 else b
        stacked_parts.append(f'<div class="bar-row"><span class="lbl" title="{SSR.esc(b)}">{SSR.esc(lbl)}</span><span class="track" style="display:flex;height:16px">')
        for i, act in enumerate(actions):
            hit = next((x for x in ba if x.get("bucket") == b and x.get("action") == act), None)
            cnt = int(hit.get("count") or 0) if hit else 0
            if cnt:
                pct = 100.0 * cnt / total
                stacked_parts.append(
                    f'<span class="fill" style="width:{pct:.1f}%;background:{palette[i % len(palette)]}" title="{SSR.esc(act)}: {cnt}"></span>'
                )
        stacked_parts.append("</span></div>")
    stacked_parts.append("</div>")
    stacked_html = "".join(stacked_parts)

    iam_rows = "".join(
        f'<tr><td>{SSR.esc(r.get("pn"))}</td><td>{SSR.esc(r.get("db"))}</td>'
        f'<td class="bucket">{SSR.esc(r.get("bucket"))}</td>'
        f'<td class="num">{SSR.fmt_num(r.get("ks_index")) if r.get("ks_index") is not None else "—"}</td>'
        f'<td class="num">{SSR.fmt_eur(r.get("forecast_eur"))}</td>'
        f'<td class="num">{SSR.fmt_eur(r.get("l12m_eur"))}</td></tr>'
        for r in (bb.get("iam_undercut") or [])
    )
    list_rows = "".join(
        f'<tr><td>{SSR.esc(r.get("pn"))}</td><td>{SSR.esc(r.get("db"))}</td>'
        f'<td class="bucket">{SSR.esc(r.get("bucket"))}</td>'
        f'<td class="num">{SSR.fmt_eur(r.get("forecast_eur"))}</td>'
        f'<td>{SSR.pill(r.get("action_class","act"), r.get("action") or "")}</td></tr>'
        for r in (bb.get("high_list") or [])
    )
    share_rows = "".join(
        f'<tr><td>{SSR.esc(r.get("pn"))}</td><td>{SSR.esc(r.get("db"))}</td>'
        f'<td class="bucket">{SSR.esc(r.get("bucket"))}</td>'
        f'<td class="num">{SSR.fmt_eur(r.get("forecast_eur"))}</td>'
        f'<td class="num">{SSR.fmt_num(r.get("growth_factor")) if r.get("growth_factor") is not None else "—"}</td>'
        f'<td>{"<span class=\"pill hold\">guardrail</span> " if r.get("guardrail_flag") else ""}'
        f'{SSR.pill(r.get("action_class","act"), r.get("action") or "")}</td></tr>'
        for r in (bb.get("share_gain_top20") or [])
    )

    return f"""
  {SSR.section_nav([("pricing-guardrails","Guardrails"),("pricing-heatmap","Bucket heatmap"),("pricing-iam","IAM register"),("pricing-list","List exposure")])}
  <div class="callout" id="pricing-guardrails">{conflict_callout}</div>
  <div class="grid2">
    <div class="card"><h3>Ambition vs guardrail</h3><p class="cap">Weighted € vs blocked € · no alloc run</p><div class="ssr-fallback">{bullets}</div></div>
    <div class="card"><h3>Conflict summary</h3><p class="cap">Growth bucket rows stopped by guardrail</p><ul class="monday-list">{conflict_summary or '<li>No conflicts flagged.</li>'}</ul></div>
  </div>
  <div class="grid2" id="pricing-heatmap">
    <div class="card"><h3>Bucket × action heatmap</h3><p class="cap">PN counts · darker = more rows</p>{heatmap}</div>
    <div class="card"><h3>Book B bucket × action (stacked)</h3><p class="cap">Growth/ambition buckets vs guardrail actions</p>{stacked_html}</div>
  </div>
  <div class="section-label" id="pricing-iam">IAM undercut · full register · {len(bb.get('iam_undercut') or [])} rows</div>
  <div class="table-scroll"><table class="matrix" id="iamTbl"><thead><tr>
    <th>PN</th><th>DB</th><th>Bucket</th><th class="num">KS index</th><th class="num">Forecast €</th><th class="num">L12M €</th>
  </tr></thead><tbody>{iam_rows}</tbody></table></div>
  <div class="section-label" id="pricing-list">High list exposure · top 30</div>
  <div class="table-scroll"><table class="matrix" id="listTbl"><thead><tr>
    <th>PN</th><th>DB</th><th>Bucket</th><th class="num">Forecast €</th><th>Action</th>
  </tr></thead><tbody>{list_rows}</tbody></table></div>
  <div class="section-label">Book B share gain · top 20 vs guardrail flags</div>
  <div class="table-scroll"><table class="matrix" id="shareGainTbl"><thead><tr>
    <th>PN</th><th>DB</th><th>Bucket</th><th class="num">Forecast €</th><th class="num">GF</th><th>Action</th>
  </tr></thead><tbody>{share_rows}</tbody></table></div>"""


def write_html(payload: dict) -> None:
    built = (payload.get("built_at") or "")[:10]
    hero = payload.get("hero") or {}
    by_db = payload.get("by_db") or []
    mix_eur = payload.get("pipeline_mix_eur") or {}
    aim_gap = payload.get("aim_l1_gap") or []
    top_pn = payload.get("top_pn") or []
    monthly = payload.get("monthly_trend") or []
    bb_buckets = payload.get("book_b_buckets") or []
    network50 = payload.get("network_top50") or []
    drill500 = payload.get("revision_rows") or []
    db_panels = payload.get("db_panels") or {}
    ituk_dealers = payload.get("ituk_dealers_top10") or payload.get("ituk_dealers_top5") or []
    waterfall = payload.get("waterfall_steps") or []
    pipe_heat = payload.get("pipeline_db_heatmap") or []
    iam_scatter = payload.get("iam_scatter") or []
    db_radar = payload.get("db_radar") or []
    spark_db = payload.get("sparkline_by_db") or []
    money5 = payload.get("money_top5") or []

    db_gap_chart = SSR.leakage_db_comparison(by_db, label_key="db", value_key="gap_eur")
    mix_chart = SSR.pipeline_mix_bar(mix_eur)
    pipe_donut_net = SSR.pipeline_donut_svg(mix_eur)
    aim_chart = SSR.horizontal_bar_rows(aim_gap, label_key="aim", value_key="gap_eur", color=SSR.COLORS["blue"], max_items=15)
    aim_treemap = SSR.treemap_cells(aim_gap, label_key="aim", value_key="gap_eur")
    top_pn_chart = SSR.horizontal_bar_rows(top_pn, label_key="pn", value_key="gap_eur", color=SSR.COLORS["leak"], max_items=20,
        label_fn=lambda t: f"{t.get('pn','')} ({t.get('db','')})")
    monthly_chart = SSR.line_chart_svg(monthly)
    spark_strip = SSR.sparkline_strip(spark_db)
    bb_bucket_chart = SSR.horizontal_bar_rows(
        sorted(bb_buckets, key=lambda x: float(x.get("weight_eur") or 0), reverse=True),
        label_key="bucket", value_key="weight_eur", color=SSR.COLORS["blue"], max_items=12,
        label_fn=lambda b: (b.get("bucket") or "")[:24],
    )
    wf_chart = SSR.waterfall_steps(waterfall)
    pipe_hm = SSR.pipeline_db_heatmap(pipe_heat)
    scatter = SSR.scatter_svg(iam_scatter, x_label="KS price index", y_label="€ gap")
    radar = SSR.radar_lite_svg(db_radar)
    money_cards = SSR.money_on_table_cards(money5)
    ituk_lb = SSR.mini_leaderboard(ituk_dealers[:10])
    book_b_bullets = SSR.bullet_chart_dual(payload.get("book_b_bullets") or [])

    db_options = "".join(
        f'<option value="{SSR.esc(d.get("db"))}"{" selected" if d.get("db")==DEFAULT_DB else ""}>{SSR.esc(d.get("db"))}</option>'
        for d in by_db
    )
    fdb_options = '<option value="">All</option>' + "".join(
        f'<option value="{SSR.esc(d.get("db"))}">{SSR.esc(d.get("db"))}</option>' for d in by_db
    )

    db_panel_blocks = ""
    for db in T.DB_ORDER:
        if db not in db_panels:
            continue
        db_panel_blocks += _db_panel_html(db, db_panels[db], ituk_dealers if db == "ITUK" else [], db == DEFAULT_DB)

    row_meta = f"{SSR.fmt_int(payload.get('revision_row_total'))} PNs in queue · showing top {len(drill500)}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Aftermarket BI Command Center</title>
<style>{T.TIER_A_CSS}{EXTRA_CSS}</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · Aftermarket BI · Mode B</div>
    <h1>Where we lose money — network command center</h1>
    <div class="rule"></div>
    <p class="lead">€ leakage from dealer sell-out vs ISZE bill · reference sell-out = PR00 × 1.785 · five DBs with sell-out files. UTI≠UMI · IUK≠ITUK · IRELAND≠IUK.</p>
    <div class="hero-kpis" id="hero-kpis">{_hero_html(hero)}</div>
  </div>
</div>
<nav class="tabs" role="tablist" aria-label="Stakeholder views">
  <button type="button" class="active" data-tab="network" role="tab" aria-selected="true">ISZE Director</button>
  <button type="button" data-tab="db" role="tab" aria-selected="false">DB Director</button>
  <button type="button" data-tab="pricing" role="tab" aria-selected="false">Pricing / revision</button>
</nav>
<div class="wrap">

<div id="panel-network" class="panel active" role="tabpanel">
  {SSR.section_nav([("net-money","Money on table"),("net-waterfall","Waterfall"),("net-heatmap","Pipeline heatmap"),("net-trends","Trends"),("net-compare","DB compare"),("net-register","Top 50")])}
  <div class="callout" id="networkCallout">{_network_callout(hero)}</div>
  <div id="net-money">
    <h3>Money on the table · top 5 leakage PNs</h3>
    <p class="cap">Ranked by € gap × reference sell-out · CY2025 five-network cut</p>
    {SSR.so_what("These five PNs are where Monday pricing calls start — IUK may dominate € but each card shows its DB.")}
    <div class="ssr-fallback">{money_cards}</div>
  </div>
  <div class="grid2" id="net-waterfall">
    <div class="card"><h3>€ leakage waterfall</h3><p class="cap">Network → DB → top PN decomposition</p>
      {SSR.so_what("Waterfall shows where network € lands — small DB bars are real money, not noise.")}
      <div class="ssr-fallback">{wf_chart}</div></div>
    <div class="card"><h3>Pipeline mix (€)</h3><p class="cap">Leakage vs overstock vs balanced sell-out €</p>
      {SSR.so_what("Roughly half the register € is leakage; overstock is the stocking-drag counter-story.")}
      <div class="ssr-fallback">{mix_chart}</div></div>
  </div>
  <div class="grid2" id="net-heatmap">
    <div class="card"><h3>Pipeline heatmap · DB × class</h3><p class="cap">Cell = € · leakage / overstock / balanced</p>
      {SSR.so_what("GREECE leakage column is blank until sell-out validates — overstock € still shows bill risk.")}
      <div class="ssr-fallback">{pipe_hm}</div></div>
    <div class="card"><h3>AIM L1 treemap · € at risk</h3><p class="cap">Area ∝ positive qty gap × reference sell-out</p>
      {SSR.so_what("Large unmapped AIM block means family tagging gap — not missing data.")}
      <div class="ssr-fallback">{aim_treemap}</div></div>
  </div>
  <div class="grid2" id="net-trends">
    <div class="card"><h3>Monthly bill vs sell-out</h3><p class="cap">Network aggregate · replenishment_bridge</p>
      {SSR.so_what("Dec bill cliff is partial-month reporting — do not read as demand collapse.")}
      <div class="ssr-fallback">{monthly_chart}</div></div>
    <div class="card"><h3>Monthly sparkline strip · sell-out € by DB</h3><p class="cap">Last month value shown · SVG polyline</p>
      {SSR.so_what("Flat UTI sparkline = honest zero sell-out months, not a broken chart.")}
      <div class="ssr-fallback">{spark_strip}</div></div>
  </div>
  <div class="grid2" id="net-compare">
    <div class="card"><h3>Network comparison · € leakage by DB</h3><p class="cap">Five DBs side-by-side · reference sell-out · log-scaled bars</p>
      {SSR.so_what("Log scale keeps ITUK/UTI visible beside IUK — read the € labels for exact values.")}
      <div class="ssr-fallback">{db_gap_chart}</div></div>
    <div class="card"><h3>Pipeline donut · network €</h3><p class="cap">Leakage vs overstock vs balanced sell-out €</p>
      {SSR.so_what("Donut is the one-screen split for director briefings — percentages are €-weighted.")}
      <div class="ssr-fallback">{pipe_donut_net}</div></div>
  </div>
  <div class="grid2">
    <div class="card"><h3>DB comparison radar</h3><p class="cap">Toggle DBs · default top 3 by gap share · normalized metrics</p>
      {SSR.so_what("Turn off IUK to compare ITUK vs UTI shape — five overlays without toggle is unreadable.")}
      <div class="ssr-fallback">{radar}</div></div>
    <div class="card"><h3>IAM price index scatter</h3><p class="cap">KS index vs € gap · top 30 with quote</p>
      {SSR.so_what("Below index=1 means IAM undercuts our reference sell-out — guardrail before list moves.")}
      <div class="ssr-fallback">{scatter}</div></div>
  </div>
  <div class="grid2">
    <div class="card"><h3>AIM L1 — € at risk (bars)</h3><p class="cap">Top families by positive gap</p><div class="ssr-fallback">{aim_chart}</div></div>
    <div class="card"><h3>Top 20 PNs — € at risk</h3><p class="cap">Highest € gap network-wide</p><div class="ssr-fallback">{top_pn_chart}</div></div>
  </div>
  <div class="grid2">
    <div class="card"><h3>Book B ambition vs guardrail</h3><p class="cap">Weighted forecast € vs blocked growth rows</p><div class="ssr-fallback">{book_b_bullets}</div></div>
    <div class="card"><h3>Book B bucket weights</h3><p class="cap">Forecast € + PN count by provisional bucket</p><div class="ssr-fallback">{bb_bucket_chart}</div></div>
  </div>
  <div class="grid2">
    <div class="card"><h3>ITUK dealer top 10 · € gap</h3><p class="cap">Dealer grain · replenishment_bridge_ituk_dealer</p>
      {SSR.so_what("Only ITUK has dealer grain — use this list for workshop calls before network-wide actions.")}
      <div class="ssr-fallback">{ituk_lb}</div></div>
  </div>
  <div class="section-label" id="net-register">Top 50 PNs · network register</div>
  <div class="toolbar" style="position:static;padding:0 0 12px;border:0">
    <label>DB <select id="fDb">{fdb_options}</select></label>
    <label>Search PN <input id="fPn" placeholder="part number"/></label>
    <span class="row-count" id="networkRowCount">{len(network50)} / 50 shown</span>
  </div>
  <div class="table-scroll">
  <table class="matrix" id="networkTbl">
    <thead><tr>
      <th data-key="pn">PN</th><th data-key="db">DB</th><th data-key="aim">AIM L1</th><th data-key="aim_l2">AIM L2</th>
      <th data-key="bill_eur" class="num">Bill €</th><th data-key="sellout_eur" class="num">Sell-out €</th>
      <th data-key="gap_eur" class="num">Gap €</th><th data-key="signal">Pipeline</th><th data-key="action">Action</th>
    </tr></thead><tbody>{_network_table_rows(network50)}</tbody>
  </table>
  </div>
</div>

<div id="panel-db" class="panel" role="tabpanel">
  <h2><span class="no">DB</span> · Your network only</h2>
  {SSR.section_nav([("db-select","Select DB"),("db-split","Leakage split"),("db-monday","Monday fix")])}
  <div class="db-select-wrap">
    <label for="dbTabSelect"><strong>Distributor</strong></label>
    <select id="dbTabSelect">{db_options}</select>
  </div>
  <div id="db-panels">{db_panel_blocks}</div>
</div>

<div id="panel-pricing" class="panel" role="tabpanel">
  <h2><span class="no">Book B</span> · Revision &amp; guardrails</h2>
  <p class="lead">Provisional weights · no alloc run · bucket × recommended action · IAM undercut register.</p>
  {_pricing_html(payload)}
</div>

<div class="section-label">Drill-down register · top 500 by € gap</div>
<p class="lead"><span id="rowMeta">{row_meta}</span> · sticky header · horizontal scroll.</p>
<div class="toolbar" style="position:static;padding:0 0 12px;border:0">
  <label>Search PN <input id="fPnDrill" placeholder="part number"/></label>
  <span class="row-count" id="drillRowCount">{len(drill500)} shown</span>
</div>
<div class="table-scroll">
<table class="matrix" id="tbl">
  <thead><tr>
    <th data-key="pn">PN</th><th data-key="db">DB</th><th data-key="gap_eur" class="num">€ gap</th>
    <th data-key="qty_gap" class="num">Qty gap</th><th data-key="signal">Signal</th><th data-key="action">Action</th>
    <th data-key="aim">AIM L1</th><th data-key="bill_qty" class="num">Bill qty</th><th data-key="sellout_qty" class="num">Sell-out</th>
    <th data-key="unit_eur" class="num">Ref sell-out €</th><th data-key="ks_index" class="num">KS index</th>
  </tr></thead><tbody>{_drill_table_rows(drill500)}</tbody>
</table>
</div>
<p class="foot">Built {built} · SSR charts + static tables · Sources: revision_exception_queue, replenishment_bridge, revision_book_b_top_review · Internal Mode B.</p>
</div>
<script>{INTERACT_JS}</script>
</body>
</html>"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(f'@echo off\r\nstart "" "%~dp0ISZE_Aftermarket_BI_Command_Center.html"\r\n', encoding="utf-8")


def rebuild_siblings() -> None:
    scripts = [
        ISZE / "01_data" / "91_build" / "build_db_dlr_commercial_stack.py",
        ISZE / "02_dashboards" / "sales" / "_build" / "build_db_dlr_replenishment_cy2025.py",
        ISZE / "01_data" / "91_build" / "build_book_b_review_workbook.py",
    ]
    for s in scripts:
        if s.is_file():
            print(f"rebuilding {s.name}...")
            subprocess.run([sys.executable, str(s)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Aftermarket BI Command Center")
    ap.add_argument("--all", action="store_true", help="Also rebuild replenishment + Book B HTML")
    args = ap.parse_args()
    if args.all:
        rebuild_siblings()
    payload = BI.build_full_payload(DERIVED)
    write_html(payload)
    verify = HERE / "verify_aftermarket_bi_command_center.py"
    if verify.is_file():
        rc = subprocess.run([sys.executable, str(verify)], check=False)
        if rc.returncode != 0:
            return rc.returncode
    payload_mb = OUT_HTML.stat().st_size / 1024 / 1024
    print(f"wrote {OUT_HTML} ({payload_mb:.2f} MB, {len(payload.get('revision_rows', []))} drill rows SSR)")
    print(f"wrote {OUT_CMD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
