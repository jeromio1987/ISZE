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
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent                    # 04_tools/price_ledger
ISZE = HERE.parents[1]
PARSERS = ISZE / "04_tools" / "delegation" / "parsers"
PROBE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
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
}

# The two checks a script can do on its own. Everything else needs a human sample.
KNOWN_JUNK_PRICES = {2.34, 2.0}     # the placeholder the retired Autodoc source used


def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        raise SystemExit(f"no manifest at {MANIFEST}")
    with MANIFEST.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("site", "").strip()]
    return rows


def parse_page(entry: dict) -> tuple[list[dict], str | None]:
    """Parse one saved page. Returns (rows, error). Never raises."""
    site = entry["site"].strip()
    page_file = entry["page_file"].strip()
    module_name = SITE_MODULE.get(site)
    if module_name is None:
        return [], f"no parser registered for site {site!r}"

    page = PROBE / page_file
    if not page.exists():
        return [], f"saved page missing on disk: {page}"

    try:
        mod = importlib.import_module(module_name)
    except Exception as e:                                          # noqa: BLE001
        return [], f"{module_name} failed to import: {type(e).__name__}: {e}"

    html = page.read_text(encoding="utf-8", errors="replace")
    try:
        rows = mod.parse(html, source_url=entry["source_url"].strip(),
                         observed_at=entry["fetched_at"].strip())
    except NotImplementedError as e:
        return [], f"{site}: parser still a stub: {e}"
    except Exception as e:                                          # noqa: BLE001
        return [], f"{site}: parse raised {type(e).__name__}: {e}"
    return rows, None


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
        "observed_at", "price_type", "loader", "description", "source_url"))
    out["obs_id"] = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return out


def verdict_for(row: dict) -> str:
    """The mechanical checks (plan §5 items 2-4). Returns '' or 'reject:<reason>'."""
    problems = ledger_schema.row_problems(row)
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

    for entry in entries:
        site = entry["site"].strip()
        rows, err = parse_page(entry)
        stat = per_site.setdefault(site, {"pages": 0, "rows": 0, "priced": 0, "rejected": 0})
        stat["pages"] += 1

        if err:
            errors.append(f"{entry['page_file']}: {err}")
            print(f"  FAIL  {site:<9} {entry['page_file']:<26} {err}")
            continue

        priced = 0
        for r in rows:
            row = normalise(r, entry, fx)
            # Which page this row was actually read from. Needed by the verbatim check:
            # a row's own source_url is often a per-item URL (autoline listings), so it
            # cannot be used to find the page the parser was given.
            row["page_file"] = entry["page_file"].strip()
            v = verdict_for(row)
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
              f"{len(rows)} row(s), {priced} priced")

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
        print(f"\nPAGE FAILURES ({len(errors)}):")
        for e in errors:
            print(f"   {e}")

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
            "errors": errors,
            "per_site": per_site,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {a.json}")

    # A page that fails to parse is a hard stop: offering a partial set would look
    # complete while quietly missing a source.
    if errors:
        print(f"\nREFUSED — {len(errors)} page(s) could not be parsed; nothing offered")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
