"""
ISZE — Vehicle Search Mapper
==============================
For PNs with NO Autodoc UK results (Status == "no_results"), attempts to find
parts by searching Autodoc UK using vehicle model + part category keywords.

Vehicle models: Isuzu D-Max, Isuzu N35, Isuzu N45, Isuzu N75
Category mapping: derived from PN Description field

Output: vehicle_search_results.csv (incremental by PN + vehicle)

Fields: ISZE_PN, Description, PR00_EUR, Vehicle, Category,
        Search_Query, Search_URL, Result_Count, Min_Price_GBP,
        Brands, Scraped_At, Status, Notes

Usage:
    python vehicle_search_mapper.py [--delay MIN MAX] [--headless]
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
INPUT_CSV  = SCRIPT_DIR / "autodoc_results.csv"
OUTPUT_CSV = SCRIPT_DIR / "vehicle_search_results.csv"

CSV_FIELDS = [
    "ISZE_PN", "Description", "PR00_EUR",
    "Vehicle", "Category",
    "Search_Query", "Search_URL",
    "Result_Count", "Min_Price_GBP",
    "Brands",
    "Scraped_At", "Status", "Notes", "scrape_error",
]

# Vehicle models to search against
VEHICLES = [
    "isuzu d-max",
    "isuzu n35",
    "isuzu n45",
    "isuzu n75",
]

# Description keyword → Autodoc category slug
CATEGORY_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bFILTER\b|\bFILT\b",          re.I), "filters"),
    (re.compile(r"\bROTOR\b|\bDISC\b|\bBRK\b|\bBRAKE\b|\bPAD\b|\bDRUM\b", re.I), "brakes"),
    (re.compile(r"\bSENSOR\b",                    re.I), "sensors"),
    (re.compile(r"\bPUMP\b",                      re.I), "pumps"),
    (re.compile(r"\bBEARING\b",                   re.I), "bearings"),
    (re.compile(r"\bBELT\b",                      re.I), "belts"),
    (re.compile(r"\bINJECT\b",                    re.I), "injectors"),
    (re.compile(r"\bSHOCK\b|\bDAMPER\b|\bSTRUT\b", re.I), "shock-absorbers"),
    (re.compile(r"\bSPARK\b|\bGLOW\b",            re.I), "spark-glow-plugs"),
    (re.compile(r"\bSTEER\b",                     re.I), "steering"),
    (re.compile(r"\bALTERNATOR\b",                re.I), "alternators"),
    (re.compile(r"\bSTARTER\b",                   re.I), "starters"),
    (re.compile(r"\bRADIATOR\b|\bCOOL\b",        re.I), "cooling"),
    (re.compile(r"\bEXHAUST\b|\bMUFFLER\b",      re.I), "exhaust"),
    (re.compile(r"\bCLUTCH\b",                    re.I), "clutch"),
    (re.compile(r"\bOIL\b",                       re.I), "engine-oils-fluids"),
    (re.compile(r"\bAIR\b",                       re.I), "air-filters"),
    (re.compile(r"\bSUSPENSION\b|\bLINK\b|\bARMBUSH\b|\bBUSH\b", re.I), "suspension"),
    (re.compile(r"\bGASKET\b|\bSEAL\b",          re.I), "gaskets-seals"),
    (re.compile(r"\bTERMINAL\b|\bBATTERY\b",     re.I), "batteries"),
]

DEFAULT_CATEGORY = "spare-parts"

# Autodoc UK search URL template
SEARCH_URL_TPL = "https://www.autodoc.co.uk/spare-parts/isuzu?search={query}"
# Also try keyword search with vehicle + category
KEYWORD_URL_TPL = "https://www.autodoc.co.uk/spares-search?keyword={query}"


# ─── Helpers ───────────────────────────────────────────────────────────────────

def map_category(description: str) -> str:
    for pattern, cat in CATEGORY_MAP:
        if pattern.search(description):
            return cat
    return DEFAULT_CATEGORY


def load_no_result_rows() -> list[dict]:
    if not INPUT_CSV.exists():
        sys.exit(f"Input not found: {INPUT_CSV}")
    rows = []
    with INPUT_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("Status") or "").strip().lower() == "no_results":
                rows.append(row)
    return rows


def _make_writer() -> IncrementalCsvWriter:
    return IncrementalCsvWriter(
        OUTPUT_CSV,
        CSV_FIELDS,
        key_fields=("ISZE_PN", "Vehicle"),
        done_statuses=None,
    )


# ─── Page parsing ──────────────────────────────────────────────────────────────

def parse_search_results(page_text: str) -> dict:
    """Reuse Autodoc UK GBP parsing from autodoc_scraper.py."""
    result_count = 0
    m = re.search(r"(\d+)\s+results?\s+found", page_text, re.I)
    if m:
        result_count = int(m.group(1))
    elif re.search(r"no results|0 results", page_text, re.I):
        return {"result_count": 0, "prices": [], "brands": []}

    prices = []
    for match in re.finditer(r"£\s*([\d,]+\.?\d*)", page_text):
        try:
            v = float(match.group(1).replace(",", ""))
            if 0.5 <= v <= 5000:
                prices.append(v)
        except ValueError:
            pass
    prices = sorted(set(prices))

    brands = []
    seen: set[str] = set()
    for bm in re.finditer(
        r"(?:Manufacturer|Brand)\s*[:\-]\s*([A-Za-z0-9& /\-\.]+?)(?:\n|\r|$|,|\|)",
        page_text, re.I,
    ):
        b = bm.group(1).strip()
        if b and b.upper() not in seen:
            seen.add(b.upper())
            brands.append(b)

    return {
        "result_count": result_count or len(prices),
        "prices": prices,
        "brands": brands,
    }


# ─── Main ──────────────────────────────────────────────────────────────────────

def run(delay_min: float, delay_max: float, headless: bool) -> None:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        sys.exit("pip install playwright && playwright install chromium")

    no_result_rows = load_no_result_rows()
    writer         = _make_writer()
    done           = writer.done_keys()
    writer.ensure_header()

    print(f"no_results rows: {len(no_result_rows)}")

    # Build pending work: (row, vehicle) pairs not yet done
    work: list[tuple[dict, str]] = []
    for row in no_result_rows:
        pn = row.get("PN", "").strip()
        for vehicle in VEHICLES:
            if (pn, vehicle) not in done:
                work.append((row, vehicle))

    print(f"Pending (PN x vehicle) pairs: {len(work)}")
    if not work:
        print("Nothing to do. Delete vehicle_search_results.csv to restart.")
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

        total  = len(work)
        errors = 0

        for i, (row, vehicle) in enumerate(work, 1):
            pn          = row.get("PN", "").strip()
            description = row.get("Description", "")
            pr00        = row.get("PR00_EUR", "")
            category    = map_category(description)
            ts          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Build search query: "isuzu d-max filters" style
            query = f"{vehicle} {category}".replace(" ", "+")
            url   = KEYWORD_URL_TPL.format(query=query)

            print(
                f"[{i:>4}/{total}] {pn}  veh={vehicle}  cat={category}  ...",
                end=" ", flush=True,
            )

            out = {
                "ISZE_PN":      pn,
                "Description":  description,
                "PR00_EUR":     pr00,
                "Vehicle":      vehicle,
                "Category":     category,
                "Search_Query": query.replace("+", " "),
                "Search_URL":   url,
                "Result_Count": 0,
                "Min_Price_GBP": "",
                "Brands":       "",
                "Scraped_At":   ts,
                "Status":       "error",
                "Notes":        "",
                "scrape_error": "",
            }

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                try:
                    page.wait_for_selector(
                        "text=/results found|no results/i",
                        timeout=10_000,
                    )
                except PwTimeout:
                    pass

                page_text = page.inner_text("body")
                parsed    = parse_search_results(page_text)

                out["Result_Count"] = parsed["result_count"]
                if parsed["prices"]:
                    out["Min_Price_GBP"] = f"{min(parsed['prices']):.2f}"
                out["Brands"] = "|".join(parsed["brands"][:10])
                out["Status"] = "ok" if parsed["result_count"] > 0 else "no_results"
                out["scrape_error"] = ""

                print(f"count={parsed['result_count']}  min_GBP={out['Min_Price_GBP'] or '-'}")

            except PwTimeout:
                out["Status"] = "timeout"
                out["Notes"]  = "Page load timeout"
                out["scrape_error"] = "timeout"
                errors += 1
                print("timeout")

            except Exception as exc:
                out["Status"] = "error"
                out["Notes"]  = str(exc)[:120]
                out["scrape_error"] = str(exc)[:240]
                errors += 1
                print(f"ERROR: {str(exc)[:60]}")

            writer.append(out)

            if i % 30 == 0:
                print(f"\n-- Progress {i}/{total} ({i/total*100:.0f}%)  errors={errors} --\n")

            if i < total:
                time.sleep(random.uniform(delay_min, delay_max))

        browser.close()

    print(f"\nDone. {total} searches ({errors} errors).")
    print(f"Output: {OUTPUT_CSV}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Vehicle-based Autodoc search for unmatched ISZE PNs"
    )
    ap.add_argument("--delay",    nargs=2, type=float, default=[2.0, 5.0],
                    metavar=("MIN", "MAX"))
    ap.add_argument("--headless", action="store_true",
                    help="Run headless (faster, higher bot detection risk)")
    args = ap.parse_args()

    print("=" * 60)
    print("  ISZE Vehicle Search Mapper")
    print(f"  delay {args.delay[0]}-{args.delay[1]}s | "
          f"{'headless' if args.headless else 'visible browser'}")
    print("=" * 60 + "\n")

    run(delay_min=args.delay[0], delay_max=args.delay[1], headless=args.headless)


if __name__ == "__main__":
    main()
