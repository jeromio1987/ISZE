"""Multi-DB replenishment dashboard CY2025 — bill vs dealer sales to dealer.

Reads  : replenishment_summary_cy2025.parquet, replenishment_exceptions_cy2025.csv
Writes : 02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html
         02_dashboards/sales/OPEN_DB_DLR_Replenishment.cmd

internal. UTI≠UMI · IUK≠ITUK · IRELAND≠IUK.
UX shell cloned from ISZE_OS_Data_Map.html + Command Center charts.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD_UI = HERE.parents[1] / "_build"
if str(BUILD_UI) not in sys.path:
    sys.path.insert(0, str(BUILD_UI))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import aftermarket_bi_data as BI  # noqa: E402
import render_ssr_charts as SSR  # noqa: E402
import tier_a_dashboard_common as T  # noqa: E402

SSR_CSS = SSR.SSR_CHART_CSS

ISZE = Path(__file__).resolve().parents[3]
DERIVED = ISZE / "01_data" / "00_derived"
OUT_HTML = ISZE / "02_dashboards" / "sales" / "ISZE_DB_DLR_Replenishment_CY2025.html"
OUT_CMD = ISZE / "02_dashboards" / "sales" / "OPEN_DB_DLR_Replenishment.cmd"

LABELS = BI.COL_LABELS


def build_payload() -> dict:
    aim_map = T.load_aim_by_pn()
    rev = BI.load_revision_queue(DERIVED)
    exc = BI.load_replenishment_exceptions(DERIVED)
    summary = BI.load_replenishment_summary(DERIVED)
    net = BI.build_network_aggregates(rev, aim_map)

    rows = BI.replenishment_rows_for_table(exc, aim_map)
    for r in rows:
        rev_hit = rev.loc[(rev["part_number"].astype(str) == r["pn"]) & (rev["distributor_code"] == r["db"])]
        if not rev_hit.empty:
            r["gap_eur"] = T.safe_float(rev_hit.iloc[0]["gap_eur"], ndigits=0)
        else:
            bill = float(r.get("bill_qty") or 0)
            r["gap_eur"] = T.safe_float(max(float(r.get("qty_gap") or 0), 0) * (float(r.get("bill_eur") or 0) / bill if bill > 0 else 0), ndigits=0)

    hero = net["hero"]
    top_exc = max(rows, key=lambda r: float(r.get("gap_eur") or r.get("qty_gap") or 0)) if rows else {}
    hero["top_pn"] = top_exc.get("pn", hero.get("biggest_pn", "—"))
    hero["top_pn_db"] = top_exc.get("db", hero.get("biggest_db", ""))
    hero["top_pn_gap"] = top_exc.get("qty_gap")
    hero["top_pn_gap_eur"] = top_exc.get("gap_eur", hero.get("biggest_pn_gap_eur"))
    hero["biggest_db"] = net["by_db"][0]["db"] if net["by_db"] else hero.get("biggest_db")
    hero["biggest_db_gap_eur"] = max((d.get("gap_eur") or 0) for d in net["by_db"]) if net["by_db"] else 0

    return {
        "built_at": net["built_at"],
        "year": 2025,
        "hero": hero,
        "distributors": net["by_db"],
        "pipeline_mix": net["pipeline_mix"],
        "top_pn": net["top_pn"][:10],
        "rows": rows,
    }


def _repl_rows(rows: list[dict]) -> str:
    parts = []
    for r in rows:
        aim_cell = SSR.pill("aim", r.get("aim")) if r.get("aim") and r.get("aim") != "—" else "—"
        # Payload key stays sellout_qty (data contract + drill-down JS); the
        # visible column header is the shared label below.
        dealer_qty = r.get("sellout_qty")
        parts.append(
            f'<tr data-pn="{SSR.esc(r.get("pn",""))}" data-db="{SSR.esc(r.get("db",""))}" '
            f'data-signal="{SSR.esc(r.get("signal",""))}" data-gap_eur="{r.get("gap_eur") or 0}" '
            f'data-bill_qty="{r.get("bill_qty") or 0}" data-sellout_qty="{dealer_qty or 0}" '
            f'data-qty_gap="{r.get("qty_gap") or 0}" data-ratio="{r.get("ratio") or ""}" data-bill_eur="{r.get("bill_eur") or 0}">'
            f'<td>{SSR.esc(r.get("pn"))}</td><td>{SSR.esc(r.get("db"))}</td>'
            f'<td>{SSR.pill(r.get("signal_class","act"), r.get("signal") or "")}</td>'
            f'<td>{aim_cell}</td><td class="num">{SSR.fmt_eur(r.get("gap_eur"))}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("bill_qty"))}</td><td class="num">{SSR.fmt_int(dealer_qty)}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("qty_gap"))}</td>'
            f'<td class="num">{SSR.fmt_num(r.get("ratio")) if r.get("ratio") is not None else "—"}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("bill_eur"))}</td></tr>'
        )
    return "".join(parts)


def write_html(payload: dict) -> None:
    built = (payload.get("built_at") or "")[:10]
    H = payload.get("hero") or {}
    dist = payload.get("distributors") or []
    mix = payload.get("pipeline_mix") or {}
    rows = payload.get("rows") or []

    hero = SSR.hero_kpis([
        (SSR.fmt_eur_compact(H.get("total_gap_eur")), "Five-DB reference-price exposure", "Reference dealer price × qty gap",
         "Five-distributor observed subset. Reference dealer price × qty gap where sales to dealer exceed ISZE bill — modelled valuation, not observed lost revenue."),
        (SSR.esc(H.get("top_pn", "—")), "Top mismatch PN", f'{SSR.esc(H.get("top_pn_db", ""))} · {SSR.fmt_eur(H.get("top_pn_gap_eur"))}',
         "Largest reference-price exposure in the exception register."),
        (SSR.fmt_int(H.get("leakage_pn_count")), "Mismatch PNs (sales > bill)", "Five-distributor subset",
         "PNs where sales to dealer exceed ISZE bill across five DBs with sales-to-dealer data."),
        (f'{round(float(H.get("network_sell_through") or 0)*100)}%', "Five-DB sales-to-dealer ratio", "Five-distributor subset",
         "Total sales to dealer qty ÷ total ISZE bill qty. CY2025."),
        (str(len(dist)), "DBs in view", "UTI≠UMI · IUK≠ITUK", "Each DB is a separate dealer sales file grain."),
    ])
    callout = (
        f"<strong>Headline:</strong> {SSR.esc(H.get('biggest_db'))} · PN <strong>{SSR.esc(H.get('top_pn'))}</strong> · ~"
        f"{SSR.fmt_eur(H.get('top_pn_gap_eur'))} reference-price exposure · five-distributor subset total "
        f"{SSR.fmt_eur(H.get('total_gap_eur'))}."
    )
    signals = sorted({str(r.get("signal") or "") for r in rows if r.get("signal")})
    sig_opts = '<option value="">All signals</option>' + "".join(f'<option value="{SSR.esc(s)}">{SSR.esc(s)}</option>' for s in signals)
    db_chips = '<button type="button" class="on" data-db="">All DBs</button>' + "".join(
        f'<button type="button" data-db="{SSR.esc(d.get("db"))}">{SSR.esc(d.get("db"))}</button>' for d in dist
    )
    eur_chart = SSR.leakage_db_comparison(dist, label_key="db", value_key="gap_eur")
    mix_chart = SSR.pipeline_mix_bar(
        {"leakage": mix.get("leakage"), "overstock": mix.get("overstock"), "balanced": mix.get("balanced")},
        labels=("Mismatch PNs (sales > bill)", "Overstock PNs", "Balanced PNs"),
        value_fmt=lambda v: SSR.fmt_int(v),
    )
    pipe_donut = SSR.pipeline_donut_svg(
        {"leakage": mix.get("leakage"), "overstock": mix.get("overstock"), "balanced": mix.get("balanced")},
        labels=("Mismatch PNs (sales > bill)", "Overstock PNs", "Balanced PNs"),
        value_fmt=lambda v: SSR.fmt_int(v),
    )
    leak_over = []
    for d in dist:
        leak_over.append({"db": d.get("db"), "leak": d.get("leakage_pn") or 0, "over": d.get("overstock_pn") or 0})
    mix_db_html = ""
    for d in dist:
        mx = max(float(d.get("leakage_pn") or 0), float(d.get("overstock_pn") or 0), 1)
        mix_db_html += (
            f'<div class="bar-row"><span class="lbl">{SSR.esc(d.get("db"))}</span><span class="track" style="display:flex;height:16px">'
            f'<span class="fill" style="width:{100*float(d.get("leakage_pn") or 0)/mx:.1f}%;background:{SSR.COLORS["leak"]}" title="Mismatch (sales > bill)"></span>'
            f'<span class="fill" style="width:{100*float(d.get("overstock_pn") or 0)/mx:.1f}%;background:{SSR.COLORS["over"]}" title="Overstock"></span>'
            f"</span></div>"
        )
    st_items = [{"db": d.get("db"), "pct": round(float(d.get("sell_through") or 0) * 100)} for d in dist]
    st_chart = SSR.sell_through_bars(st_items, label_key="db", value_key="pct", cap_pct=200.0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>DB→DLR Replenishment CY2025</title>
<style>{T.TIER_A_CSS}{SSR_CSS}
.basis-strip{{display:flex;flex-wrap:wrap;gap:10px 18px;margin:0 0 18px;padding:10px 14px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);border-radius:6px;font-size:12px;color:#c8d0dc}}
.basis-strip span{{white-space:nowrap}}
.basis-strip strong{{color:#f7f4ee;font-weight:600}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · Internal</div>
    <h1>DB→DLR Replenishment — CY2025</h1>
    <div class="rule"></div>
    <p class="lead">Which part numbers show the largest mismatch between ISZE billing and sales to dealer — and where should each distributor review replenishment or stocking? Five distributors with sales-to-dealer data · UTI sold_to 1799 only, never blended with UMI.</p>
    <div class="basis-strip">
      <span><strong>OBSERVED</strong> — Parts billed through 30 June 2026</span>
      <span><strong>SALES TO DEALER</strong> — Available for five distributors only</span>
      <span><strong>MODELLED</strong> — Reference dealer price valuation of qty gaps (not observed lost revenue)</span>
    </div>
    <div class="hero-kpis" id="hero-kpis">{hero}</div>
  </div>
</div>
<div class="toolbar">
  <div class="filters" id="db-filters">{db_chips}</div>
  <label>Signal <select id="fSignal">{sig_opts}</select></label>
  <label>Search PN <input id="fPn" placeholder="part number"/></label>
  <span class="row-count" id="rowCount">{len(rows)} rows</span>
</div>
<div class="wrap">
  <div class="callout" id="leakCallout">{callout}</div>
  <div class="grid2">
    <div class="card"><h3>Five-DB comparison · reference-price exposure</h3><p class="cap">Five-distributor observed subset · side-by-side · reference dealer price × qty gap</p>{eur_chart}</div>
    <div class="card"><h3>Pipeline donut · PN counts</h3><p class="cap">Mismatch vs overstock vs balanced · operational signals</p>{pipe_donut}</div>
  </div>
  <div class="grid2">
    <div class="card"><h3>Pipeline mix bar</h3><p class="cap">Mismatch vs overstock vs balanced · PN counts</p>{mix_chart}</div>
    <div class="card"><h3>Pipeline signal mix by DB</h3><p class="cap">Mismatch vs overstock PN counts by DB</p><div class="bar-rows">{mix_db_html}</div></div>
    <div class="card"><h3>Sales to dealer vs bill by DB</h3><p class="cap">Sales to dealer qty ÷ ISZE bill qty by DB</p>{st_chart}</div>
  </div>
  <h2><span class="no">↓</span> · Exception register</h2>
  <p class="lead">Sortable drill-down · filter by DB chip or signal · AIM L1 when mapped.</p>
  <div class="table-scroll">
  <table class="matrix" id="tbl">
    <thead><tr>
      <th data-key="pn">PN</th><th data-key="db">DB</th><th data-key="signal">Signal</th><th data-key="aim">AIM L1</th>
      <th data-key="gap_eur" class="num">Reference-price exposure €</th><th data-key="bill_qty" class="num">Bill qty</th>
      <th data-key="sellout_qty" class="num">{LABELS['sales_to_dealer_qty']}</th><th data-key="qty_gap" class="num">Qty gap</th>
      <th data-key="ratio" class="num">Ratio</th><th data-key="bill_eur" class="num">Bill €</th>
    </tr></thead>
    <tbody>{_repl_rows(rows)}</tbody>
  </table>
  </div>
  <p class="foot">Built {built} · SSR charts · Sources: replenishment_summary_cy2025.parquet, replenishment_exceptions_cy2025.csv · Internal.</p>
</div>
<script>
document.querySelectorAll('#db-filters button').forEach(btn=>{{
  btn.onclick=()=>{{
    document.querySelectorAll('#db-filters button').forEach(b=>b.classList.toggle('on',b===btn));
    filterRows();
  }};
}});
function filterRows(){{
  const db=document.querySelector('#db-filters button.on')?.dataset.db||'';
  const sig=document.getElementById('fSignal').value;
  const pn=document.getElementById('fPn').value.trim();
  let n=0;
  document.querySelectorAll('#tbl tbody tr').forEach(tr=>{{
    let ok=true;
    if(db && tr.dataset.db!==db) ok=false;
    if(sig && tr.dataset.signal!==sig) ok=false;
    if(pn && !tr.dataset.pn.includes(pn)) ok=false;
    tr.classList.toggle('is-hide',!ok); if(ok) n++;
  }});
  document.getElementById('rowCount').textContent=n+' rows';
}}
['fSignal','fPn'].forEach(id=>document.getElementById(id).addEventListener('input',filterRows));
</script>
</body>
</html>"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(f'@echo off\r\nstart "" "%~dp0ISZE_DB_DLR_Replenishment_CY2025.html"\r\n', encoding="utf-8")


def main() -> int:
    payload = build_payload()
    write_html(payload)
    print(f"wrote {OUT_HTML} ({len(payload['rows'])} rows)")
    print(f"wrote {OUT_CMD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
