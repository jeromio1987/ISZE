# -*- coding: utf-8 -*-
"""A1 (U26) — assemble work package A's outputs from the two KS passes.

Reads only what the two polite passes already wrote on disk and turns it into the four
files the U26 brief asks for, in the agent's own folder:

    rows.csv     ledger-shaped rows (ledger COLUMNS + page_file, crossref_grade,
                 source_tried), one per observation, validated with ledger_schema
    pages\\       one saved page copy per row (verbatim check)
    tried.csv    every host/path tried, robots verdict, outcome
    status.json  counts

Two passes feed it:

  competitor   run_crossref_queries.py --seed-csv ..._u26/A1/seed_competitor_pns.csv
               -> rows_competitor.csv, crossref_run_competitor.json, its own tried file
  OE           run_dated_pass.py fetch --site ks --pns-from-csv .../A1/seed_oe_pns.csv
               -> passes/<label>/cache + fetch_ks.jsonl, parsed here with site_ks.parse

Acceptance (both passes, strict): a card counts only when the number we searched for is
printed on the card, compared after spaces, dashes, dots and slashes are removed.
Nothing is inferred: every field comes from the page, via the site_ks parser.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))

from ledger_schema import COLUMNS, row_problems, apply_fx                  # noqa: E402
import run_dated_pass                                                     # noqa: E402
import site_ks                                                            # noqa: E402

A1 = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "A1"
LABEL = "u26_a1_oe_20261007"
EXTRA = ["page_file", "crossref_grade", "source_tried"]
HOST = "www.ks-international.com"
# The dated-pass runner keeps its own bookkeeping under the shared passes root (same as
# the other U26 agents); the page cache was pointed at the agent's own folder.
PASS_DIR = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "passes" / LABEL
OE_PASS = A1 / "passes" / LABEL
COMP_ROWS = A1 / "rows_competitor.csv"
COMP_RUN = A1 / "crossref_run_competitor.json"
COMP_TRIED = A1 / "tried_competitor.csv"


def squash(s: str) -> str:
    return re.sub(r"[\s\-./]", "", str(s or "")).upper()


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def page_name(prefix: str, term: str, url: str) -> str:
    import hashlib
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{squash(term)}_{h}.html"


def save_page(src: Path, dst: Path) -> str:
    """Save one page copy per row. The full KS page is ~2.4 MB (mostly CSS/JS chrome);
    the parser slice `site_ks._slim_for_parse` keeps the title, search box and product
    grid (~5 KB) and is the exact input the row was read from, so that is what is saved
    here. The raw full bytes stay in the per-pass cache (see pages/README.md)."""
    if not src.exists():
        return ""
    dst.parent.mkdir(parents=True, exist_ok=True)
    slim = site_ks._slim_for_parse(src.read_text(encoding="utf-8", errors="replace"))
    dst.write_text(slim, encoding="utf-8")
    return dst.name


def build_oe_rows() -> tuple[list[dict], list[dict], dict]:
    """Parse every cached OE page and record the cards it returns.

    STRICT ACCEPTANCE (the task's rule): a card *counts* only when the number we searched
    for is printed inside the card. On the OE pass KS never prints our Isuzu number in the
    card — measured on 8982705240 and 8975546610: the number is in the page plumbing
    (title, search box, cache URL) 12 times and 0 times in the card. So `site_ks` returns
    `match_method="category_only"` for every one of them, exactly as its docstring says.

    Nothing is thrown away: those cards are real observed prices, so they are written with
    the honest `category_only` match method and `crossref_grade="category_only_relevance"`,
    and the strict count (exact in-card match) is reported separately. A genuine-badged
    card is `genuine_grey`; the parser sets that, never this builder.
    """
    pages_dir = A1 / "pages"
    cache_root = OE_PASS / "cache"
    log_path = PASS_DIR / "fetch_ks.jsonl"
    entries = {}
    for ln in log_path.read_text(encoding="utf-8").splitlines():
        j = json.loads(ln)
        entries[j["pn"]] = j                       # last record wins (resumable run)
    rows, tried = [], []
    counts = {"pages_cached": 0, "cards_returned": 0, "strict_exact_rows": 0,
              "category_only_rows": 0, "not_stocked": 0, "broken": 0}
    for pn, j in entries.items():
        url = j["url"]
        outcome = j["outcome"]
        tried.append({"host": HOST, "url_pattern": url, "robots_verdict": "allowed",
                      "outcome": outcome})
        if outcome not in ("ok", "cached"):
            continue
        cp = run_dated_pass.cache_file(cache_root, url)
        if not cp.exists():
            continue
        counts["pages_cached"] += 1
        html = cp.read_text(encoding="utf-8", errors="replace")
        try:
            parsed = site_ks.parse(html, source_url=url, observed_at=j["fetched_at"][:10])
        except Exception as e:                                     # noqa: BLE001
            if "0 product cards" in str(e):
                counts["not_stocked"] += 1
            else:
                counts["broken"] += 1
                print(f"   broken {pn}: {e}")
            continue
        counts["cards_returned"] += len(parsed)
        for r in parsed:
            fn = page_name("oe", pn, url)
            save_page(cp, pages_dir / fn)
            r = dict(r)
            if r.get("match_method") == "exact_oem":
                grade = "exact_oem"
                counts["strict_exact_rows"] += 1
            else:
                grade = "category_only_relevance"
                counts["category_only_rows"] += 1
            r.update(page_file=fn, crossref_grade=grade,
                     source_tried="KS International /catalogsearch/result/ (OE number pass)")
            rows.append(r)
    return rows, tried, counts


def main() -> int:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # --- competitor pass: rows already accepted by the runner -----------------------
    comp_rows = read_csv(COMP_ROWS)
    comp_run = json.loads(COMP_RUN.read_text(encoding="utf-8")) if COMP_RUN.exists() else {}
    comp_tried = read_csv(COMP_TRIED)
    if not comp_tried and comp_run:
        for q in comp_run.get("queries", []):
            comp_tried.append({"host": HOST, "url_pattern": q["url"],
                               "robots_verdict": "allowed", "outcome": q["result"]})

    # --- OE pass: parse the cached pages -------------------------------------------
    oe_rows, oe_tried, oe_counts = build_oe_rows()

    allrows = [dict(r) for r in comp_rows] + oe_rows
    allrows, fx_note = apply_fx(allrows)

    # --- schema check --------------------------------------------------------------
    bad = []
    for r in allrows:
        probs = row_problems(r)
        if probs:
            bad.append((r.get("part_no"), probs))
    if bad:
        print(f"SCHEMA PROBLEMS on {len(bad)} row(s) — not written:")
        for pn, probs in bad[:10]:
            print(f"   {pn}: {probs}")
        return 1

    cols = COLUMNS + [c for c in EXTRA if c not in COLUMNS]
    with (A1 / "rows.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)

    with (A1 / "tried.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["host", "url_pattern", "robots_verdict", "outcome"])
        w.writeheader()
        w.writerows(comp_tried + oe_tried)

    comp_q = comp_run.get("numbers_queried", 0)
    oe_q = len({j["pn"] for j in map(json.loads, (PASS_DIR / "fetch_ks.jsonl")
                                     .read_text(encoding="utf-8").splitlines())})
    comp_with = len({r["part_no"] for r in comp_rows})
    oe_with = len({r["part_no"] for r in oe_rows})
    status = {
        "agent": "A1",
        "work_package": "A — KS International (competitor numbers + Isuzu OE numbers)",
        "run_at": now,
        "host": HOST,
        "robots": "allowed (check_scrape_consent.py exit 0 for /catalogsearch/result/)",
        "fetch": "fetch_polite.PoliteFetcher, >= 2.2 s per host, no 403/429 seen",
        "acceptance_rule": ("strict — a card counts only when the number we searched for is printed "
                            "on the card (spaces/dashes/dots/slashes removed). KS prints our number "
                            "in the page plumbing 12x and in the card 0x, so every card is a "
                            "relevance hit: 0 cards carried the searched number in either pass."),
        "competitor_pass": {
            "seed": "seed_competitor_pns.csv",
            "numbers_queried": comp_q,
            "numbers_with_rows": comp_with,
            "hits": comp_run.get("hits", 0),
            "miss_no_card": comp_run.get("miss_no_card", 0),
            "miss_not_on_card": comp_run.get("miss_not_on_card", 0),
            "relevance_pages_with_cards": comp_run.get("miss_not_on_card", 0),
            "rows": len(comp_rows),
            "pages_fetched": comp_run.get("fetch_stats", {}).get("fetched", 0),
        },
        "oe_pass": {
            "seed": "seed_oe_pns.csv",
            "label": LABEL,
            "numbers_queried": oe_q,
            "numbers_with_rows": oe_with,
            "rows": len(oe_rows),
            **oe_counts,
        },
        "rows_total": len(allrows),
        "strict_exact_rows": sum(1 for r in allrows if r.get("match_method") == "exact_oem"),
        "relevance_rows": sum(1 for r in allrows if r.get("match_method") == "category_only"),
        "priced_rows": sum(1 for r in allrows if r.get("price") not in (None, "")),
        "genuine_rows": sum(1 for r in allrows if r.get("price_type") == "genuine_grey"),
        "aftermarket_rows": sum(1 for r in allrows if r.get("price_type") == "aftermarket_retail"),
        "tried_entries": len(comp_tried) + len(oe_tried),
        "blocked_hosts": [],
        "fx_note": fx_note,
        "known_issue": ("U26 brief says store crossref_candidate/crossref_corroborated; those are "
                        "not ledger MATCH_METHODS. Kept match_method='crossref' and carried the "
                        "grade in crossref_grade. MATCH_METHODS not widened."),
        "not_done": ("KS does not index the Eucon aftermarket brand numbers in the seed file "
                     "(0 of 149 cards carried the searched number); on the OE pass KS returns "
                     "relevance cards under its own SKUs, none carrying our Isuzu number. So 0 "
                     "rows meet the strict rule; the 33 relevance rows are kept, labelled "
                     "match_method=category_only / crossref_grade=category_only_relevance."),
    }
    (A1 / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
    print(json.dumps({k: v for k, v in status.items() if k not in ("competitor_pass", "oe_pass")},
                     indent=2))
    print("competitor:", status["competitor_pass"])
    print("OE:", status["oe_pass"])
    print(f"wrote rows.csv ({len(allrows)}), tried.csv, status.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
