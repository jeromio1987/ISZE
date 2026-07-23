"""
ISZE — Autodoc Competitive Price Scraper
=========================================
Fetches aftermarket competitor prices from Autodoc UK for top PNs by CY2025 revenue.
Output: autodoc_results.csv  (incremental — safe to re-run, resumes where it left off)

Usage:
    python autodoc_scraper.py [--top N] [--delay MIN MAX] [--headless]

Arguments:
    --top N         Number of top PNs by CY2025 revenue to scrape (default: 300)
    --delay MIN MAX Random delay in seconds between requests (default: 3 7)
    --headless      Run browser in headless mode (default: visible, safer vs bot detection)

Requirements:
    pip install playwright pandas openpyxl
    playwright install chromium
"""

import argparse
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
_TOOLS = SCRIPT_DIR.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from scraper_pn_loader import load_top_pns
from _shared.scraper_io import IncrementalCsvWriter

# ─── Config ────────────────────────────────────────────────────────────────────

OUTPUT_CSV = SCRIPT_DIR / "autodoc_results.csv"
PROGRESS_CSV = SCRIPT_DIR / "autodoc_progress.csv"   # tracks which PNs attempted
BASE_URL = "https://www.autodoc.co.uk/spares-search?keyword={pn}"

AUTODOC_FIELDS = [
    "PN", "Description", "PR00_EUR", "Rev_CY2025_EUR", "Qty_CY2025",
    "Source", "Class", "AIM_Category",
    "Autodoc_ResultCount", "Autodoc_MinPrice_GBP",
    "Autodoc_AvgPrice_GBP", "Autodoc_MaxPrice_GBP",
    "Autodoc_CheapestBrand", "Autodoc_AllBrands",
    "Autodoc_AllPrices_GBP",
    "Autodoc_ProductURLs",
    "Autodoc_URL", "Scraped_At", "Status", "Notes",
]


def _make_writer() -> IncrementalCsvWriter:
    return IncrementalCsvWriter(
        OUTPUT_CSV,
        AUTODOC_FIELDS,
        done_statuses=frozenset({"ok", "no_results"}),
    )


# ─── Parsing ───────────────────────────────────────────────────────────────────

def parse_autodoc_page(page_text: str) -> dict:
    """
    Extract competitive data from Autodoc page text.

    Page structure observed:
      - "24 results found for 8982705240" → result count
      - "Our price: £2.59" patterns → prices
      - "Manufacturer: RIDEX" patterns → brands

    Returns dict with keys: result_count, prices, brands, notes
    """
    result = {
        "result_count": 0,
        "prices": [],
        "brands": [],
        "notes": "",
    }

    # Result count
    m = re.search(r"(\d+)\s+results?\s+found", page_text, re.IGNORECASE)
    if m:
        result["result_count"] = int(m.group(1))
    elif re.search(r"no results|0 results", page_text, re.IGNORECASE):
        result["result_count"] = 0
        result["notes"] = "No results"
        return result

    # Prices — "Our price: £X.XX" or "£X.XX" near price-like context
    price_matches = re.findall(r"£\s*([\d,]+\.?\d*)", page_text)
    prices = []
    for p in price_matches:
        try:
            v = float(p.replace(",", ""))
            if 0.5 <= v <= 5000:   # sanity range — ignore postage / page artefacts
                prices.append(v)
        except ValueError:
            pass
    result["prices"] = sorted(set(prices))   # deduplicate

    # Brands — "Manufacturer: BRANDNAME" or "Brand: BRANDNAME"
    brand_matches = re.findall(
        r"(?:Manufacturer|Brand)\s*[:\-]\s*([A-Za-z0-9& /\-\.]+?)(?:\n|\r|$|,|\|)",
        page_text, re.IGNORECASE
    )
    brands = [b.strip() for b in brand_matches if b.strip()]
    # Deduplicate preserving order
    seen = set()
    unique_brands = []
    for b in brands:
        if b.upper() not in seen:
            seen.add(b.upper())
            unique_brands.append(b)
    result["brands"] = unique_brands

    return result


# ─── Main scraper ──────────────────────────────────────────────────────────────

def run_scraper(top_n: int, delay_min: float, delay_max: float, headless: bool, force: bool = False):
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        sys.exit("❌  playwright not installed. Run: pip install playwright && playwright install chromium")

    writer = _make_writer()
    if force:
        writer.delete_file()
        print("🗑  [--force] Deleted autodoc_results.csv — scraping from scratch")

    pn_df = load_top_pns(top_n, extra_columns=True)
    done = writer.done_keys()
    pending = pn_df[~pn_df["PN"].isin(done)]

    print(f"\n📋  {len(done)} PNs already scraped → {len(pending)} remaining")
    writer.ensure_header()

    if pending.empty:
        print("✅  All PNs already scraped. Use --force to re-scrape from scratch.")
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-GB",
            timezone_id="Europe/London",
        )
        # Block image/font requests to speed up loading
        context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}", lambda r: r.abort())

        page = context.new_page()
        page.set_default_timeout(30_000)

        total  = len(pending)
        errors = 0

        for i, (_, row) in enumerate(pending.iterrows(), 1):
            pn  = row["PN"]
            url = BASE_URL.format(pn=pn)
            ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"[{i:>3}/{total}] {pn}  ({row.get('Description', '')[:40]})  …", end=" ", flush=True)

            out = {
                "PN":               pn,
                "Description":      row.get("Description", ""),
                "PR00_EUR":         row.get("PR00_EUR", ""),
                "Rev_CY2025_EUR":   row.get("Rev_CY2025_EUR", ""),
                "Qty_CY2025":       row.get("Qty_CY2025", ""),
                "Source":           row.get("Source", ""),
                "Class":            row.get("Class", ""),
                "AIM_Category":     row.get("AIM_Category", ""),
                "Autodoc_URL":      url,
                "Scraped_At":       ts,
                "Autodoc_ResultCount":  0,
                "Autodoc_MinPrice_GBP": "",
                "Autodoc_AvgPrice_GBP": "",
                "Autodoc_MaxPrice_GBP": "",
                "Autodoc_CheapestBrand": "",
                "Autodoc_AllBrands":    "",
                "Autodoc_AllPrices_GBP": "",
                "Status":           "error",
                "Notes":            "",
            }

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                # Wait for either results or "no results" message
                try:
                    page.wait_for_selector(
                        "text=/results found|no results/i",
                        timeout=12_000
                    )
                except PwTimeout:
                    pass  # Continue anyway — grab what's there

                page_text = page.inner_text("body")
                parsed    = parse_autodoc_page(page_text)

                out["Autodoc_ResultCount"] = parsed["result_count"]
                out["Notes"]               = parsed.get("notes", "")

                if parsed["result_count"] > 0 and parsed["prices"]:
                    prices = parsed["prices"]
                    out["Autodoc_MinPrice_GBP"] = min(prices)
                    out["Autodoc_AvgPrice_GBP"] = round(sum(prices) / len(prices), 2)
                    out["Autodoc_MaxPrice_GBP"] = max(prices)
                    out["Autodoc_AllPrices_GBP"] = "|".join(f"{p:.2f}" for p in prices)

                    # Cheapest brand — find brand name appearing near minimum price
                    # Try to pair from page text; if not found, use first brand
                    brands = parsed["brands"]
                    if brands:
                        out["Autodoc_CheapestBrand"] = brands[0]   # first brand = typically cheapest (page sorted by price)
                        out["Autodoc_AllBrands"] = "|".join(brands)
                out["Autodoc_ProductURLs"] = out.get("Autodoc_URL", "")

                out["Status"] = "ok" if parsed["result_count"] > 0 else "no_results"
                print(f"✅  {parsed['result_count']} results  min £{out['Autodoc_MinPrice_GBP'] or '—'}")

            except PwTimeout:
                out["Status"] = "timeout"
                out["Notes"]  = "Page load timeout"
                errors += 1
                print("⏱  timeout")

            except Exception as e:
                out["Status"] = "error"
                out["Notes"]  = str(e)[:120]
                errors += 1
                print(f"❌  {e}")

            writer.append(out)

            # Progress heartbeat every 25 PNs
            if i % 25 == 0:
                done_now = i + len(done)
                total_all = len(pn_df)
                pct = done_now / total_all * 100
                print(f"\n── Progress: {done_now}/{total_all} ({pct:.0f}%)  errors so far: {errors} ──\n")

            # Rate limiting — random delay
            if i < total:
                delay = random.uniform(delay_min, delay_max)
                time.sleep(delay)

        browser.close()

    print(f"\n{'='*60}")
    print(f"✅  Done!  Scraped {total} PNs  ({errors} errors)")
    print(f"📄  Results: {OUTPUT_CSV}")
    print(f"{'='*60}")


# ─── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Autodoc competitive price scraper for ISZE PNs"
    )
    parser.add_argument("--top",      type=int,   default=300,  help="Top N PNs by CY2025 rev (default 300)")
    parser.add_argument("--delay",    type=float, nargs=2, default=[3, 7],
                        metavar=("MIN", "MAX"), help="Random delay range in seconds (default 3 7)")
    parser.add_argument("--headless", action="store_true",
                        help="Run headless (faster but higher bot detection risk)")
    parser.add_argument("--force", action="store_true",
                        help="Delete existing CSV and re-scrape all PNs from scratch")
    args = parser.parse_args()

    print("=" * 60)
    print("  ISZE Autodoc UK Competitive Price Scraper")
    print(f"  Top {args.top} PNs | delay {args.delay[0]}–{args.delay[1]}s | "
          f"{'headless' if args.headless else 'visible browser'}"
          + (" | FORCE re-scrape" if args.force else ""))
    print("=" * 60 + "\n")

    run_scraper(
        top_n=args.top,
        delay_min=args.delay[0],
        delay_max=args.delay[1],
        headless=args.headless,
        force=args.force,
    )
