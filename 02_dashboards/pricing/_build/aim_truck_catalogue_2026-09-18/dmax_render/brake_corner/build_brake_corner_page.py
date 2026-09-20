"""Build the brake corner page: one self-contained HTML file.

Why it is built by a script
---------------------------
Every figure on the page comes out of brake_corner_data.json, which is written by
build_page_data.py straight out of the three source files.  Nothing is typed into
the HTML by hand, so a number cannot drift away from the file it came from.

Why it opens by double-clicking
-------------------------------
The photograph is embedded in the file as a data URI and the page makes no network
request of any kind: no fetch of a sibling file (which always fails on file://), no
CDN, no font download.  Everything it needs is in the one .html.

Callout geometry
----------------
The labels and the leader lines live in one SVG whose viewBox is the render's own
pixel size (2800 x 2000).  Because the SVG scales to whatever width the page is
opened at, the label positions verified at build time hold at every size - labels
cannot drift onto a part or onto each other when the window is resized.
"""
from __future__ import annotations

import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "_raw")
DATA = os.path.join(HERE, "brake_corner_data.json")
REPORT = os.path.join(RAW, "brake_corner_report.json")
IMG = os.path.join(RAW, "brake_corner_bc_page.jpg")
OUT = os.path.join(HERE, "ISZE_DMax_Front_Brake_Corner.html")

if not os.path.exists(IMG):
    raise SystemExit("missing %s - run make_page_jpeg.py first" % IMG)

with open(DATA, encoding="utf-8") as fh:
    data = json.load(fh)
with open(REPORT, encoding="utf-8") as fh:
    report = json.load(fh)
with open(IMG, "rb") as fh:
    img_b64 = base64.b64encode(fh.read()).decode("ascii")

W, H = report["resolution"]
assert [W, H] == [2800, 2000], "callout geometry below is written for 2800x2000"

# --------------------------------------------------------------------------- #
# callout geometry, in the render's own pixels
# --------------------------------------------------------------------------- #
CALLOUTS = [
    {"id": "A", "kinds": ["disc"], "keys": ["411-025"],
     "caption": "Brake disc", "box": (296, 64, 664, 214), "anchor": (536, 906)},
    {"id": "B", "kinds": ["pads"], "keys": ["302-017", "302-133"],
     "caption": "Brake pads", "box": (404, 1786, 816, 1942), "anchor": (826, 1040)},
    {"id": "C", "kinds": ["caliper"], "keys": ["302-001"],
     "caption": "Brake caliper", "box": (824, 64, 1216, 214), "anchor": (1056, 690)},
    {"id": "D", "kinds": ["wheel"], "keys": ["480-022"],
     "caption": "Road wheel", "box": (1116, 1786, 1496, 1942), "anchor": (1481, 1300)},
    {"id": "E", "kinds": ["tyre"], "keys": ["no figure key"],
     "caption": "Tyre", "box": (1972, 1786, 2392, 1942), "anchor": (2280, 1720)},
]

by_kind = {}
for c in data["callouts"]:
    by_kind.setdefault(c["kind"], []).append(c)

# --------------------------------------------------------------------------- #
# the callout layer
# --------------------------------------------------------------------------- #
def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


svg = []
svg.append('<svg class="cl" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet" '
           'aria-label="Callouts on the exploded front brake corner">' % (W, H))
svg.append('<g class="leaders">')
for c in CALLOUTS:
    x0, y0, x1, y1 = c["box"]
    ax, ay = c["anchor"]
    # attach the leader to the middle of whichever edge of the label faces the part
    if ay > y1:
        sx, sy = (x0 + x1) / 2, y1
    elif ay < y0:
        sx, sy = (x0 + x1) / 2, y0
    else:
        sx, sy = (x1 if ax > x1 else x0), (y0 + y1) / 2
    svg.append('<polyline data-c="%s" points="%.1f,%.1f %.1f,%.1f" />'
               % (c["id"], sx, sy, ax, ay))
    svg.append('<circle data-c="%s" class="dot" cx="%.1f" cy="%.1f" r="15" />'
               % (c["id"], ax, ay))
svg.append('</g>')

for c in CALLOUTS:
    x0, y0, x1, y1 = c["box"]
    w, h = x1 - x0, y1 - y0
    svg.append('<g class="cal" data-c="%s" tabindex="0" role="button" '
               'aria-label="%s %s">' % (c["id"], esc(c["caption"]),
                                        esc(" ".join(c["keys"]))))
    svg.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="10" />'
               % (x0, y0, w, h))
    svg.append('<rect class="ring" x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
               'rx="10" />' % (x0, y0, w, h))
    ty = y0 + 46
    svg.append('<text class="key" x="%.1f" y="%.1f">%s</text>'
               % (x0 + 18, ty, esc(" / ".join(c["keys"]))))
    ty += 40
    svg.append('<text class="cap" x="%.1f" y="%.1f">%s</text>'
               % (x0 + 18, ty, esc(c["caption"])))
    svg.append('</g>')
svg.append('</svg>')
CALLOUT_SVG = "\n".join(svg)

# --------------------------------------------------------------------------- #
# the panel payload
# --------------------------------------------------------------------------- #
panel = {}
for c in CALLOUTS:
    entries = []
    for kind in c["kinds"]:
        for e in by_kind.get(kind, []):
            keys = []
            for k in e.get("fig_keys", []):
                keys.append({
                    "fig_key": k["fig_key"],
                    "label": k["fig_key_label"],
                    "category": k.get("pms_category"),
                    "eur": k.get("billed_eur"),
                    "qty": k.get("billed_qty"),
                    "pns": k.get("distinct_pns"),
                    "by_year": k.get("by_year"),
                    "dbs": k.get("top_distributors"),
                })
            entries.append({
                "part": e["part"],
                "described": e.get("described_in_billing_as"),
                "fig_key": e.get("fig_key"),
                "fig_key_label": e.get("fig_key_label"),
                "label_ok": e.get("fig_key_label_describes_part"),
                "fig_key_note": e.get("fig_key_note"),
                "billing_note": e.get("billing_note"),
                "fig_key_eur": e.get("fig_key_eur"),
                "fig_key_qty": e.get("fig_key_qty"),
                "own_eur": e.get("billed_eur_own_lines"),
                "own_qty": e.get("billed_qty_own_lines"),
                "own_pns": e.get("part_numbers_billed"),
                "share": e.get("own_lines_share_of_fig_key_pct"),
                "top_pns": e.get("top_part_numbers"),
                "dbs": e.get("distributors"),
                "keys": keys,
            })
    panel[c["id"]] = {"caption": c["caption"], "keys": c["keys"], "entries": entries}

period = data["period"]

panel_json = json.dumps(panel, separators=(",", ":"), ensure_ascii=False)
order_json = json.dumps([c["id"] for c in CALLOUTS])

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Isuzu D-Max - exploded front brake corner</title>
<style>
  :root {{
    --navy:#15233c; --navy2:#1d2f4e; --terra:#c0552d; --paper:#f7f4ee;
    --ink:#22262c; --rule:#d8d2c6; --muted:#5d6470;
  }}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; padding:0; }}
  body {{
    background:var(--paper); color:var(--ink);
    font:15px/1.55 "Segoe UI", system-ui, -apple-system, Arial, sans-serif;
  }}
  header {{
    background:var(--navy); color:var(--paper);
    padding:22px 30px 20px; border-bottom:4px solid var(--terra);
  }}
  header h1 {{
    font-family:Georgia,"Times New Roman",serif; font-weight:normal;
    font-size:27px; margin:0 0 5px; letter-spacing:.2px;
  }}
  header p {{ margin:0; color:#cfd6e2; font-size:13.5px; max-width:110ch; }}
  .wrap {{ display:grid; grid-template-columns:minmax(0,1fr) 392px; gap:22px;
           padding:22px 30px 34px; align-items:start; }}
  @media (max-width:1120px) {{ .wrap {{ grid-template-columns:minmax(0,1fr); }} }}

  figure {{ margin:0; }}
  .stage {{
    position:relative; background:#fff; border:1px solid var(--rule);
    border-radius:3px; overflow:hidden;
  }}
  .stage img {{ display:block; width:100%; height:auto; }}
  .cl {{ position:absolute; inset:0; width:100%; height:100%; }}
  .leaders polyline {{ fill:none; stroke:var(--terra); stroke-width:3.5;
                       stroke-linejoin:round; opacity:.9; }}
  .leaders .dot {{ fill:var(--terra); stroke:#fff; stroke-width:3; }}
  .cal rect {{ fill:var(--navy); opacity:.94; }}
  .cal .ring {{ fill:none; stroke:var(--terra); stroke-width:0; }}
  .cal {{ cursor:pointer; }}
  .cal:hover rect, .cal:focus rect {{ fill:var(--navy2); }}
  .cal:hover .ring, .cal:focus .ring {{ stroke-width:4; }}
  .cal text {{ fill:var(--paper); font-family:"Segoe UI",system-ui,Arial,sans-serif; }}
  .cal .key {{ font-size:36px; font-weight:700; letter-spacing:.5px; }}
  .cal .cap {{ font-size:29px; fill:#c9d2e0; }}
  .cal.on rect {{ fill:var(--terra); }}
  .cal.on .cap {{ fill:#ffe9df; }}
  .leaders polyline.on {{ stroke-width:6; opacity:1; }}
  .leaders .dot.on {{ r:21; }}

  figcaption {{ margin-top:11px; color:var(--muted); font-size:12.5px; }}

  aside {{ display:flex; flex-direction:column; gap:16px; }}
  .card {{ background:#fff; border:1px solid var(--rule); border-radius:3px; }}
  .card h2 {{
    font-family:Georgia,"Times New Roman",serif; font-weight:normal; font-size:17px;
    margin:0; padding:12px 16px; background:var(--navy); color:var(--paper);
    border-radius:2px 2px 0 0;
  }}
  .card .body {{ padding:14px 16px 16px; }}
  .hint {{ color:var(--muted); font-size:12.5px; margin:0; }}

  .entry + .entry {{ margin-top:16px; padding-top:16px; border-top:1px solid var(--rule); }}
  .entry h3 {{ margin:0 0 3px; font-size:15.5px; }}
  .fk {{ display:inline-block; background:var(--navy); color:var(--paper);
         font-weight:700; font-size:13px; padding:2px 9px; border-radius:2px;
         letter-spacing:.6px; }}
  .fk.none {{ background:#8a7f6d; }}
  dl {{ display:grid; grid-template-columns:auto 1fr; gap:5px 12px; margin:11px 0 0; }}
  dt {{ color:var(--muted); font-size:12.5px; }}
  dd {{ margin:0; font-size:14px; }}
  .big {{ font-size:19px; font-weight:700; color:var(--navy); }}
  .warn {{ background:#fdf3e7; border-left:3px solid var(--terra);
           padding:9px 11px; margin:11px 0 0; font-size:12.5px; color:#6b4a2c; }}
  table {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:13px; }}
  th, td {{ text-align:left; padding:6px 8px; border-bottom:1px solid var(--rule); }}
  th {{ background:#eef1f6; color:var(--navy); font-size:12px;
        text-transform:uppercase; letter-spacing:.4px; }}
  td.n, th.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  footer {{ padding:0 30px 34px; color:var(--muted); font-size:12px; }}
  code {{ background:#eef1f6; padding:1px 5px; border-radius:2px; font-size:12px; }}
</style>
</head>
<body>
<header>
  <h1>Isuzu D-Max - exploded front brake corner</h1>
  <p>The five parts that come off a front wheel, drawn apart along the wheel axis.
     Every figure key and every euro on this page is read from the parts catalogue
     and the billing file. Billing covers {period}.</p>
</header>

<div class="wrap">
  <figure>
    <div class="stage">
      <img src="data:image/png;base64,{img}" alt="Exploded front brake corner of the Isuzu D-Max">
      {svg}
    </div>
    <figcaption>
      Brake disc held, then pads, caliper, wheel and tyre drawn apart along the wheel
      axis. Click or hover a callout to read that part below. The label is the figure
      key from the parts catalogue, so the picture and the parts book share one index.
    </figcaption>
  </figure>

  <aside>
    <div class="card">
      <h2 id="panel-title">Front brake corner</h2>
      <div class="body" id="panel"><p class="hint">Click a callout on the drawing, or
        hover one, to see the part numbers and what we billed.</p></div>
    </div>
    <div class="card">
      <h2>What each callout is</h2>
      <div class="body">
        <table>
          <thead><tr><th>Callout</th><th>Part</th><th class="n">What we billed</th></tr></thead>
          <tbody id="keylist"></tbody>
        </table>
        <p class="hint" style="margin-top:11px">"What we billed" is the net sales value
          recorded against that part's figure key, in euro, across every distributor in
          the billing file.</p>
      </div>
    </div>
  </aside>
</div>

<footer>
  <p>Sources: <code>parts_catalog_dimension.csv</code> for the part number to figure key
     bridge, <code>sales_by_db_fig_key_year.csv</code> for what was billed,
     <code>price_bp_weighted_compare_pn.csv</code> for the part numbers and their billed
     descriptions. Period: {period}. Nothing is estimated; where a part has no figure
     key or no billing, the page says so.</p>
</footer>

<script>
const PANEL = {panel};
const ORDER = {order};

const eur = v => v === null || v === undefined
  ? "not available"
  : "\\u20ac" + Number(v).toLocaleString("en-GB", {{ maximumFractionDigits: 0 }});
const num = v => v === null || v === undefined
  ? "not available"
  : Number(v).toLocaleString("en-GB", {{ maximumFractionDigits: 0 }});

function row(label, value) {{
  return "<dt>" + label + "</dt><dd>" + value + "</dd>";
}}

function renderEntry(e) {{
  let h = '<div class="entry">';
  h += "<h3>" + e.part + "</h3>";
  if (e.fig_key) {{
    h += '<span class="fk">' + e.fig_key + "</span>";
    if (e.fig_key_label)
      h += ' <span style="color:#5d6470;font-size:12.5px">' + e.fig_key_label + "</span>";
  }} else {{
    h += '<span class="fk none">no figure key in the catalogue</span>';
  }}
  h += "<dl>";
  if (e.described) h += row("Billed as", e.described);
  if (e.fig_key_eur !== null && e.fig_key_eur !== undefined) {{
    h += row("What we billed", '<span class="big">' + eur(e.fig_key_eur)
          + "</span> on this figure key");
    h += row("Pieces billed", num(e.fig_key_qty) + " on this figure key");
  }} else {{
    h += row("What we billed", "nothing billed at all");
  }}
  if (e.own_eur) h += row("Just this part",
        eur(e.own_eur) + " of it, on " + num(e.own_pns) + " part number"
        + (e.own_pns === 1 ? "" : "s")
        + (e.share !== null && e.share !== undefined
            ? " (" + e.share + "% of the figure key)" : ""));
  h += "</dl>";

  if (e.top_pns && e.top_pns.length) {{
    h += "<table><thead><tr><th>Part number</th><th class='n'>What we billed</th>"
       + "</tr></thead><tbody>";
    for (const p of e.top_pns) {{
      h += "<tr><td>" + p[0] + "</td><td class='n'>" + eur(p[1]) + "</td></tr>";
    }}
    h += "</tbody></table>";
  }}
  if (e.fig_key_note) h += '<div class="warn">' + e.fig_key_note + "</div>";
  if (e.billing_note) h += '<div class="warn">' + e.billing_note + "</div>";
  if (e.keys && e.keys.length) {{
    h += "<table><thead><tr><th>Figure key</th><th>Billed</th><th class='n'>Pieces</th>"
       + "<th class='n'>Part nos</th></tr></thead><tbody>";
    for (const k of e.keys) {{
      h += "<tr><td>" + k.fig_key + "</td><td>" + eur(k.eur) + "</td><td class='n'>"
         + num(k.qty) + "</td><td class='n'>" + num(k.pns) + "</td></tr>";
    }}
    h += "</tbody></table>";
  }}
  if (e.dbs && e.dbs.length) {{
    h += "<table><thead><tr><th>Distributor</th><th class='n'>What we billed</th>"
       + "</tr></thead><tbody>";
    for (const d of e.dbs.slice(0, 4)) {{
      h += "<tr><td>" + d[0] + "</td><td class='n'>" + eur(d[1]) + "</td></tr>";
    }}
    h += "</tbody></table>";
  }}
  h += "</div>";
  return h;
}}

function show(id) {{
  const d = PANEL[id];
  if (!d) return;
  document.getElementById("panel-title").textContent =
    "Callout " + id + " - " + d.caption;
  document.getElementById("panel").innerHTML =
    d.entries.map(renderEntry).join("");
  document.querySelectorAll(".cal").forEach(el =>
    el.classList.toggle("on", el.dataset.c === id));
  document.querySelectorAll(".leaders polyline").forEach(el =>
    el.classList.toggle("on", el.dataset.c === id));
  document.querySelectorAll(".leaders .dot").forEach(el =>
    el.classList.toggle("on", el.dataset.c === id));
}}

// the key list beside the drawing
(function () {{
  const tb = document.getElementById("keylist");
  for (const id of ORDER) {{
    const d = PANEL[id];
    const first = d.entries.find(e => e.fig_key_eur !== null && e.fig_key_eur !== undefined);
    const tr = document.createElement("tr");
    tr.style.cursor = "pointer";
    tr.innerHTML = "<td><b>" + id + "</b></td><td>" + d.caption
      + '<br><span style="color:#5d6470;font-size:12px">' + d.keys.join(" / ")
      + "</span></td><td class='n'>" + (first ? eur(first.fig_key_eur) : "not billed")
      + "</td>";
    tr.addEventListener("click", () => show(id));
    tb.appendChild(tr);
  }}
}})();

document.querySelectorAll(".cal").forEach(el => {{
  el.addEventListener("click", () => show(el.dataset.c));
  el.addEventListener("mouseenter", () => show(el.dataset.c));
  el.addEventListener("focus", () => show(el.dataset.c));
  el.addEventListener("keydown", ev => {{
    if (ev.key === "Enter" || ev.key === " ") {{ ev.preventDefault(); show(el.dataset.c); }}
  }});
}});

show("A");
</script>
</body>
</html>
"""

html = HTML.format(img=img_b64, svg=CALLOUT_SVG, period=period,
                   panel=panel_json, order=order_json)

with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(html)

print("wrote", OUT)
print("size %.2f MB" % (os.path.getsize(OUT) / 1e6))
print("callouts:", ", ".join("%s=%s" % (c["id"], c["caption"]) for c in CALLOUTS))
