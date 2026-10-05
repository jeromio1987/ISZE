"""Ad-hoc: fingerprint the family-evolution page payload and the billing cache before a label fix.

Writes _tmp_page_payload_before_20260922.json (the embedded pmfe2-data payload) and prints a hash
of the billing cache, so the same comparison can be run after the rebuild.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
CACHE = ROOT / "02_dashboards" / "sales" / "_build" / "_deep_billing_cache.parquet"
OUT = ROOT / "01_data" / "00_derived" / "_tmp_page_payload_before_20260922.json"

html = HTML.read_text(encoding="utf-8")
m = re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>', html, re.S)
payload = json.loads(m.group(1))
OUT.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")

print("page mtime       :", HTML.stat().st_mtime)
print("payload bytes    :", len(m.group(1)))
print("payload keys     :", sorted(payload.keys()))
print("generated        :", payload.get("generated"))
print("bands[0..2]      :", [(b["key"], b.get("note")) for b in payload["bands"][:3]])
print("seriesEvidence   :", {k: v.get("series") for k, v in
                             payload.get("seriesEvidence", {}).items()})
print("cache sha256     :", hashlib.sha256(CACHE.read_bytes()).hexdigest())
print("cache bytes      :", CACHE.stat().st_size)
print("wrote", OUT)
