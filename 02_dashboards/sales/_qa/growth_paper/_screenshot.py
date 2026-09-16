"""QA screenshots + paint probe for the growth paper (headless Chrome, network OFF).

Network is killed (dead proxy) so this reproduces Jerome's offline machine: if the candles
still paint, the file is genuinely self-contained.
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
HTML = ROOT / "sales" / "ISZE_Growth_Plan_2026.html"
QA = Path(__file__).resolve().parent
QA.mkdir(parents=True, exist_ok=True)

PROBE = """() => {
  const body = (document.body.innerText || '').replace(/\\s+/g, ' ').trim();
  const canvases = [...document.querySelectorAll('canvas')];
  // a canvas is "painted" if it has non-blank pixels
  const painted = canvases.map(c => {
    try {
      const ctx = c.getContext('2d');
      const d = ctx.getImageData(0, 0, c.width, c.height).data;
      let nonBlank = 0;
      for (let i = 3; i < d.length; i += 400) { if (d[i] !== 0) nonBlank++; }
      return nonBlank > 3;
    } catch (e) { return 'err'; }
  });
  const bad = ['sell-out','sellout','sell out','book b','wallet','street index','iml v7','model b']
    .filter(w => body.toLowerCase().includes(w));
  const need = {
    hero: /how we grow parts sales/i.test(body),
    gap: /18,216,555|18\\.2M/.test(body),
    clutchLead: /clutch disc/i.test(body) && /3\\.14M|3,142,767/i.test(body),
    placeholder: /placeholder/i.test(body) && /250/.test(body),
    noList: /4,955,737|4\\.96M/.test(body),
    leverage2: /defend the lines we are undercut on/i.test(body),
    portugalGap: /portugal/i.test(body) && /six/i.test(body),
    warranty: /warranty/i.test(body),
    telematics: /connected-vehicle/i.test(body),
    decision: /ride the fleet/i.test(body) && /buy capture/i.test(body),
    sources: /how to check us/i.test(body),
  };
  return {
    bodyLen: body.length,
    pages: document.querySelectorAll('section.page').length + document.querySelectorAll('section.cover').length,
    canvases: canvases.length,
    painted,
    rows: document.querySelectorAll('tbody tr').length,
    bad, need,
  };
}"""


def show(idx: int) -> str:
    return f"""() => {{
  var ps = document.querySelectorAll('section.page');
  ps.forEach((el,i) => {{ el.style.display = (i === {idx}) ? 'block' : 'none'; }});
  document.body.style.background = '#fff';
  window.dispatchEvent(new Event('resize'));
}}"""


with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome", headless=True, proxy={"server": "http://127.0.0.1:9"},
        args=["--disable-web-security", "--allow-file-access-from-files"],
    )
    page = browser.new_page(viewport={"width": 1100, "height": 1500})
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(HTML.resolve().as_uri(), wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    probe = page.evaluate(PROBE)
    print("errors:", errs[:5])
    print("probe:", json.dumps(probe, indent=1))

    # cover + one shot per chart-bearing page and the two decision pages
    targets = [(0, "page-001-cover"), (2, "page-003-market"), (3, "page-004-gap"),
               (4, "page-005-blind"), (5, "page-006-runway"), (6, "page-007-performance"),
               (8, "page-009-levers"), (10, "page-011-lever2"), (12, "page-013-lever4"),
               (19, "page-020-decision")]
    for idx, name in targets:
        page.evaluate(show(idx))
        page.wait_for_timeout(700)
        page.screenshot(path=str(QA / f"{name}.png"), full_page=True)

    for _, name in targets:
        f = QA / f"{name}.png"
        print(f"{name}.png {f.exists()} {f.stat().st_size if f.exists() else 0}")

    page.close()
    browser.close()

    if probe.get("bad"):
        raise SystemExit(f"FORBIDDEN words painted: {probe['bad']}")
    missing = [k for k, v in (probe.get("need") or {}).items() if not v]
    if missing:
        raise SystemExit(f"paint probe missing themes: {missing}")
    not_painted = [i for i, v in enumerate(probe.get("painted") or []) if v is not True]
    if not_painted:
        raise SystemExit(f"blank canvases at index {not_painted} (painted={probe.get('painted')})")
    if probe.get("pages") != 20:
        raise SystemExit(f"expected 20 pages, got {probe.get('pages')}")
    print("\nPAINT PROBE PASS — 20 pages, all canvases painted, no forbidden words")
