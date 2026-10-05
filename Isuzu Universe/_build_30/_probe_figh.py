import os

import fitz

d = fitz.open(r"_build_30\_staged_v14.pdf")
seen = {}
for p in d:
    for im in p.get_image_info():
        h = im["bbox"][3] - im["bbox"][1]
        w = im["bbox"][2] - im["bbox"][0]
        seen[round(h)] = seen.get(round(h), 0) + 1
print("rendered figure heights (pt) -> count:", dict(sorted(seen.items())))
print("in mm:", {round(k / 72 * 25.4): v for k, v in sorted(seen.items())})
