"""Render + measure the chart forms gallery at two widths, and fail on blank.

WHAT IT PROVES (and what it does not)
    * Proves every <canvas> on the page painted real pixels at 1440px and 1000px.
      Ink is counted from the canvas's own getImageData, so this is a pixel count,
      not an assumption that a chart library ran.
    * Proves no page error and no console error was raised during the render.
    * Proves each canvas has room around its ink (a crude stand-in for unclipped
      labels -- it cannot read the label text, so a human still has to look).
    * Writes a screenshot per panel per width, to be image-read by hand.

WHAT IT DOES NOT PROVE
    * That no label overlaps another label. Only the eye catches that.

RUN
    python 02_dashboards/_design/chart_gallery/qa_chart_forms_gallery.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

HERE = Path(__file__).resolve().parent
ART = HERE / "ISZE_Chart_Forms_Gallery.html"
QA = HERE / "_qa"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
WIDTHS = [1440, 1000]
PANELS = ["p" + str(i) for i in range(1, 11)]

INK_JS = """
() => {
  const out = { canvases: [], charts: 0, panelCount: 0 };
  out.panelCount = document.querySelectorAll('section.panel').length;
  if (window.__galleryCharts) { out.charts = window.__galleryCharts.length; }
  document.querySelectorAll('canvas').forEach(cv => {
    const id = cv.id || 'canvas-anon';
    const w = cv.width, h = cv.height;
    let rec = { id: id, css_w: Math.round(cv.getBoundingClientRect().width),
                css_h: Math.round(cv.getBoundingClientRect().height),
                px_w: w, px_h: h, ink: 0, ink_pct: 0, dark_edge_ink: 0 };
    try {
      const ctx = cv.getContext('2d');
      const d = ctx.getImageData(0, 0, w, h).data;
      let ink = 0, minX = w, maxX = -1, minY = h, maxY = -1, darkEdge = 0;
      const RING = 2;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const i = (y * w + x) * 4;
          if (d[i + 3] > 12) {
            ink++;
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (y < minY) minY = y;
            if (y > maxY) maxY = y;
            // Dark ink = text or a bar, not the pale grid. A dark pixel inside
            // the outer ring is a label or bar being cut off by the canvas.
            const lum = (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114);
            if (lum < 140 && (x < RING || y < RING || x >= w - RING || y >= h - RING)) {
              darkEdge++;
            }
          }
        }
      }
      rec.ink = ink;
      rec.ink_pct = +(ink / (w * h) * 100).toFixed(3);
      rec.dark_edge_ink = darkEdge;
      if (ink > 0) { rec.ink_box = [minX, minY, maxX, maxY]; }
    } catch (e) {
      rec.error = String(e);
    }
    out.canvases.push(rec);
  });
  return out;
}
"""


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    url = ART.as_uri()
    report = {"artifact": str(ART), "url": url, "widths": {}, "ok": True, "failures": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        for width in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": 1100}, device_scale_factor=2)
            page_errors = []
            console_errors = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            page.goto(url, wait_until="load")
            page.wait_for_function("window.__galleryReady === true", timeout=25000)
            page.wait_for_timeout(700)

            data = page.evaluate(INK_JS)
            build_errors = page.evaluate("window.__galleryErrors || []")
            shots = []
            for pid in PANELS:
                el = page.query_selector("#" + pid)
                if el is None:
                    report["failures"].append(str(width) + "px: panel #" + pid + " missing")
                    continue
                path = QA / ("gallery_" + str(width) + "_" + pid + ".png")
                el.screenshot(path=str(path))
                shots.append(str(path))

            full = QA / ("gallery_" + str(width) + "_full.png")
            page.screenshot(path=str(full), full_page=True)
            shots.append(str(full))

            blank = [c["id"] for c in data["canvases"] if c["ink"] < 400]
            # Only dark ink at the very edge signals a clipped label or bar.
            # A pale axis line running to the canvas edge is normal and is not
            # counted (grid lines measure ~230 luminance, text does not).
            edge = [c["id"] for c in data["canvases"] if c.get("dark_edge_ink", 0) > 0]
            min_ink = min([c["ink"] for c in data["canvases"]] or [0])

            report["widths"][str(width)] = {
                "panels": data["panelCount"],
                "chart_instances": data["charts"],
                "canvas_count": len(data["canvases"]),
                "min_ink_px": min_ink,
                "blank_canvases": blank,
                "edge_touching_canvases": edge,
                "canvases": data["canvases"],
                "page_errors": page_errors,
                "console_errors": console_errors,
                "build_errors": build_errors,
                "screenshots": shots,
            }
            if data["panelCount"] != 10:
                report["failures"].append(str(width) + "px: " + str(data["panelCount"]) + " panels, expected 10")
            if build_errors:
                report["failures"].append(str(width) + "px: panel build errors: " + str(build_errors))
            if blank:
                report["failures"].append(str(width) + "px: blank canvas(s): " + str(blank))
            if page_errors:
                report["failures"].append(str(width) + "px: page errors: " + str(page_errors))
            if console_errors:
                report["failures"].append(str(width) + "px: console errors: " + str(console_errors))
            if edge:
                report["failures"].append(str(width) + "px: ink reaching the last pixel of the canvas (clipping): " + str(edge))
            page.close()
        browser.close()

    report["ok"] = not report["failures"]
    out = QA / "gallery_render_report.json"
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")

    for width in WIDTHS:
        w = report["widths"][str(width)]
        print("--- " + str(width) + "px ---")
        print("  panels=" + str(w["panels"]) + "  chart instances=" + str(w["chart_instances"]) + "  canvases=" + str(w["canvas_count"]))
        print("  min ink px=" + str(w["min_ink_px"]) + "  blank=" + (str(w["blank_canvases"]) if w["blank_canvases"] else "none"))
        print("  ink reaching last canvas pixel=" + (str(w["edge_touching_canvases"]) if w["edge_touching_canvases"] else "none"))
        print("  page errors=" + str(len(w["page_errors"])) + "  console errors=" + str(len(w["console_errors"])) + "  panel build errors=" + str(len(w["build_errors"])))
        for c in w["canvases"]:
            print("    " + c["id"].rjust(10) + "  ink=" + str(c["ink"]).rjust(7) + " px  " + str(c["ink_pct"]).rjust(6) + "%  " + str(c["css_w"]) + "x" + str(c["css_h"]) + " css  dark-edge=" + str(c.get("dark_edge_ink", 0)))
    print("")
    print("report: " + str(out))
    if report["ok"]:
        print("GALLERY_RENDER_OK")
        return 0
    print("GALLERY_RENDER_FAIL")
    for f in report["failures"]:
        print("  - " + f)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
