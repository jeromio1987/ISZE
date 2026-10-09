# -*- coding: utf-8 -*-
"""The Kaizen ring, drawn with constructions that were measured to render.

Established by render + pixel measurement in the probes (not by arithmetic alone):
  * a DONUT is unreliable - its hole adjustment did not leave an open centre, and a
    no-fill donut renders as nothing at all.  So the guide ring is a plain OVAL with
    NO FILL and a thick line: ink only at the rim, background across the centre.
  * PowerPoint's ARC shape has no independent start angle and moves when rotated,
    so the accent segments are FREEFORM annular sectors built from computed points.
  * the step boxes are placed OUTSIDE the ring radius, so no box can ever land on the
    ring or on an accent arc.  This is the failure the brief warned about twice.

Every position is computed from the centre and the radius.
"""
from __future__ import annotations

import math

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu, Pt

_EMU = 914400

GUIDE = RGBColor(0x4B, 0x4B, 0x4B)
ACCENT = RGBColor(0xE3, 0x06, 0x13)
ARROW = RGBColor(0xF5, 0xA0, 0x00)


def _e(v_in):
    return Emu(int(round(v_in * _EMU)))


def _poly(slide, pts, color):
    """Closed freeform polygon from a list of (x, y) inch pairs."""
    fb = slide.shapes.build_freeform(_e(pts[0][0]), _e(pts[0][1]), 1.0)
    fb.add_line_segments([(_e(x), _e(y)) for x, y in pts[1:]], close=True)
    sh = fb.convert_to_shape()
    sh.shadow.inherit = False
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


def step_radius(cx, cy, box_w, box_h, clearance=0.11):
    """Smallest box-centre radius that keeps the box entirely clear of a ring of
    radius R.  Used to compute the layout rather than guess it."""
    half_h = box_h / 2.0
    return half_h + clearance


def add_ring(slide, cx, cy, radius=1.40, band=0.085,
             gap_half=26.0, arrow_len=0.21, arrow_half=0.12, segments=20,
             guide_color=GUIDE, accent_color=ACCENT, arrow_color=ARROW):
    """Guide ring + accent arcs + arrowheads.  Returns the (x, y) centre for each
    of the four steps, clockwise from the top."""
    made = []

    d = 2.0 * radius
    ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, _e(cx - radius), _e(cy - radius),
                                 _e(d), _e(d))
    ring.shadow.inherit = False
    ring.fill.background()
    ring.line.color.rgb = guide_color
    ring.line.width = Pt(band * 72.0)
    made.append(ring)

    r_out = radius + band / 2.0
    r_in = radius - band / 2.0
    for g in (315.0, 45.0, 135.0, 225.0):
        outer, inner = [], []
        for i in range(segments + 1):
            t = g - gap_half + (2.0 * gap_half) * i / float(segments)
            rad = math.radians(t)
            c, s = math.cos(rad), math.sin(rad)
            outer.append((cx + r_out * c, cy + r_out * s))
            inner.append((cx + r_in * c, cy + r_in * s))
        made.append(_poly(slide, outer + inner[::-1], accent_color))

        # arrowhead on the gap centre bearing, pointing with increasing bearing
        # (clockwise on screen).  Its own angle is computed from g, not from the
        # loop above - reusing the last arc angle is what put the arrows 26 deg off.
        arad = math.radians(g)
        c, s = math.cos(arad), math.sin(arad)
        tx, ty = -s, c
        nxp, nyp = -ty, tx
        bx, by = cx + radius * c, cy + radius * s
        tip = (bx + tx * arrow_len, by + ty * arrow_len)
        b1 = (bx - nxp * arrow_half, by - nyp * arrow_half)
        b2 = (bx + nxp * arrow_half, by + nyp * arrow_half)
        made.append(_poly(slide, [tip, b1, b2], arrow_color))

    steps = [(cx, cy - radius), (cx + radius, cy), (cx, cy + radius), (cx - radius, cy)]
    return made, steps


def free_windows(radius, box_w, box_h, box_centre_radius, n=1440):
    """For verification: bearings where a point on the ring radius is NOT inside any
    of the four axis-aligned step boxes.  Returns a list of (start, end) degrees."""
    half_w, half_h = box_w / 2.0, box_h / 2.0
    boxes = [(0.0, -box_centre_radius), (box_centre_radius, 0.0),
             (0.0, box_centre_radius), (-box_centre_radius, 0.0)]
    covered = []
    for i in range(n):
        deg = 360.0 * i / n
        rad = math.radians(deg)
        px_, py_ = radius * math.cos(rad), radius * math.sin(rad)
        hit = any(abs(px_ - bx) <= half_w and abs(py_ - by) <= half_h for bx, by in boxes)
        covered.append(hit)
    if not any(covered):
        return [(0.0, 360.0)]
    # rotate so index 0 is not covered if possible
    start = covered.index(False) if False in covered else 0
    covered = covered[start:] + covered[:start]
    segs, cur = [], None
    for i, hit in enumerate(covered):
        if not hit and cur is None:
            cur = i
        elif hit and cur is not None:
            segs.append((360.0 * cur / n + 360.0 * start / n,
                         360.0 * (i - 1) / n + 360.0 * start / n))
            cur = None
    if cur is not None:
        segs.append((360.0 * cur / n + 360.0 * start / n, 360.0 + 360.0 * start / n))
    return [(round(a % 360.0, 1), round(b % 360.0, 1)) for a, b in segs]
