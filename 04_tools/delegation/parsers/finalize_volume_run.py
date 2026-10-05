# -*- coding: utf-8 -*-
"""One command to finish the volume run: pages -> prices -> ledger -> movement -> checks.

Runs after a `run_part_queries.py --online` pass. It does NOT fetch anything.

  1. parse every cached page for the seeded part numbers, report coverage honestly
  2. copy the pages into _probe/ and append them to page_manifest.csv
  3. rebuild the offered rows (the bridge)
  4. rebuild the ledger
  5. run the four checks: verbatim, additive, movement, tender-price join

Step 1 is also the honest report of what the run actually achieved, which is the number
that matters: how many of the queried part numbers produced a usable price.

Usage:
    python 04_tools/delegation/parsers/finalize_volume_run.py
"""
from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent          # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
CACHE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "cache"
PROBE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
MANIFEST = ISZE / "04_tools" / "price_ledger" / "page_manifest.csv"

SITES = {
    "ks": ("site_ks", "https://www.ks-international.com/catalogsearch/result/?q={pn}"),
    "amayama": ("site_amayama", "https://www.amayama.com/en/part/isuzu/{pn}"),
    "omega": ("site_omega", "https://omegaspareparts.com/?s={pn}&post_type=product"),
}

# the parser messages that mean "this shop does not stock that part", not "broken"
MISS_MARKERS = ("read no 10-digit Isuzu part number", "carries 0 product cards",
                "found 0 valid data rows", "no Isuzu part numbers in any title")


def cache_path(url: str) -> Path:
    return CACHE / urlparse(url).netloc / f"{hashlib.sha256(url.encode()).hexdigest()[:16]}.html"


def seed_pns() -> list[str]:
    import pandas as pd
    p = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "seed_reach_tierA.csv"
    d = pd.read_csv(p, dtype=str)
    return [str(x) for x in d["part_no"].dropna() if len(str(x)) == 10]


def main() -> int:
    pns = seed_pns()
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"seed part numbers: {len(pns)}   date: {date}\n")

    per_site: dict[str, dict] = {}
    total_rows = 0
    priced_rows = 0
    rows_by_type = Counter()
    manifest_lines: list[str] = []

    for site, (modname, tpl) in SITES.items():
        try:
            mod = importlib.import_module(modname)
        except Exception as e:                                     # noqa: BLE001
            print(f"{site}: module failed to import ({e})")
            continue

        cached = parsed = miss = broke = 0
        rows_for_site = 0
        priced_for_site = 0
        for pn in pns:
            url = tpl.format(pn=pn)
            cp = cache_path(url)
            if not cp.exists():
                continue
            cached += 1
            html = cp.read_text(encoding="utf-8", errors="replace")
            try:
                rows = mod.parse(html, source_url=url, observed_at=date)
            except Exception as e:                                 # noqa: BLE001
                # Same MISS-vs-BREAK distinction the bridge makes. A shop returning a
                # valid "no products found" page is data, not a fault — the parser
                # message alone cannot tell them apart, so the page decides. Without
                # this, Omega's 273 genuine empty-result pages read as broken.
                low = html[:20000].lower()
                empty_page = any(m in low for m in (
                    "you searched for", "no products were found", "nothing found",
                    "returned no results", "0 results"))
                if empty_page or any(m in str(e) for m in MISS_MARKERS):
                    miss += 1
                else:
                    broke += 1
                continue
            parsed += 1
            rows_for_site += len(rows)
            priced_for_site += sum(1 for r in rows if r.get("price") is not None)
            for r in rows:
                rows_by_type[r.get("price_type")] += 1

            # make the page visible to the bridge
            name = f"run{date}_{site}_{pn}.html"
            dst = PROBE / name
            if not dst.exists():
                shutil.copy2(cp, dst)
            manifest_lines.append(f"{site},{url},{name},{date},volume run")

        per_site[site] = {"cached": cached, "parsed": parsed, "miss": miss, "broken": broke,
                          "rows": rows_for_site, "priced": priced_for_site}
        total_rows += rows_for_site
        priced_rows += priced_for_site
        print(f"{site:<9} cached={cached:>4}  with rows={parsed:>4}  not stocked={miss:>4}  "
              f"broken={broke:>3}  -> {rows_for_site:>5} rows ({priced_for_site} priced)")

    print(f"\n{'='*74}")
    print(f"TOTAL rows produced : {total_rows}")
    print(f"      with a price  : {priced_rows}")
    print(f"      price types   : {dict(rows_by_type)}")
    hit = 100 * total_rows / max(1, sum(v['cached'] for v in per_site.values()))
    print(f"      row yield     : {hit:.1f}% of fetched pages produced a row")

    # ---- append to the manifest ------------------------------------------------
    if manifest_lines:
        existing = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        new = [ln for ln in manifest_lines if ln.split(",")[2] not in existing]
        if new:
            with MANIFEST.open("a", encoding="utf-8") as fh:
                if existing and not existing.endswith("\n"):
                    fh.write("\n")
                fh.write("\n".join(new) + "\n")
            print(f"\nappended {len(new)} page(s) to page_manifest.csv")

    # ---- downstream ------------------------------------------------------------
    steps = [
        ("bridge", ISZE / "04_tools" / "price_ledger" / "build_scraped_observations.py", ["--emit"]),
        ("ledger", ISZE / "04_tools" / "price_ledger" / "build_price_ledger.py", []),
        ("verbatim check", ISZE / "04_tools" / "price_ledger" / "verify_scraped_observations.py", []),
        ("additive check", ISZE / "04_tools" / "price_ledger" / "check_loader_additive.py", []),
        ("price movement", ISZE / "04_tools" / "aftermarket_intelligence" / "build_price_movement.py", []),
        ("tender join", ISZE / "04_tools" / "aftermarket_intelligence" / "build_tender_price_context.py", []),
    ]
    print(f"\n{'='*74}\nDOWNSTREAM\n{'='*74}")
    fails = []
    for label, script, args in steps:
        p = subprocess.run([sys.executable, str(script), *args], cwd=str(ISZE),
                           capture_output=True, text=True, errors="replace")
        ok = p.returncode == 0
        print(f"{'ok  ' if ok else 'FAIL'} {label}")
        if not ok:
            fails.append(label)
            for ln in (p.stdout + p.stderr).strip().splitlines()[-5:]:
                print(f"        {ln[:120]}")

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": len(pns), "per_site": per_site,
        "total_rows": total_rows, "priced_rows": priced_rows,
        "rows_by_price_type": dict(rows_by_type),
        "downstream_failures": fails,
    }
    out = HERE / "_volume_run_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {out.name}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
