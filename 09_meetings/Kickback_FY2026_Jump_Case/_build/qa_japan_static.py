import os, sys
from pptx import Presentation
from pptx.util import Emu

DECK = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Japan_Pack_20261007.pptx"
p = Presentation(DECK)
SW = p.slide_width
SH = p.slide_height

problems = []
print("slide size %.3f x %.3f in, slides=%d" % (SW / 914400, SH / 914400, len(p.slides._sldIdLst)))

for i, s in enumerate(p.slides, 1):
    for sh in s.shapes:
        if sh.left is None:
            continue
        if sh.left < 0 or sh.top < 0 or sh.left + sh.width > SW or sh.top + sh.height > SH:
            problems.append("slide %d: OUT OF BOUNDS %s L=%.2f T=%.2f R=%.2f B=%.2f" % (
                i, sh.name, sh.left / 914400, sh.top / 914400,
                (sh.left + sh.width) / 914400, (sh.top + sh.height) / 914400))

# text overflow estimate: chars per line at font size, and lines needed
def est_lines(text, width_in, size_pt):
    # ~0.52 * size pt average glyph width for Aptos
    cpl = max(1, int(width_in * 72 / (0.50 * size_pt)))
    return max(1, -(-len(text) // cpl))

for i, s in enumerate(p.slides, 1):
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        tf = sh.text_frame
        w_in = sh.width / 914400
        need = 0.0
        avail = sh.height / 914400
        for para in tf.paragraphs:
            t = "".join(r.text for r in para.runs)
            if not t:
                continue
            sz = None
            for r in para.runs:
                if r.font.size:
                    sz = r.font.size.pt
                    break
            sz = sz or 11
            need += est_lines(t, w_in, sz) * (sz * 1.28) / 72.0
        if need > avail + 0.02:
            problems.append("slide %d: TEXT OVERFLOW %s need=%.2f avail=%.2f  %r" % (
                i, sh.name, need, avail, tf.text[:70]))

print("problems:", len(problems))
for x in problems:
    print("  -", x)
sys.exit(0 if not problems else 1)
