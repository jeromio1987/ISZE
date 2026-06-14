"""
ISZE — Mister Auto FR price scraper (EUR)
Output: mister_auto_results.csv

Usage:
    python mister_auto_scraper.py --top 200
    python mister_auto_scraper.py --top 200 --visible
    python mister_auto_scraper.py --retry-errors
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

from scraper_pn_loader import load_top_pns
from _shared.scraper_io import IncrementalCsvWriter
OUTPUT_CSV = SCRIPT_DIR / "mister_auto_results.csv"
SEARCH_URL = "https://www.mister-auto.com/en/parts/search/?query={pn}"

CSV_FIELDS = [
    "PN",
    "Description",
    "PR00_EUR",
    "Rev_CY2025_EUR",
    "MA_ResultCount",
    "MA_AM_MinPrice_EUR",
    "MA_AM_AvgPrice_EUR",
    "MA_AM_Count",
    "MA_AM_Brands",
    "MA_URL",
    "Scraped_At",
    "Status",
    "Notes",
]


def _make_writer() -> IncrementalCsvWriter:
    return IncrementalCsvWriter(
        OUTPUT_CSV,
        CSV_FIELDS,
        done_statuses=frozenset({"ok", "no_results"}),
    )


def parse_page(text: str) -> dict:
    """Parse rendered page text from inner_text() — no HTML parsing needed."""
    prices = []
    # Match "12,99 €" or "12.99€" or "€ 12.99"
    for match in re.finditer(r"([\d]+[,.][\d]{2})\s*€", text):
        try:
            v = float(match.group(1).replace(",", "."))
            if 2.5 <= v <= 8000:
                prices.append(v)
        except ValueError:
            pass
    if not prices:
        for match in re.finditer(r"€\s*([\d]+[,.][\d]{2})", text):
            try:
                v = float(match.group(1).replace(",", "."))
                if 2.5 <= v <= 8000:
                    prices.append(v)
            except ValueError:
                pass
    prices = sorted(set(prices))
    brands = re.findall(
        r"(?:brand|marque|manufacturer|fabricant)\s*[:\-]?\s*([A-Za-z0-9& /\-\.]{2,40})",
        text,
        re.I,
    )
    brands = list(dict.fromkeys(b.strip() for b in brands if b.strip()))[:15]
    result_count = 0
    m = re.search(r"(\d+)\s+(?:results?|résultats?|produits?)", text, re.I)
    if m:
        result_count = int(m.group(1))
    elif prices:
        result_count = len(prices)
    return {"prices": prices, "brands": brands, "result_count": result_count}


def run(
    top_n: int,
    delay_min: float,
    delay_max: float,
    *,
    headless: bool = True,
    retry_errors: bool = False,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
        from playwright.sync_api import TimeoutError as PwTimeout
    except ImportError:
        sys.exit("pip install playwright && playwright install chromium")

    pn_df = load_top_pns(top_n)
    writer = _make_writer()

    if retry_errors:
        error_pns: set[str] = set()
        if writer.path.is_file():
            with writer.path.open(encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    if (row.get("Status") or "").lower() == "error":
                        error_pns.add(row.get("PN", ""))
        if not error_pns:
            print("No error rows to retry.", flush=True)
            return
        writer.remove_keys(error_pns)
        pending = pn_df[pn_df["PN"].isin(error_pns)]
    else:
        pending = pn_df[~pn_df["PN"].isin(writer.done_keys())]

    writer.ensure_header()

    if pending.empty:
        print(f"Nothing to scrape -> {OUTPUT_CSV.name}", flush=True)
        return

    print(
        f"Mister Auto: {len(pending)} PNs "
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
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="fr-FR",
            timezone_id="Europe/Paris",
        )
        # Note: do NOT block images — mister-auto uses lazy-loading that may tie to JS render
        page = context.new_page()
        page.set_default_timeout(35_000)

        total = len(pending)
        for i, (_, row) in enumerate(pending.iterrows(), 1):
            pn = row["PN"]
            url = SEARCH_URL.format(pn=pn)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{i}/{total}] MA {pn}", flush=True)
            out = {f: "" for f in CSV_FIELDS}
            out.update(
                {
                    "PN": pn,
                    "Description": row.get("Description", ""),
                    "PR00_EUR": row.get("PR00_EUR", ""),
                    "Rev_CY2025_EUR": row.get("Rev_CY2025_EUR", ""),
                    "MA_URL": url,
                    "Scraped_At": ts,
                    "Status": "error",
                }
            )
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=35_000)
                # Wait for network to settle (mister-auto is a React SPA)
                try:
                    page.wait_for_load_state("networkidle", timeout=12_000)
                except PwTimeout:
                    pass
                # Try to wait for product cards or "no results" text
                try:
                    page.wait_for_selector(
                        "[class*='product'], [class*='result'], text=/résultat|no result/i",
                        timeout=8_000,
                    )
                except PwTimeout:
                    pass
                # Use inner_text (rendered text), NOT page.content() which returns pre-JS HTML
                text = page.inner_text("body")
                parsed = parse_page(text)
                prices = parsed["prices"]
                out["MA_ResultCount"] = parsed["result_count"]
                out["MA_AM_Count"] = len(prices)
                if prices:
                    out["MA_AM_MinPrice_EUR"] = min(prices)
                    out["MA_AM_AvgPrice_EUR"] = round(sum(prices) / len(prices), 2)
                if parsed["brands"]:
                    out["MA_AM_Brands"] = "|".join(parsed["brands"])
                out["Status"] = "ok" if prices else "no_results"
                print(
                    f"    -> {out['Status']} count={out['MA_ResultCount']} "
                    f"min EUR={out['MA_AM_MinPrice_EUR'] or '-'}",
                    flush=True,
                )
            except PwTimeout:
                out["Status"] = "timeout"
                out["Notes"] = "timeout"
                print("    -> timeout", flush=True)
            except Exception as exc:
                out["Notes"] = str(exc)[:200]
                print(f"    -> error: {out['Notes']}", flush=True)

            writer.append(out)
            time.sleep(random.uniform(delay_min, delay_max))

        browser.close()

    print(f"Done -> {OUTPUT_CSV}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--delay", nargs=2, type=float, default=(2.0, 5.0))
    ap.add_argument("--headless", action="store_true", default=True)
    ap.add_argument("--visible", action="store_true", help="Show browser window")
    ap.add_argument(
        "--retry-errors",
        action="store_true",
        help="Re-scrape rows where Status=='error'",
    )
    args = ap.parse_args()
    run(
        args.top,
        args.delay[0],
        args.delay[1],
        headless=not args.visible,
        retry_errors=args.retry_errors,
    )


if __name__ == "__main__":
    main()
