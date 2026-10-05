#!/usr/bin/env python3
"""
Does the measure switch actually change the numbers?

Renders the deep family page in headless Chrome, drives the page's own controls, and reads the
plotted values back out of the live Chart objects and out of the KPI tiles in the DOM. The switch
is judged on whether the numbers move, not on whether the button exists.

Also walks the denominator control, prints one market's arithmetic four ways (euro, units, euro per
vehicle, and the flat-depth figure Jerome asked for), and reads back the written key of every
panel that carries a chart.

Usage:
    python 02_dashboards/sales/_build/qa_metric_switch.py
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
    var out={steps:[], fail:[], proof:null, keys:[], notes:null};
    function check(cond,msg){ if(!cond) out.fail.push(msg); return !!cond; }
    function close(a,b,tol){ return Math.abs(a-b)<=tol; }
    try{
      if(!window.__deepTest){ out.fail.push('no test hook on the page'); }
      else{
        window.__deepTest.set({cust:['IUK'], fam:'all', clock:'CY', metric:'abs', fleet:'split'});
        var a0=window.__deepTest.state();
        var c0=window.__deepTest.chartMetric();
        var k0=window.__deepTest.kpiText();
        out.steps.push({tag:'opening: IUK, all vehicle types, CY, billed euro',
          metric:a0.metric, fleetMode:a0.fleetMode, chips:a0.metricChips,
          chartLabel:c0.label, chartValue:c0.firstValue, prevValue:c0.prevValue,
          kpi0:k0[0]});

        /* ---- the measure switch, driven the way a reader drives it: a real button click ---- */
        var btn=null;
        Array.prototype.slice.call(document.querySelectorAll('#segMetric button')).forEach(function(b){
          if(b.getAttribute('data-m')==='pv') btn=b; });
        check(!!btn,'the euro-per-vehicle button is not in the DOM');
        if(btn) btn.click();
        var a1=window.__deepTest.state();
        var c1=window.__deepTest.chartMetric();
        var k1=window.__deepTest.kpiText();
        out.steps.push({tag:'after clicking "Euro per vehicle"',
          metric:a1.metric, chips:a1.metricChips, chartLabel:c1.label,
          chartValue:c1.firstValue, prevValue:c1.prevValue, kpi0:k1[0]});

        check(a1.metric==='pv','the control did not take the euro-per-vehicle measure: '+a1.metric);
        check(c0.firstValue!==c1.firstValue,
          'the chart plotted the same value before and after the switch: '+c0.firstValue);
        check(/per vehicle/i.test(String(c1.label)),
          'the chart dataset label does not say what it is plotting: '+c1.label);
        check(k0[0].v!==k1[0].v,
          'the headline KPI did not change with the measure: '+k0[0].v+' -> '+k1[0].v);
        check(/per vehicle/i.test(String(k1[0].l)),
          'the headline KPI label does not name the measure: '+k1[0].l);

        /* the arithmetic: euro / fleet must equal the plotted rate. A market and a vehicle type that
           actually carries a fleet estimate is chosen, because a zero-fleet line cannot be divided
           and the page says so rather than printing a rate for it. */
        var proof=window.__deepTest.rateProof('IUK','n_series_truck');
        var live=proof.rows.filter(function(r){ return r.fleetUsed; });
        if(!live.length){ proof=window.__deepTest.rateProof('ITUK','n_series_truck');
          live=proof.rows.filter(function(r){ return r.fleetUsed; }); }
        out.proof=proof;
        var last=proof.rows[proof.rows.length-1];
        var per=proof.rows.filter(function(r){ return r.period===last.period; })[0];
        var was=proof.rows.filter(function(r){ return r.period===last.period-1; })[0];
        if(per&&was&&per.fleetUsed){
          check(close(per.rate, per.eur/per.fleetUsed, 1.0),
            'the printed rate is not euro divided by the printed fleet: '
            +per.eur+' / '+per.fleetUsed+' != '+per.rate);
          check(per.fleetUsed===was.fleetUsed,
            'the split denominator moved between the two periods: '+was.fleetUsed+' -> '+per.fleetUsed);
          check(per.fleetSplit===per.fleetUsed,
            'the rate used a denominator the proof does not print');
        } else {
          check(false,'the arithmetic proof did not produce two comparable periods with a fleet');
        }

        /* ---- the units measure ---- */
        var ub=null;
        Array.prototype.slice.call(document.querySelectorAll('#segMetric button')).forEach(function(b){
          if(b.getAttribute('data-m')==='units') ub=b; });
        if(ub) ub.click();
        var a2=window.__deepTest.state();
        var c2=window.__deepTest.chartMetric();
        var k2=window.__deepTest.kpiText();
        out.steps.push({tag:'after clicking "Units"', metric:a2.metric, chips:a2.metricChips,
          chartLabel:c2.label, chartValue:c2.firstValue, kpi0:k2[0]});
        check(c2.firstValue!==c1.firstValue,'units plotted the same value as euro per vehicle');
        check(k2[0].v.indexOf('pcs')>=0,'the units KPI does not say pieces: '+k2[0].v);
        /* every chart the measure applies to must have redrawn, not just the first one */
        check(a2.normInk&&a2.normInk.pct>0.4,'the normalised canvas is blank after switching measure');
        check(a2.targetInk&&a2.targetInk.pct>0.4,'the target canvas is blank after switching measure');

        /* ---- the denominator control ---- */
        var yb=window.__deepTest.set({metric:'abs', fleet:'yearly', fam:'all', clock:'CY'});
        var cy0=yb.fleetMode;
        out.steps.push({tag:'denominator switched to the per-year count', fleetMode:cy0,
          normRows:yb.normRows, industryRows:yb.industryRows});
        check(cy0==='yearly','the denominator control did not take the per-year count');
        /* The two denominators cannot differ in 2025: the flat estimate IS that year's count, so a
           single-period comparison proves nothing. The difference is read across every period from
           the chart's own two lines, which is the only place it can be seen. */
        var b=window.__deepTest.set({metric:'pv', fleet:'yearly', cust:['ITUK']});
        var cn=window.__deepTest.chart('c_norm');
        check(!!cn,'no normalised chart to read the two denominators from');
        if(cn){
          var ownLine=cn.data.datasets[1].data, flatLine=cn.data.datasets[2].data;
          var fleetBars=cn.data.datasets[0].data;
          var differs=ownLine.some(function(v,i){
            return v!==null&&flatLine[i]!==null&&Math.abs(v-flatLine[i])>0.01; });
          var equalCount=ownLine.filter(function(v,i){
            return v!==null&&flatLine[i]!==null&&Math.abs(v-flatLine[i])<=0.01; }).length;
          out.steps.push({tag:'euro per vehicle, both denominators drawn (ITUK, N-series truck)',
            ownLine:ownLine, flatLine:flatLine, fleetBars:fleetBars,
            series:[cn.data.datasets[1].label, cn.data.datasets[2].label]});
          check(differs,
            'the two denominators produced the same rate in every period, so the year axis did '
            +'not reach the chart: '+JSON.stringify(ownLine));
          check(equalCount<=1,
            'more than the estimate year produced the same rate on both denominators: '
            +equalCount+' of '+ownLine.length+' periods');
        }
        window.__deepTest.set({cust:['IUK'], metric:'abs', fleet:'yearly'});

        /* ---- the notes a reader can see ---- */
        out.notes=window.__deepTest.denominatorText();
        check(out.notes.norm.toLowerCase().indexOf('2025e')>=0,
          'the normalised section does not state the fleet vintage 2025E');
        check(out.notes.norm.length>200,'the normalised section carries no explanation');
        check(!!out.notes.industry&&out.notes.industry.length>100,
          'the industry section is empty');

        /* ---- written keys ---- */
        out.keys=window.__deepTest.keys();
        var noKey=out.keys.filter(function(x){ return x.words<4; });
        check(noKey.length===0,
          'a panel carries a chart with no written key: '+JSON.stringify(noKey));
        window.__deepTest.set({metric:'pv', fleet:'split'});
        out.steps.push({tag:'left in euro per vehicle on the split denominator'});
      }
    }catch(e){ out.fail.push('driver threw: '+String(e&&e.message?e.message:e)); }
    var el=document.createElement('script');
    el.type='application/json'; el.id='qa-out';
    el.textContent=JSON.stringify(out);
    document.body.appendChild(el);
  }, 3400);
});
</script>
"""


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    page = QA / "_metric_switch.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", DRIVER + "</body>"),
                    encoding="utf-8")
    r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--window-size=1440,3200", "--virtual-time-budget=40000", "--dump-dom",
                        page.as_uri()], capture_output=True, text=True, timeout=420)
    m = re.search(r'<script type="application/json" id="qa-out">(.*?)</script>', r.stdout, re.S)
    if not m:
        print("MEASURE-SWITCH FAIL: the driver did not run to completion")
        print((r.stderr or "")[:900])
        return 1
    out = json.loads(m.group(1))
    print("MEASURE SWITCH, DENOMINATOR AND KEYS, driven in headless Chrome")
    print("=" * 104)
    for s in out["steps"]:
        print(f"\n  [{s['tag']}]")
        if s.get("chips"):
            print(f"    switched control : {', '.join(s['chips'])}")
        if s.get("chartLabel") is not None:
            print(f"    chart dataset    : {s['chartLabel']!r}")
            print(f"    plotted          : {s['chartValue']}  (year before {s.get('prevValue')})")
        if s.get("kpi0"):
            print(f"    headline tile    : {s['kpi0']['v']}  |  {s['kpi0']['l']}"
                  + (f"  |  {s['kpi0']['s']}" if s["kpi0"].get("s") else ""))
        if s.get("fleetMode"):
            print(f"    denominator      : {s['fleetMode']}")
        if s.get("normRows"):
            print(f"    denominator rows : {s['normRows']}   industry rows: {s['industryRows']}")
    print()
    print("THE ARITHMETIC, per period, one market and one vehicle type")
    print("-" * 104)
    if out.get("proof"):
        p = out["proof"]
        print(f"  market {p['market']}, {p['family']}")
        print(f"  {'period':>6} {'billed EUR':>14} {'units':>10} {'fleet (split)':>14} "
              f"{'fleet (per year)':>17} {'EUR/veh (split)':>16} {'EUR/veh (per year)':>19}")
        for row in p["rows"]:
            rs = f"{row['rateSplit']:,.2f}" if row.get("rateSplit") else "n/a"
            ry = f"{row['rateYear']:,.2f}" if row.get("rateYear") else "n/a"
            print(f"  {row['period']:>6} {row['eur']:>14,.0f} {row['units']:>10,.0f} "
                  f"{str(row['fleetSplit']):>14} {str(row['fleetYear']):>17} {rs:>16} {ry:>19}")
        print(f"  fleet source: {p['rows'][-1].get('fleetSource','')}")
        print(f"  fleet vintage: {p['rows'][-1].get('fleetVintage','')}")
    print()
    print("WRITTEN KEYS, read from the DOM")
    print("-" * 104)
    for k in out.get("keys", []):
        print(f"  {k['canvas']:12s} {k['words']:>3} words: {str(k['text'])[:92]}...")
    print()
    print("WHAT THE PAGE SAYS ABOUT THE DENOMINATOR")
    print("-" * 104)
    for name, txt in (out.get("notes") or {}).items():
        print(f"  {name}: {str(txt)[:300]}")
    print()
    (QA / "deep_metric_switch.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    if out["fail"]:
        print("MEASURE-SWITCH FAIL:")
        for f in out["fail"]:
            print("  - " + f)
        return 1
    print("MEASURE-SWITCH PASS: the euro-per-vehicle and units measures change the plotted values, "
          "the headline tile and the label; the denominator control moves the rate; the arithmetic "
          "is euro divided by the printed fleet; and every chart panel carries a written key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
