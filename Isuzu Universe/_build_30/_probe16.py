import fitz

d = fitz.open(r"_build_30\_staged_v6.pdf")
for n in (16, 17):
    p = d[n - 1]
    print("=== page", n)
    for b in p.get_text("blocks"):
        t = " ".join(b[4].split())
        if t and 40 < b[1] < 800:
            print(f"   y={b[1]:6.0f}-{b[3]:6.0f}  {t[:96]}")
