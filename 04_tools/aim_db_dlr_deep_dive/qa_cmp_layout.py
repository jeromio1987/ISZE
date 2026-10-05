"""Confirm the lower sections paint at both widths, and that nothing is clipped.

Reports the document height, whether the coverage table and footer have content, and takes
targeted screenshots of the lower half at narrow width.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\_qa")


def main():
    runs = sys.argv[1:] or ["PORTUGAL", "ALL"]
    out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            args=["--allow-file-access-from-files"])
        for run in runs:
            for tag, w, h in (("desktop", 1500, 1000), ("narrow", 390, 900)):
                pg = b.new_page(viewport={"width": w, "height": h})
                pg.goto((DASH / f"ISZE_AIM_Comparison_{run}.html").as_uri(), wait_until="load")
                pg.wait_for_timeout(2600)
                info = pg.evaluate("""() => {
                  const doc = document.documentElement;
                  const cover = document.querySelectorAll('#t-cover tbody tr').length;
                  const foot = document.getElementById('foot').textContent.length;
                  const csv = !!document.getElementById('csv');
                  const srch = !!document.getElementById('search');
                  const bars = document.querySelectorAll('#c-drill').length;
                  // any element wider than the viewport?
                  let over = [];
                  document.querySelectorAll('body *').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 && (r.right > doc.clientWidth + 2)) {
                      over.push((el.className||el.tagName)+':'+Math.round(r.right));
                    }
                  });
                  const cv = document.getElementById('c-drill');
                  return {h: doc.scrollHeight, w: doc.clientWidth, coverRows: cover,
                          footChars: foot, csv: csv, search: srch, bars: bars,
                          overflow: over.slice(0,8),
                          kpi: Array.from(document.querySelectorAll('#kpis .val'))
                                 .map(e=>e.textContent.trim()),
                          canvasPainted: cv ? cv.height > 50 : false};
                }""")
                # scroll to the coverage card and shoot it
                pg.evaluate("document.getElementById('s4').scrollIntoView()")
                pg.wait_for_timeout(700)
                shot = QA / f"cmp_{run}_{tag}_lower.png"
                pg.screenshot(path=str(shot))
                info["lower_shot"] = str(shot)
                out[f"{run}_{tag}"] = info
                pg.close()
        b.close()
    (QA / "cmp_layout.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k, v in out.items():
        print(f"{k:<18} page {v['w']}x{v['h']}  coverage rows {v['coverRows']}  "
              f"footer {v['footChars']} chars  canvas {v['canvasPainted']}  "
              f"overflow {v['overflow'] or 'none'}")
        print(f"                   kpi {v['kpi'][:4]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
