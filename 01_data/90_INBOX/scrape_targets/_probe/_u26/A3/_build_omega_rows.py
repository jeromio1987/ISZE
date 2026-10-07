# -*- coding: utf-8 -*-
"""A3 - u26_a3_omega_20261007 pass -> ledger-shaped rows, with the Mekonomen guard.

Guard (U26 instruction 2026-10-07): a row is accepted only if the number searched for
actually appears on the page, in any Isuzu spelling. Omega answers an unknown number
with its closest unrelated product (Isuzu 8981386950 once returned a Jeep Cherokee door
mirror cover). The presence test reads only the page's PRODUCT-SCOPED text (canonical
URL, JSON-LD blocks, WooCommerce details table), never the "You searched for X" banner,
because that banner repeats the query on every page and would pass every refusal.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[5]
PARSERS = ISZE / "04_tools" / "delegation" / "parsers"
sys.path.insert(0, str(PARSERS))

import ledger_schema
from ledger_schema import COLUMNS, normalise_pn, row_problems, apply_fx
import site_omega

LABEL = "u26_a3_omega_20261007"
PASS = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "passes" / LABEL
SEED = HERE / "seed_oe_pns.csv"
OUT = HERE
PAGES = OUT / "pages"

_LD_RE = re.compile(r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.S | re.I)
_CANON_RE = re.compile(r"<link[^>]+rel=[\"']canonical[\"'][^>]*href=[\"']([^\"']+)[\"']", re.I)
_ATTR_ROW_RE = re.compile(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", re.S)
_TOK_RE = re.compile(r"[0-9][0-9\s\-\./]{6,}[0-9]")
GENUINE_RELABEL = {"dealer": "genuine_grey"}


def scope_text(html):
    parts = []
    m = _CANON_RE.search(html)
    if m:
        parts.append(m.group(1))
    for m in _LD_RE.finditer(html):
        parts.append(m.group(1))
    for m in _ATTR_ROW_RE.finditer(html):
        parts.append(m.group(1) + " " + m.group(2))
    return " \n ".join(parts)


def pns_in_scope(html):
    blob = scope_text(html)
    out = set()
    for m in _TOK_RE.finditer(blob):
        pn = normalise_pn(m.group(0))
        if pn:
            out.add(pn)
    for w in re.split(r"[\s,;()]+", blob):
        pn = normalise_pn(w)
        if pn:
            out.add(pn)
    return out


def cache_file(url):
    host = re.sub(r"[^a-zA-Z0-9._-]", "_", urlparse(url).netloc)
    return PASS / "cache" / host / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".html")


def main():
    pns = []
    with SEED.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            v = (r.get("part_no") or "").strip()
            if re.fullmatch(r"\d{10}", v):
                pns.append(v)

    log = PASS / ("fetch_" + site_omega.SITE + ".jsonl")
    entries = {}
    for ln in log.read_text(encoding="utf-8").splitlines():
        j = json.loads(ln)
        entries[j["pn"]] = j

    PAGES.mkdir(parents=True, exist_ok=True)
    rows, tried, refused = [], [], []
    counts = Counter()
    queried = 0

    for pn in pns:
        j = entries.get(pn)
        if not j:
            counts["not_attempted"] += 1
            continue
        queried += 1
        url, date, outcome = j["url"], j["fetched_at"][:10], j["outcome"]

        if outcome not in ("ok", "cached"):
            counts["fetch_" + str(outcome) + "_" + str(j.get("status"))] += 1
            tried.append({"host": "omegaspareparts.com", "pn": pn, "url": url,
                          "robots": "allowed", "outcome": "fetch " + str(outcome), "rows": 0})
            continue

        cp = cache_file(url)
        if not cp.exists():
            counts["cache_missing"] += 1
            continue
        html = cp.read_text(encoding="utf-8", errors="replace")

        if pn not in pns_in_scope(html):
            counts["refused_number_absent"] += 1
            refused.append({"pn": pn, "url": url, "reason": "searched number not present in page product data", "page_file": ""})
            tried.append({"host": "omegaspareparts.com", "pn": pn, "url": url,
                          "robots": "allowed", "outcome": "guard refused: number absent", "rows": 0})
            continue

        try:
            parsed = site_omega.parse(html, source_url=url, observed_at=date)
        except Exception as e:
            counts["refused_parse_error"] += 1
            refused.append({"pn": pn, "url": url, "reason": "parse: " + str(e)[:160], "page_file": ""})
            tried.append({"host": "omegaspareparts.com", "pn": pn, "url": url,
                          "robots": "allowed", "outcome": "guard refused: parse error", "rows": 0})
            continue

        bad = [r for r in parsed if str(r.get("part_no")) != pn]
        if bad:
            counts["refused_other_number"] += 1
            ks = sorted({str(r.get("part_no")) for r in bad})
            refused.append({"pn": pn, "url": url, "reason": "parser keyed " + ",".join(ks) + " not " + pn, "page_file": ""})
            tried.append({"host": "omegaspareparts.com", "pn": pn, "url": url,
                          "robots": "allowed", "outcome": "guard refused: parser keyed other number", "rows": 0})
            continue

        page_name = "u26a3_omega_" + pn + "_" + date + ".html"
        (PAGES / page_name).write_text(html, encoding="utf-8")
        parsed, _fx = apply_fx(parsed)
        for r in parsed:
            r["price_type"] = GENUINE_RELABEL.get(r["price_type"], r["price_type"])
            r["obs_id"] = ledger_schema.issue_obs_id(r["source"], r["part_no"], r["observed_at"], r["price_type"])
            r["page_file"] = page_name
            r["crossref_grade"] = "corroborated"
            r["source_tried"] = url
        problems = [p for r in parsed for p in row_problems(r)]
        if problems:
            counts["schema_problems"] += 1
            print("SCHEMA", pn, problems[:3])
        counts["with_rows"] += 1
        counts["rows"] += len(parsed)
        rows.extend(parsed)
        tried.append({"host": "omegaspareparts.com", "pn": pn, "url": url,
                      "robots": "allowed", "outcome": "rows", "rows": len(parsed)})

    cols = COLUMNS + ["page_file", "crossref_grade", "source_tried"]
    with (OUT / "rows.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c) for c in cols})

    with (OUT / "tried.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["host", "pn", "url", "robots", "outcome", "rows"])
        w.writeheader()
        for t in tried:
            w.writerow(t)

    with (OUT / "_refused_guard.jsonl").open("w", encoding="utf-8") as fh:
        for r in refused:
            fh.write(json.dumps(r) + "\n")

    status = {
        "label": LABEL,
        "site": "omegaspareparts.com",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "numbers_queried": queried,
        "pages_fetched_or_cached": sum(1 for j in entries.values() if j["outcome"] in ("ok", "cached")),
        "numbers_with_rows": counts.get("with_rows", 0),
        "rows": counts.get("rows", 0),
        "numbers_empty": queried - counts.get("with_rows", 0),
        "guard_refused_total": len(refused),
        "counts": dict(counts),
        "notes": [
            "match_method stays exact_oem (searched Isuzu number is on the page and is the row part_no); crossref_grade is a separate column, MATCH_METHODS not widened.",
            "Genuine-Isuzu row relabelled dealer -> genuine_grey per the U26 brief; parser label recorded, not silent.",
        ],
    }
    (OUT / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
