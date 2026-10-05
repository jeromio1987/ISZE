"""QA: customer PN table header sort + offline markers."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source.html"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
OUT = ISZE / "02_dashboards" / "pricing" / "_qa" / "cust_pn_sort.png"


def cheap() -> list[str]:
    fails: list[str] = []
    text = HTML.read_text(encoding="utf-8")
    if 'id="payload"' not in text:
        fails.append("payload not embedded")
    if "fetch(" in text:
        fails.append("fetch() present")
    cdn = [
        u
        for u in re.findall(r"https?://[^\s\"'<>]+", text)
        if any(x in u.lower() for x in ("cdn", "jsdelivr", "unpkg", "cdnjs", "chart.js"))
    ]
    if cdn:
        fails.append(f"cdn urls: {cdn[:3]}")
    if "custPnSort" not in text or "data-sort=" not in text or "custPnVal" not in text:
        fails.append("sort not wired")
    if "no internet" not in text.lower() and "no server" not in text.lower():
        fails.append("offline claim missing from header")
    return fails


def main() -> int:
    fails = cheap()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    uri = HTML.as_uri()
    with sync_playwright() as pw:
        br = pw.chromium.launch(
            executable_path=str(CHROME) if CHROME.exists() else None,
            headless=True,
        )
        page = br.new_page(viewport={"width": 1400, "height": 900})
        page.goto(uri, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(800)

        # Pick ITUK sold-to (2575) if present, else first real option
        picked = page.evaluate(
            """() => {
          const s = document.getElementById('cust');
          let v = -1;
          for (const o of s.options) {
            if (o.value === '-1') continue;
            if (/2575|ISUZU TRUCK \\(UK\\)/i.test(o.text)) { v = Number(o.value); break; }
            if (v < 0) v = Number(o.value);
          }
          s.value = String(v);
          s.dispatchEvent(new Event('change'));
          return {v, text: s.options[s.selectedIndex].text};
        }"""
        )
        page.wait_for_timeout(600)

        # Click first donut segment (or force custL2 via state if chart click flaky)
        page.evaluate(
            """() => {
          if (window.state.custL2 === null || window.state.custL2 === undefined) {
            // force into biggest family's first L2 by clicking chart if possible
            const ch = window.charts && window.charts['c-cust-mix'];
            if (ch && ch.data && ch.data.labels && ch.data.labels.length) {
              // set first non-sentinel key via internal: re-render with custL2=0-ish
              // Prefer clicking legend item 0 path: set from mix keys stored? Use EGR-like:
              window.state.custL2 = 0;
              // find a real L2 present in cust_pn for this cust+l1
              const src = window.D.cust_pn || [];
              const c = window.state.cust, l1 = window.state.custL1;
              for (let i = 0; i < src.length; i++) {
                if (src[i][0] === c && src[i][1] === l1) { window.state.custL2 = src[i][2]; break; }
              }
              window.render();
            }
          }
        }"""
        )
        page.wait_for_timeout(500)

        before = page.evaluate(
            """() => {
          const rows = [...document.querySelectorAll('#cust-pn tbody tr')].map(tr => {
            const tds = tr.querySelectorAll('td');
            return {pn: tds[0]?.textContent, step: tds[7]?.textContent, pct: tds[8]?.textContent};
          });
          return {sort: window.state.custPnSort, rows: rows.slice(0,5), n: rows.length,
                  q: document.getElementById('q-cust-pn').textContent};
        }"""
        )

        page.click('#cust-pn thead th[data-sort="pct"]')
        page.wait_for_timeout(300)

        after = page.evaluate(
            """() => {
          const rows = [...document.querySelectorAll('#cust-pn tbody tr')].map(tr => {
            const tds = tr.querySelectorAll('td');
            return {pn: tds[0]?.textContent, step: tds[7]?.textContent, pct: tds[8]?.textContent};
          });
          const pcts = rows.map(r => {
            const m = /([0-9.]+)%/.exec(r.pct || '');
            return m ? Number(m[1]) : null;
          }).filter(x => x !== null);
          let desc = true;
          for (let i = 1; i < pcts.length; i++) {
            if (pcts[i] > pcts[i-1] + 1e-9) { desc = false; break; }
          }
          return {sort: window.state.custPnSort, rows: rows.slice(0,5), n: rows.length,
                  q: document.getElementById('q-cust-pn').textContent,
                  pctsHead: pcts.slice(0,8), descOk: desc,
                  thOn: !!document.querySelector('#cust-pn thead th[data-sort="pct"].on')};
        }"""
        )

        page.locator("#cust-drill").screenshot(path=str(OUT))
        br.close()

    print("picked", json.dumps(picked))
    print("before", json.dumps(before, indent=2)[:800])
    print("after", json.dumps(after, indent=2)[:1200])
    print("screenshot", OUT)

    if fails:
        print("CHEAP_FAIL", fails)
    if after.get("sort", {}).get("key") != "pct":
        fails.append("sort key not pct after click")
    if not after.get("descOk"):
        fails.append("weighted % not descending")
    if not after.get("thOn"):
        fails.append("Weighted header not marked on")
    if after.get("n", 0) < 1:
        fails.append("no PN rows")

    if fails:
        print("FAIL", fails)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
