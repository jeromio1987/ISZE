"""Focused KS fetch for ITUK/ISZE PMS PNs + three vehicle trees. Polite delay."""
from __future__ import annotations

import csv
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

OUT = Path(__file__).resolve().parent
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
BASE = "https://www.ks-international.com"
SEARCH = BASE + "/catalogsearch/result/?q={pn}"

ITUK_37 = [
    "8983282071", "8983282070", "1876102890", "5876101170", "5876100310",
    "8975425050", "8975425400", "1876102860",
    "8981235322", "8982157230", "8981772710", "5876102500",
    "8982447940",
    "8981649171", "5876100920", "8970388314", "5876101040",
    "8975439050", "8983104491", "8983104490", "8983572930", "8975425390",
    "8983752250", "8980374810", "5876101570", "8980318470", "8980179710",
    "8976659910", "8976739570",
    "8982169220", "5876102380", "5876170050",
    "8978283700", "8982551391", "5876100771", "8980400932", "5876100910",
]
ISZE_14 = [
    "8983282070", "1876102890", "8975425400", "1876102860",
    "8981772710", "5876102500", "8982447940", "8982169220",
    "5876102320", "8981649171", "8970388314", "1313100120",
    "8983507161", "1876102341",
]
EXTRA = ["8970622940", "8971482700", "8980370110", "8982035990", "8971686340"]

TREES = {
    "4hk1_filters": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/filters.html",
    "4hk1_filters_oaf": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/filters/oil-air-fuel.html",
    "4hk1_front_brake": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake/front-brake.html",
    "4hk1_clutch": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/clutch-flywheel.html",
    "npr88_filters": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr88-7-5-4jz1tc/filters.html",
    "npr88_front_brake": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr88-7-5-4jz1tc/brake/front-brake.html",
    "npr88_clutch": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr88-7-5-4jz1tc/clutch-flywheel.html",
    "4jj1_filters": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/filters.html",
    "4jj1_front_brake": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/brake/front-brake.html",
    "4jj1_clutch": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/isuzu-npr-n75-150-4jj1tc-euro-vi-2014/clutch-flywheel.html",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def sleep():
    time.sleep(random.uniform(1.4, 2.4))


def parse_price(el) -> float | None:
    if not el:
        return None
    m = re.search(r"[\d,]+\.?\d*", el.get_text().replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group().replace(",", ""))
    except ValueError:
        return None


def parse_items(soup: BeautifulSoup, page_url: str) -> list[dict]:
    products = []
    for item in soup.select(".product-item"):
        name_a = item.select_one(".product-item-name a") or item.select_one("a.product-item-link")
        name_text = name_a.get_text(strip=True) if name_a else ""
        href = name_a.get("href") if name_a else None
        if href:
            href = urljoin(BASE, href)
        sku_el = item.select_one(".product-sku, .sku")
        sku = ""
        if sku_el:
            sku = sku_el.get_text(strip=True).replace("SKU:", "").strip()
        else:
            m = re.search(r"SKU:\s*(\S+)", item.get_text())
            sku = m.group(1) if m else ""
        price_ex_el = item.select_one(".price-excluding-tax .price") or item.select_one(
            "[data-price-type='finalPrice'] .price"
        )
        price_ex = parse_price(price_ex_el)
        item_text = item.get_text(" ")
        is_genuine = (
            "GENUINE" in name_text.upper()
            or "GENUINE OEM" in item_text.upper()
            or bool(item.select_one('.genuine-badge, [class*="genuine"]'))
        )
        brand = ""
        brand_el = item.select_one(".product-item-brand, .brand, [class*='brand']")
        if brand_el:
            brand = brand_el.get_text(strip=True)
        if "TBK" in (name_text + " " + item_text).upper():
            brand = brand or "TBK"
        oos = bool(
            item.select_one(".stock.unavailable, .out-of-stock")
            or "out of stock" in item_text.lower()
        )
        products.append({
            "name": name_text,
            "sku": sku,
            "url": href,
            "price_ex_gbp": price_ex,
            "is_genuine": is_genuine,
            "brand": brand,
            "in_stock": not oos,
            "page_url": page_url,
        })
    return products


def fetch(url: str) -> tuple[int, str]:
    r = SESSION.get(url, timeout=40)
    return r.status_code, r.text


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    tree_products: dict[str, list] = {}
    for key, url in TREES.items():
        print(f"TREE {key}", flush=True)
        try:
            code, html = fetch(url)
            soup = BeautifulSoup(html, "html.parser")
            items = parse_items(soup, url)
            tree_products[key] = {
                "url": url,
                "status": code,
                "n_items": len(items),
                "items": items,
            }
            print(f"  {code} items={len(items)}", flush=True)
        except Exception as e:
            tree_products[key] = {"url": url, "status": "error", "error": str(e), "items": []}
            print(f"  ERR {e}", flush=True)
        sleep()

    pns = list(dict.fromkeys(ITUK_37 + ISZE_14 + EXTRA))
    pn_search = []
    for pn in pns:
        url = SEARCH.format(pn=pn)
        print(f"PN {pn}", flush=True)
        rec = {"pn": pn, "url": url, "status": None, "result_count": 0, "items": []}
        try:
            code, html = fetch(url)
            rec["http"] = code
            soup = BeautifulSoup(html, "html.parser")
            count_el = soup.select_one(".toolbar-amount")
            result_count = 0
            if count_el:
                m = re.search(r"(\d+)", count_el.get_text())
                if m:
                    result_count = int(m.group(1))
            items = parse_items(soup, url)
            rec["result_count"] = result_count or len(items)
            rec["items"] = items
            rec["status"] = "ok" if items else "no_hit"
            print(f"  {code} hits={len(items)} count={rec['result_count']}", flush=True)
        except Exception as e:
            rec["status"] = "error"
            rec["error"] = str(e)
            print(f"  ERR {e}", flush=True)
        pn_search.append(rec)
        sleep()

    payload = {
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "fx_gbp_eur": 1.17,
        "trees": tree_products,
        "pn_search": pn_search,
        "ituk_37": ITUK_37,
        "isze_14": ISZE_14,
    }
    (OUT / "products.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUT / "pn_search.json").write_text(json.dumps(pn_search, indent=2), encoding="utf-8")

    rows = []
    for rec in pn_search:
        gen = [i for i in rec["items"] if i.get("is_genuine") and i.get("price_ex_gbp") is not None]
        iam = [i for i in rec["items"] if (not i.get("is_genuine")) and i.get("price_ex_gbp") is not None]
        g0 = min(gen, key=lambda x: x["price_ex_gbp"]) if gen else None
        a0 = min(iam, key=lambda x: x["price_ex_gbp"]) if iam else None
        tbk = next((i for i in iam if "TBK" in (i.get("brand", "") + i.get("name", "")).upper()), None)
        rows.append({
            "pn": rec["pn"],
            "status": rec["status"],
            "n_items": len(rec["items"]),
            "search_url": rec["url"],
            "gen_gbp": g0["price_ex_gbp"] if g0 else "",
            "gen_url": (g0 or {}).get("url") or "",
            "gen_name": (g0 or {}).get("name") or "",
            "iam_gbp": a0["price_ex_gbp"] if a0 else "",
            "iam_url": (a0 or {}).get("url") or "",
            "iam_name": (a0 or {}).get("name") or "",
            "iam_brand": (a0 or {}).get("brand") or "",
            "tbk_gbp": tbk["price_ex_gbp"] if tbk else "",
            "tbk_url": (tbk or {}).get("url") or "",
            "tbk_name": (tbk or {}).get("name") or "",
        })
    with (OUT / "products.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["pn"])
        w.writeheader()
        w.writerows(rows)
    print("WROTE", OUT, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
