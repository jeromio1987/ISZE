"""Merge one EQ-HIT result JSON object into cumulative live results + extract CSV."""
from __future__ import annotations

import json
import sys
from pathlib import Path

LIVE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_eqhit_live_results.json")
APPEND = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_append_eqhit_extract.py")


def main() -> None:
    obj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if isinstance(obj, list):
        rows = obj
    else:
        rows = [obj]
    existing = []
    if LIVE.exists():
        existing = json.loads(LIVE.read_text(encoding="utf-8"))
    by_pn = {r.get("pn"): r for r in existing if r.get("pn")}
    for r in rows:
        if r.get("pn"):
            by_pn[r["pn"]] = r
    merged = list(by_pn.values())
    LIVE.write_text(json.dumps(merged, indent=1), encoding="utf-8")
    # reuse append script
    tmp = LIVE.parent / "_eqhit_tmp.json"
    tmp.write_text(json.dumps(merged), encoding="utf-8")
    import runpy

    sys.argv = [str(APPEND), str(tmp)]
    runpy.run_path(str(APPEND), run_name="__main__")
    print(f"live_pns={len(merged)}")


if __name__ == "__main__":
    main()
