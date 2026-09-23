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


def keep_together(els):
    """Wrap a section heading and the first thing under it in one unbreakable block.

    A heading left alone at the foot of a page, and a table or figure parted from the sentence
    that introduces it, are the two layout faults this prevents. Only h3 and h4 are wrapped:
    h2 starts a new page anyway, so there is nothing to keep it with.
    """
    out, i = [], 0
    nxt_flow = re.compile(r"^(<p>|<figure>|<table>|<ul>|<ol>|<blockquote>)")
    while i < len(els):
        e = els[i]
        m = re.match(r"^<(h[34])>", e)
        if m and i + 1 < len(els) and nxt_flow.match(els[i + 1]):
            out.append(f'<div class="keep">{e}\n{els[i + 1]}</div>')
            i += 2
            continue
        out.append(e)
        i += 1
    return out


def markdown_to_html(src, figdir, figcaps):
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
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>")
            for r in body:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
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
            out.append(f"<{tag}>")
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i])
                                      or re.match(r"^\s*\d+\.\s+", lines[i])):
                out.append(f"<li>{inline(re.sub(r'^\s*(?:[-*]|\d+\.)\s+', '', lines[i]))}</li>")
                i += 1
            out.append(f"</{tag}>")
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
    return "\n".join(keep_together(out))


CSS = """
@page { size: A4; margin: 19mm 15mm 16mm 15mm; }
* { box-sizing: border-box; }
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
.keep { page-break-inside: avoid; }
/* a chapter opens a fresh page */
.chapter-start { page-break-before: always; height:0; }
/* the reading guide: chapter, pages, what it decides */
.guide { width:100%; border-collapse: collapse; font-size: 9.2pt; margin: 3mm 0 4mm; }

/* ------------------------------------------------------------------ charcoal pack
   Used only by the critique pack that goes to the other tool: the 80-pager's own palette. */
.charcoal body { background:#24282C; color:#E0E5E8; }
.charcoal .sheet { background:#24282C; }
.charcoal h1, .charcoal h2, .charcoal h3, .charcoal h4 {
  font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; color:#F5F6F7; }
.charcoal h2 { border-bottom: 1.8pt solid #D71920; }
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
        "<tr>" + f"<td>{inline(a)}</td><td>{inline(b)}</td><td>{inline(c)}</td>" + "</tr>"
        for a, b, c in rows)
    return f'<table class="guide"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def heading_pages(doc, hs):
    """Map every heading to the 0-based page it first appears on."""
    n = doc.page_count
    page_of = {}
    for lvl, text in hs:
        needle = text[:46]
        for i in range(n):
            if needle and needle in doc[i].get_text():
                page_of[text] = i
                break
    return page_of


def layout_report(doc, content_top=40.0, content_bot=798.0, head_band=0.80):
    """The five layout faults, measured on the rendered pages.

    Returns a dict of lists. Empty lists mean the fault is absent.
    """
    H = re.compile(r"^(?:ISUZU / UNIVERSE[^a-z]*)$")

    def blocks(page):
        out = []
        for b in page.get_text("blocks"):
            x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], b[4]
            if y1 < content_top or y0 > content_bot or not txt.strip():
                continue
            out.append({"y0": y0, "y1": y1, "text": txt.strip()})
        return sorted(out, key=lambda b: b["y0"])

    def heads(page):
        found = []
        for blk in page.get_text("dict")["blocks"]:
            for line in blk.get("lines", []):
                for sp in line["spans"]:
                    if ("Georgia" in sp["font"] or "Times" in sp["font"]
                            or "Arial" in sp["font"]):
                        if sp["text"].strip() and sp["size"] >= 11.0:
                            found.append({"y1": line["bbox"][3], "size": sp["size"],
                                          "text": sp["text"].strip(),
                                          "x0": line["bbox"][0]})
        return found

    stranded, cap_split, tbl_split, whitespace = [], [], [], []
    col_h = content_bot - content_top
    for i, page in enumerate(doc):
        if i == 0:
            continue
        bl = blocks(page)
        if not bl:
            continue
        hs = heads(page)
        if hs:
            lowest = max(h["y1"] for h in hs)
            after = [b for b in bl if b["y0"] > lowest + 2]
            lines_after = sum(len(b["text"].split("\n")) for b in after)
            pos = (lowest - content_top) / col_h
            if pos > head_band and lines_after < 3:
                stranded.append({"page": i + 1,
                                 "heading": [h for h in hs if h["y1"] == lowest][0]["text"],
                                 "at": round(pos, 2), "lines_after": lines_after})
        imgs = [b for b in page.get_image_info() if content_top < b["bbox"][1] < content_bot]
        cap = [b for b in bl if re.match(r"^Figure \d+\.", b["text"])]
        if imgs and not cap:
            cap_split.append({"page": i + 1, "why": "figure with no caption on the page"})
        elif imgs and cap:
            gap = min(c["y0"] for c in cap) - max(im["bbox"][3] for im in imgs)
            if gap > 60:
                cap_split.append({"page": i + 1, "why": f"caption {round(gap)} pt below figure"})
            elif gap < -4:
                cap_split.append({"page": i + 1, "why": "caption above the figure"})
        low = max(b["y1"] for b in bl)
        tail = content_bot - low
        if tail > col_h * 0.42:
            whitespace.append({"page": i + 1, "empty_pt": round(tail),
                               "pct": round(tail / col_h * 100)})
    return {"stranded_headings": stranded, "figure_caption_splits": cap_split,
            "whitespace_pages": whitespace}


def build(md, html_out, pdf_out, qa_dir, title, cover, figdir, figcaps,
          footer, closing="", theme="navy", chapters_fresh_page=False,
          reading_guide=None, guide_heading="How to read this",
          guide_intro="", guide_head=("Chapter", "Pages", "What it decides")):
    """Build one document. Returns the QA result dict.

    theme               "navy" (house palette) or "charcoal" (the 80-pager's own look)
    chapters_fresh_page put a page break before every level-2 heading
    reading_guide       list of (chapter title, purpose) - renders a guide page near the front
                        with the real page numbers, in a second pass
    """
    import fitz

    src = open(md, encoding="utf-8").read()
    hs = headings(src)

    base = markdown_to_html(src, figdir, figcaps)
    body_one = base
    if chapters_fresh_page:
        body_one = "\n".join(
            '<div class="chapter-start"></div>' + e if e.startswith("<h2>") else e
            for e in base.split("\n") if e.strip())

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

    def render(html, out_path):
        open(html_out, "w", encoding="utf-8").write(html)
        raw = os.path.join(os.path.dirname(html_out), "_raw_" + os.path.basename(out_path))
        uri = "file:///" + html_out.replace("\\", "/")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--print-to-pdf=" + raw, "--virtual-time-budget=12000", uri],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=300)
        return raw

    guide_rows = []
    if reading_guide is not None:
        # Pass one: learn the page count with the guide absent.
        raw1 = render(assemble(body_one, None), "_pass1_" + os.path.basename(pdf_out))
        d1 = fitz.open(raw1)
        pages_no_guide = d1.page_count
        d1.close()

        # Pass two: the guide is present with placeholder numbers of the same width, so the
        # page positions in this pass are the final ones. The numbers are read from here.
        placeholders = [(t, "00-00", p) for t, p in reading_guide]
        raw2 = render(assemble(body_one, placeholders), "_pass2_" + os.path.basename(pdf_out))
        d2 = fitz.open(raw2)
        pg2 = heading_pages(d2, hs)
        total2 = d2.page_count
        d2.close()

        # Map every reading-guide entry to the heading it names, in document order.
        located = []
        for ch_title, purpose in reading_guide:
            hit = None
            for lvl, text in hs:
                if lvl == 1 and ch_title.lower()[:30] in text.lower():
                    hit = text
                    break
            if hit is not None and hit in pg2:
                located.append((ch_title, pg2[hit] + 1, purpose))
        located.sort(key=lambda r: r[1])
        for k, (ch_title, start, purpose) in enumerate(located):
            end = located[k + 1][1] - 1 if k + 1 < len(located) else total2
            span = f"{start}-{end}" if end > start else str(start)
            guide_rows.append((ch_title, span, purpose))

    raw = render(assemble(body_one, guide_rows if reading_guide is not None else None), pdf_out)

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

    for i in range(n):
        page = d[i]
        if i > 0:
            sec = section_for(i)
            page.insert_text((42, 29), title, fontname="helv", fontsize=6.6, color=GREY)
            if sec:
                label = sec.upper()[:58]
                tw = fitz.get_text_length(label, fontname="hebo", fontsize=6.6)
                page.insert_text((W - 42 - tw, 29), label, fontname="hebo", fontsize=6.6,
                                 color=TERR)
            page.draw_line(fitz.Point(42, 35), fitz.Point(W - 42, 35),
                           color=(0.85, 0.83, 0.79), width=0.5)
        f = footer.format(i=i + 1, n=n)
        tw = fitz.get_text_length(f, fontname="helv", fontsize=6.6)
        page.insert_text((W - 42 - tw, page.rect.height - 25), f, fontname="helv",
                         fontsize=6.6, color=GREY)

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
        if len(" ".join(t.split())) < 60:
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
           "guide_rows": guide_rows}
    res["layout"] = layout_report(d)
    res["page_of"] = page_of
    d.close()
    return res
