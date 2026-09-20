"""Objective layout checks on the rendered page.

Things I do not want to judge by eye:

1. Label overlap, at several view states. A dotted-border box that collides with
   another box has failed, regardless of how it looks in a screenshot.
2. Clipped text in the side panel, in the legend, in the controls and in the
   IDS dealer panel. An element whose scrollWidth exceeds its clientWidth is
   truncating its own text.
3. Panel geometry against the viewport.
4. The overlay geometry at the tightest window size Jerome uses: the title
   block, the controls and the legend must not collide with each other, and the
   collapsible controls and legend must actually shrink when folded.
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8511/index.html"

LABEL_BOXES_JS = """() => {
    const els = Array.from(document.querySelectorAll('.mlabel'));
    return els.filter(e => getComputedStyle(e).display !== 'none').map(e => {
        const r = e.getBoundingClientRect();
        return {t: e.innerText.replace(/\\n/g,' ').trim(), x: r.x, y: r.y, w: r.width, h: r.height};
    });
}"""

OVERLAP_JS = """(boxes) => {
    const hits = [];
    for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
            const a = boxes[i], b = boxes[j];
            const ix = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
            const iy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
            if (ix > 0.5 && iy > 0.5) {
                hits.push({a: a.t, b: b.t, overlapX: Math.round(ix), overlapY: Math.round(iy)});
            }
        }
    }
    return hits;
}"""

CLIP_JS = """() => {
    const bad = [];
    const walk = (root) => {
        root.querySelectorAll('*').forEach(el => {
            if (el.children.length === 0 && el.innerText && el.innerText.trim()) {
                if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
                    const cs = getComputedStyle(el);
                    if (cs.overflow !== 'visible' || cs.textOverflow === 'ellipsis') {
                        bad.push({tag: el.tagName, cls: el.className,
                                  text: el.innerText.slice(0,60),
                                  scrollW: el.scrollWidth, clientW: el.clientWidth});
                    }
                }
                if (el.scrollHeight > el.clientHeight + 2 && el.clientHeight > 0) {
                    bad.push({tag: el.tagName, cls: el.className,
                              text: el.innerText.slice(0,60),
                              axis: 'vertical',
                              scrollH: el.scrollHeight, clientH: el.clientHeight});
                }
            }
        });
    };
    walk(document.getElementById('panel-body'));
    walk(document.getElementById('legend'));
    walk(document.getElementById('titlebar'));
    walk(document.getElementById('controls'));
    return bad;
}"""

OVERLAY_BOXES = """() => {
    const ids = ['titlebar', 'controls', 'legend'];
    const out = {};
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        const r = el.getBoundingClientRect();
        out[id] = {x: r.x, y: r.y, w: r.width, h: r.height, right: r.right, bottom: r.bottom};
    });
    return out;
}"""

failures: list[str] = []


def check(label, ok, detail=""):
    mark = "ok  " if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def rect_overlaps(rects):
    keys = list(rects)
    hits = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = rects[keys[i]], rects[keys[j]]
            ix = min(a["right"], b["right"]) - max(a["x"], b["x"])
            iy = min(a["bottom"], b["bottom"]) - max(a["y"], b["y"])
            if ix > 0.5 and iy > 0.5:
                hits.append(f"{keys[i]} x {keys[j]} {round(ix)}x{round(iy)}")
    return hits


with sync_playwright() as p:
    b = p.chromium.launch(headless=True,
                          executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                          args=["--use-gl=angle", "--use-angle=swiftshader",
                                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_context(viewport={"width": 1600, "height": 1000}).new_page()
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => window.__globeStatus && window.__globeStatus.ready === true", timeout=45000)
    pg.wait_for_timeout(3500)

    print("=" * 72)
    print("LABEL OVERLAP, by view state")
    print("=" * 72)

    views = [
        ("default europe+israel", None),
        ("globe out to zoom 1.2", "() => map.jumpTo({center:[8,50],zoom:1.2,pitch:0,bearing:0})"),
        ("zoomed benelux zoom 6", "() => map.jumpTo({center:[4.5,50.6],zoom:6,pitch:50,bearing:0})"),
        ("zoomed israel zoom 6", "() => map.jumpTo({center:[33.4,31.05],zoom:6,pitch:50,bearing:0})"),
        ("wide europe zoom 4.5", "() => map.jumpTo({center:[12,50],zoom:4.5,pitch:55,bearing:0})"),
    ]

    total_overlaps = 0
    for name, js in views:
        if js:
            pg.evaluate(js)
        else:
            pg.evaluate("""() => {
                const b = new maplibregl.LngLatBounds();
                state.columns.forEach(c => b.extend([c.lon, c.lat]));
                map.fitBounds(b, {padding:{top:130,bottom:40,left:320,right:60}, duration:0});
            }""")
        pg.wait_for_timeout(2600)
        boxes = pg.evaluate(LABEL_BOXES_JS)
        hits = pg.evaluate(OVERLAP_JS, boxes)
        total_overlaps += len(hits)
        print(f"\n  {name}: {len(boxes)} labels visible, {len(hits)} overlapping pairs")
        for h_ in hits:
            print(f"    OVERLAP: '{h_['a']}' x '{h_['b']}'  ({h_['overlapX']}x{h_['overlapY']} px)")
        if boxes:
            print("    labels:", ", ".join(sorted(bx["t"] for bx in boxes)))

    print(f"\n  TOTAL overlapping label pairs across all views: {total_overlaps}")
    check("no overlapping label pairs at any view", total_overlaps == 0, f"{total_overlaps} found")

    # ---- with the dealer layer on, labels must still not collide ----------
    pg.evaluate("""() => {
        document.querySelector('#ids-seg button[data-ids="on"]').click();
        map.jumpTo({center:[2.2,46.6], zoom:5.6, pitch:40, bearing:0});
    }""")
    pg.wait_for_timeout(4000)
    dl_boxes = pg.evaluate(LABEL_BOXES_JS)
    dl_hits = pg.evaluate(OVERLAP_JS, dl_boxes)
    print(f"\n  dealer layer on, zoom 5.6 over France: {len(dl_boxes)} labels, "
          f"{len(dl_hits)} overlapping pairs")
    for h_ in dl_hits:
        print(f"    OVERLAP: '{h_['a']}' x '{h_['b']}'")
    check("cluster counts do not collide with any other label", len(dl_hits) == 0,
          f"{len(dl_hits)} found")

    print()
    print("=" * 72)
    print("CLIPPED / TRUNCATED TEXT")
    print("=" * 72)

    pg.evaluate("""() => {
        document.querySelector('#ids-seg button[data-ids="off"]').click();
        map.jumpTo({center:[8,50],zoom:3.2,pitch:42,bearing:0});
        const c = state.columns.find(x => x.distributor_code === 'IUK');
        openPanel(c);
    }""")
    pg.wait_for_timeout(1800)
    clip = pg.evaluate(CLIP_JS)
    print(f"\n  with a full market panel open: {len(clip)} clipped/truncated elements")
    for c in clip:
        print("   ", json.dumps(c))
    check("no clipped text in the market panel or the overlays", len(clip) == 0,
          f"{len(clip)} elements")

    pg.evaluate("""() => {
        const c = state.placeholders.find(x => x.distributor_code === 'PALESTINE');
        openPanel(c);
    }""")
    pg.wait_for_timeout(1500)
    clip2 = pg.evaluate(CLIP_JS)
    print(f"\n  with the no-column panel open: {len(clip2)} clipped/truncated elements")
    for c in clip2:
        print("   ", json.dumps(c))
    check("no clipped text in the no-column panel", len(clip2) == 0, f"{len(clip2)} elements")

    # ---- the IDS dealer panel --------------------------------------------
    pg.evaluate("""() => {
        document.querySelector('#ids-seg button[data-ids="on"]').click();
        map.jumpTo({center:[2.2,46.6], zoom:6.4, pitch:40, bearing:0});
    }""")
    pg.wait_for_timeout(4000)
    d = pg.evaluate("""() => {
        const f = map.queryRenderedFeatures({layers:['dealer-pin-real','dealer-pin-approx']})
            .find(x => x.properties.geo_real === 0) ||
            map.queryRenderedFeatures({layers:['dealer-pin-real','dealer-pin-approx']})[0];
        return f ? state.ids.byId[f.properties.dkey] : null;
    }""")
    pg.evaluate("(d) => openDealerPanel(d)", d)
    pg.wait_for_timeout(1800)
    clip3 = pg.evaluate(CLIP_JS)
    print(f"\n  with an IDS dealer panel open ({d['name']}): "
          f"{len(clip3)} clipped/truncated elements")
    for c in clip3:
        print("   ", json.dumps(c))
    check("no clipped text in the IDS dealer panel", len(clip3) == 0, f"{len(clip3)} elements")
    geo = pg.evaluate("""() => ({
        note: document.querySelector('.gapnote').innerText.slice(0, 200),
        sections: document.querySelectorAll('.secline').length,
        bands: document.querySelectorAll('.band-chip').length
    })""")
    print("    position note:", geo["note"][:130])
    check("the dealer panel states how the position was derived",
          "This position is approximate" in geo["note"] or "surveyed" in geo["note"],
          geo["note"][:80])
    check("the dealer panel shows all five sections", geo["sections"] == 5,
          f"{geo['sections']} section lines")

    # with the panel actually open, the overlays must move out of its way
    open_geom = pg.evaluate("""() => {
        const p = document.getElementById('panel').getBoundingClientRect();
        const f = document.getElementById('titlebar').getBoundingClientRect();
        const c = document.getElementById('controls').getBoundingClientRect();
        const l = document.getElementById('legend').getBoundingClientRect();
        return {
          panelX: Math.round(p.x), panelW: Math.round(p.width),
          titlebarClear: f.right <= p.x + 0.5,
          controlsClear: c.right <= p.x + 0.5,
          legendClear: l.right <= p.x + 0.5,
          controlsRight: Math.round(c.right)
        };
    }""")
    print("    with the panel open:", json.dumps(open_geom))
    check("the controls step aside for the open panel", open_geom["controlsClear"] is True,
          f"controls right {open_geom['controlsRight']}, panel starts {open_geom['panelX']}")
    check("the title block and the legend stay clear of the open panel",
          open_geom["titlebarClear"] is True and open_geom["legendClear"] is True)
    pg.evaluate("() => closePanel()")

    print()
    print("=" * 72)
    print("PANEL GEOMETRY vs VIEWPORT")
    print("=" * 72)
    pg.evaluate("""() => {
        const c = state.columns.find(x => x.distributor_code === 'IUK');
        openPanel(c);
    }""")
    pg.wait_for_timeout(1200)
    geom = pg.evaluate("""() => {
        const p = document.getElementById('panel').getBoundingClientRect();
        const f = document.querySelector('#titlebar').getBoundingClientRect();
        const l = document.getElementById('legend').getBoundingClientRect();
        const c = document.getElementById('controls').getBoundingClientRect();
        return {
          viewport: [window.innerWidth, window.innerHeight],
          panel: [Math.round(p.x), Math.round(p.y), Math.round(p.width), Math.round(p.height)],
          panelInsideViewport: p.x >= 0 && p.right <= window.innerWidth + 0.5,
          titlebarLeft: Math.round(f.x),
          controlsRight: Math.round(c.right),
          legendBottom: Math.round(l.bottom),
          titlebarClearOfPanel: f.right <= p.x,
          controlsClearOfPanel: c.right <= p.x
        };
    }""")
    print(json.dumps(geom, indent=1))
    check("the panel is fully inside the viewport", geom["panelInsideViewport"] is True)
    check("the title block and the controls stay clear of the open panel",
          geom["titlebarClearOfPanel"] and geom["controlsClearOfPanel"],
          f"titlebarClear={geom['titlebarClearOfPanel']} controlsClear={geom['controlsClearOfPanel']}")
    pg.evaluate("() => closePanel()")
    pg.wait_for_timeout(600)

    print()
    print("=" * 72)
    print("CONTENT PRESENCE CHECKS")
    print("=" * 72)
    print(json.dumps(pg.evaluate("""() => {
        const c = state.columns.find(x => x.distributor_code === 'IUK');
        openPanel(c);
        const body = document.getElementById('panel-body').innerText;
        return {
          notYetRows: document.querySelectorAll('.ny-row').length,
          notYetMentions: ['Warranty parts','Fleet size workbook','Price revision',
                           'Live tenders','Sales to dealer']
                          .filter(t => body.includes(t)),
          glossaryTerms: document.querySelectorAll('#glossary dt').length,
          legendSwatches: document.querySelectorAll('#legend .swatch').length,
          heightHint: document.getElementById('height-hint').innerText.slice(0,90),
          colorHint: document.getElementById('color-hint').innerText.slice(0,90),
          hoverExplanations: document.querySelectorAll('.hx').length
        };
    }"""), indent=1))
    pg.evaluate("() => closePanel()")

    print()
    print("=" * 72)
    print("OVERLAY GEOMETRY AT THE TIGHTEST WINDOW (1440x900)")
    print("=" * 72)
    pg.set_viewport_size({"width": 1440, "height": 900})
    # Reload so this measures the state the page opens in, not whatever the
    # preceding checks left the folds in.
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => window.__globeStatus && window.__globeStatus.ready === true", timeout=45000)
    pg.wait_for_timeout(3200)
    open_boxes = pg.evaluate(OVERLAY_BOXES)
    open_hits = rect_overlaps(open_boxes)
    for k, r in open_boxes.items():
        print(f"    {k:<10} x{r['x']:>5.0f} y{r['y']:>5.0f}  {r['w']:>4.0f}x{r['h']:<4.0f} "
              f"right{r['right']:>5.0f} bottom{r['bottom']:>5.0f}")
    print(f"\n    controls height with everything folded: {open_boxes['controls']['h']:.0f} px")
    print(f"    overlay-vs-overlay overlaps: {len(open_hits)} {open_hits if open_hits else ''}")
    check("no overlay overlaps another at 1440x900", len(open_hits) == 0, str(open_hits))
    # The real question is crowding, which is area rather than height: a narrow
    # strip down the right edge is not crowded, but a wide one would be.
    area_pct = pg.evaluate("""() => {
        const ids = ['titlebar', 'controls', 'legend'];
        let sum = 0;
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const r = el.getBoundingClientRect();
            sum += r.width * r.height;
        });
        return Math.round(sum / (window.innerWidth * window.innerHeight) * 1000) / 10;
    }""")
    print(f"\n    the three floating overlays cover {area_pct}% of a 1440x900 window")
    check("the steady-state overlays cover under 15% of the window", area_pct < 15,
          f"{area_pct}%")
    check("the title block and the legend do not meet in the left column",
          open_boxes["legend"]["y"] > open_boxes["titlebar"]["bottom"] - 1,
          f"legend top {open_boxes['legend']['y']:.0f}, title block bottom "
          f"{open_boxes['titlebar']['bottom']:.0f}")
    check("the legend does not reach the title block at 1440x900",
          open_boxes["legend"]["y"] > open_boxes["titlebar"]["bottom"] - 1,
          f"legend top {open_boxes['legend']['y']:.0f}, title block bottom "
          f"{open_boxes['titlebar']['bottom']:.0f}")
    check("the folded legend takes little room",
          open_boxes["legend"]["h"] < 70, f"{open_boxes['legend']['h']:.0f} px")

    # unfolding every control must not push it off the bottom of the screen
    pg.evaluate("""() => {
        document.querySelectorAll('#controls .ctl-head').forEach(h => {
            const ctl = h.closest('.ctl');
            if (ctl.classList.contains('is-collapsed')) h.click();
        });
    }""")
    pg.wait_for_timeout(1200)
    unfolded = pg.evaluate(OVERLAY_BOXES)
    print(f"\n    controls height with everything unfolded: {unfolded['controls']['h']:.0f} px "
          f"(bottom edge {unfolded['controls']['bottom']:.0f} of 900)")
    # The controls scroll rather than extend, so the box must stay inside the
    # window and the scrollbar must be doing the overflow work.
    scrolls = pg.evaluate("""() => {
        const c = document.getElementById('controls');
        return {scrollH: c.scrollHeight, clientH: c.clientHeight,
                overflows: c.scrollHeight > c.clientHeight + 1};
    }""")
    print(f"    controls content {scrolls['scrollH']} px in a {scrolls['clientH']} px box "
          f"-> {'scrolls' if scrolls['overflows'] else 'fits without scrolling'}")
    check("with every control unfolded nothing runs off the bottom of the window",
          unfolded["controls"]["bottom"] <= 900, f"bottom {unfolded['controls']['bottom']:.0f}")
    pg.evaluate("() => { document.getElementById('controls').scrollTop = 0; }")
    check("nothing goes off the left or right edge", 
          all(r["x"] >= 0 and r["right"] <= 1440.5 for r in unfolded.values()),
          str({k: (r["x"], r["right"]) for k, r in unfolded.items()}))
    pg.screenshot(path=str(Path(__file__).resolve().parent / "14_layout_1440x900_all_open.png"))

    # folding must actually reduce the footprint
    pg.evaluate("""() => {
        document.querySelectorAll('#controls .ctl-head').forEach(h => {
            const ctl = h.closest('.ctl');
            if (!ctl.classList.contains('is-collapsed')) h.click();
        });
        const lh = document.getElementById('legend-head');
        if (!document.getElementById('legend').classList.contains('is-collapsed')) lh.click();
    }""")
    pg.wait_for_timeout(1200)
    folded = pg.evaluate(OVERLAY_BOXES)
    print(f"\n    controls folded: {folded['controls']['h']:.0f} px   "
          f"legend folded: {folded['legend']['h']:.0f} px")
    check("folding the controls reduces their footprint",
          folded["controls"]["h"] < unfolded["controls"]["h"] - 100,
          f"{unfolded['controls']['h']:.0f} -> {folded['controls']['h']:.0f} px")
    check("folding the legend reduces its footprint",
          folded["legend"]["h"] < 100, f"{folded['legend']['h']:.0f} px")
    pg.screenshot(path=str(Path(__file__).resolve().parent / "15_layout_1440x900_folded.png"))

    # ---- turning the dealer layer on must bring its key into view --------
    pg.evaluate("""() => {
        document.querySelector('#ids-seg button[data-ids="on"]').click();
        map.jumpTo({center:[2.2,46.6], zoom:6.4, pitch:40, bearing:0});
    }""")
    pg.wait_for_timeout(3800)
    key_state = pg.evaluate("""() => {
        const key = document.getElementById('ids-key');
        const kr = key.getBoundingClientRect();
        const last = key.querySelector('.keynote');
        const lr2 = last ? last.getBoundingClientRect() : null;
        const ctrls = document.getElementById('controls').getBoundingClientRect();
        const legend = document.getElementById('legend').getBoundingClientRect();
        const ov = (a, b) => {
            const ix = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            const iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            return ix > 0.5 && iy > 0.5 ? Math.round(ix) + 'x' + Math.round(iy) : 'none';
        };
        return {
            shown: key.classList.contains('show'),
            ariaHidden: key.getAttribute('aria-hidden'),
            keyHeight: Math.round(kr.height),
            keyTop: Math.round(kr.top),
            keyBottom: Math.round(kr.bottom),
            lastRowBottom: lr2 ? Math.round(lr2.bottom) : null,
            viewportH: window.innerHeight,
            vsControls: ov(kr, ctrls),
            vsLegend: ov(kr, legend),
            scrolls: key.scrollHeight > key.clientHeight + 1,
            scrollH: key.scrollHeight, clientH: key.clientHeight
        };
    }""")
    print(f"\n  with the dealer layer on: key shown={key_state['shown']}, "
          f"{key_state['keyHeight']} px tall, y {key_state['keyTop']}..{key_state['keyBottom']}")
    print(f"    key vs controls: {key_state['vsControls']}   key vs market legend: {key_state['vsLegend']}")
    print(f"    key content {key_state['scrollH']} px in a {key_state['clientH']} px box "
          f"-> {'scrolls' if key_state['scrolls'] else 'fits without scrolling'}")
    check("turning the dealer layer on shows the IDS key",
          key_state["shown"] is True and key_state["ariaHidden"] == "false")
    check("the IDS key has real height", key_state["keyHeight"] > 150,
          f"{key_state['keyHeight']} px")
    check("the whole key is reachable, not cut off",
          key_state["lastRowBottom"] is not None and
          key_state["lastRowBottom"] <= key_state["keyBottom"] + 0.5,
          f"last key row bottom {key_state['lastRowBottom']}, key bottom {key_state['keyBottom']}")
    check("the IDS key stays inside the window",
          key_state["keyBottom"] <= key_state["viewportH"] + 0.5 and key_state["keyTop"] >= 0,
          f"{key_state['keyTop']}..{key_state['keyBottom']} of {key_state['viewportH']}")
    check("the IDS key does not sit on the controls", key_state["vsControls"] == "none",
          str(key_state["vsControls"]))
    check("the IDS key does not sit on the market legend", key_state["vsLegend"] == "none",
          str(key_state["vsLegend"]))
    pg.screenshot(path=str(Path(__file__).resolve().parent / "21_dealers_key_1440x900.png"))

    # ---- and turning it back off must take the key away ------------------
    pg.evaluate("""() => document.querySelector('#ids-seg button[data-ids="off"]').click()""")
    pg.wait_for_timeout(1200)
    off_state = pg.evaluate("""() => ({
        shown: document.getElementById('ids-key').classList.contains('show'),
        ariaHidden: document.getElementById('ids-key').getAttribute('aria-hidden'),
        visible: window.__globeStatus.ids.layerVisible
    })""")
    print(f"  dealer layer off again: key shown={off_state['shown']}, "
          f"layer visible={off_state['visible']}")
    check("turning the dealer layer off hides the key again",
          off_state["shown"] is False and off_state["visible"] is False,
          json.dumps(off_state))

    b.close()

print()
print("=" * 72)
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:")
    for f in failures:
        print("  - " + f)
    raise SystemExit(1)
print("all layout checks passed")
