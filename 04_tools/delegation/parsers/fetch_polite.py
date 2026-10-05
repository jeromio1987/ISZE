# -*- coding: utf-8 -*-
"""Polite fetcher — the ONE place a Phase 1 request opens a connection.

Every site parser in this package must fetch through here. It does three things
and nothing else:

  1. asks `check_scrape_consent.py` first and refuses if the answer is not exit 0;
  2. keeps at least MIN_INTERVAL seconds between requests to the same host;
  3. caches the raw bytes to disk under
     `01_data/90_INBOX/scrape_targets/_probe/cache/<host>/<hash>.html`
     so a re-parse never re-fetches.

It never defeats a bot check, never logs in, and never uses a browser.

Sized for the small-batch-first rule: `limit` defaults are small, and `fetch_many`
stops on the first hard block rather than hammering.

Usage
-----
    from fetch_polite import PoliteFetcher
    f = PoliteFetcher()
    html = f.get("https://geparden.no/products/...")      # consent-checked, cached
    rows = f.fetch_many(urls, limit=50)
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent                  # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
CONSENT = ISZE / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py"
CACHE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "cache"

BOT_UA = "ISZE-parts-research/1.0 (+aftersales analytics; contact via IML)"
HEADERS = {
    "User-Agent": BOT_UA,
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# The plan (SCRAPER_REDO_DELEGATION.md §8) requires >= 2 s between requests per
# site. Kept slightly above the floor so a clock rounding cannot dip under it.
MIN_INTERVAL = 2.2
TIMEOUT = 40


class ConsentRefused(RuntimeError):
    """Raised when the robots gate says no. Callers must not retry around this."""


class PoliteFetcher:
    """One instance per run. Tracks last-request time per host."""

    def __init__(self, min_interval: float = MIN_INTERVAL, offline: bool = False):
        self.min_interval = min_interval
        self.offline = offline            # True: cache-only, never opens a connection
        self._last: dict[str, float] = {}
        self.stats = {"fetched": 0, "cached": 0, "refused": 0, "errors": 0}

    # -- consent ---------------------------------------------------------------
    @staticmethod
    def consent(base: str, path: str) -> bool:
        """Exit 0 means clear. Anything else — including UNKNOWN — means no."""
        proc = subprocess.run(
            [sys.executable, str(CONSENT), "--url", base, "--path", path],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(f"    consent REFUSED: {(proc.stdout or '').strip().splitlines()[:1]}")
            return False
        return True

    # -- cache -----------------------------------------------------------------
    @staticmethod
    def cache_path(url: str) -> Path:
        host = re.sub(r"[^a-zA-Z0-9._-]", "_", urlparse(url).netloc)
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return CACHE / host / f"{digest}.html"

    def get(self, url: str, *, force: bool = False) -> str | None:
        """Fetch one URL. Cache first, consent second, network last."""
        cp = self.cache_path(url)
        if cp.exists() and not force:
            self.stats["cached"] += 1
            return cp.read_text(encoding="utf-8", errors="replace")
        if self.offline:
            return None

        parts = urlparse(url)
        base, path = f"{parts.scheme}://{parts.netloc}", (parts.path or "/") + (
            f"?{parts.query}" if parts.query else "")
        if not self.consent(base, path):
            self.stats["refused"] += 1
            raise ConsentRefused(url)

        host = parts.netloc
        wait = self.min_interval - (time.monotonic() - self._last.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)

        try:
            import requests
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        except Exception as e:                                     # noqa: BLE001
            self.stats["errors"] += 1
            print(f"    ERROR {str(e)[:120]}")
            return None
        finally:
            self._last[host] = time.monotonic()

        if r.status_code != 200:
            self.stats["errors"] += 1
            print(f"    HTTP {r.status_code} {url}")
            return None
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_bytes(r.content)
        self.stats["fetched"] += 1
        return r.text

    def fetch_many(self, urls, *, limit: int = 50) -> list[tuple[str, str]]:
        """Small-batch fetch: stops after `limit` and on the first refusal."""
        out: list[tuple[str, str]] = []
        for i, url in enumerate(urls, 1):
            if i > limit:
                print(f"    limit {limit} reached — stopping (small-batch rule)")
                break
            try:
                html = self.get(url)
            except ConsentRefused:
                print("    stopping the batch: consent refused")
                break
            if html:
                out.append((url, html))
        return out


if __name__ == "__main__":
    f = PoliteFetcher()
    target = sys.argv[1] if len(sys.argv) > 1 else "https://geparden.no/sitemap.xml"
    print(f.get(target)[:400] if f.get(target) else "no body")
    print("stats:", f.stats)
