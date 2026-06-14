"""
ISZE — Autodoc UK Cross-Reference Extractor
============================================
Reads autodoc_results.csv (Status == "ok" rows) and for each ISZE PN visits
the Autodoc UK product search page to extract:
  - OE / OEM reference numbers
  - Aftermarket brand part numbers (e.g. "RIDEX 82B0013")
  - Product detail page URLs

Output: autodoc_crossrefs.csv (incremental — safe to re-run)

Fields: ISZE_PN, Description, PR00_EUR, Autodoc_ProductURL,
        OE_Refs, Brand_PNs, Brand, Scraped_At

Usage:
    python autodoc_crossref_scraper.py [--delay MIN MAX] [--headless]
"""

from __future__ import annotations

import argparse
import csv
import re
import random
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent
_TOOLS = SCRIPT_DIR.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.scraper_io import IncrementalCsvWriter
INPUT_CSV   = SCRIPT_DIR / "autodoc_results.csv"
OUTPUT_CSV  = SCRIPT_DIR / "autodoc_crossrefs.csv"
BASE_URL    = "https://www.autodoc.co.uk/spares-search?keyword={pn}"

CSV_FIELDS = [
    "ISZE_PN", "Description", "PR00_EUR",
    "Autodoc_ProductURL",
    "OE_Refs", "Brand_PNs", "Brand",
    "Scraped_At",
]

# Patterns to detect OE numbers from page text blocks
OE_LABEL_RE  = re.compile(
    r"(?:OE[M]?|Original(?:\s+Equipment)?|OE\s+Number|OE\s+Ref)[^\w]*[:\-]?\s*([\w\-\s,;/]+)",
    re.IGNORECASE,
)
# Standalone part-number-like tokens: 6-14 alphanumeric chars, not pure words
PN_TOKEN_RE  = re.compile(r"\b([A-Z0-9][A-Z0-9\-]{5,13})\b")
# Brand+PN patterns e.g. "RIDEX 82B0013" or "FEBI BILSTEIN 12345"
BRAND_PN_RE  = re.compile(
    r"\b([A-Z][A-Z &]+?)\s+([A-Z0-9][A-Z0-9\-]{4,})\b"
)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def load_ok_rows() -> list[dict]:
    if not INPUT_CSV.exists():
        sys.exit(f"Input file not found: {INPUT_CSV}")
    rows = []
    with INPUT_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("Status") or "").strip().lower() == "ok":
                rows.append(row)
    return rows


def _make_writer() -> IncrementalCsvWriter:
    return IncrementalCsvWriter(
        OUTPUT_CSV,
        CSV_FIELDS,
        key_field="ISZE_PN",
        done_statuses=None,
    )


# ─── OE extraction from page text ─────────────────────────────────────────────

def extract_oe_refs(page_text: str, isze_pn: str) -> list[str]:
    """
    Pull OE/OEM reference numbers from page body text.
    Strategy:
      1. Text after OE/OEM labels
      2. data-original-oe / .oe-number style content (already in innerText)
      3. Standalone part-number tokens that differ from ISZE PN
    """
    candidates: set[str] = set()

    # Strategy 1 — text after OE label
    for m in OE_LABEL_RE.finditer(page_text):
        raw = m.group(1)
        # Split on common delimiters
        for tok in re.split(r"[,;\s]+", raw):
            tok = tok.strip().upper()
            if tok and re.match(r"[A-Z0-9]{6,}", tok):
                candidates.add(tok)

    # Strategy 2 — look for blocks that follow "OE:" or "OEM:" in condensed text
    for m in re.finditer(r"(?:OE|OEM)\s*:\s*([^\n\r]{5,60})", page_text, re.I):
        raw = m.group(1)
        for tok in re.split(r"[,;\s|]+", raw):
            tok = tok.strip().upper()
            if tok and re.match(r"[A-Z0-9\-]{5,}", tok):
                candidates.add(tok)

    # Remove the ISZE PN itself and trivial tokens
    candidates.discard(isze_pn.upper())
    candidates.discard("")

    # Filter: must look like a real PN (mix of digits and letters, or all-digit 7+)
    valid = []
    for c in sorted(candidates):
        if re.match(r"^\d{7,}$", c) or re.match(r"^[A-Z0-9][A-Z0-9\-]{5,}$", c):
            valid.append(c)
    return valid[:30]  # cap at 30


def extract_brand_pns(page_text: str, isze_pn: str) -> tuple[list[str], list[str]]:
    """
    Return (brand_pns_list, brands_list).
    brand_pns = "RIDEX|82B0013" style pairs encoded as "BRAND PN"
    """
    pairs: list[str] = []
    brands: list[str] = []
    seen_pairs: set[str] = set()
    seen_brands: set[str] = set()

    # Look for Manufacturer/Brand label lines
    mfr_re = re.compile(
        r"(?:Manufacturer|Brand)\s*[:\-]\s*([A-Za-z0-9& /\-\.]+?)(?:\n|\r|$|,|\|)",
        re.I
    )
    for m in mfr_re.finditer(page_text):
        brand = m.group(1).strip()
        if brand and brand.upper() not in seen_brands:
            seen_brands.add(brand.upper())
            brands.append(brand)

    # Look for "BRAND PARTNUMBER" patterns in the text
    for m in BRAND_PN_RE.finditer(page_text):
        brand_tok = m.group(1).strip()
        pn_tok    = m.group(2).strip().upper()
        # Skip if looks like a sentence fragment rather than a PN
        if len(brand_tok) < 2 or len(brand_tok) > 30:
            continue
        if not re.search(r"\d", pn_tok):  # PNs usually have digits
            continue
        pair = f"{brand_tok} {pn_tok}"
        if pair not in seen_pairs and pn_tok != isze_pn.upper():
            seen_pairs.add(pair)
            pairs.append(pair)
            if brand_tok.upper() not in seen_brands:
                seen_brands.add(brand_tok.upper())
                brands.append(brand_tok)

    return pairs[:40], brands[:20]


def extract_product_urls(page) -> list[str]:
    """Try several selector strategies to get product detail URLs."""
    urls: list[str] = []
    try:
        # Common Autodoc product card selectors
        for selector in [
            "a.product-card__link",
            "a.listing__item-link",
            "a[href*='/spare-parts/']",
            "a[href*='/car-parts/']",
            ".product-item a",
            "article a",
        ]:
            els = page.query_selector_all(selector)
            for el in els:
                href = el.get_attribute("href") or ""
                if href and href not in urls:
                    if href.startswith("http"):
                        urls.append(href)
                    elif href.startswith("/"):
                        urls.append("https://www.autodoc.co.uk" + href)
            if urls:
                break
    except Exception:
        pass
    return urls[:10]


# ─── Main ──────────────────────────────────────────────────────────────────────

def run(delay_min: float, delay_max: float, headless: bool) -> None:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        sys.exit("pip install playwright && playwright install chromium")

    ok_rows = load_ok_rows()
    writer  = _make_writer()
    done    = writer.done_keys()
    pending = [r for r in ok_rows if r.get("PN", "") not in done]

    print(f"ok rows: {len(ok_rows)}  |  already done: {len(done)}  |  pending: {len(pending)}")
    writer.ensure_header()

    if not pending:
        print("All ok-rows already processed. Delete autodoc_crossrefs.csv to restart.")
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-GB",
            timezone_id="Europe/London",
        )
        context.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}",
            lambda r: r.abort(),
        )
        page = context.new_page()
        page.set_default_timeout(30_000)

        total  = len(pending)
        errors = 0

        for i, row in enumerate(pending, 1):
            pn  = row.get("PN", "").strip()
            url = BASE_URL.format(pn=pn)
            ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"[{i:>3}/{total}] {pn}  ({row.get('Description', '')[:45]}) ...", end=" ", flush=True)

            out = {
                "ISZE_PN":           pn,
                "Description":       row.get("Description", ""),
                "PR00_EUR":          row.get("PR00_EUR", ""),
                "Autodoc_ProductURL": url,
                "OE_Refs":           "",
                "Brand_PNs":         "",
                "Brand":             "",
                "Scraped_At":        ts,
            }

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                try:
                    page.wait_for_selector(
                        "text=/results found|no results/i",
                        timeout=12_000,
                    )
                except PwTimeout:
                    pass

                # Try JS evaluation first for richer text
                try:
                    page_text = page.evaluate("() => document.body.innerText")
                except Exception:
                    page_text = page.inner_text("body")

                oe_refs = extract_oe_refs(page_text, pn)
                brand_pns, brands = extract_brand_pns(page_text, pn)
                product_urls = extract_product_urls(page)

                # If we got product URLs, use first as the canonical product URL
                if product_urls:
                    out["Autodoc_ProductURL"] = product_urls[0]

                out["OE_Refs"]   = "|".join(oe_refs)
                out["Brand_PNs"] = "|".join(brand_pns)
                out["Brand"]     = brands[0] if brands else ""

                print(
                    f"OE={len(oe_refs)}  brand_pns={len(brand_pns)}  "
                    f"brands={len(brands)}"
                )

            except PwTimeout:
                out["Brand"] = "TIMEOUT"
                errors += 1
                print("timeout")

            except Exception as exc:
                out["Brand"] = "ERROR"
                errors += 1
                print(f"ERROR: {str(exc)[:80]}")

            writer.append(out)

            if i % 20 == 0:
                print(f"\n-- Progress {i}/{total} ({i/total*100:.0f}%)  errors={errors} --\n")

            if i < total:
                time.sleep(random.uniform(delay_min, delay_max))

        browser.close()

    print(f"\nDone. {total} PNs processed ({errors} errors).")
    print(f"Output: {OUTPUT_CSV}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract OE cross-refs from Autodoc UK product pages")
    ap.add_argument("--delay",    nargs=2, type=float, default=[3.0, 7.0],
                    metavar=("MIN", "MAX"))
    ap.add_argument("--headless", action="store_true",
                    help="Run headless (faster, higher bot detection risk)")
    args = ap.parse_args()

    print("=" * 60)
    print("  ISZE Autodoc Cross-Reference Extractor")
    print(f"  delay {args.delay[0]}-{args.delay[1]}s | "
          f"{'headless' if args.headless else 'visible browser'}")
    print("=" * 60 + "\n")

    run(delay_min=args.delay[0], delay_max=args.delay[1], headless=args.headless)


if __name__ == "__main__":
    main()
