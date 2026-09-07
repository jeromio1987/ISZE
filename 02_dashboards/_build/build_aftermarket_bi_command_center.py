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

V2_SKELETON = DERIVED / "pms_v2_lcv_opt_skeleton.csv"
V2_ACCURACY = DERIVED / "lcv_uio_accuracy_by_db.csv"
V2_WALLET = DERIVED / "gps_wallet_v2_by_distributor.csv"
V2_FINDINGS = DERIVED / "gps_pms_v2_findings.md"
V2_SENSITIVITY = DERIVED / "pms_v2_lcv_opt1_sensitivity.csv"
V2_EQHIT_COV = DERIVED / "pms_v2_eqhit_fitment_coverage.csv"
V2_EQHIT_GAP = DERIVED / "pms_v2_eqhit_category_gap_cy2025.csv"
V2_CONTESTED_DB = DERIVED / "pms_v2_eqhit_contested_by_db_cy2025.csv"
V2_CAPTURE = DERIVED / "pms_capture_by_db_year_v2_mileage.csv"
V2_EQHIT_EXTRACT = DERIVED / "eqhit_extract_priority_cy2025.csv"
IUK_V20_LOCK = "44,926"  # Decision 30 Jul 2026 — GPS figure only; car park still V19
RISK_AFTERSALES = DERIVED / "db_aftersales_risk.csv"
STD_AIM_GPS_HTML = "../sales/Dealer_Sellout_AIM_GPS_Sales_to_Dealer_2025.html"
STD_SIXDB_HTML = "../sales/Next_Analyses_Sales_to_Dealer_SixDB.html"
STD_STALE_DAYS = 90

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
.acc-A{background:#1a4d2e;color:#f7f4ee}
.acc-B{background:#2b4a78;color:#f7f4ee}
.acc-C{background:#6b6256;color:#f7f4ee}
.acc-D{background:#8a3030;color:#f7f4ee}
.acc-NA{background:#d9d3c8;color:#222}
.uio-chip{display:inline-block;position:relative;cursor:help;border-bottom:1px dotted #c0552d}
.uio-chip .tip{display:none;position:absolute;left:0;top:calc(100% + 6px);width:min(340px,70vw);
  background:#15233c;color:#f7f4ee;border-top:3px solid #c0552d;padding:10px 12px;font-size:12px;line-height:1.4;z-index:40;
  box-shadow:0 8px 24px rgba(0,0,0,.25)}
.uio-chip:hover .tip,.uio-chip:focus-within .tip{display:block}
.rank-pill{display:inline-block;padding:2px 8px;font-size:11px;font-weight:700;letter-spacing:.04em}
.v2-status{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.v2-status .chip{display:inline-block;padding:4px 10px;font-size:12px;font-weight:600;
  background:#eef3f9;color:#1a2b4a;border:1px solid #d9d3c8}
.v2-status .chip.on{background:#1a4d2e;color:#f7f4ee;border-color:#1a4d2e}
.v2-status .chip.warn{background:#fff3d6;color:#8a6500;border-color:#e8d48b}
/* V2 tables: sticky thead was covering first DB rows under sticky tabs — disable */
#panel-gpsv2 .matrix thead th{position:static;top:auto;z-index:1}
.stale-banner{background:#fff3d6;border:1px solid #e8d48b;border-left:4px solid #c0552d;
  color:#222;padding:12px 16px;margin:0 0 16px;font-size:14px;line-height:1.45}
.stale-banner strong{color:#8a6500}
.price-check{background:#eef3f9;border:1px solid #d9d3c8;padding:12px 16px;margin:0 0 16px;font-size:13px}
.price-check li{margin:4px 0}
.std-muted .ssr-fallback,.std-muted .money-cards{opacity:.55}
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


def _hero_html(hero: dict, *, stale: bool = False) -> str:
    h = hero or {}
    # Product lock: Monday = pricing. Always lead hero with Book B / revision — not StD leakage.
    pricing_first = [
        (SSR.fmt_int(h.get("pn_count")), "PNs in queue", "Revision exception register",
         "Distinct PN×DB rows in revision_exception_queue.csv."),
        (SSR.fmt_eur_compact(h.get("book_b_weighted_eur")), "Book B weighted €", "Provisional forecast weights",
         "Sum of forecast_weight_eur from book_b_bucket_summary — no alloc run."),
        (SSR.fmt_int(h.get("iam_undercut_count")), "IAM undercut PNs", "KS index &lt; 1 vs ref sell-out",
         "Peer shop below our reference sell-out — guardrail review list."),
        (SSR.fmt_eur_compact(h.get("book_b_blocked_eur")), "Ambition blocked €", "Growth bucket × guardrail",
         "Book B growth/carryover bucket rows with HOLD / leakage / IAM / list guardrails."),
        (SSR.fmt_eur_compact(h.get("high_list_exposure_eur")), "High list exposure €", "Category list % ≥ 5",
         "€ gap on PNs flagged for high planned-list exposure."),
    ]
    std_chips = [
        (SSR.fmt_eur_compact(h.get("total_gap_eur")), "Network € leakage", "Sales to dealer archive · not Monday",
         "CY cut × ref sell-out. Meeting / archive lens — not this week’s action list."),
        (SSR.fmt_eur_compact(h.get("total_overstock_eur")), "Overstock €", "Bill qty &gt; sell-out · ref €",
         "Inventory risk where ISZE bill exceeds dealer sell-out, valued at reference sell-out."),
        (SSR.fmt_int(h.get("db_count")), "DBs with sell-out", "ITUK · UTI · IRELAND · IUK · GREECE · PORTUGAL",
         "All networks with sales-to-dealer files. UTI≠UMI · IUK≠ITUK · IRELAND≠IUK."),
    ]
    # Always pricing-first (Monday product = pricing). Stale only mutes StD panels elsewhere.
    chips = pricing_first + std_chips
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


def _fmt_pct(x) -> str:
    if x is None or (isinstance(x, float) and pd_isna(x)):
        return "—"
    try:
        return f"{100.0 * float(x):.1f}%"
    except (TypeError, ValueError):
        return "—"


def pd_isna(x) -> bool:
    try:
        import pandas as pd

        return bool(pd.isna(x))
    except Exception:
        return x is None


def _std_freshness() -> dict:
    """Stale if max content period (year×period) OR newest file mtime is > STD_STALE_DAYS.

    Prefer data coverage over filesystem rewrite dates — pipeline rewrites can make
    mtimes look fresh while dealer sales were not uploaded.
    """
    from calendar import monthrange
    from datetime import datetime, timezone

    import pandas as pd

    files = sorted(DERIVED.glob("dealer_sellout_long_*.csv"))
    if not files:
        return {"stale": True, "as_of": None, "age_days": None, "n_files": 0}

    newest = max(files, key=lambda p: p.stat().st_mtime)
    mtime = datetime.fromtimestamp(newest.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    content_as_of = None
    max_ym = None
    for p in files:
        try:
            df = pd.read_csv(p, usecols=["year", "period"])
        except Exception:
            continue
        # period is usually "YYYY-MM" (or "YYYY-YTD"); month int 1–12 is rare.
        per = df["period"].astype(str).str.strip()
        m = per.str.extract(r"(?P<y>\d{4})-(?P<m>\d{2})$")
        ok = m["y"].notna() & m["m"].notna()
        if not ok.any():
            y = pd.to_numeric(df["year"], errors="coerce")
            mon = pd.to_numeric(df["period"], errors="coerce")
            mask = y.notna() & mon.notna() & (mon >= 1) & (mon <= 12)
            if not mask.any():
                continue
            yi = int(y[mask].max())
            mi = int(mon[mask & (y == yi)].max())
        else:
            ys = pd.to_numeric(m.loc[ok, "y"], errors="coerce")
            ms = pd.to_numeric(m.loc[ok, "m"], errors="coerce")
            good = ys.notna() & ms.notna()
            if not good.any():
                continue
            yi = int(ys[good].max())
            mi = int(ms[good & (ys == yi)].max())
        ym = (yi, mi)
        if max_ym is None or ym > max_ym:
            max_ym = ym
    if max_ym:
        yi, mi = max_ym
        last_day = monthrange(yi, mi)[1]
        content_as_of = datetime(yi, mi, last_day, tzinfo=timezone.utc)

    # Prefer content coverage for “how fresh is the story”; mtime alone can lie after pipeline rewrites.
    anchor = content_as_of or mtime
    age = (now - anchor).days
    as_of = anchor.strftime("%Y-%m-%d")
    content_label = f"{max_ym[0]}-{max_ym[1]:02d}" if max_ym else None
    return {
        "stale": age > STD_STALE_DAYS,
        "as_of": as_of,
        "age_days": age,
        "n_files": len(files),
        "newest_name": newest.name,
        "content_period": content_label,
        "file_mtime": mtime.strftime("%Y-%m-%d"),
    }


def _std_freshness_banner_html() -> str:
    info = _std_freshness()
    if not info.get("n_files"):
        return (
            '<div class="stale-banner" id="std-fresh">'
            "<strong>Sales to dealer data missing.</strong> "
            "Monday actions should lead with pricing / Book B — not leakage from empty sell-out.</div>"
        )
    as_of = info.get("as_of") or "—"
    age = info.get("age_days")
    content = info.get("content_period") or "—"
    if info.get("stale"):
        return (
            f'<div class="stale-banner" id="std-fresh">'
            f"<strong>Sales to dealer archive looks stale</strong> "
            f"(content through {SSR.esc(content)} · as-of {SSR.esc(as_of)} · "
            f"~{age}d · threshold {STD_STALE_DAYS}d). "
            f"Monday product is <strong>Pricing / revision</strong> — not this tab. "
            f"Meeting use only "
            f"(source {SSR.esc(info.get('newest_name') or '')}).</div>"
        )
    return (
        f'<div class="stale-banner" id="std-fresh" style="background:#eef3f9;border-color:#d9d3c8">'
        f"<strong>Sales to dealer archive as-of {SSR.esc(as_of)}</strong> "
        f"(content through {SSR.esc(content)} · {info.get('n_files')} long files · age ~{age}d). "
        f"Monday = Pricing tab.</div>"
    )


def _load_v2_lcv_rows() -> list[dict]:
    import pandas as pd

    if not V2_SKELETON.is_file():
        return []
    df = pd.read_csv(V2_SKELETON)
    return df.to_dict(orient="records")


def _load_v2_sensitivity() -> dict[str, dict]:
    import pandas as pd

    if not V2_SENSITIVITY.is_file():
        return {}
    df = pd.read_csv(V2_SENSITIVITY)
    return {str(r["distributor_code"]): r for r in df.to_dict(orient="records")}


def _v2_flag_on(val) -> bool:
    return val in (True, "True", "true", 1) or str(val).lower() in ("true", "1")


def _apples_oil_clutch_html() -> str:
    """Mandatory V1|V2 comparison table (claim framework) for oil + clutch · total CY2025."""
    import pandas as pd

    if not V2_CAPTURE.is_file():
        return ""
    cap = pd.read_csv(V2_CAPTURE)
    cats = ("oil_filter", "clutch_disc", "clutch_pressure_plate")
    sub = cap[
        (cap["year"] == 2025)
        & (cap["line_type"] == "total")
        & (cap["pms_category"].isin(cats))
    ]
    if sub.empty:
        return ""
    rows_html = []
    for cat in cats:
        g = sub[sub["pms_category"] == cat]
        if g.empty:
            continue
        exp1 = float(g["expected_qty_v1"].sum())
        exp2 = float(g["expected_qty_v2"].sum())
        act = float(g["actual_qty"].sum())
        gap2 = float(g["revenue_gap_v2_eur"].sum()) if "revenue_gap_v2_eur" in g.columns else 0.0
        # gap_v1 from same SP where available
        if "avg_sp_eur" in g.columns:
            gap1 = float(((g["expected_qty_v1"] - g["actual_qty"]) * g["avg_sp_eur"].fillna(0)).sum())
        else:
            gap1 = float("nan")
        cap1 = (act / exp1) if exp1 else None
        cap2 = (act / exp2) if exp2 else None
        driver = "mileage"  # L2 intensity; wear factors unchanged vs V1
        gap1_s = SSR.fmt_eur(gap1) if gap1 == gap1 else "—"
        rows_html.append(
            "<tr>"
            f"<td>{SSR.esc(cat)}</td>"
            f"<td class=\"num\">{SSR.fmt_int(exp1)}</td>"
            f"<td class=\"num\">{SSR.fmt_int(exp2)}</td>"
            f"<td class=\"num\">{SSR.fmt_int(act)}</td>"
            f"<td class=\"num\">{_fmt_pct(cap1)}</td>"
            f"<td class=\"num\">{_fmt_pct(cap2)}</td>"
            f"<td class=\"num\">{gap1_s}</td>"
            f"<td class=\"num\">{SSR.fmt_eur(gap2)}</td>"
            f"<td>{SSR.esc(driver)}</td>"
            "</tr>"
        )
    # Oil movers (capture delta) — L2 only
    oil = sub[sub["pms_category"] == "oil_filter"].copy()
    oil["dcap"] = oil["capture_rate_v2"] - oil["capture_rate_v1"]
    movers = oil.nsmallest(5, "dcap")
    mover_lis = "".join(
        f"<li><strong>{SSR.esc(r.distributor_code)}</strong> "
        f"{_fmt_pct(r.capture_rate_v1)} → {_fmt_pct(r.capture_rate_v2)} "
        f"(Δ {_fmt_pct(r.dcap)})</li>"
        for r in movers.itertuples()
    )
    return f"""
  <div class="section-label" id="v2-apples">Old vs new expected demand · network (calendar 2025, total lines)</div>
  <p class="cap">Same actual sales under both models. Clutch wear rate is unchanged — if expected demand jumps, it is mostly because we use real km, not a tougher wear assumption.</p>
  <div class="table-scroll">
  <table class="matrix">
    <thead><tr>
      <th>Part family</th><th class="num">Expected (old)</th><th class="num">Expected (mileage)</th><th class="num">Sold</th>
      <th class="num">Coverage old</th><th class="num">Coverage mileage</th>
      <th class="num">€ gap old</th><th class="num">€ gap mileage</th><th>Main driver</th>
    </tr></thead>
    <tbody>{"".join(rows_html)}</tbody>
  </table>
  </div>
  <div class="section-label">Markets that look weaker once we use real driving mileage (oil filters)</div>
  <p class="cap">Read as: same sales, higher expected demand from km — coverage % falls. Not a sudden sales drop.</p>
  <ul class="monday-list">{mover_lis or "<li>No oil rows.</li>"}</ul>
"""


def _v2_story_html(rows: list[dict]) -> str:
    """Plain-English Opt2/Opt3 / accuracy story from skeleton rows already on disk."""
    if not rows:
        return ""
    # Skeleton is category×DB; use oil_filter total as the readable coverage lens.
    oil = [
        r
        for r in rows
        if str(r.get("pms_category") or "") == "oil_filter"
        and str(r.get("line_type") or "total") == "total"
    ]
    if not oil:
        oil = rows
    bits = []
    for r in oil:
        db = str(r.get("distributor_code") or "")
        if db == "PORTUGAL" and _v2_flag_on(r.get("opt3_enabled")):
            bits.append(
                "<li><strong>Portugal</strong> — Opt3 uses Matriculas age ≤10y shares (preferred over VIN). "
                f"Opt1 oil coverage {_fmt_pct(r.get('capture_rate_opt1'))}; "
                f"Opt3 {_fmt_pct(r.get('capture_rate_opt3'))}. "
                "Accuracy rank is B until Trooper counts exist.</li>"
            )
        if db == "IRELAND" and _v2_flag_on(r.get("opt2_enabled")):
            bits.append(
                "<li><strong>Ireland</strong> — Opt2 on with SIMI Trooper vs D-Max aggregate "
                "(RT/RG not separable). "
                f"Opt1 {_fmt_pct(r.get('capture_rate_opt1'))}; "
                f"Opt2 {_fmt_pct(r.get('capture_rate_opt2'))}. "
                "Accuracy rank B — not A.</li>"
            )
    ranks: dict[str, int] = {}
    for r in oil:
        rk = str(r.get("uio_accuracy_rank") or "C")
        ranks[rk] = ranks.get(rk, 0) + 1
    rank_s = " · ".join(f"{k}:{v}" for k, v in sorted(ranks.items()))
    bits.append(
        f"<li><strong>UIO accuracy</strong> — ranks across oil markets in this table: {SSR.esc(rank_s)}. "
        "Hover the park chip for why. No rank A until gov subtype parks improve.</li>"
    )
    bits.append(
        "<li><strong>Claim lock</strong> — wallet index is not €/UIO. Do not rank a market on wallet "
        "against another market’s V1 €/truck. Oil stays BVP expected; EQ-HIT extract is seed PNs only.</li>"
    )
    return f"""
  <div class="section-label" id="v2-story">How to read the options (Mode B)</div>
  <ul class="monday-list">{"".join(bits)}</ul>
"""


def _contested_by_db_html() -> str:
    import pandas as pd

    if not V2_CONTESTED_DB.is_file():
        return ""
    df = pd.read_csv(V2_CONTESTED_DB)
    # Prefer extract-backed high-gap cats; skip wild capture from seed bias (brake_pad)
    focus = {"clutch_disc", "clutch_pressure_plate", "blower_filter", "fuel_filter", "brake_rotor"}
    sub = df[df["pms_category"].isin(focus)].copy()
    if sub.empty:
        return ""
    sub = sub.sort_values("revenue_gap_v2_eur", ascending=False).head(12)
    body = "".join(
        "<tr>"
        f"<td>{SSR.esc(r.distributor_code)}</td>"
        f"<td>{SSR.esc(r.pms_category)}</td>"
        f"<td class=\"num\">{_fmt_pct(r.capture_rate_v1)}</td>"
        f"<td class=\"num\">{_fmt_pct(r.capture_rate_v2)}</td>"
        f"<td class=\"num\">{SSR.fmt_eur(r.revenue_gap_v2_eur)}</td>"
        "</tr>"
        for r in sub.itertuples()
    )
    return f"""
  <div class="section-label" id="v2-contested">Contested by DB · EQ-HIT cats (total CY2025)</div>
  <p class="cap">V1 and V2 capture side-by-side · € gap uses V2 expected · brake pad/shoe seed bias excluded from this strip</p>
  <div class="table-scroll">
  <table class="matrix">
    <thead><tr>
      <th>DB</th><th>category</th><th class="num">cap_v1</th><th class="num">cap_v2</th><th class="num">gap_v2 €</th>
    </tr></thead>
    <tbody>{body}</tbody>
  </table>
  </div>
"""


def _risk_chip_html() -> str:
    """Aftersales risk overlay — separate from GPS wallet (BI OS insight #5)."""
    import pandas as pd

    if not RISK_AFTERSALES.is_file():
        return ""
    df = pd.read_csv(RISK_AFTERSALES)
    y = 2025 if (df["year"] == 2025).any() else int(df["year"].max())
    top = df[df["year"] == y].nsmallest(5, "rank") if "rank" in df.columns else df.head(5)
    if top.empty:
        return ""
    lis = "".join(
        f"<li><strong>{SSR.esc(r.distributor_code)}</strong> risk {float(r.risk_score):.0f} · "
        f"VOR share {_fmt_pct(r.vor_urgent_share)} · contested {SSR.fmt_eur(r.contested_eur)}</li>"
        for r in top.itertuples()
    )
    return f"""
  <div class="section-label" id="net-risk">Aftersales risk overlay · CY{y} (not wallet index)</div>
  <p class="cap">From db_aftersales_risk.csv · separate from GPS €/UIO and V2 wallet — who to pressure-check Monday</p>
  <ul class="monday-list">{lis}</ul>
"""


def _gps_pms_v2_panel_html() -> str:
    """SSR panel: Opt1/2/3 LCV skeleton + UIO accuracy hover chips + sensitivity."""
    rows = _load_v2_lcv_rows()
    if not rows:
        return """
<div id="panel-gpsv2" class="panel" role="tabpanel">
  <h2><span class="no">V2</span> · GPS / PMS LCV (shadow)</h2>
  <div class="callout">Shadow artefacts missing. Run
  <code>python 03_analytics/Isuzu/prism/scripts/build_gps_pms_v2_shadow.py</code>
  then rebuild this command center.</div>
</div>"""

    sens_map = _load_v2_sensitivity()
    has_sens = bool(sens_map)

    def _chip(r: dict) -> str:
        rank = str(r.get("uio_accuracy_rank") or "C")
        cls = f"acc-{rank.replace('/', '')}" if rank != "N/A" else "acc-NA"
        tip = SSR.esc(r.get("hover_text") or "")
        uio = SSR.fmt_int(r.get("lcv_uio"))
        return (
            f'<span class="uio-chip" tabindex="0">{uio} '
            f'<span class="rank-pill {cls}">{SSR.esc(rank)}</span>'
            f'<span class="tip">{tip}</span></span>'
        )

    n_opt1 = sum(1 for r in rows if _v2_flag_on(r.get("opt1_enabled")))
    n_opt2 = sum(1 for r in rows if _v2_flag_on(r.get("opt2_enabled")))
    n_opt3 = sum(1 for r in rows if _v2_flag_on(r.get("opt3_enabled")))
    ie_row = next((r for r in rows if str(r.get("distributor_code")) == "IRELAND"), None)
    ie_on = _v2_flag_on(ie_row.get("opt2_enabled")) if ie_row else False
    rank_counts: dict[str, int] = {}
    for r in rows:
        rk = str(r.get("uio_accuracy_rank") or "?")
        rank_counts[rk] = rank_counts.get(rk, 0) + 1
    rank_bits = " · ".join(f"{k}:{v}" for k, v in sorted(rank_counts.items()))

    status_chips = (
        f'<div class="v2-status" id="v2-status">'
        f'<span class="chip warn">Car park V19 — not V20</span>'
        f'<span class="chip on">IUK GPS lock {IUK_V20_LOCK}</span>'
        f'<span class="chip">PMS = total capture</span>'
        f'<span class="chip on">Opt1 {n_opt1}/{len(rows)}</span>'
        f'<span class="chip {"on" if n_opt2 else ""}">Opt2 {n_opt2}/{len(rows)}</span>'
        f'<span class="chip {"on" if n_opt3 else ""}">Opt3 {n_opt3}/{len(rows)}</span>'
        f'<span class="chip {"on" if ie_on else "warn"}">Ireland Opt2 {"ON" if ie_on else "OFF"}</span>'
        f'<span class="chip">Accuracy {SSR.esc(rank_bits)}</span>'
        f'<span class="chip {"on" if has_sens else "warn"}">Sens mid/low/high {"ON" if has_sens else "missing"}</span>'
        f"</div>"
    )
    truth_banner = (
        '<div class="callout" id="v2-truth">'
        "<strong>Car park is not fully fixed.</strong> Live UIO is still V19. "
        f"The only locked V20 number on this page is IUK LCV CY2026F = {IUK_V20_LOCK} (GPS / Extended Target). "
        "EQ-HIT is a 37-seed extract (Grade D) — not the full catalogue. "
        "This tab is a Mode B shadow. It does not overwrite published V1 capture."
        "</div>"
    )

    body = []
    for r in sorted(rows, key=lambda x: str(x.get("distributor_code") or "")):
        code = str(r.get("distributor_code") or "")
        o2 = "on" if _v2_flag_on(r.get("opt2_enabled")) else "off"
        o3 = "on" if _v2_flag_on(r.get("opt3_enabled")) else "off"
        s = sens_map.get(code) or {}
        sens_cells = ""
        if has_sens:
            sens_cells = (
                f"<td class=\"num\">{_fmt_pct(s.get('capture_rate_opt1_mid'))}</td>"
                f"<td class=\"num\">{_fmt_pct(s.get('capture_rate_opt1_low'))}</td>"
                f"<td class=\"num\">{_fmt_pct(s.get('capture_rate_opt1_high'))}</td>"
            )
        body.append(
            "<tr>"
            f"<td>{SSR.esc(code)}</td>"
            f"<td class=\"num\">{_chip(r)}</td>"
            f"<td class=\"num\">{_fmt_pct(r.get('capture_rate_opt1'))}</td>"
            f"<td class=\"num\">{SSR.fmt_int(r.get('expected_qty_opt1'))}</td>"
            f"<td>{o2}</td>"
            f"<td class=\"num\">{_fmt_pct(r.get('capture_rate_opt2'))}</td>"
            f"<td>{o3}</td>"
            f"<td class=\"num\">{_fmt_pct(r.get('capture_rate_opt3'))}</td>"
            f"{sens_cells}"
            f"<td class=\"num\">{SSR.fmt_int(r.get('actual_qty'))}</td>"
            "</tr>"
        )

    sens_heads = ""
    if has_sens:
        sens_heads = (
            '<th class="num">Sens mid</th><th class="num">Sens low</th>'
            '<th class="num">Sens high</th>'
        )

    wallet_note = ""
    if V2_WALLET.is_file():
        import pandas as pd

        w = pd.read_csv(V2_WALLET)
        w25 = w[w["year"] == 2025].nsmallest(5, "gps_index_vs_wallet") if "gps_index_vs_wallet" in w.columns else w.head(0)
        if len(w25):
            lis = "".join(
                f"<li><strong>{SSR.esc(r.distributor_code)}</strong> index "
                f"{r.gps_index_vs_wallet:.2f} · wallet {SSR.fmt_eur(r.wallet_eur)}</li>"
                for r in w25.itertuples()
            )
            wallet_note = f"<ul class=\"monday-list\">{lis}</ul>"

    # EQ-HIT fitment coverage + top gaps (shadow columns — not Mode A cutover)
    eqhit_block = ""
    if V2_EQHIT_COV.is_file() or V2_EQHIT_GAP.is_file():
        import pandas as pd

        cov_bits = []
        if V2_EQHIT_COV.is_file():
            cov = pd.read_csv(V2_EQHIT_COV)
            backed = cov[cov["fitment_source"].astype(str).str.startswith("eqhit")]
            n_cat = len(backed)
            n_pn = 0
            if V2_EQHIT_EXTRACT.is_file():
                ex = pd.read_csv(V2_EQHIT_EXTRACT, usecols=["part_number"])
                n_pn = int(ex["part_number"].nunique())
            elif n_cat and "eqhit_unique_pns" in backed.columns:
                n_pn = int(pd.to_numeric(backed["eqhit_unique_pns"], errors="coerce").fillna(0).sum())
            flips = []
            if V2_EQHIT_GAP.is_file():
                gap = pd.read_csv(V2_EQHIT_GAP).sort_values("network_revenue_gap_v2_eur", ascending=False)
                for r in gap.head(5).itertuples():
                    flips.append(
                        f"<li><strong>{SSR.esc(r.pms_category)}</strong> capture "
                        f"{_fmt_pct(r.network_capture_v2)} · gap {SSR.fmt_eur(r.network_revenue_gap_v2_eur)} "
                        f"· LCV fit {r.fitment_lcv}</li>"
                    )
            cov_bits.append(
                f'<span class="chip on">EQ-HIT {n_pn} seed PNs · {n_cat} cats · Grade D</span>'
                f'<span class="chip">oil skipped / BVP</span>'
            )
            eqhit_block = (
                f'<div class="v2-status" id="v2-eqhit">{"".join(cov_bits)}</div>'
                f'<div class="section-label">EQ-HIT extract categories · contested gap (total CY2025)</div>'
                f'<ul class="monday-list">{"".join(flips) or "<li>No gap rows.</li>"}</ul>'
                f'<p class="cap">Fitment=1 means the part family can apply to that vehicle bucket — not that every VIN '
                f'needs a replacement this year. Seed extract only ({n_pn} PNs), not full catalogue. Shadow — V1 untouched. '
                f'PMS headline = total capture. Claim gate: GPS_PMS_V2_CLAIM_FRAMEWORK.md</p>'
            )

    apples = _apples_oil_clutch_html()
    contested = _contested_by_db_html()
    story = _v2_story_html(rows)

    return f"""
<div id="panel-gpsv2" class="panel" role="tabpanel">
  <h2><span class="no">V2</span> · GPS / PMS LCV (shadow)</h2>
  {SSR.section_nav([("v2-truth","Truth"),("v2-opts","Denominator options"),("v2-status","Status"),("v2-story","How to read"),("v2-apples","V1 vs V2"),("v2-table","DB table"),("v2-eqhit","EQ-HIT gaps"),("v2-contested","Contested DB"),("v2-wallet","Wallet index")])}
  {truth_banner}
  <div class="callout" id="v2-opts">
    <strong>LCV-first Mode B challenge — not a published cutover.</strong>
    Opt1 = flat LCV park + country mileage (default read).
    Opt2 = Trooper / D-Max RT / D-Max RG where we have subtype shares (Ireland SIMI = Trooper vs D-Max roll-up).
    Opt3 = vehicles about 10 years or newer (Portugal Matriculas preferred; VIN year only where that is all we have).
    Sensitivity = same Opt1 with km ±20%. Hover UIO for accuracy A–D.
    Fitment: EQ-HIT seed extract on clutch / brake rotor / blower / fuel; oil stays BVP basket.
    Wallet index ≠ € per vehicle — never cross-rank those two scales.
  </div>
  {status_chips}
  {story}
  {apples}
  <p class="cap">Oil-filter coverage vs expected demand — by market. Opt2/Opt3 columns only light up where that option is on.</p>
  <div class="table-scroll" id="v2-table">
  <table class="matrix">
    <thead><tr>
      <th>DB</th><th class="num">LCV park · accuracy</th>
      <th class="num">Opt1 coverage</th><th class="num">Opt1 expected</th>
      <th>Opt2</th><th class="num">Opt2 coverage</th>
      <th>Opt3</th><th class="num">Opt3 coverage</th>
      {sens_heads}
      <th class="num">Sold qty</th>
    </tr></thead>
    <tbody>{"".join(body)}</tbody>
  </table>
  </div>
  {eqhit_block}
  {contested}
  <div class="section-label" id="v2-wallet">GPS wallet index · lowest CY2025 (parts € ÷ wallet €)</div>
  <p class="cap">Only compare wallet index to other wallet indices. Do not mix with classic €/UIO league tables.</p>
  {wallet_note or "<p class=\"cap\">Run V2 shadow builder for wallet rows.</p>"}
  <p class="foot">Concept: 00_docs/agent/GPS_PMS_V2_CONCEPT.md · claim: GPS_PMS_V2_CLAIM_FRAMEWORK.md
  · skeleton: pms_v2_lcv_opt_skeleton.csv · V1 files untouched</p>
</div>
"""


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

    deep = (
        f'<p class="cap" id="db-deep">Sales to dealer deep story: '
        f'<a href="{STD_AIM_GPS_HTML}">Network AIM/GPS</a> · '
        f'<a href="{STD_SIXDB_HTML}">Six-DB next analyses</a> '
        f'(open via sibling OPEN_*.cmd).</p>'
    )

    return f"""
<div class="db-panel{active}" data-db="{SSR.esc(db)}" id="db-panel-{SSR.esc(db)}">
  <div class="callout db-headline">
    <strong>{SSR.esc(db)}</strong> · leakage {SSR.fmt_eur(panel.get('leakage_eur'))} · overstock {SSR.fmt_eur(panel.get('overstock_eur'))}
    · {SSR.fmt_int(panel.get('leakage_pn'))} leakage PNs · {SSR.fmt_int(panel.get('overstock_pn'))} overstock PNs.
  </div>
  {deep}
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


def _pricing_monday_top5(payload: dict) -> str:
    """This week’s ≤5 pricing actions — Book B / IAM / list exposure only (not StD leakage)."""
    bb = payload.get("book_b") or {}
    items: list[tuple[float, str]] = []
    for r in (bb.get("share_gain_top20") or [])[:8]:
        if not r.get("guardrail_flag"):
            continue
        eur = float(r.get("forecast_eur") or 0)
        items.append(
            (
                eur,
                f"<li><strong>{SSR.esc(r.get('pn'))}</strong> · {SSR.esc(r.get('db'))} · "
                f"{SSR.fmt_eur(eur)} · {SSR.esc(r.get('action') or 'guardrail')} "
                f"(Book B growth stopped — review before list move)</li>",
            )
        )
    for r in (bb.get("iam_undercut") or [])[:5]:
        eur = float(r.get("forecast_eur") or r.get("l12m_eur") or 0)
        items.append(
            (
                eur,
                f"<li><strong>{SSR.esc(r.get('pn'))}</strong> · {SSR.esc(r.get('db'))} · "
                f"IAM undercut · KS {SSR.fmt_num(r.get('ks_index')) if r.get('ks_index') is not None else '—'} "
                f"— check reference sell-out ×1.785 before cutting list</li>",
            )
        )
    for r in (bb.get("high_list") or [])[:5]:
        eur = float(r.get("forecast_eur") or 0)
        items.append(
            (
                eur,
                f"<li><strong>{SSR.esc(r.get('pn'))}</strong> · {SSR.esc(r.get('db'))} · "
                f"{SSR.fmt_eur(eur)} · high list exposure — stage any raise</li>",
            )
        )
    # de-dupe by HTML text, keep highest € first
    seen = set()
    ordered = []
    for eur, html in sorted(items, key=lambda x: -x[0]):
        if html in seen:
            continue
        seen.add(html)
        ordered.append(html)
        if len(ordered) >= 5:
            break
    if not ordered:
        ordered = ["<li>No Book B / IAM / list flags in payload — open Action Map for specialist cuts.</li>"]
    return f"""
  <div class="section-label" id="pricing-monday">This week · top 5 pricing actions</div>
  <p class="cap">Monday list from Book B guardrails + IAM undercut + high list exposure — not sales-to-dealer leakage.</p>
  <ul class="monday-list">{"".join(ordered)}</ul>
"""


def _pricing_html(payload: dict) -> str:
    bb = payload.get("book_b") or {}
    blocked = bb.get("conflict_blocked_eur") or 0
    n = bb.get("conflict_count") or 0
    hero = payload.get("hero") or {}
    monday5 = _pricing_monday_top5(payload)
    checklist = """
  <div class="price-check" id="price-check">
    <strong>Before you conclude on price</strong>
    <ul>
      <li>State list vintage / PR00 date used</li>
      <li>Reference sell-out = PR00 × 1.785 (not “street”)</li>
      <li>State IAM match coverage % before any undercut claim</li>
      <li>Keep UTI ≠ UMI · IUK ≠ ITUK · IRELAND ≠ IUK</li>
      <li>Separate ambition € from guardrail-blocked €</li>
    </ul>
  </div>"""
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
  {SSR.section_nav([("pricing-monday","This week"),("pricing-guardrails","Guardrails"),("pricing-heatmap","Bucket heatmap"),("pricing-iam","IAM register"),("pricing-list","List exposure")])}
  {checklist}
  {monday5}
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

    std_info = _std_freshness()
    std_banner = _std_freshness_banner_html()
    # StD is archive/meeting — always mute leakage hero panels (Monday product = pricing).
    std_muted_cls = " std-muted"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Aftermarket BI — Pricing &amp; challenge</title>
<style>{T.TIER_A_CSS}{EXTRA_CSS}</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · Aftermarket BI · Mode B</div>
    <h1>Pricing &amp; revision — Monday actions</h1>
    <div class="rule"></div>
    <p class="lead">Monday = Book B / revision / IAM. Reference sell-out = PR00 × 1.785 · UTI≠UMI · IUK≠ITUK · IRELAND≠IUK. Sales to dealer is a meeting archive tab — not the Monday product.</p>
    <div class="hero-kpis" id="hero-kpis">{_hero_html(hero, stale=True)}</div>
  </div>
</div>
<nav class="tabs" role="tablist" aria-label="Stakeholder views">
  <button type="button" class="active" data-tab="pricing" role="tab" aria-selected="true">Pricing / revision</button>
  <button type="button" data-tab="gpsv2" role="tab" aria-selected="false">GPS/PMS V2 LCV</button>
  <button type="button" data-tab="network" role="tab" aria-selected="false">Sales to dealer (archive)</button>
  <button type="button" data-tab="db" role="tab" aria-selected="false">DB Director</button>
</nav>
<div class="wrap">

<div id="panel-pricing" class="panel active" role="tabpanel">
  <h2><span class="no">Book B</span> · Revision &amp; guardrails</h2>
  <p class="lead">Provisional weights · no alloc run · bucket × recommended action · IAM undercut register. This is the Monday product.</p>
  {_pricing_html(payload)}
</div>

{_gps_pms_v2_panel_html()}

<div id="panel-network" class="panel" role="tabpanel">
  <h2><span class="no">Archive</span> · Sales to dealer (meeting pack)</h2>
  {SSR.section_nav([("net-money","Money on table"),("net-risk","Risk overlay"),("net-waterfall","Waterfall"),("net-heatmap","Pipeline heatmap"),("net-trends","Trends"),("net-compare","DB compare"),("net-register","Top 50")])}
  {std_banner}
  <div class="callout" id="networkCallout">{_network_callout(hero)}</div>
  {_risk_chip_html()}
  <div id="net-money" class="{std_muted_cls.strip()}">
    <h3>Money on the table · top 5 leakage PNs</h3>
    <p class="cap">Ranked by € gap × reference sell-out · CY2025 five-network cut · archive / meeting</p>
    {SSR.so_what("Archive lens — use Pricing tab for Monday actions. IUK may dominate €; each card shows its DB.")}
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
