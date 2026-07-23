"""
ISZE — T&M Commercials (UK) competitive price scraper.

T&M Commercials (tmcgroup.co.uk) is an Isuzu & Maxus parts specialist stocking
BOTH genuine and aftermarket parts side by side (e.g. "BRAKE DISC ASSY NON
GENUINE — Aftermarket Alternative") — verified 2026-07-09, real WooCommerce
catalog with prices.

Note: the site's search endpoint (?s=...) times out consistently (tested
2026-07-09, not a fluke — retried at 15s/25s/30s timeouts) even though the
base site loads fine. This scraper crawls category pages directly instead of
searching — same category-level (not per-PN) approach as tranzparts_scraper.py,
for the same reason: aftermarket catalogs are indexed by their own SKU, not
the Isuzu OEM part number.

Output: tmc_results.csv

Usage:
    python tmc_scraper.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
_TOOLS = SCRIPT_DIR.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.cv_category_crawler import SiteConfig, crawl_site, summarise_by_category, write_products_csv

GBP_EUR = 1.17

# Known Isuzu-truck product-category leaves as of 2026-07-09 (crawled from the
# /shop/ nav — WooCommerce category pages don't automatically show child-category
# products, so leaf categories are listed explicitly). Re-check tmcgroup.co.uk/shop/
# periodically for new model/category pages.
CATEGORY_URLS = [
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-125-euro-6/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-automatic-2008/november-2013/filters-and-service-items/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-manual-2008/november-2013-n75-190-manual-2008/filters-and-service-items-november-2013-n75-190-manual-2008/",
]

CFG = SiteConfig(
    site="T&M Commercials",
    country="UK",
    currency="GBP",
    fx_to_eur=GBP_EUR,
    category_urls=CATEGORY_URLS,
    product_link_selector="a.woocommerce-LoopProduct-link, li.product > a",
    price_selector="span.price",
    next_page_selector="a.next.page-numbers",
    max_pages=3,
    headers={"Accept-Language": "en-GB,en;q=0.9"},
)


def main():
    print("=" * 60)
    print("  ISZE T&M Commercials (UK) Price Scraper")
    print("  Category-level (not PN-level) — see module docstring")
    print("=" * 60)

    products = crawl_site(CFG)
    print(f"\nFound {len(products)} priced products")

    out_csv = SCRIPT_DIR / "tmc_results.csv"
    write_products_csv(out_csv, products)
    print(f"Wrote {out_csv}")

    print("\nCategory summary:")
    for row in summarise_by_category(products):
        print(f"  {row['PMS_Category']:<12} n={row['N']:<4} min=EUR{row['Min_EUR']:<8} avg=EUR{row['Avg_EUR']}")


if __name__ == "__main__":
    main()
