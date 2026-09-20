"""Pixel-level check on the QA screenshots.

Confirms objectively:
  - the canvas is not a flat fill (i.e. something painted)
  - the exact column palette colours from the settings block appear in the image
  - how many distinct colour classes are on screen
  - the panel region is not blank when open

Reads the PNGs that the QA run wrote, so it checks the rendered artifact.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SPINE = HERE.parent / "data" / "market_spine.json"

spine = json.loads(SPINE.read_text(encoding="utf-8"))
cs = spine["settings"]["metrics"][spine["settings"]["color_metric"]]["color_scale"]
PALETTE = {}
for c in cs.get("classes", []):
    PALETTE[c["color"].lower()] = c["label"]
if cs.get("missing_color"):
    PALETTE[cs["missing_color"].lower()] = "no value"


def near(rgb, hexcolor, tol):
    h = hexcolor.lstrip("#")
    t = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return all(abs(rgb[i] - t[i]) <= tol for i in range(3))


def analyse(path: Path, region=None, label=""):
    if not path.exists():
        print(f"  {path.name}: MISSING")
        return
    img = Image.open(path).convert("RGB")
    if region:
        img = img.crop(region)
    px = list(img.getdata())
    counts = Counter(px)

    distinct = len(counts)
    top = counts.most_common(1)[0]
    dominant_share = top[1] / len(px)

    print(f"  {path.name} {label}")
    print(f"    size {img.size[0]}x{img.size[1]}  distinct colours {distinct}")
    print(f"    dominant colour {top[0]} = {dominant_share:.1%} of pixels")

    if dominant_share > 0.985:
        print("    WARNING: essentially a flat fill - nothing painted")
    else:
        print(f"    OK: {1 - dominant_share:.1%} of pixels differ from the dominant fill")

    # which palette colours are present
    found = {}
    for hexc, name in PALETTE.items():
        n = sum(v for k, v in counts.items() if near(k, hexc, 10))
        if n:
            found[name] = n
    if found:
        print("    column palette colours present:")
        for name, n in sorted(found.items(), key=lambda kv: -kv[1]):
            print(f"      {name:<26} {n:>7} px")
    else:
        print("    NO palette colours found in this crop")

    # any strong red / green / amber family at all (looser, catches blending)
    warm = sum(v for k, v in counts.items() if k[0] > 140 and k[0] - k[2] > 45)
    green = sum(v for k, v in counts.items() if k[1] > 110 and k[1] - k[0] > 25)
    print(f"    warm/red-family pixels {warm}   green-family pixels {green}")


print("=" * 70)
print("Pixel evidence from the rendered screenshots")
print(f"colour metric in the build: {spine['settings']['color_metric']}")
print("=" * 70)

print("\n--- map area only (excluding the title bar, controls, legend) ---")
# The map is full-bleed; crop out the overlay corners so panels don't skew it.
analyse(HERE / "01_globe_columns.png", region=(0, 180, 1600, 830), label="[map band]")

print("\n--- full frame ---")
for name in ["01_globe_columns.png", "02_hover_column.png", "04_zoomed_in.png",
             "06_shared_coordinate_pair.png", "07_metric_switched.png"]:
    analyse(HERE / name)

print("\n--- side panel region when open (right 430 px) ---")
analyse(HERE / "03_panel_open.png", region=(1170, 0, 1600, 1000), label="[panel]")

print("\n--- side panel region on the placeholder market ---")
analyse(HERE / "05_placeholder_market.png", region=(1170, 0, 1600, 1000), label="[panel]")
