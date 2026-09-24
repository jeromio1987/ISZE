# -*- coding: utf-8 -*-
r"""Folder index: build_index.py -> UNIVERSE_FOLDER_INDEX_2026-09-23.pdf

The index is the same kind of document as the Universe papers, so it is rendered in the same
charcoal house style they use. This builder is a small charcoal renderer of its own, in this
folder, following the visual system already proven by the white paper.

The one mechanism worth naming: headless Chrome paints an element's background only inside the
printable box, so a background set on `body` or `@page` prints as white pages with a coloured block
in the middle. The white paper solved that by writing the charcoal plate into each page's own
content stream, underneath the text, so it runs edge to edge. That is what `plate_pages` below does,
and it is the reason every page field here is charcoal rather than white.

Runs in two passes, because the reading guide prints real page numbers and those do not exist until
the document has been printed once. Pass A puts in a guide of the final row count with placeholder
numbers of the same width, so the pagination of pass A is the pagination of pass B.

Run from the Isuzu Universe folder:  python _build_index\build_index.py
"""
import html as H
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# the visual system, from megaprompt section 8
CHARCOAL = "#24282C"      # page and section field
DEEPER = "#1C2024"        # deeper field
PANEL = "#353B3E"         # secondary dark panel
RED = "#D71920"           # emphasis only
LIGHT_RED = "#FF686D"     # accents on charcoal
WHITE = "#FFFFFF"         # primary text
SECOND = "#CCD1D2"        # secondary text
FAINT = "#A3ADB3"         # faint text
HAIRLINE = "#535B61"      # hairline rule
NAVY = "#15233C"          # charts and structure only
TERR = "#C0552D"          # second accent
PALE_RULE = "#E4E9F0"     # pale rule
PALE_BAND = "#F2F4F7"     # pale table band, where the text on it is ink

MD = os.path.join(HERE, "UNIVERSE_FOLDER_INDEX_2026-09-23.md")
HTMLOUT = os.path.join(HERE, "UNIVERSE_FOLDER_INDEX_2026-09-23.html")
PDFOUT = os.path.join(ROOT, "UNIVERSE_FOLDER_INDEX_2026-09-23.pdf")
QA = os.path.join(HERE, "_qa")
TITLE = "ISUZU / UNIVERSE - Folder Index"
FOOTER = "Universe folder index  ·  23 September 2026  ·  {i} of {n}"

READING_GUIDE = [
    ("What this folder is", "The programme in one page, and why there are several papers."),
    ("The documents to read first", "The current documents, how long each is, and what it is."),
    ("Opening them", "How the launchers work, for a reader who has not seen this folder."),
    ("Where the sources live", "The folder holding the source text of each document."),
    ("The GPT handover pack", "The review pack that goes back to the external partner."),
    ("How these documents are made", "Why a document is dated, and why a chart cannot drift."),
    ("Footnotes", "The older showcase, and the two withdrawn papers."),
    ("The rest of the folder", "The working programme, one line per folder."),
]

COVER = {
    "org": "ISZE / Parts Europe",
    "family": "Folder Index",
    "title": "Universe",
    "strap": "What is in this folder, which document to open,<br>"
             "and where the source text sits.",
    "focus": [
        "Seven current documents, and what each one is for.",
        "How to open each of them.",
        "Where the source text and the working notes live.",
        "The two withdrawn papers, kept on disk and not to be quoted.",
    ],
    "meta": "Folder index &nbsp;·&nbsp; 23 September 2026",
    "meta2": "Internal &nbsp;·&nbsp; Isuzu Universe working folder",
}

CSS = """
@page { size: A4; margin: 19mm 15mm 16mm 15mm; }
* { box-sizing: border-box; }
/* The plate that makes the page charcoal is drawn into the PDF afterwards; these two lines keep
   the print area dark as well, so nothing pale shows through around the text. */
html, body { background: #24282C; }
body { font: 10.1pt/1.55 Arial, "Helvetica Neue", Helvetica, sans-serif;
       color: #FFFFFF; margin: 0; }
h1, h2, h3, h4 { font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
                 color: #FFFFFF; page-break-after: avoid; }
h1 { font-size: 21pt; line-height: 1.16; margin: 0 0 4mm 0; letter-spacing: -.005em; }
h1::after { content: ""; display: block; width: 34mm; border-top: 3pt solid #D71920;
            margin-top: 3.2mm; }
h2 { font-size: 12.6pt; margin: 7.5mm 0 2.4mm; border-bottom: 1.2pt solid #535B61;
     padding-bottom: 1.4mm; }
h3 { font-size: 10.8pt; margin: 5.2mm 0 1.6mm; color: #E6EAEC; }
h4 { font-size: 10.1pt; margin: 4mm 0 1.4mm; color: #FF686D; }
p { margin: 0 0 2.5mm; color: #FFFFFF; }
hr { border: 0; border-top: .8pt solid #E4E9F0; opacity: .30; margin: 5mm 0; }
strong { color: #FFFFFF; }
em { color: #CCD1D2; }
a { color: #FF686D; }
code { font-family: Consolas, "Courier New", monospace; font-size: 8.9pt;
       background: #353B3E; color: #FFFFFF; padding: 0 .7mm; }
table { width: 100%; border-collapse: collapse; font-size: 8.9pt; margin: 2mm 0 4.5mm;
        page-break-inside: avoid; }
th { background: #353B3E; color: #FFFFFF; text-align: left; padding: 1.7mm 2mm;
     font-weight: 700; font-size: 8.4pt; border-bottom: 1.2pt solid #D71920; }
td { padding: 1.5mm 2mm; border-bottom: .6pt solid #454C51; vertical-align: top; color: #FFFFFF; }
tr:nth-child(even) td { background: #2A3035; color: #E9ECEE; }
blockquote { margin: 3mm 0; padding: 2.8mm 3.8mm; background: #353B3E;
             border-left: 3pt solid #D71920; color: #FFFFFF; }
ul, ol { margin: 0 0 3mm 5mm; padding: 0; }
li { margin-bottom: 1.2mm; color: #FFFFFF; }
.pagebreak { page-break-after: always; height: 0; }
.chapter-start { page-break-before: always; height: 0; }
.keep { page-break-inside: avoid; break-inside: avoid; }
p { orphans: 3; widows: 2; }
li, td { orphans: 2; widows: 2; }
/* a long table may flow, with its header repeated and its rows intact */
table.tbl-flow { page-break-inside: auto; }
table.tbl-flow thead { display: table-header-group; }
table.tbl-flow tr { page-break-inside: avoid; }

/* the reading guide */
.guide { width: 100%; border-collapse: collapse; font-size: 9.2pt; margin: 3mm 0 4mm; }
.guide th { background: #353B3E; color: #FFFFFF; }
.guide td { border-bottom: .6pt solid #3C4348; color: #FFFFFF; }
.guide tr:nth-child(even) td { background: #282E33; }
.guide td.pg { white-space: nowrap; width: 18mm; color: #FFFFFF; font-weight: 700; }

/* the pale band, used only where the text on it is ink - never white on a pale panel */
.chip { background: #F2F4F7; color: #24282C; padding: 2.4mm 3mm; margin: 3mm 0;
        border-left: 3pt solid #15233C; font-size: 9.2pt; }
.chip p, .chip li { color: #24282C; margin: 0; }
.chip b { color: #15233C; }

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
"""


def rgb(hexstr):
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def latin1(s):
    """The PDF stamper's built-in fonts are Latin-1, so fold anything outside it."""
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
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            out.append((len(m.group(1)), re.sub(r"[`*]", "", m.group(2)).strip()))
    return out


def md_to_html(src):
    """Markdown to house HTML. A heading is bound to the block below it, so a heading can never be
    the last thing on a page, and a sentence is never parted from the table it introduces."""
    lines = src.split("\n")
    els, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.strip() == "[[READING_GUIDE]]":
            els.append(("slot", '<div id="reading-guide-slot"></div>'))
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
            tbl = ['<table class="tbl-flow"><thead><tr>'
                   + "".join("<th>%s</th>" % inline(c) for c in head)
                   + "</tr></thead><tbody>"]
            for r in body:
                tbl.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            tbl.append("</tbody></table>")
            els.append(("table", "".join(tbl)))
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            els.append(("h%d" % len(m.group(1)), "<h%d>%s</h%d>"
                        % (len(m.group(1)), inline(m.group(2).strip()), len(m.group(1)))))
            i += 1
            continue
        if re.match(r"^---+\s*$", ln):
            els.append(("hr", "<hr>"))
            i += 1
            continue
        if ln.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            els.append(("quote", "<blockquote>"
                        + "<br>".join(inline(b) for b in buf if b) + "</blockquote>"))
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
                    items[-1] += " " + lines[i].strip()
                    i += 1
                else:
                    break
            els.append(("ul", "<%s>%s</%s>" % (tag, "".join(
                "<li>%s</li>" % inline(x) for x in items), tag)))
            continue
        buf = [ln]
        i += 1
        while (i < len(lines) and lines[i].strip()
               and not re.match(r"^(#{1,3}\s|---|\s*[-*]\s|\s*\d+\.\s|>)", lines[i])
               and not lines[i].lstrip().startswith("|")):
            buf.append(lines[i])
            i += 1
        els.append(("p", "<p>%s</p>" % inline(" ".join(b.strip() for b in buf))))

    # bind each heading to its first following block, and a sentence to the table it introduces
    out, i = [], 0
    while i < len(els):
        kind, el = els[i]
        if kind.startswith("h") and i + 1 < len(els):
            nxt = els[i + 1]
            inner = [el, nxt[1]]
            i += 2
            # one more short paragraph, and the table those sentences introduce
            if i < len(els) and els[i][0] == "p" and nxt[0] != "table":
                inner.append(els[i][1])
                i += 1
            if i < len(els) and els[i][0] == "table":
                inner.append(els[i][1])
                i += 1
            out.append('<div class="keep">' + "\n".join(inner) + "</div>")
            continue
        if kind == "p" and i + 1 < len(els) and els[i + 1][0] == "table":
            out.append('<div class="keep">' + el + "\n" + els[i + 1][1] + "</div>")
            i += 2
            continue
        out.append(el)
        i += 1
    return "\n".join(out)


def cover_html(c):
    focus = "".join("<li>%s</li>" % x for x in c.get("focus", []))
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
           strap=c.get("strap", ""), focus_head="What this index covers", focus=focus,
           meta=c.get("meta", ""), meta2=c.get("meta2", ""))


def guide_html(rows):
    trs = "".join("<tr><td>%s</td><td class=\"pg\">%s</td><td>%s</td></tr>"
                  % (inline(a), b, inline(c)) for a, b, c in rows)
    return ('<div class="keep"><h2>What is in this index</h2>'
            '<p>Every part of this index, and the one thing it settles.</p>'
            '<table class="guide"><thead><tr><th>Part</th><th>Pages</th>'
            '<th>What it settles</th></tr></thead><tbody>' + trs + "</tbody></table></div>")


def heading_pages(doc, hs):
    """Map each heading to the 1-based page it lands on, matched on rendered heading spans so the
    guide's own list of chapter titles cannot be mistaken for the chapters themselves."""
    rendered = []
    for i in range(doc.page_count):
        lines = []
        for blk in doc[i].get_text("dict")["blocks"]:
            for line in blk.get("lines", []):
                for sp in line["spans"]:
                    if (sp["text"].strip() and sp["size"] >= 10.4
                            and ("Arial" in sp["font"] or "Helvetica" in sp["font"]
                                 or "Georgia" in sp["font"] or "Times" in sp["font"])):
                        lines.append(sp["text"].strip())
        rendered.append(" · ".join(lines))

    def norm(t):
        return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()

    page_of = {}
    for _lvl, text in hs:
        needle = norm(text)[:44]
        if not needle:
            continue
        for i in range(1, doc.page_count):     # start at page 2: page 1 is the cover
            if needle in norm(rendered[i]):
                page_of[text] = i + 1
                break
    return page_of


def plate_pages(doc, colour=CHARCOAL):
    """Draw the charcoal field into every page's own content stream, underneath the text.

    This is the mechanism that makes the whole document charcoal rather than the cover alone.
    Chrome paints an element background only inside the printable box, which leaves the margins
    white; writing the plate into the page contents runs it edge to edge without touching the
    pagination, because it is drawn with overlay=False.
    """
    col = rgb(colour)
    for page in doc:
        page.draw_rect(page.rect, color=None, fill=col, overlay=False)


def build():
    import fitz

    src = open(MD, encoding="utf-8").read()
    hs = headings(src)
    body = md_to_html(src)

    def assemble(guide_rows):
        b = body.replace('<div id="reading-guide-slot"></div>', guide_html(guide_rows))
        return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{t}</title>
<style>{css}</style></head><body>
{cover}
{b}
</body></html>""".format(t=TITLE, css=CSS, cover=cover_html(COVER), b=b)

    def render(html, tag):
        open(HTMLOUT, "w", encoding="utf-8").write(html)
        raw = os.path.join(HERE, "_raw_%s_%s" % (tag, os.path.basename(PDFOUT)))
        uri = "file:///" + HTMLOUT.replace("\\", "/")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--print-to-pdf=" + raw, "--virtual-time-budget=15000", uri],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=300)
        return raw

    # ---- pass A: the guide with placeholder numbers of the final width, so pagination is final
    stub = [(t, "00-00", p) for t, p in READING_GUIDE]
    da = fitz.open(render(assemble(stub), "passA"))
    page_of_a = heading_pages(da, hs)
    total_a = da.page_count
    da.close()

    located = []
    for title, purpose in READING_GUIDE:
        for _lvl, text in hs:
            if title.lower()[:26] in text.lower():
                located.append((title, page_of_a.get(text), purpose))
                break
    located = [r for r in located if r[1]]
    rows = []
    for k, (title, start, purpose) in enumerate(located):
        end = located[k + 1][1] - 1 if k + 1 < len(located) else total_a
        rows.append((title, "%d-%d" % (start, end) if end > start else str(start), purpose))

    # ---- pass B: the real numbers, same row count, then the plate and the furniture
    d = fitz.open(render(assemble(rows), "passB"))
    n = d.page_count
    page_of = heading_pages(d, hs)

    def section_for(pno):
        best = ""
        for lvl, text in hs:
            if lvl == 1 and page_of.get(text, 10 ** 6) <= pno:
                best = text
        return best

    plate_pages(d)

    for i, page in enumerate(d):
        if i > 0:
            page.insert_text((42, 28), latin1(TITLE), fontname="helv", fontsize=6.6,
                             color=rgb(SECOND))
            sec = section_for(i + 1)
            if sec:
                label = latin1(sec.upper())[:58]
                tw = fitz.get_text_length(label, fontname="hebo", fontsize=6.6)
                page.insert_text((page.rect.width - 42 - tw, 28), label, fontname="hebo",
                                 fontsize=6.6, color=rgb(RED))
            page.draw_line(fitz.Point(42, 35), fitz.Point(page.rect.width - 42, 35),
                           color=rgb(HAIRLINE), width=0.5)
        f = latin1(FOOTER.format(i=i + 1, n=n))
        tw = fitz.get_text_length(f, fontname="helv", fontsize=6.6)
        page.insert_text((page.rect.width - 42 - tw, page.rect.height - 25), f,
                         fontname="helv", fontsize=6.6, color=rgb(SECOND))

    d.set_toc([[lvl, t, page_of.get(t, 1)] for lvl, t in hs if lvl <= 2])
    d.set_metadata({"title": TITLE, "author": "ISZE / Parts Europe",
                    "creator": "ISZE Universe folder index",
                    "subject": "Internal folder index"})
    # If a reader has the root PDF open, Windows will not let us replace it. Stage the rebuild
    # inside this folder and report the path, rather than leaving a stale file behind.
    target = PDFOUT
    try:
        probe = open(PDFOUT, "ab")
        probe.close()
        d.save(PDFOUT, garbage=3, deflate=True)
    except (PermissionError, OSError) as exc:
        target = os.path.join(HERE, os.path.basename(PDFOUT))
        d.save(target, garbage=3, deflate=True)
        print("NOTE: %s could not be written (%s)." % (PDFOUT, exc.__class__.__name__))
        print("      The rebuild is staged at %s" % target)
    d.close()

    # ---- page images for the visual check
    os.makedirs(QA, exist_ok=True)
    for f in os.listdir(QA):
        os.remove(os.path.join(QA, f))
    d = fitz.open(PDFOUT)
    res = {"pages": d.page_count, "guide_rows": rows, "blank": [], "artefacts": [],
           "missing_header": [], "edges": [], "bookmarks": len(d.get_toc())}
    for i, page in enumerate(d):
        t = page.get_text()
        if len(" ".join(t.split())) < 40:
            res["blank"].append(i + 1)
        if i > 0 and latin1(TITLE) not in t:
            res["missing_header"].append(i + 1)
        for pat in ["**", "##", "|---", "&nbsp;", "&amp;", "<strong>", "[[", "`"]:
            if pat in t:
                res["artefacts"].append((i + 1, pat))
        for blk in page.get_text("dict")["blocks"]:
            x0, y0, x1, y1 = blk.get("bbox", (0, 0, 0, 0))
            if x1 > page.rect.x1 - 1 or x0 < page.rect.x0 + 1 or y1 > page.rect.y1 - 1 \
                    or y0 < page.rect.y0 + 1:
                res["edges"].append(i + 1)
        page.get_pixmap(dpi=110).save(os.path.join(QA, "p%02d.png" % (i + 1)))
    res["pdf_bytes"] = os.path.getsize(PDFOUT)
    d.close()
    return res


if __name__ == "__main__":
    r = build()
    print("pages=%d bookmarks=%d bytes=%d" % (r["pages"], r["bookmarks"], r["pdf_bytes"]))
    print("near-blank pages: %s" % (r["blank"] or "none"))
    print("blocks touching the edge: %s" % (r["edges"] or "none"))
    print("markdown artefacts: %s" % (r["artefacts"] or "none"))
    print("pages missing the running header: %s" % (r["missing_header"] or "none"))
    print("--- reading guide ---")
    for t, p, _x in r["guide_rows"]:
        print("  %-8s %s" % (p, t))
    print("page images written to %s" % QA)
