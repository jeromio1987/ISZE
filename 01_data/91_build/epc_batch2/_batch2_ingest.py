"""Ingest one CDP response file into the batch-2 JSONL.

The browser tool saves large Runtime.evaluate responses to a JSON file shaped
    {"result": {"type": "string", "value": "<json array of records>"}}
This pulls the array out, deduplicates by part number (keeping first occurrence order), and
rewrites the JSONL.

usage: python _batch2_ingest.py <cdp-response.json> [<more.json> ...]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
JSONL = ROOT / "01_data" / "00_derived" / "epc_decode_batch2_20260919.jsonl"


def load_file(p: Path) -> list[dict]:
    raw = json.loads(p.read_text(encoding="utf-8"))
    val = raw["result"]["value"]
    if isinstance(val, str):
        val = json.loads(val)
    return val


def main(files: list[str]) -> int:
    rows: list[dict] = []
    if JSONL.is_file():
        for line in JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    before = len(rows)
    for f in files:
        rows.extend(load_file(Path(f)))

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        pn = str(r.get("pn", ""))
        if not pn or pn.startswith("__"):
            continue
        if pn in seen:
            continue
        seen.add(pn)
        out.append(r)

    with open(JSONL, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    print(json.dumps({
        "existing_rows": before,
        "files_ingested": len(files),
        "unique_rows_now": len(out),
        "errors": sum(1 for r in out if r.get("error")),
        "jsonl": str(JSONL),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
