# -*- coding: utf-8 -*-
"""Temp: measure Jerome's report screenshot to find the layout mode and text start."""
import sys
from PIL import Image

SRC = r"C:\Users\jerom\.cursor\projects\c-Users-jerom-Desktop-claude\assets\C__Users_jerom_.cursor_projects_c-Users-jerom-Desktop-claude_assets_c__Users_jerom_AppData_Roaming_Cursor_User_workspaceStorage_decc595274288534534ba854ac94685d_images_image-6795b4c9-404b-4c5e-9c4f-28c894be4e5c.png"
sys.stdout.reconfigure(encoding="utf-8")
im = Image.open(SRC).convert("RGB")
print("size", im.size)
W, H = im.size
px = im.load()

# scan a horizontal line inside the first layer card heading to see where ink starts
def rowscan(y, x0=0, x1=None):
    x1 = x1 or W
    runs = []
    for x in range(x0, x1):
        r, g, b = px[x, y]
        dark = (r + g + b) / 3 < 200
        runs.append(dark)
    # find first dark x
    first = next((x0 + i for i, v in enumerate(runs) if v), None)
    return first

for y in range(100, 260, 6):
    print("y=%4d first_ink_x=%s" % (y, rowscan(y)))

# vertical scan at several x to find card edges (paper #f7f4ee vs white #fff vs navy)
print("--- vertical scan x=80..1000 step, find column boundaries at y in card ---")
for x in [60, 70, 74, 76, 78, 80, 82, 84, 86, 88, 90, 95, 100, 105, 110, 120, 130, 140]:
    print("x=%4d color@y=100 %s  color@y=170 %s" % (x, px[x, 100], px[x, 170]))
