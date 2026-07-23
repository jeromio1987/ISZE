"""
ISZE — Auto 365 (auto365.co.il, Israel) competitive price scraper.

Auto 365 sells certified new aftermarket parts ("בעלי תקן ובאישור משרד
התחבורה" — approved by the Ministry of Transport) for Isuzu, not used/salvage
parts — verified 2026-07-09, distinct from giltechparts.com which is a
salvage/breakers yard (a different competitive dynamic, not used here).

Category-level (not per-PN) approach, same reasoning as tranzparts_scraper.py
and tmc_scraper.py — this catalog is not indexed by Isuzu OEM part number.

FX note: ILS_EUR below is an approximate placeholder (not from sources.yaml,
which only has GBP/SEK rates) — confirm the real rate before citing Price_EUR
externally; Price (ILS) is the authoritative figure.

Output: auto365_results.csv

Usage:
    python auto365_scraper.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
_TOOLS = SCRIPT_DIR.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.cv_category_crawler import SiteConfig, crawl_site, summarise_by_category, write_products_csv

ILS_EUR = 0.25  # APPROXIMATE placeholder — confirm before citing externally

# 2026-07-10: confirmed pagination — ?page=N query param, 21 pages total (~10
# products/page, ~210 products). The "next" link shares the same CSS class as the
# numbered page links (page-link), so it can't be targeted by next_page_selector
# (CSS-only, no text matching) — listing all 21 page URLs directly instead of
# chaining through crawl_site's next_page_selector mechanism.
_BASE = "https://www.auto365.co.il/cat/71?manid=48"
_PAGE_URLS = [f"{_BASE}&page={n}" for n in range(1, 22)]

CFG = SiteConfig(
    site="Auto 365",
    country="Israel",
    currency="ILS",
    fx_to_eur=ILS_EUR,
    category_urls=_PAGE_URLS,
    product_link_selector='a[href*="/product/"]',
    price_selector=".price",
    next_page_selector=None,
    max_pages=1,  # each URL above is already one full page
    headers={"Accept-Language": "en-US,en;q=0.9,he;q=0.8"},
)


def main():
    print("=" * 60)
    print("  ISZE Auto 365 (Israel) Price Scraper")
    print("  Category-level (not PN-level) — see module docstring")
    print("  FX rate is an approximation — see docstring")
    print("=" * 60)

    products = crawl_site(CFG)
    print(f"\nFound {len(products)} priced products")

    out_csv = SCRIPT_DIR / "auto365_results.csv"
    write_products_csv(out_csv, products)
    print(f"Wrote {out_csv}")

    print("\nCategory summary:")
    for row in summarise_by_category(products):
        print(f"  {row['PMS_Category']:<12} n={row['N']:<4} min=EUR{row['Min_EUR']:<8} avg=EUR{row['Avg_EUR']}")


if __name__ == "__main__":
    main()
