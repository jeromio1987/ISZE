# -*- coding: utf-8 -*-
"""Read-only: prove a csv round-trip reproduces the master byte-for-byte, so the write is safe."""
from __future__ import annotations

import csv
import hashlib
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv")
orig = P.read_bytes()
print("orig bytes", len(orig), "sha256", hashlib.sha256(orig).hexdigest()[:16])

with P.open(encoding="utf-8", newline="") as fh:
    rd = csv.reader(fh)
    rows = list(rd)

buf = io.StringIO()
w = csv.writer(buf, lineterminator="\r\n")
w.writerows(rows)
out = buf.getvalue().encode("utf-8")
print("round-trip bytes", len(out), "sha256", hashlib.sha256(out).hexdigest()[:16])
print("BYTE-IDENTICAL:", out == orig)
if out != orig:
    # find first difference
    for i, (a, b) in enumerate(zip(orig, out)):
        if a != b:
            print("first diff at byte", i)
            print("orig:", orig[max(0, i - 80):i + 80])
            print("out :", out[max(0, i - 80):i + 80])
            break
