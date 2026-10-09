# -*- coding: utf-8 -*-
"""
Ring builder for the kickback management deck, 2026-10-07.

Draws a genuine circular continuous-improvement cycle: a thin open-centre arc
ring with four step boxes sitting ON the ring at the four cardinal points, and
chevron arrows BETWEEN them so the direction of travel is visible and the loop
visibly closes.

Design rules learned from the two earlier failures:
  * the ring is a THIN TRACK, not a filled donut, so the centre stays open and
    the centre caption sits inside the hole;
  * the step boxes sit ON the ring at 0/90/180/270 degrees, and the arrows sit
    BETWEEN the boxes, so nothing overlaps a box;
  * the centre caption is added AFTER the ring, so it is above it in z-order.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
DECK = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"

RED = RGBColor(0xE3, 0x06, 0x13)
INK = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
PANEL = RGBColor(0x30, 0x30, 0x30)
BG = RGBColor(0x26, 0x26, 0x26)
GOLD = RGBColor(0xC8, 0x9B, 0x3C)
FONT = "Aptos"

# --- ring geometry, in inches on the slide ---------------------------------
CX, CY = 6.663, 4.72           # ring centre
R_OUT = 2.28                   # ring outer radius
R_IN = 2.06                    # ring inner radius -> open centre of 4.12 in
TRACK = 0.115                  # arc stroke


def set_fill(shape, rgb):
    if rgb is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb


def set_line(shape, rgb, pt):
    if rgb is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb
        shape.line.width = Pt(pt)


def no_shadow(shape):
    try:
        shape.shadow.inherit = False
    except Exception:
        pass


def text(shape, lines, size, rgb, bold=False, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, space_after=0):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    first = True
    for line in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = rgb
    return shape


def arc(slide, cx, cy, r, a0, a1, width, rgb):
    """Draw one arc segment between angles a0 and a1 (degrees, 0 = 3 o'clock,
    clockwise because PowerPoint's y axis points down).

    An ARC preset is a pie slice of its bounding ellipse whose start/end angles
    live in `adj1`/`adj2` (60000ths of a degree), with a /360 adjustment guide.
    A -360 start is what PowerPoint itself refuses to reopen, so full-width
    sweeps are split into 180-degree halves and each half is emitted with its
    own pair of sectors rather than one 360-degree run.
    """
    end_raw = -a1
    start_raw = -a0
    left = Inches(cx - r)
    top = Inches(cy - r)
    size = Inches(2 * r)
    sh = slide.shapes.add_shape(MSO_SHAPE.ARC, left, top, size, size)
    sh.name = "RingArc"
    sh.adjustments[0] = start_raw
    sh.adjustments[1] = end_raw
    set_fill(sh, None)
    set_line(sh, rgb, width)
    no_shadow(sh)
    return sh


def ring_track(slide, cx, cy, r, width, rgb):
    """The ring itself: an unfilled, thin-stroked oval, so the centre is open.

    Deliberately NOT a donut and NOT arcs for the track: a filled donut hides
    the centre caption, and spanning a full circle with ARC adjustments is the
    thing that produced an unopenable file. An oval outline is a single
    well-formed shape with no adjustment maths at all.
    """
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                Inches(cx - r), Inches(cy - r),
                                Inches(2 * r), Inches(2 * r))
    sh.name = "RingTrack"
    set_fill(sh, None)
    set_line(sh, rgb, width)
    no_shadow(sh)
    return sh


def box_slot(slide, cx, cy, r, ang, w=2.70, h=1.02):
    """A step box centred at radius r and angle ang on the ring."""
    a = math.radians(ang)
    x = cx + r * math.cos(a) - w / 2
    y = cy + r * math.sin(a) - h / 2
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    sh.name = "RingStep"
    sh.adjustments[0] = 0.10
    set_fill(sh, PANEL)
    set_line(sh, RED, 1.5)
    no_shadow(sh)
    return sh


def label(slide, x, y, w, h, lines, size, rgb, bold=False, align=PP_ALIGN.CENTER):
    sh = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    sh.name = "RingLabel"
    text(sh, lines, size, rgb, bold=bold, align=align)
    sh.text_frame.auto_size = None
    return sh


def marker(slide, cx, cy, r, ang, rgb, size=0.34):
    """A chevron on the ring at angle ang, pointing along the direction of travel.

    All arguments are in INCHES for the ring centre and radius. An earlier
    version of this helper was handed Emu values and added an inch-based radius
    to them, which placed the chevrons millions of EMU off the slide and made
    the file unopenable; keep the units consistent here.
    """
    a = math.radians(ang)
    px = cx + r * math.cos(a)
    py = cy + r * math.sin(a)
    # PowerPoint chevrons point to the right; a clockwise ring at angle a moves
    # in direction a + 90 degrees, so the shape is rotated by a + 90.
    sh = slide.shapes.add_shape(MSO_SHAPE.CHEVRON,
                                Inches(px - size * 1.25 / 2), Inches(py - size / 2),
                                Inches(size * 1.25), Inches(size))
    sh.name = "RingArrow"
    set_fill(sh, rgb)
    set_line(sh, None, 0)
    no_shadow(sh)
    sh.rotation = (ang + 90) % 360
    return sh


def build_ring(prs, slide_no, steps, caption_lines, ring_rgb=RED,
               caption_rgb=INK, caption_size=10.5, arrow_rgb=RED,
               arrows=True, cx=CX, cy=CY):
    """Replace whatever box-flow is on the slide with the ring."""
    slide = prs.slides[slide_no - 1]

    # --- clear the previous flow: boxes, bars and step labels only
    for sh in list(slide.shapes):
        if sh.name in ("RingStep", "RingLabel", "RingArrow", "RingArc",
                       "Oval 8", "TextBox 9"):
            sh._element.getparent().remove(sh._element)
        elif sh.name.startswith("Rounded Rectangle") or sh.name.startswith("Rectangle "):
            sh._element.getparent().remove(sh._element)
        elif sh.has_text_frame and sh.text_frame.text.strip().startswith(("1  ·", "2  ·", "3  ·", "4  ·")):
            sh._element.getparent().remove(sh._element)

    # --- ring: a thin unfilled track, so the centre stays open
    ring_track(slide, cx, cy, (R_OUT + R_IN) / 2, TRACK * 72, ring_rgb)

    # --- chevrons BETWEEN the boxes, on the ring, showing the direction of travel
    if arrows:
        for ang in (45, 135, 225, 315):
            marker(slide, cx, cy, (R_OUT + R_IN) / 2, ang, arrow_rgb, size=0.34)

    # --- four step boxes, ON the ring at the four cardinal points
    for ang, (tag, body) in zip((270, 0, 90, 180), steps):
        sh = box_slot(slide, cx, cy, (R_OUT + R_IN) / 2, ang)
        text(sh, [tag, body], 8.6, INK, bold=False, align=PP_ALIGN.CENTER)
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(8.6)
        sh.text_frame.paragraphs[0].runs[0].font.size = Pt(7.4)
        sh.text_frame.paragraphs[0].runs[0].font.color.rgb = GOLD
        sh.text_frame.paragraphs[0].runs[0].font.bold = True

    # --- the centre caption, added LAST so it sits above the ring
    label(slide, cx - 1.42, cy - 0.62, 2.84, 1.24, caption_lines,
          caption_size, caption_rgb, align=PP_ALIGN.CENTER)
    return slide


if __name__ == "__main__":
    prs = Presentation(str(DECK))
    build_ring(
        prs, 20,
        steps=[("CONFIRM", "Confirm the monthly plan for each distributor"),
               ("CHECK AT MONTH 6", "Against the 10% tolerance"),
               ("CHECK AT MONTH 9", "Against the 10% tolerance"),
               ("ACT", "Close the reporting gaps and load ISD Feb-Jul 2026")],
        caption_lines=["A CYCLE,", "NOT A SINGLE", "APPROVAL",
                       "The plan is reset from the agreed",
                       "monthly targets after every checkpoint."],
    )
    prs.save(str(DECK))
    print("ring drawn on physical 20")
