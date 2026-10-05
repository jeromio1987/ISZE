"""Does MapLibre GL JS 5.6.2 substitute the {r} retina token in raster tile URLs?

Not part of the product. Loads the probe with the two raster styles and records
the exact tile URLs Chrome actually requested. If {r} is honoured the retina
variant asks for the @2x files; if it is not honoured the URL still contains a
literal "{r}" (a 404) or is identical to the plain variant.

Run:  python _qa/vec_ratio_test.py
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8511/_qa/vector_style_probe.html"
HERE = Path(__file__).resolve().parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

out = {}
with sync_playwright() as p:
    b = p.chromium.launch(
        headless=True, executable_path=CHROME,
        args=["--use-gl=angle", "--use-angle=swiftshader",
              "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
    )
    ctx = b.new_context(viewport={"width": 1400, "height": 950}, device_scale_factor=2)
    pg = ctx.new_page()

    urls: list[str] = []
    pg.on("request", lambda r: urls.append(r.url) if "cartocdn" in r.url else None)

    for key in ("raster-now", "raster-retina"):
        urls.clear()
        pg.goto(f"{BASE}?style={key}&proj=globe", wait_until="load", timeout=60000)
        try:
            pg.wait_for_function("() => window.__probe && window.__probe.idle === true",
                                 timeout=45000)
        except Exception:
            pass
        pg.wait_for_timeout(6000)
        tile_urls = sorted({u for u in urls if "rastertiles" in u})
        out[key] = {
            "tile_urls": tile_urls,
            "tile_request_count": len([u for u in urls if "rastertiles" in u]),
            "any_url_contains_literal_braces": any("{" in u for u in tile_urls),
            "any_2x_variant": any("@2x" in u for u in tile_urls),
        }
        print("=" * 74)
        print(f"  {key}")
        print("=" * 74)
        print(json.dumps(out[key], indent=1))
        print()

    b.close()

(HERE / "vec_ratio_test.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("wrote vec_ratio_test.json")
