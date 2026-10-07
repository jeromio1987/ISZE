# -*- coding: utf-8 -*-
"""A2 harvester - the two UK sellers that are not KS, plus a bounded TMC category walk.

Work package A, agent A2 of U26. Owns T&M Commercials and Tranzparts.

Route, as measured before this script was written (see the two site_*.py docstrings):
  * Tranzparts - search?q=<n>&type=product answers and returns server-rendered cards;
    the card links to a product page whose JSON-LD holds the price and whose
    cross-reference list holds the Isuzu numbers. So: search -> follow card -> parse.
  * T&M Commercials - every search route (/?s=, wp-json store/v2, sitemaps, /page/2/)
    returns HTTP 504. The category tree answers. So: walk a bounded set of leaf
    categories and read the cards, which carry the Isuzu number as the sku.

Discipline: every fetch through fetch_polite.PoliteFetcher (consent gate first,
>= 2.2 s per host, disk cache). Stop on the second hard block on a host.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[5]
PARSERS = WT / "04_tools" / "delegation" / "parsers"
sys.path.insert(0, str(PARSERS))
for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from fetch_polite import PoliteFetcher, ConsentRefused, MIN_INTERVAL
from ledger_schema import COLUMNS, apply_fx
import site_tranzparts
import site_tmc

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
EXTRA_COLS = ["page_file", "crossref_grade", "source_tried"]

TRANZ = "tranzparts.co.uk"
TMC = "www.tmcgroup.co.uk"
TRANZ_SEARCH = "https://tranzparts.co.uk/search?q={q}&type=product"

TMC_CATEGORIES = [
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-125-euro-6/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-125-euro-6/brakes/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-125-euro-6/service-items/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-120-2010/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-150-euro6-2013/braking/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/grafter-n35-150-euro6-2013/filtersandserviceitems-grafter-n35-150-euro6-2013/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-150-urban-2014/braking-n75-150-urban-2014/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-150-urban-2014/filtersandserviceitems-n75-150-urban-2014/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-automatic-11-2013/braking-n75-190-automatic-11-2013/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-automatic-11-2013/filtersandserviceitems-n75-190-automatic-11-2013/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-automatic-2008/braking-november-2013/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-automatic-2008/filters-and-service-items/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-manual-2013/braking-n75-190-manual-2013/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-manual-2013/filtersandserviceitems/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-manual-2008/braking-november-2013-n75-190-manual-2008/",
    "https://www.tmcgroup.co.uk/product-category/isuzu-trucks/n75-190-manual-2008/filters-and-service-items-november-2013-n75-190-manual-2008/",
]

TRIED = []

# Other UK sellers checked from the recon list and from a short candidate sweep, BEFORE any
# fetch. One entry each, so the "what was tried and failed" record is complete and nobody
# retries them blindly. Verdicts are the consent gate's own output, 2026-10-07.
OTHER_UK_HOSTS = [
    ("www.eurocarparts.com", "/search?query=<pn>", "blocked",
     "robots.txt disallows the search path; also in the 2026-10-01 recon as blocked"),
    ("www.carparts4less.co.uk", "/search?query=<pn>", "blocked",
     "robots.txt disallows the search path"),
    ("www.gsfcarparts.com", "/search?q=<pn>", "allowed",
     "robots allows, but the search route returns HTTP 404 - no usable query URL found"),
    ("www.milneroffroad.com", "/?s=<pn>", "allowed",
     "robots allows and /?s= renders a real search page, but it returns no product cards "
     "(0 match) - no Isuzu coverage"),
    ("www.ukpartsdirect.com", "/catalogsearch/result/?q=<pn>", "allowed",
     "robots allows and the Magento route works, but it returns 17 product cards with no "
     "price and a no-results block - nothing readable"),
    ("www.japanpartsuk.co.uk", "/search?q=<pn>", "unknown",
     "robots.txt unreachable - UNKNOWN means stop"),
    ("www.truckpartsonline.co.uk", "/search?q=<pn>", "unknown",
     "robots.txt unreachable - UNKNOWN means stop"),
    ("www.buycarparts.co.uk", "/search?keyword=<pn>", "unknown",
     "robots.txt returns HTTP 403 - UNKNOWN means stop"),
    ("www.tmcshop.co.uk", "/?s=isuzu", "unknown",
     "robots.txt unreachable (the host is dead); the live T&M shop is www.tmcgroup.co.uk, "
     "which is allowed and is harvested below"),
]


def read_seed(name):
    p = HERE / name
    if not p.exists():
        return []
    out, seen = [], set()
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        v = line.strip().strip('"')
        if not v or v.lower() in ("part_no", "competitor_pn", "pn"):
            continue
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def squashed(s):
    return re.sub(r"[\s\-./]", "", str(s or "")).upper()


_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def save_page(fetcher, url, name):
    """Copy the cached bytes next to the report under a Windows-safe name.

    Product URLs carry a query string, which is illegal in a Windows filename, so
    every name is sanitised before it is written.
    """
    src = fetcher.cache_path(url)
    safe = _SAFE.sub("_", name).strip("._")
    if not safe:
        safe = "page"
    if not safe.lower().endswith(".html"):
        safe += ".html"
    dst = HERE / "pages" / safe
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        try:
            dst.write_bytes(src.read_bytes())
        except OSError:
            return ""
    return safe if dst.exists() else ""


class Blocked(Exception):
    """Two hard blocks on one host in one run - stop that host."""


class Runner:
    def __init__(self, online):
        self.f = PoliteFetcher(offline=not online)
        self.rows = []
        self.host_blocks = {}
        self.counts = {"pages": 0, "oe_queried": 0, "oe_hit": 0, "oe_empty": 0,
                       "comp_queried": 0, "comp_hit": 0, "comp_empty": 0,
                       "cards_seen": 0, "cards_followed": 0, "card_fetch_failed": 0,
                       "cards_rejected": 0,
                       "tmc_pages": 0, "tmc_cards": 0}

    def get(self, url, host):
        try:
            html = self.f.get(url)
        except ConsentRefused:
            TRIED.append({"host": host, "url_pattern": url, "robots_verdict": "blocked",
                          "outcome": "consent_refused"})
            raise Blocked(host)
        if html is None:
            self.host_blocks[host] = self.host_blocks.get(host, 0) + 1
            if self.host_blocks[host] >= 2:
                TRIED.append({"host": host, "url_pattern": url, "robots_verdict": "allowed",
                              "outcome": "hard_block_stop"})
                raise Blocked(host)
            return None
        self.counts["pages"] += 1
        return html

    def tranz_lookup(self, number, kind):
        """Two preconditions, both required, before any row is built.

        The runner enforces the toolchain's Mekonomen rule at BOTH steps: the search
        page must carry the number we asked for, and the product page must carry it
        too. `parse()` needs `expected_pn` precisely because the shop's search is a
        relevance search over a mixed cross-reference list - the 105-number brake-valve
        page returned for a 14459 query is proof that reading numbers off the page
        instead of keying on the query fabricates part numbers.
        """
        url = TRANZ_SEARCH.format(q=number)
        html = self.get(url, TRANZ)
        if html is None:
            TRIED.append({"host": TRANZ, "url_pattern": url, "robots_verdict": "allowed",
                          "outcome": "no_page"})
            return
        save_page(self.f, url, "search_" + kind + "_" + number + ".html")
        if not site_tranzparts.page_carries(html, number):
            TRIED.append({"host": TRANZ, "url_pattern": url, "robots_verdict": "allowed",
                          "outcome": "searched_number_not_on_search_page"})
            self.counts[kind + "_empty"] += 1
            print("   %-10s %-16s searched number absent from the search page" % (kind, number))
            return
        try:
            found = site_tranzparts.parse_search(html, source_url=url)
        except site_tranzparts.ParseError as e:
            TRIED.append({"host": TRANZ, "url_pattern": url, "robots_verdict": "allowed",
                          "outcome": "parse_error:" + str(e)[:120]})
            print("   %-10s %-16s search page not recognised: %s" % (kind, number, e))
            return
        cands = found["candidates"]
        TRIED.append({"host": TRANZ, "url_pattern": url, "robots_verdict": "allowed",
                      "outcome": "hit_search" if cands else "empty"})
        if not cands:
            self.counts[kind + "_empty"] += 1
            print("   %-10s %-16s 0 cards" % (kind, number))
            return
        self.counts["cards_seen"] += len(cands)
        accepted = 0
        for c in cands:
            self.counts["cards_followed"] += 1
            p_html = self.get(c["url"], TRANZ)
            if p_html is None:
                self.counts["card_fetch_failed"] += 1
                continue
            slug = c["url"].rstrip("/").split("/")[-1][:40]
            p_file = save_page(self.f, c["url"], "product_" + slug + ".html")
            try:
                rows = site_tranzparts.parse(p_html, expected_pn=number, source_url=c["url"],
                                             observed_at=TODAY)
            except site_tranzparts.ParseError as e:
                self.counts["cards_rejected"] = self.counts.get("cards_rejected", 0) + 1
                if "not printed on this product page" in str(e):
                    print("   %-10s %-16s card %s does not print the number - skipped"
                          % (kind, number, slug[:24]))
                continue
            for r in rows:
                # A competitor-number search can only ever produce a cross-reference
                # observation, and this shop's product pages do not name the competitor
                # brand behind a number (the vendor on an F 026 407 311 page is Bosch the
                # shop's supplier, not the graded edge), so there is nothing to cross-
                # reference FROM. Emitting the competitor number as `part_no` would also
                # put a number that is not 10 digits in the Isuzu slot. Nothing is
                # written for a competitor search: the hit is recorded in tried.csv.
                if kind == "comp":
                    continue
                r.update(page_file=p_file, crossref_grade="candidate",
                         source_tried="Tranzparts search by " + kind + " number")
                self.rows.append(r)
                accepted += 1
        if accepted:
            self.counts[kind + "_hit"] += 1
        else:
            self.counts[kind + "_empty"] += 1
        print("   %-10s %-16s %d card(s), %d row(s)" % (kind, number, len(cands), accepted))

    def tmc_walk(self):
        seen_pn = set()
        for url in TMC_CATEGORIES:
            html = self.get(url, TMC)
            if html is None:
                TRIED.append({"host": TMC, "url_pattern": url, "robots_verdict": "allowed",
                              "outcome": "no_page"})
                print("   tmc  no page  " + url)
                continue
            self.counts["tmc_pages"] += 1
            page_file = save_page(self.f, url, "cat_%d.html" % (abs(hash(url)) % 100000))
            try:
                rows = site_tmc.parse_category(html, source_url=url, observed_at=TODAY)
            except site_tmc.ParseError as e:
                TRIED.append({"host": TMC, "url_pattern": url, "robots_verdict": "allowed",
                              "outcome": "parse_error:" + str(e)[:120]})
                print("   tmc  %s -> %s" % (url, e))
                continue
            self.counts["tmc_cards"] += len(rows)
            added = 0
            for r in rows:
                if r["part_no"] in seen_pn:
                    continue
                seen_pn.add(r["part_no"])
                r.update(page_file=page_file, crossref_grade="candidate",
                         source_tried="T&M Commercials category walk")
                self.rows.append(r)
                added += 1
            TRIED.append({"host": TMC, "url_pattern": url, "robots_verdict": "allowed",
                          "outcome": "ok:%dcards" % len(rows)})
            print("   tmc  %3d card(s), %d new row(s)  %s" % (len(rows), added, url))


def write_rows(path, rows):
    cols = COLUMNS + [c for c in EXTRA_COLS if c not in COLUMNS]
    if path.exists():
        with path.open(encoding="utf-8", newline="") as fh:
            prev = list(csv.DictReader(fh))
        keys = {(r.get("loader"), r.get("part_no"), r.get("competitor_pn"),
                 r.get("source_url"), str(r.get("price")), r.get("observed_at")) for r in rows}
        keep = [p for p in prev
                if (p.get("loader"), p.get("part_no"), p.get("competitor_pn"),
                    p.get("source_url"), p.get("price"), p.get("observed_at")) not in keys]
        rows = keep + rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_tried(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"host": h, "url_pattern": u, "robots_verdict": v, "outcome": note}
            for h, u, v, note in OTHER_UK_HOSTS] + TRIED
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["host", "url_pattern", "robots_verdict", "outcome"])
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--online", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--oe", action="store_true")
    ap.add_argument("--competitors", action="store_true")
    ap.add_argument("--tmc-categories", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    oe = read_seed("seed_oe_pns.csv")
    comp = read_seed("seed_competitor_pns.csv")
    if a.limit:
        oe, comp = oe[:a.limit], comp[:a.limit]

    if not a.online or a.plan:
        print("mode            : plan only")
        print("Tranzparts OE   : %d numbers -> %s" % (len(oe), TRANZ_SEARCH.format(q="<pn>")))
        print("Tranzparts comp : %d numbers" % len(comp))
        print("T&M categories  : %d leaf pages (search route is 504)" % len(TMC_CATEGORIES))
        print("spacing         : >= %ss per host" % MIN_INTERVAL)
        return 0

    run = Runner(online=True)
    if a.all or a.competitors:
        print("\n--- Tranzparts: %d competitor numbers ---" % len(comp))
        for n in comp:
            run.counts["comp_queried"] += 1
            try:
                run.tranz_lookup(n, "comp")
            except Blocked:
                print("   STOP: %s hard-blocked twice" % TRANZ)
                break
            except Exception as e:
                run.counts["comp_errors"] = run.counts.get("comp_errors", 0) + 1
                print("   comp %-18s ERROR %s: %s" % (n, type(e).__name__, str(e)[:90]))
    if a.all or a.oe:
        print("\n--- Tranzparts: %d Isuzu numbers ---" % len(oe))
        for n in oe:
            run.counts["oe_queried"] += 1
            try:
                run.tranz_lookup(n, "oe")
            except Blocked:
                print("   STOP: %s hard-blocked twice" % TRANZ)
                break
            except Exception as e:
                run.counts["oe_errors"] = run.counts.get("oe_errors", 0) + 1
                print("   oe   %-18s ERROR %s: %s" % (n, type(e).__name__, str(e)[:90]))
    if a.all or a.tmc_categories:
        print("\n--- T&M Commercials: %d category pages ---" % len(TMC_CATEGORIES))
        try:
            run.tmc_walk()
        except Blocked:
            print("   STOP: %s hard-blocked twice" % TMC)

    rows = apply_fx(run.rows)[0]
    write_rows(HERE / "rows.csv", rows)
    write_tried(HERE / "tried.csv")

    tranz_rows = [r for r in rows if r.get("loader") == "tranzparts"]
    tmc_rows = [r for r in rows if r.get("loader") == "tmc"]
    status = {
        "agent": "A2",
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "date": TODAY,
        "online": True,
        "hosts": {
            "tranzparts.co.uk": {
                "robots": "allowed",
                "route": "search?q=<n>&type=product then the product page",
                "pages": run.counts["pages"],
                "rows": len(tranz_rows),
                "priced_rows": sum(1 for r in tranz_rows if r.get("price") is not None)},
            "www.tmcgroup.co.uk": {
                "robots": "allowed",
                "route": "category walk (every search route returns HTTP 504)",
                "pages": run.counts["tmc_pages"],
                "cards": run.counts["tmc_cards"],
                "rows": len(tmc_rows),
                "priced_rows": sum(1 for r in tmc_rows if r.get("price") is not None)}},
        "numbers_queried_oe": run.counts["oe_queried"],
        "numbers_with_rows_oe": run.counts["oe_hit"],
        "numbers_empty_oe": run.counts["oe_empty"],
        "numbers_queried_competitor": run.counts["comp_queried"],
        "numbers_with_rows_competitor": run.counts["comp_hit"],
        "numbers_empty_competitor": run.counts["comp_empty"],
        "cards_seen": run.counts["cards_seen"],
        "cards_followed": run.counts["cards_followed"],
        "card_fetch_failed": run.counts["card_fetch_failed"],
        "cards_rejected_number_not_on_page": run.counts.get("cards_rejected", 0),
        "fetch_stats": run.f.stats,
        "known_issue": ("match_method stays schema-valid; the U26 grade (candidate) travels "
                        "in the separate crossref_grade column. MATCH_METHODS not widened."),
        "measured_limits": {
            "tranzparts": ("the search card does NOT print the searched number; the number is "
                           "on the product page cross-reference list. One query costs the search "
                           "page plus one product page per card, all >= 2.2 s apart."),
            "tmc": ("no part-number query URL exists: /?s=, wp-json store/v2, wp-json wp/v2, "
                    "sitemap_index.xml and product-sitemap.xml all return HTTP 504, and "
                    "/product-category/.../page/2/ is 504. Only the /page/1 category tree answers.")},
    }
    (HERE / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    print("\nrows %d (tranzparts %d, tmc %d)" % (len(rows), len(tranz_rows), len(tmc_rows)))
    print("wrote rows.csv / tried.csv / status.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
