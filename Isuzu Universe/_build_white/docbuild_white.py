# -*- coding: utf-8 -*-
r"""Charcoal renderer for the Isuzu Universe white paper.

A separate renderer from `_build_30\docbuild.py`, in a new folder, so that the two documents can be
rebuilt independently. The layout ideas are the same (a markdown source, headless Chrome to print,
running furniture and a bookmark tree stamped afterwards); the styling is not.

Charcoal carries the whole document, not only the cover. Every page is on `#24282C` with white or
`#CCD1D2` body text. The pale values in the palette are used as rules and as the background of a small
number of figure chips, and where they are used the text on them is ink - never white on a pale panel.

Two-pass index. Page numbers do not exist until the document has been rendered once, so:
  pass A  renders the contents, figure list and table list with placeholder numbers of the same row
          count and width as the final lists, so pagination in pass A equals pagination in pass B
  read    every heading, figure and table is located in the pass-A PDF
  pass B  renders again with the real page numbers
The caller then verifies the printed numbers against pass B's own text.
"""
import html as H
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CHARCOAL = "#24282C"
PANEL = "#353B3E"
RED = "#D71920"
WHITE = "#FFFFFF"
SECOND = "#CCD1D2"
NAVY = "#15233C"
TERR = "#C0552D"
RULE = "#E4E9F0"
BAND = "#F2F4F7"

sys.stdout.reconfigure(encoding="utf-8")


def rgb(hexstr):
    """A palette hex string as the 0-1 triple the PDF stamper wants."""
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def latin1(s):
    """The PDF stamper's built-in fonts are Latin-1, so fold any character outside it.

    Section headings in the source carry typographic dashes and quotes; these would otherwise
    raise on insert_text. The body of the paper keeps its typography because it is set by Chrome.
    """
    table = {"\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
             "\u201c": '"', "\u201d": '"', "\u00b7": "-", "\u2026": "...", "\u20ac": "EUR"}
    for a, b in table.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


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
        m = re.match(r"^(#{1,2})\s+(.*)$", ln)
        if m:
            out.append((len(m.group(1)), re.sub(r"[`*]", "", m.group(2)).strip()))
    return out


CSS = """
@page { size: A4; margin: 20mm 16mm 17mm 16mm; }
* { box-sizing: border-box; }
html, body { background: #24282C; }
body { font: 10.2pt/1.55 Arial, "Helvetica Neue", Helvetica, sans-serif;
       color: #FFFFFF; margin: 0; }
h1, h2, h3, h4 { font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
                 color: #FFFFFF; page-break-after: avoid; }
h1 { font-size: 21pt; line-height: 1.16; margin: 0 0 4mm 0; letter-spacing: -.005em; }
h1::after { content: ""; display: block; width: 34mm; border-top: 3pt solid #D71920;
            margin-top: 3.2mm; }
h2 { font-size: 12.6pt; margin: 8mm 0 2.6mm; color: #FFFFFF; }
h3 { font-size: 10.8pt; margin: 5.4mm 0 1.8mm; color: #E6EAEC; }
h4 { font-size: 10.2pt; margin: 4mm 0 1.4mm; color: #D71920; }
p { margin: 0 0 2.5mm; color: #FFFFFF; }
hr { border: 0; border-top: 0.8pt solid #E4E9F0; opacity: .35; margin: 5mm 0; }
strong { color: #FFFFFF; }
em { color: #CCD1D2; }
a { color: #FF686D; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt;
       background: #353B3E; color: #FFFFFF; padding: 0 .7mm; }
table { width: 100%; border-collapse: collapse; font-size: 8.9pt; margin: 2mm 0 4.5mm;
        page-break-inside: avoid; }
th { background: #353B3E; color: #FFFFFF; text-align: left; padding: 1.7mm 2mm;
     font-weight: 700; font-size: 8.4pt; border-bottom: 1.2pt solid #D71920; }
td { padding: 1.5mm 2mm; border-bottom: .6pt solid #454C51; vertical-align: top;
     color: #FFFFFF; }
tr:nth-child(even) td { background: #2A3035; color: #E9ECEE; }
blockquote { margin: 3mm 0; padding: 2.8mm 3.8mm; background: #353B3E;
             border-left: 3pt solid #D71920; color: #FFFFFF; }
blockquote p { color: #FFFFFF; margin: 0; }
ul, ol { margin: 0 0 3mm 5mm; padding: 0; }
li { margin-bottom: 1.2mm; color: #FFFFFF; }
figure { margin: 4mm 0 5mm; page-break-inside: avoid; text-align: center; }
figure img { width: 100%; max-width: 176mm; height: auto; }
figcaption { font-size: 8.1pt; color: #CCD1D2; text-align: left; margin-top: 2mm;
             line-height: 1.45; }
figcaption b { color: #FFFFFF; }
.pagebreak { page-break-after: always; height: 0; }
.chapter-start { page-break-before: always; height: 0; }
.keep { page-break-inside: avoid; break-inside: avoid; }
p { orphans: 3; widows: 2; }
li, td { orphans: 2; widows: 2; }

/* a figure caption and the table caption are part of the numbered index */
.tabcap { font-size: 8.6pt; color: #FFFFFF; margin: 4mm 0 1.4mm; font-weight: 700;
          page-break-after: avoid; }
.tabcap span { color: #D71920; }
.tabnote { font-size: 8pt; color: #CCD1D2; margin: 0 0 1mm; }

/* the pale band, used only where the text on it is ink */
.chip { background: #F2F4F7; color: #24282C; padding: 2.4mm 3mm; margin: 3mm 0;
        border-left: 3pt solid #15233C; font-size: 9.2pt; }
.chip b { color: #15233C; }
.chip p { color: #24282C; margin: 0; }

/* index pages */
.idx { width: 100%; border-collapse: collapse; font-size: 9.2pt; margin: 2mm 0 4mm; }
.idx th { background: #353B3E; color: #FFFFFF; }
.idx td { border-bottom: .6pt solid #3C4348; color: #FFFFFF; }
.idx tr:nth-child(even) td { background: #282E33; }
.idx td.pg { text-align: right; width: 16mm; color: #FFFFFF; font-weight: 700; }
.idx td.lvl2 { padding-left: 7mm; color: #CCD1D2; }

/* cover */
.cover { height: 250mm; display: flex; flex-direction: column; page-break-after: always;
         padding-top: 2mm; }
.cover .org { font-size: 10pt; letter-spacing: .30em; text-transform: uppercase;
              color: #CCD1D2; font-weight: 700; }
.cover .family { font-size: 12pt; letter-spacing: .40em; text-transform: uppercase;
                 color: #D71920; margin-top: 3mm; font-weight: 700; }
.cover .rule { border-top: 3.4pt solid #D71920; margin: 6mm 0 10mm; }
.cover .title { font-size: 46pt; line-height: 1.02; color: #FFFFFF; margin: 0;
                letter-spacing: -.02em; }
.cover .title .thin { color: #CCD1D2; }
.cover .strap { font-size: 14pt; line-height: 1.5; color: #CCD1D2; margin: 7mm 0 0;
                max-width: 150mm; }
.cover .grow { flex: 1; }
.cover .focus { border-top: 1pt solid #4A5257; padding-top: 5mm; }
.cover .focus .h { font-size: 8.2pt; letter-spacing: .20em; text-transform: uppercase;
                   color: #CCD1D2; margin-bottom: 3mm; }
.cover .focus li { font-size: 10.4pt; color: #FFFFFF; margin-bottom: 2.2mm; }
.cover .meta { border-top: 2.4pt solid #D71920; margin-top: 7mm; padding-top: 4mm;
               font-size: 9.4pt; color: #FFFFFF; font-weight: 700; letter-spacing: .10em;
               text-transform: uppercase; }
.cover .meta2 { font-size: 8.2pt; color: #CCD1D2; margin-top: 2mm; letter-spacing: .10em;
                text-transform: uppercase; }
.closing { border-top: 1px solid #4A5257; color: #CCD1D2; font-size: 8.2pt; margin-top: 8mm;
           padding-top: 3mm; line-height: 1.5; }
.closing b { color: #FFFFFF; }
"""


def cover_html(c):
    focus = "".join("<li>{}</li>".format(x) for x in c.get("focus", []))
    return """
<div class="cover">
  <div class="org">{org}</div>
  <div class="family">{family}</div>
  <div class="rule"></div>
  <div class="title">{title}</div>
  <div class="strap">{strap}</div>
  <div class="grow"></div>
  <div class="focus">
    <div class="h">{focus_head}</div>
    <ul style="list-style:none;margin:0;padding:0">{focus}</ul>
  </div>
  <div class="meta">{meta}</div>
  <div class="meta2">{meta2}</div>
</div>
""".format(org=c.get("org", ""), family=c.get("family", ""), title=c.get("title", ""),
           strap=c.get("strap", ""), focus_head=c.get("focus_head", ""), focus=focus,
           meta=c.get("meta", ""), meta2=c.get("meta2", ""))


def md_to_html(src, figdir, figcaps):
    """Markdown to house HTML. Returns (html, figure_numbers_in_order, table_captions_in_order)."""
    lines = src.split("\n")
    out, i = [], 0
    figs, tabs = [], []
    tbl_n = [0]

    def next_tbl():
        tbl_n[0] += 1
        return tbl_n[0]

    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue

        m = re.match(r"^\[\[FIG(\d+)\]\]\s*$", ln.strip())
        if m:
            n = int(m.group(1))
            figs.append(n)
            img = None
            if os.path.isdir(figdir):
                for f in sorted(os.listdir(figdir)):
                    if f.startswith("f%02d_" % n):
                        img = f
            cap = figcaps.get(n, ("", ""))[0]
            out.append('<figure><img src="figures/{}" alt="Figure {}">'
                       '<figcaption><b>Figure {}.</b> {}</figcaption></figure>'
                       .format(img, n, n, inline(cap)))
            i += 1
            continue

        m = re.match(r"^\[\[TABLE\s+(.*?)\]\]\s*$", ln.strip())
        if m:
            k = next_tbl()
            cap = m.group(1).strip()
            tabs.append((k, cap))
            out.append('<div class="tabcap"><span>Table {}.</span> {}</div>'
                       .format(k, inline(cap)))
            i += 1
            continue

        if ln.strip() == "[[PAGEBREAK]]":
            out.append('<div class="pagebreak"></div>')
            i += 1
            continue

        for slot in ("TOC", "FIGLIST", "TABLELIST"):
            if ln.strip() == "[[%s]]" % slot:
                out.append('<div id="slot-%s"></div>' % slot.lower())
                i += 1
                break
        else:
            pass
        if ln.strip() in ("[[TOC]]", "[[FIGLIST]]", "[[TABLELIST]]"):
            continue

        if ln.lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            rows = [[c.strip() for c in r.strip("|").split("|")] for r in block]
            rows = [r for r in rows
                    if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)]
            head, body = rows[0], rows[1:]
            out.append("<table><thead><tr>"
                       + "".join("<th>{}</th>".format(inline(c)) for c in head)
                       + "</tr></thead><tbody>")
            for r in body:
                out.append("<tr>" + "".join("<td>{}</td>".format(inline(c)) for c in r) + "</tr>")
            out.append("</tbody></table>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            out.append("<h{l}>{t}</h{l}>".format(l=lvl, t=inline(txt)))
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
            out.append("<blockquote><p>" + "<br>".join(
                inline(b) for b in buf if b) + "</p></blockquote>")
            continue

        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            tag = "ol" if re.match(r"^\s*\d+\.\s+", ln) else "ul"
            out.append("<{}>".format(tag))
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i])
                                      or re.match(r"^\s*\d+\.\s+", lines[i])):
                # an item may wrap over several source lines; join them so a bold span that
                # starts on one line and ends on the next is still a single span
                item = [re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i])]
                i += 1
                while (i < len(lines) and lines[i].strip()
                       and not re.match(r"^\s*(?:[-*]|\d+\.)\s+", lines[i])
                       and not re.match(r"^(#{1,4}\s|---|\s*>|\[\[)", lines[i])
                       and not lines[i].lstrip().startswith("|")):
                    item.append(lines[i].strip())
                    i += 1
                out.append("<li>{}</li>".format(inline(" ".join(item))))
            out.append("</{}>".format(tag))
            continue

        buf = [ln]
        i += 1
        while (i < len(lines) and lines[i].strip()
               and not re.match(r"^(#{1,4}\s|---|\s*[-*]\s|\s*\d+\.\s|>)", lines[i])
               and not lines[i].lstrip().startswith("|")
               and not lines[i].strip().startswith("[[FIG")
               and not lines[i].strip().startswith("[[TABLE")):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(b.strip() for b in buf)) + "</p>")

    # keep each heading with what follows it, so a heading is never the last thing on a page
    merged, j = [], 0
    while j < len(out):
        e = out[j]
        if re.match(r"^<h[123]>", e) and j + 1 < len(out) and \
                re.match(r"^(<p>|<figure>|<table>|<ul>|<ol>|<blockquote>|"
                         r"<div class=\"tabcap\">)", out[j + 1]):
            inner = [e, out[j + 1]]
            j += 2
            cap = 1 if e.startswith("<h1") else 2
            while j < len(out) and re.match(r"^<p>", out[j]) and len(inner) - 1 < cap:
                inner.append(out[j])
                j += 1
            merged.append('<div class="keep">' + "\n".join(inner) + "</div>")
            continue
        if re.match(r"^(<p>|<div class=\"tabcap\">)", e) and j + 1 < len(out) \
                and re.match(r"^<table>", out[j + 1]):
            merged.append('<div class="keep">' + e + "\n" + out[j + 1] + "</div>")
            j += 2
            continue
        merged.append(e)
        j += 1

    return "\n".join(merged), figs, tabs


def heading_pages(doc, hs):
    """Map each heading to the 1-based page it first appears on, using rendered heading runs."""
    n = doc.page_count
    rendered = []
    for i in range(n):
        parts = []
        for blk in doc[i].get_text("dict")["blocks"]:
            for line in blk.get("lines", []):
                for sp in line["spans"]:
                    if sp["size"] >= 11.0 and sp["text"].strip():
                        parts.append(sp["text"].strip())
        rendered.append(" \u00b7 ".join(parts))

    def norm(t):
        return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()

    page_of = {}
    for lvl, text in hs:
        needle = norm(text)[:44]
        if not needle:
            continue
        for i in range(n):
            if needle in norm(rendered[i]):
                page_of[text] = i + 1
                break
    return page_of


def index_html(rows, head, cls="idx"):
    th = "".join("<th>{}</th>".format(H.escape(h)) for h in head)
    trs = []
    for r in rows:
        cells = []
        for k, c in enumerate(r):
            klass = ""
            if c is not None and r and len(r) >= 2 and k == len(r) - 1 and \
                    isinstance(c, str) and re.fullmatch(r"[\d,\u2013 -]+", c):
                klass = ' class="pg"'
            cells.append("<td{}>{}</td>".format(klass, H.escape(str(c))))
        trs.append("<tr>" + "".join(cells) + "</tr>")
    return '<table class="{}"><thead><tr>{}</tr></thead><tbody>{}</tbody></table>'.format(
        cls, th, "".join(trs))


def build(md, html_out, pdf_out, qa_dir, title, cover, figdir, figcaps, footer,
          closing="", contents_intro="", figs_intro="", tabs_intro=""):
    import fitz

    src = open(md, encoding="utf-8").read()
    hs = headings(src)
    body, figs, tabs = md_to_html(src, figdir, figcaps)

    def assemble(toc_rows, fig_rows, tab_rows):
        b = body
        if toc_rows is not None:
            b = b.replace('<div id="slot-toc"></div>',
                          index_html(toc_rows, ("Chapter and section", "Page")) + "\n")
        else:
            b = b.replace('<div id="slot-toc"></div>',
                          index_html([("", "00")] * len(hs), ("Chapter and section", "Page")))
        if fig_rows is not None:
            b = b.replace('<div id="slot-figlist"></div>',
                          index_html(fig_rows, ("Figure", "Page")) + "\n")
        else:
            b = b.replace('<div id="slot-figlist"></div>',
                          index_html([("", "00")] * len(figs), ("Figure", "Page")))
        if tab_rows is not None:
            b = b.replace('<div id="slot-tablelist"></div>',
                          index_html(tab_rows, ("Table", "Page")) + "\n")
        else:
            b = b.replace('<div id="slot-tablelist"></div>',
                          index_html([("", "00")] * len(tabs), ("Table", "Page")))
        return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{t}</title>
<style>{css}</style></head><body>
{cover}
{body}
{closing}
</body></html>""".format(t=title, css=CSS, cover=cover_html(cover), body=b, closing=closing)

    def render(html, tag):
        open(html_out, "w", encoding="utf-8").write(html)
        raw = os.path.join(os.path.dirname(html_out),
                           "_raw_" + tag + "_" + os.path.basename(pdf_out))
        uri = "file:///" + html_out.replace("\\", "/")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--print-to-pdf=" + raw, "--virtual-time-budget=15000", uri],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=300)
        return raw

    # ---- pass A: placeholder lists of the final row count, so the pagination is the final one
    raw_a = render(assemble(None, None, None), "passA")
    da = fitz.open(raw_a)
    page_of = heading_pages(da, hs)

    # locate each figure and each table caption in pass A
    def find_page(needle):
        for i in range(da.page_count):
            t = re.sub(r"\s+", " ", da[i].get_text())
            if needle in t:
                return i + 1
        return None

    fig_pages = {}
    for n in figs:
        hit = find_page("Figure {}. ".format(n))
        fig_pages[n] = hit
    tab_pages = {}
    for k, cap in tabs:
        hit = find_page("Table {}. ".format(k))
        tab_pages[k] = hit
    total_a = da.page_count
    da.close()

    toc_rows = [(("  " * (lvl - 1)) + text, str(page_of.get(text, "")) if page_of.get(text)
                 else "") for lvl, text in hs]
    toc_rows = [(t.strip(), p) for t, p in toc_rows]
    fig_rows = [("Figure {} — {}".format(n, figcaps.get(n, ("", ""))[0][:96] +
                                         ("…" if len(figcaps.get(n, ("", ""))[0]) > 96 else "")),
                 str(fig_pages.get(n) or "")) for n in figs]
    tab_rows = [("Table {} — {}".format(k, cap), str(tab_pages.get(k) or "")) for k, cap in tabs]

    # ---- pass B: the real numbers, same row count
    raw_b = render(assemble(toc_rows, fig_rows, tab_rows), "passB")
    d = fitz.open(raw_b)
    n_pages = d.page_count
    page_of_b = heading_pages(d, hs)

    def section_for(pno):
        best = ""
        for lvl, text in hs:
            if lvl == 1 and page_of_b.get(text, 10 ** 6) <= pno:
                best = text
        return best

    # stamp the running furniture
    for i in range(n_pages):
        page = d[i]
        if i > 0:
            page.insert_text((45, 30), latin1(title), fontname="helv", fontsize=6.6,
                             color=rgb(SECOND))
            sec = section_for(i + 1)
            if sec and sec != "Contents" and sec != cover.get("family", ""):
                label = latin1(sec.upper())[:56]
                if label.strip():
                    tw = fitz.get_text_length(label, fontname="hebo", fontsize=6.6)
                    page.insert_text((page.rect.width - 45 - tw, 30), label, fontname="hebo",
                                     fontsize=6.6, color=rgb(RED))
            page.draw_line(fitz.Point(45, 36), fitz.Point(page.rect.width - 45, 36),
                           color=rgb("#5A6469"), width=0.5)
        f = latin1(footer.format(i=i + 1, n=n_pages))
        tw = fitz.get_text_length(f, fontname="helv", fontsize=6.6)
        page.insert_text((page.rect.width - 45 - tw, page.rect.height - 26), f,
                         fontname="helv", fontsize=6.6, color=rgb(SECOND))

    # normalise the bookmark hierarchy: the first heading level present becomes level 1
    levels = sorted({lvl for lvl, _t in hs})
    shift = (levels[0] - 1) if levels else 0
    bookmarks = [[max(1, lvl - shift), text, page_of_b.get(text, 1)] for lvl, text in hs]
    # PyMuPDF requires the first bookmark to be level 1; the paper opens on a section heading,
    # so promote it rather than inserting a placeholder entry.
    if bookmarks and bookmarks[0][0] != 1:
        bookmarks[0][0] = 1
    d.set_toc(bookmarks)
    d.set_metadata({"title": title, "author": "ISZE / Parts Europe",
                    "creator": "ISZE Universe paper build", "subject":
                    "Internal draft for the business owner"})
    d.save(pdf_out, garbage=3, deflate=True)
    d.close()

    # ---- page images for the visual check
    os.makedirs(qa_dir, exist_ok=True)
    for f in os.listdir(qa_dir):
        os.remove(os.path.join(qa_dir, f))
    d = fitz.open(pdf_out)
    checks = {"thin_pages": [], "artefacts": [], "missing_header": [], "edge_bleed": []}
    for i, page in enumerate(d):
        t = page.get_text()
        if len(" ".join(t.split())) < 60:
            checks["thin_pages"].append(i + 1)
        if i > 0 and latin1(title) not in t:
            checks["missing_header"].append(i + 1)
        for pat in ["**", "##", "|---", "[[FIG", "[[TABLE", "[[TOC", "&amp;", "&nbsp;"]:
            if pat in t:
                checks["artefacts"].append((i + 1, pat))
        for blk in page.get_text("dict")["blocks"]:
            x0, y0, x1, y1 = blk.get("bbox", (0, 0, 0, 0))
            if x1 > page.rect.x1 - 1 or x0 < page.rect.x0 + 1 or y1 > page.rect.y1 - 1:
                checks["edge_bleed"].append(i + 1)
        page.get_pixmap(dpi=110).save(os.path.join(qa_dir, "p{:02d}.png".format(i + 1)))
    result = {"pages": n_pages, "pages_before_lists": total_a,
              "chars": sum(len(p.get_text()) for p in d),
              "bookmarks": len(d.get_toc()),
              "toc_rows": toc_rows, "fig_rows": fig_rows, "tab_rows": tab_rows,
              "heading_pages": page_of_b, "checks": checks}
    d.close()
    return result
