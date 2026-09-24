"""What the rendered page actually says in the two cards whose table is empty.

Returns the heading, the question line and the table area for section 6 (heat) and section 7
(dealer) on each page, so an empty table can be judged as explained or as a blank shell.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright  # noqa: E402

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

PAGES = [
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
]

PROBE = r"""
() => {
  const out = {};
  for (const id of ['s6','s7']) {
    const c = document.getElementById(id);
    out[id] = c ? c.innerText.replace(/\n+/g, ' | ').slice(0, 700) : '(card absent)';
  }
  return out;
}
"""

for rel in PAGES:
    p = ISZE / rel
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        pg.goto(p.as_uri(), wait_until="load", timeout=120000)
        pg.wait_for_timeout(3000)
        data = pg.evaluate(PROBE)
        b.close()
    print("=" * 100)
    print(rel)
    for k, v in data.items():
        print(f"  -- {k}: {v}")
    print()
