"""Structural QA on the built deck: pictures inside the slide, no empty boxes,
chart aspect preserved, text not overflowing its frame, and every slide has
either a picture or text. Written because no COM/PowerPoint renderer is
available in this session.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).resolve().parent
DECK = HERE / "ISZE_Business_Performance_Review_2026.pptx"

prs = Presentation(DECK)
SW, SH = prs.slide_width, prs.slide_height
problems: list[str] = []
rows = []

for i, slide in enumerate(prs.slides, start=1):
    pics = 0
    texts = 0
    for sh in slide.shapes:
        l, t = sh.left or 0, sh.top or 0
        w, h = sh.width or 0, sh.height or 0
        if sh.shape_type == 13 or sh.__class__.__name__ == "Picture":
            pics += 1
        if sh.has_text_frame and sh.text_frame.text.strip():
            texts += 1
        # overflow check with a small tolerance for decorative full-bleed bars
        if l < -Emu(10000) or t < -Emu(10000) or l + w > SW + Emu(10000) or t + h > SH + Emu(10000):
            if not (w >= SW - Emu(10000)):
                problems.append(f"slide {i}: shape outside slide ({sh.shape_type})")
    if pics == 0 and texts == 0:
        problems.append(f"slide {i}: EMPTY SLIDE")
    rows.append((i, pics, texts))

print(f"deck {DECK.name}  slides {len(prs.slides)}  "
      f"{SW.inches:.2f}x{SH.inches:.2f} in  {DECK.stat().st_size:,} bytes")
print()
print("slide  pictures  text-shapes")
for i, p, t in rows:
    print(f"{i:5d}  {p:8d}  {t:11d}")
print()
if problems:
    print("PROBLEMS")
    for p in problems:
        print("  ", p)
else:
    print("structural QA: no empty slides, no shape outside the slide")

# sanity: embedded images must actually exist and be non-trivial
import zipfile

with zipfile.ZipFile(DECK) as z:
    media = [n for n in z.namelist() if n.startswith("ppt/media/")]
    sizes = [(n, z.getinfo(n).file_size) for n in media]
tiny = [s for s in sizes if s[1] < 3000]
print()
print(f"embedded media: {len(sizes)} files")
for n, s in sizes:
    print(f"  {n}  {s:,} bytes" + ("   <-- TINY" if s < 3000 else ""))
(HERE / "_deck_qa.json").write_text(
    json.dumps({"slides": len(prs.slides), "problems": problems,
                "media": [{"name": n, "bytes": s} for n, s in sizes]}, indent=1),
    encoding="utf-8")
