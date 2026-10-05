#!/usr/bin/env python3
"""Paint-check original + Nordics prototype; write SHIP_RECEIPTs."""
from __future__ import annotations

import base64
import hashlib
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
QA = ROOT / "_qa"
QA.mkdir(parents=True, exist_ok=True)

PAGES = [
    {
        "html": ROOT / "ISZE_Pricing_Revision_AIM_Source.html",
        "open": ROOT / "OPEN_Pricing_Revision_AIM_Source.cmd",
        "receipt": ROOT / "ISZE_Pricing_Revision_AIM_Source.SHIP_RECEIPT.json",
        "shot": QA / "original_network_home.png",
        "shot_spine": QA / "original_spine_l3.png",
        "kind": "original",
    },
    {
        "html": ROOT / "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
        "open": ROOT / "OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.cmd",
        "receipt": ROOT / "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.SHIP_RECEIPT.json",
        "shot": QA / "prototype_alldb_home.png",
        "kind": "prototype",
    },
]

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


def paint(page: dict, port: int) -> dict:
    html: Path = page["html"]
    exe = browser()
    url = html.resolve().as_uri()
    profile = Path(os.environ["TEMP"]) / f"isze_paint_{port}_{int(time.time())}"
    proc = subprocess.Popen(
        [
            exe,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            "--window-size=1600,1100",
            "--allow-file-access-from-files",
            "--no-first-run",
            "--no-default-browser-check",
            url + f"?t={int(time.time())}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ws = None
    try:
        for _ in range(50):
            time.sleep(0.4)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=3) as r:
                    tabs = json.loads(r.read().decode())
                tabs = [t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
                if tabs:
                    ws = tabs[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                continue
        if not ws:
            raise RuntimeError("could not attach to Chrome")

        host, p = "127.0.0.1", port
        path = ws.split(f"{host}:{p}", 1)[1]
        s = socket.create_connection((host, p), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        s.sendall(
            (
                f"GET {path} HTTP/1.1\r\nHost: {host}:{p}\r\nUpgrade: websocket\r\n"
                f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                f"Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
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
                    payload = buf[off : off + ln]
                    buf = buf[off + ln :]
                    try:
                        return json.loads(payload.decode())
                    except Exception:
                        continue
            return None

        def call(method, params=None, wait_id=None):
            mid[0] += 1
            i = mid[0]
            send({"id": i, "method": method, "params": params or {}})
            want = wait_id if wait_id is not None else i
            for _ in range(80):
                msg = recv()
                if not msg:
                    continue
                if msg.get("id") == want:
                    return msg
            raise RuntimeError(f"timeout waiting for {method}")

        call("Page.enable")
        call("Runtime.enable")
        time.sleep(2.5)

        # wait for __qa
        qa = None
        for _ in range(20):
            mid[0] += 1
            i = mid[0]
            send(
                {
                    "id": i,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "typeof window.__qa === 'function' ? JSON.stringify(window.__qa()) : null",
                        "returnByValue": True,
                    },
                }
            )
            msg = None
            for _ in range(40):
                msg = recv()
                if msg and msg.get("id") == i:
                    break
            val = (msg or {}).get("result", {}).get("result", {}).get("value")
            if val:
                qa = json.loads(val)
                break
            time.sleep(0.4)
        if not qa:
            raise RuntimeError("window.__qa not ready")

        spine = None  # set for original spine drill; stays None on prototype
        if page.get("kind") == "original":
            mid[0] += 1
            i = mid[0]
            send(
                {
                    "id": i,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "typeof window.__qaDrillSpine === 'function' ? JSON.stringify(window.__qaDrillSpine()) : null",
                        "returnByValue": True,
                    },
                }
            )
            msg = None
            for _ in range(40):
                msg = recv()
                if msg and msg.get("id") == i:
                    break
            val = (msg or {}).get("result", {}).get("result", {}).get("value")
            if val:
                spine = json.loads(val)
            time.sleep(0.8)
            mid[0] += 1
            i = mid[0]
            send({"id": i, "method": "Page.captureScreenshot", "params": {"format": "png", "fromSurface": True}})
            shot_msg = None
            for _ in range(60):
                shot_msg = recv(timeout=90)
                if shot_msg and shot_msg.get("id") == i:
                    break
            data2 = (shot_msg or {}).get("result", {}).get("data")
            if data2 and page.get("shot_spine"):
                page["shot_spine"].write_bytes(base64.b64decode(data2))

        # home screenshot: re-render home for original after spine drill
        if page.get("kind") == "original":
            mid[0] += 1
            i = mid[0]
            send(
                {
                    "id": i,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "document.getElementById('reset').click(); true",
                        "returnByValue": True,
                    },
                }
            )
            for _ in range(20):
                msg = recv()
                if msg and msg.get("id") == i:
                    break
            time.sleep(1.0)

        mid[0] += 1
        i = mid[0]
        send({"id": i, "method": "Page.captureScreenshot", "params": {"format": "png", "fromSurface": True}})
        shot_msg = None
        for _ in range(60):
            shot_msg = recv(timeout=90)
            if shot_msg and shot_msg.get("id") == i:
                break
        data = (shot_msg or {}).get("result", {}).get("data")
        if not data:
            raise RuntimeError("screenshot failed")
        page["shot"].write_bytes(base64.b64decode(data))
        s.close()
        if spine is not None:
            qa["spine"] = spine
        return qa
    finally:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass


def write_receipt(page: dict, qa: dict) -> None:
    html: Path = page["html"]
    open_cmd: Path = page["open"]
    text = html.read_text(encoding="utf-8", errors="ignore")
    shots = [page["shot"]]
    if page.get("shot_spine") and Path(page["shot_spine"]).exists():
        shots.append(page["shot_spine"])
    checks = [
        {"id": "exists", "ok": html.exists(), "detail": str(html)},
        {"id": "min_size", "ok": html.stat().st_size > 500_000, "detail": f"{html.stat().st_size} bytes"},
        {"id": "no_cdn", "ok": "cdn.jsdelivr" not in text.lower() and "cdnjs.cloudflare" not in text.lower(),
         "detail": "no chart/lib CDN"},
        {"id": "no_nan_json", "ok": ": NaN" not in text and ",NaN" not in text, "detail": "no NaN literals"},
        {"id": "open_cmd", "ok": open_cmd.exists(), "detail": str(open_cmd)},
        {"id": "open_cmd_crlf", "ok": b"\r\n" in open_cmd.read_bytes() if open_cmd.exists() else False,
         "detail": "CRLF launcher"},
        {"id": "qa_probe", "ok": not qa.get("errors"), "detail": json.dumps(qa)[:500]},
        {"id": "visual_screenshots", "ok": all(s.exists() and s.stat().st_size > 20_000 for s in shots),
         "detail": f"{len(shots)} PNG — agent must image-Read: " + "; ".join(str(s) for s in shots)},
    ]
    if page["kind"] == "original":
        checks.append({
            "id": "network_aim_without_soldto",
            "ok": qa.get("cust", 0) == -1 and qa.get("custPn", 0) > 5 and any(
                c.get("id") == "c-cust-mix" and c.get("points", 0) > 3 for c in qa.get("charts", [])
            ),
            "detail": f"cust={qa.get('cust')} custPn={qa.get('custPn')} charts={qa.get('charts')}",
        })
        checks.append({
            "id": "has_content_markers",
            "ok": qa.get("kpi", 0) >= 4 and qa.get("drill", 0) > 5,
            "detail": f"kpi={qa.get('kpi')} drill={qa.get('drill')}",
        })
        spine = qa.get("spine") or {}
        step_ok = bool(spine.get("ok")) and 80_000 < float(spine.get("step") or 0) < 95_000
        all_ok = bool(spine.get("ok")) and 1_500_000 < float(spine.get("all") or 0) < 1_800_000
        not_net = abs(float(spine.get("step") or 0) - 1_652_140.71) > 100_000
        checks.append({
            "id": "spine_kpi_filtered",
            "ok": step_ok and all_ok and not_net,
            "detail": f"spine step={spine.get('step')} all={spine.get('all')} kpi={spine.get('kpiVals')}",
        })
    else:
        checks.append({
            "id": "alldb_click_ui",
            "ok": qa.get("compare", 0) >= 20 and qa.get("rail", 0) > 3 and qa.get("zoomDrawn") is True
                 and qa.get("db", 0) == -1,
            "detail": f"compare={qa.get('compare')} rail={qa.get('rail')} db={qa.get('db')} zoom={qa.get('zoomDrawn')}",
        })
        checks.append({
            "id": "has_content_markers",
            "ok": qa.get("kpi", 0) >= 4 and qa.get("detail", 0) > 5,
            "detail": f"kpi={qa.get('kpi')} detail={qa.get('detail')}",
        })

    ok = all(c["ok"] for c in checks)
    receipt = {
        "schema": "ship_receipt/v1",
        "artifact": str(html),
        "artifact_mtime_ms": int(html.stat().st_mtime * 1000),
        "written_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": ok,
        "checks": checks,
        "screenshots": [str(s) for s in shots],
        "notes": "original: AIM drill KPIs follow filtered slice; prototype: All-network DB cards + zoom",
        "qa": qa,
    }
    page["receipt"].write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"{'PASS' if ok else 'FAIL'} {html.name}")
    for c in checks:
        print(f"  [{'OK' if c['ok'] else 'NO'}] {c['id']}: {c['detail'][:160]}")


def main() -> int:
    # frozen files must stay put
    frozen = [
        ROOT / "ISZE_Pricing_Revision_AIM_Source_L3PN_20260918.html",
        ROOT / "ISZE_Pricing_Revision_AIM_FX_20261001.html",
    ]
    frozen_meta = {str(p): (p.stat().st_mtime, p.stat().st_size) for p in frozen if p.exists()}

    base_port = 9400 + (os.getpid() % 300)
    results = []
    for i, page in enumerate(PAGES):
        print("paint", page["html"].name)
        qa = paint(page, base_port + i)
        write_receipt(page, qa)
        results.append((page, qa))

    for p, (mt, sz) in frozen_meta.items():
        cur = Path(p)
        assert cur.stat().st_mtime == mt and cur.stat().st_size == sz, f"FROZEN TOUCHED: {p}"
        print("frozen untouched:", Path(p).name)

    # image-read reminder for parent: print paths
    for page, _ in results:
        print("SHOT", page["shot"])
        print("RECEIPT", page["receipt"])
    return 0 if all(json.loads(p["receipt"].read_text(encoding="utf-8"))["ok"] for p, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
