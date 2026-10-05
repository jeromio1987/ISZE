#!/usr/bin/env python
"""
EPC catalogue collector -- receives POSTed JSON from the Snap-on EPC browser tab and
appends it to disk immediately, one JSON record per line (JSONL).

Why this exists: the EPC requires a per-request signed header that only the page itself
can produce, so the page must make the calls. But results must NOT live only in the
browser -- an earlier run nearly lost 25 minutes of work that way. So the page POSTs each
payload here the moment it lands, and this process writes it to disk.

READ-ONLY on the EPC: this only stores what the app itself returned.

Usage:
    python collector.py [--port 8793] [--out <jsonl path>]

Endpoints:
    POST /append   body = {"kind": "...", "meta": {...}, "payload": <anything>}
                   -> appends one line, returns {"ok": true, "n": <lines now>}
    POST /finalize body = {"meta": {...}}  -> writes a .done marker
    GET  /status   -> {"ok": true, "lines": n, "bytes": n, "kinds": {...}}
    GET  /health   -> {"ok": true}
"""
import argparse
import json
import os
import sys
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
STATE = {"lines": 0, "bytes": 0, "kinds": Counter(), "out": None, "done": None}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_GET(self):
        if self.path.startswith("/health"):
            return self._send(200, {"ok": True})
        if self.path.startswith("/status"):
            with LOCK:
                return self._send(200, {
                    "ok": True,
                    "lines": STATE["lines"],
                    "bytes": STATE["bytes"],
                    "kinds": dict(STATE["kinds"]),
                    "out": STATE["out"],
                    "done": STATE["done"],
                })
        return self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception as e:
            return self._send(400, {"ok": False, "error": "bad json: %s" % e})

        if self.path.startswith("/append"):
            kind = body.get("kind") or "unknown"
            with LOCK:
                line = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
                with open(STATE["out"], "a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
                STATE["lines"] += 1
                STATE["bytes"] += len(line.encode("utf-8"))
                STATE["kinds"][kind] += 1
                return self._send(200, {"ok": True, "n": STATE["lines"]})

        if self.path.startswith("/finalize"):
            with LOCK:
                with open(STATE["done"], "w", encoding="utf-8") as fh:
                    json.dump(body.get("meta") or {}, fh, indent=2)
                return self._send(200, {"ok": True, "lines": STATE["lines"]})

        return self._send(404, {"ok": False, "error": "not found"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8793)
    ap.add_argument("--out", default=None)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()

    if a.out is None:
        here = os.path.dirname(os.path.abspath(__file__))
        a.out = os.path.normpath(os.path.join(
            here, "..", "..", "00_derived", "_epc_catalogue_raw.jsonl"))

    STATE["out"] = a.out
    STATE["done"] = a.out + ".done.json"
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    if os.path.exists(STATE["done"]):
        os.remove(STATE["done"])

    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print("collector listening on http://%s:%d" % (a.host, a.port), flush=True)
    print("appending to %s" % a.out, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("stopped: %d lines, %d bytes -> %s"
              % (STATE["lines"], STATE["bytes"], a.out), flush=True)


if __name__ == "__main__":
    sys.exit(main())
