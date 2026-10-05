import sys, fitz
sys.stdout.reconfigure(encoding="utf-8")

d = fitz.open("ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf")
for n in (9, 13, 15):
    d[n - 1].get_pixmap(dpi=80).save(rf"_build_30\_probe_img\33_p{n:02d}.png")
    print("wrote 33_p%02d" % n)
d.close()
v = fitz.open("ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf")
for n in (49,):
    v[n - 1].get_pixmap(dpi=80).save(rf"_build_30\_probe_img\80_p{n:02d}.png")
    print("wrote 80_p%02d" % n)
v.close()
