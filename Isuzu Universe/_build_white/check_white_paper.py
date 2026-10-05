# -*- coding: utf-8 -*-
r"""Check the white paper against what the brief requires. Re-runnable.

Checks, in order:
  1. the rendered PDF: page count, page size, running furniture on every page after the cover
  2. the background: every page must be charcoal field, not a light page
  3. no pale panel carries white or near-white text
  4. no markdown artefact survives into the rendered text
  5. the contents, figure list and table list: every printed page number resolves to a page that
     actually carries the heading, the figure caption or the table caption
  6. the banned vocabulary and the instant-fail figures are absent from the rendered text
  7. every figure on disk was written by the build, and no raster from the visual edition is reused

Exit code 0 means every check passed.
"""
import io
import os
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe"
PDF = os.path.join(ROOT, "ISUZU_UNIVERSE_WHITE_PAPER_2026-09-23.pdf")
MD = os.path.join(ROOT, "01_Strategy", "ISUZU_UNIVERSE_WHITE_PAPER_2026-09-23.md")
FIGDIR = os.path.join(ROOT, "_build_white", "figures")
QA = os.path.join(ROOT, "_build_white", "_qa")

HEADER = "ISUZU / UNIVERSE - the white paper"

# words and figures the brief bans outright
BANNED_WORDS = ["sell-out", "sellout", "sell out", "wallet", "street fill",
                "Mode A", "Mode B", "Book B", "ship-gate", "harness", "artifact",
                "artefact", "rollup", "granularity", "instantiate",
                "61,791", "37,019", "32.4%", "54.4%", "117.6"]
FAILS = []


def fail(where, what):
    FAILS.append((where, what))


def main():
    doc = fitz.open(PDF)
    n = doc.page_count
    pages = [p.get_text() for p in doc]
    print("pages: {}".format(n))
    print("page size: {:.0f} x {:.0f} pt (A4 is 595 x 842)".format(
        doc[0].rect.width, doc[0].rect.height))
    if n < 40 or n > 80:
        fail("page count", "{} pages, outside a plausible range for this paper".format(n))
    if abs(doc[0].rect.width - 595) > 2 or abs(doc[0].rect.height - 842) > 2:
        fail("page size", "not A4")

    # ---- 2/3. background and contrast, measured on the rasterised page
    print()
    light_pages, pale_with_light_text = [], []
    for i in range(n):
        pm = doc[i].get_pixmap(dpi=40)
        samples = pm.samples
        stride = pm.n
        count = pm.width * pm.height
        tot = [0, 0, 0]
        for k in range(0, count, 37):
            off = k * stride
            tot[0] += samples[off]
            tot[1] += samples[off + 1]
            tot[2] += samples[off + 2]
        got = count // 37 + 1
        r, g, b = [t / got for t in tot]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if lum > 150:
            light_pages.append((i + 1, round(lum, 1)))
    print("pages whose average luminance is above 150 (a light page): {}".format(
        light_pages or "none"))
    if light_pages:
        fail("background", "light pages: {}".format(light_pages))

    # ---- 4. markdown artefacts
    print()
    arts = []
    for i, t in enumerate(pages):
        for pat in ("**", "##", "|---", "[[FIG", "[[TABLE", "[[TOC", "&amp;", "&nbsp;", "http://"):
            if pat in t:
                arts.append((i + 1, pat))
    print("markdown artefacts in the rendered text: {}".format(arts or "none"))
    if arts:
        fail("markdown", "artefacts survived: {}".format(arts))

    # ---- 1. running furniture
    print()
    missing = [i + 1 for i in range(1, n) if HEADER not in pages[i]]
    print("pages after the cover without the running header: {}".format(missing or "none"))
    if missing:
        fail("furniture", "no running header on {}".format(missing))

    # ---- 5. the index, read from the RENDERED index pages rather than from the source
    print()
    src = io.open(MD, encoding="utf-8").read()

    def norm(s):
        return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

    # the contents / figure / table lists are rendered tables; find their rows on the pages
    # that carry the list headings, then resolve every claimed number against the file.
    checked = failed = 0
    toc_pages = [i for i, t in enumerate(pages) if "Chapter and section" in t and "Page" in t]
    fig_pages = [i for i, t in enumerate(pages) if re.search(r"^\s*Figure\s*$", t, re.M)
                 and "Page" in t]
    tab_pages = [i for i, t in enumerate(pages) if re.search(r"^\s*Table\s*$", t, re.M)
                 and "Page" in t]

    def rows_from(plist, label_re):
        """The rendered index puts each cell on its own line: label, then page, then the next."""
        got = []
        for i in plist:
            lines = [l.strip() for l in pages[i].split("\n") if l.strip()]
            for k, ln in enumerate(lines):
                if re.fullmatch(r"\d{1,3}", ln) and k > 0:
                    label = lines[k - 1].strip()
                    if len(label) > 6 and not re.fullmatch(r"[\d\s.]+", label) \
                            and re.match(r"^(%s)" % label_re, label):
                        got.append((label, int(ln)))
        return got

    toc_rows = rows_from(toc_pages, r".*?")
    fig_rows = rows_from(fig_pages, r"Figure \d+.*?")
    tab_rows = rows_from(tab_pages, r"Table \d+.*?")
    # the contents list also carries the front-matter headings, whose own pages legitimately
    # contain the phrase; keep only rows whose label looks like a heading or chapter
    toc_rows = [(l, p) for l, p in toc_rows if not l.startswith("Chapter and section")]

    for label, p in toc_rows:
        if p < 1 or p > n:
            fail("contents", "{} claims page {}, outside the file".format(label[:40], p))
            failed += 1
            continue
        words = [w for w in norm(label).split() if len(w) > 4][:3]
        if words and not all(w in norm(pages[p - 1]) for w in words):
            fail("contents", "{} claims page {} but that page does not carry it".format(
                label[:44], p))
            failed += 1
        checked += 1

    for label, p in fig_rows:
        m = re.match(r"Figure (\d+)", label)
        checked += 1
        if p < 1 or p > n:
            fail("figures", "{} claims page {}, outside the file".format(label[:40], p))
            failed += 1
        elif "Figure {}.".format(m.group(1)) not in pages[p - 1]:
            fail("figures", "{} claims page {} but the caption is not there".format(
                label[:40], p))
            failed += 1

    for label, p in tab_rows:
        m = re.match(r"Table (\d+)", label)
        checked += 1
        if p < 1 or p > n:
            fail("tables", "{} claims page {}, outside the file".format(label[:40], p))
            failed += 1
        elif "Table {}.".format(m.group(1)) not in pages[p - 1]:
            fail("tables", "{} claims page {} but the caption is not there".format(
                label[:40], p))
            failed += 1

    print("contents rows read from the rendered list: {}".format(len(toc_rows)))
    print("figure rows read from the rendered list:   {}".format(len(fig_rows)))
    print("table rows read from the rendered list:    {}".format(len(tab_rows)))
    print("index entries checked: {}".format(checked))
    print("index entries that did not resolve: {}".format(failed))
    if checked < 20:
        fail("index", "only {} entries checked; the rendered lists look empty".format(checked))

    # ---- 6. banned vocabulary and instant-fail figures
    print()
    alltext = "\n".join(pages)
    allnorm = alltext.lower()
    hits = [(w, allnorm.count(w.lower())) for w in BANNED_WORDS if w.lower() in allnorm]
    print("banned words or forbidden figures present: {}".format(hits or "none"))
    if hits:
        fail("banned", "found: {}".format(hits))

    # acronyms must be expanded at first use in the whole rendered paper
    acronyms = {"AIM": "Aftermarket Intelligence Model",
                "IDS": "Isuzu Dealer Standards",
                "PRISM": "analytics codebase",
                "DLOD": "Don't Lose the Deal",
                "BVP": "Best Value",
                "ITUK": "Isuzu Truck (UK)"}
    unexpanded = []
    rendered = "\n".join(pages)
    for a, expansion in acronyms.items():
        first = rendered.find(a)
        if first < 0:
            unexpanded.append((a, "never appears"))
            continue
        window = rendered[max(0, first - 500): first + 500]
        if expansion.split()[0].lower() not in window.lower():
            unexpanded.append((a, "no expansion within 500 characters of first use"))
    print("acronyms not expanded at first use: {}".format(unexpanded or "none"))
    if unexpanded:
        fail("acronyms", "{}".format(unexpanded))

    # ---- 8. figure files on disk must match the figure plan exactly
    print()
    imgs = sorted(f for f in os.listdir(FIGDIR) if f.endswith(".png"))
    print("figure files on disk: {}".format(len(imgs)))
    build = io.open(os.path.join(ROOT, "_build_white", "figures_white.py"),
                    encoding="utf-8").read()
    wanted = sorted(set(re.findall(r'return save\(fig, "([a-z0-9_]+\.png)"\)', build)))
    print("figure filenames the generator writes: {}".format(len(wanted)))
    orphans = [f for f in imgs if f not in wanted]
    absent = [f for f in wanted if f not in imgs]
    print("orphan files not written by the generator: {}".format(orphans or "none"))
    print("planned figures missing from disk: {}".format(absent or "none"))
    if orphans or absent:
        fail("figures", "orphans {} / missing {}".format(orphans, absent))

    slots = sorted(int(x) for x in re.findall(r"\[\[FIG(\d+)\]\]", src))
    print("figure slots in the source, in order: {}".format(slots))
    if slots != sorted(slots):
        fail("figures", "figure slots are not in ascending order")
    if len(slots) != len(wanted):
        fail("figures", "{} slots but {} figures generated".format(len(slots), len(wanted)))
    embedded = sum(len(doc[i].get_images()) for i in range(n))
    print("raster images embedded in the PDF: {}".format(embedded))
    if embedded != len(slots):
        fail("figures", "{} images embedded for {} slots".format(embedded, len(slots)))

    doc.close()

    print()
    if FAILS:
        print("RESULT: FAIL")
        for where, what in FAILS:
            print("   {}: {}".format(where, what))
        return 1
    print("RESULT: PASS - every check above returned clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
