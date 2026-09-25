# -*- coding: utf-8 -*-
"""Tungen Bil AS — an Isuzu DEALER's own older-original-stock list. TRUSTWORTHY BUT THIN.

Evidence
--------
Page: `v_tungen_list.html`  (168,504 bytes on disk, 168,449 chars as read)
       Saved 2026-09-24 under `01_data/90_INBOX/scrape_targets/_probe/`.
       URL, exactly as the page itself records it: the form's own
       `_wp_http_referer` value is
       `/nettbutikk/eldre-originale-bildeler/isuzu/isuzu-eldre-originale-deler/`
       and the breadcrumb category link is `/produktkategori/eldre-originale-bildeler/`.
       So the real URL is

           https://www.tungen-bil.no/nettbutikk/eldre-originale-bildeler/isuzu/isuzu-eldre-originale-deler/

       The alternative spelling `.../eldre-originale-biler/...` (one `d` missing in
       "bil-deler") appears in the work order but is NOT what the saved page's own
       links and referer say. Verified, not assumed.

Verified on that page (asserted by `selftest`, from the page not from expectation):

* exactly **ONE** `<table>` element (`<table id="tablepress-4-no-2">`, a tablepress
  block inside a WooCommerce/Kadence page);
* its `<th>` headers, in order: `Varenummer`, `Beskrivelse`, `Antall`, `Pris (ex. mva)`;
* exactly **ONE** data row in `<tbody>`:
  `8-98214687-0 | CAP. WEEL | 1 | 737`;
* there is **NO JSON-LD `Product`** on this page. The only `ld+json` block is a Yoast
  `@graph` (WebPage / CollectionPage), so a JSON-LD reader would find nothing here and
  silently return no rows. This parser reads the table.

What it extracts
----------------
One ledger row per `<tbody>` row of that table:

* `part_no` from the Varenummer column, run through the shared
  `ledger_schema.normalise_pn()`. **The trap:** the column is in the dashed 11-digit
  printed form `8-98214687-0`, which `normalise_pn()` reduces to the bare 10 digits
  `8982146870`. No private digit-stripping is done here; the shared helper is the only
  converter, so this parser cannot drift from the ledger's part-number rule.
* `price` = the `Pris (ex. mva)` number, native NOK, taken as-is.
* `currency = "NOK"`, `country = "NO"`, `vat = "excl"`.
* `price_type = "dealer"`.

`price_type = "dealer"` — this is the Isuzu **dealer's** own older-original stock, so
these rows must NEVER be mixed with aftermarket prices (`aftermarket_retail` /
`aftermarket_trade`), and must not be read as a genuine grey-channel quote
(`genuine_grey`) either. The dealer channel is its own observation. Blending this with
an aftermarket price on the same part number is exactly the `OE RRP` mistake recorded in
`MATCH_INDEX_REPORT.md` RULE 1.

Two decisions stated plainly, because the work order asked for the reasoning
--------------------------------------------------------------------------------
**`n_obs` is left at 1, and `Antall` is not used as an observation count.** `Antall`
("quantity") is the number of pieces the dealer holds of that one part. The ledger's
`n_obs` counts how many independent observations went into a price (see its other
loaders: a competitor count, a survey sample size). One stock table row is one
observation regardless of how many pieces sit on the shelf, so mapping `Antall` into
`n_obs` would claim four observations for a single price. For a quantity of 1 the two
readings coincide, which is exactly why the mistake would stay invisible — so `n_obs=1`
is set explicitly and the Antall value is carried in `description` instead
(`"CAP. WEEL (Antall 1 tilgjengelig)"`) so the reader can still see it.

**`stock = "in"`, and here is why.** The page markup does contain a WooCommerce
out-of-stock class, but it sits on the single-product summary wrapping the category
itself:

    <div id="product-2179" class="... product type-product ... outofstock ...">

That element is the category page's `ISUZU ELDRE ORIGINALE DELER` summary, it carries
an empty price (`<p class="price"></p>`), and it is not the table. The stock signal that
belongs to a *row* is the row's own presence in the dealer's published availability
table together with a non-zero `Antall`: a part the dealer did not hold would not be
listed with a quantity and a price. So this parser reads the row, not the page
furniture, and writes `stock = "in"`. It does **not** infer `out` from the unrelated
`outofstock` class above the table. If a future page version marks individual rows,
read it from the row.

Honest coverage statement — do not present this as reach
--------------------------------------------------------
This source is **trustworthy but THIN**: the whole saved page carries exactly **one**
part. It is not a catalogue and must not be presented as coverage, as a market
representative, or as "Tungen's prices" in the plural. One row is one data point. The
recon note already says the same thing (`SCRAPER_PHASE1_REACH_RECON_20260924.md` §3:
"trustworthy but will only ever contribute a handful of rows").

The failure this parser must never repeat
-----------------------------------------
The threat here is not a wrong price, it is a **silent empty list**. A recognised table
that yields zero data rows must RAISE, because `[]` is indistinguishable from "the
dealer had no parts today" — the failure mode that let seven false prices sit in a
dashboard for six weeks in this project. `parse()` therefore raises in three separate
places: no table at all, a table whose header it does not recognise, and a recognised
table with no data rows. The selftest proves the third case by deleting the real data
row from the real HTML and asserting `ParseError`.

Currency: rows carry the **native NOK price**. The ledger's FX table as of 2026-09-24
has no NOK rate, so `price_eur` stays `None` with an `fx_note` saying why. No rate is
invented here and nothing is converted by hand.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))
from ledger_schema import make_row, normalise_pn                      # noqa: E402

SITE = "tungen"
PROBE_PAGE = "v_tungen_list.html"
PROBE_URL = "https://www.tungen-bil.no/nettbutikk/eldre-originale-bildeler/isuzu/isuzu-eldre-originale-deler/"
PROBE_DATE = "2026-09-24"
COUNTRY = "NO"
COUNTRY_DEFAULT = COUNTRY

FX_NOTE = "NOK native price carried unconverted here; the euro value is applied centrally from fx_rates.json (ECB rates, 2026-09-24) by run_probe/apply_fx"

# The header we must recognise before we are allowed to trust any row count.
EXPECTED_HEADERS = ["Varenummer", "Beskrivelse", "Antall", "Pris (ex. mva)"]


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


def _text(fragment: str) -> str:
    """Tag-stripped, whitespace-collapsed, entity-simplified cell text."""
    s = re.sub(r"<[^>]+>", " ", fragment)
    for ent, ch in (("&nbsp;", " "), ("&#160;", " "), ("&amp;", "&"),
                    ("&quot;", '"'), ("&#039;", "'"), ("&apos;", "'")):
        s = s.replace(ent, ch)
    return re.sub(r"\s+", " ", s).strip()


def _table_blocks(html: str) -> list[str]:
    """Every `<table>...</table>` on the page, in order. Non-greedy, so nested-safe enough."""
    return re.findall(r"<table\b.*?</table>", html, re.S | re.I)


def _parse_price(raw: str) -> float | None:
    """Norwegian price cell -> float. `737`, `1 234,50` and `1.234,50` all read correctly."""
    s = raw.replace("\xa0", " ").replace(" ", "").replace("kr", "").replace("NOK", "").strip()
    if not s:
        return None
    if "," in s:
        # comma is the decimal mark; a dot in the same cell is a thousands separator
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a parts list ({len(html or '')} chars)")

    tables = _table_blocks(html)
    if not tables:
        raise ParseError("no <table> on the page — the layout has changed")
    if len(tables) != 1:
        raise ParseError(f"expected exactly 1 table, found {len(tables)} — cannot pick safely")
    table = tables[0]

    # -- header first: a row count is meaningless if we are reading the wrong table ----
    head = re.search(r"<thead\b.*?</thead>", table, re.S | re.I)
    header_html = head.group(0) if head else table
    headers = [_text(m.group(1)) for m in re.finditer(r"<th\b[^>]*>(.*?)</th>", header_html, re.S | re.I)]
    if not headers:
        raise ParseError("table has no <th> header cells — cannot tell which table this is")
    if headers != EXPECTED_HEADERS:
        raise ParseError(
            "table header not recognised — expected "
            f"{EXPECTED_HEADERS}, found {headers}. Refusing to guess a column meaning."
        )

    price_header = headers[3].lower()
    if "mva" not in price_header:
        raise ParseError(f"price column does not state its VAT basis: {headers[3]!r}")
    vat = "excl" if re.search(r"\bex\.?\b", price_header) else "incl"

    # -- then the rows ----------------------------------------------------------------
    body = re.search(r"<tbody\b.*?</tbody>", table, re.S | re.I)
    body_html = body.group(0) if body else table
    if not body:
        raise ParseError("recognised the table header but it has no <tbody> — cannot count rows")

    rows: list[dict] = []
    bad_rows: list[str] = []
    for tr in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", body_html, re.S | re.I):
        cells = [_text(m.group(1)) for m in re.finditer(r"<td\b[^>]*>(.*?)</td>", tr.group(1), re.S | re.I)]
        if not cells:
            continue                                    # a spacer row is not a data row
        if len(cells) != len(headers):
            bad_rows.append(f"{len(cells)} cells where {len(headers)} were expected: {cells!r}")
            continue

        raw_pn, beskrivelse, antall, raw_price = cells
        pn = normalise_pn(raw_pn)                        # shared helper, never local stripping
        if not pn:
            bad_rows.append(f"Varenummer {raw_pn!r} is not a 10-digit Isuzu number")
            continue
        price = _parse_price(raw_price)
        if price is None:
            bad_rows.append(f"price {raw_price!r} is not a number")
            continue

        stock = "in" if _qty(antall) not in (0, None) else "out"
        desc = beskrivelse or f"Isuzu part {pn}"
        rows.append(make_row(
            part_no=pn,
            price=price,
            currency="NOK",                              # native price, never converted here
            price_eur=None,
            fx_note=FX_NOTE,
            vat=vat,
            price_type="dealer",
            match_method="exact_oem",
            source="Tungen Bil AS",
            source_url=source_url or PROBE_URL,
            country=COUNTRY,
            observed_at=observed_at,
            vintage=f"Tungen {observed_at}",
            competitor_brand="Isuzu (dealer, older original stock)",
            competitor_pn=pn,
            description=f"{desc} (Antall {antall} tilgjengelig)",
            stock=stock,
            n_obs=1,                                     # one stock-table row = one observation
            loader=SITE,
        ))

    # The whole point of this module: a recognised-but-empty table is a FAILURE, not an
    # answer. `[]` here would be indistinguishable from "the dealer listed no parts".
    if not rows:
        detail = f"; rejected rows: {bad_rows}" if bad_rows else ""
        raise ParseError(
            "recognised the table header "
            f"{EXPECTED_HEADERS} but found 0 valid data rows{detail}. "
            "An empty list must not be returned here."
        )
    return rows


def _qty(raw: str) -> int | None:
    """Antall cell -> int, or None if it is not a plain count."""
    m = re.fullmatch(r"\d+", (raw or "").strip())
    return int(m.group(0)) if m else None


def selftest() -> int:
    probe = HERE.parents[2] / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
    page = probe / PROBE_PAGE
    problems: list[str] = []

    if not page.exists():
        print(f"  MISSING {page}")
        print("\n  SELFTEST FAIL")
        return 1

    html = page.read_text(encoding="utf-8", errors="replace")
    print("=" * 74)
    print(f"  {PROBE_PAGE}  ({page.stat().st_size:,} bytes)  as of {PROBE_DATE}")

    # -- what the page itself says, before any parser runs ---------------------------
    table_count = len(_table_blocks(html))
    thead = re.search(r"<thead\b.*?</thead>", html, re.S | re.I)
    page_headers = ([_text(m.group(1)) for m in
                     re.finditer(r"<th\b[^>]*>(.*?)</th>", thead.group(0), re.S | re.I)]
                    if thead else [])
    tbody = re.search(r"<tbody\b.*?</tbody>", html, re.S | re.I)
    page_rows = len(re.findall(r"<tr\b", tbody.group(0), re.I)) if tbody else 0
    print(f"  page says: {table_count} table(s), headers {page_headers}, {page_rows} data row(s)")

    if table_count != 1:
        problems.append(f"page no longer has exactly 1 table (found {table_count})")
    if page_headers != EXPECTED_HEADERS:
        problems.append(f"page header changed: {page_headers}")
    if page_rows != 1:
        problems.append(f"page no longer has exactly 1 data row (found {page_rows})")
    if page.stat().st_size != 168_504:
        problems.append(f"page bytes changed: {page.stat().st_size} != 168504 (re-verify the fixtures)")

    # -- the parser ----------------------------------------------------------------
    rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)
    for r in rows:
        print(f"    PN {r['part_no']}  {r['price']} {r['currency']}  type={r['price_type']}  "
              f"vat={r['vat']}  country={r['country']}  stock={r['stock']}  | {r['description']}")

    if len(rows) != 1:
        problems.append(f"expected exactly 1 row, got {len(rows)}")
    if not rows:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1

    r0 = rows[0]
    if r0["part_no"] != "8982146870":
        problems.append(f"part_no {r0['part_no']!r} != '8982146870' (normalise_pn on '8-98214687-0')")
    if r0["price"] != 737.0:
        problems.append(f"price {r0['price']!r} != 737.0")
    if r0["currency"] != "NOK":
        problems.append(f"currency {r0['currency']!r} != 'NOK'")
    if r0["price_type"] != "dealer":
        problems.append(f"price_type {r0['price_type']!r} != 'dealer'")
    if r0["vat"] != "excl":
        problems.append(f"vat {r0['vat']!r} != 'excl'")
    if r0["country"] != "NO":
        problems.append(f"country {r0['country']!r} != 'NO'")
    if r0["stock"] != "in":
        problems.append(f"stock {r0['stock']!r} != 'in'")
    if r0["match_method"] != "exact_oem":
        problems.append(f"match_method {r0['match_method']!r} != 'exact_oem'")
    if r0["source"] != "Tungen Bil AS":
        problems.append(f"source {r0['source']!r} != 'Tungen Bil AS'")
    if r0["loader"] != "tungen":
        problems.append(f"loader {r0['loader']!r} != 'tungen'")
    if r0["vintage"] != f"Tungen {PROBE_DATE}":
        problems.append(f"vintage {r0['vintage']!r} != 'Tungen {PROBE_DATE}'")
    if r0["price_eur"] is not None:
        problems.append("price_eur was filled — no NOK rate exists in the ledger FX table")
    if r0["n_obs"] != 1:
        problems.append(f"n_obs {r0['n_obs']!r} != 1 (Antall is stock, not an observation count)")
    if "CAP. WEEL" not in (r0["description"] or ""):
        problems.append(f"the Beskrivelse column was lost: {r0['description']!r}")
    if "Antall 1" not in (r0["description"] or ""):
        problems.append(f"the Antall value was not carried in the description: {r0['description']!r}")

    # -- THE test this module exists for: header recognised, data row gone ------------
    header_only = re.sub(r"<tbody\b.*?</tbody>", "<tbody></tbody>", html, flags=re.S | re.I)
    if header_only == html:
        problems.append("could not build the header-only fixture — the tbody pattern did not match")
    else:
        try:
            got = parse(header_only, source_url=PROBE_URL, observed_at=PROBE_DATE)
            problems.append(f"header-only table returned {got!r} instead of raising ParseError")
        except ParseError as e:
            print(f"\n  header-only table raises ParseError as required: {e}")

    # -- other shapes that must fail loudly, never quietly ---------------------------
    broken = [
        ("", "empty string"),
        ("<html>no tables at all</html>", "no table"),
        ("<html><table><thead><tr><th>A</th><th>B</th></tr></thead>"
         "<tbody><tr><td>x</td><td>y</td></tr></tbody></table></html>", "a different table"),
    ]
    for bad, label in broken:
        try:
            parse(bad)
            problems.append(f"{label}: parse returned instead of raising")
        except ParseError:
            print(f"  {label}: raises ParseError" if label != "" else "  empty string: raises ParseError")

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("\n  SELFTEST PASS - 1 row; 8982146870 / 737.0 NOK / dealer / excl; "
          "header-only table raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
