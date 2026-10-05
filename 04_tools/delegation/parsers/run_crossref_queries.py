# -*- coding: utf-8 -*-
"""Search KS International by the COMPETITOR's part number, not ours.

WHY THIS EXISTS
---------------
Measured 2026-10-01: the graded cross-reference holds 1,281 usable edges (286 competitor
numbers), and no live scraper had priced a single one. Every live price came in by our
own Isuzu number or by product type. The only script meant to search by competitor number,
`04_tools/autodoc_scraper/crossref_search_runner.py`, reads a file that no longer exists
and targets two retired sites. This replaces it, on the one parts site still answering.

WHAT COUNTS AS A HIT
--------------------
KS is a relevance search: it returns *something* for almost any query. A card is accepted
only when the competitor number we searched for is printed on the card itself (compared
with spaces, dashes, dots and slashes removed, case-insensitive). Anything else is a miss
and is recorded as one; it never becomes a price.

An accepted card becomes one row per OUR part number that the graded edge links to that
competitor number: `match_method = "crossref"`, `competitor_brand` / `competitor_pn` from
the graded edge, price ex-VAT GBP exactly as the KS parser reads it. A card badged genuine
is kept as `genuine_grey`, never as an aftermarket price.

DATA BOUNDARY
-------------
The competitor numbers come from Eucon files. Using them to drive a scrape was Jerome's
explicit go of 2026-09-24. Only the competitor number goes out, as a KS search term. No
Eucon row goes to DeepSeek or any other service; this script calls no model.

Discipline: every fetch goes through `fetch_polite.PoliteFetcher` (consent check,
>= 2.2 s per host, disk cache).

Output: `04_tools/price_ledger/KS_CROSSREF_ROWS.csv` (accepted rows, read by the ledger)
        `04_tools/delegation/parsers/_crossref_query_run.json` (every query, hit or miss)

Usage
-----
    python run_crossref_queries.py                 # plan only
    python run_crossref_queries.py --online --limit 5
    python run_crossref_queries.py --online --limit 999
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent            # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))

from bs4 import BeautifulSoup                                            # noqa: E402
from fetch_polite import PoliteFetcher, ConsentRefused, MIN_INTERVAL     # noqa: E402
import site_ks                                                            # noqa: E402

GRADED = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
OUT_ROWS = ISZE / "04_tools" / "price_ledger" / "KS_CROSSREF_ROWS.csv"
REPORT = HERE / "_crossref_query_run.json"
KS_TPL = "https://www.ks-international.com/catalogsearch/result/?q={q}"
USABLE = {"confirmed", "likely"}


def squash(s: str) -> str:
    return re.sub(r"[\s\-./]", "", str(s or "")).upper()


def seed() -> list[dict]:
    """One entry per distinct competitor number: the number, its brands, our parts."""
    import pandas as pd
    d = pd.read_csv(GRADED, dtype=str)
    d = d[d["tier"].isin(USABLE) & d["competitor_pn"].notna()]
    out = []
    for key, g in d.groupby(d["competitor_pn"].map(squash)):
        if len(key) < 4:                        # too short to be safely matched on a card
            continue
        out.append({
            "cpn_key": key,
            "query": g["competitor_pn"].mode().iat[0].strip(),
            "brands": sorted(set(g["competitor_brand"].dropna())),
            "part_nos": sorted(set(g["part_no"].dropna())),
            "tiers": sorted(set(g["tier"])),
        })
    return sorted(out, key=lambda e: e["cpn_key"])


def card_carries(card, key: str) -> bool:
    return key in squash(card.get_text(" ", strip=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5, help="competitor numbers to query (default 5)")
    ap.add_argument("--online", action="store_true", help="actually fetch")
    a = ap.parse_args()

    entries = seed()
    todo = entries[:a.limit]
    print(f"usable competitor numbers : {len(entries)}")
    print(f"this run                  : {len(todo)} KS searches, >= {MIN_INTERVAL}s apart")
    print(f"mode                      : {'LIVE FETCH' if a.online else 'plan only (use --online)'}")
    if not a.online:
        for e in todo:
            print(f"   {e['query']:<22} {', '.join(e['brands'])[:40]:<40} -> {', '.join(e['part_nos'])}")
        return 0

    fetcher = PoliteFetcher()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log, rows = [], []
    for e in todo:
        url = KS_TPL.format(q=quote_plus(e["query"]))
        rec = {"query": e["query"], "url": url, "part_nos": e["part_nos"], "result": None,
               "cards": 0, "accepted": 0}
        try:
            html = fetcher.get(url)
        except ConsentRefused:
            rec["result"] = "consent_refused"
            log.append(rec)
            print("   consent refused — stopping")
            break
        if not html:
            rec["result"] = "no_page"
            log.append(rec)
            print(f"   {e['query']:<22} no page")
            continue
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(site_ks.CARD_SELECTOR)
        rec["cards"] = len(cards)
        hits = [c for c in cards if card_carries(c, e["cpn_key"])]
        for c in hits:
            r = site_ks._card_row(c, query_pn=None, source_url=url, observed_at=today)
            if not r or r.get("price") is None:
                continue
            rec["accepted"] += 1
            for pn in e["part_nos"]:
                rr = dict(r)
                rr.update(part_no=pn, match_method="crossref",
                          competitor_brand="|".join(e["brands"]) or r.get("competitor_brand"),
                          competitor_pn=e["query"],
                          description=f"{r['description']} — found by competitor number "
                                      f"{e['query']} (graded {'/'.join(e['tiers'])})",
                          loader="ks_crossref", vintage=f"KS International {today}")
                rows.append(rr)
        rec["result"] = "hit" if rec["accepted"] else ("miss_no_card" if not cards else "miss_not_on_card")
        log.append(rec)
        print(f"   {e['query']:<22} cards={len(cards):<3} accepted={rec['accepted']}  {rec['result']}")

    # Merge with earlier runs: keep previous rows for queries not re-run today.
    prev = []
    if OUT_ROWS.exists():
        with OUT_ROWS.open(encoding="utf-8", newline="") as fh:
            prev = list(csv.DictReader(fh))
    done_q = {e["query"] for e in todo}
    keep = [p for p in prev if p.get("competitor_pn") not in done_q]
    allrows = keep + rows
    if allrows:
        cols = list(rows[0].keys()) if rows else list(prev[0].keys())
        with OUT_ROWS.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(allrows)

    summ = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "queried": len(log),
        "hits": sum(1 for r in log if r["result"] == "hit"),
        "miss_not_on_card": sum(1 for r in log if r["result"] == "miss_not_on_card"),
        "miss_no_card": sum(1 for r in log if r["result"] == "miss_no_card"),
        "no_page": sum(1 for r in log if r["result"] == "no_page"),
        "rows_written_this_run": len(rows),
        "rows_in_file": len(allrows),
        "fetch_stats": fetcher.stats,
        "queries": log,
    }
    REPORT.write_text(json.dumps(summ, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nqueried {summ['queried']}  hits {summ['hits']}  "
          f"not-on-card {summ['miss_not_on_card']}  no-card {summ['miss_no_card']}  "
          f"no-page {summ['no_page']}  rows {len(rows)}")
    print(f"wrote {OUT_ROWS}\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
