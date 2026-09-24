"""Which tables on the four rebuilt pages have no tbody rows, and what are they for?

A table with no rows is only acceptable when the page says so in words (an amber banner or an
explicit 'no data' line). This prints the table's own label and the nearest heading so the empty
ones can be judged rather than assumed.
"""
from __future__ import annotations

import json
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
() => Array.from(document.querySelectorAll('table')).map((t, i) => {
  const rows = t.querySelectorAll('tbody tr').length;
  const head = t.querySelector('thead') ? t.querySelector('thead').innerText.replace(/\s+/g,' ').slice(0,110) : '';
  let prev = t.previousElementSibling, label = '';
  for (let k = 0; k < 4 && prev; k++, prev = prev.previousElementSibling) {
    if (/H[1-4]|\.h\b|card/.test(prev.className || '') || /^H[1-4]$/.test(prev.tagName)) {
      label = prev.innerText.replace(/\s+/g,' ').slice(0,140); break;
    }
  }
  const par = t.parentElement ? t.parentElement.innerText.replace(/\s+/g,' ').slice(0,160) : '';
  return {i: i, id: t.id, cls: t.className, rows: rows, head: head, label: label, parent: par};
})
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
    for t in data:
        flag = "EMPTY" if t["rows"] == 0 else "     "
        print(f"  [{flag}] table {t['i']} id={t['id']!r} class={t['cls'][:40]!r} rows={t['rows']}")
        if t["rows"] == 0:
            print(f"           label : {t['label']}")
            print(f"           head  : {t['head']}")
            print(f"           parent: {t['parent']}")
