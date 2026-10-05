"""Crop the QA screenshots into close-ups so the fine detail is readable."""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent


def crop(src, box, out, scale=2):
    p = HERE / src
    img = Image.open(p).convert("RGB")
    c = img.crop(box)
    if scale != 1:
        c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    dst = HERE / out
    c.save(dst)
    print(f"{src} {box} -> {out}  {c.size[0]}x{c.size[1]}")


# Israel pair: the two columns that share 31.05 / 34.85 in the source.
crop("06_shared_coordinate_pair.png", (500, 250, 950, 620), "crop_israel_pair.png", 2)

# The placeholder market panel, so the amber wording can be read.
crop("05_placeholder_market.png", (1170, 0, 1600, 780), "crop_placeholder_panel.png", 2)

# Panel on a market WITH numbers, lower half (fleet + PMS + not-included).
crop("03_panel_open.png", (1170, 380, 1600, 1000), "crop_panel_numbers.png", 2)

# Two labels that are close together in the default view (Nordics + Baltics area).
crop("01_globe_columns.png", (330, 170, 900, 560), "crop_labels_dense.png", 2)
