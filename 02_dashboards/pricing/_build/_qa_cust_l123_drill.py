"""QA: customer L1→L2→L3 drill + network league benchmark."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source.html"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
OUT = ISZE / "02_dashboards" / "pricing" / "_qa" / "cust_l123_drill.png"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fails: list[str] = []
    uri = HTML.as_uri()
    with sync_playwright() as pw:
        br = pw.chromium.launch(
            executable_path=str(CHROME) if CHROME.exists() else None,
            headless=True,
        )
        page = br.new_page(viewport={"width": 1400, "height": 900})
        page.goto(uri, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(900)

        page.evaluate(
            """() => {
          const s = document.getElementById('cust');
          let v = -1;
          for (const o of s.options) {
            if (o.value === '-1') continue;
            if (/Imotors Portugal \\(92\\)/i.test(o.text) || /\\(92\\)/.test(o.text)) {
              v = Number(o.value); break;
            }
            if (v < 0) v = Number(o.value);
          }
          s.value = String(v);
          s.dispatchEvent(new Event('change'));
          return v;
        }"""
        )
        page.wait_for_timeout(500)

        step1 = page.evaluate(
            """() => {
          const qa = window.__qa();
          const title = document.getElementById('t-cust-mix').textContent;
          const rows = document.querySelectorAll('#cust-pn tbody tr').length;
          const label = document.getElementById('cust').selectedOptions[0].text;
          return {custL1: qa.custL1, custL2: qa.custL2, custL3: qa.custL3,
                  title, rows, label, errors: qa.errors};
        }"""
        )
        if step1["custL1"] != -1:
            fails.append("expected L1 start, got custL1=" + str(step1["custL1"]))
        if "(92) (92)" in (step1.get("label") or ""):
            fails.append("duplicate (92) in customer label")
        if step1["rows"] < 2:
            fails.append("L1 table empty")

        # click first L1 row
        page.click("#cust-pn tbody tr")
        page.wait_for_timeout(400)
        step2 = page.evaluate(
            """() => {
          const qa = window.__qa();
          return {custL1: qa.custL1, custL2: qa.custL2, custL3: qa.custL3,
                  title: document.getElementById('t-cust-mix').textContent,
                  rows: document.querySelectorAll('#cust-pn tbody tr').length,
                  crumb: document.getElementById('cust-crumb').textContent};
        }"""
        )
        if step2["custL1"] < 0:
            fails.append("L1 click did not set custL1")
        if step2["custL2"] is not None:
            fails.append("L2 should still be null after L1")

        page.click("#cust-pn tbody tr")
        page.wait_for_timeout(400)
        step3 = page.evaluate(
            """() => {
          const qa = window.__qa();
          return {custL1: qa.custL1, custL2: qa.custL2, custL3: qa.custL3,
                  title: document.getElementById('t-cust-mix').textContent,
                  rows: document.querySelectorAll('#cust-pn tbody tr').length};
        }"""
        )
        if step3["custL2"] is None:
            fails.append("L2 click did not set custL2")

        page.click("#cust-pn tbody tr")
        page.wait_for_timeout(400)
        step4 = page.evaluate(
            """() => {
          const qa = window.__qa();
          const first = document.querySelector('#cust-pn tbody tr td');
          return {custL3: qa.custL3, rows: document.querySelectorAll('#cust-pn tbody tr').length,
                  title: document.getElementById('t-cust-pn').textContent,
                  firstCell: first ? first.textContent : null,
                  hasWeighted: !!document.querySelector('#cust-pn thead th[data-sort="pct"]')};
        }"""
        )
        if step4["custL3"] is None or step4["custL3"] < 0:
            fails.append("L3 click did not set custL3")
        if not step4["hasWeighted"]:
            fails.append("PN table missing Weighted sort header")

        league = page.evaluate(
            """() => {
          const ch = window.charts['c-league'];
          const labels = ch ? ch.data.labels : [];
          return {labels, hasNetwork: labels.indexOf('Network') >= 0,
                  q: document.getElementById('q-league').textContent};
        }"""
        )
        if not league["hasNetwork"]:
            fails.append("single-DB league missing Network bar")

        page.locator("#cust-drill").screenshot(path=str(OUT))
        br.close()

    print("step1", json.dumps(step1, indent=2)[:600])
    print("step2", json.dumps(step2, indent=2)[:500])
    print("step3", json.dumps(step3, indent=2)[:500])
    print("step4", json.dumps(step4, indent=2)[:500])
    print("league", json.dumps(league))
    print("screenshot", OUT)
    if fails:
        print("FAIL", fails)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
