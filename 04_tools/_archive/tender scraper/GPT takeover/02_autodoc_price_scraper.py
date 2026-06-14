"""
Autodoc IAM Price Scraper — ISZE / Isuzu Europe
Fetches competitor IAM prices for ~50 key parts across 5 markets.
Output: Excel + JSON for Power BI competitor price intelligence.

Markets: UK, Ireland, Portugal, Greece, Poland
Source: autodoc.co.uk / autodoc.ie / autodoc.pt / autodoc.gr / autodoc.pl

Usage:
    pip install requests beautifulsoup4 openpyxl --break-system-packages
    python 02_autodoc_price_scraper.py

Note on scraping: Autodoc uses dynamic rendering on some pages.
This script uses their search API endpoint where available,
and falls back to HTML parsing. If blocked, add rotating user-agents
or use a headless browser (playwright) — see comments at bottom.
"""

import json
import time
import datetime
import random
from dataclasses import dataclass, asdict
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Run: pip install requests beautifulsoup4 openpyxl --break-system-packages")
    exit()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# Market configs: country code, Autodoc domain, currency
MARKETS = {
    "GBR": {"domain": "autodoc.co.uk", "currency": "GBP", "locale": "en_GB"},
    "IRL": {"domain": "autodoc.ie",    "currency": "EUR", "locale": "en_IE"},
    "PRT": {"domain": "autodoc.pt",    "currency": "EUR", "locale": "pt_PT"},
    "GRC": {"domain": "autodoc.gr",    "currency": "EUR", "locale": "el_GR"},
    "POL": {"domain": "autodoc.pl",    "currency": "PLN", "locale": "pl_PL"},
}

# ── KEY PARTS LIST ──
# Format: {"oem_ref": "...", "description": "...", "category": "..."}
# OEM refs are Isuzu genuine part numbers — used to search IAM alternatives.
# Expand this list up to ~50 parts. Grouped by category for reporting.
KEY_PARTS = [
    # Engine
    {"oem_ref": "8980392190", "description": "Oil filter — 4JJ1 engine",        "category": "Engine"},
    {"oem_ref": "8971328760", "description": "Air filter — N-series",             "category": "Engine"},
    {"oem_ref": "8981320490", "description": "Fuel filter — 4JJ1",                "category": "Engine"},
    {"oem_ref": "5878106830", "description": "Injector — 4HK1",                   "category": "Engine"},
    {"oem_ref": "8980038590", "description": "EGR valve — 4JJ1",                  "category": "Engine"},
    # Brakes
    {"oem_ref": "8971858401", "description": "Front brake pads — D-Max",         "category": "Brakes"},
    {"oem_ref": "8973554080", "description": "Rear brake shoes — D-Max",         "category": "Brakes"},
    {"oem_ref": "8971761340", "description": "Brake disc front — D-Max",         "category": "Brakes"},
    # Suspension
    {"oem_ref": "8970856090", "description": "Front shock absorber — D-Max",     "category": "Suspension"},
    {"oem_ref": "8970856080", "description": "Rear shock absorber — D-Max",      "category": "Suspension"},
    {"oem_ref": "8970990540", "description": "Front control arm — D-Max",        "category": "Suspension"},
    # Drivetrain
    {"oem_ref": "8970361730", "description": "Clutch kit — D-Max",               "category": "Drivetrain"},
    {"oem_ref": "8971520920", "description": "Drive shaft — D-Max front",        "category": "Drivetrain"},
    # Cooling
    {"oem_ref": "8970388580", "description": "Radiator — 4JJ1",                  "category": "Cooling"},
    {"oem_ref": "8971922480", "description": "Water pump — 4JJ1",                "category": "Cooling"},
    {"oem_ref": "5878107830", "description": "Thermostat — 4JJ1",                "category": "Cooling"},
    # Electrical
    {"oem_ref": "8971039380", "description": "Alternator — D-Max",               "category": "Electrical"},
    {"oem_ref": "8970921370", "description": "Starter motor — D-Max",            "category": "Electrical"},
    {"oem_ref": "8971866940", "description": "Glow plug — 4JJ1",                 "category": "Electrical"},
    # Tyres / wheels
    {"oem_ref": "8970777130", "description": "Wheel bearing front — D-Max",      "category": "Wheels"},
    # Fluids / service
    {"oem_ref": "5878106480", "description": "Timing belt kit — 4HK1",           "category": "Service"},
    # ── Add up to 50 parts ──
    # {"oem_ref": "XXXXXXXXX", "description": "...", "category": "..."},
]

# Delay between requests (seconds) — be polite
REQUEST_DELAY_MIN = 1.5
REQUEST_DELAY_MAX = 3.0

# Minimum results per part to consider reliable
MIN_RESULTS_THRESHOLD = 2

# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class PriceResult:
    oem_ref: str
    description: str
    category: str
    market: str
    currency: str
    brand: str
    iam_ref: str
    price: Optional[float]
    price_with_vat: Optional[float]
    unit: str
    availability: str
    url: str
    scraped_at: str
    error: Optional[str] = None


# ─────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────

HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
]


def get_headers():
    return random.choice(HEADERS_POOL)


def search_autodoc(oem_ref: str, market_config: dict) -> list[dict]:
    """
    Search Autodoc for IAM alternatives to an OEM part number.
    Returns list of raw product dicts.

    Autodoc's search URL pattern:
    https://{domain}/search/{oem_ref}
    or via their catalog search API.
    """
    domain = market_config["domain"]
    url = f"https://www.{domain}/search/{oem_ref}"

    try:
        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
        session = requests.Session()
        resp = session.get(url, headers=get_headers(), timeout=20, allow_redirects=True)

        if resp.status_code == 429:
            print(f"    Rate limited on {domain} — waiting 30s")
            time.sleep(30)
            resp = session.get(url, headers=get_headers(), timeout=20)

        if resp.status_code != 200:
            return [{"error": f"HTTP {resp.status_code}"}]

        return parse_autodoc_results(resp.text, domain, oem_ref)

    except requests.RequestException as e:
        return [{"error": str(e)}]


def parse_autodoc_results(html: str, domain: str, oem_ref: str) -> list[dict]:
    """
    Parse Autodoc search results page.
    Autodoc renders product cards with class patterns — these may change.
    Update selectors if Autodoc redesigns their frontend.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Try to find product listing cards
    # Autodoc uses multiple possible structures depending on search result type
    product_cards = (
        soup.select("div.product-card") or
        soup.select("article.product-item") or
        soup.select("div[data-product-id]") or
        soup.select("li.product") or
        []
    )

    if not product_cards:
        # Try JSON-LD structured data
        json_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_scripts:
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        product = item.get("item", {})
                        offer = product.get("offers", {})
                        results.append({
                            "brand": product.get("brand", {}).get("name", "Unknown"),
                            "iam_ref": product.get("sku", oem_ref),
                            "price": offer.get("price"),
                            "currency": offer.get("priceCurrency", ""),
                            "availability": offer.get("availability", ""),
                            "name": product.get("name", ""),
                            "url": product.get("url", f"https://www.{domain}/search/{oem_ref}"),
                        })
            except (json.JSONDecodeError, AttributeError):
                continue

    # Parse individual product cards
    for card in product_cards[:10]:  # cap at 10 per search
        try:
            brand_el = card.select_one("[class*='brand'], [class*='manufacturer'], .brand")
            price_el = card.select_one("[class*='price'], .price-value, [data-price]")
            sku_el = card.select_one("[class*='article'], [class*='sku'], [data-sku]")
            avail_el = card.select_one("[class*='availability'], [class*='stock']")
            link_el = card.select_one("a[href]")

            price_text = price_el.get_text(strip=True) if price_el else ""
            price_value = None
            if price_text:
                import re
                price_match = re.search(r"[\d,]+\.?\d*", price_text.replace(",", "."))
                if price_match:
                    price_value = float(price_match.group().replace(",", "."))

            results.append({
                "brand": brand_el.get_text(strip=True) if brand_el else "Unknown",
                "iam_ref": sku_el.get_text(strip=True) if sku_el else oem_ref,
                "price": price_value,
                "currency": "",  # parsed separately from context
                "availability": avail_el.get_text(strip=True) if avail_el else "Unknown",
                "name": "",
                "url": f"https://www.{domain}{link_el['href']}" if link_el else f"https://www.{domain}/search/{oem_ref}",
            })
        except Exception:
            continue

    return results if results else [{"error": "No products found — check selectors or verify part number"}]


# ─────────────────────────────────────────────
# MAIN SCRAPE LOOP
# ─────────────────────────────────────────────

def scrape_all() -> list[PriceResult]:
    all_results = []
    total = len(KEY_PARTS) * len(MARKETS)
    done = 0

    for part in KEY_PARTS:
        for country, market_cfg in MARKETS.items():
            done += 1
            print(f"  [{done}/{total}] {part['oem_ref']} — {part['description'][:40]} | {country}")

            raw_products = search_autodoc(part["oem_ref"], market_cfg)
            scraped_at = datetime.datetime.now().isoformat()

            if not raw_products or (len(raw_products) == 1 and raw_products[0].get("error")):
                error_msg = raw_products[0].get("error", "No results") if raw_products else "No results"
                all_results.append(PriceResult(
                    oem_ref=part["oem_ref"],
                    description=part["description"],
                    category=part["category"],
                    market=country,
                    currency=market_cfg["currency"],
                    brand="", iam_ref="", price=None, price_with_vat=None,
                    unit="each", availability="Unknown",
                    url=f"https://www.{market_cfg['domain']}/search/{part['oem_ref']}",
                    scraped_at=scraped_at, error=error_msg,
                ))
                continue

            for product in raw_products[:3]:  # top 3 results per part/market
                price = product.get("price")
                all_results.append(PriceResult(
                    oem_ref=part["oem_ref"],
                    description=part["description"],
                    category=part["category"],
                    market=country,
                    currency=market_cfg["currency"],
                    brand=product.get("brand", "Unknown"),
                    iam_ref=product.get("iam_ref", part["oem_ref"]),
                    price=price,
                    price_with_vat=round(price * 1.20, 2) if price else None,
                    unit="each",
                    availability=product.get("availability", "Unknown"),
                    url=product.get("url", ""),
                    scraped_at=scraped_at,
                    error=product.get("error"),
                ))

    return all_results


# ─────────────────────────────────────────────
# EXCEL EXPORT
# ─────────────────────────────────────────────

def _header_fill():
    return PatternFill("solid", fgColor="1F4E79")

def _subheader_fill():
    return PatternFill("solid", fgColor="2E75B6")

def _cat_fill():
    return PatternFill("solid", fgColor="D6E4F0")

def _border():
    thin = Side(style="thin", color="CCCCCC")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def export_excel(results: list[PriceResult], filepath: str):
    wb = openpyxl.Workbook()

    # ── Sheet 1: Raw data ──
    ws_raw = wb.active
    ws_raw.title = "Raw Data"

    headers = ["Category", "Description", "OEM Ref", "Market", "Currency",
               "Brand", "IAM Ref", "Price (ex VAT)", "Price (inc VAT)",
               "Availability", "URL", "Scraped At", "Error"]

    for col_idx, h in enumerate(headers, 1):
        cell = ws_raw.cell(row=1, column=col_idx, value=h)
        cell.font = Font(color="FFFFFF", bold=True, size=10)
        cell.fill = _header_fill()
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _border()

    ws_raw.row_dimensions[1].height = 18

    for row_idx, r in enumerate(results, 2):
        row_data = [
            r.category, r.description, r.oem_ref, r.market, r.currency,
            r.brand, r.iam_ref, r.price, r.price_with_vat,
            r.availability, r.url, r.scraped_at, r.error or ""
        ]
        for col_idx, value in enumerate(row_data, 1):
            cell = ws_raw.cell(row=row_idx, column=col_idx, value=value)
            cell.font = Font(size=10)
            cell.border = _border()
            if r.error:
                cell.fill = PatternFill("solid", fgColor="FFF2CC")

    # Auto-width columns
    col_widths = [12, 40, 16, 8, 10, 16, 16, 14, 14, 14, 40, 20, 25]
    for i, width in enumerate(col_widths, 1):
        ws_raw.column_dimensions[get_column_letter(i)].width = width

    ws_raw.freeze_panes = "A2"

    # ── Sheet 2: Price comparison pivot (market vs. category) ──
    ws_pivot = wb.create_sheet("Price by Market")

    # Build pivot: avg price per category per market
    from collections import defaultdict
    pivot = defaultdict(lambda: defaultdict(list))
    for r in results:
        if r.price and not r.error:
            pivot[r.category][r.market].append(r.price)

    markets = list(MARKETS.keys())
    categories = sorted(pivot.keys())

    # Header row
    ws_pivot.cell(1, 1, "Category").font = Font(bold=True, color="FFFFFF", size=10)
    ws_pivot.cell(1, 1).fill = _header_fill()
    for m_idx, market in enumerate(markets, 2):
        cell = ws_pivot.cell(1, m_idx, f"Avg Price ({MARKETS[market]['currency']})")
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = _header_fill()
        cell.alignment = Alignment(horizontal="center")

    ws_pivot.cell(1, len(markets) + 2, "Coverage %").font = Font(bold=True, color="FFFFFF", size=10)
    ws_pivot.cell(1, len(markets) + 2).fill = _header_fill()

    for row_idx, cat in enumerate(categories, 2):
        ws_pivot.cell(row_idx, 1, cat).font = Font(bold=True, size=10)
        ws_pivot.cell(row_idx, 1).fill = _cat_fill()

        covered = 0
        for m_idx, market in enumerate(markets, 2):
            prices = pivot[cat][market]
            if prices:
                avg = round(sum(prices) / len(prices), 2)
                ws_pivot.cell(row_idx, m_idx, avg).number_format = "#,##0.00"
                covered += 1
            else:
                ws_pivot.cell(row_idx, m_idx, "—")

        coverage_pct = round(covered / len(markets) * 100)
        ws_pivot.cell(row_idx, len(markets) + 2, f"{coverage_pct}%")

    for i in range(1, len(markets) + 3):
        ws_pivot.column_dimensions[get_column_letter(i)].width = 18

    ws_pivot.freeze_panes = "B2"

    # ── Sheet 3: Summary stats ──
    ws_summary = wb.create_sheet("Summary")
    total = len(results)
    with_price = sum(1 for r in results if r.price and not r.error)
    errors = sum(1 for r in results if r.error)

    summary_rows = [
        ("Scrape date", datetime.date.today().isoformat()),
        ("Total records", total),
        ("Records with price", with_price),
        ("Coverage %", f"{round(with_price / total * 100)}%" if total else "0%"),
        ("Errors / no result", errors),
        ("Parts scraped", len(KEY_PARTS)),
        ("Markets", len(MARKETS)),
    ]
    for row_idx, (label, value) in enumerate(summary_rows, 1):
        ws_summary.cell(row_idx, 1, label).font = Font(bold=True, size=10)
        ws_summary.cell(row_idx, 2, value).font = Font(size=10)

    ws_summary.column_dimensions["A"].width = 22
    ws_summary.column_dimensions["B"].width = 22

    wb.save(filepath)
    print(f"  Excel saved: {filepath}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("\nAutodoc IAM Price Scraper — ISZE")
    print(f"Parts: {len(KEY_PARTS)} | Markets: {list(MARKETS.keys())}\n")

    results = scrape_all()

    date_str = datetime.date.today().strftime("%Y%m%d")
    excel_path = f"autodoc_prices_{date_str}.xlsx"
    json_path = f"autodoc_prices_{date_str}.json"

    print("\nExporting results...")
    export_excel(results, excel_path)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
    print(f"  JSON saved: {json_path}")

    with_price = sum(1 for r in results if r.price and not r.error)
    print(f"\nDone. {with_price}/{len(results)} records with price data.")
    print("Next: load autodoc_prices_YYYYMMDD.json into Power BI for competitor price index.")


"""
── PLAYWRIGHT FALLBACK ──
If Autodoc blocks requests-based scraping (JavaScript-rendered content),
replace search_autodoc() with this:

    pip install playwright --break-system-packages
    playwright install chromium

    from playwright.sync_api import sync_playwright

    def search_autodoc_playwright(oem_ref, market_config):
        domain = market_config["domain"]
        url = f"https://www.{domain}/search/{oem_ref}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            html = page.content()
            browser.close()
        return parse_autodoc_results(html, domain, oem_ref)
"""

if __name__ == "__main__":
    main()
