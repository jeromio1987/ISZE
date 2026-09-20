"""A very small Chrome DevTools Protocol client, so the checks can drive a real browser.

Playwright's bundled browsers are not installed on this machine and cannot be downloaded from
here, and `selenium` would need a driver binary. Chrome itself is installed, and it exposes the
same DevTools Protocol over a websocket when it is started with `--remote-debugging-port`. This
module is the minimum needed to open a page, run JavaScript in it, measure the DOM and take a
screenshot - which is what the drill, breadcrumb and first-viewport checks require.

The browser is driven from Python so it can be compared, asserted and reported on rather than
looked at.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import websocket  # websocket-client

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

# A profile directory inside this repo's temp area keeps the run away from the real Chrome
# profile: a debug port on the user's own profile would attach to his open windows.
PROFILE_ROOT = Path(tempfile.gettempdir()) / "isze_cdp_profile"


def chrome_path() -> Path:
    for c in CHROME_CANDIDATES:
        p = Path(c)
        if p.is_file():
            return p
    raise RuntimeError("chrome not found in any known location")


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Chrome:
    """A headless Chrome with a CDP endpoint, and a small set of page operations."""

    def __init__(self, width: int = 1440, height: int = 900, scale: float = 1.0,
                 timeout: float = 30.0, extra_args: list[str] | None = None):
        self.width = width
        self.height = height
        self.scale = scale
        self.timeout = timeout
        self._id = 0
        self._ws: websocket.WebSocket | None = None
        self.proc: subprocess.Popen | None = None
        self.profile = PROFILE_ROOT / f"{os.getpid()}_{int(time.time()*1000)}"
        self._extra = extra_args or []

    # ── lifecycle ────────────────────────────────────────────────────────────────────────────
    def __enter__(self) -> Chrome:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()

    def start(self) -> None:
        self.profile.mkdir(parents=True, exist_ok=True)
        args = [
            str(chrome_path()),
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-sync",
            "--mute-audio",
            "--hide-scrollbars",
            f"--user-data-dir={self.profile}",
            "--remote-debugging-port=0",
            f"--window-size={self.width},{self.height}",
            f"--force-device-scale-factor={self.scale}",
            "about:blank",
        ] + self._extra
        # `--remote-debugging-port=0` makes Chrome pick a free port and write it into the profile.
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        devtools = self.profile / "DevToolsActivePort"
        deadline = time.time() + self.timeout
        port = None
        while time.time() < deadline:
            if devtools.is_file():
                text = devtools.read_text(encoding="utf-8", errors="replace").splitlines()
                if text and text[0].strip().isdigit():
                    port = int(text[0].strip())
                    break
            if self.proc.poll() is not None:
                raise RuntimeError("chrome exited before the debug port appeared")
            time.sleep(0.1)
        if port is None:
            raise RuntimeError("chrome did not publish a debug port in time")
        self.port = port
        self._open_target()
        self.cmd("Page.enable")
        self.cmd("Runtime.enable")
        self.cmd("DOM.enable")

    def _endpoint(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def _open_target(self) -> None:
        deadline = time.time() + self.timeout
        ws_url = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(self._endpoint("/json/list"), timeout=2) as r:
                    targets = json.loads(r.read().decode("utf-8"))
                pages = [t for t in targets if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:  # noqa: BLE001  the port is still coming up
                pass
            time.sleep(0.15)
        if not ws_url:
            raise RuntimeError("no page target appeared on the debug port")
        self._ws = websocket.create_connection(ws_url, timeout=self.timeout,
                                              suppress_origin=True)
        self._ws.settimeout(self.timeout)

    def stop(self) -> None:
        try:
            if self._ws is not None:
                self._ws.close()
        except Exception:  # noqa: BLE001
            pass
        if self.proc is not None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=8)
            except Exception:  # noqa: BLE001
                try:
                    self.proc.kill()
                except Exception:  # noqa: BLE001
                    pass
        shutil.rmtree(self.profile, ignore_errors=True)

    # ── protocol ─────────────────────────────────────────────────────────────────────────────
    def cmd(self, method: str, params: dict[str, Any] | None = None,
            timeout: float | None = None) -> dict[str, Any]:
        if self._ws is None:
            raise RuntimeError("browser is not started")
        self._id += 1
        mid = self._id
        self._ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        deadline = time.time() + (timeout or self.timeout)
        while time.time() < deadline:
            raw = self._ws.recv()
            if not raw:
                continue
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(f"{method} did not answer within {timeout or self.timeout}s")

    def js(self, expression: str, timeout: float | None = None, await_promise: bool = False) -> Any:
        """Evaluate JavaScript in the page and return the value by value."""
        res = self.cmd("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
            "userGesture": True,
        }, timeout=timeout)
        if res.get("exceptionDetails"):
            det = res["exceptionDetails"]
            desc = (det.get("exception") or {}).get("description") or det.get("text")
            raise RuntimeError(f"page JavaScript threw: {desc}")
        return (res.get("result") or {}).get("value")

    # ── page operations ──────────────────────────────────────────────────────────────────────
    def goto(self, url: str, wait_ms: int = 1200) -> None:
        self.cmd("Page.navigate", {"url": url})
        self.wait_ready(wait_ms)

    def wait_ready(self, extra_ms: int = 800) -> None:
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                state = self.js("document.readyState")
                if state == "complete":
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.1)
        time.sleep(extra_ms / 1000.0)

    def viewport(self, width: int, height: int, scale: float = 1.0) -> None:
        self.width, self.height, self.scale = width, height, scale
        self.cmd("Emulation.setDeviceMetricsOverride", {
            "width": width, "height": height, "deviceScaleFactor": scale, "mobile": False,
        })

    def screenshot(self, out: Path, full_page: bool = False) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        params: dict[str, Any] = {"format": "png"}
        if full_page:
            params["captureBeyondViewport"] = True
        res = self.cmd("Page.captureScreenshot", params, timeout=120)
        out.write_bytes(base64.b64decode(res["data"]))
        return out

    def screenshot_clip(self, out: Path, x: float, y: float, w: float, h: float) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        res = self.cmd("Page.captureScreenshot", {
            "format": "png",
            "clip": {"x": x, "y": y, "width": w, "height": h, "scale": 1},
        }, timeout=120)
        out.write_bytes(base64.b64decode(res["data"]))
        return out


def file_url(p: Path) -> str:
    return p.resolve().as_uri()
