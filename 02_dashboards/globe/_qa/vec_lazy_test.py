"""Does declaring a vector source with `url` cause an external request even when
no layer uses it?

This matters because index.html is offline-first today and the offline check
proves it: with the live layer off, the page makes ZERO non-localhost requests
(check_offline.py printed "external requests blocked: 0"). If adding a vector
source at map-build time fetches its TileJSON immediately, that property is
lost and the vector layer must be created lazily on toggle instead.

Not part of the product.

Run:  python _qa/vec_lazy_test.py
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PAGE = """
<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="../_ui/maplibre-gl.css">
<style>html,body{margin:0;height:100%}#map{position:absolute;inset:0}</style>
</head><body><div id="map"></div>
<script src="../_ui/maplibre-gl.js"></script>
<script>
window.__r = {requests: [], ready: false, errors: []};
const map = new maplibregl.Map({
  container: 'map',
  style: { version: 8, sources: {},
           layers: [{id:'bg', type:'background', paint:{'background-color':'#e8e2d6'}}] },
  center: [8, 50], zoom: 3.1, attributionControl: false,
  projection: { type: 'globe' }
});
map.on('error', e => window.__r.errors.push(String(e && e.error ? e.error.message : e)));
map.on('load', () => {
  /* Declare a vector source with `url` and a hidden layer, exactly the shape
     index.html uses for its raster source today. */
  try {
    map.setGlyphs('https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf');
    map.addSource('vec', { type: 'vector', url: 'https://tiles.openfreemap.org/planet' });
    map.addLayer({ id: 'vec-hidden', type: 'fill', source: 'vec',
                   'source-layer': 'water', layout: { visibility: 'none' },
                   paint: { 'fill-color': '#88a' } });
    window.__r.declared = true;
  } catch (e) { window.__r.errors.push('declare: ' + e.message); }
  window.__r.ready = true;
});
window.__m = map;
</script></body></html>
"""

probe = HERE / "_vec_lazy_probe.html"
probe.write_text(PAGE, encoding="utf-8")

out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME,
                          args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_context(viewport={"width": 900, "height": 600}).new_page()

    reqs: list[str] = []
    pg.on("request", lambda r: reqs.append(r.url)
          if "openfreemap.org" in r.url else None)

    pg.goto("http://localhost:8511/_qa/_vec_lazy_probe.html",
            wait_until="load", timeout=60000)
    pg.wait_for_function("() => window.__r && window.__r.ready === true", timeout=30000)
    pg.wait_for_timeout(8000)

    out["at_declare_hidden_layer"] = {
        "openfreemap_requests": sorted(set(reqs)),
        "count": len(reqs),
    }
    print("=" * 74)
    print("  VECTOR SOURCE DECLARED, LAYER HIDDEN (visibility: none)")
    print("=" * 74)
    print(f"  openfreemap.org requests: {len(reqs)}")
    for u in sorted(set(reqs)):
        print(f"    {u}")
    print(f"  tiledata fetched before any toggle? {'YES' if any('.pbf' in u for u in reqs) else 'NO'}")
    print()

    # now make it visible and count again
    reqs.clear()
    pg.evaluate("() => window.__m.setLayoutProperty('vec-hidden','visibility','visible')")
    pg.wait_for_timeout(9000)
    out["after_visibility_on"] = {
        "openfreemap_requests_count": len(reqs),
        "tile_requests": len([u for u in reqs if ".pbf" in u]),
        "example": reqs[:4],
    }
    print("=" * 74)
    print("  SAME SOURCE, LAYER MADE VISIBLE")
    print("=" * 74)
    print(f"  openfreemap.org requests: {len(reqs)}  "
          f"(vector tiles: {len([u for u in reqs if '.pbf' in u])})")
    for u in reqs[:5]:
        print(f"    {u}")
    print()
    print("  errors:", pg.evaluate("() => window.__r.errors"))

    b.close()

(HERE / "vec_lazy_test.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
probe.unlink(missing_ok=True)
print("\nwrote vec_lazy_test.json")
