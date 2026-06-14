# -*- coding: utf-8 -*-
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Projects" / "Propertiq" / "mockups"
DST_ASSETS = ROOT / "Dashboards" / "propertiq-assets"
INJECT = (
    '  <link rel="stylesheet" href="_ui/editorial.css">\n'
    '  <link rel="stylesheet" href="_ui/editorial-full.css">\n'
    '  <script src="_ui/editorial-charts.js"></script>\n'
    '  <script src="_ui/isze-shell.js" defer></script>\n'
)

DST_ASSETS.mkdir(parents=True, exist_ok=True)
for f in (SRC / "assets").glob("*"):
    if f.is_file() and f.stat().st_size > 10_000:
        shutil.copy2(f, DST_ASSETS / f.name)
        print(f"  asset: {f.name}")

text = (SRC / "v01_split_hero.html").read_text(encoding="utf-8")
text = text.replace("assets/", "propertiq-assets/")
if "isze-shell.js" not in text:
    text = text.replace("</head>", INJECT + "</head>", 1)
(ROOT / "Dashboards" / "PROPERTIQ.html").write_text(text, encoding="utf-8")
print("  wrote Dashboards/PROPERTIQ.html")
