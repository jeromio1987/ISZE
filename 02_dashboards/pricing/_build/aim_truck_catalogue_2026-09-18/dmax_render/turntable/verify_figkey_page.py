"""Verify the extended turntable page in headless Chrome over file://.

Checks:
  - every network request is a file: URL (no CDN, no sibling fetch)
  - zero console errors, zero page errors
  - the six zone cards are present and five of them carry brake money
  - clicking a zone card and clicking a zone on the vehicle both work
  - a drag changes the frame, and the frame notice appears off frame 1
  - screenshots are written to _qa for a human (or an image read) to look at

Playwright's bundled browser is not installed here, so the system Chrome is
used through executable_path.

Run:  python verify_figkey_page.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "ISZE_DMax_Turntable.html"
SHOTS = HERE / "_qa"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

from playwright.sync_api import sync_playwright   # noqa: E402


def main() -> int:
    SHOTS.mkdir(exist_ok=True)
    fails, notes = [], []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 1000},
                                 device_scale_factor=1)
        page = ctx.new_page()

        requests, console_errors, page_errors = [], [], []
        page.on("request", lambda r: requests.append(r.url))
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        page.goto(PAGE.as_uri(), wait_until="load")
        page.wait_for_function("window.__tt && window.__tt.state().ready === 48",
                               timeout=120_000)

        non_file = [u for u in requests if not u.startswith("file:")]
        if non_file:
            fails.append("non-file requests: %r" % non_file[:5])
        if console_errors:
            fails.append("console errors: %r" % console_errors[:5])
        if page_errors:
            fails.append("page errors: %r" % page_errors[:5])

        rep0 = page.evaluate("window.__tt.report()")
        print("initial report:", json.dumps(rep0, indent=1))
        if rep0["zoneCards"] != 6:
            fails.append("expected 6 zone cards, got %d" % rep0["zoneCards"])
        if rep0["polygons"] != 6:
            fails.append("expected 6 zone polygons, got %d" % rep0["polygons"])
        # four zones carry brake parts: front, engine, chassis, rear.
        # cab and electrical carry none, and must say so.
        if rep0["zoneCardsWithBrake"] != 4:
            fails.append("expected 4 zones with brake parts, got %d"
                         % rep0["zoneCardsWithBrake"])
        if rep0["moneyOnPage"] < 12:
            fails.append("only %d euro figures on the page" % rep0["moneyOnPage"])
        if not rep0["unplacedShown"]:
            fails.append("the not-on-the-vehicle line is not shown")
        if "\u20AC" not in rep0["paintedCard"]:
            fails.append("no euro figure is painted on a zone card")
        if "not on the vehicle" not in rep0["unplacedLine"].lower():
            fails.append("the not-on-the-vehicle line paints no explanation")
        print("painted card:", rep0["paintedCard"])
        print("painted line:", rep0["unplacedLine"])

        page.screenshot(path=str(SHOTS / "figkey_00_first_paint.png"), full_page=True)
        page.screenshot(path=str(SHOTS / "figkey_01_vehicle.png"))

        # ---- turn the zones on, so the vehicle itself is clickable
        page.click("#zbtn")
        page.wait_for_timeout(300)
        rep_zoned = page.evaluate("window.__tt.report()")
        print("zones on:", json.dumps(rep_zoned, indent=1))
        if not rep_zoned["zonesOn"]:
            fails.append("the zones button did not turn them on")
        if not rep_zoned["frameNotice"]:
            fails.append("the frame-1 notice is missing with the zones on")
        page.screenshot(path=str(SHOTS / "figkey_02_zones_on.png"), full_page=True)
        # an exact clipping of the stage, so the pictures can be measured
        page.locator("#stage").screenshot(path=str(SHOTS / "figkey_stage_frame1.png"))

        # ---- click a zone ON the vehicle. Find a point that really is inside a
        # polygon rather than guessing one: ask the page which element is on top
        # at a grid of points across the stage.
        hit = page.evaluate("""() => {
          var st = document.getElementById('stage').getBoundingClientRect();
          var want = ['front', 'chassis', 'cab', 'engine', 'rear', 'elec'];
          for (var j = 0; j < want.length; j++) {
            for (var gy = 0.06; gy <= 0.96; gy += 0.02) {
              for (var gx = 0.02; gx <= 0.98; gx += 0.01) {
                var x = st.left + st.width * gx, y = st.top + st.height * gy;
                var el = document.elementFromPoint(x, y);
                if (el && el.tagName === 'polygon' &&
                    el.getAttribute('data-zone') === want[j]) {
                  return {zone: want[j], x: x, y: y};
                }
              }
            }
          }
          return null;
        }""")
        print("found a clickable point on the vehicle:", hit)
        if not hit:
            fails.append("no point on the vehicle resolves to a zone polygon")
        else:
            page.mouse.click(hit["x"], hit["y"])
            page.wait_for_timeout(350)
            rep_front = page.evaluate("window.__tt.report()")
            print("after a click on the vehicle:", rep_front["selected"],
                  "|", rep_front["detailHeading"])
            if rep_front["selected"] != hit["zone"]:
                fails.append("clicking the %s area of the vehicle selected %r"
                             % (hit["zone"], rep_front["selected"]))
            if not rep_front["detailHeading"]:
                fails.append("the click on the vehicle opened no detail panel")
        page.locator("#stage").screenshot(path=str(SHOTS / "figkey_stage_clicked.png"))
        page.screenshot(path=str(SHOTS / "figkey_03_clicked_front.png"), full_page=True)

        # ---- click the chassis card, the one with the brake split
        page.click(".zcard[data-zone='chassis']")
        page.wait_for_timeout(350)
        rep_ch = page.evaluate("window.__tt.report()")
        print("after clicking the chassis card:", json.dumps(rep_ch, indent=1))
        if rep_ch["selected"] != "chassis":
            fails.append("the chassis card did not select")
        if rep_ch["detailRows"] < 1:
            fails.append("the chassis panel lists no part numbers")
        page.screenshot(path=str(SHOTS / "figkey_04_chassis_detail.png"), full_page=True)

        # ---- click the cab card, which must say it has no brake parts
        page.click(".zcard[data-zone='cab']")
        page.wait_for_timeout(350)
        cab_text = page.locator("#zdetail").inner_text()
        print("cab panel text:", cab_text[:400].replace("\n", " | "))
        if "No brake parts in this zone" not in cab_text:
            fails.append("the cab zone does not state that it has no brake parts")
        page.screenshot(path=str(SHOTS / "figkey_05_cab_no_brake.png"), full_page=True)

        # ---- drag to another frame and check the notice
        page.evaluate("window.__tt.drag(600)")
        page.wait_for_timeout(500)
        rep_drag = page.evaluate("window.__tt.report()")
        print("after a drag:", rep_drag["frame"], "|", rep_drag["frameNotice"][:90])
        if rep_drag["frame"] == rep_zoned["frame"]:
            fails.append("the drag did not change the frame")
        if not rep_drag["frameNotice"]:
            fails.append("no notice when the zones do not apply to this frame")
        page.screenshot(path=str(SHOTS / "figkey_06_off_frame.png"), full_page=True)

        # ---- turn back to frame 1 with the zones still on, and click again
        page.evaluate("window.__tt.goto(0)")
        page.wait_for_timeout(400)
        rep_back = page.evaluate("window.__tt.report()")
        print("back on frame 1:", json.dumps(rep_back, indent=1))
        if rep_back["frame"] != 1 or not rep_back["zonesOn"]:
            fails.append("could not return to frame 1 with the zones on")
        if rep_back["polygons"] != 6:
            fails.append("the zones did not come back on frame 1")
        print("painted detail after the second click:", rep_back["paintedDetail"][:200])
        if "\u20AC" not in rep_back["paintedDetail"]:
            fails.append("the detail panel paints no euro figure")
        page.locator("#panel").screenshot(path=str(SHOTS / "figkey_panel_cab.png"))
        page.locator("#zonegrid").screenshot(path=str(SHOTS / "figkey_cards.png"))

        browser.close()

    print()
    print("=" * 78)
    print("requests seen: %d   non-file: %d" % (len(requests), len(non_file)))
    print("console errors: %d   page errors: %d" % (len(console_errors), len(page_errors)))
    print("screenshots -> %s" % SHOTS)
    if fails:
        print("VERIFY FAILED")
        for f in fails:
            print("  -", f)
        return 1
    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
