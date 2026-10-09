"""Build the two Excellence Partner films.

  film_a.js  Partner Intake Phase 0 - the life of one monthly file   (internal, 122 s)
  film_b.js  Your month with ISZE                                      (distributor draft, 76 s)

Each film is drawn on a canvas as a pure function of time, so the same code gives
  - a self-contained HTML player (double-click, play / pause / scrub), and
  - an MP4 rendered frame by frame through headless Chromium + ffmpeg.

Usage (from the ISZE root):
  python 09_meetings/Excellence_Partner_Program_2026/_build/build_films.py            # both, html + mp4
  python 09_meetings/Excellence_Partner_Program_2026/_build/build_films.py a --html   # one film, html only
  python 09_meetings/Excellence_Partner_Program_2026/_build/build_films.py a --frames 10,30,60   # stills (seconds) for QA
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "films"
OUT.mkdir(exist_ok=True)
FPS = 24

FILMS = {
    "a": ("film_a.js", "Partner_Intake_Phase0_Film_Internal_2026-10-09"),
    "b": ("film_b.js", "Excellence_Partner_Your_Month_Film_Distributor_Draft_2026-10-09"),
}

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
html,body{margin:0;height:100%;background:#0d1626;font-family:Segoe UI,system-ui,sans-serif;color:#f7f4ee}
#wrap{display:flex;flex-direction:column;height:100%}
#stage{flex:1;display:flex;align-items:center;justify-content:center;min-height:0}
canvas{max-width:100%;max-height:100%;aspect-ratio:16/9;background:#15233c}
#ui{display:flex;gap:14px;align-items:center;padding:10px 18px;background:#0d1626}
button{background:#c0552d;color:#f7f4ee;border:0;border-radius:6px;padding:7px 16px;font-size:15px;cursor:pointer}
input[type=range]{flex:1;accent-color:#c0552d}
#tm{font-variant-numeric:tabular-nums;min-width:90px;text-align:right;font-size:14px}
.rec #ui{display:none}.rec #stage{align-items:flex-start;justify-content:flex-start}.rec canvas{max-width:none;max-height:none}
</style></head><body>
<div id="wrap"><div id="stage"><canvas id="c" width="1280" height="720"></canvas></div>
<div id="ui"><button id="pp">Pause</button><input id="sc" type="range" min="0" max="1000" value="0"><span id="tm">0:00</span></div></div>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
const W=1280,H=720;
__FILM__
window.__render=function(s){draw(s);};
(function(){
  const rec=/[?&]rec=1/.test(location.search); if(rec){document.body.classList.add('rec');return;}
  let cur=0,playing=true,last=performance.now();
  const pp=document.getElementById('pp'),sc=document.getElementById('sc'),tm=document.getElementById('tm');
  const fmt=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
  function frame(now){ if(playing){cur+=(now-last)/1000; if(cur>=TOTAL){cur=TOTAL;playing=false;pp.textContent='Replay';}} last=now;
    draw(cur); sc.value=cur/TOTAL*1000; tm.textContent=fmt(cur)+' / '+fmt(TOTAL); requestAnimationFrame(frame); }
  pp.onclick=()=>{ if(cur>=TOTAL){cur=0;} playing=!playing; pp.textContent=playing?'Pause':'Play'; };
  sc.oninput=()=>{cur=sc.value/1000*TOTAL; draw(cur);};
  document.addEventListener('keydown',e=>{ if(e.code==='Space'){e.preventDefault();pp.click();} });
  requestAnimationFrame(frame);
})();
</script></body></html>"""


def build(key, html_only=False, stills=None):
    js_name, stem = FILMS[key]
    js = (HERE / js_name).read_text(encoding="utf-8")
    title = [l for l in js.splitlines() if "FILM_TITLE" in l][-1].split("FILM_TITLE='")[1].split("'")[0]
    html = OUT / f"{stem}.html"
    html.write_text(PAGE.replace("__TITLE__", title).replace("__FILM__", js), encoding="utf-8")
    print(html)
    total = int(js.split("const TOTAL=")[1].split(",")[0].split(";")[0])
    if html_only:
        return
    from playwright.sync_api import sync_playwright
    tmp = Path(tempfile.mkdtemp(prefix="film_frames_"))
    times = stills if stills else [i / FPS for i in range(total * FPS + 1)]
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(html.as_uri() + "?rec=1")
        pg.wait_for_timeout(400)
        for i, s in enumerate(times):
            pg.evaluate(f"window.__render({s})")
            pg.screenshot(path=str(tmp / f"f{i:05d}.png"))
        b.close()
    if errs:
        print("PAGE ERRORS:", errs[:5])
        sys.exit(1)
    if stills:
        qa = OUT / "_qa"
        qa.mkdir(exist_ok=True)
        for i, s in enumerate(times):
            shutil.copy(tmp / f"f{i:05d}.png", qa / f"{key}_{s:06.1f}s.png")
        print(f"{len(times)} stills -> {qa}")
    else:
        mp4 = OUT / f"{stem}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%05d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(mp4)], check=True)
        print(mp4, f"{mp4.stat().st_size/1e6:.1f} MB")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    keys = [a for a in args if a in FILMS] or list(FILMS)
    stills = None
    if "--frames" in args:
        stills = [float(x) for x in args[args.index("--frames") + 1].split(",")]
    for k in keys:
        build(k, html_only="--html" in args, stills=stills)
