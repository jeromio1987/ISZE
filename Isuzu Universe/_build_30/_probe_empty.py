import sys
import fitz

sys.path.insert(0, "_build_30")
import layoutqa

d = fitz.open(r"_build_30\_staged_v15.pdf")
for n in (15, 20, 16, 23):
    p = d[n - 1]
    print("=== page", n, "fill", round(layoutqa.column_share(p), 3),
          "| next page starts:", " ".join(d[n].get_text().split())[:70] if n < d.page_count else "-")
    for b in p.get_text("blocks"):
        t = " ".join(b[4].split())
        if t and 40 < b[1] < 800:
            print(f"   y={b[1]:6.0f}-{b[3]:6.0f}  {t[:80]}")
    for im in p.get_image_info():
        print(f"   IMAGE y={im['bbox'][1]:6.0f}-{im['bbox'][3]:6.0f}")
    print()
