"""Find live Isuzu truck / N75 category URLs on KS."""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).with_name("_ks_isuzu_truck_hub_diag_20260818.json")
SEEDS = [
    "https://www.ks-international.com/",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-7-5-ton.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton.html",
    "https://www.ks-international.com/isuzu-4x4-and-truck-parts/isuzu-truck-parts/isuzu-3-5-ton/isuzu-nlr87-rz4e-1-9ltr-hp-2016/brakes.html",
]


def main() -> None:
    profile = Path(tempfile.mkdtemp(prefix="ks_hub_"))
    pages_out = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            channel="chrome",
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="en-GB",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for url in SEEDS:
            resp = page.goto(url, wait_until="domcontentloaded")
            time.sleep(2.0)
            data = page.evaluate(
                """() => {
                  const h1 = (document.querySelector('h1')||{}).innerText || '';
                  const links = [...document.querySelectorAll('a')]
                    .map(a => ({href: a.href, text: (a.innerText||'').trim().slice(0,100)}))
                    .filter(x => x.href && /isuzu/i.test(x.href));
                  const interesting = links.filter(x =>
                    /n75|npr|nqr|nlr|7-5|3-5|truck|brake|n-series/i.test(x.href + ' ' + x.text)
                  );
                  return {
                    title: document.title,
                    url: location.href,
                    h1,
                    status404: /whoops|not found/i.test(h1 + ' ' + document.title),
                    n_isuzu_links: links.length,
                    interesting: interesting.slice(0, 80),
                    product_item: document.querySelectorAll('.product-item').length,
                    toolbar: (document.querySelector('.toolbar-amount')||{}).innerText || '',
                  };
                }"""
            )
            data["http"] = resp.status if resp else None
            data["requested"] = url
            pages_out.append(data)
            print(data["http"], data["h1"][:80], url)
        ctx.close()
    OUT.write_text(json.dumps(pages_out, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
