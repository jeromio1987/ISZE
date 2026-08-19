"""Pass 4: live N75 /brake.html (singular) PDPs — KS Magento truck taxonomy."""
from __future__ import annotations

import csv
import json
import random
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

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

SEEDS = [
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-nqr-4he1tc-1998-2003/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-nqr-4he1tc-euro-2-2003-2005/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2005-2008/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2008-11-2013/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-nlr87-rz4e-1-9ltr-hp-2016/brakes.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-grafter-n35-4jj1tc-2010/isuzu-n35-150-euro-vi-twin-rear-wheel.html",
]
MAX_LISTING_PAGES = 8
MAX_PDPS = 160
NAV_TIMEOUT = 45_000


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    profile = Path(tempfile.mkdtemp(prefix="ks_anon_n75b_"))
    notes: list[str] = []
    cats: list[str] = []
    product_urls: list[str] = []
    seen_p: set[str] = set()
    rows: list[dict] = []
    cat_meta: list[dict] = []

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
                resp = page.goto(seed, wait_until="domcontentloaded")
                st = resp.status if resp else None
            except PwTimeout:
                cat_meta.append({"url": seed, "status": "timeout"})
                continue
            time.sleep(1.6)
            h1 = page.locator("h1").first.inner_text() if page.locator("h1").count() else ""
            n_prod = page.locator(".product-item").count()
            kids = page.eval_on_selector_all(
                "a",
                """els => {
                  const here = location.pathname.replace(/\\.html$/, '');
                  return [...new Set(els.map(e => (e.href||'').split('#')[0].split('?')[0])
                    .filter(h => h.includes(here) && /\\/brake/i.test(h)))];
                }""",
            )
            cat_meta.append(
                {
                    "url": seed,
                    "final": page.url,
                    "http": st,
                    "h1": h1[:120],
                    "n_product_item": n_prod,
                    "child_brake": kids[:20],
                }
            )
            print(f"SEED http={st} n_item={n_prod} {h1[:80]}", flush=True)
            cats.append(seed)
            for k in kids:
                if k.endswith(".html") and k not in cats:
                    cats.append(k)

        notes.append(f"cats={len(cats)}")

        for cat in cats:
            try:
                page.goto(cat, wait_until="domcontentloaded")
            except PwTimeout:
                notes.append(f"timeout_cat:{cat}")
                continue
            time.sleep(1.1)
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
                time.sleep(0.8 + random.random())

        notes.append(f"listing_product_urls={len(product_urls)}")
        print(f"listing_product_urls={len(product_urls)} cats={len(cats)}", flush=True)

        def p_rank(u: str) -> int:
            lu = u.lower()
            if "pad" in lu:
                return 0
            if "disc" in lu:
                return 1
            if "shoe" in lu or "lining" in lu:
                return 2
            return 3

        product_urls = sorted(product_urls, key=p_rank)[:MAX_PDPS]
        for i, url in enumerate(product_urls, 1):
            print(f"PDP {i}/{len(product_urls)}", flush=True)
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
            time.sleep(0.75 + random.random())
            rec = p1.extract_pdp(page)
            rec["status"] = "ok"
            rows.append(rec)
            if rec.get("matched_isze_oem"):
                notes.append(
                    f"HIT {rec['matched_isze_oem']} sku={rec['ks_sku']} exGBP={rec['price_ex_vat_gbp']} {rec['title'][:80]}"
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
        "note": "KS truck N75 uses /brake.html not /brakes.html (latter 404)",
        "target_oems": sorted(p1.TARGET_OEMS),
        "cat_meta": cat_meta,
        "n_pdps": len(rows),
        "n_hits": len(hits),
        "hits": hits,
        "notes": notes,
        "csv": str(CSV_PATH),
    }
    JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {CSV_PATH} n={len(rows)} hits={len(hits)}")
    for n in notes:
        print(n[:400])


if __name__ == "__main__":
    main()
