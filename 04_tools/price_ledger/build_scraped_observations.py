# -*- coding: utf-8 -*-
"""Parse every saved page into candidate ledger rows — and check them before they load.

This is the bridge between the per-site parsers in `04_tools/delegation/parsers/` and
the price-observation ledger. It produces the rows; `build_price_ledger.py` writes
them. It is deliberately separate from both, for two reasons:

  1. **Scope.** A parser must not decide what enters the ledger. That decision needs
     the acceptance checks (plan §5) and the data boundary (§3) in one visible place.
  2. **Blast radius.** Nothing here touches a parquet file, a dashboard or a receipt.
     It writes its own review CSV and nothing else.

What it does, in order
----------------------
1. Reads `page_manifest.csv` — the explicit list of saved pages, one row each, with
   the URL and the date. No globbing, so a page cannot enter the ledger by accident.
2. Parses each page with its site parser and the matching date.
3. Normalises every row against the ledger schema: `part_no` to 10 digits, `vintage`
   always set, `price_eur` filled from the ONE shared rate table, `obs_id` issued.
4. Runs the mechanical checks and writes `OFFERED_ROWS.csv` with a `verdict` column
   (`offer` / `reject:<reason>`), so the rejects are reviewable rather than silent.
5. Refuses to offer anything if a page fails to parse.

**Nothing is loaded.** `--emit` writes the CSV; loading is `build_price_ledger.py`'s job.

The data boundary (plan §3) is respected by construction: only public page text and
public prices are read. No billed revenue, no price list, no dealer identities, and
the Eucon match rows are not touched by any of this.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import re
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent                    # 04_tools/price_ledger
ISZE = HERE.parents[1]
ROOT = Path(__file__).resolve().parents[2]
PARSERS = ROOT / "04_tools" / "delegation" / "parsers"
PROBE = ROOT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
MANIFEST = HERE / "page_manifest.csv"
OFFERED = HERE / "OFFERED_ROWS.csv"
PLACEHOLDER_MAX = 2.34          # Autodoc-style "no result" placeholder, same as the ledger

if str(PARSERS) not in sys.path:
    sys.path.insert(0, str(PARSERS))

import ledger_schema                                               # noqa: E402

# A saved page can only become a ledger row if its site parser knows how to read it.
SITE_MODULE = {
    "amayama": "site_amayama",
    "ks": "site_ks",
    "omega": "site_omega",
    "geparden": "site_geparden",
    "mekster": "site_mekster",
    "tungen": "site_tungen",
    "autoline": "site_autoline",
    # U26 (2026-10-07, agent E merge): the three sources the harvest added. `tmc` pages
    # in the manifest are category listing pages, so they go through `parse_category`
    # (see `dispatch_parse`); `tranzparts` product pages need the number that was
    # searched for, which the search URL does not carry, so it is read from
    # `_u26_e_page_query.csv`; `spareto` pages name their own OE number in the title.
    "tmc": "site_tmc",
    "tranzparts": "site_tranzparts",
    "spareto": "site_spareto",
}

# U26: page_file -> the Isuzu number the shop was searched for, where the page URL
# does not carry it. Written by the U26 merge helper. Absent file = no change to any
# existing site's behaviour.
PAGE_QUERY = HERE / "_u26_e_page_query.csv"
_PAGE_QUERY_CACHE: dict[str, str] | None = None


def _accepts_keyword(fn, name: str) -> bool:
    """True when `fn` declares a keyword argument called `name` (data, not bytecode).

    `co_argcount` counts positional parameters only; a parser that takes its extra
    inputs keyword-only (`def parse(html, *, expected_pn="", ...)`) would be missed,
    so the keyword-only names are counted too.
    """
    try:
        code = fn.__code__
        n = code.co_argcount + code.co_kwonlyargcount
        return name in code.co_varnames[:n]
    except AttributeError:
        return False


def page_query_map() -> dict[str, str]:
    """{page_file: queried Isuzu number}. Empty when the sidecar is absent."""
    global _PAGE_QUERY_CACHE
    if _PAGE_QUERY_CACHE is None:
        _PAGE_QUERY_CACHE = {}
        if PAGE_QUERY.exists():
            with PAGE_QUERY.open(encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    p = (r.get("page_file") or "").strip()
                    q = (r.get("queried_pn") or "").strip()
                    if p and q:
                        _PAGE_QUERY_CACHE[p] = q
    return _PAGE_QUERY_CACHE

# The two checks a script can do on its own. Everything else needs a human sample.
KNOWN_JUNK_PRICES = {2.34, 2.0}     # the placeholder the retired Autodoc source used


def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        raise SystemExit(f"no manifest at {MANIFEST}")
    with MANIFEST.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("site", "").strip()]
    return rows


_MOD_CACHE: dict[str, object] = {}


def parse_page(entry: dict) -> tuple[list[dict], str | None, str]:
    """Parse one saved page. Returns (rows, error, html). Never raises.

    `html` is returned so the Mekonomen guard does not re-read a multi-MB Magento
    page from disk (KS pages are ~2.3 MB each; measured 2026-10-05).
    """
    site = entry["site"].strip()
    page_file = entry["page_file"].strip()
    module_name = SITE_MODULE.get(site)
    if module_name is None:
        return [], f"no parser registered for site {site!r}", ""

    page = PROBE / page_file
    if not page.exists():
        return [], f"saved page missing on disk: {page}", ""

    try:
        mod = _MOD_CACHE.get(module_name)
        if mod is None:
            mod = importlib.import_module(module_name)
            _MOD_CACHE[module_name] = mod
    except Exception as e:                                          # noqa: BLE001
        return [], f"{module_name} failed to import: {type(e).__name__}: {e}", ""

    html = page.read_text(encoding="utf-8", errors="replace")
    try:
        if site == "tmc" and hasattr(mod, "parse_category"):
            # U26: a manifest row for T&M is a category listing page, not a product page.
            rows = mod.parse_category(html, source_url=entry["source_url"].strip(),
                                      observed_at=entry["fetched_at"].strip())
        elif site == "tranzparts" and _accepts_keyword(mod.parse, "expected_pn"):
            # U26: the Tranzparts product page must print the number that was searched
            # for, and that number is not in the product URL. It travels in the sidecar.
            q = page_query_map().get(entry["page_file"].strip(), "")
            rows = mod.parse(html, expected_pn=q,
                             source_url=entry["source_url"].strip(),
                             observed_at=entry["fetched_at"].strip())
        else:
            rows = mod.parse(html, source_url=entry["source_url"].strip(),
                             observed_at=entry["fetched_at"].strip())
    except NotImplementedError as e:
        return [], f"{site}: parser still a stub: {e}", html
    except Exception as e:                                          # noqa: BLE001
        return [], f"{site}: parse raised {type(e).__name__}: {e}", html
    return rows, None, html


def normalise(row: dict, entry: dict, fx: dict) -> dict:
    """Force the row into the ledger's shape. Never invents a value."""
    out = ledger_schema.make_row()
    out.update({k: v for k, v in row.items() if k in ledger_schema.COLUMNS})

    out["part_no"] = ledger_schema.normalise_pn(row.get("part_no"))
    out["observed_at"] = entry["fetched_at"].strip()
    out["vintage"] = row.get("vintage") or f"{entry['site'].strip()} {out['observed_at']}"
    out["source"] = row.get("source") or entry["site"].strip()
    out["source_url"] = row.get("source_url") or entry["source_url"].strip()
    out["loader"] = row.get("loader") or f"scrape_{entry['site'].strip()}"

    # The ONE currency conversion, from the shared table. A parser never converts.
    price = row.get("price")
    currency = row.get("currency")
    out["price_eur"] = ledger_schema.price_eur_for(price, currency, fx)
    if price is not None and currency:
        out["fx_note"] = (f"converted from the shared fx_rates.json at "
                          f"{fx.get(currency.upper())} EUR per {currency.upper()}")

    key = "|".join(str(out.get(c)) for c in (
        "part_no", "competitor_brand", "competitor_pn", "source", "country",
        "observed_at", "price_type", "loader", "description", "source_url",
        # price and currency belong in the key: Amayama quotes the SAME part from
        # several warehouses at different prices (measured 2026-10-01: one part at
        # 18.72 / 20.62 / 24.79 USD). Without these the rows collide on obs_id and the
        # ledger refuses the whole file with "duplicate obs_id" — real prices rejected
        # as if they were a data fault.
        "price", "currency"))
    out["obs_id"] = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return out


def verdict_for(row: dict, page_text: str = "", queried_pn: str = "") -> str:
    """The mechanical checks (plan §5 items 2-4). Returns '' or 'reject:<reason>'."""
    problems = ledger_schema.row_problems(row)

    # --- the Mekonomen guard ---------------------------------------------------
    # When a shop was SEARCHED for our part number, the row is only trustworthy if the
    # page actually carries that number. A shop that cannot find our part often returns
    # its closest unrelated product instead, and a parser reading that page will happily
    # record a price for a different article.
    #
    # Measured 2026-10-01 on the Tier A volume run: asking Omega for Isuzu 8981386950
    # returned a Jeep Cherokee DOOR MIRROR COVER, and the row went in as an Isuzu air
    # filter at GBP 51.11. Eight such rows. This is the same failure as Mekonomen in
    # September, where seven part numbers were priced against a coil spring. Both times
    # the wrong price had a clean audit trail.
    if queried_pn and page_text and queried_pn not in page_text:
        variants = [queried_pn]
        if len(queried_pn) == 10:
            variants += [f"{queried_pn[0]}-{queried_pn[1:6]}-{queried_pn[6:9]}-{queried_pn[9]}",
                         f"{queried_pn[0]}-{queried_pn[1:9]}-{queried_pn[9]}",
                         f"ISU{queried_pn}"]
        if not any(v in page_text for v in variants):
            return (f"reject:shop was searched for {queried_pn} but that number is not on "
                    f"the page — the shop returned a different product")

    # `no part_no` on a category_only row is allowed here: the ledger stores such rows
    # and the match_method says the number is not evidenced. It is recorded, not fatal.
    soft = {"no part_no"}
    hard = [p for p in problems if p not in soft]
    if hard:
        return "reject:" + "; ".join(hard)
    if row.get("part_no") is None and row.get("match_method") != "category_only":
        return f"reject:no part number and match_method={row.get('match_method')!r}"

    price = row.get("price")
    if price is not None:
        try:
            price = float(price)
        except (TypeError, ValueError):
            return f"reject:price not numeric ({row.get('price')!r})"
        # Placeholder check (plan §5 item 3): the retired Autodoc "no result" value.
        if price in KNOWN_JUNK_PRICES:
            return f"reject:known placeholder price {price}"
        if price <= PLACEHOLDER_MAX:
            return f"reject:price at or below the placeholder floor ({price})"
        # Plausibility check (plan §5 item 4): flag, do not reject.
        if row.get("currency") and row.get("price_eur") is None:
            return "flag:no FX rate, euro value unknown"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true", help="write OFFERED_ROWS.csv")
    ap.add_argument("--json", help="also write a machine-readable summary here")
    a = ap.parse_args()

    fx, fx_note = ledger_schema.load_fx_rates()
    entries = read_manifest()
    print(f"page manifest : {len(entries)} saved page(s)")
    print(f"fx            : {fx_note}")
    print()

    all_rows: list[dict] = []
    rejected: list[dict] = []
    errors: list[str] = []
    per_site: dict[str, dict] = {}
    n_entries = len(entries)

    t_start = time.monotonic()
    for i, entry in enumerate(entries, 1):
        # Progress every 100 pages so a redirected batch log is not silent for minutes.
        if i == 1 or i % 100 == 0 or i == n_entries:
            print(f"  ... page {i}/{n_entries}, {time.monotonic() - t_start:.0f} s", flush=True)
        site = entry["site"].strip()
        rows, err, page_text = parse_page(entry)
        stat = per_site.setdefault(site, {"pages": 0, "rows": 0, "priced": 0, "rejected": 0})
        stat["pages"] += 1

        if err:
            errors.append(f"{entry['page_file']}: {err}")
            print(f"  FAIL  {site:<9} {entry['page_file']:<26} {err}", flush=True)
            continue

        # The page text and, where the page came from a part-number query, the number we
        # asked for. Both are needed by the Mekonomen guard in verdict_for().
        queried_pn = ""
        m = re.search(r"[?&](?:q|s)=(\d{10})\b", entry["source_url"] or "")
        if m:
            queried_pn = m.group(1)

        priced = 0
        for r in rows:
            row = normalise(r, entry, fx)
            # Which page this row was actually read from. Needed by the verbatim check:
            # a row's own source_url is often a per-item URL (autoline listings), so it
            # cannot be used to find the page the parser was given.
            row["page_file"] = entry["page_file"].strip()
            v = verdict_for(row, page_text=page_text, queried_pn=queried_pn)
            if v.startswith("reject:"):
                row["verdict"] = v
                rejected.append(row)
                stat["rejected"] += 1
            else:
                row["verdict"] = v or "offer"
                all_rows.append(row)
                stat["rows"] += 1
                if row.get("price") is not None:
                    priced += 1
                    stat["priced"] += 1

        print(f"  ok    {site:<9} {entry['page_file']:<26} "
              f"{len(rows)} row(s), {priced} priced", flush=True)

    print()
    print("=" * 78)
    print(f"{'site':<10} {'pages':>6} {'rows':>6} {'priced':>7} {'rejected':>9}")
    for site in sorted(per_site):
        s = per_site[site]
        print(f"{site:<10} {s['pages']:>6} {s['rows']:>6} {s['priced']:>7} {s['rejected']:>9}")
    print(f"{'TOTAL':<10} {len(entries):>6} {len(all_rows):>6} "
          f"{sum(s['priced'] for s in per_site.values()):>7} {len(rejected):>9}")

    joinable = [r for r in all_rows if r.get("part_no")]
    print(f"\nrows carrying an Isuzu part number (joinable to the book): {len(joinable)}")
    print(f"distinct part numbers: {len({r['part_no'] for r in joinable})}")
    print(f"distinct price types  : {sorted({r['price_type'] for r in all_rows})}")

    flags = [r for r in all_rows if r["verdict"].startswith("flag:")]
    if flags:
        print(f"\nflagged (offered, but read the verdict): {len(flags)}")
        for r in flags[:6]:
            print(f"   {r.get('part_no') or '(no PN)'} {r.get('price')} "
                  f"{r.get('currency')} — {r['verdict']}")

    if rejected:
        print(f"\nREJECTED ({len(rejected)}) — not offered to the ledger:")
        for r in rejected[:8]:
            print(f"   {r.get('part_no') or '(no PN)'} {r.get('price')} "
                  f"{r.get('currency')} — {r['verdict']}")

    if errors:
        print(f"\nPAGE NOTES ({len(errors)} page(s) produced no rows):")

    # Separate a MISS from a BREAK. A page failure is not one kind of thing:
    #
    #   * the shop matched our query to a product that is not ours, or the number is
    #     simply not in their catalogue -> a real answer, not a fault. Measured
    #     2026-10-01: asking Omega for 5876150021 returned an Alfa Romeo brake disc,
    #     and the parser refused it. That refusal is the parser working.
    #   * the JSON-LD is gone, the page is empty, the module will not import -> the
    #     parser is broken and must fail loudly.
    #
    # Treating both as one blocked the first real runner load. The distinction is carried
    # in the message the parser raised.
    MISS_MARKERS = (
        "read no 10-digit Isuzu part number",   # omega: matched a different product
        "carries 0 product cards",               # ks: search returned nothing
        "found 0 valid data rows",                # tungen: table recognised, empty
        "recognised the page but found no price rows",   # amayama: genuine part, no price
        "no Isuzu part numbers in any title",     # autoline: no OEM numbers on the page
        "found no price rows",                    # amayama: page read, but see the page test
    )
    # Some sites return a valid "no results" page rather than an empty product page, and
    # the parser's message for it ("no JSON-LD Product block — the page layout has
    # changed") reads like a fault. The page itself says which it is, so the page decides.
    EMPTY_RESULT_MARKERS = ("you searched for", "no products were found",
                            "nothing found", "0 results", "no results")
    # A part that EXISTS but is out of stock has no price. That is a real answer, not a
    # fault: Amayama shows "Out of stock" and "No deliveries to", and carries no price
    # element at all. Found on four pages 2026-10-01 (8975546610, 8980062591, 8980139111,
    # 8982834751) which were being reported as broken pages.
    NO_PRICE_STATE_MARKERS = ("out-of-stock", "out of stock", "no deliveries",
                              "currently unavailable", "discontinued")

    def is_miss(err: str, page_html: str) -> bool:
        if any(m in err for m in MISS_MARKERS):
            return True
        low = (page_html or "")[:20000].lower()
        if any(m in low for m in EMPTY_RESULT_MARKERS):
            return True
        return any(m in low for m in NO_PRICE_STATE_MARKERS)

    hard_errors, misses = [], []
    for e in errors:
        page_html = ""
        for entry in entries:
            if e.startswith(entry["page_file"]):
                p = PROBE / entry["page_file"]
                if p.exists():
                    page_html = p.read_text(encoding="utf-8", errors="replace")
                break
        (misses if is_miss(e, page_html) else hard_errors).append(e)

    if misses:
        print(f"\nNOT THEIR PART ({len(misses)}) — a real answer, not a fault:")
        for e in misses[:10]:
            print(f"   {e[:150]}")
    if hard_errors:
        print(f"\nBROKEN PAGES ({len(hard_errors)}) — these must be fixed:")
        for e in hard_errors[:10]:
            print(f"   {e[:150]}")

    # Write LAST, so a hard failure leaves the previous OFFERED_ROWS.csv untouched
    # rather than rewriting it and then refusing (which is what happened on 2026-10-01).
    if a.emit:
        cols = ledger_schema.COLUMNS + ["page_file", "verdict"]
        with OFFERED.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in all_rows + rejected:
                w.writerow({c: r.get(c) for c in cols})
        print(f"\nwrote {OFFERED}  ({len(all_rows) + len(rejected)} rows)")

    if a.json:
        Path(a.json).write_text(json.dumps({
            "fx": fx_note,
            "pages": len(entries),
            "offered": len(all_rows),
            "rejected": len(rejected),
            "pages_with_no_rows": len(errors),
            "not_their_part": len(misses),
            "broken_pages": len(hard_errors),
            "errors": errors,
            "per_site": per_site,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {a.json}")

    # Only a BROKEN page stops the run. A shop that does not carry our part is data.
    if hard_errors:
        print(f"\nREFUSED — {len(hard_errors)} page(s) look broken; fix them before loading")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
