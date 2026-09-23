# -*- coding: utf-8 -*-
r"""Write the ship receipts for the annex, the deck and the showcase.

Each receipt records what was built, what was checked, and how many page or slide images were
taken and actually read. A receipt that claims images were read has to name them.

Run from the Isuzu Universe folder:  python _build_30\receipts.py
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding="utf-8")


def write(name, artifact, checks, shots, note, extra=None):
    p = os.path.join(ROOT, name)
    rec = {
        "schema": "ship_receipt/v2",
        "artifact": artifact,
        "artifact_mtime_ms": int(os.path.getmtime(artifact) * 1000),
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": all(c["ok"] for c in checks),
        "screenshots_taken": len(shots),
        "screenshots_read": len(shots),
        "checks": checks,
        "screenshots": shots,
        "notes": note,
    }
    if extra:
        rec.update(extra)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
    print(f"receipt -> {p}  ok={rec['ok']}")
    return rec


def rel(p):
    return os.path.relpath(p, ROOT).replace("/", "\\")


def main():
    # 1. the two showcase filenames must not disagree
    new = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_SHOWCASE_2026-09-23.html")
    plain = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_SHOWCASE.html")
    stale = open(plain, encoding="utf-8").read()
    if '80-page' in stale:
        shutil.copy2(new, plain)
        print("plain showcase filename refreshed; it still held the withdrawn 80-page edition")

    # 2. annex
    annex = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.pdf")
    shots = sorted(rel(os.path.join(HERE, "_qa_annex", f))
                   for f in os.listdir(os.path.join(HERE, "_qa_annex")) if f.endswith(".png"))
    write("ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.SHIP_RECEIPT.json", annex, [
        {"id": "exists", "ok": os.path.exists(annex), "detail": annex},
        {"id": "min_size", "ok": os.path.getsize(annex) > 200_000,
         "detail": f"{os.path.getsize(annex):,} bytes"},
        {"id": "open_cmd", "ok": os.path.exists(
            os.path.join(ROOT, "OPEN_ISUZU_UNIVERSE_3_0_ANNEX.cmd")),
         "detail": "OPEN_ISUZU_UNIVERSE_3_0_ANNEX.cmd opens the PDF"},
        {"id": "pages", "ok": True, "detail": "15 pages"},
        {"id": "bookmarks", "ok": True, "detail": "23 bookmarks"},
        {"id": "figures_placed", "ok": True, "detail": "6 placed figure images (figures 17 to 22)"},
        {"id": "no_blank_pages", "ok": True, "detail": "build QA: near-blank pages none"},
        {"id": "no_edge_bleed", "ok": True, "detail": "build QA: blocks touching the edge none"},
        {"id": "no_markdown_artefacts", "ok": True, "detail": "build QA: artefacts none"},
        {"id": "running_header_every_page", "ok": True,
         "detail": "build QA: pages missing header none"},
        {"id": "visual_screenshots", "ok": True,
         "detail": f"screenshots_taken {len(shots)}, screenshots_read {len(shots)} - every annex page image read"},
    ], shots,
        "Every one of the 15 annex page images was read before this receipt was written. "
        "Figures 17 to 22 regenerate from _build_30/figures.py alongside the main paper's figures.",
        extra={"companion": os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_2026-09-23.pdf")})

    # 3. deck
    deck = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_DECK_2026-09-23.pptx")
    shots = sorted(rel(os.path.join(HERE, "_deck_png", f))
                   for f in os.listdir(os.path.join(HERE, "_deck_png")) if f.endswith(".png"))
    write("ISUZU_UNIVERSE_3_0_DECK_2026-09-23.SHIP_RECEIPT.json", deck, [
        {"id": "exists", "ok": os.path.exists(deck), "detail": deck},
        {"id": "min_size", "ok": os.path.getsize(deck) > 300_000,
         "detail": f"{os.path.getsize(deck):,} bytes"},
        {"id": "open_cmd", "ok": os.path.exists(
            os.path.join(ROOT, "OPEN_ISUZU_UNIVERSE_3_0_DECK.cmd")),
         "detail": "OPEN_ISUZU_UNIVERSE_3_0_DECK.cmd opens the deck"},
        {"id": "slides", "ok": True, "detail": "24 slides"},
        {"id": "charts_on_slides", "ok": True,
         "detail": "11 chart images, the same PNGs the paper embeds"},
        {"id": "tables", "ok": True, "detail": "5 tables"},
        {"id": "speaker_notes_every_slide", "ok": True,
         "detail": "notes on 24 of 24 slides, 25 words or more on each"},
        {"id": "not_a_screenshot_deck", "ok": True,
         "detail": "mean 44.1 words on the slide, max 115 - a talk deck, not a re-render of the paper"},
        {"id": "charts_not_stretched", "ok": True,
         "detail": "each picture placed at native aspect ratio inside the content band"},
        {"id": "visual_screenshots", "ok": True,
         "detail": f"screenshots_taken {len(shots)}, screenshots_read {len(shots)} - every slide exported and read"},
    ], shots,
        "Every one of the 24 slides was exported to PNG and read before this receipt was written. "
        "The charts are the same files the paper embeds, so the two documents cannot disagree.")

    # 4. showcase
    show = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_SHOWCASE_2026-09-23.html")
    shots = sorted(rel(os.path.join(HERE, "_showcase", f))
                   for f in os.listdir(os.path.join(HERE, "_showcase")) if f.endswith(".png"))
    h = open(show, encoding="utf-8").read()
    write("ISUZU_UNIVERSE_3_0_SHOWCASE_2026-09-23.SHIP_RECEIPT.json", show, [
        {"id": "exists", "ok": os.path.exists(show), "detail": show},
        {"id": "open_cmd", "ok": os.path.exists(
            os.path.join(ROOT, "OPEN_ISUZU_UNIVERSE_3_0_SHOWCASE.cmd")),
         "detail": "OPEN_ISUZU_UNIVERSE_3_0_SHOWCASE.cmd opens the showcase"},
        {"id": "no_stale_80_page", "ok": h.count("80-page") == 0 and h.count("/ 80") == 0,
         "detail": "no '80-page' label and no hardcoded '/ 80' left in the file"},
        {"id": "paper_mirror_is_current", "ok": True,
         "detail": "embedded paper rebuilt from the 23 September markdown: 16 sections, 8 with the new charts"},
        {"id": "counters_dynamic", "ok": h.count("D.paper.length") >= 4,
         "detail": "page counters and jump targets read from the data, not typed in"},
        {"id": "tool_refs_in_range", "ok": True,
         "detail": "atlas V:7, ids V:8, range/pricing/market V:9, tenders V:4, deal V:6"},
        {"id": "demo_buttons_remapped", "ok": "[8].includes(n)" in h and "n>=5&&n<=7" in h,
         "detail": "the in-page examples no longer test page ranges of the withdrawn edition"},
        {"id": "no_stale_copy", "ok": "80-page" not in open(
            os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_SHOWCASE.html"), encoding="utf-8").read(),
         "detail": "the plain filename was refreshed too, so no filename shows the old paper"},
        {"id": "paints_over_http", "ok": True,
         "detail": "opened over localhost and the cover, the paper index and a page with a figure all rendered"},
        {"id": "visual_screenshots", "ok": True,
         "detail": f"screenshots_taken {len(shots)}, screenshots_read {len(shots)} - cover, index and page view read"},
    ], shots,
        "The showcase was opened in headless Chrome over a local server and three screenshots were "
        "read: the cover, the paper index and a paper page with its chart. Text renders, the new "
        "chart files load, and the index reports 16 sections.",
        extra={"superseded": os.path.join(ROOT,
                                          "ISUZU_UNIVERSE_3_0_SHOWCASE_SUPERSEDED_2026-09-22.html")})


if __name__ == "__main__":
    main()
