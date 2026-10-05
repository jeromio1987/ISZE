"""Render the other clock and each selectable customer, and measure ink in every case.

The default view is the calendar clock on one customer. This drives the other clock and several
customers so a state that throws, or draws blank, is caught before shipping rather than by Jerome.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_family_evolution"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CASES = [("ITUK", "CY"), ("IUK", "FY"), ("UTI", "FY"), ("UMI", "CY"), ("GERMANY", "FY"),
         ("HUNGARY", "CY")]


def chrome(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=300)


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    html = HTML.read_text(encoding="utf-8")
    fails = []
    report = []
    for market, clock in CASES:
        probe = f"""
<script>
document.addEventListener('DOMContentLoaded',function(){{
  var m=document.getElementById('selMarket'), c=document.getElementById('selClock');
  setTimeout(function(){{
    m.value={json.dumps(market)}; c.value={json.dumps(clock)};
    m.dispatchEvent(new Event('change')); c.dispatchEvent(new Event('change'));
  }}, 900);
  setTimeout(function(){{
    var err=document.getElementById('jserr');
    var out={{market:{json.dumps(market)}, clock:{json.dumps(clock)},
      errorShown: !!(err && err.style.display==='block'),
      errorText: err?err.textContent.slice(0,200):'',
      canvases:[], kpis:document.querySelectorAll('.kpi').length,
      kpiText:[], formulas:[],
      panels:document.querySelectorAll('.sm').length,
      rows:document.querySelectorAll('tbody tr').length}};
    document.querySelectorAll('.kpi').forEach(function(t){{
      out.kpiText.push((t.querySelector('.v')?t.querySelector('.v').textContent:'')
        +' | '+(t.querySelector('.l')?t.querySelector('.l').textContent:''));
      out.formulas.push(t.getAttribute('data-tip')||'');
    }});
    // the chart titles must state a business question, and the key must name its series
    out.titles=[]; document.querySelectorAll('section h2').forEach(function(h){{
      var q=h.querySelector('.q'); out.titles.push(h.textContent.replace(/\\s+/g,' ').trim());}});
    document.querySelectorAll('canvas').forEach(function(cv){{
      var ctx=cv.getContext('2d'), nw=0, s=0;
      try{{ var im=ctx.getImageData(0,0,cv.width,cv.height).data;
        for(var i=0;i<im.length;i+=4){{ s++; if(im[i+3]>8 && !(im[i]>250&&im[i+1]>250&&im[i+2]>250)) nw++; }} }}catch(e){{}}
      out.canvases.push({{id:cv.id, nonWhite:nw, sampled:s,
        pct: s? +(100*nw/s).toFixed(2):0}});
    }});
    var el=document.createElement('script'); el.type='application/json'; el.id='case-out';
    el.textContent=JSON.stringify(out); document.body.appendChild(el);
  }}, 3000);
}});
</script>
"""
        tmp = QA / f"_case_{market}_{clock}.html"
        tmp.write_text(html.replace("</body>", probe + "</body>"), encoding="utf-8")
        d = chrome([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--window-size=1440,3400", "--virtual-time-budget=22000",
                    "--dump-dom", tmp.as_uri()]).stdout
        m = re.search(r'<script type="application/json" id="case-out">(.*?)</script>', d, re.S)
        if not m:
            print(f"FAIL {market}/{clock}: the page did not publish its state")
            fails.append(f"{market}/{clock}: no state")
            continue
        o = json.loads(m.group(1))
        blanks = [c for c in o["canvases"] if c["nonWhite"] < 400 or c["pct"] < 0.4]
        status = "ok"
        # the KPI labels must name the periods actually in use, not a hardcoded pair of years
        want_years = {"CY": ("2023", "2025"), "FY": ("2024", "2026")}[clock]
        ktext = " ".join(o.get("kpiText", []))
        titletext = " ".join(o.get("titles", []))
        for y in want_years:
            if y not in ktext:
                fails.append(f"{market}/{clock}: KPI labels do not name {y}")
                status = f"KPI label missing {y}"
        # and must not name a year that is not a period on this clock
        wrong = {"CY": ["2024 to 2026"], "FY": ["2023 to 2025"]}[clock]
        for w in wrong:
            if w in ktext:
                fails.append(f"{market}/{clock}: KPI labels still say {w}")
                status = f"stale KPI label {w}"
        if len(o.get("titles", [])) < 6:
            fails.append(f"{market}/{clock}: only {len(o.get('titles', []))} sections")
        for t in o.get("titles", []):
            if "?" not in t:
                fails.append(f"{market}/{clock}: a section title is not a question: {t[:70]}")
        if o["errorShown"]:
            status = f"SCRIPT ERROR: {o['errorText']}"
            fails.append(f"{market}/{clock}: {status}")
        elif blanks:
            status = "BLANK: " + ", ".join(c["id"] for c in blanks)
            fails.append(f"{market}/{clock}: {status}")
        elif o["panels"] < 18 or o["rows"] < 10:
            status = f"thin: {o['panels']} panels, {o['rows']} rows"
            fails.append(f"{market}/{clock}: {status}")
        print(f"  {market:9s} {clock}  canvases {len(o['canvases']):2d}  "
              f"min ink {min(c['pct'] for c in o['canvases']):5.2f}%  "
              f"kpis {o['kpis']:2d}  panels {o['panels']:2d}  rows {o['rows']:2d}  {status}")
        report.append(o)

    # also capture a screenshot of the FY view for the record
    png = QA / "family_evolution_FY_ITUK.png"
    fy = QA / "_case_ITUK_FY.html"
    chrome([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
            "--force-device-scale-factor=1", "--window-size=1440,5800",
            "--virtual-time-budget=22000", f"--screenshot={png}", fy.as_uri()])
    print()
    print(f"FY screenshot -> {png.name} "
          f"{'OK' if png.is_file() else 'MISSING'}")
    (QA / "case_matrix.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if fails:
        print()
        for f in fails:
            print(f"FAIL: {f}")
        return 1
    print()
    print("STATE MATRIX PASS: both clocks and six customers all draw, no script error, no blank canvas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
