# -*- coding: utf-8 -*-
"""Remove MH review markup and fix GPS/PMS slides 6-9 in EU Conf deck."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Pt

SRC = Path(r"C:\Users\jerom\Downloads\EU Conf 26 ISZE Parts Sales 20260608 MH CHK.pptx")
BACKUP = SRC.with_name(SRC.stem + "_backup_" + datetime.now().strftime("%Y%m%d_%H%M") + ".pptx")

RED = RGBColor(0xD2, 0x00, 0x00)
GRAY = RGBColor(0x64, 0x64, 0x64)
BLACK = RGBColor(0x24, 0x24, 0x24)


def remove_shape(shape) -> None:
    el = shape._element
    el.getparent().remove(el)


def set_run_text(shape, text: str, *, size_pt: float | None = None, bold: bool | None = None,
                 color: RGBColor | None = None, font_name: str = "Arial") -> None:
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = ""
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    if size_pt is not None:
        run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def replace_in_shapes(slide, old: str, new: str) -> None:
    for sh in slide.shapes:
        if sh.has_text_frame and old in sh.text_frame.text:
            set_run_text(sh, sh.text_frame.text.replace(old, new))


def remove_by_name_prefix(slide, *prefixes: str) -> int:
    removed = 0
    for sh in list(slide.shapes):
        name = sh.name or ""
        if any(name.startswith(p) for p in prefixes):
            remove_shape(sh)
            removed += 1
    return removed


def remove_speech_bubbles(slide) -> int:
    removed = 0
    for sh in list(slide.shapes):
        name = sh.name or ""
        if "Speech Bubble" in name:
            remove_shape(sh)
            removed += 1
        elif sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t in ("VIN?", "Text overflow") or t.startswith("Use the same logic"):
                remove_shape(sh)
                removed += 1
    return removed


def remove_yellow_review_shapes(slide) -> int:
    """Remove yellow ovals / arrows MH added (no fill text, large oval overlays)."""
    removed = 0
    for sh in list(slide.shapes):
        name = sh.name or ""
        if name in ("Oval 42", "Oval 57"):
            remove_shape(sh)
            removed += 1
            continue
        if "Straight Arrow Connector" in name or name == "Connector 60":
            remove_shape(sh)
            removed += 1
    return removed


def fix_slide_6(prs) -> None:
    replace_in_shapes(
        prs.slides[5],
        "Periodic Maintenance system",
        "Periodic Maintenance Service",
    )


def fix_slide_7(prs) -> None:
    replace_in_shapes(prs.slides[6], "first?", "first")


def fix_slide_8(prs) -> None:
    slide = prs.slides[7]
    remove_speech_bubbles(slide)
    remove_yellow_review_shapes(slide)

    # GPS column — mirror PMS formula styling (shape indices stable in this deck)
    by_idx = {i: slide.shapes[i] for i in range(len(slide.shapes))}
    # Re-fetch after removals — indices shift; match by original names via scan
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        name = sh.name or ""
        if name == "TextBox 10" or t == "Genuine Parts Spend per Unit":
            set_run_text(sh, "Genuine Parts Share (GPS)", size_pt=14, bold=True, color=BLACK)
        elif t.startswith("Net Sales EUR"):
            set_run_text(
                sh,
                "Actual genuine sales  ÷  Estimated parts demand  =  GPS %",
                size_pt=14,
                bold=True,
                color=RED,
            )
        elif t.startswith("Used to benchmark total parts performance"):
            set_run_text(
                sh,
                "Same logic as PMS: actual, estimate, coverage — applied to the full genuine parts basket.",
                size_pt=12,
                bold=False,
                color=GRAY,
            )


def fix_slide_9(prs) -> None:
    slide = prs.slides[8]
    remove_speech_bubbles(slide)
    remove_yellow_review_shapes(slide)

    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.replace("\x0b", "\n").strip()
        name = sh.name or ""

        if t == "GPS — broad benchmark across all part numbers":
            set_run_text(
                sh,
                "GPS — same actual / estimate / coverage logic, full parts basket",
                size_pt=12,
                bold=False,
                color=BLACK,
            )
        elif "All genuine PN" in t and "net sales" in t:
            set_run_text(sh, "Estimated\nparts demand", size_pt=11, bold=True, color=BLACK)
        elif t.replace("\n", " ") == "UIO vehicle parc":
            set_run_text(sh, "Actual genuine\ninvoiced sales", size_pt=11, bold=True, color=BLACK)
        elif t == "€/vehicle/year":
            set_run_text(sh, "GPS %\n(coverage)", size_pt=11, bold=True, color=BLACK)
        elif t.startswith("PMS Coverage = Actual"):
            set_run_text(
                sh,
                "GPS = Actual genuine invoiced sales ÷ Estimated total parts demand    ·    "
                "PMS Coverage = Actual ISZE invoiced PMS sales ÷ Estimated potential PMS demand",
                size_pt=11,
                bold=True,
                color=RED,
            )


def fix_slide_11(prs) -> None:
    slide = prs.slides[10]
    remove_speech_bubbles(slide)
    for sh in slide.shapes:
        if sh.has_text_frame and "reporting for reporting" in sh.text_frame.text:
            set_run_text(
                sh,
                "The goal is real parts opportunities — not reporting for reporting's sake.",
                size_pt=12,
                bold=True,
                color=BLACK,
            )


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Missing source deck: {SRC}")

    shutil.copy2(SRC, BACKUP)
    print(f"Backup: {BACKUP}")

    prs = Presentation(str(SRC))
    fix_slide_6(prs)
    fix_slide_7(prs)
    fix_slide_8(prs)
    fix_slide_9(prs)
    fix_slide_11(prs)

    prs.save(str(SRC))
    print(f"Saved: {SRC}")

    # Verify
    prs2 = Presentation(str(SRC))
    s8 = prs2.slides[7]
    bad = []
    for sh in s8.shapes:
        name = sh.name or ""
        if "Speech Bubble" in name or name in ("Oval 42",):
            bad.append(name)
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t in ("VIN?", "Text overflow") or t.startswith("Use the same logic"):
                bad.append(t)
            if "Net Sales EUR" in t:
                bad.append("old GPS formula")
    print("Slide 8 issues remaining:", bad or "none")


if __name__ == "__main__":
    main()
