"""Drive the shipped page the way Jerome does and confirm the three fixes are real."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

SALES = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
HTML = SALES / "ISZE_PMS_Family_Evolution_v2.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

errors: list[str] = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--headless=new", "--disable-gpu"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(HTML.as_uri(), wait_until="load")
    pg.wait_for_timeout(1500)

    print("=" * 94)
    print("1. CONTROLS — is the customer list box really there with 18 options?")
    print("=" * 94)
    ctrls = pg.evaluate(
        """() => [...document.querySelectorAll('select')].map(s => ({
             id: s.id, multiple: s.multiple, size: s.size, opts: s.options.length,
             selected: [...s.selectedOptions].map(o => o.value).slice(0,4)
           }))"""
    )
    for c in ctrls:
        print("  ", json.dumps(c))

    print()
    print("=" * 94)
    print("2. FIRST-VIEWPORT — where does the toolbar end and the first chart start?")
    print("=" * 94)
    geo = pg.evaluate(
        """() => {
            const bar = document.querySelector('.controls') || document.querySelector('.bar')
                     || document.querySelector('.toolbar');
            const c = document.querySelector('canvas');
            return {barBottom: bar ? Math.round(bar.getBoundingClientRect().bottom) : null,
                    firstCanvasTop: c ? Math.round(c.getBoundingClientRect().top) : null,
                    firstCanvasH: c ? Math.round(c.getBoundingClientRect().height) : null,
                    viewportH: window.innerHeight};
        }"""
    )
    print("  ", json.dumps(geo))
    print("   -> first chart inside the fold:",
          geo["firstCanvasTop"] is not None and geo["firstCanvasTop"] < geo["viewportH"])

    print()
    print("=" * 94)
    print("3. SWITCH TO UTI — do the figures change?")
    print("=" * 94)

    def kpis():
        return pg.evaluate(
            """() => [...document.querySelectorAll('.kpi .v, .tile .v, .kv .v')]
                     .map(e => e.textContent.trim()).slice(0,6)"""
        )

    before = kpis()
    print("  all customers:", before)
    try:
        pg.evaluate(
            """() => {
                const s=[...document.querySelectorAll('select')].find(x=>x.options.length>10);
                if(!s) return 'no multi select';
                const o=[...s.options].find(o=>/^\\s*UTI\\s*$/i.test(o.textContent||''));
                if(!o) return 'no UTI option';
                [...s.options].forEach(x=>x.selected=false);
                o.selected=true;
                s.dispatchEvent(new Event('change',{bubbles:true}));
                return 'selected UTI';
            }"""
        )
        pg.wait_for_timeout(1000)
        after = kpis()
        print("  UTI           :", after)
        print("   -> changed:", before != after)
    except Exception as e:
        print("  switch failed:", str(e)[:180])

    print()
    print("=" * 94)
    print("4. DECOMPOSITION AXIS — cents, or still zeros?")
    print("=" * 94)
    ticks = pg.evaluate(
        """() => {
            const labels=[];
            document.querySelectorAll('canvas').forEach(c=>{
                const ch = window.Chart && Chart.getChart ? Chart.getChart(c) : null;
                if(ch && ch.scales){
                    const s = ch.scales.x || Object.values(ch.scales)[0];
                    if(s && s.ticks) labels.push({id:c.id, ticks:s.ticks.map(t=>t.label).slice(0,8)});
                }
            });
            return labels;
        }"""
    )
    for t in ticks:
        print(f"  {t['id']:10s} {t['ticks']}")

    print()
    print("=" * 94)
    print("5. ERRORS AFTER DRIVING IT")
    print("=" * 94)
    print("  pageerrors:", len(errors))
    for e in errors[:6]:
        print("   ", e[:200])
    if not errors:
        print("    (none)")
    b.close()
