"""Visual QA for ISZE_OS_Console.html — real Chrome, full-page slices, overflow assertions.

Usage:  python qa_os_console.py
Writes PNGs into _qa_console/ and prints a JSON report of every defect found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
HTML = OPS / "ISZE_OS_Console.html"
OUT = HERE
OUT.mkdir(exist_ok=True)
SLICE = 1250
WIDTHS = [1440, 1280, 1024, 390]

OVERFLOW_JS = r"""
() => {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const bad = [];
  const clipped = [];
  const all = document.querySelectorAll('body *');
  for (const el of all) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right > w + 1 || r.left < -1) {
      bad.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className || '').toString().slice(0, 60),
        text: (el.textContent || '').trim().slice(0, 60),
        left: Math.round(r.left), right: Math.round(r.right),
      });
    }
    const cs = getComputedStyle(el);
    if ((cs.overflow === 'hidden' || cs.overflowX === 'hidden' || cs.overflowY === 'hidden')
        && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)) {
      clipped.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className || '').toString().slice(0, 60),
        text: (el.textContent || '').trim().slice(0, 60),
        sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight,
      });
    }
  }
  return {
    innerWidth: w, innerHeight: h,
    docScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    docScrollHeight: document.documentElement.scrollHeight,
    horizontalOverflow: document.documentElement.scrollWidth > w + 1,
    outsideBox: bad.slice(0, 40),
    outsideBoxCount: bad.length,
    clipped: clipped.slice(0, 40),
    clippedCount: clipped.length,
  };
}
"""


def main() -> None:
    report: dict = {"screenshots": [], "widths": {}}
    shots: list[str] = []

    with sync_playwright() as p:
        # Real Chrome, not the headless shell.
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--disable-gpu", "--no-first-run", "--force-device-scale-factor=1"],
        )
        for width in WIDTHS:
            ctx = browser.new_context(viewport={"width": width, "height": 900},
                                      device_scale_factor=1)
            page = ctx.new_page()
            page.goto(HTML.as_uri(), wait_until="load")
            page.wait_for_timeout(700)
            res = page.evaluate(OVERFLOW_JS)
            report["widths"][str(width)] = res

            total = res["docScrollHeight"]
            n = max(1, (total + SLICE - 1) // SLICE)
            for i in range(n):
                y = i * SLICE
                h = min(SLICE, total - y)
                if h < 80:
                    break
                name = "w%d_slice%02d.png" % (width, i + 1)
                page.screenshot(path=str(OUT / name), full_page=True,
                                clip={"x": 0, "y": y, "width": width, "height": h})
                shots.append(name)
            ctx.close()

        # Section zooms + hover states at 1440.
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000},
                                  device_scale_factor=1)
        page = ctx.new_page()
        page.goto(HTML.as_uri(), wait_until="load")
        page.wait_for_timeout(700)

        def zoom(sel: str, name: str, pad: int = 12) -> None:
            el = page.query_selector(sel)
            if not el:
                report.setdefault("missing_selectors", []).append(sel)
                return
            box = el.bounding_box()
            if not box:
                report.setdefault("missing_selectors", []).append(sel + " (no box)")
                return
            page.screenshot(path=str(OUT / name), full_page=True, clip={
                "x": max(0, box["x"] - pad),
                "y": max(0, box["y"] - pad),
                "width": min(1440, box["width"] + pad * 2),
                "height": box["height"] + pad * 2,
            })
            shots.append(name)

        zoom("section:nth-of-type(1) svg", "zoom_loop_svg.png")
        zoom(".grid2 .card.wide:nth-of-type(1)", "zoom_chart1.png")
        zoom(".grid2", "zoom_grid2_top.png")
        cards = page.query_selector_all(".grid2 .card")
        for idx, name in [(1, "zoom_chart2_growth.png"), (2, "zoom_chart3_cover.png"),
                          (4, "zoom_chart5_visibility.png"), (5, "zoom_chart6_capture.png"),
                          (6, "zoom_chart7_categories.png")]:
            if len(cards) > idx:
                b = cards[idx].bounding_box()
                page.screenshot(path=str(OUT / name), full_page=True,
                                clip={"x": max(0, b["x"] - 10), "y": max(0, b["y"] - 10),
                                      "width": min(1440, b["width"] + 20), "height": b["height"] + 20})
                shots.append(name)
        if len(cards) > 3:
            b = cards[3].bounding_box()
            page.screenshot(path=str(OUT / "zoom_chart4_split.png"), full_page=True,
                            clip={"x": max(0, b["x"] - 10), "y": max(0, b["y"] - 10),
                                  "width": min(1440, b["width"] + 20), "height": b["height"] + 20})
            shots.append("zoom_chart4_split.png")
        if len(cards) > 7:
            b = cards[7].bounding_box()
            page.screenshot(path=str(OUT / "zoom_chart8_km.png"), full_page=True,
                            clip={"x": max(0, b["x"] - 10), "y": max(0, b["y"] - 10),
                                  "width": min(1440, b["width"] + 20), "height": b["height"] + 20})
            shots.append("zoom_chart8_km.png")
        zoom("table.queue", "zoom_queue.png")
        zoom("section:nth-of-type(5)", "zoom_honesty.png")
        zoom(".loop-narrow", "zoom_loop_narrow_hidden.png")

        # Hover states: a hero chip, a bar value chip, a queue state chip.
        hovers = [
            (".hero-kpis .hk:nth-child(4)", "hover_hero_chip.png"),
            (".bar-row:nth-child(1) .bv .kpi", "hover_bar_value.png"),
            (".queue tbody tr:nth-child(3) .chip", "hover_queue_chip.png"),
        ]
        for sel, name in hovers:
            el = page.query_selector(sel)
            if not el:
                report.setdefault("missing_selectors", []).append(sel)
                continue
            el.hover()
            page.wait_for_timeout(250)
            box = el.bounding_box()
            page.screenshot(path=str(OUT / name), full_page=False)
            shots.append(name)
            # also capture the tooltip region expanded
            page.mouse.move(0, 0)
            page.wait_for_timeout(150)

        ctx.close()

        # 390 hover/stack check for the stacked bars reflowing to column blocks.
        ctx = browser.new_context(viewport={"width": 390, "height": 900},
                                  device_scale_factor=1)
        page = ctx.new_page()
        page.goto(HTML.as_uri(), wait_until="load")
        page.wait_for_timeout(600)
        for sel, name in [(".stack", "w390_stack.png"), (".loop-narrow", "w390_loop.png"),
                          ("table.queue", "w390_queue.png"), (".hero-kpis", "w390_hero.png")]:
            el = page.query_selector(sel)
            if not el:
                report.setdefault("missing_selectors", []).append(sel + " @390")
                continue
            box = el.bounding_box()
            page.screenshot(path=str(OUT / name), full_page=True, clip={
                "x": 0, "y": max(0, box["y"] - 8), "width": 390,
                "height": min(box["height"] + 16, 1600)})
            shots.append(name)
        ctx.close()

        browser.close()

    report["screenshots"] = shots
    report["count"] = len(shots)
    (OUT / "_qa_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "screenshots"}, indent=1))
    print("SCREENSHOTS: %d" % len(shots))
    for s in shots:
        print("  " + s)


if __name__ == "__main__":
    main()
