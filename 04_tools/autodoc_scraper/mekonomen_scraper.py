"""
ISZE - Mekonomen Nordic price scraper (Sweden) - Playwright edition
====================================================================
Mekonomen is JS-rendered (Magento SPA), so plain requests returns empty HTML.
This version uses Playwright to render and extract.

Search: https://www.mekonomen.se/catalogsearch/result/?q={PN}
Output: mekonomen_results.csv (incremental, safe to re-run)

Usage:
    python mekonomen_scraper.py --top 300 --delay 1 3
    python mekonomen_scraper.py --top 300 --visible
    python mekonomen_scraper.py --retry-errors
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
OUTPUT_CSV = SCRIPT_DIR / "mekonomen_results.csv"
BASE_URL = "https://www.mekonomen.se/catalogsearch/result/?q={pn}"

CSV_FIELDS = [
    "PN",
    "Description",
    "PR00_EUR",
    "Rev_CY2025_EUR",
    "MEK_ResultCount",
    "MEK_AM_MinPrice_SEK",
    "MEK_AM_AvgPrice_SEK",
    "MEK_AM_Count",
    "MEK_AM_Brands",
    "MEK_AllProducts",
    "MEK_URL",
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


def parse_page_text(text: str) -> dict:
    """Extract result count, prices, brands from rendered Mekonomen page text.

    Page text pattern observed (PN 8975056801):
        Tillverkare
        Lesjofors
        (1)
        Active filtering
        Search result for "PN"
        Sortera efter:
        Relevans
        Lagsta pris
        1 Item
        <product name> <Brand>
        ...specs...
        <Brand>
        957 kr
    """
    out = {"result_count": 0, "prices": [], "brands": [], "products": []}

    m_count = re.search(r"(\d+)\s+Items?", text)
    if m_count:
        out["result_count"] = int(m_count.group(1))

    if "0 Items" in text or "Inga resultat" in text.lower() or "inga produkter" in text.lower():
        return out

    prices = []
    for m in re.finditer(r"([\d\s]+(?:[,.]\d{1,2})?)\s*kr\b", text):
        raw = m.group(1).replace(" ", "").replace("\xa0", "").replace(",", ".")
        try:
            v = float(raw)
            if 10 <= v <= 100_000:
                prices.append(v)
        except ValueError:
            pass
    out["prices"] = sorted(set(prices))

    brands = set()
    m_makers = re.search(r"Tillverkare\s*\n([\s\S]{1,400}?)(?:Active filtering|Sortera|Search result)", text, re.I)
    if m_makers:
        block = m_makers.group(1)
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"^\(\d+\)$", line):
                continue
            if line.lower() in {"tillverkare", "more"}:
                continue
            if re.search(r"[A-Za-z]", line) and len(line) <= 40:
                brands.add(line)

    out["brands"] = sorted(brands)

    if out["result_count"] == 0 and prices:
        out["result_count"] = len(prices)

    return out


def run(
    top_n: int,
    delay_min: float,
    delay_max: float,
    *,
    headless: bool = True,
    retry_errors: bool = False,
    force_rescrape: bool = False,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
        from playwright.sync_api import TimeoutError as PwTimeout
    except ImportError:
        sys.exit("pip install playwright && playwright install chromium")

    pn_df = load_top_pns(top_n)
    writer = _make_writer()

    if force_rescrape:
        writer.delete_file()

    if retry_errors:
        error_pns: set[str] = set()
        if writer.path.is_file():
            with writer.path.open(encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    if (row.get("Status") or "").lower() in ("error", "no_results"):
                        error_pns.add(row.get("PN", ""))
        if not error_pns:
            print("No errors/no_results rows to retry.", flush=True)
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
        f"Mekonomen: {len(pending)} PNs "
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
            locale="sv-SE",
            timezone_id="Europe/Stockholm",
        )
        context.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}",
            lambda r: r.abort(),
        )
        page = context.new_page()
        page.set_default_timeout(30_000)

        total = len(pending)
        for i, (_, row) in enumerate(pending.iterrows(), 1):
            pn = row["PN"]
            url = BASE_URL.format(pn=pn)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{i}/{total}] MEK {pn}", flush=True)
            out = {f: "" for f in CSV_FIELDS}
            out.update(
                {
                    "PN": pn,
                    "Description": row.get("Description", ""),
                    "PR00_EUR": row.get("PR00_EUR", ""),
                    "Rev_CY2025_EUR": row.get("Rev_CY2025_EUR", ""),
                    "MEK_URL": url,
                    "Scraped_At": ts,
                    "Status": "error",
                }
            )
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                try:
                    page.wait_for_load_state("networkidle", timeout=12_000)
                except PwTimeout:
                    pass
                # Wait for search result count text to confirm SPA has rendered
                try:
                    page.wait_for_selector(
                        "text=/\\d+ Items?|Inga resultat|inga produkter/i",
                        timeout=8_000,
                    )
                except PwTimeout:
                    pass  # still try to read — may have results without count
                time.sleep(1.0)
                text = page.inner_text("body")
                parsed = parse_page_text(text)
                prices = parsed["prices"]
                out["MEK_ResultCount"] = parsed["result_count"]
                out["MEK_AM_Count"] = len(prices)
                if prices:
                    out["MEK_AM_MinPrice_SEK"] = min(prices)
                    out["MEK_AM_AvgPrice_SEK"] = round(sum(prices) / len(prices), 2)
                if parsed["brands"]:
                    out["MEK_AM_Brands"] = "|".join(parsed["brands"])
                out["MEK_AllProducts"] = "|".join(f"{p:.2f}kr" for p in prices[:20])
                out["Status"] = "ok" if (prices or parsed["result_count"]) else "no_results"
                print(
                    f"    -> {out['Status']} count={parsed['result_count']} "
                    f"min SEK={out['MEK_AM_MinPrice_SEK'] or '-'} brands={out['MEK_AM_Brands'][:40]}",
                    flush=True,
                )
            except PwTimeout:
                out["Status"] = "timeout"
                out["Notes"] = "timeout"
                print("    -> timeout", flush=True)
            except Exception as exc:
                out["Notes"] = str(exc)[:200]
                print(f"    -> error: {out['Notes'][:80]}", flush=True)

            writer.append(out)
            time.sleep(random.uniform(delay_min, delay_max))

        browser.close()

    print(f"Done -> {OUTPUT_CSV}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--delay", nargs=2, type=float, default=(1.5, 3.5))
    ap.add_argument("--visible", action="store_true", help="Show browser window")
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--force", action="store_true", help="Delete CSV and re-scrape all")
    args = ap.parse_args()
    run(
        args.top,
        args.delay[0],
        args.delay[1],
        headless=not args.visible,
        retry_errors=args.retry_errors,
        force_rescrape=args.force,
    )


if __name__ == "__main__":
    main()
