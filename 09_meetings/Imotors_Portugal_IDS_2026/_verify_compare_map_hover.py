"""Verify embedded Map tab: tiles + hover tooltip vs Portugal national average."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

html = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026"
    r"\IDS_2026_dealer_compare_Portugal.html"
)
out = html.with_name("_compare_map_verify.png")
uri = html.as_uri()
print("uri", uri)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto(uri, wait_until="domcontentloaded", timeout=60000)

    # Open Map tab
    page.click('.tab[data-tab="map"]')
    page.wait_for_timeout(4000)

    info = page.evaluate(
        """() => {
      const pins = document.querySelectorAll('.rank-pin');
      const tiles = document.querySelectorAll('.leaflet-tile-loaded');
      const status = (document.getElementById('pt-tile-status') || {}).textContent || '';
      return {
        hasLeaflet: typeof L !== 'undefined',
        hasMap: !!window.__ptMap,
        pins: pins.length,
        tiles: tiles.length,
        status,
        mapSize: (() => {
          const el = document.getElementById('pt-map');
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return [Math.round(r.width), Math.round(r.height)];
        })(),
        pointsSample: (window.__ptMap ? null : null)
      };
    }"""
    )
    print("INFO", info)

    # Hover first pin
    pin = page.locator(".rank-pin").first
    pin.hover(force=True)
    page.wait_for_timeout(800)
    tip = page.evaluate(
        """() => {
      const tip = document.querySelector('.leaflet-tooltip.pt-map-tooltip, .leaflet-tooltip');
      return tip ? tip.innerText : null;
        }"""
    )
    print("TOOLTIP", tip)

    # Also check POINTS data for national avg
    sample = page.evaluate(
        """() => {
          // find POINTS from script text
          const scripts = [...document.scripts].map(s => s.textContent || '');
          const hit = scripts.find(t => t.includes('Portugal national average') && t.includes('POINTS'));
          if (!hit) return null;
          const m = hit.match(/const POINTS = (\\[.*?\\]);/s);
          if (!m) return {hasPoints:false};
          try {
            const pts = JSON.parse(m[1]);
            return {
              hasPoints: true,
              n: pts.length,
              first: pts[0],
              withAvg: pts.filter(x => x.country_avg != null).length,
              withDelta: pts.filter(x => x.delta_pp != null).length,
            };
          } catch (e) {
            return {err: String(e)};
          }
        }"""
    )
    print("POINTS", sample)

    page.screenshot(path=str(out), full_page=False)
    browser.close()

print("saved", out)

ok = (
    info.get("hasLeaflet")
    and info.get("hasMap")
    and info.get("pins", 0) >= 15
    and tip
    and "national average" in (tip or "").lower()
    and "Dealer total score" in (tip or "")
)
if not ok:
    print("VERIFY_FAIL")
    sys.exit(2)
print("VERIFY_OK hover shows dealer score vs Portugal national average")
