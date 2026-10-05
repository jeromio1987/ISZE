from PIL import Image, ImageChops, ImageDraw
import numpy as np
qa = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\_qa"
live = Image.open(qa + r"\AFTER_pathfix_20260919.png").convert("RGB")
stag = Image.open(qa + r"\STAGED_repro_20260919.png").convert("RGB")
dl = np.asarray(live).astype(int); ds = np.asarray(stag).astype(int)
mad = np.abs(dl - ds).mean(axis=2)
print("mean abs diff (whole page):", round(float(mad.mean()), 3))
print("max diff:", int(mad.max()))
print("pct pixels differing by >8:", round(float((mad > 8).mean())*100, 2), "%")
print("pct pixels differing by >32:", round(float((mad > 32).mean())*100, 2), "%")
# try to find a vertical shift that aligns them
best = None
for off in range(-6, 7):
    if off >= 0:
        a = dl[off:, :, :]; b = ds[:dl.shape[0]-off, :, :]
    else:
        a = dl[:dl.shape[0]+off, :, :]; b = ds[-off:, :, :]
    v = float(np.abs(a-b).mean())
    if best is None or v < best[1]:
        best = (off, v)
    print(f"  shift {off:+d} -> mean abs diff {v:.3f}")
print("BEST SHIFT:", best)
def stack(rows, name):
    y0, y1 = rows
    h = y1 - y0
    canvas = Image.new("RGB", (1440, h*3 + 24), "white")
    canvas.paste(live.crop((0, y0, 1440, y1)), (0, 0))
    canvas.paste(stag.crop((0, y0, 1440, y1)), (0, h + 8))
    d = ImageChops.difference(live.crop((0,y0,1440,y1)), stag.crop((0,y0,1440,y1)))
    canvas.paste(Image.eval(d, lambda v: min(255, v*5)), (0, 2*h + 16))
    canvas.save(qa + "\\" + name)
    print("wrote", name, canvas.size)
stack((0, 210), "cmp_TOP.png")
stack((300, 620), "cmp_MID.png")
