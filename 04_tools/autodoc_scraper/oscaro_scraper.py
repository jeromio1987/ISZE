"""
ISZE — Oscaro FR price scraper (EUR)
Output: oscaro_results.csv

STATUS (2026-05-30): PERMANENTLY CLOUDFLARE BLOCKED
  oscaro.com returns Cloudflare challenge for all headless requests.
  No fix available without rotating residential proxies.
  Script kept for reference — do not include in run_all_scrapers.bat.

Usage:
    python oscaro_scraper.py --top 200
    python oscaro_scraper.py --top 200 --visible
    python oscaro_scraper.py --retry-errors
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
OUTPUT_CSV = SCRIPT_DIR / "oscaro_results.csv"
SEARCH_URL = "https://www.oscaro.com/en/parts/search?query={pn}"

CSV_FIELDS = [
    "PN",
    "Description",
    "PR00_EUR",
    "Rev_CY2025_EUR",
    "OSC_ResultCount",
    "OSC_AM_MinPrice_EUR",
    "OSC_AM_AvgPrice_EUR",
    "OSC_AM_Count",
    "OSC_AM_Brands",
    "OSC_URL",
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


def parse_page(html: str) -> dict:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    prices = []
    for match in re.finditer(r"([\d]+[,.][\d]{2})\s*€", text):
        try:
            v = float(match.group(1).replace(",", "."))
            if 2.5 <= v <= 8000:
                prices.append(v)
        except ValueError:
            pass
    prices = sorted(set(prices))
    brands = re.findall(
        r"(?:brand|marque|manufacturer)\s*[:\-]?\s*([A-Za-z0-9& /\-\.]{2,40})",
        text,
        re.I,
    )
    brands = list(dict.fromkeys(b.strip() for b in brands if b.strip()))[:15]
    return {"prices": prices, "brands": brands, "result_count": len(prices)}


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
        f"Oscaro: {len(pending)} PNs "
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
            locale="fr-FR",
            timezone_id="Europe/Paris",
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
            url = SEARCH_URL.format(pn=pn)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{i}/{total}] OSC {pn}", flush=True)
            out = {f: "" for f in CSV_FIELDS}
            out.update(
                {
                    "PN": pn,
                    "Description": row.get("Description", ""),
                    "PR00_EUR": row.get("PR00_EUR", ""),
                    "Rev_CY2025_EUR": row.get("Rev_CY2025_EUR", ""),
                    "OSC_URL": url,
                    "Scraped_At": ts,
                    "Status": "error",
                }
            )
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                try:
                    page.wait_for_selector(
                        "text=/results|résultats|no results/i", timeout=10_000
                    )
                except PwTimeout:
                    pass
                html = page.content()
                parsed = parse_page(html)
                prices = parsed["prices"]
                out["OSC_ResultCount"] = parsed["result_count"]
                out["OSC_AM_Count"] = len(prices)
                if prices:
                    out["OSC_AM_MinPrice_EUR"] = min(prices)
                    out["OSC_AM_AvgPrice_EUR"] = round(sum(prices) / len(prices), 2)
                if parsed["brands"]:
                    out["OSC_AM_Brands"] = "|".join(parsed["brands"])
                out["Status"] = "ok" if prices else "no_results"
                print(
                    f"    -> {out['Status']} count={out['OSC_ResultCount']} "
                    f"min EUR={out['OSC_AM_MinPrice_EUR'] or '-'}",
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
