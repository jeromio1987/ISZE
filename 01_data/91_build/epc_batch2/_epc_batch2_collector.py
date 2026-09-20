"""Collector for EPC decode batch 2.

Why this exists: batch 1's results lived only in the browser tab for the whole run, so a reload
would have lost ~25 minutes of work. This is a tiny local HTTP endpoint the EPC tab posts each
part number's result to as soon as it is collected. Every result is appended to a JSONL file on
disk immediately, and the consolidated JSON is written at the end (and on demand).

Endpoints
---------
POST /append    body: {"pn": "...", "result": {...}}      -> appended to the .jsonl
POST /finalize  body: {"meta": {...}}                     -> writes the consolidated .json
GET  /status                                              -> counts so far
GET  /health                                              -> ok

Binds 127.0.0.1 only. Chrome treats http://127.0.0.1 as a trustworthy origin, so the HTTPS EPC
page can post to it without a mixed-content block; CORS is opened for that reason.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
BUILD = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\epc_batch2"
JSONL = os.path.join(ROOT, "epc_decode_batch2_20260919.jsonl")
FINAL = os.path.join(ROOT, "epc_decode_batch2_20260919.json")
PORT = 8791

_lock = threading.Lock()
_rows: list[dict] = []


def _load_existing() -> None:
    if os.path.isfile(JSONL):
        with open(JSONL, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        _rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass


def _append(pn: str, result: dict) -> int:
    with _lock:
        _rows.append(result)
        with open(JSONL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return len(_rows)


def _finalize(meta: dict | None) -> str:
    with _lock:
        payload = {
            "batch": 2,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "records": len(_rows),
            "meta": meta or {},
            "results": list(_rows),
        }
        with open(FINAL, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        return FINAL


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        # Chrome's Private Network Access: a public HTTPS page (the EPC) may only reach a loopback
        # address if the response to the preflight says so. Without this header the fetch fails
        # with "TypeError: Failed to fetch" even though the server is up.
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: str, ctype: str) -> None:
        if not os.path.isfile(path):
            self._json(404, {"error": "not found"})
            return
        with open(path, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/status"):
            self._json(200, {"rows": len(_rows), "jsonl": JSONL, "final": FINAL})
        elif self.path.startswith("/health"):
            self._json(200, {"ok": True})
        elif self.path.startswith("/driver.js"):
            self._file(os.path.join(BUILD, "_epc_batch2_driver.js"), "application/javascript")
        elif self.path.startswith("/pns.json"):
            self._file(os.path.join(BUILD, "_epc_batch2_pns.json"), "application/json")
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            self._json(400, {"error": "bad json"})
            return

        if self.path.startswith("/append"):
            result = data.get("result") or {}
            n = _append(str(data.get("pn", "")), result)
            self._json(200, {"rows": n})
        elif self.path.startswith("/finalize"):
            path = _finalize(data.get("meta") or {})
            self._json(200, {"rows": len(_rows), "file": path})
        else:
            self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # keep the console quiet
        pass


def main() -> int:
    _load_existing()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"collector listening on http://127.0.0.1:{PORT}")
    print(f"jsonl : {JSONL}  (pre-existing rows: {len(_rows)})")
    print(f"final : {FINAL}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        if _rows:
            print("finalized ->", _finalize({"closed": "interrupt"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
