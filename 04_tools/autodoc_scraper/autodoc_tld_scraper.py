"""
ISZE — Autodoc DE / EU / FR price scraper (EUR, Playwright)
============================================================================
Output:
  autodoc_fr_results.csv  (--tld fr)  ← USE THIS for EUR prices (replaces broken eu/de)
  autodoc_de_results.csv  (--tld de)  ← unreliable: 404s + bot detection
  autodoc_eu_results.csv  (--tld eu)  ← broken: country selector wall

Fix history (2026-05-30):
  - Added --tld fr (autodoc.fr) — French EUR store, no country selector, working
  - EU was showing country selector page for every PN → 0 results
  - DE was returning 404 for /spares-search?keyword= URL format
  - Added browser page crash recovery (recreates page on context error)
  - Added --force flag to delete CSV and re-scrape from scratch

Usage:
    python autodoc_tld_scraper.py --tld fr --top 200
    python autodoc_tld_scraper.py --tld fr --top 200 --force
    python autodoc_tld_scraper.py --tld de --top 200 --retry-errors
"""

from __future__ import annotations

import argparse
import csv
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

from _shared.scraper_io import IncrementalCsvWriter

TLD_MAP = {
    "fr": (
        "fr",
        "autodoc_fr_results.csv",
        "https://www.autodoc.fr/spares-search?keyword={pn}",
        "fr-FR",
        "Europe/Paris",
    ),
    "de": (
        "de",
        "autodoc_de_results.csv",
        "https://www.autodoc.de/spares-search?keyword={pn}",
        "de-DE",
        "Europe/Berlin",
    ),
    "eu": (
        "eu",
        "autodoc_eu_results.csv",
        "https://www.autodoc.eu/spares-search?keyword={pn}",
        "en-GB",
        "Europe/London",
    ),
}

CSV_FIELDS = [
    "PN",
    "Description",
    "PR00_EUR",
    "Rev_CY2025_EUR",
    "Autodoc_ResultCount",
    "Autodoc_MinPrice_EUR",
    "Autodoc_AvgPrice_EUR",
    "Autodoc_AllPrices_EUR",
    "Autodoc_CheapestBrand",
    "Autodoc_AllBrands",
    "Autodoc_ProductURLs",
    "Autodoc_URL",
    "Scraped_At",
    "Status",
    "Notes",
]


def _make_writer(output_csv: Path) -> IncrementalCsvWriter:
    return IncrementalCsvWriter(
        output_csv,
        CSV_FIELDS,
        done_statuses=frozenset({"ok", "no_results"}),
    )


def load_top_pns(n: int):
    from scraper_pn_loader import load_top_pns as _load

    return _load(n)


def parse_page_text(page_text: str) -> dict:
    """Extract EUR prices and brands from Autodoc search page body text."""
    result_count = 0
    m = re.search(r"(\d+)\s+results?\s+found", page_text, re.I)
    if m:
        result_count = int(m.group(1))
    elif re.search(r"no results|0 results", page_text, re.I):
        return {"result_count": 0, "prices": [], "brands": [], "notes": "No results"}

    prices = []
    for match in re.finditer(r"([\d]+[,.][\d]{2})\s*€", page_text):
        try:
            v = float(match.group(1).replace(",", "."))
            if 2.5 <= v <= 8000:
                prices.append(v)
        except ValueError:
            pass
    if not prices:
        for match in re.finditer(r"€\s*([\d]+[,.][\d]{2})", page_text):
            try:
                v = float(match.group(1).replace(",", "."))
                if 2.5 <= v <= 8000:
                    prices.append(v)
            except ValueError:
                pass
    prices = sorted(set(prices))

    brand_matches = re.findall(
        r"(?:Manufacturer|Brand|Hersteller)\s*[:\-]\s*([A-Za-z0-9& /\-\.]+?)(?:\n|\r|$|,|\|)",
        page_text,
        re.I,
    )
    brands = []
    seen: set[str] = set()
    for b in brand_matches:
        b = b.strip()
        if b and b.upper() not in seen:
            seen.add(b.upper())
            brands.append(b)

    return {
        "result_count": result_count,
        "prices": prices,
        "brands": brands,
        "notes": "",
    }


def _rows_to_scrape(
    writer: IncrementalCsvWriter, pn_df, retry_errors: bool
) -> list[dict]:
    if not retry_errors or not writer.path.is_file():
        pending = pn_df[~pn_df["PN"].isin(writer.done_keys())]
        return pending.to_dict("records")

    error_pns: set[str] = set()
    with writer.path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("Status") or "").lower() == "error":
                error_pns.add(row.get("PN", ""))
    if not error_pns:
        return []
    subset = pn_df[pn_df["PN"].isin(error_pns)]
    return subset.to_dict("records")


def run(
    tld: str,
    top_n: int,
    delay_min: float,
    delay_max: float,
    *,
    headless: bool = True,
    retry_errors: bool = False,
    force: bool = False,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
        from playwright.sync_api import TimeoutError as PwTimeout
    except ImportError:
        sys.exit("pip install playwright && playwright install chromium")

    if tld not in TLD_MAP:
        sys.exit(f"Unknown tld {tld}; use: {', '.join(TLD_MAP)}")
    _, outfile_name, url_tpl, locale, tz = TLD_MAP[tld]
    output_csv = SCRIPT_DIR / outfile_name
    writer = _make_writer(output_csv)

    if force:
        writer.delete_file()
        print(f"[--force] Deleted {output_csv.name} — scraping from scratch", flush=True)

    pn_df = load_top_pns(top_n)
    if retry_errors:
        retry_set = {r["PN"] for r in _rows_to_scrape(writer, pn_df, True)}
        writer.remove_keys(retry_set)
        pending_records = _rows_to_scrape(writer, pn_df, True)
    else:
        pending_records = _rows_to_scrape(writer, pn_df, False)

    writer.ensure_header()

    if not pending_records:
        print(f"Nothing to scrape for {tld.upper()} -> {output_csv.name}", flush=True)
        return

    print(
        f"Autodoc {tld.upper()}: {len(pending_records)} PNs "
        f"(headless={headless}, delay {delay_min}-{delay_max}s)",
        flush=True,
    )

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
            locale=locale,
            timezone_id=tz,
        )
        context.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}",
            lambda r: r.abort(),
        )
        def new_page():
            p = context.new_page()
            p.set_default_timeout(30_000)
            return p

        page = new_page()

        total = len(pending_records)
        for i, row in enumerate(pending_records, 1):
            pn = row["PN"]
            url = url_tpl.format(pn=pn)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{i}/{total}] {tld.upper()} {pn}", flush=True)

            out = {f: "" for f in CSV_FIELDS}
            out.update(
                {
                    "PN": pn,
                    "Description": row.get("Description", ""),
                    "PR00_EUR": row.get("PR00_EUR", ""),
                    "Rev_CY2025_EUR": row.get("Rev_CY2025_EUR", ""),
                    "Autodoc_URL": url,
                    "Scraped_At": ts,
                    "Status": "error",
                }
            )
            try:
                # Recreate page if it was closed by a previous crash
                try:
                    page.title()  # cheap liveness check
                except Exception:
                    print("    [page crashed — recreating]", flush=True)
                    page = new_page()

                page.goto(url, wait_until="domcontentloaded", timeout=30_000)

                # Check for country selector (autodoc.eu problem) — click first country or skip
                body_quick = page.inner_text("body")[:500]
                if "PLEASE SELECT YOUR COUNTRY" in body_quick or "SELECTIONNER VOTRE PAYS" in body_quick:
                    print("    [country selector detected — skipping]", flush=True)
                    out["Status"] = "no_results"
                    out["Notes"] = "country_selector_wall"
                    writer.append(out)
                    time.sleep(random.uniform(delay_min, delay_max))
                    continue

                # Check for 404
                if "404" in page.title() or "nicht gefunden" in body_quick.lower() or "page not found" in body_quick.lower():
                    print("    -> 404 (URL format broken for this TLD)", flush=True)
                    out["Status"] = "no_results"
                    out["Notes"] = "404"
                    writer.append(out)
                    time.sleep(random.uniform(delay_min, delay_max))
                    continue

                try:
                    page.wait_for_selector(
                        "text=/results found|no results|Ergebnisse|résultats/i",
                        timeout=12_000,
                    )
                except PwTimeout:
                    pass
                parsed = parse_page_text(page.inner_text("body"))
                prices = parsed["prices"]
                out["Autodoc_ResultCount"] = parsed["result_count"] or len(prices)
                if prices:
                    out["Autodoc_MinPrice_EUR"] = min(prices)
                    out["Autodoc_AvgPrice_EUR"] = round(sum(prices) / len(prices), 2)
                    out["Autodoc_AllPrices_EUR"] = "|".join(str(p) for p in prices[:20])
                if parsed["brands"]:
                    out["Autodoc_CheapestBrand"] = parsed["brands"][0]
                    out["Autodoc_AllBrands"] = "|".join(parsed["brands"])
                out["Status"] = "ok" if prices or parsed["result_count"] else "no_results"
                out["Notes"] = parsed.get("notes", "")
                print(
                    f"    -> {out['Status']} count={out['Autodoc_ResultCount']} "
                    f"min EUR={out['Autodoc_MinPrice_EUR'] or '-'}",
                    flush=True,
                )
            except PwTimeout:
                out["Status"] = "timeout"
                out["Notes"] = "Page load timeout"
                print("    -> timeout", flush=True)
            except Exception as exc:
                err_msg = str(exc)
                out["Notes"] = err_msg[:200]
                # If the page context was closed by the site, recreate it next iteration
                if "closed" in err_msg.lower() or "target" in err_msg.lower():
                    print(f"    -> page context error (will recreate): {err_msg[:80]}", flush=True)
                    try:
                        page.close()
                    except Exception:
                        pass
                    page = new_page()
                else:
                    print(f"    -> error: {out['Notes']}", flush=True)

            writer.append(out)
            time.sleep(random.uniform(delay_min, delay_max))

        browser.close()

    print(f"Done -> {output_csv}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tld", choices=list(TLD_MAP), default="fr")
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--delay", nargs=2, type=float, default=(2.0, 5.0))
    ap.add_argument("--headless", action="store_true", default=True)
    ap.add_argument("--visible", action="store_true", help="Show browser window")
    ap.add_argument(
        "--retry-errors",
        action="store_true",
        help="Re-scrape rows that failed (e.g. HTTP 403)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Delete existing CSV and re-scrape from scratch",
    )
    args = ap.parse_args()
    run(
        args.tld,
        args.top,
        args.delay[0],
        args.delay[1],
        headless=not args.visible,
        retry_errors=args.retry_errors,
        force=args.force,
    )


if __name__ == "__main__":
    main()
