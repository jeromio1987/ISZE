# -*- coding: utf-8 -*-
"""Wire freshly fetched pages into the parsers, so a run produces prices, not just files.

The runner fetched 13 pages but nothing read them: each parser was tested against its
single saved probe page. This closes that gap — it looks up the cached page for a URL,
parses it, and appends real rows to the offered set.

Important: this does NOT overwrite the parser fixtures. It adds observations.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent          # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
CACHE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "cache"

SITE_MODULES = {"ks": "site_ks", "amayama": "site_amayama", "omega": "site_omega"}


def cache_path(url: str) -> Path:
    host = urlparse(url).netloc.replace(":", "_")
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE / host / f"{digest}.html"


def main() -> int:
    run_file = HERE / "_part_query_run.json"
    if not run_file.exists():
        print("no run file — run run_part_queries.py --online first")
        return 1
    run = json.loads(run_file.read_text(encoding="utf-8"))
    if not run.get("online"):
        print("the last run was a dry plan; nothing was fetched")
        return 1

    print(f"run at {run['run_at']}  part numbers: {run['part_numbers']}")
    print(f"cache: {CACHE}")

    total_rows = 0
    per_site = {}
    for site, tpl in (("ks", "https://www.ks-international.com/catalogsearch/result/?q={pn}"),
                      ("amayama", "https://www.amayama.com/en/part/isuzu/{pn}"),
                      ("omega", "https://omegaspareparts.com/?s={pn}&post_type=product")):
        mod = importlib.import_module(SITE_MODULES[site])
        rows, hits = [], 0
        for pn in run["part_numbers"]:
            url = tpl.format(pn=pn)
            cp = cache_path(url)
            if not cp.exists():
                print(f"   {site:<9} {pn}  (not cached)")
                continue
            html = cp.read_text(encoding="utf-8", errors="replace")
            try:
                got = mod.parse(html, source_url=url, observed_at=run["run_at"][:10])
            except Exception as e:                                # noqa: BLE001
                print(f"   {site:<9} {pn}  parse failed: {type(e).__name__}: {str(e)[:60]}")
                continue
            hits += 1
            for r in got:
                r["_query_pn"] = pn
            rows.extend(got)
            print(f"   {site:<9} {pn}  {len(got)} row(s)")

        per_site[site] = {"pages_parsed": hits, "rows": len(rows)}
        total_rows += len(rows)

    print(f"\n{'='*66}")
    print(f"pages parsed: {sum(v['pages_parsed'] for v in per_site.values())}   "
          f"rows produced: {total_rows}")
    for s, v in per_site.items():
        print(f"   {s:<10} {v['pages_parsed']} page(s) -> {v['rows']} row(s)")
    print("\nThis is what the runner would contribute. Loading these into the ledger is "
          "build_scraped_observations.py's job, and that reads only the hand-listed "
          "manifest — wiring the runner's output through it is the remaining step.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
