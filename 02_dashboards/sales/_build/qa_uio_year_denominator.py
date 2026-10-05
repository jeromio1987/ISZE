#!/usr/bin/env python3
"""
Does the euro-per-vehicle figure on the deep family page divide by that period's own fleet?

Renders the page in headless Chrome, drives the page's own controls, and reads the numbers back
out of the live chart objects and the DOM. What it proves:

  1. the default denominator is the period's own fleet, not the single 2025 estimate;
  2. on ITUK the two denominators are different numbers in 2023, 2024 and 2025 — a flat
     denominator cannot change a percentage, so if the two columns are identical the rebuild
     failed;
  3. the two lines on the normalised chart carry different data, so the pair is really drawn;
  4. the same euro divided by each period's own fleet does NOT have to move in the same direction
     as the euro divided by the flat estimate — that difference is the whole finding;
  5. the normalised table prints both denominators for every period;
  6. every chart panel carries a written key in words.

Usage:
    python 02_dashboards/sales/_build/qa_uio_year_denominator.py
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

DRIVER = r"""
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    var out={fail:[], proof:null, states:[], keys:[], labels:null, payLoad:null};
    function check(cond,msg){ if(!cond) out.fail.push(msg); return !!cond; }
    try{
      var T=window.__deepTest;
      check(!!T,'no test hook on the page');
      if(T){
        /* the payload's own view of the per-year file, so the page's claims can be checked
           against the file rather than against the page */
        out.payLoad=window.__deepTest.payloadCheck?window.__deepTest.payloadCheck():null;

        /* 1. the default denominator */
        var s0=T.state();
        out.states.push({tag:'opening state', flex:s0});
        check(s0.fleetMode==='yearly',
          'the default denominator is not the period\'s own fleet: '+s0.fleetMode);

        /* 2 and 4. ITUK, N-series truck, both denominators, three complete years */
        T.set({cust:['ITUK'], fam:'n_series_truck', clock:'CY', metric:'pv', fleet:'yearly'});
        out.proof=T.rateProof('ITUK','n_series_truck');
        var rows=out.proof.rows||[];
        var full=rows.filter(function(r){ return r.fleetUsed&&r.fleetSplit; });
        check(full.length>=3,'fewer than three complete periods carry both denominators: '+full.length);
        var moved=false, identical=true;
        full.forEach(function(r){
          if(r.fleetUsed!==r.fleetSplit) identical=false;
        });
        check(!identical,
          'both denominators produced the same fleet in every period, so the year axis did not land');
        if(full.length>=2){
          var own=full[full.length-1].rate/full[0].rate-1;
          var flat=full[full.length-1].rateSplit/full[0].rateSplit-1;
          out.proof.ownMove=own; out.proof.flatMove=flat;
          out.proof.directionDiffers=(own<0)!==(flat<0);
          check(Math.abs(own-flat)>1e-9,
            'the two denominators produced the same move, so one of them is not being applied');
        }
        /* the arithmetic: the printed rate must be the printed euro over the printed fleet */
        full.forEach(function(r){
          if(r.rate!==null&&r.fleetUsed){
            check(Math.abs(r.rate-r.eur/r.fleetUsed)<=1.0,
              'the printed rate is not euro divided by the printed own-period fleet: '
              +r.eur+' / '+r.fleetUsed+' != '+r.rate);
          }
          if(r.rateSplit!==null&&r.fleetSplit){
            check(Math.abs(r.rateSplit-r.eur/r.fleetSplit)<=1.0,
              'the flat rate is not euro divided by the 2025 estimate: '+r.eur+' / '
              +r.fleetSplit+' != '+r.rateSplit);
          }
        });

        /* 3. the two lines must carry different data */
        var ch=window.__deepTest.chart('c_norm');
        if(ch){
          var a=ch.data.datasets[1].data, b=ch.data.datasets[2].data;
          var same=a.every(function(v,i){ return v===b[i]; });
          check(!same,'the normalised chart plots the same two lines for both denominators');
          out.states.push({tag:'c_norm lines', own:a, flat:b,
            fleet:ch.data.datasets[0].data,
            labels:[ch.data.datasets[0].label,ch.data.datasets[1].label,ch.data.datasets[2].label]});
        } else { check(false,'no c_norm chart on the page'); }

        /* 5. the normalised table and the family table print both denominators */
        var st=T.state();
        out.states.push({tag:'table rows', normRows:st.normRows, pv:true});
        check(st.normRows>=3,'the normalised table carries fewer than three periods: '+st.normRows);
        var heads=window.__deepTest.tableHeads?window.__deepTest.tableHeads('t_norm'):null;
        out.labels={normHeads:heads};
        if(heads){
          var joined=heads.join(' | ');
          check(/2025 estimate/i.test(joined),'the table does not name the flat denominator column');
          check(/own fleet/i.test(joined),'the table does not name the per-period column');
          check(heads.length>=8,'the table lost columns: '+heads.length);
        }

        /* 6. written keys */
        out.keys=T.keys();
        var noKey=out.keys.filter(function(x){ return x.words<4; });
        check(noKey.length===0,'a panel carries a chart with no written key: '+JSON.stringify(noKey));

        /* the note must name the two defects and the default */
        var notes=T.denominatorText();
        out.notes=notes;
        check(/Israel/.test(notes.norm)&&/25%/.test(notes.norm),
          'the normalised section does not carry the Israel fleet-quality defect');
        check(/LD/.test(notes.norm),'the normalised section does not carry the LD-label defect');
        check(/forecast/i.test(notes.norm),
          'the normalised section does not say that forward periods are forecast');
        check(/own/i.test(notes.fleetNote),
          'the denominator note does not name what is in force');
        T.set({metric:'abs', fleet:'yearly', fam:'all'});
      }
    }catch(e){ out.fail.push('driver threw: '+String(e&&e.message?e.message:e)); }
    var el=document.createElement('script');
    el.type='application/json'; el.id='qa-out';
    el.textContent=JSON.stringify(out);
    document.body.appendChild(el);
  }, 3600);
});
</script>
"""


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    page = QA / "_uio_year_qa.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", DRIVER + "</body>"),
                    encoding="utf-8")
    r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--window-size=1440,3200", "--virtual-time-budget=40000", "--dump-dom",
                        page.as_uri()], capture_output=True, text=True, timeout=420)
    m = re.search(r'<script type="application/json" id="qa-out">(.*?)</script>', r.stdout, re.S)
    if not m:
        print("UIO-YEAR QA FAIL: the driver did not run to completion")
        print((r.stderr or "")[:900])
        return 1
    out = json.loads(m.group(1))

    print("EURO PER VEHICLE ON ITS OWN FLEET, driven in headless Chrome")
    print("=" * 104)
    for s in out["states"]:
        if s.get("tag") == "opening state":
            print(f"  opening denominator : {s['flex'].get('fleetMode')}")
        elif s.get("tag") == "table rows":
            print(f"  normalised table    : {s['normRows']} periods")
        elif s.get("tag") == "c_norm lines":
            print(f"  c_norm series       : {s['labels'][1]!r}")
            print(f"                        {s['labels'][2]!r}")
            print(f"    fleet per period  : {s['fleet']}")
            print(f"    per own fleet     : {[None if v is None else round(v,2) for v in s['own']]}")
            print(f"    per 2025 estimate : {[None if v is None else round(v,2) for v in s['flat']]}")
    print()
    p = out.get("proof") or {}
    if p:
        print(f"  ITUK, N-series truck, calendar years (both denominators, same euro)")
        print(f"  {'year':>6} {'billed EUR':>13} {'units':>8} {'own fleet':>10} {'2025 est':>10} "
              f"{'EUR/veh own':>12} {'EUR/veh 2025est':>16}")
        for row in p.get("rows", []):
            def f(v, d=2):
                return "n/a" if v is None else f"{v:,.{d}f}"
            print(f"  {row['period']:>6} {row['eur']:>13,.0f} {row['units']:>8,.0f} "
                  f"{f(row['fleetUsed'],0):>10} {f(row['fleetSplit'],0):>10} "
                  f"{f(row['rate']):>12} {f(row['rateSplit']):>16}")
        if p.get("ownMove") is not None:
            print(f"  move over the span : own fleet {100*p['ownMove']:+.1f}%   "
                  f"flat 2025 estimate {100*p['flatMove']:+.1f}%   "
                  f"direction differs: {p['directionDiffers']}")
    print()
    print("WRITTEN KEYS, read from the DOM")
    print("-" * 104)
    for k in out.get("keys", []):
        print(f"  {k['canvas']:12s} {k['words']:>3} words: {str(k['text'])[:88]}...")
    print()
    print("WHAT THE PAGE SAYS ABOUT THE DENOMINATOR")
    print("-" * 104)
    for name, txt in (out.get("notes") or {}).items():
        print(f"  {name}: {str(txt)[:260]}")
    if out.get("labels", {}).get("normHeads"):
        print()
        print("  t_norm columns: " + " | ".join(out["labels"]["normHeads"]))
    print()
    (QA / "deep_uio_year_qa.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    if out["fail"]:
        print("UIO-YEAR QA FAIL:")
        for f in out["fail"]:
            print("  - " + f)
        return 1
    print("UIO-YEAR QA PASS: the default denominator is each period's own fleet; the two "
          "denominators are different numbers on ITUK; both lines are drawn; the table prints "
          "both; and every chart panel carries a written key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
