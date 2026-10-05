#!/usr/bin/env python3
"""Second pass: remove the old drawn-vehicle render block that the first pass
left behind. It now duplicates functions the photograph layer provides, and a
later duplicate silently wins in JavaScript, which would ship the old engine.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "build_truck_page.py")

src = io.open(PAGE, encoding="utf-8").read()
before = len(src)

START = "/* Fit the current vehicle to the stage using the real projected corners"
END = "/* ================= tooltip ================= */"

a = src.index(START)
b = src.index(END, a)
removed = src[a:b]

src = src[:a] + src[b:]
io.open(PAGE, "w", encoding="utf-8", newline="\n").write(src)

print(f"removed {len(removed):,} bytes of the old render block")
print(f"{before:,} -> {len(src):,} bytes")
for k in ("drawFaces", "extrude(", "projectZ(", "CAM.az", "HALF_W", "G.bounds",
          "screenOnTruck", "pointInPolyWorld", "drawArch", "drawWheel", "MAT."):
    print("  remaining", k.ljust(18), src.count(k))
