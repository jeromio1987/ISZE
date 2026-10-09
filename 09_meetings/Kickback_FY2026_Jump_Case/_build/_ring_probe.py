# -*- coding: utf-8 -*-
"""Probe: prove which ring constructions actually render in PowerPoint.

Builds one slide with several candidate ring drawings, renders via COM, so the
image can be inspected before committing to the real slide.
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(OUT_DIR, "_ring_probe.pptx")

BG = RGBColor(0x26, 0x26, 0x26)
PANEL = RGBColor(0x30, 0x30, 0x30)
RED = RGBColor(0xE3, 0x06, 0x13)
WHITE = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
GREEN = RGBColor(0x31, 0xA3, 0x54)
AMBER = RGBColor(0xF5, 0xA0, 0x00)
FONT = "Aptos"

prs = Presentation()
prs.slide_width = Inches(13.3333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def new_slide():
    s = prs.slides.add_slide(blank)
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = BG
    return s


def label(s, x, y, w, h, t, size=9, color=MUTED):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = t
    r.font.size = Pt(size)
    r.font.name = FONT
    r.font.color.rgb = color
    return tb


def shp(s, kind, x, y, w, h, fill=None, line=None, lw=1.0, rot=0):
    sh = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
    if rot:
        sh.rotation = rot
    return sh


# ---------------------------------------------------------------- probe 1
s = new_slide()
label(s, 0.2, 0.2, 8, 0.3, "PROBE 1: candidates on a dark background", 12, WHITE)

# A. DONUT, solid fill red
shp(s, MSO_SHAPE.DONUT, 0.4, 0.8, 2.2, 2.2, fill=RED)
label(s, 0.4, 3.05, 2.6, 0.3, "A DONUT solid RED")

# B. DONUT, no fill
shp(s, MSO_SHAPE.DONUT, 3.0, 0.8, 2.2, 2.2, fill=None)
label(s, 3.0, 3.05, 2.6, 0.3, "B DONUT no fill")

# C. BLOCK_ARC solid red, adj defaults
shp(s, MSO_SHAPE.BLOCK_ARC, 5.6, 0.8, 2.2, 2.2, fill=RED)
label(s, 5.6, 3.05, 2.6, 0.3, "C BLOCK_ARC solid RED")

# D. CIRCULAR_ARROW red
shp(s, MSO_SHAPE.CIRCULAR_ARROW, 8.2, 0.8, 2.6, 2.2, fill=RED)
label(s, 8.2, 3.05, 3.2, 0.3, "D CIRCULAR_ARROW solid RED")

# E. BLOCK_ARC no fill, thick line
shp(s, MSO_SHAPE.BLOCK_ARC, 11.4, 0.8, 1.6, 1.6, fill=None, line=AMBER, lw=6)
label(s, 10.9, 2.5, 2.4, 0.3, "E ARC no fill + line")

# F. OVAL no fill, thick line = ring outline
shp(s, MSO_SHAPE.OVAL, 0.4, 3.5, 2.2, 2.2, fill=None, line=GREEN, lw=8)
label(s, 0.4, 5.75, 2.6, 0.3, "F OVAL no fill + 8pt line")

# G. PIE
shp(s, MSO_SHAPE.PIE, 3.0, 3.5, 2.2, 2.2, fill=RED)
label(s, 3.0, 5.75, 2.6, 0.3, "G PIE solid RED")

# H. ARC shape
shp(s, MSO_SHAPE.ARC, 5.6, 3.5, 2.2, 2.2, fill=None, line=AMBER, lw=6)
label(s, 5.6, 5.75, 2.6, 0.3, "H ARC default (no fill,line)")

# I. centre text box added AFTER the ring, on top
shp(s, MSO_SHAPE.DONUT, 8.2, 3.5, 2.2, 2.2, fill=None, line=RED, lw=14)
tb = s.shapes.add_textbox(Inches(8.6), Inches(4.25), Inches(1.4), Inches(0.7))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "CENTRE\nON TOP"
r.font.size = Pt(12)
r.font.name = FONT
r.font.bold = True
r.font.color.rgb = WHITE
label(s, 8.0, 5.75, 2.8, 0.3, "I DONUT no-fill 14pt + text")

# J. CHEVRON default
shp(s, MSO_SHAPE.CHEVRON, 11.2, 3.5, 1.6, 0.9, fill=AMBER)
label(s, 11.0, 4.55, 2.2, 0.3, "J CHEVRON solid AMBER")

prs.save(OUT)
print("saved", OUT, os.path.getsize(OUT))
