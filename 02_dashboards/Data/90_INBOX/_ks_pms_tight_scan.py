"""Tight KS PMS crawl — explicit category URLs + PN search. Incremental JSONL."""
from __future__ import annotations

import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ks_pms_scan_20260818")
OUT.mkdir(parents=True, exist_ok=True)
PROD_JL = OUT / "products.jsonl"
PN_JL = OUT / "pn_search.jsonl"

BASE = "https://www.ks-international.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.ks-international.com/",
}

# Campaign vehicles + the 4JJ1 page Duncan was sharing.
CATS = [
    ("N75_4HK1_2013on", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/filters.html"),
    ("N75_4HK1_2013on", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/fuel.html"),
    ("N75_4HK1_2013on", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake.html"),
    ("N75_4HK1_2013on", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/clutch-flywheel.html"),
    ("N75_4JJ1_2014", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/filters.html"),
    ("N75_4JJ1_2014", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/fuel.html"),
    ("N75_4JJ1_2014", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/brake.html"),
    ("N75_4JJ1_2014", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/clutch-flywheel.html"),
    ("N75_4JJ1_2014", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/brake/front-brake.html"),
    ("N75_NPR88_4JZ1", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr88-7-5-4jz1tc/filters.html"),
    ("N75_NPR88_4JZ1", "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr88-7-5-4jz1tc.html"),
]

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
]


def log(msg: str) -> None:
    print(msg, flush=True)


def abs_url(href: str) -> str:
    if not href:
        return ""
    return urljoin(BASE + "/", href.split("?")[0].split("#")[0])


def parse_products(html: str, page_url: str) -> list[dict]:
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
        price_ex_el = item.select_one(".price-excluding-tax .price")
        if not price_ex_el:
            price_ex_el = item.select_one("[data-price-type='finalPrice'] .price")
        price_inc_el = item.select_one(".price-including-tax .price")
        price_ex = price_inc = None
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
        oos = "out of stock" in text.lower() or bool(item.select_one(".stock.unavailable, .out-of-stock"))
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


def child_under(html: str, parent_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    stem = parent_url.replace(".html", "")
    out, seen = [], set()
    for a in soup.select("a"):
        href = abs_url(a.get("href") or "")
        name = a.get_text(" ", strip=True)
        if not href.endswith(".html") or href in seen or href == parent_url:
            continue
        if not href.startswith(stem + "/"):
            continue
        rest = href[len(stem) + 1:].replace(".html", "")
        if rest.count("/") > 1:
            continue
        blob = f"{name} {rest}".lower()
        if any(k in blob for k in (
            "filter", "fuel", "oil", "air", "brake", "clutch", "pad", "disc",
            "rotor", "caliper", "cabin", "pollen", "urea", "def", "adblue",
            "flywheel", "front", "rear",
        )):
            seen.add(href)
            out.append((name or rest, href))
    return out


def next_page(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    a = soup.select_one("a.action.next, li.pages-item-next a")
    if a and a.get("href"):
        return abs_url(a["href"])
    return None


def fetch(session, url: str) -> str:
    r = session.get(url, timeout=25)
    r.raise_for_status()
    return r.text


def walk(session, model: str, cat_url: str, products: list, visited: set) -> None:
    queue = [(cat_url.split("/")[-1].replace(".html", ""), cat_url)]
    while queue:
        cat, url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        log(f"CAT {model} {cat} {url}")
        try:
            html = fetch(session, url)
        except Exception as e:
            log(f"  ERR {e}")
            continue
        time.sleep(random.uniform(0.25, 0.55))
        rows = parse_products(html, url)
        if rows:
            for r in rows:
                r["model"] = model
                r["category"] = cat
                products.append(r)
                PROD_JL.open("a", encoding="utf-8").write(json.dumps(r) + "\n")
            log(f"  {len(rows)} products")
            nxt = next_page(html)
            page_i = 1
            while nxt and page_i < 8:
                page_i += 1
                if nxt in visited:
                    break
                visited.add(nxt)
                try:
                    html2 = fetch(session, nxt)
                except Exception as e:
                    log(f"  ERR page {e}")
                    break
                time.sleep(random.uniform(0.25, 0.55))
                rows2 = parse_products(html2, nxt)
                for r in rows2:
                    r["model"] = model
                    r["category"] = cat
                    products.append(r)
                    PROD_JL.open("a", encoding="utf-8").write(json.dumps(r) + "\n")
                log(f"  page{page_i} {len(rows2)} products")
                nxt = next_page(html2)
        else:
            kids = child_under(html, url)
            log(f"  no products, {len(kids)} child cats")
            for name, href in kids:
                if href not in visited:
                    queue.append((name, href))


def main() -> int:
    if PROD_JL.exists():
        PROD_JL.unlink()
    if PN_JL.exists():
        PN_JL.unlink()
    session = requests.Session()
    session.headers.update(HEADERS)
    products: list[dict] = []
    visited: set[str] = set()
    for model, url in CATS:
        walk(session, model, url, products, visited)

    pn_hits = []
    for pn in PNS:
        url = f"{BASE}/catalogsearch/result/?q={pn}"
        log(f"PN {pn}")
        rec = {"pn": pn, "search_url": url, "products": []}
        try:
            html = fetch(session, url)
            time.sleep(random.uniform(0.25, 0.5))
            rec["products"] = parse_products(html, url)
            soup = BeautifulSoup(html, "html.parser")
            el = soup.select_one(".toolbar-amount")
            rec["toolbar"] = el.get_text(" ", strip=True) if el else ""
            rec["n_products"] = len(rec["products"])
        except Exception as e:
            rec["err"] = str(e)
            rec["n_products"] = 0
        pn_hits.append(rec)
        PN_JL.open("a", encoding="utf-8").write(json.dumps(rec) + "\n")

    meta = {
        "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_products": len(products),
        "n_pn": len(pn_hits),
        "n_pages": len(visited),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (OUT / "products.json").write_text(json.dumps(products, indent=2), encoding="utf-8")
    (OUT / "pn_search.json").write_text(json.dumps(pn_hits, indent=2), encoding="utf-8")
    log(f"DONE products={len(products)} pn={len(pn_hits)} pages={len(visited)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
