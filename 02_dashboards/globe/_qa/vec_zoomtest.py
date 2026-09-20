"""High-zoom comparison: raster vs vector at street level.

The argument for vector is resolution independence, not just a prettier default
view. A retina raster (@2x) closes much of the gap at one particular zoom; the
claim to test is that it falls behind again as you zoom past its native
resolution, while vector geometry stays crisp.

Same camera for every case: centre Amsterdam-ish [4.9, 52.37], pitch 0, zoom
from the --zoom argument. deviceScaleFactor 2.

Not part of the product.

Run:  python _qa/vec_zoomtest.py
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
BASE = "http://localhost:8511/_qa/vector_style_probe.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CASES = [
    ("raster-now", "vec_16_z12_raster_now.png"),
    ("raster-at2x", "vec_17_z12_raster_at2x.png"),
    ("ofm-liberty", "vec_18_z12_ofm_liberty.png"),
]
ZOOM = 12.0
CENTER = [4.9, 52.37]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME,
                          args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    ctx = b.new_context(viewport={"width": 1400, "height": 950}, device_scale_factor=2)
    pg = ctx.new_page()
    net_count = {}
    pg.on("response", lambda r: net_count.__setitem__(
        "vector" if (".pbf" in r.url or ".mvt" in r.url) else "raster",
        net_count.get("vector" if (".pbf" in r.url or ".mvt" in r.url) else "raster", 0) + 1)
        if ("cartocdn" in r.url or "openfreemap" in r.url) else None)

    for key, shot in CASES:
        net_count.clear()
        pg.goto(f"{BASE}?style={key}&proj=mercator", wait_until="load", timeout=60000)
        try:
            pg.wait_for_function("() => window.__probe && window.__probe.idle === true",
                                 timeout=45000)
        except Exception:
            pass
        pg.evaluate("([c,z]) => window.__probeMap.jumpTo({center:c, zoom:z, pitch:0, bearing:0})",
                    [CENTER, ZOOM])
        pg.wait_for_timeout(11000)
        pg.screenshot(path=str(HERE / shot))
        st = pg.evaluate("() => window.__probe")
        print(f"  {key:<14} labels={st.get('renderedSymbolFeatures'):<5} "
              f"tiles={json.dumps(net_count)} errors={len(st.get('errors') or [])}  -> {shot}")

    b.close()
