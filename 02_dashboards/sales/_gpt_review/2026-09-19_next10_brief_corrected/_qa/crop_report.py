"""Crop the changed regions out of the tall full-page renders so the reader can inspect them at
legible size. Read-only on the HTML; writes crops into _qa/."""
import os
from PIL import Image

QA = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\_qa"

def report(p):
    im = Image.open(p)
    # find the last row that is not uniform white-ish
    return im

jobs = [
    ("defectfix_01_full.png", "defectfix_01crop_page6.png", None),
    ("defectfix_01_full.png", "defectfix_01crop_page16.png", None),
    ("defectfix_03_full.png", "defectfix_03crop_sec7.png", None),
    ("defectfix_10_full.png", "defectfix_10crop_scope.png", (0, 0, 1440, 1300)),
    ("defectfix_02_full.png", "defectfix_02crop_bottom.png", None),
]

for src, dst, box in jobs:
    p = os.path.join(QA, src)
    im = Image.open(p)
    print(src, "size", im.size)
