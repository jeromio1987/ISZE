"""Focused KS fetch for N35 / 3.5T vehicle trees + ITUK N35 PNs. Polite delay.

Not a full ks-international.com crawl. Never fetches isuzu-7-5-ton / N75 4HK1 / N75 4JJ1.
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

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

# ITUK pack slides 17–18 (N35.125 RZ4E + N35.150 4JZ1), unique, order preserved
ITUK_N35 = [
    "8982705240", "5876150530", "8975080920", "8975080932", "8981596930",
    "5876150170", "8981941190", "5876150240", "8983214130", "5876102900",
    "8975095290", "8982169210", "8982169220", "5876102380", "8973319320",
    "5878320440", "8983753331", "8982831940",
    "8975439050", "8983104491", "8977903031", "8975425390", "8983752250",
    "8976739570", "8976643531", "8978293170", "8980400932", "5876100910",
]

VEHICLE_ROOTS = {
    "nlr87_rz4e": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-nlr87-rz4e-1-9ltr-hp-2016.html",
    "npr88_3_5_4jz1": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-npr88-3-5-4jz1tc-2018-on.html",
    "n35_150_euro_vi_trw": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-grafter-n35-4jj1tc-2010/isuzu-n35-150-euro-vi-twin-rear-wheel.html",
    "nlr_4jj1_2014": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-nlr-4jj1tc-2014.html",
    "nnr_4jj1_2008": BASE + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-nnr-4jj11tc-2008.html",
}

FN_PATH = re.compile(
    r"/(filters|filter|brakes?|clutch-flywheel|clutch|fuel|oil-air-fuel|"
    r"front-brake|rear-brake|urea|adblue)(/|$|\.html)",
    re.I,
)
BLOCKED = re.compile(r"isuzu-7-5-ton|/npr-n75-|/npr88-7-5-", re.I)
MAX_PAGES = 6

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def sleep():
    time.sleep(random.uniform(1.4, 2.4))


def forbidden(url: str) -> bool:
    return bool(BLOCKED.search(url or ""))


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
        sku_el = item.select_one(".product-sku, .sku, [data-product-sku]")
        sku = ""
        if sku_el:
            sku = (
                sku_el.get("data-product-sku")
                or sku_el.get_text(strip=True).replace("SKU:", "").strip()
            )
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


def child_fn_links(soup: BeautifulSoup, page_url: str, root_prefix: str) -> list[str]:
    out = []
    seen = set()
    prefix = root_prefix.replace(".html", "")
    for a in soup.select("a[href]"):
        href = urljoin(page_url, a.get("href") or "").split("?")[0].split("#")[0]
        if forbidden(href):
            continue
        if not href.startswith(prefix):
            continue
        if href.rstrip("/") == prefix.rstrip("/") or href == root_prefix:
            continue
        if not FN_PATH.search(urlparse(href).path):
            continue
        if href not in seen:
            seen.add(href)
            out.append(href)
    return out


def next_page(soup: BeautifulSoup, page_url: str) -> str | None:
    a = soup.select_one("a.action.next, li.pages-item-next a")
    if not a or not a.get("href"):
        return None
    href = urljoin(page_url, a["href"])
    if forbidden(href):
        return None
    return href


def key_from_url(root_key: str, url: str) -> str:
    path = urlparse(url).path
    tail = path.split("/isuzu-3-5-ton/", 1)[-1].replace(".html", "").replace("/", "__")
    tail = re.sub(r"[^a-z0-9_]+", "_", tail.lower())
    return f"{root_key}__{tail}"[:120]


SUFFIXES = [
    "filters.html",
    "filters/oil-air-fuel.html",
    "brakes.html",
    "brake.html",
    "brakes/front-brake.html",
    "brake/front-brake.html",
    "brakes/rear-brake.html",
    "brake/rear-brake.html",
    "clutch-flywheel.html",
    "fuel.html",
]


def collect_tree_pages(root_key: str, root_url: str) -> tuple[list[str], list[dict]]:
    """Vehicle root only (once). Queue function children + common suffixes. Listings fetched later."""
    log: list[dict] = []
    pages: list[str] = []
    seen: set[str] = set()

    def add(url: str):
        if forbidden(url) or url in seen:
            return
        seen.add(url)
        pages.append(url)

    print(f"ROOT {root_key}", flush=True)
    try:
        code, html = fetch(root_url)
        soup = BeautifulSoup(html, "html.parser")
        kids = child_fn_links(soup, root_url, root_url) if code == 200 else []
        log.append({"url": root_url, "http": code, "role": "vehicle_root", "n_fn_children": len(kids)})
        print(f"  {code} children={len(kids)}", flush=True)
        if code == 200:
            for k in kids:
                add(k)
            stem = root_url.replace(".html", "")
            for suf in SUFFIXES:
                add(f"{stem}/{suf}")
        elif code == 404:
            print("  skip 404 root", flush=True)
    except Exception as e:
        log.append({"url": root_url, "http": "error", "error": str(e), "role": "vehicle_root"})
        print(f"  ERR {e}", flush=True)
    sleep()
    return pages, log


def fetch_listing(url: str, root_url: str) -> tuple[int, list[dict], list[str], list[str]]:
    """Fetch listing + pagination. Returns http, items, page urls, nested function links."""
    items: list[dict] = []
    page_urls = [url]
    nested: list[str] = []
    first_code = None
    current = url
    for i in range(MAX_PAGES):
        code, html = fetch(current)
        if first_code is None:
            first_code = code
        if code == 404:
            return code, [], page_urls, []
        if code != 200:
            return code, items, page_urls, nested
        soup = BeautifulSoup(html, "html.parser")
        if i == 0:
            nested = child_fn_links(soup, current, root_url)
        items.extend(parse_items(soup, current))
        nxt = next_page(soup, current)
        if not nxt or nxt in page_urls:
            break
        page_urls.append(nxt)
        current = nxt
        sleep()
    return first_code or 0, items, page_urls, nested


def real_search_items(items: list[dict]) -> list[dict]:
    """Drop Magento stubs: ok + blank name/url/£ is not a hit."""
    out = []
    for it in items:
        name = (it.get("name") or "").strip()
        url = (it.get("url") or "").strip()
        gbp = it.get("price_ex_gbp")
        if not name or not url or gbp is None:
            continue
        out.append(it)
    return out


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    discovery_log: list[dict] = []
    tree_products: dict[str, dict] = {}

    for root_key, root_url in VEHICLE_ROOTS.items():
        if forbidden(root_url):
            continue
        pages, log = collect_tree_pages(root_key, root_url)
        discovery_log.extend(log)
        for url in pages:
            if forbidden(url):
                continue
            key = key_from_url(root_key, url)
            if key in tree_products:
                continue
            print(f"LIST {key}", flush=True)
            try:
                code, items, page_urls, nested = fetch_listing(url, root_url)
                tree_products[key] = {
                    "url": url,
                    "status": code,
                    "n_items": len(items),
                    "items": items,
                    "page_urls": page_urls,
                    "vehicle": root_key,
                }
                print(f"  {code} items={len(items)} pages={len(page_urls)} nested={len(nested)}", flush=True)
                for nu in nested:
                    if nu not in pages and not forbidden(nu):
                        pages.append(nu)
            except Exception as e:
                tree_products[key] = {
                    "url": url,
                    "status": "error",
                    "error": str(e),
                    "items": [],
                    "vehicle": root_key,
                }
                print(f"  ERR {e}", flush=True)
            sleep()

    pns = list(dict.fromkeys(ITUK_N35))
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
            raw = parse_items(soup, url)
            items = real_search_items(raw)
            rec["result_count"] = result_count
            rec["n_raw_items"] = len(raw)
            rec["items"] = items
            rec["status"] = "ok" if items else "no_hit"
            print(f"  {code} real={len(items)} raw={len(raw)} toolbar={result_count}", flush=True)
        except Exception as e:
            rec["status"] = "error"
            rec["error"] = str(e)
            print(f"  ERR {e}", flush=True)
        pn_search.append(rec)
        sleep()

    finished = datetime.now(timezone.utc).isoformat()
    n_rows = sum(len(v.get("items") or []) for v in tree_products.values())
    payload = {
        "started": started,
        "finished": finished,
        "fx_gbp_eur": 1.17,
        "scope": "N35 / 3.5T vehicle trees only — not full KS site, not 7.5T/N75",
        "n35_ituk_pn_count": len(pns),
        "ituk_n35": pns,
        "vehicle_roots": VEHICLE_ROOTS,
        "discovery_log": discovery_log,
        "trees": tree_products,
        "pn_search": pn_search,
        "n_tree_pages": len(tree_products),
        "n_rows": n_rows,
    }
    meta = {
        "started": started,
        "finished": finished,
        "n_rows": n_rows,
        "n_tree_pages": len(tree_products),
        "n35_ituk_pn_count": len(pns),
        "trees": {
            k: {
                "url": v.get("url"),
                "http": v.get("status"),
                "n_items": v.get("n_items") or len(v.get("items") or []),
                "vehicle": v.get("vehicle"),
            }
            for k, v in tree_products.items()
        },
        "discovery_log": discovery_log,
        "no_full_site_crawl": True,
    }
    (OUT / "products.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUT / "pn_search.json").write_text(json.dumps(pn_search, indent=2), encoding="utf-8")
    (OUT / "products.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    rows = []
    for rec in pn_search:
        gen = [i for i in rec["items"] if i.get("is_genuine") and i.get("price_ex_gbp") is not None]
        iam = [i for i in rec["items"] if (not i.get("is_genuine")) and i.get("price_ex_gbp") is not None]
        g0 = min(gen, key=lambda x: x["price_ex_gbp"]) if gen else None
        a0 = min(iam, key=lambda x: x["price_ex_gbp"]) if iam else None
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
        })
    with (OUT / "products.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["pn"])
        w.writeheader()
        w.writerows(rows)

    tree_rows = []
    for key, block in tree_products.items():
        for it in block.get("items") or []:
            tree_rows.append({
                "tree": key,
                "vehicle": block.get("vehicle"),
                "http": block.get("status"),
                "tree_url": block.get("url"),
                "name": it.get("name") or "",
                "sku": it.get("sku") or "",
                "url": it.get("url") or "",
                "price_ex_gbp": it.get("price_ex_gbp"),
                "is_genuine": it.get("is_genuine"),
                "brand": it.get("brand") or "",
            })
    with (OUT / "tree_products.csv").open("w", newline="", encoding="utf-8") as f:
        fields = [
            "tree", "vehicle", "http", "tree_url", "name", "sku", "url",
            "price_ex_gbp", "is_genuine", "brand",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(tree_rows)

    print("WROTE", OUT, "n_rows", n_rows, "pages", len(tree_products), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
