"""The headline numbers a person sees on each rebuilt page, read from the rendered page."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright  # noqa: E402

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

PAGES = [
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_ALL.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html",
]

PROBE = r"""
() => {
  const kpis = Array.from(document.querySelectorAll('.kpi')).map(e => e.textContent.replace(/\s+/g,' ').trim()).slice(0, 16);
  const h1 = document.querySelector('h1') ? document.querySelector('h1').innerText : '';
  const sub = document.querySelector('.sub') ? document.querySelector('.sub').innerText.replace(/\s+/g,' ').slice(0, 260) : '';
  const secs = Array.from(document.querySelectorAll('.card h2')).map(e => e.innerText.replace(/\s+/g,' '));
  return {h1: h1, sub: sub, kpis: kpis, sections: secs};
}
"""

for rel in PAGES:
    p = ISZE / rel
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        pg.goto(p.as_uri(), wait_until="load", timeout=120000)
        pg.wait_for_timeout(3500)
        d = pg.evaluate(PROBE)
        b.close()
    print("=" * 100)
    print(rel)
    print("  h1      :", d["h1"])
    print("  sub     :", d["sub"])
    print("  sections:", " / ".join(d["sections"]))
    print("  KPIs    :")
    for k in d["kpis"]:
        print("     -", k[:150])
    print()
