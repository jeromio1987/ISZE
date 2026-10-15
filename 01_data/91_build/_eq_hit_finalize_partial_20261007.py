"""Merge status batch + write final partial summary. Evidence only."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build")
STATUS_BATCH = DER / "_eq_hit_harvest_status_batch_20261007.json"
PRIOR = DER / "_eq_hit_harvest_raw_20261007.json"
MERGE = BUILD / "_eq_hit_merge_harvest_20261007.py"


def main() -> int:
    if not STATUS_BATCH.exists():
        print("missing status batch", STATUS_BATCH)
        return 2
    status = json.loads(STATUS_BATCH.read_text(encoding="utf-8"))
    prior = json.loads(PRIOR.read_text(encoding="utf-8")) if PRIOR.exists() else []
    by = {h["pn"]: h for h in prior}
    for h in status:
        # do not overwrite rich fig hits with status-only empties
        old = by.get(h["pn"])
        if old and (old.get("eq_fig_name") or old.get("eq_part_name")) and not (
            h.get("eq_fig_name") or h.get("eq_part_name")
        ):
            continue
        by[h["pn"]] = h
    out = list(by.values())
    PRIOR.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("merged_total", len(out))
    r = subprocess.run([sys.executable, str(MERGE), "partial_session_slow_ui"], check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
