# -*- coding: utf-8 -*-
r"""Shared builder for the Universe 3.0 papers.

Renders a markdown source to house-styled HTML, prints it with headless Chrome, then stamps the
running header, the footer and the bookmark tree, and checks the PDF page by page.

Used by build.py (the main paper) and build_annex.py (the detail annex).
"""
import os
import re
import subprocess
import sys
import html as H

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

NAVY = (0.082, 0.137, 0.235)
GREY = (0.36, 0.39, 0.45)
TERR = (0.753, 0.333, 0.176)
CHARCOAL = (0.141, 0.157, 0.173)      # #24282C, the 80-pager's page colour

sys.stdout.reconfigure(encoding="utf-8")


def inline(t):
    t = H.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def headings(src):
    out, in_code = [], False
    for ln in src.split("\n"):
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            out.append((len(m.group(1)), re.sub(r"[`*]", "", m.group(2)).strip()))
    return out


def _est_height_mm(el):
    """Rough printed height of one rendered element, in millimetres.

    Only used to stop a keep block growing taller than a page; being approximate is fine,
    because the block is checked against a limit well inside the page height.
    """
    if el.startswith("<figure"):
        return 85.0                      # a full-width chart plus its caption (measured 70-103 mm)
    if el.startswith("<table"):
        rows = el.count("<tr>")
        # A table of nine rows or fewer is kept unbreakable by CSS, so the estimate has to match
        # what CSS will actually do. A longer table flows across pages; estimate it as one that
        # can break, so wrapping it in an unbreakable block cannot force a blank page.
        if rows > 9:
            return 34.0
        return 6.0 + rows * 5.6
    text = re.sub(r"<[^>]+>", " ", el)
    text = re.sub(r"\s+", " ", text).strip()
    bullets = el.count("<li>")
    if bullets:
        return 6.0 + bullets * 5.0
    if el.startswith("<h"):
        return 9.0
    per_line = 108                       # about 108 characters per line at 10.1pt on 180mm
    return max(1, -(-len(text) // per_line)) * 4.6 + 2.5


def keep_together(els, max_block_mm=165.0, fill_mm=225.0):
    """Wrap a heading and the material under it in one unbreakable block.

    A heading left alone at the foot of a page, and a table or figure parted from the sentence
    that introduces it, are the layout faults this prevents. A level-2 chapter heading is
    wrapped with its first paragraph or figure too, so the heading cannot be the last thing on a
    page. A block is never allowed to grow beyond max_block_mm, because an over-tall unbreakable
    block forces a near-empty page. Returns (heading-text-or-None, html) pairs so the caller can
    insert page breaks.
    """
    out, i = [], 0
    nxt_flow = re.compile(r"^(<p>|<figure>|<table>|<ul>|<ol>|<blockquote>)")

    def wrap(items, plain):
        # A table long enough to break across pages carries class tbl-flow, and CSS gives it
        # page-break-inside:auto. Wrapping it in an unbreakable div would cap it at one page and
        # can push it onto a fresh sheet, leaving the previous page blank. So a flowing table is
        # emitted bare and its companions get their own unbreakable blocks. Every element is
        # emitted exactly once.
        if any(re.match(r'^<table class="tbl-flow">', x) for x in items):
            html = []
            for x in items:
                if re.match(r'^<table class="tbl-flow">', x):
                    html.append(x)
                else:
                    html.append('<div class="keep">' + x + "</div>")
            return (plain, "\n".join(html))
        return (plain, '<div class="keep">' + "\n".join(items) + "</div>")

    while i < len(els):
        e = els[i]
        m = re.match(r"^<h([234])>(.*?)</h\1>$", e)
        if not m:
            # a paragraph and the table it introduces must not be parted by a page break
            if (re.match(r"^<(p|ul|ol|blockquote)>", e) and i + 1 < len(els)
                    and re.match(r"^<table>", els[i + 1])):
                inner = [e, els[i + 1]]
                i += 2
                # keep a short closing paragraph with the table it comments on
                while (i < len(els) and re.match(r"^<p>", els[i])
                       and _est_height_mm("".join(inner)) + _est_height_mm(els[i])
                       <= max_block_mm * 0.90
                       and len([x for x in inner if x.startswith("<p")]) < 2):
                    inner.append(els[i])
                    i += 1
                out.append(wrap(inner, None))
                continue
            out.append((None, e))
            i += 1
            continue
        plain = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if i + 1 < len(els) and nxt_flow.match(els[i + 1]):
            inner = [e, els[i + 1]]
            used = _est_height_mm(e) + _est_height_mm(els[i + 1])
            is_figure = els[i + 1].startswith("<figure")
            i += 2
            # take one more short paragraph, so a heading is never the last thing on a page
            while (i < len(els) and re.match(r"^<p>", els[i])
                   and used + _est_height_mm(els[i]) <= max_block_mm * 0.75
                   and len([x for x in inner if x.startswith("<p")]) < 2):
                inner.append(els[i])
                used += _est_height_mm(els[i])
                i += 1
            # and the table those sentences introduce, so it is never parted from them
            if (i < len(els) and re.match(r"^<table>", els[i])
                    and re.match(r"^<p>", inner[-1])
                    and used + _est_height_mm(els[i]) <= max_block_mm):
                inner.append(els[i])
                i += 1
            # a chapter that opens with a figure keeps the next sub-heading and its paragraph
            # too, so the page carries the chart and the first idea rather than the chart alone
            if is_figure and m.group(1) == "2" and i + 1 < len(els):
                if (re.match(r"^<h[34]>", els[i]) and re.match(r"^<p>", els[i + 1])
                        and used + _est_height_mm(els[i]) + _est_height_mm(els[i + 1])
                        <= max_block_mm * 0.90):
                    inner.extend([els[i], els[i + 1]])
                    i += 2
            out.append(wrap(inner, plain))
            continue
        out.append((plain, e))
        i += 1
    return out


def markdown_to_html(src, figdir, figcaps, breaks=()):
    lines = src.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue

        m = re.match(r"^\[\[FIG(\d+)\]\]\s*$", ln.strip())
        if m:
            n = int(m.group(1))
            if os.path.isdir(figdir):
                for f in sorted(os.listdir(figdir)):
                    if f.startswith("f%02d_" % n):
                        out.append(f'<figure><img src="figures/{f}" alt="Figure {n}">'
                                   f'<figcaption><b>Figure {n}.</b> {figcaps.get(n, "")}'
                                   f'</figcaption></figure>')
            i += 1
            continue

        if ln.strip() == "[[PAGEBREAK]]":
            out.append('<div class="pagebreak"></div>')
            i += 1
            continue

        if ln.strip() == "[[READING_GUIDE]]":
            out.append('<div id="reading-guide-slot"></div>')
            i += 1
            continue

        if ln.lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            rows = [[c.strip() for c in r.strip("|").split("|")] for r in block]
            rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)]
            head, body = rows[0], rows[1:]
            # one element for the whole table, so nothing can break the block it belongs to
            tbl = ["<table><thead><tr>"
                   + "".join(f"<th>{inline(c)}</th>" for c in head)
                   + "</tr></thead><tbody>"]
            for r in body:
                tbl.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            tbl.append("</tbody></table>")
            out.append("".join(tbl))
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            out.append(f"<h{lvl}>{inline(txt)}</h{lvl}>")
            i += 1
            continue

        if re.match(r"^---+\s*$", ln):
            out.append("<hr>")
            i += 1
            continue

        if ln.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append("<blockquote>" + "<br>".join(inline(b) for b in buf if b) + "</blockquote>")
            continue

        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            tag = "ol" if re.match(r"^\s*\d+\.\s+", ln) else "ul"
            items = []
            while i < len(lines):
                if re.match(r"^\s*(?:[-*]|\d+\.)\s+", lines[i]):
                    items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i]).strip())
                    i += 1
                elif (items and lines[i].strip() and lines[i].startswith(("  ", "\t"))
                      and not re.match(r"^\s*(?:[-*]|\d+\.)\s+", lines[i])):
                    items[-1] += " " + lines[i].strip()      # a wrapped continuation line
                    i += 1
                else:
                    break
            out.append(f"<{tag}>"
                       + "".join(f"<li>{inline(x)}</li>" for x in items)
                       + f"</{tag}>")
            continue

        buf = [ln]
        i += 1
        while (i < len(lines) and lines[i].strip()
               and not re.match(r"^(#{1,4}\s|---|\s*[-*]\s|\s*\d+\.\s|>)", lines[i])
               and not lines[i].lstrip().startswith("|")
               and not lines[i].strip().startswith("[[FIG")):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(b.strip() for b in buf)) + "</p>")

    want = {b.strip() for b in breaks}
    html = []
    for plain, el in keep_together(out):
        if plain in want:
            # a rule sitting immediately before a forced chapter break is stranded on the page
            # by itself: the break moves the chapter, and the rule is left behind on a blank sheet
            while html and html[-1] in ("<hr>", '<div class="pagebreak"></div>'):
                html.pop()
            html.append('<div class="chapter-start"></div>')
        # mark a long table so it may flow across pages with its header repeated
        el = el.replace("<table>", '<table class="tbl-flow">') if el.count("<tr>") > 9 else el
        html.append(el)
    return "\n".join(html)


CSS = """
@page { size: A4; margin: 19mm 15mm 16mm 15mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10.1pt/1.5 "Segoe UI", Helvetica, Arial, sans-serif; color:#222; margin:0; }
h1,h2,h3,h4 { font-family: Georgia, "Times New Roman", serif; color:#15233c; }
h1 { font-size: 24pt; line-height:1.14; margin: 0 0 5mm 0; }
h2 { font-size: 15pt; margin: 9mm 0 3mm; padding-bottom: 1.6mm;
     border-bottom: 1.8pt solid #15233c; page-break-after: avoid; }
h3 { font-size: 11.8pt; margin: 6mm 0 2mm; color:#1a2b4a; page-break-after: avoid; }
h4 { font-size: 10.4pt; margin: 4.5mm 0 1.5mm; color:#c0552d; page-break-after: avoid; }
p { margin: 0 0 2.5mm; }
hr { border:0; border-top:1px solid #d8d2c8; margin: 5mm 0; }
strong { color:#15233c; }
em { color:#1a2b4a; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt;
       background:#f2efe9; padding: 0 .6mm; }
table { width:100%; border-collapse: collapse; font-size: 8.9pt; margin: 2mm 0 4mm;
        page-break-inside: avoid; }
/* a long table may flow across pages, with its header repeated and its rows intact */
table.tbl-flow { page-break-inside: auto; }
table.tbl-flow thead { display: table-header-group; }
table.tbl-flow tr { page-break-inside: avoid; }
th { background:#15233c; color:#f7f4ee; text-align:left; padding: 1.6mm 2mm;
     font-weight:600; font-size:8.5pt; }
td { padding: 1.4mm 2mm; border-bottom: .6pt solid #ddd7cc; vertical-align: top; }
tr:nth-child(even) td { background:#faf8f3; }
blockquote { margin: 3mm 0; padding: 2.6mm 3.6mm; background:#f4f1ea;
             border-left: 2.8pt solid #c0552d; font-style: italic; }
ul, ol { margin: 0 0 3mm 5mm; padding:0; }
li { margin-bottom: 1.2mm; }
figure { margin: 4mm 0 5mm; page-break-inside: avoid; text-align:center; }
figure img { width: 100%; max-width: 178mm; height:auto; border: 1px solid #e6e1d7; }
figcaption { font-size: 8.2pt; color:#5b6472; text-align:left; margin-top: 1.8mm;
            line-height:1.42; }
figcaption b { color:#15233c; }
.pagebreak { page-break-after: always; height:0; }
.keep { page-break-inside: avoid; break-inside: avoid; }
/* never leave a heading's paragraph as a two-line orphan at the foot of a page */
p { orphans: 3; widows: 2; }
li, td { orphans: 2; widows: 2; }
/* a chapter opens a fresh page */
.chapter-start { page-break-before: always; height:0; }
/* the reading guide: chapter, pages, what it decides */
.guide { width:100%; border-collapse: collapse; font-size: 9.2pt; margin: 3mm 0 4mm; }
/* keep the page range on one line: "12-15", never "12-" and then "15" */
.guide td.pg { white-space: nowrap; }

/* ------------------------------------------------------------------ charcoal pack
   Used only by the critique pack that goes to the other tool: the 80-pager's own palette. */
.charcoal { background:#24282C; }
.charcoal body { background:#24282C; color:#E0E5E8;
  font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; }
.charcoal .sheet { background:#24282C; }
/* Chrome will not paint an element's background over a printed page unless the document asks it
   to; without this the whole charcoal pack prints white with pale text on it. */
@media print {
  html.charcoal, html.charcoal body { background:#24282C !important; }
}
.charcoal h1, .charcoal h2, .charcoal h3, .charcoal h4 {
  font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; color:#F5F6F7; }.charcoal h2 { border-bottom: 1.8pt solid #D71920; }
.charcoal h3 { color:#F5F6F7; }
.charcoal h4 { color:#FF686D; }
.charcoal p, .charcoal li, .charcoal td { color:#E0E5E8; }
.charcoal strong { color:#F5F6F7; }
.charcoal em { color:#C2C8CC; }
.charcoal a { color:#FF686D; }
.charcoal hr { border-top:1px solid #48525B; }
.charcoal code { background:#30363B; color:#F5F6F7; }
.charcoal table { color:#E0E5E8; }
.charcoal th { background:#D71920; color:#F5F6F7; }
.charcoal td { border-bottom: .6pt solid #48525B; }
.charcoal tr:nth-child(even) td { background:#2A3035; }
.charcoal blockquote { background:#30363B; border-left:2.8pt solid #D71920; color:#E0E5E8; }
.charcoal figcaption { color:#C2C8CC; }
.charcoal figcaption b { color:#FF686D; }
.charcoal .keep { }
.charcoal .cover-page { background:#24282C; }
.charcoal .cover-page .org { color:#F5F6F7; }
.charcoal .cover-page .family { color:#FF686D; }
.charcoal .cover-page .rule { border-top:3pt solid #D71920; }
.charcoal .cover-page .title { color:#F5F6F7; }
.charcoal .cover-page .strap { color:#C2C8CC; }
.charcoal .cover-page .focus { border-top:1pt solid #48525B; }
.charcoal .cover-page .focus .h { color:#A3ADB3; }
.charcoal .cover-page .focus li { color:#E0E5E8; }
.charcoal .cover-page .meta { border-top:2.4pt solid #D71920; color:#F5F6F7; }
.charcoal .cover-page .meta2 { color:#A3ADB3; }
.charcoal .closing { border-top:1px solid #48525B; color:#A3ADB3; }
.charcoal .guide th { background:#30363B; color:#FF686D; }
.charcoal .guide td { border-bottom:.6pt solid #3C4348; }
.charcoal .guide tr:nth-child(even) td { background:#282E33; }
.cover-page { height: 252mm; display:flex; flex-direction:column; page-break-after: always;
              padding-top: 3mm; }
.cover-page .org { font-size: 10.5pt; letter-spacing:.30em; text-transform:uppercase;
                   color:#15233c; font-weight:600; }
.cover-page .family { font-size: 12.5pt; letter-spacing:.40em; text-transform:uppercase;
                      color:#c0552d; margin-top:3mm; font-weight:700; }
.cover-page .rule { border-top: 3pt solid #15233c; margin: 6mm 0 11mm; }
.cover-page .title { font-family: Georgia, serif; font-size: 50pt; line-height:1.02;
                     color:#15233c; margin:0; }
.cover-page .strap { font-family: Georgia, serif; font-size: 16pt; line-height:1.45;
                     color:#1a2b4a; margin: 7mm 0 0; max-width: 152mm; }
.cover-page .grow { flex:1; }
.cover-page .focus { border-top:1pt solid #d8d2c8; padding-top: 5mm; }
.cover-page .focus .h { font-size: 8.4pt; letter-spacing:.20em; text-transform:uppercase;
                        color:#5b6472; margin-bottom: 3mm; }
.cover-page .focus li { font-size: 11pt; color:#15233c; margin-bottom: 2.4mm;
                        font-family: Georgia, serif; }
.cover-page .meta { border-top: 2.4pt solid #c0552d; margin-top: 7mm; padding-top: 4mm;
                    font-size: 9.6pt; color:#15233c; font-weight:600; letter-spacing:.10em;
                    text-transform:uppercase; }
.cover-page .meta2 { font-size: 8.4pt; color:#5b6472; margin-top: 2mm; letter-spacing:.12em;
                     text-transform:uppercase; }
"""


def cover_html(cl):
    fig = ""
    if cl.get("figure"):
        fig = (f'<div style="margin-top:9mm"><img src="figures/{cl["figure"]}" '
               f'style="width:100%;border:1px solid #e6e1d7"></div>'
               f'<div style="font-size:8.4pt;color:#5b6472;margin-top:3mm;line-height:1.45">'
               f'{cl.get("figure_caption", "")}</div>')
    focus = "".join(f"<li>{x}</li>" for x in cl.get("focus", []))
    return f"""
<div class="cover-page">
  <div class="org">{cl.get('org', 'ISZE / Parts Europe')}</div>
  <div class="family">{cl.get('family', 'Commercial Vision')}</div>
  <div class="rule"></div>
  <div class="title">{cl.get('title', 'Universe 3.0')}</div>
  <div class="strap">{cl.get('strap', '')}</div>
  {fig}
  <div class="grow"></div>
  <div class="focus">
    <div class="h">{cl.get('focus_head', 'What this edition settles')}</div>
    <ul style="list-style:none;margin:0;padding:0">{focus}</ul>
  </div>
  <div class="meta">{cl.get('meta', '')}</div>
  <div class="meta2">{cl.get('meta2', '')}</div>
</div>
"""


def guide_table(rows, head=("Chapter", "Pages", "What it decides")):
    """The reading-guide table. rows = [(chapter title, page range, one-line purpose)]."""
    th = "".join(f"<th>{inline(h)}</th>" for h in head)
    trs = "".join(
        "<tr>" + f"<td>{inline(a)}</td>"
        + f'<td class="pg">{inline(b)}</td>'
        + f"<td>{inline(c)}</td>" + "</tr>"
        for a, b, c in rows)
    return f'<table class="guide"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def heading_pages(doc, hs):
    """Map every heading to the 0-based page it first appears on.

    Matched on rendered heading spans, not on raw page text: once a reading guide lists the
    chapter titles, the plain-text search finds every chapter on the guide page.
    """
    n = doc.page_count
    # page -> the heading-like lines rendered on it
    rendered = []
    for i in range(n):
        lines = []
        for blk in doc[i].get_text("dict")["blocks"]:
            for line in blk.get("lines", []):
                for sp in line["spans"]:
                    face = ("Georgia" in sp["font"] or "Times" in sp["font"]
                            or "Arial" in sp["font"] or "Helvetica" in sp["font"])
                    if face and sp["text"].strip() and sp["size"] >= 10.4:
                        lines.append(sp["text"].strip())
        rendered.append(" \u00b7 ".join(lines))

    def norm(t):
        return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()

    page_of = {}
    for lvl, text in hs:
        needle = norm(text)[:44]
        if not needle:
            continue
        # start at page 2: page 1 is the cover, and its strapline or focus bullets can repeat a
        # heading's exact wording, which would pull the bookmark onto the cover
        for i in range(1, n):
            if needle in norm(rendered[i]):
                page_of[text] = i
                break
    return page_of


def build(md, html_out, pdf_out, qa_dir, title, cover, figdir, figcaps,
          footer, closing="", theme="navy", chapters_fresh_page=False,
          reading_guide=None, guide_heading="", guide_intro="",
          guide_head=("Chapter", "Pages", "What it decides"), layout_qa=True):
    """Build one document. Returns the QA result dict.

    theme               "navy" (house palette) or "charcoal" (the 80-pager's own look)
    chapters_fresh_page put every level-2 heading on a fresh page; when layout_qa is on, only
                        the chapters that would otherwise start low on a full page get one
    reading_guide       list of (chapter title, one-line purpose). A guide page is rendered
                        near the front with the real page numbers, decided in a second pass.
    layout_qa           measure the five layout faults on the rendered PDF and return them
    """
    import fitz
    import layoutqa

    src = open(md, encoding="utf-8").read()
    hs = headings(src)

    def body_with(breaks):
        return markdown_to_html(src, figdir, figcaps, breaks=breaks)

    def assemble(body, rows=None):
        guide_html = ""
        if reading_guide is not None and rows is not None:
            head = f'<h2>{inline(guide_heading)}</h2>\n' if guide_heading else ""
            guide_html = (head
                          + (f"<p>{inline(guide_intro)}</p>\n" if guide_intro else "")
                          + guide_table(rows, guide_head) + "\n")
        body = body.replace('<div id="reading-guide-slot"></div>', guide_html)
        return f"""<!DOCTYPE html>
<html lang="en" class="{theme}"><head><meta charset="utf-8">
<title>{title}</title>
<style>{CSS}</style></head><body>
{cover_html(cover)}
{body}
{closing}
</body></html>"""

    def render(html, tag):
        open(html_out, "w", encoding="utf-8").write(html)
        raw = os.path.join(os.path.dirname(html_out), "_raw_" + tag + "_" +
                           os.path.basename(pdf_out))
        uri = "file:///" + html_out.replace("\\", "/")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--print-to-pdf=" + raw, "--virtual-time-budget=12000", uri],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=300)
        return raw

    # The guide is inserted before the breaks are decided, because its own height moves the
    # pagination. The placeholder rows have the final width, so the page positions found here are
    # the page positions of the finished document. Every pass below uses the same guide.
    stub = [(t, "00-00", p) for t, p in reading_guide] if reading_guide is not None else None

    def paginated(html_tag, with_breaks):
        # Renders the body with the guide in place; `with_breaks` is spliced in as the break list.
        return assemble(body_with(with_breaks), stub)

    breaks = []
    if chapters_fresh_page:
        if layout_qa:
            # The rule is not a fixed point: adding a break moves the headings after it, so the
            # answer to "which chapters start low" changes with the answer itself. Two passes are
            # enough. Ask once on the natural flow, ask again with that first answer applied, and
            # take the union - a chapter that reads badly under either pagination gets its own
            # page. Deterministic, and the same on every rebuild.
            wanted = []
            for it in range(2):
                da = fitz.open(render(paginated(None, wanted), "passA%d" % it))
                got = layoutqa.chapter_breaks(da)
                n_pages = da.page_count
                da.close()
                print(f"    chapter-break pass {it}: {n_pages} pages, {len(got)} wanted")
                for t in got:
                    if t not in wanted:
                        wanted.append(t)
            breaks = wanted
        else:
            breaks = [t for lvl, t in hs if lvl == 2]
    body_one = body_with(breaks)

    guide_rows = []
    if reading_guide is not None:
        # Pass two: the guide present with placeholder numbers of the same width, so the page
        # positions in this pass are the final ones. The real numbers are read from here.
        raw2 = render(assemble(body_one, stub), "pass2")
        d2 = fitz.open(raw2)
        h2 = heading_pages(d2, hs)
        total2 = d2.page_count
        d2.close()

        # A reading-guide entry names any heading level, so match on the text itself, not the
        # level. Search longest title first so "12. Reference: measures" does not shadow a
        # longer relative.
        located = []
        for ch_title, purpose in reading_guide:
            key = re.sub(r"[^a-z0-9]+", " ", ch_title.lower()).strip()
            hit = None
            for lvl, text in sorted(hs, key=lambda x: -len(x[1])):
                if key and key[:30] in re.sub(r"[^a-z0-9]+", " ", text.lower()):
                    hit = text
                    break
            if hit is not None and hit in h2:
                located.append((ch_title, h2[hit] + 1, purpose))
        located.sort(key=lambda r: r[1])
        for k, (ch_title, start, purpose) in enumerate(located):
            end = located[k + 1][1] - 1 if k + 1 < len(located) else total2
            span = f"{start}-{end}" if end > start else str(start)
            guide_rows.append((ch_title, span, purpose))

    raw = render(assemble(body_one, guide_rows if reading_guide is not None else None), "final")

    d = fitz.open(raw)
    n = d.page_count
    W = d[0].rect.width
    page_of = heading_pages(d, hs)

    def section_for(pno):
        best = ""
        for lvl, text in hs:
            if lvl == 1 and page_of.get(text, 10 ** 6) <= pno:
                best = text
        return best

    # On the dark pack the running head and footer must be legible against the charcoal page, so
    # the stamp colours come from the theme. The light house palette is unchanged.
    if theme == "charcoal":
        ink, accent, rule = (0.96, 0.97, 0.97), (1.0, 0.41, 0.43), (0.33, 0.38, 0.41)
    else:
        ink, accent, rule = GREY, TERR, (0.85, 0.83, 0.79)

    for i in range(n):
        page = d[i]
        if theme == "charcoal":
            # Chrome paints an element background only inside the printable box, which leaves the
            # margins white. Drawing the plate into the page's own content stream, underneath the
            # text (overlay=False), gives the full-bleed charcoal without touching the pagination.
            page.draw_rect(page.rect, color=None, fill=CHARCOAL, overlay=False)
        if i > 0:
            sec = section_for(i)
            page.insert_text((42, 29), title, fontname="helv", fontsize=6.6, color=ink)
            if sec:
                label = sec.upper()[:58]
                tw = fitz.get_text_length(label, fontname="hebo", fontsize=6.6)
                page.insert_text((W - 42 - tw, 29), label, fontname="hebo", fontsize=6.6,
                                 color=accent)
            page.draw_line(fitz.Point(42, 35), fitz.Point(W - 42, 35),
                           color=rule, width=0.5)
        f = footer.format(i=i + 1, n=n)
        tw = fitz.get_text_length(f, fontname="helv", fontsize=6.6)
        page.insert_text((W - 42 - tw, page.rect.height - 25), f, fontname="helv",
                         fontsize=6.6, color=ink)

    d.set_toc([[lvl, t, page_of.get(t, 1) + 1] for lvl, t in hs if lvl <= 2])
    d.set_metadata({"title": title, "author": "ISZE / Parts Europe",
                    "creator": "ISZE Universe document revision"})
    d.save(pdf_out, garbage=3, deflate=True)
    d.close()

    os.makedirs(qa_dir, exist_ok=True)
    for f in os.listdir(qa_dir):
        os.remove(os.path.join(qa_dir, f))
    d = fitz.open(pdf_out)
    blank, bleed, artefacts, nofurn = [], [], [], []
    for i, page in enumerate(d):
        t = page.get_text()
        words = len(t.split())
        # The running header and footer are stamped after the fact, so a page whose only content is
        # the furniture scores around 85 characters and slips past a plain character count. Measure
        # the body instead: strip the header line, the footer line and the page number, and a page
        # with no argument on it is caught.
        body = " ".join(t.split())
        body = body.replace(title, "")
        for w in (footer.split("{i}")[0].strip(), footer.split("{n}")[-1].strip()):
            body = body.replace(w, "")
        body = re.sub(r"\b\d{1,3}\s+of\s+\d{1,3}\b", "", body)
        body = re.sub(r"^[\s\d.,·]+$", "", body)
        if len(body.split()) < 30:
            blank.append(i + 1)
        if i > 0 and title not in t:
            nofurn.append(i + 1)
        r = page.rect
        for blk in page.get_text("dict")["blocks"]:
            x0, y0, x1, y1 = blk.get("bbox", (0, 0, 0, 0))
            if x1 > r.x1 - 1 or x0 < r.x0 + 1 or y1 > r.y1 - 1 or y0 < r.y0 + 1:
                bleed.append(i + 1)
        for pat in ["**", "##", "|---", "&nbsp;", "&amp;", "<strong>", "&lt;", "[[FIG"]:
            if pat in t:
                artefacts.append((i + 1, pat))
        page.get_pixmap(dpi=96).save(os.path.join(qa_dir, f"p{i + 1:02d}.png"))
    res = {"pages": d.page_count, "chars": sum(len(p.get_text()) for p in d),
           "bookmarks": len(d.get_toc()), "blank": sorted(set(blank)),
           "edges": sorted(set(bleed)), "artefacts": artefacts,
           "missing_header": sorted(set(nofurn)), "pdf_bytes": os.path.getsize(pdf_out),
           "guide_rows": guide_rows, "chapter_breaks": breaks}
    res["layout"] = layoutqa.analyse(d, md_path=md) if layout_qa else {}
    res["page_of"] = page_of
    d.close()
    return res
