"""Read the band cards and the two band tables back as text, so the copy can be checked."""
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
    o={};
    function txt(id){var e=document.getElementById(id);return e?e.textContent.replace(/\s+/g,' ').trim():null;}
    function cards(){var out=[];document.querySelectorAll('#band_cards .bandcard').forEach(function(c){
      out.push(c.textContent.replace(/\s+/g,' ').trim());});return out;}
    function table(id){var out=[];document.querySelectorAll('#'+id+' tbody tr').forEach(function(tr){
      out.push(Array.prototype.map.call(tr.querySelectorAll('td'),function(td){
        return td.textContent.replace(/\s+/g,' ').trim();}).join(' | '));});return out;}
    window.__deepTest.set({cust:ALL18, fam:'n_series_truck', clock:'CY', reset:true});
    o.cardsCY=cards(); o.splitCY=table('t_bandsplit'); o.evCY=table('t_bandev');
    o.intro=txt('bands_intro'); o.nband=txt('n_band'); o.nsplit=txt('n_bandsplit');
    o.smbands=txt('k_smbands'); o.ndrill=txt('n_drill'); o.edrill=txt('k_drill');
    window.__deepTest.set({clock:'FY'});
    o.cardsFY=cards();
    var el=document.createElement('script'); el.type='application/json'; el.id='txt-out';
    el.textContent=JSON.stringify(o);
    document.body.appendChild(el);
  }, 3400);
});
</script>
"""


def main() -> int:
    page = QA / "_bandtext.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace(
        "</body>", DRIVER.replace("ALL18", json.dumps(ALL18)) + "</body>"), encoding="utf-8")
    dom = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                          "--window-size=1440,3000", "--virtual-time-budget=35000", "--dump-dom",
                          page.as_uri()], capture_output=True, text=True, timeout=420).stdout
    m = re.search(r'<script type="application/json" id="txt-out">(.*?)</script>', dom, re.S)
    if not m:
        print("PROBE FAIL")
        return 1
    o = json.loads(m.group(1))
    print("=" * 104)
    print("BAND CARDS, CY")
    for c in o["cardsCY"]:
        print("  * " + c)
    print()
    print("=" * 104)
    print("EXCLUSIVE VERSUS SHARED TABLE")
    for r in o["splitCY"]:
        print("  " + r)
    print()
    print("=" * 104)
    print("SOURCED SERIES TABLE")
    for r in o["evCY"]:
        print("  " + r[:190])
    print()
    print("=" * 104)
    print("INTRO:", o["intro"])
    print()
    print("CHART NOTE:", o["nband"])
    print()
    print("TABLE NOTE:", o["nsplit"])
    print()
    print("SMALL MULTIPLES KEY:", o["smbands"])
    print()
    print("DRILL NOTE:", o["ndrill"])
    print()
    print("DRILL KEY:", o["edrill"])
    print()
    print("=" * 104)
    print("BAND CARDS, FY")
    for c in o["cardsFY"]:
        print("  * " + c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
