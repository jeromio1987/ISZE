"""Read the rendered page's text back, so the headline claims are checked rather than eyeballed."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_Deep.html"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

PROBE = r"""
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    function txt(id){ var e=document.getElementById(id); return e? e.textContent.replace(/\s+/g,' ').trim() : null; }
    var kpis=[];
    document.querySelectorAll('#kpis .kpi').forEach(function(k){
      kpis.push({v:k.querySelector('.v').textContent.trim(),
                 l:k.querySelector('.l').textContent.trim(),
                 s:k.querySelector('.s')?k.querySelector('.s').textContent.trim():null});});
    var rows=[];
    document.querySelectorAll('#t_before tbody tr').forEach(function(tr){
      rows.push(Array.prototype.map.call(tr.querySelectorAll('td'),function(td){
        return td.textContent.replace(/\s+/g,' ').trim();}).join(' | '));});
    var o={kpis:kpis, beforeTable:rows, clockNote:txt('clockNote'), lane:txt('laneNotice'),
           n_funnel:txt('n_funnel'), n_before:txt('n_before'), foot:txt('foot'),
           funnelKey:txt('k_funnel'), beforeKey:txt('k_before'), title:document.title,
           drillKey:txt('k_drill'), drillLabels:(function(){
             var c=document.getElementById('c_drill');
             return c? 'present':'missing';})()};
    var el=document.createElement('script');
    el.type='application/json'; el.id='probe-out';
    el.textContent=JSON.stringify(o);
    document.body.appendChild(el);
  }, 3000);
});
</script>
"""


def main() -> int:
    page = HTML.parent / "_qa_family_deep" / "_text_probe.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", PROBE + "</body>"),
                    encoding="utf-8")
    r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--window-size=1440,4000", "--virtual-time-budget=25000", "--dump-dom",
                        page.as_uri()], capture_output=True, text=True, timeout=420)
    m = re.search(r'<script type="application/json" id="probe-out">(.*?)</script>', r.stdout, re.S)
    if not m:
        print("PROBE FAIL")
        print((r.stderr or "")[:600])
        return 1
    o = json.loads(m.group(1))
    print("TITLE:", o["title"])
    print()
    print("HEADLINE FIGURES AS RENDERED")
    print("-" * 100)
    for k in o["kpis"]:
        print(f"  {k['v']:>22s}   {k['l']}")
        if k["s"]:
            print(f"  {'':>22s}   -> {k['s']}")
    print()
    print("CLOCK NOTE:", o["clockNote"])
    print()
    print("LANE NOTICE:", (o["lane"] or "")[:340])
    print()
    print("FUNNEL KEY:", o["funnelKey"])
    print()
    print("BEFORE/AFTER TABLE, as rendered")
    print("-" * 100)
    for r_ in o["beforeTable"]:
        print("  " + r_)
    print()
    print("BEFORE/AFTER NOTE:", (o["n_before"] or "")[:600])
    print()
    print("FOOT:", (o["foot"] or "")[:700])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
