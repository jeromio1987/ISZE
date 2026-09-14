"""
Shared crawler for CV/LCV aftermarket parts sites that do NOT index by Isuzu OEM
part number (confirmed 2026-07-09: Tranzparts search on a raw Isuzu PN returned
zero hits — its catalog is keyed to the aftermarket brand's own part number, e.g.
Mann-Filter "C 934 X". This is normal for non-Isuzu-specialist catalogs; only
Isuzu-specialist stockists like KS International index by Isuzu PN directly).

Strategy here is therefore category-level, not per-PN: crawl each site's own
Isuzu (or Isuzu-relevant) parts category page(s), extract every product's name
+ price, and classify each by PMS category via the same keyword regexes used in
build_executive_dashboard.py's PMS_BRIDGE_CATEGORIES. Output is a category-level
price benchmark per site (min/avg/count), NOT a per-PN match — do not conflate
with KS International's PN-level data when combining sources.

Several target sites block plain `requests` via TLS fingerprinting (confirmed on
motointegrator.de, euautoonderdelen.be — see diagnostic notes 2026-07-09) but allow
curl and curl_cffi's browser-impersonation. curl_cffi is used throughout for
consistency, with retry since at least one site (motointegrator.de) was observed
to intermittently 403 even under impersonation.
"""
from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as creq
except ImportError as e:
    raise SystemExit(f"curl_cffi required: pip install curl_cffi ({e})")

# Same 5 PMS categories as PMS_BRIDGE_CATEGORIES in build_executive_dashboard.py —
# kept in sync manually since this lives in a different tool tree (04_tools/_shared
# vs 04_tools/autodoc_scraper). If one changes, check the other.
PMS_CATEGORY_PATTERNS: list[tuple[str, str]] = [
    ("oil_filter",  r"oil filter|olie ?filter|\Ölfilter|filtre.{0,3}huile|מסנן שמן"),
    ("fuel_filter", r"fuel filter|brandstoffilter|kraftstofffilter|filtre.{0,3}(gas)?oil|מסנן דלק"),
    ("air_filter",  r"air filter|luchtfilter|luftfilter|filtre.{0,3}air|מסנן אוויר"),
    ("clutch",      r"clutch|koppeling|kupplung|embrayage|מצמד"),
    ("brake",       r"brake|rem(voering|blok|schijf)?|brems|frein|בלם|בלמים"),
]


def classify_pms_category(name: str) -> str | None:
    low = (name or "").lower()
    for key, pattern in PMS_CATEGORY_PATTERNS:
        if re.search(pattern, low, re.IGNORECASE):
            return key
    return None


@dataclass
class SiteConfig:
    site: str
    country: str
    currency: str
    fx_to_eur: float
    category_urls: list[str]
    product_link_selector: str          # CSS selector for <a> product links on listing page
    price_selector: str                 # CSS selector for a price element (searched within product card)
    card_selector: str | None = None    # CSS selector for the product "card" wrapping link+price; if None, price is searched near the link's parent
    price_regex: str = r"[\d.,]+"
    next_page_selector: str | None = None  # CSS selector for a "next page" <a> (rel=next or similar)
    max_pages: int = 5
    headers: dict = field(default_factory=dict)
    impersonate: str = "chrome"


def _parse_price(text: str, regex: str) -> float | None:
    m = re.search(regex, text.replace("\xa0", " "))
    if not m:
        return None
    raw = m.group().strip()
    # Normalise "1.234,56" (EU) vs "1,234.56" (UK) vs plain "29.60"
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        # Ambiguous: "29,60" (EU decimal) vs "1,234" (UK thousands). Treat as
        # decimal comma only when exactly 2 digits follow the last comma.
        if re.search(r",\d{2}$", raw):
            raw = raw.replace(",", ".")
        else:
            raw = raw.replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _fetch(url: str, cfg: SiteConfig, retries: int = 3) -> tuple[str | None, str | None]:
    last_err = None
    for attempt in range(retries):
        try:
            r = creq.get(url, headers=cfg.headers, impersonate=cfg.impersonate, timeout=25)
            if r.status_code == 200:
                return r.text, None
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
        if attempt < retries - 1:
            time.sleep(random.uniform(2, 5))
    print(f"    !! giving up on {url} ({last_err})")
    return None, last_err or "fetch failed"


def crawl_site(cfg: SiteConfig, on_product: Callable[[dict], None] | None = None) -> list[dict]:
    """Crawl all category URLs (+ pagination) for a site, return list of product dicts."""
    products: list[dict] = []
    seen_urls: set[str] = set()

    for i, start_url in enumerate(cfg.category_urls):
        if i > 0:
            # 2026-07-10: this loop had no delay between category_urls at all — only
            # between next_page_selector hops within one URL. Harmless for a single
            # category page, but auto365_scraper.py now lists 21 page URLs directly
            # (site's "next" link isn't selector-distinguishable — see its comment),
            # which would have fired 21 requests back-to-back with zero pacing.
            time.sleep(random.uniform(1.5, 3.0))
        url = start_url
        for page in range(1, cfg.max_pages + 1):
            print(f"  [{cfg.site}] page {page}: {url}")
            html, fetch_err = _fetch(url, cfg)
            if html is None:
                products.append(
                    {
                        "Country": cfg.country,
                        "Site": cfg.site,
                        "PMS_Category": "",
                        "Product_Name": "",
                        "Price": "",
                        "Currency": cfg.currency,
                        "Price_EUR": "",
                        "Product_URL": url,
                        "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "scrape_error": fetch_err or "fetch failed",
                        "Status": "error",
                    }
                )
                break
            soup = BeautifulSoup(html, "html.parser")

            links = soup.select(cfg.product_link_selector)
            if not links:
                break

            # Bug fixed 2026-07-09: product grids commonly wrap ONE product in
            # MULTIPLE <a> tags sharing the same href (image link, title link,
            # "view details" link) — only some of them contain the title text.
            # Grouping by href first and pulling the best name/price from
            # anywhere in the group fixed a "0 products found" bug that hit
            # every site (was only ever inspecting the first, usually
            # text-less, <a> per product).
            by_href: dict[str, list] = {}
            for a in links:
                href = a.get("href") or ""
                if not href:
                    continue
                full_url = href if href.startswith("http") else _urljoin(url, href)
                by_href.setdefault(full_url, []).append(a)

            for full_url, elements in by_href.items():
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                price_el = None
                for a in elements:
                    card = a
                    for _ in range(5):
                        price_el = card.select_one(cfg.price_selector)
                        if price_el is not None:
                            break
                        if card.parent is None:
                            break
                        card = card.parent
                    if price_el is not None:
                        break
                if price_el is None:
                    continue
                price = _parse_price(price_el.get_text(" ", strip=True), cfg.price_regex)
                if price is None or price <= 0:
                    continue

                name = ""
                for a in elements:
                    name = a.get_text(" ", strip=True) or a.get("title", "") or ""
                    if name:
                        break
                if not name:
                    continue

                row = {
                    "Country": cfg.country,
                    "Site": cfg.site,
                    "PMS_Category": classify_pms_category(name) or "",
                    "Product_Name": name[:120],
                    "Price": price,
                    "Currency": cfg.currency,
                    "Price_EUR": round(price * cfg.fx_to_eur, 2),
                    "Product_URL": full_url,
                    "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "scrape_error": "",
                    "Status": "ok",
                }
                products.append(row)
                if on_product:
                    on_product(row)

            next_el = soup.select_one(cfg.next_page_selector) if cfg.next_page_selector else None
            if not next_el or not next_el.get("href"):
                break
            url = _urljoin(url, next_el["href"])
            time.sleep(random.uniform(1.5, 3.0))

    return products


def _urljoin(base: str, href: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, href)


def write_products_csv(path: Path, products: list[dict]) -> None:
    import csv
    fields = ["Country", "Site", "PMS_Category", "Product_Name", "Price", "Currency",
              "Price_EUR", "Product_URL", "Scraped_At", "scrape_error", "Status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in products:
            w.writerow({k: row.get(k, "") for k in fields})


def summarise_by_category(products: list[dict]) -> list[dict]:
    """One row per (Site, PMS_Category) with min/avg/count — the category-level benchmark."""
    from collections import defaultdict
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for p in products:
        if p.get("scrape_error"):
            continue
        if not p.get("PMS_Category"):
            continue
        try:
            price = float(p["Price_EUR"])
        except (TypeError, ValueError, KeyError):
            continue
        groups[(p["Site"], p["PMS_Category"])].append(price)
    out = []
    for (site, cat), prices in sorted(groups.items()):
        out.append({
            "Site": site,
            "PMS_Category": cat,
            "N": len(prices),
            "Min_EUR": round(min(prices), 2),
            "Avg_EUR": round(sum(prices) / len(prices), 2),
        })
    return out
