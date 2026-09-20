"""Headless QA for the pricing dashboard: state probe, interaction, screenshots.

Uses Chrome's remote debugging port so the page's own window.__qa() can be read
back, and so the dropdowns can actually be driven. Then every screenshot is
written for the agent to image-read.

Run: python 02_dashboards/pricing/_build/_qa_pricing_dashboard.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
            r"\ISZE_Pricing_Revision_AIM_Source.html")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_qa")
PORT = 9333 + (os.getpid() % 400)

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def browser() -> str:
    for c in CHROME:
        if Path(c).exists():
            return c
    raise SystemExit("no Chrome found")


def cdp(ws_url: str, method: str, params: dict | None = None, timeout: float = 30):
    payload = json.dumps({"id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(ws_url, data=payload,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    exe = browser()
    url = HTML.resolve().as_uri()
    print("browser:", exe)
    print("url    :", url)

    profile = Path(os.environ["TEMP"]) / f"isze_qa_profile_{int(time.time())}"
    proc = subprocess.Popen([
        exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
        "--window-size=1600,1000", "--allow-file-access-from-files",
        "--no-first-run", "--no-default-browser-check",
        "--disk-cache-size=1", "--media-cache-size=1",
        url + f"?t={int(time.time())}",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    for _ in range(40):
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
        raise SystemExit("could not attach to Chrome")

    # raw websocket via a tiny helper because urllib cannot speak ws
    import socket
    import base64
    import hashlib
    import struct

    host, port = "127.0.0.1", PORT
    path = ws.split(f"{host}:{port}", 1)[1]
    s = socket.create_connection((host, port))
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall((
        f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
        f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
    hdr = b""
    while b"\r\n\r\n" not in hdr:
        hdr += s.recv(4096)

    # message ids must be unique per request, and the screenshot helper needs one too
    mid = [1000]

    def send(obj):
        data = json.dumps(obj).encode()
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

    def recv(timeout=40):
        s.settimeout(timeout)
        while True:
            b1 = s.recv(2)
            if not b1:
                return None
            ln = b1[1] & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", s.recv(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", s.recv(8))[0]
            buf = b""
            while len(buf) < ln:
                buf += s.recv(ln - len(buf))
            try:
                msg = json.loads(buf.decode())
            except Exception:
                continue
            if msg.get("id") == 1:
                return msg

    def ev(expr: str):
        send({"id": 1, "method": "Runtime.evaluate",
              "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}})
        r = recv()
        if not r:
            return {"error": "no reply"}
        res = r.get("result", {})
        if "exceptionDetails" in res:
            return {"error": res["exceptionDetails"].get("text"),
                    "detail": str(res["exceptionDetails"])[:400]}
        return res.get("result", {}).get("value")

    def shot(name: str, full: bool = False):
        """Capture through the live session, so the screenshot shows the state the
        page is actually in - a fresh Chrome load would reset to network."""
        mid[0] += 1
        myid = mid[0]
        params = {"format": "png", "captureBeyondViewport": bool(full)}
        if full:
            m = ev("JSON.stringify({w:document.documentElement.scrollWidth,"
                   "h:document.documentElement.scrollHeight})")
            try:
                import json as _j
                d = _j.loads(m)
                params["clip"] = {"x": 0, "y": 0, "width": d["w"], "height": min(d["h"], 9000),
                                  "scale": 1}
            except Exception:
                pass
        send({"id": myid, "method": "Page.captureScreenshot", "params": params})
        s.settimeout(60)
        while True:
            b1 = s.recv(2)
            if not b1:
                return
            ln = b1[1] & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", s.recv(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", s.recv(8))[0]
            buf = b""
            while len(buf) < ln:
                buf += s.recv(ln - len(buf))
            try:
                msg = json.loads(buf.decode())
            except Exception:
                continue
            if msg.get("id") != myid:
                continue
            data = msg.get("result", {}).get("data")
            if not data:
                print(f"  shot {name}: no data")
                return
            import base64 as _b
            out = QA / name
            out.write_bytes(_b.b64decode(data))
            print(f"  shot {name}  {out.stat().st_size/1024:.0f} KB")
            return

    def set_viewport(w: int, h: int):
        send({"id": 900, "method": "Emulation.setDeviceMetricsOverride",
              "params": {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False}})

    time.sleep(6.0)
    # Wait until the customer dropdown is populated (large inlined payload).
    for _ in range(50):
        ready = ev("""
          (function(){
            var s=document.getElementById('cust');
            var qa=window.__qa ? window.__qa() : null;
            return {
              custOpts: s ? s.options.length : -1,
              hasQa: !!qa,
              chartIds: qa ? qa.charts.map(function(c){return c.id;}) : null,
              kpi0: qa && qa.kpiVals ? qa.kpiVals[0] : null,
              errors: qa ? qa.errors : null
            };
          })()
        """)
        print("ready?", ready)
        if isinstance(ready, dict) and ready.get("custOpts", 0) > 2 and ready.get("hasQa"):
            break
        time.sleep(0.6)

    print("\n=== initial render (network) ===")
    print(ev("window.__qa ? JSON.stringify(window.__qa()) : 'no probe'"))
    set_viewport(1600, 1100)
    shot("live_01_network_top.png")
    shot("live_02_network_full.png", full=True)

    print("\n=== customer drill: pick top weighted sold-to, click donut, list PNs ===")
    print(ev("""
      (function(){
        document.getElementById('reset').click();
        var s=document.getElementById('cust');
        if(!s || s.options.length<2) return JSON.stringify({error:'no customer options'});
        s.value=String(s.options[1].value);
        s.dispatchEvent(new Event('change'));
        var qa1=window.__qa();
        var ch=window.charts && charts['c-cust-mix'];
        var labels=ch? ch.data.labels : null;
        // click first donut segment via Chart.js onClick path
        if(ch && ch.data.datasets[0].data.length){
          var meta=ch.getDatasetMeta(0);
          if(meta && meta.data && meta.data[0]){
            var pt=meta.data[0];
            ch.options.onClick({}, [{index:0, element:pt, datasetIndex:0}]);
          }
        }
        var qa2=window.__qa();
        var firstPn=null;
        var tr=document.querySelector('#cust-pn tbody tr');
        if(tr && tr.cells.length>1) firstPn=tr.cells[0].textContent+' | '+tr.cells[7].textContent;
        return JSON.stringify({
          picked:s.options[s.selectedIndex].text,
          cust:qa2.cust, custL1:qa2.custL1, custL2:qa2.custL2,
          mixTitle:document.getElementById('t-cust-mix').textContent,
          donutLabels:labels, custPnRows:qa2.custPn,
          custCrumb:qa2.custCrumb, firstPn:firstPn,
          kpi:qa2.kpiVals, errors:qa2.errors,
          leagueLabels:(charts['c-league']?charts['c-league'].data.labels:null)
        });
      })()
    """))
    shot("live_07_customer_drill.png")

    print("\n=== select UTI (Israel trucks) by calling the page control ===")
    print(ev("""
      (function(){ var s=document.getElementById('db');
        var o=Array.prototype.filter.call(s.options,function(x){return x.text.trim()==='UTI';})[0]; if(!o) return JSON.stringify({error:'no UTI option'}); var i=o.value;
        if(i<0) return JSON.stringify({error:'UTI not in list'});
        s.value=String(i); s.dispatchEvent(new Event('change'));
        var rows=Array.prototype.map.call(document.querySelectorAll('#custs tbody tr'),
          function(tr){ return tr.cells[0].textContent+' '+tr.cells[1].textContent; });
        var league = (window.charts && charts['c-league'])
          ? charts['c-league'].data.labels : null;
        return JSON.stringify({picked:s.options[s.selectedIndex].text, crumb:document.getElementById('crumb').textContent,
          accounts:rows.length, firstAccount:rows[0]||null, drillRows:document.querySelectorAll('#drill tbody tr').length,
          leagueLabels:league, kpi:window.__qa().kpiVals}); })()
    """))

    print("\n=== then restrict to Thailand only ===")
    print(ev("""
      (function(){ var s=document.getElementById('src');
        var o=Array.prototype.filter.call(s.options,function(x){return /Thailand/.test(x.text.trim());})[0]; var i=o.value;
        if(i<0) return JSON.stringify({error:'Thailand not in list'});
        s.value=String(i); s.dispatchEvent(new Event('change'));
        var opts=Array.prototype.map.call(s.options,function(o){return o.text;});
        return JSON.stringify({picked:s.options[s.selectedIndex].text, kpi:window.__qa().kpiVals, allOptions:opts,
          leagueLabels:(window.charts&&charts['c-league'])?charts['c-league'].data.labels:null}); })()
    """))
    set_viewport(1600, 1100)
    shot("live_03_uti_thailand.png")
    set_viewport(900, 1100)
    shot("live_04_narrow.png")
    set_viewport(1600, 1100)

    print("\n=== Not held source filter — billed chip must show the full Not held pile ===")
    print(ev("""
      (function(){ document.getElementById('reset').click();
        var s=document.getElementById('src');
        var o=Array.prototype.filter.call(s.options,function(x){return /Not held/.test(x.text.trim());})[0];
        if(!o) return JSON.stringify({error:'no Not held option'});
        s.value=String(o.value); s.dispatchEvent(new Event('change'));
        var nhi = Number(o.value);
        var sumAll=0, sumBilled=0, n=0;
        var DD = window.D || (typeof D!=='undefined'?D:null);
        if(!DD){
          try{ DD = JSON.parse(document.getElementById('payload').textContent); }catch(e){ DD=null; }
        }
        if(!DD) return JSON.stringify({error:'no data'});
        for(var i=0;i<DD.groups.length;i++){
          var r=DD.groups[i];
          if(r[4]!==nhi) continue;
          sumAll+=r[12]; sumBilled+=r[8]; n++;
        }
        return JSON.stringify({picked:s.options[s.selectedIndex].text, kpi:window.__qa().kpiVals,
          drillRows:document.querySelectorAll('#drill tbody tr').length,
          stateDb:window.state.db, stateSrc:window.state.src, nhi:nhi, groupsNh:n, sumAll:Math.round(sumAll),
          sumBilled:Math.round(sumBilled), errors:window.__qa().errors}); })()
    """))
    shot("live_06_not_held.png")

    print("\n=== reset, then metric = step euro ===")
    print(ev("""
      (function(){ document.getElementById('reset').click();
        Array.prototype.forEach.call(document.querySelectorAll('#meas button'), function(b){
          if(b.getAttribute('data-m')==='step'){ b.click(); } });
        return JSON.stringify({crumb:document.getElementById('crumb').textContent,
          metricOn:document.querySelector('#meas button.on').textContent,
          srcTitle:document.getElementById('t-src').textContent,
          errors:window.__qa().errors}); })()
    """))

    print("\n=== drill: click the biggest real family at level 1 ===")
    print(ev("""
      (function(){ document.getElementById('reset').click();
        var trs=document.querySelectorAll('#drill tbody tr');
        var first=trs[0];
        var name=first? first.cells[0].textContent : null;
        if(first) first.click();
        return JSON.stringify({tableHad:trs.length, clicked:name,
          crumb:document.getElementById('crumb').textContent,
          rowsNow:document.querySelectorAll('#drill tbody tr').length,
          mixTitle:document.getElementById('t-mix').textContent}); })()
    """))

    print("\n=== drill one more level, into a level 2 group ===")
    print(ev("""
      (function(){ var trs=document.querySelectorAll('#drill tbody tr');
        var second=trs.length>1? trs[1] : null;
        var name=second? second.cells[0].textContent : null;
        if(second) second.click();
        return JSON.stringify({clicked:name, crumb:document.getElementById('crumb').textContent,
          rowsNow:document.querySelectorAll('#drill tbody tr').length,
          errors:window.__qa().errors}); })()
    """))
    shot("live_05_drilled_l2.png")

    print("\n=== drill to level 3, then check the movers survived ===")
    print(ev("""
      (function(){ var trs=document.querySelectorAll('#drill tbody tr');
        var second=trs.length>1? trs[1] : null;
        if(second) second.click();
        return JSON.stringify({crumb:document.getElementById('crumb').textContent,
          drillRows:document.querySelectorAll('#drill tbody tr').length,
          movers:document.querySelectorAll('#movers tbody tr').length,
          errors:window.__qa().errors}); })()
    """))

    print("\n=== the account table follows the distributor selection ===")
    print(ev("""
      (function(){ var s=document.getElementById('db');
        var o=Array.prototype.filter.call(s.options,function(x){return x.text.trim()==='ITUK';})[0]; var i=o.value;
        s.value=String(i); s.dispatchEvent(new Event('change'));
        var rows=Array.prototype.map.call(document.querySelectorAll('#custs tbody tr'),
          function(tr){ return tr.cells[0].textContent+' '+tr.cells[1].textContent; });
        return JSON.stringify({dist:s.options[s.selectedIndex].text, n:rows.length, first:rows.slice(0,3)}); })()
    """))

    # screenshots for visual inspection
    for label, w, h, full in (("01_network", 1600, 2600, False),
                              ("02_drill", 1600, 2600, False),
                              ("03_900px", 900, 2600, False),
                              ("04_fullpage", 1600, 1200, True)):
        out = QA / f"shot_{label}.png"
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--window-size={w},{h}", f"--screenshot={out}",
                        "--virtual-time-budget=8000", "--allow-file-access-from-files",
                        url], capture_output=True, timeout=120)
        if out.exists():
            print(f"shot {out.name}  {out.stat().st_size/1024:.0f} KB  ({w}x{h})")

    s.close()
    proc.terminate()
    time.sleep(1)
    try:
        proc.kill()
    except Exception:
        pass
    print("\nQA_DIR:", QA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
