import sys
sys.path.insert(0, r"_build_30")
import docbuild, layoutqa, fitz, os

md = r"01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md"
src = open(md, encoding="utf-8").read()
hs = docbuild.headings(src)
stub = [("x", "00-00", "y")]
print("headings lvl2:", [t for l, t in hs if l == 2])
print()
for p in range(20, 24):
    d = fitz.open(r"_build_30\_staged_v21.pdf")
    pg = d[p - 1]
    print("page", p, "fill", round(layoutqa.column_share(pg), 3))
    for h in layoutqa._heads(pg, min_size=14.5):
        print("   HEAD y1=%.0f x0=%.0f size=%.1f %r" % (h["y1"], h["x0"], h["size"], h["text"][:60]))
    d.close()
d = fitz.open(r"_build_30\_staged_v21.pdf")
print()
print("chapter_breaks on final:", layoutqa.chapter_breaks(d))
d.close()
