"""QA driver for the vector basemap probe. Not part of the product.

Loads _qa/vector_style_probe.html over http://localhost:8511 in headless Chrome,
captures one screenshot per candidate, and dumps the machine-readable status
from window.__probe. Writes vec_*.png so it cannot collide with the existing
01_..14_ screenshot set.

Run (server must already be up via run_globe_server.ps1):
    python _qa/vec_probe_run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8511/_qa/vector_style_probe.html"
HERE = Path(__file__).resolve().parent

# style key -> screenshot file
CASES = [
    ("ofm-positron", "globe", "style", "vec_01_ofm_positron_globe.png", 14000),
    ("ofm-liberty", "globe", "style", "vec_02_ofm_liberty_globe.png", 14000),
    ("ofm-bright", "globe", "style", "vec_03_ofm_bright_globe.png", 14000),
    ("carto-positron", "globe", "style", "vec_04_carto_positron_globe.png", 14000),
    ("demo", "globe", "style", "vec_05_maplibre_demo_globe.png", 12000),
    ("ofm-positron", "mercator", "style", "vec_06_ofm_positron_mercator.png", 12000),
    ("raster-now", "globe", "style", "vec_07_raster_now_globe.png", 14000),
    ("raster-at2x", "globe", "style", "vec_11_raster_at2x_globe.png", 14000),
    ("carto-voyager", "globe", "style", "vec_09_carto_voyager_globe.png", 14000),
    # mode=overlay / mode=real: the exact mechanism the spec proposes
    ("ofm-positron", "globe", "overlay", "vec_12_overlay_ofm_positron_globe.png", 16000),
    ("ofm-positron", "mercator", "overlay", "vec_13_overlay_ofm_positron_mercator.png", 14000),
    ("ofm-liberty", "globe", "overlay", "vec_14_overlay_ofm_liberty_globe.png", 16000),
    # mode=real: the product's own layer stack, vector inserted before bm-land
    ("ofm-liberty", "globe", "real", "vec_22_real_liberty_globe.png", 18000),
    ("ofm-positron", "globe", "real", "vec_23_real_positron_globe.png", 18000),
    ("ofm-liberty", "mercator", "real", "vec_24_real_liberty_mercator.png", 16000),
]

# which (style, mode) pairs also get a second, zoomed screenshot
ZOOM_CROP = {("ofm-positron", "style"), ("raster-now", "style"),
             ("raster-at2x", "style"), ("carto-voyager", "style"),
             ("ofm-liberty", "style"), ("ofm-liberty", "real")}

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

results = []

with sync_playwright() as p:
    b = p.chromium.launch(
        headless=True,
        executable_path=CHROME,
        args=["--use-gl=angle", "--use-angle=swiftshader",
              "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
    )
    ctx = b.new_context(viewport={"width": 1400, "height": 950}, device_scale_factor=2)
    pg = ctx.new_page()

    console_msgs: list[str] = []
    pg.on("console", lambda m: console_msgs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: console_msgs.append(f"[pageerror] {e}"))

    net: dict[str, dict] = {}

    def on_response(resp):
        u = resp.url
        if "openfreemap.org" in u or "cartocdn.com" in u or "demotiles.maplibre.org" in u:
            if "/fonts/" in u or "/font/" in u:
                k = "glyph"
            elif "/sprite" in u:
                k = "sprite"
            elif u.endswith(".pbf") or ".mvt" in u:
                k = "vector_tile"
            elif "rastertiles" in u or "/natural_earth/" in u or "ne2sr" in u:
                k = "raster_tile"
            elif u.endswith(".json") or "/styles/" in u or u.endswith("/planet"):
                k = "style_json"
            else:
                k = "other"
            slot = net.setdefault(k, {"ok": 0, "bad": 0, "examples": []})
            if 200 <= resp.status < 400:
                slot["ok"] += 1
            else:
                slot["bad"] += 1
                if len(slot["examples"]) < 3:
                    slot["examples"].append(f"{resp.status} {u}")

    pg.on("response", on_response)
    pg.on("requestfailed", lambda r: (
        net.setdefault("requestfailed", {"ok": 0, "bad": 0, "examples": []})
        ["examples"].append(f"{r.failure} {r.url}")
        if len(net.setdefault("requestfailed", {"ok": 0, "bad": 0, "examples": []})["examples"]) < 6
        else None
    ))

    for key, proj, mode, shot, wait_ms in CASES:
        console_msgs.clear()
        net.clear()
        url = f"{BASE}?style={key}&proj={proj}&mode={mode}"
        print("=" * 74)
        print(f"  {key}  /  {proj}  /  mode={mode}")
        print("=" * 74)
        try:
            pg.goto(url, wait_until="load", timeout=60000)
            # wait for the map's idle event, but never hang
            try:
                pg.wait_for_function(
                    "() => window.__probe && window.__probe.idle === true",
                    timeout=45000,
                )
            except Exception as we:
                print(f"  WARN: idle wait failed: {we}")
            pg.wait_for_timeout(wait_ms)

            st = pg.evaluate("() => window.__probe")
            out = {
                "style": key,
                "projection": proj,
                "mode": mode,
                "sources": st.get("sources"),
                "layerCount": st.get("layerCount"),
                "overlayApplied": st.get("overlayApplied"),
                "overlayAdded": (st.get("overlayAdded") or [])[:6],
                "loaded": st.get("loaded"),
                "idle": st.get("idle"),
                "labelLayers": st.get("labelLayers"),
                "renderedSymbolFeatures": st.get("renderedSymbolFeatures"),
                "network": {k: {"ok": v["ok"], "bad": v["bad"],
                                "examples": v["examples"]}
                            for k, v in sorted(net.items())},
                "errors": st.get("errors"),
                "mapErrors": st.get("mapErrors")[:8],
                "console": console_msgs[:14],
            }
            print(json.dumps(out, indent=1))
            results.append(out)
            pg.screenshot(path=str(HERE / shot))
            print(f"  -> {shot}")

            # dense-detail crop: the same view zoomed into Benelux, where the
            # graininess is worst on raster
            if (key, mode) in ZOOM_CROP:
                pg.evaluate(
                    """() => {
                        window.__probeMap.jumpTo({center: [5.0, 50.6], zoom: 6.4,
                                                  pitch: 0, bearing: 0});
                    }"""
                )
                pg.wait_for_timeout(9000)
                crop = shot.replace(".png", "_zoom_benelux.png")
                pg.screenshot(path=str(HERE / crop))
                st2 = pg.evaluate("() => window.__probe")
                print(f"  -> {crop}  renderedSymbolFeatures="
                      f"{st2.get('renderedSymbolFeatures')}  net="
                      + json.dumps({k: f"{v['ok']}ok/{v['bad']}bad"
                                    for k, v in sorted(net.items())}))
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {exc}")
            results.append({"style": key, "projection": proj, "FAILED": str(exc)})
        print()

    b.close()

(HERE / "vec_probe_results.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8"
)
print("wrote vec_probe_results.json")
