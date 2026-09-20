#!/usr/bin/env python3
"""Re-paint Nordics prototype after crumb fix."""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing")
html = ROOT / "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html"
shot = ROOT / "_qa" / "prototype_nordics_home.png"
receipt = ROOT / "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.SHIP_RECEIPT.json"
open_cmd = ROOT / "OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.cmd"
exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
port = 9522
url = html.resolve().as_uri()
profile = Path(os.environ["TEMP"]) / f"isze_proto_{int(time.time())}"
proc = subprocess.Popen(
    [
        exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--remote-debugging-port={port}", f"--user-data-dir={profile}",
        "--window-size=1600,1100", "--allow-file-access-from-files", "--no-first-run",
        url + f"?t={int(time.time())}",
    ],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
ws = None
for _ in range(40):
    time.sleep(0.4)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=3) as r:
            tabs = json.loads(r.read().decode())
        tabs = [t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
        if tabs:
            ws = tabs[0]["webSocketDebuggerUrl"]
            break
    except Exception:
        pass
assert ws, "no ws"
host, p = "127.0.0.1", port
path = ws.split(f"{host}:{p}", 1)[1]
s = socket.create_connection((host, p), timeout=10)
key = base64.b64encode(os.urandom(16)).decode()
s.sendall((
    f"GET {path} HTTP/1.1\r\nHost: {host}:{p}\r\nUpgrade: websocket\r\n"
    f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
).encode())
hdr = b""
while b"\r\n\r\n" not in hdr:
    hdr += s.recv(4096)
mid = [3000]


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


def recv(timeout=60):
    s.settimeout(timeout)
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            return None
        buf += chunk
        while True:
            if len(buf) < 2:
                break
            ln = buf[1] & 0x7F
            off = 2
            if ln == 126:
                if len(buf) < 4:
                    break
                ln = struct.unpack(">H", buf[2:4])[0]
                off = 4
            elif ln == 127:
                if len(buf) < 10:
                    break
                ln = struct.unpack(">Q", buf[2:10])[0]
                off = 10
            if len(buf) < off + ln:
                break
            payload = buf[off:off + ln]
            buf = buf[off + ln:]
            try:
                return json.loads(payload.decode())
            except Exception:
                continue


def call(method, params=None):
    mid[0] += 1
    i = mid[0]
    send({"id": i, "method": method, "params": params or {}})
    for _ in range(80):
        msg = recv()
        if msg and msg.get("id") == i:
            return msg
    raise RuntimeError(method)


call("Page.enable")
call("Runtime.enable")
time.sleep(2.5)
expr = "JSON.stringify({qa:window.__qa(), crumb:document.getElementById('crumb').textContent})"
qa_wrap = None
for _ in range(20):
    mid[0] += 1
    i = mid[0]
    send({"id": i, "method": "Runtime.evaluate",
          "params": {"expression": expr, "returnByValue": True}})
    msg = None
    for _ in range(40):
        msg = recv()
        if msg and msg.get("id") == i:
            break
    val = (msg or {}).get("result", {}).get("result", {}).get("value")
    if val:
        qa_wrap = json.loads(val)
        break
    time.sleep(0.3)

assert qa_wrap, "no qa"
print("CRUMB", qa_wrap["crumb"])
print("QA", qa_wrap["qa"])
assert "All other groups" not in qa_wrap["crumb"], qa_wrap["crumb"]
assert qa_wrap["qa"]["compare"] == 4 and qa_wrap["qa"]["zoomDrawn"]

mid[0] += 1
i = mid[0]
send({"id": i, "method": "Page.captureScreenshot",
      "params": {"format": "png", "fromSurface": True}})
shot_msg = None
for _ in range(60):
    shot_msg = recv(timeout=90)
    if shot_msg and shot_msg.get("id") == i:
        break
shot.write_bytes(base64.b64decode(shot_msg["result"]["data"]))
s.close()
proc.kill()

text = html.read_text(encoding="utf-8", errors="ignore")
checks = [
    {"id": "exists", "ok": True, "detail": str(html)},
    {"id": "min_size", "ok": html.stat().st_size > 500_000, "detail": str(html.stat().st_size)},
    {"id": "no_cdn", "ok": "cdn.jsdelivr" not in text.lower(), "detail": "no CDN"},
    {"id": "open_cmd", "ok": open_cmd.exists() and b"\r\n" in open_cmd.read_bytes(),
     "detail": str(open_cmd)},
    {"id": "crumb_l1_clean", "ok": "All other groups" not in qa_wrap["crumb"],
     "detail": qa_wrap["crumb"]},
    {"id": "nordics_customer_ui",
     "ok": qa_wrap["qa"]["compare"] == 4 and qa_wrap["qa"]["zoomDrawn"],
     "detail": json.dumps(qa_wrap["qa"])},
    {"id": "visual_screenshots", "ok": shot.stat().st_size > 20_000, "detail": str(shot)},
]
ok = all(c["ok"] for c in checks)
receipt.write_text(json.dumps({
    "schema": "ship_receipt/v1",
    "artifact": str(html),
    "artifact_mtime_ms": int(html.stat().st_mtime * 1000),
    "written_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "ok": ok,
    "checks": checks,
    "screenshots": [str(shot)],
    "notes": "prototype nordics crumb fix",
    "qa": qa_wrap,
}, indent=2), encoding="utf-8")
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
