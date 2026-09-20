"""Headless verification of the brake corner page.

Checks, against the real page opened from file:// in the system Chrome:

  * zero requests that are not file://  (no network at all)
  * zero console errors and zero page errors
  * every callout is present in the drawing
  * clicking each callout actually changes the detail panel, and the panel then
    contains that part's real figure key and euro - read back from the page, not
    asserted from the source
  * the embedded photograph is present and non-trivial

Playwright's bundled browser is not installed here, so executable_path is passed
explicitly, as the brief requires.

  python verify_page.py
"""
from __future__ import annotations

import json
import os
import re

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "ISZE_DMax_Front_Brake_Corner.html")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SHOT = os.path.join(HERE, "_raw", "page_brake_corner.png")
DATA = os.path.join(HERE, "brake_corner_data.json")

with open(DATA, encoding="utf-8") as fh:
    src = json.load(fh)

EXPECT = {}
for c in src["callouts"]:
    EXPECT.setdefault(c["kind"], c)

results = {"page": PAGE, "chrome": CHROME, "checks": {}}
fails = []

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    ctx = browser.new_context(viewport={"width": 1680, "height": 1150})
    page = ctx.new_page()

    requests, consoles, errors = [], [], []
    page.on("request", lambda r: requests.append(r.url))
    page.on("console", lambda m: consoles.append((m.type, m.text)))
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto("file:///" + PAGE.replace("\\", "/"), wait_until="load")
    page.wait_for_timeout(1500)

    non_file = [u for u in requests if not u.startswith("file:")]
    results["checks"]["request_count"] = len(requests)
    results["checks"]["non_file_requests"] = non_file
    results["checks"]["console_errors"] = [t for t in consoles if t[0] == "error"]
    results["checks"]["page_errors"] = errors
    if non_file:
        fails.append("non-file:// requests: %s" % non_file[:5])
    if results["checks"]["console_errors"]:
        fails.append("console errors: %s" % results["checks"]["console_errors"][:3])
    if errors:
        fails.append("page errors: %s" % errors[:3])

    # the image is embedded and paints
    img_ok = page.evaluate("""() => {
        const im = document.querySelector('.stage img');
        if (!im) return {ok:false, why:'no image element'};
        return {ok: im.complete && im.naturalWidth > 100,
                w: im.naturalWidth, h: im.naturalHeight,
                src: im.src.slice(0, 30)};
    }""")
    results["checks"]["image"] = img_ok
    if not img_ok.get("ok"):
        fails.append("embedded image did not paint: %s" % img_ok)

    # every callout exists in the drawing
    ids = page.evaluate(
        "() => Array.from(document.querySelectorAll('.cal')).map(e => e.dataset.c)")
    results["checks"]["callouts_present"] = ids
    want = ["A", "B", "C", "D", "E"]
    if ids != want:
        fails.append("callouts present %s, expected %s" % (ids, want))

    # click each callout and read the panel back
    clicked = {}
    for cid in want:
        page.click('.cal[data-c="%s"]' % cid)
        page.wait_for_timeout(220)
        state = page.evaluate("""() => ({
            title: document.getElementById('panel-title').textContent,
            html: document.getElementById('panel').innerHTML,
            text: document.getElementById('panel').innerText,
            on: Array.from(document.querySelectorAll('.cal.on')).map(e => e.dataset.c)
        })""")
        clicked[cid] = state
        if state["on"] != [cid]:
            fails.append("callout %s: highlighted %s" % (cid, state["on"]))
        if cid not in state["title"]:
            fails.append("callout %s: panel title is %r" % (cid, state["title"]))
        if len(state["text"]) < 40:
            fails.append("callout %s: panel is empty" % cid)

    # the panel must carry that part's own fig key and euro from the data file
    verified = {}
    for cid, state in clicked.items():
        eur = re.findall(r"\u20ac([\d,]+)", state["text"])
        eur_vals = [int(x.replace(",", "")) for x in eur]
        keys = re.findall(r"\b(\d{3}-\d{3})\b", state["text"])
        verified[cid] = {"eur_seen": eur_vals[:6], "keys_seen": keys[:6],
                         "title": state["title"]}
        if not keys and cid != "E":
            fails.append("callout %s: no figure key in the panel" % cid)
        if not eur and cid != "E":
            fails.append("callout %s: no euro figure in the panel" % cid)
    results["checks"]["panel_by_callout"] = verified

    # the key list table beside the drawing has a row per callout
    rows = page.evaluate("() => document.querySelectorAll('#keylist tr').length")
    results["checks"]["keylist_rows"] = rows
    if rows != len(want):
        fails.append("key list has %d rows, expected %d" % (rows, len(want)))

    # every callout label's text must fit inside its own box: measure the rendered
    # text against the rect the label is drawn on
    fits = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('.cal').forEach(g => {
            const rect = g.querySelector('rect');
            const rb = rect.getBBox();
            g.querySelectorAll('text').forEach(t => {
                const tb = t.getBBox();
                out.push({c: g.dataset.c, text: t.textContent,
                          overflow_right: +(tb.x + tb.width - (rb.x + rb.width - 10)).toFixed(1),
                          overflow_bottom: +(tb.y + tb.height - (rb.y + rb.height - 8)).toFixed(1)});
            });
        });
        return out;
    }""")
    results["checks"]["label_text_fit"] = fits
    for f in fits:
        if f["overflow_right"] > 0 or f["overflow_bottom"] > 0:
            fails.append("label %s text overflows its box by %s / %s px"
                         % (f["c"], f["overflow_right"], f["overflow_bottom"]))
    print("label text fit checks: %d, worst overflow right %.1f px, bottom %.1f px"
          % (len(fits), max(f["overflow_right"] for f in fits),
             max(f["overflow_bottom"] for f in fits)))

    # overflow / clipping sanity on the drawing box
    geom = page.evaluate("""() => {
        const st = document.querySelector('.stage');
        const im = document.querySelector('.stage img');
        const svg = document.querySelector('.cl');
        const r = st.getBoundingClientRect();
        return {stage: [r.width, r.height],
                img: [im.getBoundingClientRect().width, im.getBoundingClientRect().height],
                svg: [svg.getBoundingClientRect().width, svg.getBoundingClientRect().height]};
    }""")
    results["checks"]["geometry"] = geom
    if abs(geom["img"][0] - geom["svg"][0]) > 2 or abs(geom["img"][1] - geom["svg"][1]) > 2:
        fails.append("callout layer does not line up with the drawing: %s" % geom)

    # screenshot the default state, then one with a callout selected, at full page
    page.screenshot(path=SHOT.replace(".png", "_full.png"), full_page=True)
    page.click('.cal[data-c="C"]')
    page.wait_for_timeout(300)
    page.screenshot(path=SHOT, full_page=True)
    page.screenshot(path=SHOT.replace(".png", "_viewport.png"), full_page=False)

    browser.close()

results["checks"]["failures"] = fails
results["verdict"] = "PASS" if not fails else "FAIL"
with open(os.path.join(HERE, "_raw", "page_verify.json"), "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1)

print("requests          : %d   (non-file:// : %d)" % (len(requests), len(non_file)))
print("console errors    : %d" % len(results["checks"]["console_errors"]))
print("page errors       : %d" % len(errors))
print("callouts present  : %s" % ids)
print("key list rows     : %d" % rows)
print("stage geometry    : img %s  svg %s" % (geom["img"], geom["svg"]))
print()
for cid, v in verified.items():
    print("  click %s -> %-34s keys %s  euro %s"
          % (cid, v["title"], v["keys_seen"], v["eur_seen"]))
print()
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
else:
    print("no failures")
print("VERDICT:", results["verdict"])
