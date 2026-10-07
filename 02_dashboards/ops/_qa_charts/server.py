"""QA server for the chart matrix: serves the ops folder and accepts a POST to write a file.

Python's stock http.server cannot accept a POST, so the page had no way to hand the matrix back.
This adds one: POST /save?f=<name> writes the body to _qa_charts/<name>. Local QA only;
it binds to 127.0.0.1 and is stopped when the run is finished.
"""
from __future__ import annotations

import argparse
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops")
QA = ROOT / "_qa_charts"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def do_POST(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/save":
            self.send_error(404)
            return
        q = urllib.parse.parse_qs(parsed.query)
        name = Path((q.get("f") or ["matrix.json"])[0]).name
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        QA.mkdir(parents=True, exist_ok=True)
        dest = QA / name
        dest.write_bytes(body)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(str(dest).encode("utf-8"))
        print("wrote", dest, len(body), "bytes", flush=True)

    def log_message(self, *a):  # keep the console for our own prints
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8952)
    args = ap.parse_args()
    print(f"serving {ROOT} on http://127.0.0.1:{args.port}  (POST /save?f=name writes to {QA})")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
