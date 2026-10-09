# -*- coding: utf-8 -*-
"""QA screenshots for DPD reman feasibility HTML."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Chrome

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Reman_Feasibility_20261006.html")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_dpd_reman")
QA.mkdir(parents=True, exist_ok=True)


def main() -> None:
    uri = HTML.as_uri()
    with Chrome(width=1440, height=900) as c:
        c.goto(uri)
        time.sleep(0.5)
        h = c.js("document.body.scrollHeight")
        print("scrollHeight", h)
        c.screenshot(QA / "00_fullpage.png", full_page=True)
        print("wrote 00_fullpage.png")
        # hero / two columns top
        c.js("window.scrollTo(0,0)")
        time.sleep(0.2)
        c.screenshot(QA / "01_hero_two_tracks.png", full_page=False)
        # mail band
        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Peter|Osamu|asked/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "01b_mail_brief.png", full_page=False)
        # public anchors
        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Public competitive/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "01c_web_anchors.png", full_page=False)
        # track A card
        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Track A/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "02_track_a.png", full_page=False)
        # track B
        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/Track B/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "03_track_b.png", full_page=False)
        # worklist
        c.js(
            "(() => { const h=[...document.querySelectorAll('h2')].find(x=>/worklist/i.test(x.textContent||'')); if(h) h.scrollIntoView({block:'start'}); })()"
        )
        time.sleep(0.35)
        c.screenshot(QA / "04_worklist.png", full_page=False)
        # paint checks
        checks = c.js(
            """(() => {
              const t = document.body.innerText || '';
              return {
                has_track_a: /Track A/.test(t),
                has_track_b: /Track B/.test(t),
                has_euro6d: /8975359391/.test(t),
                has_ituk: /8975074422/.test(t) || /new-in-lieu/i.test(t),
                has_collect: /COLLECT/.test(t),
                has_mail: /What Peter/.test(t) && /Osamu/.test(t),
                has_anchors: /Public competitive anchors/.test(t) && /Driveline/.test(t),
                tables: document.querySelectorAll('table').length,
                cards: document.querySelectorAll('.card').length,
                mail_cards: document.querySelectorAll('.mail').length,
              };
            })()"""
        )
        print("checks", checks)


if __name__ == "__main__":
    main()
