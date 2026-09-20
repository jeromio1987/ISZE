"""Reproduce the real sequence: drill down, THEN switch the customer.

Jerome's report: "if you switch to UTI nothing happened". A load-then-switch test does not
exercise that. This drills two levels first, then switches, capturing every error.
"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

FILES = ["ISZE_PMS_Family_Evolution_v2.html",
         "ISZE_PMS_Family_Evolution_Deep.html"]

for name in FILES:
    p = BASE / name
    if not p.is_file():
        print(f"{name}: MISSING")
        continue
    errors: list[str] = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME,
                               args=["--headless=new", "--disable-gpu"])
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(p.as_uri(), wait_until="load")
        pg.wait_for_timeout(1200)

        print("=" * 96)
        print(f"FILE: {name}")
        print("=" * 96)
        print("  errors on load:", len(errors))

        # list every select AND any listbox / multi-picker
        ctrls = pg.evaluate(
            """() => {
                const out = [];
                document.querySelectorAll('select').forEach(e => out.push(
                    {kind:'select', id:e.id||'(no id)', opts:e.options.length}));
                document.querySelectorAll('select[multiple], [role=listbox], .pick, .multi')
                    .forEach(e => out.push({kind:'other', id:e.id||e.className.slice(0,30),
                                            opts:(e.options?e.options.length:0)}));
                document.querySelectorAll('button').forEach(e => {
                    const t=(e.textContent||'').trim();
                    if(/UTI|all 18|clear|only/i.test(t)) out.push({kind:'button', id:t.slice(0,24), opts:0});
                });
                return out;
            }"""
        )
        print("  controls found:")
        for c in ctrls:
            print("   ", json.dumps(c))

        # drill: click the first bar via the chart's own handler (deepest path the QA used)
        def drill():
            return pg.evaluate(
                """() => {
                    const c = (Chart.getChart && (Chart.getChart('c_main')||Chart.getChart('c_dec')));
                    const ch = c || (window.Chart && Chart.instances && Object.values(Chart.instances)[0]);
                    if (!ch || !ch.options || !ch.options.onClick) return 'no handler';
                    const meta = ch.getDatasetMeta(0);
                    if (!meta || !meta.data || !meta.data.length) return 'no bars';
                    try { ch.options.onClick({}, [{index:0, datasetIndex:0}]); return 'clicked'; }
                    catch(e) { return 'click threw: '+e.message; }
                }"""
            )

        print()
        print("  drill 1:", drill())
        pg.wait_for_timeout(700)
        print("  drill 2:", drill())
        pg.wait_for_timeout(700)
        print("  errors after drilling:", len(errors))

        # NOW switch a control, which is what Jerome did
        try:
            pg.select_option("#selFam", index=2)
            pg.wait_for_timeout(900)
            print("  switched vehicle type -> errors now:", len(errors))
        except Exception as e:
            print("  vehicle-type switch failed:", str(e)[:140])

        try:
            pg.select_option("#selClock", index=1)
            pg.wait_for_timeout(900)
            print("  switched clock       -> errors now:", len(errors))
        except Exception as e:
            print("  clock switch failed:", str(e)[:140])

        # try clicking any UTI button / option
        try:
            pg.evaluate(
                """() => {
                    const els=[...document.querySelectorAll('button,li,div,a')];
                    const uti=els.find(e=>/^\\s*UTI\\s*$/i.test(e.textContent||''));
                    if(uti){ uti.click(); return 'clicked UTI'; }
                    const opt=[...document.querySelectorAll('option')].find(o=>/UTI/i.test(o.textContent||''));
                    if(opt){ const s=opt.closest('select'); s.value=opt.value;
                             s.dispatchEvent(new Event('change',{bubbles:true})); return 'set UTI option'; }
                    return 'no UTI control found';
                }"""
            )
            pg.wait_for_timeout(1000)
        except Exception as e:
            print("  UTI switch failed:", str(e)[:140])

        state = pg.evaluate(
            """() => {
                const eb=document.getElementById('errbar');
                const out=[];
                document.querySelectorAll('canvas').forEach(c=>{
                    let ink=0;
                    try{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
                        for(let i=3;i<d.length;i+=4) if(d[i]>8) ink++;}catch(e){ink=-1;}
                    out.push({id:c.id, ink});
                });
                return {errbar:(eb?getComputedStyle(eb).display!=='none':null),
                        errtext:(eb?eb.textContent.slice(0,200):''), canvases:out};
            }"""
        )
        print()
        print("  errbar visible:", state["errbar"])
        print("  errbar text   :", state["errtext"][:200])
        for c in state["canvases"]:
            print(f"    {c['id']:10s} ink {c['ink']:>8}  {'EMPTY' if c['ink']==0 else 'painted'}")

        print()
        print("  ALL ERRORS:")
        for e in errors[:10]:
            print("   ", e[:230])
        if not errors:
            print("    (none)")
        b.close()
        print()
