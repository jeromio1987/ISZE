# -*- coding: utf-8 -*-
"""A dated observation pass over the three part-number shops, kept apart from every other pass.

WHY THIS FILE EXISTS (and why it does not change run_part_queries.py)
---------------------------------------------------------------------
`fetch_polite.PoliteFetcher` caches by URL alone. A second visit to the same URL is
answered from disk and never reaches the shop, so the shared runner cannot take a
second reading of a part it has already read: "re-fetch" returns the old page. That is
the right behaviour for a re-parse and the wrong one for measuring price movement.

This runner keeps each pass in its own folder:

    01_data/90_INBOX/scrape_targets/_probe/passes/<label>/cache/<host>/<hash>.html
    01_data/90_INBOX/scrape_targets/_probe/passes/<label>/fetch_<site>.jsonl   (one line per URL)

so pass 1's cache and observations are never overwritten. Fetching keeps every rule of
`fetch_polite`: the consent gate first, >= MIN_INTERVAL seconds between requests to one
host, the same User-Agent, no browser, no login. In addition a site is STOPPED (not
retried) on HTTP 403/429, on a page that looks like a bot challenge, or after 8
consecutive network/server errors — a refusal is recorded, never worked around.

Two steps:

  fetch     python run_dated_pass.py fetch --label tierA_pass2_2026-10-02 \
                 --pns-from-run _part_query_run_pass1.json --site ks --online
            python run_dated_pass.py fetch --label tierB_2026-10-01 \
                 --tier B --site omega --online
  finalize  python run_dated_pass.py finalize --label <label>
            (copies the pages into _probe/, appends them to page_manifest.csv dated by the
             UTC day each page was fetched, backs up the ledger files, then runs the bridge,
             the ledger, the verbatim/additive checks, price movement and the tender join)

The date a page enters the ledger under is the UTC date it was fetched, read from the
pass log — never the date the finalize step happens to run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent            # 04_tools/delegation/parsers
ISZE = HERE.parents[2]
sys.path.insert(0, str(HERE))

import fetch_polite                                # noqa: E402
from fetch_polite import PoliteFetcher, ConsentRefused, MIN_INTERVAL   # noqa: E402

PROBE = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
PASSES = PROBE / "passes"
SHARED_CACHE = PROBE / "cache"
MANIFEST = ISZE / "04_tools" / "price_ledger" / "page_manifest.csv"
TIERS = ISZE / "04_tools" / "delegation" / "state" / "refresh_tiers.csv"
LEDGER = ISZE / "01_data" / "00_derived" / "price_observations.parquet"

SITES = {
    "ks": ("site_ks", "https://www.ks-international.com/catalogsearch/result/?q={pn}"),
    "amayama": ("site_amayama", "https://www.amayama.com/en/part/isuzu/{pn}"),
    "omega": ("site_omega", "https://omegaspareparts.com/?s={pn}&post_type=product"),
}

STOP_STATUSES = {403, 429}
CHALLENGE_MARKERS = ("captcha", "cf-challenge", "challenge-platform", "are you a robot",
                     "verify you are human", "access denied", "attention required")
MAX_CONSECUTIVE_ERRORS = 8

MISS_MARKERS = ("read no 10-digit Isuzu part number", "carries 0 product cards",
                "found 0 valid data rows", "no Isuzu part numbers in any title",
                "recognised the page but found no price rows", "found no price rows")
EMPTY_PAGE_MARKERS = ("you searched for", "no products were found", "nothing found",
                      "returned no results", "0 results", "no results",
                      "out-of-stock", "out of stock", "no deliveries",
                      "currently unavailable", "discontinued")


def host_dir(url: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", urlparse(url).netloc)


def cache_file(root: Path, url: str) -> Path:
    return root / host_dir(url) / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}.html"


class PassFetcher(PoliteFetcher):
    """PoliteFetcher with a per-pass cache and a recorded status for every URL."""

    def __init__(self, cache_root: Path):
        super().__init__()
        self.cache_root = cache_root

    def get_status(self, url: str) -> tuple[str, int | None, int]:
        """Returns (outcome, http_status, bytes). Outcome: cached|ok|http|error|refused|challenge."""
        cp = cache_file(self.cache_root, url)
        if cp.exists():
            self.stats["cached"] += 1
            return "cached", 200, cp.stat().st_size

        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        if not self.consent(base, path):
            self.stats["refused"] += 1
            raise ConsentRefused(url)

        host = parts.netloc
        wait = self.min_interval - (time.monotonic() - self._last.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        try:
            import requests
            r = requests.get(url, timeout=fetch_polite.TIMEOUT, headers=fetch_polite.HEADERS,
                             allow_redirects=True)
        except Exception as e:                                     # noqa: BLE001
            self.stats["errors"] += 1
            print(f"    ERROR {str(e)[:120]}")
            return "error", None, 0
        finally:
            self._last[host] = time.monotonic()

        if r.status_code != 200:
            self.stats["errors"] += 1
            return "http", r.status_code, len(r.content)
        low = r.text[:30000].lower()
        if any(m in low for m in CHALLENGE_MARKERS) and len(r.content) < 60000:
            # a short page carrying challenge wording: treat as bot detection, do not store
            return "challenge", r.status_code, len(r.content)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_bytes(r.content)
        self.stats["fetched"] += 1
        return "ok", 200, len(r.content)


def pns_from_run(path: Path) -> list[str]:
    run = json.loads(path.read_text(encoding="utf-8"))
    return [str(p) for p in run["part_numbers"]]


def pns_from_tier(tier: str) -> list[str]:
    with TIERS.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = [r["part_no"].strip().zfill(10) for r in rows if r["tier"].strip() == tier]
    return [p for p in out if re.fullmatch(r"\d{10}", p)]


def cmd_fetch(a) -> int:
    pdir = PASSES / a.label
    cache_root = pdir / "cache"
    pdir.mkdir(parents=True, exist_ok=True)

    if a.pns_from_run:
        pns = pns_from_run(Path(a.pns_from_run))
        seed_desc = f"part list of {a.pns_from_run}"
    elif a.tier:
        pns = pns_from_tier(a.tier)
        seed_desc = f"refresh_tiers.csv tier {a.tier}"
    else:
        raise SystemExit("give --pns-from-run or --tier")
    if a.limit:
        pns = pns[:a.limit]

    site = a.site
    _, tpl = SITES[site]

    skipped = []
    if a.skip_uncached_in and site == "amayama":
        prev = Path(a.skip_uncached_in)
        keep = []
        for pn in pns:
            if cache_file(prev, tpl.format(pn=pn)).exists():
                keep.append(pn)
            else:
                skipped.append(pn)
        pns = keep

    meta = {"label": a.label, "site": site, "seed": seed_desc, "n_pns": len(pns),
            "skipped_known_404": len(skipped), "min_interval_s": MIN_INTERVAL,
            "online": a.online,
            "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (pdir / f"plan_{site}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    if not a.online:
        print("plan only (use --online to fetch)")
        return 0

    log = pdir / f"fetch_{site}.jsonl"
    done = set()
    if log.exists():
        for ln in log.read_text(encoding="utf-8").splitlines():
            try:
                j = json.loads(ln)
            except Exception:                                      # noqa: BLE001
                continue
            if j.get("outcome") in ("ok", "cached", "http"):
                done.add(j["pn"])

    f = PassFetcher(cache_root)
    consecutive = 0
    counts = Counter()
    stop_reason = None
    with log.open("a", encoding="utf-8") as fh:
        for i, pn in enumerate(pns, 1):
            if pn in done:
                counts["already_logged"] += 1
                continue
            url = tpl.format(pn=pn)
            ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
            try:
                outcome, status, size = f.get_status(url)
            except ConsentRefused:
                outcome, status, size = "refused", None, 0
            counts[outcome if outcome != "http" else f"http_{status}"] += 1
            fh.write(json.dumps({"pn": pn, "url": url, "fetched_at": ts, "outcome": outcome,
                                 "status": status, "bytes": size}) + "\n")
            fh.flush()
            if i % 50 == 0:
                print(f"   {site} {i}/{len(pns)}  {dict(counts)}", flush=True)

            if outcome == "refused":
                stop_reason = f"consent gate refused at {pn}"
                break
            if outcome == "challenge":
                stop_reason = f"bot-challenge page at {pn}"
                break
            if outcome == "http" and status in STOP_STATUSES:
                stop_reason = f"HTTP {status} at {pn}"
                break
            if outcome == "error" or (outcome == "http" and status and status >= 500):
                consecutive += 1
                if consecutive >= MAX_CONSECUTIVE_ERRORS:
                    stop_reason = f"{consecutive} consecutive errors, last at {pn}"
                    break
            else:
                consecutive = 0

    meta.update({"finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "counts": dict(counts), "stopped": stop_reason})
    (pdir / f"plan_{site}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 2 if stop_reason else 0


def backup(paths: list[Path], tag: str) -> list[str]:
    out = []
    for p in paths:
        if p.exists():
            dst = p.with_name(f"{p.name}.bak_{tag}")
            shutil.copy2(p, dst)
            out.append(str(dst))
    return out


def cmd_finalize(a) -> int:
    pdir = PASSES / a.label
    cache_root = pdir / "cache"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary = {"label": a.label, "finalized_at": stamp, "per_site": {}}
    manifest_lines: list[str] = []
    collisions: list[str] = []

    existing_manifest = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
    for site, (modname, _tpl) in SITES.items():
        log = pdir / f"fetch_{site}.jsonl"
        if not log.exists():
            continue
        mod = importlib.import_module(modname)
        entries = {}
        for ln in log.read_text(encoding="utf-8").splitlines():
            j = json.loads(ln)
            entries[j["pn"]] = j            # last record wins (a resumed run)
        c = Counter()
        for pn, j in entries.items():
            c[j["outcome"] if j["outcome"] != "http" else f"http_{j['status']}"] += 1
            if j["outcome"] not in ("ok", "cached"):
                continue
            cp = cache_file(cache_root, j["url"])
            if not cp.exists():
                c["cache_missing"] += 1
                continue
            date = j["fetched_at"][:10]
            html = cp.read_text(encoding="utf-8", errors="replace")
            try:
                rows = mod.parse(html, source_url=j["url"], observed_at=date)
            except Exception as e:                                 # noqa: BLE001
                low = html[:20000].lower()
                if any(m in str(e) for m in MISS_MARKERS) or any(m in low for m in EMPTY_PAGE_MARKERS):
                    c["not_stocked"] += 1
                else:
                    c["broken"] += 1
                continue
            c["with_rows"] += 1
            c["rows"] += len(rows)
            name = f"run{date}_{site}_{pn}.html"
            dst = PROBE / name
            if name in existing_manifest:
                # the same part, site and date is already in the ledger from another run
                # (e.g. an earlier small batch). One reading per page per day: keep the
                # one already loaded, do not add a second same-date observation.
                c["already_observed_same_day"] += 1
                continue
            if dst.exists():
                if dst.read_bytes() != cp.read_bytes():
                    collisions.append(name)
                    continue
            else:
                shutil.copy2(cp, dst)
            if name not in existing_manifest:
                manifest_lines.append(f"{site},{j['url']},{name},{date},dated pass {a.label}")
        summary["per_site"][site] = dict(c)
        print(f"{site:<9} {dict(c)}")

    if collisions:
        summary["collisions"] = collisions
        print(f"REFUSED — {len(collisions)} page name(s) already exist in _probe with other "
              f"content: {collisions[:5]}")
        (pdir / "finalize_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return 1

    if a.dry:
        print(f"dry: would append {len(manifest_lines)} manifest row(s)")
        return 0

    # back up everything the load rewrites, timestamped, before touching anything
    off = ISZE / "04_tools" / "price_ledger" / "OFFERED_ROWS.csv"
    summary["backups"] = backup([LEDGER, LEDGER.with_suffix(".meta.json"), MANIFEST, off],
                                f"{stamp}_before_{a.label}")
    print("backups:", *summary["backups"], sep="\n   ")

    if manifest_lines:
        with MANIFEST.open("a", encoding="utf-8") as fh:
            if existing_manifest and not existing_manifest.endswith("\n"):
                fh.write("\n")
            fh.write("\n".join(manifest_lines) + "\n")
    summary["manifest_rows_added"] = len(manifest_lines)
    print(f"appended {len(manifest_lines)} page(s) to page_manifest.csv")

    steps = [
        ("bridge", ISZE / "04_tools" / "price_ledger" / "build_scraped_observations.py", ["--emit"]),
        ("ledger", ISZE / "04_tools" / "price_ledger" / "build_price_ledger.py", []),
        ("verbatim check", ISZE / "04_tools" / "price_ledger" / "verify_scraped_observations.py", []),
        ("additive check", ISZE / "04_tools" / "price_ledger" / "check_loader_additive.py", []),
        ("price movement", ISZE / "04_tools" / "aftermarket_intelligence" / "build_price_movement.py", []),
        ("tender join", ISZE / "04_tools" / "aftermarket_intelligence" / "build_tender_price_context.py", []),
    ]
    fails = []
    for label, script, args in steps:
        p = subprocess.run([sys.executable, str(script), *args], cwd=str(ISZE),
                           capture_output=True, text=True, errors="replace")
        (pdir / f"step_{label.replace(' ', '_')}.log").write_text(p.stdout + "\n" + p.stderr,
                                                                   encoding="utf-8")
        ok = p.returncode == 0
        print(f"{'ok  ' if ok else 'FAIL'} {label}")
        if not ok:
            fails.append(label)
            for ln in (p.stdout + p.stderr).strip().splitlines()[-6:]:
                print(f"        {ln[:140]}")
            if label in ("bridge", "ledger"):
                break                      # nothing downstream is meaningful
    summary["downstream_failures"] = fails
    (pdir / "finalize_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {pdir / 'finalize_summary.json'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--label", required=True)
    f.add_argument("--site", choices=list(SITES), required=True)
    f.add_argument("--pns-from-run")
    f.add_argument("--tier")
    f.add_argument("--limit", type=int, default=0)
    f.add_argument("--skip-uncached-in", help="amayama only: skip part numbers that have no "
                   "page in this earlier cache (the known 404s)")
    f.add_argument("--online", action="store_true")
    z = sub.add_parser("finalize")
    z.add_argument("--label", required=True)
    z.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    return cmd_fetch(a) if a.cmd == "fetch" else cmd_finalize(a)


if __name__ == "__main__":
    raise SystemExit(main())
