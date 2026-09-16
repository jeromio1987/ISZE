"""Page 2+ of N75.190 11-2013-on front/rear brake listings."""
from __future__ import annotations

import csv
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright
import importlib.util

_p1 = Path(__file__).with_name("_ks_browser_brake_crawl_20260818.py")
spec = importlib.util.spec_from_file_location("ks_p1", _p1)
p1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p1)

OUT = Path(__file__).resolve().parent / "ks_catalog_n75_190_2013on_brake_p2_20260818.csv"
JSONP = OUT.with_suffix(".json")
CATS = [
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake/front-brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake/rear-brake.html",
]


def main() -> None:
    profile = Path(tempfile.mkdtemp(prefix="ks_anon_p2_"))
    seen: set[str] = set()
    urls: list[str] = []
    rows: list[dict] = []
    notes: list[str] = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            channel="chrome",
            headless=False,
            locale="en-GB",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for cat in CATS:
            page.goto(cat, wait_until="domcontentloaded")
            time.sleep(1.2)
            pages = 0
            while pages < 6:
                pages += 1
                notes.append(f"{page.url} items={page.locator('.product-item').count()}")
                for h in p1.listing_product_hrefs(page):
                    if h not in seen:
                        seen.add(h)
                        urls.append(h)
                nxt = p1.next_listing_url(page)
                if not nxt:
                    break
                page.goto(nxt, wait_until="domcontentloaded")
                time.sleep(1.0)
        for url in urls:
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(0.7)
            rec = p1.extract_pdp(page)
            rec["status"] = "ok"
            rows.append(rec)
            if rec.get("matched_isze_oem"):
                notes.append(f"HIT {rec['matched_isze_oem']} {rec['ks_sku']}")
        ctx.close()
    fields = [
        "url", "ks_sku", "title", "line", "price_ex_vat_gbp", "price_inc_vat_gbp",
        "stock", "oem_on_page", "matched_isze_oem", "status", "scraped_at",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    hits = [r for r in rows if r.get("matched_isze_oem")]
    JSONP.write_text(
        json.dumps({"n": len(rows), "hits": hits, "notes": notes, "csv": str(OUT)}, indent=2),
        encoding="utf-8",
    )
    print(f"n={len(rows)} hits={len(hits)}")
    for n in notes:
        print(n)


if __name__ == "__main__":
    main()
