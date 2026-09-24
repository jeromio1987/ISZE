# -*- coding: utf-8 -*-
"""
Scraper consent gate.

Before any scraper request runs, this checks the target's robots.txt for the bot
identity we actually use, and refuses (exit 1) where the site asks us away.

It exists because a 2026-09-18 review found two live problems in this stack:
  - auto365_scraper.py walks 21 product pages on a site whose robots.txt is
    "User-agent: * / Disallow: /"  -- disallowed for every bot except Google
  - mekonomen_scraper.py requests /catalogsearch/result/?q=<PN> and that site
    disallows both "*/?q" and "*/artiklar/search/" -- and it does not carry the
    Isuzu line at all, so the scrape is both disallowed and pointless

Nothing in this folder parsed robots.txt before this file.

Run:  python 04_tools/autodoc_scraper/check_scrape_consent.py
      python 04_tools/autodoc_scraper/check_scrape_consent.py --url <url> [--path <path>]
Exit 0 = clear. Exit 1 = blocked, do not fetch.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from urllib.parse import urljoin

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# The identity we use. Declared once, here, so it cannot drift per script.
BOT_UA = "ISZE-parts-research/1.0 (+aftersales analytics; contact via IML)"

# Every target this folder's scrapers reach, with the exact path they request.
TARGETS = [
    ("auto365_scraper.py", "https://www.auto365.co.il", "/product/5108/"),
    ("mekonomen_scraper.py", "https://www.mekonomen.se", "/catalogsearch/result/?q=8982705240"),
    ("ks_scraper.py", "https://www.ks-international.com", "/catalogsearch/result/?q=8982705240"),
    ("ks_scraper.py", "https://www.ks-international.com", "/sitemap.xml"),
    ("tmc_scraper.py", "https://www.tmcshop.co.uk", "/?s=isuzu"),
    ("tranzparts_scraper.py", "https://www.tranzparts.co.uk", "/collections/all"),
    ("autodoc_scraper.py", "https://www.autodoc.co.uk", "/search?keyword=8982705240"),
    ("-- new, 2026-09-18 --", "https://m-savion.co.il", "/itm/8980139111.UMI/"),
    ("-- new --", "https://giltechparts.com", "/?s=8973656540"),
    ("-- new --", "https://mekster.no", "/sok?q=8982705240"),
    ("-- new --", "https://geparden.no", "/produkt/ISU5876150000"),
    # 2026-09-24 (card C5): targets whose parsers are being written in
    # 04_tools/delegation/parsers/price_parsers.py. Listed here so no future fetch can
    # open a connection without the consent gate having been asked first.
    ("parsers/amayama", "https://www.amayama.com", "/en/part/isuzu/8974995480"),
    # Omega's real domain is omegaspareparts.com (verified in the 2026-09-18 UK/Ireland
    # research). Path = HTML search, NOT /wp-json/ — robots disallows /wp-json/.
    ("parsers/omega", "https://omegaspareparts.com", "/?s=8970622940&post_type=product"),
    ("parsers/tungen", "https://www.tungen-bil.no", "/nettbutikk/eldre-originale-bildeler/isuzu/isuzu-eldre-originale-deler/"),
]


def fetch_robots(base: str, timeout: int = 20):
    url = urljoin(base, "/robots.txt")
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": BOT_UA})
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}", url
        return r.text, None, url
    except Exception as e:                                    # noqa: BLE001
        return None, str(e)[:70], url


def allowed(robots_txt: str, path: str, ua: str = BOT_UA):
    """robots.txt check that DOES honour '*' wildcards and '$' anchors.

    Python's RobotFileParser treats '*' literally, so a rule like 'Disallow: */?q'
    never matches '/catalogsearch/result/?q=123' and the site looks permissive when
    it is not. Mekonomen is exactly that case. This matcher is minimal, ignores
    nothing, and when two rules conflict it takes the more restrictive one.
    """
    groups, current = [], None

    def new_group():
        return {"agents": [], "rules": []}

    for raw in robots_txt.splitlines():
        line = raw.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip()
        if field == "user-agent":
            if current is None or current["rules"]:
                current = new_group()
                groups.append(current)
            current["agents"].append(value.lower())
        elif field in ("allow", "disallow") and current is not None:
            current["rules"].append((field, value))

    def matches(rule: str, p: str) -> bool:
        if rule == "":
            return False
        pattern = re.escape(rule).replace(r"\*", ".*")
        if pattern.endswith(r"\$"):
            pattern = pattern[:-2] + "$"
        return re.match(pattern, p) is not None

    ua_l = ua.lower()
    verdict = True
    for g in groups:
        applies = any(a == "*" or a in ua_l for a in g["agents"])
        if not applies:
            continue
        for field, rule in g["rules"]:
            if matches(rule, path):
                # a longer Allow overrides a shorter Disallow, per convention
                if field == "disallow":
                    verdict = False
                else:
                    verdict = True if len(rule) >= 2 else verdict
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--path", default="/")
    a = ap.parse_args()

    if a.url:
        txt, err, rurl = fetch_robots(a.url)
        if err:
            print(f"UNKNOWN  {a.url}  robots.txt unreachable ({err})")
            print("         UNKNOWN means stop, not proceed.")
            sys.exit(1)
        ok = allowed(txt, a.path)
        print(f"{'ALLOWED' if ok else 'BLOCKED'}  {a.url}{a.path}")
        sys.exit(0 if ok else 1)

    print("=" * 84)
    print("SCRAPE CONSENT GATE")
    print(f"bot identity: {BOT_UA}")
    print("=" * 84)
    cache, blocked, unknown = {}, [], []

    for owner, base, path in TARGETS:
        if base not in cache:
            cache[base] = fetch_robots(base)
        txt, err, rurl = cache[base]
        if err:
            print(f"  UNKNOWN  {base:<34} robots unreachable: {err}")
            unknown.append((owner, base, path, err))
            continue
        ok = allowed(txt, path)
        mark = "allowed" if ok else "BLOCKED"
        print(f"  {mark:<8} {base:<34} {path[:44]:<46} ({owner})")
        if not ok:
            blocked.append((owner, base, path))

    print()
    print("=" * 84)
    if blocked:
        print(f"BLOCKED ON {len(blocked)} TARGET(S) - do not fetch:")
        for owner, base, path in blocked:
            print(f"  {base}{path}   ({owner})")
    if unknown:
        print(f"UNKNOWN ON {len(unknown)} TARGET(S) - treat as blocked:")
        for owner, base, path, err in unknown:
            print(f"  {base}   ({owner}) - {err}")
    if not blocked and not unknown:
        print("all targets clear for the declared bot identity")
    print()
    print("Rule: where a site asks crawlers away, stop and record it. Get the data")
    print("by licence, feed or written request instead. Never defeat the control.")
    sys.exit(1 if (blocked or unknown) else 0)


if __name__ == "__main__":
    main()
