#!/usr/bin/env python3
"""Belgian retail discount scanner — ISZE competitive pricing hygiene.

Uses Playwright (headless Chromium) when available; falls back to requests+BS4.

Outputs:
  deals.json           — machine-readable scrape
  deals_dashboard.html — human review dashboard
"""
from __future__ import annotations

import html as html_module
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
OUT_JSON = ROOT / "deals.json"
OUT_HTML = ROOT / "deals_dashboard.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "nl-BE,fr-BE,en;q=0.8",
}

PRICE_RE = re.compile(r"(\d+[.,]\d{2})\s*€|€\s*(\d+[.,]\d{2})", re.I)

STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]

STORES = [
    {
        "id": "lidl",
        "name": "Lidl BE",
        # Probed 2026-09-14: /c/a10051271 → HTTP 404. Search URL returns 200.
        "url": "https://www.lidl.be/q/search?query=aanbieding",
        "wait_ms": 4000,
        "prefer_requests": True,
    },
    {
        "id": "delhaize",
        "name": "Delhaize",
        "url": "https://www.delhaize.be/nl",
        "wait_ms": 8000,
        "follow_url": "https://www.delhaize.be/nl/aanbiedingen",
    },
    {
        "id": "colruyt",
        "name": "Colruyt",
        "url": "https://www.colruyt.be/nl/aanbiedingen",
        "wait_ms": 5000,
        "warmup_url": "https://www.colruyt.be/nl/producten",
    },
    {
        "id": "ah",
        "name": "Albert Heijn BE",
        "url": "https://www.ah.be/bonus",
        "wait_ms": 6000,
    },
    {
        "id": "carrefour",
        "name": "Carrefour BE",
        "url": "https://www.carrefour.be/nl/promoties",
        "wait_ms": 5000,
    },
]

COOKIE_SELECTORS = [
    "#onetrust-accept-btn-handler",
    "button:has-text('Alles accepteren')",
    "button:has-text('Tout accepter')",
    "button:has-text('Accepteren')",
    "button:has-text('Accepter')",
    "[data-testid='uc-accept-all-button']",
]

JUNK_TITLES = re.compile(
    r"^(cookie|privacy|accept|menu|home|promo|promotion|winkel|shop|€|\d)",
    re.I,
)


def _parse_price(text: str) -> float | None:
    m = PRICE_RE.search(text.replace("\xa0", " "))
    if not m:
        return None
    raw = next((g for g in m.groups() if g), None)
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _add_deal(
    deals: list[dict],
    seen: set[str],
    *,
    title: str,
    price: float,
    source_url: str,
    store_id: str,
) -> None:
    title = " ".join(title.split()).strip()[:120]
    if len(title) < 4 or JUNK_TITLES.match(title):
        return
    if price <= 0 or price > 5000:
        return
    key = f"{title.lower()}|{price:.2f}"
    if key in seen:
        return
    seen.add(key)
    deals.append(
        {
            "title": title,
            "price_eur": round(price, 2),
            "source_url": source_url,
            "store": store_id,
        }
    )


def _coerce_price(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        for key in ("value", "amount", "price", "current"):
            if key in raw:
                return _coerce_price(raw[key])
        return None
    try:
        p = float(str(raw).replace(",", ".").replace("€", "").strip())
    except (TypeError, ValueError):
        return None
    if p <= 0:
        return None
    if p > 5000:
        p = p / 100
    return p if 0 < p <= 5000 else None


def _price_from_obj(obj: dict) -> float | None:
    for key in (
        "price",
        "currentPrice",
        "sellingPrice",
        "displayPrice",
        "promoPrice",
        "basePrice",
        "amount",
        "value",
        "formattedPrice",
        "formattedValue",
        "unitPrice",
        "finalPrice",
    ):
        p = _coerce_price(obj.get(key))
        if p is not None:
            return p
    if isinstance(obj.get("priceInfo"), dict):
        p = _price_from_obj(obj["priceInfo"])
        if p is not None:
            return p
    if isinstance(obj.get("offers"), dict):
        p = _price_from_obj(obj["offers"])
        if p is not None:
            return p
    return None


def _name_from_obj(obj: dict) -> str | None:
    for key in ("fullTitle", "title", "name", "label", "productName", "description"):
        val = obj.get(key)
        if isinstance(val, str) and len(val.strip()) >= 4:
            return val.strip()
    brand = obj.get("manufacturerName")
    if isinstance(brand, str) and len(brand.strip()) >= 4 and obj.get("name"):
        return f"{brand.strip()} {obj['name'].strip()}"
    return None


def _extract_lidl_embedded(text: str, url: str, store_id: str) -> list[dict]:
    deals: list[dict] = []
    seen: set[str] = set()
    decoded = html_module.unescape(text)
    for chunk in re.split(r'"fullTitle"\s*:\s*"', decoded)[1:]:
        title = chunk.split('"', 1)[0].strip()
        pm = re.search(
            r'"price"\s*:\s*\{[^}]{0,500}?"price"\s*:\s*(\d+\.?\d*)',
            chunk[:3000],
        )
        if not pm:
            pm = re.search(r'"deletedPrice"\s*:\s*(\d+\.?\d*)', chunk[:3000])
        if not pm:
            continue
        path_m = re.search(r'"canonicalPath"\s*:\s*"([^"]+)"', chunk[:3000])
        link = urljoin("https://www.lidl.be", path_m.group(1)) if path_m else url
        _add_deal(
            deals,
            seen,
            title=title,
            price=float(pm.group(1)),
            source_url=link,
            store_id=store_id,
        )
        if len(deals) >= 40:
            break
    return deals


def _parse_colruyt_api(data: dict, url: str, store_id: str) -> list[dict]:
    deals: list[dict] = []
    seen: set[str] = set()
    for product in data.get("products") or []:
        name = (product.get("name") or "").strip()
        brand = (product.get("brand") or "").strip()
        title = f"{brand} {name}".strip() if brand else name
        pinfo = product.get("price") or {}
        price = pinfo.get("quantityPrice") or pinfo.get("basicPrice")
        if price is None:
            continue
        seo = product.get("seoName") or product.get("commercialArticleNumber") or ""
        link = f"https://www.colruyt.be/nl/producten/{seo}" if seo else url
        _add_deal(deals, seen, title=title, price=float(price), source_url=link, store_id=store_id)
        if len(deals) >= 40:
            break
    return deals


def _parse_ah_gql(data: dict, url: str, store_id: str) -> list[dict]:
    deals: list[dict] = []
    seen: set[str] = set()
    promos = (data.get("data") or {}).get("bonusPromotions") or []
    if not promos:
        for cat in (data.get("data") or {}).get("bonusCategories") or []:
            promos.extend(cat.get("promotions") or [])
    for promo in promos:
        product = promo.get("product") or {}
        title = (promo.get("title") or product.get("title") or "").strip()
        amount = ((promo.get("price") or {}).get("now") or {}).get("amount")
        if not title or amount is None:
            continue
        link = promo.get("webPath") or product.get("webPath") or url
        if link.startswith("/"):
            link = urljoin("https://www.ah.be", link)
        _add_deal(deals, seen, title=title, price=float(amount), source_url=link, store_id=store_id)
        if len(deals) >= 40:
            break
    return deals


def _parse_delhaize_product(
    product: dict,
    url: str,
    store_id: str,
    deals: list[dict],
    seen: set[str],
) -> None:
    name = (product.get("name") or product.get("title") or "").strip()
    brand = (product.get("manufacturerName") or product.get("brand") or "").strip()
    if brand and name and brand.lower() not in name.lower():
        title = f"{brand} {name}"
    else:
        title = name or brand
    price = _price_from_obj(product)
    if not title or price is None:
        return
    href = product.get("url") or product.get("productUrl")
    if not href and product.get("code"):
        href = f"/nl/producten/{product['code']}"
    link = urljoin("https://www.delhaize.be", href) if href and str(href).startswith("/") else (href or url)
    _add_deal(deals, seen, title=title, price=price, source_url=link, store_id=store_id)


def _parse_delhaize_api(data: dict, url: str, store_id: str) -> list[dict]:
    deals: list[dict] = []
    seen: set[str] = set()
    root = data.get("data") or {}
    for key in ("predictMyProducts", "searchProducts", "categoryProducts", "promotions"):
        block = root.get(key)
        if isinstance(block, dict):
            products = block.get("products") or block.get("items") or []
            for product in products:
                if isinstance(product, dict):
                    _parse_delhaize_product(product, url, store_id, deals, seen)
    products = root.get("products")
    if isinstance(products, list):
        for product in products:
            if isinstance(product, dict):
                _parse_delhaize_product(product, url, store_id, deals, seen)
    _walk_json_prices(data, deals, seen, url=url, store_id=store_id)
    return deals[:40]


def _ah_bonus_period() -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return str(start), str(end)


def _fetch_ah_bonus_in_browser(page: Any) -> dict | None:
    start, end = _ah_bonus_period()
    query = """
    query bonusPromotions($input: PromotionSearchInput) {
      bonusPromotions(filterSet: WEB_BONUS_PAGE, input: $input) {
        id title webPath
        price { now { amount } }
        product { title webPath }
      }
    }
    """
    payload = {
        "operationName": "bonusPromotions",
        "variables": {
            "input": {
                "periodStart": start,
                "periodEnd": end,
                "filterUnavailableProducts": False,
                "forcePromotionVisibility": True,
            }
        },
        "query": query,
    }
    headers = {
        "content-type": "application/json",
        "client-name": "ah-bonus",
        "client-version": "3.544.16",
        "origin": "https://www.ah.be",
        "referer": "https://www.ah.be/bonus",
    }
    for endpoint in ("https://www.ah.nl/gql", "https://www.ah.be/gql"):
        try:
            resp = page.context.request.post(endpoint, headers=headers, data=payload)
            if not resp.ok:
                continue
            result = resp.json()
            if (result.get("data") or {}).get("bonusPromotions"):
                return result
        except Exception:
            continue
    cat_payload = {
        "operationName": "bonusCategories",
        "variables": {"input": {"periodStart": start, "periodEnd": end}},
        "query": (
            "query bonusCategories($input: PromotionSearchInput) {"
            " bonusCategories(filterSet: WEB_CATEGORIES, input: $input) {"
            " promotions { id title webPath price { now { amount } } product { title webPath } }"
            " } }"
        ),
    }
    for endpoint in ("https://www.ah.nl/gql", "https://www.ah.be/gql"):
        try:
            resp = page.context.request.post(endpoint, headers=headers, data=cat_payload)
            if not resp.ok:
                continue
            result = resp.json()
            if (result.get("data") or {}).get("bonusCategories"):
                return result
        except Exception:
            continue
    return None


def _walk_json_prices(
    obj: Any,
    deals: list[dict],
    seen: set[str],
    *,
    url: str,
    store_id: str,
) -> None:
    if isinstance(obj, dict):
        name = _name_from_obj(obj)
        price = _price_from_obj(obj)
        if name and price is not None:
            link = url
            if isinstance(obj.get("url"), str):
                base = "https://www.delhaize.be" if store_id == "delhaize" else url
                link = urljoin(base, obj["url"])
            elif isinstance(obj.get("canonicalPath"), str):
                link = urljoin("https://www.lidl.be", obj["canonicalPath"])
            _add_deal(deals, seen, title=name, price=price, source_url=link, store_id=store_id)
        for v in obj.values():
            _walk_json_prices(v, deals, seen, url=url, store_id=store_id)
    elif isinstance(obj, list):
        for item in obj:
            _walk_json_prices(item, deals, seen, url=url, store_id=store_id)


def extract_deals_from_html(html: str, url: str, store_id: str) -> list[dict]:
    deals: list[dict] = []
    seen: set[str] = set()

    if store_id == "lidl":
        deals.extend(_extract_lidl_embedded(html, url, store_id))
        seen.update(f"{d['title'].lower()}|{d['price_eur']:.2f}" for d in deals)

    text = html.replace("\xa0", " ")
    soup = BeautifulSoup(text, "html.parser")

    for script in soup.find_all("script", id="__NEXT_DATA__"):
        try:
            blob = json.loads(script.string or "{}")
            _walk_json_prices(blob, deals, seen, url=url, store_id=store_id)
        except json.JSONDecodeError:
            pass

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            blob = json.loads(script.string or "{}")
            items = blob if isinstance(blob, list) else [blob]
            for item in items:
                _walk_json_prices(item, deals, seen, url=url, store_id=store_id)
        except json.JSONDecodeError:
            pass

    for el in soup.find_all(["a", "article", "li", "div", "h2", "h3", "span", "p"]):
        chunk = " ".join(el.get_text(" ", strip=True).split())
        if len(chunk) < 10 or len(chunk) > 200:
            continue
        price = _parse_price(chunk)
        if price is None:
            continue
        title = re.sub(r"\s*\d+[.,]\d{2}\s*€.*$", "", chunk).strip()
        href = el.get("href") if el.name == "a" else None
        if not href and el.find("a"):
            href = el.find("a").get("href")
        link = urljoin(url, href) if href else url
        _add_deal(deals, seen, title=title, price=price, source_url=link, store_id=store_id)
        if len(deals) >= 40:
            break

    if len(deals) < 5:
        for m in re.finditer(
            r"([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 \-'/&]{6,70})\s+(\d+[.,]\d{2})\s*€",
            text,
        ):
            title, raw = m.group(1).strip(), m.group(2).replace(",", ".")
            try:
                _add_deal(
                    deals,
                    seen,
                    title=title,
                    price=float(raw),
                    source_url=url,
                    store_id=store_id,
                )
            except ValueError:
                pass
            if len(deals) >= 30:
                break

    return deals[:40]


def _accept_cookies(page: Any) -> None:
    for sel in COOKIE_SELECTORS:
        try:
            page.locator(sel).first.click(timeout=2000)
            page.wait_for_timeout(600)
            return
        except Exception:
            pass


def scrape_store_requests(cfg: dict) -> dict:
    store_id = cfg["id"]
    url = cfg["url"]
    deals: list[dict] = []
    error = None
    method = "requests"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code >= 400 and not cfg.get("allow_soft_404"):
            r.raise_for_status()
        deals = extract_deals_from_html(r.text, url, store_id)
    except Exception as exc:
        error = str(exc)
    return _store_result(cfg, deals, error, method)


def scrape_store_playwright(page: Any, cfg: dict) -> dict:
    store_id = cfg["id"]
    url = cfg["url"]
    deals: list[dict] = []
    error = None
    method = "playwright"
    captured: list[tuple[str, dict]] = []

    def on_resp(resp: Any) -> None:
        if resp.status != 200:
            return
        resp_url = resp.url
        try:
            if store_id == "colruyt" and "product-search-prs" in resp_url:
                captured.append(("colruyt", resp.json()))
            elif store_id == "ah" and "gql" in resp_url:
                captured.append(("ah", resp.json()))
            elif store_id == "delhaize" and "delhaize.be/api" in resp_url:
                captured.append(("delhaize", resp.json()))
        except Exception:
            pass

    try:
        page.on("response", on_resp)
        if store_id == "ah":
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            _accept_cookies(page)
            page.wait_for_timeout(2000)
            ah_data = _fetch_ah_bonus_in_browser(page)
            if ah_data:
                captured.append(("ah", ah_data))
            page.wait_for_timeout(cfg.get("wait_ms", 3000))
        elif store_id == "delhaize":
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            _accept_cookies(page)
            page.wait_for_timeout(cfg.get("wait_ms", 3000))
            follow = cfg.get("follow_url")
            if follow:
                page.goto(follow, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(4000)
        else:
            warmup = cfg.get("warmup_url")
            if warmup:
                page.goto(warmup, wait_until="domcontentloaded", timeout=60_000)
                _accept_cookies(page)
                page.wait_for_timeout(2000)
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            _accept_cookies(page)
            page.wait_for_timeout(cfg.get("wait_ms", 3000))
        for _ in range(4):
            page.mouse.wheel(0, 1800)
            page.wait_for_timeout(900)
        html = page.content()
        deals = extract_deals_from_html(html, url, store_id)
        seen = {f"{d['title'].lower()}|{d['price_eur']:.2f}" for d in deals}
        for kind, payload in captured:
            if kind == "colruyt":
                extra = _parse_colruyt_api(payload, url, store_id)
            elif kind == "ah":
                extra = _parse_ah_gql(payload, url, store_id)
            else:
                extra = _parse_delhaize_api(payload, url, store_id)
            for d in extra:
                key = f"{d['title'].lower()}|{d['price_eur']:.2f}"
                if key not in seen:
                    seen.add(key)
                    deals.append(d)
        deals = deals[:40]
    except Exception as exc:
        error = str(exc)
    return _store_result(cfg, deals, error, method)


def scrape_store(cfg: dict, page: Any | None = None) -> dict:
    if cfg.get("prefer_requests"):
        block = scrape_store_requests(cfg)
        if block["deal_count"] > 0:
            return block
        if block.get("error"):
            if page is not None:
                return scrape_store_playwright(page, cfg)
            return block
    if page is not None:
        block = scrape_store_playwright(page, cfg)
        if block["deal_count"] > 0 or not cfg.get("prefer_requests"):
            return block
        # Playwright empty — last chance via requests (e.g. Lidl SSR JSON)
        return scrape_store_requests(cfg)
    return scrape_store_requests(cfg)


def _store_result(cfg: dict, deals: list[dict], error: str | None, method: str) -> dict:
    return {
        "store": cfg["id"],
        "name": cfg["name"],
        "url": cfg["url"],
        "method": method,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "deal_count": len(deals),
        "error": error,
        "deals": deals[:40],
    }


def scrape_all_playwright(stores: list[dict]) -> list[dict]:
    from playwright.sync_api import sync_playwright

    results: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=STEALTH_ARGS)
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="nl-BE",
            geolocation={"latitude": 50.85, "longitude": 4.35},
        )
        context.grant_permissions(["geolocation"])
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()
        for cfg in stores:
            page = context.new_page()
            block = scrape_store(cfg, page)
            page.close()
            if block["deal_count"] == 0 and not block.get("error"):
                cfg2 = {**cfg, "wait_ms": cfg.get("wait_ms", 3000) + 2500, "prefer_requests": False}
                block = scrape_store(cfg2, page)
            results.append(block)
            print(f"  {cfg['id']}: {block['deal_count']} deals ({block['method']})")
        browser.close()
    return results


def scrape_all(stores: list[dict]) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401

        print("Scraping with Playwright…")
        return scrape_all_playwright(stores)
    except ImportError:
        print("Playwright not installed — falling back to requests")
    except Exception as exc:
        print(f"Playwright failed ({exc}) — falling back to requests")

    out = []
    for cfg in stores:
        block = scrape_store(cfg)
        out.append(block)
        print(f"  {cfg['id']}: {block['deal_count']} deals ({block['method']})")
    return out


def build_html(report: dict) -> str:
    rows = ""
    for block in report["stores"]:
        err = f'<p class="err">{block["error"]}</p>' if block.get("error") else ""
        method = block.get("method", "?")
        rows += (
            f'<section class="store"><h2>{block["name"]} '
            f'<span class="cnt">{block["deal_count"]} deals · {method}</span></h2>'
        )
        rows += f'<p class="meta"><a href="{block["url"]}" target="_blank">{block["url"]}</a></p>{err}<table>'
        rows += "<tr><th>Product</th><th>Price</th><th>Link</th></tr>"
        for d in block.get("deals", [])[:25]:
            rows += (
                f'<tr><td>{d["title"]}</td><td>€{d["price_eur"]:.2f}</td>'
                f'<td><a href="{d["source_url"]}" target="_blank">source</a></td></tr>'
            )
        if not block.get("deals"):
            rows += '<tr><td colspan="3" class="empty">No deals parsed</td></tr>'
        rows += "</table></section>"

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>ISZE Discount Scanner</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f4f4f5;margin:0;padding:24px;color:#1a1a1a}}
h1{{border-left:6px solid #CC0E1E;padding-left:12px}}
.store{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px;margin:16px 0}}
.cnt{{font-size:12px;color:#666;font-weight:normal}}
.meta{{font-size:12px;color:#666}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}}
th{{background:#CC0E1E;color:#fff;text-align:left;padding:6px 8px}}
td{{border-bottom:1px solid #eee;padding:6px 8px}}
.err{{color:#b91c1c;font-size:12px}}
.empty{{color:#888;font-style:italic}}
</style></head><body>
<h1>Discount promotions — {report["generated_at"]}</h1>
<p>Playwright + JSON walk. Re-run: <code>run_discount_scraper.bat</code></p>
{rows}
</body></html>"""


def main() -> int:
    stores = scrape_all(STORES)
    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "stores": stores,
        "total_deals": sum(s["deal_count"] for s in stores),
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_HTML.write_text(build_html(report), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({report['total_deals']} deals)")
    print(f"Wrote {OUT_HTML}")
    failed = [s["store"] for s in stores if s.get("error") or s["deal_count"] == 0]
    if failed:
        print("WARN: zero/error stores:", ", ".join(failed))
    return 0 if report["total_deals"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
