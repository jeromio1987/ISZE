"""Ink measurement for the deep family page.

Measures dark pixels per canvas from the rendered screenshot, and counts the drawn marks from the
canvas pixel buffer itself. A blank canvas is found by measurement, not by reading a screenshot.

Also verifies the thing the last page shipped without: a written key for every chart that carries
more than one series. That is checked in the DOM, not asserted.

Usage:
    python 02_dashboards/sales/_build/measure_deep_chart_ink.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_Deep.html"
QA = ROOT / "02_dashboards" / "sales" / "_qa_family_deep"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
WIDTHS = [1440, 1000]

PROBE = r"""
<script>
window.addEventListener('load',function(){
  setTimeout(function(){
    var out=[], multi=[], keys=[];
    document.querySelectorAll('canvas').forEach(function(c){
      var r=c.getBoundingClientRect();
      var ctx=c.getContext('2d');
      var nonWhite=0, sampled=0, colours={};
      try{
        var im=ctx.getImageData(0,0,c.width,c.height).data;
        for(var i=0;i<im.length;i+=4){
          sampled++;
          if(im[i+3]>8 && !(im[i]>250&&im[i+1]>250&&im[i+2]>250)) nonWhite++;
          colours[(im[i]>>4)+','+(im[i+1]>>4)+','+(im[i+2]>>4)]=1;
        }
      }catch(e){}
      out.push({id:c.id, x:Math.round(r.left), y:Math.round(r.top+window.scrollY),
                w:Math.round(r.width), h:Math.round(r.height),
                cw:c.width, ch:c.height, nonWhite:nonWhite, sampled:sampled,
                nonWhitePct: sampled? +(100*nonWhite/sampled).toFixed(2):0,
                colours:Object.keys(colours).length});
    });
    /* every canvas that belongs to a chart with more than one series must sit in a panel that
       carries a written key in words */
    var panels=document.querySelectorAll('.card');
    panels.forEach(function(p){
      var cv=p.querySelectorAll('canvas');
      if(cv.length!==1) return;
      var key=p.querySelector('.key');
      keys.push({canvas:cv[0].id,
                 text: key? key.textContent.replace(/\s+/g,' ').trim().slice(0,300) : null,
                 chips: key? key.querySelectorAll('span').length : 0,
                 words: key? key.textContent.replace(/\s+/g,' ').trim().split(' ').filter(function(w){return w.length>2;}).length : 0});
    });
    var el=document.createElement('script');
    el.type='application/json'; el.id='probe-out';
    el.textContent=JSON.stringify({canvases:out, keys:keys,
                                   pageH:document.documentElement.scrollHeight,
                                   title:document.title});
    document.body.appendChild(el);
  }, 3000);
});
</script>
"""


def chrome(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=420)


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    html = HTML.read_text(encoding="utf-8")
    page = QA / "_probe.html"
    page.write_text(html.replace("</body>", PROBE + "</body>"), encoding="utf-8")

    ok = True
    report = {}
    for w in WIDTHS:
        dom = chrome([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                      f"--window-size={w},4000", "--virtual-time-budget=25000",
                      "--dump-dom", page.as_uri()]).stdout
        m = re.search(r'<script type="application/json" id="probe-out">(.*?)</script>', dom, re.S)
        if not m:
            print(f"FAIL {w}px: the probe did not run to completion")
            ok = False
            continue
        probe = json.loads(m.group(1))
        page_h = int(probe["pageH"]) + 60
        png = QA / f"deep_{w}.png"
        r = chrome([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-sandbox", "--force-device-scale-factor=1",
                    f"--window-size={w},{page_h}", "--virtual-time-budget=25000",
                    f"--screenshot={png}", page.as_uri()])
        if not png.is_file():
            print(f"FAIL {w}px: no screenshot\n{r.stderr[:600]}")
            ok = False
            continue
        img = Image.open(png).convert("RGB")
        a = np.asarray(img).astype(int)
        H, W = a.shape[0], a.shape[1]
        print()
        print("=" * 104)
        print(f"CANVAS INK AT {w}px  (screenshot {W}x{H}, page height {probe['pageH']}, "
              f"{len(probe['canvases'])} canvases)")
        print("=" * 104)
        print(f"{'canvas':12s} {'box':>12s} {'painted':>9s} {'colours':>8s} {'dark ink':>9s}  verdict")
        for c in probe["canvases"]:
            x0, y0 = max(0, c["x"]), max(0, c["y"])
            x1, y1 = min(W, c["x"] + c["w"]), min(H, c["y"] + c["h"])
            box = f"{c['w']}x{c['h']}"
            if x1 <= x0 or y1 <= y0:
                print(f"{c['id']:12s} {box:>12s} {c['nonWhitePct']:>8.2f}% "
                      f"{c['colours']:>8d}   OFF-SCREEN  FAIL")
                ok = False
                continue
            crop = a[y0:y1, x0:x1]
            dark = (crop.sum(axis=2) < 700).mean() * 100
            verdict = "ok"
            if c["nonWhitePct"] < 0.4 or c["nonWhite"] < 400:
                verdict = "BLANK"
                ok = False
            elif c["colours"] < 4:
                verdict = "TOO FEW COLOURS"
                ok = False
            elif dark < 0.15:
                verdict = "no drawn marks"
                ok = False
            print(f"{c['id']:12s} {box:>12s} {c['nonWhitePct']:>8.2f}% {c['colours']:>8d} "
                  f"{dark:>8.2f}%  {verdict}")
            report.setdefault(str(w), []).append(
                {"id": c["id"], "w": c["w"], "h": c["h"], "nonWhitePct": c["nonWhitePct"],
                 "colours": c["colours"], "darkPct": round(float(dark), 3), "verdict": verdict})
        if w == WIDTHS[0]:
            print()
            print("WRITTEN KEYS, read from the DOM at", w, "px")
            print("-" * 104)
            for k in probe["keys"]:
                if k["text"] is None:
                    print(f"  {k['canvas']:12s} NO KEY ELEMENT  FAIL")
                    ok = False
                elif k["words"] < 4:
                    print(f"  {k['canvas']:12s} key too short: {k['text']!r}  FAIL")
                    ok = False
                else:
                    print(f"  {k['canvas']:12s} {k['chips']} keyed item(s): {k['text'][:96]}...")
            report["keys"] = probe["keys"]
    (QA / "deep_chart_ink.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print()
    if ok:
        print("DEEP CHART INK PASS: every canvas painted on both widths and every panel carries a "
              "written key")
        return 0
    print("DEEP CHART INK FAIL: see the verdicts above")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
