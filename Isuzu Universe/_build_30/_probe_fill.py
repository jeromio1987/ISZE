import sys, fitz
sys.path.insert(0, r"_build_30")
import layoutqa
sys.stdout.reconfigure(encoding="utf-8")

d = fitz.open(r"_build_30\_staged_v25.pdf")
res = layoutqa.analyse(d, md_path=r"01_Strategy\ISUZU_UNIVERSE_3_0_2026-09-23.md")
print("page fills:")
for i, f in enumerate(res["fills"], 1):
    print("   p%-3d %3d%%" % (i, round(f * 100)))
print()
print("early ends:", res["early_ends"] or "none")
print("figure tails:", res["figure_tails"] or "none")
d.close()
