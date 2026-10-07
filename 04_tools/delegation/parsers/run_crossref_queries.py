# -*- coding: utf-8 -*-
"""Search KS International by the COMPETITOR's part number, not ours.

WHY THIS EXISTS
---------------
Measured 2026-10-01: the graded cross-reference holds 1,281 usable edges (286 competitor
numbers), and no live scraper had priced a single one. Every live price came in by our
own Isuzu number or by product type. The only script meant to search by competitor number,
`04_tools/autodoc_scraper/crossref_search_runner.py`, reads a file that no longer exists
and targets two retired sites. This replaces it, on the one parts site still answering.

U26 (2026-10-07) — per-agent seed and per-agent output
------------------------------------------------------
Work package A searched a fixed list of competitor numbers (the 153 Eucon UK/A numbers of
the U26 worklist) rather than every number in the shared graph, and it must not write into
the shared `04_tools/price_ledger/KS_CROSSREF_ROWS.csv` or the shared
`_crossref_query_run.json` while eight other agents are running. Two changes, nothing else:

  * `--seed-csv <file>`  — one competitor number per line (header or headerless). When
    given, the run queries exactly those numbers, in file order, instead of the shared
    graded graph.
  * `--out-rows`, `--out-report`, `--pages-dir`, `--tried-csv` — the two outputs and the
    saved page copies go where the caller says. With `--seed-csv` and no explicit paths,
    they default into the caller's own `_u26/<ID>/` folder.

The acceptance rule, the fetch discipline and the data boundary below are unchanged.

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

KNOWN ISSUE (U26) — `crossref_candidate` / `crossref_corroborated` are NOT ledger
`match_method` values, so the ledger schema would reject a row carrying them. This runner
does NOT widen the allowed set. It keeps `match_method="crossref"` and carries the grade in
the separate `crossref_grade` column (`candidate` | `corroborated`), which is written to
the caller's own row CSV.

DATA BOUNDARY
-------------
The competitor numbers come from Eucon files. Using them to drive a scrape was Jerome's
explicit go of 2026-09-24. Only the competitor number goes out, as a KS search term. No
Eucon row goes to DeepSeek or any other service; this script calls no model.

Discipline: every fetch goes through `fetch_polite.PoliteFetcher` (consent check,
>= 2.2 s per host, disk cache).

Usage
-----
    python run_crossref_queries.py                       # plan only, shared-graph seed
    python run_crossref_queries.py --online --limit 5
    # U26 work package A (writes into _u26/A1/):
    python run_crossref_queries.py --seed-csv <...\\_u26\\A1\\seed_competitor_pns.csv> ^
        --online --limit 999
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse

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
from ledger_schema import COLUMNS                                        # noqa: E402
import site_ks                                                            # noqa: E402

GRADED = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
OUT_ROWS = ISZE / "04_tools" / "price_ledger" / "KS_CROSSREF_ROWS.csv"
REPORT = HERE / "_crossref_query_run.json"
U26_A1 = (ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "A1")
KS_TPL = "https://www.ks-international.com/catalogsearch/result/?q={q}"
USABLE = {"confirmed", "likely"}
HOST = "www.ks-international.com"
EXTRA_COLS = ["page_file", "crossref_grade", "source_tried"]


def squash(s: str) -> str:
    return re.sub(r"[\s\-./]", "", str(s or "")).upper()


def _grade_of(tiers) -> str:
    """U26 grade: corroborated when a confirmed/likely edge links the number, else candidate."""
    return "corroborated" if (set(tiers) & USABLE) else "candidate"


def _edges_by_key() -> dict:
    import pandas as pd
    d = pd.read_csv(GRADED, dtype=str)
    d = d[d["competitor_pn"].notna()]
    return {key: g for key, g in d.groupby(d["competitor_pn"].map(squash)) if key}


def seed_from_graph() -> list[dict]:
    """One entry per distinct competitor number: the number, its brands, our parts."""
    out = []
    for key, g in _edges_by_key().items():
        if len(key) < 4:                        # too short to be safely matched on a card
            continue
        out.append({
            "cpn_key": key,
            "query": g["competitor_pn"].mode().iat[0].strip(),
            "brands": sorted(set(g["competitor_brand"].dropna())),
            "part_nos": sorted(set(g["part_no"].dropna())),
            "tiers": sorted(set(g["tier"])),
            "linked": True,
        })
    return sorted(out, key=lambda e: e["cpn_key"])


def seed_from_csv(path: Path) -> list[dict]:
    """One entry per competitor number in the caller's own file, in file order.

    A number with no graded edge is still queried (the file is the worklist), but has no
    `part_nos`, so a card that carries it cannot become a price row — it is recorded as a
    hit with no linked part and counted in the report.
    """
    by_key = _edges_by_key()
    text = path.read_text(encoding="utf-8-sig")
    lines = [ln.strip().strip('"') for ln in text.splitlines()]
    nums = [ln for ln in lines if ln and ln.lower() not in ("part_no", "competitor_pn")]
    out, seen = [], set()
    for raw in nums:
        key = squash(raw)
        if not key or key in seen:
            continue
        seen.add(key)
        g = by_key.get(key)
        out.append({
            "cpn_key": key,
            "query": raw,
            "brands": sorted(set(g["competitor_brand"].dropna())) if g is not None else [],
            "part_nos": sorted(set(g["part_no"].dropna())) if g is not None else [],
            "tiers": sorted(set(g["tier"])) if g is not None else [],
            "linked": g is not None,
        })
    return out


def card_carries(card, key: str) -> bool:
    return key in squash(card.get_text(" ", strip=True))


def _save_page(fetcher: PoliteFetcher, url: str, pages_dir: Path, name: str) -> str:
    src = fetcher.cache_path(url)
    pages_dir.mkdir(parents=True, exist_ok=True)
    dst = pages_dir / name
    if src.exists():
        dst.write_bytes(src.read_bytes())
    return name if dst.exists() else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5, help="competitor numbers to query (default 5)")
    ap.add_argument("--online", action="store_true", help="actually fetch")
    ap.add_argument("--seed-csv", help="query these competitor numbers (one per line), in order")
    ap.add_argument("--out-rows", help="accepted rows CSV (default: shared, or _u26/<id> with --seed-csv)")
    ap.add_argument("--out-report", help="run report JSON (default: shared, or _u26/<id> with --seed-csv)")
    ap.add_argument("--pages-dir", help="folder for one saved page per row")
    ap.add_argument("--tried-csv", help="every host/path tried with robots verdict and outcome")
    a = ap.parse_args()

    if a.seed_csv:
        entries = seed_from_csv(Path(a.seed_csv))
        out_rows = Path(a.out_rows) if a.out_rows else U26_A1 / "rows_competitor.csv"
        out_report = Path(a.out_report) if a.out_report else U26_A1 / "crossref_run_competitor.json"
        pages_dir = Path(a.pages_dir) if a.pages_dir else U26_A1 / "pages"
        tried_csv = Path(a.tried_csv) if a.tried_csv else U26_A1 / "tried_competitor.csv"
        source_tried = "KS International /catalogsearch/result/ (competitor number pass)"
    else:
        entries = seed_from_graph()
        out_rows = Path(a.out_rows) if a.out_rows else OUT_ROWS
        out_report = Path(a.out_report) if a.out_report else REPORT
        pages_dir = Path(a.pages_dir) if a.pages_dir else None
        tried_csv = Path(a.tried_csv) if a.tried_csv else None
        source_tried = "KS International /catalogsearch/result/ (shared-graph seed)"

    todo = entries[:a.limit] if a.limit else entries
    linked = sum(1 for e in todo if e["linked"])
    print(f"competitor numbers seeded : {len(entries)}")
    print(f"this run                  : {len(todo)} KS searches, >= {MIN_INTERVAL}s apart")
    print(f"with a graded edge        : {linked} of {len(todo)}")
    print(f"mode                      : {'LIVE FETCH' if a.online else 'plan only (use --online)'}")
    print(f"rows -> {out_rows}")
    if not a.online:
        for e in todo:
            print(f"   {e['query']:<22} {', '.join(e['brands'])[:36]:<36} "
                  f"-> {', '.join(e['part_nos']) or '(no linked part)'}")
        return 0

    fetcher = PoliteFetcher()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log, rows, tried = [], [], []
    robots_verdict = "allowed"
    for e in todo:
        url = KS_TPL.format(q=quote_plus(e["query"]))
        rec = {"query": e["query"], "url": url, "part_nos": e["part_nos"], "result": None,
               "cards": 0, "accepted": 0, "linked": e["linked"]}
        try:
            html = fetcher.get(url)
        except ConsentRefused:
            rec["result"] = "consent_refused"
            log.append(rec)
            tried.append({"host": HOST, "url_pattern": url, "robots_verdict": "blocked",
                          "outcome": "consent_refused"})
            print("   consent refused — stopping")
            break
        if not html:
            rec["result"] = "no_page"
            log.append(rec)
            tried.append({"host": HOST, "url_pattern": url, "robots_verdict": robots_verdict,
                          "outcome": "no_page"})
            print(f"   {e['query']:<22} no page")
            continue
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(site_ks.CARD_SELECTOR)
        rec["cards"] = len(cards)
        hits = [c for c in cards if card_carries(c, e["cpn_key"])]
        for c in hits:
            r = site_ks._card_row(c, query_pn=None, source_url=url, observed_at=today)
            if not r:
                continue
            rec["accepted"] += 1
            tag = f"ks_competitor_{e['cpn_key']}_{hashlib.sha256(url.encode()).hexdigest()[:8]}.html"
            page_file = _save_page(fetcher, url, pages_dir, tag) if pages_dir else ""
            for pn in (e["part_nos"] or [None]):
                rr = dict(r)
                extra = f"found by competitor number {e['query']} (graded {'/'.join(e['tiers']) or 'no edge'})"
                rr.update(
                    part_no=pn, match_method="crossref",
                    competitor_brand="|".join(e["brands"]) or r.get("competitor_brand"),
                    competitor_pn=e["query"],
                    description=f"{r['description']} — {extra}",
                    loader="ks_crossref", vintage=f"KS International {today}",
                    page_file=page_file, crossref_grade=_grade_of(e["tiers"]),
                    source_tried=source_tried,
                )
                rows.append(rr)
        rec["result"] = "hit" if rec["accepted"] else (
            "miss_no_card" if not cards else "miss_not_on_card")
        log.append(rec)
        tried.append({"host": HOST, "url_pattern": url, "robots_verdict": robots_verdict,
                      "outcome": rec["result"]})
        print(f"   {e['query']:<22} cards={len(cards):<3} accepted={rec['accepted']}  {rec['result']}")

    # Merge with earlier runs of THIS file: keep previous rows for queries not re-run.
    prev = []
    if out_rows.exists():
        with out_rows.open(encoding="utf-8", newline="") as fh:
            prev = list(csv.DictReader(fh))
    done_q = {e["query"] for e in todo}
    keep = [p for p in prev if p.get("competitor_pn") not in done_q]
    allrows = keep + rows
    if allrows:
        cols = COLUMNS + [c for c in EXTRA_COLS if c not in COLUMNS]
        out_rows.parent.mkdir(parents=True, exist_ok=True)
        with out_rows.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(allrows)

    if tried_csv is not None:
        tried_csv.parent.mkdir(parents=True, exist_ok=True)
        with tried_csv.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["host", "url_pattern", "robots_verdict", "outcome"])
            w.writeheader()
            w.writerows(tried)

    summ = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed_csv": a.seed_csv,
        "queried": len(log),
        "hits": sum(1 for r in log if r["result"] == "hit"),
        "miss_not_on_card": sum(1 for r in log if r["result"] == "miss_not_on_card"),
        "miss_no_card": sum(1 for r in log if r["result"] == "miss_no_card"),
        "no_page": sum(1 for r in log if r["result"] == "no_page"),
        "consent_refused": sum(1 for r in log if r["result"] == "consent_refused"),
        "numbers_queried": len(log),
        "numbers_with_rows": len({r["query"] for r in log if r["accepted"]}),
        "rows_written_this_run": len(rows),
        "rows_in_file": len(allrows),
        "fetch_stats": fetcher.stats,
        "known_issue": ("match_method kept as 'crossref' (schema-valid); the U26 grade "
                        "(candidate/corroborated) travels in the separate crossref_grade column. "
                        "MATCH_METHODS was not widened."),
        "queries": log,
    }
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(summ, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nqueried {summ['queried']}  hits {summ['hits']}  "
          f"not-on-card {summ['miss_not_on_card']}  no-card {summ['miss_no_card']}  "
          f"no-page {summ['no_page']}  rows {len(rows)}")
    print(f"wrote {out_rows}\nwrote {out_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
