"""Static QA for the v2 deck: off-slide shapes, text-overflow estimate, and for the new slide 21
the chevron/text geometry (does any text box leave the chevron's inner band, do chevrons overlap
their neighbours' text, is the notch depth right)."""
from __future__ import annotations
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Emu

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
PPTX = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
EMU_IN = 914400
TARGET_SIZE = float(sys.argv[1]) if len(sys.argv) > 1 else None   # last-render point size

prs = Presentation(PPTX)
SW, SH = prs.slide_width, prs.slide_height
issues = []

for si, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        l, t, w, h = sh.left, sh.top, sh.width, sh.height
        if l is None:
            continue
        if l < -10000 or t < -10000 or l + w > SW + 10000 or t + h > SH + 10000:
            issues.append("S%02d OUTSIDE %s l=%.3f t=%.3f r=%.3f b=%.3f"
                          % (si, sh.name, l / EMU_IN, t / EMU_IN, (l + w) / EMU_IN, (t + h) / EMU_IN))
        if sh.has_text_frame and sh.text_frame.text.strip():
            tf = sh.text_frame
            box_w = (w or 0) / EMU_IN
            box_h = (h or 0) / EMU_IN
            total = 0.0
            for p in tf.paragraphs:
                txt = "".join(r.text for r in p.runs)
                if not txt:
                    total += 0.10
                    continue
                size = TARGET_SIZE
                if size is None:
                    for r in p.runs:
                        if r.font.size:
                            size = r.font.size.pt
                            break
                    size = size or 10
                line_h = size * 1.22 / 72
                cpl = max(1, int(box_w * 72 / (size * 0.52)))
                lines = max(1, -(-len(txt) // cpl))
                total += lines * line_h * 1.10
            if box_h > 0.05 and total > box_h * 1.02:
                issues.append("S%02d OVERFLOW %s est %.2fin > box %.2fin  '%s'"
                              % (si, sh.name, total, box_h, tf.text[:48].replace("\n", " / ")))

print("slides:", len(prs.slides._sldIdLst))
print("issues:", len(issues))
for i in issues:
    print("  ", i)

# ---- dedicated geometry audit of the last slide (the arrow chain) ----
print("\n--- slide 21 geometry ---")
s21 = list(prs.slides)[20]
shapes = []
for sh in s21.shapes:
    shapes.append((sh.name, sh.left / EMU_IN, sh.top / EMU_IN,
                   (sh.left + sh.width) / EMU_IN, (sh.top + sh.height) / EMU_IN, sh))
chev = [x for x in shapes if "Chevron" in x[0]]
downs = [x for x in shapes if x[0].startswith("Down Arrow")]
rects = [x for x in shapes if x[0].startswith("Rectangle")]
print("chevrons:", [(x[0], round(x[1], 3), round(x[3], 3), round(x[2], 3), round(x[4], 3)) for x in chev])
for a, b in zip(chev, chev[1:]):
    overlap = a[3] - b[1]
    print("  %s right=%.4f  %s left=%.4f  overlap=%.4f in" % (a[0], a[3], b[0], b[1], overlap))
print("down arrows:", [(x[0], round(x[1], 3), round(x[2], 3), round(x[4], 3)) for x in downs])

# every text box must sit inside its chevron's *inner* band (notch .. point)
DEPTH = 0.26
print("\n  text box horizontal clearance inside its chevron:")
for x in chev:
    cx0, cx1 = x[1], x[3]
    inner_lo, inner_hi = cx0 + DEPTH, cx1 - DEPTH
    for t in [z for z in shapes if z[0].startswith("Text") or z[0].startswith("TextBox")]:
        if t[2] >= x[2] - 0.01 and t[4] <= x[4] + 0.01 and t[1] >= cx0 - 0.01 and t[3] <= cx1 + 0.01:
            ok_l = t[1] >= inner_lo - 0.005
            ok_r = t[3] <= inner_hi + 0.005
            print("    %-14s chev %-10s txt l=%.3f r=%.3f  inner %.3f..%.3f  L%s R%s"
                  % (t[0], x[0], t[1], t[3], inner_lo, inner_hi,
                     "ok" if ok_l else "CLIP", "ok" if ok_r else "CLIP"))
