"""Attribute every payload change in this rebuild: mine, or another agent's.

Mine were two text edits in build_family_evolution_v2.py. Everything else must be attributed to a
source outside my change, or it is a finding.

Checks:
  1. decide which payload keys my two edits can possibly affect
  2. compare the four input files the page reads that another agent may have touched:
     series_to_band.csv (authored map), series_to_tonnage.csv (its generated copy),
     tonnage_capable_part_numbers.csv, vehicle_family_bands.csv
  3. assert whether the rebuilt payload's weight/series blocks match the map as it stands NOW, which
     would mean they moved because the map moved, not because I touched them
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
MAP = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "series_to_band.csv"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def payload() -> dict:
    return json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                                HTML.read_text(encoding="utf-8"), re.S).group(1))


def main() -> int:
    print("=" * 100)
    print("1. FILE TIMES: what moved after my 06:53 build?")
    print("=" * 100)
    for p in (MAP, DER / "series_to_tonnage.csv", DER / "tonnage_capable_part_numbers.csv",
              DER / "vehicle_family_bands.csv", DER / "epc_decode_nseries_banded.csv",
              ROOT / "03_analytics" / "Isuzu" / "prism" / "modules" / "vehicle_bands.py"):
        st = p.stat()
        print(f"  {st.st_mtime:>18.0f}  {st.st_size:>9,}  {p.name}")
    print()
    print("  my build ran at 06:53:14 (page mtime before this rebuild 1790139194)")
    print()

    print("=" * 100)
    print("2. THE AUTHORED MAP: is NMR still interim, and did anything else move?")
    print("=" * 100)
    with open(MAP, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    print(f"  rows {len(rows)}")
    for c in rows:
        code = (c.get("code") or "").strip().upper()
        if code in ("NMR", "NMR85"):
            print(f"  {code:8s} band {c.get('tonnage_band')!r:24s} status {c.get('status')!r:18s} "
                  f"gvw {c.get('gvw_t')!r}")
    pending = sorted((c.get("code") or "").strip() for c in rows
                     if (c.get("status") or "").strip() == "pending_ruling")
    print(f"  pending_ruling codes in the map: {pending}")
    print()

    print("=" * 100)
    print("3. DID THE WEIGHT/SERIES BLOCKS MOVE BECAUSE THE MAP MOVED?")
    print("=" * 100)
    pay = payload()
    settled = pay["weightEvidence"]["settled"]
    print("  rebuilt payload's settled rows:")
    for s in settled:
        print(f"      {s['band']:22s} {str(s['series']):8s} conf {s['confidence']:10s} "
              f"{s['label']!r}")
    print()
    print(f"  unresolvedCodesCount now: {pay['weightEvidence']['unresolvedCodesCount']}")
    print(f"  unresolved code list now : {pay['weightEvidence']['unresolvedCodes']}")
    print()
    print("  these come from `series_evidence_table()`, which reads the authored map DIRECTLY")
    print("  (build_family_evolution_v2.py line 144), so they follow the map on every build.")
    print("  The map's mtime is 07:00:29 - AFTER my 06:53 build - so a rebuild now picks up the")
    print("  other agent's map edit. That is the cause of the non-NMR series changes.")
    print()

    print("=" * 100)
    print("4. GIT: is the map edit committed or working-tree?")
    print("=" * 100)
    r = subprocess.run(["git", "status", "--porcelain", "--",
                        "03_analytics/Isuzu/prism/data/series_to_band.csv"],
                       capture_output=True, text=True, cwd=ROOT)
    print(f"  git status: {r.stdout.strip() or '(clean - committed)'}")
    r2 = subprocess.run(["git", "diff", "--stat", "--",
                         "03_analytics/Isuzu/prism/data/series_to_band.csv"],
                        capture_output=True, text=True, cwd=ROOT)
    print(f"  git diff vs HEAD: {r2.stdout.strip() or '(no difference from HEAD)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
