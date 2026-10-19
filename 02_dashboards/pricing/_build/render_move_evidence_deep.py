# -*- coding: utf-8 -*-
"""Render ISZE_Price_Move_Evidence_by_AIM_2026-10-15.html (deep version, clickable drill-down). Self-contained, no CDN."""
import json, html
from pathlib import Path

R = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
B = R / "02_dashboards/pricing/_build"
J = json.loads((B / "move_evidence_deep.json").read_text(encoding="utf-8"))
K = json.loads((B / "move_evidence_by_aim.json").read_text(encoding="utf-8"))   # tender rows + step by PMS category
OUT = R / "02_dashboards/pricing/ISZE_Price_Move_Evidence_by_AIM_2026-10-15.html"
e = html.escape


def eur(x): return "EUR " + f"{x:,.0f}"
def m(x): return f"EUR {x/1e6:.2f}M"
def pc(x, d=1): return f"{x*100:.{d}f}%"
def tip(txt, t): return f'<span class="tip" tabindex="0" data-tip="{e(t)}">{txt}</span>'


base = J["base_total"]; T = J["total"]
L = [r for r in J["l1"] if r["billed"] >= 100000]
rest = [r for r in J["l1"] if r["billed"] < 100000]
brakes = next(r for r in L if r["name"] == "Brakes")
extra_total = sum(r["billed"] * r["step"] for r in J["l1"] if r["step"] is not None)
wstep = extra_total / base
nothing = T["alt_nothing"] / base
weak = (T["alt_weak_edge"] + T["alt_rival_number"]) / base
rp = T["alt_rival_price"] / base
own = T["alt_own_line"] / base
gb = J["gen_bands"]; gbe = J["gen_bands_eur"]
rob = J["robust"]; ra = J["react_all"]
tr = J["tender_results"]
tn, ta = K["tender_total_now"], K["tender_total_after"]

# ---- parsed result notices (winner and contract value, read from the source documents)
import csv as _csv
from collections import Counter as _C
_rows = list(_csv.DictReader(open(R / "01_data/90_INBOX/tender_result_notices_20261015/tender_result_notices_parsed.csv", encoding="utf-8-sig")))
_win = [r for r in _rows if r["result_code"] == "selec-w" and r["winner"]]
_nowin = [r for r in _rows if r["result_code"] == "clos-nw"]
_val = {c: [float(r["value"].split("; ")[0]) for r in _win if r["value"] and r["currency"] == c] for c in ("EUR", "NOK")}
_kind = _C(r["kind"] for r in _rows)
_top = _C(r["winner"] for r in _win).most_common(8)
_rep = [r for r in _rows if r["kind"] == "repair or service" and r["result_code"]]
_tr = sorted(int(r["tenders_received"]) for r in _rows if r["tenders_received"])
_med_tr = (_tr[len(_tr)//2-1] + _tr[len(_tr)//2]) / 2 if len(_tr) % 2 == 0 else _tr[len(_tr)//2]
res_n = len({r["notice_id"] for r in _rows}); res_win_n = len({r["notice_id"] for r in _win})
def _med(x): x = sorted(x); return x[len(x)//2] if len(x) % 2 else (x[len(x)//2-1] + x[len(x)//2]) / 2
top_rows = "".join(f'<tr><td>{e(n)}</td><td class="n">{c}</td></tr>' for n, c in _top)
rep_rows = "".join(f'<tr><td>{e(r["buyer"])}</td><td>{e((r["lot_title"] or r["title"])[:60])}</td><td>{e(r["winner"][:40]) or "no winner stated"}</td><td class="n">{(eur(float(r["value"])) if r["value"] and r["currency"]=="EUR" else "")}</td></tr>' for r in _rep)


def share_rp(r): return r["alt_rival_price"] / r["billed"]


# ---------------------------------------------------------------- chart 1: bubbles (clickable)
W, H, ML, MR, MT, MB = 900, 430, 62, 20, 20, 52
xmin, xmax, ymax, ymin = 0.02, 0.085, 0.70, -0.07
def X(v): return ML + (v - xmin) / (xmax - xmin) * (W - ML - MR)
def Y(v): return H - MB - (v - ymin) / (ymax - ymin) * (H - MT - MB)
bmax = max(r["billed"] for r in L)
s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Price move against rival price coverage per AIM category; each bubble opens its detail">']
for t in [0, .1, .2, .3, .4, .5, .6, .7]:
    s.append(f'<line x1="{ML}" x2="{W-MR}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="gl"/><text x="{ML-8}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{int(round(t*100))}%</text>')
for t in [.02, .03, .04, .05, .06, .07, .08]:
    s.append(f'<text x="{X(t):.1f}" y="{H-MB+18}" class="ax" text-anchor="middle">+{int(round(t*100))}%</text>')
s.append(f'<text x="{(ML+W-MR)/2}" y="{H-8}" class="axt" text-anchor="middle">Base price step for the category (weighted by what we billed)</text>')
s.append(f'<text transform="translate(16 {(MT+H-MB)/2}) rotate(-90)" class="axt" text-anchor="middle">Share of billed euros with a rival price seen</text>')
s.append(f'<rect x="{X(.06):.1f}" y="{Y(.25):.1f}" width="{X(xmax)-X(.06):.1f}" height="{Y(0)-Y(.25):.1f}" class="zone"/>')
s.append(f'<text x="{X(.0605):.1f}" y="{Y(.25)-6:.1f}" class="zt">Move above 6%, rival prices on under a quarter of billing</text>')
NAME = {"Intake Exhaust Emission": "Intake, exhaust", "Maintenance Service": "Service items"}
OFF = {"Brakes": (-1, 0, 4), "Cabin Interior": (1, 0, 4), "Maintenance Service": (0, -1, 0), "Clutch": (0, -1, 0),
       "Intake Exhaust Emission": (1, 0, -4), "Accident & Body": (1, 0, 8), "Electrical": (0, 0, 0), "Fuel System": (-1, 0, 4), "Steering": (1, 0, 4)}
for r in L:
    cx, cy = X(r["step"]), Y(share_rp(r)); rad = 6 + 26 * (r["billed"] / bmax) ** .5
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" class="bub" data-l1="{e(r["name"])}" tabindex="0" role="button" aria-label="{e(r["name"])}: open detail"><title>{e(r["name"])}: billed {m(r["billed"])}, step {pc(r["step"],2)}, rival price on {pc(share_rp(r),0)} of billed euros. Click for the levels and parts underneath.</title></circle>')
    o = OFF.get(r["name"])
    if o is None: continue
    if r["name"] == "Electrical":
        s.append(f'<text x="{cx-6:.1f}" y="{cy+rad+14:.1f}" class="bl" text-anchor="middle">Electrical</text>'); continue
    dx = o[0] * (rad + 6); dy = (o[1] * (rad + 5)) + o[2]
    a = "start" if o[0] > 0 else ("end" if o[0] < 0 else "middle")
    s.append(f'<text x="{cx+dx:.1f}" y="{cy+dy:.1f}" class="bl" text-anchor="{a}">{e(NAME.get(r["name"], r["name"]))}</text>')
s.append("</svg>")
chart1 = "\n".join(s)

# ---------------------------------------------------------------- chart 2: what we know per category (stacked)
top = L[:14]
SW, RH = 900, 26
SH = 40 + len(top) * RH + 30
x0, x1 = 190, 700
cols = [("alt_rival_price", "Rival price seen", "#15233c"), ("alt_rival_number", None, None), ("alt_weak_edge", "Rival number known, no price", "#6f8fb5"),
        ("alt_own_line", "Our own value line only", "#8aa596"), ("alt_nothing", "Nothing known", "#d8d1c2")]
t2 = [f'<svg viewBox="0 0 {SW} {SH}" role="img" aria-label="For each AIM category, how much of the billing has a known alternative">']
lx = x0
for key, lab, col in [("a", "Rival price seen", "#15233c"), ("b", "Rival number known, no price", "#6f8fb5"), ("c", "Our own value line only", "#8aa596"), ("d", "Nothing known", "#d8d1c2")]:
    t2.append(f'<rect x="{lx}" y="8" width="12" height="12" fill="{col}"/><text x="{lx+17}" y="19" class="ax">{lab}</text>'); lx += 24 + len(lab) * 6.3
for i, r in enumerate(top):
    y = 40 + i * RH; b = r["billed"]
    parts_ = [(r["alt_rival_price"], "#15233c"), (r["alt_rival_number"] + r["alt_weak_edge"], "#6f8fb5"), (r["alt_own_line"], "#8aa596"), (r["alt_nothing"], "#d8d1c2")]
    t2.append(f'<text x="{x0-8}" y="{y+15}" class="ax" text-anchor="end" style="fill:var(--ink)">{e(NAME.get(r["name"], r["name"]))}</text>')
    cx_ = x0
    for v, col in parts_:
        w = (v / b) * (x1 - x0)
        if w > 0: t2.append(f'<rect x="{cx_:.1f}" y="{y}" width="{w:.1f}" height="{RH-6}" fill="{col}"><title>{e(r["name"])}: {pc(v/b,0)} of billed euros</title></rect>')
        cx_ += w
    t2.append(f'<text x="{x1+8}" y="{y+15}" class="ax">{m(b)} · {pc(r["alt_nothing"]/b,0)} unknown</text>')
t2.append("</svg>")
chart2 = "\n".join(t2)

# ---------------------------------------------------------------- tables
rows = []
for r in sorted(L, key=lambda r: -(r["billed"] * r["step"])):
    ex = r["billed"] * r["step"]
    rows.append(f'<tr class="clk" data-l1="{e(r["name"])}" tabindex="0"><td>{e(r["name"])}</td><td class="n">{m(r["billed"])}</td><td class="n">{pc(r["step"],2)}</td><td class="n">{eur(ex)}</td>'
                f'<td class="n">{r["n_rival_price"]}</td><td class="n">{pc(share_rp(r),0)}</td><td class="n">{pc(r["alt_nothing"]/r["billed"],0)}</td></tr>')
rb = sum(r["billed"] for r in rest)
rows.append(f'<tr class="dim"><td>{len(rest)} small categories (each under EUR 0.1M)</td><td class="n">{m(rb)}</td><td class="n">n/a</td><td class="n">{eur(sum(r["billed"]*r["step"] for r in rest))}</td><td class="n">{sum(r["n_rival_price"] for r in rest)}</td><td class="n">{pc(sum(r["alt_rival_price"] for r in rest)/rb,0)}</td><td class="n">{pc(sum(r["alt_nothing"] for r in rest)/rb,0)}</td></tr>')

grows = []
for r in sorted(L, key=lambda r: -r["gen_billed"]):
    if r["gen_billed"] <= 0: continue
    grows.append(f'<tr><td>{e(r["name"])}</td><td class="n">{r["gen_n"]}</td><td class="n">{m(r["gen_billed"])}</td><td class="n">{pc(r["gen_billed"]/r["billed"],0)}</td><td class="n">{r["genb_n"]}</td><td class="n">{eur(r["genb_billed"])}</td></tr>')

def lo_hi(v): return f'{v["beta"]-1.96*v["se"]:+.2f} to {v["beta"]+1.96*v["se"]:+.2f}'
reacts = [("Weighted by euros (main cut)", ra), ("Every part counts the same", rob["unweighted"]), ("2024 against 2023 only", rob["only_2024"]),
          ("2025 against 2024 only", rob["only_2025"]), ("Price moves under 15% only", rob["small_moves_only"])]
rrows = "".join(f'<tr><td>{n}</td><td class="n">{v["n"]:,}</td><td class="n">{v["beta"]:+.2f}</td><td class="n">{lo_hi(v)}</td></tr>' for n, v in reacts)

byd = {}
for r in K["tender_rows"]:
    d = byd.setdefault(r["dist"], {"opp": set(), "now": 0.0, "after": 0.0}); d["opp"].add(r["opp"]); d["now"] += r["now"]; d["after"] += r["after"]
trows = "".join(f'<tr><td>{e(k.title())}</td><td class="n">{len(v["opp"])}</td><td class="n">{eur(v["now"])}</td><td class="n">{eur(v["after"])}</td><td class="n">+{eur(v["after"]-v["now"])}</td></tr>' for k, v in sorted(byd.items(), key=lambda kv: -kv[1]["now"]))

drill = {r["name"]: {k: r[k] for k in ("billed", "step", "parts", "alt_rival_price", "alt_rival_number", "alt_weak_edge", "alt_own_line", "alt_nothing", "gen_n", "gen_billed", "genb_n", "genb_billed", "l2", "parts_list", "react")} for r in J["l1"] if r["billed"] >= 100000}
payload = json.dumps(drill, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

CSS = """
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#d9d3c7;--mute:#5b6577;--card:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#10151f;--ink:#e8e4da;--line:#2b3548;--mute:#9aa5b8;--card:#1a2233}}
*{box-sizing:border-box} html,body{overflow-x:hidden}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:28px 16px 44px}
h1{font:700 28px/1.2 Georgia,serif;color:var(--navy);margin:0 0 6px} h2{font:700 20px/1.3 Georgia,serif;color:var(--navy);margin:36px 0 6px} h3{font:700 16px Georgia,serif;color:var(--navy);margin:16px 0 4px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) h1,:root:not([data-theme="light"]) h2,:root:not([data-theme="light"]) h3{color:#f7f4ee}}
.sub{color:var(--mute);margin:0 0 16px} .q{color:var(--mute);margin:0 0 10px;font-style:italic}
.verdict{background:var(--navy);color:#f7f4ee;border-left:6px solid var(--terra);padding:16px 18px;border-radius:4px;font-size:16px} .verdict b{color:#fff} .verdict p{margin:0 0 8px} .verdict p:last-child{margin:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0}
.k{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--terra);padding:10px 12px;border-radius:3px} .k b{display:block;font:700 22px Georgia,serif;color:var(--navy)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .k b{color:#f7f4ee}}
.k span{font-size:13px;color:var(--mute)}
.dia{overflow-x:auto} svg{width:100%;min-width:640px;height:auto;display:block}
.gl{stroke:var(--line);stroke-width:1} .ax{font:12px system-ui;fill:var(--mute)} .axt{font:600 12px system-ui;fill:var(--mute)}
.bub{fill:#15233c;fill-opacity:.55;stroke:#15233c;stroke-width:1.5;cursor:pointer;transition:fill-opacity .12s} .bub:hover,.bub:focus{fill-opacity:.8;outline:none} .bub.sel{stroke:#c0552d;stroke-width:4;fill-opacity:.85}
.bl{font:600 12px system-ui;fill:var(--ink);paint-order:stroke;stroke:var(--paper);stroke-width:3px;pointer-events:none}
.zone{fill:#c0552d;fill-opacity:.09;stroke:#c0552d;stroke-dasharray:6 4} .zt{font:600 12px system-ui;fill:#c0552d}
table{width:100%;border-collapse:collapse;margin:8px 0;background:var(--card)} th{background:var(--navy);color:#f7f4ee;text-align:left;padding:8px 10px;font-size:13px}
td{padding:8px 10px;border-bottom:1px solid var(--line);font-size:14px;vertical-align:top} td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} tr.dim td{color:var(--mute)}
tr.clk{cursor:pointer} tr.clk:hover td,tr.clk:focus td{background:rgba(192,85,45,.10);outline:none}
.tw{overflow-x:auto} .tw table{min-width:560px}
.tip{position:relative;border-bottom:1px dotted var(--terra);cursor:help}
.tip::after{content:attr(data-tip);position:absolute;left:0;top:130%;width:min(300px,70vw);background:#15233c;color:#f7f4ee;border-top:3px solid #c0552d;padding:8px 10px;border-radius:3px;font:400 12px/1.4 system-ui;opacity:0;pointer-events:none;transition:opacity .12s;z-index:60}
.tip:hover::after,.tip:focus::after{opacity:1}
.note{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--terra);padding:10px 14px;margin:10px 0;font-size:14px}
#drill{margin-top:14px;border:2px solid var(--navy);border-radius:4px;background:var(--card);display:none} #drill.on{display:block}
#drill .hd{background:var(--navy);color:#f7f4ee;padding:10px 14px;display:flex;justify-content:space-between;gap:10px;align-items:flex-start;flex-wrap:wrap}
#drill .hd b{font:700 18px Georgia,serif} #drill .hd button{background:transparent;border:1px solid #f7f4ee;color:#f7f4ee;border-radius:3px;padding:2px 10px;cursor:pointer}
#drill .bd{padding:6px 14px 14px} #drill details{border-bottom:1px solid var(--line)} #drill summary{cursor:pointer;padding:8px 0;display:grid;grid-template-columns:1fr 90px 70px 90px 90px;gap:8px;font-size:14px}
#drill summary span.n{text-align:right;font-variant-numeric:tabular-nums} #drill .l3 td{font-size:13px;color:var(--mute)}
#drill select{padding:4px 6px;font:inherit;margin-left:6px} #drill a{color:var(--terra)}
.foot{color:var(--mute);font-size:12px;margin-top:28px;border-top:1px solid var(--line);padding-top:10px} .foot code{font-size:11px;word-break:break-all}
#drill .bd{overflow-x:auto} #drill .gh{display:grid;grid-template-columns:1fr 90px 70px 90px 90px;gap:8px;font-size:12px;color:var(--mute);padding:4px 0}
@media (max-width:640px){#drill summary,#drill .gh{grid-template-columns:1fr 70px 60px}#drill summary span:nth-child(n+4),#drill .gh span:nth-child(n+4){display:none}#drill .l3 td:nth-child(n+4){display:none}#drill .l3{min-width:0}}
"""

JS = """
const D=JSON.parse(document.getElementById('deep').textContent);
const f0=x=>Math.round(x).toLocaleString('en-GB'), pc=(x,d=0)=>(x*100).toFixed(d)+'%', mil=x=>'EUR '+(x/1e6).toFixed(2)+'M';
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ALT={rival_price:'Rival price seen',rival_number:'Rival number, no price',weak_edge:'Weak rival number',own_line:'Own value line only',nothing:'Nothing known'};
let cur=null;
function open(name){
  const d=D[name]; if(!d) return; cur=name;
  document.querySelectorAll('.bub').forEach(b=>b.classList.toggle('sel',b.dataset.l1===name));
  const el=document.getElementById('drill'); el.classList.add('on');
  const rp=d.alt_rival_price/d.billed, nn=d.alt_nothing/d.billed;
  let h='<div class="hd"><div><b>'+esc(name)+'</b><div style="font-size:13px;opacity:.85">'+mil(d.billed)+' billed, base price step '+pc(d.step,2)+', rival price on '+pc(rp)+' of billed euros, nothing known on '+pc(nn)+'. Genuine part seen outside our network on '+d.gen_n+' parts ('+mil(d.gen_billed)+'), of which '+d.genb_n+' below our own list.</div></div><button type="button" id="cl">Close</button></div><div class="bd">';
  h+='<h3>Second and third AIM level (click a row to open its third level)</h3><div class="gh"><span>Level</span><span style="text-align:right">Billed</span><span style="text-align:right">Step</span><span style="text-align:right">Rival price</span><span style="text-align:right">Nothing known</span></div>';
  d.l2.filter(x=>x.billed>=1000).forEach((x,i)=>{
    h+='<details><summary><span>'+esc(x.name)+'</span><span class="n">'+mil(x.billed)+'</span><span class="n">'+pc(x.step,1)+'</span><span class="n">'+pc(x.alt_rival_price/x.billed)+'</span><span class="n">'+pc(x.alt_nothing/x.billed)+'</span></summary><table class="l3"><tbody>';
    x.l3.filter(y=>y.billed>=500).forEach(y=>{h+='<tr><td>'+esc(y.name)+'</td><td class="n">'+mil(y.billed)+'</td><td class="n">'+pc(y.step,1)+'</td><td class="n">'+pc(y.alt_rival_price/y.billed)+' rival</td><td class="n">'+pc(y.alt_nothing/y.billed)+' none</td></tr>'});
    h+='</tbody></table></details>';
  });
  h+='<h3>Parts <label style="font-weight:400;font-size:13px">level <select id="pf"><option value="">all</option>'+[...new Set(d.parts_list.map(p=>p.l2))].sort().map(v=>'<option>'+esc(v)+'</option>').join('')+'</select></label></h3>';
  h+='<p class="q" style="margin:0 0 6px">The 60 biggest parts by billed euros, plus every part with a rival price or a genuine price outside our network below our own list. Part numbers open the Parts Price Intelligence page.</p><div class="tw"><table><thead><tr><th>Part</th><th>Description</th><th class="n">Billed</th><th class="n">Step</th><th class="n">Our list</th><th class="n">Rival price seen</th><th class="n">Genuine outside, lowest</th><th>Known alternative</th></tr></thead><tbody id="pb"></tbody></table></div></div>';
  el.innerHTML=h;
  document.getElementById('cl').onclick=()=>{el.classList.remove('on');document.querySelectorAll('.bub').forEach(b=>b.classList.remove('sel'))};
  const draw=()=>{const f=document.getElementById('pf').value;
    document.getElementById('pb').innerHTML=d.parts_list.filter(p=>!f||p.l2===f).map(p=>'<tr><td><a href="ISZE_Parts_Price_Intelligence.html#pn='+esc(p.pn)+'" target="_blank" rel="noopener">'+esc(p.pn)+'</a></td><td>'+esc(p.desc)+'<div style="font-size:12px;color:var(--mute)">'+esc(p.l3)+'</div></td><td class="n">'+f0(p.billed)+'</td><td class="n">'+pc(p.step,1)+'</td><td class="n">'+(p.our_list==null?'':p.our_list.toFixed(2))+'</td><td class="n">'+(p.riv_min==null?'':(p.riv_min===p.riv_max?p.riv_min.toFixed(2):p.riv_min.toFixed(2)+' to '+p.riv_max.toFixed(2)))+'</td><td class="n">'+(p.gen_min==null?'':p.gen_min.toFixed(2))+'</td><td>'+ALT[p.alt]+'</td></tr>').join('')};
  document.getElementById('pf').onchange=draw; draw();
  el.scrollIntoView({behavior:'smooth',block:'start'});
}
const hm=decodeURIComponent((location.hash.match(/^#open=(.+)$/)||[])[1]||''); if(hm&&D[hm]){open(hm);document.querySelector('#drill details')&&(document.querySelector('#drill details').open=true)}
document.querySelectorAll('.bub,tr.clk').forEach(n=>{n.addEventListener('click',()=>open(n.dataset.l1));n.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();open(n.dataset.l1)}})});
"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Price move evidence by AIM category</title><style>{CSS}</style></head><body><div class="wrap">
<h1>Which price moves have evidence behind them</h1>
<p class="sub">Internal read, 15 October 2026. The 22 markets in the price revision simulator v6 (no MIDI). Base: what we billed, July 2025 to June 2026, {m(base)}.</p>

<div class="verdict">
<p><b>Most of the price move has no rival evidence behind it, and our own history cannot fill the gap.</b> Rival prices exist for {pc(rp,0)} of billed euros. For {pc(nothing,0)} we know of no alternative at all, and that does not prove those parts are captive; it may only mean nobody has looked.</p>
<p><b>Genuine parts sold outside our network show no sign of broad undercutting.</b> The same genuine part is priced outside our network on {T["gen_n"]:,} of our parts ({m(T["gen_billed"])}, {pc(T["gen_billed"]/base,0)} of billing). On {gb["above_ref"]:,} of them ({m(gbe["above_ref"])}) it costs more than the price a dealer would charge. Only {gb["below_list"]} parts ({eur(gbe["below_list"])}) sell below our own list.</p>
<p><b>Volume reaction cannot be measured from our own price changes.</b> Our list moved by more than 5% on only {pc(J["spread"]["share_moved_over_5pct"],0)} of parts in 2024 and 2025, and the estimate changes sign depending on how it is cut. The simulator's assumption of -0.16 stays an assumption.</p>
<p><b>Brakes is still the place to check first:</b> largest step of the big categories (+{brakes["step"]*100:.1f}%), rival prices on {pc(share_rp(brakes),0)} of billing.</p>
</div>

<div class="kpis">
<div class="k"><b>{pc(wstep,2)}</b><span>{tip("weighted base price step on this base","Billed euros times each part's base price step, summed, divided by total billed. The official index of 5.9616% weights by quantity at the prior base price, so the two differ by 0.04 points.")}</span></div>
<div class="k"><b>{pc(rp,0)}</b><span>{tip("of billed euros have a rival price seen","Billed euros of parts that carry an aftermarket price for the same part (exact or cross-referenced), divided by total billed.")}</span></div>
<div class="k"><b>{pc(nothing,0)}</b><span>{tip("of billed euros: no known alternative","Parts with no rival price, no rival number, no weak cross-reference and no own value line. This is unknown, not proven captive.")}</span></div>
<div class="k"><b>{pc(T["gen_billed"]/base,0)}</b><span>{tip("of billed euros: same genuine part priced outside our network","Parts where the ledger holds a genuine Isuzu price from a seller outside our network for the same part number, mostly an export retailer in Japan.")}</span></div>
</div>

<h2>1. Where the move meets rival prices</h2>
<p class="q">For each AIM category, is the price step backed by prices we have seen from rivals? Click a bubble or a table row for the levels and parts underneath.</p>
<div class="dia">{chart1}</div>
<div id="drill"></div>
<div class="note">Reading it: bubble size is billed euros. The shaded box is the weak spot, a big move with little rival evidence. Rival coverage says we have looked, not that the move is safe. The comparison basis for rival prices is still provisional, so this page counts coverage and does not claim a price gap.</div>
<div class="tw"><table><thead><tr><th>AIM category (click a row)</th><th class="n">Billed</th><th class="n">Base price step</th><th class="n">Extra euros a year</th><th class="n">Parts with a rival price</th><th class="n">Billed euros with a rival price</th><th class="n">Billed euros, nothing known</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>

<h2>2. What do we know about alternatives?</h2>
<p class="q">Per category: how much of the billing has a rival price, a rival number without a price, only our own value line, or nothing.</p>
<div class="dia">{chart2}</div>
<div class="note">The dark segment is what the evidence covers. The pale segment is the unknown. Where it dominates (body, electrical, engine, steering) we cannot tell a captive part, where a move is safe, from a contested part nobody has searched. Searching those categories is what separates the two. A rival number with no price still tells us where to look next; there are {T["n_weak_edge"]+T["n_rival_number"]} such parts, {m(T["alt_weak_edge"]+T["alt_rival_number"])} billed.</div>

<h2>3. Genuine parts sold outside our network</h2>
<p class="q">Is the same genuine part cheaper elsewhere than what we charge?</p>
<div class="tw"><table><thead><tr><th>Where the lowest outside price sits</th><th class="n">Parts</th><th class="n">Billed euros</th></tr></thead><tbody>
<tr><td>Below our own list price to the distributor</td><td class="n">{gb["below_list"]}</td><td class="n">{eur(gbe["below_list"])}</td></tr>
<tr><td>Above our list, below the price a dealer would charge</td><td class="n">{gb["list_to_ref"]}</td><td class="n">{eur(gbe["list_to_ref"])}</td></tr>
<tr><td>Above the price a dealer would charge</td><td class="n">{gb["above_ref"]}</td><td class="n">{eur(gbe["above_ref"])}</td></tr>
</tbody></table></div>
<div class="note">The median outside price is {J["gen_median_ratio"]:.1f} times our list. The comparison is crude: most of these prices come from an export retailer in Japan that charges consumers, shipping is not included, and tax status is unknown on most rows. Read it as "no sign of broad undercutting by the same genuine part", not as proof of headroom. The price a dealer would charge is our list, times 1.40 to the dealer, times 1.275 to the customer.</div>
<div class="tw"><table><thead><tr><th>AIM category</th><th class="n">Parts</th><th class="n">Billed euros</th><th class="n">Share of category</th><th class="n">Below our list: parts</th><th class="n">Below our list: euros</th></tr></thead><tbody>{"".join(grows)}</tbody></table></div>

<h2>4. How did volume react to our own price changes?</h2>
<p class="q">Using our 2023 to 2025 list prices and billing, per part, year on year. Reaction is the percent change in volume for a 1% price change.</p>
<div class="tw"><table><thead><tr><th>Way of cutting it</th><th class="n">Part-years</th><th class="n">Reaction</th><th class="n">95% range</th></tr></thead><tbody>{rrows}
<tr class="dim"><td>The simulator's central assumption (four markets, April 2026)</td><td class="n"></td><td class="n">-0.16</td><td class="n">not stated</td></tr></tbody></table></div>
<div class="note"><b>Inconclusive.</b> Every cut has a range that includes zero except one, and that one has the opposite sign of the main cut. The reason is the data, not the method: only {pc(J["spread"]["share_moved_over_5pct"],0)} of part-years saw a list move over 5% ({pc(J["spread"]["weighted_share_over_5pct"],0)} of the euros), so there is almost no variation to learn from, and volumes are noisy. Distributors also buy ahead of announced increases, which would push the estimate downward. The cleaner test is the sales-to-dealer files for IUK, ITUK, Ireland, UTI and Greece around the April 2026 increase. Per category the ranges are far wider still (for example brakes -3.2, range -7.5 to +1.1), so no category figure should be quoted.</div>

<h2>5. Tenders at the revised list, and tender results</h2>
<div class="tw"><table><thead><tr><th>Distributor</th><th class="n">Tenders</th><th class="n">Per year, today's price</th><th class="n">Per year, revised list</th><th class="n">Change</th></tr></thead><tbody>{trows}
<tr><td><b>Total</b></td><td class="n"><b>{K["tender_opps"]}</b></td><td class="n"><b>{eur(tn)}</b></td><td class="n"><b>{eur(ta)}</b></td><td class="n"><b>+{eur(ta-tn)}</b></td></tr></tbody></table></div>
<div class="note"><b>Demand.</b> {K["tender_opps"]} of 734 tenders carry both a parts demand and a matched distributor: {eur(tn)} a year, {eur(ta-tn)} more at the revised list. Too small to move a pricing decision.<br>
<b>Outcomes.</b> Our own outcome store is empty (0 of 734), because it fills only when distributors answer the weekly tender digest. The public result notices are a separate source, covered in the next section.</div>

<h3>What the {res_n} public result notices say (Germany 48, Norway 15)</h3>
<p class="q">Winner and contract value read from each original notice document, not from the feed summary.</p>
<div class="kpis">
<div class="k"><b>{len(_win)} lots</b><span>{tip(f"won, in {res_win_n} notices", "Lots with a stated winner (result code: winner selected). Every winner name and amount was checked against its own source file.")}</span></div>
<div class="k"><b>{len(_nowin)} lots</b><span>{tip("closed with no winner", "Lots the buyer closed without selecting a tender. These are cancelled or unsuccessful procurements.")}</span></div>
<div class="k"><b>0</b><span>{tip("mention Isuzu or D-Max","Searched notice title, lot title and winner for Isuzu and D-Max.")}</span></div>
<div class="k"><b>{_med_tr:.1f}</b><span>{tip("median tenders received per lot","Number of tenders the buyer reports receiving, over the lots that state it. Low numbers mean thin competition.")}</span></div>
</div>
<div class="note"><b>Value.</b> {len(_val["EUR"])} German lots state a contract value: EUR {sum(_val["EUR"])/1e6:.2f}M in total, median {eur(_med(_val["EUR"]))} per lot. {len(_val["NOK"])} Norwegian lots state one: NOK {sum(_val["NOK"])/1e6:.1f}M in total, median NOK {_med(_val["NOK"])/1e6:.1f}M per lot. The two currencies are not added. Five values are a placeholder of 1 in the source and are left blank.<br>
<b>What they are.</b> {_kind["vehicle or equipment supply"]} of {len(_rows)} lot rows are vehicle or equipment supply, {_kind["repair or service"]} are repair or service, {_kind["other"]} other. The winners are truck makers, body builders and dealers, not parts sellers. So these notices show who wins fleets in your markets and at what contract value. They carry no parts prices, so they do not answer "what price wins" for parts.</div>
<div class="tw"><table><thead><tr><th>Most frequent winner</th><th class="n">Lots won</th></tr></thead><tbody>{top_rows}</tbody></table></div>
<div class="tw"><table><thead><tr><th>Repair and service lots (the only ones near parts)</th><th>Lot</th><th>Winner</th><th class="n">Value</th></tr></thead><tbody>{rep_rows}</tbody></table></div>

<h2>What this says for the price decision</h2>
<div class="note"><b>1.</b> Check brakes first: biggest step among the big categories, and the only large one with real rival coverage. Brake pads alone step +10.1%.<br>
<b>2.</b> Body, electrical, intake and exhaust, steering and lighting carry {m(sum(r["billed"] for r in L if r["name"] in ("Accident & Body","Electrical","Intake Exhaust Emission","Steering","Lighting")))} of billing, and rival prices cover {pc(sum(r["alt_rival_price"] for r in L if r["name"] in ("Accident & Body","Electrical","Intake Exhaust Emission","Steering","Lighting"))/sum(r["billed"] for r in L if r["name"] in ("Accident & Body","Electrical","Intake Exhaust Emission","Steering","Lighting")),0)} of it. Searching them for a rival, or confirming none exists, is the data job that pays most.<br>
<b>3.</b> The genuine price outside our network does not argue for holding back on the {m(gbe["above_ref"])} of parts where it sits above the dealer price, with the caveats above. It says nothing about the aftermarket.<br>
<b>4.</b> Volume reaction stays an assumption until the sales-to-dealer files are used. Tender results are now readable, but the public result notices cover vehicle supply and carry no parts prices, so they tell us who wins fleets, not what a winning parts price is.</div>

<p class="foot">Sources and method. Billed base and base price step per part: <code>02_dashboards/pricing/_build/price_tool_html_v6_2026-10-15/payload6.json</code> (ties to the simulator base, EUR 32,595,852.63, difference 0.00). Prices seen: <code>01_data/00_derived/price_observations.parquet</code>, same-part matches only. Cross-reference numbers: <code>04_tools/aftermarket_intelligence/state/crossref_graded.csv</code>; own value line: <code>01_data/00_derived/genuine_bvp_crossref.parquet</code>. Our list: <code>pricing_pr00_ie40.parquet</code>. Reaction: <code>sales_fact.parquet</code> with the list vintages <code>pricing_pr00_ie40_2023/2024/2025.parquet</code>, categories from <code>AIM_Master_PN_Categories_Figkey_release_2026-10-15.csv</code>; a list vintage dated year Y matches billing in year Y (median billed price over list 1.00). Tenders: <code>01_data/14_dashboards/tender_data.json</code> (12 Oct 2026). Result notices: the 63 original notice documents saved in <code>01_data/90_INBOX/tender_result_notices_20261015/raw/</code> and read into <code>tender_result_notices_parsed.csv</code> in the same folder by <code>fetch_result_notices.py</code> and <code>parse_result_notices.py</code>; the count of winner lots and every winner name and amount were re-checked against the source files. Built by <code>build_move_evidence_deep.py</code> and <code>render_move_evidence_deep.py</code> in <code>02_dashboards/pricing/_build/</code>. Simulator v6 is untouched. AIM is our parts category tree; base price is the yen list price before exchange rate and discount.</p>
</div>
<script type="application/json" id="deep">{payload}</script>
<script>{JS}</script>
</body></html>"""
OUT.write_text(page, encoding="utf-8")
print("wrote", OUT, len(page))
