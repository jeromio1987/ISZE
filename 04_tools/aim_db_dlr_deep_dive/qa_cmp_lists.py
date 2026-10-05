"""Read the top of each ranked list straight off the page, so the report can name the movers."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\_qa")


def main():
    runs = sys.argv[1:] or ["PORTUGAL"]
    report = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            args=["--allow-file-access-from-files"])
        for run in runs:
            pg = b.new_page(viewport={"width": 1500, "height": 1200})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto((DASH / f"ISZE_AIM_Comparison_{run}.html").as_uri(), wait_until="load")
            pg.wait_for_timeout(2600)
            names = pg.evaluate("""() => {
              const g = sel => Array.from(document.querySelectorAll(sel))
                .map(tr => ({name: tr.querySelector('td').childNodes[0].textContent.trim(),
                             sub: (tr.querySelector('td .muted')||{}).textContent||'',
                             val: tr.querySelectorAll('td')[1].textContent.trim()}));
              return {up: g('#t-up tbody tr').slice(0,12),
                      dn: g('#t-dn tbody tr').slice(0,12)};
            }""")
            report[run] = names
            # report the coverage table too
            report[run + "_coverage"] = pg.evaluate("""() => {
              const rows = Array.from(document.querySelectorAll('#t-cover tbody tr'));
              return rows.map(tr => Array.from(tr.querySelectorAll('td'))
                .map(td => td.textContent.replace(/\\s+/g,' ').trim()));
            }""")
            report[run + "_recon"] = pg.evaluate("""() => {
              const o = {pairs: Array.from(document.getElementById('pair').options)
                          .map(x=>x.text), db: document.getElementById('db').value,
                         note: document.getElementById('pairnote').textContent
                          .replace(/\\s+/g,' ').trim()};
              return o;
            }""")
            report[run + "_errors"] = errs
            b_ = pg
            b_.close()
        b.close()
    (OUT / "cmp_lists.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for run in runs:
        print(f"== {run}")
        print("  pair(s):", report[run + "_recon"]["pairs"])
        print("  NOTE:", report[run + "_recon"]["note"][:300])
        print("  improvements:")
        for x in report[run]["up"]:
            print(f"    {x['name'][:44]:<44} {x['val']:>14}   {x['sub'][:60]}")
        print("  declines:")
        for x in report[run]["dn"]:
            print(f"    {x['name'][:44]:<44} {x['val']:>14}   {x['sub'][:60]}")
        print("  errors:", report[run + "_errors"] or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
