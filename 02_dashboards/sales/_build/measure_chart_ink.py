"""Per-chart ink measurement.

Crops each chart's box out of the screenshot and counts dark pixels inside it, so a blank canvas is
found by measurement rather than by looking. The canvas positions are read from the live page, not
guessed from the stylesheet.

Usage:
    python 02_dashboards/sales/_build/measure_chart_ink.py
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
WIDTHS = [1440, 1000]


def chrome(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=300)


def page_with_rects(width: int) -> Path:
    """A temp copy of the page that publishes every chart's page coordinates into the DOM."""
    html = HTML.read_text(encoding="utf-8")
    probe = """
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    var out=[];
    document.querySelectorAll('canvas').forEach(function(c){
      var r=c.getBoundingClientRect();
      var ctx=c.getContext('2d');
      var nonWhite=0, sampled=0, colours={};
      try{
        var im=ctx.getImageData(0,0,c.width,c.height).data;
        for(var i=0;i<im.length;i+=4){
          sampled++;
          if(im[i+3]>8 && !(im[i]>250&&im[i+1]>250&&im[i+2]>250)) nonWhite++;
          if(i%4===0){ colours[(im[i]>>4)+','+(im[i+1]>>4)+','+(im[i+2]>>4)]=1; }
        }
      }catch(e){}
      out.push({id:c.id, x:Math.round(r.left), y:Math.round(r.top+window.scrollY),
                w:Math.round(r.width), h:Math.round(r.height),
                cssW:c.width, cssH:c.height, nonWhite:nonWhite, sampled:sampled,
                nonWhitePct: sampled? +(100*nonWhite/sampled).toFixed(2):0,
                colours:Object.keys(colours).length});
    });
    var el=document.createElement('script');
    el.type='application/json'; el.id='probe-rects';
    el.textContent=JSON.stringify({canvases:out, pageH:document.documentElement.scrollHeight});
    document.body.appendChild(el);
  }, 2500);
});
</script>
"""
    tmp = QA / f"_probe_{width}.html"
    tmp.write_text(html.replace("</body>", probe + "</body>"), encoding="utf-8")
    return tmp


def probe_page(width: int, page: Path) -> dict | None:
    d = chrome([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                f"--window-size={width},3200", "--virtual-time-budget=20000",
                "--dump-dom", page.as_uri()]).stdout
    m = re.search(r'<script type="application/json" id="probe-rects">(.*?)</script>', d, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    all_ok = True
    report = {}
    for w in WIDTHS:
        page = page_with_rects(w)
        probe = probe_page(w, page)
        if probe is None:
            print(f"FAIL {w}px: the probe script did not run to completion")
            all_ok = False
            continue
        page_h = int(probe["pageH"]) + 40
        png = QA / f"family_evolution_{w}.png"
        r = chrome([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-sandbox", "--force-device-scale-factor=1",
                    f"--window-size={w},{page_h}", "--virtual-time-budget=20000",
                    f"--screenshot={png}", page.as_uri()])
        if not png.is_file():
            print(f"FAIL {w}px: no screenshot\n{r.stderr[:600]}")
            all_ok = False
            continue
        rects = probe["canvases"]

        img = Image.open(png).convert("RGB")
        a = np.asarray(img).astype(int)
        H, W = a.shape[0], a.shape[1]
        print()
        print("=" * 100)
        print(f"CANVAS INK AT {w}px  (screenshot {W}x{H}, page height {probe['pageH']})")
        print("=" * 100)
        print(f"{'canvas':10s} {'box':>13s} {'drawn px':>10s} {'non-white':>10s} "
              f"{'colours':>8s}  {'dark ink':>9s}  verdict")
        for c in rects:
            x0, y0 = max(0, c["x"]), max(0, c["y"])
            x1, y1 = min(W, c["x"] + c["w"]), min(H, c["y"] + c["h"])
            box = f"{c['w']}x{c['h']}"
            if x1 <= x0 or y1 <= y0:
                print(f"{c['id']:10s} {box:>13s} {c['nonWhitePct']:>9.2f}% {c['colours']:>8d}   "
                      f"OFF-SCREEN  FAIL (screenshot shorter than the page)")
                all_ok = False
                continue
            crop = a[y0:y1, x0:x1]
            lum = crop.sum(axis=2)
            dark = (lum < 700).mean() * 100
            verdict = "ok"
            if c["nonWhitePct"] < 0.4 or c["nonWhite"] < 400:
                verdict = "BLANK"
                all_ok = False
            elif c["colours"] < 4:
                verdict = "TOO FEW COLOURS"
                all_ok = False
            elif dark < 0.15:
                verdict = "no drawn marks"
                all_ok = False
            print(f"{c['id']:10s} {box:>13s} {c['nonWhitePct']:>9.2f}% {c['colours']:>8d}   "
                  f"{dark:>8.2f}%  {verdict}")
            report.setdefault(str(w), []).append(
                {"id": c["id"], "w": c["w"], "h": c["h"], "nonWhitePct": c["nonWhitePct"],
                 "colours": c["colours"], "darkPct": round(float(dark), 3), "verdict": verdict,
                 "nonWhite": c["nonWhite"], "sampled": c["sampled"], "pageHeight": probe["pageH"]})
    (QA / "chart_ink.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print()
    if all_ok:
        print("CHART INK PASS: every canvas has drawn marks on both widths")
        return 0
    print("CHART INK FAIL: see the verdicts above")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
