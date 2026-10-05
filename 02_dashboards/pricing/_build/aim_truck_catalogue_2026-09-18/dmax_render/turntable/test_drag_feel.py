"""Deterministic drag check: does the page turn the way a hand does?

The full verifier passes, but its drag assertions are timing-dependent because the page
has inertia. This drives the page through a controlled sequence and prints the angle
trajectory, so the feel can be checked numerically rather than by eye.
"""
from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ISZE_DMax_Turntable.html")


def main() -> int:
    url = "file:///" + PAGE.replace("\\", "/")
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, headless=True)
        pg = b.new_context(viewport={"width": 1440, "height": 950}).new_page()
        pg.goto(url, wait_until="load")
        pg.wait_for_function("window.__tt && window.__tt.state().ready === window.__tt.frames",
                             timeout=60000)
        pg.wait_for_timeout(600)

        box = pg.locator("#stage").bounding_box()
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        stag = pg.evaluate("window.__tt.step")
        print("frame step: %.2f deg, frames: %d" % (stag, pg.evaluate("window.__tt.frames")))

        def state():
            return pg.evaluate("window.__tt.state()")

        def slow_drag(dx, steps=40, settle=900, watch=False):
            """A drag with many small moves, which suppresses the inertia kick."""
            pg.mouse.move(cx, cy)
            pg.mouse.down()
            for i in range(1, steps + 1):
                pg.mouse.move(cx + dx * i / steps, cy)
                if watch:
                    pg.wait_for_timeout(4)
            pg.mouse.up()
            pg.wait_for_timeout(settle)
            return state()

        print("\n1) a slow drag right of 300 px")
        pg.evaluate("window.__tt.goto(0)")
        pg.wait_for_timeout(200)
        a0 = state()
        a1 = slow_drag(300)
        print("   before: frame %d angle %.1f" % (a0["index"], a0["angle"]))
        print("   after : frame %d angle %.1f  (moved %+.1f deg)"
              % (a1["index"], a1["angle"], a1["angle"] - a0["angle"]))
        exp = 300 * 0.42
        print("   expected from 0.42 deg/px: %+.1f deg; momentum adds a little on release" % exp)

        print("\n2) from there, a slow drag left of the same 300 px")
        a2 = slow_drag(-300)
        print("   after : frame %d angle %.1f  (moved %+.1f deg)"
              % (a2["index"], a2["angle"], a2["angle"] - a1["angle"]))
        print("   net over the two drags: %+.1f deg (should be near 0, plus momentum)"
              % (a2["angle"] - a0["angle"]))

        print("\n3) a fast flick right (inertia should carry it further)")
        pg.evaluate("window.__tt.goto(0)")
        pg.wait_for_timeout(200)
        pg.mouse.move(cx, cy)
        pg.mouse.down()
        for i in range(1, 9):
            pg.mouse.move(cx + 300 * i / 8, cy)
        pg.mouse.up()
        pg.wait_for_timeout(1600)
        f = state()
        print("   after flick: frame %d angle %.1f (started at 0, so %+.1f deg)"
              % (f["index"], f["angle"], f["angle"]))
        print("   the flick travelled further than 126 deg would be: %s"
              % ("yes" if f["angle"] > 126 + 5 else "NO"))

        print("\n4) continuous spin in one direction, 8 drags, does it advance monotonically?")
        pg.evaluate("window.__tt.goto(0)")
        pg.wait_for_timeout(200)
        prev = state()["angle"]
        mono = True
        for k in range(8):
            s = slow_drag(-120, steps=16, settle=700)
            print("   drag %d -> frame %2d angle %8.1f" % (k + 1, s["index"], s["angle"]))
            if s["angle"] >= prev:
                mono = False
            prev = s["angle"]
        print("   monotonic in the drag direction:", mono)

        print("\n5) does the visible frame always match the nearest multiple of the step?")
        ok = True
        for ang in (0, 7.5, 15, 45, 180, 359, 360, 367.5, -7.5, -15, -360, 3600):
            pg.evaluate("window.__tt.goto(%f / window.__tt.step)" % ang)
            pg.wait_for_timeout(60)
            s = state()
            want = round(ang / stag) % pg.evaluate("window.__tt.frames")
            if s["index"] != want:
                ok = False
                print("   MISMATCH at angle %.1f: got frame %d, want %d"
                      % (ang, s["index"], want))
        print("   all angles map to the nearest frame:", ok)

        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
