from PIL import Image, ImageChops
import sys
qa = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\_qa"
a = Image.open(qa + r"\AFTER_pathfix_20260919.png").convert("RGB")
b = Image.open(qa + r"\STAGED_repro_20260919.png").convert("RGB")
print("sizes", a.size, b.size)
diff = ImageChops.difference(a, b)
bbox = diff.getbbox()
print("diff bbox:", bbox)
# per-row difference magnitude
import numpy as np
d = np.asarray(diff).sum(axis=2)
rows = d.sum(axis=1)
nz = np.nonzero(rows)[0]
print("rows with any diff:", len(nz), "first:", nz[0] if len(nz) else None, "last:", nz[-1] if len(nz) else None)
# report the top differing row bands
band = 40
for start in range(0, a.size[1], band):
    s = rows[start:start+band].sum()
    if s > 0:
        print(f"  rows {start:4d}-{start+band-1:4d}  diffsum={int(s)}")
