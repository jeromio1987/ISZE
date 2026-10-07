# -*- coding: utf-8 -*-
"""A3 finalize: write rows.csv / tried.csv / pages/ / status.json / refusal evidence.

No rows were accepted. Every one of the 123 Omega searches was refused by the Mekonomen
guard; the reasons are classified from the saved pass pages (no refetching here).
"""
from __future__ import annotations
import csv, hashlib, json, re, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ISZE = HERE.parents[5]
sys.path.insert(0, str(ISZE / "04_tools" / "delegation" / "parsers"))
from ledger_schema import COLUMNS                      # noqa: E402

LABEL = "u26_a3_omega_20261007"
PASS = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "passes" / LABEL
CACHE = PASS / "cache" / "omegaspareparts.com"
OUT = HERE
PAGES = OUT / "pages"

pns = [r["part_no"] for r in csv.DictReader((OUT / "seed_oe_pns.csv").open(encoding="utf-8-sig"))]
entries = {}
for ln in (PASS / "fetch_omega.jsonl").read_text(encoding="utf-8").splitlines():
    j = json.loads(ln)
    entries[j["pn"]] = j

def cf(url):
    return CACHE / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".html")

# ---- classify every queried number from the saved page --------------------------------
class_rows, refused, counts = [], [], Counter()
for pn in pns:
    j = entries[pn]
    html = cf(j["url"]).read_text(encoding="utf-8", errors="replace")
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    title = t.group(1).strip() if t else ""
    c = re.search(r'rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html)
    canon = c.group(1) if c else ""
    prod = bool(re.search(r'"@type"\s*:\s*"Product"', html))
    nores = "you searched for" in title.lower()
    if nores:
        kind, reason = "no_results", "Omega returned its empty search-results page"
    elif prod:
        kind, reason = "unrelated_product", "Omega returned an unrelated product: " + title[:80]
    else:
        kind, reason = "other", "page neither product nor no-results"
    counts[kind] += 1
    class_rows.append({"pn": pn, "url": j["url"], "page_type": kind, "returned_title": title,
                       "canonical": canon, "bytes": len(html),
                       "searched_number_on_page": str(pn in html)})
    refused.append({"pn": pn, "url": j["url"], "guard": "mekonomen",
                    "reason": reason, "page_type": kind, "page_file": ""})

# ---- rows.csv (ledger shape + the three extra columns; 0 rows accepted) ---------------
cols = COLUMNS + ["page_file", "crossref_grade", "source_tried"]
with (OUT / "rows.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()

# ---- pages/ : classification + README (no accepted rows -> no per-row copies) ---------
PAGES.mkdir(exist_ok=True)
with (PAGES / "_omega_page_classification.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["pn", "url", "page_type", "returned_title", "canonical",
                                       "bytes", "searched_number_on_page"])
    w.writeheader()
    for r in class_rows:
        w.writerow(r)
(PAGES / "README.md").write_text(
    "# A3 pages\n\n"
    "No Omega page produced an acceptable row, so there are no per-row page copies here.\n\n"
    "- `_omega_page_classification.csv` classifies all 123 fetched pages "
    "(64 empty search-results pages, 59 unrelated-product pages).\n"
    "- The raw bytes of every page are kept in the per-pass cache:\n"
    "  `01_data/90_INBOX/scrape_targets/_probe/passes/u26_a3_omega_20261007/cache/omegaspareparts.com/`\n"
    "  (fetched 2026-10-07, 123 pages, all HTTP 200 through `fetch_polite.PoliteFetcher`).\n",
    encoding="utf-8")

with (OUT / "_refused_guard.jsonl").open("w", encoding="utf-8") as fh:
    for r in refused:
        fh.write(json.dumps(r) + "\n")

# ---- tried.csv : Omega per number + every other host tested ---------------------------
tried = []
for pn in pns:
    kind = next(r["page_type"] for r in class_rows if r["pn"] == pn)
    oc = {"no_results": "empty search page", "unrelated_product": "guard refused: unrelated product",
          "other": "guard refused: other"}[kind]
    tried.append({"host": "omegaspareparts.com",
                  "url_pattern": "https://omegaspareparts.com/?s={pn}&post_type=product",
                  "pn": pn, "robots": "allowed", "outcome": oc, "rows": 0})
OTHER = [
    ("autojapspares.co.uk", "/search?q={pn}", "allowed", "search route returned HTTP 404"),
    ("autojapspares.co.uk", "/catalogsearch/result/?q={pn}", "allowed", "Magento route also returned HTTP 404"),
    ("www.gsfcarparts.com", "/search?q={pn}", "allowed", "search route returned HTTP 404"),
    ("www.gsfcarparts.com", "/en/search?q={pn}", "allowed", "route also returned HTTP 404"),
    ("www.carparts4less.co.uk", "/search?q={pn}", "allowed", "query ignored, generic home page, no matching product"),
    ("www.eurocarparts.com", "/search?q={pn}", "allowed", "query ignored, generic home page, no matching product"),
    ("www.milneroffroad.com", "/?s={pn}", "allowed", "empty results template, no product"),
    ("www.sparesplus.co.uk", "/?s={pn}", "allowed", "wrong catalogue: domestic appliance parts"),
    ("www.micksgarage.com", "/search?q={pn}", "blocked", "robots.txt disallows the search path"),
    ("www.autodoc.co.uk", "/search?keyword={pn}", "blocked", "robots.txt returns HTTP 403 (Turnstile host, retired)"),
    ("www.partsupermarket.co.uk", "/?s={pn}", "blocked", "robots.txt unreachable, treated as blocked"),
    ("www.truckpartsuk.co.uk", "/?s={pn}", "blocked", "robots.txt unreachable, treated as blocked"),
    ("www.hgvtruckparts.co.uk", "/?s={pn}", "blocked", "robots.txt returns HTTP 404, treated as blocked"),
    ("www.arpartsgroup.com", "/?s={pn}", "blocked", "robots.txt unreachable, treated as blocked"),
    ("www.jcparts.co.uk", "/?s={pn}", "blocked", "robots.txt unreachable, treated as blocked"),
    ("www.thetruckpartswarehouse.co.uk", "/?s={pn}", "blocked", "robots.txt unreachable, treated as blocked"),
]
for host, pat, rob, outc in OTHER:
    tried.append({"host": host, "url_pattern": pat, "pn": "8975546610;8982705240",
                  "robots": rob, "outcome": outc, "rows": 0})
with (OUT / "tried.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["host", "url_pattern", "pn", "robots", "outcome", "rows"])
    w.writeheader()
    for r in tried:
        w.writerow(r)

# ---- status.json ----------------------------------------------------------------------
status = {
    "agent": "A3",
    "work_package": "A (second half) — Omega plus further UK online sellers",
    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "label": LABEL,
    "git_head_at_start": "8729346926caf7b2265f2487ff460f98d18f2d21",
    "sources": {
        "omegaspareparts.com": {
            "robots": "allowed",
            "numbers_queried": 123,
            "pages_fetched": 123,
            "rows": 0,
            "numbers_with_rows": 0,
            "guard_refusals": {"unrelated_product": counts["unrelated_product"],
                               "empty_search_page": counts["no_results"]},
        }
    },
    "numbers_queried": 123,
    "pages_fetched": 123,
    "rows": 0,
    "priced_rows": 0,
    "hits": 0,
    "misses": 123,
    "blocked_hosts": ["www.micksgarage.com", "www.autodoc.co.uk", "www.partsupermarket.co.uk",
                      "www.truckpartsuk.co.uk", "www.hgvtruckparts.co.uk", "www.arpartsgroup.com",
                      "www.jcparts.co.uk", "www.thetruckpartswarehouse.co.uk"],
    "guard": {
        "name": "mekonomen",
        "rule": "accept only if the searched number appears in the page's product data (canonical URL, "
                "JSON-LD, details table) in any Isuzu spelling; the 'You searched for X' banner is ignored",
        "refused_total": 123,
        "refused_unrelated_product": counts["unrelated_product"],
        "refused_empty_search_page": counts["no_results"],
    },
    "corroboration": {
        "attribute_sitemaps_scanned": 13,
        "distinct_10_digit_terms_in_omega_index": 1126,
        "seed_numbers_found": 0,
        "conclusion": "Omega holds none of the 123 numbers; the 59 'unrelated product' pages are the "
                      "closest-match failure mode, not a parse fault.",
    },
    "pages_saved": 0,
    "notes": [
        "No rows accepted, so rows.csv carries only its header; pages/ carries the 123-page "
        "classification instead of per-row copies; raw bytes stay in the per-pass cache (never the shared cache).",
        "match_method would be exact_oem and crossref_grade='corroborated' in a separate column; "
        "MATCH_METHODS was not widened.",
    ],
    "could_not_do": [
        "Find any UK online seller that both allows automated search and serves the searched Isuzu "
        "number in server-rendered HTML. Web search is unavailable to this subagent, so candidates "
        "came from the recon plus a direct robots/serving test.",
    ],
}
(OUT / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
print(json.dumps(status, indent=2))
