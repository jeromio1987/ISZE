# -*- coding: utf-8 -*-
"""Sitemap walker — turns each shop's own sitemap into a CANDIDATE page manifest.

Why this exists
---------------
`04_tools/price_ledger/page_manifest.csv` is hand-listed (or written by the part-number
runner for the three sites whose URL can carry a part number). geparden and mekster
can only be reached through their sitemaps, tungen and autoline through listing pages,
and nothing walked the sitemaps. This module does, and nothing more:

  1. per site: reads robots.txt once (cached), takes its `Sitemap:` lines and the
     crawl-delay for our bot identity;
  2. walks the sitemap index -> child sitemaps (only the children named in SITES, with
     a cap), caching every download under
     `01_data/90_INBOX/scrape_targets/_probe/sitemap_cache/<host>/`;
  3. keeps the URLs that look like product (or, for autoline/tungen, listing) pages;
  4. matches them to OUR part numbers: a 10-digit Isuzu number in the URL (strict,
     via `ledger_schema.normalise_pn`), or a graded competitor number from
     `crossref_graded.csv` (confirmed/likely only);
  5. drops every candidate robots.txt disallows for our bot identity;
  6. writes `04_tools/price_ledger/page_manifest_candidates.csv` in exactly the
     `page_manifest.csv` schema, a detail CSV and a per-site summary JSON.

It does NOT fetch product pages at volume. `--prove N` (hard cap 5 per site) fetches
at most N candidate pages per site through `fetch_polite.PoliteFetcher` (consent gate
+ cache) and runs the site parser on them, to prove the parser accepts the walker's
URLs. Candidates that were not fetched carry an empty `fetched_at`, so the ledger
bridge cannot mistake them for observed pages.

It never defeats a bot check, never logs in, never uses a browser. It does not edit
`page_manifest.csv`, the runners or the parsers; it only imports them.

Usage
-----
    python 04_tools/delegation/parsers/walk_sitemaps.py --selftest
    python 04_tools/delegation/parsers/walk_sitemaps.py                       # all sites, sitemaps only
    python 04_tools/delegation/parsers/walk_sitemaps.py --site geparden --prove 5
    python 04_tools/delegation/parsers/walk_sitemaps.py --offline --prove 5   # cache only, no network
    python 04_tools/delegation/parsers/walk_sitemaps.py --refresh             # re-download sitemaps
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html as html_lib
import importlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent                     # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
_CONSENT_DIR = ISZE / "04_tools" / "autodoc_scraper"
if str(_CONSENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CONSENT_DIR))

from fetch_polite import BOT_UA, HEADERS, MIN_INTERVAL, PoliteFetcher, ConsentRefused  # noqa: E402
from ledger_schema import normalise_pn                                                # noqa: E402

PROBE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
SITEMAP_CACHE = PROBE / "sitemap_cache"
MANIFEST = ISZE / "04_tools" / "price_ledger" / "page_manifest.csv"           # read for its header only
CANDIDATES = ISZE / "04_tools" / "price_ledger" / "page_manifest_candidates.csv"
DETAIL = HERE / "_sitemap_walk_candidates_detail.csv"
SUMMARY = HERE / "_sitemap_walk_summary.json"

TIERS = ISZE / "04_tools" / "delegation" / "state" / "refresh_tiers.csv"     # 16,511 billed PNs, A/B/C
SEED_A = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "seed_reach_tierA.csv"
GRADED = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"

MANIFEST_COLUMNS = ["site", "source_url", "page_file", "fetched_at", "note"]
DETAIL_COLUMNS = ["site", "source_url", "part_no", "tier", "in_seed_tierA", "match_kind",
                  "matched_token", "competitor_brand", "sitemap_url", "page_file", "proved"]

# Spacing for THIS module: never below the shared floor, and never below 5 s, because a
# volume runner may be hitting the same hosts through its own PoliteFetcher instance.
WALK_INTERVAL = max(MIN_INTERVAL, 5.0)
MAX_SITEMAP_BYTES = 60_000_000
PROVE_HARD_CAP = 5
TIMEOUT = 90

# ---------------------------------------------------------------------------
# Per-site configuration. Everything a site needs is here; adding one = one entry.
#   base           scheme+host whose robots.txt governs the walk
#   fallback       sitemap paths tried only when robots.txt names none
#   child_include  regex a child sitemap URL must match to be walked (None = all)
#   child_caps     {regex: max children of that family} — keeps autoline's 140 x 5 MB
#                  advert sitemaps out of a default run
#   product_re     regex a URL must match to count as a product page
#   listing_re     optional: listing pages the site parser reads (autoline, tungen);
#                  these become candidates without a part-number match
#   page_kind      what the site parser expects, for the summary
# ---------------------------------------------------------------------------
SITES: dict[str, dict] = {
    "omega": {
        "base": "https://omegaspareparts.com",
        "fallback": ["/sitemap_index.xml"],
        "child_include": r"/product-sitemap\d*\.xml$",
        "child_caps": {},
        "product_re": r"^https?://[^/]+/product/[^/?#]+/?$",
        "listing_re": None,
        "page_kind": "product",
    },
    "geparden": {
        "base": "https://geparden.no",
        "fallback": ["/sitemap.xml"],
        "child_include": r"/sitemaps/products-\d+\.xml$",
        "child_caps": {},
        # product codes after `-p-` can carry hyphens/underscores (`-p-ntyegr-bm-016a`,
        # `-p-pol08-27_17-139a-kit`); every loc in the product sitemaps is a product
        "product_re": r"^https?://[^/]+/products/[^/?#]+/?$",
        "listing_re": None,
        "page_kind": "product",
    },
    "mekster": {
        "base": "https://www.mekster.no",
        "fallback": ["/media/no_products_google_sitemap_index.xml"],
        "child_include": r"no_products_google_sitemap(_\d+)?\.xml$",
        "child_caps": {},
        "product_re": r"^https?://[^/]+/[^/?#]+\.html$",
        "listing_re": None,
        "page_kind": "product",
    },
    "tungen": {
        "base": "https://www.tungen-bil.no",
        "fallback": ["/sitemap_index.xml"],
        "child_include": r"/(product|product_cat)-sitemap\d*\.xml$",
        "child_caps": {},
        "product_re": r"/(produkt|product)/[^/?#]+/?$",
        # the parser reads the Isuzu older-original-parts category table
        "listing_re": r"/nettbutikk/[^?#]*isuzu[^?#]*/?$",
        "page_kind": "listing table",
    },
    "autoline": {
        "base": "https://autoline.dk",
        "fallback": ["/sitemap.xml"],
        "child_include": r"/sitemap-(advert-lists|adverts)-\d+\.xml$",
        # 140 advert sitemaps of ~5 MB each: walk a 2-file sample by default
        "child_caps": {r"/sitemap-adverts-\d+\.xml$": 2},
        "product_re": r"^https?://[^/]+/-/salg/",
        # Isuzu (tm2615) brand pages inside a spare-parts ('reservedele') category
        "listing_re": r"/-/[^/]*reservedele[^/]*/Isuzu--c\d+tm2615/?$",
        "page_kind": "listing (JSON-LD ItemList)",
    },
    "amayama": {
        "base": "https://www.amayama.com",
        "fallback": ["/sitemap.xml"],
        "child_include": None,
        "child_caps": {},
        "product_re": r"^https?://[^/]+/en/part/isuzu/[^/?#]+/?$",
        "listing_re": None,
        "page_kind": "product",
    },
    "ks": {
        "base": "https://www.ks-international.com",
        "fallback": ["/sitemap.xml"],
        "child_include": None,
        "child_caps": {},
        # Magento: products sit at the root as /<slug>.html; categories are nested
        "product_re": r"^https?://[^/]+/[^/?#]+\.html$",
        "listing_re": None,
        "page_kind": "search results (parser reads catalogsearch cards)",
    },
}


# ---------------------------------------------------------------------------
# robots.txt — group-aware crawl-delay + sitemap lines; Allow/Disallow via the gate
# ---------------------------------------------------------------------------
def _gate_allowed():
    """The consent gate's own matcher (honours '*' and '$'). Imported, never copied.

    That module swaps sys.stdout on import; flush first so nothing printed earlier is lost.
    """
    sys.stdout.flush()
    from check_scrape_consent import allowed
    return allowed


def parse_robots(text: str, ua: str = BOT_UA) -> dict:
    """Sitemap URLs, crawl-delay for our identity, and the disallow lines that apply.

    Crawl-delay: a group naming our agent wins over '*'; with neither, None.
    """
    groups, current = [], None
    sitemaps = []
    for raw in text.splitlines():
        line = raw.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()
        if field == "sitemap":
            sitemaps.append(value)
            continue
        if field == "user-agent":
            if current is None or current["rules_seen"]:
                current = {"agents": [], "rules": [], "delay": None, "rules_seen": False}
                groups.append(current)
            current["agents"].append(value.lower())
        elif current is not None and field in ("allow", "disallow"):
            current["rules_seen"] = True
            current["rules"].append((field, value))
        elif current is not None and field == "crawl-delay":
            current["rules_seen"] = True
            try:
                current["delay"] = float(value)
            except ValueError:
                pass

    ua_l = ua.lower()
    ua_token = ua_l.split("/")[0]
    specific = [g for g in groups if any(a != "*" and a and a in ua_l for a in g["agents"])
                or any(a == ua_token for a in g["agents"])]
    star = [g for g in groups if "*" in g["agents"]]
    applying = specific or star
    delays = [g["delay"] for g in applying if g["delay"] is not None]
    disallows = [v for g in (specific + star) for f, v in g["rules"] if f == "disallow" and v]
    return {"sitemaps": sitemaps, "crawl_delay": max(delays) if delays else None,
            "disallows": disallows, "groups": len(groups)}


# ---------------------------------------------------------------------------
# Fetching — robots-checked, spaced, cached. Sitemaps only.
# ---------------------------------------------------------------------------
class SitemapFetcher:
    def __init__(self, *, offline: bool = False, refresh: bool = False):
        self.offline = offline
        self.refresh = refresh
        self._last: dict[str, float] = {}
        self._robots: dict[str, str] = {}
        self.stats = Counter()

    @staticmethod
    def cache_path(url: str, ext: str = "xml") -> Path:
        host = re.sub(r"[^a-zA-Z0-9._-]", "_", urlparse(url).netloc)
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return SITEMAP_CACHE / host / f"{digest}.{ext}"

    def _network_get(self, url: str, interval: float) -> tuple[int, bytes]:
        import requests
        host = urlparse(url).netloc
        wait = interval - (time.monotonic() - self._last.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS, stream=True)
            body = bytearray()
            for chunk in r.iter_content(65536):
                body.extend(chunk)
                if len(body) > MAX_SITEMAP_BYTES:
                    r.close()
                    raise RuntimeError(f"larger than {MAX_SITEMAP_BYTES:,} bytes — refused")
            return r.status_code, bytes(body)
        finally:
            self._last[host] = time.monotonic()

    def _cached(self, url: str, ext: str, interval: float) -> tuple[str | None, str]:
        cp = self.cache_path(url, ext)
        meta = cp.with_suffix(cp.suffix + ".meta.json")
        if cp.exists() and not self.refresh:
            self.stats["cache_hits"] += 1
            return cp.read_text(encoding="utf-8", errors="replace"), "cache"
        if self.offline:
            self.stats["offline_misses"] += 1
            return None, "offline: not in cache"
        status, body = self._network_get(url, interval)
        if status >= 500:                       # one polite retry on a server error
            self.stats["retries_5xx"] += 1
            time.sleep(max(15.0, interval))
            status, body = self._network_get(url, interval)
        self.stats["downloads"] += 1
        self.stats["bytes"] += len(body)
        if status != 200:
            self.stats["http_errors"] += 1
            return None, f"HTTP {status}"
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_bytes(body)
        meta.write_text(json.dumps({"url": url, "fetched_at": _now(), "bytes": len(body)},
                                   indent=1), encoding="utf-8")
        return body.decode("utf-8", errors="replace"), "network"

    def robots(self, base: str) -> tuple[str | None, str]:
        """robots.txt is re-read on every live run (it is the authority); cached for offline."""
        if base in self._robots:
            return self._robots[base], "memo"
        url = base.rstrip("/") + "/robots.txt"
        saved_refresh = self.refresh
        self.refresh = not self.offline          # always fresh when online
        try:
            text, how = self._cached(url, "txt", WALK_INTERVAL)
        finally:
            self.refresh = saved_refresh
        if text is not None:
            self._robots[base] = text
        return text, how

    def sitemap(self, url: str, robots_text: str, interval: float) -> tuple[str | None, str]:
        path = urlparse(url).path or "/"
        if urlparse(url).query:
            path += "?" + urlparse(url).query
        if not _gate_allowed()(robots_text, path):
            self.stats["robots_refused"] += 1
            return None, "robots.txt disallows this sitemap"
        return self._cached(url, "xml", interval)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_LOC_RE = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.S | re.I)


def parse_sitemap(xml_text: str) -> tuple[str, list[str]]:
    """('index'|'urlset'|'unknown', [loc, ...]). Namespace-agnostic, tolerant of CDATA."""
    head = xml_text[:4000].lower()
    kind = "index" if "<sitemapindex" in head else ("urlset" if "<urlset" in head else "unknown")
    if kind == "unknown":
        low = xml_text.lower()
        kind = "index" if "<sitemapindex" in low else ("urlset" if "<urlset" in low else "unknown")
    locs = [html_lib.unescape(m.group(1).strip()) for m in _LOC_RE.finditer(xml_text)]
    return kind, locs


# ---------------------------------------------------------------------------
# Part-number universe and URL matching
# ---------------------------------------------------------------------------
def _read_pn_column(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_universe(extra_seeds: list[str] | None = None) -> dict:
    """{pn: {'tier': 'A'|'B'|'C'|'seed', 'tierA_seed': bool}} plus the crossref map."""
    pns: dict[str, dict] = {}
    for r in _read_pn_column(TIERS):
        pn = normalise_pn(r.get("part_no"))
        if pn:
            pns[pn] = {"tier": (r.get("tier") or "").strip() or "?", "tierA_seed": False}
    seedA = set()
    for r in _read_pn_column(SEED_A):
        pn = normalise_pn(r.get("part_no"))
        if pn:
            seedA.add(pn)
            pns.setdefault(pn, {"tier": "A", "tierA_seed": True})["tierA_seed"] = True
    for sp in extra_seeds or []:
        rows = _read_pn_column(Path(sp))
        col = next((c for c in (rows[0].keys() if rows else [])
                    if c.lower() in ("part_no", "pn", "part_number", "isze_pn")), None)
        if not col:
            raise SystemExit(f"seed {sp} needs a part_no column")
        for r in rows:
            pn = normalise_pn(r.get(col))
            if pn:
                pns.setdefault(pn, {"tier": "seed", "tierA_seed": False})

    # Competitor numbers: graded usable edges only. ALL of these are Eucon-sourced
    # (CROSSREF_GRADING_REPORT.md) — used locally for matching, never sent anywhere.
    xref: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for r in _read_pn_column(GRADED):
        if (r.get("tier") or "") not in ("confirmed", "likely"):
            continue
        key = re.sub(r"[^A-Z0-9]", "", (r.get("cpn_key") or r.get("competitor_pn") or "").upper())
        pn = normalise_pn(r.get("part_no"))
        if pn and _xref_key_ok(key):
            xref[key].append((pn, r.get("competitor_brand") or ""))
    return {"pns": pns, "seedA": seedA, "xref": dict(xref)}


def _xref_key_ok(key: str) -> bool:
    """A competitor key long and specific enough not to match slug noise."""
    return len(key) >= 6 and any(c.isdigit() for c in key) and any(c.isalpha() for c in key) \
        or (key.isdigit() and len(key) >= 8)


_DIGIT_RUN = re.compile(r"(?<!\d)\d+(?!\d)")
_DASHED_RUN = re.compile(r"(?<![0-9])\d{1,5}(?:-\d{1,5}){2,4}(?![0-9])")
_ISU_RUN = re.compile(r"(?:^|[^a-z])isu(\d{10})(?!\d)", re.I)


def match_url(url: str, universe: dict) -> list[dict]:
    """Every part number this URL points at. Strict: the number must be in OUR universe.

    Kinds, in order of trust:
      pn_slug_isu   geparden-style `-p-isu<10 digits>`
      pn_exact      a bare 10-digit run in the path
      pn_dashed     a dashed run (8-97062-294-0) that reduces to 10 digits
      crossref      a graded competitor number (confirmed/likely) as slug token(s)
    """
    path = urlparse(url).path
    low = path.lower()
    pns = universe["pns"]
    hits: dict[str, dict] = {}

    def add(pn, kind, token, brand=""):
        if pn in pns and pn not in hits:
            hits[pn] = {"part_no": pn, "match_kind": kind, "matched_token": token,
                        "competitor_brand": brand}

    for m in _ISU_RUN.finditer(low):
        add(normalise_pn(m.group(1)), "pn_slug_isu", "isu" + m.group(1))
    for m in _DIGIT_RUN.finditer(low):
        if len(m.group(0)) == 10:
            add(m.group(0), "pn_exact", m.group(0))
    for m in _DASHED_RUN.finditer(low):
        pn = normalise_pn(m.group(0))
        if pn:
            add(pn, "pn_dashed", m.group(0))

    xref = universe["xref"]
    if xref:
        seg = low.rstrip("/").rsplit("/", 1)[-1]
        seg = re.sub(r"\.html?$", "", seg)
        toks = [t for t in re.split(r"[^a-z0-9]+", seg) if t]
        seen = set()
        for i in range(len(toks)):
            for w in range(1, 5):
                if i + w > len(toks):
                    break
                key = "".join(toks[i:i + w]).upper()
                if key in seen or key not in xref:
                    continue
                seen.add(key)
                for pn, brand in xref[key]:
                    add(pn, "crossref", "-".join(toks[i:i + w]), brand)
    return list(hits.values())


def _pn_shaped(url: str) -> bool:
    """A product URL carrying an Isuzu-shaped number that is NOT one we bill (reported only)."""
    low = urlparse(url).path.lower()
    return bool(_ISU_RUN.search(low)) or ("isuzu" in low and any(
        len(m.group(0)) == 10 and m.group(0)[0] in "1589" for m in _DIGIT_RUN.finditer(low)))


def existing_manifest_urls() -> set[str]:
    """source_url values already in the hand manifest (read-only)."""
    if not MANIFEST.exists():
        return set()
    with MANIFEST.open(encoding="utf-8", newline="") as fh:
        return {(r.get("source_url") or "").strip() for r in csv.DictReader(fh)}


# ---------------------------------------------------------------------------
# The walk
# ---------------------------------------------------------------------------
def _child_allowed(url: str, cfg: dict, counts: Counter) -> bool:
    if cfg["child_include"] and not re.search(cfg["child_include"], url):
        return False
    for pat, cap in cfg["child_caps"].items():
        if re.search(pat, url):
            if counts[pat] >= cap:
                return False
            counts[pat] += 1
    return True


def walk_site(name: str, fetcher: SitemapFetcher, universe: dict, *, max_children: int) -> dict:
    cfg = SITES[name]
    base = cfg["base"]
    rep: dict = {"site": name, "base": base, "page_kind": cfg["page_kind"],
                 "robots": None, "crawl_delay": None, "interval_used_s": None,
                 "sitemaps_named_in_robots": [], "sitemaps_walked": [], "sitemaps_skipped": [],
                 "sitemaps_failed": [], "urls_seen": 0, "product_urls": 0, "listing_urls": 0,
                 "isuzu_keyword_urls": 0, "matched_urls": 0, "matched_part_numbers": 0,
                 "matched_tierA": 0, "matched_in_seed_tierA": 0, "match_kinds": {},
                 "robots_disallowed_candidates": 0, "robots_disallow_rules": 0,
                 "pn_shaped_outside_universe": 0, "already_in_page_manifest": 0,
                 "candidates": [], "notes": []}

    robots_text, how = fetcher.robots(base)
    if robots_text is None:
        rep["robots"] = f"UNREACHABLE ({how}) — site skipped; unknown means stop"
        return rep
    rb = parse_robots(robots_text)
    rep["robots"] = f"read ({how})"
    rep["crawl_delay"] = rb["crawl_delay"]
    rep["robots_disallow_rules"] = len(rb["disallows"])
    interval = max(WALK_INTERVAL, rb["crawl_delay"] or 0)
    rep["interval_used_s"] = interval
    rep["sitemaps_named_in_robots"] = rb["sitemaps"]
    allowed = _gate_allowed()

    roots = [u for u in rb["sitemaps"] if urlparse(u).netloc.endswith(urlparse(base).netloc.replace("www.", ""))]
    if not roots:
        roots = [base.rstrip("/") + p for p in cfg["fallback"]]
        rep["notes"].append(f"robots.txt names no sitemap; tried fallback {cfg['fallback']}")

    product_re = re.compile(cfg["product_re"], re.I)
    listing_re = re.compile(cfg["listing_re"], re.I) if cfg["listing_re"] else None
    queue = list(roots)
    seen_sm, family = set(), Counter()
    walked_children = 0
    cand_by_url: dict[str, dict] = {}
    kinds = Counter()
    matched_pns = set()

    while queue:
        sm = queue.pop(0)
        if sm in seen_sm:
            continue
        seen_sm.add(sm)
        text, how = fetcher.sitemap(sm, robots_text, interval)
        if text is None:
            rep["sitemaps_failed"].append({"url": sm, "why": how})
            continue
        kind, locs = parse_sitemap(text)
        rep["sitemaps_walked"].append({"url": sm, "kind": kind, "locs": len(locs), "via": how})
        if kind == "index":
            for child in locs:
                is_root_level = child in roots
                if not is_root_level and not _child_allowed(child, cfg, family):
                    rep["sitemaps_skipped"].append(child)
                    continue
                if walked_children >= max_children:
                    rep["sitemaps_skipped"].append(child)
                    continue
                walked_children += 1
                queue.append(child)
            continue

        for url in locs:
            rep["urls_seen"] += 1
            if "isuzu" in url.lower():
                rep["isuzu_keyword_urls"] += 1
            is_product = bool(product_re.search(url))
            is_listing = bool(listing_re and listing_re.search(url))
            if is_product:
                rep["product_urls"] += 1
            if is_listing:
                rep["listing_urls"] += 1
            if not (is_product or is_listing):
                continue
            hits = match_url(url, universe) if is_product else []
            if not hits and not is_listing:
                if is_product and _pn_shaped(url):
                    rep["pn_shaped_outside_universe"] += 1
                continue
            p = urlparse(url)
            path = (p.path or "/") + (f"?{p.query}" if p.query else "")
            if not allowed(robots_text, path):
                rep["robots_disallowed_candidates"] += 1
                continue
            if url in cand_by_url:
                continue
            if not hits:
                hits = [{"part_no": "", "match_kind": "listing_page", "matched_token": "",
                         "competitor_brand": ""}]
            cand_by_url[url] = {"url": url, "sitemap": sm, "hits": hits}
            for h in hits:
                kinds[h["match_kind"]] += 1
                if h["part_no"]:
                    matched_pns.add(h["part_no"])

    pns = universe["pns"]
    rep["matched_urls"] = sum(1 for c in cand_by_url.values() if c["hits"][0]["part_no"])
    rep["matched_part_numbers"] = len(matched_pns)
    rep["matched_tierA"] = sum(1 for pn in matched_pns if pns.get(pn, {}).get("tier") == "A")
    rep["matched_in_seed_tierA"] = sum(1 for pn in matched_pns if pn in universe["seedA"])
    rep["match_kinds"] = dict(kinds)
    rep["sitemaps_skipped_count"] = len(rep["sitemaps_skipped"])
    rep["sitemaps_skipped"] = rep["sitemaps_skipped"][:10]

    # stable order: tier A first, then exact kinds before crossref, then URL
    rank = {"pn_slug_isu": 0, "pn_exact": 1, "pn_dashed": 2, "crossref": 3, "listing_page": 4}
    tier_rank = {"A": 0, "B": 1, "C": 2}

    def key(c):
        h = c["hits"][0]
        return (tier_rank.get(pns.get(h["part_no"], {}).get("tier"), 3),
                rank.get(h["match_kind"], 9), c["url"])

    rep["candidates"] = sorted(cand_by_url.values(), key=key)
    return rep


# ---------------------------------------------------------------------------
# Proof: at most 5 product pages per site through the consent-gated fetcher
# ---------------------------------------------------------------------------
SITE_MODULE = {"amayama": "site_amayama", "ks": "site_ks", "omega": "site_omega",
               "geparden": "site_geparden", "mekster": "site_mekster",
               "tungen": "site_tungen", "autoline": "site_autoline"}


def page_file_for(url: str) -> str:
    """Where PoliteFetcher caches this URL, relative to the probe folder the bridge reads."""
    return PoliteFetcher.cache_path(url).relative_to(PROBE).as_posix()


def prove_site(rep: dict, n: int, offline: bool = False) -> list[dict]:
    n = min(n, PROVE_HARD_CAP)
    if n <= 0 or not rep["candidates"]:
        return []
    interval = max(WALK_INTERVAL, rep.get("crawl_delay") or 0)
    pf = PoliteFetcher(min_interval=interval, offline=offline)   # offline: cached pages only
    mod = importlib.import_module(SITE_MODULE[rep["site"]])
    out = []
    for c in rep["candidates"][:n]:
        url = c["url"]
        res = {"url": url, "expected_part_no": c["hits"][0]["part_no"], "fetched": False,
               "rows": 0, "rows_with_price": 0, "expected_pn_in_rows": None, "error": None}
        try:
            html = pf.get(url)
        except ConsentRefused:
            res["error"] = "consent gate refused"
            out.append(res)
            break
        if not html:
            res["error"] = "no body (HTTP error or empty)"
            out.append(res)
            continue
        res["fetched"] = True
        try:
            rows = mod.parse(html, source_url=url, observed_at=date.today().isoformat())
            res["rows"] = len(rows)
            res["rows_with_price"] = sum(1 for r in rows if r.get("price") is not None)
            if res["expected_part_no"]:
                res["expected_pn_in_rows"] = any(
                    res["expected_part_no"] == (r.get("part_no") or "") for r in rows)
            h0 = c["hits"][0]
            if h0["match_kind"] == "crossref":
                # the parser cannot know OUR number on a crossref page; the proof is that the
                # competitor number the walker matched is what the parsed row describes
                key = re.sub(r"[^A-Z0-9]", "", h0["matched_token"].upper())
                res["matched_token_in_rows"] = any(
                    key in re.sub(r"[^A-Z0-9]", "", " ".join(
                        str(r.get(f) or "") for f in ("part_no", "competitor_pn", "description")).upper())
                    for r in rows)
                res["parser_part_nos"] = sorted({str(r.get("part_no")) for r in rows if r.get("part_no")})
        except Exception as e:                                         # noqa: BLE001
            res["error"] = f"parse raised {type(e).__name__}: {str(e)[:160]}"
        out.append(res)
    rep["prove_stats"] = pf.stats
    return out


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
def manifest_rows(reports: list[dict], proofs: dict[str, list[dict]], universe: dict) -> tuple[list, list]:
    today = date.today().isoformat()
    pns = universe["pns"]
    man, det = [], []
    listed = existing_manifest_urls()
    for rep in reports:
        proved = {p["url"]: p for p in proofs.get(rep["site"], []) if p["fetched"]}
        rep["already_in_page_manifest"] = sum(1 for c in rep["candidates"] if c["url"] in listed)
        for c in rep["candidates"]:
            url = c["url"]
            pf = page_file_for(url)
            dup = "; ALREADY in page_manifest.csv" if url in listed else ""
            h0 = c["hits"][0]
            match_txt = "; ".join(
                f"{h['part_no'] or '-'} {h['match_kind']}"
                + (f" via {h['competitor_brand']} {h['matched_token']}" if h["match_kind"] == "crossref" else "")
                + (f" tier {pns.get(h['part_no'], {}).get('tier')}" if h["part_no"] else "")
                for h in c["hits"][:4])
            if url in proved:
                p = proved[url]
                fetched_at = today
                note = (f"fetched by walk_sitemaps.py --prove; parser rows {p['rows']}"
                        f" ({p['rows_with_price']} priced); match {match_txt}")
                if p["error"]:
                    note += f"; PARSE ERROR {p['error']}"
            else:
                fetched_at = ""
                note = f"CANDIDATE not fetched; from sitemap {c['sitemap']}; match {match_txt}"
            man.append({"site": rep["site"], "source_url": url, "page_file": pf,
                        "fetched_at": fetched_at, "note": note + dup})
            for h in c["hits"]:
                det.append({"site": rep["site"], "source_url": url, "part_no": h["part_no"],
                            "tier": pns.get(h["part_no"], {}).get("tier", "") if h["part_no"] else "",
                            "in_seed_tierA": h["part_no"] in universe["seedA"] if h["part_no"] else "",
                            "match_kind": h["match_kind"], "matched_token": h["matched_token"],
                            "competitor_brand": h["competitor_brand"], "sitemap_url": c["sitemap"],
                            "page_file": pf, "proved": url in proved})
    return man, det


def write_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def manifest_header() -> list[str]:
    with MANIFEST.open(encoding="utf-8", newline="") as fh:
        return next(csv.reader(fh))


# ---------------------------------------------------------------------------
# Selftest — offline, no network
# ---------------------------------------------------------------------------
def selftest() -> int:
    problems: list[str] = []

    def check(ok, msg):
        print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
        if not ok:
            problems.append(msg)

    print("walk_sitemaps selftest (offline)")
    # 1. schema identical to the hand manifest
    check(manifest_header() == MANIFEST_COLUMNS, f"candidate schema == page_manifest.csv header {MANIFEST_COLUMNS}")

    # 2. robots: crawl-delay group logic, sitemap lines, gate matcher reused
    rt = ("User-agent: *\nDisallow: /search\nDisallow: */catalogsearch/\nCrawl-delay: 5\n\n"
          "User-agent: SemrushBot\nCrawl-delay: 120\n\nSitemap: https://x.no/sitemap.xml\n")
    rb = parse_robots(rt)
    check(rb["crawl_delay"] == 5.0, "crawl-delay taken from '*' group, not SemrushBot's 120")
    check(rb["sitemaps"] == ["https://x.no/sitemap.xml"], "Sitemap: line read")
    allowed = _gate_allowed()
    check(not allowed(rt, "/search?q=1"), "gate matcher blocks /search")
    check(not allowed(rt, "/a/catalogsearch/result"), "gate matcher honours '*' wildcard")
    check(allowed(rt, "/products/x-p-isu8982705240"), "gate matcher allows a product path")
    rt2 = "User-agent: ISZE-parts-research\nCrawl-delay: 9\n\nUser-agent: *\nCrawl-delay: 2\n"
    check(parse_robots(rt2)["crawl_delay"] == 9.0, "group naming our bot wins over '*'")

    # 3. sitemap parsing: index, urlset, CDATA, entities, gzip handled by fetcher
    idx = ('<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           '<sitemap><loc>https://x.no/sitemaps/products-1.xml</loc></sitemap>'
           '<sitemap><loc><![CDATA[https://x.no/sitemaps/brands-1.xml]]></loc></sitemap></sitemapindex>')
    k, locs = parse_sitemap(idx)
    check(k == "index" and len(locs) == 2 and locs[1].endswith("brands-1.xml"), "index + CDATA parsed")
    us = ('<urlset><url><loc>https://x.no/a?x=1&amp;y=2</loc></url>'
          '<url><loc> https://x.no/b </loc></url></urlset>')
    k, locs = parse_sitemap(us)
    check(k == "urlset" and locs == ["https://x.no/a?x=1&y=2", "https://x.no/b"], "urlset + entities + whitespace")

    # 4. matching against a synthetic universe (no project data needed)
    uni = {"pns": {"8982705240": {"tier": "A"}, "8970622940": {"tier": "B"}, "5876150000": {"tier": "C"}},
           "seedA": {"8982705240"},
           "xref": {"LUCACP01114": [("8970622940", "Lucas")], "F026407311": [("5876150000", "Bosch")]}}
    m = match_url("https://geparden.no/products/oljefilter-isuzu-genuine-p-isu8982705240", uni)
    check([h["match_kind"] for h in m] == ["pn_slug_isu"] and m[0]["part_no"] == "8982705240", "geparden isu slug")
    m = match_url("https://geparden.no/products/x-p-isu4039378425944", uni)
    check(m == [], "13-digit isu accessory code is NOT trimmed into a part number")
    m = match_url("https://omegaspareparts.com/product/8-97062-294-0-air-filter/", uni)
    check(len(m) == 1 and m[0]["match_kind"] == "pn_dashed", "dashed 8-97062-294-0 matched")
    m = match_url("https://shop.no/filter-8970622940.html", uni)
    check(len(m) == 1 and m[0]["match_kind"] == "pn_exact", "bare 10-digit matched")
    m = match_url("https://shop.no/filter-1234567890.html", uni)
    check(m == [], "10-digit number outside OUR universe is ignored")
    m = match_url("https://geparden.no/products/ac-kompressor-lucas-p-lucacp01114", uni)
    check(len(m) == 1 and m[0]["match_kind"] == "crossref" and m[0]["part_no"] == "8970622940",
          "crossref single token (lucacp01114)")
    m = match_url("https://x.no/products/bosch-f-026-407-311-filter", uni)
    check(len(m) == 1 and m[0]["match_kind"] == "crossref", "crossref joined tokens (f-026-407-311)")
    check(not _xref_key_ok("ISC63") and _xref_key_ok("ISC633") and not _xref_key_ok("ABCDEFG"),
          "short / letter-only competitor keys refused")

    # 5. child-sitemap caps
    cfg = SITES["autoline"]
    fam = Counter()
    took = [u for u in (f"https://autoline.dk/sitemap-adverts-{i}.xml" for i in range(1, 9))
            if _child_allowed(u, cfg, fam)]
    check(len(took) == 2, "autoline advert sitemaps capped at 2")
    check(_child_allowed("https://autoline.dk/sitemap-advert-lists-3.xml", cfg, fam), "advert-lists walked")
    check(not _child_allowed("https://autoline.dk/sitemap-models-catalog-1.xml", cfg, fam), "other families skipped")
    check(bool(re.search(cfg["listing_re"], "https://autoline.dk/-/reservedele/Isuzu--c456tm2615")),
          "autoline Isuzu parts listing recognised")

    # 6. page_file is the path PoliteFetcher will cache to, relative to the bridge's folder
    u = "https://geparden.no/products/x-p-isu8982705240"
    check((PROBE / page_file_for(u)) == PoliteFetcher.cache_path(u), "page_file resolves to PoliteFetcher cache")

    # 7. on-disk recon sitemaps (if present): walker regexes see what the recon counted
    for f in sorted(PROBE.glob("v_geparden_products*.xml")):
        _, locs = parse_sitemap(f.read_text(encoding="utf-8", errors="replace"))
        prod = sum(1 for l in locs if re.search(SITES["geparden"]["product_re"], l, re.I))
        check(prod == len(locs) and len(locs) > 0, f"{f.name}: {len(locs):,} locs, all match geparden product_re")
    for f in sorted(PROBE.glob("v_mekster_sitemap_*.xml"))[:1]:
        _, locs = parse_sitemap(f.read_text(encoding="utf-8", errors="replace"))
        prod = sum(1 for l in locs if re.search(SITES["mekster"]["product_re"], l, re.I))
        check(prod / max(1, len(locs)) > 0.95, f"{f.name}: {prod:,}/{len(locs):,} match mekster product_re")

    # 8. the real universe loads and is sane (counts are read, not asserted to a number)
    u = load_universe()
    check(len(u["pns"]) > 1000 and len(u["seedA"]) > 100, f"universe: {len(u['pns']):,} billed PNs, "
          f"{len(u['seedA'])} Tier A seed, {len(u['xref']):,} usable competitor keys")

    print(f"\n{'SELFTEST PASS' if not problems else 'SELFTEST FAIL: ' + str(len(problems))}")
    return 0 if not problems else 1


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--site", choices=list(SITES) + ["all"], default="all")
    ap.add_argument("--max-children", type=int, default=12,
                    help="max child sitemaps walked per site (default 12)")
    ap.add_argument("--prove", type=int, default=0,
                    help=f"fetch + parse up to N candidate pages per site (hard cap {PROVE_HARD_CAP})")
    ap.add_argument("--seed", action="append", default=[],
                    help="extra CSV with a part_no column to add to the universe")
    ap.add_argument("--offline", action="store_true", help="cache only; open no connection")
    ap.add_argument("--refresh", action="store_true", help="re-download sitemaps even if cached")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.prove > PROVE_HARD_CAP:
        print(f"--prove capped at {PROVE_HARD_CAP} (sitemaps-only module; no volume fetching)")
        a.prove = PROVE_HARD_CAP
    if a.offline and a.prove:
        print("--offline: --prove re-parses cached pages only; nothing is fetched")

    universe = load_universe(a.seed)
    print(f"universe: {len(universe['pns']):,} part numbers ({TIERS.name} + {SEED_A.name}"
          f"{' + ' + ', '.join(a.seed) if a.seed else ''}); {len(universe['xref']):,} competitor keys "
          f"(crossref_graded confirmed/likely, Eucon-sourced, local use only)")

    sites = list(SITES) if a.site == "all" else [a.site]
    fetcher = SitemapFetcher(offline=a.offline, refresh=a.refresh)
    reports, proofs = [], {}
    for name in sites:
        print(f"\n== {name}  ({SITES[name]['base']})")
        t0 = time.monotonic()
        rep = walk_site(name, fetcher, universe, max_children=a.max_children)
        rep["walk_seconds"] = round(time.monotonic() - t0, 1)
        print(f"   robots {rep['robots']}; crawl-delay {rep['crawl_delay']}; interval {rep['interval_used_s']}s")
        print(f"   sitemaps walked {len(rep['sitemaps_walked'])}, skipped {rep.get('sitemaps_skipped_count', 0)}, "
              f"failed {len(rep['sitemaps_failed'])}")
        print(f"   urls {rep['urls_seen']:,} | product {rep['product_urls']:,} | listing {rep['listing_urls']:,} | "
              f"'isuzu' in url {rep['isuzu_keyword_urls']:,}")
        print(f"   candidates {len(rep['candidates']):,} | matched PNs {rep['matched_part_numbers']:,} "
              f"(Tier A {rep['matched_tierA']}, seed Tier A {rep['matched_in_seed_tierA']}) | kinds {rep['match_kinds']} "
              f"| robots-disallowed {rep['robots_disallowed_candidates']}")
        if a.prove:
            proofs[name] = prove_site(rep, a.prove, offline=a.offline)
            for p in proofs[name]:
                print(f"   prove: rows {p['rows']} priced {p['rows_with_price']} "
                      f"pn_in_rows {p['expected_pn_in_rows']} token_in_rows {p.get('matched_token_in_rows')} "
                      f"parser_pn {p.get('parser_part_nos')} err {p['error']}  {p['url'][:90]}")
        reports.append(rep)

    man, det = manifest_rows(reports, proofs, universe)
    if a.site != "all":                        # partial run: keep the other sites' rows
        for path, rows in ((CANDIDATES, man), (DETAIL, det)):
            if path.exists():
                with path.open(encoding="utf-8", newline="") as fh:
                    rows[:0] = [r for r in csv.DictReader(fh) if r.get("site") not in sites]
    write_csv(CANDIDATES, MANIFEST_COLUMNS, man)
    write_csv(DETAIL, DETAIL_COLUMNS, det)

    summary = {
        "built_at": _now(),
        "module": "04_tools/delegation/parsers/walk_sitemaps.py",
        "bot_identity": BOT_UA,
        "universe": {"part_numbers": len(universe["pns"]), "seed_tierA": len(universe["seedA"]),
                     "competitor_keys": len(universe["xref"]),
                     "sources": [str(TIERS.relative_to(ISZE)), str(SEED_A.relative_to(ISZE)),
                                 str(GRADED.relative_to(ISZE)) + " (confirmed/likely; Eucon-sourced)"]
                     + a.seed},
        "fetch": dict(fetcher.stats),
        "outputs": {"candidates": str(CANDIDATES.relative_to(ISZE)), "detail": str(DETAIL.relative_to(ISZE)),
                    "sitemap_cache": str(SITEMAP_CACHE.relative_to(ISZE))},
        "sites": [{k: v for k, v in r.items() if k != "candidates"} | {"candidates": len(r["candidates"]),
                   "proofs": proofs.get(r["site"], [])} for r in reports],
    }
    if a.site != "all" and SUMMARY.exists():
        try:                                 # keep other sites' last results
            old = json.loads(SUMMARY.read_text(encoding="utf-8"))
            keep = [s for s in old.get("sites", []) if s["site"] not in sites]
            summary["sites"] = keep + summary["sites"]
            summary["note"] = "partial run merged into the previous summary; candidates CSV holds only this run"
        except Exception:                                             # noqa: BLE001
            pass
    SUMMARY.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {CANDIDATES} ({len(man):,} rows)\nwrote {DETAIL} ({len(det):,} rows)\nwrote {SUMMARY}")
    print(f"fetch stats: {dict(fetcher.stats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
