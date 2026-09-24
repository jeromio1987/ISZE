"""Compare the before copies with the rebuilt pages on the two cards whose table is empty.

If the blank section 6 on the Portugal page is the same before and after the repoint, it is
pre-existing and not introduced by this pass. If it differs, the rebuild caused it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright  # noqa: E402

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BEF = ISZE / "02_dashboards" / "_build" / "_aim_pass2"

PAIRS = [
    (BEF / "before_sales__ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
     ISZE / "02_dashboards" / "sales" / "ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html"),
    (BEF / "before_sales__ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
     ISZE / "02_dashboards" / "sales" / "ISZE_AIM_DB_DLR_Deep_Dive_ALL.html"),
]

PROBE = r"""
() => {
  const out = {};
  for (const id of ['s6','s7']) {
    const c = document.getElementById(id);
    if (!c) { out[id] = null; continue; }
    out[id] = {
      text: c.innerText.replace(/\n+/g, ' | ').slice(0, 260),
      rows: Array.from(c.querySelectorAll('table')).map(t => t.querySelectorAll('tbody tr').length),
      thead: Array.from(c.querySelectorAll('table')).map(t => t.querySelectorAll('thead th').length)
    };
  }
  return out;
}
"""


def run(path: Path) -> dict:
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        pg.goto(path.as_uri(), wait_until="load", timeout=120000)
        pg.wait_for_timeout(3000)
        d = pg.evaluate(PROBE)
        b.close()
    return d


for before, after in PAIRS:
    print("=" * 100)
    for label, p in (("BEFORE", before), ("AFTER ", after)):
        if not p.exists():
            print(f"  {label} missing: {p}")
            continue
        d = run(p)
        print(f"  {label} {p.name}")
        for k, v in d.items():
            print(f"        {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
    print()
