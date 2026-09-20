"""Draw the hotspots straight onto each photograph and lay the four out, so the
fit can be judged and corrected in one look instead of through the page.

This is the loop for fitting: edit the fractions in vehicle_images.py, run this,
look at the picture. No page rebuild needed.
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vehicle_images as VI   # noqa: E402

OUT = os.path.join(HERE, "_qa")
os.makedirs(OUT, exist_ok=True)

# alpha fill per zone so the underlying vehicle is still visible
COL = {
    "front":   (192, 85, 45, 105),
    "cab":     (176, 135, 58, 105),
    "engine":  (29, 48, 84, 105),
    "chassis": (91, 107, 127, 105),
    "rear":    (138, 86, 34, 105),
    "elec":    (30, 107, 79, 105),
}
EDGE = {
    "front": (192, 85, 45), "cab": (176, 135, 58), "engine": (29, 48, 84),
    "chassis": (91, 107, 127), "rear": (138, 86, 34), "elec": (30, 107, 79),
}

hs = VI.build_zones()
nhs = VI.build_anchors()
want = sys.argv[1:] if len(sys.argv) > 1 else ["dmax", "nlr", "nmr", "frr"]
GRIDDED = os.environ.get("GRID") == "1"
try:
    from PIL import ImageFont
    FONT = ImageFont.truetype("arial.ttf", 13)
except Exception:
    FONT = None
tiles = []
for key in want:
    im = Image.open(VI.PICTURES[key]).convert("RGBA")
    w, h = im.size
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    for zone in VI.ZONE_ORDER:
        for poly in hs[key][zone]:
            pts = [(x * w, y * h) for x, y in poly]
            dr.polygon(pts, fill=COL[zone])
            dr.line(pts + [pts[0]], fill=EDGE[zone], width=3)
    # label anchors, so the preview shows where each label will attach
    for zone in VI.ZONE_ORDER:
        a = nhs[key].get(zone)
        if a:
            ax, ay = a[0] * w, a[1] * h
            dr.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=(21, 35, 60),
                       outline=(255, 255, 255), width=2)
    merged = Image.alpha_composite(im, ov).convert("RGB")
    if GRIDDED:
        gd = ImageDraw.Draw(merged)
        for i in range(1, 20):
            x = int(i * w / 20)
            major = (i % 2 == 0)
            gd.line([(x, 0), (x, h)],
                    fill=(255, 0, 0) if major else (255, 185, 185),
                    width=1)
            if major:
                gd.text((x + 2, 3), str(i * 5), fill=(180, 0, 0), font=FONT)
                gd.text((x + 2, h - 18), str(i * 5), fill=(180, 0, 0), font=FONT)
        for j in range(1, 20):
            y = int(j * h / 20)
            major = (j % 2 == 0)
            gd.line([(0, y), (w, y)],
                    fill=(0, 80, 255) if major else (175, 205, 255), width=1)
            if major:
                gd.text((4, y + 2), str(j * 5), fill=(0, 60, 200), font=FONT)
                gd.text((w - 42, y + 2), str(j * 5), fill=(0, 60, 200), font=FONT)
    merged.save(os.path.join(OUT, f"hotspot_{key}.png"))
    print(f"{key}: wrote hotspot_{key}.png {merged.size}")
    tiles.append((key, merged))

# one sheet with all four stacked, so a single look covers the lot
CW = 1180 if len(tiles) > 1 else 1400
scaled = []
for key, im in tiles:
    s = im.resize((CW, int(im.height * CW / im.width)), Image.LANCZOS)
    scaled.append((key, s))
sheet = Image.new("RGB", (CW, sum(s.height + 26 for _, s in scaled) + 10),
                  (235, 233, 227))
dr = ImageDraw.Draw(sheet)
y = 6
for key, s in scaled:
    dr.text((6, y), f"===== {key}  ({VI.DEPICTS[key]}) =====", fill=(20, 35, 60))
    y += 20
    sheet.paste(s, (0, y))
    y += s.height + 6
sheet.save(os.path.join(OUT, "hotspot_sheet.png"))
print("wrote", os.path.join(OUT, "hotspot_sheet.png"), sheet.size)
