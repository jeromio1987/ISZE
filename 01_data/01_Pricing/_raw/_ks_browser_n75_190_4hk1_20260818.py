"""Pass 4: N75 190 4HK1 front/rear brake PDPs only (ITUK-class)."""
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
CSV_PATH = OUT_DIR / "ks_catalog_n75_190_4hk1_brake_sku_hunt_20260818.csv"
JSON_PATH = OUT_DIR / "ks_catalog_n75_190_4hk1_brake_sku_hunt_20260818.json"

CATS = [
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake/front-brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake/rear-brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2008-11-2013/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2008-11-2013/brake/front-brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2008-11-2013/brake/rear-brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2005-2008/brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2005-2008/brake/front-brake.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2005-2008/brake/rear-brake.html",
]


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    profile = Path(tempfile.mkdtemp(prefix="ks_anon_4hk1_"))
    notes: list[str] = []
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
        for cat in CATS:
            try:
                page.goto(cat, wait_until="domcontentloaded")
            except PwTimeout:
                notes.append(f"timeout {cat}")
                continue
            time.sleep(1.2)
            notes.append(f"cat title={page.title()!r} url={page.url}")
            extra = page.eval_on_selector_all(
                "a",
                "els => els.map(e => e.href).filter(h => h && h.includes('/brake/'))",
            )
            for h in extra:
                h0 = h.split("?")[0]
                if h0.endswith(".html") and "n75-190" in h0 and h0 not in CATS:
                    if "/front-brake/" in h0 or "/rear-brake/" in h0 or "pad" in h0:
                        if h0 not in seen and "brake.html" not in h0.split("/")[-1]:
                            # likely PDP if slug not exactly front-brake.html
                            pass
            n_items = page.locator(".product-item").count()
            notes.append(f"  product-items={n_items}")
            for h in p1.listing_product_hrefs(page):
                if h in seen:
                    continue
                seen.add(h)
                product_urls.append(h)
            # Magento sometimes nests products only on child cats
            for h in extra:
                h0 = h.split("#")[0]
                if h0 in seen or h0 in CATS:
                    continue
                if "n75-190" not in h0:
                    continue
                if h0.endswith("/front-brake.html") or h0.endswith("/rear-brake.html"):
                    CATS.append(h0) if h0 not in CATS else None

        notes.append(f"products={len(product_urls)}")
        for url in product_urls:
            try:
                page.goto(url, wait_until="domcontentloaded")
            except PwTimeout:
                continue
            time.sleep(0.75 + random.random() * 0.4)
            rec = p1.extract_pdp(page)
            rec["status"] = "ok"
            rows.append(rec)
            if rec.get("matched_isze_oem"):
                notes.append(f"HIT {rec['matched_isze_oem']} {rec['ks_sku']}")
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
    JSON_PATH.write_text(
        json.dumps(
            {
                "started": started,
                "finished": datetime.now(timezone.utc).isoformat(),
                "n_pdps": len(rows),
                "n_hits": len(hits),
                "hits": hits,
                "notes": notes,
                "csv": str(CSV_PATH),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {CSV_PATH} n={len(rows)} hits={len(hits)}")
    for n in notes:
        print(n)


if __name__ == "__main__":
    main()
