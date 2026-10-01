# -*- coding: utf-8 -*-
"""Run the part-number shops over a list of OUR part numbers.

WHY ONLY THREE SHOPS
--------------------
A runner needs a site whose address can carry a part number. Measured 2026-09-25:

  QUERY BY PART NUMBER (this runner covers these)
    ks        catalogsearch/result/?q=<pn>
    amayama   /en/part/isuzu/<pn>
    omega     /?s=<pn>&post_type=product          (redirects to the product page)

  NOT QUERYABLE — a different, larger job
    geparden  robots blocks /search; product slugs contain a description, so a URL
              cannot be built from the part number alone. Sitemap walk only.
    mekster   /sok 404s and robots blocks */catalogsearch/. Sitemap walk only.
    tungen    one static category page, no query parameter.
    autoline  a brand listing page, not a part-number lookup.

Saying this plainly matters: "run the scraper across the part list" is only true for
three of the seven sites.

DISCIPLINE
----------
Every fetch goes through `fetch_polite.PoliteFetcher`, which runs
`check_scrape_consent.py` first, keeps >= 2.2 s between requests to the same host, and
caches the bytes to disk so a re-parse never re-fetches.

Small-batch first, per the plan: `--limit` defaults to a small number and the run
reports what it did before anyone scales it.

Usage
-----
    python 04_tools/delegation/parsers/run_part_queries.py --limit 5
    python 04_tools/delegation/parsers/run_part_queries.py --site ks --limit 20
    python 04_tools/delegation/parsers/run_part_queries.py --seed my_pns.csv --parse
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent            # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))

from fetch_polite import PoliteFetcher, ConsentRefused, MIN_INTERVAL   # noqa: E402

GRADED = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
REPORT = HERE / "_part_query_run.json"

# site -> (url template, country, page kind the parser expects)
SITES = {
    "ks": ("https://www.ks-international.com/catalogsearch/result/?q={pn}", "UK", "search"),
    "amayama": ("https://www.amayama.com/en/part/isuzu/{pn}", "JP", "product"),
    "omega": ("https://omegaspareparts.com/?s={pn}&post_type=product", "UK", "product"),
}


def default_seed() -> list[str]:
    """OUR part numbers that already have a graded, usable rival cross-reference.

    That is the right seed: those are the parts where a competitor number is known to
    exist, so a shop that carries the aftermarket line should return something. Parts
    with no known counterpart are a coverage question, not a lookup.
    """
    if not GRADED.exists():
        return []
    import pandas as pd
    d = pd.read_csv(GRADED, dtype=str)
    usable = d[d["tier"].isin(["confirmed", "likely"])]
    return sorted(usable["part_no"].dropna().unique().tolist())


def read_seed(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"seed file not found: {p}")
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    col = next((c for c in (rows[0].keys() if rows else []) if c.lower() in
                ("part_no", "pn", "part_number", "isze_pn")), None)
    if not col:
        raise SystemExit(f"seed needs a part-number column; got {list(rows[0].keys()) if rows else []}")
    import re
    out = []
    for r in rows:
        digits = re.sub(r"\D", "", str(r[col]))
        if len(digits) == 10:
            out.append(digits)
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", help="CSV with a part-number column (default: graded usable parts)")
    ap.add_argument("--site", choices=list(SITES) + ["all"], default="all")
    ap.add_argument("--limit", type=int, default=5,
                    help="how many part numbers to query (small-batch-first; default 5)")
    ap.add_argument("--parse", action="store_true", help="also parse what was fetched")
    ap.add_argument("--online", action="store_true",
                    help="actually fetch. Without this the run is a dry plan.")
    a = ap.parse_args()

    pns = read_seed(a.seed) if a.seed else default_seed()
    if not pns:
        print("no part numbers to work with")
        return 1

    sites = list(SITES) if a.site == "all" else [a.site]
    todo = pns[:a.limit]

    print(f"seed part numbers : {len(pns):,}")
    print(f"this run          : {len(todo)} part numbers x {len(sites)} site(s) "
          f"= {len(todo) * len(sites)} requests")
    print(f"spacing           : >= {MIN_INTERVAL}s per host")
    print(f"mode              : {'LIVE FETCH' if a.online else 'plan only (use --online to fetch)'}")
    print()

    for s in sites:
        print(f"   {s:<9} {SITES[s][0]}")

    result = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "online": a.online, "limit": a.limit, "sites": sites,
              "part_numbers": todo, "fetched": 0, "cached": 0, "errors": 0,
              "refused": 0, "by_site": {}}

    if not a.online:
        print("\nNothing fetched. Re-run with --online to make the requests.")
        REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0

    fetcher = PoliteFetcher()
    for site in sites:
        tpl, country, kind = SITES[site]
        got = 0
        print(f"\n--- {site} ---")
        for pn in todo:
            url = tpl.format(pn=pn)
            try:
                html = fetcher.get(url)
            except ConsentRefused:
                print(f"   {pn}  REFUSED by the consent gate — stopping this site")
                result["refused"] += 1
                break
            if html:
                got += 1
                print(f"   {pn}  ok  ({len(html):,} chars)")
            else:
                print(f"   {pn}  no page")
        result["by_site"][site] = got

    result["fetched"] = fetcher.stats["fetched"]
    result["cached"] = fetcher.stats["cached"]
    result["errors"] = fetcher.stats["errors"]
    result["refused"] += fetcher.stats["refused"]

    print(f"\n{'='*70}")
    print(f"fetched {result['fetched']}  cached {result['cached']}  "
          f"errors {result['errors']}  refused {result['refused']}")
    for s, n in result["by_site"].items():
        print(f"   {s:<10} {n} page(s)")

    if a.parse:
        print("\n--- parsing what was fetched ---")
        import registry
        import run_probe
        for site in sites:
            try:
                res = run_probe.run_one(site)
                print(f"   {site:<10} rows={res['rows']}  ok={res['ok']}  {res.get('error') or ''}")
            except Exception as e:                                 # noqa: BLE001
                print(f"   {site:<10} parse failed: {type(e).__name__}: {e}")
        print("\n   note: the parser reads its OWN saved probe page, so a row count here is "
              "the fixture, not the newly fetched pages. Wiring the new pages into the "
              "parsers is the next step and is not done.")

    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {REPORT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
