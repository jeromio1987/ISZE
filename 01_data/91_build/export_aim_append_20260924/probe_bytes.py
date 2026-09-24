# -*- coding: utf-8 -*-
"""Read-only: byte-level facts about the master and the existing dated pairs."""
from __future__ import annotations

import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
P = D / "aim_master_v2.csv"

b = P.read_bytes()
print("bytes", len(b))
print("BOM", b[:3] == b"\xef\xbb\xbf")
print("double quotes", b.count(b'"'))
print("CRLF", b.count(b"\r\n"), "bare LF", b.count(b"\n") - b.count(b"\r\n"))
print("sha256", hashlib.sha256(b).hexdigest())
lines = b.split(b"\r\n")
print("split parts", len(lines))
print("head", lines[0][:200])
print("last non-empty", lines[-2][:160] if lines[-1] == b"" else lines[-1][:160])
print("trailing newline", b.endswith(b"\r\n"))
st = P.stat()
print("mtime", datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat())

print("\n--- existing dated pairs in 00_derived ---")
for f in sorted(D.glob("AIM_Master_PN_Categories_Figkey_*")):
    print(f"  {f.name:<56} {f.stat().st_size:>12,} bytes   {f.stat().st_mtime}")

print("\n--- max row length in master (to check quoting need) ---")
with P.open(encoding="utf-8", newline="") as fh:
    rd = csv.reader(fh)
    hdr = next(rd)
    mx = 0
    mxrow = None
    for r in rd:
        n = sum(len(x) for x in r)
        if n > mx:
            mx, mxrow = n, r
print("max combined field length:", mx, "| longest cells:", sorted((len(x) for x in mxrow), reverse=True)[:6])
