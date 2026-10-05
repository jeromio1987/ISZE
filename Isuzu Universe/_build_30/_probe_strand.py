import sys
import fitz

sys.path.insert(0, "_build_30")
import layoutqa

d = fitz.open(r"_build_30\_staged_v8.pdf")
for n in (4, 8, 25):
    p = d[n - 1]
    print("=== page", n, "fill", round(layoutqa.column_share(p), 3))
    print("  heads:", layoutqa._heads(p))
    bl = layoutqa._blocks(p)
    for b in bl[-3:]:
        print(f"  last blk y={b['y0']:.0f}-{b['y1']:.0f} {b['text'][:70]!r}")
res = layoutqa.analyse(d, md_path=r"01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md")
print()
print("stranded:", res["stranded_headings"])
print("figure_tails:", res["figure_tails"])
print("fresh:", res["chapters_that_could_open_fresh"])
