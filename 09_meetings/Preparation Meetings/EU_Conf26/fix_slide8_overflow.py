# -*- coding: utf-8 -*-
"""Fix slide 8 layout: keep text inside column boxes and restore footer icon row."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Pt

FILES = [
    Path(r"C:\Users\jerom\Downloads\EU Conf 26 ISZE Parts Sales 20260608 CLEAN.pptx"),
    Path(
        r"C:\Users\jerom\Desktop\claude\ISZE\Preparation Meetings\EU_Conf26"
        r"\EU Conf 26 ISZE Parts Sales 20260608 CLEAN.pptx"
    ),
]

RED = RGBColor(0xD2, 0x00, 0x00)
GRAY = RGBColor(0x64, 0x64, 0x64)
BLACK = RGBColor(0x24, 0x24, 0x24)

# Column boxes on slide 8 (CLEAN deck coordinates)
LEFT_BOX = {"left": 932688, "top": 2057400, "width": 5166360, "height": 3090672}
RIGHT_BOX = {"left": 6382512, "top": 2057400, "width": 5166360, "height": 3090672}
PAD_X = 180000
PAD_TOP = 155000

# Footer row — five evenly spaced items (from MH CHK layout, shifted for CLEAN box)
FOOTER_ICONS = {
    "Oval 23": 1207008,
    "Oval 26": 3264408,
    "Oval 29": 5321808,
    "Oval 32": 7381208,
    "Oval 35": 9436608,
    "TextBox 24": 1207008,
    "TextBox 27": 3264408,
    "TextBox 30": 5321808,
    "TextBox 33": 7381208,
    "TextBox 36": 9436608,
    "TextBox 25": 1719072,
    "TextBox 28": 3776472,
    "TextBox 31": 5833872,
    "TextBox 34": 7891272,
    "TextBox 37": 9948672,
}
FOOTER_ICON_TOP = 5532120
FOOTER_EMOJI_TOP = 5568696
FOOTER_LABEL_TOP = 5614416

# Column headers
LEFT_ICON_LEFT = 1143000
LEFT_TITLE_LEFT = 1911096
RIGHT_ICON_LEFT = 6592824
RIGHT_TITLE_LEFT = 7360920
HEADER_TOP = 2212848
ICON_TOP = 2240280
EMOJI_TOP = 2276856
SUBTITLE_TOP = 2542032


def set_multiline(
    shape,
    lines: list[tuple[str, float, bool, RGBColor]],
    *,
    left: int | None = None,
    top: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> None:
    if left is not None:
        shape.left = left
    if top is not None:
        shape.top = top
    if width is not None:
        shape.width = width
    if height is not None:
        shape.height = height
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.margin_left = Pt(2)
    tf.margin_right = Pt(2)
    tf.margin_top = Pt(1)
    tf.margin_bottom = Pt(1)
    for i, (text, size_pt, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(2)
        run = p.add_run()
        run.text = text
        run.font.name = "Arial"
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.color.rgb = color


def place(shape, *, left: int, top: int | None = None) -> None:
    shape.left = left
    if top is not None:
        shape.top = top


def fix_footer_and_headers(slide) -> None:
    for sh in slide.shapes:
        name = sh.name or ""
        if name in FOOTER_ICONS:
            place(sh, left=FOOTER_ICONS[name])
            if name.startswith("Oval"):
                sh.top = FOOTER_ICON_TOP
            elif name in ("TextBox 24", "TextBox 27", "TextBox 30", "TextBox 33", "TextBox 36"):
                sh.top = FOOTER_EMOJI_TOP
            elif name in ("TextBox 25", "TextBox 28", "TextBox 31", "TextBox 34", "TextBox 37"):
                sh.top = FOOTER_LABEL_TOP
                sh.width = 1280160
        elif name == "Oval 7":
            place(sh, left=LEFT_ICON_LEFT, top=ICON_TOP)
        elif name == "Oval 15":
            place(sh, left=RIGHT_ICON_LEFT, top=ICON_TOP)
        elif name == "TextBox 8":
            place(sh, left=LEFT_ICON_LEFT, top=EMOJI_TOP)
        elif name == "TextBox 16":
            place(sh, left=RIGHT_ICON_LEFT, top=EMOJI_TOP)
        elif name == "TextBox 9":
            set_multiline(
                sh,
                [("GPS", 16, True, RED)],
                left=LEFT_TITLE_LEFT,
                top=HEADER_TOP,
                width=1463040,
                height=320040,
            )
        elif name == "TextBox 17":
            set_multiline(
                sh,
                [("PMS Coverage", 16, True, RED)],
                left=RIGHT_TITLE_LEFT,
                top=HEADER_TOP,
                width=2560320,
                height=320040,
            )


def fix_slide_8_columns(slide) -> None:
    # Align body copy with the title row (right of the icon), not under the icon.
    left_x = LEFT_TITLE_LEFT
    right_x = RIGHT_TITLE_LEFT
    left_w = LEFT_BOX["left"] + LEFT_BOX["width"] - PAD_X - left_x
    right_w = RIGHT_BOX["left"] + RIGHT_BOX["width"] - PAD_X - right_x
    y0 = LEFT_BOX["top"] + PAD_TOP

    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()

        if t == "Genuine Parts Share (GPS)":
            set_multiline(
                sh,
                [("Genuine Parts Share (GPS)", 13, True, BLACK)],
                left=left_x,
                top=y0 + 330000,
                width=left_w,
                height=260000,
            )
        elif t == "Broad lens across all genuine part numbers.":
            set_multiline(
                sh,
                [("Broad lens across all genuine part numbers.", 11, False, GRAY)],
                left=left_x,
                top=y0 + 730000,
                width=left_w,
                height=240000,
            )
        elif "Actual genuine sales" in t and "GPS" in t:
            set_multiline(
                sh,
                [
                    ("Actual genuine sales ÷ Estimated parts demand", 12, True, RED),
                    ("= GPS %", 12, True, RED),
                ],
                left=left_x,
                top=y0 + 1290000,
                width=left_w,
                height=460000,
            )
        elif t.startswith("Same logic as PMS"):
            set_multiline(
                sh,
                [("Same logic as PMS: actual, estimate, coverage — full parts basket.", 10, False, GRAY)],
                left=left_x,
                top=y0 + 1880000,
                width=left_w,
                height=420000,
            )
        elif t == "Periodic Maintenance Service parts capture" or t.startswith(
            "Periodic Maintenance Service"
        ):
            set_multiline(
                sh,
                [
                    ("Periodic Maintenance Service", 12, True, BLACK),
                    ("parts capture", 12, True, BLACK),
                ],
                left=right_x,
                top=y0 + 330000,
                width=right_w,
                height=300000,
            )
        elif t == "Focused lens on competitive, interval-driven parts.":
            set_multiline(
                sh,
                [("Focused lens on competitive, interval-driven parts.", 11, False, GRAY)],
                left=right_x,
                top=y0 + 730000,
                width=right_w,
                height=240000,
            )
        elif "Actual PMS sales" in t and "Coverage" in t:
            set_multiline(
                sh,
                [
                    ("Actual PMS sales ÷ Estimated PMS demand", 12, True, RED),
                    ("= Coverage %", 12, True, RED),
                ],
                left=right_x,
                top=y0 + 1220000,
                width=right_w,
                height=460000,
            )
        elif t.startswith("Pinpoints leakage") or t.startswith("Used to pinpoint leakage"):
            set_multiline(
                sh,
                [
                    (
                        "Pinpoints leakage in filters, brake, clutch, lubricants and other PMS items.",
                        10,
                        False,
                        GRAY,
                    )
                ],
                left=right_x,
                top=y0 + 1810000,
                width=right_w,
                height=420000,
            )


def fix_slide_9_footer(slide) -> None:
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if t.startswith("GPS = Actual genuine") or t.startswith("PMS Coverage = Actual"):
            set_multiline(
                sh,
                [
                    ("GPS = Actual genuine sales ÷ Estimated parts demand", 10, True, RED),
                    ("PMS Coverage = Actual PMS sales ÷ Estimated PMS demand", 10, True, RED),
                ],
                width=10195560,
                height=400000,
            )
        elif t.startswith("Scope is refined per market"):
            tf = sh.text_frame
            tf.word_wrap = True
            tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE


def main() -> None:
    src = FILES[0]
    if not src.exists():
        raise SystemExit(f"Missing {src}")

    backup = src.with_name(src.stem + f"_pre_slide8_layout_{datetime.now():%Y%m%d_%H%M}.pptx")
    shutil.copy2(src, backup)
    print("Backup:", backup)

    prs = Presentation(str(src))
    slide = prs.slides[7]
    fix_footer_and_headers(slide)
    fix_slide_8_columns(slide)
    fix_slide_9_footer(prs.slides[8])

    for out in FILES:
        try:
            prs.save(str(out))
            print("Saved", out)
        except PermissionError:
            alt = out.with_name(out.stem + "_NEW.pptx")
            prs.save(str(alt))
            print("LOCKED — saved", alt)


if __name__ == "__main__":
    main()
