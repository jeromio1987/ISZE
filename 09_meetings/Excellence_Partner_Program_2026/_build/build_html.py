"""Build one self-contained HTML from the two Excellence Partner analysis documents.

Inputs (same folder, one level up):
  ANALYSE_Excellence_Partner_Program_2026-10-09.md
  SYNERGIE_Excellence_Partner_x_Universe_2026-10-09.md
  _build/order_mix_fy2026.csv
  01_data/08_Distributor/IDS_2026/reports/kaizen_ids/study_payload.json

Output: Excellence_Partner_Program_Analyse_2026-10-09.html (no external files, opens by double-click)

Run from the ISZE root:  python 09_meetings/Excellence_Partner_Program_2026/_build/build_html.py
"""
import html
import json
import re
from pathlib import Path

import markdown
import pandas as pd

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOT = HERE.parents[2]
OUT = PACK / "Excellence_Partner_Program_Analyse_2026-10-09.html"

DOCS = [
    ("analyse", "Deel 1 · Het programma", PACK / "ANALYSE_Excellence_Partner_Program_2026-10-09.md"),
    ("synergie", "Deel 2 · Samen met Universe", PACK / "SYNERGIE_Excellence_Partner_x_Universe_2026-10-09.md"),
]

IDS_NAMES = {
    "MALTA": "Malta", "PORTUGAL": "Portugal", "HUNGARY": "Hongarije", "ITUK": "Isuzu Truck UK",
    "RSA": "Noorwegen", "IUK": "Isuzu UK pickup", "DENMARK": "Denemarken", "ISRAEL": "UMI",
    "ROMANIA": "Roemenië", "BE": "België", "NL": "Nederland", "CYPRUS": "Cyprus", "PETROS": "Griekenland",
}


def eur_k(v):
    return f"€{v/1e6:,.2f}M".replace(".", ",") if v >= 1e6 else f"€{v/1e3:,.0f}k"


def ids_chart():
    p = json.loads((ROOT / "01_data/08_Distributor/IDS_2026/reports/kaizen_ids/study_payload.json").read_text(encoding="utf-8"))
    rows = [(IDS_NAMES[c["country"]], c["total_pct"] * 100, c["dealer_count"])
            for c in p["country_matrix"] if c["country"] in IDS_NAMES]
    rows.sort(key=lambda r: -r[1])
    lo, hi = 70.0, 92.0
    def x(v):
        return (v - lo) / (hi - lo) * 100
    bars = []
    for name, pct, n in rows:
        cls = "pass" if pct >= 85 else "fail"
        label = f"{pct:.1f}%".replace(".", ",")
        bars.append(
            f'<div class="hb-row"><div class="hb-label">{html.escape(name)} <span class="muted">({n})</span></div>'
            f'<div class="hb-track"><div class="hb-bar {cls}" style="width:{x(pct):.1f}%"></div>'
            f'<span class="hb-val">{label}</span></div></div>'
        )
    line = x(85)
    return f"""
<figure class="chart">
  <figcaption><strong>IDS 2026 — gemiddelde score per distributeurnetwerk</strong><span class="muted"> · tussen haakjes: aantal dealers · lijn = drempel 85% · as begint bij 70%</span></figcaption>
  <div class="hb" style="--thr:{line:.2f}">
    {''.join(bars)}
    <div class="hb-threshold"><span>85%</span></div>
  </div>
  <p class="source">Bron: IDS 2026, studie 24 juli 2026. Zelfevaluatie; Isuzu Truck UK alleen totalen. Geen IDS: Duitsland, Ierland, UTI, Zweden, Finland, IJsland, CIS.</p>
</figure>
"""


def cost_chart():
    o = pd.read_csv(HERE / "order_mix_fy2026.csv", index_col=0)
    cis = ["UKRAINE", "ARMENIA", "KAZAKHSTAN"]
    sor_all = o.drop(cis).SOR_eur.sum()
    year1 = o.loc[["IUK", "UTI", "IRELAND", "PORTUGAL", "ITUK", "GREECE", "ROMANIA"], "SOR_eur"].sum()
    items = [
        ("Niveau 1, realistisch jaar 1", year1 * 0.025, "Excellence", "c1"),
        ("Niveau 1, alle 19 distributeurs", sor_all * 0.025, "Excellence", "c2"),
        ("Niveau 2, alle 19 distributeurs", sor_all * 0.05, "Excellence", "c2"),
        ("Universe, aanbevolen route", 100_000, "Universe", "c3"),
        ("Universe, plafond", 300_000, "Universe", "c3"),
        ("DLOD Route A", 90_000, "Universe", "c3"),
    ]
    mx = 1_200_000
    rows = []
    for label, v, grp, cls in items:
        rows.append(
            f'<div class="hb-row"><div class="hb-label">{html.escape(label)}</div>'
            f'<div class="hb-track"><div class="hb-bar {cls}" style="width:{v/mx*100:.1f}%"></div>'
            f'<span class="hb-val">{eur_k(v)}</span></div></div>'
        )
    band_l, band_r = 638_000 / mx * 100, 726_000 / mx * 100
    return f"""
<figure class="chart">
  <figcaption><strong>Kost per jaar naast elkaar</strong><span class="muted"> · gearceerde band = wat de prijsherziening +5% opbrengt (€638k–€726k)</span></figcaption>
  <div class="hb cost" style="--bl:{band_l:.2f};--bw:{band_r-band_l:.2f}">
    <div class="hb-band"></div>
    {''.join(rows)}
  </div>
  <div class="legend"><span><i class="c1"></i>Excellence, realistisch</span><span><i class="c2"></i>Excellence, maximum</span><span><i class="c3"></i>Universe-voorstellen</span></div>
  <p class="source">Bron: stockorders FY2026 per distributeur (CIS uitgesloten); Universe 3.0 §9; DLOD-uitrol §7; €300k term sheet §2.</p>
</figure>
"""


def coverage_chart():
    rows = [
        ("Isuzu Truck UK", "nee", "dealer", "alleen 2025 per dealer (64)"),
        ("Isuzu UK pickup", "ja", "netwerk", ""),
        ("Ierland", "ja", "netwerk", ""),
        ("UTI", "ja", "netwerk", ""),
        ("Portugal", "ja", "netwerk", ""),
        ("Griekenland", "nee", "netwerk", ""),
        ("Roemenië", "nee", "netwerk", "na formele vraag, sep 2026"),
        ("Duitsland", "ja", "geen", ""),
        ("Benelux", "ja", "geen", ""),
        ("Zweden", "ja", "geen", ""),
        ("Noorwegen", "ja", "geen", ""),
        ("UMI", "ja", "geen", ""),
        ("Cyprus, Hongarije, Finland, Malta, Denemarken, IJsland, Palestina", "nee", "geen", ""),
    ]
    lab = {"dealer": "per dealer", "netwerk": "netwerktotaal", "geen": "niets in de workspace"}
    cells = "".join(
        f'<div class="cov-row"><div class="cov-name">{html.escape(n)}</div>'
        f'<div class="cov-kb">{"kickback" if kb == "ja" else ""}</div>'
        f'<div class="cov-pill {g}">{lab[g]}</div><div class="cov-note muted">{html.escape(note)}</div></div>'
        for n, kb, g, note in rows
    )
    return f"""
<figure class="chart">
  <figcaption><strong>Sales to dealer: wat er vandaag binnenkomt</strong><span class="muted"> · per distributeur, beste beschikbare detailniveau</span></figcaption>
  <div class="cov">{cells}</div>
  <p class="source">Bron: sales-to-dealer-register en de genormaliseerde bestanden per distributeur, oktober 2026.</p>
</figure>
"""


INSERTS = {
    "analyse": [("| **Geen IDS 2026** |", ids_chart)],
    "synergie": [
        ("| Cyprus, Hongarije, Finland, Malta, Denemarken, IJsland, Palestina | nee | geen | — |", coverage_chart),
        ("| Ter vergelijking: prijsherziening +5% |", cost_chart),
    ],
}


def slug(text, prefix):
    s = re.sub(r"<[^>]+>", "", text)
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return f"{prefix}-{s[:60]}"


def convert(key, md_text):
    lines = md_text.splitlines()
    out = []
    pending = {anchor: fn for anchor, fn in INSERTS.get(key, [])}
    for ln in lines:
        out.append(ln)
        for anchor, fn in list(pending.items()):
            if ln.startswith(anchor):
                out.append("")
                out.append(fn().strip())
                out.append("")
                del pending[anchor]
    assert not pending, f"chart anchors not found in {key}: {list(pending)}"
    # drop the H1 (the page has its own header) and the first status line block
    body = "\n".join(out)
    body = re.sub(r"^# .*\n", "", body, count=1)
    htm = markdown.markdown(body, extensions=["tables", "sane_lists"])
    toc = []

    def add_id(m):
        level, inner = m.group(1), m.group(2)
        sid = slug(inner, key)
        if level == "2":
            toc.append((sid, re.sub(r"<[^>]+>", "", inner)))
        return f'<h{level} id="{sid}">{inner}</h{level}>'

    htm = re.sub(r"<h([23])>(.*?)</h\1>", add_id, htm)
    htm = htm.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    return htm, toc


CSS = """
:root{--bg:#ffffff;--panel:#f4f5f6;--ink:#1d2124;--muted:#5f676e;--line:#dfe2e5;--red:#D71920;--navy:#15233C;
--terra:#C0552D;--char:#24282C;--ok:#2e7d4f;--warn:#b26a00;--bar2:#8a9096;--bar3:#4f6d8f;--hdr-ink:#ffffff}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#16191c;--panel:#1f2327;--ink:#e8eaec;
--muted:#9aa3ab;--line:#30363b;--char:#0f1113;--ok:#5fbf86;--warn:#e0a040;--bar2:#6f777e;--bar3:#7f9dc0}}
:root[data-theme="dark"]{--bg:#16191c;--panel:#1f2327;--ink:#e8eaec;--muted:#9aa3ab;--line:#30363b;--char:#0f1113;
--ok:#5fbf86;--warn:#e0a040;--bar2:#6f777e;--bar3:#7f9dc0}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Arial,Helvetica,sans-serif}
header.top{background:var(--char);color:var(--hdr-ink);padding:28px 24px 22px}
header.top .wrap{max-width:1240px;margin:0 auto}
header.top .eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#ff6b70;font-weight:700}
header.top h1{margin:6px 0 6px;font-size:30px;line-height:1.2}
header.top p{margin:0;color:#c9ced3;max-width:860px}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;max-width:1240px;margin:18px auto 0}
.kpi{background:#2f343a;border-radius:8px;padding:12px 14px}
.kpi b{display:block;font-size:24px;color:#fff}
.kpi span{font-size:12.5px;color:#c9ced3}
.layout{max-width:1240px;margin:0 auto;display:grid;grid-template-columns:270px minmax(0,1fr);gap:32px;padding:24px}
.layout>*{min-width:0}
nav.toc{position:sticky;top:12px;align-self:start;max-height:calc(100vh - 24px);overflow:auto;font-size:13.5px}
nav.toc summary{cursor:pointer;font-weight:700;font-size:13px;margin-bottom:4px}
nav.toc h4{margin:14px 0 6px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--red)}
nav.toc a{display:block;color:var(--ink);text-decoration:none;padding:3px 0 3px 10px;border-left:2px solid var(--line)}
nav.toc a:hover{border-left-color:var(--red);color:var(--red)}
.themebtn{margin-top:16px;font:inherit;font-size:12.5px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:6px 10px;cursor:pointer}
main section.doc{margin-bottom:56px}
.partlabel{display:inline-block;background:var(--red);color:#fff;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:4px}
main h2{font-size:22px;margin:36px 0 10px;padding-top:6px;border-top:1px solid var(--line)}
main h3{font-size:17px;margin:24px 0 8px;color:var(--navy)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) main h3{color:#9fb6d8}}
:root[data-theme="dark"] main h3{color:#9fb6d8}
main p,main li{max-width:880px}
main code{font-size:12.5px;background:var(--panel);padding:1px 5px;border-radius:4px;word-break:break-all}
main hr{display:none}
.tablewrap{overflow-x:auto;margin:12px 0 18px;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{padding:8px 10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--panel);font-weight:700}
tr:last-child td{border-bottom:none}
td:has(> strong:only-child){}
figure.chart{margin:16px 0 22px;padding:16px 18px;background:var(--panel);border-radius:10px;max-width:880px}
figcaption{margin-bottom:12px;font-size:14px}
.muted{color:var(--muted)}
.source{font-size:12px;color:var(--muted);margin:10px 0 0}
.hb{position:relative}
.hb-row{display:grid;grid-template-columns:200px minmax(0,1fr);gap:10px;align-items:center;margin:5px 0}
.hb-label{font-size:13px;text-align:right}
.hb-track{position:relative;height:20px;display:flex;align-items:center}
.hb-bar{height:16px;border-radius:3px;background:var(--bar2);min-width:2px}
.hb-bar.pass{background:var(--ok)}.hb-bar.fail{background:var(--bar2)}
.hb-bar.c1{background:var(--red)}.hb-bar.c2{background:var(--terra)}.hb-bar.c3{background:var(--bar3)}
.hb-val{margin-left:5px;padding:0 3px;font-size:12.5px;white-space:nowrap;position:relative;z-index:3;background:var(--panel);border-radius:3px}
.hb-row{position:relative;z-index:1}.hb-threshold{z-index:2}.hb.cost .hb-band{z-index:0}
.hb-threshold{position:absolute;top:0;bottom:0;left:calc(210px + (100% - 210px) * var(--thr) / 100);border-left:2px dashed var(--red);pointer-events:none}
.hb-threshold span{position:absolute;top:-18px;left:-14px;font-size:11px;color:var(--red);font-weight:700}
.hb.cost .hb-band{position:absolute;top:0;bottom:0;left:calc(210px + (100% - 210px) * var(--bl) / 100);width:calc((100% - 210px) * var(--bw) / 100);
background:repeating-linear-gradient(45deg,rgba(215,25,32,.14) 0 6px,transparent 6px 12px);border-left:1px solid rgba(215,25,32,.5);border-right:1px solid rgba(215,25,32,.5)}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:12.5px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.legend i.c1{background:var(--red)}.legend i.c2{background:var(--terra)}.legend i.c3{background:var(--bar3)}
.cov-row{display:grid;grid-template-columns:minmax(0,1.6fr) 80px 170px minmax(0,1.2fr);gap:10px;align-items:center;padding:5px 0;border-bottom:1px solid var(--line);font-size:13px}
.cov-row:last-child{border-bottom:none}
.cov-kb{font-size:11.5px;color:var(--muted)}
.cov-pill{font-size:12px;font-weight:700;border-radius:999px;padding:2px 10px;text-align:center}
.cov-pill.dealer{background:var(--ok);color:#fff}.cov-pill.netwerk{background:var(--warn);color:#fff}.cov-pill.geen{background:var(--line);color:var(--ink)}
footer{max-width:1240px;margin:0 auto;padding:0 24px 40px;font-size:12px;color:var(--muted)}
@media (max-width:900px){.layout{grid-template-columns:1fr;padding:16px}nav.toc{position:static;max-height:none}
.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}header.top{padding:22px 16px}header.top h1{font-size:24px}
.hb-row{grid-template-columns:110px minmax(0,1fr)}.hb-label{font-size:12px}
.hb-threshold{left:calc(120px + (100% - 120px) * var(--thr) / 100)}
.hb.cost .hb-band{left:calc(120px + (100% - 120px) * var(--bl) / 100);width:calc((100% - 120px) * var(--bw) / 100)}
.cov-row{grid-template-columns:minmax(0,1fr) auto;}.cov-kb,.cov-note{grid-column:1 / -1}}
@media print{nav.toc,.themebtn{display:none}.layout{grid-template-columns:1fr}}
"""

JS = """
(function(){var d=document.getElementById('tocd');if(d&&window.innerWidth<900)d.removeAttribute('open')})();
(function(){var b=document.getElementById('themebtn');if(!b)return;var r=document.documentElement;
function cur(){return r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}
function lab(){b.textContent=cur()==='dark'?'Licht thema':'Donker thema'}
try{var s=localStorage.getItem('iepp-theme');if(s)r.setAttribute('data-theme',s)}catch(e){}
lab();b.addEventListener('click',function(){var n=cur()==='dark'?'light':'dark';r.setAttribute('data-theme',n);
try{localStorage.setItem('iepp-theme',n)}catch(e){}lab()})})();
"""


def main():
    o = pd.read_csv(HERE / "order_mix_fy2026.csv", index_col=0)
    sor_all = o.drop(["UKRAINE", "ARMENIA", "KAZAKHSTAN"]).SOR_eur.sum()
    year1 = o.loc[["IUK", "UTI", "IRELAND", "PORTUGAL", "ITUK", "GREECE", "ROMANIA"], "SOR_eur"].sum()

    sections, tocs = [], []
    for key, label, path in DOCS:
        htm, toc = convert(key, path.read_text(encoding="utf-8"))
        sections.append(f'<section class="doc" id="{key}"><span class="partlabel">{html.escape(label)}</span>{htm}</section>')
        tocs.append((label, key, toc))

    nav = "".join(
        f'<h4><a href="#{key}" style="border:none;padding:0;color:inherit">{html.escape(label)}</a></h4>'
        + "".join(f'<a href="#{sid}">{html.escape(t)}</a>' for sid, t in toc)
        for label, key, toc in tocs
    )
    kpis = [
        (eur_k(year1 * 0.025), "niveau 1, realistisch jaar 1"),
        (eur_k(sor_all * 0.025), "niveau 1, als alle 19 meedoen"),
        (eur_k(sor_all * 0.05), "niveau 2, als alle 19 het halen"),
        ("1 van 7", "distributeurs met sales to dealer levert per dealer"),
    ]
    kpi_html = "".join(f'<div class="kpi"><b>{v}</b><span>{html.escape(t)}</span></div>' for v, t in kpis)

    page = f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Excellence Partner Program</title><style>{CSS}</style></head>
<body>
<header class="top"><div class="wrap">
  <div class="eyebrow">Intern · draft · 9 oktober 2026</div>
  <h1>Isuzu Excellence Partner Program — analyse en uitwerking</h1>
  <p>Het voorstel getoetst aan de data in de workspace, bijgesteld na de antwoorden van 9 oktober, en hoe het samen met Isuzu Universe kan werken. Bedragen per jaar, op stockorders FY2026 (1 april 2025 – 31 maart 2026), zonder de CIS-markten.</p>
  <div class="kpis">{kpi_html}</div>
</div></header>
<div class="layout">
  <nav class="toc" aria-label="Inhoud"><details id="tocd" open><summary>Inhoud</summary>{nav}</details><button class="themebtn" id="themebtn" type="button">Donker thema</button></nav>
  <main>{''.join(sections)}</main>
</div>
<footer>Gebouwd uit de twee analysebestanden in deze map met <code>_build/build_html.py</code>. Cijfers: verificatierapport groen (24 sep 2026). Geen externe bestanden nodig.</footer>
<script>{JS}</script>
</body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(OUT, f"{len(page)/1024:.0f} KB")


if __name__ == "__main__":
    main()
