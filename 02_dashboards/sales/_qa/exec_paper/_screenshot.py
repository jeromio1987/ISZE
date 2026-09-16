"""QA screenshots for exec aftersales paper (headless Chrome)."""
from pathlib import Path
import json

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "ISZE_Exec_Aftersales_Paper.html"
QA = Path(__file__).resolve().parent
QA.mkdir(parents=True, exist_ok=True)

PROBE = """() => {
  const body = (document.body.innerText || '').replace(/\\s+/g, ' ').trim();
  const bars = document.querySelectorAll('.bar-row').length;
  const rows = document.querySelectorAll('tbody tr').length;
  const h1 = document.querySelector('h1')?.textContent || '';
  const bad = ['wallet','street','iml v7','model b','prism lane']
    .filter(w => body.toLowerCase().includes(w));
  const need = {
    clutch: /clutch disc/i.test(body),
    brakePad: /brake pad/i.test(body),
    placeholder: /flat\\s*€?\\s*250|placeholder/i.test(body),
    telematics: /telematic|subscription/i.test(body),
    gp: /GP at risk|gross margin/i.test(body),
    tenders: /376\\s+opportunit/i.test(body),
    selloutPct: /54\\.4%\\s+of\\s+GPS\\s+billed/i.test(body),
  };
  return {
    bodyLen: body.length,
    bars,
    rows,
    h1: h1.slice(0, 160),
    bad,
    need,
    pages: document.querySelectorAll('.paper-page').length
  };
}"""


def show_only(pid: str) -> str:
    return f"""() => {{
  document.querySelectorAll('.paper-page').forEach(el => {{
    el.style.display = el.id === '{pid}' ? 'block' : 'none';
  }});
  document.body.style.background = '#f7f4ee';
}}"""


with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=True,
        proxy={"server": "http://127.0.0.1:9"},
        args=["--disable-web-security", "--allow-file-access-from-files"],
    )
    page = browser.new_page(viewport={"width": 1100, "height": 1400})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(HTML.resolve().as_uri(), wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    probe = page.evaluate(PROBE)
    shots = {
        "page-001-cover.png": None,
        "page-003-billed-target.png": "p3",
        "page-004-opportunity.png": "p4",
        "page-008-price-pn.png": "p8",
        "page-010-tenders.png": "p10",
        "page-011-holes.png": "p11",
    }
    # cover first (all pages visible initially — crop viewport = cover)
    shot1 = QA / "page-001-cover.png"
    page.screenshot(path=str(shot1), full_page=False)
    for name, pid in shots.items():
        if pid is None:
            continue
        page.evaluate(show_only(pid))
        page.wait_for_timeout(600)
        page.screenshot(path=str(QA / name), full_page=False)
    print("errs", errs[:4])
    print("probe", json.dumps(probe, indent=2))
    for name in shots:
        pth = QA / name
        print(name, pth.exists(), pth.stat().st_size if pth.exists() else 0)
    page.close()
    browser.close()
    if probe.get("bad"):
        raise SystemExit(f"forbidden words in paint: {probe['bad']}")
    need = probe.get("need") or {}
    missing = [k for k, v in need.items() if not v]
    if missing:
        raise SystemExit(f"paint probe missing themes: {missing}")
    if probe.get("bars", 0) < 40 or probe.get("pages") != 16:
        raise SystemExit(f"paint probe weak: {probe}")
