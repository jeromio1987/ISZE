"""Harvest EQ CDP JSON (inline or browser-logs) into overnight RESULTS."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HARVEST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\harvest_eq_hit_session_20260919.py")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_harvest_payload_tmp.json")


def extract_hits(raw):
    # Unwrap common CDP shapes
    val = raw
    if isinstance(val, dict):
        if "result" in val:
            val = val["result"]
        if isinstance(val, dict) and "result" in val:
            val = val["result"]
        if isinstance(val, dict) and "value" in val:
            val = val["value"]
    if isinstance(val, str):
        val = json.loads(val)
    if isinstance(val, dict) and "hits" in val:
        return val["hits"], val
    if isinstance(val, list):
        return val, {"n": len(val)}
    raise ValueError(f"unrecognized shape: {type(val)}")


def main() -> int:
    path = Path(sys.argv[1])
    view = sys.argv[2] if len(sys.argv) > 2 else ""
    raw = json.loads(path.read_text(encoding="utf-8"))
    hits, meta = extract_hits(raw)
    print(f"extracted n={len(hits)} meta={ {k: meta.get(k) for k in ('from','to','n') if isinstance(meta, dict)} }")
    payload = {"view_id": view, "hits": hits}
    OUT.write_text(json.dumps(payload), encoding="utf-8")
    r = subprocess.run([sys.executable, str(HARVEST), str(OUT)], check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
