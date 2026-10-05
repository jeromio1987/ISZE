"""Verify the proposed live-layer health probe for a VECTOR style.

The existing probe (index.html probeLiveTiles) fetches one raster tile with
fetch(url, {mode:'no-cors'}) and treats "the promise resolved" as success. That
is only sound because raster tiles are same-shape opaque images and the only
way that fetch rejects is a transport failure the browser will report.

For a vector style there is no single image tile to fetch, and a style JSON
fetch is CORS-readable (Access-Control-Allow-Origin: *), so the probe can and
must be stricter: read the HTTP status, parse the JSON, follow the TileJSON to
a real tile URL, and check the tile's HTTP status AND content type.

This script asserts three things the probe MUST satisfy:

  1. ONLINE, healthy        -> probe returns ok, naming the provider
  2. OFFLINE, all blocked   -> probe returns NOT ok
  3. ONLINE but tile 404    -> probe returns NOT ok   (the false-positive case
                               the old raster probe would have called success)

Not part of the product.

Run:  python _qa/vec_probe_health_test.py
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

STYLE_URL = "https://tiles.openfreemap.org/styles/positron"

# The probe as it should be written into index.html.
# Takes ONE object argument. (Playwright spreads an array across parameters, and
# an array reaching an arrow function with one param gets stringified by fetch()
# into "url," with a trailing comma, which 404s. Object argument avoids that.)
PROBE_JS = """
async ({styleUrl, forceTileUrl}) => {
  const out = { ok: false, reason: "", styleStatus: null, tileStatus: null,
                tileType: null, tileUrl: null, provider: null, tileBytes: null };
  let style;
  try {
    const r = await fetch(styleUrl, { cache: "no-store" });
    out.styleStatus = r.status;
    if (!r.ok) { out.reason = "style HTTP " + r.status; return out; }
    style = await r.json();
  } catch (e) {
    out.reason = "style fetch failed: " + e.message; return out;
  }
  if (!style || !style.sources) { out.reason = "style is not JSON with sources"; return out; }

  // name the vector source and resolve its real tile URL
  let tileUrl = forceTileUrl || null;
  if (!tileUrl) {
    for (const k of Object.keys(style.sources)) {
      const s = style.sources[k];
      if (s.type !== "vector") continue;
      if (s.tiles && s.tiles.length) { tileUrl = s.tiles[0]; break; }
      if (s.url) {
        try {
          const tj = await (await fetch(s.url, { cache: "no-store" })).json();
          if (tj && tj.tiles && tj.tiles.length) { tileUrl = tj.tiles[0]; break; }
        } catch (e) { /* try the next source */ }
      }
    }
  }
  if (!tileUrl) { out.reason = "no vector tile URL found in the style"; return out; }

  // z/x/y chosen to land on land in Europe rather than open sea
  tileUrl = tileUrl.replace("{z}", "4").replace("{x}", "8").replace("{y}", "5");
  out.tileUrl = tileUrl;

  try {
    const t = await fetch(tileUrl, { cache: "no-store" });
    out.tileStatus = t.status;
    out.tileType = t.headers.get("content-type");
    const buf = await t.arrayBuffer();
    out.tileBytes = buf.byteLength;
    if (!t.ok) { out.reason = "tile HTTP " + t.status; return out; }
    if (!buf.byteLength) { out.reason = "tile was empty"; return out; }
    // a vector tile is a protobuf, never an HTML error page
    if (out.tileType && /text\\/html/i.test(out.tileType)) {
      out.reason = "tile served as HTML (interstitial or error page)";
      return out;
    }
  } catch (e) {
    out.reason = "tile fetch failed: " + e.message; return out;
  }

  out.ok = true;
  out.provider = "OpenFreeMap";
  return out;
}
"""

results = {}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME,
                          args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    ctx = b.new_context(viewport={"width": 900, "height": 600})

    # ---- 1. online, healthy
    pg = ctx.new_page()
    pg.goto("http://localhost:8511/_qa/vector_style_probe.html", wait_until="load", timeout=60000)
    pg.wait_for_timeout(2000)
    r1 = pg.evaluate(PROBE_JS, {"styleUrl": STYLE_URL, "forceTileUrl": None})
    results["1_online_healthy"] = r1
    print("=" * 74)
    print("  1. ONLINE, HEALTHY  ->  must be ok:true")
    print("=" * 74)
    print(json.dumps(r1, indent=1))
    pg.close()

    # ---- 2. offline, every non-localhost request blocked
    pg2 = ctx.new_page()
    blocked = []
    pg2.route("**/*", lambda route: (
        route.continue_() if route.request.url.startswith("http://localhost")
        else (blocked.append(route.request.url), route.abort())[1]
    ))
    pg2.goto("http://localhost:8511/_qa/vector_style_probe.html", wait_until="load", timeout=60000)
    pg2.wait_for_timeout(2000)
    r2 = pg2.evaluate(PROBE_JS, {"styleUrl": STYLE_URL, "forceTileUrl": None})
    results["2_offline_blocked"] = r2
    results["2_offline_blocked"]["_blocked_count"] = len(blocked)
    print()
    print("=" * 74)
    print("  2. OFFLINE, ALL NON-LOCALHOST BLOCKED  ->  must be ok:false")
    print("=" * 74)
    print(json.dumps(r2, indent=1))
    pg2.close()

    # ---- 3. the false-positive case: style reachable, tile 404s
    pg3 = ctx.new_page()
    pg3.goto("http://localhost:8511/_qa/vector_style_probe.html", wait_until="load", timeout=60000)
    pg3.wait_for_timeout(2000)
    bogus = "https://tiles.openfreemap.org/planet/20260913_164504_pt/{z}/{x}/{y}.pbf"
    r3 = pg3.evaluate(PROBE_JS, {
        "styleUrl": STYLE_URL,
        "forceTileUrl": bogus.replace("_pt/", "_pt/NOPE/"),
    })
    results["3_tile_404"] = r3
    print()
    print("=" * 74)
    print("  3. STYLE OK BUT TILE RETURNS 404  ->  must be ok:false")
    print("=" * 74)
    print(json.dumps(r3, indent=1))
    pg3.close()

    # ---- 4. what the OLD raster-style probe does in the same situation
    pg4 = ctx.new_page()
    pg4.goto("http://localhost:8511/_qa/vector_style_probe.html", wait_until="load", timeout=60000)
    pg4.wait_for_timeout(1500)
    r4 = pg4.evaluate("""async (u) => {
      try { await fetch(u, {mode:'no-cors', cache:'no-store'}); return {resolved:true, verdict:'SUCCESS'}; }
      catch (e) { return {resolved:false, verdict:'failure', err:String(e)}; }
    }""", "https://tiles.openfreemap.org/planet/20260913_164504_pt/4/8/5.pbf")
    results["4_old_method_on_404"] = r4
    print()
    print("=" * 74)
    print("  4. THE OLD {mode:'no-cors'} METHOD AGAINST A 404  ->  false positive")
    print("=" * 74)
    print(json.dumps(r4, indent=1))
    pg4.close()

    b.close()

(HERE / "vec_probe_health_test.json").write_text(json.dumps(results, indent=2),
                                                 encoding="utf-8")

print()
print("=" * 74)
print("  VERDICT")
print("=" * 74)
print(f"  1 online healthy   ok={results['1_online_healthy']['ok']}   (want True)")
print(f"  2 offline blocked  ok={results['2_offline_blocked']['ok']}  (want False)")
print(f"  3 tile 404         ok={results['3_tile_404']['ok']}  (want False)")
print(f"  4 old method on 404         -> {results['4_old_method_on_404']['verdict']}")
print()
print("wrote vec_probe_health_test.json")
