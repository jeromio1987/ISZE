# -*- coding: utf-8 -*-
"""Build Don't Lose the Deal cinematic motion HTML + OPEN cmd + optional mp4."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ROOT / "Isuzu Universe" / "01_Strategy"
HTML_NAME = "DLOD_OPEX_MOTION_FILM_2026-10-08.html"
CMD_NAME = "OPEN_DLOD_OPEX_MOTION_FILM_2026-10-08.cmd"
MP4_NAME = "DLOD_OPEX_MOTION_FILM_2026-10-08.mp4"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Don't Lose the Deal — OPEX that buys the job</title>
<style>
:root{
  --navy:#0c1524;
  --paper:#f7f4ee;
  --ink:#e8e2d6;
  --mute:#9aa3b2;
  --terra:#c0552d;
  --terra2:#e07848;
  --amber:#d4a017;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#05080f;color:var(--ink);font-family:"Segoe UI",system-ui,sans-serif;overflow:hidden}
.stage{position:relative;width:100vw;height:100vh;background:radial-gradient(1200px 700px at 70% 20%,#1a2b4a 0%,#05080f 55%)}
.scene{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:7vh 8vw;opacity:0;pointer-events:none;transform:translateY(18px) scale(0.985);transition:opacity .7s ease, transform .9s cubic-bezier(.2,.8,.2,1)}
.scene.on{opacity:1;pointer-events:auto;transform:none}
.kicker{font-size:13px;letter-spacing:.22em;text-transform:uppercase;color:var(--terra2);margin-bottom:18px;font-weight:600}
h1{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:clamp(34px,5.2vw,64px);line-height:1.08;color:var(--paper);max-width:16ch}
h2{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:clamp(28px,3.8vw,46px);line-height:1.15;color:var(--paper);max-width:22ch;margin-bottom:18px}
.sub{margin-top:18px;font-size:clamp(16px,1.6vw,22px);color:var(--mute);max-width:46ch;line-height:1.45}
.big{font-family:Georgia,serif;font-size:clamp(56px,9vw,110px);color:var(--terra2);line-height:1;margin:10px 0 8px}
.big small{display:block;font-size:.28em;letter-spacing:.08em;color:var(--mute);margin-top:10px;font-family:"Segoe UI",system-ui,sans-serif}
.row{display:flex;gap:28px;flex-wrap:wrap;margin-top:28px}
.card{background:rgba(21,35,60,.72);border:1px solid rgba(247,244,238,.08);border-left:4px solid var(--terra);padding:18px 22px;min-width:180px}
.card .n{font-family:Georgia,serif;font-size:34px;color:var(--paper)}
.card .l{font-size:13px;color:var(--mute);margin-top:6px;max-width:18ch}
.barwrap{margin-top:34px;max-width:720px}
.barlab{display:flex;justify-content:space-between;font-size:13px;color:var(--mute);margin-bottom:8px}
.track{height:18px;background:rgba(247,244,238,.08);border-radius:2px;overflow:hidden}
.fill{height:100%;width:0;background:linear-gradient(90deg,var(--terra),var(--terra2));transition:width 1.4s cubic-bezier(.2,.8,.2,1)}
.fill.on{width:var(--w)}
.layers{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-top:28px;max-width:980px}
.layer{padding:20px;background:rgba(12,21,36,.85);border:1px solid rgba(247,244,238,.1)}
.layer h3{font-family:Georgia,serif;font-size:18px;color:var(--paper);margin-bottom:8px}
.layer p{font-size:14px;color:var(--mute);line-height:1.4}
.layer .pct{font-family:Georgia,serif;font-size:40px;color:var(--terra2);margin:10px 0}
.warn{margin-top:24px;padding:16px 18px;border:1px solid rgba(212,160,23,.45);background:rgba(212,160,23,.08);color:#f0d78c;max-width:52ch;font-size:15px;line-height:1.4}
.ladder{margin-top:26px;display:flex;flex-direction:column;gap:12px;max-width:640px}
.step{display:flex;align-items:center;gap:16px;padding:14px 16px;background:rgba(21,35,60,.7);border:1px solid rgba(247,244,238,.08)}
.step .tag{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--terra2);min-width:72px}
.step .amt{font-family:Georgia,serif;font-size:26px;color:var(--paper);min-width:140px}
.step .why{font-size:14px;color:var(--mute)}
.footer{position:absolute;left:8vw;right:8vw;bottom:4.5vh;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--mute);letter-spacing:.04em;z-index:5}
.prog{position:absolute;left:0;bottom:0;height:3px;background:var(--terra);width:0;z-index:6;transition:width .25s linear}
.grain{pointer-events:none;position:absolute;inset:0;opacity:.05;z-index:2;
  background-image:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,.015) 2px,rgba(255,255,255,.015) 3px)}
.vline{position:absolute;left:8vw;top:0;bottom:0;width:1px;background:linear-gradient(transparent,rgba(192,85,45,.5),transparent);opacity:.35}
#clickhint{position:absolute;right:8vw;top:5vh;font-size:12px;color:var(--mute);z-index:5}
</style>
</head>
<body>
<div class="stage" id="stage">
  <div class="grain"></div>
  <div class="vline"></div>
  <div id="clickhint">Space / click — next · Autoplay on</div>

  <section class="scene on" data-t="0">
    <div class="kicker">Cold open</div>
    <h1>Customer at the counter. The price is wrong.</h1>
    <p class="sub">He walks. The job walks. The parts walk with him — usually to an independent, a used part, or the internet.</p>
  </section>

  <section class="scene" data-t="7000">
    <div class="kicker">The opex lever</div>
    <h1>Don't Lose the Deal</h1>
    <p class="sub">Not a slogan. A signed ISZE–ITUK agreement: operating spend that buys the right to keep the workshop job when the competitor's price is hostile.</p>
  </section>

  <section class="scene" data-t="15000">
    <div class="kicker">The MOA — 1 April 2025</div>
    <div class="big">EUR 30,000<small>ISZE pays ITUK · one fiscal year</small></div>
    <p class="sub">One hard condition in the signed paper: ITUK must send the Don't Lose the Deal activity record. No margin clause. No dealer keep-rate. No Japan per-case approval line.</p>
  </section>

  <section class="scene" data-t="24000">
    <div class="kicker">What the register actually did</div>
    <h2>Duncan's deal file — measured, not modelled</h2>
    <div class="row">
      <div class="card"><div class="n" data-count="54922" data-prefix="£">0</div><div class="l">ITUK support logged</div></div>
      <div class="card"><div class="n" data-count="218">0</div><div class="l">regional deal lines</div></div>
      <div class="card"><div class="n" data-count="86" data-prefix="£">0</div><div class="l">median support / case</div></div>
      <div class="card"><div class="n" data-count="172" data-prefix="£">0</div><div class="l">average (few big jobs)</div></div>
    </div>
  </section>

  <section class="scene" data-t="34000">
    <div class="kicker">Three margin layers — never blend them</div>
    <div class="layers">
      <div class="layer"><h3>MOA</h3><div class="pct">—</div><p>Signed paper. Money + activity record. Silent on %GM.</p></div>
      <div class="layer"><h3>ISZE GP</h3><div class="pct">~50%</div><p>Your mail to Yoshimoto on those deals. Our margin. About 5.5× on EUR 30k.</p></div>
      <div class="layer"><h3>ITUK after offer</h3><div class="pct">~43%</div><p>Duncan register: ~47% before the deal price, ~41–43% median after. Still above cost.</p></div>
    </div>
  </section>

  <section class="scene" data-t="44000">
    <div class="kicker">The hole in the story</div>
    <div class="big">1 <span style="font-size:.45em;color:var(--mute)">of</span> 218<small>competitor prices filled</small></div>
    <div class="warn">Without the competing offer on the line, EUR 30,000 is a rebate you cannot defend. With it, the same money becomes a measured sales-defence machine.</div>
    <div class="barwrap">
      <div class="barlab"><span>Evidence fill</span><span>0.5%</span></div>
      <div class="track"><div class="fill" style="--w:0.5%"></div></div>
    </div>
  </section>

  <section class="scene" data-t="54000">
    <div class="kicker">Why this is an opex → sales lever</div>
    <h2>Small cash. Large counter moments.</h2>
    <p class="sub">Half a percent of a distributor's parts billed is the scaling frame — for ITUK that sits near the EUR 30k you already run. The return is not the spend. The return is the job that did not leave the network, and the parts family that stayed genuine.</p>
    <div class="barwrap" style="margin-top:32px">
      <div class="barlab"><span>EUR 30k vs ITUK FY parts billed</span><span>~0.5%</span></div>
      <div class="track"><div class="fill" style="--w:50%"></div></div>
    </div>
  </section>

  <section class="scene" data-t="64000">
    <div class="kicker">Next week's Japan ask — a ladder, not a fog</div>
    <div class="ladder">
      <div class="step"><div class="tag">Floor</div><div class="amt">EUR 30k</div><div class="why">Confirm the existing ITUK Don't Lose the Deal line</div></div>
      <div class="step"><div class="tag">Stretch</div><div class="amt">EUR 70–80k</div><div class="why">Pilot IUK + one book market — only with evidence rules</div></div>
      <div class="step"><div class="tag">Later</div><div class="amt">~EUR 163k</div><div class="why">Full-book 0.5% — after the pilot can prove wins</div></div>
    </div>
  </section>

  <section class="scene" data-t="74000">
    <div class="kicker">The mind-blower is not the money</div>
    <h1>OPEX that refuses to lose the workshop.</h1>
    <p class="sub">EUR 30,000 is tiny next to parts billed. What changes a Managing Director conversation is proof: competitor price on the line, case → credit, margin still held, jobs kept. That is the enabler. Everything else is a discount with better stationery.</p>
  </section>

  <div class="footer">
    <span>Don't Lose the Deal · internal · 8 Oct 2026</span>
    <span id="clock">0:00</span>
  </div>
  <div class="prog" id="prog"></div>
</div>
<script>
(function(){
  const scenes=[...document.querySelectorAll('.scene')];
  const total=82000;
  let t0=performance.now();
  let idx=0;
  let paused=false;
  const prog=document.getElementById('prog');
  const clock=document.getElementById('clock');

  function show(i){
    idx=Math.max(0,Math.min(scenes.length-1,i));
    scenes.forEach((s,j)=>s.classList.toggle('on',j===idx));
    scenes[idx].querySelectorAll('.fill').forEach(el=>{
      el.classList.remove('on');
      requestAnimationFrame(()=>el.classList.add('on'));
    });
    scenes[idx].querySelectorAll('[data-count]').forEach(el=>{
      const target=+el.dataset.count;
      const prefix=el.dataset.prefix||'';
      const suffix=el.dataset.suffix||'';
      const start=performance.now();
      const dur=1100;
      function tick(now){
        const p=Math.min(1,(now-start)/dur);
        const eased=1-Math.pow(1-p,3);
        const v=Math.round(target*eased);
        el.textContent=prefix+v.toLocaleString('en-GB')+suffix;
        if(p<1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  function sync(ms){
    let i=0;
    for(let k=0;k<scenes.length;k++){
      if(+scenes[k].dataset.t<=ms) i=k;
    }
    if(i!==idx) show(i);
    prog.style.width=((ms/total)*100)+'%';
    const s=Math.floor(ms/1000);
    clock.textContent=(Math.floor(s/60))+':'+(('0'+(s%60)).slice(-2));
  }

  function loop(now){
    if(!paused){
      const ms=now-t0;
      if(ms>=total){ sync(total-1); return; }
      sync(ms);
    }
    requestAnimationFrame(loop);
  }

  function jump(dir){
    show(idx+dir);
    t0=performance.now()-+scenes[idx].dataset.t;
  }

  document.addEventListener('keydown',e=>{
    if(e.code==='Space'){e.preventDefault();jump(1)}
    if(e.code==='ArrowRight')jump(1);
    if(e.code==='ArrowLeft')jump(-1);
    if(e.code==='KeyP'){paused=!paused; if(!paused) t0=performance.now()-+scenes[idx].dataset.t;}
  });
  document.getElementById('stage').addEventListener('click',()=>jump(1));

  show(0);
  requestAnimationFrame(loop);
})();
</script>
</body>
</html>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html_path = OUT_DIR / HTML_NAME
    html_path.write_text(HTML, encoding="utf-8")
    cmd_path = OUT_DIR / CMD_NAME
    cmd_path.write_bytes(
        f'@echo off\r\nstart "" "%~dp0{HTML_NAME}"\r\n'.encode("ascii")
    )
    print("WROTE", html_path, html_path.stat().st_size)
    print("WROTE", cmd_path)


if __name__ == "__main__":
    main()
