# -*- coding: utf-8 -*-
"""Autoline Danmark — USED-parts marketplace. Good for MATCHING, weak for pricing.

Evidence
--------
Page: `v_autoline_isuzu.html` (757,870 bytes on disk / 742,824 chars decoded)
      Fetched 2026-09-24 through the consent gate (ALLOWED for this path), saved by the
      Phase 1 recon. URL: https://autoline.dk/-/reservedele/Isuzu--c456tm2615
      Category note: `--c456` is the spare-parts category; `--c6` alone is military
      vehicles, and robots.txt disallows `/search/` and `/search.php`.

What was verified on that page (asserted in `selftest()`, not assumed)
---------------------------------------------------------------------
1. One JSON-LD `ItemList` block:
   `offers` = `AggregateOffer`, priceCurrency **DKK**, offerCount **578**,
   lowPrice "220", highPrice "41000". `itemListElement` = **4** `ListItem`s, one
   `Product` each with `name`, `url`, `brand.name`, `description` and its own
   `offers` (`price`, `priceCurrency`, `availability`, `itemCondition`).

   **The listing currency is per row and is NOT the aggregate's.**
   The four listings are, in order:
       1. `Baklucka Isuzu til Isuzu D-Max bil`      500 SEK   (UsedCondition)
       2. `Isuzu D-Max karrosseri til bil`         2000 SEK   (UsedCondition)
       3. `8-97368-919-0 bremsekaliber ...`         200 EUR   (UsedCondition)
       4. `1-13650133-0 pumpe til Isuzu`         205.09 USD   (NewCondition)
   Three currencies, none of them the aggregate's DKK. Stamping every row
   "DKK" from the aggregate would be wrong on all four, so the currency is read from
   each row's own `offers.priceCurrency`.

2. The rendered list carries **25** listings (`div.item.sales-list-item` with
   `data-code` and `data-name`). **16** of those titles carry an Isuzu part number and
   go out as rows; **9** do not and are skipped (see the coverage note below). Only
   **4** listings on the page show a price at all — the same four as the JSON-LD, so
   every priced listing is covered by its own offer. The other 21 show
   `Pris efter forespørgsel` = "price on request" = **no price**, and are emitted as
   match rows with `price=None` (the OE-RRP convention: keep the match, record honestly
   that there is no price). Nothing is defaulted when there is no price.

3. `itemCondition` is `UsedCondition` for the three used listings and `NewCondition`
   for the fourth — but **these are marketplace listings of used or one-off parts**.
   `price_type = "marketplace"` on every row so that a listing price from this site can
   never be blended with a new-part price from this or any other source. Two rendered
   listings carry `Tilstand: ny` (the seller says new); **neither yields an Isuzu
   number**, so no emitted row is a new part, and a row is never re-typed out of
   `marketplace` on the strength of a seller's one-word claim.

Honest assessment of the source
-------------------------------
This is a used-parts marketplace, not a price list. Its Isuzu OEM numbers in the
listing titles are a genuine **match source** — a real second-hand asking price
attached to an Isuzu number is evidence that the number exists in the field. It is
**weak for price comparison**: 21 of the 25 listings show no price at all, the four
that do are one-off used or single new parts in three currencies (none of them the
aggregate's DKK), and a used rear axle is not comparable with a new one. Do not
average these rows with anything.

Coverage caveats recorded, not hidden
-------------------------------------
- 9 of the 25 rendered listings yield no Isuzu number from the title (`4JH1-X motor`,
  `Isuzu D-Max karrosseri`, `451-01013`, `898287808` — 9 digits, `1-13650133-0` …).
  They are skipped because the ledger requires a 10-digit `part_no`, and the brief
  forbids inventing one. The 3 priced listings among them are therefore **not** rows
  even though they carry a price; the selftest prints exactly which.
- `find_pns` accepts any 10-digit code in a title, not only `8…` Isuzu numbers
  (e.g. `3811502920`). That is the project's shared rule for this field, so it is
  followed here — and it is why `000 bremsekaliber` and `451-01013` are skipped while
  `3811502920` is kept.
- `country` is `"DK"` (the marketplace's own market, per the module contract). The
  seller's physical location (Italy, Turkey, Sweden, Poland, UK) is written into each
  row's description, because a used Italian caliper is not a Danish price.
- No currency conversion happens here. `price_eur` stays `None` and `fx_note` says why
  rather than guessing a rate: the ledger's FX table (`build_price_ledger.py`) holds
  EUR / GBP / SEK only, so a DKK or USD row would be refused at load, and a SEK row
  would be converted by the ledger's own table, which owns that decision.
  (`build_price_ledger.py` is not edited by this module and stays the authority on FX.)
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
from ledger_schema import find_pns, make_row, row_problems          # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

SITE = "autoline"
PROBE_PAGE = "v_autoline_isuzu.html"
PROBE_URL = "https://autoline.dk/-/reservedele/Isuzu--c456tm2615"
PROBE_DATE = "2026-09-24"
COUNTRY = "DK"

SOURCE_NAME = "Autoline Danmark"
PRICE_ON_REQUEST_MARKER = "foresp"          # `Pris efter forespørgsel`, accent-free test
# Mirrors the keys of build_price_ledger.FX (read-only copy, see _selftest_schema.py):
# a currency outside this set cannot be converted by the ledger and must be reported.
_LEDGER_FX = ("EUR", "GBP", "SEK")

_LDJSON_RE = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                        re.S | re.I)
_ITEM_RE = re.compile(
    r'<div class="item sales-list-item[^"]*"[^>]*?data-code="(\d+)"\s+data-name="([^"]*)"')
_ADVERT_CODE_IN_URL_RE = re.compile(r"--(\d+)(?:[?#].*)?$")
_PRICE_TEXT_RE = re.compile(r'<span class="price-value([^"]*)"[^>]*>(.*?)</span>', re.S)
_SELLER_RE = re.compile(r'branding-company-name"[^>]*>(.*?)</div>\s*</div>', re.S)
_LOCATION_RE = re.compile(r'class="location-text">(.*?)</span>', re.S)
_REFS_RE = re.compile(r'title="referencenummer">\s*<span class="value">(.*?)</span>', re.S)
_CONDITION_RE = re.compile(
    r'title="tilstand">\s*<span class="name">.*?</span>\s*<span class="value">(.*?)</span>', re.S)
_HREF_RE = re.compile(r'href="(https://autoline\.dk/[^"]+)"')


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


# ---------------------------------------------------------------------------
# Layer readers
# ---------------------------------------------------------------------------
def _itemlist(html: str) -> dict | None:
    """The JSON-LD `ItemList` node, or None if this page has none."""
    for block in _LDJSON_RE.findall(html):
        try:
            node = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(node, dict) and node.get("@type") == "ItemList":
            return node
    return None


def _offer_index(itemlist: dict) -> dict[str, dict]:
    """`{advert code: the listing's own offers dict}` from the ItemList.

    The advert code is the numeric suffix of the listing URL (`...--25071116164283230700`),
    which is the same code the rendered listing carries in `data-code`. That is the only
    join between the JSON-LD layer and the rendered layer.
    """
    out: dict[str, dict] = {}
    for el in itemlist.get("itemListElement") or []:
        item = (el or {}).get("item") if isinstance(el, dict) else None
        if not isinstance(item, dict):
            continue
        m = _ADVERT_CODE_IN_URL_RE.search(str(item.get("url") or ""))
        if not m:
            continue
        out[m.group(1)] = {
            "offers": item.get("offers") if isinstance(item.get("offers"), dict) else {},
            "brand": (item.get("brand") or {}).get("name") if isinstance(item.get("brand"), dict) else None,
        }
    return out


def _to_float(value) -> float | None:
    """A price from the page as a positive float, or None. Never invents a number."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if float(value) > 0 else None
    s = re.sub(r"[^\d.,]", "", str(value).strip())
    if not s:
        return None
    if "," in s and "." in s:                       # 1.234,56 -> 1234.56 ; 1,234.56 -> 1234.56
        s = (s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".")
             else s.replace(",", ""))
    elif "," in s:
        s = s.replace(",", ".")
    try:
        f = float(s)
    except ValueError:
        return None
    return f if f > 0 else None


def _offer_price(offer: dict) -> tuple[float | None, str | None]:
    """(price, currency) from one listing's own offer.

    A price without a currency is dropped rather than defaulted: guessing the currency
    is exactly the mistake that would put a used part in the wrong money.
    """
    price = _to_float(offer.get("price"))
    currency = offer.get("priceCurrency")
    currency = str(currency).upper() if currency else None
    if price is None or not currency:
        return None, None
    return price, currency


def _clean(text: str | None) -> str:
    """HTML entity + tag strip, whitespace collapsed."""
    text = _html.unescape(str(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _first(pattern: re.Pattern, seg: str) -> str | None:
    m = pattern.search(seg)
    if not m:
        return None
    value = _clean(m.group(1))
    return value or None


def _availability(offer: dict) -> str:
    avail = str(offer.get("availability") or "")
    if "InStock" in avail:
        return "in"
    if "OutOfStock" in avail:
        return "out"
    return "unknown"


def _fx_note(currency: str | None) -> str | None:
    """Why `price_eur` is empty, when the ledger cannot convert this currency."""
    if not currency or currency in _LEDGER_FX:
        return None
    return f"{currency}: no rate in the ledger FX table as of {PROBE_DATE}"


def _price_spans(seg: str) -> list[str]:
    """The visible price texts of one rendered listing block.

    `Pris efter forespørgsel` ("price on request") arrives in the same element as a real
    price, so it is filtered out here and the caller only ever sees real price text.
    """
    out: list[str] = []
    for m in _PRICE_TEXT_RE.finditer(seg):
        text = _clean(m.group(2))
        if text and PRICE_ON_REQUEST_MARKER not in text.lower():
            out.append(text)
    return out


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------
def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """One saved autoline.dk Isuzu listing page -> ledger rows.

    Every row is `price_type="marketplace"` (used parts), `match_method="exact_oem"`
    (the number came out of the listing title) and `country="DK"`. A listing whose
    title carries no Isuzu number is skipped — the ledger refuses a row without a
    10-digit `part_no`, and no number is invented to fill the gap.

    Raises `ParseError` when the page is not the shape this parser knows, or when the
    shape is there but nothing was extracted. It never returns `[]` for a page it
    recognised.
    """
    if not html or len(html) < 5000:
        raise ParseError(f"page too small to be an autoline listing page ({len(html or '')} chars)")

    itemlist = _itemlist(html)
    if itemlist is None:
        raise ParseError("no JSON-LD ItemList block — the page layout has changed")

    aggregate = itemlist.get("offers") or {}
    if not isinstance(aggregate, dict) or aggregate.get("@type") != "AggregateOffer":
        raise ParseError("ItemList carries no AggregateOffer — the page layout has changed")
    if not (itemlist.get("itemListElement") or []):
        raise ParseError("ItemList carries no itemListElement — the page layout has changed")

    offers = _offer_index(itemlist)

    blocks = list(_ITEM_RE.finditer(html))
    if not blocks:
        raise ParseError("no rendered listing blocks (item sales-list-item) — layout has changed")

    rows: list[dict] = []
    for i, m in enumerate(blocks):
        end = blocks[i + 1].start() if i + 1 < len(blocks) else len(html)
        seg = html[m.start():end]
        code = m.group(1)
        title = _clean(m.group(2))

        pns = find_pns(title)
        if not pns:
            # No Isuzu number in the title -> not a ledger match row. Reported by the
            # caller's coverage note; never padded with an invented number.
            continue
        pn = pns[0]

        entry = offers.get(code) or {}
        offer = entry.get("offers") or {}
        price, currency = _offer_price(offer)

        seller = _first(_SELLER_RE, seg)
        location = _first(_LOCATION_RE, seg)
        refs = _first(_REFS_RE, seg)
        condition = (_first(_CONDITION_RE, seg) or "").lower()
        condition = "new" if re.search(r"\bny\b|new", condition) else "used"

        url = source_url or PROBE_URL
        href = _HREF_RE.search(seg)
        if href:
            url = _html.unescape(href.group(1))

        description = [f"Autoline marketplace listing: {title}"]
        if seller:
            description.append(f"seller {seller}")
        if location:
            description.append(location)
        if refs:
            description.append(f"ref {refs}")
        if price is None:
            description.append("price on request — no price on the listing")
        if condition == "new":
            description.append("marked new by the seller")

        rows.append(make_row(
            part_no=pn,
            match_method="exact_oem",
            competitor_brand=seller or entry.get("brand") or None,
            competitor_pn=pn,
            description=" | ".join(description),
            source=SOURCE_NAME,
            source_url=url,
            country=COUNTRY,
            observed_at=observed_at,
            vintage=f"Autoline {observed_at}",
            price=price,
            price_avg=None,
            currency=currency,
            price_eur=None,
            fx_note=_fx_note(currency),
            vat="unknown",
            price_type="marketplace",
            stock=_availability(offer),
            n_obs=1,
            loader=SITE,
        ))

    if not rows:
        raise ParseError("recognised the ItemList and the listing blocks but found "
                         "no Isuzu part numbers in any title")
    return rows


# ---------------------------------------------------------------------------
# Self-test — against the saved page, no network
# ---------------------------------------------------------------------------
def _coverage(html: str) -> dict:
    """What the page holds and what the parser does with it. For the selftest only."""
    blocks = list(_ITEM_RE.finditer(html))
    itemlist = _itemlist(html) or {}
    offers = _offer_index(itemlist)
    priced_titles, unpriced_titles, skipped, price_texts = [], [], [], []
    for i, m in enumerate(blocks):
        end = blocks[i + 1].start() if i + 1 < len(blocks) else len(html)
        seg = html[m.start():end]
        title = _clean(m.group(2))
        texts = _price_spans(seg)
        price_texts.extend(texts)
        has_price = bool(_offer_price(offers.get(m.group(1), {}).get("offers") or {})[0]) \
            or bool(texts)
        (priced_titles if has_price else unpriced_titles).append(title)
        if not find_pns(title):
            skipped.append(title)
    return {
        "blocks": len(blocks),
        "itemlist_elements": len(itemlist.get("itemListElement") or []),
        "priced": priced_titles,
        "unpriced": len(unpriced_titles),
        "skipped": skipped,
        "price_texts": price_texts,
    }


def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    page = probe / PROBE_PAGE
    problems: list[str] = []

    print("Autoline parser — selftest against the saved page")
    if not page.exists():
        print(f"  SELFTEST FAIL — saved page missing: {page}")
        return 1

    raw = page.read_bytes()
    html = page.read_text(encoding="utf-8", errors="replace")
    print(f"  page      : {page}")
    print(f"  bytes     : {len(raw):,} on disk / {len(html):,} chars decoded")

    # --- layer 1: the JSON-LD ItemList -------------------------------------
    itemlist = _itemlist(html)
    if itemlist is None:
        problems.append("no JSON-LD ItemList block found")
    else:
        agg = itemlist.get("offers") or {}
        print(f"  ItemList  : {agg.get('@type')} {agg.get('priceCurrency')} "
              f"offers={agg.get('offerCount')} low={agg.get('lowPrice')} high={agg.get('highPrice')}")
        if agg.get("priceCurrency") != "DKK":
            problems.append(f"aggregate currency is {agg.get('priceCurrency')!r}, expected DKK")
        if agg.get("offerCount") != 578:
            problems.append(f"aggregate offerCount is {agg.get('offerCount')!r}, expected 578")
        if agg.get("lowPrice") != "220" or agg.get("highPrice") != "41000":
            problems.append(f"aggregate range is {agg.get('lowPrice')!r}-{agg.get('highPrice')!r}, "
                            f"expected 220-41000")

        listing_offers = []
        for el in itemlist.get("itemListElement") or []:
            item = el.get("item") or {}
            o = item.get("offers") or {}
            listing_offers.append((str(o.get("price")), str(o.get("priceCurrency")),
                                   str(o.get("itemCondition") or "").rsplit("/", 1)[-1],
                                   item.get("name")))
        for p, c, cond, nm in listing_offers:
            print(f"    listing offer: {p:>8} {c:<4} {cond:<14} {nm}")
        if len(listing_offers) != 4:
            problems.append(f"expected 4 itemListElement listings, got {len(listing_offers)}")
        got_cur = [c for _, c, _, _ in listing_offers]
        if got_cur != ["SEK", "SEK", "EUR", "USD"]:
            problems.append(f"per-listing currencies are {got_cur}, expected SEK/SEK/EUR/USD")
        if any(c == "DKK" for _, c, _, _ in listing_offers):
            problems.append("a listing offer is DKK — the aggregate currency leaked onto a row")
        if listing_offers and listing_offers[0][0] != "500":
            problems.append(f"first listing price is {listing_offers[0][0]!r}, expected '500'")

    # --- layer 2: the rendered listings ------------------------------------
    cov = _coverage(html)
    print(f"  rendered  : {cov['blocks']} listing blocks, {cov['unpriced']} without a price, "
          f"{len(cov['priced'])} with a price, {len(cov['skipped'])} skipped (no Isuzu number)")
    print(f"  price texts visible on the page ({len(cov['price_texts'])}): {cov['price_texts']}")
    print(f"  priced listings on the page ({len(cov['priced'])}):")
    for t in cov["priced"]:
        pns = find_pns(t)
        print(f"    {'PN ' + pns[0] if pns else 'no Isuzu number -> not a ledger row':<42} {t}")
    print(f"  skipped listings without an Isuzu number ({len(cov['skipped'])}):")
    for t in cov["skipped"]:
        print(f"    {t}")

    if cov["blocks"] != 25:
        problems.append(f"expected 25 rendered listing blocks, got {cov['blocks']}")
    if len(cov["priced"]) != 4:
        problems.append(f"expected 4 listings with a price on the page, got {len(cov['priced'])}")
    if cov["unpriced"] != 21:
        problems.append(f"expected 21 listings without a price, got {cov['unpriced']}")
    if cov["itemlist_elements"] != 4:
        problems.append(f"expected 4 ItemList elements, got {cov['itemlist_elements']}")
    if len(cov["skipped"]) != 9:
        problems.append(f"expected 9 listings with no Isuzu number, got {len(cov['skipped'])}")
    if len(cov["price_texts"]) != 4:
        problems.append(f"expected 4 visible price texts, got {cov['price_texts']}")
    if not all("Pris efter foresp" not in t for t in cov["price_texts"]):
        problems.append("a price-on-request string was counted as a price")

    # --- the rows ----------------------------------------------------------
    rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)
    priced = [r for r in rows if r["price"] is not None]
    on_request = [r for r in rows if r["price"] is None]
    print(f"\n  rows: {len(rows)}  |  with a price: {len(priced)}  |  "
          f"price-on-request match rows: {len(on_request)}")
    for r in rows:
        print(f"    PN {r['part_no']}  {str(r['price']):>8} {str(r['currency']):<4} "
              f"type={r['price_type']} cur_note={r['fx_note']} seller={r['competitor_brand']}")

    if not rows:
        problems.append("no rows parsed")
    if len(rows) != 16:
        problems.append(f"expected 16 rows (16 titles carry an Isuzu number), got {len(rows)}")
    if len(priced) != 1:
        problems.append(f"expected exactly 1 priced row, got {len(priced)}")
    if len(on_request) != 15:
        problems.append(f"expected 15 price-on-request rows, got {len(on_request)}")
    if not any(r["part_no"] == "8973675060" for r in rows):
        problems.append("part number 8973675060 (bare, from a title) not found")
    if not any(r["part_no"] == "8982049420" for r in rows):
        problems.append("part number 8982049420 (from dashed 8-98204-942-0) not found")
    if not any(r["part_no"] == "8972615492" for r in rows):
        problems.append("part number 8972615492 (from dashed 8-97261-549-2) not found")
    if not any(r["part_no"] == "8973689190" and r["price"] == 200.0 and r["currency"] == "EUR"
               for r in rows):
        got = [(r["part_no"], r["price"], r["currency"]) for r in priced]
        problems.append(f"expected 8973689190 at 200.0 EUR, got {got}")
    if any(r["currency"] == "DKK" for r in rows):
        problems.append("a row carries DKK — the aggregate currency was copied onto rows")
    if any(r["price"] is not None and r["currency"] is None for r in rows):
        problems.append("a row has a price but no currency")
    if not all(r["price_type"] == "marketplace" for r in rows):
        problems.append("a row is not price_type=marketplace")
    if not all(r["match_method"] == "exact_oem" for r in rows):
        problems.append("a row is not match_method=exact_oem")
    if not all(r["country"] == "DK" for r in rows):
        problems.append("a row is not country=DK")
    if not all(r["vat"] == "unknown" for r in rows):
        problems.append("a row claims a VAT basis the page does not state")
    if not all(r["observed_at"] == PROBE_DATE for r in rows):
        problems.append("a row is missing the observation date")
    if any(r["part_no"] and len(str(r["part_no"])) != 10 for r in rows):
        problems.append("a part number is not 10 digits")
    for r in rows:
        bad = row_problems(r)
        if bad:
            problems.append(f"{r['part_no']}: {bad}")

    # --- broken input must raise, not return [] ----------------------------
    stripped = re.sub(_LDJSON_RE,
                      lambda m: "" if '"ItemList"' in m.group(1) else m.group(0), html)
    no_numbers = re.sub(r'data-name="([^"]*)"',
                        lambda m: 'data-name="' + re.sub(r"\d", "", m.group(1)) + '"', html)
    for bad_html, label in (
        ("", "empty string"),
        ("<html>nothing here</html>", "no ItemList"),
        (stripped, "page with the ItemList removed"),
        (no_numbers, "listing blocks with the part numbers removed"),
    ):
        try:
            got = parse(bad_html)
            problems.append(f"{label}: parse returned {len(got)} rows instead of raising")
        except ParseError as e:
            print(f"  raises as required ({label}): {e}")

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print(f"\n  SELFTEST PASS — {len(rows)} marketplace rows ({len(priced)} priced, "
          f"{len(on_request)} price-on-request); per-row currency honoured; broken input raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
