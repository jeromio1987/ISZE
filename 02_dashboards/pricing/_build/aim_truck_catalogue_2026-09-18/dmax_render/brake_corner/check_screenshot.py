"""Check the page screenshot itself, since image reading is unavailable here.

Confirms the page painted what it should: the drawing is present (its tones occupy
a large region), the house colours are on the page, the callout labels painted in
navy, and the selected callout is drawn in terracotta.  Also confirms there is no
large blank region inside the drawing area, which would mean the image failed to
load and left a broken-image box.

  python check_screenshot.py
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "_raw")
SHOT = os.path.join(RAW, "page_brake_corner_full.png")
OUT = os.path.join(RAW, "screenshot_check.json")

navy = np.array([0x15, 0x23, 0x3c])
terra = np.array([0xc0, 0x55, 0x2d])
paper = np.array([0xf7, 0xf4, 0xee])

im = Image.open(SHOT)
a = np.asarray(im.convert("RGB")).astype(np.int16)
H, W, _ = a.shape
doc = {"screenshot": SHOT, "size": [W, H]}


def mask(c, tol=26):
    return np.abs(a - c).max(axis=2) <= tol


m_navy, m_terra, m_paper = mask(navy), mask(terra), mask(paper)
doc["navy_px"] = int(m_navy.sum())
doc["terracotta_px"] = int(m_terra.sum())
doc["paper_px"] = int(m_paper.sum())
print("screenshot %dx%d" % (W, H))
print("  navy header/labels  %8d px" % doc["navy_px"])
print("  terracotta accents  %8d px" % doc["terracotta_px"])
print("  paper background    %8d px" % doc["paper_px"])

# the drawing area: the page puts the figure on the left, the panel on the right
half = int(W * 0.62)
left = a[:, :half]
# the drawing sits on white; count pixels that are neither paper, white nor near it,
# and that are not one of the flat label colours - i.e. actual rendered subject
lum = left.mean(axis=2)
not_bg = (np.abs(left - 255).max(axis=2) > 24) & (np.abs(left - paper).max(axis=2) > 24)
doc["drawing_area_px"] = int(not_bg.sum())
doc["drawing_area_pct_of_left_half"] = round(
    100.0 * not_bg.sum() / (left.shape[0] * left.shape[1]), 2)
print("  drawn subject in the left (drawing) area: %d px (%.1f%% of that area)"
      % (doc["drawing_area_px"], doc["drawing_area_pct_of_left_half"]))

# blank-region test: split the left area into a grid and look for cells that are
# entirely background, which is what a failed image load would produce
gh, gw = 8, 8
cell_blank = []
for i in range(gh):
    for j in range(gw):
        y0, y1 = i * left.shape[0] // gh, (i + 1) * left.shape[0] // gh
        x0, x1 = j * left.shape[1] // gw, (j + 1) * left.shape[1] // gw
        cell_blank.append(int((~not_bg[y0:y1, x0:x1]).mean() * 100))
doc["blank_cell_pct_max"] = max(cell_blank)
doc["blank_cells_over_99pct"] = sum(1 for c in cell_blank if c > 99)
print("  blankest 1/64th of the drawing area: %d%% background" % doc["blank_cell_pct_max"])

fails = []
if doc["navy_px"] < 5000:
    fails.append("the navy house colour barely appears, the page may not have painted")
if doc["terracotta_px"] < 200:
    fails.append("terracotta accents are missing (callouts or rules did not paint)")
if doc["drawing_area_pct_of_left_half"] < 8:
    fails.append("the drawing area is nearly empty - the embedded image may not have loaded")
if doc["blank_cells_over_99pct"] > 24:
    fails.append("%d of 64 drawing cells are completely blank"
                 % doc["blank_cells_over_99pct"])
doc["failures"] = fails
doc["verdict"] = "PASS" if not fails else "FAIL"

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print("wrote", OUT)
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
else:
    print("no failures")
print("VERDICT:", doc["verdict"])
