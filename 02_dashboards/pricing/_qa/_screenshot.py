"""QA screenshot for IAM vs billed scatter (headless Chrome)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing")
HTML = ROOT / "ISZE_IAM_Price_vs_Billed_PN.html"
QA = ROOT / "_qa"
QA.mkdir(parents=True, exist_ok=True)

PROBE = """() => {
  const body = (document.body.innerText || '').replace(/\\s+/g, ' ').trim();
  const bars = document.querySelectorAll('.bar-row').length;
  const rows = document.querySelectorAll('tbody tr').length;
  const canvases = [...document.querySelectorAll('canvas')].map(c => {
    let nz = 0;
    try {
      const ctx = c.getContext('2d');
      const w = Math.min(c.width || 0, 800), h = Math.min(c.height || 0, 500);
      if (!w || !h) return {blank: true, w, h, nz: 0};
      const d = ctx.getImageData(0, 0, w, h).data;
      for (let i = 3; i < d.length; i += 16) if (d[i] > 10) nz++;
    } catch (e) {
      return {blank: true, err: String(e)};
    }
    return {w: c.width, h: c.height, nz, blank: nz < 10};
  });
  const hero = document.querySelector('.hero .v');
  return {
    bodyLen: body.length,
    bars,
    rows,
    canvases,
    nHero: hero ? hero.textContent : '',
    sample: body.slice(0, 280)
  };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=True,
        proxy={"server": "http://127.0.0.1:9"},
        args=["--disable-web-security", "--allow-file-access-from-files"],
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(HTML.resolve().as_uri(), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)
    probe = page.evaluate(PROBE)
    shot1 = QA / "page-001.png"
    shot2 = QA / "page-scatter.png"
    page.screenshot(path=str(shot1), full_page=False)
    page.evaluate("window.scrollTo(0, 720)")
    page.wait_for_timeout(400)
    page.screenshot(path=str(shot2), full_page=False)
    print("errs", errs[:4])
    print("probe", probe)
    print("shot1", shot1)
    print("shot2", shot2)
    page.close()
    browser.close()
