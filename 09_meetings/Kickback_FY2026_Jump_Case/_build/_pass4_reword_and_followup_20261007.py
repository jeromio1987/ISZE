# -*- coding: utf-8 -*-
"""
Pass 4 on the v2 kickback management deck, 2026-10-07.

Two small items, no content change beyond what is stated:

 1. Put the commercial follow-up back on the commercial-action slide. The
    'confirm the remaining stock before proposing another brake-pad campaign'
    action was lost when the stock-timing slide was deleted. It is NOT already
    covered: the SPA recommendations there are about price support, not about
    replenishment after a campaign, and the brake-pad row's action says
    'check stock and replenishment'. The restored line is added as a separate
    closing clause so no action is overwritten. No quantity, no pads figure.

 2. Reword '76% less buying for four months' on the two slides that carry it,
    so it cannot read as a quantity claim. It is a euro ratio between two
    four-month windows (campaign_window_totals.csv: next4_avg 24,083 against
    win_avg_per_month 100,947, i.e. -76.1%); both euro figures are now printed.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
DECK = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"

RED = RGBColor(0xE3, 0x06, 0x13)
INK = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
FONT = "Aptos"

NEW_FOOTER = ("For any SPA: agree a dealer price reduction and measure monthly sales to dealers. "
              "Confirm the remaining brake-pad stock before proposing another campaign.")
NEW_S10 = ["After the brake campaign, buying fell 76%:",
           "EUR 100,947 a month in the campaign window, EUR 24,083 a month after."]
NEW_S21 = ("IUK: a EUR 764,436 stock build, 51 to 97 days after the brake campaign, then brake buying fell "
           "76%. EUR 100,947 a month was billed in the campaign window, EUR 24,083 a month for the four "
           "months after.")


def one_run(shape):
    """The shape's single run, or None when it does not hold exactly one."""
    runs = [r for p in shape.text_frame.paragraphs for r in p.runs]
    return runs[0] if len(runs) == 1 else None


def replace_paragraph(shape, old, new, size=None):
    """Replace the paragraph whose text is `old` with a list of new lines."""
    tf = shape.text_frame
    for i, p in enumerate(tf.paragraphs):
        if p.text.strip() != old.strip():
            continue
        keep = None
        for r in p.runs:
            if r.font.size:
                keep = r.font.size
                break
        src = p.runs[0] if p.runs else None
        # strip every run in this paragraph
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        for j, line in enumerate(new):
            run = p.add_run()
            run.text = line
            run.font.name = FONT
            run.font.size = Pt(size) if size else (keep or Pt(12))
            run.font.color.rgb = src.font.color.rgb if src is not None and src.font.color and src.font.color.type is not None else INK
            run.font.bold = False
            if j < len(new) - 1:
                run.text = line
                br = copy.deepcopy(run._r)
                p._p.append(br)
                br.getparent().remove(br) if False else None
        return True
    return False


prs = Presentation(str(DECK))
sl = list(prs.slides)

# ---------------------------------------------------------------- item 2a: slide 6
s6 = sl[6]
hit = False
for sh in s6.shapes:
    if not sh.has_text_frame:
        continue
    if sh.text_frame.text.strip().startswith("For any SPA:"):
        before = sh.text_frame.text.strip()
        r = one_run(sh)
        r.text = NEW_FOOTER
        hit = True
        print("slide 7 footer")
        print("   before: %r" % before)
        print("   after : %r" % r.text)
        break
assert hit, "commercial-action footer not found"

# ---------------------------------------------------------------- item 2b: slide 10
s10 = sl[9]
hit = 0
for sh in s10.shapes:
    if not sh.has_text_frame:
        continue
    txt = sh.text_frame.text.strip()
    if txt == "After the brake campaign; then\n76% less buying for four months.":
        tf = sh.text_frame
        tf.clear()
        first = True
        for line in NEW_S10:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            run = p.add_run()
            run.text = line
            run.font.name = FONT
            run.font.size = Pt(11.0)
            run.font.color.rgb = INK
            run.font.bold = False
        sh.height = Inches(0.68)
        hit += 1
        print("slide 10 IUK card reworded:")
        for line in NEW_S10:
            print("   %s" % line)
assert hit == 1, hit
# ---------------------------------------------------------------- item 2c: slide 21
s21 = sl[20]
hit = 0
for sh in s21.shapes:
    if not sh.has_text_frame:
        continue
    for p in sh.text_frame.paragraphs:
        if p.text.strip().startswith("IUK: a EUR 764,436 stock build"):
            before = p.text.strip()
            for r in list(p.runs):
                r._r.getparent().remove(r._r)
            run = p.add_run()
            run.text = NEW_S21
            run.font.name = FONT
            run.font.size = Pt(9.5)
            run.font.color.rgb = MUTED
            run.font.bold = False
            hit += 1
            print("slide 21 bullet reworded:")
            print("   before: %r" % before)
            print("   after : %r" % NEW_S21)
assert hit == 1, hit

prs.save(str(DECK))
print("saved", DECK)
