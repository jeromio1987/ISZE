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

# cp1252 consoles (Task Scheduler) can't print some scraped brand strings —
# degrade to '?' instead of crashing the run (same failure class that killed
# ks_scraper.py on 2026-07-13).
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

SCRIPT_DIR = Path(__file__).parent
_TOOLS = SCRIPT_DIR.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from scraper_pn_loader import load_top_pns
from _shared.scraper_io import IncrementalCsvWriter
OUTPUT_CSV = SCRIPT_DIR / "mekonomen_results.csv"
BASE_URL = "https://www.mekonomen.se/catalogsearch/result/?q={pn}"

# Page-chrome labels from Mekonomen's tire-filter panel that the Tillverkare
# block parser was picking up as "brands" (confirmed on every ok-row of the
# 2026-07-13 run: Bredd|Däckprofil|...). Lowercase for comparison.
JUNK_BRAND_LABELS = frozenset({
    "bredd", "däckprofil", "rullmotstånd", "våtgrepp", "tum",
    "hastighetsindex", "lastindex", "se alla", "tillverkare", "more",
})

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

    # Guard (same class as the Autodoc £2.00 artifact): only harvest kr amounts
    # when the page explicitly shows a result count. Without this, page chrome
    # (e.g. a 259-kr tire promo) was harvested on zero-result pages and reported
    # as a "min price" — identical 259.0 on unrelated PNs in the 2026-07-13 run.
    prices = []
    if out["result_count"] > 0:
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
            if line.lower() in JUNK_BRAND_LABELS:
                continue
            if re.search(r"[A-Za-z]", line) and len(line) <= 40:
                brands.add(line)

    out["brands"] = sorted(brands)

    # NOTE: there used to be a fallback here that fabricated result_count from
    # len(prices) when the "N Items" text was missing — that is exactly how
    # chrome prices became fake "ok" rows. A rendered results page always shows
    # the count (the scraper waits for it), so no count = no results.

    return out


def _row_prices(row: dict) -> list[float]:
    out = []
    for p in (row.get("MEK_AllProducts") or "").split("|"):
        if p.endswith("kr"):
            try:
                out.append(float(p[:-2]))
            except ValueError:
                pass
    return out


def strip_chrome_artifacts(csv_path: Path = OUTPUT_CSV, min_repeat: int = 3) -> int:
    """Post-run validation sweep (Autodoc-£2.00-class guard, cross-PN variant).

    An identical price appearing on >= min_repeat distinct PNs is page chrome
    (banner/promo text), not a product price — real unrelated Isuzu parts don't
    share an exact kr amount. Confirmed 2026-07-13: 259.0 SEK reported as min
    price for a DPD sensor, a DEF tank sensor AND a rear final drive. Strips the
    offending value from each row, recomputes min/avg/count, demotes rows with
    nothing left to no_results, and scrubs junk chrome labels from the brand
    column. Returns the number of rows fixed.
    """
    if not csv_path.is_file():
        return 0
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    pn_count_per_price: dict[float, int] = {}
    for row in rows:
        for v in set(_row_prices(row)):
            pn_count_per_price[v] = pn_count_per_price.get(v, 0) + 1
    chrome = {v for v, n in pn_count_per_price.items() if n >= min_repeat}

    fixed = 0
    for row in rows:
        brands = [b for b in (row.get("MEK_AM_Brands") or "").split("|")
                  if b and b.lower() not in JUNK_BRAND_LABELS]
        row["MEK_AM_Brands"] = "|".join(brands)

        prices = _row_prices(row)
        hit = sorted(set(prices) & chrome)
        if not hit:
            continue
        kept = [p for p in prices if p not in chrome]
        row["MEK_AllProducts"] = "|".join(f"{p:.2f}kr" for p in kept)
        row["MEK_AM_Count"] = len(kept)
        if kept:
            row["MEK_AM_MinPrice_SEK"] = min(kept)
            row["MEK_AM_AvgPrice_SEK"] = round(sum(kept) / len(kept), 2)
        else:
            row["MEK_AM_MinPrice_SEK"] = ""
            row["MEK_AM_AvgPrice_SEK"] = ""
            row["MEK_ResultCount"] = 0
            row["Status"] = "no_results"
        note = "chrome_price_stripped:" + ",".join(f"{v:g}" for v in hit)
        row["Notes"] = f"{row['Notes']};{note}" if row.get("Notes") else note
        fixed += 1

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    if chrome:
        print(f"Chrome-price guard: stripped {sorted(chrome)} from {fixed} rows", flush=True)
    else:
        print("Chrome-price guard: no repeated cross-PN prices found", flush=True)
    return fixed


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

    strip_chrome_artifacts(writer.path)
    print(f"Done -> {OUTPUT_CSV}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--delay", nargs=2, type=float, default=(1.5, 3.5))
    ap.add_argument("--visible", action="store_true", help="Show browser window")
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--force", action="store_true", help="Delete CSV and re-scrape all")
    ap.add_argument("--clean-artifacts", action="store_true",
                    help="Only run the chrome-price/junk-brand sweep on the existing CSV, no scraping")
    args = ap.parse_args()
    if args.clean_artifacts:
        strip_chrome_artifacts()
        return
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
