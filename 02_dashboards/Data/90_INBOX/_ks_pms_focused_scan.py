"""Focused KS crawl: PMS cats on N75 4HK1 / 4JJ1 / NPR88 + PN search with product URLs."""
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

VEHICLES = {
    "N75_4HK1_2013on": "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on.html",
    "N75_4JJ1_2014": "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014.html",
    "N75_NPR88_4JZ1": "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr88-7-5-4jz1tc.html",
    "N75_4HK1_2008_2013": "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-2008-11-2013.html",
}

PMS_SLUGS = (
    "filters", "fuel", "brake", "clutch-flywheel", "engine", "cooling-heating",
)

PNS = [
    "8983282071", "8983282070", "1876102890", "5876101170", "5876100310",
    "8975425050", "8975425400", "1876102860",
    "8981235322", "8982157230", "8981772710", "5876102500",
    "8982447940",
    "8981649171", "5876100920", "8970388314", "5876101040",
    "8975439050", "8983104491", "8983104490", "8983572930",
    "8975425390", "8983752250", "8980374810", "5876101570",
    "8980318470", "8980179710",
    "8976659910", "8976739570",
    "8982169220", "5876102380", "5876170050",
    "8978283700", "8982551391", "5876100771", "8980400932", "5876100910",
    "8983507161", "1876102341", "8981919560", "8982488951",
    "5876102320", "1313100120", "8981649181",
    "8982705240", "5876150530", "8975080920", "8975080932",
    "8981596930", "5876150170", "8981941190", "5876150240",
    "8983214130", "5876102900", "8975095290",
    "8982169210", "8973319320", "5878320440",
    "8983753331", "8982831940",
    "8977903031", "8976643531", "8978293170",
]


def sleep():
    time.sleep(random.uniform(0.35, 0.75))


def get(session, url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def abs_url(href):
    if not href:
        return ""
    return urljoin(BASE + "/", href.split("?")[0].split("#")[0])


def parse_products(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for item in soup.select(".product-item"):
        a = item.select_one("a.product-item-link, .product-item-name a")
        name = a.get_text(" ", strip=True) if a else ""
        href = abs_url(a.get("href") if a else "")
        sku_el = item.select_one(".product-sku")
        sku = ""
        if sku_el:
            sku = re.sub(r"(?i)sku:?\s*", "", sku_el.get_text(" ", strip=True)).strip()
        else:
            m = re.search(r"SKU:\s*(\S+)", item.get_text(" ", strip=True))
            sku = m.group(1) if m else ""
        price_ex_el = item.select_one(".price-excluding-tax .price") or item.select_one("[data-price-type='finalPrice'] .price")
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
        is_genuine = "GENUINE" in name.upper() or "GENUINE OEM" in text.upper()
        oos = bool(item.select_one(".stock.unavailable, .out-of-stock")) or "out of stock" in text.lower()
        brand = ""
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


def child_cats(html, parent_url):
    soup = BeautifulSoup(html, "html.parser")
    parent_stem = parent_url.replace(".html", "")
    out = []
    seen = set()
    for a in soup.select("a"):
        href = abs_url(a.get("href") or "")
        name = a.get_text(" ", strip=True)
        if not href.endswith(".html") or href in seen:
            continue
        if not href.startswith(parent_stem) or href == parent_url:
            continue
        # only one extra path segment preferred, but allow two
        rest = href[len(parent_stem):].strip("/")
        if rest.count("/") > 2:
            continue
        seen.add(href)
        out.append((name or rest, href))
    return out


def next_page(html):
    soup = BeautifulSoup(html, "html.parser")
    a = soup.select_one("a.action.next, li.pages-item-next a")
    if a and a.get("href"):
        return abs_url(a["href"])
    return None


def walk_listing(session, start_url, model, cat, products, visited):
    queue = [(cat, start_url)]
    while queue:
        cat_name, url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        print("  CAT", cat_name[:50], url.split("/")[-1])
        page = url
        pages = 0
        got_products = False
        html = None
        while page and pages < 10:
            pages += 1
            try:
                html = get(session, page)
            except Exception as e:
                print("   ERR", e)
                break
            sleep()
            rows = parse_products(html, page)
            if rows:
                got_products = True
                for r in rows:
                    r["model"] = model
                    r["category"] = cat_name
                    products.append(r)
                nxt = next_page(html)
                page = nxt
            else:
                break
        if html and not got_products:
            for cname, curl in child_cats(html, url):
                if curl not in visited:
                    queue.append((f"{cat_name} / {cname}", curl))


def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    products = []
    visited = set()
    errors = []

    for model, vurl in VEHICLES.items():
        print("VEHICLE", model)
        stem = vurl.replace(".html", "")
        # discover which PMS slugs exist
        try:
            html = get(session, vurl)
            sleep()
        except Exception as e:
            errors.append({"url": vurl, "err": str(e)})
            continue
        kids = child_cats(html, vurl)
        # also try constructed PMS slugs
        wanted = []
        for slug in PMS_SLUGS:
            wanted.append((slug, f"{stem}/{slug}.html"))
        for name, href in kids:
            blob = f"{name} {href}".lower()
            if any(s in blob for s in PMS_SLUGS + ("filter", "brake", "clutch", "fuel", "oil", "air", "pad", "disc")):
                wanted.append((name, href))
        seen_u = set()
        uniq = []
        for n, u in wanted:
            if u in seen_u:
                continue
            seen_u.add(u)
            uniq.append((n, u))
        for n, u in uniq:
            walk_listing(session, u, model, n, products, visited)

    pn_hits = []
    for pn in PNS:
        url = f"{BASE}/catalogsearch/result/?q={pn}"
        print("PN", pn)
        try:
            html = get(session, url)
        except Exception as e:
            pn_hits.append({"pn": pn, "search_url": url, "err": str(e), "products": []})
            continue
        sleep()
        rows = parse_products(html, url)
        soup = BeautifulSoup(html, "html.parser")
        count_el = soup.select_one(".toolbar-amount")
        pn_hits.append({
            "pn": pn,
            "search_url": url,
            "toolbar": count_el.get_text(" ", strip=True) if count_el else "",
            "n_products": len(rows),
            "products": rows,
        })

    ts = datetime.now(timezone.utc).isoformat()
    (OUT / "products.json").write_text(json.dumps(products, indent=2), encoding="utf-8")
    (OUT / "pn_search.json").write_text(json.dumps(pn_hits, indent=2), encoding="utf-8")
    (OUT / "meta.json").write_text(json.dumps({
        "scraped_at_utc": ts,
        "n_products": len(products),
        "n_pn": len(pn_hits),
        "n_visited": len(visited),
        "errors": errors,
        "vehicles": VEHICLES,
    }, indent=2), encoding="utf-8")
    fields = ["model", "category", "name", "sku", "brand", "is_genuine", "in_stock",
              "price_ex_gbp", "price_inc_gbp", "product_url", "listing_url"]
    with (OUT / "products.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(products)
    print("DONE products", len(products), "pn", len(pn_hits), "pages", len(visited))


if __name__ == "__main__":
    main()
