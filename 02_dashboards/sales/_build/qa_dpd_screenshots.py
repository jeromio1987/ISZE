# -*- coding: utf-8 -*-
"""QA screenshots for DPD full analysis HTML."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Chrome

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Full_Analysis_20261006.html")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_dpd")
QA.mkdir(parents=True, exist_ok=True)


def main() -> None:
    uri = HTML.as_uri()
    with Chrome(width=1400, height=900) as c:
        c.goto(uri)
        time.sleep(0.4)
        h = c.js("document.body.scrollHeight")
        print("scrollHeight", h)
        c.screenshot(QA / "03_fullpage.png", full_page=True)
        print("wrote 03_fullpage.png")
        labels = c.js(
            "(() => [...document.querySelectorAll('h2')].map(el => (el.textContent||'').trim().slice(0,48)))()"
        )
        print("h2", labels)
        for i, lab in enumerate(labels):
            c.js(
                f"(() => {{ const hs=[...document.querySelectorAll('h2')]; "
                f"const el=hs[{i}]; if(el) el.scrollIntoView({{block:'start'}}); }})()"
            )
            time.sleep(0.35)
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (lab or f"s{i}"))[:40]
            path = QA / f"{i+4:02d}_{safe}.png"
            c.screenshot(path, full_page=False)
            print("wrote", path.name, path.stat().st_size)
        c.js(
            "(() => { const tr=document.querySelector('#pn-table tbody tr.clickrow'); if(tr) tr.click(); })()"
        )
        time.sleep(0.4)
        open_ok = c.js(
            "(() => { const d=document.getElementById('drawer'); return !!(d && d.classList.contains('open')); })()"
        )
        print("drawer_open", open_ok)
        c.screenshot(QA / "08_drawer_pn.png", full_page=False)
        print("wrote 08_drawer_pn.png")
        c.js(
            "(() => { const tr=document.querySelector('#db-table tbody tr.clickrow'); if(tr) tr.click(); })()"
        )
        time.sleep(0.4)
        c.screenshot(QA / "09_drawer_db.png", full_page=False)
        print("wrote 09_drawer_db.png")


if __name__ == "__main__":
    main()
