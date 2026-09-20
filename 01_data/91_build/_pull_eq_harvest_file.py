"""Pull EQ overnight hits from a JSON file (from CDP) and harvest."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

INBOX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
HARVEST = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\harvest_eq_hit_session_20260919.py")


def main() -> int:
    path = Path(sys.argv[1])
    view = sys.argv[2] if len(sys.argv) > 2 else ""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, str):
        hits = json.loads(raw)
    else:
        hits = raw
    payload = {"view_id": view, "hits": hits}
    tmp = INBOX / "_eq_harvest_payload_tmp.json"
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    r = subprocess.run([sys.executable, str(HARVEST), str(tmp)], check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
