# -*- coding: utf-8 -*-
"""KS International — search-results page for one Isuzu part number. GBP, ex-VAT.

Evidence
--------
Page: `v_ks_search.html` — **2,394,154 bytes** on disk, saved 2026-09-24.
       URL: https://www.ks-international.com/catalogsearch/result/?q=8974995480
       Title: `Search results for: '8974995480'`. Magento, server side.
       UTF-8 throughout (the £ signs are real `\\xc2\\xa3`, so no repair pass is needed).

What the page actually contains (counted, not assumed):

  * **exactly ONE product card** — `<li class="item product product-item">`.
    The string `product-item` occurs **54** times on the page, but 53 of those are
    CSS rules (`.product-items .product-item{...}` in the merged stylesheet), the
    Magento ProLabels `data-mage-init` config and the empty compare-sidebar template.
    A substring count over-counts by 53; this parser selects the real card element.
  * **0 JSON-LD blocks, 0 `itemprop` attributes** — nothing to read from structured
    data, so the card is the only evidence. (The Amayama parser can use JSON-LD;
    this page cannot.)
  * The single card, verbatim facts:
      - name `AIR FILTER (GENUINE)` (h2.product-item-name > a.product-item-link)
      - SKU `0707723G` (`<div class="sku"><label>Sku: </label>0707723G</div>`)
      - **ex-VAT £30.00** — `#price-excluding-tax-product-price-17219`,
        `data-price-amount="30"`, `data-label="Excl. VAT"`
      - inc-VAT £36.00 — `#price-including-tax-product-price-17219`,
        `data-price-amount="36.000001"` (Magento float noise for the displayed `£36.00`)
      - `Out of stock` — `<div class="stock unavailable"><span>Out of stock</span></div>`
      - genuine badge: ProLabels `{"text":"Genuine OEM"}` + `(GENUINE)` in the name
      - toolbar agrees: `<span class="toolbar-number">1</span> Item`
      - **no brand element and no Isuzu part number inside the card.**

The important finding, stated plainly
-------------------------------------
The page was searched for `8974995480` and it returned **one** product that is
*not* that number on its face. The searched number appears 12 times on the page,
but every one of those is search plumbing — the `<title>`, the meta title, the
`name="q"` search input, the page-cache URL, the sorter form's `url` and the
Facebook pixel payload. It appears **zero** times inside the product card, whose
SKU is `0707723G`, a KS/supplier code and `normalise_pn` of it is `None` (it is
not an Isuzu number, so it must not be written into `part_no`).

So the card is a **relevance hit, not a proven exact match**. This parser records
that honestly: it emits one row for the card, with

  * `part_no` = the number that was searched for (`8974995480`), because that is
    the only Isuzu number this page has any claim to, and
  * `match_method = "category_only"` — **not** `exact_oem`, because the OEM number
    is not evidenced anywhere on the card.

If a future KS page puts the OEM number inside the card text, the parser flips to
`match_method="exact_oem"` by itself. It never guesses a number that is not on the
page, and it never uses the shop SKU as if it were an Isuzu number.

What it extracts — one row per product card
-------------------------------------------
`price` is the **excluding-VAT** figure, the basis that compares with our list
price, so `vat="excl"`; the including-VAT figure is named in `description`.
`price_type` is `genuine_grey` for a GENUINE-badged card and `aftermarket_retail`
otherwise — never blended. `stock` is `out` when `.stock.unavailable` /
`.out-of-stock` is present. Currency is GBP and country UK, both read from the page
and the site, never converted here (the ledger owns FX; no `price_eur` is written).

A card that shows no ex-VAT price is still emitted, with `price=None` and the
reason in `fx_note` — the `OE RRP` convention: a match row with no price. A
recognised search page that yields **no** card, or cards that yield no row, raises
`ParseError` rather than returning `[]`.
"""
from __future__ import annotations

import html as html_lib
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))
from ledger_schema import find_pns, make_row, normalise_pn, read_delivery_basis  # noqa: E402

SITE = "ks"
PROBE_PAGE = "v_ks_search.html"
PROBE_URL = "https://www.ks-international.com/catalogsearch/result/?q=8974995480"
PROBE_DATE = "2026-09-24"
COUNTRY = "UK"

SOURCE = "KS International"

# The real product card. NOT `li.product-item` on its own — that also matches the
# empty compare-sidebar template, and `.product-item` alone matches 53 CSS rules.
CARD_SELECTOR = "li.item.product.product-item"
GRID_SELECTOR = "div.products.wrapper.grid, ol.product-items"


class ParseError(RuntimeError):
    """The page was not the shape we know, or it had nothing in it. Never return [] for this."""


def _slim_for_parse(html: str) -> str:
    """Keep title, search box and the products grid — drop the Magento chrome.

    Measured 2026-10-05 on `v_ks_search.html` (2.39 MB): full-page BeautifulSoup takes
    ~1.1 s; the same parse on this ~5 KB slice takes ~6 ms and returns the same card.
    At 938 KS pages that is ~18 min vs under a minute. Fallback is the full page so a
    layout change cannot silently empty the parser.
    """
    title_m = re.search(r"<title\b[^>]*>.*?</title>", html, re.I | re.S)
    q_m = re.search(r'<input\b[^>]*\bname=["\']q["\'][^>]*>', html, re.I)
    head = (title_m.group(0) if title_m else "") + (q_m.group(0) if q_m else "")

    start = html.find('<div class="products wrapper')
    if start < 0:
        start = html.find("products wrapper")
        if start >= 0:
            start = html.rfind("<div", 0, start)
    if start < 0:
        # Empty-result pages often have no products wrapper. Title + search box are
        # enough for the recogniser; keep a small tail so "0 product cards" still fires.
        return head + html[:8000] if head else html

    end = html.find('class="toolbar toolbar-products"', start)
    if end < 0:
        end = html.find("toolbar-products", start)
    if end < 0:
        end = html.find("</ol>", start)
        if end >= 0:
            end += len("</ol>")
    if end < 0 or end <= start:
        return head + html[start : start + 200_000]

    return head + html[start : end + 80]


def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """One row per product card on a KS search-results page. Raises if there is none."""
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a search-results page ({len(html or '')} chars)")

    # ~1/3 of the KS volume pages have no product card. Pull the title first so the
    # miss path does not pay for BeautifulSoup at all (measured ~34% of a 80-page sample).
    title_m = re.search(r"<title\b[^>]*>(.*?)</title>", html, re.I | re.S)
    title_raw = html_lib.unescape(title_m.group(1).strip()) if title_m else ""
    if 'li class="item product product-item"' not in html and "item product product-item" not in html:
        if "search results for" in title_raw.lower():
            raise ParseError(
                f"recognised the KS search page ({title_raw!r}) but it carries 0 product cards"
            )
        raise ParseError(
            f"not a KS search-results page (no products grid, title={title_raw!r}) — layout has changed"
        )

    soup = BeautifulSoup(_slim_for_parse(html), "html.parser")

    title_el = soup.find("title")
    title = html_lib.unescape(title_el.get_text(strip=True)) if title_el else title_raw
    looks_like_search = bool(soup.select_one(GRID_SELECTOR)) or "search results for" in title.lower()
    if not looks_like_search:
        raise ParseError(
            f"not a KS search-results page (no products grid, title={title!r}) — layout has changed"
        )

    query_pn = _searched_pn(soup, title)

    cards = soup.select(CARD_SELECTOR)
    if not cards:
        raise ParseError(
            f"recognised the KS search page ({title!r}) but it carries 0 product cards"
        )

    # U26 2026-10-07: the delivery basis, read off the search page. KS states no per-listing
    # delivery term on the card, so this normally returns blank. The shared reader reads the
    # SERVED Page Source (the runner's bytes), so a threshold added later on a product page
    # is not silently read from a different static file. Read once per page, before the loop
    # that builds the rows, so a 2.4 MB Magento page is not rescanned per card.
    _page_text = html or ""
    _del_note_pre, _del_inc_pre = read_delivery_basis(_page_text, price=None, currency="GBP")

    rows: list[dict] = []
    for card in cards:
        row = _card_row(card, query_pn=query_pn, source_url=source_url, observed_at=observed_at,
                        page_text=_page_text, delivery_pre=(_del_note_pre, _del_inc_pre))
        if row:
            rows.append(row)

    if not rows:
        raise ParseError(f"{len(cards)} product card(s) present but none carried a product name")
    return rows


# ── card → row ─────────────────────────────────────────────────────────────────

def _card_row(card, *, query_pn: str | None, source_url: str,
              observed_at: str, page_text: str = "", delivery_pre=None) -> dict | None:
    name_el = (card.select_one("a.product-item-link")
               or card.select_one(".product-item-name a")
               or card.select_one(".product-item-name"))
    name = re.sub(r"\s+", " ", name_el.get_text(" ", strip=True)) if name_el else ""
    if not name:
        return None                                  # a stub, not a product (see ks_scraper)

    card_text = card.get_text(" ", strip=True)

    sku = _sku(card)
    price_ex = _price(card, "excl")
    price_inc = _price(card, "incl")
    genuine = _is_genuine(name, card)
    price_type = "genuine_grey" if genuine else "aftermarket_retail"

    # Is the Isuzu number we searched for actually printed on the card?
    card_pns = find_pns(card_text)
    if card_pns:
        part_no, match_method = card_pns[0], "exact_oem"
    else:
        part_no, match_method = query_pn, "category_only"

    bits = [name]
    if sku:
        bits.append(f"KS sku {sku}")
    if price_inc is not None:
        bits.append(f"inc-VAT £{price_inc:,.2f}")
    if not card_pns and query_pn:
        bits.append(f"no Isuzu {query_pn} on the card — KS relevance hit for our search, "
                    f"not a confirmed exact match")
    if price_ex is None:
        bits.append("no ex-VAT price on the card")

    return make_row(
        part_no=part_no, match_method=match_method,
        competitor_brand=_brand(card), competitor_pn=sku or None,
        description=" — ".join(bits),
        source=SOURCE, source_url=source_url or PROBE_URL, country=COUNTRY,
        observed_at=observed_at, vintage=f"KS International {observed_at}",
        price=price_ex, currency="GBP", price_eur=None,
        fx_note=None if price_ex is not None else "no ex-VAT price shown on the card",
        vat="excl", price_type=price_type, stock=_stock(card, card_text),
        n_obs=1, loader=SITE,
        # No per-listing delivery term is stated on a KS card. Rather than assume blank,
        # the shared reader is given the page: it returns blank when the page says nothing
        # about carriage, and a stated threshold if KS ever publishes one.
        delivery_note=(delivery_pre[0] if delivery_pre else
                       read_delivery_basis(page_text or card_text, price=price_ex,
                                           currency="GBP")[0]),
        delivery_included=(delivery_pre[1] if delivery_pre else
                           read_delivery_basis(page_text or card_text, price=price_ex,
                                               currency="GBP")[1]),
    )


def _sku(card) -> str:
    """The shop's own part code. Never an Isuzu number on this page."""
    el = card.select_one(".product-sku") or card.select_one(".sku")
    if el:
        text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        m = re.search(r"Sku\s*:\s*(\S+)", text, re.I)
        if m:
            return m.group(1).strip()
        text = re.sub(r"^Sku\s*:?\s*", "", text, flags=re.I).strip()
        if text:
            return text
    m = re.search(r"SKU\s*:\s*(\S+)", card.get_text(" ", strip=True), re.I)
    return m.group(1) if m else ""


def _price(card, which: str) -> float | None:
    """30 (ex-VAT) / 36.000001 (inc-VAT) from the price wrapper, or None.

    `which` is "excl" or "incl". The recorded `data-price-amount` is preferred and
    the printed `.price` text is the fallback, so a rounding-free 30 is kept as 30
    and Magento's float noise (36.000001) still lands on the displayed £36.00.
    """
    cls = "price-excluding-tax" if which == "excl" else "price-including-tax"
    wrap = card.select_one(f".{cls}")
    if wrap is not None:
        amount = wrap.get("data-price-amount")
        if amount not in (None, ""):
            try:
                return float(str(amount))
            except ValueError:
                pass
        inner = wrap.select_one(".price")
        if inner is not None:
            return _amount_from_text(inner.get_text(" ", strip=True))
    loose = card.select_one(f".{cls} .price")
    return _amount_from_text(loose.get_text(" ", strip=True)) if loose is not None else None


def _amount_from_text(text: str) -> float | None:
    m = re.search(r"(\d[\d,]*\.?\d*)", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _is_genuine(name: str, card) -> bool:
    """Genuine OEM claim, from the name, the ProLabels badge text or a class."""
    if "GENUINE" in name.upper():
        return True
    if "genuine oem" in card.get_text(" ", strip=True).lower():
        return True
    return card.select_one('[class*="genuine"]') is not None


def _stock(card, card_text: str) -> str:
    out = (card.select_one(".stock.unavailable")
           or card.select_one(".out-of-stock")
           or "out of stock" in card_text.lower())
    return "out" if out else "in"


def _brand(card) -> str | None:
    """A brand the card actually shows, else None. This page shows none."""
    el = card.select_one(".product-brand") or card.select_one(".brand")
    if el is None:
        return None
    text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
    return text or None


def _searched_pn(soup, title: str) -> str | None:
    """The Isuzu number this page was searched for, if it is a part number.

    Read from the search box (`name="q"`), falling back to the page title. A text
    search that is not a part number returns None — never a padded guess.
    """
    box = soup.find("input", attrs={"name": "q"})
    query = ""
    if box is not None and box.get("value"):
        query = html_lib.unescape(str(box.get("value"))).strip()
    if not query:
        m = re.search(r"Search results for:\s*'?([^']+?)'?\s*$", title, re.I)
        if m:
            query = m.group(1).strip()
    return normalise_pn(query)


# ── selftest ───────────────────────────────────────────────────────────────────

def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    page = probe / PROBE_PAGE
    problems: list[str] = []

    print("=" * 74)
    if not page.exists():
        print(f"  MISSING {page}")
        print("\n  SELFTEST FAIL\n    - fixture missing")
        return 1

    raw = page.read_bytes()
    html = raw.decode("utf-8", errors="replace")
    print(f"  {PROBE_PAGE}  ({len(raw):,} bytes on disk, {len(html):,} chars decoded)")
    print(f"  title: {re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip()}")
    print(f"  naive 'product-item' substring count: {html.count('product-item')}  "
          f"(CSS + JS + compare sidebar — NOT the card count)")

    rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)

    # --- what the page really has, asserted from the page ---------------------
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(CARD_SELECTOR)
    priced = [c for c in cards if _price(c, "excl") is not None]
    toolbar = soup.select_one(".toolbar-number")
    toolbar_n = int(re.search(r"\d+", toolbar.get_text()).group()) if toolbar else None

    print(f"  real product cards ({CARD_SELECTOR}): {len(cards)}")
    print(f"  cards with a usable ex-VAT price:      {len(priced)}")
    print(f"  toolbar-amount says:                   {toolbar_n}")
    print(f"  JSON-LD blocks: {len(re.findall(r'application/ld+json', html))}   "
          f"itemprop attributes: {html.count('itemprop=')}")
    print("  rows:")
    for r in rows:
        print(f"    PN {r['part_no']}  £{r['price']} {r['currency']} ({r['vat']})  "
              f"type={r['price_type']}  match={r['match_method']}  "
              f"stock={r['stock']}  country={r['country']}  sku={r['competitor_pn']}")

    if len(cards) != 1:
        problems.append(f"expected exactly 1 product card on this page, found {len(cards)}")
    if len(priced) != 1:
        problems.append(f"expected exactly 1 card with an ex-VAT price, found {len(priced)}")
    if html.count("product-item") <= 10:
        problems.append("the naive product-item count is no longer the documented over-count")
    if toolbar_n != 1:
        problems.append(f"toolbar says {toolbar_n} item(s), expected 1")

    if len(rows) != 1:
        problems.append(f"expected 1 row, got {len(rows)}")
    else:
        r = rows[0]
        # The facts of the one card, quoted from the page.
        if r["part_no"] != "8974995480":
            problems.append(f"part_no {r['part_no']!r}, expected the searched 8974995480")
        if r["match_method"] != "category_only":
            problems.append(f"match_method {r['match_method']!r}: the OEM number is NOT on the "
                            f"card, so exact_oem would be a false claim")
        if r["price"] != 30.0:
            problems.append(f"ex-VAT price {r['price']!r}, expected 30.0")
        if r["currency"] != "GBP":
            problems.append(f"currency {r['currency']!r}, expected GBP")
        if r["vat"] != "excl":
            problems.append(f"vat {r['vat']!r}, expected excl")
        if r["price_type"] != "genuine_grey":
            problems.append(f"price_type {r['price_type']!r}, expected genuine_grey "
                            f"(the card is badged Genuine OEM and named (GENUINE))")
        if r["stock"] != "out":
            problems.append(f"stock {r['stock']!r}, expected out (.stock.unavailable is present)")
        if r["country"] != "UK":
            problems.append(f"country {r['country']!r}, expected UK")
        if r["competitor_pn"] != "0707723G":
            problems.append(f"competitor_pn {r['competitor_pn']!r}, expected the KS sku 0707723G")
        if r["competitor_brand"] is not None:
            problems.append(f"competitor_brand {r['competitor_brand']!r}: the card shows no brand")
        if "36.00" not in (r["description"] or ""):
            problems.append("description does not name the inc-VAT £36.00")
        if r["price_eur"] is not None:
            problems.append("price_eur was converted by the parser — the ledger owns FX")

        # The card must genuinely not carry an Isuzu number: that is the whole
        # reason this row is category_only. If it ever does, this test is stale.
        card = cards[0]
        if find_pns(card.get_text(" ", strip=True)):
            problems.append("the card now contains an Isuzu part number — match_method "
                            "should be exact_oem and this assertion is out of date")
        # And the number we searched for is only in the search plumbing.
        if "8974995480" in card.get_text(" ", strip=True):
            problems.append("the searched number is inside the card after all")
        if html.count("8974995480") < 5:
            problems.append("the searched number is no longer in the page plumbing")

    # --- a page whose structure is gone must RAISE, never return [] -----------
    stripped = html.replace('<li class="item product product-item"',
                            '<li class="card-removed"')
    still_search = bool(BeautifulSoup(stripped, "html.parser").select_one(GRID_SELECTOR))
    if not still_search:
        problems.append("the stripped page is no longer recognisable as a search page — "
                        "this test no longer proves what it claims")
    for bad, label in (
        ("", "empty string"),
        ("<html><body>nothing here</body></html>", "tiny page"),
        (stripped, "search page with the product markers removed"),
        ("<html><body>" + "<p>x</p>" * 200 + "</body></html>", "no search structure"),
    ):
        try:
            out = parse(bad, source_url=PROBE_URL, observed_at=PROBE_DATE)
            problems.append(f"{label}: parse returned {out!r} instead of raising")
        except ParseError as e:
            print(f"  raises as required ({label}): {e}")

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("\n  SELFTEST PASS — 1 card, ex-VAT £30.00 genuine_grey, category_only match; "
          "broken input raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
