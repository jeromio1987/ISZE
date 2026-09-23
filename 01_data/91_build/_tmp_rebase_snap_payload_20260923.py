"""Freeze the page's own payload before the re-base, so the rebuild can be diffed against it.

Writes the embedded JSON to disk as a JSON file. After the rebuild the same extraction is diffed
against this, which is how "no other number moved" is proved rather than asserted.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
OUT = ROOT / "01_data" / "91_build" / "_rebase_payload_before_20260923.json"

m = re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
              HTML.read_text(encoding="utf-8"), re.S)
if not m:
    print("no payload found")
    raise SystemExit(2)
data = json.loads(m.group(1))
OUT.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
print(f"payload keys {len(data)} -> {OUT}")
print(f"size {OUT.stat().st_size:,} bytes")
for k in sorted(data):
    v = data[k]
    print(f"   {k:22s} {type(v).__name__:6s} "
          f"{len(v) if isinstance(v, (list, dict, str)) else v}")
