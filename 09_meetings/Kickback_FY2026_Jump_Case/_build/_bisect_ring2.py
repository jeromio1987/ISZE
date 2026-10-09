# -*- coding: utf-8 -*-
"""Bisect the real ring helpers, one sub-step at a time."""
import importlib.util
import sys
from pathlib import Path

from pptx import Presentation

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
spec = importlib.util.spec_from_file_location("ringv3", HERE / "_build" / "_ring_v3_20261007.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

STEP = int(sys.argv[1])
SRC = HERE / "_build" / "_backup" / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pre-dynamics-20261007-1512.pptx"
OUT = HERE / "_build" / ("_bis2_%d.pptx" % STEP)

prs = Presentation(str(SRC))
slide = prs.slides[19]
cx, cy = R.CX, R.CY
mid = (R.R_OUT + R.R_IN) / 2

if STEP >= 1:                                  # clear old flow
    for sh in list(slide.shapes):
        if sh.name in ("Oval 8", "TextBox 9"):
            sh._element.getparent().remove(sh._element)
        elif sh.name.startswith("Rounded Rectangle") or sh.name.startswith("Rectangle "):
            sh._element.getparent().remove(sh._element)
        elif sh.has_text_frame and sh.text_frame.text.strip().startswith(("1  ·", "2  ·", "3  ·", "4  ·")):
            sh._element.getparent().remove(sh._element)

if STEP >= 2:                                  # the ring track alone
    R.ring_track(slide, cx, cy, mid, R.TRACK * 72, R.RED)

if STEP >= 3:                                  # + chevrons
    for ang in (45, 135, 225, 315):
        R.marker(slide, R.Inches(cx - R.R_OUT), R.Inches(cy - R.R_OUT),
                 R.Inches(2 * R.R_OUT), R.Inches(2 * R.R_OUT), ang, R.RED, size=0.34)

if STEP >= 4:                                  # + ONE empty step box
    R.box_slot(slide, cx, cy, mid, 270)

if STEP >= 5:                                  # + the rest of the step boxes, empty
    for ang in (0, 90, 180):
        R.box_slot(slide, cx, cy, mid, ang)

if STEP >= 6:                                  # + text in the first box only
    from pptx.enum.text import PP_ALIGN
    sh = R.box_slot(slide, cx, cy, mid, 270)
    R.text(sh, ["CONFIRM", "Confirm the monthly plan for each distributor"], 8.6, R.INK,
           align=PP_ALIGN.CENTER)

if STEP >= 7:                                  # + text in all four boxes
    from pptx.enum.text import PP_ALIGN
    for ang, (tag, body) in zip((270, 0, 90, 180),
                                [("CONFIRM", "Confirm the monthly plan"),
                                 ("CHECK AT MONTH 6", "Against the 10% tolerance"),
                                 ("CHECK AT MONTH 9", "Against the 10% tolerance"),
                                 ("ACT", "Close the reporting gaps")]):
        sh = R.box_slot(slide, cx, cy, mid, ang)
        R.text(sh, [tag, body], 8.6, R.INK, align=PP_ALIGN.CENTER)

if STEP >= 8:                                  # + the centre caption
    R.label(slide, cx - 1.42, cy - 0.62, 2.84, 1.24,
            ["A CYCLE,", "NOT A SINGLE", "APPROVAL"], 10.5, R.INK)

prs.save(str(OUT))
print("wrote", OUT.name, "step", STEP)
