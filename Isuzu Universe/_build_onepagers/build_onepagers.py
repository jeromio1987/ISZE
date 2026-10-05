# -*- coding: utf-8 -*-
"""Distributor one-pagers. Reads only from 01_data/00_derived (never raw sales). Does not edit
Isuzu Universe/_build_final/charts.py or build.py -- palette, primitives and banned-term list are
copied from them, data loaders are re-implemented against the same source files.
"""
import csv
import os
import json
import re
import subprocess
import tempfile
from html import escape

DERIVED = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
OUT_DIR = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\02_Atlas\DISTRIBUTOR_ONE_PAGERS_2026-09"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
QA_DIR = os.path.join(OUT_DIR, "_qa")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(QA_DIR, exist_ok=True)

CHAR = "#24282C"
RED = "#D71920"
MID = "#6B7078"
LIGHT = "#B9BDC3"
GRID = "#E4E5E7"
INK = "#1E2124"
FONT = "Arial, Helvetica, sans-serif"
W = 680

NAMES = {
    "UKRAINE": "Ukraine", "PORTUGAL": "Portugal", "IUK": "Isuzu UK", "GERMANY": "Germany", "SWEDEN": "Sweden",
    "IRELAND": "Ireland", "DENMARK": "Denmark", "CYPRUS": "Cyprus", "NORWAY": "Norway",
    "PALESTINE": "Palestine", "ITUK": "Isuzu Truck UK", "GREECE": "Greece", "ICELAND": "Iceland",
    "BELGIUM": "Belgium", "MALTA": "Malta", "FINLAND": "Finland", "UMI": "Isuzu Israel (light commercial)",
    "KAZAKHSTAN": "Kazakhstan", "ARMENIA": "Armenia", "HUNGARY": "Hungary", "ROMANIA": "Romania",
    "UTI": "Isuzu Israel (trucks)",
}

IDS_TAB_FOR_DB = {
    "BELGIUM": "Belgium", "CYPRUS": "Cyprus", "DENMARK": "Denmark", "GREECE": "Greece",
    "HUNGARY": "Hungary", "UMI": "Israel LCV", "MALTA": "Malta", "NORWAY": "Norway",
    "PORTUGAL": "Portugal", "ROMANIA": "Romania", "ITUK": "UK CV", "IUK": "UK LCV",
}

FAMILY_LABEL = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "urea_filter": "AdBlue filter", "blower_filter": "Blower unit filter", "brake_pad": "Brake pad",
    "brake_shoe": "Brake shoe", "clutch_disc": "Clutch disc", "clutch_pressure_plate": "Clutch pressure plate",
    "clutch_kit": "Clutch kit", "release_bearing": "Release bearing", "pilot_bearing": "Pilot bearing",
    "clutch_booster": "Clutch booster", "brake_rotor": "Brake rotor",
}


def load(name):
    with open(os.path.join(DERIVED, name), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def eur(v, dec=0):
    return "\u20ac" + f"{v:,.{dec}f}"


def eurk(v):
    if abs(v) >= 1e6:
        return f"\u20ac{v / 1e6:.2f}M"
    return f"\u20ac{v / 1e3:,.0f}k"


def t(x, y, s, size=11, fill=INK, anchor="start", weight="normal", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" {extra}>{escape(str(s))}</text>')


def svg(h, body, label):
    return (f'<svg viewBox="0 0 {W} {h}" width="100%" role="img" aria-label="{escape(label)}" '
            f'xmlns="http://www.w3.org/2000/svg" style="display:block">{body}</svg>')


def nice_max(v):
    for step in (1, 2, 2.5, 5):
        for mag in range(0, 10):
            m = step * 10 ** mag
            if m >= v:
                return m
    return v


def paired_bars(panels, h=250):
    """panels: list of (title, v2024, v2025, fmt)."""
    n = len(panels)
    pw = W / n
    body = []
    top, bottom = 58, h - 34
    for i, (title, a, b, fmt) in enumerate(panels):
        x0 = i * pw
        mx = max(a, b, 1) * 1.12
        body.append(t(x0 + 20, 20, title, 12, MID, weight="bold"))
        pctv = (b - a) / a * 100 if a else 0
        body.append(t(x0 + pw - 24, 22, f"{pctv:+.1f}%", 20, RED, "end", "bold"))
        bw = 84
        for j, (lab, v, col) in enumerate((("2024", a, LIGHT), ("2025", b, RED))):
            cx = x0 + 60 + j * 130
            bh = (bottom - top) * v / mx
            body.append(f'<rect x="{cx:.1f}" y="{bottom - bh:.1f}" width="{bw}" height="{bh:.1f}" fill="{col}" rx="2"/>')
            body.append(t(cx + bw / 2, bottom - bh - 7, fmt(v), 12, INK, "middle", "bold"))
            body.append(t(cx + bw / 2, bottom + 18, lab, 11, MID, "middle"))
        body.append(f'<line x1="{x0 + 40}" y1="{bottom}" x2="{x0 + pw - 30}" y2="{bottom}" stroke="{MID}" stroke-width="0.8"/>')
    return svg(h, "".join(body), " / ".join(p[0] for p in panels))


def hbars(items, fmt, h=None, label_w=190, value_w=150, title=None, maxv=None, note_fn=None):
    row = 28
    top = 34 if title else 8
    h = h or top + row * len(items) + 16
    mx = maxv or nice_max(max((v for _, v, _ in items), default=1) * 1.05)
    plot_w = W - label_w - value_w
    body = []
    if title:
        body.append(t(0, 16, title, 12, MID, weight="bold"))
    for i, (lab, v, hi) in enumerate(items):
        y = top + i * row
        bw = max(plot_w * v / mx, 1.5) if mx else 1.5
        body.append(t(label_w - 10, y + 15, lab, 11.5, INK, "end", "bold" if hi else "normal"))
        body.append(f'<rect x="{label_w}" y="{y + 3}" width="{bw:.1f}" height="18" fill="{RED if hi else LIGHT}" rx="2"/>')
        txt = fmt(v) + (("   " + note_fn(lab, v)) if note_fn else "")
        body.append(t(label_w + bw + 8, y + 16, txt, 11, INK if hi else MID, weight="bold" if hi else "normal"))
    return svg(h, "".join(body), title or "ranked bars")


def stacked_two(labels_vals, h=180, title=None):
    """labels_vals: list of (label, part_a_val, part_a_name, part_b_val, part_b_name)."""
    row, top, lw = 40, 34 if title else 6, 190
    hh = top + row * len(labels_vals) + 10
    body = []
    if title:
        body.append(t(0, 16, title, 12, MID, weight="bold"))
    plot = W - lw - 60
    for i, (lab, a, aname, b, bname) in enumerate(labels_vals):
        y = top + i * row
        tot = a + b
        aw = plot * (a / tot) if tot else 0
        bw = plot * (b / tot) if tot else 0
        body.append(t(lw - 10, y + 15, lab, 11.5, INK, "end", "bold"))
        body.append(f'<rect x="{lw}" y="{y + 2}" width="{aw:.1f}" height="18" fill="{RED}" rx="1"/>')
        body.append(f'<rect x="{lw + aw:.1f}" y="{y + 2}" width="{bw:.1f}" height="18" fill="{LIGHT}" rx="1"/>')
        body.append(t(lw + plot + 8, y + 15, f"{a / tot * 100:.0f}% / {b / tot * 100:.0f}%" if tot else "n/a", 11, INK, weight="bold"))
    return svg(hh, "".join(body), title or "genuine vs best value")


# ------------------------------------------------------------- data loading
GPS = load("gps_spu_by_distributor.csv")
GPS_25 = {r["distributor_code"]: r for r in GPS if r["year"] == "2025"}
GPS_24 = {r["distributor_code"]: r for r in GPS if r["year"] == "2024"}
BVP = load("pms_genuine_bvp_vs_price_2024_2025.csv")
CAP = load("pms_capture_by_db_year.csv")
CAP25_TOTAL = [r for r in CAP if r["year"] == "2025" and r["line_type"] == "total"]
IDS_ROWS = load("ids_dealer_network_cleaned_2026-09-20.csv")

DEALER_FILES = [f for f in os.listdir(DERIVED) if f.startswith("dealer_sellout_long_") and f.endswith(".csv")]


def dealer_visibility(db):
    """Any sales-to-dealer data for CY2025, and is any of it by named dealer?"""
    fname = f"dealer_sellout_long_{db}_CY2025.csv"
    if fname not in DEALER_FILES:
        return {"any": False, "named": False, "rows": 0, "named_rows": 0}
    rows = load(fname)
    named_rows = sum(1 for r in rows if r.get("dealer_name", "").strip())
    return {"any": True, "named": named_rows > 0, "rows": len(rows), "named_rows": named_rows}


def network_visibility_counts():
    any_2025 = set()
    named_2025 = set()
    for f in DEALER_FILES:
        if "CY2025" not in f or "network" in f:
            continue
        db = f.replace("dealer_sellout_long_", "").split("_CY2025")[0]
        any_2025.add(db)
        rows = load(f)
        if any(r.get("dealer_name", "").strip() for r in rows):
            named_2025.add(db)
    return any_2025, named_2025


ANY_2025, NAMED_2025 = network_visibility_counts()
N_DB = len(GPS_25)


def genuine_bvp(db):
    rows = [r for r in BVP if r["distributor_code"] == db]
    g25 = sum(float(r["genuine_eur_2025"] or 0) for r in rows)
    b25 = sum(float(r["bvp_eur_2025"] or 0) for r in rows)
    g24 = sum(float(r["genuine_eur_2024"] or 0) for r in rows)
    b24 = sum(float(r["bvp_eur_2024"] or 0) for r in rows)
    return {"g25": g25, "b25": b25, "g24": g24, "b24": b24, "n_lines": len(rows)}


def capture_families(db, top_n=6):
    rows = [r for r in CAP25_TOTAL if r["distributor_code"] == db]
    ok = [r for r in rows if r["capture_rate"] not in ("", None) and float(r["capture_rate"]) <= 1
          and float(r["expected_qty"] or 0) > 0]
    bad = [r for r in rows if r not in ok]
    ok_sorted = sorted(ok, key=lambda r: -float(r["expected_qty"]) * float(r["avg_sp_eur"] or 0))
    top = ok_sorted[:top_n]
    exp_val = sum(float(r["expected_qty"]) * float(r["avg_sp_eur"] or 0) for r in ok)
    act_val = sum(float(r["actual_rev_eur"]) for r in ok)
    return {
        "reliable": top, "n_reliable": len(ok), "n_unreliable": len(bad),
        "unreliable_names": [FAMILY_LABEL.get(r["pms_category"], r["pms_category"]) for r in bad],
        "n_total": len(rows), "overall_capture": (act_val / exp_val * 100) if exp_val else None,
    }


def ids_stats(db):
    tab = IDS_TAB_FOR_DB.get(db)
    if not tab:
        return None
    rows = [r for r in IDS_ROWS if r["ids_tab"] == tab]
    scored = [r for r in rows if r["points_pct"].strip() and float(r["points_pct"]) > 0]
    return {"tab": tab, "n_dealers": len(rows), "n_scored": len(scored)}


def parts_billed(db):
    r25, r24 = GPS_25[db], GPS_24.get(db)
    v25 = float(r25["total_sales_eur"] or 0)
    v24 = float(r24["total_sales_eur"] or 0) if r24 else None
    return v25, v24


# ------------------------------------------------------------- HTML shell
CSS = """
@page { size: A4; margin: 16mm 16mm 16mm 16mm;
  @bottom-left { content: "Isuzu Universe  \\00b7  Distributor review  \\00b7  September 2026"; font: 7.5pt Arial, sans-serif; color: #6B7078; }
  @bottom-right { content: counter(page); font: bold 8pt Arial, sans-serif; color: #D71920; } }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; line-height: 1.48; color: #1E2124; background: #FFFFFF; }
.hero { background: #24282C; color: #fff; padding: 10mm 14mm 8mm; }
.hero .kicker { font-size: 8pt; letter-spacing: .2em; color: #B9BDC3; font-weight: bold; text-transform: uppercase; }
.hero h1 { font-size: 26pt; margin: 3mm 0 1mm; }
.hero .sub { font-size: 10.5pt; color: #D9DBDE; max-width: 160mm; }
.wrap { padding: 6mm 14mm 4mm; }
h2 { font-size: 12.5pt; color: #24282C; margin: 5mm 0 2mm; border-left: 3px solid #D71920; padding-left: 2.5mm; break-after: avoid; }
p { margin: 0 0 2.2mm; }
.lead { font-size: 10pt; color: #24282C; }
figure { margin: 2mm 0 3mm; break-inside: avoid; }
figcaption { font-size: 7.8pt; color: #6B7078; margin-top: 1mm; }
figcaption b { color: #24282C; }
.callout { border-left: 3px solid #D71920; background: #F5F5F4; padding: 3mm 4mm; margin: 2.5mm 0 3.5mm; break-inside: avoid; font-size: 9.3pt; }
.note { color: #6B7078; font-style: italic; font-size: 9pt; }
.bignum { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin: 3mm 0 4mm; }
.bignum div { background: #F5F5F4; border-top: 3px solid #24282C; padding: 2.5mm 3mm; }
.bignum div.r { border-top-color: #D71920; }
.bignum .v { font-size: 15pt; font-weight: bold; color: #24282C; line-height: 1.1; }
.bignum div.r .v { color: #D71920; }
.bignum .l { font-size: 7.6pt; color: #6B7078; margin-top: 1mm; line-height: 1.25; }
table { width: 100%; border-collapse: collapse; margin: 1.5mm 0 3mm; font-size: 8.6pt; }
th { background: #24282C; color: #fff; text-align: left; padding: 1.6mm 2mm; font-size: 7.6pt; }
td { padding: 1.5mm 2mm; border-bottom: .6px solid #E4E5E7; }
tbody tr:nth-child(even) td { background: #F5F5F4; }
.question { border: 2px solid #D71920; padding: 4mm 5mm; margin: 4mm 0 2mm; background: #fff; break-inside: avoid; }
.question .q { font-size: 13pt; font-weight: bold; color: #24282C; }
.question .lines { margin-top: 4mm; border-top: 1px dashed #B9BDC3; }
.question .lines div { height: 7mm; border-bottom: 1px dashed #B9BDC3; }
.foot { font-size: 7.3pt; color: #8A8F96; border-top: .6px solid #E4E5E7; padding-top: 2mm; margin-top: 4mm; }
.sectionbreak { height: 1mm; }
"""


def fig(svg_body, caption, source):
    return f'<figure>{svg_body}<figcaption><b>{caption}</b> {escape(source)}</figcaption></figure>'


def table(head, rows):
    h = "".join(f"<th>{escape(str(x))}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def build_page(db):
    name = NAMES.get(db, db.title())
    v25, v24 = parts_billed(db)
    pct = (v25 - v24) / v24 * 100 if v24 else None

    vis = dealer_visibility(db)
    gb = genuine_bvp(db)
    cap = capture_families(db)
    ids = ids_stats(db)

    H = []
    H.append(f"""<div class="hero"><div class="kicker">Isuzu Universe &middot; Distributor review</div>
    <h1>{escape(name)}</h1>
    <div class="sub">Prepared for a working conversation with {escape(name)}, calendar 2025 against 2024 unless stated. Figures are {escape(name)}'s own; every comparison is against its own history or an anonymised network aggregate.</div></div>""")

    H.append('<div class="wrap">')

    # 1. Parts billed
    H.append('<h2>Parts billed by Isuzu to you</h2>')
    if v24:
        H.append(fig(paired_bars([("Parts billed (EUR)", v24, v25, lambda v: eur(v))], h=210),
                      f"Parts billed, {'up' if pct >= 0 else 'down'} {abs(pct):.1f}% year on year.",
                      "Source: ISZE billing records, calendar 2024 and 2025."))
    else:
        H.append(f'<p class="note">2024 not available on a comparable basis; 2025 parts billed: {eur(v25)}.</p>')

    # 2. Visibility
    H.append('<h2>What we can see of your own dealer network</h2>')
    if vis["named"]:
        H.append(f'<p>You sent us sales-to-dealer data for 2025, broken down <b>by named dealer</b> ({vis["rows"]:,} lines). '
                  f'Across the network, {len(ANY_2025)} of {N_DB} distributors sent any sales-to-dealer data for 2025, and you are the only one that sent it by named dealer.</p>')
    elif vis["any"]:
        H.append(f'<p>You sent us sales-to-dealer data for 2025 ({vis["rows"]:,} lines), but <b>not broken down by named dealer</b> &mdash; '
                  f'it arrives as a network total, so we cannot see which of your dealers bought what. '
                  f'Across the network, {len(ANY_2025)} of {N_DB} distributors sent some sales-to-dealer data for 2025; only one sent it by named dealer.</p>')
    else:
        H.append(f'<p>We hold <b>no sales-to-dealer data</b> from you for 2025. We see what we bill to you; what you sell on to each dealer is not visible to us. '
                  f'Across the network, {len(ANY_2025)} of {N_DB} distributors sent any sales-to-dealer data for 2025; you are not one of them.</p>')
    H.append('<div class="callout"><p>This is the same blindness ISZE has about you that you may have about your own dealers: we see what is billed, not what is sold on or serviced.</p></div>')

    # 3. Maintenance parts vs modelled need
    H.append('<h2>Maintenance parts supplied against modelled need</h2>')
    if cap["reliable"]:
        items = []
        for r in cap["reliable"]:
            lab = FAMILY_LABEL.get(r["pms_category"], r["pms_category"])
            items.append((lab, float(r["capture_rate"]) * 100, float(r["capture_rate"]) < 0.5))
        H.append(fig(hbars(items, lambda v: f"{v:.0f}%", label_w=150, value_w=70, maxv=100,
                            title="Share of modelled service need supplied by ISZE, families with a reliable model, 2025"),
                      "Capped at 100% by construction; capture above 100% is withheld as unreliable, not shown as a figure.",
                      "Source: maintenance-parts revenue-capture model, calendar 2025."))
        if cap["overall_capture"] is not None:
            H.append(f'<p>Weighted across the {cap["n_reliable"]} reliable families, supply covers <b>{cap["overall_capture"]:.0f}%</b> of modelled need.</p>')
        if cap["n_unreliable"]:
            H.append(f'<p class="note">{cap["n_unreliable"]} families ({", ".join(cap["unreliable_names"])}) are not shown: the model\'s expected demand '
                      f'is exceeded by what was actually supplied, which means the model is not reliable for those families in your market. We do not show a figure above 100%.</p>')
    else:
        H.append('<p class="note">No family in your market has a reliable modelled-need figure this year &mdash; either there is no verified vehicle-in-service count, '
                  'or supply exceeds every modelled expectation. We are not showing a capture figure here rather than showing one we do not trust.</p>')

    H.append('<div class="sectionbreak"></div>')

    # 4. Genuine vs Best Value
    H.append('<h2>Genuine and Best Value</h2>')
    if gb["n_lines"]:
        H.append(fig(stacked_two([("2025", gb["g25"], "Genuine", gb["b25"], "Best Value"),
                                   ("2024", gb["g24"], "Genuine", gb["b24"], "Best Value")], h=140),
                      "Share of maintenance-parts billing, Genuine (red) against Best Value (grey).",
                      "Source: maintenance-parts pricing analysis, calendar 2024 and 2025."))
        tot25 = gb["g25"] + gb["b25"]
        H.append(f'<p>In 2025, {eur(gb["g25"])} Genuine and {eur(gb["b25"])} Best Value ({eurk(tot25)} together across {gb["n_lines"]} product lines with a reference price).</p>')
    else:
        H.append('<p class="note">No maintenance-parts lines with a reference price recorded for you in this period.</p>')

    # 5. Dealer spread
    H.append('<h2>Spread of parts purchases across your dealers</h2>')
    if db == "ITUK":
        rows = load("dealer_sellout_gps_2025.csv")
        vals = sorted((float(r["total_eur"]) for r in rows if r["distributor_code"] == "ITUK"), reverse=True)
        items = [(f"#{i+1}", v, i < 5) for i, v in enumerate(vals)]
        top10_share = sum(vals[:10]) / sum(vals) * 100
        med = vals[len(vals) // 2]
        H.append(fig(hbars(items[:20], eurk, label_w=50, value_w=90, maxv=nice_max(vals[0] * 1.1),
                            title=f"Parts bought from you by each of your {len(vals)} dealers, 2025, ranked and anonymised (top 20 shown)"),
                      f"Top 10 dealers: {top10_share:.1f}% of the total. Median dealer: {eurk(med)}.",
                      "Source: named-dealer sales records, calendar 2025. Dealer identities withheld on this page."))
    else:
        H.append('<p class="note">We cannot show this: we do not hold named-dealer sales data for you for 2025 (see above). '
                  'Without it, a ranked spread across your dealers cannot be built &mdash; showing one would mean estimating a per-dealer '
                  'figure from a national total, which this review deliberately does not do.</p>')

    # 6. Isuzu Dealer Standards
    H.append('<h2>Isuzu Dealer Standards</h2>')
    if ids:
        H.append(f'<p><b>{ids["n_dealers"]}</b> dealer records are listed for your network in the Isuzu Dealer Standards assessment, of which '
                  f'<b>{ids["n_scored"]}</b> carry a recorded self-assessment score. The remainder are listed without a score, which means the assessment was never carried out for them &mdash; not that they scored zero.</p>')
    else:
        H.append('<p class="note">Your network is not separately represented in the Isuzu Dealer Standards network lists we hold, so no dealer count or score is shown here.</p>')

    H.append("""<div class="question"><div class="q">What would you need to judge each of your dealers?</div>
    <div class="lines"><div></div><div></div><div></div></div></div>""")

    H.append(f'<div class="foot">Figures: ISZE parts billing, maintenance-parts pricing and revenue-capture records, sales-to-dealer submissions and the Isuzu Dealer Standards network lists, all as held by ISZE as of September 2026. '
             f'Anchors: the ISZE data-quality sign-off, then the headline-metrics file, then the single facts sheet. Prepared for {escape(name)} only; no other distributor is named on this page.</div>')
    H.append('</div>')

    body = "\n".join(H)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{escape(name)} &mdash; Isuzu Universe distributor review</title>
<style>{CSS}</style></head><body>{body}</body></html>"""


BANNED = [r"\bcampaign", r"\bAIM\b", r"\bPRISM\b", r"\bDLOD\b", r"\bDLAD\b", r"\bIDS\b", r"\.csv", r"\.json", r"\.md\b",
          r"\.py\b", r"_build", r"internal draft", r"business owner", r"snapshot", r"checks, 0 fail", r"megaprompt",
          r"workspace", r"\bGPS\b", r"\bBVP\b", r"\bIML\b", r"\bITUK\b", r"\bIUK\b", r"\bUMI\b", r"\bUTI\b",
          r"\bAtlas\b", r"\bDon't Lose the Deal\b"]


def scan_banned(text):
    hits = {}
    for b in BANNED:
        found = re.findall(r".{0,30}" + b + r".{0,30}", text, flags=re.I)
        if found:
            hits[b] = found
    return hits


def render_pdf(html_path, pdf_path):
    prof = tempfile.mkdtemp(prefix="chrome_prof_")
    url = "file:///" + html_path.replace("\\", "/")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    "--proxy-server=127.0.0.1:9", "--virtual-time-budget=6000", f"--user-data-dir={prof}",
                    f"--print-to-pdf={pdf_path}", url], check=True, capture_output=True, timeout=60)


def render_png(pdf_path, png_prefix):
    import fitz
    doc = fitz.open(pdf_path)
    paths = []
    for i, pg in enumerate(doc):
        p = f"{png_prefix}_p{i+1}.png"
        pg.get_pixmap(dpi=110).save(p)
        paths.append(p)
    return paths


if __name__ == "__main__":
    all_bans = {}
    results = []
    for db in sorted(GPS_25.keys()):
        name = NAMES.get(db, db.title())
        html = build_page(db)
        fname_base = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
        html_path = os.path.join(OUT_DIR, f"{fname_base}.html")
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        hits = scan_banned(html)
        if hits:
            all_bans[db] = hits
        pdf_path = os.path.join(OUT_DIR, f"{fname_base}.pdf")
        render_pdf(html_path, pdf_path)
        png_paths = render_png(pdf_path, os.path.join(QA_DIR, fname_base))
        results.append((db, name, fname_base, len(png_paths)))
        print("built", db, "->", fname_base, "pages", len(png_paths))

    print("\nBANNED TERM HITS:", len(all_bans))
    for db, hits in all_bans.items():
        print(" ", db, {k: v[:1] for k, v in hits.items()})

    with open(os.path.join(OUT_DIR, "_build_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump([{"code": db, "name": name, "file": fb} for db, name, fb, _ in results], fh, indent=2)
    print("\ndone,", len(results), "distributors built")
