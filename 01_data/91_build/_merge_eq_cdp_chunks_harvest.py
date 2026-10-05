"""Merge CDP chunk dumps (value.chunk) and harvest into RESULTS. No AIM apply."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HARVEST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\harvest_eq_hit_session_20260919.py")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_harvest_payload_tmp.json")


def unwrap(raw):
    val = raw
    for _ in range(4):
        if isinstance(val, dict) and "result" in val:
            val = val["result"]
            continue
        break
    if isinstance(val, dict) and "value" in val:
        val = val["value"]
    if isinstance(val, str):
        val = json.loads(val)
    return val


def main() -> int:
    view = sys.argv[1]
    paths = [Path(p) for p in sys.argv[2:]]
    hits = []
    for p in paths:
        val = unwrap(json.loads(p.read_text(encoding="utf-8")))
        if isinstance(val, dict) and "chunk" in val:
            hits.extend(val["chunk"])
        elif isinstance(val, list):
            hits.extend(val)
        elif isinstance(val, dict) and "hits" in val:
            hits.extend(val["hits"])
        else:
            raise ValueError(f"bad shape in {p}: {type(val)} keys={list(val)[:8] if isinstance(val, dict) else None}")
    # de-dupe by pn keeping last
    by_pn = {}
    for h in hits:
        pn = h.get("pn")
        if pn:
            by_pn[pn] = h
    hits = list(by_pn.values())
    print(f"merged n={len(hits)} from {len(paths)} files view={view}")
    payload = {"view_id": view, "hits": hits}
    OUT.write_text(json.dumps(payload), encoding="utf-8")
    r = subprocess.run([sys.executable, str(HARVEST), str(OUT)], check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
