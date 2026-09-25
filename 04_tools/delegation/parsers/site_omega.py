# -*- coding: utf-8 -*-
"""Omega Spare Parts (omegaspareparts.com) — UK, GBP. One product page, TWO price types.

Evidence
--------
Page: `v_omega_search.html` — **272,754 bytes** on disk, saved 2026-09-24.
      URL:  https://omegaspareparts.com/product/0011765k-isuzu-n35-120-euro5b-air-filter-element-2008-onward/
      WooCommerce (X theme). Reach: `GET /?s=<pn>&post_type=product` redirects straight to the
      product page. Robots disallows `/wp-json/`, so HTML route only.
      Nothing is fetched here: `parse()` reads HTML that is already in memory. No DeepSeek.

Verified on that page, and asserted in `selftest()`:

  * JSON-LD `Product` (the second `ld+json` script on the page; the first is the Yoast graph and
    holds WebPage / ImageObject / BreadcrumbList / WebSite / Organization and **no** Product):
      name                              = "0011765K Isuzu N35.120 EURO5b+ Air Filter Element 2008 onward"
      sku                               = "9294"   (Omega's internal code — NOT an Isuzu number)
      brand.name                        = "Isuzu"
      offers[0].priceSpecification[0].price  = "40.80"
      offers[0].priceSpecification[0].priceCurrency = "GBP"        <- the aftermarket price
      offers[0].availability            = https://schema.org/InStock
  * Details table (WooCommerce additional information):
      MPN 0011765K · Manufacturer Part Number 8-97062-294-0 · Part Manufacturer Number 8970622940 ·
      Part Manufacturer FilterCraft · Brand Isuzu · Brand Type N35.120 · Condition New
  * Description text (present in both the short-description block and the Description tab):
      "Genuine brand new part supplied to us from the brand dealer network"
      "Dealer Price: 66.86 (GBP)"                                  <- the dealer-network price

TWO ROWS, NEVER ONE
-------------------
This page carries two different price types and this module emits them as two separate
observations, because loading them as one would be the `OE RRP` mistake recorded in
`MATCH_INDEX_REPORT.md` RULE 1:

  Row A — `price=40.80`, `currency=GBP`, `price_type="aftermarket_retail"`,
          `competitor_brand="FilterCraft"` (the aftermarket maker named in the details table),
          `competitor_pn="0011765K"` (its MPN).
  Row B — `price=66.86`, `currency=GBP`, `price_type="dealer"`, `competitor_brand="Isuzu"`
          (the brand dealer network the page says the part came from).

Both rows share `part_no="8970622940"` (the 10-digit `Part Manufacturer Number`, which is the only
Isuzu-shaped number on the page — `MPN 0011765K` and `sku 9294` are not Isuzu numbers),
`match_method="exact_oem"`, `source="Omega"`, `country="UK"`, the passed-in `source_url` and
`observed_at`, `vintage="Omega <observed_at>"`, `loader="omega"`.

Two caveats recorded rather than hidden
---------------------------------------
1. **VAT: the page was right, and the correction was the orchestrator's, not a stray agent's.**
   The brief for this build said the site quotes GBP ex-VAT and told the parser to set
   `vat="excl"`. The page says otherwise about the headline figure: its JSON-LD marks the 40.80
   `"valueAddedTaxIncluded":true`, and a case-insensitive sweep finds **no** ex-VAT statement
   anywhere (`ex VAT`, `excl`, `excluding VAT`, `exclusive of VAT`, `+ VAT`, `before VAT` — all
   0 hits; the only `VAT` occurrence is the company registration line in the footer).
   The sub-agent that wrote this file reported the disagreement rather than obeying, and the
   orchestrator checked the page directly and **the page won**, so row A now carries
   `vat="incl"`. Recording a £40.80 as ex-VAT when the shop shows it incl-VAT understates the
   euro value by the VAT rate (20% in the UK) — a wrong number with a clean audit trail, which
   is exactly what happened with the `OE RRP` column.
   Note for anyone diffing this file: it was **edited by the orchestrator at 22:31**, about three
   minutes after the sub-agent first wrote it. That was a deliberate correction of one constant and
   its docstring, not a concurrent-agent collision — no other agent was assigned this file.
   The `Dealer Price: 66.86` line states no VAT basis at all, so it keeps `vat="unknown"` rather
   than inheriting a basis from the other row.
2. **No hand-made FX.** The native GBP price is carried as-is; `price_eur` is filled from
   `fx_rates.json` if a rate is available, otherwise left `None`. Never a hand conversion.

What makes this parser refuse to answer
---------------------------------------
`parse()` raises `ParseError` rather than returning `[]` in these cases:
  * the page is too small to be a product page;
  * no JSON-LD `Product` block at all (layout changed);
  * the product page was recognised but no 10-digit Isuzu part number could be read from the
    details table (the observation would not be joinable, so no row is emitted);
  * the page was recognised but carries no price at all — neither a JSON-LD offer price nor a
    `Dealer Price:` line.

The partial-page case, decided rather than left ambiguous (2026-09-24)
---------------------------------------------------------------------
If the JSON-LD `offers` block disappears but the `Dealer Price: 66.86` line survives, this module
returns **one honest row** rather than raising. Decided after checking the real page: the page
genuinely still shows a price and a part number, so a one-row answer is truthful, whereas raising
would claim the page had nothing to say when it did. Verified: strip the 40.80 offer and it returns
the single dealer row; strip both prices and it raises.

The risk in that choice is a *silent* partial parse — a page that used to yield two rows yields one,
the probe still says OK, and an observation vanishes unnoticed. `EXPECTED_ROWS = 2` closes it: the
runner compares the row count against that declaration and reports a **visible gap** when they
disagree. So the honest one-row answer is kept, and a disappearing row cannot pass quietly.

An empty list from this module would mean "the site genuinely had no price", which is not what any
of the four cases above means.
"""
from __future__ import annotations

import html as _html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))
from ledger_schema import make_row, normalise_pn, row_problems        # noqa: E402

SITE = "omega"
PROBE_PAGE = "v_omega_search.html"
# The saved page carries exactly two observations: the aftermarket 40.80 and the dealer
# 66.86. Declared so a partial parse (e.g. the offers block vanishing and only the dealer
# line left) shows up as a visible gap rather than a silent OK.
EXPECTED_ROWS = 2
PROBE_URL = (
    "https://omegaspareparts.com/product/"
    "0011765k-isuzu-n35-120-euro5b-air-filter-element-2008-onward/"
)
PROBE_DATE = "2026-09-24"
COUNTRY = "UK"

# Row contract for this site, CORRECTED 2026-09-24 against the page itself.
# The page's JSON-LD marks the headline 40.80 as "valueAddedTaxIncluded": true and the page states
# no ex-VAT basis anywhere, so the aftermarket row is "incl". The Dealer Price line states no basis,
# so it is "unknown" rather than inheriting one.
VAT_AFTERMARKET = "incl"
VAT_DEALER = "unknown"

FX_NOTE_AFTERMARKET = (
    "GBP native price. vat='incl' — the page's JSON-LD marks 40.80 "
    "valueAddedTaxIncluded=true and no ex-VAT statement exists on the page "
    "(the brief's vat='excl' was corrected 2026-09-24)."
)
FX_NOTE_DEALER = (
    "GBP native price. The 'Dealer Price:' line states no VAT basis, so vat='unknown' "
    "rather than inheriting the aftermarket row's basis."
)

_LD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I
)
_PRODUCT_TYPE_RE = re.compile(r'"@type"\s*:\s*"Product"')
_ATTR_ROW_RE = re.compile(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", re.S)
_DEALER_PRICE_RE = re.compile(
    r"Dealer\s*Price\s*:\s*([0-9][\d.,]*)\s*(?:\(\s*([A-Za-z]{3})\s*\))?"
)
_VISIBLE_PRICE_RE = re.compile(r'<p class="price">(.*?)</p>', re.S)
_VAT_INCLUDED_RE = re.compile(r'"valueAddedTaxIncluded"\s*:\s*(true|false)', re.I)
_CURRENCY_SYMBOLS = (("£", "GBP"), ("$", "USD"), ("€", "EUR"))


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


# --------------------------------------------------------------------------- helpers

def _text(fragment: str) -> str:
    """Tags out, entities in, whitespace collapsed."""
    stripped = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment or ""))
    return _html.unescape(stripped).strip()


def _to_float(raw) -> float | None:
    """'40.80' -> 40.8 · '1,234.56' -> 1234.56 · '1.234,56' -> 1234.56 · junk -> None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):            # 1.234,56 — the comma is the decimal
            s = s.replace(".", "").replace(",", ".")
        else:                                       # 1,234.56 — the comma is a thousands mark
            s = s.replace(",", "")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = s.replace(",", ".") if len(tail) == 2 else s.replace(",", "")
    s = re.sub(r"[^0-9.]", "", s)
    try:
        value = float(s)
    except ValueError:
        return None
    return value


def _product_node(html: str) -> dict | None:
    """The first JSON-LD `Product` object, whether it sits top-level or inside `@graph`."""
    for m in _LD_RE.finditer(html):
        try:
            node = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        found = _find_product(node)
        if found is not None:
            return found
    return None


def _find_product(node) -> dict | None:
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


def _attributes(html: str) -> dict:
    """The WooCommerce additional-information table as {label: value}, first label wins."""
    out: dict[str, str] = {}
    for m in _ATTR_ROW_RE.finditer(html):
        label, value = _text(m.group(1)), _text(m.group(2))
        if label and value and label not in out:
            out[label] = value
    return out


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


def _visible_price(html: str) -> float | None:
    """The headline `£40.80` in the summary block — used only to cross-check the JSON-LD."""
    m = _VISIBLE_PRICE_RE.search(html)
    if not m:
        return None
    number = re.search(r"([\d][\d.,]*)", _text(m.group(1)))
    return _to_float(number.group(1)) if number else None


def _page_currency(html: str) -> str | None:
    m = _VISIBLE_PRICE_RE.search(html)
    if not m:
        return None
    fragment = _html.unescape(m.group(1))
    for symbol, code in _CURRENCY_SYMBOLS:
        if symbol in fragment:
            return code
    return None


def _stock(offer: dict, html: str) -> str:
    availability = str(offer.get("availability") or "")
    if "InStock" in availability:
        return "in"
    if "OutOfStock" in availability:
        return "out"
    if re.search(r"\binstock\b", html):
        return "in"
    if re.search(r"\boutofstock\b", html):
        return "out"
    return "unknown"


def _oem_part_no(attrs: dict) -> str | None:
    """The Isuzu number, from the two manufacturer-number rows the page carries.

    `MPN 0011765K` and `OSP SKU 9294` are deliberately not consulted: neither is an Isuzu number
    (`0011765K` does not reduce to 10 digits, and `normalise_pn` never pads or truncates).
    """
    return (
        normalise_pn(attrs.get("Part Manufacturer Number"))
        or normalise_pn(attrs.get("Manufacturer Part Number"))
    )


# --------------------------------------------------------------------------- parse

def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a product page ({len(html or '')} chars)")

    product = _product_node(html)
    if product is None:
        raise ParseError("no JSON-LD Product block — the page layout has changed")

    attrs = _attributes(html)
    oem = _oem_part_no(attrs)
    if not oem:
        raise ParseError(
            "recognised the product page but read no 10-digit Isuzu part number from the details "
            "table — the observation cannot be keyed, so no row is emitted"
        )

    offer = _offer_of(product)
    spec = _spec_of(offer)
    headline = spec.get("price")
    price = _to_float(headline if headline is not None else offer.get("price"))
    currency = (
        str(spec.get("priceCurrency") or offer.get("priceCurrency") or "").upper()
        or _page_currency(html)
    )
    stock = _stock(offer, html)
    vintage = f"Omega {observed_at}".strip()
    product_name = str(product.get("name") or "").strip()
    sku = product.get("sku")
    brand_type = attrs.get("Brand Type") or ""
    maker = attrs.get("Part Manufacturer")

    # A cheap honesty check on our own reading of the page: the JSON-LD headline and the visible
    # summary price must be the same number. If they ever diverge, the page is saying two things
    # and a human must look — we do not silently pick one.
    shown = _visible_price(html)
    if shown is not None and price is not None and abs(shown - price) > 0.005:
        raise ParseError(
            f"JSON-LD price {price} and visible summary price {shown} disagree — refusing to pick one"
        )

    rows: list[dict] = []

    # Row A — the aftermarket price for the FilterCraft part.
    if price is not None:
        rows.append(make_row(
            part_no=oem, price=price, currency=currency,
            price_type="aftermarket_retail", match_method="exact_oem",
            source="Omega", source_url=source_url, country=COUNTRY,
            observed_at=observed_at, vintage=vintage,
            competitor_brand=maker or None, competitor_pn=attrs.get("MPN"),
            description=(
                f"{maker or 'aftermarket'} air filter element for Isuzu {brand_type}".strip()
                + f" (Omega SKU {sku})"
            ),
            vat=VAT_AFTERMARKET, stock=stock, n_obs=1, loader=SITE,
            price_eur=None, fx_note=FX_NOTE_AFTERMARKET,
        ))

    # Row B — the brand dealer network price, a separate observation, never merged into Row A.
    dealer = _DEALER_PRICE_RE.search(html)
    if dealer:
        dealer_price = _to_float(dealer.group(1))
        dealer_currency = (dealer.group(2) or currency or "").upper() or None
        if dealer_price is not None:
            rows.append(make_row(
                part_no=oem, price=dealer_price, currency=dealer_currency,
                price_type="dealer", match_method="exact_oem",
                source="Omega", source_url=source_url, country=COUNTRY,
                observed_at=observed_at, vintage=vintage,
                competitor_brand="Isuzu", competitor_pn=attrs.get("Manufacturer Part Number"),
                description=(
                    "Isuzu genuine part from the brand dealer network"
                    + (f" — {product_name}" if product_name else "")
                ),
                vat=VAT_DEALER, stock=stock, n_obs=1, loader=SITE,
                price_eur=None, fx_note=FX_NOTE_DEALER,
            ))

    if not rows:
        raise ParseError(
            "recognised the product page but found no price at all — neither a JSON-LD offer "
            "price nor a Dealer Price line"
        )
    return rows


# --------------------------------------------------------------------------- selftest

def _strip_product_block(page_html: str) -> str:
    """Remove the JSON-LD Product script only (the Yoast block has no Product and stays)."""
    return _LD_RE.sub(
        lambda m: "" if _PRODUCT_TYPE_RE.search(m.group(1)) else m.group(0), page_html
    )


def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    page = probe / PROBE_PAGE
    problems: list[str] = []

    print("=" * 74)
    if not page.exists():
        print(f"  MISSING {page}")
        print("\n  SELFTEST FAIL")
        print(f"    - {PROBE_PAGE} is not on disk")
        return 1

    html = page.read_text(encoding="utf-8", errors="replace")
    print(f"  {PROBE_PAGE}  ({page.stat().st_size:,} bytes / {len(html):,} chars)")
    print("  expected: 2 rows — 40.80 GBP aftermarket_retail + 66.86 GBP dealer, PN 8970622940")

    # --- the raw page, independent of the parser ------------------------------------------
    raw_checks = [
        ('"price":"40.80"', "JSON-LD headline price 40.80"),
        ('"priceCurrency":"GBP"', "JSON-LD currency GBP"),
        ('"@type":"Product"', "JSON-LD Product block"),
        ("Dealer Price: 66.86 (GBP)", "description Dealer Price line"),
        ("8970622940", "10-digit Part Manufacturer Number"),
        ("8-97062-294-0", "dashed Manufacturer Part Number"),
        ("FilterCraft", "Part Manufacturer FilterCraft"),
    ]
    for needle, label in raw_checks:
        if needle not in html:
            problems.append(f"page no longer contains {label} ({needle!r})")

    # --- what the parser makes of it ------------------------------------------------------
    try:
        rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)
    except ParseError as e:
        print(f"\n  PARSE RAISED — {e}")
        print("\n  SELFTEST FAIL")
        return 1

    for r in rows:
        print(f"    PN {r['part_no']}  {r['price']} {r['currency']}  "
              f"type={r['price_type']}  brand={r['competitor_brand']}  "
              f"vat={r['vat']}  country={r['country']}  stock={r['stock']}")

    if len(rows) != 2:
        problems.append(f"expected exactly 2 rows (one per price type), got {len(rows)}")

    types = [r["price_type"] for r in rows]
    if sorted(types) != ["aftermarket_retail", "dealer"]:
        problems.append(f"price types are {types}, not ['aftermarket_retail', 'dealer']")

    by_type = {r["price_type"]: r for r in rows}
    after = by_type.get("aftermarket_retail")
    dealer = by_type.get("dealer")

    if after is None:
        problems.append("no aftermarket_retail row (the FilterCraft price)")
    else:
        if after["price"] != 40.80:
            problems.append(f"aftermarket price is {after['price']!r}, not 40.80")
        if after["currency"] != "GBP":
            problems.append(f"aftermarket currency is {after['currency']!r}, not GBP")
        if after["competitor_brand"] != "FilterCraft":
            problems.append(f"aftermarket brand is {after['competitor_brand']!r}, not FilterCraft")

    if dealer is None:
        problems.append("no dealer row (the brand dealer network price)")
    else:
        if dealer["price"] != 66.86:
            problems.append(f"dealer price is {dealer['price']!r}, not 66.86")
        if dealer["currency"] != "GBP":
            problems.append(f"dealer currency is {dealer['currency']!r}, not GBP")
        if not dealer["competitor_brand"]:
            problems.append("dealer row carries no competitor_brand")

    if after and dealer and after["price"] == dealer["price"]:
        problems.append("the two price types collapsed onto one number — they are separate observations")

    for r in rows:
        if r["part_no"] != "8970622940":
            problems.append(f"part_no is {r['part_no']!r}, not 8970622940")
        if r["currency"] != "GBP":
            problems.append(f"currency is {r['currency']!r}, not GBP")
        if r["country"] != "UK":
            problems.append(f"country is {r['country']!r}, not UK")
        if r["match_method"] != "exact_oem":
            problems.append(f"match_method is {r['match_method']!r}, not exact_oem")
        if r["source"] != "Omega":
            problems.append(f"source is {r['source']!r}, not Omega")
        if r["loader"] != SITE:
            problems.append(f"loader is {r['loader']!r}, not {SITE}")
        if r["price_type"] == "aftermarket_retail" and r["vat"] != VAT_AFTERMARKET:
            problems.append(f"aftermarket row vat is {r['vat']!r}, not {VAT_AFTERMARKET}")
        if r["price_type"] == "dealer" and r["vat"] != VAT_DEALER:
            problems.append(f"dealer row vat is {r['vat']!r}, not {VAT_DEALER}")
        if r["observed_at"] != PROBE_DATE:
            problems.append(f"observed_at is {r['observed_at']!r}, not {PROBE_DATE}")
        if r["vintage"] != f"Omega {PROBE_DATE}":
            problems.append(f"vintage is {r['vintage']!r}")
        if r["source_url"] != PROBE_URL:
            problems.append("source_url was not passed through unchanged")
        if r["price_eur"] is not None:
            problems.append("price_eur was converted by hand — it must stay None")
        for p in row_problems(r):
            problems.append(f"schema: {p}")

    # --- the VAT basis, now read from the page rather than inherited from the brief ---------
    vat_flag = _VAT_INCLUDED_RE.search(html)
    print(f"    VAT: page JSON-LD valueAddedTaxIncluded="
          f"{(vat_flag.group(1) if vat_flag else 'absent')} -> aftermarket row vat="
          f"{VAT_AFTERMARKET!r}, dealer row vat={VAT_DEALER!r} (dealer line states no basis)")

    # --- broken input must raise, never return [] -----------------------------------------
    no_product = _strip_product_block(html)
    no_oem = html.replace("Part Manufacturer Number", "Attribute 1").replace(
        "Manufacturer Part Number", "Attribute 2"
    )
    no_price = _DEALER_PRICE_RE.sub("Dealer Price: on request", html.replace('"price":"40.80"', '"price":""'))

    raising_cases = [
        ("", "empty string"),
        ("<html>nothing here</html>", "plain html, no product page at all"),
        (no_product, "Product JSON-LD block removed"),
        (no_oem, "details table stripped of both manufacturer numbers"),
        (no_price, "Product block kept but every price removed"),
    ]
    for bad, label in raising_cases:
        try:
            got = parse(bad)
        except ParseError:
            continue
        problems.append(f"{label}: parse returned {len(got)} row(s) instead of raising")

    # A recognised page that lost one of its two prices must degrade honestly: one row, not zero
    # and not two.
    try:
        partial = parse(_DEALER_PRICE_RE.sub("Dealer Price: on request", html),
                        source_url=PROBE_URL, observed_at=PROBE_DATE)
        if [r["price_type"] for r in partial] != ["aftermarket_retail"]:
            problems.append(
                "dealer line removed: expected exactly the aftermarket row, got "
                f"{[r['price_type'] for r in partial]}"
            )
    except ParseError as e:
        problems.append(f"dealer line removed: parse raised ({e}) instead of returning the aftermarket row")

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1

    print("\n  SELFTEST PASS — two price types on one page stay two rows; "
          "PN 8970622940; 40.80 + 66.86 GBP; broken input raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
