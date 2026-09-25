# -*- coding: utf-8 -*-
"""geparden.no — Norwegian parts webshop. Two channels on one site; NOK, prices inc. MVA.

Evidence status (honest — read this before trusting the parser)
---------------------------------------------------------------
Page on disk (REAL, fetched 2026-09-24 through the consent gate, ALLOWED):
  `v_geparden_product.html` — 45,184 bytes on disk (45,085 chars read).
  URL: https://geparden.no/products/ac-kompressor-isuzu-d-max-ii-2-5-td-air-conditioning-compressor-lucas-p-lucacp01114
  Verified by reading the file, not from notes:
    - JSON-LD `Product`: `sku="LUCACP01114"`, `brand="Lucas"`,
      `name="AC-kompressor Isuzu D-Max II 2.5 TD │ Air conditioning compressor"`,
      `offers.price="6645.25"`, `offers.priceCurrency="NOK"`,
      `offers.availability="http://schema.org/InStock"`, `itemCondition=NewCondition`.
    - Nested `offers.priceSpecification.price="6995"`, `valueAddedTaxIncluded=true`
      — the same 6995 the page prints as the struck-through before-price.
    - `__NEXT_DATA__` corroborates the pair: `salesPrice={brutto:664525, originalBrutto:699500}`
      i.e. 6645.25 now against 6995.00 before.
    - Rendered: `<p ... line-through>6995,00</p>` above
      `<p data-testid="product-price">6645,25 NOK</p>` and the caption `inkl. MVA`.
    - The canonical/og:url slug ends `-p-lucacp01114` — a Lucas code, **not** an Isuzu number.
  This fixture is aftermarket and the selftest asserts it row by row.

Genuine Isuzu page on disk: **none.** Only the sitemaps are saved, and they hold **7** URLs
with a `-p-isu<digits>` suffix (0 of them in products-1.xml):
  products-2: 8983417890 (giroljefilter), 8981654120 (kupevifte)
  products-3: 5876150000 (oljefilter D-Max II), 8982705240 (oljefilter D-Max III 1.9)
  products-4: 8981073183 (senterkopp), 4039378425944 (skiltholder), 5867605593 (stoffmatter)
  products-1: none with digits · products-5: none
Counted from the files on 2026-09-24: 7 raw suffixes, but only **6** reduce to a real
10-digit Isuzu number — `-p-isu4039378425944` is 13 digits and yields nothing.
There is an **eighth** `-p-isu` slug the recon's count does not mention, in products-1.xml:
`...demper-bakluke-lem-easy-up-down-isuzu-d-max-isuzu-motors-limited-p-isupacl5867636330`
(tailgate damper). Its suffix is `pacl5867636330` — letters, not digits — so the documented
rule correctly ignores it and extracts no part number. Read `-p-isu` as the shape
`-p-isu<manufacturer code>`, where the code is the Isuzu OEM **when it is 10 digits**.
`GENUINE_SAMPLE_URL` below is a real URL copied from products-3.xml. **The genuine-channel
fixture built in `selftest()` is SYNTHETIC HTML**: that page was never fetched. It exists
only to exercise the slug rule; its price is invented by the test and asserted against
what the test itself put in. It is not evidence about the live page.

What it extracts
----------------
JSON-LD `Product` first (selector-first, per the build brief): `price`, `priceCurrency`,
`sku`, `brand`, `availability`, plus the nested `priceSpecification` pair. The rendered
`data-testid="product-price"` element and the `line-through` before-price are read as a
cross-check / fallback — never as the primary number, because the Tailwind classes around
them are cosmetic and will move. The page's own **`OEM` table** is also read (see below).

Where the Isuzu part number comes from
-------------------------------------
Primary rule, as briefed: the URL slug suffix `-p-isu<digits>`, e.g.
`...-genuine-oil-filter-isuzu-motors-limited-p-isu8982705240` -> `8982705240`.
`oem_from_slug()` reads `source_url` only. No `-p-isu<digits>` suffix = **no Isuzu number
from the slug**, and the row is still emitted so the price is not lost.
The manufacturer SKU (`LUCACP01114`) is never loaded as a part number — it goes in
`competitor_pn`, where it is labelled for what it is.

**Contradiction found on the real page, recorded rather than papered over.** The brief says
the Isuzu number is "not the JSON-LD. It is in the URL slug". That is true of the slug, but
it is not the whole story: `v_geparden_product.html` — the aftermarket Lucas AC compressor
whose slug carries **no** OEM — still prints a product table headed **`OEM`**:

    ISUZU   8981028240
    ISUZU   8981028241

and the same two lines are in `__NEXT_DATA__` as
`product.tables[0] = {"csv":"ISUZU,\t8981028240\nISUZU,\t8981028241","name":"OEM"}`.
So on this page the OEM number **is** on the page, in the OEM table, and the slug is not the
only carrier. What the brief means is still respected — this is **not** the manufacturer SKU
being promoted, and nothing is invented.

What the parser does with that, and why:
  - The **aftermarket** channel keeps `part_no=None` and `match_method="category_only"`.
    `8981028240/41` are Calsonic CR12 compressor bodies the Lucas part **replaces across a
    range of vehicles** (the page's own `Passer til` table lists D-Max 2.5 CRDi, 3.0, and
    more) — a cross-reference, not one exact application. Loading it as `exact_oem` would be
    the `OE RRP` mistake: a category match dressed as an exact one. The two numbers are
    recorded in the row `description` so the evidence is not lost, and remain available for a
    `crossref` pass once the ledger's FX/validation question is settled.
  - The **genuine** channel keeps the slug number and `exact_oem`, because there the number
    is the part actually being sold by that URL.

Two near-miss traps in the slugs, both real, both tested:
  - `...-p-8-97946-822-0` (bladfjar bak) carries an Isuzu-shaped dashed number but no
    `-p-isu` marker, so it is not the genuine channel and yields no part number here.
  - `...-p-isu4039378425944` (skiltholder) has the marker but a 13-digit code that does
    not reduce to 10 digits. `normalise_pn` returns None and nothing is invented.

A third trap the sitemaps revealed, and it is bigger than either: `-p-isu` is **also used
for Isuzu-licensed accessories**, whose suffix is not digits at all. Across the five
sitemaps there are 20 `-p-isu` slugs, and only **7** have a digit suffix:
`-p-isupacl*` (floor mats, wind deflectors, roof rails, tailgate damper — Isuzu part numbers
of their own, printed `PACL…`), `-p-isukitpa1569` (roof rails) and `-p-isupaclaig/bis`
(fender flares). Those are genuine Isuzu accessories, but their 10-digit form is not in the
slug, so this parser records **no** part number for them rather than guessing one. Reading
`-p-isu` as "10-digit Isuzu OEM follows" is only right for the 7; the site uses it for
"this is an Isuzu-licensed product".

Also note the genuine channel's second signal must **not** be read off the slug: every
`-p-isu<digits>` URL carries "isuzu-motors-limited" in the slug itself, so testing the URL
would make the title rule test nothing. `_says_genuine()` looks at the page's name/brand
only, and the selftest exercises the case where a `-p-isu<digits>` slug is paired with a
plain aftermarket title (it stays `aftermarket_retail`).

The two channels — and they are different rows
---------------------------------------------
1. slug has `-p-isu<10-digit>` **and** the page's own words say genuine (the title/brand
   carries "genuine" or "isuzu motors limited") -> `price_type="genuine_grey"`,
   `match_method="exact_oem"`, `part_no` from the slug.
2. anything else -> `price_type="aftermarket_retail"`, `match_method="category_only"`,
   `part_no=None`, `competitor_brand` = the JSON-LD brand (e.g. "Lucas").
A slug marker whose digits do not reduce to 10 digits stays in the genuine channel
(`genuine_grey`) with `part_no=None` and `match_method="category_only"` — the channel is
what the page says, and the ledger's `row_problems` will flag the missing number rather
than let a fabricated one through. Never blended: one row carries one price type.

The price choice
----------------
The **current/effective** price is the observation: `offers.price` = **6645.25 NOK**
(corroborated by the rendered `6645,25 NOK` and by `brutto`). The struck-through **6995**
is the before-price, carried in JSON-LD as `priceSpecification.price` and in the DOM as
`line-through`; it is recorded in the row `description` as context and is **not** loaded as
a second observation, because a crossed-out price is not a price anyone can buy at today.

`vat="incl"` — the page says `inkl. MVA` and the JSON-LD says
`valueAddedTaxIncluded=true`. (tungen-bil.no, the other Norwegian source, is `excl`; the two
must never be subtracted from each other without saying so.)

Honest gaps, not worked around
------------------------------
Prices are **NOK** and the ledger's FX table (`build_price_ledger.py`) has no NOK rate, so
every row carries `price_eur=None` and
`fx_note="NOK: no rate in ledger FX table as of 2026-09-24"`. No rate is invented here.

A page that shows the Product block but no price at all **raises** `ParseError`: on a
product page that is a broken read, not a "no price" answer.
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

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))
from ledger_schema import make_row, normalise_pn, row_problems        # noqa: E402

SITE = "geparden"
PROBE_PAGE = "v_geparden_product.html"
PROBE_URL = ("https://geparden.no/products/"
             "ac-kompressor-isuzu-d-max-ii-2-5-td-air-conditioning-compressor-lucas-p-lucacp01114")
PROBE_DATE = "2026-09-24"
COUNTRY = "NO"

# REAL genuine-channel fixtures, fetched 2026-09-24 through the consent gate.
# These replaced a synthetic fixture on 2026-09-24: the synthetic one exercised the
# slug rule but proved nothing about the live site, and a test that asserts its own
# input is not evidence. Both real pages are on disk and are asserted in selftest().
GENUINE_FIXTURES = [
    # (page file, canonical URL, expected Isuzu number from the slug,
    #  expected price NOK, expected struck-through before-price)
    ("v_geparden_genuine.html",
     "https://geparden.no/products/oljefilter-isuzu-d-max-iii-1-9-tdi-2019-genuine-oil-filter-"
     "isuzu-motors-limited-p-isu8982705240",
     "8982705240", 407.55, 429),
    ("v_geparden_genuine2.html",
     "https://geparden.no/products/oljefilter-isuzu-d-max-ii-2-0-2-5-3-0-td-2011-2019-genuine-"
     "oil-filter-isuzu-motors-limited-p-isu5876150000",
     "5876150000", 379.05, 399),
]

SOURCE_NAME = "Geparden"
FX_NOTE_NOK = "NOK native price carried unconverted here; the euro value is applied centrally from fx_rates.json (ECB rates, 2026-09-24) by run_probe/apply_fx"

# The genuine marker the site puts in the slug before the OEM digits.
_SLUG_OEM_RE = re.compile(r"-p-isu(\d+)", re.I)
# The page's own words for "this is an Isuzu genuine part".
_GENUINE_WORDS = ("genuine", "isuzu motors limited")
# Slack below which two readings of the same price count as agreement.
_PRICE_TOLERANCE = 0.01


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


# ---------------------------------------------------------------------------
# The slug rule — the only place an Isuzu part number can come from on this site
# ---------------------------------------------------------------------------
def raw_slug_suffix(source_url: str | None) -> str | None:
    """The raw digits after `-p-isu` in the URL slug, or None. No validation."""
    if not source_url:
        return None
    m = _SLUG_OEM_RE.search(str(source_url))
    return m.group(1) if m else None


def oem_from_slug(source_url: str | None) -> str | None:
    """Isuzu part number from a `-p-isu<digits>` slug suffix, or None.

    Never guesses: the suffix must reduce to exactly 10 digits, so the 13-digit
    accessory code `-p-isu4039378425944` returns None rather than a trimmed number.
    """
    return normalise_pn(raw_slug_suffix(source_url))


def oem_from_table(html: str) -> list[str]:
    """Isuzu OEM numbers from the page's own `OEM` table, in order of first sight.

    The page prints a table headed "OEM" with rows `ISUZU <10 digits>` (on
    `v_geparden_product.html`: 8981028240, 8981028241). These are read from the rendered
    `<dl>` first, then from the `__NEXT_DATA__` copy of the same table, so a page that
    renders the block differently still yields them.

    Returns 10-digit numbers only, and never invents one: the page's aftermarket product
    usually **replaces** a range of applications, so these are cross-references. The caller
    decides which channel may use them, and this function is not a licence to set
    `exact_oem`.
    """
    found: list[str] = []
    seen: set[str] = set()
    csv_blobs = []
    for m in re.finditer(r'"csv"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"name"\s*:\s*"OEM"', html):
        csv_blobs.append(m.group(1))
    if not csv_blobs:
        # The table as painted, with its header, when the JSON copy is absent.
        for m in re.finditer(r'text-stone">OEM</h3>(.*?)</div></div>', html, re.S):
            csv_blobs.append(re.sub(r"<[^>]+>", " ", m.group(1)))
    for blob in csv_blobs:
        text = blob.replace("\\r", "\n").replace("\\n", "\n").replace("\\t", " ")
        for line in text.split("\n"):
            if "ISUZU" not in line.upper():
                continue
            pn = normalise_pn(line)
            if pn and pn not in seen:
                seen.add(pn)
                found.append(pn)
    return found


def _says_genuine(name: str, brand: str) -> bool:
    """Do the page's own title/name/brand say this is genuine Isuzu?

    Deliberately **not** given `source_url`: the slug is where the part number comes from,
    and using it here too would make the second half of the rule vacuous (every
    `-p-isu<digits>` URL on this site also carries the words "isuzu-motors-limited").
    The two signals are kept independent on purpose.
    """
    haystack = f"{name or ''} {brand or ''}".lower()
    return any(w in haystack for w in _GENUINE_WORDS)


# ---------------------------------------------------------------------------
# Reading the price off the page
# ---------------------------------------------------------------------------
def _jsonld_product(html: str) -> dict | None:
    """The JSON-LD `Product` node, or None.

    Each `<script type="application/ld+json">` block is parsed on its own: the page also
    carries a BreadcrumbList block starting with the same `{"@context` opening, so one
    regex spanning from the first ld+json tag would capture invalid JSON.
    """
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            node = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(node, dict) and node.get("@type") == "Product":
            return node
    return None


def _first_offer(node: dict) -> dict:
    offers = node.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    return offers if isinstance(offers, dict) else {}


def _before_price(offer: dict, html: str) -> float | None:
    """The struck-through before-price, from JSON-LD first, then the DOM. Context only."""
    spec = offer.get("priceSpecification") or {}
    if isinstance(spec, list):
        spec = spec[0] if spec else {}
    if isinstance(spec, dict) and spec.get("price") is not None:
        try:
            return float(spec["price"])
        except (TypeError, ValueError):
            pass
    m = re.search(r'line-through[^>]*>\s*([\d\s.,\u00a0]+?)\s*<', html)
    return _no_number(m.group(1)) if m else None


def _no_number(txt: str) -> float | None:
    """Norwegian money text -> float. '6 645,25' and '6645,25' both mean 6645.25."""
    t = (txt or "").replace("\u00a0", "").replace("\u202f", "").replace(" ", "").strip()
    t = t.replace("kr", "").replace("NOK", "").strip()
    if not t:
        return None
    try:
        if "," in t and "." in t:
            if t.rfind(",") > t.rfind("."):
                t = t.replace(".", "").replace(",", ".")
            else:
                t = t.replace(",", "")
        elif "," in t:
            t = t.replace(",", ".")
        return float(t)
    except ValueError:
        return None


def _rendered_price(html: str) -> tuple[float | None, str | None]:
    """What the page paints: the `product-price` element and the currency beside it."""
    m = re.search(r'data-testid="product-price"[^>]*>(.*?)</p>', html, re.S)
    if not m:
        return None, None
    text = re.sub(r"<!--.*?-->", " ", m.group(1))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    hit = re.search(r"([\d][\d\s.,\u00a0]*?)\s*([A-Za-z]{3})?\s*$", text)
    if not hit:
        return None, None
    return _no_number(hit.group(1)), (hit.group(2).upper() if hit.group(2) else None)


def _vat_included(offer: dict, html: str) -> bool:
    """True when the page says the price includes Norwegian VAT (MVA)."""
    spec = offer.get("priceSpecification") or {}
    if isinstance(spec, list):
        spec = spec[0] if spec else {}
    if isinstance(spec, dict) and spec.get("valueAddedTaxIncluded") is True:
        return True
    return bool(re.search(r"inkl\.?\s*MVA", html, re.I))


def _availability(offer: dict) -> str:
    """schema.org availability -> in / out / unknown. Never guessed from the DOM."""
    av = str(offer.get("availability") or "")
    if "InStock" in av:
        return "in"
    if "OutOfStock" in av or "SoldOut" in av:
        return "out"
    return "unknown"


# ---------------------------------------------------------------------------
# parse()
# ---------------------------------------------------------------------------
def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """One saved geparden.no product page -> one ledger row for that page's channel.

    `source_url` is required for the genuine channel: it is the only place the Isuzu part
    number exists on this site. Pass the URL the page was saved from.

    Raises `ParseError` when the page is not the shape we know (too small, no JSON-LD
    `Product` block, or a Product block with no price). It never returns `[]` for a page
    it recognised.
    """
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a product page ({len(html or '')} chars)")

    node = _jsonld_product(html)
    if node is None:
        raise ParseError("no JSON-LD Product block — the page layout has changed")

    name = str(node.get("name") or "").strip()
    brand = node.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")
    brand = str(brand or "").strip()
    offer = _first_offer(node)

    price = None
    currency = None
    if offer.get("price") is not None:
        try:
            price = float(offer["price"])
        except (TypeError, ValueError):
            price = None
        currency = str(offer.get("priceCurrency") or "").strip().upper() or None

    rendered_price, rendered_currency = _rendered_price(html)
    if price is None:
        # Fallback only: the JSON-LD headline is the primary read.
        price, currency = rendered_price, currency or rendered_currency
        if price is None:
            raise ParseError("Product block found but no price on the page "
                             "(neither JSON-LD offers.price nor the rendered price)")

    before = _before_price(offer, html)
    vat = "incl" if _vat_included(offer, html) else "unknown"

    # --- channel, and where the part number can come from ---------------------
    slug_oem = oem_from_slug(source_url)
    genuine = bool(slug_oem) and _says_genuine(name, brand)
    if genuine:
        price_type = "genuine_grey"
        match_method = "exact_oem"
        part_no = slug_oem
        competitor_brand = brand or "Isuzu"
        competitor_pn = slug_oem
    else:
        price_type = "aftermarket_retail"
        match_method = "category_only"
        part_no = None
        competitor_brand = brand or None
        competitor_pn = str(node.get("sku") or "").strip() or None

    bits = [name or "geparden.no product"]
    if competitor_pn and price_type == "aftermarket_retail":
        bits.append(f"manufacturer sku {competitor_pn} (not an Isuzu number)")
    if before is not None:
        bits.append(f"before-price {before:g} {currency or 'NOK'} struck through")
    if raw_slug_suffix(source_url) and not slug_oem:
        bits.append(f"slug suffix -p-isu{raw_slug_suffix(source_url)} is not a 10-digit "
                    f"Isuzu number — no part number loaded")
    table_oems = oem_from_table(html)
    if table_oems and not genuine:
        # Cross-references, not an exact application: the aftermarket part replaces a range
        # of vehicles (the page's "Passer til" table), so these stay out of part_no.
        bits.append("OEM table cross-references " + ", ".join(table_oems) + " (crossref, not exact_oem)")
    description = " — ".join(bits)

    return [make_row(
        part_no=part_no,
        match_method=match_method,
        competitor_brand=competitor_brand,
        competitor_pn=competitor_pn,
        description=description,
        source=SOURCE_NAME,
        source_url=source_url or PROBE_URL,
        country=COUNTRY,
        observed_at=observed_at,
        vintage=f"{SOURCE_NAME} {observed_at}".strip(),
        price=price,
        price_avg=price,
        currency=currency,
        price_eur=None,
        fx_note=FX_NOTE_NOK,
        vat=vat,
        price_type=price_type,
        stock=_availability(offer),
        n_obs=1,
        loader=SITE,
    )]


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------
PROBE_DIR = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"

# SYNTHETIC page for the genuine-slug path. The URL is real (products-3.xml); this HTML
# was written by this test and was never fetched. The price is the test's own input.
_SYNTHETIC_GENUINE_PRICE = 1090.0
_SYNTHETIC_GENUINE_HTML = """<!doctype html><html lang="no"><head>
<title>Oljefilter Isuzu D-Max III 1.9 TDI 2019 – Genuine Oil Filter Isuzu Motors Limited | Geparden.no</title>
<link rel="canonical" href="__URL__">
<meta property="product:price:amount" content="1090.00"/>
<meta property="product:price:currency" content="NOK"/>
<script type="application/ld+json">
{"@context":"https://schema.org/","@type":"Product","sku":"ISU8982705240",
 "name":"Oljefilter Isuzu D-Max III 1.9 TDI 2019 \\u2013 Genuine Oil Filter Isuzu Motors Limited",
 "brand":"Isuzu Motors Limited",
 "offers":{"@type":"Offer","price":"1090.00","priceCurrency":"NOK",
   "priceSpecification":{"@type":"PriceSpecification","price":"1290","priceCurrency":"NOK",
     "valueAddedTaxIncluded":true},
   "url":"__URL__","availability":"http://schema.org/InStock",
   "itemCondition":"https://schema.org/NewCondition"}}
</script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[]}
</script></head><body>
<p class="text-sm tabular-nums text-stone line-through">1290,00</p>
<p data-testid="product-price" class="text-[34px] font-semibold">1090,00<!-- --> <!-- -->NOK</p>
<p class="mt-0.5 text-[10px] uppercase tracking-[0.14em] text-stone">inkl. MVA</p>
</body></html>"""


def _check(problems: list[str], ok: bool, msg: str) -> None:
    if not ok:
        problems.append(msg)


def selftest() -> int:
    """Assert the parser against the real saved page, then against built fixtures.

    Fixture 1 `v_geparden_product.html` is REAL (45,184 bytes, fetched 2026-09-24).
    Fixture 2 is SYNTHETIC: only its URL is real. See the docstring.
    """
    problems: list[str] = []
    page = PROBE_DIR / PROBE_PAGE

    print("=" * 74)
    print("geparden.no parser — selftest")
    print(f"  fixture 1 : {page.name}  (REAL, fetched {PROBE_DATE})")
    if not page.exists():
        print(f"  MISSING {page}")
        print("\n  SELFTEST FAIL")
        print(f"    - {PROBE_PAGE} not on disk")
        return 1

    html = page.read_text(encoding="utf-8", errors="replace")
    print(f"  bytes     : {len(html):,} chars")
    print(f"  source_url: {PROBE_URL}")

    # --- 1. the real aftermarket page ---------------------------------------
    rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)
    for r in rows:
        print(f"    row: PN {r['part_no']}  {r['price']} {r['currency']}  "
              f"type={r['price_type']}  match={r['match_method']}  vat={r['vat']}  "
              f"brand={r['competitor_brand']}  stock={r['stock']}  country={r['country']}")

    _check(problems, len(rows) == 1, f"expected exactly 1 row from the real page, got {len(rows)}")
    if rows:
        r = rows[0]
        _check(problems, r["price"] == 6645.25, f"price {r['price']!r} is not 6645.25")
        _check(problems, r["currency"] == "NOK", f"currency {r['currency']!r} is not NOK")
        _check(problems, r["vat"] == "incl", f"vat {r['vat']!r} is not 'incl' (page says inkl. MVA)")
        _check(problems, r["competitor_brand"] == "Lucas",
               f"brand {r['competitor_brand']!r} is not 'Lucas'")
        _check(problems, r["price_type"] == "aftermarket_retail",
               f"price_type {r['price_type']!r} is not aftermarket_retail")
        _check(problems, r["match_method"] == "category_only",
               f"match_method {r['match_method']!r} is not category_only")
        _check(problems, r["part_no"] is None,
               f"part_no {r['part_no']!r} must be None — the slug has no -p-isu suffix")
        _check(problems, r["competitor_pn"] == "LUCACP01114",
               f"competitor_pn {r['competitor_pn']!r} is not the Lucas sku LUCACP01114")
        _check(problems, r["country"] == "NO", f"country {r['country']!r} is not NO")
        _check(problems, r["price_eur"] is None and "NOK" in (r["fx_note"] or ""),
               "NOK rows must carry price_eur=None and say why in fx_note")
        _check(problems, str(r["part_no"] or "") != "LUCACP01114",
               "the manufacturer sku was loaded as if it were an Isuzu part number")
        # `row_problems` will always report "no part_no" for a category match: on this site
        # the aftermarket channel genuinely has no Isuzu number to give. The ledger records
        # that as a match row the way `match_method="category_only"` is meant to; the check
        # here is that the row is correct in every other respect, not that a number was found.
        rp = [p for p in row_problems(r) if p != "no part_no"]
        _check(problems, rp == [], f"real row fails row_problems (ignoring 'no part_no'): {rp}")
        _check(problems, row_problems(r) == ["no part_no"],
               "the real aftermarket row must be flagged by the ledger for exactly one thing: "
               f"no part_no (got {row_problems(r)})")
        _check(problems, "6995" in (r["description"] or ""),
               "the struck-through before-price 6995 is not recorded in the description")
        _check(problems, "8981028240" in (r["description"] or "")
               and "8981028241" in (r["description"] or ""),
               "the page's OEM-table cross-references are not recorded in the description")
        print(f"  before-price carried in description: "
              f"{'yes' if '6995' in (r['description'] or '') else 'NO'}")
        print(f"  fx_note  : {r['fx_note']}")
        print(f"  desc     : {r['description']}")

    # --- 2. the same page read without its URL must still not invent a PN ----
    rows_nourl = parse(html, observed_at=PROBE_DATE)
    _check(problems, len(rows_nourl) == 1 and rows_nourl[0]["part_no"] is None,
           "parsing the real page without source_url must give one row with part_no=None")

    # --- 3. the genuine-slug path, against TWO REAL fetched pages ---------------
    # Replaced a synthetic fixture on 2026-09-24: a test that asserts its own input
    # proves nothing about the live site.
    for fname, url, want_pn, want_price, want_before in GENUINE_FIXTURES:
        gpage = PROBE_DIR / fname
        print(f"\n  fixture : {fname}  (REAL, fetched {PROBE_DATE})")
        print(f"  source_url: {url}")
        if not gpage.exists():
            problems.append(f"{fname}: real genuine fixture missing from disk")
            print(f"    MISSING {gpage}")
            continue
        ghtml = gpage.read_text(encoding="utf-8", errors="replace")
        grows = parse(ghtml, source_url=url, observed_at=PROBE_DATE)
        for r in grows:
            print(f"    row: PN {r['part_no']}  {r['price']} {r['currency']}  "
                  f"type={r['price_type']}  match={r['match_method']}  vat={r['vat']}  "
                  f"brand={r['competitor_brand']}  stock={r['stock']}")
        _check(problems, len(grows) == 1,
               f"{fname}: expected 1 row from the real genuine page, got {len(grows)}")
        if not grows:
            continue
        g = grows[0]
        _check(problems, g["part_no"] == want_pn,
               f"{fname}: part_no {g['part_no']!r} is not {want_pn} from the slug")
        _check(problems, g["price"] == want_price,
               f"{fname}: price {g['price']!r} is not the page's {want_price}")
        _check(problems, g["price_type"] == "genuine_grey",
               f"{fname}: price_type {g['price_type']!r} is not genuine_grey")
        _check(problems, g["match_method"] == "exact_oem",
               f"{fname}: match_method {g['match_method']!r} is not exact_oem")
        _check(problems, g["currency"] == "NOK", f"{fname}: currency {g['currency']!r} is not NOK")
        _check(problems, g["vat"] == "incl", f"{fname}: vat {g['vat']!r} is not 'incl'")
        _check(problems, str(want_before) in (g["description"] or ""),
               f"{fname}: the struck-through before-price {want_before} is not in the description")
        _check(problems, row_problems(g) == [],
               f"{fname}: genuine row fails row_problems: {row_problems(g)}")

    # --- 4. the OEM table on the real page, read and declared as crossref ---
    print(f"  OEM table on the real page: {oem_from_table(html)}")
    _check(problems, oem_from_table(html) == ["8981028240", "8981028241"],
           f"the real page's OEM table read as {oem_from_table(html)}, expected "
           "[8981028240, 8981028241]")

    # --- 5. the slug rule itself, against the real sitemaps -----------------
    print("\n  slug rule against the saved sitemaps:")
    _check(problems, oem_from_slug(PROBE_URL) is None,
           "the real product URL must yield no Isuzu number")
    _check(problems, oem_from_slug(GENUINE_FIXTURES[0][1]) == "8982705240",
           "the genuine sample URL must yield 8982705240")
    _check(problems, oem_from_slug(GENUINE_FIXTURES[1][1]) == "5876150000",
           "the second genuine sample URL must yield 5876150000")
    _check(problems, oem_from_slug(
        "https://geparden.no/products/bladfjar-bak-isuzu-d-max-i-ii-2002-2019-p-8-97946-822-0") is None,
        "the -p-8-97946-822-0 near-miss must not be read as the genuine channel")
    _check(problems, oem_from_slug(
        "https://geparden.no/products/skiltholder-logo-isuzu-red-edition-nummerskiltholder-"
        "license-plate-frame-1-stk-isuzu-motors-limited-p-isu4039378425944") is None,
        "the 13-digit -p-isu4039378425944 code must not reduce to a 10-digit number")
    _check(problems, oem_from_slug(
        "https://geparden.no/products/demper-bakluke-lem-easy-up-down-isuzu-d-max-isuzu-motors-"
        "limited-p-isupacl5867636330") is None,
        "the lettered -p-isupacl5867636330 suffix must yield no part number")

    sitemaps = sorted(PROBE_DIR.glob("v_geparden_products*.xml"))
    if not sitemaps:
        print("    sitemaps not on disk — coverage count not re-verified here")
    else:
        digit_total = 0
        marker_total = 0
        for f in sitemaps:
            text = f.read_text(encoding="utf-8", errors="replace")
            markers = re.findall(r"-p-isu([A-Za-z0-9]+)", text)
            digit = [m for m in markers if m.isdigit()]
            print(f"    {f.name}: {len(markers)} '-p-isu' slug(s), of which {len(digit)} "
                  f"digit-suffixed {digit}")
            marker_total += len(markers)
            digit_total += len(digit)
        print(f"    TOTAL: {marker_total} '-p-isu' slugs, {digit_total} with digits")
        _check(problems, digit_total == 7,
               f"expected 7 digit-suffixed -p-isu URLs, counted {digit_total}")
        # The other 13 are Isuzu-licensed accessories whose suffix is a lettered code
        # (paclaig, pacl5867636330, kitpa1569, …), not an OEM number. The parser must ignore
        # them rather than read a part number out of a product-family code.
        _check(problems, marker_total == 20,
               f"expected 20 '-p-isu' slugs in total across the sitemaps, counted {marker_total}")
        _check(problems, marker_total - digit_total == 13,
               f"expected 13 non-digit '-p-isu' suffixes (Isuzu-licensed accessories), "
               f"got {marker_total - digit_total}")
        p1 = PROBE_DIR / "v_geparden_products1.xml"
        if p1.exists():
            p1_digits = [m for m in re.findall(r"-p-isu([A-Za-z0-9]+)",
                                               p1.read_text(encoding="utf-8", errors="replace"))
                         if m.isdigit()]
            _check(problems, p1_digits == [],
                   f"products-1.xml was expected to contain 0 digit-suffixed genuine URLs, got {p1_digits}")

    # --- 6. a slug marker with a non-genuine title stays aftermarket -------
    # Note this is deliberately NOT one of the genuine fixture URLs: those slugs themselves
    # contain "genuine-...-isuzu-motors-limited", so they would prove nothing about the
    # title rule. This case mangles a REAL fetched page so the HTML is real and only the
    # title/brand are changed.
    odd_url = ("https://geparden.no/products/kupevifte-isuzu-d-max-ii-2012-2019-"
               "p-isu8981654120")
    real_html = (PROBE_DIR / GENUINE_FIXTURES[0][0]).read_text(encoding="utf-8", errors="replace")
    odd = (real_html
           .replace("Genuine® Oil filter", "Kupevifte D-Max II")
           .replace("Genuine Oil filter Isuzu Motors Limited", "Kupevifte D-Max II")
           .replace("Isuzu Motors Limited", "Some Brand")
           .replace(GENUINE_FIXTURES[0][1], odd_url)
           .replace(GENUINE_FIXTURES[0][1].split("/products/")[-1], odd_url.split("/products/")[-1]))
    orows = parse(odd, source_url=odd_url, observed_at=PROBE_DATE)
    _check(problems, len(orows) == 1 and orows[0]["price_type"] == "aftermarket_retail"
           and orows[0]["part_no"] is None,
           f"a -p-isu8981654120 slug whose title does not say genuine must stay "
           f"aftermarket_retail with no part_no, got "
           f"{[(r['price_type'], r['part_no']) for r in orows]}")
    if orows:
        print(f"\n  fixture 3 : same numbers under a -p-isu slug with a NON-genuine title\n"
              f"    row: PN {orows[0]['part_no']}  {orows[0]['price']} {orows[0]['currency']}  "
              f"type={orows[0]['price_type']}  match={orows[0]['match_method']}")

    # --- 7. broken input must raise, never return [] -----------------------
    bad_cases = [
        ("", "empty string"),
        ("<html>nothing here</html>", "no Product block"),
        (real_html.replace('"price":"407.55"', '"price":""').replace(
            '"price":"407.55",', "").replace(
            'data-testid="product-price"', 'data-testid="gone"'), "Product block with no price"),
    ]
    for bad, label in bad_cases:
        try:
            parse(bad, source_url=GENUINE_FIXTURES[0][1])
            problems.append(f"{label}: parse returned instead of raising")
        except ParseError:
            print(f"    raises on {label}: OK")

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("\n  SELFTEST PASS — real page: 6645.25 NOK, incl, Lucas, aftermarket_retail, "
          "no Isuzu number; genuine slug 8982705240 -> genuine_grey; broken input raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
