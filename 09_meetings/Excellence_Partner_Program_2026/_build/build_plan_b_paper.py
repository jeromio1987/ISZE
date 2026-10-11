"""Build the Plan B white paper (self-contained HTML, then PDF) from the Markdown source and planb_numbers.json.

Run first:  python 09_meetings/Excellence_Partner_Program_2026/_build/plan_b_numbers.py
Then:       python 09_meetings/Excellence_Partner_Program_2026/_build/build_plan_b_paper.py [--no-pdf]

Inputs : Plan_B_Universe_White_Paper_2026-10-09.md  (placeholders {{CHART:name}})
         planb_numbers.json, planb_basis_fy2026.csv
Outputs: Plan_B_Universe_White_Paper_2026-10-09.html (no external files) and .pdf, plus _qa_planb/ page images
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
STEM = "Plan_B_Universe_White_Paper_2026-10-09"
MD = PACK / f"{STEM}.md"
OUT_HTML = PACK / f"{STEM}.html"
OUT_PDF = PACK / f"{STEM}.pdf"
QA = PACK / "_qa_planb"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

N = json.loads((PACK / "planb_numbers.json").read_text(encoding="utf-8"))
src = MD.read_text(encoding="utf-8")

# ---- the paper may only quote what the numbers file says -------------------------------------------------------------
def must(text):
    assert text in src, f"paper no longer contains: {text}"

must(f"€{N['billed_total']/1e6:.2f}M")                      # 31.78M
must(f"€{N['stock_total']/1e6:.2f}M")                       # 22.38M
must(f"{N['stock_share']*100:.1f}%")                        # 70.4%
must(f"{N['kickback_share_billed']*100:.1f}%")              # 71.7%
must(f"{N['kickback_share_stock']*100:.1f}%")               # 74.1%
must(f"€{N['rebate_total']:,}")                             # 430,030
must(f"€{N['kickback_rebate_credit']:,}")                   # 288,030
must(f"€{N['ituk_credit']:,}")                              # 142,000
must(f"{N['with_file_share']*100:.1f}%")                    # 55.3%
must(f"{N['ituk_share']*100:.1f}%")                         # 21.4%
must(f"€{N['kickback_20pct']:,}")                           # 57,606
assert N["kickback_with_credit_n"] == 8 and N["with_file_n"] == 5 and N["kickback_without_file_n"] == 6
assert N["ireland_credit"] == 0

NAVY, TERRA, PAPER, INK, GREY, LIGHT, GREEN, AMBER, STEEL = "#15233c", "#c0552d", "#f7f4ee", "#222", "#6b7585", "#e4ddd0", "#3f8f6b", "#c98f1f", "#8aa0bd"
eur = lambda v: f"€{v/1e6:.2f}M" if abs(v) >= 1e6 else f"€{v/1e3:,.0f}k" if abs(v) >= 1e4 else f"€{v:,.0f}"
open_svg = lambda w, h: f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI,Arial,sans-serif" role="img">'


def T(x, y, s, sz=13, col=INK, anc="start", wt=400):
    return f'<text x="{x}" y="{y}" font-size="{sz}" fill="{col}" text-anchor="{anc}" font-weight="{wt}">{html.escape(str(s))}</text>'


def fig(inner, title, note):
    return f'<figure class="chart"><div class="ft">{title}</div>{inner}<p class="fnote">{note}</p></figure>'


# ---- charts ------------------------------------------------------------------------------------------------------------
def chart_reach():
    rows = sorted(N["per_distributor"].items(), key=lambda kv: -kv[1]["billed"])
    w, rh, top, x0, x1, mx = 900, 27, 62, 175, 590, 7_000_000
    h = top + rh * len(rows) + 52
    o = open_svg(w, h)
    for g in range(0, 8):
        gx = x0 + (x1 - x0) * g * 1e6 / mx
        o += f'<line x1="{gx:.1f}" y1="{top-8}" x2="{gx:.1f}" y2="{top+rh*len(rows)}" stroke="{LIGHT}"/>' + T(gx, top + rh * len(rows) + 16, "€0" if g == 0 else f"€{g}M", 11, GREY, "middle")
    o += T(x0, 18, "Parts billed FY2026", 12, GREY, "start", 700) + T(650, 18, "Sales-to-dealer file held, FY2026", 12, GREY, "start", 700)
    o += f'<rect x="{x0}" y="30" width="14" height="10" fill="{NAVY}"/>' + T(x0 + 20, 39, "has a kickback", 11) + f'<rect x="{x0+120}" y="30" width="14" height="10" fill="{STEEL}"/>' + T(x0 + 140, 39, "no kickback", 11)
    for i, (name, r) in enumerate(rows):
        y = top + i * rh
        o += T(x0 - 10, y + 17, name, 12.5, INK, "end", 700 if name == "Isuzu Truck UK" else 400)
        o += f'<rect x="{x0}" y="{y+4}" width="{(x1-x0)*r["billed"]/mx:.1f}" height="18" fill="{NAVY if r["kickback"] else STEEL}" rx="2"/>'
        o += T(x0 + (x1 - x0) * r["billed"] / mx + 6, y + 18, eur(r["billed"]), 11.5, INK)
        m = r["months"]
        if m:
            o += f'<rect x="650" y="{y+5}" width="{m*8}" height="16" fill="{GREEN}" rx="2"/>' + T(650 + m * 8 + 6, y + 18, f"{m} of 12 months", 11.5, INK)
        else:
            o += T(650, y + 18, "none", 11.5, TERRA, "start", 700)
    return fig(o + "</svg>", "Who the kickback reaches, and whose sales-to-dealer data we hold", "Source: <code>sales_fact.parquet</code>, <code>billed_vs_std_warranty_fy2026.csv</code>; list of nine kickback distributors from the first white paper. Billed without credit notes, freight and rebate lines.")


def chart_stake():
    rows = sorted([(k, v["credit"]) for k, v in N["per_distributor"].items() if v["kickback"]], key=lambda kv: -kv[1])
    w, rh, top, x0, x1, mx = 900, 29, 40, 175, 700, 20_000
    h = top + rh * len(rows) + 56
    o = open_svg(w, h)
    for g in range(0, 5):
        gx = x0 + (x1 - x0) * g * 5000 / mx
        o += f'<line x1="{gx:.1f}" y1="{top-6}" x2="{gx:.1f}" y2="{top+rh*len(rows)}" stroke="{LIGHT}"/>' + T(gx, top + rh * len(rows) + 16, "€0" if g == 0 else f"€{g*5}k", 11, GREY, "middle")
    for i, (name, credit) in enumerate(rows):
        y = top + i * rh
        stake = credit * 0.2
        o += T(x0 - 10, y + 18, name, 12.5, INK, "end")
        if credit:
            o += f'<rect x="{x0}" y="{y+4}" width="{(x1-x0)*stake/mx:.1f}" height="19" fill="{TERRA}" rx="2"/>' + T(x0 + (x1 - x0) * stake / mx + 6, y + 18, f"{eur(stake)}  (of a {eur(credit)} credit)", 11.5)
        else:
            o += T(x0, y + 18, "no credit line in FY2026 billing", 11.5, GREY)
    o += T(x0, top + rh * len(rows) + 40, f"All together: {eur(N['kickback_20pct'])} a year if the data share is 20%. The first paper's {eur(N['all_credit_20pct'])} counted Isuzu Truck UK's credit too.", 12, NAVY, "start", 700)
    return fig(o + "</svg>", "What the data condition puts at risk for each kickback distributor (20% of the FY2026 credit)", "Source: rebate credit lines in <code>sales_fact.parquet</code>. The 20% is Jerome's confirmed figure; the contract text is not in the workspace.")


def chart_build():
    # (group, technically verified, implemented, total) - progress.json on main, written 2026-10-07T06:07:42Z
    groups = [("Foundation", 7, 1, 8), ("Pricing maths", 8, 0, 8), ("Data handling", 8, 0, 8), ("Review screens", 8, 0, 8), ("Usability", 8, 0, 8),
              ("Case records", 8, 0, 8), ("Competitor prices", 8, 0, 8), ("Product range", 8, 0, 8), ("Links to IDS, fleet, tenders", 8, 0, 8),
              ("Access and security", 8, 0, 8), ("Shared running service", 8, 0, 8), ("Checks, then tests with real people", 3, 0, 8)]
    assert sum(g[1] for g in groups) == 90 and sum(g[2] for g in groups) == 1 and sum(g[3] for g in groups) == 96
    w, rh, top, x0, x1 = 900, 25, 12, 255, 600
    h = top + rh * len(groups) + 66
    o = open_svg(w, h)
    for i, (n, v, im, t) in enumerate(groups):
        y = top + i * rh
        o += T(x0 - 10, y + 16, n, 12.5, INK, "end")
        o += f'<rect x="{x0}" y="{y+3}" width="{(x1-x0)}" height="17" fill="{LIGHT}" rx="2"/><rect x="{x0}" y="{y+3}" width="{(x1-x0)*v/t:.1f}" height="17" fill="{GREEN}" rx="2"/>'
        if im:
            o += f'<rect x="{x0+(x1-x0)*v/t:.1f}" y="{y+3}" width="{(x1-x0)*im/t:.1f}" height="17" fill="{AMBER}" rx="2"/>'
        o += T(x1 + 10, y + 16, f"{v + im} of {t}" + (" (1 implemented)" if im else ""), 12, INK, "start", 700)
    yy = top + rh * len(groups) + 20
    o += T(x0, yy, "90 of 96 technically verified, 1 implemented, 5 not started (the tests with real people).", 12, NAVY, "start", 700)
    o += T(x0, yy + 20, "Technically verified: a named check was run on made-up data. It is not acceptance by a person.", 12, GREY)
    return fig(o + "</svg>", "Universe build status, 7 October 2026", "Source: <code>05_AIM_Universe/progress/progress.json</code> on the main branch, written 7 October 2026.")


def chart_cost():
    rows = [("Rebates paid today", 430_030, STEEL, "€430k"), ("Universe route, new cash", 0, GREEN, "€0"),
            ("Discount, small hybrid, year 3", 290_000, AMBER, "€0.29M"), ("Discount as the deck proposes, year 3", 930_000, TERRA, "€0.93M")]
    w, rh, top, x0, x1, mx = 900, 44, 14, 270, 780, 1_000_000
    h = top + rh * len(rows) + 54
    o = open_svg(w, h)
    for g in range(0, 5):
        gx = x0 + (x1 - x0) * g * 250_000 / mx
        o += f'<line x1="{gx:.1f}" y1="{top-6}" x2="{gx:.1f}" y2="{top+rh*len(rows)}" stroke="{LIGHT}"/>' + T(gx, top + rh * len(rows) + 16, "€0" if g == 0 else f"€{g*250}k", 11, GREY, "middle")
    for i, (n, v, c, lab) in enumerate(rows):
        y = top + i * rh
        o += T(x0 - 10, y + 25, n, 13, INK, "end", 700) + f'<rect x="{x0}" y="{y+8}" width="{max((x1-x0)*v/mx,3):.1f}" height="26" fill="{c}" rx="2"/>' + T(x0 + max((x1 - x0) * v / mx, 3) + 8, y + 27, lab, 13, INK, "start", 700)
    o += T(x0, top + rh * len(rows) + 40, "Cash a year, on the same 19 distributors. Internal time is not counted in any bar.", 12, GREY)
    return fig(o + "</svg>", "Cash cost per year: the Universe route against the discount", "Source: rebates from billing (<code>sales_fact.parquet</code>); discount designs from the first white paper and its ROI model, carried and not recalculated.")


def chart_funnel():
    dist = [("Accepts the opening", 75), ("Uses the review inside", 45), ("Picks a case with an owner", 50), ("Shares detail beyond today's report", 35),
            ("Uses it to develop its dealers", 40), ("Co-funds participation", 25), ("Joins as designed", 55)]
    deal = [("Accepts the first review", 55), ("Corrects the reading", 70), ("Uses its own IDS profile", 65), ("Returns for a second task", 30),
            ("Shares more than a correction", 20), ("Joins as designed", 45)]
    w, rh, top = 900, 29, 34
    h = top + rh * max(len(dist), len(deal)) + 44
    o = open_svg(w, h)
    for off, ttl, rows, col in ((0, "Distributor", dist, NAVY), (455, "Dealer", deal, TERRA)):
        o += T(off + 10, 20, ttl, 14, col, "start", 700)
        for i, (n, v) in enumerate(rows):
            y = top + i * rh
            last = i == len(rows) - 1
            o += T(off + 10, y + 18, n, 11.5, INK, "start", 700 if last else 400)
            bx = off + 195
            o += f'<rect x="{bx}" y="{y+5}" width="200" height="16" fill="{LIGHT}" rx="2"/><rect x="{bx}" y="{y+5}" width="{2*v}" height="16" fill="{col}" rx="2"/>' + T(bx + 206, y + 18, v, 12, INK, "start", 700)
    o += T(10, top + rh * len(dist) + 26, "Scores out of 100 are Universe's own judgement on its own design. They are not measurements.", 12, GREY)
    return fig(o + "</svg>", "How likely each step is, by Universe's own score", "Source: <code>ISUZU_UNIVERSE_3_0_2026-09-23</code>, chapter 8.")


def chart_timeline():
    months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    w, x0, cw, top = 900, 330, 46, 44
    rows = [("Decision on the route; Move 1 audit", 0, 2, AMBER), ("Contract, Japan, legal review", 1, 3, AMBER), ("Intake, checks, receipts (P01 to P03)", 2, 5, NAVY),
            ("Classification version; prepared views", 2, 5, NAVY), ("Trial with 3 or 4 distributors", 3, 6, GREEN), ("Written rules final", 5, 6, AMBER),
            ("Route starts, FY2028", 6, 7, TERRA), ("Billing match, check, return (P04 to P06)", 4, 9, NAVY),
            ("First quarterly check", 8, 9, TERRA), ("Review: carry on, narrow, or discount", 11, 12, GREY)]
    rh = 29
    h = top + rh * len(rows) + 34
    o = open_svg(w, h)
    for i, m in enumerate(months):
        gx = x0 + i * cw
        o += f'<line x1="{gx}" y1="{top-8}" x2="{gx}" y2="{top+rh*len(rows)}" stroke="{LIGHT}"/>' + T(gx + cw / 2, top - 14, m, 11.5, GREY, "middle")
    o += T(x0, top - 30, "2026", 11.5, NAVY, "start", 700) + T(x0 + 3 * cw, top - 30, "2027", 11.5, NAVY, "start", 700)
    for i, (n, a, b, c) in enumerate(rows):
        y = top + i * rh
        o += T(x0 - 10, y + 18, n, 11.5, INK, "end") + f'<rect x="{x0+a*cw}" y="{y+5}" width="{(b-a)*cw-3}" height="17" fill="{c}" rx="3"/>'
    return fig(o + "</svg>", "From decision to first quarterly check", "Proposal. Dates follow the first white paper and the technical specification; they are not agreed.")


CHARTS = {"reach": chart_reach, "stake": chart_stake, "build": chart_build, "cost": chart_cost, "funnel": chart_funnel, "timeline": chart_timeline}


# ---- tiny Markdown -----------------------------------------------------------------------------------------------------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*\[([MIAPU])\]\*\*", lambda m: f'<span class="tag t{m.group(1)}">{m.group(1)}</span>', s)
    s = re.sub(r"\*\*\[([MIAPU])\]/\[([MIAPU])\]\*\*", lambda m: f'<span class="tag t{m.group(1)}">{m.group(1)}</span><span class="tag t{m.group(2)}">{m.group(2)}</span>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    return s


def render(md):
    out, lines, i = [], md.split("\n"), 0
    slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = re.match(r"\{\{CHART:(\w+)\}\}", ln.strip())
        if m:
            out.append(CHARTS[m.group(1)]())
            i += 1
            continue
        if ln.startswith("---"):
            out.append("<hr>")
            i += 1
            continue
        h = re.match(r"(#{1,3}) (.*)", ln)
        if h:
            lvl = len(h.group(1))
            out.append(f'<h{lvl} id="{slug(h.group(2))}">{inline(h.group(2))}</h{lvl}>')
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            al = [("r" if c.endswith(":") else "") for c in rows[1]]
            body = rows[2:]
            t = "<table><thead><tr>" + "".join(f'<th class="{al[j]}">{inline(c)}</th>' for j, c in enumerate(rows[0])) + "</tr></thead><tbody>"
            for r in body:
                t += "<tr>" + "".join(f'<td class="{al[j] if j < len(al) else ""}">{inline(c)}</td>' for j, c in enumerate(r)) + "</tr>"
            out.append(t + "</tbody></table>")
            continue
        if re.match(r"\d+\. ", ln) or ln.startswith("- "):
            ordered = bool(re.match(r"\d+\. ", ln))
            items = []
            while i < len(lines) and (re.match(r"\d+\. ", lines[i]) or lines[i].startswith("- ") or lines[i].startswith("   ")):
                if lines[i].startswith("   "):
                    items[-1] += "<br>" + inline(lines[i].strip())
                else:
                    items.append(inline(re.sub(r"^(\d+\.|-) ", "", lines[i])))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
            continue
        para = [ln]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||\d+\. |- |---|\{\{)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


CSS = f"""
:root{{--navy:{NAVY};--terra:{TERRA};--paper:{PAPER};--ink:{INK};--grey:{GREY};--line:{LIGHT}}}
*{{box-sizing:border-box}}
html{{background:#fff}}
body{{margin:0 auto;max-width:880px;padding:34px 26px 70px;font:15.5px/1.58 "Segoe UI",Arial,sans-serif;color:var(--ink);background:#fff}}
h1{{font:700 34px/1.18 Georgia,serif;color:var(--navy);margin:6px 0 10px;letter-spacing:-.2px}}
h2{{font:700 23px/1.25 Georgia,serif;color:var(--navy);margin:34px 0 8px;padding-top:14px;border-top:3px solid var(--terra);break-after:avoid}}
h3+table,h3+figure{{break-before:avoid}}
h3{{font:700 17px/1.3 Georgia,serif;color:var(--navy);margin:22px 0 6px;break-after:avoid}}
p{{margin:8px 0}}
hr{{border:0;border-top:1px solid var(--line);margin:18px 0}}
code{{font:12.5px Consolas,monospace;background:#f1ede4;padding:1px 4px;border-radius:3px}}
table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px}}
p:has(+table),p:has(+figure){{break-after:avoid}}
th{{background:var(--navy);color:var(--paper);text-align:left;padding:7px 9px;font-weight:600}}
td{{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:nth-child(even) td{{background:#faf8f3}}
th.r,td.r{{text-align:right}}
ul,ol{{margin:8px 0 8px 22px;padding:0}} li{{margin:4px 0}}
.tag{{display:inline-block;font:700 10.5px/1 Consolas,monospace;padding:2px 5px;border-radius:3px;color:#fff;vertical-align:1px;margin-right:2px}}
.tM{{background:{GREEN}}}.tI{{background:{STEEL}}}.tA{{background:{AMBER}}}.tP{{background:{NAVY}}}.tU{{background:{TERRA}}}
figure.chart{{margin:18px 0;padding:14px 16px 8px;border:1px solid var(--line);border-radius:8px;background:#fff;break-inside:avoid}}
figure.chart svg{{width:100%;height:auto;display:block}}
.ft{{font:700 15px Georgia,serif;color:var(--navy);margin-bottom:6px}}
.fnote{{font-size:11.5px;color:var(--grey);margin:4px 0 4px}}
.cover{{border-bottom:4px solid var(--terra);padding-bottom:14px;margin-bottom:10px}}
@media print{{
  @page{{size:A4;margin:15mm 14mm 16mm}}
  body{{max-width:none;padding:0;font-size:10.8pt}}
  h1{{font-size:26pt}} h2{{font-size:16pt;margin-top:22px}} h3{{font-size:12pt}}
  table{{font-size:9.4pt}} figure.chart{{padding:8px 10px 4px}} .fnote{{font-size:8pt}}
  tr{{break-inside:avoid}}
}}
"""

body = render(src)
page = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Isuzu Universe without a discount</title><style>{CSS}</style></head><body>{body}</body></html>'
OUT_HTML.write_text(page, encoding="utf-8")
print(OUT_HTML, f"{OUT_HTML.stat().st_size/1e3:.0f} KB")

if "--no-pdf" in sys.argv:
    sys.exit(0)

import tempfile

try:
    OUT_PDF.unlink(missing_ok=True)  # a silent Chrome no-op must not leave a stale PDF behind
except PermissionError:  # the old PDF is open in a viewer: write beside it, never overwrite silently
    OUT_PDF = PACK / f"{STEM}.NEW.pdf"
    OUT_PDF.unlink(missing_ok=True)
    print("old PDF is open in a viewer; writing", OUT_PDF.name)
profile = tempfile.mkdtemp(prefix="chrome_planb_")  # a fresh profile: with the default one a running Chrome swallows the print
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={profile}", f"--print-to-pdf={OUT_PDF}", OUT_HTML.as_uri()],
               check=True, capture_output=True, timeout=120)
assert OUT_PDF.exists(), "Chrome wrote no PDF"
import fitz

QA.mkdir(exist_ok=True)
for f in QA.glob("*.png"):
    f.unlink()
doc = fitz.open(OUT_PDF)
for n, pg in enumerate(doc, 1):
    pg.get_pixmap(dpi=80).save(QA / f"p{n:02d}.png")
print(OUT_PDF, f"{doc.page_count} pages")
