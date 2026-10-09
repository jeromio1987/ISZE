# -*- coding: utf-8 -*-
from pathlib import Path
import json, html as H

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
S = json.loads((ROOT/"01_data/90_INBOX/_imotors_bo_compare_20261006/IMOTORS_BO_HISTORY_ANALYSIS_20261006/summary.json").read_text(encoding="utf-8"))
out_dir = ROOT/"09_meetings/Imotors_Portugal_IDS_2026"
html_path = out_dir/"IMotors_BO_AIM_Deep_Dive_20261006.html"
cmd_path = out_dir/"OPEN_IMotors_BO_AIM_Deep_Dive.cmd"

def eur(x):
    try: v=float(x)
    except: return "€0"
    return f"€{v:,.0f}" if abs(v)>=100 else f"€{v:,.2f}"

def pct(x):
    if x is None: return "—"
    return f"{float(x)*100:.1f}%"

ov = S["overlap"]
months = [m for m in S["monthly"] if not m.get("empty")]
age = S["age_band_aug"]
mx_lines = max(m["lines"] for m in months) or 1
mx_eur = max(m["eur_open"] for m in months) or 1

def month_bars():
    parts=[]
    for m in months:
        w=100*m["lines"]/mx_lines
        we=100*m["eur_open"]/mx_eur
        kpi=m.get("kpi_bo_lines")
        match="same as KPI" if kpi==m["lines"] else f"KPI {kpi}"
        parts.append(
            f'<div class="bar-row"><div class="bar-lab">{m["ym"][5:]}/26<span class="sub">{match}</span></div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{w:.1f}%;background:#1a2b4a"></div></div>'
            f'<div class="bar-val">{m["lines"]} · {eur(m["eur_open"])}</div></div>'
            f'<div class="bar-row thin"><div class="bar-lab">euro</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{we:.1f}%;background:#c0552d"></div></div>'
            f'<div class="bar-val">{pct(m.get("competitive_share"))} comp</div></div>'
        )
    return "\n".join(parts)

def l1_bars(d, color="#1a2b4a"):
    rows=sorted(d.items(), key=lambda kv:-kv[1]["eur"])[:8]
    mx=max((v["eur"] for _,v in rows), default=1) or 1
    return "\n".join(
        f'<div class="bar-row"><div class="bar-lab">{H.escape(k)}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{100*v["eur"]/mx:.1f}%;background:{color}"></div></div>'
        f'<div class="bar-val">{eur(v["eur"])} · {v["lines"]}L</div></div>'
        for k,v in rows
    )

def table_rows(rows, cols):
    out=[]
    for i,r in enumerate(rows,1):
        tds=[f'<td class="num">{i}</td>']
        for c in cols:
            v=r.get(c,"")
            if c in ("their_eur","our_eur","eur"):
                tds.append(f'<td class="num">{eur(v)}</td>')
            elif c in ("their_qty","our_qty","their_age_max"):
                tds.append(f'<td class="num">{H.escape(str(v))}</td>')
            elif c=="pn":
                tds.append(f'<td class="mono">{H.escape(str(v))}</td>')
            elif c=="aim":
                tds.append(f'<td>{H.escape(str(r.get("aim_l1","")))}<div class="sub">{H.escape(str(r.get("aim_l2","")))}</div></td>')
            else:
                tds.append(f'<td>{H.escape(str(v))}</td>')
        out.append("<tr>"+"".join(tds)+"</tr>")
    return "\n".join(out)

age_rows=""
for b,l,e in zip(age["band"], age["lines"], age["eur"]):
    age_rows += f'<tr><td>{b}d</td><td class="num">{l}</td><td class="num">{eur(e)}</td></tr>\n'

persist_rows=""
for ym,v in S["persist_aug_vs_prior"].items():
    persist_rows += f'<tr><td>{ym}</td><td class="num">{v["pn_overlap_with_aug"]}</td><td class="num">{pct(v["share_of_aug_pns"])}</td></tr>\n'

doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>I-Motors back orders — historical deep dive 6 Oct 2026</title>
<style>
:root {{
  --ink:#1a2332; --muted:#5c6b7a; --paper:#f6f3ee; --card:#fff;
  --navy:#15233c; --terra:#c0552d; --line:#d9d2c5; --ok:#2f6b4f; --bad:#9b2c2c;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --sans:"Segoe UI",system-ui,sans-serif;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.55 var(--sans); }}
.wrap {{ max-width:1180px; margin:0 auto; padding:28px 22px 80px; }}
header.hero {{
  background:linear-gradient(145deg,#15233c 0%,#243b5c 55%,#3a2a22 100%);
  color:#f7f4ee; border-radius:18px; padding:34px; margin-bottom:28px;
  box-shadow:0 18px 40px rgba(21,35,60,.22);
}}
.kicker {{ letter-spacing:.12em; text-transform:uppercase; font-size:11px; opacity:.75; }}
h1 {{ font-family:var(--serif); font-weight:600; font-size:clamp(1.55rem,3vw,2.2rem); margin:10px 0 12px; line-height:1.15; }}
.lede {{ font-size:1.05rem; max-width:68ch; opacity:.92; }}
.meta {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }}
.chip {{ background:rgba(247,244,238,.1); border:1px solid rgba(247,244,238,.22); padding:6px 10px; border-radius:999px; font-size:12px; }}
.grid {{ display:grid; gap:16px; }}
.g4 {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
.g2 {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
@media (max-width:900px) {{ .g4,.g2 {{ grid-template-columns:1fr; }} }}
.kpi {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; }}
.kpi .lbl {{ font-size:11px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }}
.kpi .val {{ font-family:var(--serif); font-size:1.7rem; margin-top:4px; }}
.kpi .note {{ font-size:12px; color:var(--muted); margin-top:6px; }}
.kpi.warn {{ border-color:#e2c089; background:#fff9ef; }}
.kpi.bad {{ border-color:#e2b0b0; background:#fff5f5; }}
.kpi.ok {{ border-color:#b7d3c3; background:#f3faf6; }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:22px; margin:18px 0; }}
section h2 {{ font-family:var(--serif); font-size:1.4rem; margin:0 0 8px; color:var(--navy); }}
section h3 {{ font-size:1.02rem; margin:16px 0 8px; color:var(--navy); }}
.prose {{ max-width:75ch; }}
.prose p {{ margin:0 0 12px; }}
.callout {{ border-left:4px solid var(--terra); background:#faf6f2; padding:12px 14px; border-radius:0 10px 10px 0; margin:14px 0; }}
.callout.navy {{ border-left-color:var(--navy); background:#f3f6fa; }}
.callout.bad {{ border-left-color:var(--bad); background:#fff5f5; }}
.callout.ok {{ border-left-color:var(--ok); background:#f3faf6; }}
.bar-row {{ display:grid; grid-template-columns:110px 1fr 110px; gap:10px; align-items:center; margin:5px 0; }}
.bar-row.thin {{ opacity:.85; margin-top:-2px; margin-bottom:10px; }}
.bar-row.thin .bar-lab {{ font-size:11px; color:var(--muted); }}
@media (max-width:700px) {{ .bar-row {{ grid-template-columns:1fr; gap:2px; }} }}
.bar-lab {{ font-size:12.5px; }}
.bar-track {{ background:#ece7de; height:11px; border-radius:999px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:999px; }}
.bar-val {{ font-variant-numeric:tabular-nums; font-size:12px; text-align:right; color:var(--muted); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
th {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:#f7f4ee; background:var(--navy); }}
tbody tr:nth-child(even) {{ background:#faf8f4; }}
.num {{ font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }}
.mono {{ font-family:Consolas,monospace; font-size:12px; }}
.sub {{ font-size:11px; color:var(--muted); }}
.toc {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 0; }}
.toc a {{ color:var(--navy); text-decoration:none; background:#eef2f7; border:1px solid #d5deea; padding:6px 10px; border-radius:999px; font-size:12px; }}
.two-col {{ display:grid; grid-template-columns:1.15fr .85fr; gap:18px; }}
@media (max-width:900px) {{ .two-col {{ grid-template-columns:1fr; }} }}
ul.tight {{ margin:8px 0 0 18px; padding:0; }}
ul.tight li {{ margin:6px 0; }}
.footer {{ color:var(--muted); font-size:12px; margin-top:28px; }}
.tag {{ display:inline-block; font-size:11px; padding:2px 7px; border-radius:6px; background:#eef2f7; color:var(--navy); }}
.tag.bad {{ background:#f8e0e0; color:#7a2222; }}
.tag.ok {{ background:#dff0e6; color:#21553a; }}
</style>
</head>
<body>
<div class="wrap">
<header class="hero">
  <div class="kicker">I-Motors · Portugal · internal · rebuilt 6 Oct 2026</div>
  <h1>Their monthly back-order file is the KPI count — and August still holds €34k of lines older than 90 days</h1>
  <p class="lede">Nuno’s <em>Backordered lines 2026.xlsx</em> (29 Sep) is PN-level, month-end. Jan–Aug line counts match the KPI B/O row exactly. September’s KPI spike to 495 is real on the scorecard, but the Sep tab in this workbook is empty — so the Sep PN story is not in the file yet. Match to our open sales orders is therefore August vs 6 Oct, with an honest as-of gap.</p>
  <div class="meta">
    <span class="chip">Their Aug BO: 282 lines · {eur(ov['their_eur'])}</span>
    <span class="chip">Sep KPI B/O: 495 (tab empty in mail file)</span>
    <span class="chip">Our open 6 Oct: 906 lines · {eur(ov['our_eur'])}</span>
    <span class="chip">PN overlap Aug↔Oct: {ov['pn_both']} parts</span>
  </div>
</header>

<nav class="toc">
  <a href="#verdict">Verdict</a>
  <a href="#history">History</a>
  <a href="#age">Age &amp; euro</a>
  <a href="#aim">AIM Aug</a>
  <a href="#match">Match vs us</a>
  <a href="#lists">PN lists</a>
  <a href="#ask">Wednesday</a>
  <a href="#method">Method</a>
</nav>

<section id="verdict">
  <h2>1. Verdict</h2>
  <div class="prose">
    <p>I was wrong earlier: Nuno did send a back-order file. It is not a single snapshot — it is eight filled month-ends (Jan–Aug 2026). The KPI “B/O lines” number is simply the row count of that extract. So when fill rate was fine in August (85.4%) with 282 BO lines, the file confirms it. When September jumped to 495 on the KPI, we still lack the Sep PN tab in the 29 Sep mail.</p>
    <p>Inside the last filled month (31 Aug), the book is <strong>young in count</strong> (median age 6 days, 151 of 282 lines under 8 days) but <strong>old in euro</strong>: the 91+ day pocket is only 21 lines and holds {eur(33556.57)} — almost half of August’s open euro. That pocket is mostly accident / body hardware that is not on our 6 Oct open sales-order book.</p>
    <p>Against our open orders to sold-to 519 (6 Oct), only <strong>{ov['pn_both']} part numbers</strong> sit in both lists. Most of their August euro ({eur(ov['eur_only_them'])}) is not on our open book now; most of our open euro ({eur(ov['eur_only_us'])}) was not on their August BO. That is expected with a five-week gap plus September’s intake — it does <em>not</em> mean the files are useless. It means Wednesday needs the Sep/Oct BO tab before anyone claims a clean supply match for the 495.</p>
  </div>
  <div class="callout bad">
    <strong>Hard limit:</strong> Sep KPI = 495 lines, but sheet <span class="mono">BO 20260930</span> is empty in the file Nuno attached. Ask for the closed September extract (and October if ready) before arguing the spike PN-by-PN.
  </div>
</section>

<div class="grid g4" style="margin:18px 0">
  <div class="kpi"><div class="lbl">Their Aug BO €</div><div class="val">{eur(ov['their_eur'])}</div><div class="note">282 lines · 31 Aug extract</div></div>
  <div class="kpi warn"><div class="lbl">Sep KPI B/O lines</div><div class="val">495</div><div class="note">PN tab missing in mail file</div></div>
  <div class="kpi"><div class="lbl">Our open 6 Oct €</div><div class="val">{eur(ov['our_eur'])}</div><div class="note">906 lines · sold-to 519</div></div>
  <div class="kpi bad"><div class="lbl">91+ day € (Aug)</div><div class="val">{eur(33556)}</div><div class="note">21 lines · half the Aug euro</div></div>
</div>

<section id="history">
  <h2>2. History — their BO Jan–Aug (matches KPI)</h2>
  <p class="prose">Navy bars = open lines at month-end. Terracotta = euro scale. “comp” = share of that month’s open euro in Competitive parts (catalogue AIM).</p>
  <div class="bar-chart">{month_bars()}</div>
  <div class="two-col" style="margin-top:16px">
    <div class="prose">
      <h3>What the series says</h3>
      <ul class="tight">
        <li><strong>Feb peak</strong> — 550 lines / {eur(96668)} — worst fill month (76.1%).</li>
        <li><strong>May euro peak</strong> — {eur(114053)} on 487 lines — euro and lines do not move together.</li>
        <li><strong>Jul–Aug calm on count</strong> — 279 → 282 lines, fill back above 85% in Aug — then Sep KPI blows to 495.</li>
        <li><strong>Competitive share fell</strong> — from ~58% of euro in Feb to ~28% in Aug as accident / body euro stayed sticky.</li>
      </ul>
    </div>
    <div>
      <h3>KPI beside the file</h3>
      <table>
        <thead><tr><th>Month</th><th class="num">BO lines</th><th class="num">Fill</th><th class="num">MOS</th><th class="num">Sales→dlr €</th></tr></thead>
        <tbody>
          {''.join(f'<tr><td>{m["ym"]}</td><td class="num">{m["lines"]}</td><td class="num">{pct(m.get("kpi_fill"))}</td><td class="num">{m.get("kpi_mos")}</td><td class="num">{eur(m.get("kpi_std_eur") or 0)}</td></tr>' for m in months)}
          <tr><td>2026-09 <span class="tag bad">KPI only</span></td><td class="num">495</td><td class="num">81.0%</td><td class="num">2.49</td><td class="num">{eur(416806)}</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section id="age">
  <h2>3. August age — young lines, old money</h2>
  <div class="two-col">
    <div>
      <table>
        <thead><tr><th>Age band</th><th class="num">Lines</th><th class="num">EUR open</th></tr></thead>
        <tbody>{age_rows}</tbody>
      </table>
      <p class="sub" style="margin-top:8px">Median age 6 days · max 489 days (brake pad kit still open).</p>
    </div>
    <div class="prose">
      <div class="callout navy">
        Count looks healthy; euro does not. Clear the 91+ day body / shutter / fender cluster and the aged pad kit before you trust “BO is only 282.”
      </div>
      <h3>How sticky is August?</h3>
      <p>Share of August PNs that were already open in earlier month-ends:</p>
      <table>
        <thead><tr><th>Prior month</th><th class="num">PNs still in Aug</th><th class="num">of Aug PNs</th></tr></thead>
        <tbody>{persist_rows}</tbody>
      </table>
      <p class="sub">About a third of August PNs were already open in July — not a pure one-week pile.</p>
    </div>
  </div>
</section>

<section id="aim">
  <h2>4. AIM on their August BO</h2>
  <p class="prose">Catalogue families on the 31 Aug extract. Accident / body leads euro; Competitive is second — brakes and filters show up again in the overlap with us.</p>
  <div class="bar-chart">{l1_bars(S['aug_by_l1'])}</div>
  <h3>Level 2 money (Aug)</h3>
  <div class="bar-chart">{''.join(
    f'<div class="bar-row"><div class="bar-lab">{H.escape(r["l1"])} · {H.escape(r["l2"] or "—")}</div>'
    f'<div class="bar-track"><div class="bar-fill" style="width:{100*r["eur"]/max(x["eur"] for x in S["aug_by_l2"]):.1f}%;background:#c0552d"></div></div>'
    f'<div class="bar-val">{eur(r["eur"])}</div></div>'
    for r in S["aug_by_l2"][:10]
  )}</div>
</section>

<section id="match">
  <h2>5. Match — their 31 Aug BO vs our 6 Oct open orders</h2>
  <div class="callout">
    Different clocks. Their file = Astara back orders to supplier (proveedor 3006) at month-end. Ours = ISZE sales-document lines still open to sold-to 519. Use the overlap as a supply shortlist, not as a reconciliation.
  </div>
  <div class="grid g4">
    <div class="kpi ok"><div class="lbl">PN in both</div><div class="val">{ov['pn_both']}</div><div class="note">{eur(ov['eur_both_their'])} their / {eur(ov['eur_both_our'])} ours</div></div>
    <div class="kpi warn"><div class="lbl">Only on their Aug BO</div><div class="val">{ov['pn_only_them']}</div><div class="note">{eur(ov['eur_only_them'])} — cleared or never ordered to us?</div></div>
    <div class="kpi"><div class="lbl">Only on our Oct open</div><div class="val">{ov['pn_only_us']}</div><div class="note">{eur(ov['eur_only_us'])} — mostly Sep intake</div></div>
    <div class="kpi bad"><div class="lbl">As-of gap</div><div class="val">5 wks</div><div class="note">Aug 31 → Oct 6 + empty Sep tab</div></div>
  </div>
  <div class="prose" style="margin-top:14px">
    <p><strong>In both:</strong> filters, brake pads/rotors, windscreen glass, AC compressor — classic availability parts still open on both sides.</p>
    <p><strong>Only them (Aug):</strong> heavy accident body (shutter lid, sail panel, over fender) plus a 489-day pad kit and NOx sensors — either filled since August, local/other supply, or never raised as an ISZE sales order that is still open.</p>
    <p><strong>Only us (Oct):</strong> partial engine, steering unit, gear set, turbo, injectors — the September open book we already cut. That is the post-August stress, not the August cemetery.</p>
  </div>
</section>

<section id="lists">
  <h2>6. PN shortlists</h2>
  <h3>A — In both books (top by their Aug €)</h3>
  <div style="overflow:auto"><table>
    <thead><tr><th>#</th><th>PN</th><th>Part</th><th>AIM</th><th class="num">Their €</th><th class="num">Age</th><th class="num">Our €</th><th>SaTy</th></tr></thead>
    <tbody>{table_rows(S['top_both'][:20], ["pn","desc","aim","their_eur","their_age_max","our_eur","our_saty"])}</tbody>
  </table></div>

  <h3>B — Only on their August BO (top €) — ask why not on our open book</h3>
  <div style="overflow:auto"><table>
    <thead><tr><th>#</th><th>PN</th><th>Part</th><th>AIM</th><th class="num">Their €</th><th class="num">Age</th></tr></thead>
    <tbody>{table_rows(S['top_only_them'][:20], ["pn","desc","aim","their_eur","their_age_max"])}</tbody>
  </table></div>

  <h3>C — Only on our 6 Oct open orders (top €) — September stress</h3>
  <div style="overflow:auto"><table>
    <thead><tr><th>#</th><th>PN</th><th>Part</th><th>AIM</th><th class="num">Our €</th><th>SaTy</th></tr></thead>
    <tbody>{table_rows(S['top_only_us'][:20], ["pn","desc","aim","our_eur","our_saty"])}</tbody>
  </table></div>
</section>

<section id="ask">
  <h2>7. Force on Wednesday</h2>
  <ol class="prose">
    <li><strong>Send closed Sep (and Oct) BO tab</strong> — same layout as Aug — so the 495 can be cut by PN / AIM / age.</li>
    <li><strong>91+ day euro</strong> — who owns clearing shutter lid / sail panel / over fender / aged pad kit? Local? Supersession? Dead?</li>
    <li><strong>List A (both)</strong> — confirm ETA on filter asm, pad kits, glass, compressor.</li>
    <li><strong>List C (only us)</strong> — VOR engine / heads / turbos: are these already on their live BO after 31 Aug?</li>
    <li><strong>Stock floor</strong> — MOS back to 3.0 without another fill-rate break when sales to dealers stay at Sep pace.</li>
  </ol>
</section>

<section id="method">
  <h2>8. Method</h2>
  <table>
    <thead><tr><th>Input</th><th>Role</th></tr></thead>
    <tbody>
      <tr><td>Nuno mail 29 Sep — <span class="mono">Backordered lines 2026.xlsx</span></td><td>Their monthly PN-level BO (Jan–Aug filled)</td></tr>
      <tr><td>Nuno KPI sheet 1 Oct</td><td>Fill / MOS / B/O count / sales to dealers (incl. Sep 495)</td></tr>
      <tr><td>EXPORT Order 6 Oct — sold-to 519</td><td>ISZE open sales orders</td></tr>
      <tr><td>AIM catalogue release 2026-10-04</td><td>Competitive / Repair / Accident / High value</td></tr>
    </tbody>
  </table>
  <p class="sub" style="margin-top:12px">Analysis: <span class="mono">01_data\\90_INBOX\\_imotors_bo_compare_20261006\\IMOTORS_BO_HISTORY_ANALYSIS_20261006\\</span></p>
</section>

<p class="footer">Internal / private. GPS Capture for the Portugal trip stays the locked meeting figure 63.3%. This page replaces the earlier open-order-only cut.</p>
</div>
</body>
</html>
"""
html_path.write_text(doc, encoding="utf-8")
cmd_path.write_bytes(b'@echo off\r\nstart "" "%~dp0IMotors_BO_AIM_Deep_Dive_20261006.html"\r\n')
print("HTML", html_path, html_path.stat().st_size)
print("bars", doc.count("bar-row"), "tables", doc.count("<tr>"))
