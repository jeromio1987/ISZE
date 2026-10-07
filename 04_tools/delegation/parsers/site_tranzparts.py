# -*- coding: utf-8 -*-
"""Tranzparts (tranzparts.co.uk) — UK Isuzu truck parts. GBP, ex-VAT on product pages.

Evidence
--------
Pages on disk, fetched 2026-10-07 through `fetch_polite.PoliteFetcher` (consent gate
first, >= 2.2 s per host):

  * `v_tranzparts_search.html` — search results for Isuzu 8982447940
        URL `https://tranzparts.co.uk/search?q=8982447940&type=product`
        Title `Search: 1 result found for "8982447940" – Tranzparts`
        Shopify, **server-rendered**: one `<product-card>` with `Universal Components`
        / `BRAKE PAD SET` / `£56.58` in `span.price__current > span.js-value`.
  * `v_tranzparts_product.html` — that card's product page
        URL `https://tranzparts.co.uk/products/3651102922`
        JSON-LD `Product`: `sku` and `mpn` `3651102922` (the shop's own code),
        `brand.name` `Universal Components`, `name` `BRAKE PAD SET`,
        `offers.price` `56.58`, `offers.priceCurrency` `GBP`,
        `offers.availability` `…/InStock`.
  * `v_tranzparts_nonisuzu.html` — a product page on the same shop for a brake valve
        (`DOUBLE CHECK VALVE`, sku 3651124775, EBS) whose cross-reference list holds
        **~105 numbers, none of them Isuzu**. This is the page that shaped this parser.

The two findings that shaped this parser
----------------------------------------
**1. The search index answers an Isuzu number and matches on the page's cross-reference
list, not on the card.** Measured across query types (2026-10-07): Isuzu
`8982447940` returns 1 card, `8982169220` returns 2, `8981596930` returns 0, and the
bare aftermarket code `KLTE0272` returns 0. The searched number appears on the search
page only in the title, the canonical URL, the social tags and analytics plumbing —
never inside the `<product-card>`, which prints just vendor, title and price. So a
search is a **route to a product page**, and the product page is the evidence.

**2. The cross-reference list is a mixed competitor list, so reading it as "the Isuzu
numbers on this page" is wrong.** The brake-valve page above lists 105 numbers under
`Cross reference:` — Bosch, Mahle/Knecht, Fleetguard, Brembo, EBS, Mercedes/Wabco —
and shape alone cannot separate them from Isuzu numbers. Measured 2026-10-07: a
leading-digit test (Isuzu 8/1/5 vs the rest) let ten competitor numbers through
(`1102681000`, `5000039183`, `5010038414`, `5021170111`, `8283121000`, …). That
would have put ten fabricated Isuzu part numbers into the ledger with a clean audit
trail. The first version of this parser did exactly that, which is why it is gone.

So this parser implements the toolchain's Mekonomen rule
(`build_scraped_observations.verdict_for`): **the number that was searched for has to
be printed on the page**. `parse()` takes `expected_pn`, returns exactly one row for
that number, and raises when the page does not carry it. Nothing is read off the
cross-reference list into `part_no` at all.

The runner passes the searched number and additionally requires it to appear on the
search page, so a row can never be keyed on a number the shop was not asked about.

VAT and delivery, read off the page
-----------------------------------
**VAT is stated on the product page and not on the search card.** The product page
prints a `product-policies` line reading `EX VAT` under the price, and the site's
terms say "All prices include VAT at 20% (except where indicated)". The "except where
indicated" is that line, so product rows carry `vat="excl"`; the listing card carries
no VAT marker and no row is built from it.

**Delivery is stated and is not part of the price** — free tracked delivery over £80,
otherwise £5.99 ex VAT standard or £19.99 ex VAT next day. The ledger has no delivery
column, so the wording travels in `fx_note` and those amounts are never read as a
part price.

**Genuine is decided from the page, never assumed** — a page whose own text says
GENUINE / ISUZU is `genuine_grey`, one that says "non genuine" / "aftermarket" is not,
and the rest are `aftermarket_retail`.

What makes this parser refuse to answer
---------------------------------------
`parse()` raises `ParseError` rather than returning `[]` when the `expected_pn` is
missing; when the page is too small; when there is no `Product` JSON-LD whose `@type`
is a bare `Product`; or when the page does not print the searched number in any of
its written forms. `parse_search()` raises when the page is not a search-results page
or when a card carries no product link.
"""
from __future__ import annotations

import html as _html
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))
from ledger_schema import normalise_pn, make_row, row_problems               # noqa: E402

SITE = "tranzparts"
PROBE_PAGE = "v_tranzparts_product.html"
PROBE_URL = "https://tranzparts.co.uk/products/3651102922"
PROBE_PN = "8982447940"
SEARCH_PROBE_PAGE = "v_tranzparts_search.html"
SEARCH_PROBE_URL = "https://tranzparts.co.uk/search?q=8982447940&type=product"
# A product page on the same shop that carries ~105 numbers and none of them Isuzu.
NON_ISUZU_PROBE_PAGE = "v_tranzparts_nonisuzu.html"
NON_ISUZU_PROBE_URL = "https://tranzparts.co.uk/products/3651124775"
NON_ISUZU_PROBE_PN = "8982705240"
PROBE_DATE = "2026-10-07"
COUNTRY = "UK"
SOURCE = "Tranzparts"

VAT_PRODUCT = "excl"        # the page prints "EX VAT" under the price
VAT_SEARCH = "unknown"      # a listing card carries no VAT marker

DELIVERY_NOTE = (
    "Delivery is stated separately and is not part of this price: free tracked "
    "delivery over £80 to mainland UK, otherwise £5.99 ex VAT standard (2-3 working "
    "days) or £19.99 ex VAT next working day."
)

_LD_RE = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                    re.S | re.I)
_GENUINE_RE = re.compile(r"\bgenuine\b", re.I)
_NON_GENUINE_RE = re.compile(r"non[\s-]?genuine|aftermarket", re.I)
_SKU_VALUE_RE = re.compile(r'class="product-sku__value"[^>]*>([^<]+)<', re.I)
_EX_VAT_RE = re.compile(r"\bEX\s*VAT\b", re.I)
_CARD_RE = re.compile(r"<product-card\b.*?</product-card>", re.S | re.I)
_SQUASH_RE = re.compile(r"[\s\-./]")


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


# ------------------------------------------------------------------ helpers

def squash(s) -> str:
    """Digits only, so 8-98244-794-0, 8 98244 794 0 and 8982447940 all compare equal."""
    return _SQUASH_RE.sub("", str(s or "")).upper()


def _text(fragment) -> str:
    stripped = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment or ""))
    return _html.unescape(stripped).strip()


def _to_float(raw) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    s = re.sub(r"[^0-9.,]", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = s.replace(",", ".") if len(tail) == 2 else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _product_node(html: str) -> dict | None:
    """The first JSON-LD object whose `@type` is a bare `Product`.

    Deliberately not a recursive `@graph` walk like the Omega/TMC parsers: this site
    emits an Organization block and a BreadcrumbList block before the Product, and a
    loose walk can pick the wrong node. Here `@type` must be exactly `Product`.
    """
    for m in _LD_RE.finditer(html):
        try:
            node = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        for candidate in (node if isinstance(node, list) else [node]):
            if isinstance(candidate, dict) and candidate.get("@type") == "Product":
                return candidate
    return None


def page_carries(html: str, pn: str) -> bool:
    """Is this number printed on the page, in any of the forms the shop writes it?

    The test is the same one the toolchain's Mekonomen guard uses: separators removed
    on both sides, so `8-98244-794-0` and `8982447940` compare equal. A number that is
    only in the query string does not count, because the query is not the page.
    """
    target = squash(pn)
    if not target:
        return False
    return target in squash(html)


def _is_genuine(*blobs: str) -> bool:
    joined = " ".join(b or "" for b in blobs)
    if _NON_GENUINE_RE.search(joined):
        return False
    return bool(_GENUINE_RE.search(joined))


def _stock_from(product: dict, html: str) -> str:
    offers = product.get("offers")
    availability = str((offers or {}).get("availability") or "") if isinstance(offers, dict) else ""
    if "InStock" in availability:
        return "in"
    if "OutOfStock" in availability:
        return "out"
    if re.search(r"\bout of stock\b", html, re.I):
        return "out"
    if re.search(r"\bin stock\b", html, re.I):
        return "in"
    return "unknown"


# ------------------------------------------------------------------ product page

def parse(html: str, *, expected_pn: str = "", source_url: str = "",
          observed_at: str = "") -> list[dict]:
    """One row for the number that was searched for, or nothing.

    `expected_pn` is required for any real page. The page must print that number,
    because the shop's search is a relevance search over a mixed cross-reference list
    and will happily return a brake valve for an oil-filter query. Reading "the Isuzu
    numbers on the page" instead of "the number we asked for" is what fabricated ten
    competitor numbers on 2026-10-07 (see the module docstring).

    The one exception is the saved fixture: `run_probe.py` and the generic builders call
    `parse(html, source_url=..., observed_at=...)` with no number, so when `expected_pn`
    is empty **and** the URL is the probe fixture, `PROBE_PN` is used. That cannot
    misfire on a live page, because a live page always carries its own product URL and
    the runner always passes the number explicitly. Anything else without a number
    raises rather than guessing.
    """
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a product page ({len(html or '')} chars)")
    if not expected_pn:
        if source_url in ("", PROBE_URL):
            expected_pn = PROBE_PN
        else:
            raise ParseError(
                "parse() needs the number that was searched for (expected_pn); without it a "
                "row could only be keyed on a number read off the page, which the 105-number "
                "brake-valve page proves is not safe on this shop"
            )

    product = _product_node(html)
    if product is None:
        raise ParseError("no JSON-LD Product block — the page layout has changed")

    if not page_carries(html, expected_pn):
        raise ParseError(
            f"the searched number {expected_pn} is not printed on this product page — the "
            f"shop returned a different article, so no row is emitted"
        )

    name = _text(product.get("name") or "")
    description = str(product.get("description") or "")
    offer = product.get("offers") if isinstance(product.get("offers"), dict) else {}
    price = _to_float(offer.get("price"))
    currency = str(offer.get("priceCurrency") or "").upper() or ("GBP" if "£" in html else None)
    stock = _stock_from(product, html)
    sku = str(product.get("sku") or "").strip()
    if not sku:
        m = _SKU_VALUE_RE.search(html)
        sku = m.group(1).strip() if m else ""
    brand_node = product.get("brand")
    brand = (brand_node.get("name") if isinstance(brand_node, dict)
             else str(brand_node or "")) or None
    genuine = _is_genuine(name, brand)
    vat = VAT_PRODUCT if _EX_VAT_RE.search(html) else "unknown"

    bits = [name or expected_pn, f"Tranzparts sku {sku}" if sku else ""]
    if brand:
        bits.append(f"brand {brand}")
    bits.append("the number we searched for is printed on this product page")
    if description:
        bits.append(f"page cross-reference list: {description[:180].strip()}")
    if genuine:
        bits.append("page badged genuine")

    return [make_row(
        part_no=expected_pn, match_method="exact_oem",
        competitor_brand=brand or ("Isuzu" if genuine else None),
        competitor_pn=sku or None,
        description=" — ".join(b for b in bits if b),
        source=SOURCE, source_url=source_url or PROBE_URL, country=COUNTRY,
        observed_at=observed_at, vintage=f"Tranzparts {observed_at}".strip(),
        price=price, currency=currency, price_eur=None,
        fx_note=DELIVERY_NOTE, vat=vat,
        price_type="genuine_grey" if genuine else "aftermarket_retail",
        stock=stock, n_obs=1, loader=SITE,
    )]


# ------------------------------------------------------------------ search page

def parse_search(html: str, *, source_url: str = "") -> dict:
    """Read a search-results page: the query, the result count, and the candidates.

    Returns `{"query", "result_count", "candidates": [{url, title, vendor, price,
    currency, vat}]}`. **No ledger rows** — a card does not print the Isuzu number, so
    a card cannot evidence a match. The runner checks the searched number is on the
    page and then follows each candidate URL, letting `parse()` build the row.
    """
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a search page ({len(html or '')} chars)")
    title_m = re.search(r"<title\b[^>]*>(.*?)</title>", html, re.I | re.S)
    title = _html.unescape(title_m.group(1).strip()) if title_m else ""
    if "result" not in title.lower() or "tranzparts" not in title.lower():
        raise ParseError(f"not a Tranzparts search-results page (title={title!r})")

    q_m = re.search(r"result[s]? found for\s*\"?([^\"]+?)\"?\s*[–\-]", title)
    query = q_m.group(1).strip() if q_m else ""
    n_m = re.search(r"(\d+)\s+result", title, re.I)
    count = int(n_m.group(1)) if n_m else None

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("product-card")
    candidates: list[dict] = []
    for card in cards:
        link = card.select_one("a.js-prod-link") or card.select_one("a[href*='/products/']")
        href = link.get("href") if link else None
        if not href:
            raise ParseError("a search card carries no product link — layout has changed")
        if href.startswith("/"):
            href = "https://tranzparts.co.uk" + href
        title_el = card.select_one("p.card__title") or card.select_one(".card__title")
        vendor_el = card.select_one("p.card__vendor") or card.select_one(".card__vendor")
        price_el = (card.select_one("span.price__current .js-value")
                    or card.select_one("span.price__current"))
        card_text = _text(card.get_text(" ", strip=True))
        candidates.append({
            "url": href,
            "title": _text(title_el.get_text(" ", strip=True)) if title_el else "",
            "vendor": _text(vendor_el.get_text(" ", strip=True)) if vendor_el else "",
            "price": _to_float(_text(price_el.get_text(" ", strip=True))) if price_el else None,
            "currency": "GBP" if "£" in card_text else None,
            "vat": VAT_SEARCH,
        })

    if count and count != len(candidates):
        print(f"    note: title says {count} result(s), {len(candidates)} card(s) parsed")
    return {"query": query, "result_count": count, "candidates": candidates,
            "url": source_url}


# ------------------------------------------------------------------ selftest

def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    page = probe / PROBE_PAGE
    search_page = probe / SEARCH_PROBE_PAGE
    ni_page = probe / NON_ISUZU_PROBE_PAGE
    problems: list[str] = []

    print("=" * 74)
    for p in (page, search_page, ni_page):
        if not p.exists():
            print(f"  MISSING {p}")
            print("\n  SELFTEST FAIL")
            return 1

    html = page.read_text(encoding="utf-8", errors="replace")
    print(f"  {PROBE_PAGE}  ({page.stat().st_size:,} bytes)")
    print(f"  {SEARCH_PROBE_PAGE}  ({search_page.stat().st_size:,} bytes)")
    print(f"  {NON_ISUZU_PROBE_PAGE}  ({ni_page.stat().st_size:,} bytes)")
    print("  expected: 1 row for the searched 8982447940, £56.58 GBP ex VAT, "
          "aftermarket_retail, in stock")

    for needle, label in [
        ('"@type":"Product"', "JSON-LD Product block"),
        ('"price":"56.58"', "JSON-LD headline price 56.58"),
        ('"priceCurrency":"GBP"', "JSON-LD currency GBP"),
        ('"availability":"http:\\/\\/schema.org\\/InStock"', "JSON-LD availability InStock"),
        ("Cross References:", "a cross-reference list"),
        ("8982447940", "the searched number"),
        ('"sku":"3651102922"', "the shop's own sku"),
        ("Universal Components", "the vendor"),
        ("EX VAT", "the ex-VAT marker under the price"),
        ("£5.99", "the delivery charge wording"),
    ]:
        if needle not in html:
            problems.append(f"the product page no longer contains {label} ({needle!r})")

    rows = parse(html, expected_pn=PROBE_PN, source_url=PROBE_URL, observed_at=PROBE_DATE)
    for r in rows:
        print(f"    PN {r['part_no']}  £{r['price']} {r['currency']} ({r['vat']})  "
              f"type={r['price_type']}  match={r['match_method']}  stock={r['stock']}  "
              f"brand={r['competitor_brand']}")
    if len(rows) != 1:
        problems.append(f"expected exactly 1 row, got {len(rows)}")
    else:
        r = rows[0]
        if r["part_no"] != PROBE_PN:
            problems.append(f"part_no {r['part_no']!r}, expected the searched {PROBE_PN}")
        if r["price"] != 56.58:
            problems.append(f"price {r['price']!r}, expected 56.58")
        if r["currency"] != "GBP":
            problems.append(f"currency {r['currency']!r}, expected GBP")
        if r["vat"] != VAT_PRODUCT:
            problems.append(f"vat {r['vat']!r}, expected {VAT_PRODUCT} (the page prints EX VAT)")
        if r["price_type"] != "aftermarket_retail":
            problems.append(f"price_type {r['price_type']!r}, expected aftermarket_retail")
        if r["stock"] != "in":
            problems.append(f"stock {r['stock']!r}, expected in")
        if r["match_method"] != "exact_oem":
            problems.append(f"match_method {r['match_method']!r}, expected exact_oem")
        if r["price"] in (5.99, 19.99):
            problems.append("the delivery charge was read as a part price")
        if r["price_eur"] is not None:
            problems.append("price_eur was converted by the parser — the ledger owns FX")
        for p in row_problems(r):
            problems.append(f"schema: {p}")

    # The same page queried for its OTHER cross-referenced Isuzu number must answer that
    # number, keyed on the query — not on whatever the cross-reference list happens to say.
    other = [r for r in parse(html, expected_pn="8982169220", source_url=PROBE_URL,
                              observed_at=PROBE_DATE)]
    print(f"    queried 8982169220 -> {len(other)} row(s), part_no "
          f"{[r['part_no'] for r in other]}")
    if len(other) != 1 or other[0]["part_no"] != "8982169220":
        problems.append("a second query against the same page did not key on the queried number")

    # --- the contamination guard, on the real brake-valve page --------------------
    ni_html = ni_page.read_text(encoding="utf-8", errors="replace")
    ni_product = _product_node(ni_html) or {}
    ni_desc = str(ni_product.get("description") or "")
    printed = [t.strip() for t in re.split(r"[,\s]+", ni_desc) if t.strip()]
    ten_digit = [t for t in printed if len(re.sub(r"\D", "", t)) == 10 and re.search(r"\d", t)]
    print(f"\n  contamination fixture: {len(ten_digit)} ten-digit numbers in its "
          f"cross-reference list, and {ni_html.count('8982705240')} sign(s) of the Isuzu "
          f"number we would ask for")
    print(f"    e.g. {ten_digit[:8]}")
    if len(ten_digit) < 20:
        problems.append(f"the contamination fixture now lists only {len(ten_digit)} ten-digit "
                        f"numbers — it no longer tests what it was saved for")
    for pn in ("0004203571", "0004290047", "4425000900", "1102681000", "8283121000"):
        if pn not in ten_digit:
            problems.append(f"the fixture no longer contains the competitor number {pn}, so "
                            f"the guard is not exercised on a real value")
    if page_carries(ni_html, NON_ISUZU_PROBE_PN):
        problems.append(f"the brake-valve page unexpectedly prints {NON_ISUZU_PROBE_PN} — the "
                        f"guard is no longer being tested against a number that is absent")
    try:
        got = parse(ni_html, expected_pn=NON_ISUZU_PROBE_PN, source_url=NON_ISUZU_PROBE_URL,
                    observed_at=PROBE_DATE)
        problems.append(f"the brake-valve page produced {len(got)} row(s) "
                        f"({[r['part_no'] for r in got][:5]}) for a number it does not print")
    except ParseError as e:
        print(f"    raises as required: {str(e)[:110]}")

    # --- the search page, and the reason it cannot produce rows -------------------
    s_html = search_page.read_text(encoding="utf-8", errors="replace")
    found = parse_search(s_html, source_url=SEARCH_PROBE_URL)
    print(f"\n  search page: query={found['query']!r} title says {found['result_count']} "
          f"result(s), {len(found['candidates'])} candidate(s)")
    for c in found["candidates"]:
        print(f"    {c['vendor']} | {c['title']} | £{c['price']} | {c['url']}")
    if found["query"] != PROBE_PN:
        problems.append(f"search query read as {found['query']!r}, expected {PROBE_PN}")
    if found["result_count"] != 1:
        problems.append(f"search result count read as {found['result_count']}, expected 1")
    if len(found["candidates"]) != 1:
        problems.append(f"{len(found['candidates'])} candidates, expected 1")
    if found["candidates"]:
        c = found["candidates"][0]
        if c["price"] != 56.58:
            problems.append(f"candidate price {c['price']!r}, expected 56.58")
        if not c["url"].startswith("https://tranzparts.co.uk/products/"):
            problems.append(f"candidate url {c['url']!r} is not a product URL")
        if c["vat"] != VAT_SEARCH:
            problems.append(f"candidate vat {c['vat']!r}, expected {VAT_SEARCH}")

    # The guard is "the number is absent from every product card", not a raw page count.
    # The number legitimately appears several times elsewhere — title, canonical, social
    # tags, an inline page-cache URL, the Shopify `search_submitted` event and its
    # `Performed Search` call; all were read by hand on the live page.
    card_slices = _CARD_RE.findall(s_html)
    if not card_slices:
        problems.append("no <product-card> element found in the search HTML at all")
    for slice_html in card_slices:
        if PROBE_PN in slice_html:
            problems.append("the searched number is now inside a search card — revisit the "
                            "product-page route this parser is built on")
    outside_count = _CARD_RE.sub("", s_html).count(PROBE_PN)
    print(f"  searched number: {len(card_slices)} card(s), {outside_count} occurrence(s) "
          f"outside the cards (title/canonical/social/analytics)")
    if outside_count < 3:
        problems.append(f"the searched number appears only {outside_count} time(s) outside the "
                        f"cards — expected the documented search plumbing; page changed shape?")

    # --- broken input must raise, never return [] ---------------------------------
    for bad, label in [
        ("", "empty string"),
        ("<html><body>nothing here</body></html>", "tiny page"),
        (search_page.read_text(encoding="utf-8", errors="replace"),
         "a search-results page passed to the product parser"),
    ]:
        try:
            got = parse(bad, expected_pn=PROBE_PN)
        except ParseError:
            continue
        problems.append(f"{label}: parse returned {len(got)} row(s) instead of raising")

    try:
        parse(html, source_url="https://tranzparts.co.uk/products/some-other-item",
              observed_at=PROBE_DATE)
        problems.append("parse() answered for a non-fixture URL without being told which "
                        "number was searched for")
    except ParseError:
        pass

    try:
        parse_search(page.read_text(encoding="utf-8", errors="replace"))
        problems.append("parse_search accepted a product page")
    except ParseError:
        pass

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print(f"\n  SELFTEST PASS — product page 1 row keyed on the searched number "
          f"({PROBE_PN}, £56.58 ex VAT, aftermarket_retail); the 105-number brake-valve page "
          f"raises instead of fabricating rows; search page yields candidates only")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
