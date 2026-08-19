"""Harvest child model + brakes URLs from KS Isuzu truck hubs."""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).with_name("_ks_isuzu_truck_children_20260818.json")
HUBS = [
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton.html",
]


def main() -> None:
    profile = Path(tempfile.mkdtemp(prefix="ks_kids_"))
    out = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            channel="chrome",
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="en-GB",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for url in HUBS:
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(2)
            data = page.evaluate(
                """() => {
                  const here = location.pathname.replace(/\\.html$/, '');
                  const kids = [];
                  const seen = new Set();
                  for (const a of document.querySelectorAll('a')) {
                    const href = a.href || '';
                    if (!href.includes('isuzu-truck-parts')) continue;
                    const path = href.split('?')[0].split('#')[0];
                    if (seen.has(path)) continue;
                    if (!path.includes(here)) continue;
                    if (path.replace(/\\.html$/,'') === here) continue;
                    seen.add(path);
                    kids.push({href: path, text: (a.innerText||'').trim().slice(0,120)});
                  }
                  return {
                    url: location.href,
                    h1: (document.querySelector('h1')||{}).innerText || '',
                    kids,
                    product_item: document.querySelectorAll('.product-item').length,
                    categories: [...document.querySelectorAll('.categories-list a, .subcategory a, .item.product a, .category-image a, ol.products a')]
                      .map(a => ({href: a.href, text: (a.innerText||'').trim().slice(0,80)}))
                      .slice(0, 80),
                    main_html_sample: (document.querySelector('main, .page-main, .column.main')||document.body).innerText.slice(0, 2500),
                  };
                }"""
            )
            out.append(data)
            print(data["h1"], "kids", len(data["kids"]), "catsel", len(data["categories"]))
            for k in data["kids"][:40]:
                print(" ", k["text"][:60], k["href"])
        ctx.close()
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
