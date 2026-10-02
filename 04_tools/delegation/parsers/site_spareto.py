# -*- coding: utf-8 -*-
"""Spareto (spareto.com) — OE-number page: aftermarket brand numbers listed against an
Isuzu OE number, with a EUR price per brand part. The first working COMPETITOR-NUMBER
source in this package. Recon: `00_docs/agent/CROSSREF_SOURCE_RECON_2026-10-01.md`.

Evidence (all saved 2026-10-01 under `_recon_crossref/spareto/`)
---------------------------------------------------------------
* `oe_8982705240.html` — https://spareto.com/oe/8982705240, title
  `8982705240 - Oil filter, oil filter by ISUZU`, **13** brand cards
  (BLUE PRINT ADZ92130 EUR 8.54 ... ASHIKA 10-ECO150 EUR 6.58 ... BOSCH F 026 407 349
  EUR 8.47 ... HENGST FILTER E1194H D1072 EUR 8.20).
* `oe_5876102320.html` — clutch kit: "Nothing Matches your Search for: 5876102320".
  A clean miss, not a broken page.
* `product_blueprint_adz94218.html` — a brand product page; its "OE Numbers" block
  lists ISUZU 8-98244-794-0 (= our 8982447940), which is the reverse direction
  (brand number -> Isuzu OE).
* robots.txt (`_recon_crossref/robots/spareto.com.robots.txt`): `/oe/` and `/products/`
  are not disallowed; `Crawl-delay: 1`. Conditions of Sale (`spareto/terms.html`) carry no
  clause on automated access. Seller: Spareto OU, Tallinn, Estonia.

What one row is
---------------
One row per brand card on `/oe/<our number>`:

  part_no          our Isuzu number — ONLY if the page states it is the OE page for that
                   number (title `<pn> - ... by ... ISUZU`). Never read off a card.
  match_method     `crossref` — Spareto lists the brand part as compatible with the OE
                   number; the brand number is not our number.
  competitor_brand / competitor_pn   from the card's own GTM item JSON (`item_brand`,
                   `item_id`), i.e. exactly what the card prints.
  price / currency the card's `data-variant-card-price-value` / `-currency-value`.
  vat              `incl` — the Conditions of Sale say EU prices are shown including VAT.
                   The rate is the delivery country's, which the page states (Belgium on
                   these fixtures, from the requesting IP). Not stripped here: the parser
                   does not know Spareto's VAT treatment well enough to back it out.
  price_type       `aftermarket_retail`; a card whose brand is ISUZU is `genuine_grey`.

Same columns as `04_tools/price_ledger/KS_CROSSREF_ROWS.csv` (ledger `COLUMNS`).

Coverage limits seen in the recon (do not over-read)
----------------------------------------------------
* The product pages for the two N-series truck numbers tested show an EMPTY
  "Fit Vehicles" list: Spareto holds the number link, not the truck fitment. The D-Max
  brake disc (8983767550) does show `D-MAX 2017 - ...`.
* 1 of 5 seed numbers (clutch kit 5876102320) returned nothing.

Fetching is NOT done in `parse()`. `main()` fetches only through
`fetch_polite.PoliteFetcher` (consent gate, >= 2.2 s per host, disk cache), small batch.

Usage
-----
    python site_spareto.py --selftest
    python site_spareto.py --parse-recon            # parse the saved recon pages, write a sample CSV
    python site_spareto.py --online --pn 8982705240 # one live page, through the consent gate
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))
from ledger_schema import COLUMNS, make_row, normalise_pn, row_problems   # noqa: E402

SITE = "spareto"
SOURCE = "Spareto"
PROBE_PAGE = "v_spareto_oe_8982705240.html"          # copy of the recon page, in _probe/
PROBE_URL = "https://spareto.com/oe/8982705240"
PROBE_DATE = "2026-10-01"
COUNTRY = "BE"                                       # delivery country the fixtures show
OE_URL = "https://spareto.com/oe/{pn}"
RECON = HERE / "_recon_crossref" / "spareto"
SAMPLE_OUT = RECON / "SPARETO_CROSSREF_SAMPLE.csv"

CARD_SELECTOR = "div.card-product[data-variant-card-gtm-item-value]"
_COUNTRY_CODES = {"belgium": "BE", "netherlands": "NL", "germany": "DE", "united kingdom": "UK",
                  "france": "FR", "ireland": "IE", "portugal": "PT", "spain": "ES",
                  "estonia": "EE", "united states": "US"}


class ParseError(RuntimeError):
    """The page was not the shape we know. Never return [] for this."""


def _soup(html: str):
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "html.parser")


def _squash(s: str | None) -> str:
    return re.sub(r"[\s\-./]", "", str(s or "")).upper()


def is_no_match(html: str) -> bool:
    return "Nothing Matches your Search" in (html or "")


def page_oe(soup) -> tuple[str | None, list[str]]:
    """(our number, OE makes) if this is an OE page: title `<number> - <name> by <MAKES>`."""
    title = soup.title.get_text(strip=True) if soup.title else ""
    m = re.match(r"^\s*([0-9A-Z\-\s]+?)\s+-\s+.*\sby\s+(.+)$", title)
    if not m:
        return None, []
    makes = [x.strip().upper() for x in m.group(2).split(",")]
    return normalise_pn(m.group(1)), makes


def delivery_country(html: str) -> str | None:
    m = re.search(r"id='dropdownProposition'[^>]*>\s*([^<]+?)\s*</a>", html)
    if not m:
        return None
    name = m.group(1).strip()
    return _COUNTRY_CODES.get(name.lower(), name)


def parse(html: str, *, source_url: str = "", observed_at: str = "") -> list[dict]:
    """`/oe/<pn>` page -> one crossref row per brand card. [] on Spareto's clean miss."""
    if not html or len(html) < 500:
        raise ParseError(f"page too small to be a Spareto page ({len(html or '')} chars)")
    if is_no_match(html):
        return []
    soup = _soup(html)
    pn, makes = page_oe(soup)
    if not pn:
        raise ParseError("title is not `<isuzu number> - <name> by <makes>` — not an OE page, "
                         "or the layout changed")
    if "ISUZU" not in makes:
        raise ParseError(f"OE page for {pn} but the makes are {makes}, not ISUZU")
    cards = soup.select(CARD_SELECTOR)
    if not cards:
        raise ParseError(f"OE page for {pn} with no brand cards — layout changed?")

    country = delivery_country(html) or COUNTRY
    rows: list[dict] = []
    for c in cards:
        try:
            item = json.loads(c["data-variant-card-gtm-item-value"])
        except (KeyError, json.JSONDecodeError):
            continue
        brand = (item.get("item_brand") or "").strip()
        cpn = (item.get("item_id") or "").strip()
        if not brand or not cpn:
            continue
        # The card must print the same brand number it carries in its JSON.
        if _squash(cpn) not in _squash(c.get_text(" ", strip=True)):
            continue
        try:
            price = float(c.get("data-variant-card-price-value"))
        except (TypeError, ValueError):
            price = None
        currency = (c.get("data-variant-card-currency-value") or "").strip() or None
        text = c.get_text(" ", strip=True)
        dispatch = re.search(r"(?i)(dispatch\s+(?:on|in)\s+(?:next\s+business\s+day|\d+\s+business\s+days?))", text)
        dispatch = re.sub(r"\s+", " ", dispatch.group(1)) if dispatch else None
        genuine = brand.upper() == "ISUZU"
        name = item.get("item_name") or ""
        bits = [f"{brand} {cpn} {name}".strip(),
                f"listed by Spareto as compatible with OE {pn}"]
        if dispatch:
            bits.append(dispatch)
        rows.append(make_row(
            part_no=pn, match_method="crossref",
            competitor_brand=brand, competitor_pn=cpn,
            description=" — ".join(bits),
            source=SOURCE, source_url=source_url or OE_URL.format(pn=pn), country=country,
            observed_at=observed_at, vintage=f"Spareto {observed_at}",
            price=price, currency=currency, price_eur=None, fx_note=None,
            vat="incl", price_type="genuine_grey" if genuine else "aftermarket_retail",
            stock="in" if dispatch and "next business day" in dispatch.lower() else "unknown",
            n_obs=1, loader="spareto_crossref",
        ))
    if not rows:
        raise ParseError(f"{len(cards)} card(s) on the OE page for {pn}, none readable")
    return rows


def parse_product(html: str) -> dict:
    """Brand product page -> reverse lookup: {brand, number, isuzu_oe[], cross_refs{}}.

    `isuzu_oe` holds only numbers `normalise_pn` accepts as Isuzu 10-digit numbers.
    """
    soup = _soup(html)
    block = soup.select_one("#nav-oe")
    if block is None:
        raise ParseError("no `#nav-oe` Reference Numbers block — not a product page")
    title = soup.title.get_text(strip=True) if soup.title else ""
    out = {"title": title, "isuzu_oe": [], "oe": {}, "cross_refs": {}}
    section = None
    for el in block.find_all(["h3", "div"], recursive=True):
        if el.name == "h3":
            section = el.get_text(strip=True)
            continue
        if "row" not in (el.get("class") or []):
            continue
        cols = el.find_all("div", recursive=False)
        if len(cols) < 2:
            continue
        make = cols[0].get_text(strip=True).upper()
        nums = [x.get_text(strip=True) for x in cols[1].find_all(["a", "span"])]
        bucket = out["oe"] if section == "OE Numbers" else out["cross_refs"]
        bucket.setdefault(make, []).extend(n for n in nums if n)
    for n in out["oe"].get("ISUZU", []):
        p = normalise_pn(n)
        if p and p not in out["isuzu_oe"]:
            out["isuzu_oe"].append(p)
    out["number"] = title.split()[0] if title else None      # `ADZ94218 BLUE PRINT ... | Spareto`
    return out


# ── selftest ───────────────────────────────────────────────────────────────────

def selftest() -> int:
    problems: list[str] = []
    print("=" * 74)

    def load(name: str) -> str | None:
        p = RECON / name
        if not p.exists():
            problems.append(f"fixture missing: {p}")
            return None
        return p.read_text(encoding="utf-8", errors="replace")

    # 1. OE page, oil filter: 13 cards, values quoted from the page.
    html = load("oe_8982705240.html")
    if html:
        rows = parse(html, source_url=PROBE_URL, observed_at=PROBE_DATE)
        print(f"  oe_8982705240.html -> {len(rows)} rows")
        for r in rows[:4]:
            print(f"    {r['part_no']}  {r['competitor_brand']:<22} {r['competitor_pn']:<18} "
                  f"{r['price']} {r['currency']} vat={r['vat']} stock={r['stock']} {r['country']}")
        if len(rows) != 13:
            problems.append(f"expected 13 rows on the oil-filter page, got {len(rows)}")
        got = {(r["competitor_brand"], r["competitor_pn"]): r["price"] for r in rows}
        for key, price in {("ASHIKA", "10-ECO150"): 6.58, ("BOSCH", "F 026 407 349"): 8.47,
                           ("BLUE PRINT", "ADZ92130"): 8.54,
                           ("HENGST FILTER", "E1194H D1072"): 8.20}.items():
            if got.get(key) != price:
                problems.append(f"{key}: expected {price}, got {got.get(key)}")
        if {r["part_no"] for r in rows} != {"8982705240"}:
            problems.append("part_no must be the page's OE number on every row")
        if any(r["match_method"] != "crossref" for r in rows):
            problems.append("every row must be match_method=crossref")
        if any(r["currency"] != "EUR" or r["vat"] != "incl" for r in rows):
            problems.append("currency/vat must be EUR/incl as the page states")
        if sum(r["stock"] == "in" for r in rows) != 11:
            problems.append("11 of 13 cards say 'Dispatch on next business day' (2 say 28 days)")
        if any(r["country"] != "BE" for r in rows):
            problems.append("delivery country on the fixture is Belgium")
        for r in rows:
            bad = row_problems(r)
            if bad:
                problems.append(f"row_problems {r['competitor_pn']}: {bad}")
            if list(r.keys()) != COLUMNS:
                problems.append("row keys are not the ledger COLUMNS in order")
                break

    # 2. Clean miss: [] and not an exception.
    html = load("oe_5876102320.html")
    if html:
        rows = parse(html)
        print(f"  oe_5876102320.html -> {len(rows)} rows (clean miss expected)")
        if rows != []:
            problems.append("the clutch-kit page is a 'Nothing Matches' page and must give []")

    # 3. Reverse direction: brand product page -> Isuzu OE numbers.
    html = load("product_blueprint_adz94218.html")
    if html:
        rev = parse_product(html)
        print(f"  product_blueprint_adz94218.html -> isuzu_oe {rev['isuzu_oe']}  "
              f"cross-ref makes {len(rev['cross_refs'])}")
        if "8982447940" not in rev["isuzu_oe"]:
            problems.append("ADZ94218 product page must list ISUZU 8-98244-794-0 = 8982447940")

    # 4. A page that is not an OE page must raise, never return [].
    html = load("terms.html")
    if html:
        try:
            parse(html)
            problems.append("terms page parsed as an OE page — must raise ParseError")
        except ParseError as e:
            print(f"  terms.html -> ParseError as expected ({str(e)[:60]}...)")

    if problems:
        print("\n  SELFTEST FAIL")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("\n  SELFTEST PASS")
    return 0


# ── small-batch CLI ────────────────────────────────────────────────────────────

def _write(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--parse-recon", action="store_true",
                    help="parse the saved recon pages (no network), write the sample CSV")
    ap.add_argument("--online", action="store_true", help="fetch live, through fetch_polite")
    ap.add_argument("--pn", action="append", default=[], help="Isuzu number(s) for --online")
    ap.add_argument("--limit", type=int, default=5, help="max pages with --online (default 5)")
    ap.add_argument("--out", default=str(SAMPLE_OUT))
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    rows: list[dict] = []
    if a.parse_recon:
        for p in sorted(RECON.glob("oe_*.html")):
            got = parse(p.read_text(encoding="utf-8", errors="replace"),
                        source_url=OE_URL.format(pn=p.stem[3:]), observed_at=PROBE_DATE)
            print(f"  {p.name:<22} {len(got)} rows")
            rows += got
    elif a.online:
        from datetime import datetime, timezone
        from fetch_polite import PoliteFetcher, ConsentRefused
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        f = PoliteFetcher()
        for pn in a.pn[:a.limit]:
            url = OE_URL.format(pn=pn)
            try:
                html = f.get(url)
            except ConsentRefused:
                print("  consent refused — stopping")
                break
            got = parse(html, source_url=url, observed_at=today) if html else []
            print(f"  {pn}  {len(got)} rows")
            rows += got
        print(f"  fetch stats {f.stats}")
    else:
        print(__doc__)
        return 0
    _write(rows, Path(a.out))
    print(f"wrote {len(rows)} rows -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
