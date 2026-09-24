#!/usr/bin/env python3
"""Measure the rendered page height, then re-capture at that height and slice into bands."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image

BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\dealer_demand_ituk_20260924")
PAGE = BUILD / "page" / "Dealer_Parts_Demand_ITUK_CY2025_INTERNAL.html"
QA = BUILD / "page" / "_qa"
EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def shot(out: Path, height: int) -> None:
    cmd = [EXE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           f"--window-size=1400,{height}", "--force-device-scale-factor=1",
           "--user-data-dir=" + str(QA / "_profile"), "--virtual-time-budget=5000",
           "--screenshot=" + str(out),
           "file:///" + str(PAGE).replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    print("shot", height, "exit", r.returncode)


def main() -> None:
    QA.mkdir(parents=True, exist_ok=True)
    for p in QA.glob("band_*.png"):
        p.unlink()

    # probe the real height by measuring the png that results from a very tall window
    probe = QA / "_probe.png"
    shot(probe, 30000)
    with Image.open(probe) as im:
        w, h = im.size
    print("probe size", w, h)

    # find where the content actually ends: the last row carrying anything that is not
    # the page background. Body is #f7f4ee, so compare against a sampled background pixel
    # rather than a fixed threshold, which would treat the page itself as ink.
    with Image.open(probe).convert("RGB") as g:
        w, h = g.size
        px = g.load()
        bg = px[3, h - 3]
        last = 0
        for y in range(h - 1, 0, -2):
            for x in range(0, w, 6):
                r, gg, b = px[x, y]
                if abs(r - bg[0]) + abs(gg - bg[1]) + abs(b - bg[2]) > 18:
                    last = y
                    break
            if last:
                break
    print("content ends at", last, "background", bg)

    # re-shoot at exactly the content height so nothing is cut
    final = QA / "page.png"
    shot(final, last + 40)
    with Image.open(final) as im:
        print("final size", im.size)
        H = im.size[1]
        bands = 6
        step = H // bands
        for i in range(bands):
            top = i * step
            bot = H if i == bands - 1 else (i + 1) * step
            im.crop((0, top, im.size[0], bot)).save(QA / f"band_{i+1}.png")
    print("bands:", sorted(p.name for p in QA.glob("band_*.png")))

    # a zoom on the dealer table, captured with a real scroll so the table can be read
    zoom = QA / "zoom_dealers.png"
    shot(zoom, 2400)
    with Image.open(zoom) as im:
        im.crop((0, 900, im.size[0], 2300)).save(QA / "zoom_dealers.png")

    (QA / "shot_meta.json").write_text(json.dumps(
        {"content_end": last, "final_height": H, "bands": bands}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
