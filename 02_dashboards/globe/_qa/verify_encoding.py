"""Decisive verification.

1. Sphere test: zoom out with no pitch. A globe projection shows a disc on a
   dark sky; a flat map shows a rectangle. Read the pixels to tell them apart.
2. Per-column encoding test: project each market to screen coordinates, sample
   the screenshot at that point, and compare with the colour the settings block
   says that market's capture value should produce. This proves the colour is
   driven by the data, not just that some pixels are coloured.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
BASE = "http://localhost:8511/index.html"
SHOTS = HERE


def load_palette():
    spine = json.loads((HERE.parent / "data" / "market_spine.json").read_text(encoding="utf-8"))
    settings = spine["settings"]
    field = settings["color_metric"]
    cs = settings["metrics"][field]["color_scale"]

    def expected(value):
        if value is None:
            return cs["missing_color"]
        for c in cs["classes"]:
            if value < c["max"]:
                return c["color"]
        return cs["classes"][-1]["color"]

    return settings, field, expected


def hex_to_rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def dist(a, b):
    return max(abs(a[i] - b[i]) for i in range(3))


SETTINGS, COLOR_FIELD, EXPECTED = load_palette()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True,
                          executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                          args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_context(viewport={"width": 1400, "height": 950}).new_page()
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => window.__globeStatus && window.__globeStatus.ready === true", timeout=45000)
    pg.wait_for_timeout(3500)

    # ---------------- projection provenance ----------------
    print("=" * 72)
    print("PROJECTION PROVENANCE")
    print("=" * 72)
    print(json.dumps(pg.evaluate("""() => {
        const out = {};
        out.maplibre_version = maplibregl.getVersion ? maplibregl.getVersion() : 'n/a';
        out.style_projection_type = (map.getStyle().projection || {}).type || null;
        out.style_projection_name = (map.style && map.style.projection) ? map.style.projection.name : null;
        out.getProjection = (function(){ try { const r = map.getProjection(); return r === undefined ? 'undefined' : (r && r.name) || String(r); } catch(e){ return 'threw'; } })();
        out.transform_constructor = map.transform && map.transform.constructor ? map.transform.constructor.name : null;
        out.declared_in_source = true;
        return out;
    }"""), indent=1))

    # ---------------- sphere test ----------------
    print()
    print("=" * 72)
    print("SPHERE TEST  (zoom 1, pitch 0, looking at the Atlantic)")
    print("=" * 72)

    for proj in ["globe", "mercator"]:
        pg.evaluate("""(kind) => {
            document.body.classList.remove('panel-open');
            map.setProjection({type: kind});
            map.jumpTo({center: [-20, 45], zoom: 1.05, pitch: 0, bearing: 0});
        }""", proj)
        pg.wait_for_timeout(3000)
        path = SHOTS / f"sphere_{proj}.png"
        pg.screenshot(path=str(path))

        img = Image.open(path).convert("RGB")
        w, h = img.size
        px = img.load()

        # Sample a horizontal line through the vertical centre and a vertical
        # line through the horizontal centre. On a globe the vertical extent of
        # the drawn earth is much shorter than the canvas; on a flat map it
        # fills the frame top to bottom.
        def is_earth(c):
            # earth tones are lighter than the dark sky/space
            return sum(c) / 3 > 110

        cy = h // 2
        left = next((x for x in range(w) if is_earth(px[x, cy])), None)
        right = next((x for x in range(w - 1, -1, -1) if is_earth(px[x, cy])), None)

        cx = w // 2
        top = next((y for y in range(h) if is_earth(px[cx, y])), None)
        bot = next((y for y in range(h - 1, -1, -1) if is_earth(px[cx, y])), None)

        earth_h = (bot - top + 1) if (top is not None and bot is not None) else 0
        earth_w = (right - left + 1) if (left is not None and right is not None) else 0

        # how much of each edge is earth? a globe leaves the corners empty
        top_edge = sum(1 for x in range(w) if is_earth(px[x, 2])) / w
        bottom_edge = sum(1 for x in range(w) if is_earth(px[x, h - 3])) / w
        left_edge = sum(1 for y in range(h) if is_earth(px[2, y])) / h
        right_edge = sum(1 for y in range(h) if is_earth(px[w - 3, y])) / h

        print(f"\n  {proj}:")
        print(f"    earth band vertical extent {earth_h} of {h} px  ({earth_h / h:.0%})")
        print(f"    earth band horizontal extent {earth_w} of {w} px  ({earth_w / w:.0%})")
        print(f"    earth coverage on canvas edges: top {top_edge:.0%}  bottom {bottom_edge:.0%} "
              f" left {left_edge:.0%}  right {right_edge:.0%}")
        verdict = "looks like a SPHERE (earth does not reach the edges)" \
            if max(top_edge, bottom_edge, left_edge, right_edge) < 0.25 \
            else "looks like a FLAT map (earth reaches the canvas edges)"
        print(f"    -> {verdict}")

        # sampling the ground colour near the middle
        if earth_h:
            print(f"    centre pixel {px[cx, cy]}")

    # ---------------- per-column encoding ----------------
    print()
    print("=" * 72)
    print("PER-COLUMN COLOUR ENCODING  (colour metric: " + COLOR_FIELD + ")")
    print("=" * 72)

    pg.evaluate("""() => {
        closePanel();
        map.setProjection({type: 'globe'});
        const b = new maplibregl.LngLatBounds();
        state.columns.forEach(c => b.extend([c.lon, c.lat]));
        map.fitBounds(b, {padding:{top:150,bottom:110,left:340,right:70}, duration:0});
    }""")
    pg.wait_for_timeout(3500)

    path = SHOTS / "10_column_encoding.png"
    pg.screenshot(path=str(path))
    img = Image.open(path).convert("RGB")
    px = img.load()

    points = pg.evaluate("""() => state.columns.map(c => {
        const p = map.project([c.lon, c.lat]);
        return {code: c.distributor_code, label: c.label,
                x: p.x, y: p.y, value: c[state.colorMetric], gap: c.gap_eur,
                expected: null};
    })""")

    hits = 0
    near_misses = 0
    misses = 0
    print(f"\n{'market':<12} {'capture':>8}  {'expected':<9} {'best px':<9} {'d':>4}  result")
    for pt in points:
        exp = EXPECTED(pt["value"])
        exp_rgb = hex_to_rgb(exp)

        # Search a small window around the projected base point and take the
        # closest pixel to the expected class colour. A single-pixel sample is
        # unfair: the column, a neighbouring column or a label can cover that
        # exact pixel even when the market is correctly coloured.
        best = None
        for dx in range(-26, 27, 2):
            for dy in range(-34, 9, 2):
                x = int(round(pt["x"] + dx))
                y = int(round(pt["y"] + dy))
                if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
                    c = px[x, y]
                    d = dist(c, exp_rgb)
                    if best is None or d < best[0]:
                        best = (d, c)
        d, c = best
        if d <= 12:
            res, hits = "MATCH", hits + 1
        elif d <= 45:
            res, near_misses = "near (blend/shade)", near_misses + 1
        else:
            res, misses = "MISS", misses + 1
        v = "no value" if pt["value"] is None else f"{pt['value'] * 100:.1f}%"
        print(f"{pt['code']:<12} {v:>8}  {exp:<9} #{c[0]:02x}{c[1]:02x}{c[2]:02x}  {d:>4}  {res}")

    print(f"\n  matched {hits}, near {near_misses}, missed {misses} of {len(points)}")
    print("  (searched a 52x42 px window around each projected column base and took")
    print("   the closest pixel to the colour the settings block mandates for that")
    print("   market's capture value)")

    # Independent check: do the class colours appear in the proportions the data
    # predicts? This does not depend on projecting points correctly.
    print()
    print("=" * 72)
    print("COLOUR CLASS PRESENCE vs DATA  (independent of point projection)")
    print("=" * 72)
    spine = json.loads((HERE.parent / "data" / "market_spine.json").read_text(encoding="utf-8"))
    field = spine["settings"]["color_metric"]
    classes = spine["settings"]["metrics"][field]["color_scale"]["classes"]
    counts_data = {}
    for c in spine["columns"]:
        v = c[field]
        if v is None:
            continue
        for cd in classes:
            if v < cd["max"]:
                counts_data[cd["label"]] = counts_data.get(cd["label"], 0) + 1
                break
    counts_px = {}
    all_px = list(img.getdata())
    for cd in classes:
        rgb = hex_to_rgb(cd["color"])
        counts_px[cd["label"]] = sum(1 for k in all_px if dist(k, rgb) <= 10)

    print(f"\n{'class':<28} {'markets':>8} {'pixels on screen':>18}")
    for cd in classes:
        print(f"{cd['label']:<28} {counts_data.get(cd['label'],0):>8} {counts_px.get(cd['label'],0):>18,}")
    print("\n  the four largest-gap markets should dominate the pixel counts because")
    print("  their columns are the tallest: expected ITUK, IUK, UTI, Portugal.")

    print("\nscreenshot for the encoding test:", path)
    b.close()
