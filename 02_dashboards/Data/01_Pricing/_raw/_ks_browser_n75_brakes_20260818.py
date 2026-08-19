"""Pass 3: N75 / 7.5-ton truck tree only (not Trooper/D-Max)."""
from __future__ import annotations

import csv
import json
import random
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PwTimeout
from playwright.sync_api import sync_playwright
import importlib.util

_p1 = Path(__file__).with_name("_ks_browser_brake_crawl_20260818.py")
spec = importlib.util.spec_from_file_location("ks_p1", _p1)
p1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p1)

OUT_DIR = Path(__file__).resolve().parent
STAMP = "20260818"
CSV_PATH = OUT_DIR / f"ks_catalog_n75_brake_sku_hunt_{STAMP}.csv"
JSON_PATH = OUT_DIR / f"ks_catalog_n75_brake_sku_hunt_{STAMP}.json"

HUB = "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton.html"
MUST = ("7-5-ton", "npr-n75")


def keep(url: str) -> bool:
    u = (url or "").lower()
    if "ks-international.com" not in u:
        return False
    path = urlparse(u).path.lower()
    if "trooper" in path or "d-max" in path or "mu-x" in path:
        return False
    return any(k in path for k in MUST)


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    profile = Path(tempfile.mkdtemp(prefix="ks_anon_n75_"))
    notes: list[str] = []
    model_urls: set[str] = set()
    brake_cats: set[str] = set()
    product_urls: list[str] = []
    seen: set[str] = set()
    rows: list[dict] = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            channel="chrome",
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="en-GB",
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(45_000)
        page.goto(HUB, wait_until="domcontentloaded")
        brake_cats.add(
            "https://www.ks-international.com/isuzu-4x4-and-truck-parts/"
            "isuzu-truck-parts/isuzu-7-5-ton/"
            "isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake.html"
        )
        time.sleep(2)
        hrefs = page.eval_on_selector_all("a", "els => els.map(e => e.href).filter(Boolean)")
        for h in hrefs:
            h0 = h.split("?")[0]
            if keep(h0):
                model_urls.add(h0)
                if "/brake" in h0.lower():
                    brake_cats.add(h0)
        notes.append(f"hub_status={page.title()!r} url={page.url}")
        notes.append(f"model_urls={len(model_urls)}")

        n75_seed = (
            "https://www.ks-international.com/isuzu-4x4-and-truck-parts/"
            "isuzu-truck-parts/isuzu-7-5-ton/"
            "isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on.html"
        )
        hubs = [n75_seed, HUB] + [
            u
            for u in sorted(model_urls)
            if u.rstrip("/").endswith(".html")
            and u.rstrip("/").count("/") <= 7
        ]
        for hub in hubs[:20]:
            if "/brake" not in hub.lower() and hub.count("/") > 8:
                continue
            try:
                page.goto(hub, wait_until="domcontentloaded")
            except PwTimeout:
                notes.append(f"timeout:{hub}")
                continue
            time.sleep(0.8)
            for h in page.eval_on_selector_all("a", "els => els.map(e => e.href).filter(Boolean)"):
                h0 = h.split("?")[0]
                if keep(h0) and "/brake" in h0.lower():
                    brake_cats.add(h0)
            notes.append(f"visited_hub {page.url} brakes_so_far={len(brake_cats)}")

        notes.append(f"brake_cats={len(brake_cats)}")
        # prefer pages that look like category listings (path ends brakes.html or brakes/xxx.html)
        cats = sorted(brake_cats)
        for cat in cats[:30]:
            try:
                page.goto(cat, wait_until="domcontentloaded")
            except PwTimeout:
                continue
            time.sleep(0.9)
            pages = 0
            while pages < 8:
                pages += 1
                for h in p1.listing_product_hrefs(page):
                    if not keep(h):
                        continue
                    if h in seen:
                        continue
                    seen.add(h)
                    product_urls.append(h)
                nxt = p1.next_listing_url(page)
                if not nxt:
                    break
                page.goto(nxt, wait_until="domcontentloaded")
                time.sleep(0.7)

        notes.append(f"products={len(product_urls)}")

        def rank(u: str) -> int:
            lu = u.lower()
            if "pad" in lu:
                return 0
            if "disc" in lu:
                return 1
            return 2

        for url in sorted(product_urls, key=rank)[:100]:
            try:
                page.goto(url, wait_until="domcontentloaded")
            except PwTimeout:
                continue
            time.sleep(0.8 + random.random() * 0.4)
            rec = p1.extract_pdp(page)
            rec["status"] = "ok"
            rows.append(rec)
            if rec.get("matched_isze_oem"):
                notes.append(f"HIT {rec['matched_isze_oem']} {rec['ks_sku']} {url}")

        context.close()

    fields = [
        "url", "ks_sku", "title", "line", "price_ex_vat_gbp", "price_inc_vat_gbp",
        "stock", "oem_on_page", "matched_isze_oem", "status", "scraped_at",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    hits = [r for r in rows if r.get("matched_isze_oem")]
    payload = {
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "hub": HUB,
        "n_pdps": len(rows),
        "n_hits": len(hits),
        "hits": hits,
        "notes": notes,
        "brake_cats_sample": sorted(brake_cats)[:40],
        "csv": str(CSV_PATH),
    }
    JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {CSV_PATH} n={len(rows)} hits={len(hits)}")
    for n in notes[:40]:
        print(n)


if __name__ == "__main__":
    main()
