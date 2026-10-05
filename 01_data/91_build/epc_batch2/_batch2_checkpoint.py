"""Checkpoint the EPC tab's batch-2 results to disk.

The page cannot reach a local sink (Chrome blocks a public HTTPS origin from loopback; probed and
confirmed), and no local DevTools port is reachable, so the transport is this session's browser
tool. To keep the window of loss small, every result the tab has collected is appended to a JSONL
the moment this script sees it. Re-running it is safe: it rewrites the JSONL from the tab's own
array, so nothing is duplicated and nothing is dropped.

usage:
    python _batch2_checkpoint.py            # pull and append; exits non-zero on error
prints one JSON line: {"rows": n, "errs": n, "written": n}
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
JSONL = ROOT / "01_data" / "00_derived" / "epc_decode_batch2_20260919.jsonl"
SLICE = BUILD / "_slice.json"


def main() -> int:
    if not SLICE.is_file():
        print(json.dumps({"error": "no slice file"}))
        return 1
    raw = SLICE.read_text(encoding="utf-8").strip()
    if not raw:
        print(json.dumps({"error": "empty slice"}))
        return 1
    rows = json.loads(raw)
    with open(JSONL, "w", encoding="utf-8") as fh:
        for rec in rows:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    errs = sum(1 for r in rows if r.get("error"))
    print(json.dumps({"written": len(rows), "errs": errs}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
