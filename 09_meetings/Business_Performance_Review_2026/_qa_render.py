"""Render-based QA. Reads the PNGs PowerPoint actually produced and looks for
the defects a geometry check cannot see:

  1. title text crossing the red rule (dark pixels touching/below the rule)
  2. text running into the bottom edge of the slide
  3. text sitting on top of the chart image (dark-on-dark)
  4. a slide that is mostly empty

This is the check that was missing: it uses rendered pixels, not my estimate of
how text wraps.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
RENDER = HERE / "_qa" / "render"

problems: list[dict] = []
summary = []

for png in sorted(RENDER.glob("s*.png")):
    idx = int(png.stem[1:])
    im = Image.open(png).convert("RGB")
    a = np.array(im)
    h, w, _ = a.shape
    issues = []

    # 1. the red rule row
    rule_y = None
    for y in range(int(h * 0.30)):
        row = a[y]
        red = ((row[:, 0] > 140) & (row[:, 1] < 100) & (row[:, 2] < 100)).sum()
        if red > w * 0.5:
            rule_y = y
            break

    # "Text ink" only: near-black pixels. The house palette has a red rule and a
    # red footer bar, and counting red as ink produced two false alarms on every
    # slide (the rule's own anti-aliased edge, and the footer bar), so the
    # detector is explicitly colour-aware.
    s = a.sum(axis=2)
    is_red = (a[:, :, 0] > 120) & (a[:, :, 1] < 110) & (a[:, :, 2] < 110)
    dark = (s < 300) & (~is_red)

    if rule_y is not None:
        # dark pixels in the three rows immediately above the rule = a title
        # whose last line is touching it
        band = dark[max(0, rule_y - 3):rule_y]
        if band.mean() > 0.03:
            issues.append(f"title touches the rule at y={rule_y}")

    # 2. text at the very bottom, excluding the designed footer bar (bottom 1.2%)
    foot = int(h * 0.985)
    below = dark[foot:]
    if below.mean() > 0.02:
        issues.append("text reaches the bottom edge")

    # 3. chart-vs-text: look for dark text rows inside the chart area that sit
    #    directly on a dark chart bar (the legend-on-bars failure)
    if rule_y is not None:
        chart_top = rule_y + int(h * 0.03)
        chart_bot = int(h * 0.92)
        for y in range(chart_top, chart_bot, 3):
            row = a[y]
            nonwhite = (row.sum(axis=1) < 720)
            if not nonwhite.any():
                continue
            # a run of near-black pixels wider than 200px inside the chart is a
            # bar; light text over it is fine, but mid-grey on it is not
            black = (row.sum(axis=1) < 200)
            if black.mean() > 0.55:
                mid = ((row.sum(axis=1) > 200) & (row.sum(axis=1) < 600))
                if mid.sum() > 40:
                    issues.append(f"possible text on a dark bar at y={y}")
                    break

    ink = float((np.array(im.convert("L")) < 245).mean() * 100)
    if ink < 3.0:
        issues.append(f"slide is nearly empty (ink {ink:.1f}%)")

    summary.append({"slide": idx, "ink": round(ink, 2), "issues": issues})
    if issues:
        problems.append({"slide": idx, "issues": issues})

print(f"checked {len(summary)} rendered slides")
print()
if problems:
    print(f"PROBLEMS on {len(problems)} slide(s):")
    for p in problems:
        print(f"  slide {p['slide']:02d}: " + "; ".join(p["issues"]))
else:
    print("render QA: no title-rule collisions, no bottom-edge overrun, "
          "no text on bars, no empty slides")
low = [s for s in summary if s["ink"] < 6]
if low:
    print()
    print("lowest-ink slides (worth a look, not necessarily wrong):")
    for s in sorted(low, key=lambda x: x["ink"])[:6]:
        print(f"  slide {s['slide']:02d}  ink {s['ink']}%")
(RENDER / "_render_qa.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
