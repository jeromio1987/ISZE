# -*- coding: utf-8 -*-
"""Load what the runner fetched into the ledger, through the existing manifest.

The pieces already exist and this adds no new path:

  1. copy each cached page into `_probe/` under a readable name
  2. append a row per page to `page_manifest.csv` (the explicit list the bridge reads)
  3. the bridge, the ledger and the verbatim check then work unchanged

`page_manifest.csv` is the designed entry point — "a page cannot enter the ledger by
accident" — so runner output goes in the same way a hand-saved page does.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent           # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
PROBE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
CACHE = PROBE / "cache"
MANIFEST = ISZE / "04_tools" / "price_ledger" / "page_manifest.csv"

SITE_TPL = {
    "ks": ("https://www.ks-international.com/catalogsearch/result/?q={pn}", "ks"),
    "amayama": ("https://www.amayama.com/en/part/isuzu/{pn}", "amayama"),
    "omega": ("https://omegaspareparts.com/?s={pn}&post_type=product", "omega"),
}


def cache_path(url: str) -> Path:
    host = urlparse(url).netloc.replace(":", "_")
    return CACHE / host / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}.html"


def main() -> int:
    run_file = HERE / "_part_query_run.json"
    if not run_file.exists():
        print("no run file — run run_part_queries.py --online first")
        return 1
    run = json.loads(run_file.read_text(encoding="utf-8"))
    if not run.get("online"):
        print("the last run was a dry plan; nothing to load")
        return 1

    date = run["run_at"][:10]
    existing = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
    added, copied = [], 0

    for site, (tpl, tag) in SITE_TPL.items():
        for pn in run["part_numbers"]:
            url = tpl.format(pn=pn)
            src = cache_path(url)
            if not src.exists():
                continue
            name = f"run{date}_{tag}_{pn}.html"
            dst = PROBE / name
            if not dst.exists():
                shutil.copy2(src, dst)
                copied += 1
            if name in existing or any(name in a for a in added):
                continue
            added.append(f"{site},{url},{name},{date},fetched by run_part_queries.py")

    if not added:
        print("nothing new to add to the manifest")
        return 0

    if not MANIFEST.exists():
        MANIFEST.write_text(
            "site,source_url,page_file,fetched_at,note\n" + "\n".join(added) + "\n",
            encoding="utf-8")
    else:
        with MANIFEST.open("a", encoding="utf-8") as fh:
            if not existing.endswith("\n"):
                fh.write("\n")
            fh.write("\n".join(added) + "\n")

    print(f"copied {copied} page(s) into _probe")
    print(f"appended {len(added)} row(s) to page_manifest.csv:")
    for a in added:
        print(f"   {a.split(',')[0]:<9} {a.split(',')[2]}")

    # sanity: the manifest must still parse
    rows = list(csv.DictReader((MANIFEST).read_text(encoding="utf-8").splitlines()))
    print(f"\nmanifest now holds {len(rows)} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
