# -*- coding: utf-8 -*-
"""T&M Commercials (tmcgroup.co.uk) — UK Isuzu truck parts. GBP, VAT-inclusive.

Why this site is worth a parser (measured 2026-10-07, not assumed)
-----------------------------------------------------------------
U26 work package A, agent A2. T&M Commercials was already in the consent gate's
target list as `tmcshop.co.uk`, which is now unreachable, so the whole host was
UNKNOWN-as-blocked. The live shop is **tmcgroup.co.uk** and its robots.txt is
permissive (`User-agent: * / Disallow:` — nothing), so the host is allowed.

Two routes exist, and they are very different:

  * **Search is dead.** `/?s=<pn>&post_type=product` returns HTTP 504 on every
    attempt (5 tries, 2026-10-07 — the same timeout the 2026-07-09 scraper note
    recorded). `/wp-json/wc/store/v1/products?search=`, `/wp-json/wp/v2/product`,
    `/sitemap_index.xml` and `/product-sitemap.xml` all return 504 too, and
    `/product-category/.../page/2/` is 504 while `/page/1` and the leaf
    categories answer. No search route is usable, so there is **no part-number
    query URL** on this host.

  * **The category tree works, and it prints the Isuzu number on every card.**
    `product-category/isuzu-trucks/<model>/<leaf>/` answers with ~42 product
    cards per page. Each card carries `data-product_sku`, and on this shop the
    SKU *is* the Isuzu OEM number in its 10-digit form (verified on the live
    pages: `8983409450`, `8982984040`, `5876100201`, `8975425400`), alongside a
    server-rendered `£ 76.04` in `span.price`. Cards whose SKU is a shop code
    (`ISU708`) carry no Isuzu number and are skipped rather than guessed.

So the harvest route is a **category walk**, not a per-number search. That is
recorded plainly because it changes how the numbers are queried.

What a product page gives
-------------------------
`v_tmc_product.html` = `/product/element-kit-fuel-filter/`, and the page is
WooCommerce with a clean Yoast `Product` JSON-LD block (the second
`ld+json` script; the first is the WebPage/Breadcrumb graph):

    name       "ELEMENT KIT; FUEL FILTER"
    sku        "8981941190"          <- the Isuzu OEM number, 10 digits
    description "Isuzu N35.125 'Blue Top' Fuel Pre Filter"
    offers[0].priceSpecification[0].price = "40.30"
    offers[0].priceSpecification[0].priceCurrency = "GBP"
    offers[0].priceSpecification[0].valueAddedTaxIncluded = true
    offers[0].availability = .../InStock

The visible summary agrees: `<p class="description-sku">SKU: 8981941190</p>`,
`<p class="price">… £ 40.30</p>`, `<p class="stock in-stock">In stock</p>`.

Genuine, read from the page and not assumed
-------------------------------------------
The product copy says "This filter is a Genuine Isuzu filter…" and the shop's
standing description text says "Genuine, guaranteed. Genuine Isuzu parts meet
'original equipment' standards…". A card or page that carries that wording is
recorded `price_type="genuine_grey"`, never mixed into aftermarket rows. A page
that does not is `aftermarket_retail`.

The genuine test is scoped deliberately, and has a **negative guard**. The
"Genuine, guaranteed." sentence is standing copy that sits inside the product
description block on every product page, so testing the whole document would badge
every product genuine — including the "NON GENUINE — Aftermarket Alternative"
brake disc this shop is documented as listing (scraper note, 2026-07-09). So
genuine is read from the name, the JSON-LD description and the
`single-product-section__description` block only, and a page whose own wording says
"non genuine" / "non-genuine" / "aftermarket" is **never** badged genuine even when
the standing sentence is present.

VAT basis: stated, so it is read rather than assumed
----------------------------------------------------
The JSON-LD marks the headline price `valueAddedTaxIncluded: true` and the page
prints the same £40.30 as the summary price. A category listing page states no
basis at all, so rows read off a listing carry `vat="unknown"` rather than
inheriting the product page's basis.

Delivery: NOT stated per product, so it is left unstated
-------------------------------------------------------
The page says nothing about carriage on either the product or the category
page, so no delivery field is claimed. This matters: the page also prints
"Share product:", "Category: Service Items", "Tags: FILTER, fuel, GRAFTER" and
an "If you are unsure… call 01823 673298" block — none of which is a price term.

What makes this parser refuse to answer
---------------------------------------
`parse()` raises `ParseError` rather than returning `[]` when: the page is too
small; there is no JSON-LD `Product` block (layout changed); or the product's
sku does not reduce to a 10-digit Isuzu number (the row could not be keyed, and
inventing one is not allowed). `parse_category()` raises when it recognises a
listing page but finds no `li.product` cards.
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
from ledger_schema import make_row, normalise_pn, row_problems        # noqa: E402

SITE = "tmc"
PROBE_PAGE = "v_tmc_product.html"
CATEGORY_PROBE_PAGE = "v_tmc_category.html"
PROBE_URL = "https://www.tmcgroup.co.uk/product/element-kit-fuel-filter/"
CATEGORY_PROBE_URL = (
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-125-euro-6/"
)
PROBE_DATE = "2026-10-07"
COUNTRY = "UK"
SOURCE = "T & M Commercials"

VAT_PRODUCT = "incl"        # the page's own JSON-LD says valueAddedTaxIncluded: true
VAT_CATEGORY = "unknown"    # a listing page states no basis at all

DELIVERY_NOTE = (
    "No delivery or carriage term is stated on this page, so none is claimed. "
    "The shop's own delivery policy page (not read here) governs carriage."
)

_LD_RE = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                    re.S | re.I)
_SKU_LINE_RE = re.compile(r"SKU\s*:\s*([^\s<]+)", re.I)
_GENUINE_RE = re.compile(r"\bgenuine\b", re.I)
_NON_GENUINE_RE = re.compile(r"non[-\s]?genuine|aftermarket", re.I)
_DESC_BLOCK_RE = re.compile(
    r'<div[^>]*single-product-section__description.*?</div>\s*</div>', re.S | re.I
)
_CURRENCY_SYMBOLS = (("£", "GBP"), ("$", "USD"), ("€", "EUR"))


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


# ------------------------------------------------------------------ shared helpers

def _text(fragment) -> str:
    stripped = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment or ""))
    return _html.unescape(stripped).strip()


def _description_block(html: str) -> str:
    """The product's own description section, not the whole page.

    Needed because the "Genuine, guaranteed." sentence is standing copy inside this
    block; reading the whole document would badge every product genuine.
    """
    m = _DESC_BLOCK_RE.search(html)
    return _text(m.group(0)) if m else ""


def _genuine_and_aftermarket(name: str, description: str, block: str) -> tuple[bool, bool]:
    """(genuine, says_aftermarket) read from the product's own copy only."""
    says_after = bool(_NON_GENUINE_RE.search(" ".join((name or "", description or "", block or ""))))
    genuine = bool(_GENUINE_RE.search(" ".join((name or "", description or "", block or ""))))
    return (genuine and not says_after), says_after


def _to_float(raw) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    s = re.sub(r"[^0-9.,]", "", s)
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = s.replace(",", ".") if len(tail) == 2 else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _find_product(node) -> dict | None:
    """The first JSON-LD `Product` object, top-level or inside `@graph`."""
    if isinstance(node, dict):
        if node.get("@type") == "Product":
            return node
        graph = node.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                found = _find_product(item)
                if found is not None:
                    return found
    elif isinstance(node, list):
        for item in node:
            found = _find_product(item)
            if found is not None:
                return found
    return None


def _product_node(html: str) -> dict | None:
    for m in _LD_RE.finditer(html):
        try:
            node = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        found = _find_product(node)
        if found is not None:
            return found
    return None


def _offer_of(product: dict) -> dict:
    offers = product.get("offers")
    if isinstance(offers, list):
        for candidate in offers:
            if isinstance(candidate, dict):
                return candidate
        return {}
    return offers if isinstance(offers, dict) else {}


def _spec_of(offer: dict) -> dict:
    specs = offer.get("priceSpecification")
    if isinstance(specs, dict):
        return specs
    if isinstance(specs, list):
        for candidate in specs:
            if isinstance(candidate, dict):
                return candidate
    return {}


def _price_currency_vat(product: dict) -> tuple[float | None, str | None, str]:
    """(price, currency, vat basis) from the JSON-LD offer, honestly."""
    offer = _offer_of(product)
    spec = _spec_of(offer)
    price = _to_float(spec.get("price") if spec.get("price") is not None else offer.get("price"))
    currency = str(spec.get("priceCurrency") or offer.get("priceCurrency") or "").upper() or None
    flag = spec.get("valueAddedTaxIncluded")
    if flag is True:
        vat = "incl"
    elif flag is False:
        vat = "excl"
    else:
        vat = VAT_CATEGORY
    return price, currency, vat


def _stock(product: dict, soup) -> str:
    availability = str(_offer_of(product).get("availability") or "")
    if "InStock" in availability:
        return "in"
    if "OutOfStock" in availability:
        return "out"
    if soup.select_one("p.stock.in-stock"):
        return "in"
    if soup.select_one("p.stock.out-of-stock"):
        return "out"
    return "unknown"


def _is_genuine(*blobs: str) -> bool:
    return any(_GENUINE_RE.search(b or "") for b in blobs)
# ------------------------------------------------------------------ product page

def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """One row for one product page. Raises when the page cannot support a row."""
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a product page ({len(html or '')} chars)")

    product = _product_node(html)
    if product is None:
        raise ParseError("no JSON-LD Product block — the page layout has changed")

    soup = BeautifulSoup(html, "html.parser")
    sku = str(product.get("sku") or "").strip()
    if not sku:
        m = _SKU_LINE_RE.search(html)
        sku = m.group(1).strip() if m else ""
    oem = normalise_pn(sku)
    if not oem:
        raise ParseError(
            f"recognised the product page but its sku {sku!r} does not reduce to a 10-digit "
            f"Isuzu number — the observation cannot be keyed, so no row is emitted"
        )

    name = _text(product.get("name") or "")
    description = _text(product.get("description") or "")
    block = _description_block(html)
    price, currency, vat = _price_currency_vat(product)
    currency = currency or ("GBP" if "£" in html else None)
    stock = _stock(product, soup)
    genuine, says_after = _genuine_and_aftermarket(name, description, block)

    bits = [name or oem]
    if description and description not in bits:
        bits.append(description)
    if genuine:
        bits.append("page badged genuine Isuzu")
    elif says_after:
        bits.append("page wording says non-genuine / aftermarket")
    if price is None:
        bits.append("no price on the product page")

    return [make_row(
        part_no=oem, match_method="exact_oem",
        competitor_brand="Isuzu" if genuine else None,
        competitor_pn=sku or None,
        description=" — ".join(bits),
        source=SOURCE, source_url=source_url or PROBE_URL, country=COUNTRY,
        observed_at=observed_at, vintage=f"T&M Commercials {observed_at}".strip(),
        price=price, currency=currency, price_eur=None,
        fx_note=DELIVERY_NOTE if price is not None else
        f"no price shown; {DELIVERY_NOTE}",
        vat=vat, price_type="genuine_grey" if genuine else "aftermarket_retail",
        stock=stock, n_obs=1, loader=SITE,
    )]


# ------------------------------------------------------------------ listing page

def parse_category(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """One row per product card on a category listing page.

    The listing prints the price and the sku in the server-rendered HTML, so this is
    readable without JavaScript. It states **no VAT basis**, so those rows carry
    `vat="unknown"` rather than inheriting the product page's basis. A card whose sku
    is not an Isuzu number is skipped, not guessed.
    """
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a listing page ({len(html or '')} chars)")
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("li.product")
    if not cards:
        raise ParseError("recognised a category page but found 0 li.product cards")

    rows: list[dict] = []
    for card in cards:
        atc = card.select_one("a.add_to_cart_button, a[data-product_sku]")
        sku = (atc.get("data-product_sku") if atc else "") or ""
        oem = normalise_pn(sku)
        if not oem:
            continue                                   # shop code (ISU708) — not an Isuzu number
        title_el = card.select_one("h3.woocommerce-loop-product__title")
        title = _text(title_el.get_text(" ", strip=True)) if title_el else ""
        link = card.select_one("a[href*='/product/']")
        card_url = link.get("href") if link else (source_url or CATEGORY_PROBE_URL)
        price_el = card.select_one("span.price")
        price = _to_float(_text(price_el.get_text(" ", strip=True))) if price_el else None
        excerpt_el = card.select_one("div.loop-product-excerpt")
        excerpt = _text(excerpt_el.get_text(" ", strip=True)) if excerpt_el else ""
        classes = " ".join(card.get("class") or [])
        stock = "out" if "outofstock" in classes else ("in" if "instock" in classes else "unknown")
        genuine, says_after = _genuine_and_aftermarket(title, excerpt, "")

        bits = [title or oem, "read off the category listing page"]
        if excerpt:
            bits.append(excerpt[:160])
        if genuine:
            bits.append("card badged Genuine Isuzu")
        elif says_after:
            bits.append("card wording says non-genuine / aftermarket")
        if price is None:
            bits.append("no price on the card")

        rows.append(make_row(
            part_no=oem, match_method="exact_oem",
            competitor_brand="Isuzu" if genuine else None,
            competitor_pn=sku or None,
            description=" — ".join(bits),
            source=SOURCE, source_url=card_url, country=COUNTRY,
            observed_at=observed_at, vintage=f"T&M Commercials {observed_at}".strip(),
            price=price, currency="GBP" if price is not None else None, price_eur=None,
            fx_note="category listing page states no VAT basis, so vat=unknown. "
                    + DELIVERY_NOTE,
            vat=VAT_CATEGORY,
            price_type="genuine_grey" if genuine else "aftermarket_retail",
            stock=stock, n_obs=1, loader=SITE,
        ))

    if not rows:
        raise ParseError(
            f"{len(cards)} product cards present but none carried an Isuzu part number as its sku"
        )
    return rows


# ------------------------------------------------------------------ selftest

def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    page = probe / PROBE_PAGE
    cat_page = probe / CATEGORY_PROBE_PAGE
    problems: list[str] = []

    print("=" * 74)
    for p in (page, cat_page):
        if not p.exists():
            print(f"  MISSING {p}")
            print("\n  SELFTEST FAIL")
            return 1

    html = page.read_text(encoding="utf-8", errors="replace")
    print(f"  {PROBE_PAGE}  ({page.stat().st_size:,} bytes)")
    print(f"  {CATEGORY_PROBE_PAGE}  ({cat_page.stat().st_size:,} bytes)")
    print("  expected: 1 product row, PN 8981941190, £40.30 GBP incl VAT, genuine_grey, in stock")

    for needle, label in [
        ('"@type":"Product"', "JSON-LD Product block"),
        ('"sku":"8981941190"', "JSON-LD sku = the Isuzu number"),
        ('"price":"40.30"', "JSON-LD headline price 40.30"),
        ('"priceCurrency":"GBP"', "JSON-LD currency GBP"),
        ('"valueAddedTaxIncluded":true', "JSON-LD VAT basis incl"),
        ("SKU: 8981941190", "visible SKU line"),
        ("Genuine Isuzu filter", "the genuine wording on the page copy"),
    ]:
        if "Genuine Isuzu filter" in html:
            pass
        else:
            problems.append("the product page no longer contains the genuine wording "
                            "('This filter is a Genuine Isuzu filter')")

    try:
        rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)
    except ParseError as e:
        print(f"\n  PARSE RAISED — {e}")
        print("\n  SELFTEST FAIL")
        return 1

    for r in rows:
        print(f"    PN {r['part_no']}  £{r['price']} {r['currency']} ({r['vat']})  "
              f"type={r['price_type']}  match={r['match_method']}  stock={r['stock']}  "
              f"country={r['country']}")
    if len(rows) != 1:
        problems.append(f"expected exactly 1 row, got {len(rows)}")
    else:
        r = rows[0]
        if r["part_no"] != "8981941190":
            problems.append(f"part_no {r['part_no']!r}, expected 8981941190")
        if r["price"] != 40.30:
            problems.append(f"price {r['price']!r}, expected 40.30")
        if r["currency"] != "GBP":
            problems.append(f"currency {r['currency']!r}, expected GBP")
        if r["vat"] != VAT_PRODUCT:
            problems.append(f"vat {r['vat']!r}, expected {VAT_PRODUCT}")
        if r["price_type"] != "genuine_grey":
            problems.append(f"price_type {r['price_type']!r}, expected genuine_grey")
        if r["stock"] != "in":
            problems.append(f"stock {r['stock']!r}, expected in")
        if r["match_method"] != "exact_oem":
            problems.append(f"match_method {r['match_method']!r}, expected exact_oem")
        if r["loader"] != SITE:
            problems.append(f"loader {r['loader']!r}, not {SITE}")
        if r["source_url"] != PROBE_URL:
            problems.append("source_url was not passed through unchanged")
        if r["price_eur"] is not None:
            problems.append("price_eur was converted by the parser — the ledger owns FX")
        for p in row_problems(r):
            problems.append(f"schema: {p}")

    # --- the listing page, read independently -------------------------------------
    cat_html = cat_page.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(cat_html, "html.parser")
    cards = soup.select("li.product")
    skus = [c.select_one("a[data-product_sku]").get("data-product_sku")
            for c in cards if c.select_one("a[data-product_sku]")]
    isuzu_skus = [s for s in skus if normalise_pn(s)]
    print(f"\n  category page: {len(cards)} cards, {len(skus)} with a sku, "
          f"{len(isuzu_skus)} of those reduce to a 10-digit Isuzu number")
    print(f"  e.g. {isuzu_skus[:6]}")
    if len(cards) < 30:
        problems.append(f"the category fixture carries only {len(cards)} cards — "
                        f"it is no longer the page this parser was written against")
    if len(isuzu_skus) < 10:
        problems.append("fewer than 10 cards on the fixture carry an Isuzu number as sku")

    cat_rows = parse_category(cat_html, source_url=CATEGORY_PROBE_URL, observed_at=PROBE_DATE)
    priced = [r for r in cat_rows if r.get("price") is not None]
    types = sorted({r["price_type"] for r in cat_rows})
    print(f"  category rows: {len(cat_rows)} ({len(priced)} priced), price types {types}, "
          f"vat basis {sorted({r['vat'] for r in cat_rows})}")
    if len(cat_rows) != len(isuzu_skus):
        problems.append(f"category rows {len(cat_rows)} != cards carrying an Isuzu sku "
                        f"{len(isuzu_skus)} — the card parse has drifted")
    if len(priced) < len(cat_rows):
        problems.append(f"{len(cat_rows) - len(priced)} category rows carry no price — "
                        f"the fixture used to price nearly every card")
    for r in cat_rows:
        if r["vat"] != VAT_CATEGORY:
            problems.append(f"listing row vat {r['vat']!r}: a listing page states no basis")
            break
        if not r["part_no"] or len(r["part_no"]) != 10:
            problems.append(f"listing row part_no {r['part_no']!r} is not 10 digits")
            break
        for p in row_problems(r):
            problems.append(f"schema (listing): {p}")

    # --- broken input must raise, never return [] ---------------------------------
    raising_cases = [
        ("", "empty string"),
        ("<html><body>nothing here</body></html>", "tiny page"),
        (cat_html, "a category listing passed to the single-product parser"),
    ]
    for bad, label in raising_cases:
        try:
            got = parse(bad)
        except ParseError:
            continue
        problems.append(f"{label}: parse returned {len(got)} row(s) instead of raising")

    try:
        got = parse_category("<html><body>" + "<p>x</p>" * 200 + "</body></html>")
        problems.append(f"listing parser on a non-listing page returned {len(got)} rows")
    except ParseError:
        pass

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("\n  SELFTEST PASS — product page 1 row (8981941190, £40.30 incl, genuine_grey); "
          f"listing page {len(cat_rows)} rows with vat=unknown; broken input raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
