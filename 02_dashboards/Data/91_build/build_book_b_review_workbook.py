#!/usr/bin/env python3
"""Book B revision review workbook — filterable HTML (internal).

Reads  : revision_book_b_top_review.csv
Writes : 01_data/01_Pricing/BOOK_B_REVISION_REVIEW_20260819.html
         01_data/01_Pricing/OPEN_BOOK_B_REVISION_REVIEW.cmd

UX shell cloned from ISZE_OS_Data_Map.html + Command Center charts.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1] / "02_dashboards" / "_build"
if str(BUILD) not in sys.path:
    sys.path.insert(0, str(BUILD))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import aftermarket_bi_data as BI  # noqa: E402
import render_ssr_charts as SSR  # noqa: E402
import tier_a_dashboard_common as T  # noqa: E402

SSR_CSS = SSR.SSR_CHART_CSS

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
TOP = DERIVED / "revision_book_b_top_review.csv"
OUT_HTML = ISZE / "01_data" / "01_Pricing" / "BOOK_B_REVISION_REVIEW_20260819.html"
OUT_CMD = OUT_HTML.with_name("OPEN_BOOK_B_REVISION_REVIEW.cmd")


def build_payload(df: pd.DataFrame) -> dict:
    aim_map = T.load_aim_by_pn()
    built_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = BI.book_b_rows_for_table(df, aim_map)
    bb_agg = BI.book_b_aggregates(df)

    leak = [x for x in rows if "LEAKAGE" in (x.get("action") or "").upper()]
    db_gap: dict[str, float] = {}
    for r in leak:
        db_gap[r["db"]] = db_gap.get(r["db"], 0) + float(r.get("qty_gap") or 0)
    biggest_db = max(db_gap, key=db_gap.get) if db_gap else "—"
    top = max(leak, key=lambda r: float(r.get("qty_gap") or 0)) if leak else {}
    by_action: dict[str, int] = {}
    for r in rows:
        by_action[r["action"]] = by_action.get(r["action"], 0) + 1

    seen = {r["db"] for r in rows if r.get("db")}
    dbs_in_data = [db for db in T.DB_ORDER if db in seen] + sorted(seen - set(T.DB_ORDER))
    return {
        "built_at": built_at,
        "dbs": dbs_in_data,
        "book_b": bb_agg,
        "hero": {
            "row_count": len(rows),
            "leakage_rows": len(leak),
            "biggest_db": biggest_db,
            "biggest_db_gap": T.safe_float(db_gap.get(biggest_db), ndigits=0),
            "top_pn": top.get("pn", "—"),
            "top_pn_gap": top.get("qty_gap"),
            "total_leak_gap": T.safe_float(sum(float(r.get("qty_gap") or 0) for r in leak), ndigits=0),
            "by_action": by_action,
            "book_b_conflicts": bb_agg.get("conflict_count", 0),
            "iam_undercut_count": len(bb_agg.get("iam_undercut", [])),
        },
        "rows": rows,
    }


def _book_b_rows(rows: list[dict]) -> str:
    parts = []
    for r in rows:
        aim_cell = SSR.pill("aim", r.get("aim")) if r.get("aim") and r.get("aim") != "—" else "—"
        parts.append(
            f'<tr data-pn="{SSR.esc(r.get("pn",""))}" data-db="{SSR.esc(r.get("db",""))}" '
            f'data-action="{SSR.esc(r.get("action",""))}" data-pipeline="{SSR.esc(r.get("pipeline",""))}">'
            f'<td>{SSR.esc(r.get("pn"))}</td><td>{SSR.esc(r.get("db"))}</td>'
            f'<td>{SSR.pill(r.get("action_class","act"), r.get("action") or "")}</td>'
            f'<td>{SSR.pill(r.get("pipeline_class","act"), r.get("pipeline") or "")}</td>'
            f'<td>{aim_cell}</td><td class="num">{SSR.fmt_int(r.get("bill_qty"))}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("sellout_qty"))}</td><td class="num">{SSR.fmt_int(r.get("qty_gap"))}</td>'
            f'<td class="num">{SSR.fmt_num(r.get("ks_index")) if r.get("ks_index") is not None else "—"}</td>'
            f'<td class="bucket">{SSR.esc(r.get("bucket"))}</td>'
            f'<td class="num">{SSR.fmt_int(r.get("forecast_eur"))}</td></tr>'
        )
    return "".join(parts)


def write_html(payload: dict) -> None:
    built = (payload.get("built_at") or "")[:10]
    H = payload.get("hero") or {}
    bb = payload.get("book_b") or {}
    rows = payload.get("rows") or []
    dbs = payload.get("dbs") or []

    hero = SSR.hero_kpis([
        (SSR.fmt_int(H.get("leakage_rows")), "REVIEW_LEAKAGE rows", f'of {SSR.fmt_int(H.get("row_count"))} in register',
         "Rows flagged REVIEW_LEAKAGE in the Book B revision queue. Provisional — no allocation run applied."),
        (SSR.fmt_int(H.get("book_b_conflicts")), "Ambition vs guardrail", f'{SSR.fmt_int(H.get("iam_undercut_count"))} IAM undercut',
         "Growth/ambition Book B bucket rows that also carry HOLD, proxy adverse, IAM undercut, or high list exposure."),
        (SSR.esc(H.get("biggest_db")), "Biggest leakage DB", f'{SSR.fmt_int(H.get("biggest_db_gap"))} unit gap',
         "DB with largest sell-out minus bill qty gap among REVIEW_LEAKAGE rows."),
        (SSR.esc(H.get("top_pn")), "Top leakage PN", f'Gap {SSR.fmt_int(H.get("top_pn_gap"))} units',
         "Highest qty gap among leakage review rows."),
        (str(len(H.get("by_action") or {})), "Action types", "Filter dropdown",
         "KS index = shop price ÷ reference sell-out where KS quote exists."),
    ])
    callout = (
        f"<strong>Headline:</strong> {SSR.fmt_int(H.get('leakage_rows'))} REVIEW_LEAKAGE rows · "
        f"{SSR.fmt_int(H.get('book_b_conflicts'))} ambition/guardrail conflicts · top PN "
        f"<strong>{SSR.esc(H.get('top_pn'))}</strong> gaps {SSR.fmt_int(H.get('top_pn_gap'))} units. No alloc run."
    )
    actions = sorted({str(r.get("action") or "") for r in rows if r.get("action")})
    act_opts = '<option value="">All actions</option>' + "".join(f'<option value="{SSR.esc(a)}">{SSR.esc(a)}</option>' for a in actions)
    db_chips = '<button type="button" class="on" data-db="">All DBs</button>' + "".join(
        f'<button type="button" data-db="{SSR.esc(db)}">{SSR.esc(db)}</button>' for db in dbs
    )
    ba = bb.get("bucket_action") or []
    buckets = list(dict.fromkeys(x.get("bucket") for x in ba))[:8]
    actions_ba = list(dict.fromkeys(x.get("action") for x in ba))
    palette = ["#c0552d", "#15233c", "#2a78d6", "#1d9e75", "#eda100", "#8a3030", "#1a4a7a"]
    stacked = ['<div class="bar-rows ssr-chart">']
    for b in buckets:
        total = sum(int(x.get("count") or 0) for x in ba if x.get("bucket") == b) or 1
        stacked.append(f'<div class="bar-row"><span class="lbl">{SSR.esc(b[:20])}</span><span class="track" style="display:flex;height:16px">')
        for i, act in enumerate(actions_ba):
            hit = next((x for x in ba if x.get("bucket") == b and x.get("action") == act), None)
            cnt = int(hit.get("count") or 0) if hit else 0
            if cnt:
                stacked.append(f'<span class="fill" style="width:{100*cnt/total:.1f}%;background:{palette[i%len(palette)]}" title="{SSR.esc(act)}"></span>')
        stacked.append("</span></div>")
    stacked.append("</div>")
    stacked_html = "".join(stacked)
    by_action = H.get("by_action") or {}
    action_items = [{"action": k, "count": v} for k, v in sorted(by_action.items(), key=lambda x: -x[1])[:8]]
    action_chart = SSR.horizontal_bar_rows(action_items, label_key="action", value_key="count", color=SSR.COLORS["blue"],
        value_fn=lambda v: str(int(v)))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Book B Revision Review</title>
<style>{T.TIER_A_CSS}{SSR_CSS}</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · Book B · internal internal</div>
    <h1>Book B Revision Review</h1>
    <div class="rule"></div>
    <p class="lead">Top non-HOLD revision queue · provisional forecast weights · no alloc run · charts first. IUK≠ITUK · UTI≠UMI.</p>
    <div class="hero-kpis" id="hero-kpis">{hero}</div>
  </div>
</div>
<div class="toolbar">
  <div class="filters" id="db-filters">{db_chips}</div>
  <label>Action <select id="fAct">{act_opts}</select></label>
  <label>Search PN <input id="fPn" placeholder="part number"/></label>
  <span class="row-count" id="rowCount">{len(rows)} rows</span>
</div>
<div class="wrap">
  <div class="callout" id="leakCallout">{callout}</div>
  <div class="grid2">
    <div class="card"><h3>Book B bucket × action</h3><p class="cap">Stacked counts · ambition vs guardrail visible</p>{stacked_html}</div>
    <div class="card"><h3>Recommended action mix</h3><p class="cap">Top 500 review pack · no alloc</p>{action_chart}</div>
  </div>
  <h2><span class="no">↓</span> · Revision register</h2>
  <p class="lead">Sortable drill-down · Book B bucket column — full width, no cut-off.</p>
  <div class="table-scroll">
  <table class="matrix" id="tbl">
    <thead><tr>
      <th data-key="pn">PN</th><th data-key="db">DB</th><th data-key="action">Action</th><th data-key="pipeline">Pipeline</th>
      <th data-key="aim">AIM L1</th><th data-key="bill_qty" class="num">Bill qty</th><th data-key="sellout_qty" class="num">Sell-out</th>
      <th data-key="qty_gap" class="num">Qty gap</th><th data-key="ks_index" class="num">KS index</th>
      <th data-key="bucket">Book B bucket</th><th data-key="forecast_eur" class="num">Forecast €</th>
    </tr></thead>
    <tbody>{_book_b_rows(rows)}</tbody>
  </table>
  </div>
  <p class="foot">Built {built} · SSR charts · Source: revision_book_b_top_review.csv · Provisional weights — no alloc · Internal internal.</p>
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
  const act=document.getElementById('fAct').value;
  const pn=document.getElementById('fPn').value.trim();
  let n=0;
  document.querySelectorAll('#tbl tbody tr').forEach(tr=>{{
    let ok=true;
    if(db && tr.dataset.db!==db) ok=false;
    if(act && tr.dataset.action!==act) ok=false;
    if(pn && !tr.dataset.pn.includes(pn)) ok=false;
    tr.classList.toggle('is-hide',!ok); if(ok) n++;
  }});
  document.getElementById('rowCount').textContent=n+' rows';
}}
['fAct','fPn'].forEach(id=>document.getElementById(id).addEventListener('input',filterRows));
</script>
</body>
</html>"""
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(f'@echo off\r\nstart "" "%~dp0{OUT_HTML.name}"\r\n', encoding="utf-8")


def main() -> int:
    if not TOP.is_file():
        print(f"MISSING {TOP}", file=sys.stderr)
        return 1
    df = pd.read_csv(TOP, dtype=str, low_memory=False)
    payload = build_payload(df)
    write_html(payload)
    print(f"wrote {OUT_HTML} ({len(df)} source rows)")
    print(f"wrote {OUT_CMD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
