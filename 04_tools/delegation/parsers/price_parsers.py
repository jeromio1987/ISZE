# -*- coding: utf-8 -*-
"""
ISZE price parsers — Phase 1 skeletons, OFFLINE (delegation card C5).

What these are
--------------
One function per target site that turns a saved product page into price-observation
rows in the ledger schema of `04_tools/price_ledger/build_price_ledger.py`
(`COLUMNS`, `PRICE_TYPES`, `MATCH_METHODS`).

What these are NOT
------------------
They do not fetch anything. There is no network call in this package. Phase 1
scraping is still gated on Jerome's explicit go (SCRAPER_REDO_DELEGATION.md §10).

How they are meant to be used later
-----------------------------------
1. `check_scrape_consent.py` BEFORE any future fetch (see `consent_ok()` below).
2. Fetch politely (>= 2 s per request per site), write the HTML to disk.
3. Parse the saved HTML with the per-site function here.
4. If the selector returns nothing, hand the page text to `deepseek_batch.py`
   (the self-healing fallback in the plan, §2). A parser that goes quiet is a
   signal to repair the selector, not to accept a blank.

Evidence status per site (honest — read this before trusting a parser)
---------------------------------------------------------------------
  amayama   PAGE ON DISK. `01_data/90_INBOX/scrape_targets/_probe/v_amayama.html`.
            Parsed and asserted against the real file by `--selftest`.
            Selector: the JSON-LD `Product` block, plus the per-warehouse rows.
  omega     STUB. No saved product page. The 2026-09-18 UK/Ireland research fetched a
            real one and recorded the fields (internal code + 10-digit OEM + GBP price +
            a competitor `Dealer Price` line) — see the parse_omega docstring. Domain is
            `omegaspareparts.com`; robots disallows `/wp-json/`, so use HTML search.
  geparden  STUB. Documented pattern only (SKU *is* the OEM number, `ISU` + 10 digits,
            e.g. `ISU5876150000`), from the 2026-09-18 Nordic research. No page on disk.
  tungen    STUB. Documented pattern only (a WooCommerce-style table with columns
            Varenummer / Beskrivelse / Antall / Pris ex. mva), from the same research.
            No page on disk.

A stub raises `NotImplementedError` rather than returning an empty list, so a future
caller cannot mistake "not written yet" for "no price on the page".
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Windows console can be cp1252 under Task Scheduler — degrade instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent          # 04_tools/delegation/parsers
ROOT = HERE.parents[2]                          # ISZE
CONSENT_SCRIPT = HERE.parents[1] / "autodoc_scraper" / "check_scrape_consent.py"
PROBE = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"

ISUZU_PN_RE = re.compile(r"\b(?:8[- ]?)?(8\d{8})\b")
TEN_DIGIT_RE = re.compile(r"\b\d{10}\b")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def normalise_pn(raw: str | None) -> str | None:
    """Any Isuzu part-number shape -> bare 10 digits, or None.

    Handles `8974995480`, `8-97499-548-0`, `ISU5876150000`, `8980139111.UMI`.
    """
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) == 10:
        return digits
    if len(digits) == 11 and digits.startswith("0"):
        return digits[1:]
    return None


def consent_ok(url: str, path: str = "/") -> bool:
    """Run the existing consent gate for one target. Never fetches the part page.

    Returns True only on exit 0. Kept as a function so a future Phase 1 fetcher has
    exactly one place to call before it opens a connection.
    """
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(CONSENT_SCRIPT), "--url", url, "--path", path],
        capture_output=True, text=True,
    )
    return proc.returncode == 0


# ---------------------------------------------------------------------------
# Amayama — selector parser, proven against the saved page
# ---------------------------------------------------------------------------
def parse_amayama(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """Amayama product page -> ledger rows (genuine / grey-import tier).

    Amayama is not a UK company and its stock sits in several warehouses (Japan,
    UAE, Latvia). Prices are in the currency the visitor selected when the page was
    saved (USD on the file on disk) — read `priceCurrency` from the page, never assume.

    Two layers, in this order:
      1. JSON-LD `Product` block — the authoritative headline: `price`, `priceCurrency`,
         `sku`, `mpn`, `availability`. This is what the earlier probes quoted.
      2. Per-warehouse rows — `warehouse-name` plus `part-price`. These give one row per
         warehouse, which is what makes shipping cost readable later.

    Returns ledger rows. `price_type` is `genuine_grey`: genuine Isuzu parts bought
    outside the authorised network. Never blend with `aftermarket_trade`/`retail`.
    """
    rows: list[dict] = []
    if not html:
        return rows

    pn = None

    # Collect every JSON-LD block and take the Product one. The page also carries a
    # BreadcrumbList block that starts with the same {"@context" opening, so a single
    # regex spanning from the first ld+json tag would capture invalid JSON.
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            node = json.loads(block)
        except json.JSONDecodeError:
            continue
        if not isinstance(node, dict) or node.get("@type") != "Product":
            continue
        pn = normalise_pn(node.get("mpn") or node.get("name"))
        offer = node.get("offers") or {}
        price = offer.get("price")
        currency = offer.get("priceCurrency")
        if price and currency:
            rows.append(_row(
                part_no=pn, price=float(price), currency=str(currency),
                price_type="genuine_grey", match_method="exact_oem",
                source="Amayama", source_url=source_url, country="JP",
                observed_at=observed_at, vintage=f"Amayama {observed_at}",
                competitor_brand="Isuzu (genuine, grey channel)", competitor_pn=pn,
                description=f"Isuzu genuine {pn}", vat="unknown",
                stock="in" if "InStock" in str(offer.get("availability", "")) else "out",
                n_obs=1, loader="amayama",
            ))
        break

    # Fallback / supplement: the visible per-warehouse table. The warehouse cell has a
    # nested <span class="gst"> inside it, so the name is captured loosely and stripped.
    for m in re.finditer(
        r'<span class="warehouse-name">(.*?)<span class="part-price">([\d.,]+)</span>',
        html, re.S,
    ):
        warehouse = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip(" -")
        price_txt = m.group(2).replace(",", "")
        try:
            price = float(price_txt)
        except ValueError:
            continue
        rows.append(_row(
            part_no=pn, price=price, currency=_currency_near(html, m.start()),
            price_type="genuine_grey", match_method="exact_oem",
            source="Amayama", source_url=source_url,
            country=_warehouse_country(warehouse), observed_at=observed_at,
            vintage=f"Amayama {observed_at}",
            competitor_brand="Isuzu (genuine, grey channel)", competitor_pn=pn,
            description=f"Isuzu genuine {pn} — {warehouse}", vat="unknown",
            stock="in", n_obs=1, loader="amayama",
        ))

    return rows


def _currency_near(html: str, pos: int) -> str:
    """The page's selected currency, taken from the nearest currency selector."""
    window = html[max(0, pos - 4000): pos]
    hits = re.findall(r'data-type="selected-option-name">([A-Z]{3})<', window)
    return hits[-1] if hits else "USD"


def _warehouse_country(name: str) -> str:
    low = name.lower()
    if "latvia" in low:
        return "LV"
    if "uae" in low or "emirates" in low:
        return "AE"
    if "japan" in low:
        return "JP"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Stubs — NO saved page on disk, so no selector is written and no guess is made
# ---------------------------------------------------------------------------
def parse_omega(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """TODO — no product page saved on disk (only the research notes).

    What the 2026-09-18 UK/Ireland research established on a real fetched page
    (`01_data/90_INBOX/scrape_targets/uk_ireland.md` § omegaspareparts.com):
      - the page exposes its own internal code (`0011765K`) AND the 10-digit OEM
        (`8970622940`) as separate fields, plus `Manufacturer Part Number:
        8-97062-294-0` and `Part Manufacturer Number: 8970622940`
      - it prints a GBP price (e.g. £40.80) AND a competitor line `Dealer Price: 66.86`,
        which is the most valuable single field on any UK target
      - reach it by HTML search `?s=<pn>&post_type=product`; robots disallows `/wp-json/`
      - one caveat to resolve first: the REST API reports 3,729 products but only 3 match
        a search for "isuzu", so the Isuzu range may be much thinner than that one page
        implies. Reconcile before relying on coverage.

    To finish: save that product page into `_probe/`, write the selector against it, add
    it to `--selftest`, then set `price_type` from what the page actually is (the
    competitor `Dealer Price` line is a separate observation, not the same price point).
    """
    raise NotImplementedError("Omega parser not written — no product page on disk (see docstring)")


def parse_geparden(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """TODO — no product page on disk.

    Known pattern (2026-09-18 Nordic research, marked [S] there, not [V]): the product
    SKU **is** the Isuzu OEM number with no separators, prefixed `ISU`,
    e.g. `ISU5876150000`; the product is titled as genuine Isuzu; NOK price inc. mva.
    `/search` is disallowed in robots.txt, so product pages must be reached by sitemap,
    not by search.

    To finish this: save one real geparden.no product page, confirm the SKU shape, then
    write the selector. `price_type` = `genuine_grey` if the page sells genuine Isuzu,
    `aftermarket_retail` otherwise — read the page.
    """
    raise NotImplementedError("geparden parser not written — no product page on disk (see docstring)")


def parse_tungen(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """TODO — no product page on disk.

    Known pattern (same research pass): an Isuzu dealer publishing older original parts
    in a table with columns `Varenummer / Beskrivelse / Antall / Pris`, price ex. mva,
    searchable by part number, order by form (no direct purchase). Only one row was on
    the page when that research was done, so expect a thin but trustworthy source.

    To finish this: save the table page, write the row parser, and tag rows
    `price_type = "dealer"` — never mixed with aftermarket. `country = "NO"`.
    """
    raise NotImplementedError("tungen-bil parser not written — no product page on disk (see docstring)")


PARSERS = {
    "amayama": parse_amayama,
    "omega": parse_omega,
    "geparden": parse_geparden,
    "tungen": parse_tungen,
}


def _row(**kw) -> dict:
    """Fill the ledger COLUMNS with None so every row is schema-complete."""
    cols = [
        "obs_id", "part_no", "match_method", "competitor_brand", "competitor_pn", "description",
        "source", "source_url", "country", "observed_at", "vintage",
        "price", "price_avg", "currency", "price_eur", "fx_note", "vat",
        "price_type", "stock", "n_obs", "loader",
    ]
    out = {c: None for c in cols}
    out.update(kw)
    return out


# ---------------------------------------------------------------------------
# Self-test — parses the ONE real page on disk and prints what it found
# ---------------------------------------------------------------------------
def selftest() -> int:
    page = PROBE / "v_amayama.html"
    if not page.exists():
        print(f"SELFTEST FAIL — saved page missing: {page}")
        return 1

    html = page.read_text(encoding="utf-8", errors="replace")
    observed = "2026-09-18"  # date the probe was saved (see scrape_targets research)
    rows = parse_amayama(
        html,
        source_url="https://www.amayama.com/en/part/isuzu/8974995480",
        observed_at=observed,
    )

    print("Amayama parser — selftest against the saved page")
    print(f"  page      : {page}")
    print(f"  bytes     : {len(html):,}")
    print(f"  rows found: {len(rows)}")
    for r in rows:
        print(f"    PN {r['part_no']}  {r['price']} {r['currency']}  "
              f"type={r['price_type']}  country={r['country']}  stock={r['stock']}  "
              f"| {r['description']}")

    # Assertions — a parser that returns nothing must fail loudly, not quietly.
    problems = []
    if not rows:
        problems.append("no rows parsed")
    if not any(r["part_no"] == "8974995480" for r in rows):
        problems.append("expected part number 8974995480 not found")
    if not any(r["price"] == 54.25 for r in rows):
        problems.append("expected headline price 54.25 not found")
    if not any(r["price_type"] == "genuine_grey" for r in rows):
        problems.append("price_type not genuine_grey")
    if any(r["part_no"] and len(r["part_no"]) != 10 for r in rows):
        problems.append("a part number is not 10 digits")

    print("\n  stubs (no page on disk, so deliberately not written):")
    for name in ("omega", "geparden", "tungen"):
        try:
            PARSERS[name]("")
        except NotImplementedError as e:
            print(f"    {name:9s} OK — raises rather than returning empty: {e}")

    if problems:
        print("\nSELFTEST FAIL — " + "; ".join(problems))
        return 1
    print("\nSELFTEST PASS — 8974995480, 54.25 USD, genuine_grey, from the saved page")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    print(__doc__)
    print("Usage:  python 04_tools/delegation/parsers/price_parsers.py --selftest")
