#!/usr/bin/env python3
"""Prove the ISZE (April-March) clock divides by the right calendar year.

A financial year named by its closing year — ISZE 2024 — spends the calendar-2023 fleet, because
April 2023 to March 2024 is overwhelmingly calendar 2023. This drives the page's own control and
compares each ISZE period's denominator with the calendar year it should be using.

Usage:
    python 02_dashboards/sales/_build/qa_uio_year_fy_clock.py
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
    var out={fail:[], cyRows:null, fyRows:null};
    try{
      var T=window.__deepTest;
      T.set({cust:['ITUK'], fam:'n_series_truck', clock:'CY', metric:'abs', fleet:'yearly'});
      out.cyRows=T.rateProof('ITUK','n_series_truck').rows;
      T.set({clock:'FY'});
      out.fyRows=T.rateProof('ITUK','n_series_truck').rows;
      /* ISZE 2024 must carry the calendar-2023 count; ISZE 2027 must carry calendar 2026 */
      var cy=null, fy=null;
      out.cyRows.forEach(function(r){ cy=cy||{}; cy[r.period]=r.fleetUsed; });
      out.fyRows.forEach(function(r){ fy=fy||{}; fy[r.period]=r.fleetUsed; });
      out.cyMap=cy; out.fyMap=fy;
      Object.keys(fy).forEach(function(p){
        var expect=cy[String(Number(p)-1)];
        if(expect===undefined) return;
        if(fy[p]!==expect){
          out.fail.push('ISZE '+p+' divided by '+fy[p]+' vehicles, but the calendar-'
            +(Number(p)-1)+' fleet is '+expect);
        }
      });
      if(!Object.keys(fy).length) out.fail.push('the ISZE clock produced no periods');
      if(!Object.keys(cy).length) out.fail.push('the calendar clock produced no periods');
    }catch(e){ out.fail.push('driver threw: '+String(e&&e.message?e.message:e)); }
    var el=document.createElement('script');
    el.type='application/json'; el.id='fy-out';
    el.textContent=JSON.stringify(out);
    document.body.appendChild(el);
  }, 3600);
});
</script>
"""


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    page = QA / "_uio_fy_qa.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", DRIVER + "</body>"),
                    encoding="utf-8")
    r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--window-size=1440,3000", "--virtual-time-budget=40000", "--dump-dom",
                        page.as_uri()], capture_output=True, text=True, timeout=420)
    m = re.search(r'<script type="application/json" id="fy-out">(.*?)</script>', r.stdout, re.S)
    if not m:
        print("FY-CLOCK QA FAIL: the driver did not run to completion")
        print((r.stderr or "")[:800])
        return 1
    out = json.loads(m.group(1))
    print("DOES THE ISZE (APRIL-MARCH) CLOCK DIVIDE BY THE RIGHT CALENDAR YEAR?")
    print("=" * 104)
    print(f"  {'ISZE period':>12} {'own fleet used':>15} {'calendar year before':>22} {'same?':>7}")
    for p in sorted(int(k) for k in out.get("fyMap", {})):
        used = out["fyMap"][str(p)]
        expect = out["cyMap"].get(str(p - 1))
        same = "yes" if used == expect else ("no count" if expect is None else "NO")
        print(f"  {p:>12} {str(used):>15} {str(expect):>22} {same:>7}")
    print()
    if out["fail"]:
        print("FY-CLOCK QA FAIL:")
        for f in out["fail"]:
            print("  - " + f)
        return 1
    print("FY-CLOCK QA PASS: every ISZE period divides by the calendar year it starts in, so the "
          "April-March clock is not silently reusing the closing year's fleet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
