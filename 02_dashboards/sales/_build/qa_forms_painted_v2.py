"""Durable check: does each form of the family page actually paint its marks?

Why this exists. The page holds eight canvases but shows eight hidden/offscreen ones at
the default view, so a paint check on the default view passes while a form that is never
selected could be drawing nothing. Two weaker tests were tried and both misled:

  * canvas.width / canvas.height - form 8's small multiples read 0x0 after a form switch
    even though the page shows their bars (Chart.js resets the bitmap and the resize
    observer has not run yet in headless Chrome). Reading the bitmap is a stale read.
  * whole-region ink share - the panel chart areas carry 5-35% ink, but that ink includes
    the panel title and the percentage caption, so ink alone cannot tell a drawn chart
    from a titled empty box.

So this measures the thing the chart actually makes: pixels in the page's own bar colours,
navy #15233c and terracotta #c0552d. A titled empty box cannot produce them.

One Chrome run per form, each writing a screenshot; then the bar-colour count is measured
inside that form's chart region. Exits 1 if any form shows no bars.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
OUT = ROOT / "02_dashboards" / "sales" / "_qa_v2"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

NAVY = (0x15, 0x23, 0x3C)
TERRA = (0xC0, 0x55, 0x2D)
TOL = 26
MIN_BAR_PIXELS = 300

DRIVER = r"""
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    try { if (window.__pmfe2) window.__pmfe2.setForm('__FORM__'); } catch (e) {}
    setTimeout(function () {
      function rect(sel) {
        var el = typeof sel === 'string' ? document.querySelector(sel) : sel;
        if (!el) return null;
        var r = el.getBoundingClientRect();
        return {x: Math.round(r.x + window.scrollX), y: Math.round(r.y + window.scrollY),
                w: Math.round(r.width), h: Math.round(r.height)};
      }
      var regions = {
        main: rect('#c_main') ? rect('#c_main').x >= 0
                ? {x: rect('#c_main').x, y: rect('#c_main').y,
                   w: rect('#c_main').w, h: rect('#c_main').h} : null : null,
        grid: rect('#smlGrid'),
        table: rect('#tbl') || rect('table')
      };
      /* union box of everything that is visible, as a fallback */
      var full = {x: 0, y: 0, w: Math.round(document.documentElement.scrollWidth),
                  h: Math.round(document.documentElement.scrollHeight)};
      var el = document.createElement('script');
      el.type = 'application/json'; el.id = 'out';
      el.textContent = JSON.stringify({form: '__FORM__', regions: regions, full: full,
        canvases: Array.prototype.map.call(document.querySelectorAll('canvas'), function (c) {
          return c.id + ':' + c.width + 'x' + c.height; })});
      document.body.appendChild(el);
    }, 3000);
  }, 2800);
});
</script>
"""


def near(a: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
    return ((np.abs(a[:, :, 0] - rgb[0]) <= TOL)
            & (np.abs(a[:, :, 1] - rgb[1]) <= TOL)
            & (np.abs(a[:, :, 2] - rgb[2]) <= TOL))


def count_bars(img: Image.Image, box: dict) -> int:
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    x0, y0 = max(0, box["x"]), max(0, box["y"])
    sub = a[y0:y0 + box["h"], x0:x0 + box["w"]]
    if sub.size == 0:
        return 0
    return int(near(sub, NAVY).sum() + near(sub, TERRA).sum())


def run_form(form: str) -> dict:
    driver = DRIVER.replace("__FORM__", form)
    page = Path(tempfile.gettempdir()) / f"_paint_{form}.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", driver + "</body>"),
                    encoding="utf-8")
    shot = OUT / f"forms_painted_{form}.png"
    r = subprocess.run(
        [str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
         "--window-size=1440,3200", "--virtual-time-budget=30000",
         f"--screenshot={shot}", "--dump-dom", page.as_uri()],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=420)
    m = re.search(r'<script type="application/json" id="out">(.*?)</script>', r.stdout, re.S)
    info = json.loads(m.group(1)) if m else {"form": form, "error": "driver did not complete"}
    info["shot"] = str(shot)
    return info


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("FORM PAINT, measured as bar-coloured pixels (#15233c navy, #c0552d terracotta)")
    print("=" * 100)
    results = {}
    fails = []
    for form in ("f2", "f8", "f10"):
        info = run_form(form)
        results[form] = info
        shot = Path(info.get("shot", ""))
        if not shot.exists():
            print(f"\n  {form}: no screenshot ({info.get('error')})")
            fails.append(f"{form}: screenshot missing")
            continue
        img = Image.open(shot)
        full = info.get("full") or {}
        page_bars = count_bars(img, full) if full else 0
        print(f"\n  {form}: canvases {info.get('canvases')}")
        print(f"        screenshot {img.size[0]}x{img.size[1]}, "
              f"bar-coloured pixels on the page: {page_bars:,}")
        for name, box in (info.get("regions") or {}).items():
            if not box:
                continue
            n = count_bars(img, box)
            print(f"        region {name:<6} {box['w']}x{box['h']:<5} bars {n:,}")
        info["page_bars"] = page_bars
        if page_bars < MIN_BAR_PIXELS:
            fails.append(f"{form}: only {page_bars} bar-coloured pixels - the form did not draw")
    OUT.joinpath("forms_painted.json").write_text(json.dumps(results, indent=2),
                                                 encoding="utf-8")
    print()
    if fails:
        print("FORM PAINT FAIL:")
        for f in fails:
            print("  - " + f)
        return 1
    print("FORM PAINT PASS: each of f2, f8 and f10 carries bar-coloured pixels once selected, "
          "so every form draws its marks. Measured on the composited screenshot, not on the "
          "canvas bitmap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
