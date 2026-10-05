"""Sharpness comparison for the vector-vs-raster basemap question.

Not part of the product. Reads the vec_*_zoom_benelux screenshots (identical
camera: centre [5.0, 50.6], zoom 6.4, pitch 0, bearing 0, 1400x950 CSS px at
deviceScaleFactor 2), crops the same window from each, and reports a sharpness
proxy per crop:

  * mean gradient magnitude (Sobel), and
  * Laplacian variance,

both standard no-reference sharpness measures. Higher means more high-frequency
detail actually present in the rendered pixels. The window is chosen to exclude
the probe HUD in the top-left corner.

Also writes vec_10_sharpness_3up.png, a stacked crop so the difference can be
looked at directly.

Run:  python _qa/vec_sharpness.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent

# 1400x950 CSS px at deviceScaleFactor 2 -> 2800x1900 device px.
# Crop window: right of the HUD, above the attribution, land + sea + labels.
CROP = (900, 420, 2700, 1600)

CASES = [
    ("raster-now (what the page draws today, 256 px tiles, no retina)",
     "vec_07_raster_now_globe_zoom_benelux.png"),
    ("raster @2x hardcoded (CARTO 512 px retina tile, best-case raster)",
     "vec_11_raster_at2x_globe_zoom_benelux.png"),
    ("OpenFreeMap Positron (vector)",
     "vec_01_ofm_positron_globe_zoom_benelux.png"),
    ("OpenFreeMap Liberty (vector)",
     "vec_02_ofm_liberty_globe_zoom_benelux.png"),
    ("CARTO Voyager (vector)",
     "vec_09_carto_voyager_globe_zoom_benelux.png"),
]


def grey(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"), dtype=np.float64)


def sobel_mean_gradient(a: np.ndarray) -> float:
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    ky = kx.T
    gx = np.zeros_like(a)
    gy = np.zeros_like(a)
    # simple valid correlation via summation (avoid scipy dependency)
    h, w = a.shape
    for dy in range(3):
        for dx in range(3):
            sub = a[dy:h - 2 + dy, dx:w - 2 + dx]
            gx[1:h - 1, 1:w - 1] += kx[dy, dx] * sub
            gy[1:h - 1, 1:w - 1] += ky[dy, dx] * sub
    return float(np.mean(np.hypot(gx[1:h - 1, 1:w - 1], gy[1:h - 1, 1:w - 1])))


def laplacian_variance(a: np.ndarray) -> float:
    k = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)
    h, w = a.shape
    out = np.zeros_like(a)
    for dy in range(3):
        for dx in range(3):
            if k[dy, dx] == 0:
                continue
            out[1:h - 1, 1:w - 1] += k[dy, dx] * a[dy:h - 2 + dy, dx:w - 2 + dx]
    return float(np.var(out[1:h - 1, 1:w - 1]))


rows = []
crops = []
for label, fname in CASES:
    path = HERE / fname
    if not path.exists():
        rows.append({"label": label, "file": fname, "MISSING": True})
        print(f"  MISSING: {fname}")
        continue
    img = Image.open(path).convert("RGB")
    box = (CROP[0], CROP[1], min(CROP[2], img.width), min(CROP[3], img.height))
    crop = img.crop(box)
    g = grey(crop)
    mg = sobel_mean_gradient(g)
    lv = laplacian_variance(g)
    rows.append({
        "label": label,
        "file": fname,
        "image_size": list(img.size),
        "crop_box": list(box),
        "crop_size": list(crop.size),
        "mean_gradient": round(mg, 3),
        "laplacian_variance": round(lv, 2),
    })
    print(f"  {label:<58} mean|grad|={mg:7.3f}  lapVar={lv:10.2f}")
    crops.append((label, crop))

# base = the page's current raster, for % uplift
base = next((r for r in rows if r.get("file", "").startswith("vec_07_")), None)
if base:
    for r in rows:
        if "mean_gradient" in r and base.get("mean_gradient"):
            r["mean_gradient_vs_raster_now_pct"] = round(
                100.0 * (r["mean_gradient"] / base["mean_gradient"] - 1.0), 1)
            r["laplacian_vs_raster_now_pct"] = round(
                100.0 * (r["laplacian_variance"] / base["laplacian_variance"] - 1.0), 1)

(HERE / "vec_sharpness.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

# 3-up stacked crop, labels burned in
if crops:
    cw = max(c.width for _, c in crops)
    ch = max(c.height for _, c in crops)
    band = 34
    sheet = Image.new("RGB", (cw, (ch + band) * len(crops)), (247, 244, 238))
    d = ImageDraw.Draw(sheet)
    for i, (label, c) in enumerate(crops):
        y = i * (ch + band)
        d.rectangle([0, y, cw, y + band], fill=(21, 35, 60))
        d.text((10, y + 10), label, fill=(247, 244, 238))
        sheet.paste(c, (0, y + band))
    out = HERE / "vec_10_sharpness_3up.png"
    sheet.save(out)
    print(f"\n  wrote {out.name}  ({sheet.width}x{sheet.height})")

print("\n  wrote vec_sharpness.json")
