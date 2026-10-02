# -*- coding: utf-8 -*-
"""mekster.no — D-Max aftermarket accessories, B2C retail. Norwegian krone. THIN coverage.

Evidence
--------
Page on disk: `01_data/90_INBOX/scrape_targets/_probe/v_mekster_product.html`
              1,914,633 bytes (1.9 MB), saved 2026-09-24, fetched through the consent gate.
              URL: https://www.mekster.no/climair-vindavviser-foran-isuzu-d-max-583471.html
              Magento + Algolia. The page carries FOUR `ld+json` scripts; exactly one is the
              `@type=Product` block. Everything this parser reads comes from that one block —
              the other 1.9 MB of DOM, template source and Algolia payload is never touched.

Verified values in that block (asserted by `selftest`, not assumed):
    name          "Vindavviser, Foran - Isuzu D Max"     (a ClimAir wind deflector, front)
    sku / mpn     "TP2268CL3533"                          (ClimAir's own code)
    brand.name    "ClimAir"                               (real aftermarket brand, not Isuzu)
    offers[0]     price 859, priceCurrency "NOK",
                  availability https://schema.org/OutOfStock, seller.name "mekster.no"
    Rendered price "859 Nok" agrees with the JSON-LD 859. The page also states
    "På mekster.no er alle priser spesifisert inkludert norsk moms" and shows "inkl. norsk mva"
    beside the price, so 859 is the VAT-inclusive figure (its ex-VAT toggle reads 687, which
    this parser does not use).

Coverage reality — read this before quoting mekster.no as reach
---------------------------------------------------------------
Across the five product sitemaps (`media/no_products_google_sitemap_{1..5}.xml`, re-counted on
the files on disk 2026-09-24) there are **229,060 product URLs and only 15 of them contain
"isuzu"**. Six are ClimAir wind deflectors for the D-Max (this page is one of them); the rest
are 2 Connect2 install kits, 1 oil-filter socket tool, and stereo-adapter / wiring items that
are Chevrolet-and-Isuzu or Fiat-and-Suzuki fitments, not Isuzu D-Max parts. One of the fifteen
is a tool, not a part.

**mekster.no is not an Isuzu parts source at meaningful volume.** Do not report 229,060 URLs as
Isuzu coverage; the honest number is six accessories, of which this is one.

Route: sitemap only. robots.txt carries `Disallow: */catalogsearch/`, and the `/sok?q=` search
path returns **HTTP 404**, so there is no part-number search either allowed or working.

What it extracts
----------------
One row, from the JSON-LD `Product` block:

    competitor_brand = brand.name   ("ClimAir")
    competitor_pn    = sku / mpn    ("TP2268CL3533")
    price            = 859, currency "NOK"   (native, never converted)
    price_type       = "aftermarket_retail"  (a real aftermarket brand: not genuine at any tier)
    stock            = schema.org availability -> "in" / "out" / "unknown"
    vat              = read from the page as above, else "unknown"

`part_no` is **None, deliberately, and the row is still emitted.** This page carries no Isuzu
OEM number anywhere: the JSON-LD has no `gtin`, the `mpn` is ClimAir's code, and the
"Originalnummer og kompatible kjøretøy" tab lists only compatible vehicles (D-Max 2.5/3.0 DDI,
2002-2013) with no original numbers under it. The manufacturer code is **not** an Isuzu number
and must never be written into `part_no`. So this row is an honest `match_method="category_only"`
aftermarket observation with no Isuzu number attached — kept rather than dropped, because the
price is real and the day a page does carry an OEM number an `exact_oem` row can be joined to it.
The ledger's own `validate()` permits a null `part_no` (it only checks numbers that are present);
`ledger_schema.row_problems()` is the stricter reader and reports "no part_no" for this row, which
`selftest` asserts explicitly rather than hiding.

Currency: NOK is carried natively with `price_eur=None` and an `fx_note` saying why. The ledger's
FX table (`build_price_ledger.py`, FX = EUR/GBP/SEK) has no NOK rate as of 2026-09-24, so
converting here would mean inventing a rate. That is a reported gap for the orchestrator to close
centrally with a dated, cited source — not for this parser to paper over.
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
sys.path.insert(0, str(HERE))
from ledger_schema import find_pns, make_row, normalise_pn, row_problems   # noqa: E402

SITE = "mekster"
PROBE_PAGE = "v_mekster_product.html"
PROBE_URL = "https://www.mekster.no/climair-vindavviser-foran-isuzu-d-max-583471.html"
PROBE_DATE = "2026-09-24"
COUNTRY = "NO"
COUNTRY_DEFAULT = COUNTRY      # same alias the Amayama module exposes

SOURCE = "mekster.no"
FX_NOTE = "NOK native price carried unconverted here; the euro value is applied centrally from fx_rates.json (ECB rates, 2026-09-24) by run_probe/apply_fx"

# The parsed shape of this page, asserted in selftest.
EXPECT_NAME = "Vindavviser, Foran - Isuzu D Max"
EXPECT_SKU = "TP2268CL3533"
EXPECT_BRAND = "ClimAir"
EXPECT_PRICE = 859.0
EXPECT_CURRENCY = "NOK"
EXPECT_STOCK = "out"

# schema.org availability URL -> ledger stock. Anything unrecognised is "unknown".
AVAILABILITY_MAP = {
    "instock": "in",
    "outofstock": "out",
    "preorder": "unknown",
    "backorder": "unknown",
    "discontinued": "unknown",
    "soldout": "out",
    "limitedavailability": "unknown",
    "onlineonly": "unknown",
    "instoreonly": "unknown",
}

_LD_JSON_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S)
_VAT_INCL_RE = re.compile(r"inkl\.?\s*(?:norsk\s+)?mva", re.I)
_VAT_STATEMENT_RE = re.compile(r"alle priser\s+spesifisert\s+inkludert\s+(?:norsk\s+)?moms", re.I)


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


def parse(html: str, *, source_url: str = "", observed_at: str = "",
          xref: dict | None = None) -> list[dict]:
    """mekster.no product page -> one ledger row from the JSON-LD `Product` block.

    `price_type = "aftermarket_retail"`. `part_no` comes only from `resolve_part()`: the brand's
    number in the title resolved through the graded cross-reference (confirmed/likely, brand
    agreeing) -> `match_method="crossref"`; otherwise `part_no=None`, `category_only` (the
    ClimAir probe page). A number in the title is never itself written as an Isuzu number.
    `xref` may be injected (selftest); default is `crossref_graded.csv`.

    Raises `ParseError` when the page is empty, carries no JSON-LD `Product` block, or carries a
    `Product` block with no offer to price — an empty list is never returned for a page this
    parser recognised.
    """
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a product page ({len(html or '')} chars)")

    node = _product_node(html)
    if node is None:
        raise ParseError("no JSON-LD Product block — the page layout has changed")

    offer = _first_offer(node)
    if offer is None:
        raise ParseError("JSON-LD Product block carries no offers[] — cannot price it")

    price = _as_price(offer.get("price"))
    if price is None:
        raise ParseError(f"JSON-LD offer has no numeric price (price={offer.get('price')!r})")
    currency = offer.get("priceCurrency")
    if not currency:
        raise ParseError("JSON-LD offer has no priceCurrency — a price without a currency is not a row")

    name = str(node.get("name") or "").strip()
    brand = _brand_name(node)
    pn, match_method, competitor_pn = resolve_part(name, brand, node, xref=xref)

    return [make_row(
        part_no=pn,
        match_method=match_method,
        competitor_brand=brand,
        competitor_pn=competitor_pn,
        description=name or None,
        source=SOURCE,
        source_url=source_url or offer.get("url") or node.get("url") or PROBE_URL,
        country=COUNTRY,
        observed_at=observed_at,
        vintage=f"{SOURCE} {observed_at}".strip(),
        price=price,
        price_avg=None,
        currency=str(currency),
        price_eur=None,
        fx_note=FX_NOTE,
        vat=_vat_from_page(html),
        price_type="aftermarket_retail",
        stock=map_availability(offer.get("availability")),
        n_obs=1,
        loader=SITE,
    )]


# ---------------------------------------------------------------------------
# Competitor number -> our Isuzu number (fix of 2026-10-02)
# ---------------------------------------------------------------------------
# BUG FIXED 2026-10-02. This parser used to run `find_pns()` over the product title and
# write any ten-digit run as `part_no` with `match_method="exact_oem"`. On
# `bosch-spridare-0445110980` that wrote the BOSCH injector number 0445110980 as an
# Isuzu part number. mekster sells aftermarket brands; a number in its title is the
# brand's number, never ours. It also wrote mekster's internal SKU (`16663589`) as
# `competitor_pn`, so the brand number was lost from the row.
#
# Now:
#   * `competitor_pn` is the brand's own number as written in the title (e.g. `0445110980`,
#     `ADBP250064`, `0 986 424 916`, `D7033S`); the JSON-LD sku is only a fallback when the
#     title carries no number (the ClimAir page, where sku == ClimAir's own code).
#   * `part_no` is set ONLY by resolving that number through the graded cross-reference
#     (`crossref_graded.csv`, tier confirmed or likely), with the brand on the page agreeing
#     with the brand on the edge, and to exactly one Isuzu number. `match_method="crossref"`.
#   * Anything that does not resolve stays `part_no=None`, `match_method="category_only"`:
#     it is never offered to the ledger as an Isuzu part.
#   * `exact_oem` is only possible when the page's brand is Isuzu itself.
GRADED = HERE.parents[1] / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
USABLE_TIERS = ("confirmed", "likely")
_XREF_CACHE: dict | None = None


def _norm_key(s: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def load_xref(path: Path = GRADED) -> dict:
    """{cpn_key: {(isuzu_pn, BRANDKEY), ...}} from the graded edges, confirmed/likely only."""
    import csv
    out: dict[str, set] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if (r.get("tier") or "").strip() not in USABLE_TIERS:
                continue
            key = _norm_key(r.get("cpn_key") or r.get("competitor_pn"))
            pn = normalise_pn(r.get("part_no"))
            if key and pn:
                out.setdefault(key, set()).add((pn, _norm_key(r.get("competitor_brand"))))
    return out


def _xref() -> dict:
    global _XREF_CACHE
    if _XREF_CACHE is None:
        _XREF_CACHE = load_xref()
    return _XREF_CACHE


def _brand_agrees(page_brand: str, edge_brand: str) -> bool:
    if not page_brand or not edge_brand:
        return False
    return page_brand == edge_brand or page_brand in edge_brand or edge_brand in page_brand


def _title_number(name: str) -> str | None:
    """The trailing run of digit-bearing tokens in the title: the brand's number as written."""
    toks = [t for t in re.split(r"[\s,;]+", name) if t]
    tail: list[str] = []
    for t in reversed(toks):
        if any(c.isdigit() for c in t) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9\-\./]*", t):
            tail.append(t)
        else:
            break
    return " ".join(reversed(tail)) or None


def resolve_part(name: str, brand: str | None, node: dict | None = None, *,
                 xref: dict | None = None) -> tuple[str | None, str, str | None]:
    """(part_no, match_method, competitor_pn) for one mekster title. Never guesses."""
    xref = _xref() if xref is None else xref
    bkey = _norm_key(brand)
    sku = str((node or {}).get("sku") or (node or {}).get("mpn") or "").strip() or None

    # A genuine Isuzu article: only then may a number in the title be ours.
    if bkey == "ISUZU":
        pns = find_pns(name)
        if len(pns) == 1:
            return pns[0], "exact_oem", None

    # Competitor number through the graded cross-reference, brand must agree.
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", name) if t]
    for w in (4, 3, 2, 1):                       # longest written form first
        for i in range(0, len(toks) - w + 1):
            written = toks[i:i + w]
            key = _norm_key("".join(written))
            if len(key) < 5 or not any(c.isdigit() for c in key) or key not in xref:
                continue
            pns = {pn for pn, eb in xref[key] if _brand_agrees(bkey, eb)}
            if len(pns) == 1:
                return pns.pop(), "crossref", _title_written(name, written)
            # 0 = brand disagrees, >1 = ambiguous: do not pick, keep looking / fall through

    return None, "category_only", _title_number(name) or sku


def _title_written(name: str, toks: list[str]) -> str:
    """The matched tokens exactly as the title writes them (keeps `0 986 424 916` spacing)."""
    pat = r"[^A-Za-z0-9]{0,3}".join(re.escape(t) for t in toks)
    m = re.search(pat, name)
    return m.group(0) if m else " ".join(toks)


def map_availability(availability: object) -> str:
    """schema.org availability -> "in" / "out" / "unknown".

    Reads the last path segment, so both `https://schema.org/OutOfStock` and a bare
    `OutOfStock` map the same way. Anything not in AVAILABILITY_MAP is "unknown":
    an unread availability is not evidence that a part is in stock.
    """
    if not availability:
        return "unknown"
    token = str(availability).rstrip("/").rsplit("/", 1)[-1].strip().lower()
    return AVAILABILITY_MAP.get(token, "unknown")


def _product_node(html: str) -> dict | None:
    """The one JSON-LD block whose @type is Product."""
    for block in _LD_JSON_RE.findall(html):
        try:
            node = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue
        candidates = node if isinstance(node, list) else [node]
        for cand in candidates:
            if isinstance(cand, dict) and cand.get("@type") == "Product":
                return cand
    return None


def _first_offer(node: dict) -> dict | None:
    """offers may be a dict, or a list of offers. Take the first we can read."""
    offers = node.get("offers")
    if isinstance(offers, dict):
        return offers
    if isinstance(offers, list):
        for o in offers:
            if isinstance(o, dict):
                return o
    return None


def _brand_name(node: dict) -> str | None:
    brand = node.get("brand") or node.get("manufacturer")
    if isinstance(brand, dict):
        return str(brand.get("name") or "").strip() or None
    if isinstance(brand, str):
        return brand.strip() or None
    return None


def _as_price(raw: object) -> float | None:
    if raw is None:
        return None
    try:
        price = float(str(raw).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    return price if price > 0 else None


def _vat_from_page(html: str) -> str:
    """What the page says about VAT, or "unknown" — never a guess.

    This page says it twice: "inkl. norsk mva" next to the price, and
    "På mekster.no er alle priser spesifisert inkludert norsk moms". The JSON-LD price equals
    the VAT-inclusive rendered price (859), so "incl" is the read. An ex-VAT toggle value (687)
    also exists on the page and is not used.
    """
    if _VAT_INCL_RE.search(html) or _VAT_STATEMENT_RE.search(html):
        return "incl"
    return "unknown"


def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    page = probe / PROBE_PAGE
    problems: list[str] = []

    print("mekster.no parser — selftest against the saved page")
    if not page.exists():
        print(f"  SELFTEST FAIL — saved page missing: {page}")
        return 1

    html = page.read_text(encoding="utf-8", errors="replace")
    print(f"  page      : {page}")
    print(f"  bytes     : {len(html.encode('utf-8')):,} on disk ({len(html):,} chars read)")
    print(f"  country   : {COUNTRY}   currency read from the page: {EXPECT_CURRENCY}")

    rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)
    print(f"  rows found: {len(rows)}")
    for r in rows:
        print(f"    brand={r['competitor_brand']!r}  competitor_pn={r['competitor_pn']!r}  "
              f"part_no={r['part_no']!r}")
        print(f"    price={r['price']} {r['currency']}  price_eur={r['price_eur']!r}  "
              f"vat={r['vat']}  stock={r['stock']}")
        print(f"    type={r['price_type']}  match={r['match_method']}  country={r['country']}  "
              f"vintage={r['vintage']!r}")
        print(f"    description={r['description']!r}")
        print(f"    fx_note={r['fx_note']!r}")

    # --- the real values off the page -------------------------------------------------
    if len(rows) != 1:
        problems.append(f"expected exactly 1 row from one JSON-LD Product block, got {len(rows)}")
    row = rows[0] if rows else {}

    if row.get("description") != EXPECT_NAME:
        problems.append(f"name: expected {EXPECT_NAME!r}, got {row.get('description')!r}")
    if row.get("competitor_brand") != EXPECT_BRAND:
        problems.append(f"brand: expected {EXPECT_BRAND!r}, got {row.get('competitor_brand')!r}")
    if row.get("competitor_pn") != EXPECT_SKU:
        problems.append(f"competitor_pn: expected {EXPECT_SKU!r}, got {row.get('competitor_pn')!r}")
    if row.get("price") != EXPECT_PRICE:
        problems.append(f"price: expected {EXPECT_PRICE}, got {row.get('price')!r}")
    if row.get("currency") != EXPECT_CURRENCY:
        problems.append(f"currency: expected {EXPECT_CURRENCY}, got {row.get('currency')!r}")
    if row.get("stock") != EXPECT_STOCK:
        problems.append(f"stock: expected {EXPECT_STOCK!r} (schema.org OutOfStock), got {row.get('stock')!r}")
    if row.get("vat") != "incl":
        problems.append(f"vat: the page states prices are incl. mva, read {row.get('vat')!r}")
    if row.get("price_type") != "aftermarket_retail":
        problems.append(f"price_type: expected aftermarket_retail, got {row.get('price_type')!r}")
    if row.get("match_method") != "category_only":
        problems.append(f"match_method: expected category_only, got {row.get('match_method')!r}")
    if row.get("country") != COUNTRY:
        problems.append(f"country: expected {COUNTRY}, got {row.get('country')!r}")
    if row.get("source") != SOURCE:
        problems.append(f"source: expected {SOURCE}, got {row.get('source')!r}")
    if row.get("source_url") != PROBE_URL:
        problems.append(f"source_url: expected {PROBE_URL}, got {row.get('source_url')!r}")
    if row.get("observed_at") != PROBE_DATE:
        problems.append(f"observed_at: expected {PROBE_DATE}, got {row.get('observed_at')!r}")
    if row.get("vintage") != f"{SOURCE} {PROBE_DATE}":
        problems.append(f"vintage: got {row.get('vintage')!r}")
    if row.get("n_obs") != 1:
        problems.append(f"n_obs: got {row.get('n_obs')!r}")

    # --- the no-Isuzu-number decision, asserted rather than assumed --------------------
    if row.get("part_no") is not None:
        problems.append(f"part_no: this page has no Isuzu number, expected None, got {row.get('part_no')!r}")
    if normalise_pn(EXPECT_SKU) is not None:
        problems.append("the ClimAir SKU must not reduce to an Isuzu number")
    if find_pns(EXPECT_NAME):
        problems.append("an Isuzu number appeared in the product name — re-read the page")
    if "gtin" in json.dumps(_product_node(html) or {}):
        problems.append("the JSON-LD now carries a gtin — re-read the page, part_no may no longer be None")

    # --- currency: native, and the gap recorded, never a hand-made rate ----------------
    if row.get("price_eur") is not None:
        problems.append("price_eur must be None: the ledger has no NOK rate to convert with")
    if not row.get("fx_note") or "NOK" not in str(row.get("fx_note")) or "2026-09-24" not in str(row.get("fx_note")):
        problems.append(f"fx_note must name NOK and the date, got {row.get('fx_note')!r}")

    # --- the ledger checker: state the one known finding, do not hide it ---------------
    found = row_problems(row)
    print(f"\n  row_problems: {found}")
    if found != ["no part_no"]:
        problems.append(f"row_problems changed: expected ['no part_no'], got {found}")
    else:
        print("    the single finding is 'no part_no' — correct for a category row with no Isuzu")
        print("    number. build_price_ledger.validate() accepts a null part_no (it only checks")
        print("    numbers that are present); ledger_schema.row_problems() is the stricter reader.")

    # --- a recognised-but-empty page must raise, not return [] -------------------------
    broken = [
        ("", "empty string"),
        # Long enough to pass the size guard, so this exercises the layout check itself
        # rather than the "too small" guard.
        ("<html><body>" + "no product markup here " * 40 + "</body></html>", "no Product block (full-size page)"),
        (re.sub(re.escape(_product_node_source(html)), "", html, count=1), "JSON-LD Product block removed")
        if _product_node_source(html) else (html, "JSON-LD Product block removed"),
        ('<script type="application/ld+json">{"@type":"Product","name":"x"}</script>' + " " * 600,
         "Product block with no offer"),
    ]
    print("\n  broken input must raise ParseError:")
    for bad, label in broken:
        try:
            got = parse(bad, observed_at=PROBE_DATE)
            problems.append(f"{label}: parse returned {len(got)} rows instead of raising")
        except ParseError as e:
            print(f"    {label:34s} OK — ParseError: {e}")

    # --- the 0445110980 bug (2026-10-02): a competitor number is never an Isuzu number --
    print("\n  competitor-number case (Bosch 0445110980, the bug fixed 2026-10-02):")
    bosch = ('<script type="application/ld+json">' + json.dumps({
        "@type": "Product", "name": "Bosch spridare 0445110980", "sku": "16663589",
        "mpn": "16663589", "brand": {"@type": "Brand", "name": "Bosch"},
        "offers": {"price": "4212", "priceCurrency": "NOK",
                   "availability": "https://schema.org/InStock"}}) + "</script>"
             + " inkl. norsk mva " + " " * 600)
    fake_xref = {"0445110980": {("8984890190", "BOSCH")}}
    cases = [
        ("resolves via confirmed/likely edge", fake_xref, "8984890190", "crossref"),
        ("no usable edge -> not an Isuzu part", {}, None, "category_only"),
        ("edge under another brand -> refused", {"0445110980": {("8984890190", "DENSO")}},
         None, "category_only"),
        ("ambiguous edge (2 Isuzu numbers) -> refused",
         {"0445110980": {("8984890190", "BOSCH"), ("8973297034", "BOSCH")}}, None, "category_only"),
    ]
    for label, xr, want_pn, want_mm in cases:
        r = parse(bosch, observed_at=PROBE_DATE, xref=xr)[0]
        ok = (r["part_no"] == want_pn and r["match_method"] == want_mm
              and r["competitor_pn"] == "0445110980" and r["part_no"] != "0445110980")
        print(f"    {label:44s} part_no={r['part_no']!r} match={r['match_method']} "
              f"competitor_pn={r['competitor_pn']!r}  {'OK' if ok else 'FAIL'}")
        if not ok:
            problems.append(f"bosch case '{label}': got part_no={r['part_no']!r}, "
                            f"match={r['match_method']!r}, competitor_pn={r['competitor_pn']!r}")
    if _title_written("Bosch Bremseklosser Foran, 0 986 424 916", ["0", "986", "424", "916"]) \
            != "0 986 424 916":
        problems.append("spaced competitor number not kept as written")
    # the real cached page, if the sitemap walker's cache is on disk
    real = probe / "cache" / "www.mekster.no" / "3e9469d3d307a1ef.html"
    if real.exists():
        r = parse(real.read_text(encoding="utf-8", errors="replace"), observed_at=PROBE_DATE)[0]
        print(f"    real cached page (graded file)               part_no={r['part_no']!r} "
              f"match={r['match_method']} competitor_pn={r['competitor_pn']!r}")
        if r["part_no"] == "0445110980" or r["competitor_pn"] != "0445110980":
            problems.append(f"real Bosch page: part_no={r['part_no']!r}, competitor_pn={r['competitor_pn']!r}")

    # --- coverage reality printed, so nobody quotes 229,060 as Isuzu reach -------------
    print("\n  coverage reality (mekster.no, 2026-09-24):")
    print("    229,060 product URLs across five sitemaps; 15 contain 'isuzu'.")
    print("    Of those: 6 ClimAir wind deflectors for D-Max, 2 Connect2 install kits,")
    print("    1 oil-filter socket (a tool), and Chevrolet/Isuzu or Fiat/Suzuki stereo adapters.")
    print("    Not an Isuzu parts source at meaningful volume. Sitemap-only route:")
    print("    robots.txt disallows */catalogsearch/ and /sok?q= returns HTTP 404.")

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("\n  SELFTEST PASS — 859 NOK, aftermarket_retail, ClimAir/TP2268CL3533, "
          "OutOfStock -> stock 'out', vat incl, part_no None; broken pages raise")
    return 0


def _product_node_source(html: str) -> str:
    """The literal text of the JSON-LD Product script, for the removal test."""
    for m in _LD_JSON_RE.finditer(html):
        try:
            node = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
        candidates = node if isinstance(node, list) else [node]
        if any(isinstance(c, dict) and c.get("@type") == "Product" for c in candidates):
            return m.group(0)
    return ""


if __name__ == "__main__":
    raise SystemExit(selftest())
