"""
ISZE — Tranzparts (UK) competitive price scraper.

Tranzparts (tranzparts.co.uk, est. 1979, Preston) is a dedicated Isuzu truck
parts stockist — verified 2026-07-09 as a real e-commerce catalog (not a
lead-gen page), Shopify-based, no bot-block observed.

Unlike KS International, this catalog is NOT indexed by Isuzu OEM part number
(confirmed: searching a raw Isuzu PN returns zero hits — products are titled
by the aftermarket brand's own part number, e.g. "AIR FILTER C 29 939"). This
scraper therefore crawls the whole /collections/isuzu catalog and classifies
each product into a PMS category (oil/fuel/air filter, clutch, brake) by
keyword match on the product title — a category-level price benchmark, not a
per-PN match. Do not conflate with KS International's PN-level data.

Output: tranzparts_results.csv (one row per product found)

Usage:
    python tranzparts_scraper.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
_TOOLS = SCRIPT_DIR.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.cv_category_crawler import SiteConfig, crawl_site, summarise_by_category, write_products_csv

GBP_EUR = 1.17  # matches build_executive_dashboard.py — update both if it changes

CFG = SiteConfig(
    site="Tranzparts",
    country="UK",
    currency="GBP",
    fx_to_eur=GBP_EUR,
    category_urls=["https://tranzparts.co.uk/collections/isuzu"],
    product_link_selector='a[href*="/products/"]',
    price_selector=".price__current",
    next_page_selector='a[rel="next"]',
    max_pages=5,
    headers={"Accept-Language": "en-GB,en;q=0.9"},
)


def main():
    print("=" * 60)
    print("  ISZE Tranzparts (UK) Price Scraper")
    print("  Category-level (not PN-level) — see module docstring")
    print("=" * 60)

    products = crawl_site(CFG)
    print(f"\nFound {len(products)} priced products")

    out_csv = SCRIPT_DIR / "tranzparts_results.csv"
    write_products_csv(out_csv, products)
    print(f"Wrote {out_csv}")

    print("\nCategory summary:")
    for row in summarise_by_category(products):
        print(f"  {row['PMS_Category']:<12} n={row['N']:<4} min=EUR{row['Min_EUR']:<8} avg=EUR{row['Avg_EUR']}")


if __name__ == "__main__":
    main()
