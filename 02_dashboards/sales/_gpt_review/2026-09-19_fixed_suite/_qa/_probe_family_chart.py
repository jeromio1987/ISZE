from playwright.sync_api import sync_playwright
from pathlib import Path
import json

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\ISZE_PMS_Family_Evolution_v2.html")
qa = html.parent / "_qa"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(html.resolve().as_uri(), wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    info = page.evaluate(
        """() => {
      const c = document.getElementById('c_main');
      const ch = window.Chart && Chart.getChart ? Chart.getChart(c) : null;
      if (!ch) return {noChart: true};
      const cfg = ch.config;
      return {
        type: cfg.type,
        indexAxis: (cfg.options && cfg.options.indexAxis) || null,
        labels: cfg.data.labels,
        ds: cfg.data.datasets.map(d => ({
          label: d.label,
          n: (d.data || []).length,
          sample: (d.data || []).slice(0, 3),
        })),
      };
    }"""
    )
    print(json.dumps(info, indent=2))
    page.locator("#c_main").screenshot(path=str(qa / "02_family_c_main.png"))
    # scroll to small multiples section if any
    page.evaluate("window.scrollTo(0, 2100)")
    page.wait_for_timeout(800)
    sm = page.evaluate(
        """() => [...document.querySelectorAll('[id^=sml_]')].map(c => ({
      id: c.id, w: c.width, h: c.height
    }))"""
    )
    print("sml", sm)
    browser.close()
