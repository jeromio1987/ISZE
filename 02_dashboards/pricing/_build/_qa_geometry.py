"""Geometry check for the two new sections: clipped text, overflowing tables,
overlapping blocks. Better evidence than squinting at a screenshot.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
            r"\ISZE_Pricing_Revision_AIM_Source.html")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_qa")
PORT = 9880 + (os.getpid() % 200)
CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

PROBE = r"""
(function(){
  function box(e){ var r=e.getBoundingClientRect();
    return {x:r.left,y:r.top,w:r.width,h:r.height}; }
  function overlap(a,b){
    var ox=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x);
    var oy=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);
    return (ox>1&&oy>1) ? {ox:Math.round(ox),oy:Math.round(oy)} : null;
  }
  var out={clipped:[],overlap:[],tables:{},canvas:[],mising:[]};

  /* text that is cut off by its own box */
  ['#conc-figs','#brake-figs','#t-conc','#t-brake','#q-conc','#q-brake','#brake-crumb',
   '#concscope','#c-conc','#c-brake'].forEach(function(sel){
    var e=document.querySelector(sel);
    if(!e){ out.mising.push(sel); return; }
    if(e.scrollWidth > e.clientWidth+2 || e.scrollHeight > e.clientHeight+2){
      out.clipped.push({sel:sel, sw:e.scrollWidth, cw:e.clientWidth,
                        sh:e.scrollHeight, ch:e.clientHeight});
    }
  });

  /* every rendered text node inside the new sections: is it inside its parent? */
  function textOverflow(root, label){
    var bad=[];
    Array.prototype.forEach.call(root.querySelectorAll('*'), function(e){
      if(!e.textContent || !e.textContent.trim()) return;
      if(e.children.length) return;
      var r=e.getBoundingClientRect(), p=e.parentElement.getBoundingClientRect();
      if(r.width<1||r.height<1) return;
      if(r.right > p.right+2 || r.bottom > p.bottom+2 || r.left < p.left-2){
        bad.push({tag:e.tagName, cls:e.className, txt:e.textContent.trim().slice(0,40),
                  er:Math.round(r.right), pr:Math.round(p.right),
                  eb:Math.round(r.bottom), pb:Math.round(p.bottom)});
      }
    });
    return bad.slice(0,8);
  }
  ['#conc-figs','#brake-figs','#brake-l2wrap','#brake-crumb'].forEach(function(sel){
    var e=document.querySelector(sel);
    if(e) out.tables[sel]=textOverflow(e, sel);
  });

  /* do the figure blocks and the chart collide? */
  var f1=document.querySelector('#conc-figs'), ch1=document.querySelector('#c-conc');
  if(f1&&ch1) out.overlap.push({pair:'conc figs/chart', o:overlap(box(f1),box(ch1))});
  var f2=document.querySelector('#brake-figs'), ch2=document.querySelector('#c-brake');
  if(f2&&ch2) out.overlap.push({pair:'brake figs/chart', o:overlap(box(f2),box(ch2))});
  var l2=document.querySelector('#brake-l2'), pn=document.querySelector('#brake-pn');
  if(l2&&pn) out.overlap.push({pair:'l2 table/pn table', o:overlap(box(l2),box(pn))});

  /* every canvas actually painted? */
  ['c-conc','c-brake'].forEach(function(id){
    var c=document.getElementById(id);
    var ch=window.Chart.getChart(c);
    var inked=false;
    try{
      var ctx=c.getContext('2d');
      var d=ctx.getImageData(0,0,c.width,c.height).data;
      var n=0;
      for(var i=3;i<d.length;i+=4*97){ if(d[i]>0) n++; }
      inked = n>50;
    }catch(e){ inked='err:'+e.message; }
    out.canvas.push({id:id, w:c.width, h:c.height, chartType:ch?ch.config.type:null,
      datasets: ch?ch.data.datasets.length:0,
      points: ch?ch.data.datasets.reduce(function(a,d){return a+(d.data?d.data.length:0);},0):0,
      drawn: !!(ch&&ch.chartArea&&ch.chartArea.width>10), nonEmptyPixels:inked});
  });

  /* figure chips: value and label both present and not clipped */
  out.figs=[];
  ['#conc-figs .fig','#brake-figs .fig'].forEach(function(sel){
    Array.prototype.forEach.call(document.querySelectorAll(sel), function(f){
      var v=f.querySelector('.fv'), l=f.querySelector('.fl');
      out.figs.push({sel:sel, value:v?v.textContent.trim().slice(0,40):null,
        label:l?l.textContent.trim().slice(0,44):null,
        h:Math.round(f.getBoundingClientRect().height),
        vClipped: v? (v.scrollWidth>v.clientWidth+2):null});
    });
  });

  /* first rows of each new table, to show real data reached the DOM */
  function firstRows(sel,n){
    return Array.prototype.slice.call(document.querySelectorAll(sel+' tbody tr'),0,n)
      .map(function(tr){ return Array.prototype.map.call(tr.cells,function(td){
        return td.textContent.trim(); }).join(' | '); });
  }
  out.l2First=firstRows('#brake-l2',3);
  out.pnFirst=firstRows('#brake-pn',3);
  out.headings=Array.prototype.map.call(document.querySelectorAll('h2'),
    function(h){return h.textContent;});
  out.accountsGone = document.getElementById('custs')===null;
  out.bodyScrollW=document.body.scrollWidth;
  out.winW=window.innerWidth;
  out.errors=window.__qa().errors;
  return JSON.stringify(out);
})()
"""


def main() -> int:
    exe = next(c for c in CHROME if Path(c).exists())
    url = HTML.resolve().as_uri()
    profile = Path(os.environ["TEMP"]) / f"isze_geo_{int(time.time())}"
    proc = subprocess.Popen([
        exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
        "--window-size=1600,1100", "--allow-file-access-from-files",
        "--no-first-run", "--no-default-browser-check", url,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    for _ in range(50):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=3) as r:
                tabs = json.loads(r.read().decode())
            tabs = [t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
            if tabs:
                ws = tabs[0]["webSocketDebuggerUrl"]
                break
        except Exception:
            continue
    if not ws:
        proc.kill()
        raise SystemExit("no attach")

    host, port = "127.0.0.1", PORT
    path = ws.split(f"{host}:{port}", 1)[1]
    s = socket.create_connection((host, port))
    k = base64.b64encode(os.urandom(16)).decode()
    s.sendall((f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {k}\r\n"
               f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
    hdr = b""
    while b"\r\n\r\n" not in hdr:
        hdr += s.recv(4096)

    def call(expr):
        data = json.dumps({"id": 7, "method": "Runtime.evaluate",
                           "params": {"expression": expr, "returnByValue": True}}).encode()
        mask = os.urandom(4)
        masked = bytes(b ^ mask[j % 4] for j, b in enumerate(data))
        n = len(data)
        head = bytes([0x81])
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        s.sendall(head + mask + masked)
        s.settimeout(60)
        while True:
            b1 = s.recv(2)
            ln = b1[1] & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", s.recv(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", s.recv(8))[0]
            buf = b""
            while len(buf) < ln:
                buf += s.recv(ln - len(buf))
            try:
                m = json.loads(buf.decode())
            except Exception:
                continue
            if m.get("id") == 7:
                res = m.get("result", {})
                if "exceptionDetails" in res:
                    return {"error": res["exceptionDetails"].get("text")}
                return res.get("result", {}).get("value")

    time.sleep(7.0)
    for _ in range(60):
        if call("!!(window.__qa && window.Chart.getChart(document.getElementById('c-brake')))"):
            break
        time.sleep(0.5)

    for label, setup in (
        ("NETWORK", "document.getElementById('reset').click()"),
        ("ITUK", """(function(){document.getElementById('reset').click();
            var s=document.getElementById('db');
            var o=Array.prototype.filter.call(s.options,function(x){return x.text.trim()==='ITUK';})[0];
            s.value=String(o.value); s.dispatchEvent(new Event('change'));})()"""),
        ("ITUK+BRAKE CONC", """(function(){
            var cs=document.getElementById('concscope');
            cs.value='brake'; cs.dispatchEvent(new Event('change'));})()"""),
    ):
        call(setup)
        time.sleep(1.0)
        out = call(PROBE)
        print("=" * 78)
        print(label)
        print("=" * 78)
        if not isinstance(out, str):
            print("  probe failed:", out)
            continue
        d = json.loads(out)
        print("  errors           :", d["errors"])
        print("  accounts table   :", "gone" if d["accountsGone"] else "STILL PRESENT")
        print("  body/win width   :", d["bodyScrollW"], "/", d["winW"],
              "(no horizontal overflow)" if d["bodyScrollW"] <= d["winW"] + 2 else "OVERFLOW")
        print("  clipped blocks   :", d["clipped"] or "none")
        print("  collisions       :", [x for x in d["overlap"] if x["o"]] or "none")
        print("  stray text       :", {k: v for k, v in d["tables"].items() if v} or "none")
        for c in d["canvas"]:
            print("  canvas %-8s type=%-9s datasets=%d points=%-5d drawn=%-5s painted=%s"
                  % (c["id"], c["chartType"], c["datasets"], c["points"], c["drawn"],
                     c["nonEmptyPixels"]))
        for f in d["figs"]:
            print("    fig %-24s = %-14s (%s)%s" % (f["value"], f["label"], f["h"],
                                                    " CLIPPED" if f["vClipped"] else ""))
        print("  L2 rows          :")
        for r in d["l2First"]:
            print("     ", r)
        print("  PN rows          :")
        for r in d["pnFirst"]:
            print("     ", r)

    print("\nheadings:", json.dumps(d["headings"], ensure_ascii=True))
    s.close()
    proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
