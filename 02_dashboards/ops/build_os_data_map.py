"""Generate ISZE_OS_Data_Map.html from 00_docs/ISZE_OS_DATA_MAP.yaml.

Run from anywhere:
  python ISZE/02_dashboards/ops/build_os_data_map.py
"""
from __future__ import annotations

import html
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ISZE_ROOT = HERE.parents[1]
YAML_PATH = ISZE_ROOT / "00_docs" / "ISZE_OS_DATA_MAP.yaml"
OUT_HTML = HERE / "ISZE_OS_Data_Map.html"
OUT_CMD = HERE / "OPEN_ISZE_OS_Data_Map.cmd"

STATUS_ORDER = ("have", "partial", "need", "closed", "org")
STATUS_HEX = {
    "have": "#1d9e75",
    "partial": "#eda100",
    "need": "#c0552d",
    "closed": "#888780",
    "org": "#2a78d6",
}
STATUS_BG = {
    "have": "#e4f5ee",
    "partial": "#fff3d6",
    "need": "#f8e4dc",
    "closed": "#eceae4",
    "org": "#dcecfc",
}
STATUS_INK = {
    "have": "#1d6b4f",
    "partial": "#8a6500",
    "need": "#8a3030",
    "closed": "#444",
    "org": "#1a4a7a",
}


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def counts_for(items: list[dict]) -> dict[str, int]:
    out = {k: 0 for k in STATUS_ORDER}
    for it in items:
        st = it.get("status")
        if st in out:
            out[st] += 1
    return out


def all_items(data: dict) -> list[dict]:
    rows = []
    for cap in data["capabilities"]:
        for it in cap["items"]:
            rows.append({**it, "cap_id": cap["id"], "cap_name": cap["name"]})
    return rows


def build(data: dict) -> str:
    items = all_items(data)
    tot = counts_for(items)
    index_den = tot["have"] + tot["partial"] + tot["need"]
    completeness = round(100.0 * tot["have"] / index_den) if index_den else 0
    n_caps = len(data["capabilities"])
    n_items = len(items)
    n_asks = len(data.get("asks") or [])
    n_closed = len(data.get("closed_doors") or [])
    snap = data["snapshot_date"]
    completeness_tip = (data.get("completeness") or {}).get("tooltip") or ""

    # Heatmap SVG — rows = capabilities, cols = statuses
    row_h, label_w, col_w, head_h = 36, 168, 72, 28
    svg_w = label_w + col_w * 5 + 16
    svg_h = head_h + row_h * n_caps + 8
    heat_rows = []
    for i, cap in enumerate(data["capabilities"]):
        c = counts_for(cap["items"])
        y = head_h + i * row_h
        heat_rows.append(
            f'<text x="8" y="{y + 24}" class="ax">{esc(cap["name"])}</text>'
        )
        for j, st in enumerate(STATUS_ORDER):
            n = c[st]
            x = label_w + j * col_w
            fill = STATUS_BG[st] if n else "#f7f4ee"
            ink = STATUS_INK[st] if n else "#c4bfb4"
            heat_rows.append(
                f'<rect x="{x + 4}" y="{y + 6}" width="{col_w - 10}" height="{row_h - 10}" '
                f'rx="3" fill="{fill}" stroke="#d9d3c8"/>'
                f'<text x="{x + col_w / 2}" y="{y + 24}" text-anchor="middle" '
                f'fill="{ink}" font-weight="700" font-size="14">{n}</text>'
            )
    col_heads = []
    for j, st in enumerate(STATUS_ORDER):
        x = label_w + j * col_w + col_w / 2
        col_heads.append(
            f'<text x="{x}" y="18" text-anchor="middle" class="tk">'
            f'{esc(data["statuses"][st]["label"])}</text>'
        )
    heatmap_svg = (
        f'<svg viewBox="0 0 {svg_w} {svg_h}" class="ch" role="img" '
        f'aria-label="Capability by status counts">'
        f"{''.join(col_heads)}{''.join(heat_rows)}</svg>"
    )

    # Stacked bars — share of requestable (have+partial+need) plus closed/org as thin tail
    bar_w = 420
    stacked = []
    for i, cap in enumerate(data["capabilities"]):
        c = counts_for(cap["items"])
        total = sum(c.values()) or 1
        y = 10 + i * 32
        x = 168
        stacked.append(
            f'<text x="160" y="{y + 14}" text-anchor="end" class="ax">{esc(cap["name"])}</text>'
        )
        for st in STATUS_ORDER:
            w = (c[st] / total) * bar_w
            if c[st] == 0:
                continue
            stacked.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="18" fill="{STATUS_HEX[st]}"/>'
            )
            x += w
        stacked.append(
            f'<text x="{168 + bar_w + 8}" y="{y + 14}" class="tk">{total}</text>'
        )
    stacked_h = 10 + n_caps * 32 + 8
    stacked_svg = (
        f'<svg viewBox="0 0 640 {stacked_h}" class="ch" role="img" '
        f'aria-label="Status mix per capability">'
        f"{''.join(stacked)}</svg>"
    )

    # Matrix rows
    matrix_rows = []
    for cap in data["capabilities"]:
        matrix_rows.append(
            f'<tr class="caphead" data-cap="{esc(cap["id"])}">'
            f'<td colspan="6">{esc(cap["name"])} — {esc(cap["question"])}</td></tr>'
        )
        for it in cap["items"]:
            st = it["status"]
            ask = it.get("ask") or it.get("how_to_find") or "—"
            integ = it.get("integrity") or ""
            period = it.get("period") or "—"
            matrix_rows.append(
                f'<tr class="item" data-status="{esc(st)}" data-cap="{esc(cap["id"])}">'
                f'<td>{esc(it["name"])}</td>'
                f'<td class="period">{esc(period)}</td>'
                f'<td><span class="pill {esc(st)}">{esc(data["statuses"][st]["label"])}</span></td>'
                f'<td>{esc(it.get("owner") or "—")}</td>'
                f'<td>{esc(integ)}</td>'
                f'<td>{esc(ask)}</td></tr>'
            )

    filter_btns = ['<button type="button" class="on" data-filter="all">All</button>']
    for st in STATUS_ORDER:
        filter_btns.append(
            f'<button type="button" data-filter="{esc(st)}">'
            f'{esc(data["statuses"][st]["label"])} · {tot[st]}</button>'
        )

    ask_cards = []
    item_by_id = {it["id"]: it for it in items}
    for a in data.get("asks") or []:
        it = item_by_id.get(a["item"], {})
        ask_cards.append(
            f'<article class="ask">'
            f'<div class="ask-rank">{a["rank"]:02d}</div>'
            f'<div><h3>{esc(it.get("name") or a["item"])}</h3>'
            f'<p class="who">Ask {esc(a["who"])}</p>'
            f'<p>{esc(a["ask"])}</p></div></article>'
        )

    door_cards = []
    for d in data.get("closed_doors") or []:
        door_cards.append(
            f'<article class="door">'
            f'<p class="since">Closed {esc(d.get("since") or "")}</p>'
            f'<h3>{esc(d["title"])}</h3>'
            f'<p>{esc(d["note"])}</p></article>'
        )

    integ = data.get("integrity") or {}
    guard_cards = []
    for g in integ.get("quote_guards") or []:
        guard_cards.append(
            f'<article class="guard">'
            f'<div class="gid">{esc(g["id"])}</div>'
            f'<div><h3>{esc(g["title"])}</h3>'
            f'<p>{esc(g["note"])}</p></div></article>'
        )
    frag_rows = []
    for f in integ.get("fragments") or []:
        frag_rows.append(
            f"<tr><td>{esc(f['name'])}</td><td>{esc(f['role'])}</td></tr>"
        )
    stale_lis = "".join(f"<li>{esc(s)}</li>" for s in (integ.get("stale_on_page10") or []))
    donot_lis = "".join(f"<li>{esc(s)}</li>" for s in (integ.get("do_not") or []))

    status_legend = " · ".join(
        f'{esc(data["statuses"][st]["label"])}: {esc(data["statuses"][st]["meaning"])}'
        for st in STATUS_ORDER
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE · Isuzu OS data map</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:15px;line-height:1.5}}
h1,h2,h3,h4{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}}
.hero{{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:42px 28px 28px}}
.hero-inner{{max-width:1180px;margin:0 auto}}
.brand{{font-family:Georgia,serif;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#c9d4e6;margin-bottom:14px}}
.hero h1{{color:#fff;font-size:34px;line-height:1.12;margin:0 0 12px;font-weight:400}}
.hero .rule{{width:64px;height:3px;background:#c0552d;margin:0 0 16px}}
.hero .lead{{max-width:760px;font-size:15.5px;color:#d5dce8;margin:0 0 22px}}
.hero-kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}
.hk{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);padding:14px 16px;position:relative;cursor:help}}
.hk .v{{font-size:28px;font-weight:700;letter-spacing:-.5px;color:#fff}}
.hk .l{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#aeb9cb;margin-top:4px}}
.hk .n{{font-size:12px;color:#9aa8bd;margin-top:6px;line-height:1.35}}
.hk .tip{{display:none;position:absolute;left:0;top:calc(100% + 8px);width:min(320px,70vw);
  background:#15233c;color:#f7f4ee;border-top:3px solid #c0552d;padding:12px 14px;
  font-size:12.5px;line-height:1.45;z-index:50;box-shadow:0 8px 24px rgba(0,0,0,.25)}}
.hk:hover .tip,.hk:focus-within .tip{{display:block}}
.tabs{{display:flex;gap:0;max-width:1180px;margin:0 auto;padding:0 28px;background:#f7f4ee;
  border-bottom:1px solid #d9d3c8;position:sticky;top:0;z-index:20}}
.tabs button{{appearance:none;border:0;background:transparent;padding:14px 20px;font:inherit;
  font-size:14px;color:#6b6256;cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-1px}}
.tabs button.active{{color:#1a2b4a;font-weight:600;border-bottom-color:#c0552d}}
.tabs button:hover{{color:#1a2b4a}}
.panel{{display:none}}
.panel.active{{display:block}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 28px 80px}}
h2{{font-size:22px;margin:8px 0 8px;padding-bottom:8px;border-bottom:2px solid #1a2b4a}}
h2 .no{{color:#c0552d}}
.lead{{color:#6b6256;margin:0 0 18px;max-width:820px}}
.callout{{border-left:3px solid #c0552d;background:#fff;padding:14px 16px;margin:0 0 20px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.card{{background:#fff;border:1px solid #d9d3c8;padding:18px 18px 14px}}
.card h3{{font-size:15px;margin:0 0 6px}}
.card .cap{{font-size:12.5px;color:#6b6256;margin:0 0 12px}}
.legend{{font-size:12.5px;color:#6b6256;margin:12px 0 0;line-height:1.55}}
svg.ch{{width:100%;height:auto;display:block}}
svg.ch text{{font-family:"Segoe UI",Arial,sans-serif}}
svg.ch .tk{{font-size:11px;fill:#6b6256}}
svg.ch .ax{{font-size:12px;fill:#222}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}}
.filters button{{appearance:none;border:1px solid #d9d3c8;background:#fff;color:#222;
  padding:7px 12px;font:inherit;font-size:13px;cursor:pointer}}
.filters button.on{{background:#15233c;color:#f7f4ee;border-color:#15233c}}
.filters button:hover{{border-color:#c0552d}}
table.matrix{{width:100%;border-collapse:collapse;font-size:13px;background:#fff}}
.matrix thead th{{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:8px 10px;
  font-size:11px;text-transform:uppercase;letter-spacing:.05em;position:sticky;top:48px;z-index:6}}
.matrix td{{padding:8px 10px;border-bottom:1px solid #e8e4dc;color:#222;vertical-align:top}}
.matrix td.period{{font-size:12px;color:#444;max-width:220px}}
.matrix tbody tr.caphead td,
.matrix tbody tr.caphead.pack td{{background:#15233c;color:#f7f4ee;font-family:Georgia,serif;font-size:14px}}
.matrix tbody tr.item td{{background:#fff;color:#222}}
.matrix tbody tr.item:nth-child(even) td{{background:#faf8f4;color:#222}}
.matrix tbody tr.is-hide{{display:none}}
.pill{{display:inline-block;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;
  padding:2px 8px;font-weight:700}}
.pill.have{{background:#e4f5ee;color:#1d6b4f}}
.pill.partial{{background:#fff3d6;color:#8a6500}}
.pill.need{{background:#f8e4dc;color:#8a3030}}
.pill.closed{{background:#eceae4;color:#444}}
.pill.org{{background:#dcecfc;color:#1a4a7a}}
.asks{{display:grid;gap:10px}}
.ask{{display:grid;grid-template-columns:52px 1fr;gap:12px;background:#fff;border:1px solid #d9d3c8;padding:14px 16px}}
.ask-rank{{font-family:Georgia,serif;font-size:22px;color:#c0552d}}
.ask h3{{font-size:16px;margin:0 0 4px}}
.ask .who{{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#6b6256;margin:0 0 6px}}
.ask p{{margin:0;font-size:13.5px}}
.doors{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.door{{background:#fff;border:1px solid #d9d3c8;border-top:3px solid #888780;padding:14px 16px}}
.door .since{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#6b6256;margin:0 0 6px}}
.door h3{{font-size:15px;margin:0 0 8px}}
.door p{{margin:0;font-size:13.5px}}
.guards{{display:grid;gap:10px;margin-bottom:22px}}
.guard{{display:grid;grid-template-columns:72px 1fr;gap:12px;background:#fff;border:1px solid #d9d3c8;
  border-left:3px solid #c0552d;padding:14px 16px}}
.gid{{font-family:Georgia,serif;font-size:15px;color:#c0552d}}
.guard h3{{font-size:15px;margin:0 0 6px}}
.guard p{{margin:0;font-size:13.5px}}
.frag td{{padding:8px 10px;border-bottom:1px solid #e8e4dc;color:#222}}
.frag th{{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase}}
.frag tbody tr:nth-child(even) td{{background:#faf8f4;color:#222}}
.stale,.donot{{background:#fff;border:1px solid #d9d3c8;padding:14px 18px;margin:0 0 14px}}
.stale h3,.donot h3{{font-size:15px;margin:0 0 8px}}
.stale ul,.donot ul{{margin:0;padding-left:18px}}
.foot{{margin-top:40px;padding-top:14px;border-top:1px solid #d9d3c8;font-size:11.5px;color:#6b6256;line-height:1.65}}
@media(max-width:900px){{
  .hero-kpis,.grid2,.doors{{grid-template-columns:1fr}}
  .hero h1{{font-size:26px}}
  .wrap,.hero,.tabs{{padding-left:16px;padding-right:16px}}
}}
@media print{{
  .tabs,.filters{{display:none}}
  .panel{{display:block!important}}
}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · aftersales OS</div>
    <h1>What data the OS still needs</h1>
    <div class="rule"></div>
    <p class="lead">{esc(data["purpose"]).strip()}</p>
    <div class="hero-kpis">
      <div class="hk" tabindex="0">
        <div class="v">{completeness}%</div>
        <div class="l">Catalogue completeness</div>
        <div class="n">Have ÷ requestable · {snap}</div>
        <div class="tip">{esc(completeness_tip).strip()}</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{tot["have"]}</div>
        <div class="l">Have</div>
        <div class="n">Wired and quotable when the gate is green</div>
        <div class="tip">{esc(data["statuses"]["have"]["meaning"])} Count on this catalogue, snapshot {esc(snap)}. Not a FACTS KPI.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{tot["partial"]}</div>
        <div class="l">Partial</div>
        <div class="n">Some markets, years, or joins only</div>
        <div class="tip">{esc(data["statuses"]["partial"]["meaning"])} Snapshot {esc(snap)}. Caveat lives on the row.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{tot["need"]}</div>
        <div class="l">Need</div>
        <div class="n">{n_asks} ranked asks still requestable</div>
        <div class="tip">{esc(data["statuses"]["need"]["meaning"])} Ranked on the Ask list tab. Snapshot {esc(snap)}.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{n_closed}</div>
        <div class="l">Closed doors</div>
        <div class="n">Do not re-ask · {tot["org"]} org-scale items aside</div>
        <div class="tip">{esc(data["statuses"]["closed"]["meaning"])} Org-scale programmes ({tot["org"]}) sit on a separate chip logic: they are not holes in this catalogue. Snapshot {esc(snap)}.</div>
      </div>
    </div>
  </div>
</div>

<nav class="tabs" role="tablist" aria-label="OS data map sections">
  <button type="button" class="active" data-tab="matrix" role="tab" aria-selected="true">Matrix</button>
  <button type="button" data-tab="asks" role="tab" aria-selected="false">Ask list</button>
  <button type="button" data-tab="closed" role="tab" aria-selected="false">Closed doors</button>
  <button type="button" data-tab="integrity" role="tab" aria-selected="false">Integrity overlay</button>
</nav>

<div class="wrap">

<div id="panel-matrix" class="panel active" role="tabpanel">
  <h2><span class="no">01</span> · Capability × status</h2>
  <p class="lead">{n_caps} OS layers · {n_items} data decisions. Colour is status, not rank. Closed and org are shown so they are not mistaken for missing requests.</p>
  <div class="grid2">
    <div class="card">
      <h3>Counts per layer</h3>
      <p class="cap">Each cell is how many data decisions sit in that status. Zero is pale, not green.</p>
      {heatmap_svg}
    </div>
    <div class="card">
      <h3>Mix inside each layer</h3>
      <p class="cap">Bar width = share of that layer. Green have · amber partial · terracotta need · grey closed · blue org.</p>
      {stacked_svg}
    </div>
  </div>
  <p class="legend">{status_legend}</p>

  <h2 style="margin-top:36px"><span class="no">02</span> · Every decision the OS should take</h2>
  <p class="lead">Filter by status. Capability headers stay navy; data rows stay ink on paper.</p>
  <div class="filters" id="filters">{''.join(filter_btns)}</div>
  <table class="matrix" id="matrix">
    <thead>
      <tr><th>Data decision</th><th>Period</th><th>Status</th><th>Owner</th><th>Integrity overlay</th><th>Ask / how to find</th></tr>
    </thead>
    <tbody>
      {''.join(matrix_rows)}
    </tbody>
  </table>
</div>

<div id="panel-asks" class="panel" role="tabpanel">
  <h2><span class="no">03</span> · Ranked asks</h2>
  <p class="lead">What to request next. This list does not implement P4, collect sell-out, or mail IML — it names the asks.</p>
  <div class="asks">{''.join(ask_cards)}</div>
</div>

<div id="panel-closed" class="panel" role="tabpanel">
  <h2><span class="no">04</span> · Do not re-ask</h2>
  <p class="lead">Confirmed unavailable, ruled out, or out of scope. Designing around these is the OS, not waiting for them.</p>
  <div class="doors">{''.join(door_cards)}</div>
</div>

<div id="panel-integrity" class="panel" role="tabpanel">
  <h2><span class="no">05</span> · Integrity is an overlay</h2>
  <div class="callout">There is already a pipeline page, a flag list, an open-issues note, an Evidence board, per-distributor pack holes, and a March 2026 IE40 dispute workbook. This tab does not clone any of them. It only says what still guards a quote, and what on the Streamlit page is stale.</div>

  <h3 class="sub" style="font-family:Georgia,serif;color:#1a2b4a;margin:8px 0 10px">Quote-guards still open</h3>
  <div class="guards">{''.join(guard_cards)}</div>

  <div class="grid2">
    <div class="stale">
      <h3>Refresh on the existing Streamlit page — do not rebuild it</h3>
      <ul>{stale_lis}</ul>
    </div>
    <div class="donot">
      <h3>Out of scope this pass</h3>
      <ul>{donot_lis}</ul>
    </div>
  </div>

  <h3 style="font-family:Georgia,serif;color:#1a2b4a;font-size:17px;margin:24px 0 8px">Where integrity already lives</h3>
  <p class="lead">Human names only — paths stay in the YAML for agents.</p>
  <table class="frag" style="width:100%;border-collapse:collapse;background:#fff">
    <thead><tr><th>Fragment</th><th>What it is</th></tr></thead>
    <tbody>{''.join(frag_rows)}</tbody>
  </table>
</div>

<p class="foot">{esc(data.get("sources_footnote") or "").strip()}</p>
</div>

<script>
(function(){{
  var tabs = document.querySelectorAll(".tabs button");
  tabs.forEach(function(btn){{
    btn.addEventListener("click", function(){{
      tabs.forEach(function(b){{ b.classList.remove("active"); b.setAttribute("aria-selected","false"); }});
      document.querySelectorAll(".panel").forEach(function(p){{ p.classList.remove("active"); }});
      btn.classList.add("active");
      btn.setAttribute("aria-selected","true");
      document.getElementById("panel-" + btn.getAttribute("data-tab")).classList.add("active");
    }});
  }});
  var filterBtns = document.querySelectorAll("#filters button");
  var rows = document.querySelectorAll("#matrix tbody tr.item");
  var caps = document.querySelectorAll("#matrix tbody tr.caphead");
  function apply(st){{
    filterBtns.forEach(function(b){{ b.classList.toggle("on", b.getAttribute("data-filter") === st); }});
    var visibleCaps = {{}};
    rows.forEach(function(tr){{
      var show = (st === "all") || (tr.getAttribute("data-status") === st);
      tr.classList.toggle("is-hide", !show);
      if (show) visibleCaps[tr.getAttribute("data-cap")] = true;
    }});
    caps.forEach(function(tr){{
      var id = tr.getAttribute("data-cap");
      tr.classList.toggle("is-hide", st !== "all" && !visibleCaps[id]);
    }});
  }}
  filterBtns.forEach(function(btn){{
    btn.addEventListener("click", function(){{ apply(btn.getAttribute("data-filter")); }});
  }});
}})();
</script>
</body>
</html>
"""


def main() -> None:
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    html_out = build(data)
    # visueel-rapport Regel 0: no CDN src/href
    if "https://" in html_out.split("<body", 1)[0] and (
        'src="https://' in html_out or "href=\"https://" in html_out
    ):
        raise SystemExit("CDN URL leaked into head")
    OUT_HTML.write_text(html_out, encoding="utf-8")
    OUT_CMD.write_text(
        f'@echo off\r\nstart "" "%~dp0{OUT_HTML.name}"\r\n',
        encoding="utf-8",
    )
    items = all_items(data)
    tot = counts_for(items)
    den = tot["have"] + tot["partial"] + tot["need"]
    pct = round(100 * tot["have"] / den) if den else 0
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {OUT_CMD}")
    print(
        f"items={len(items)} have={tot['have']} partial={tot['partial']} "
        f"need={tot['need']} closed={tot['closed']} org={tot['org']} completeness={pct}%"
    )


if __name__ == "__main__":
    main()
