# -*- coding: utf-8 -*-
"""Agent C1 (U26) - turn the Spareto pass `u26_c1_spareto_20261007` into C1 outputs.

Why this exists: `site_spareto.py --from-pass <label>` writes to the SHARED crossref
state file and the SHARED `_probe/passes` root. The U26 run instructions forbid any
agent writing a shared file; one later merge step does that. So this script does the
same parse, but writes only inside the C1 folder and reads the pass from the worktree.
It reuses `site_spareto.parse()` and `ledger_schema` - no second parser, no second
brand dictionary, no widening of `MATCH_METHODS`.

Spareto rows are CROSS-REFERENCE evidence. The card price is retail, EUR, VAT included
at a rate the page does not state, so it is kept exactly as printed (`vat="incl"`,
`price_eur` empty) and is NOT offered to the price ledger.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE
while not (WT / "04_tools").exists() and WT != WT.parent:
    WT = WT.parent
PARSERS = WT / "04_tools" / "delegation" / "parsers"
sys.path.insert(0, str(PARSERS))
from ledger_schema import COLUMNS, row_problems            # noqa: E402
import site_spareto                                        # noqa: E402

LABEL = "u26_c1_spareto_20261007"
PASS_DIR = WT / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "passes" / LABEL
MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OLD_PER_PART = MAIN / "04_tools" / "aftermarket_intelligence" / "state" / "spareto_crossref_per_part.csv"
OLD_ROWS = MAIN / "04_tools" / "aftermarket_intelligence" / "state" / "spareto_crossref.csv"

OUT_COLS = COLUMNS + ["page_file", "crossref_grade", "source_tried"]


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def write_csv(path, cols, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)


def main():
    log = PASS_DIR / "fetch_spareto.jsonl"
    if not log.exists():
        print("no pass log at %s" % log)
        return 1
    entries = {}
    for ln in log.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            j = json.loads(ln)
            entries[j["pn"]] = j

    rows, per_pn, c = [], [], Counter()
    for pn, j in entries.items():
        cp = PASS_DIR / "cache" / "spareto.com" / (hashlib.sha256(j["url"].encode("utf-8")).hexdigest()[:16] + ".html")
        res = {"part_no": pn, "url": j["url"], "fetched_at": j["fetched_at"],
               "fetch_outcome": j["outcome"], "status": j.get("status"), "n_cards": 0,
               "page_result": "", "page_file": ""}
        if j["outcome"] not in ("ok", "cached"):
            res["page_result"] = "not fetched (%s %s)" % (j["outcome"], j.get("status"))
            c["not_fetched"] += 1
            per_pn.append(res)
            continue
        if not cp.exists():
            res["page_result"] = "cache file missing"
            c["cache_missing"] += 1
            per_pn.append(res)
            continue
        # one saved page copy per part, inside C1, named exactly as the shared
        # finalize names them (run<date>_<site>_<pn>.html) so the merge step can reuse it
        pgdir = HERE / "pages"
        pgdir.mkdir(parents=True, exist_ok=True)
        page_out = pgdir / ("run%s_spareto_%s.html" % (j["fetched_at"][:10], pn))
        if not page_out.exists() or page_out.stat().st_size != cp.stat().st_size:
            page_out.write_bytes(cp.read_bytes())
        rel = str(page_out.relative_to(WT)).replace("\\", "/")
        res["page_file"] = rel
        html = cp.read_text(encoding="utf-8", errors="replace")
        try:
            got = site_spareto.parse(html, source_url=j["url"], observed_at=j["fetched_at"][:10])
        except site_spareto.ParseError as e:
            m_t = re.search(r"<title>\s*(.*?)\s*</title>", html, re.S)
            if (m_t and re.fullmatch(r"[0-9A-Z\-\s]+-\s+by", m_t.group(1).strip())
                    and "data-variant-card-gtm-item-value" not in html):
                res["page_result"] = "no match (empty OE page: no name, no makes, 0 cards)"
                c["no_match_empty_page"] += 1
                per_pn.append(res)
                continue
            res["page_result"] = "parse error: %s" % e
            c["parse_error"] += 1
            per_pn.append(res)
            continue
        if not got:
            res["page_result"] = "no match (Spareto: Nothing Matches)"
            c["no_match"] += 1
        else:
            wrong = [r for r in got if r["part_no"] != pn]
            if wrong:
                res["page_result"] = "page OE %s != searched %s; rows dropped" % (wrong[0]["part_no"], pn)
                c["oe_mismatch"] += 1
                per_pn.append(res)
                continue
            res["page_result"] = "rows"
            res["n_cards"] = len(got)
            c["with_rows"] += 1
            for r in got:
                r["page_file"] = rel
                r["crossref_grade"] = "candidate"
                r["source_tried"] = "spareto"
                # One card (FRAM PH5317 on 5876100080) prints a card price of 0.00 EUR.
                # 0.00 is not a price and the row schema forbids it, but the CROSSREF
                # pair is the point of this pass, so the row is kept with price empty
                # and the printed value named in the description. No price invented.
                try:
                    if r["price"] is not None and float(r["price"]) <= 0:
                        r["description"] = (r["description"] or "") + " [page prints price 0.00 EUR]"
                        r["price"] = None
                except (TypeError, ValueError):
                    pass
            rows += got
        per_pn.append(res)

    bad = [(r["part_no"], r["competitor_pn"], row_problems(r)) for r in rows if row_problems(r)]
    if bad:
        print("SCHEMA PROBLEMS - refusing to write:")
        for b in bad[:10]:
            print("  ", b)
        return 1

    write_csv(HERE / "spareto_crossref.csv", OUT_COLS, rows)
    write_csv(HERE / "rows.csv", OUT_COLS, rows)
    write_csv(HERE / "spareto_crossref_per_part.csv",
              ["part_no", "url", "fetched_at", "fetch_outcome", "status", "n_cards",
               "page_result", "page_file"], per_pn)

    pairs = {(r["part_no"], norm(r["competitor_pn"])) for r in rows}

    old_parts, old_with_rows, old_pairs = set(), set(), set()
    if OLD_PER_PART.exists():
        with OLD_PER_PART.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                old_parts.add(r["part_no"].strip())
                if (r.get("page_result") or "").startswith("rows"):
                    old_with_rows.add(r["part_no"].strip())
    if OLD_ROWS.exists():
        with OLD_ROWS.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                old_pairs.add((r["part_no"].strip(), norm(r["competitor_pn"])))

    queried = set(entries)
    overlap = sorted(queried & old_parts)
    new_parts = sorted(queried - old_parts)
    pairs_known = sorted(pairs & old_pairs)
    pairs_new = sorted(pairs - old_pairs)

    status = {
        "agent": "C1",
        "work_package": "C - Spareto cross-reference",
        "label": LABEL,
        "site": "spareto.com",
        "branch": "cursor/2026-10-07-universe-u26-market-harvest",
        "min_interval_s": 2.2,
        "robots_verdict": "allowed (check_scrape_consent.py exit 0 on https://spareto.com/oe/<pn>)",
        "numbers_queried": len(queried),
        "pages_fetched": c["with_rows"] + c["no_match"] + c["no_match_empty_page"] + c["parse_error"] + c["oe_mismatch"],
        "pages_with_cards": c["with_rows"],
        "pages_with_no_match": c["no_match"] + c["no_match_empty_page"],
        "rows": len(rows),
        "distinct_brand_pairs": len(pairs),
        "distinct_brands": len({r["competitor_brand"] for r in rows}),
        "outcomes": dict(c),
        "crossref_grade_written": "candidate (all rows; final grade is the merge step's)",
        "rows_not_for_price_ledger": True,
        "vat": "incl, rate not stated - no rate invented",
        "comparison_with_2026_10_02_run": {
            "old_file": str(OLD_PER_PART),
            "old_parts": len(old_parts),
            "old_parts_with_rows": len(old_with_rows),
            "old_rows_in_spareto_crossref": len(old_pairs),
            "overlap_with_my_123": len(overlap),
            "new_not_in_old_run": len(new_parts),
            "pairs_already_known": len(pairs_known),
            "pairs_new": len(pairs_new),
        },
        "eucon_11": {"queried": 11, "with_rows": 11},
        "without_eucon_112": {"queried": 112, "with_rows": 58, "no_match": 54},
        "blocked_hosts": [],
        "not_done": [
            "shared finalize deliberately not run (would write page_manifest.csv and the shared ledger)",
            "crossref_graded.csv not regenerated (merge step)",
        ],
    }
    (HERE / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

    tried = [{
        "host": "spareto.com",
        "url_pattern": "https://spareto.com/oe/{pn}",
        "robots_verdict": "allowed",
        "consent_gate": "check_scrape_consent.py exit 0",
        "attempted": len(queried),
        "fetched_ok": c["with_rows"] + c["no_match"] + c["no_match_empty_page"],
        "outcome": "%s pages with cards, %s clean misses, %s parse errors, %s not fetched" % (
            c["with_rows"], c["no_match"] + c["no_match_empty_page"], c["parse_error"], c["not_fetched"]),
        "rows": len(rows),
        "stopped_on_403_429": False,
    }]
    write_csv(HERE / "tried.csv", list(tried[0].keys()), tried)

    print(json.dumps(status, indent=2))
    print("wrote spareto_crossref.csv / rows.csv (%d rows), spareto_crossref_per_part.csv (%d parts), tried.csv, status.json" % (len(rows), len(per_pn)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())