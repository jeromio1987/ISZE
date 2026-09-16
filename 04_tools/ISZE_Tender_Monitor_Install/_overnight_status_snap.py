#!/usr/bin/env python3
from pathlib import Path
import json

env = Path("nordics_api_keys.env").read_text(encoding="utf-8")
for line in env.splitlines():
    if "KEY" in line and "=" in line:
        k, v = line.split("=", 1)
        print(k, "EMPTY" if not v.strip() else f"LEN={len(v.strip())}")

h = json.loads(Path("_source_health.json").read_text(encoding="utf-8"))
for k, v in h.items():
    print(f"{k}: {v.get('status')} count={v.get('last_count')}")
