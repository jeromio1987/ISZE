# -*- coding: utf-8 -*-
"""QA screenshots for DPD case study HTML."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Chrome

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Case_Study_20261006.html")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_dpd_case")
QA.mkdir(parents=True, exist_ok=True)


def main() -> None:
    uri = HTML.as_uri()
    with Chrome(width=1440, height=900) as c:
        c.goto(uri)
        time.sleep(0.6)
        print("scrollHeight", c.js("document.body.scrollHeight"))
        c.screenshot(QA / "00_fullpage.png", full_page=True)
        c.js("window.scrollTo(0,0)")
        time.sleep(0.2)
        c.screenshot(QA / "01_hero.png", full_page=False)

        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Peter|Osamu/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.3)
        c.screenshot(QA / "02_mail.png", full_page=False)

        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Public competitive/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.3)
        c.screenshot(QA / "03_anchors.png", full_page=False)

        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Ranked DPD/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.3)
        c.screenshot(QA / "04_assemblies.png", full_page=False)

        # open PN drawer on hero Track A
        c.js(
            """(() => {
              const tr = document.querySelector("tr.clickrow[data-id='8975359391']");
              if (tr) tr.click();
            })()"""
        )
        time.sleep(0.45)
        c.screenshot(QA / "05_drawer_pn_a.png", full_page=False)
        c.js("(() => { const b=document.getElementById('dx'); if(b) b.click(); })()")
        time.sleep(0.25)

        # open DB drawer UMI
        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Every distributor/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.3)
        c.js(
            """(() => {
              const tr = document.querySelector("tr.clickrow[data-id='UMI']");
              if (tr) tr.click();
            })()"""
        )
        time.sleep(0.45)
        c.screenshot(QA / "06_drawer_db_umi.png", full_page=False)
        c.js("(() => { const b=document.getElementById('dx'); if(b) b.click(); })()")
        time.sleep(0.25)

        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Reman feasibility/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "07_reman_tracks.png", full_page=False)

        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/three pipes|Demand we can see|big enough for transport/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "07b_transport_scale.png", full_page=False)

        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/worklist/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "08_worklist.png", full_page=False)

        checks = c.js(
            """(() => {
              const t = document.body.innerText || '';
              const drawer = document.getElementById('drawer');
              // reopen PN to verify sandwich in DOM after close
              const tr = document.querySelector("tr.clickrow[data-id='8975359391']");
              if (tr) tr.click();
              const dtxt = document.getElementById('dbody')?.innerText || '';
              return {
                clickrows: document.querySelectorAll('tr.clickrow').length,
                has_mail: /What Peter/.test(t) && /Osamu/.test(t),
                has_anchors: /Public competitive anchors/.test(t) && /Driveline/.test(t),
                has_hold: /HOLD/.test(t),
                has_conditional: /CONDITIONAL/.test(t),
                has_nav: !!document.querySelector('.navstick'),
                has_transport: /three pipes/i.test(t) && /Honest limits/.test(t) && /ASSUMPTION/.test(t),
                no_fake_first_dpd_pct: !(/share of first DPD sold in warranty is/.test(t)),
                has_first_dpd_caveat: /cannot compute/.test(t) || /First-DPD warranty % cannot/.test(t) || /no non-warranty first-fail/.test(t),
                has_filter_split: /FILTER/.test(t) && /full can|full ASM/i.test(t),
                no_fake_450: !(/~€450 on the Euro 5/.test(t)),
                drawer_open: drawer && drawer.classList.contains('open'),
                sandwich_in_drawer: /Price sandwich/.test(dtxt) && /COLLECT/.test(dtxt),
                tables: document.querySelectorAll('table').length,
              };
            })()"""
        )
        print("checks", checks)


if __name__ == "__main__":
    main()
