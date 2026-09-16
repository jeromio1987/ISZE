"""Emit KS PMS decision dashboard HTML. Facts only from scan + known PR00."""
from __future__ import annotations

from pathlib import Path

OUT = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Preparation Meetings"
    r"\IML_ITUK_PMS\mp\JEROME_ONLY\KS_PMS_Parts_Overview_20260818.html"
)

FX = 1.17
F_MULT = 1.59375  # filters / clutch / urea
P_MULT = 1.5045   # pads
SEARCH = "https://www.ks-international.com/catalogsearch/result/?q={}"


def eur(gbp: float) -> float:
    return gbp * FX


def dc(pr00: float, pads: bool = False) -> float:
    return pr00 * (P_MULT if pads else F_MULT)


def money(x: float) -> str:
    return f"€{round(x + 1e-12, 2):,.2f}"


def gbp_s(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return f"£{int(round(x))}"
    return f"£{x:.2f}"


def tip_dc(pr00: float, pads: bool = False) -> str:
    m = P_MULT if pads else F_MULT
    chain = "PR00 × 1.18 × 1.275 = ×1.5045" if pads else "PR00 × 1.25 × 1.275 = ×1.59375"
    fam = "Pads only." if pads else "Filters / clutch / urea."
    return (
        f"ITUK-to-dealer compare = {chain}. Jérôme’s assumption. {fam} "
        f"{pr00:.2f} × {m:g} ≈ {money(dc(pr00, pads))}. "
        "ISZE PR00 to ITUK, IE40, 13 Mar 2026."
    )


def tip_ks(gbp: float) -> str:
    return (
        f"KS ex-VAT {gbp_s(gbp)} × €1.17 = {money(eur(gbp))}. "
        "Listings 19 Aug 2026. Not a dealer-compare."
    )


def tip_span(label: str, box: str) -> str:
    return f'<span class="tip">{label}<span class="tipbox">{box}</span></span>'


def a(href: str, text: str) -> str:
    return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{text}</a>'


def pn_a(pn: str) -> str:
    return f'<a class="pn" href="{SEARCH.format(pn)}" target="_blank" rel="noopener noreferrer">{pn}</a>'


html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KS vs ITUK PMS — decide</title>
<style>
*{box-sizing:border-box;}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
html{scroll-behavior:smooth;}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:15px;line-height:1.45;background:#e8e4dc;}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0;}
a{color:#c0552d;}
a:hover{color:#15233c;}
.kicker{font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.85;}
.cover{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:28px 32px 22px;margin:0 auto;max-width:1240px;}
.cover h1{color:#fff;font-size:30px;line-height:1.12;}
.cover .rule{width:64px;height:3px;background:#c0552d;margin:12px 0 10px;}
.cover ol{margin:10px 0 0;padding:0;list-style:none;counter-reset:c;}
.cover ol li{counter-increment:c;position:relative;padding:10px 12px 10px 44px;margin:0 0 8px;background:rgba(0,0,0,.22);color:#f7f4ee;font-size:15.5px;line-height:1.4;}
.cover ol li::before{content:counter(c);position:absolute;left:12px;top:10px;font-family:Georgia,serif;color:#c0552d;font-size:18px;width:24px;}
.cover ol li b{color:#fff;}
.nav{position:sticky;top:0;z-index:80;background:#15233c;border-bottom:3px solid #c0552d;}
.nav .inner{max-width:1240px;margin:0 auto;display:flex;flex-wrap:wrap;}
.nav a{color:#f7f4ee;text-decoration:none;font-size:12px;letter-spacing:.04em;text-transform:uppercase;padding:12px 16px;display:inline-block;}
.nav a:hover,.nav a:focus{background:#c0552d;color:#fff;}
.page{max-width:1240px;margin:0 auto 12px;background:#fff;padding:22px 28px 28px;box-shadow:0 1px 6px rgba(0,0,0,.08);}
section[id]{scroll-margin-top:52px;}
h2.sec{font-size:20px;margin:0 0 10px;padding-bottom:6px;border-bottom:2px solid #1a2b4a;color:#1a2b4a;}
.lead{color:#6b6256;font-size:13px;margin:0 0 12px;}
.strip{display:flex;flex-wrap:wrap;gap:8px 18px;background:#f7f4ee;border-left:4px solid #c0552d;padding:10px 14px;margin:0 0 16px;font-size:13px;color:#222;}
.strip b{color:#1a2b4a;}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 8px;}
.brand{background:#f7f4ee;padding:12px 14px 14px;border-top:4px solid #1a2b4a;color:#222;}
.brand.tbk{border-top-color:#c0552d;}
.brand.iam{border-top-color:#888780;}
.brand.lub{border-top-color:#2a78d6;}
.brand .lbl{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#6b6256;}
.brand h3{margin:4px 0 6px;font-size:16px;color:#1a2b4a;}
.brand p{margin:0;font-size:13px;color:#222;}
.heroes{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:0 0 14px;}
.hero{background:#f7f4ee;padding:12px 14px;border-top:3px solid #1a2b4a;color:#222;}
.hero.phase{border-top-color:#c0552d;}
.hero .lbl{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#6b6256;}
.hero h3{margin:4px 0 8px;font-size:15px;color:#1a2b4a;}
.hero a.btn{display:inline-block;background:#c0552d;color:#fff;text-decoration:none;font-size:11px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:7px 10px;}
.hero a.btn:hover{background:#15233c;color:#f7f4ee;}
.tip{position:relative;cursor:help;border-bottom:1px dotted #c0552d;}
.tipbox{display:none;position:absolute;z-index:200;left:0;top:calc(100% + 8px);width:280px;background:#15233c;color:#f7f4ee;border-left:3px solid #c0552d;padding:10px 12px;font-size:12px;line-height:1.45;font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-weight:400;text-transform:none;letter-spacing:0;box-shadow:0 10px 24px rgba(21,35,60,.28);}
.tip:hover .tipbox,.tip:focus .tipbox{display:block;}
.wrap{overflow:auto;margin:0 0 8px;}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:980px;}
th{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:8px 9px;font-size:11px;text-transform:uppercase;letter-spacing:.03em;}
thead th{position:sticky;top:44px;z-index:20;background:#1a2b4a;color:#f7f4ee;}
td{padding:8px 9px;border-bottom:1px solid #d9d3c8;color:#222;vertical-align:top;}
tbody tr:nth-child(even){background:#f7f4ee;color:#222;}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
.pn{font-variant-numeric:tabular-nums;font-family:Consolas,"Courier New",monospace;font-size:12px;}
a.pn{text-decoration:none;border-bottom:1px solid #c0552d;}
.tag{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:2px 6px;vertical-align:middle;}
.tag.bvp{background:#1d9e75;color:#fff;}
.tag.gen{background:#1a2b4a;color:#f7f4ee;}
.tag.spa{background:#2a78d6;color:#fff;}
.tag.dead{background:#e24b4a;color:#fff;}
.tag.npr{background:#c0552d;color:#fff;}
.ks{font-size:12px;line-height:1.4;}
.ks .miss{color:#6b6256;}
.dec{font-weight:700;color:#1a2b4a;}
.row-ok td:first-child{box-shadow:inset 4px 0 0 #1d9e75;}
.row-navy td:first-child{box-shadow:inset 4px 0 0 #1a2b4a;}
.row-spa td:first-child{box-shadow:inset 4px 0 0 #2a78d6;}
.row-npr td:first-child{box-shadow:inset 4px 0 0 #c0552d;}
.gapgrid{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:12px;margin-top:8px;align-items:start;}
.gapcard{border:1px solid #d9d3c8;background:#fff;}
.ghd{padding:12px 14px;background:#15233c;color:#f7f4ee;}
.ghd h3{color:#f7f4ee;font-size:15px;margin:2px 0 4px;}
.ghd p{margin:0;font-size:12px;color:#f7f4ee;opacity:.95;}
.gapcard.ituk .ghd{border-bottom:3px solid #c0552d;}
.gapcard.isze .ghd{border-bottom:3px solid #2a78d6;}
.gapcard.both .ghd{border-bottom:3px solid #1d9e75;}
.chips{padding:10px 12px;display:flex;flex-wrap:wrap;gap:6px;}
.chips a{background:#f7f4ee;color:#1a2b4a;text-decoration:none;font-family:Consolas,"Courier New",monospace;font-size:11px;padding:4px 7px;border:1px solid #d9d3c8;}
.chips a:hover{background:#15233c;color:#f7f4ee;}
.misslist{list-style:none;margin:0;padding:0;}
.misslist li{display:grid;grid-template-columns:118px 1fr;gap:8px;padding:7px 12px;border-bottom:1px solid #d9d3c8;font-size:12.5px;color:#222;}
.misslist li:nth-child(even){background:#f7f4ee;}
.misslist .why{color:#444;}
.footer{margin-top:18px;padding-top:8px;border-top:1px solid #d9d3c8;font-size:11px;color:#6b6256;}
@media(max-width:1100px){
  .grid4,.heroes,.gapgrid{grid-template-columns:1fr;}
  thead th{position:static;}
}
@media print{
  .nav{position:static;}
  thead th{position:static;}
  body{background:#fff;}
  a{color:#15233c;}
  .tipbox{display:none !important;}
}
</style>
</head>
<body>

<section class="cover" id="conclusions">
  <div class="kicker">Jérôme only · 19 Aug 2026 · KS prices live-fetched · do not forward as-is</div>
  <h1>Five decisions. Then the table.</h1>
  <div class="rule"></div>
  <ol>
    <li>Oil → <b>BVP</b> """ + pn_a("1876102890") + """ (already 56% of ITUK oil; unnamed KS IAM is cheaper still — do not chase with genuine).</li>
    <li>Fuel → <b>genuine</b> """ + pn_a("8975425400") + """ (BVP """ + pn_a("1876102860") + """ sold 0).</li>
    <li>Air → <b>BVP</b> """ + pn_a("5876102500") + """ (cover 20% on the 37; KS IAM ~€35 vs BVP dealer-compare ~€27.87; also count """ + pn_a("8970622940") + """ 684 units, not on the 37).</li>
    <li>Pads → <b>SPA genuine</b> """ + pn_a("8982447940") + """ vs <b>TBK</b> (OE-equivalent Japanese CV brake; £45 vs our dealer-compare ~€134). Condition-based. ITUK showed 4JJ1 tree OE """ + pn_a("8971686340") + """, not this R90 PN.</li>
    <li>Clutch → <b>BVP kit</b> """ + pn_a("5876102320") + """ manuals only. Urea → <b>keep genuine</b> """ + pn_a("8983507161") + """ (ITUK asked; still not on slides 15–16).</li>
  </ol>
</section>

<nav class="nav" aria-label="Page">
  <div class="inner">
    <a href="#conclusions">Conclusions</a>
    <a href="#quality">Quality</a>
    <a href="#compare">Compare</a>
    <a href="#missed">Who missed</a>
  </div>
</nav>

<section class="page" id="quality">
  <h2 class="sec">Brand quality — four cards, then stop</h2>
  <div class="grid4">
    <div class="brand tbk">
      <div class="lbl">Pads · named IAM</div>
      <h3>TBK</h3>
      <p>Tokyo Buhin Kogyo. Founded as Isuzu Buhin Kogyo. Isuzu still ~9.5%. Japanese CV brake OE. This is the pad competitor — not unnamed £35.</p>
    </div>
    <div class="brand iam">
      <div class="lbl">Filters · unnamed</div>
      <h3>KS own / unnamed</h3>
      <p>Budget on oil, air, fuel. Do not chase that price with genuine. BVP is the filter answer where it sells or exists.</p>
    </div>
    <div class="brand">
      <div class="lbl">Parallel genuine</div>
      <h3>KS genuine OEM</h3>
      <p>Often an older OE hung on the vehicle tree — not automatically the current ITUK PN. Catalog search misses most 4HK1 offer PNs.</p>
    </div>
    <div class="brand lub">
      <div class="lbl">Not this pack</div>
      <h3>Titan Cargo Maxx</h3>
      <p>Fuchs 10W40 on the 4HK1 filter page. Lubricants. Not a filter, pad, clutch, or urea line.</p>
    </div>
  </div>
</section>

<section class="page" id="compare">
  <h2 class="sec">Compare — one row per offer</h2>
  <p class="lead">4HK1 first, then NPR88 where KS search actually matches. Offer PN is the decision part. KS genuine / IAM are live 19 Aug listings (ex-VAT). Hover derived euros.</p>
  <div class="strip" id="assume">
    <span>Jérôme: filters / clutch / urea = <b>PR00 × 1.25 × 1.275</b> (×1.59375)</span>
    <span>Pads = <b>PR00 × 1.18 × 1.275</b> (×1.5045)</span>
    <span>KS ex-VAT <b>£ × 1.17 → €</b></span>
    <span>PR00 = to ITUK, IE40, 13 Mar 2026</span>
  </div>
  <div class="heroes">
    <div class="hero">
      <div class="lbl">What ITUK shared</div>
      <h3>4JJ1 front brake</h3>
      <a class="btn" href="https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/brake/front-brake.html" target="_blank" rel="noopener noreferrer">Open 4JJ1</a>
    </div>
    <div class="hero phase">
      <div class="lbl">Phase 1 truck</div>
      <h3>4HK1 front brake</h3>
      <a class="btn" href="https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake/front-brake.html" target="_blank" rel="noopener noreferrer">Open 4HK1</a>
    </div>
    <div class="hero">
      <div class="lbl">PNs that search-match</div>
      <h3>NPR88 filters</h3>
      <a class="btn" href="https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr88-7-5-4jz1tc/filters.html" target="_blank" rel="noopener noreferrer">Open NPR88</a>
    </div>
  </div>
  <div class="wrap">
  <table>
    <thead>
      <tr>
        <th>Family</th>
        <th>Engine</th>
        <th>Offer (PN)</th>
        <th class="num">ISZE PR00</th>
        <th class="num">Dealer-compare (Jérôme)</th>
        <th>KS genuine £/€</th>
        <th>KS IAM brand · £/€</th>
        <th>Decision</th>
      </tr>
    </thead>
    <tbody>
"""

# rows
U_OIL_G = "https://www.ks-international.com/oil-filter-genuine-1998-2006.html"
U_OIL_A = "https://www.ks-international.com/oil-filter-aftermarket-1998-2006.html"
U_FUEL_G = "https://www.ks-international.com/filter-fuel-genuine-2006.html"
U_FUEL_A = "https://www.ks-international.com/filter-fuel-after-market-2006.html"
U_AIR_G = "https://www.ks-international.com/air-filter-genuine-2004-0011765.html"
U_AIR_A = "https://www.ks-international.com/air-filter-aftermarket-2004-0011765k.html"
U_PAD_G = "https://www.ks-international.com/brake-pads-front-genuine-1.html"
U_PAD_TBK = "https://www.ks-international.com/brake-pads-front-oem.html"
U_PAD_A = "https://www.ks-international.com/brake-pads-front-aftermarket-1.html"
U_CLU_G = "https://www.ks-international.com/clutch-kit-genuine-0012213g.html"
U_CLU_A = "https://www.ks-international.com/clutch-kit-aftermarket-0012213k.html"
U_OIL88_G = "https://www.ks-international.com/oil-filter-genuine-0013721.html"
U_OIL88_A = "https://www.ks-international.com/oil-filter-0013721k.html"
U_FUEL88_G = "https://www.ks-international.com/fuel-filter-genuine-0013722.html"
U_FUEL88_A = "https://www.ks-international.com/fuel-filter-0013722k.html"
U_AIR88_G = "https://www.ks-international.com/air-filter-13724.html"
U_AIR88_A = "https://www.ks-international.com/air-filter-0013723.html"
U_BRG = "https://www.ks-international.com/clutch-release-bearing-0301.html"


def ks_cell(no_hit_pn, gbp, url, label, extra=""):
    miss = (
        f'<div class="miss">no KS hit · {a(SEARCH.format(no_hit_pn), "catalogsearch")}</div>'
        if no_hit_pn
        else ""
    )
    price = ""
    if gbp is not None:
        price = (
            f"{a(url, label)} {gbp_s(gbp)} / "
            + tip_span(money(eur(gbp)), tip_ks(gbp))
        )
    return f'<td class="ks">{miss}{price}{extra}</td>'


def row(css, family, engine, offer_html, pr00, pads, ks_g, ks_iam, decision):
    dcv = dc(pr00, pads) if pr00 is not None else None
    pr00_td = f'<td class="num">{money(pr00)}</td>' if pr00 is not None else '<td class="num">—</td>'
    if dcv is not None:
        dc_td = f'<td class="num">{tip_span(money(dcv), tip_dc(pr00, pads))}</td>'
    else:
        dc_td = '<td class="num">—</td>'
    return (
        f'<tr class="{css}"><td>{family}</td><td>{engine}</td>'
        f"<td>{offer_html}</td>{pr00_td}{dc_td}{ks_g}{ks_iam}"
        f'<td class="dec">{decision}</td></tr>\n'
    )


html += row(
    "row-ok",
    "Oil",
    "4HK1",
    f'<span class="tag bvp">BVP</span> {pn_a("1876102890")}',
    9.96,
    False,
    ks_cell(
        "1876102890",
        13.50,
        U_OIL_G,
        "tree older OE",
        extra=f'<div class="miss">OE {pn_a("8971482700")}</div>',
    ),
    ks_cell(None, 7.50, U_OIL_A, "unnamed"),
    "BVP — do not chase IAM",
)
html += row(
    "row-npr",
    "Oil",
    "NPR88",
    f'<span class="tag npr">NPR88</span> {pn_a("8975439050")}',
    6.73,
    False,
    ks_cell(None, 15.0, U_OIL88_G, "genuine"),
    ks_cell(None, 12.0, U_OIL88_A, "unnamed"),
    "Search-matches; pack oil stays 4HK1 BVP",
)
html += row(
    "row-navy",
    "Fuel",
    "4HK1",
    f'<span class="tag gen">Genuine</span> {pn_a("8975425400")}',
    12.56,
    False,
    ks_cell(
        "8975425400",
        13.0,
        U_FUEL_G,
        "tree other OE",
        extra=f'<div class="miss">OE {pn_a("8980370110")}</div>',
    ),
    ks_cell(None, 10.0, U_FUEL_A, "unnamed"),
    "Genuine — BVP sold 0",
)
html += row(
    "row-npr",
    "Fuel",
    "NPR88",
    f'<span class="tag npr">NPR88</span> {pn_a("8975425390")}',
    10.71,
    False,
    '<td class="ks"><div class="miss">no KS hit · '
    + a(SEARCH.format("8975425390"), "catalogsearch")
    + "</div>S/S listed "
    + pn_a("8983752250")
    + " · "
    + a(U_FUEL88_G, "genuine")
    + f" {gbp_s(20)} / "
    + tip_span(money(eur(20)), tip_ks(20))
    + "</td>",
    ks_cell(None, 12.0, U_FUEL88_A, "unnamed"),
    "KS hit is the S/S PN; pack fuel stays 4HK1 genuine",
)
html += row(
    "row-ok",
    "Air",
    "4HK1",
    f'<span class="tag bvp">BVP</span> {pn_a("5876102500")}',
    17.49,
    False,
    ks_cell("5876102500", 55.0, U_AIR_G, "tree genuine"),
    ks_cell(None, 30.0, U_AIR_A, "unnamed"),
    "BVP sits under KS IAM — push it",
)
html += row(
    "row-npr",
    "Air",
    "NPR88",
    f'<span class="tag npr">NPR88</span> {pn_a("8976739570")}',
    30.73,
    False,
    ks_cell(None, 50.0, U_AIR88_G, "genuine"),
    ks_cell(None, 35.0, U_AIR88_A, "unnamed"),
    "Search-matches; pack air stays 4HK1 BVP",
)
html += row(
    "row-ok",
    "Air",
    "4HK1 · not on 37",
    f'<span class="tag gen">Genuine</span> {pn_a("8970622940")}',
    31.36,
    False,
    ks_cell(None, 55.0, U_AIR_G, "4HK1 listing"),
    ks_cell(None, 30.0, U_AIR_A, "unnamed"),
    "Count it — 684 units; on KS 4HK1 tree",
)
html += row(
    "row-spa",
    "Pads",
    "4HK1 / 4JJ1",
    f'<span class="tag spa">SPA</span> {pn_a("8982447940")}',
    89.11,
    True,
    ks_cell(
        "8982447940",
        125.0,
        U_PAD_G,
        "genuine 0001187",
        extra=f'<div class="miss">screen OE {pn_a("8971686340")}</div>',
    ),
    '<td class="ks">'
    + a(U_PAD_TBK, "TBK 0001187J")
    + f" {gbp_s(45)} / "
    + tip_span(money(eur(45)), tip_ks(45))
    + f'<div class="miss">unnamed {a(U_PAD_A, "£35")} — ignore</div></td>',
    "SPA vs TBK · condition-based",
)
html += row(
    "row-spa",
    "Pads",
    "NPR88",
    f'<span class="tag spa">SPA</span> {pn_a("8982169220")}',
    81.00,
    True,
    ks_cell("8982169220", None, SEARCH.format("8982169220"), ""),
    '<td class="ks"><div class="miss">no KS hit · '
    + a(SEARCH.format("8982169220"), "catalogsearch")
    + "</div>Same TBK SKU as 4HK1/4JJ1 "
    + a(U_PAD_TBK, "£45")
    + " / "
    + tip_span(money(eur(45)), tip_ks(45))
    + "</td>",
    "Second genuine in both packs; lead SPA stays 8982447940",
)
html += row(
    "row-ok",
    "Clutch",
    "4HK1",
    f'<span class="tag bvp">BVP kit</span> {pn_a("5876102320")}',
    194.69,
    False,
    ks_cell("5876102320", 325.0, U_CLU_G, "3-piece genuine"),
    ks_cell(None, 195.0, U_CLU_A, "3-piece unnamed"),
    "BVP kit · manuals / VIN only",
)
html += row(
    "row-navy",
    "Urea",
    "N75",
    f'<span class="tag gen">Genuine</span> {pn_a("8983507161")}',
    70.53,
    False,
    ks_cell("8983507161", None, SEARCH.format("8983507161"), ""),
    ks_cell("1876102341", None, SEARCH.format("1876102341"), ""),
    "Keep genuine — not on KS N75 tree",
)

BOTH = [
    "8983282070", "1876102890", "8975425400", "1876102860",
    "8981772710", "5876102500", "8982447940", "8982169220",
    "8981649171", "8970388314",
]
ITUK_ONLY = [
    ("8983282071", "Oil genuine sibling", "FINAL kept 8983282070"),
    ("5876101170", "Oil S/S → 1876102890", "dead twin"),
    ("5876100310", "Oil S/S → 1876102890", "dead twin"),
    ("8975425050", "Fuel ASM", "ASM not a service-set line"),
    ("8981235322", "Air ASM", "ASM not a service-set line"),
    ("8982157230", "Air ASM", "ASM not a service-set line"),
    ("5876100920", "Clutch BVP piece", "FINAL headlines the kit"),
    ("5876101040", "Clutch BVP piece", "FINAL headlines the kit"),
    ("8975439050", "NPR88 oil", "NPR88 — not 4HK1 headline"),
    ("8983104491", "NPR88 fuel ASM", "NPR88 / ASM"),
    ("8983104490", "NPR88 fuel S/S", "S/S"),
    ("8983572930", "NPR88 fuel sedimenter", "NPR88"),
    ("8975425390", "NPR88 fuel", "NPR88"),
    ("8983752250", "NPR88 fuel S/S", "S/S · KS search hit"),
    ("8980374810", "NPR88 fuel cartridge", "NPR88"),
    ("5876101570", "NPR88 fuel BVP", "NPR88 BVP"),
    ("8980318470", "NPR88 fuel S/S", "S/S"),
    ("8980179710", "NPR88 fuel S/S", "S/S"),
    ("8976659910", "NPR88 air ASM", "NPR88 / ASM"),
    ("8976739570", "NPR88 air", "NPR88 — KS search hit"),
    ("5876102380", "NPR88 pad BVP", "dead twin"),
    ("5876170050", "NPR88 pad BVP-related", "dead / related BVP"),
    ("8978283700", "NPR88 clutch", "NPR88 piece"),
    ("8982551391", "NPR88 clutch", "NPR88 piece"),
    ("5876100771", "NPR88 clutch", "NPR88 piece"),
    ("8980400932", "NPR88 clutch", "NPR88 piece"),
    ("5876100910", "NPR88 clutch", "NPR88 piece"),
]
assert len(ITUK_ONLY) == 27

ISZE_ONLY = [
    ("8983507161", "Urea genuine", "ITUK asked; still missing slides 15–16"),
    ("1876102341", "Urea BVP", "keep genuine — BVP not the offer"),
    ("5876102320", "Clutch BVP kit", "ITUK listed pieces, not the kit"),
    ("1313100120", "Clutch release bearing", "ITUK slides 15–16 miss"),
]

html += """
    </tbody>
  </table>
  </div>
  <p class="lead">Rotor PNs ISZE proposed and ITUK did not list sit as one gap line under Who missed — not a chapter.</p>
</section>

<section class="page" id="missed">
  <h2 class="sec">Who missed what — then stop</h2>
  <p class="lead">ITUK Rev2 18 Aug slides 15–16 = 37 unique. ISZE FINAL headline = 14. Intersection = 10. Every PN links to KS.</p>
  <div class="gapgrid">
    <div class="gapcard ituk">
      <div class="ghd">
        <div class="kicker">ITUK 37 · not in ISZE FINAL headline</div>
        <h3>ITUK only (27)</h3>
        <p>One line: PN · what it is · why FINAL skipped.</p>
      </div>
      <ul class="misslist">
"""
for pn, what, why in ITUK_ONLY:
    html += (
        f'<li>{pn_a(pn)}<span class="why">{what} · {why}</span></li>\n'
    )
html += """
      </ul>
    </div>
    <div class="gapcard isze">
      <div class="ghd">
        <div class="kicker">ISZE FINAL · not on ITUK 15–16</div>
        <h3>ISZE only (4)</h3>
        <p>Urea 2, kit, bearing.</p>
      </div>
      <ul class="misslist">
"""
for pn, what, why in ISZE_ONLY:
    extra = ""
    if pn == "1313100120":
        extra = " · " + a(U_BRG, "KS bearing £90")
    html += (
        f'<li>{pn_a(pn)}<span class="why">{what} · {why}{extra}</span></li>\n'
    )
html += """
      </ul>
      <div class="ghd" style="margin-top:0;border-top:1px solid #2b4a78;">
        <div class="kicker">Neither 37 but real</div>
        <h3>Count anyway</h3>
        <p>Plus one rotor gap-row — not a chapter.</p>
      </div>
      <ul class="misslist">
        <li>""" + pn_a("8970622940") + """<span class="why">Air · 684 units CY2025 · on KS 4HK1 tree """ + a(U_AIR_G, "genuine £55") + " / " + a(U_AIR_A, "IAM £30") + """</span></li>
        <li>""" + pn_a("8981919560") + """<span class="why">ISZE proposed · ITUK pack did not list (same for """ + pn_a("8982488951") + """)</span></li>
      </ul>
    </div>
    <div class="gapcard both">
      <div class="ghd">
        <div class="kicker">Intersection</div>
        <h3>Both (10)</h3>
        <p>No need to repeat 27 times.</p>
      </div>
      <div class="chips">
"""
for pn in BOTH:
    html += a(SEARCH.format(pn), pn) + "\n"
html += """
      </div>
    </div>
  </div>
  <div class="footer">
    KS prices ex-VAT, live fetch 19 Aug 2026, £1 = €1.17.
    Dealer-compare is Jérôme’s assumption (filters / clutch / urea ×1.59375 · pads ×1.5045).
    ISZE PR00 to ITUK, IE40, 13 Mar 2026.
    Sources: KS International vehicle trees and catalog search · ITUK PMS pack slides 15–16 · ISZE Parts Support.
    This page is Jérôme-only. Not for forwarding as-is.
  </div>
</section>
</body>
</html>
"""

OUT.write_text(html, encoding="utf-8")
print("WROTE", OUT, "bytes", OUT.stat().st_size)
# sanity
low = html.lower()
for bad in ("duncan", "campaign", "junk", "street", "route card"):
    print("FORBIDDEN", bad, low.count(bad))
print("hrefs", html.count("https://www.ks-international.com"))
print("conclusions id", 'id="conclusions"' in html)
print("compare table", html.count("<tr class="))
