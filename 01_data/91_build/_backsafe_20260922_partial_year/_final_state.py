"""Final state check across every file in the change set. Read-only.
Writes nothing except a JSON record of after-sha256 for the manifest.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent

FILES = [
    "03_analytics/Isuzu/prism/scripts/enrich_gps_spu_v9.py",
    "01_data/00_derived/gps_spu_by_distributor.csv",
    "01_data/15_gpt_safe/gps_spu_by_distributor.csv",
    "03_analytics/Isuzu/prism/evidence-app/data/derived/gps_spu_by_distributor.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_distributor.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv",
    "01_data/00_derived/network_percentile.csv",
    "01_data/00_derived/aim_gps_matrix.csv",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(p: Path):
    raw = p.read_bytes()
    enc = "utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8"
    with p.open(encoding=enc, newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


record = {}
for rel in FILES:
    p = ROOT / rel
    entry = {"sha256_after": sha(p), "bytes_after": p.stat().st_size}
    if p.suffix == ".csv":
        cols, rws = rows(p)
        entry["rows"] = len(rws)
        entry["cols"] = len(cols)
        entry["has_period_basis"] = "period_basis" in cols
        y26 = [r for r in rws if r.get("year") == "2026"]
        entry["n_2026"] = len(y26)
        entry["n_2026_with_capture"] = sum(
            1 for r in y26 if (r.get("gps_capture_vs_max") or "").strip()
        )
        entry["n_2026_coloured_v9"] = sum(
            1
            for r in y26
            if (r.get("traffic_light_v9") or "").strip() not in ("", "unknown")
        )
    record[rel] = entry

(HERE / "_after.json").write_text(json.dumps({"files": record}, indent=2), encoding="utf-8")

for rel, e in record.items():
    print(f"{rel}")
    print(f"   {e['sha256_after'][:16]}  {e['bytes_after']:>7} bytes  {e}")
print(f"\nrecorded -> {HERE / '_after.json'}")
