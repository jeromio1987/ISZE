"""Evidence of concurrent writes to the backlog page and the classification file."""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

OPS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops")
DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

html = OPS / "ISZE_Backlog_IML_WK41.html"
s = html.read_text(encoding="utf-8")
m = re.search(r'"build":"([^"]+)"', s)
print("artifact              :", html)
print("mtime                 :", dt.datetime.fromtimestamp(html.stat().st_mtime))
print("bytes                 :", len(s))
print("build stamp in file   :", m.group(1) if m else "none")
print("my defensive marker   :", "Fallbacks used during this render" in s)
print("my warning slots      :", s.count('id="warn-p-'))
print("another writer marker :", ("click that distributor" in s) or ("deep dive for that distributor" in s))
print("another writer marker2:", "click that distributor's bar above" in s)
print()

print("aim_master_v2.csv     :", dt.datetime.fromtimestamp((DER / "aim_master_v2.csv").stat().st_mtime))
for p in sorted(DER.glob("aim_master_v2.csv.bak*"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
    print("   backup             :", dt.datetime.fromtimestamp(p.stat().st_mtime), p.name)
print()

now = dt.datetime.now()
print("files in ops/ and 00_derived/ changed in the last 60 minutes:")
rows = []
for base in (OPS, DER):
    for p in base.rglob("*"):
        if p.is_file() and (now - dt.datetime.fromtimestamp(p.stat().st_mtime)) < dt.timedelta(minutes=60):
            rows.append((dt.datetime.fromtimestamp(p.stat().st_mtime), p))
for t, p in sorted(rows, reverse=True)[:20]:
    print(f"   {t}  {p.name}")
