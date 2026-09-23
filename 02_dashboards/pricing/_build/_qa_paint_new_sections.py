"""Paint check for the two new sections and the area where the accounts table was.

Clips each element to its own bounding box so the screenshot is readable at full
resolution, then writes the PNGs for the agent to image-read.
"""
from __future__ import annotations

import json
import os
import socket
import base64
import hashlib
import struct
import subprocess
import time
import urllib.request
from pathlib import Path

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
            r"\ISZE_Pricing_Revision_AIM_Source.html")
QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_qa")
PORT = 9711 + (os.getpid() % 300)

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


def main() -> int:
    QA.mkdir(parents=True, exist_ok=True)
    exe = browser()
    url = HTML.resolve().as_uri()
    profile = Path(os.environ["TEMP"]) / f"isze_paint_{int(time.time())}"
    proc = subprocess.Popen([
        exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
        "--window-size=1600,1100", "--allow-file-access-from-files",
        "--no-first-run", "--no-default-browser-check",
        "--disk-cache-size=1", "--media-cache-size=1",
        url + f"?t={int(time.time())}",
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
        raise SystemExit("could not attach to Chrome")

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

    mid = [2000]

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

    def recv_frame(want_id=None, timeout=60):
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
            if want_id is None or msg.get("id") == want_id:
                return msg

    def ev(expr):
        send({"id": 1, "method": "Runtime.evaluate",
              "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}})
        r = recv_frame(want_id=1)
        if not r:
            return {"error": "no reply"}
        res = r.get("result", {})
        if "exceptionDetails" in res:
            return {"error": res["exceptionDetails"].get("text")}
        return res.get("result", {}).get("value")

    def clip_shot(name, selector, pad=14):
        """Screenshot exactly one element, at native scale."""
        box = ev(f"""
          (function(){{
            var e=document.querySelector({selector!r});
            if(!e) return null;
            e.scrollIntoView({{block:'center'}});
            var r=e.getBoundingClientRect();
            return JSON.stringify({{x:r.left,y:r.top,w:r.width,h:r.height,
              top:document.documentElement.scrollTop}});
          }})()
        """)
        if not isinstance(box, str):
            print(f"  {name}: element not found ({selector})")
            return None
        b = json.loads(box)
        time.sleep(0.7)
        # re-measure after scroll settled
        box = ev(f"""
          (function(){{ var e=document.querySelector({selector!r});
            var r=e.getBoundingClientRect();
            return JSON.stringify({{x:r.left,y:r.top,w:r.width,h:r.height}}); }})()
        """)
        b = json.loads(box)
        mid[0] += 1
        myid = mid[0]
        params = {"format": "png", "captureBeyondViewport": True,
                  "clip": {"x": max(0, b["x"] - pad), "y": max(0, b["y"] - pad),
                           "width": b["w"] + 2 * pad, "height": b["h"] + 2 * pad, "scale": 1}}
        send({"id": myid, "method": "Page.captureScreenshot", "params": params})
        msg = recv_frame(want_id=myid, timeout=90)
        data = (msg or {}).get("result", {}).get("data")
        if not data:
            print(f"  {name}: no data")
            return None
        out = QA / name
        out.write_bytes(base64.b64decode(data))
        print(f"  {name}  {out.stat().st_size/1024:.0f} KB  "
              f"({int(b['w'])}x{int(b['h'])})")
        return out

    time.sleep(7.0)
    for _ in range(60):
        ready = ev("!!(window.__qa && document.querySelector('#cust').options.length>2)")
        if ready is True:
            break
        time.sleep(0.5)

    set_viewport = lambda w, h: send({"id": 901, "method": "Emulation.setDeviceMetricsOverride",
                                      "params": {"width": w, "height": h, "deviceScaleFactor": 1,
                                                 "mobile": False}})
    set_viewport(1600, 1100)

    print("network view")
    print(" probe:", ev("JSON.stringify({errors:window.__qa().errors, conc:window.__qa().concFigs, "
                        "brakeFigs:window.__qa().brakeFigs})"))
    clip_shot("paint_1_concentration.png", "#conc-figs")
    clip_shot("paint_2_concentration_chart.png", "#c-conc")
    clip_shot("paint_3_brake_figs.png", "#brake-figs")
    clip_shot("paint_4_brake_chart.png", "#c-brake")
    clip_shot("paint_5_brake_l2_table.png", "#brake-l2")
    clip_shot("paint_6_brake_pn_table.png", ".tblwrap:has(#brake-pn)")
    print("ITUK view")
    ev("""(function(){ document.getElementById('reset').click();
        var s=document.getElementById('db');
        var o=Array.prototype.filter.call(s.options,function(x){return x.text.trim()==='ITUK';})[0];
        s.value=String(o.value); s.dispatchEvent(new Event('change')); return 1; })()""")
    time.sleep(1.0)
    print(" probe:", ev("JSON.stringify({brakeFigs:window.__qa().brakeFigs, brakeL2:window.__qa().brakeL2, "
                        "brakePn:window.__qa().brakePn, conc:window.__qa().concFigs})"))
    clip_shot("paint_7_ituk_brake_figs.png", "#brake-figs")
    clip_shot("paint_8_ituk_brake_l2.png", "#brake-l2")
    clip_shot("paint_9_ituk_brake_pn.png", ".tblwrap:has(#brake-pn)")

    print("brake-only concentration")
    ev("""(function(){ var cs=document.getElementById('concscope');
        cs.value='brake'; cs.dispatchEvent(new Event('change')); return 1; })()""")
    time.sleep(1.0)
    clip_shot("paint_10_ituk_conc_figs.png", "#conc-figs")
    clip_shot("paint_11_ituk_conc_chart.png", "#c-conc")

    print("end of page, where the accounts table used to be")
    ev("window.scrollTo(0, document.documentElement.scrollHeight)")
    time.sleep(0.8)
    tail = ev("""JSON.stringify({
        accounts: document.getElementById('custs') ? 1 : 0,
        pageH: document.documentElement.scrollHeight,
        tailCards: Array.prototype.map.call(
          document.querySelectorAll('.wrap > .grid > .card > h2'),
          function(h){return h.textContent;})})""")
    print(" tail probe:", json.dumps(tail, ensure_ascii=True)[:600])
    clip_shot("paint_12_page_tail.png", "#foot")
    # one viewport-sized shot of the bottom, to see the page does not end abruptly
    ev("window.scrollTo(0, document.documentElement.scrollHeight - 900)")
    time.sleep(0.8)
    mid[0] += 1
    myid = mid[0]
    send({"id": myid, "method": "Page.captureScreenshot",
          "params": {"format": "png", "captureBeyondViewport": False}})
    msg = recv_frame(want_id=myid, timeout=90)
    data = (msg or {}).get("result", {}).get("data")
    if data:
        out = QA / "paint_13_bottom_viewport.png"
        out.write_bytes(base64.b64decode(data))
        print(f"  paint_13_bottom_viewport.png  {out.stat().st_size/1024:.0f} KB")

    print("\nQA_DIR:", QA)
    s.close()
    proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
