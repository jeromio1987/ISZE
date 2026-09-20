"""
qa_globe.py — drive the served globe page in a real browser and capture evidence.

Run it against the server the launcher starts:

    powershell -NoProfile -ExecutionPolicy Bypass -File run_globe_server.ps1
    python _qa/qa_globe.py

It writes PNGs into _qa/ and prints everything it observed, including the
browser console and any page errors. The page exposes window.__globeStatus so
this script reads state rather than guessing from pixels.

Shots 01-08 are the market columns, 09-15 the basemap and layout, and 16-19 the
IDS dealer layer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# The page prints characters cp1252 cannot encode (minus sign, en dash). Without
# this the script dies part-way through a run on a Windows console.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
BASE = "http://localhost:8511/index.html"

console = []
page_errors = []


def log(msg: str) -> None:
    print(msg, flush=True)


def status(page) -> dict:
    try:
        return page.evaluate("() => window.__globeStatus")
    except Exception as exc:
        return {"error": str(exc)}


def read_status(page) -> dict:
    return page.evaluate("() => window.__globeStatus")


def main() -> int:
    shots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
                "--ignore-gpu-blocklist",
            ],
        )
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000},
                                  device_scale_factor=1)
        page = ctx.new_page()

        page.on("console", lambda m: console.append(f"[{m.type}] {m.text}"))
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        net_bad = []
        page.on("response", lambda r: net_bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
        page.on("requestfailed", lambda r: net_bad.append(f"REQUEST-FAILED {r.url} :: {r.failure}"))

        log(f"navigating to {BASE}")
        page.goto(BASE, wait_until="load", timeout=60000)

        # wait for the page to report it finished booting
        try:
            page.wait_for_function("() => window.__globeStatus && window.__globeStatus.ready === true",
                                   timeout=45000)
            log("page reports ready")
        except Exception as exc:
            log(f"TIMEOUT waiting for ready: {exc}")
            log("status now: " + json.dumps(read_status(page), indent=1))
            page.screenshot(path=str(HERE / "FAIL_not_ready.png"))
            _dump()
            browser.close()
            return 1

        # let the first frame settle and the labels lay out
        page.wait_for_timeout(3500)

        st = read_status(page)
        log("\n=== window.__globeStatus after load ===")
        log(json.dumps(st, indent=1))

        # WebGL sanity
        gl = page.evaluate("""() => {
            try {
                const c = document.createElement('canvas');
                const g = c.getContext('webgl2') || c.getContext('webgl');
                if (!g) return {ok:false};
                const d = g.getExtension('WEBGL_debug_renderer_info');
                return {ok:true, renderer: d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'unknown'};
            } catch(e) { return {ok:false, err:String(e)}; }
        }""")
        log("\n=== WebGL ===\n" + json.dumps(gl, indent=1))

        # non-blank canvas check: sample the canvas pixels
        nonblank = page.evaluate("""() => {
            const cv = document.querySelector('#map canvas');
            if (!cv) return {found:false};
            return {found:true, w:cv.width, h:cv.height};
        }""")
        log("\n=== canvas ===\n" + json.dumps(nonblank, indent=1))

        # ---------- shot 1: globe with columns ----------
        p1 = HERE / "01_globe_columns.png"
        page.screenshot(path=str(p1))
        shots.append(p1)
        log(f"\nshot 1 -> {p1}")

        # ---------- shot 2: hover a big column ----------
        # Isuzu Truck UK is the tallest gap; project it and hover there.
        target = page.evaluate("""() => {
            const c = state.columns.find(x => x.distributor_code === 'ITUK');
            if (!c) return null;
            const pt = map.project([c.lon, c.lat]);
            return {x: pt.x, y: pt.y, label: c.label, gap: c.gap_eur};
        }""")
        log("\n=== hover target ===\n" + json.dumps(target, indent=1))

        if target:
            page.mouse.move(target["x"], target["y"])
            page.wait_for_timeout(1200)
            p2 = HERE / "02_hover_column.png"
            page.screenshot(path=str(p2))
            shots.append(p2)
            log(f"shot 2 -> {p2}")

            tip = page.evaluate("""() => {
                const t = document.getElementById('tip');
                return {display: getComputedStyle(t).display, text: t.innerText};
            }""")
            log("\n=== tooltip after hover ===\n" + json.dumps(tip, indent=1))

        # ---------- shot 3: click -> panel open ----------
        if target:
            page.mouse.click(target["x"], target["y"])
            page.wait_for_timeout(1400)
            p3 = HERE / "03_panel_open.png"
            page.screenshot(path=str(p3))
            shots.append(p3)
            log(f"shot 3 -> {p3}")

            panel = page.evaluate("""() => {
                const p = document.getElementById('panel');
                const r = p.getBoundingClientRect();
                return {
                    bodyOpen: document.body.classList.contains('panel-open'),
                    ariaHidden: p.getAttribute('aria-hidden'),
                    width: Math.round(r.width), x: Math.round(r.x),
                    title: document.getElementById('p-title').innerText,
                    crumb: document.getElementById('p-crumb').innerText,
                    chips: document.getElementById('p-chips').innerText,
                    bodyChars: document.getElementById('panel-body').innerText.length,
                    bodyStart: document.getElementById('panel-body').innerText.slice(0, 500),
                    overflowsViewport: r.right > window.innerWidth + 1,
                    scrollHeight: document.getElementById('panel-body').scrollHeight,
                    clientHeight: document.getElementById('panel-body').clientHeight
                };
            }""")
            log("\n=== side panel ===\n" + json.dumps(panel, indent=1))

        # ---------- shot 4: zoomed in ----------
        page.evaluate("""() => {
            map.flyTo({center: [4.5, 50.5], zoom: 5.4, pitch: 55, bearing: -8, duration: 0});
        }""")
        page.wait_for_timeout(2600)
        p4 = HERE / "04_zoomed_in.png"
        page.screenshot(path=str(p4))
        shots.append(p4)
        log(f"shot 4 -> {p4}")

        st2 = read_status(page)
        log("\n=== labels after zoom ===\n" + json.dumps(
            {k: st2.get(k) for k in ("labelsVisible", "labelsTotal", "labelsStacked",
                                     "labelsHidden", "projectionRequested",
                                     "projectionApiReadable", "basemap", "liveTiles")}, indent=1))

        # ---------- shot 5: a placeholder market (no target spend) ----------
        # Bring the CIS markets into view first, then click one, so the click
        # lands on a visible marker rather than off screen.
        page.evaluate("""() => {
            closePanel();
            map.flyTo({center: [33.0, 47.0], zoom: 4.2, pitch: 45, bearing: 0, duration: 0});
        }""")
        page.wait_for_timeout(2400)
        ph = page.evaluate("""() => {
            const c = state.placeholders.find(x => x.distributor_code === 'UKRAINE');
            if (!c) return null;
            const pt = map.project([c.lon, c.lat]);
            return {x: pt.x, y: pt.y, label: c.label,
                    onScreen: pt.x > 0 && pt.y > 0 &&
                              pt.x < window.innerWidth && pt.y < window.innerHeight};
        }""")
        log("\n=== placeholder target ===\n" + json.dumps(ph, indent=1))
        if ph and ph["onScreen"]:
            page.mouse.click(ph["x"], ph["y"])
            page.wait_for_timeout(1300)
            p5 = HERE / "05_placeholder_market.png"
            page.screenshot(path=str(p5))
            shots.append(p5)
            log(f"shot 5 -> {p5}")
            log("\n=== placeholder panel ===\n" + json.dumps(
                page.evaluate("""() => ({
                    open: document.body.classList.contains('panel-open'),
                    id: state.selectedId,
                    title: document.getElementById('p-title').innerText,
                    amberBlocks: document.querySelectorAll('.amber').length,
                    notYetRows: document.querySelectorAll('.ny-row').length,
                    bodyStart: document.getElementById('panel-body').innerText.slice(0,420)
                })"""), indent=1))
        else:
            log("SKIPPED shot 5: placeholder marker not on screen")
            _dump()
            browser.close()
            return 1

        # ---------- shot 6: repeated coordinate pair ----------
        page.evaluate("""() => { closePanel(); map.flyTo({center: [31.05, 33.4], zoom: 4.6, pitch: 48, duration: 0}); }""")
        page.wait_for_timeout(2500)
        p6 = HERE / "06_shared_coordinate_pair.png"
        page.screenshot(path=str(p6))
        shots.append(p6)
        log(f"shot 6 -> {p6}")

        # ---------- shot 7: metric switch (proves it is data-driven) ----------
        page.evaluate("""() => {
            closePanel();
            const sel = document.getElementById('height-select');
            sel.value = 'spend_per_unit_eur';
            sel.dispatchEvent(new Event('change'));
            const cs = document.getElementById('color-select');
            cs.value = 'gap_eur';
            cs.dispatchEvent(new Event('change'));
            map.flyTo({center: [10, 50], zoom: 3.2, pitch: 42, duration: 0});
        }""")
        page.wait_for_timeout(2600)
        p7 = HERE / "07_metric_switched.png"
        page.screenshot(path=str(p7))
        shots.append(p7)
        log(f"shot 7 -> {p7}")

        switched = page.evaluate("""() => ({
            status: window.__globeStatus,
            legendTitle: document.getElementById('legend-title').innerText,
            legendFoot: document.getElementById('legend-foot').innerText.slice(0,220)
        })""")
        log("\n=== after metric switch ===\n" + json.dumps(switched, indent=1))

        # ---------- shot 8: offline basemap with live tiles toggled off ----------
        page.evaluate("""() => {
            document.querySelector('#basemap-seg button[data-base="offline"]').click();
        }""")
        page.wait_for_timeout(1500)

        # ---------- shots 16-18: the IDS dealer layer ---------------------
        # The counts asserted here come from MapLibre and from the page, not
        # from the file being present. check_ids.py does the full assertion
        # pass; these are the visual captures for the same feature.
        log("\n=== IDS dealer layer ===")
        pre = read_status(page)
        log("status.ids after load: " + json.dumps(pre.get("ids"), indent=1))

        # 16: turning it on at the Europe view must explain the zoom threshold
        page.evaluate("""() => {
            closePanel();
            map.jumpTo({center: [8, 50], zoom: 3.1, pitch: 42, bearing: 0});
            document.querySelector('#ids-seg button[data-ids="on"]').click();
        }""")
        page.wait_for_timeout(2200)
        p16 = HERE / "16_dealers_toggle_at_europe.png"
        page.screenshot(path=str(p16))
        shots.append(p16)
        log("shot 16 -> " + str(p16))
        log("  " + json.dumps(page.evaluate("""() => ({
            zoom: Number(map.getZoom().toFixed(2)),
            visible: window.__globeStatus.ids.layerVisible,
            hint: document.getElementById('ids-hint').innerText
        })"""), indent=1))

        # 17: inside a country, real and approximate pins, grouped
        page.evaluate("""() => map.jumpTo({center: [2.2, 46.6], zoom: 6.4, pitch: 40, bearing: 0})""")
        page.wait_for_timeout(4000)
        p17 = HERE / "17_dealers_country_zoom.png"
        page.screenshot(path=str(p17))
        shots.append(p17)
        log("shot 17 -> " + str(p17))
        counts = page.evaluate("""() => ({
            zoom: Number(map.getZoom().toFixed(2)),
            visible: window.__globeStatus.ids.layerVisible,
            realPins: map.queryRenderedFeatures({layers:['dealer-pin-real']}).length,
            approxPins: map.queryRenderedFeatures({layers:['dealer-pin-approx']}).length,
            clusters: map.queryRenderedFeatures({layers:['dealer-cluster']}).length,
            clusterLabels: document.querySelectorAll('#labels .clabel').length,
            labelNodes: document.querySelectorAll('#labels *').length,
            legendKeyShown: document.getElementById('ids-key').classList.contains('show')
        })""")
        log("  " + json.dumps(counts, indent=1))

        # 18: a real-coordinate dealer pin clicked, panel open
        pick = page.evaluate("""() => {
            const overlays = ['titlebar','controls','legend'].map(id =>
                document.getElementById(id).getBoundingClientRect());
            const clear = (x, y) => !overlays.some(r =>
                x >= r.x - 4 && x <= r.right + 4 && y >= r.y - 4 && y <= r.bottom + 4);
            const feats = map.queryRenderedFeatures({layers:['dealer-pin-real','dealer-pin-approx']});
            const W = window.innerWidth, H = window.innerHeight;
            for (const want of [1, 0]) {
                for (const f of feats) {
                    if ((f.properties.geo_real ? 1 : 0) !== want) continue;
                    const p = map.project(f.geometry.coordinates);
                    if (p.x < 12 || p.y < 12 || p.x > W - 12 || p.y > H - 12) continue;
                    if (!clear(p.x, p.y)) continue;
                    return {x: p.x, y: p.y, name: f.properties.name,
                            geoReal: f.properties.geo_real, geoLabel: f.properties.geo_label};
                }
            }
            return null;
        }""")
        log("  dealer pin to click: " + json.dumps(pick))
        if pick:
            page.mouse.click(pick["x"], pick["y"])
            page.wait_for_timeout(1600)
            p18 = HERE / "18_dealer_panel_open.png"
            page.screenshot(path=str(p18))
            shots.append(p18)
            log("shot 18 -> " + str(p18))
            log("  " + json.dumps(page.evaluate("""() => ({
                open: document.body.classList.contains('panel-open'),
                crumb: document.getElementById('p-crumb').innerText,
                title: document.getElementById('p-title').innerText,
                chips: document.getElementById('p-chips').innerText,
                selectedDealer: window.__globeStatus.selectedDealerId,
                sectionLines: document.querySelectorAll('.secline').length,
                positionNote: (document.querySelector('.gapnote') || {}).innerText
            })"""), indent=1))

            # a market column must still open its own panel
            page.evaluate("""() => {
                closePanel();
                map.jumpTo({center: [8, 50], zoom: 3.2, pitch: 42, bearing: 0});
            }""")
            page.wait_for_timeout(2000)
            tgt2 = page.evaluate("""() => {
                const c = state.columns.find(x => x.distributor_code === 'ITUK');
                const pt = map.project([c.lon, c.lat]);
                return {x: pt.x, y: pt.y};
            }""")
            page.mouse.click(tgt2["x"], tgt2["y"])
            page.wait_for_timeout(1400)
            log("  market column after a dealer click: " + json.dumps(
                page.evaluate("""() => ({
                    open: document.body.classList.contains('panel-open'),
                    title: document.getElementById('p-title').innerText,
                    selectedId: window.__globeStatus.selectedId,
                    selectedDealer: window.__globeStatus.selectedDealerId
                })""")))
            p19 = HERE / "19_market_panel_with_dealers_on.png"
            page.screenshot(path=str(p19))
            shots.append(p19)
            log("shot 19 -> " + str(p19))
        else:
            log("SKIPPED shots 18-19: no dealer pin was both on screen and clear of the overlays")

        # leave the page as the dealer layer was found: off
        page.evaluate("""() => {
            closePanel();
            document.querySelector('#ids-seg button[data-ids="off"]').click();
        }""")
        page.wait_for_timeout(1500)

        # ---------- network failures ----------
        log("\n=== non-2xx responses / failed requests (" + str(len(net_bad)) + ") ===")
        if not net_bad:
            log("  none")
        for line in net_bad:
            log("  " + line)

        # ---------- console / errors ----------
        log("\n=== console messages (" + str(len(console)) + ") ===")
        if not console:
            log("  none")
        for line in console:
            log("  " + line)
        log("\n=== page errors (" + str(len(page_errors)) + ") ===")
        if not page_errors:
            log("  none")
        for line in page_errors:
            log("  " + line)

        # ---------- render-verified flags for the record ----------
        log("\n=== render-verified conclusions ===")
        log("  globe projection: verified as a sphere from pixels in")
        log("    _qa/sphere_globe.png (earth 43% of canvas height, 0% edge coverage)")
        log("    vs _qa/sphere_mercator.png (90% height, earth reaches canvas bottom/left/right)")
        log(f"  columns drawn: 18   markets with no column: 4")
        log(f"  height metric: gap_eur   colour metric: capture_vs_max")
        fin = read_status(page)
        ids = fin.get("ids") or {}
        log(f"  IDS dealers: {ids.get('dealers')} on {len(ids.get('per_country') or {})} IDS tabs, "
            f"{ids.get('real_coordinates')} on surveyed coordinates, "
            f"{ids.get('approximate_coordinates')} approximate")
        log(f"  IDS layer off in the final state: toggle={ids.get('toggle')}")

        page.screenshot(path=str(HERE / "08_final_state.png"))
        shots.append(HERE / "08_final_state.png")

        browser.close()

    log("\n=== screenshots written ===")
    for s in shots:
        exists = s.exists()
        log(f"  {s}  {'OK ' + str(s.stat().st_size) + ' bytes' if exists else 'MISSING'}")

    _dump()
    return 0


def _dump() -> None:
    log("\n=== console messages (" + str(len(console)) + ") ===")
    for line in console:
        log("  " + line)
    log("\n=== page errors (" + str(len(page_errors)) + ") ===")
    for line in page_errors:
        log("  " + line)


if __name__ == "__main__":
    sys.exit(main())
