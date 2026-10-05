"""Verify the turntable page the way the brief asks: in headless Chrome, over file://.

Checks, each of which fails the run rather than warns:
  1. the page loads from a file:// URL with ZERO requests to anything but file:
  2. zero console errors and zero page errors
  3. every frame image actually decodes (not just that a data URI exists)
  4. the still fallback is on screen before the frames are ready
  5. dragging changes the displayed frame, in BOTH directions
  6. the spin wraps: past the last frame forward, and past the first frame backward
  7. keyboard arrows step the frame
  8. screenshots are written for the record

Playwright's own bundled browser is not installed here, so Chrome is passed
explicitly via executable_path.

Run:  python verify_turntable.py --page <path to html> --shots _qa
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

import numpy as np
from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--page", required=True)
    p.add_argument("--shots", required=True)
    return p.parse_args()


def main() -> int:
    a = parse()
    page_path = os.path.abspath(a.page)
    shots = os.path.abspath(a.shots)
    os.makedirs(shots, exist_ok=True)
    url = "file:///" + page_path.replace("\\", "/")
    print("page :", page_path)
    print("url  :", url)
    if not os.path.exists(CHROME):
        raise SystemExit("Chrome not found at %s" % CHROME)

    failures = []
    report = {"page": page_path, "url": url, "checks": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True,
                                     args=["--allow-file-access-from-files"])
        ctx = browser.new_context(viewport={"width": 1440, "height": 950},
                                  device_scale_factor=1)
        page = ctx.new_page()

        requests, bad_requests = [], []
        console_msgs, console_errors, page_errors, failed_reqs = [], [], [], []

        def on_console(m):
            console_msgs.append(m.text)
            if m.type == "error":
                console_errors.append(m.text)

        page.on("request", lambda r: (requests.append(r.url),
                                      bad_requests.append(r.url)
                                      if not r.url.startswith("file:") else None))
        page.on("requestfailed", lambda r: failed_reqs.append(r.url))
        page.on("console", on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        page.goto(url, wait_until="load")
        page.wait_for_function("window.__tt && window.__tt.state().ready > 0",
                               timeout=60000)
        page.wait_for_timeout(2500)

        st = page.evaluate("window.__tt.state()")
        total = page.evaluate("window.__tt.frames")
        print("\n--- after load ---")
        print("frames in page :", total)
        print("frames decoded :", st["ready"], " failed:", st["failed"])
        print("network requests: %d, non-file: %d" % (len(requests), len(bad_requests)))
        print("console errors  : %d   page errors: %d" % (len(console_errors), len(page_errors)))

        report["checks"]["frames_in_page"] = total
        report["checks"]["frames_decoded"] = st["ready"]
        report["checks"]["frames_failed"] = st["failed"]
        report["checks"]["request_count"] = len(requests)
        report["checks"]["non_file_requests"] = bad_requests
        report["checks"]["console_errors"] = console_errors
        report["checks"]["page_errors"] = page_errors
        report["checks"]["failed_requests"] = failed_reqs
        report["checks"]["request_schemes"] = sorted(set(
            u.split(":")[0] for u in requests if ":" in u))

        if st["failed"]:
            failures.append("%d frame(s) failed to decode" % st["failed"])
        if st["ready"] != total:
            failures.append("only %d of %d frames decoded" % (st["ready"], total))
        if bad_requests:
            failures.append("%d non-file request(s): %s" % (len(bad_requests), bad_requests[:3]))
        if console_errors:
            failures.append("%d console error(s): %s" % (len(console_errors), console_errors[:3]))
        if page_errors:
            failures.append("page error(s): %s" % page_errors[:3])
        if failed_reqs:
            failures.append("failed request(s): %s" % failed_reqs[:3])

        # ---- 4. the still fallback is present before the frames are ready
        page.goto(url, wait_until="commit")
        page.wait_for_timeout(150)
        early = page.evaluate(
            "(() => { const p=document.getElementById('poster');"
            " return {src: !!p.src && p.src.startsWith('data:image'),"
            " vis: getComputedStyle(p).visibility,"
            " complete: p.complete,"
            " nat: p.naturalWidth}; })()")
        print("\n--- fallback at first paint ---")
        print("poster present and data-URI:", early["src"], " visibility:", early["vis"],
              " loaded:", early["complete"], " naturalWidth:", early["nat"])
        report["checks"]["poster_fallback"] = early
        if not early["src"]:
            failures.append("no still-image fallback present before frames load")
        if not early["nat"]:
            failures.append("the still fallback did not load")

        page.wait_for_function(
            "window.__tt && window.__tt.state().ready === window.__tt.frames", timeout=60000)
        page.wait_for_timeout(900)

        # ---- 5. dragging changes the frame, both directions
        def drag(dx, steps=12):
            box = page.locator("#stage").bounding_box()
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            page.mouse.move(cx, cy)
            page.mouse.down()
            for i in range(1, steps + 1):
                page.mouse.move(cx + dx * i / steps, cy, steps=2)
            page.mouse.up()
            page.wait_for_timeout(560)
            return page.evaluate("window.__tt.state()")

        page.evaluate("window.__tt.goto(0)")
        page.wait_for_timeout(350)
        before = page.evaluate("window.__tt.state()")
        right = drag(320)
        left = drag(-320)
        print("\n--- drag ---")
        print("start           : frame %d" % before["index"])
        print("after drag right: frame %d (angle %.1f)" % (right["index"], right["angle"]))
        print("after drag left : frame %d (angle %.1f)" % (left["index"], left["angle"]))
        report["checks"]["drag"] = {"start": before, "right": right, "left": left}
        if right["index"] == before["index"]:
            failures.append("dragging right did not change the displayed frame")
        if right["angle"] <= before["angle"]:
            failures.append("dragging right did not increase the angle")
        if left["index"] == right["index"]:
            failures.append("dragging left did not change the displayed frame")
        if left["angle"] >= right["angle"]:
            failures.append("dragging left did not decrease the angle")

        # the canvas must actually change pixels between two frames
        def sig():
            return page.evaluate(
                "(() => { const c=document.getElementById('cv');"
                " const g=c.getContext('2d');"
                " const d=g.getImageData(0,0,c.width,c.height).data;"
                " let h=0; for(let i=0;i<d.length;i+=997) h=(h*31+d[i])>>>0;"
                " return h; })()")

        page.evaluate("window.__tt.goto(0)")
        page.wait_for_timeout(320)
        s0 = sig()
        page.evaluate("window.__tt.drag(300)")
        page.wait_for_timeout(320)
        s1 = sig()
        print("canvas signature frame1=%s other=%s changed=%s" % (s0, s1, s0 != s1))
        report["checks"]["canvas_signature"] = {"frame1": s0, "other": s1, "changed": s0 != s1}
        if s0 == s1:
            failures.append("canvas pixels identical after turning - nothing was drawn")

        # ---- 6. wrap in both directions
        # __tt.goto() sets the angle exactly, with no momentum, so it is the right tool
        # for the wrap test.  (__tt.drag() takes PIXELS and feeds the inertia model,
        # which is deliberate in the page but wrong for an exact wrap assertion.)
        n = total
        page.evaluate("window.__tt.goto(0)")
        page.wait_for_timeout(240)
        page.evaluate("window.__tt.goto(-2 * %d)" % n)
        page.wait_for_timeout(260)
        back = page.evaluate("window.__tt.state()['index']")
        page.evaluate("window.__tt.goto(2 * %d)" % n)
        page.wait_for_timeout(260)
        fwd = page.evaluate("window.__tt.state()['index']")
        print("\n--- wrap ---")
        print("two full turns back from frame 1   -> frame %d (expect 0)" % back)
        print("two full turns forward from frame 1-> frame %d (expect 0)" % fwd)
        report["checks"]["wrap"] = {"back_to": back, "forward_to": fwd}
        if back != 0:
            failures.append("wrapping backward did not return to frame 1 (got %d)" % back)
        if fwd != 0:
            failures.append("wrapping forward did not return to frame 1 (got %d)" % fwd)

        # the true wrap edge, exactly one step past each end
        page.evaluate("window.__tt.goto(%d)" % (n - 1))
        page.wait_for_timeout(240)
        page.evaluate("window.__tt.goto(%d + 1)" % (n - 1))
        page.wait_for_timeout(280)
        edge = page.evaluate("window.__tt.state()['index']")
        page.evaluate("window.__tt.goto(-1)")
        page.wait_for_timeout(280)
        edge_back = page.evaluate("window.__tt.state()['index']")
        print("one step past the last frame     -> frame %d (expect 0)" % edge)
        print("one step before the first frame  -> frame %d (expect %d)" % (edge_back, n - 1))
        report["checks"]["wrap_edge"] = edge
        report["checks"]["wrap_edge_back"] = edge_back
        if edge != 0:
            failures.append("stepping forward off the last frame did not wrap to frame 1")
        if edge_back != n - 1:
            failures.append("stepping back off the first frame did not wrap to the last")

        # ---- 7. keyboard
        page.evaluate("window.__tt.goto(0)")
        page.wait_for_timeout(240)
        page.locator("#stage").click(position={"x": 5, "y": 5})
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        kr = page.evaluate("window.__tt.state()['index']")
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(300)
        kl = page.evaluate("window.__tt.state()['index']")
        print("\n--- keyboard ---")
        print("ArrowRight -> frame %d, then ArrowLeft -> frame %d" % (kr, kl))
        report["checks"]["keyboard"] = {"after_right": kr, "after_left": kl}
        if kr != 1:
            failures.append("ArrowRight did not advance to frame 2 (got %d)" % kr)
        if kl != 0:
            failures.append("ArrowLeft did not return to frame 1 (got %d)" % kl)

        # ---- 4d. the page must still show the truck with scripting unavailable.  A
        # fallback that only works because JS lays it out is not a fallback: the stage's
        # aspect ratio used to come from a JS-set CSS variable, which collapsed the stage
        # to zero height and hid the poster entirely with scripting off.
        nctx = ctx.browser.new_context(viewport={"width": 1440, "height": 950},
                                       java_script_enabled=False)
        npg = nctx.new_page()
        npg.goto(url, wait_until="load")
        npg.wait_for_timeout(1800)
        nojs_path = os.path.join(shots, "page_05_nojs.png")
        npg.screenshot(path=nojs_path, full_page=True)
        nctx.close()
        na = np.asarray(Image.open(nojs_path).convert("RGB")).astype(np.float32)
        nlum = na.mean(axis=2)
        dark = float((nlum < 170).mean())
        print("\n--- with scripting disabled ---")
        print("dark (truck) pixel share: %.3f" % dark)
        report["checks"]["no_js"] = {"screenshot": nojs_path, "truck_pixel_share": round(dark, 4)}
        if dark < 0.05:
            failures.append("with scripting off the truck is not visible (dark share %.3f) - "
                            "the fallback depends on JS" % dark)

        # ---- screenshots
        page.evaluate("window.__tt.goto(0)")
        page.wait_for_timeout(800)
        p1 = os.path.join(shots, "page_01_frame1.png")
        page.screenshot(path=p1, full_page=True)
        page.evaluate("window.__tt.goto(%d)" % (n // 2))
        page.wait_for_timeout(500)
        p2 = os.path.join(shots, "page_02_mid.png")
        page.screenshot(path=p2, full_page=True)
        report["checks"]["screenshot_frame1"] = p1
        report["checks"]["screenshot_mid"] = p2
        zb = page.locator("#zbtn")
        if zb.is_visible():
            zb.click()
            page.wait_for_timeout(700)
            p3 = os.path.join(shots, "page_03_zones.png")
            page.screenshot(path=p3, full_page=True)
            report["checks"]["screenshot_zones"] = p3
            # and confirm the zones are hidden again on a different frame
            page.evaluate("window.__tt.goto(%d)" % (n // 3))
            page.wait_for_timeout(500)
            zstate = page.evaluate(
                "(() => { const z=document.getElementById('zones');"
                " return {on: z.classList.contains('on'),"
                " polys: z.querySelectorAll('polygon').length}; })()")
            report["checks"]["zones_off_other_frame"] = zstate
            p4 = os.path.join(shots, "page_04_zones_off.png")
            page.screenshot(path=p4, full_page=True)
            report["checks"]["screenshot_zones_off"] = p4
        print("\nscreenshots:", p1, p2)
        browser.close()

    report["failures"] = failures
    report["ok"] = not failures
    outp = os.path.join(shots, "verify_turntable.json")
    with open(outp, "w") as fh:
        json.dump(report, fh, indent=1)
    print("\nwrote", outp)
    if failures:
        print("\n=== VERIFY FAILED ===")
        for f in failures:
            print("  -", f)
        return 1
    print("\n=== VERIFY OK ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
