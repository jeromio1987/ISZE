"""Expand KS Magento catalog coverage via polite requests (listing → PDP OEM).

Writes ks_catalog_tree_expand_20260825.csv for load_ks_pn_index (oem_on_page + price).
Does not touch ks_results.csv. No Cloudflare bypass — Magento pages only.
"""
from __future__ import annotations

import csv
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT_DIR = Path(__file__).resolve().parent
STAMP = "20260825"
CSV_PATH = OUT_DIR / f"ks_catalog_tree_expand_{STAMP}.csv"
JSON_PATH = OUT_DIR / f"ks_catalog_tree_expand_{STAMP}.json"

BASE = "https://www.ks-international.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": BASE + "/",
}

# High-value trees not fully covered by 20260818 brake hunts / PMS listing scrapes.
TREES = {
    "4hk1_rear_brake": (
        BASE
        + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/"
        "isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brake/rear-brake.html"
    ),
    "4hk1_filters_oaf": (
        BASE
        + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/"
        "isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/filters/oil-air-fuel.html"
    ),
    "4jj1_rear_brake": (
        BASE
        + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/"
        "isuzu-npr-n75-150-4jj1tc-euro-vi-2014/brake/rear-brake.html"
    ),
    "4jj1_filters_oaf": (
        BASE
        + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/"
        "isuzu-npr-n75-150-4jj1tc-euro-vi-2014/filters/oil-air-fuel.html"
    ),
    "npr88_filters_oaf": (
        BASE
        + "/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton/"
        "isuzu-npr88-7-5-4jz1tc/filters/oil-air-fuel.html"
    ),
}

FIELDS = [
    "tree",
    "url",
    "sku",
    "name",
    "line",
    "price_ex_vat_gbp",
    "price_inc_vat_gbp",
    "stock",
    "oem_on_page",
    "http_status",
    "scraped_at",
]

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def sleep(a: float = 1.2, b: float = 2.2) -> None:
    time.sleep(random.uniform(a, b))


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


def listing_links(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    seen: set[str] = set()
    for item in soup.select(".product-item"):
        a = item.select_one("a.product-item-link") or item.select_one(".product-item-name a")
        if not a or not a.get("href"):
            continue
        href = urljoin(BASE, a["href"])
        if href in seen:
            continue
        seen.add(href)
        name = a.get_text(strip=True)
        sku_el = item.select_one(".product-sku, .sku")
        sku = ""
        if sku_el:
            sku = sku_el.get_text(strip=True).replace("SKU:", "").strip()
        price_ex = parse_price(
            item.select_one(".price-excluding-tax .price")
            or item.select_one("[data-price-type='finalPrice'] .price")
        )
        price_inc = parse_price(item.select_one(".price-including-tax .price"))
        text = item.get_text(" ")
        is_genuine = "GENUINE" in name.upper() or "GENUINE OEM" in text.upper()
        oos = bool(
            item.select_one(".stock.unavailable, .out-of-stock")
            or "out of stock" in text.lower()
        )
        out.append(
            {
                "url": href,
                "name": name,
                "sku": sku,
                "price_ex_vat_gbp": price_ex,
                "price_inc_vat_gbp": price_inc,
                "line": "genuine" if is_genuine else "aftermarket",
                "stock": "out_of_stock" if oos else "in_stock",
                "listing_url": page_url,
            }
        )
    return out


def pdp_oems(html: str) -> list[str]:
    text = BeautifulSoup(html, "html.parser").get_text(" ")
    # Prefer OEM-looking 10-digit Isuzu-style PNs; keep unique order.
    found = re.findall(r"\b(\d{10})\b", text)
    out: list[str] = []
    for pn in found:
        if pn not in out:
            out.append(pn)
    return out[:12]


def main() -> int:
    rows: list[dict] = []
    meta = {
        "started": datetime.now(timezone.utc).isoformat(),
        "trees": {},
        "csv": str(CSV_PATH),
    }

    for tree, url in TREES.items():
        print(f"TREE {tree}", flush=True)
        try:
            r = SESSION.get(url, timeout=40)
            items = listing_links(r.text, url) if r.status_code == 200 else []
            meta["trees"][tree] = {
                "url": url,
                "http": r.status_code,
                "listing_items": len(items),
            }
            print(f"  listing {r.status_code} items={len(items)}", flush=True)
        except Exception as e:
            meta["trees"][tree] = {"url": url, "error": str(e), "listing_items": 0}
            print(f"  ERR {e}", flush=True)
            continue
        sleep()

        for i, item in enumerate(items, 1):
            ts = datetime.now(timezone.utc).isoformat()
            rec = {
                "tree": tree,
                "url": item["url"],
                "sku": item.get("sku") or "",
                "name": item.get("name") or "",
                "line": item.get("line") or "",
                "price_ex_vat_gbp": item.get("price_ex_vat_gbp") or "",
                "price_inc_vat_gbp": item.get("price_inc_vat_gbp") or "",
                "stock": item.get("stock") or "",
                "oem_on_page": "",
                "http_status": "",
                "scraped_at": ts,
            }
            try:
                pr = SESSION.get(item["url"], timeout=40)
                rec["http_status"] = str(pr.status_code)
                if pr.status_code == 200:
                    oems = pdp_oems(pr.text)
                    rec["oem_on_page"] = "|".join(oems)
                    # Prefer PDP price if listing lacked one
                    if not rec["price_ex_vat_gbp"]:
                        soup = BeautifulSoup(pr.text, "html.parser")
                        px = parse_price(
                            soup.select_one(".price-excluding-tax .price")
                            or soup.select_one("[data-price-type='finalPrice'] .price")
                        )
                        if px is not None:
                            rec["price_ex_vat_gbp"] = px
                print(
                    f"  [{i}/{len(items)}] {rec['sku'] or rec['name'][:28]} "
                    f"oem={rec['oem_on_page'] or '-'} gbp={rec['price_ex_vat_gbp'] or '-'}",
                    flush=True,
                )
            except Exception as e:
                rec["http_status"] = "error"
                rec["oem_on_page"] = ""
                print(f"  [{i}/{len(items)}] ERR {e}", flush=True)
            rows.append(rec)
            sleep(1.0, 1.8)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for rec in rows:
            w.writerow(rec)

    meta["finished"] = datetime.now(timezone.utc).isoformat()
    meta["rows"] = len(rows)
    meta["rows_with_oem"] = sum(1 for r in rows if r.get("oem_on_page"))
    meta["rows_with_price"] = sum(
        1 for r in rows if str(r.get("price_ex_vat_gbp") or "").strip() not in ("", "None")
    )
    JSON_PATH.write_text(
        __import__("json").dumps(meta, indent=2),
        encoding="utf-8",
    )
    print(
        f"DONE rows={meta['rows']} with_oem={meta['rows_with_oem']} "
        f"with_price={meta['rows_with_price']} -> {CSV_PATH.name}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
