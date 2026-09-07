"""QA screenshots for master IDS dealer compare Map tab (headless, not user open)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
HTML = ROOT.parent / "IDS_2026_dealer_compare.html"
SHOTS = ROOT
SHOTS.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def shot(page, name: str) -> Path:
    out = SHOTS / name
    page.screenshot(path=str(out), full_page=False)
    print("wrote", out)
    return out


def wait_map_tiles(page) -> None:
    page.locator('button.tab[data-tab="map"]').click()
    page.wait_for_selector("#ids-map", timeout=15000)
    page.wait_for_timeout(400)
    page.wait_for_selector(".leaflet-tile-loaded", timeout=25000)
    page.wait_for_timeout(2500)


def main() -> None:
    if not HTML.is_file():
        raise SystemExit(f"missing {HTML}")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(HTML.as_uri(), wait_until="load", timeout=60000)
        page.wait_for_selector("#stats", timeout=15000)
        page.wait_for_timeout(400)
        wait_map_tiles(page)
        shot(page, "master_map.png")
        body = page.inner_text("body")
        assert "API KEY" not in body.upper()
        assert "CARTO" not in body.upper()
        assert "Offline pin map" not in body
        assert "pin grid only" not in body.lower()
        tile_src = page.evaluate(
            """() => {
              const img = document.querySelector('#ids-map img.leaflet-tile');
              return img ? img.src : '';
            }"""
        )
        print("tile_src", tile_src)
        assert "openstreetmap.org" in tile_src, tile_src
        loaded = page.locator(".leaflet-tile-loaded").count()
        print("loaded_tiles", loaded)
        assert loaded > 0
        # MIDI 4 still toggles on master
        page.locator("#btn-midi4").click()
        page.wait_for_timeout(800)
        page.wait_for_selector(".leaflet-tile-loaded", timeout=15000)
        page.wait_for_timeout(1500)
        shot(page, "master_map_midi4.png")
        midi_on = page.evaluate(
            """() => document.getElementById('btn-midi4').getAttribute('aria-pressed')"""
        )
        print("midi4_pressed", midi_on)
        assert midi_on == "true"
        browser.close()


if __name__ == "__main__":
    main()
