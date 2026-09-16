"""Diagnose N75 brakes Magento listing selectors."""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = (
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/"
    "isuzu-truck-parts/isuzu-7-5-ton/"
    "isuzu-npr-n75-190-4hk1tc-euro-vi-5-2ltr-140kw-190hp-11-2013-on/brakes.html"
)
OUT = Path(__file__).with_name("_ks_n75_brakes_diag_20260818.json")


def main() -> None:
    profile = Path(tempfile.mkdtemp(prefix="ks_diag_"))
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            channel="chrome",
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="en-GB",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        time.sleep(3)
        data = page.evaluate(
            """() => {
              const q = (s) => document.querySelectorAll(s).length;
              const hrefs = [...document.querySelectorAll('a')]
                .map(a => ({href: a.href, text: (a.innerText||'').trim().slice(0,80)}))
                .filter(x => x.href && x.href.includes('/brakes'));
              return {
                title: document.title,
                url: location.href,
                h1: (document.querySelector('h1')||{}).innerText || '',
                product_item: q('.product-item'),
                product_item_link: q('a.product-item-link'),
                product_name: q('.product-item-name a'),
                li_item: q('ol.products li.item'),
                empty: (document.querySelector('.message.empty')||{}).innerText || '',
                toolbar: (document.querySelector('.toolbar-amount')||{}).innerText || '',
                body_len: (document.body.innerText||'').length,
                body_head: (document.body.innerText||'').slice(0, 1500),
                brake_hrefs: hrefs.slice(0, 40),
              };
            }"""
        )
        shot = Path(__file__).with_name("_ks_n75_brakes_diag_20260818.png")
        page.screenshot(path=str(shot), full_page=True)
        data["screenshot"] = str(shot)
        ctx.close()
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({k: data[k] for k in data if k != "brake_hrefs"}, indent=2)[:4000])
    print("n_brake_hrefs", len(data.get("brake_hrefs") or []))
    for x in (data.get("brake_hrefs") or [])[:25]:
        print(x)


if __name__ == "__main__":
    main()
