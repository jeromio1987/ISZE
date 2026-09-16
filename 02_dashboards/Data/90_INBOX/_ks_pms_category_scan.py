"""One-shot KS International category crawl for N-series PMS parts.

Intake only: writes JSON/CSV under 01_data/90_INBOX. Does not rebuild dashboards.
Polite delays. Uses the same User-Agent as 04_tools/autodoc_scraper/ks_scraper.py.
"""
from __future__ import annotations

import csv
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ks_pms_scan_20260818")
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://www.ks-international.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.ks-international.com/",
}

# PMS-relevant category name fragments (lowercased).
PMS_KEYS = (
    "filter", "oil", "fuel", "air", "brake", "clutch", "urea", "adblue", "def",
    "cabin", "pollen", "blower", "coolant", "water pump", "belt", "wiper",
    "service", "maintenance", "pad", "disc", "rotor", "shoe", "caliper",
    "sedimenter", "engine",
)

# Skip body/electrical clutter even if they sit under a vehicle.
SKIP_KEYS = (
    "body", "panel", "bumper", "light", "lamp", "mirror", "glass", "door",
    "cab ", "interior trim", "seat", "electrical wiring", "harness",
)

SEED_PAGES = [
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton.html",
]

DUNCAN_PNS = [
    # NPR75 4HK1
    "8983282071", "8983282070", "1876102890", "5876101170", "5876100310",
    "8975425050", "8975425400", "1876102860",
    "8981235322", "8982157230", "8981772710", "5876102500",
    "8982447940",
    "8981649171", "5876100920", "8970388314", "5876101040",
    # NPR88 4JZ1
    "8975439050", "8983104491", "8983104490", "8983572930",
    "8975425390", "8983752250", "8980374810", "5876101570",
    "8980318470", "8980179710",
    "8976659910", "8976739570",
    "8982169220", "5876102380", "5876170050",
    "8978283700", "8982551391", "5876100771", "8980400932", "5876100910",
    # Jerome extras
    "8983507161", "1876102341", "8981919560", "8982488951",
    "5876102320", "1313100120", "8981649181",
    # N35 (phase 2, still scan)
    "8982705240", "5876150530", "8975080920", "8975080932",
    "8981596930", "5876150170", "8981941190", "5876150240",
    "8983214130", "5876102900", "8975095290",
    "8982169210", "8973319320", "5878320440",
    "8983753331", "8982831940",
    "8977903031", "8976643531", "8978293170",
]


def sleep():
    time.sleep(random.uniform(0.7, 1.6))


def get(session: requests.Session, url: str) -> str:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def abs_url(href: str) -> str:
    if not href:
        return ""
    return urljoin(BASE + "/", href.split("?")[0])


def is_pms_cat(name: str, href: str) -> bool:
    blob = f"{name} {href}".lower()
    if any(k in blob for k in SKIP_KEYS) and not any(k in blob for k in ("filter", "brake", "clutch")):
        return False
    return any(k in blob for k in PMS_KEYS)


def parse_products(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for item in soup.select(".product-item, li.product-item, .product.details"):
        name_el = item.select_one(".product-item-name a, a.product-item-link, .product-item-name")
        name = name_el.get_text(" ", strip=True) if name_el else ""
        href = abs_url(name_el.get("href", "") if name_el else "")
        sku_el = item.select_one(".product-sku, .sku")
        sku = ""
        if sku_el:
            sku = re.sub(r"(?i)sku:?\s*", "", sku_el.get_text(" ", strip=True)).strip()
        else:
            m = re.search(r"SKU:\s*(\S+)", item.get_text(" ", strip=True))
            sku = m.group(1) if m else ""
        brand_el = item.select_one(".product-item-brand, .brand, [class*='brand']")
        brand = brand_el.get_text(" ", strip=True) if brand_el else ""
        price_ex_el = item.select_one(".price-excluding-tax .price, [data-price-type='finalPrice'] .price")
        price_inc_el = item.select_one(".price-including-tax .price")
        price_ex = None
        price_inc = None
        if price_ex_el:
            m = re.search(r"[\d,]+\.?\d*", price_ex_el.get_text().replace(",", ""))
            if m:
                price_ex = float(m.group())
        if price_inc_el:
            m = re.search(r"[\d,]+\.?\d*", price_inc_el.get_text().replace(",", ""))
            if m:
                price_inc = float(m.group())
        text = item.get_text(" ", strip=True)
        is_genuine = ("GENUINE" in name.upper()) or ("GENUINE OEM" in text.upper())
        oos = bool(item.select_one(".stock.unavailable, .out-of-stock")) or "out of stock" in text.lower()
        # Brand often sits in parentheses in the title: FRONT BRAKE PAD SET (TBK)
        if not brand:
            m = re.search(r"\(([^)]+)\)\s*$", name)
            if m:
                brand = m.group(1).strip()
        if not brand and is_genuine:
            brand = "GENUINE OEM"
        if not name:
            continue
        rows.append({
            "name": name,
            "sku": sku,
            "brand": brand,
            "price_ex_gbp": price_ex,
            "price_inc_gbp": price_inc,
            "is_genuine": is_genuine,
            "in_stock": not oos,
            "product_url": href,
            "listing_url": page_url,
        })
    return rows


def category_links(html: str, page_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    found = []
    seen = set()
    for a in soup.select("a"):
        href = a.get("href") or ""
        name = a.get_text(" ", strip=True)
        if not href or not name:
            continue
        url = abs_url(href)
        if urlparse(url).netloc.replace("www.", "") != "ks-international.com":
            continue
        if not url.endswith(".html"):
            continue
        if url in seen:
            continue
        seen.add(url)
        found.append((name, url))
    return found


def next_page(html: str, page_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    a = soup.select_one("a.action.next, li.pages-item-next a, a[title='Next']")
    if a and a.get("href"):
        return abs_url(a["href"])
    return None


def main() -> int:
    session = requests.Session()
    session.headers.update(HEADERS)
    log = []
    products: list[dict] = []
    visited = set()
    cat_queue: list[tuple[str, str, str]] = []  # model, cat_name, url

    # 1) seed vehicle model URLs
    models = []
    for seed in SEED_PAGES:
        print("SEED", seed)
        html = get(session, seed)
        sleep()
        for name, url in category_links(html, seed):
            if "/isuzu-truck-parts/" in url and url != seed:
                # vehicle or subcategory under tonnage
                models.append({"from": seed, "name": name, "url": url})
        Path(OUT / "seed_html").mkdir(exist_ok=True)
        (OUT / "seed_html" / (urlparse(seed).path.strip("/").replace("/", "_") + ".html")).write_text(html, encoding="utf-8")

    (OUT / "models.json").write_text(json.dumps(models, indent=2), encoding="utf-8")
    print(f"models discovered: {len(models)}")

    # 2) for each vehicle page, collect PMS category links (one more level, then products)
    vehicle_pages = [m for m in models if any(k in m["url"] for k in (
        "n75", "npr", "nqr", "n35", "nlr", "4hk1", "4jz1", "4jj1", "rz4e", "7-5-ton", "3-5-ton"
    ))]
    # Prefer current parc generations; still keep older 7.5T for completeness
    for m in vehicle_pages:
        url = m["url"]
        if url in visited:
            continue
        visited.add(url)
        print("VEHICLE", m["name"][:80], url)
        try:
            html = get(session, url)
        except Exception as e:
            log.append({"url": url, "err": str(e)})
            continue
        sleep()
        for cname, curl in category_links(html, url):
            if curl == url:
                continue
            # stay under this vehicle path
            if urlparse(url).path.rstrip(".html") not in curl and "/isuzu-truck-parts/" in curl:
                # child category typically extends parent path
                if not curl.startswith(url.replace(".html", "")):
                    continue
            if is_pms_cat(cname, curl):
                cat_queue.append((m["name"], cname, curl))

    # unique cats
    seen_c = set()
    uniq = []
    for t in cat_queue:
        if t[2] in seen_c:
            continue
        seen_c.add(t[2])
        uniq.append(t)
    cat_queue = uniq
    (OUT / "categories.json").write_text(json.dumps(
        [{"model": a, "cat": b, "url": c} for a, b, c in cat_queue], indent=2
    ), encoding="utf-8")
    print(f"PMS categories: {len(cat_queue)}")

    # 3) walk categories (and one more child level if still a category page)
    to_walk = list(cat_queue)
    walked = set()
    while to_walk:
        model, cat, url = to_walk.pop(0)
        if url in walked:
            continue
        walked.add(url)
        print("CAT", cat[:60], url)
        page = url
        page_i = 0
        while page and page_i < 8:
            page_i += 1
            try:
                html = get(session, page)
            except Exception as e:
                log.append({"url": page, "err": str(e)})
                break
            sleep()
            rows = parse_products(html, page)
            if rows:
                for r in rows:
                    r["model"] = model
                    r["category"] = cat
                    products.append(r)
                nxt = next_page(html, page)
                page = nxt
                continue
            # maybe still a category index
            children = 0
            for cname, curl in category_links(html, page):
                if curl in walked or curl == page:
                    continue
                if not is_pms_cat(cname, curl):
                    continue
                if page.rstrip(".html") not in curl and not curl.startswith(page.replace(".html", "")):
                    continue
                to_walk.append((model, f"{cat} / {cname}", curl))
                children += 1
            if children == 0:
                break
            page = None

    # 4) PN search for Duncan/Jerome list
    pn_hits = []
    for pn in DUNCAN_PNS:
        url = f"{BASE}/catalogsearch/result/?q={pn}"
        print("PN", pn)
        try:
            html = get(session, url)
        except Exception as e:
            pn_hits.append({"pn": pn, "url": url, "err": str(e)})
            continue
        sleep()
        rows = parse_products(html, url)
        soup = BeautifulSoup(html, "html.parser")
        count_el = soup.select_one(".toolbar-amount")
        count = count_el.get_text(" ", strip=True) if count_el else ""
        pn_hits.append({
            "pn": pn,
            "url": url,
            "toolbar": count,
            "n_products": len(rows),
            "products": rows,
        })

    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "scraped_at_utc": ts,
        "n_products_category": len(products),
        "n_pn_searches": len(pn_hits),
        "errors": log,
    }
    (OUT / "meta.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUT / "products.json").write_text(json.dumps(products, indent=2), encoding="utf-8")
    (OUT / "pn_search.json").write_text(json.dumps(pn_hits, indent=2), encoding="utf-8")

    fields = [
        "model", "category", "name", "sku", "brand", "is_genuine", "in_stock",
        "price_ex_gbp", "price_inc_gbp", "product_url", "listing_url",
    ]
    with (OUT / "products.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in products:
            w.writerow(r)

    print("DONE", OUT)
    print("products", len(products), "pn_searches", len(pn_hits), "errors", len(log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
