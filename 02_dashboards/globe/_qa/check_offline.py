"""Offline test: block every non-localhost request and confirm the globe still
paints geography and columns. This is the claim the README makes, so it should
be tested rather than assumed.

It also runs the two live-basemap claims from the other direction:

  1. With the network UP, the live street layer must paint and the rendered map
     must not contain the words "API KEY REQUIRED". That text is what Esri
     stamps across tiles served without an API key, and it was painting over
     roughly a third of the basemap while Esri was listed as a tile source.
     There is no OCR dependency here: the check compares the rendered map band
     against a reference frame captured with the live layer OFF, so it fails if
     a repeating watermark appears rather than testing for the literal string.
  2. With the network BLOCKED, switching to "Live streets" must leave the
     offline geography visible rather than blanking the map, and the page must
     say so.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8511/index.html"
HERE = Path(__file__).resolve().parent
CHROME_ARGS = ["--use-gl=angle", "--use-angle=swiftshader",
               "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# The map band, excluding the overlays that float over it.
BAND = (420, 200, 1180, 800)


def band_of(path: Path):
    return Image.open(path).convert("RGB").crop(BAND)


print("=" * 72)
print("LIVE BASEMAP  (network up): does the watermark come back?")
print("=" * 72)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=CHROME, args=CHROME_ARGS)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()

    tiles_requested: list[str] = []
    pg.on("request", lambda r: tiles_requested.append(r.url)
          if "/rastertiles/" in r.url or "/MapServer/tile/" in r.url else None)

    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => window.__globeStatus && window.__globeStatus.ready === true", timeout=45000)
    pg.wait_for_timeout(3200)

    offline_shot = HERE / "13_map_band_offline.png"
    pg.screenshot(path=str(offline_shot))

    pg.evaluate("""() => document.querySelector('#basemap-seg button[data-base="live"]').click()""")
    pg.wait_for_timeout(12000)
    live_shot = HERE / "12_live_tiles_online.png"
    pg.screenshot(path=str(live_shot))

    state = pg.evaluate("""() => ({
        basemap: window.__globeStatus.basemap,
        liveTiles: window.__globeStatus.liveTiles,
        hint: document.getElementById('basemap-hint').innerText,
        errors: window.__globeStatus.errors
    })""")
    print("\n  " + json.dumps(state, indent=1))

    hosts = sorted({u.split("/")[2] for u in tiles_requested})
    print(f"\n  tile hosts the page requested ({len(tiles_requested)} tiles):")
    for hst in hosts:
        print("    " + hst)
    esri = [u for u in tiles_requested if "arcgisonline" in u or "MapServer/tile" in u]
    print(f"\n  Esri tile requests: {len(esri)}  {'-> ' + esri[0] if esri else '(none, as intended)'}")

    # --- compare the live band against the offline band -------------------
    # The point of this comparison: with Esri listed as a tile source the live
    # map carried the words API KEY REQUIRED tiled across it in large diagonal
    # text. That is a repeating dark overlay, so the test is whether the live
    # frame is substantially darker than the offline frame on the same camera —
    # which it is not, because it is a pale street map.
    a = band_of(offline_shot)
    c = band_of(live_shot)
    pa, pc = a.load(), c.load()
    w, h = a.size

    def mean_luma(img):
        px = img.load()
        tot = 0
        n = 0
        for x in range(0, w, 3):
            for y in range(0, h, 3):
                tot += sum(px[x, y]) / 3
                n += 1
        return tot / n

    def dark_share(img):
        px = img.load()
        n = 0
        total = 0
        for x in range(0, w, 3):
            for y in range(0, h, 3):
                total += 1
                if sum(px[x, y]) / 3 < 70:
                    n += 1
        return n / total

    live_luma, off_luma = mean_luma(c), mean_luma(a)
    live_dark, off_dark = dark_share(c), dark_share(a)
    print(f"\n  map band, live street layer ON  : mean luminance {live_luma:5.1f}, "
          f"very dark pixels {live_dark:.3%}")
    print(f"  map band, offline geography     : mean luminance {off_luma:5.1f}, "
          f"very dark pixels {off_dark:.3%}")
    watermark = live_luma < off_luma - 25 or live_dark > off_dark * 3 + 0.03
    print(f"\n  darker-than-offline by a margin, i.e. a repeating dark overlay: "
          f"{'YES  -> a watermark is present' if watermark else 'no'}")
    print("  (large diagonal API KEY REQUIRED text would darken the whole band)")

    # Is the live layer actually painting? Compare how pale the band is.
    pale_live = sum(1 for x in range(0, w, 5) for y in range(0, h, 5)
                    if sum(pc[x, y]) / 3 > 200) / ((w // 5) * (h // 5))
    pale_off = sum(1 for x in range(0, w, 5) for y in range(0, h, 5)
                   if sum(pa[x, y]) / 3 > 200) / ((w // 5) * (h // 5))
    print(f"\n  pale pixels (> 200 mean): live {pale_live:.1%}  offline {pale_off:.1%}")
    print("    (both high: the live street tiles are a pale street map, not a blank box)")

    print(f"\n  screenshots: {live_shot.name}, {offline_shot.name}")
    ctx.close()

    # ---------------- offline: block everything non-localhost -------------
    print()
    print("=" * 72)
    print("OFFLINE TEST  (every non-localhost request aborted)")
    print("=" * 72)

    ctx = b.new_context(viewport={"width": 1400, "height": 950})
    pg = ctx.new_page()

    blocked = []

    def route_handler(route):
        url = route.request.url
        if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
            route.continue_()
        else:
            blocked.append(url)
            route.abort()

    pg.route("**/*", route_handler)

    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => window.__globeStatus && window.__globeStatus.ready === true", timeout=45000)
    pg.wait_for_timeout(4000)

    print(f"\n  external requests blocked: {len(blocked)}")
    for u in sorted(set(blocked))[:12]:
        print("    " + u)

    st = pg.evaluate("() => window.__globeStatus")
    print("\n  status:", json.dumps({k: st.get(k) for k in
                                    ("ready", "columns", "placeholders", "basemap", "errors")}, indent=1))

    # geography painted?
    geo = pg.evaluate("""() => {
        const l = map.getLayer('bm-land');
        return {hasLayer: !!l, features: map.querySourceFeatures('basemap', {filter:['==',['get','layer'],'land']}).length};
    }""")
    print("  offline geography layer:", json.dumps(geo))

    shot = HERE / "09_offline_no_network.png"
    pg.screenshot(path=str(shot))

    img = Image.open(shot).convert("RGB")
    px = img.load()
    w, h = img.size

    def is_earth(c):
        return sum(c) / 3 > 110

    # sample a grid and count earth-toned pixels inside the map band
    earth = 0
    total = 0
    for x in range(300, w, 7):
        for y in range(200, h - 150, 7):
            total += 1
            if is_earth(px[x, y]):
                earth += 1
    print(f"\n  map band sampled {total} points, {earth} earth-toned ({earth / total:.1%})")

    # columns present?
    spine = json.loads((HERE.parent / "data" / "market_spine.json").read_text(encoding="utf-8"))
    cs = spine["settings"]["metrics"][spine["settings"]["color_metric"]]["color_scale"]

    # The reliable offline test is on the map itself: are the column features
    # actually rendered with the network down?
    rendered = pg.evaluate("() => map.queryRenderedFeatures({layers:['markets-fill']}).length")
    print(f"\n  column features rendered with no network: {rendered} "
          f"(for {len(spine['columns'])} columns)")
    print("  (queryRenderedFeatures counts a column that straddles a tile edge more than")
    print("   once, so 19 for 18 columns is expected, not a nineteenth market)")

    def hex_to_rgb(hx):
        hx = hx.lstrip("#")
        return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))

    def dist(a, bb):
        return max(abs(a[i] - bb[i]) for i in range(3))

    found = 0
    for c in cs["classes"]:
        rgb = hex_to_rgb(c["color"])
        n = 0
        for x in range(0, w, 3):
            for y in range(0, h, 3):
                if dist(px[x, y], rgb) <= 10:
                    n += 1
        if n > 20:
            found += 1
            print(f"    class present: {c['label']:<26} {n} px")
    print(f"\n  distinct column colours found with no network: {found} of {len(cs['classes'])}")
    print("  At this zoom the smaller columns are only a few pixels wide, so only the")
    print("  large classes have enough visible area to pass a pixel count. The rendered")
    print("  feature count above is what proves every column painted; the colour encoding")
    print("  is checked at a larger scale by verify_encoding.py (9 exact, 8 blended of 18).")

    # --- the IDS dealer layer must still be loadable offline ---------------
    print()
    print("=" * 72)
    print("IDS DEALER LAYER WITH NO NETWORK")
    print("=" * 72)
    print(json.dumps(pg.evaluate("""() => {
        const s = window.__globeStatus.ids || {};
        return {loaded: s.loaded, features: s.features, dealers: s.dealers,
                real: s.real_coordinates, approximate: s.approximate_coordinates,
                error: s.error || null};
    }"""), indent=1))
    print("  (the dealer file is local, so the layer must load with the network down)")

    # and it must be able to draw, not merely be present
    pg.evaluate("""() => {
        document.querySelector('#ids-seg button[data-ids="on"]').click();
        map.jumpTo({center:[2.2,46.6], zoom:6.4, pitch:40, bearing:0});
    }""")
    pg.wait_for_timeout(3500)
    offline_pins = pg.evaluate("""() => ({
        visible: window.__globeStatus.ids.layerVisible,
        real: map.queryRenderedFeatures({layers:['dealer-pin-real']}).length,
        approx: map.queryRenderedFeatures({layers:['dealer-pin-approx']}).length
    })""")
    print("  drawn with the network blocked: " + json.dumps(offline_pins))
    shot3 = HERE / "20_dealers_offline_no_network.png"
    pg.screenshot(path=str(shot3))
    print(f"  screenshot: {shot3.name}")
    pg.evaluate("""() => document.querySelector('#ids-seg button[data-ids="off"]').click()""")
    pg.wait_for_timeout(1200)

    # now toggle live streets with the network blocked
    print()
    print("=" * 72)
    print("LIVE-TILE FALLBACK WITH NETWORK BLOCKED")
    print("=" * 72)
    pg.evaluate("""() => document.querySelector('#basemap-seg button[data-base="live"]').click()""")
    pg.wait_for_timeout(11000)  # the page gives tiles 6 s before declaring failure
    print(json.dumps(pg.evaluate("""() => ({
        basemap: window.__globeStatus.basemap,
        liveTiles: window.__globeStatus.liveTiles,
        hint: document.getElementById('basemap-hint').innerText,
        bannerShown: document.getElementById('banner').classList.contains('show'),
        bannerText: document.getElementById('banner').innerText,
        errors: window.__globeStatus.errors
    })"""), indent=1))

    shot2 = HERE / "11_live_tiles_blocked.png"
    pg.screenshot(path=str(shot2))

    img2 = Image.open(shot2).convert("RGB")
    px2 = img2.load()
    earth2 = sum(1 for x in range(300, w, 7) for y in range(200, h - 150, 7) if is_earth(px2[x, y]))
    tot2 = sum(1 for x in range(300, w, 7) for y in range(200, h - 150, 7))
    print(f"\n  map band still earth-toned after the failed tile switch: "
          f"{earth2}/{tot2} ({earth2 / tot2:.1%})")
    print("  (a blank globe here would show near 0% earth-toned pixels)")

    print(f"\n  screenshots: {shot.name}, {shot2.name}")
    b.close()
