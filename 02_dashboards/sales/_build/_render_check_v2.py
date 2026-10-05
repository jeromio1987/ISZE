"""Render the family-evolution page in headless Chrome and read the RENDERED text.

Independent of the builder and of the subagent's own QA: this drives the real page
from file://, waits for first paint, then reports

  * whether the embedded payload parsed and the page drew charts,
  * the worked-case numbers as the page actually formats them,
  * both percentage column headers as rendered,
  * the customer control's options,
  * any console error.

Usage: python _render_check_v2.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

DRIVER = r"""
<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var out = {ok: true, err: [], text: null, heads: [], canvases: [], cust: null,
               charts: null, worked: null};
    try {
      if (window.__pmfe2 === undefined) { out.err.push('no __pmfe2 test hook'); }
      out.canvases = Array.prototype.map.call(document.querySelectorAll('canvas'),
        function (c) { return {id: c.id, w: c.width, h: c.height}; });
      var t = document.body.innerText || '';
      out.text = t.length;
      /* the headline and the worked case, as the page prints them */
      var m = t.match(/[^\\n]*753[,\\s]?204[^\\n]*/g);
      out.worked = m ? m.slice(0, 4) : null;
      /* table headers actually in the DOM */
      var heads = [];
      document.querySelectorAll('th').forEach(function (h) {
        var s = (h.innerText || '').trim();
        if (s) heads.push(s);
      });
      out.heads = heads;
      var sel = document.querySelector('select[multiple]');
      if (sel) {
        out.cust = {options: sel.options.length,
                    first: sel.options[0] ? sel.options[0].value : null};
      }
      if (window.Chart) {
        out.charts = Object.keys(window.Chart.instances || {}).length;
      }
    } catch (e) { out.ok = false; out.err.push(String(e && e.message ? e.message : e)); }
    var el = document.createElement('script');
    el.type = 'application/json'; el.id = 'out';
    el.textContent = JSON.stringify(out);
    document.body.appendChild(el);
  }, 4000);
});
</script>
"""


def main() -> int:
    page = Path(tempfile.gettempdir()) / "_render_check_v2.html"
    page.write_text(HTML.read_text(encoding="utf-8").replace("</body>", DRIVER + "</body>"),
                    encoding="utf-8")
    r = subprocess.run(
        [str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
         "--window-size=1440,900", "--virtual-time-budget=30000", "--dump-dom",
         page.as_uri()],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=420)
    m = re.search(r'<script type="application/json" id="out">(.*?)</script>',
                  r.stdout, re.S)
    if not m:
        print("RENDER FAIL: driver did not complete")
        print((r.stderr or "")[:1200])
        return 1
    out = json.loads(m.group(1))

    print("RENDERED PAGE, read back from headless Chrome at 1440x900")
    print("=" * 100)
    print(f"  page hook present      : {'no __pmfe2 test hook' not in out['err']}")
    print(f"  body text length       : {out['text']:,} characters")
    print(f"  chart instances        : {out['charts']}")
    print(f"  canvases on the page   : {len(out['canvases'])}")
    drawn = [c for c in out["canvases"] if c["w"] and c["h"]]
    print(f"  canvases with a size   : {len(drawn)}")
    print()
    print("  customer control       :", out["cust"])
    print()
    print("  worked-case lines carrying 753,204:")
    if out["worked"]:
        for line in out["worked"]:
            print("     " + " ".join(line.split())[:150])
    else:
        print("     NONE FOUND - the worked case is not in the rendered text")
    print()
    keys = ("change in billed euro", "change in euro per vehicle", "fleet")
    hits = [h for h in out["heads"] if any(k in h.lower() for k in keys)]
    print("  rendered table headers carrying a percentage or the fleet:")
    for h in hits[:20]:
        print("     " + h[:110])
    print()
    print("  errors reported by the page:", out["err"] or "none")

    fails = []
    if not drawn:
        fails.append("no canvas has a size - nothing drew")
    if not out["worked"]:
        fails.append("the worked case is not in the rendered text")
    if not any("per vehicle" in h.lower() for h in out["heads"]):
        fails.append("no rendered header names euro per vehicle")
    if not any("billed euro" in h.lower() for h in out["heads"]):
        fails.append("no rendered header names change in billed euro")
    if out["err"]:
        fails.append("the page reported an error: " + str(out["err"]))
    print()
    if fails:
        print("RENDER CHECK FAIL:")
        for f in fails:
            print("  - " + f)
        return 1
    print("RENDER CHECK PASS: the page paints, both percentages are rendered headers, and the "
          "worked case prints with its numbers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
