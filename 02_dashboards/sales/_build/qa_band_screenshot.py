"""Screenshot the N-series tonnage section on its own, so the band cards and tables are read
at full resolution rather than skimmed off a 10,000-pixel page."""
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

# hide the rest of the page so the band section paints at the top, then shoot it
DRIVER = r"""
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    window.__deepTest.set({cust:ALL18, fam:'n_series_truck', clock:'CY', reset:true});
    document.querySelectorAll('body > header, body > .wrap > *').forEach(function(n){
      if(n.id!=='sec_bands'){ n.style.display='none'; }
    });
    var s=document.getElementById('sec_bands');
    if(s){ s.style.paddingTop='0'; }
    var b=document.querySelector('.wrap');
    if(b){ b.style.padding='0 32px 40px'; }
    var el=document.createElement('script'); el.type='application/json'; el.id='shot-out';
    el.textContent=JSON.stringify({h:document.documentElement.scrollHeight});
    document.body.appendChild(el);
  }, 3200);
});
</script>
"""


def main() -> int:
    page = QA / "_bands_only.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", DRIVER + "</body>"),
                    encoding="utf-8")
    dom = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                          "--window-size=1440,4000", "--virtual-time-budget=25000", "--dump-dom",
                          page.as_uri()], capture_output=True, text=True, timeout=420).stdout
    m = re.search(r'<script type="application/json" id="shot-out">(.*?)</script>', dom, re.S)
    h = int(json.loads(m.group(1))["h"]) + 40 if m else 4000
    for w, name in ((1440, "bands_1440.png"), (1000, "bands_1000.png")):
        out = QA / name
        subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-sandbox", "--force-device-scale-factor=1",
                        f"--window-size={w},{h}", "--virtual-time-budget=25000",
                        f"--screenshot={out}", page.as_uri()],
                       capture_output=True, timeout=420)
        print(f"wrote {out}  {out.stat().st_size if out.is_file() else 'MISSING'} bytes  "
              f"({w}x{h})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
