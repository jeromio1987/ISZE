"""
BPR 2.0 deck layouts — house style, extended from 04_tools/ppt_template_v2.

Extra layouts beyond the v2 template:
  chapter_divider   numbered section opener
  big_numbers       a row of headline figures
  bullets_only      a text page with a right-hand callout
  two_chart         two charts side by side, one story
  chart_with_note   one chart plus a full-width note strip underneath
  table_simple      a clean table (no gridlines, alternating rows)

Brand: real Isuzu logo from the v2 assets folder, red accent, Calibri body.
"""
from __future__ import annotations

import os
import sys
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

TEMPLATE_DIR = r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ppt_template_v2"
if TEMPLATE_DIR not in sys.path:
    sys.path.insert(0, TEMPLATE_DIR)

from isze_deck_builder import (  # noqa: E402
    BLACK,
    GRAY,
    GRAY_BG,
    LIGHT_RED,
    LOGO_RED,
    RED,
    SH,
    SW,
    WHITE,
    add_footer_bar,
    add_logo,
    add_page_number,
    add_picture_fit,
    blank_slide,
    bullet_list,
    new_presentation,
    rect,
    set_white_bg,
    txt,
)

CREAM = RGBColor(0xF7, 0xF4, 0xEE)
INK_SOFT = RGBColor(0x3D, 0x3B, 0x36)
GREEN = RGBColor(0x2E, 0x6B, 0x4F)
CHARCOAL = RGBColor(0x1A, 0x1A, 0x1A)
LINE = RGBColor(0xDE, 0xD8, 0xCA) if False else RGBColor(0xDE, 0xD8, 0xCA)


# --------------------------------------------------------------- helpers --
def _measure_lines(text: str, size_pt: float, width_in: float, bold: bool) -> int:
    """Count wrapped lines using the real Calibri metrics, not a guess.

    A character-count estimate said the urgent-order title fits on one line and
    PowerPoint wrapped it onto two, straight through the rule. So this measures
    the actual glyph widths off the installed font file.
    """
    from PIL import ImageFont

    cands = [r"C:\Windows\Fonts\calibrib.ttf", r"C:\Windows\Fonts\segoeuib.ttf",
             r"C:\Windows\Fonts\arialbd.ttf"] if bold else [
        r"C:\Windows\Fonts\calibri.ttf", r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf"]
    font = None
    for c in cands:
        if os.path.exists(c):
            try:
                font = ImageFont.truetype(c, max(8, int(round(size_pt * 4))))
                break
            except OSError:
                continue
    if font is None:
        return max(1, int(len(text) * size_pt * 0.53 / (width_in * 72)) + 1)

    px_per_pt = 4
    avail_px = width_in * 72 * px_per_pt
    lines = 0
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines += 1
            continue
        cur = ""
        n = 1
        for wd in words:
            trial = (cur + " " + wd).strip()
            if font.getlength(trial) <= avail_px or not cur:
                cur = trial
            else:
                n += 1
                cur = wd
        lines += n
    return max(1, lines)


def eyebrow_and_title(slide, title, eyebrow=None, page_no=None):
    """Title that cannot cross the rule under it.

    Every title is measured against the real font. The rule is placed after the
    lines the title actually needs, and the content top is reported back so the
    body below shifts with it.
    """
    y = Inches(0.22)
    if eyebrow:
        txt(slide, eyebrow.upper(), Inches(0.32), y, Inches(12.5), Inches(0.3),
            size=11, bold=True, color=RED)
        y = Inches(0.52)

    width_in = 12.7
    size = 23.0
    lines = _measure_lines(title, size, width_in, bold=True)
    if lines > 2:
        size = 19.0
        lines = _measure_lines(title, size, width_in, bold=True)
    two_lines = lines >= 2

    box_h = Inches(0.42 * lines + 0.12)
    txt(slide, title, Inches(0.32), y, Inches(width_in), box_h, size=size,
        bold=True, color=BLACK)

    rule_y = y + box_h + Inches(0.10)
    rect(slide, Inches(0.32), rule_y, Inches(12.7), Emu(28000), RED)
    if page_no:
        add_page_number(slide, page_no)
    return rule_y + Inches(0.22)


_CONTENT_TOP: dict[int, int] = {}


def content_slide(prs, title, eyebrow=None, page_no=None):
    s = blank_slide(prs)
    set_white_bg(s)
    add_logo(s)
    add_footer_bar(s)
    _CONTENT_TOP[id(s)] = eyebrow_and_title(s, title, eyebrow=eyebrow,
                                           page_no=page_no)
    return s


# --------------------------------------------------------------- layouts --
def chapter_divider(prs, number, title, blurb=None, page_no=None):
    s = blank_slide(prs)
    set_white_bg(s)
    rect(s, 0, 0, Inches(0.30), SH, RED)
    rect(s, Inches(0.30), 0, Inches(4.35), SH, CREAM)
    txt(s, f"{number:02d}", Inches(0.72), Inches(2.25), Inches(3.4),
        Inches(1.6), size=76, bold=True, color=RED)
    txt(s, title, Inches(5.15), Inches(2.55), Inches(7.4), Inches(1.5),
        size=34, bold=True, color=BLACK)
    if blurb:
        txt(s, blurb, Inches(5.15), Inches(4.15), Inches(7.2), Inches(1.5),
            size=14, color=GRAY)
    add_logo(s, left=Inches(0.72), top=SH - Inches(1.15))
    add_footer_bar(s)
    if page_no:
        add_page_number(s, page_no)
    return s


def big_numbers(prs, title, items, eyebrow=None, page_no=None, note=None,
                per_row=4):
    """items: list of (label, value, sub). Renders as cards in the house style."""
    s = content_slide(prs, title, eyebrow=eyebrow, page_no=page_no)
    top = _CONTENT_TOP.get(id(s), Inches(1.42)) + Inches(0.10)
    rows = (len(items) + per_row - 1) // per_row
    # fit the cards into the space that is actually left, so a long title and a
    # footnote can never push the last card off the slide
    foot_h = Inches(1.05) if note else Inches(0.25)
    usable = SH - top - foot_h - Inches(0.55)
    gap = Inches(0.22)
    card_h = int((usable - gap * (rows - 1)) / rows)
    left0 = Inches(0.32)
    total_w = Inches(12.7)
    card_w = int((total_w - gap * (per_row - 1)) / per_row)
    for i, (label, value, sub) in enumerate(items):
        r, c = divmod(i, per_row)
        left = left0 + c * (card_w + gap)
        top_i = top + r * (card_h + gap)
        rect(s, left, top_i, card_w, card_h, RGBColor(0xF4, 0xF4, 0xF4))
        rect(s, left, top_i, card_w, Emu(40000), RED)
        txt(s, label.upper(), left + Inches(0.22), top_i + Inches(0.16),
            card_w - Inches(0.4), Inches(0.3), size=10.5, bold=True, color=RED)
        txt(s, str(value), left + Inches(0.22), top_i + Inches(0.50),
            card_w - Inches(0.4), Inches(0.72), size=28, bold=True, color=BLACK)
        txt(s, sub, left + Inches(0.22), top_i + card_h - Inches(0.62),
            card_w - Inches(0.4), Inches(0.55), size=11, color=GRAY)
    if note:
        txt(s, note, Inches(0.32), top + rows * (card_h + gap) + Inches(0.10),
            Inches(12.7), foot_h - Inches(0.15), size=10.5, color=GRAY)
    return s


def two_col(prs, title, chart_path, takeaways, eyebrow=None, page_no=None,
            takeaway_heading="Takeaways", chart_ratio=0.62):
    s = content_slide(prs, title, eyebrow=eyebrow, page_no=page_no)
    content_top = _CONTENT_TOP.get(id(s), Inches(1.42))
    content_h = SH - content_top - Inches(0.62)
    chart_w = int(Inches(12.7) * chart_ratio)
    add_picture_fit(s, chart_path, Inches(0.32), content_top, chart_w, content_h)
    col_left = Inches(0.32) + chart_w + Inches(0.18)
    col_w = Inches(12.7) - chart_w - Inches(0.18)
    rect(s, col_left, content_top, Emu(20000), content_h, LINE)
    txt(s, takeaway_heading.upper(), col_left + Inches(0.20),
        content_top + Inches(0.02), col_w - Inches(0.3), Inches(0.3),
        size=11, bold=True, color=RED)
    bullet_list(s, takeaways, col_left + Inches(0.20), content_top + Inches(0.42),
                col_w - Inches(0.32), content_h - Inches(0.5), size=11.5)
    return s


def two_chart(prs, title, left_chart, right_chart, eyebrow=None, page_no=None,
              left_caption=None, right_caption=None):
    s = content_slide(prs, title, eyebrow=eyebrow, page_no=page_no)
    top = _CONTENT_TOP.get(id(s), Inches(1.42))
    h = SH - top - Inches(0.62)
    half = int((Inches(12.7) - Inches(0.24)) / 2)
    add_picture_fit(s, left_chart, Inches(0.32), top, half, h - Inches(0.5))
    add_picture_fit(s, right_chart, Inches(0.32) + half + Inches(0.24), top,
                    half, h - Inches(0.5))
    if left_caption:
        txt(s, left_caption, Inches(0.32), top + h - Inches(0.42), half,
            Inches(0.4), size=11, color=GRAY)
    if right_caption:
        txt(s, right_caption, Inches(0.32) + half + Inches(0.24),
            top + h - Inches(0.42), half, Inches(0.4), size=11, color=GRAY)
    return s


def chart_with_note(prs, title, chart_path, note, eyebrow=None, page_no=None,
                    note_label="So what"):
    s = content_slide(prs, title, eyebrow=eyebrow, page_no=page_no)
    top = _CONTENT_TOP.get(id(s), Inches(1.42))
    note_h = Inches(0.95)
    chart_h = SH - top - note_h - Inches(0.72)
    add_picture_fit(s, chart_path, Inches(0.32), top, Inches(12.7), chart_h)
    strip_top = top + chart_h + Inches(0.12)
    rect(s, Inches(0.32), strip_top, Inches(12.7), note_h,
         RGBColor(0xF4, 0xF4, 0xF4))
    rect(s, Inches(0.32), strip_top, Emu(40000), note_h, RED)
    txt(s, note_label.upper(), Inches(0.52), strip_top + Inches(0.07),
        Inches(2.0), Inches(0.3), size=10.5, bold=True, color=RED)
    txt(s, note, Inches(0.52), strip_top + Inches(0.31), Inches(12.2),
        note_h - Inches(0.36), size=11.5, color=INK_SOFT)
    return s


def table_simple(prs, title, headers, rows, eyebrow=None, page_no=None,
                 note=None, col_widths=None, font_size=11.5):
    """Clean table: navy header band, alternating rows, no gridlines."""
    s = content_slide(prs, title, eyebrow=eyebrow, page_no=page_no)
    top = _CONTENT_TOP.get(id(s), Inches(1.42))
    left = Inches(0.32)
    total_w = Inches(12.7)
    ncols = len(headers)
    widths = col_widths or [total_w / ncols] * ncols
    row_h = Inches(0.42)
    # header
    rect(s, left, top, total_w, row_h, CHARCOAL)
    x = left
    for i, htxt in enumerate(headers):
        txt(s, htxt, x + Inches(0.12), top + Inches(0.055), widths[i] - Inches(0.2),
            row_h, size=font_size, bold=True, color=WHITE)
        x += widths[i]
    y = top + row_h
    for r_i, row in enumerate(rows):
        if r_i % 2 == 1:
            rect(s, left, y, total_w, row_h, RGBColor(0xF4, 0xF4, 0xF4))
        x = left
        for c_i, cell in enumerate(row):
            col = RED if c_i == 0 else BLACK
            bold = c_i == 0
            txt(s, str(cell), x + Inches(0.12), y + Inches(0.055),
                widths[c_i] - Inches(0.2), row_h, size=font_size, bold=bold,
                color=col)
            x += widths[c_i]
        y += row_h
    if note:
        txt(s, note, left, y + Inches(0.12), total_w, Inches(0.8), size=11,
            color=GRAY)
    return s


def bullets_with_callout(prs, title, bullets, callout_title, callout_body,
                         eyebrow=None, page_no=None):
    s = content_slide(prs, title, eyebrow=eyebrow, page_no=page_no)
    top = _CONTENT_TOP.get(id(s), Inches(1.42))
    left_w = Inches(8.0)
    body_h = SH - top - Inches(0.75)
    bullet_list(s, bullets, Inches(0.32), top + Inches(0.08), left_w,
                body_h, size=12)
    right_left = Inches(0.32) + left_w + Inches(0.25)
    right_w = Inches(12.7) - left_w - Inches(0.25)
    rect(s, right_left, top, right_w, body_h - Inches(0.15), CREAM)
    rect(s, right_left, top, right_w, Emu(40000), RED)
    txt(s, callout_title.upper(), right_left + Inches(0.22),
        top + Inches(0.24), right_w - Inches(0.44), Inches(0.4), size=11.5,
        bold=True, color=RED)
    txt(s, callout_body, right_left + Inches(0.22), top + Inches(0.72),
        right_w - Inches(0.44), Inches(3.6), size=12.5, color=INK_SOFT)
    return s


def cover_2(prs, title, subtitle, eyebrow="ISZE  ·  VEHICLE PARTS & ACCESSORIES",
            meta=None):
    s = blank_slide(prs)
    set_white_bg(s)
    rect(s, 0, 0, Inches(0.22), SH, RED)
    rect(s, Inches(0.22), 0, Inches(0.10), SH, CHARCOAL)
    txt(s, eyebrow, Inches(0.62), Inches(0.55), Inches(10), Inches(0.4),
        size=12, bold=True, color=RED)
    txt(s, title, Inches(0.62), Inches(2.05), Inches(11.6), Inches(2.4),
        size=40, bold=True, color=BLACK)
    txt(s, subtitle, Inches(0.62), Inches(4.30), Inches(9.6), Inches(0.6),
        size=16, color=GRAY)
    if meta:
        txt(s, meta, Inches(0.62), Inches(5.05), Inches(11.0), Inches(0.5),
            size=12, color=GRAY)
    s.shapes.add_picture(LOGO_RED, Inches(0.62), SH - Inches(1.05),
                         height=Inches(0.42))
    add_footer_bar(s)
    return s


def new_deck():
    return new_presentation()
