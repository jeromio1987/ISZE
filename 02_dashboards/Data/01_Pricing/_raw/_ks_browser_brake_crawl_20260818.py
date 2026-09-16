"""One-shot: headed Chromium, empty profile, crawl KS brake PDPs.

Not requests/WebFetch. Does not write ks_results.csv or oem_peer_basket.
"""
from __future__ import annotations

import csv
import json
import random
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PwTimeout
from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).resolve().parent
STAMP = "20260818"
CSV_PATH = OUT_DIR / f"ks_catalog_brake_sku_hunt_{STAMP}.csv"
JSON_PATH = OUT_DIR / f"ks_catalog_brake_sku_hunt_{STAMP}.json"

HOME = "https://www.ks-international.com/"
TARGET_OEMS = {
    "8982447940",
    "8975056801",
    "8982169210",
    "8982169220",
    "8982488951",
    "8983767550",
}
MAX_LISTING_PAGES = 8
MAX_PDPS = 90
NAV_TIMEOUT = 45_000


def digits_only(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def oem_hits(text: str) -> list[str]:
    d = digits_only(text)
    hits = []
    for oem in TARGET_OEMS:
        if oem in d:
            hits.append(oem)
    return hits


def extract_pdp(page) -> dict:
    def txt(sel: str) -> str:
        loc = page.locator(sel).first
        try:
            if loc.count() and loc.is_visible(timeout=800):
                return loc.inner_text(timeout=1500).strip()
        except Exception:
            pass
        return ""

    title = txt("h1.page-title") or txt("h1") or page.title()
    sku = txt(".product.attribute.sku .value") or txt("[itemprop='sku']")
    if not sku:
        m = re.search(r"SKU:\s*(\S+)", page.inner_text("body")[:4000], re.I)
        sku = m.group(1) if m else ""

    price_ex = None
    price_ex_txt = txt(".price-excluding-tax .price")
    if price_ex_txt:
        m = re.search(r"[\d,]+\.?\d*", price_ex_txt.replace(",", ""))
        if m:
            try:
                price_ex = float(m.group())
            except ValueError:
                price_ex = None

    price_inc = None
    price_inc_txt = txt(".price-including-tax .price")
    if price_inc_txt:
        m = re.search(r"[\d,]+\.?\d*", price_inc_txt.replace(",", ""))
        if m:
            try:
                price_inc = float(m.group())
            except ValueError:
                price_inc = None

    body = page.inner_text("body")
    stock = ""
    if re.search(r"out of stock", body, re.I):
        stock = "out_of_stock"
    elif re.search(r"in stock", body, re.I):
        stock = "in_stock"
    avail = txt(".stock.available")
    unavail = txt(".stock.unavailable")
    if unavail:
        stock = "out_of_stock"
    elif avail:
        stock = "in_stock"

    title_u = (title or "").upper()
    genuine = "GENUINE" in title_u or "GENUINE OEM" in body[:2500].upper()
    line = "genuine" if genuine else "aftermarket"

    extra = ""
    for sel in (
        "#product-attribute-specs-table",
        ".additional-attributes",
        ".product.attribute.oem",
        ".product.info.detailed",
    ):
        chunk = txt(sel)
        if chunk:
            extra += "\n" + chunk

    search_blob = f"{title}\n{sku}\n{extra}\n{body[:8000]}"
    hits = oem_hits(search_blob)

    oem_field = ""
    m_oem = re.search(
        r"OEM Part Number[:\s]+([0-9\-,\s/]+)",
        search_blob,
        re.I,
    )
    if m_oem:
        oem_field = re.sub(r"\s+", " ", m_oem.group(1)).strip()[:500]

    return {
        "url": page.url,
        "ks_sku": sku,
        "title": title[:300],
        "line": line,
        "price_ex_vat_gbp": price_ex,
        "price_inc_vat_gbp": price_inc,
        "stock": stock,
        "oem_on_page": oem_field,
        "matched_isze_oem": "|".join(hits),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def listing_product_hrefs(page) -> list[str]:
    hrefs = page.eval_on_selector_all(
        "a.product-item-link, .product-item-name a",
        "els => els.map(e => e.href).filter(Boolean)",
    )
    out, seen = [], set()
    for h in hrefs:
        if h in seen:
            continue
        seen.add(h)
        out.append(h)
    return out


def is_brake_url_or_label(s: str) -> bool:
    t = (s or "").lower()
    return any(
        k in t
        for k in (
            "brake",
            "brakes",
            "pad",
            "disc",
            "rotor",
            "lining",
            "shoe",
        )
    )


def collect_nav_brake_urls(page) -> list[str]:
    data = page.eval_on_selector_all(
        "a",
        """els => els.map(e => ({href: e.href || '', text: (e.innerText || '').trim()}))
           .filter(x => x.href && x.href.startsWith('http'))""",
    )
    urls, seen = [], set()
    for item in data:
        href = item.get("href") or ""
        text = item.get("text") or ""
        if "ks-international.com" not in href:
            continue
        path = urlparse(href).path.lower()
        if is_brake_url_or_label(text) or is_brake_url_or_label(path):
            if any(x in path for x in ("customer", "checkout", "cart", "account", "login")):
                continue
            if href in seen:
                continue
            seen.add(href)
            urls.append(href)
    return urls


def next_listing_url(page) -> str | None:
    href = page.eval_on_selector_all(
        "a.action.next, li.pages-item-next a, a[title='Next']",
        "els => (els.find(e => e.href) || {}).href || null",
    )
    return href or None


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    profile = Path(tempfile.mkdtemp(prefix="ks_anon_"))
    rows: list[dict] = []
    cat_urls: list[str] = []
    notes: list[str] = []

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
        page.goto(HOME, wait_until="domcontentloaded")
        time.sleep(2.5)

        # cookie banner if any
        for label in ("Accept", "I Agree", "Allow all", "Accept All"):
            btn = page.get_by_role("button", name=re.compile(label, re.I))
            try:
                if btn.count() and btn.first.is_visible(timeout=800):
                    btn.first.click()
                    time.sleep(0.8)
                    break
            except Exception:
                pass

        cat_urls = collect_nav_brake_urls(page)
        notes.append(f"homepage_brake_nav_links={len(cat_urls)}")

        # Prefer pad-like categories first
        def rank(u: str) -> int:
            lu = u.lower()
            if "pad" in lu:
                return 0
            if "brake" in lu:
                return 1
            return 2

        cat_urls = sorted(set(cat_urls), key=rank)
        product_urls: list[str] = []
        seen_p = set()

        for cat in cat_urls[:12]:
            try:
                page.goto(cat, wait_until="domcontentloaded")
            except PwTimeout:
                notes.append(f"timeout_cat:{cat}")
                continue
            time.sleep(1.2 + random.random())
            pages = 0
            while pages < MAX_LISTING_PAGES:
                pages += 1
                for h in listing_product_hrefs(page):
                    if h in seen_p:
                        continue
                    seen_p.add(h)
                    product_urls.append(h)
                nxt = next_listing_url(page)
                if not nxt or nxt == page.url:
                    break
                try:
                    page.goto(nxt, wait_until="domcontentloaded")
                except PwTimeout:
                    break
                time.sleep(1.0 + random.random())

        notes.append(f"listing_product_urls={len(product_urls)}")

        # Prefer pad/disc titles in the URL slug
        def p_rank(u: str) -> int:
            lu = u.lower()
            if "pad" in lu:
                return 0
            if "disc" in lu or "rotor" in lu:
                return 1
            if "brake" in lu:
                return 2
            return 3

        product_urls = sorted(product_urls, key=p_rank)[:MAX_PDPS]

        for i, url in enumerate(product_urls, 1):
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
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "status": "timeout",
                    }
                )
                continue
            time.sleep(0.9 + random.random())
            rec = extract_pdp(page)
            rec["status"] = "ok"
            rows.append(rec)
            if rec.get("matched_isze_oem"):
                notes.append(f"HIT {rec['matched_isze_oem']} sku={rec['ks_sku']} {url}")

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
        "home": HOME,
        "session": "playwright_chromium_fresh_user_data_dir (IDE browser MCP tabs would not persist)",
        "target_oems": sorted(TARGET_OEMS),
        "category_urls_sample": cat_urls[:20],
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
