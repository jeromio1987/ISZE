"""
ISZE — Cross-Reference Search Runner
=====================================
Reads autodoc_crossrefs.csv, collects all OE_Refs and Brand_PNs for each
ISZE PN, then searches those reference numbers on:
  - Autodoc EU  (EUR prices)
  - Autodoc DE  (EUR prices — skips on 403)
  - Mekonomen SE (SEK prices)

Output: crossref_results.csv (incremental by ISZE_PN + Site pair)

Fields: ISZE_PN, Description, PR00_EUR, Matched_Ref, Site,
        Min_Price, Currency, Brands, URL, Scraped_At, Status

Usage:
    python crossref_search_runner.py [--delay MIN MAX] [--max-refs N]
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

SCRIPT_DIR  = Path(__file__).parent
_TOOLS = SCRIPT_DIR.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.scraper_io import IncrementalCsvWriter
INPUT_CSV   = SCRIPT_DIR / "autodoc_crossrefs.csv"
OUTPUT_CSV  = SCRIPT_DIR / "crossref_results.csv"

CSV_FIELDS = [
    "ISZE_PN", "Description", "PR00_EUR",
    "Matched_Ref", "Site",
    "Min_Price", "Currency",
    "Brands", "URL",
    "Scraped_At", "Status",
]

SITES = {
    "autodoc_eu": {
        "url": "https://www.autodoc.eu/spares-search?keyword={ref}",
        "currency": "EUR",
        "locale": "en-GB",
    },
    "autodoc_de": {
        "url": "https://www.autodoc.de/spares-search?keyword={ref}",
        "currency": "EUR",
        "locale": "de-DE",
    },
    "mekonomen_se": {
        "url": "https://www.mekonomen.se/catalogsearch/result/?q={ref}",
        "currency": "SEK",
        "locale": "sv-SE",
    },
}

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


# ─── Parsing ───────────────────────────────────────────────────────────────────

def parse_eur_page(text: str) -> dict:
    """Extract EUR prices and brands from Autodoc EU/DE page text (reuses tld_scraper logic)."""
    result_count = 0
    m = re.search(r"(\d+)\s+results?\s+found", text, re.I)
    if m:
        result_count = int(m.group(1))
    elif re.search(r"no results|0 results|Keine Ergebnisse", text, re.I):
        return {"result_count": 0, "prices": [], "brands": [], "notes": "no_results"}

    prices = []
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

    brands = []
    seen: set[str] = set()
    for m in re.finditer(
        r"(?:Manufacturer|Brand|Hersteller)\s*[:\-]\s*([A-Za-z0-9& /\-\.]+?)(?:\n|\r|$|,|\|)",
        text, re.I,
    ):
        b = m.group(1).strip()
        if b and b.upper() not in seen:
            seen.add(b.upper())
            brands.append(b)

    return {
        "result_count": result_count or len(prices),
        "prices": prices,
        "brands": brands,
        "notes": "",
    }


def parse_sek_page(text: str) -> dict:
    """Extract SEK prices from Mekonomen page text."""
    prices = []
    # Try structured patterns first: "199,00 kr" / "199.00 SEK"
    for m in re.finditer(r"([\d]+[,.][\d]{2})\s*(?:kr|SEK)\b", text, re.I):
        try:
            v = float(m.group(1).replace(",", "."))
            if v > 10:
                prices.append(v)
        except ValueError:
            pass
    # Fallback: large integers followed by kr
    if not prices:
        for m in re.finditer(r"\b(\d{3,5})\s*(?:kr|SEK)\b", text, re.I):
            try:
                v = float(m.group(1))
                if 10 < v < 100000:
                    prices.append(v)
            except ValueError:
                pass
    prices = sorted(set(prices))

    brands = []
    seen: set[str] = set()
    for m in re.finditer(
        r"(?:Manufacturer|Brand|Varumärke)\s*[:\-]\s*([A-Za-z0-9& /\-\.]+?)(?:\n|\r|$|,|\|)",
        text, re.I,
    ):
        b = m.group(1).strip()
        if b and b.upper() not in seen:
            seen.add(b.upper())
            brands.append(b)

    result_count = 0
    mc = re.search(r"(\d+)\s+(?:results?|produkter|träffar)", text, re.I)
    if mc:
        result_count = int(mc.group(1))
    else:
        result_count = len(prices)

    return {
        "result_count": result_count,
        "prices": prices,
        "brands": brands,
        "notes": "",
    }


# ─── Input loading ─────────────────────────────────────────────────────────────

def load_crossrefs() -> list[dict]:
    if not INPUT_CSV.exists():
        sys.exit(f"Input not found: {INPUT_CSV}. Run autodoc_crossref_scraper.py first.")
    rows = []
    with INPUT_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def collect_refs_per_pn(rows: list[dict]) -> dict[str, dict]:
    """
    Returns { ISZE_PN: { 'description': ..., 'pr00': ..., 'refs': set() } }
    """
    per_pn: dict[str, dict] = {}
    for row in rows:
        pn   = row.get("ISZE_PN", "").strip()
        if not pn:
            continue
        if pn not in per_pn:
            per_pn[pn] = {
                "description": row.get("Description", ""),
                "pr00":        row.get("PR00_EUR", ""),
                "refs":        set(),
            }
        # Collect OE_Refs
        for ref in (row.get("OE_Refs") or "").split("|"):
            ref = ref.strip()
            if ref and len(ref) >= 5:
                per_pn[pn]["refs"].add(ref)
        # Collect just the PN part from Brand_PNs ("RIDEX 82B0013" → "82B0013")
        for bp in (row.get("Brand_PNs") or "").split("|"):
            bp = bp.strip()
            if " " in bp:
                ref = bp.split(" ", 1)[1].strip()
                if ref and len(ref) >= 5:
                    per_pn[pn]["refs"].add(ref)
    return per_pn


def _make_writer() -> IncrementalCsvWriter:
    return IncrementalCsvWriter(
        OUTPUT_CSV,
        CSV_FIELDS,
        key_fields=("ISZE_PN", "Site"),
        done_statuses=None,
    )


# ─── HTTP session ──────────────────────────────────────────────────────────────

def make_session(locale: str = "en-GB"):
    import requests
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(UA_POOL),
        "Accept-Language": f"{locale},{locale.split('-')[0]};q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    return session


def fetch_text(session, url: str, timeout: int = 20) -> tuple[str, int]:
    """
    Returns (body_text, status_code). On network error returns ("", 0).
    """
    try:
        resp = session.get(url, timeout=timeout)
        return resp.text, resp.status_code
    except Exception as exc:
        return "", 0


# ─── Main ──────────────────────────────────────────────────────────────────────

def run(delay_min: float, delay_max: float, max_refs: int) -> None:
    try:
        import requests  # noqa: F401 — verify installed
    except ImportError:
        sys.exit("pip install requests")

    crossref_rows = load_crossrefs()
    per_pn        = collect_refs_per_pn(crossref_rows)
    writer        = _make_writer()
    done          = writer.done_keys()
    writer.ensure_header()

    total_pns = len(per_pn)
    print(f"Loaded {total_pns} unique ISZE PNs from crossrefs file.")

    pn_list = sorted(per_pn.keys())
    pn_count = 0

    for pn in pn_list:
        pn_count += 1
        info = per_pn[pn]
        refs = sorted(info["refs"])[:max_refs]  # limit refs per PN

        if not refs:
            # No refs found — write a no_refs row for each site so we skip next time
            for site_name in SITES:
                if (pn, site_name) in done:
                    continue
                writer.append({
                    "ISZE_PN":     pn,
                    "Description": info["description"],
                    "PR00_EUR":    info["pr00"],
                    "Matched_Ref": "",
                    "Site":        site_name,
                    "Min_Price":   "",
                    "Currency":    "",
                    "Brands":      "",
                    "URL":         "",
                    "Scraped_At":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Status":      "no_refs",
                })
            continue

        print(f"\n[{pn_count}/{total_pns}] {pn}  ({info['description'][:40]})  "
              f"refs={len(refs)}")

        for site_name, site_cfg in SITES.items():
            if (pn, site_name) in done:
                print(f"  [{site_name}] skipped (already done)")
                continue

            currency = site_cfg["currency"]
            best_price: float | None = None
            best_ref   = ""
            best_url   = ""
            all_brands: set[str] = set()
            found_status = "no_results"

            session = make_session(site_cfg["locale"])

            for ref in refs:
                url  = site_cfg["url"].format(ref=ref)
                text, status_code = fetch_text(session, url)

                if status_code == 403:
                    print(f"  [{site_name}] 403 blocked — skipping site for this PN")
                    found_status = "blocked_403"
                    best_url = url
                    break

                if status_code == 0:
                    print(f"  [{site_name}] network error on ref {ref}")
                    time.sleep(random.uniform(1, 3))
                    continue

                if currency == "SEK":
                    parsed = parse_sek_page(text)
                else:
                    parsed = parse_eur_page(text)

                if parsed["prices"]:
                    min_p = min(parsed["prices"])
                    if best_price is None or min_p < best_price:
                        best_price  = min_p
                        best_ref    = ref
                        best_url    = url
                    for b in parsed["brands"]:
                        all_brands.add(b)
                    found_status = "ok"
                    print(f"  [{site_name}] ref={ref}  min {currency}={min_p}")

                time.sleep(random.uniform(delay_min / 2, delay_max / 2))

            writer.append({
                "ISZE_PN":     pn,
                "Description": info["description"],
                "PR00_EUR":    info["pr00"],
                "Matched_Ref": best_ref,
                "Site":        site_name,
                "Min_Price":   f"{best_price:.2f}" if best_price is not None else "",
                "Currency":    currency,
                "Brands":      "|".join(sorted(all_brands)[:15]),
                "URL":         best_url,
                "Scraped_At":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Status":      found_status,
            })

            time.sleep(random.uniform(delay_min, delay_max))

        if pn_count % 20 == 0:
            print(f"\n-- Progress {pn_count}/{total_pns} ({pn_count/total_pns*100:.0f}%) --\n")

    print(f"\nDone. {total_pns} PNs processed.")
    print(f"Output: {OUTPUT_CSV}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Search cross-ref PNs on EU/DE/Mekonomen")
    ap.add_argument("--delay",    nargs=2, type=float, default=[1.5, 4.0],
                    metavar=("MIN", "MAX"),
                    help="Delay range between site requests (default 1.5 4.0)")
    ap.add_argument("--max-refs", type=int, default=10,
                    help="Max cross-ref numbers to try per PN per site (default 10)")
    args = ap.parse_args()

    print("=" * 60)
    print("  ISZE Cross-Reference Search Runner")
    print(f"  delay {args.delay[0]}-{args.delay[1]}s | max-refs {args.max_refs}")
    print("=" * 60 + "\n")

    run(delay_min=args.delay[0], delay_max=args.delay[1], max_refs=args.max_refs)


if __name__ == "__main__":
    main()
