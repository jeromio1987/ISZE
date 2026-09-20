from PIL import Image, ImageChops
import numpy as np
qa = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\_qa"
b = Image.open(qa + r"\BEFORE_pathfix_20260919.png").convert("RGB")
a = Image.open(qa + r"\AFTER_pathfix_20260919.png").convert("RGB")
print("sizes", b.size, a.size)
d = np.abs(np.asarray(b).astype(int) - np.asarray(a).astype(int)).mean(axis=2)
print("mean abs diff BEFORE vs AFTER:", round(float(d.mean()),2))
print("pct pixels differing >24:", round(float((d>24).mean())*100,2), "%")
rows = d.sum(axis=1)
bands=[]
band=100
for s in range(0, b.size[1], band):
    bands.append((int(rows[s:s+band].sum()), s))
bands.sort(reverse=True)
print("top 6 differing 100px bands (diffsum, y-start):", bands[:6])
# save side-by-side of the biggest differing band
_, y = bands[0]
h = min(100, b.size[1]-y)
c = Image.new("RGB",(1440, h*2+8),"white")
c.paste(b.crop((0,y,1440,y+h)),(0,0)); c.paste(a.crop((0,y,1440,y+h)),(0,h+8))
c.save(qa + r"\BEFORE_vs_AFTER_band.png")
# also a broad band
c2 = Image.new("RGB",(1440, 300*2+8),"white")
c2.paste(b.crop((0,300,1440,600)),(0,0)); c2.paste(a.crop((0,300,1440,600)),(0,308))
c2.save(qa + r"\BEFORE_vs_AFTER_mid.png")
print("wrote BEFORE_vs_AFTER_band.png, BEFORE_vs_AFTER_mid.png")
