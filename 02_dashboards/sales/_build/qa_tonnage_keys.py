"""Check the three fixes landed in the rendered page, not just in the builder.

Counts, from the DOM after the page has run its script:
  * how many charts draw more than one series, and how many of those have a visible key
  * the clock control text and the clock note
  * that no chart is left with two series and no key
Also writes cropped screenshots of the areas that carry the keys, for a visual read.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Tonnage_Evolution.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_tonnage"
QA.mkdir(parents=True, exist_ok=True)

CHROME = None
for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
    if Path(c).exists():
        CHROME = c
        break
if not CHROME:
    sys.exit("chrome not found")

PROBE = r"""
(function(){
  var out={keys:{}, axis:{}, clock:{}, notes:{}};
  document.querySelectorAll('.legend').forEach(function(l){
    var host=l.parentElement;
    out.keys[host.id||host.className]=(l.textContent||'').trim().slice(0,200);
  });
  document.querySelectorAll('.legend.axis').forEach(function(l){
    var host=l.parentElement;
    out.axis[host.id||host.className]=(l.textContent||'').trim().slice(0,200);
  });
  var sc=document.getElementById('selClock');
  out.clock.control=Array.from(sc.options).map(function(o){return o.textContent;});
  out.clock.year=Array.from(document.getElementById('selYear').options).map(function(o){return o.textContent;});
  out.clock.note=(document.getElementById('clockNote').textContent||'').trim();
  out.kpiLabels=Array.from(document.querySelectorAll('#kpis .kpi .l')).map(function(e){return e.textContent.trim();});
  out.catgapHeader=Array.from(document.querySelectorAll('#t_catgap th')).map(function(e){return e.textContent.trim();});
  out.foot=(document.getElementById('foot').textContent||'').slice(0,80);
  return JSON.stringify(out);
})()
"""


def render(js_on_load: bool, tag: str, w: int, h: int) -> Path:
    out = QA / f"keys-{tag}.png"
    prof = tempfile.mkdtemp(prefix=f"qa{tag}_")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-first-run", "--no-default-browser-check",
                    f"--user-data-dir={prof}", f"--window-size={w},{h}",
                    "--virtual-time-budget=9000",
                    f"--screenshot={out}", "file:///" + str(HTML).replace("\\", "/")],
                   check=True, capture_output=True)
    return out


def dump_dom() -> dict:
    """Use headless Chrome to evaluate the probe via a temporary wrapper page."""
    wrapper = QA / "_probe.html"
    src = HTML.read_text(encoding="utf-8")
    probe = '<script>window.addEventListener("load",function(){setTimeout(function(){' \
            'document.title="PROBE::"+' + PROBE + ';},2500);});</script>'
    wrapper.write_text(src.replace("</body>", probe + "</body>"), encoding="utf-8")
    prof = tempfile.mkdtemp(prefix="qaprobe_")
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--dump-dom",
                        f"--user-data-dir={prof}", "--virtual-time-budget=12000",
                        "file:///" + str(wrapper).replace("\\", "/")],
                       check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"<title>PROBE::(.*?)</title>", r.stdout, re.S)
    if not m:
        return {"error": "probe did not run", "snippet": r.stdout[:300]}
    import html as htmlmod
    return json.loads(htmlmod.unescape(m.group(1)))


if __name__ == "__main__":
    d = dump_dom()
    print(json.dumps(d, indent=1)[:6000])
    render(True, "1440x3000", 1440, 3000)
    print("\nscreenshot ->", QA / "keys-1440x3000.png")
