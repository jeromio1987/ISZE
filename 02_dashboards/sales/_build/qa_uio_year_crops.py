#!/usr/bin/env python3
"""Crop the normalised chart out of the deep family page and save it as a PNG for image-reading.

The whole-point panel of this rebuild is the fleet denominator, so it gets its own picture as well
as the ink measurement: one at 1440px and one at 1000px, cropped to the chart and its key.

Usage:
    python 02_dashboards/sales/_build/qa_uio_year_crops.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_Deep.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_family_deep"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

PROBE = r"""
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    function box(sel){
      var el=document.querySelector(sel); if(!el) return null;
      var r=el.getBoundingClientRect();
      return {x:Math.round(r.left),y:Math.round(r.top+window.scrollY),
              w:Math.round(r.width),h:Math.round(r.height)};
    }
    var el=document.createElement('script');
    el.type='application/json'; el.id='crop-out';
    el.textContent=JSON.stringify({
      norm:box('#sec_normal'), normCanvas:box('#c_norm'),
      famTable:box('#t_fam'), fleetNote:box('#fleetNote'),
      pageH:document.documentElement.scrollHeight});
    document.body.appendChild(el);
  }, 3200);
});
</script>
"""


def shot(width: int) -> dict:
    page = QA / f"_crop_{width}.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", PROBE + "</body>"),
                    encoding="utf-8")
    dom = subprocess.run(
        [str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--window-size={width},3000", "--virtual-time-budget=30000", "--dump-dom",
         page.as_uri()], capture_output=True, text=True, timeout=420).stdout
    m = re.search(r'<script type="application/json" id="crop-out">(.*?)</script>', dom, re.S)
    if not m:
        raise SystemExit(f"crop probe did not run at {width}px")
    boxes = json.loads(m.group(1))
    h = int(boxes["pageH"]) + 60
    png = QA / f"deep_full_{width}.png"
    subprocess.run(
        [str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
         "--force-device-scale-factor=1", f"--window-size={width},{h}",
         "--virtual-time-budget=30000", f"--screenshot={png}", page.as_uri()],
        capture_output=True, text=True, timeout=420)
    img = Image.open(png)
    out = {}
    for name, key in (("norm", "norm"), ("famtable", "famTable")):
        b = boxes.get(key)
        if not b:
            continue
        pad = 8
        crop = img.crop((max(0, b["x"] - pad), max(0, b["y"] - pad),
                         min(img.width, b["x"] + b["w"] + pad),
                         min(img.height, b["y"] + b["h"] + pad)))
        f = QA / f"uio_year_{name}_{width}.png"
        crop.save(f)
        out[name] = str(f)
        print(f"wrote {f}  ({crop.width}x{crop.height})")
    return out


if __name__ == "__main__":
    QA.mkdir(parents=True, exist_ok=True)
    for w in (1440, 1000):
        shot(w)
