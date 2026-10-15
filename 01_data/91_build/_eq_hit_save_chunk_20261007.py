"""Save one harvest chunk JSON from argv file path -> append to cumulative harvest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
CUM = DER / "_eq_hit_harvest_cum_20261007.json"
PRIOR = DER / "_eq_hit_harvest_raw_20261007.json"


def main() -> int:
    chunk_path = Path(sys.argv[1])
    chunk = json.loads(chunk_path.read_text(encoding="utf-8"))
    if CUM.exists():
        cum = json.loads(CUM.read_text(encoding="utf-8"))
    elif PRIOR.exists():
        cum = json.loads(PRIOR.read_text(encoding="utf-8"))
    else:
        cum = []
    by = {h["pn"]: h for h in cum}
    for h in chunk:
        by[h["pn"]] = h
    out = list(by.values())
    CUM.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    # also point merge input at cum
    (DER / "_eq_hit_harvest_raw_20261007.json").write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8"
    )
    print(f"cum={len(out)} chunk={len(chunk)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
