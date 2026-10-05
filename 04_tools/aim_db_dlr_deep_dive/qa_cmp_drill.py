"""Drive the built comparison page in headless Chrome: drill level 1 -> 2 -> 3 -> part numbers.

Reads and writes nothing but its own screenshots and console log. The drill is driven by clicking
the ranked-list rows and by dispatching the chart's onClick path, so both routes are exercised.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\_qa")


def main():
    runs = sys.argv[1:] or ["PORTUGAL"]
    report = {}
    with sync_playwright() as pw:
        for run in runs:
            html = DASH / f"ISZE_AIM_Comparison_{run}.html"
            b = pw.chromium.launch(
                executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                args=["--allow-file-access-from-files"])
            pg = b.new_page(viewport={"width": 1500, "height": 1000})
            errs, logs = [], []
            pg.on("console", lambda m: (errs if m.type == "error" else logs).append(m.text))
            pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
            pg.goto(html.as_uri(), wait_until="load")
            pg.wait_for_timeout(2500)

            def state():
                return pg.evaluate("""() => {
                  const cr = document.getElementById('crumb');
                  const t = document.getElementById('t-drill').textContent;
                  const up = document.querySelectorAll('#t-up tbody tr').length;
                  const dn = document.querySelectorAll('#t-dn tbody tr').length;
                  const tb = document.querySelectorAll('#t-drilltb tbody tr').length;
                  const th = document.querySelectorAll('#t-drilltb thead th').length;
                  const bars = document.querySelectorAll('#c-drill').length;
                  const kpi = Array.from(document.querySelectorAll('#kpis .val'))
                                .map(e=>e.textContent.trim());
                  const canvas = document.getElementById('c-drill');
                  return {crumb:cr.textContent.replace(/\\s+/g,' ').trim(), title:t, up, dn,
                          table:tb, thead:th, canvas:bars,
                          kpi:kpi, pair:document.getElementById('pair').value,
                          pairOpts:document.getElementById('pair').options.length,
                          pairText:document.getElementById('pair').options.length
                            ? document.getElementById('pair').options[0].text : '',
                          w:canvas.width, h:canvas.height,
                          note:document.getElementById('pairnote').textContent
                            .replace(/\\s+/g,' ').trim().slice(0,220)};
                }""")

            steps = [{"step": "L1", **state()}]
            # drill to level 2 by clicking the top row of the improvements list
            pg.click("#t-up tbody tr:first-child")
            pg.wait_for_timeout(1200)
            steps.append({"step": "L2", **state()})
            pg.click("#t-up tbody tr:first-child")
            pg.wait_for_timeout(1200)
            steps.append({"step": "L3", **state()})
            pg.click("#t-up tbody tr:first-child")
            pg.wait_for_timeout(1400)
            steps.append({"step": "PN", **state()})
            pg.screenshot(path=str(QA / f"cmp_{run}_drill_pn.png"), full_page=False)

            # measure switch and csv presence
            pg.select_option("#measure", "eur_gm")
            pg.wait_for_timeout(900)
            steps.append({"step": "PN+GM", **state()})
            pg.select_option("#measure", "units")
            pg.wait_for_timeout(900)
            steps.append({"step": "PN+units", **state()})
            # one step back up through the breadcrumb
            pg.select_option("#measure", "eur_list")
            pg.wait_for_timeout(600)
            pg.click("#crumb span.link:first-child")
            pg.wait_for_timeout(1100)
            steps.append({"step": "back to L1", **state()})

            # every distributor view: does it offer a pair, and does the table fill
            pg.select_option("#measure", "eur_list")
            pg.wait_for_timeout(400)
            views = []
            opts = pg.evaluate("""() => Array.from(document.getElementById('db').options)
                                        .map(o=>o.value)""")
            for v in opts:
                pg.select_option("#db", v)
                pg.wait_for_timeout(1100)
                s = state()
                views.append({"db": v, "pairOpts": s["pairOpts"], "pairText": s["pairText"],
                              "up": s["up"], "dn": s["dn"], "table": s["table"],
                              "kpi": s["kpi"][:2], "note": s["note"]})
            report[run] = {"steps": steps, "views": views, "console_errors": errs,
                           "console_logs": logs[:20]}
            b.close()
    (QA / "cmp_drill.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for run, r in report.items():
        print(f"== {run}")
        for s in r["steps"]:
            print(f"   {s['step']:<11} crumb={s['crumb'][:70]:<70} up={s['up']:<4} dn={s['dn']:<4} "
                  f"table={s['table']:<5} kpi={s['kpi'][:2]}")
        print(f"   console errors: {r['console_errors'] or 'none'}")
        for v in r["views"]:
            print(f"   view {v['db']:<9} pairs={v['pairOpts']} up={v['up']:<4} dn={v['dn']:<4} "
                  f"rows={v['table']:<5} {str(v['kpi'])[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
