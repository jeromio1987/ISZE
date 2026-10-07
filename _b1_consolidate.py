# -*- coding: utf-8 -*-
"""B1 phase 24 — consolidate outputs.

Writes, into _u26/B1/:
  rows.csv        ledger-shaped rows (header only: no host passed every gate), plus
                  page_file, crossref_grade, source_tried
  tried.csv       one row per host attempted (deduped from the raw log), with verdict
  tried_raw.csv   the raw append-only attempt log
  why_failed.csv  exact failure reason per non-allowed host (already written)
  status.json     counts

Nothing here touches a shared file except _u26/B_HOSTS_CLAIMED.csv, which was appended
to during discovery. The ledger parquet is not touched.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
for c in [HERE, *HERE.parents]:
    if (c / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py").exists():
        ISZE = c
        break
sys.path.insert(0, str(ISZE / "04_tools" / "delegation" / "parsers"))
from ledger_schema import COLUMNS   # noqa: E402

B1 = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1"
PROBE = B1.parent
SHARED = PROBE / "B_HOSTS_CLAIMED.csv"

# page-shape conclusions per allowed/looked-at host, read from the fetched bytes.
# (host: robots_verdict, page_shape, outcome)
FINDINGS: dict[str, tuple[str, str, str]] = {
    "www.megapecas.pt": ("allowed", "server-rendered prices (EUR, IVA), ISUZU is a make",
                         "search ignores the OE term: identical 24-card list for 'filtro', "
                         "'travao' and every OE/brand number; make page has no products"),
    "www.autosil.pt": ("allowed", "battery shop, no product prices in HTML, IVA wording only",
                       "not an Isuzu parts seller"),
    "www.soauto.pt": ("allowed", "robots blocks /*? and /*search; group marketing site",
                      "no part-number search path allowed"),
    "www.roady.pt": ("allowed", "robots.txt is 0 bytes; JS chain site",
                     "no server-rendered prices"),
    "www.feuvert.pt": ("allowed", "robots blocks /catalogsearch/, /search/, /product*",
                       "every part-search path disallowed"),
    "www.motocar.pt": ("allowed", "moto/bicycle dealer site, 0 price tokens in HTML",
                       "not an auto-parts seller"),
    "www.ersatzteile-24.com": ("allowed", "household-appliance spares (Bosch/AEG/Miele)",
                               "wrong catalogue (white goods)"),
    "www.autopartslogistic.com": ("allowed", "login wall + JS search form (POST index.php?id=23)",
                                  "no server-rendered prices, no accessible part search"),
    "www.casadaspecas.pt": ("allowed", "household-appliance spares (electrodomesticos)",
                            "wrong catalogue; /pt/pesquisa robots-disallowed"),
    "www.lojadaspecas.pt": ("allowed", "household-appliance spares", "wrong catalogue"),
    "www.rodasa.com": ("allowed", "industrial castors, 1,001 product URLs, 0 Isuzu",
                       "not an Isuzu parts seller"),
    "www.rasch.pt": ("allowed", "construction/remodelling company", "not a parts seller"),
    "www.agauto.pt": ("allowed", "search rejected by the site (429); 15-URL sitemap",
                      "no usable catalogue"),
    "www.pneubeato.com": ("allowed", "tyres + EBC brakes, Isuzu D-Max category; no prices in HTML",
                          "Isuzu brake coverage exists but prices load from JavaScript"),
    "www.parts.pt": ("allowed", "1-URL placeholder sitemap", "no catalogue"),
    "www.areal.pt": ("allowed", "1-URL placeholder sitemap", "no catalogue"),
    "www.epecas.pt": ("allowed", "WordPress, 14-URL sitemap, no products", "no catalogue"),
    "www.motointegrator.pt": ("allowed", "home page returns HTTP 403 (bot check)", "blocked on fetch"),
    "www.winparts.es": ("allowed", "TecDoc shop, ships PT, EUR; /search?q= and /parts/ robots-blocked; "
                                   "product pages show no price in HTML",
                        "part-number search disallowed; prices JavaScript"),
    "www.winparts.nl": ("allowed", "robots Disallow: / and /zoekresultaten?zoek=",
                        "site disallows crawlers"),
    "www.todoparatucoche.com": ("allowed", "/buscar and ?search_query= robots-blocked",
                                "part search disallowed"),
    "www.autoparts24.eu": ("allowed", "used-parts platform; /search is a JS shell, 0 prices",
                           "prices not server-rendered"),
    "www.b-parts.com": ("allowed", "PT used-parts marketplace; home 200 with server prices, "
                                   "product/ search pages HTTP 403",
                        "bot check on the pages that matter"),
    "www.oscaro.pt": ("allowed", "robots Disallow: / (final catch-all)", "site disallows crawlers"),
    "www.oscaro.es": ("allowed", "robots Disallow: / (final catch-all)", "site disallows crawlers"),
    "www.isuzu.pt": ("allowed", "Isuzu PT importer marketing site, 0 prices", "no shop"),
    "www.acp.pt": ("allowed", "Automovel Club de Portugal, non-shop", "no parts shop"),
    "www.pecasauto.com.pt": ("allowed", "Volpecas truck parts, contacts only, 0 prices", "no shop"),
    "www.autopecas.online": ("allowed", "114-byte placeholder page", "dead domain"),
    "www.autopecas.com.pt": ("allowed", "multibrand workshop site, 0 prices in HTML", "no shop"),
    "www.autolux.pt": ("allowed", "car dealer (buys/sells vehicles)", "not a parts seller"),
    "www.autocenter.pt": ("allowed", "WooCommerce; /?s= search returns unrelated products, 0 prices",
                          "no Isuzu stock; prices not in HTML"),
    "www.nortecar.pt": ("allowed", "'sitemap.xml' is an HTML page; used-car dealer", "not a parts seller"),
    "www.silvauto.pt": ("allowed", "used-car stand", "not a parts seller"),
    "www.rodauto.pt": ("allowed", "used-car listings", "not a parts seller"),
    "www.midas.pt": ("allowed", "workshop chain, no parts catalogue", "no parts shop"),
    "www.custojusto.pt": ("allowed", "classifieds; robots header says spiders are expressly forbidden",
                          "dropped: terms forbid automated access"),
    "www.pecasoriginais.pt": ("allowed", "HTTP 503 on the home page", "site down"),
    "www.pecasauto.com": ("allowed", "114-byte placeholder page", "dead domain"),
    "www.intercars.pt": ("unreachable", "robots.txt HTTP 404", "no robots -> treated as blocked"),
    "www.intercars.eu": ("unreachable", "robots.txt HTTP 403", "no robots -> treated as blocked"),
}


def dedupe_tried() -> list[list[str]]:
    raw = B1 / "tried.csv"
    rows = list(csv.reader(raw.open(encoding="utf-8")))
    header, body = rows[0], rows[1:]
    (B1 / "tried_raw.csv").write_text(
        "\n".join(",".join(r) for r in rows) + "\n", encoding="utf-8")
    best: "OrderedDict[str, list[str]]" = OrderedDict()
    rank = {"allowed": 0, "blocked": 1, "unreachable": 2, "not_retried": 3}
    for r in body:
        if not r:
            continue
        host = r[0]
        if host not in best or rank.get(r[2], 9) < rank.get(best[host][2], 9):
            best[host] = r
    # enrich the allowed ones with the page-shape finding
    out = []
    for host, r in best.items():
        f = FINDINGS.get(host)
        if f:
            out.append([host, r[1], f[0], f[2], f[1]])
        else:
            out.append(r)
    return out


def main() -> int:
    hosts = dedupe_tried()
    with (B1 / "tried.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["host", "url_pattern", "robots_verdict", "outcome", "checked_at"])
        w.writerows(hosts)

    # rows.csv — ledger shape, header only (no host passed every gate)
    with (B1 / "rows.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS + ["page_file", "crossref_grade", "source_tried"])

    verdicts = Counter(r[2] for r in hosts)
    allowed = [r[0] for r in hosts if r[2] == "allowed"]
    status = {
        "agent": "B1",
        "work_package": "B (Portugal) — discovery + first usable host",
        "ran_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "branch": "cursor/2026-10-07-universe-u26-market-harvest",
        "hosts_tried": len(hosts),
        "hosts_by_verdict": dict(verdicts),
        "hosts_allowed_by_robots": allowed,
        "usable_hosts": [],
        "numbers_queried_to_a_usable_host": 0,
        "numbers_with_at_least_one_row": 0,
        "numbers_still_empty": 123,
        "competitor_numbers_queried": 0,
        "pages_fetched": len(list((B1 / "pages").glob("*.html"))),
        "rows": 0,
        "priced_rows": 0,
        "hits": 0,
        "misses": 0,
        "blocked_hosts": verdicts.get("unreachable", 0) + verdicts.get("blocked", 0),
        "result": ("No Portuguese host passed all three gates at once (server-rendered price, "
                   "HTTP 200 to the declared bot, robots-allowed path). The Portuguese market "
                   "is closed to automated price collection through the shops reachable from "
                   "this machine."),
        "exact_blockers": {
            "bot_check_403_or_turnstile": ["www.norauto.pt", "www.olx.pt", "www.endado.com",
                                           "www.skruvat.com", "www.motointegrator.pt",
                                           "www.b-parts.com (product pages)",
                                           "www.autodoc.co.uk", "www.oscaro.com", "www.trodo.com",
                                           "www.alvadi.pt"],
            "robots_disallows_the_search": ["www.soauto.pt", "www.feuvert.pt", "www.winparts.es",
                                            "www.winparts.nl", "www.todoparatucoche.com",
                                            "www.oscaro.pt", "www.oscaro.es",
                                            "www.casadaspecas.pt (pt/pesquisa)"],
            "prices_only_in_javascript": ["www.pneubeato.com", "www.autoparts24.eu",
                                          "www.autocenter.pt", "www.winparts.es product pages"],
            "no_isuzu_coverage": ["www.megapecas.pt", "www.autocenter.pt", "www.autosil.pt",
                                  "www.rodasa.com", "www.lojadaspecas.pt", "www.casadaspecas.pt"],
            "not_a_parts_shop": ["www.motocar.pt", "www.rodauto.pt", "www.silvauto.pt",
                                 "www.autolux.pt", "www.nortecar.pt", "www.midas.pt",
                                 "www.isuzu.pt", "www.acp.pt", "www.rasch.pt"],
            "no_robots_txt_404_or_403": ["www.intercars.pt", "www.intercars.eu",
                                         "katalog.intercars.eu"],
            "dead_or_no_catalogue": ["www.parts.pt", "www.areal.pt", "www.epecas.pt",
                                     "www.autopecas.online", "www.pecasauto.com",
                                     "www.pecasoriginais.pt (503)", "www.agauto.pt",
                                     "www.pecasauto.com.pt"],
            "terms_forbid_automation": ["www.custojusto.pt"],
            "dns_or_ssl_failure": ["most of the .pt guesses tested (see tried.csv)"],
        },
        "reconciliation": {
            "match_method": ("kept schema-valid `crossref`; the brief's `crossref_candidate` / "
                             "`crossref_corroborated` are not in MATCH_METHODS, so the grade "
                             "travels in the separate `crossref_grade` column, as the run "
                             "instructions require. MATCH_METHODS was NOT widened."),
            "tax_basis": ("Portuguese pages were read for IVA wording but no page states a price "
                          "basis in the HTML we could read, so no `vat` value was written."),
        },
        "parser": ("No host passed, so no `site_*.py` parser was written. "
                   "`price_parsers.py --selftest` was run to confirm the existing parsers are green."),
        "could_not_do": [
            "Fetch any Portuguese part price: no allowed host served one server-side.",
            "Query the 123 OE / 153 competitor numbers against a usable PT host: no usable host.",
            "Use megapacas OR b-parts search: megapecas ignores the OE term (identical 24-card "
            "list for every query, verified on 'filtro', 'travao', 2 OEs and a brand number); "
            "b-parts product pages return HTTP 403 to our identity (bot check). Nothing was "
            "bypassed.",
        ],
    }
    (B1 / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
    print(json.dumps({k: status[k] for k in ("hosts_tried", "hosts_by_verdict", "rows",
                                             "pages_fetched")}, indent=2))
    print(f"\nwrote rows.csv, tried.csv, tried_raw.csv, status.json in {B1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
