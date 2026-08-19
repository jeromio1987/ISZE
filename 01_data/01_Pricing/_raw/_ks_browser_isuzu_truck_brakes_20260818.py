"""Pass 2: fresh Chrome profile, Isuzu truck (N75/7.5t) brake PDPs only."""
from __future__ import annotations

import csv
import json
import random
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PwTimeout
from playwright.sync_api import sync_playwright

# reuse extractors from pass 1
import importlib.util

_p1 = Path(__file__).with_name("_ks_browser_brake_crawl_20260818.py")
spec = importlib.util.spec_from_file_location("ks_p1", _p1)
p1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p1)

OUT_DIR = Path(__file__).resolve().parent
STAMP = "20260818"
CSV_PATH = OUT_DIR / f"ks_catalog_isuzu_truck_brake_sku_hunt_{STAMP}.csv"
JSON_PATH = OUT_DIR / f"ks_catalog_isuzu_truck_brake_sku_hunt_{STAMP}.json"

SEEDS = [
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brakes.html",
]
MAX_LISTING_PAGES = 12
MAX_PDPS = 120
NAV_TIMEOUT = 45_000


def is_isuzu_truck_brake(url: str) -> bool:
    u = (url or "").lower()
    if "ks-international.com" not in u:
        return False
    if "isuzu" not in u:
        return False
    if "d-max" in u or "mu-x" in u or "rodeo" in u:
        return False
    return "/brakes" in urlparse(u).path


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    profile = Path(tempfile.mkdtemp(prefix="ks_anon_isuzu_"))
    notes: list[str] = []
    cat_urls: set[str] = set(SEEDS)
    product_urls: list[str] = []
    seen_p: set[str] = set()
    rows: list[dict] = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            channel="chrome",
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="en-GB",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(NAV_TIMEOUT)

        for seed in SEEDS:
            try:
                page.goto(seed, wait_until="domcontentloaded")
            except PwTimeout:
                notes.append(f"timeout_seed:{seed}")
                continue
            time.sleep(1.4)
            hrefs = page.eval_on_selector_all(
                "a",
                "els => els.map(e => e.href).filter(Boolean)",
            )
            for h in hrefs:
                if is_isuzu_truck_brake(h):
                    cat_urls.add(h.split("?")[0])
                lu = (h or "").lower()
                if "isuzu" in lu and "truck" in lu and "7-5" in lu:
                    cat_urls.add(h.split("?")[0])

        notes.append(f"discovered_urls={len(cat_urls)}")
        cats = [u for u in cat_urls if is_isuzu_truck_brake(u)]
        if not cats:
            cats = [u for u in SEEDS if "brake" in u]
        notes.append(f"brake_cats={len(cats)}")

        for cat in sorted(cats)[:40]:
            try:
                page.goto(cat, wait_until="domcontentloaded")
            except PwTimeout:
                notes.append(f"timeout_cat:{cat}")
                continue
            time.sleep(1.0 + random.random())
            pages = 0
            while pages < MAX_LISTING_PAGES:
                pages += 1
                for h in p1.listing_product_hrefs(page):
                    if h in seen_p:
                        continue
                    seen_p.add(h)
                    product_urls.append(h)
                nxt = p1.next_listing_url(page)
                if not nxt or nxt == page.url:
                    break
                try:
                    page.goto(nxt, wait_until="domcontentloaded")
                except PwTimeout:
                    break
                time.sleep(0.9 + random.random())

        notes.append(f"listing_product_urls={len(product_urls)}")

        def p_rank(u: str) -> int:
            lu = u.lower()
            if "pad" in lu:
                return 0
            if "disc" in lu or "rotor" in lu:
                return 1
            if "shoe" in lu or "lining" in lu:
                return 2
            return 3

        product_urls = sorted(product_urls, key=p_rank)[:MAX_PDPS]
        for url in product_urls:
            try:
                page.goto(url, wait_until="domcontentloaded")
            except PwTimeout:
                rows.append(
                    {
                        "url": url,
                        "ks_sku": "",
                        "title": "",
                        "line": "",
                        "price_ex_vat_gbp": None,
                        "price_inc_vat_gbp": None,
                        "stock": "",
                        "oem_on_page": "",
                        "matched_isze_oem": "",
                        "status": "timeout",
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                continue
            time.sleep(0.85 + random.random())
            rec = p1.extract_pdp(page)
            rec["status"] = "ok"
            rows.append(rec)
            if rec.get("matched_isze_oem"):
                notes.append(
                    f"HIT {rec['matched_isze_oem']} sku={rec['ks_sku']} {url}"
                )

        context.close()

    fields = [
        "url",
        "ks_sku",
        "title",
        "line",
        "price_ex_vat_gbp",
        "price_inc_vat_gbp",
        "stock",
        "oem_on_page",
        "matched_isze_oem",
        "status",
        "scraped_at",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    hits = [r for r in rows if r.get("matched_isze_oem")]
    payload = {
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "session": "chrome_channel_fresh_user_data_dir",
        "target_oems": sorted(p1.TARGET_OEMS),
        "n_pdps": len(rows),
        "n_hits": len(hits),
        "hits": hits,
        "notes": notes,
        "csv": str(CSV_PATH),
    }
    JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {CSV_PATH} n={len(rows)} hits={len(hits)}")
    for n in notes:
        print(n)


if __name__ == "__main__":
    main()
