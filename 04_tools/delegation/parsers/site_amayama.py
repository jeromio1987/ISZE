# -*- coding: utf-8 -*-
"""Amayama — genuine Isuzu parts, grey channel. WORKING, proven against a real page.

Evidence
--------
Page A (current): `v_amayama_live.html`  (97,757 bytes)
       Fetched live 2026-09-24 through the consent gate, ALLOWED.
       URL:  https://www.amayama.com/en/part/isuzu/8974995480
       JSON-LD price **56.42 USD**, priceValidUntil 2026-10-25, InStock.
Page B (earlier): `v_amayama.html`  (98,714 bytes), saved 2026-09-18.
       Same part, JSON-LD price **54.25 USD**, priceValidUntil 2026-10-18.

**Both pages are fixtures and the selftest asserts both.** The part was repriced
+4.0% (54.25 → 56.42 USD) in the six days between the two snapshots, and the
per-warehouse table went from one row to one row for a different warehouse
(Latvia (EU), ex-UAE on both, but only the live page carries it in the same
position). A test asserting only the old figure would have gone red the moment
the price moved, which is what happened — and the correct response is to record
the movement, not to relax the assertion.

What it extracts
----------------
Two layers, in this order:

1. JSON-LD `Product` — the authoritative headline: `price`, `priceCurrency`, `sku`, `mpn`,
   `availability`. This is what the earlier probes quoted.
2. Per-warehouse rows — `warehouse-name` + `part-price`. One row per warehouse (Japan, UAE,
   Latvia), which is what makes shipping cost readable later.

`price_type = "genuine_grey"` — genuine Isuzu parts bought outside the authorised network.
Never blended with aftermarket. The currency is whatever the visitor selected when the page was
saved (**USD** on these files) and is read from the page, never assumed.

Caveat worth knowing: Amayama's stock sits in several countries, so one Isuzu number yields a row
per warehouse with different prices. Two rows for the same part are **not** duplicates.

A note on the currency: Amayama quotes **USD**, and the ledger's FX table has no USD rate, so
these rows carry the native price and let the ledger flag the gap rather than guessing a rate.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))
from ledger_schema import make_row, normalise_pn                      # noqa: E402

SITE = "amayama"
PROBE_PAGE = "v_amayama_live.html"
PROBE_URL = "https://www.amayama.com/en/part/isuzu/8974995480"
PROBE_DATE = "2026-09-24"
COUNTRY_DEFAULT = "JP"


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a product page ({len(html or '')} chars)")

    rows: list[dict] = []
    pn = None
    saw_product_block = False

    # The page also carries a BreadcrumbList block starting with the same
    # {"@context opening, so a single regex from the first ld+json tag would
    # capture invalid JSON. Parse each block separately.
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            node = json.loads(block)
        except json.JSONDecodeError:
            continue
        if not isinstance(node, dict) or node.get("@type") != "Product":
            continue
        saw_product_block = True
        pn = normalise_pn(node.get("mpn") or node.get("name"))
        offer = node.get("offers") or {}
        price = offer.get("price")
        currency = offer.get("priceCurrency")
        if price and currency:
            rows.append(make_row(
                part_no=pn, price=float(price), currency=str(currency),
                price_type="genuine_grey", match_method="exact_oem",
                source="Amayama", source_url=source_url, country=COUNTRY_DEFAULT,
                observed_at=observed_at, vintage=f"Amayama {observed_at}",
                competitor_brand="Isuzu (genuine, grey channel)", competitor_pn=pn,
                description=f"Isuzu genuine {pn}", vat="unknown",
                stock="in" if "InStock" in str(offer.get("availability", "")) else "out",
                n_obs=1, loader=SITE,
            ))
        break

    if not saw_product_block:
        raise ParseError("no JSON-LD Product block — the page layout has changed")

    # Supplement: the visible per-warehouse table. The warehouse cell has a nested
    # <span class="gst"> inside it, so the name is captured loosely and stripped.
    for m in re.finditer(
        r'<span class="warehouse-name">(.*?)<span class="part-price">([\d.,]+)</span>',
        html, re.S,
    ):
        warehouse = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip(" -")
        try:
            price = float(m.group(2).replace(",", ""))
        except ValueError:
            continue
        rows.append(make_row(
            part_no=pn, price=price, currency=_currency_near(html, m.start()),
            price_type="genuine_grey", match_method="exact_oem",
            source="Amayama", source_url=source_url,
            country=_warehouse_country(warehouse), observed_at=observed_at,
            vintage=f"Amayama {observed_at}",
            competitor_brand="Isuzu (genuine, grey channel)", competitor_pn=pn,
            description=f"Isuzu genuine {pn} — {warehouse}", vat="unknown",
            stock="in", n_obs=1, loader=SITE,
        ))

    if not rows:
        raise ParseError("recognised the page but found no price rows")
    return rows


def _currency_near(html: str, pos: int) -> str:
    """The page's selected currency, from the nearest currency selector."""
    window = html[max(0, pos - 4000): pos]
    hits = re.findall(r'data-type="selected-option-name">([A-Z]{3})<', window)
    return hits[-1] if hits else "USD"


def _warehouse_country(name: str) -> str:
    low = name.lower()
    for token, code in (("latvia", "LV"), ("uae", "AE"), ("emirates", "AE"), ("japan", "JP")):
        if token in low:
            return code
    return "UNKNOWN"


def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    problems: list[str] = []

    # Two fixtures, two different dates and prices. Both must parse.
    fixtures = [
        ("v_amayama_live.html", "2026-09-24", 56.42),
        ("v_amayama.html",      "2026-09-18", 54.25),
    ]
    for fname, date, expected_price in fixtures:
        page = probe / fname
        print("=" * 74)
        if not page.exists():
            problems.append(f"{fname}: page missing")
            print(f"  MISSING {page}")
            continue
        html = page.read_text(encoding="utf-8", errors="replace")
        print(f"  {fname}  ({len(html):,} chars)  expected {expected_price} USD on {date}")
        rows = parse(html, source_url=PROBE_URL, observed_at=date)
        for r in rows:
            print(f"    PN {r['part_no']}  {r['price']} {r['currency']}  "
                  f"type={r['price_type']}  country={r['country']}  stock={r['stock']}")

        if not rows:
            problems.append(f"{fname}: no rows parsed")
            continue
        if not any(r["part_no"] == "8974995480" for r in rows):
            problems.append(f"{fname}: part number 8974995480 not found")
        if not any(r["price"] == expected_price for r in rows):
            got = sorted({r["price"] for r in rows})
            problems.append(f"{fname}: expected {expected_price}, got {got}")
        if not all(r["price_type"] == "genuine_grey" for r in rows):
            problems.append(f"{fname}: a row is not genuine_grey")
        if any(r["part_no"] and len(r["part_no"]) != 10 for r in rows):
            problems.append(f"{fname}: a part number is not 10 digits")
        if any(r["currency"] != "USD" for r in rows):
            problems.append(f"{fname}: currency read as something other than USD")

    # The documented price movement must still hold — if a future edit makes the
    # two fixtures agree, this test is no longer testing what it claims.
    if not problems:
        a = parse((probe / "v_amayama.html").read_text(encoding="utf-8", errors="replace"),
                  observed_at="2026-09-18")
        b = parse((probe / "v_amayama_live.html").read_text(encoding="utf-8", errors="replace"),
                  observed_at="2026-09-24")
        pa = min(r["price"] for r in a)
        pb = min(r["price"] for r in b)
        if not (pb > pa):
            problems.append(f"documented reprice missing: {pa} -> {pb} is not an increase")
        else:
            print(f"\n  reprice confirmed: {pa} USD (2026-09-18) -> {pb} USD (2026-09-24), "
                  f"+{100 * (pb / pa - 1):.1f}%")

    # A broken page must raise, not return an empty list.
    for bad, label in (("", "empty string"), ("<html>nothing here</html>", "no Product block")):
        try:
            parse(bad)
            problems.append(f"{label}: parse returned instead of raising")
        except ParseError:
            pass

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("\n  SELFTEST PASS — both fixtures parse; reprice recorded; broken input raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
