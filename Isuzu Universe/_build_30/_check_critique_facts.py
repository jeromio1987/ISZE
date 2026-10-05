# -*- coding: utf-8 -*-
r"""Re-verify every numeric or counted claim the critique pack makes.

Read-only: opens the two 22 September PDFs, the GPS distributor file and the IDS dealer
network file, and prints what each claim actually reproduces to.

Run from the Isuzu Universe folder:  python _build_30\_check_critique_facts.py
"""
import csv
import os
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(os.path.dirname(ROOT), "01_data", "00_derived")

V80 = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf")
V33 = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf")
PPTX = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pptx")

out = []


def say(line=""):
    print(line)
    out.append(line)


def flat(path):
    d = fitz.open(path)
    return d, re.sub(r"\s+", " ", "".join(p.get_text() for p in d)).lower()


def paragraphs(doc):
    """Split each page into text blocks; a block of only short lines is a caption block."""
    total = 0
    caps = 0
    for p in doc:
        for blk in p.get_text("blocks"):
            txt = blk[4].strip()
            if not txt:
                continue
            total += 1
            lines = [l for l in txt.split("\n") if l.strip()]
            if len(lines) >= 2 and all(len(l.strip()) < 46 for l in lines):
                caps += 1
    return total, caps


def main():
    say("=" * 78)
    say("1  THE SCOPE BOUNDARY: WORD COUNTS IN EACH PAPER")
    say("=" * 78)
    d80, low80 = flat(V80)
    d33, low33 = flat(V33)
    say(f"80-pager pages: {d80.page_count}      33-pager pages: {d33.page_count}")
    say("")
    say(f"{'term':<16}{'80-pager':>10}{'33-pager':>10}")
    for w in ["routine", "day to day", "day-to-day", "help desk", "support ticket"]:
        say(f"{w:<16}{low80.count(w):>10}{low33.count(w):>10}")
    say("")
    for w in ["deal of the day", "aim commercial atlas", "ids development studio",
              "range & campaign planner", "pricing & margin lab",
              "prism market intelligence"]:
        say(f"{w:<26}{low80.count(w):>10}{low33.count(w):>10}")

    say("")
    say("=" * 78)
    say("2  STRUCTURE: WHERE DEAL OF THE DAY FIRST APPEARS")
    say("=" * 78)
    for i in range(d80.page_count):
        if "deal of the day" in d80[i].get_text().lower():
            say(f"first body heading appearance: page {i + 1} of {d80.page_count}")
            break
    say("reading guide (page 4) lists:")
    for ln in d80[3].get_text().split("\n"):
        if ln.strip():
            say("   " + ln.strip())

    say("")
    say("=" * 78)
    say("3  PICTURE INVENTORY")
    say("=" * 78)
    say(f"  'proposed sequence' caption:            {low80.count('proposed sequence')}")
    say(f"  'illustrative design' caption:          {low80.count('illustrative design')}")
    say(f"  'proposed feedback mechanism' caption:  {low80.count('proposed feedback mechanism')}")
    say(f"  'no measured causal effect is implied': {low80.count('no measured causal effect is implied')}")
    tot80, caps80 = paragraphs(d80)
    tot33, caps33 = paragraphs(d33)
    say(f"  80-pager text blocks {tot80}, of which caption-like {caps80}")
    say(f"  33-pager text blocks {tot33}, of which caption-like {caps33}")

    say("")
    say("=" * 78)
    say("4  CHART PAGES")
    say("=" * 78)
    for label, doc in (("80-pager", d80), ("33-pager", d33)):
        scored = []
        for i, p in enumerate(doc):
            t = p.get_text()
            axis = len(re.findall(r"(?<![A-Za-z0-9])\d+(?:k|%)?(?![A-Za-z0-9])", t))
            tick = t.lower().count("recorded isze billing") + t.lower().count("hypothetical")
            scored.append((axis, tick, i + 1))
        top = sorted(scored, reverse=True)[:6]
        say(f"  {label}: busiest pages by numeric axis text -> "
            + ", ".join(f"p{n}({a} numbers)" for a, _t, n in top))

    say("")
    say("=" * 78)
    say("5  THE ECONOMICS")
    say("=" * 78)
    rows = list(csv.DictReader(open(os.path.join(DERIVED, "gps_spu_by_distributor.csv"),
                                    encoding="utf-8-sig")))
    cols = list(rows[0].keys())
    say(f"  gps_spu_by_distributor.csv columns: {cols}")
    ycol = "year" if "year" in cols else None
    r25 = [r for r in rows if (not ycol or r.get(ycol) == "2025")]
    money = [float(r["total_sales_eur"]) for r in r25
             if r.get("total_sales_eur") not in (None, "")]
    say(f"  2025 rows {len(r25)}; rows carrying a euro figure {len(money)}")
    say(f"  network parts billed 2025: EUR {sum(money):,.2f}")
    if money:
        t = sum(money)
        say(f"  EUR 100,000 as share: {100000 / t * 100:.2f}%")
        say(f"  EUR 300,000 as share: {300000 / t * 100:.2f}%")
    uio_col = [c for c in cols if "uio" in c.lower()]
    if uio_col:
        c = uio_col[0]
        sub = [float(r["total_sales_eur"]) for r in r25 if r.get(c) not in (None, "", "0")]
        say(f"  rows with a {c} figure: {len(sub)}; their billed total EUR {sum(sub):,.2f}")

    say("")
    ids = list(csv.DictReader(open(os.path.join(DERIVED, "ids_dealer_network_cleaned_2026-09-20.csv"),
                                   encoding="utf-8-sig")))
    icols = list(ids[0].keys())
    say(f"  ids_dealer_network_cleaned_2026-09-20.csv columns: {icols}")
    say(f"  dealer rows: {len(ids)}")
    ncol = [c for c in icols if "net" in c.lower() or "country" in c.lower()]
    if ncol:
        say(f"  distinct {ncol[0]}: {len({r[ncol[0]] for r in ids if r.get(ncol[0])})}")
    scol = [c for c in icols if "points" in c.lower() or "score" in c.lower()]
    if scol:
        c = scol[0]
        vals = [float(r[c]) for r in ids if r.get(c, "").strip()]
        say(f"  rows with a {c}: {len(vals)}, min {min(vals):g}, max {max(vals):g}, "
            f"average {sum(vals) / len(vals):.1f}")
        say(f"  EUR 15,000 / {len(ids)} rows = EUR {15000 / len(ids):,.2f}")
        pt = [r for r in ids if (r.get(ncol[0]) if ncol else "") == "Portugal"] if ncol else []
        if pt:
            say(f"  Portugal rows {len(pt)} -> EUR 15,000 / {len(pt)} = "
                f"EUR {15000 / len(pt):,.2f}")
    say(f"  EUR 100,000 / EUR 2,500 = {100000 / 2500:.0f} qualifying actions")
    say(f"  EUR 300,000 / EUR 2,500 = {300000 / 2500:.0f} qualifying actions")
    say(f"  EUR 120,000 x 5% = EUR {120000 * 0.05:,.0f}")
    say(f"  20 units x EUR 30 gross profit x 5% = EUR {20 * 30 * 0.05:,.2f}")

    say("")
    say("=" * 78)
    say("6  THE COMPANION DECK")
    say("=" * 78)
    say(f"  {os.path.basename(PPTX)} exists: {os.path.exists(PPTX)} "
        f"({os.path.getsize(PPTX):,} bytes)" if os.path.exists(PPTX) else "  missing")
    try:
        from pptx import Presentation
        pr = Presentation(PPTX)
        slides = list(pr.slides)
        words = shapes = charts = pics = tbls = 0
        for s in slides:
            for sh in s.shapes:
                shapes += 1
                if sh.has_text_frame:
                    words += len(sh.text_frame.text.split())
                if sh.shape_type is not None and "CHART" in str(sh.shape_type):
                    charts += 1
                if sh.shape_type is not None and "PICTURE" in str(sh.shape_type):
                    pics += 1
                if getattr(sh, "has_table", False):
                    tbls += 1
        say(f"  slides {len(slides)}  words {words}  autoshapes {shapes}  "
            f"charts {charts}  images {pics}  tables {tbls}")
    except Exception as exc:  # noqa: BLE001
        say(f"  python-pptx not available or failed: {exc}")

    say("")
    say("=" * 78)
    say("7  LAUNCHERS AND CHECK FILES")
    say("=" * 78)
    for name in ["ISUZU_UNIVERSE_3_0_2026-09-23.pdf", "ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf",
                 "ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf",
                 "Universe_Yellow_Paper_v0.5_2026-09-22.pdf", "Universe_Opportunity_Page.html"]:
        stem = os.path.splitext(name)[0]
        sibs = [f for f in os.listdir(ROOT)
                if f.endswith(".cmd") and stem.split("_")[-1] in f]
        exact = os.path.exists(os.path.join(ROOT, "OPEN_" + stem + ".cmd"))
        say(f"  {name:<52} OPEN_<stem>.cmd: {exact}   loose .cmd matches: {sibs}")
    say("  every OPEN_*.cmd in the folder:")
    for f in sorted(os.listdir(ROOT)):
        if f.startswith("OPEN_") and f.endswith(".cmd"):
            say("     " + f)

    say("")
    say("=" * 78)
    say("8  MEASURED PRICE RESPONSE FILE")
    say("=" * 78)
    p = os.path.join(DERIVED, "pms_price_volume_response_2024_2025.csv")
    if os.path.exists(p):
        rr = list(csv.DictReader(open(p, encoding="utf-8-sig")))
        say(f"  columns: {list(rr[0].keys())}")
        for r in rr:
            say("  " + " | ".join(f"{k}={v}" for k, v in r.items()))
    else:
        say("  file not found")

    say("")
    say("=" * 78)
    say("9  ARITHMETIC RE-CHECK ON THE FLAGGED FIGURES")
    say("=" * 78)
    say(f"  120 units: 3000/25 = {3000 / 25:.0f} units; baseline 100 at 30 = EUR {100 * 30:,}, "
        f"120 units at 25 = EUR {120 * 25:,}")
    say(f"  20 additional units at 25 = EUR {20 * 25:,} + 100 baseline at 30 = "
        f"EUR {100 * 30 + 20 * 25:,}")
    say(f"  45023.33 / 47068.77 = {45023.33 / 47068.77 * 100:.1f}%")
    say(f"  Portugal 1742.60 / 29959.87 = {1742.60 / 29959.87 * 100:.1f}%")
    say(f"  ITUK (347389.58-302366.25)/347389.58 = "
        f"{(347389.58 - 302366.25) / 347389.58 * 100:.1f}%")
    say(f"  ITUK qty (4562-3402)/4562 = {(4562 - 3402) / 4562 * 100:.1f}%")

    with open(os.path.join(HERE, "_critique_facts.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    say("")
    say("written to _build_30\\_critique_facts.txt")


if __name__ == "__main__":
    main()
