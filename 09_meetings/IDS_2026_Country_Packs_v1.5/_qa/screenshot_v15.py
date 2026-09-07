"""QA screenshots for IDS country packs v1.5 Map tab (headless, not user open)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
PACK = ROOT.parent
SHOTS = ROOT
SHOTS.mkdir(parents=True, exist_ok=True)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def shot(page, name: str) -> Path:
    out = SHOTS / name
    page.screenshot(path=str(out), full_page=False)
    print("wrote", out)
    return out


def paint_country(page, html: Path, slug: str) -> None:
    page.goto(html.as_uri(), wait_until="load", timeout=60000)
    page.wait_for_selector("#stats", timeout=15000)
    page.wait_for_timeout(400)
    shot(page, f"{slug}_overview.png")

    page.locator('button.tab[data-tab="notes"]').click()
    page.wait_for_timeout(300)
    shot(page, f"{slug}_notes.png")

    page.locator('button.tab[data-tab="vs-network"]').click()
    page.wait_for_timeout(400)
    shot(page, f"{slug}_vs_network.png")

    page.locator('button.tab[data-tab="map"]').click()
    page.wait_for_selector("#ids-map", timeout=15000)
    page.wait_for_timeout(400)
    page.wait_for_selector(".leaflet-tile-loaded", timeout=25000)
    page.wait_for_timeout(2500)
    shot(page, f"{slug}_map.png")

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
    print(slug, "tile_src", tile_src)
    assert "openstreetmap.org" in tile_src, tile_src
    loaded = page.locator(".leaflet-tile-loaded").count()
    print(slug, "loaded_tiles", loaded)
    assert loaded > 0
    assert page.locator("#btn-midi4").count() == 0
    print(slug, "no API KEY / CARTO; OSM tiles loaded; no MIDI 4")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        paint_country(
            page,
            PACK / "Switzerland" / "IDS_2026_dealer_compare_Switzerland.html",
            "ch",
        )
        paint_country(
            page,
            PACK / "France" / "IDS_2026_dealer_compare_France.html",
            "fr",
        )
        browser.close()


if __name__ == "__main__":
    main()
