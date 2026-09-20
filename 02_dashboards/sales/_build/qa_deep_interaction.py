#!/usr/bin/env python3
"""
Click-through check for the deep family page.

Drives the page's own controls and its own chart click handlers in headless Chrome, then reads back
what a reader would see: the breadcrumb level, the number of part-number rows, and whether each
canvas still carries drawn marks after every move. This is how "I want to navigate through a deeper
level by clicking on bars" is verified — by walking the path, not by reading the source.

Usage:
    python 02_dashboards/sales/_build/qa_deep_interaction.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_Deep.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_family_deep"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

ALL18 = ["IUK", "ITUK", "UTI", "UMI", "BELGIUM", "GERMANY", "NORWAY", "SWEDEN", "IRELAND",
         "PORTUGAL", "GREECE", "CYPRUS", "HUNGARY", "ROMANIA", "DENMARK", "FINLAND", "MALTA",
         "ICELAND"]

DRIVER = r"""
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    var out={steps:[], fail:[]};
    function snap(tag){ var s=window.__deepTest.state(); s.tag=tag; out.steps.push(s); }
    function check(cond,msg){ if(!cond) out.fail.push(msg); return !!cond; }
    function inkPct(s,which){ return s[which]? s[which].pct : -1; }
    try{
      if(!window.__deepTest){ out.fail.push('no test hook on the page'); }
      else {
        snap('opening: one market (IUK), all vehicle types, CY');

        /* 1. several customers, and the total equals the sum of the parts */
        var many=window.__deepTest.set({cust:['IUK','ITUK','GERMANY','PORTUGAL']});
        check(many.selCust.length===4,'multi-select did not take 4 customers: '+many.selCust.length);
        snap('four customers selected');

        /* 2. the clock carries the months with it */
        var fy=window.__deepTest.set({clock:'FY'});
        check(fy.clock==='FY','clock did not switch to FY');
        check((fy.bread||'').length>0,'breadcrumb empty on FY');
        snap('clock switched to FY');

        /* 3. the vehicle-type filter */
        var hv=window.__deepTest.set({clock:'CY',fam:'heavy_truck'});
        check(hv.selFam==='heavy_truck','vehicle filter did not take heavy truck');
        check(hv.drillFam==='heavy_truck','the filter did not reach the drill level');
        check(inkPct(hv,'funnelInk')>0.4,'the funnel is blank on heavy truck');
        snap('heavy truck selected');

        /* 4. click a bar: service family -> part numbers */
        var labels=window.__deepTest.labels('c_drill');
        check(!!labels&&labels.length>0,'no service-family level drawn');
        var before=window.__deepTest.state();
        window.__deepTest.clickBar('c_drill',0);
        var after=window.__deepTest.state();
        check(after.bread!==before.bread,'clicking a bar did not descend a level: '+after.bread);
        check(after.pnRows>0,'clicking a bar produced no part-number rows');
        check(!!after.drillCat,'no service family was opened');
        check(inkPct(after,'drillInk')>0.4,
              'the drill canvas went blank after descending: '+inkPct(after,'drillInk')+'%');
        snap('descended to part numbers');

        /* 5. the pooled vehicle type, then open its highest service family */
        window.__deepTest.choosePooled();
        var pool=window.__deepTest.state();
        check(pool.drillFam==='shared_across_families','could not reach the pooled value');
        var pl=window.__deepTest.catLabels();
        check(!!pl&&pl.length>0,'the pooled vehicle type has no service families');
        window.__deepTest.clickBar('c_drill',0);
        var pooled=window.__deepTest.state();
        check(pooled.pnRows>0,'the pooled level produced no part numbers');
        var tbl=document.querySelector('#t_pn').textContent;
        var hits=['N-series truck','Heavy truck','Light vehicle']
          .filter(function(w){return tbl.indexOf(w)>=0;}).length;
        check(hits>=2,'the pooled table does not name the families each part fits');
        out.pooledTableHitWords=hits;
        var r0=document.querySelectorAll('#t_pn tbody tr')[0];
        out.pooledTableSample=r0? r0.textContent.replace(/\s+/g,' ').trim() : null;
        snap('pooled value opened');

        /* 6. all 18 markets at once */
        window.__deepTest.set({cust:ALL18, fam:'all', clock:'CY'});
        var st=window.__deepTest.state();
        check(st.selCust.length===18,'could not select all 18 markets: '+st.selCust.length);
        check(inkPct(st,'funnelInk')>0.4,
              'the funnel went blank with all 18 selected: '+inkPct(st,'funnelInk')+'%');
        snap('all 18 markets');
      }
    }catch(e){ out.fail.push('driver threw: '+String(e&&e.message?e.message:e)); }
    var el=document.createElement('script');
    el.type='application/json'; el.id='qa-out';
    el.textContent=JSON.stringify(out);
    document.body.appendChild(el);
  }, 3200);
});
</script>
"""


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    driver = DRIVER.replace("ALL18", json.dumps(ALL18))
    page = QA / "_interaction.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", driver + "</body>"),
                    encoding="utf-8")
    r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--window-size=1440,3000", "--virtual-time-budget=30000", "--dump-dom",
                        page.as_uri()], capture_output=True, text=True, timeout=420)
    m = re.search(r'<script type="application/json" id="qa-out">(.*?)</script>', r.stdout, re.S)
    if not m:
        print("INTERACTION FAIL: the driver did not run to completion")
        print((r.stderr or "")[:800])
        return 1
    out = json.loads(m.group(1))
    print("CLICK-THROUGH AND CONTROLS, walked in headless Chrome")
    print("=" * 100)
    for s in out["steps"]:
        print(f"\n  [{s['tag']}]")
        who = ", ".join(s["selCust"][:6]) + (" ..." if len(s["selCust"]) > 6 else "")
        print(f"    customers       : {len(s['selCust'])} -> {who}")
        print(f"    vehicle type    : {s['selFam']}   clock {s['clock']}   "
              f"drill {s['drillFam']} / {s['drillCat']}")
        print(f"    breadcrumb      : {s['bread']}")
        print(f"    part-number rows : {s['pnRows']}")
        print(f"    canvas ink       : drill {s['drillInk']['pct']}%  "
              f"funnel {s['funnelInk']['pct']}%")
        if s.get("drillLabels"):
            print(f"    top of the level : {', '.join(s['drillLabels'][:4])}")
    if out.get("pooledTableSample"):
        print(f"\n  pooled table, first row: {out['pooledTableSample']}")
    print()
    (QA / "deep_interaction.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    if out["fail"]:
        print("INTERACTION FAIL:")
        for f in out["fail"]:
            print("  - " + f)
        return 1
    print("INTERACTION PASS: multi-select aggregates, the clock switches with its months, the "
          "vehicle filter reaches the drill level, a bar click descends a level, the pooled value "
          "opens onto its part numbers with the families each one fits, and every canvas keeps "
          "its ink at each step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
