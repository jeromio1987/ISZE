# -*- coding: utf-8 -*-
"""Probe 3: the real ring construction.

Tests
  A  four ARC segments using (5,85)(95,175)(185,265)(275,355)
  B  ARC whose range includes 0  -> (0,88) and (352,360) forms
  C  BLOCK_ARC with explicit adjustments
  D  freeform arrowhead polygons at computed bearings
  E  thin full DONUT guide ring (hole 0.94) under the arcs
"""
import math
import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(OUT_DIR, "_ring_probe3.pptx")

BG = RGBColor(0x26, 0x26, 0x26)
RED = RGBColor(0xE3, 0x06, 0x13)
WHITE = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
GREEN = RGBColor(0x31, 0xA3, 0x54)
AMBER = RGBColor(0xF5, 0xA0, 0x00)
PANEL = RGBColor(0x30, 0x30, 0x30)
GREY = RGBColor(0x4B, 0x4B, 0x4B)
FONT = "Aptos"

prs = Presentation()
prs.slide_width = Inches(13.3333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]
s = prs.slides.add_slide(blank)
f = s.background.fill
f.solid()
f.fore_color.rgb = BG


def label(x, y, w, h, t, size=8.5, color=MUTED):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = False
    r = tf.paragraphs[0].add_run()
    r.text = t
    r.font.size = Pt(size)
    r.font.name = FONT
    r.font.color.rgb = color
    return tb


def arc(x, y, d, a1, a2, color=RED, lw=10, tag=""):
    sh = s.shapes.add_shape(MSO_SHAPE.ARC, Inches(x), Inches(y), Inches(d), Inches(d))
    sh.shadow.inherit = False
    sh.fill.background()
    sh.line.color.rgb = color
    sh.line.width = Pt(lw)
    sh.adjustments[0] = a1
    sh.adjustments[1] = a2
    return sh


def donut(x, y, d, hole, color=GREY):
    sh = s.shapes.add_shape(MSO_SHAPE.DONUT, Inches(x), Inches(y), Inches(d), Inches(d))
    sh.shadow.inherit = False
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.adjustments[0] = hole
    return sh


def blockarc(x, y, d, a1, a2, thick, color=AMBER):
    sh = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, Inches(x), Inches(y), Inches(d), Inches(d))
    sh.shadow.inherit = False
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    for i, v in enumerate((a1, a2, thick)):
        try:
            sh.adjustments[i] = v
        except Exception as e:
            print("blockarc adj", i, "fail", e)
    return sh


def arrowhead(cx, cy, bearing_deg, size_in, color=AMBER):
    """triangle pointing outward along bearing (0 = 3 o'clock, clockwise)."""
    a = math.radians(bearing_deg)
    ux, uy = math.cos(a), math.sin(a)
    px_, py_ = -uy, ux
    tip = (cx + ux * size_in, cy + uy * size_in)
    b1 = (cx - px_ * size_in * 0.72, cy - py_ * size_in * 0.72)
    b2 = (cx + px_ * size_in * 0.72, cy + py_ * size_in * 0.72)
    fb = s.shapes.build_freeform(Emu(int(tip[0] * 914400)), Emu(int(tip[1] * 914400)), 1.0)
    fb.add_line_segments([
        (Emu(int(b1[0] * 914400)), Emu(int(b1[1] * 914400))),
        (Emu(int(b2[0] * 914400)), Emu(int(b2[1] * 914400))),
    ], close=True)
    sh = fb.convert_to_shape()
    sh.shadow.inherit = False
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


print("A: four ARC segments (5,85)(95,175)(185,265)(275,355) on a 3.4in disc at x=0.6")
D1 = 3.4
for a1, a2 in ((5, 85), (95, 175), (185, 265), (275, 355)):
    arc(0.6, 0.7, D1, a1, a2, RED, 14, "%d-%d" % (a1, a2))
label(0.6, 4.25, 5, 0.3, "A: four arcs, angles clockwise from 3 o'clock")

print("B: ARC with a 0 endpoint, and a near-0 pair")
arc(4.6, 0.7, D1 / 2, 0, 88, GREEN, 12, "0-88")
arc(6.4, 0.7, D1 / 2, 352, 360, AMBER, 12, "352-360")
arc(8.2, 0.7, D1 / 2, 100, 190, GREEN, 12, "100-190")
arc(10.0, 0.7, D1 / 2, 4, 92, AMBER, 12, "4-92")
label(4.6, 4.25, 6.4, 0.3, "B: (0,88) (352,360) (100,190) (4,92)  D=1.7in")

print("C: BLOCK_ARC with explicit adjustments")
blockarc(0.6, 4.6, 2.4, 20, 120, 0.22, AMBER)
blockarc(3.4, 4.6, 2.4, 200, 320, 0.22, RED)
label(0.6, 7.05, 5.4, 0.3, "C: BLOCK_ARC (20,120,0.22) and (200,320,0.22)")

print("D: freeform arrowheads on a circle, bearings 45/135/225/315")
CCX, CCY = 9.6, 5.9
for b in (45, 135, 225, 315):
    arrowhead(CCX, CCY, b, 0.34, AMBER)
donut(CCX - 1.0, CCY - 1.0, 2.0, 0.90, GREY)
label(7.6, 7.05, 4.6, 0.3, "D: freeform arrowheads at 45/135/225/315")

print("E: guide ring + arcs layered")
donut(12.0, 4.6, 1.3, 0.93, GREY)
arc(11.85, 4.45, 1.6, 5, 85, RED, 9, "e1")
arc(11.85, 4.45, 1.6, 185, 265, RED, 9, "e2")
label(11.6, 6.0, 1.9, 0.5, "E: guide\nring + arcs", 8.0)

prs.save(OUT)
print("saved", OUT, os.path.getsize(OUT))
