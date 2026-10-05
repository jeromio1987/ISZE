"""Consolidate the batch-2 JSONL into the same shape as batch 1, and report the split.

Batch 1 output shape, which downstream scripts parse:
    [ {pn, total, found, editions, families, models}, ... ]
This writes batch 2 that way (payload.json) and prints the light-vehicle / truck split.

usage: python _batch2_finalize.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
JSONL = DER / "epc_decode_batch2_20260919.jsonl"
FINAL = DER / "epc_decode_batch2_20260919.json"
B2_TXT = DER / "epc_decode_batch_2.txt"


def main() -> int:
    rows = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    requested = [p.strip() for p in B2_TXT.read_text(encoding="ascii").splitlines() if p.strip()]
    have = {r["pn"] for r in rows}
    missing = [p for p in requested if p not in have]

    FINAL.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    lv, truck, none = [], [], []
    for r in rows:
        fams = " ".join(r.get("families") or []).upper()
        if not fams:
            none.append(r["pn"])
            continue
        if "PASSENGER" in fams and "TRUCK" not in fams and "BUS" not in fams:
            lv.append(r["pn"])
        else:
            truck.append(r["pn"])

    print(json.dumps({
        "records": len(rows),
        "requested": len(requested),
        "missing": len(missing),
        "found": sum(1 for r in rows if r.get("found")),
        "errors": sum(1 for r in rows if r.get("error")),
        "light_vehicle_only": len(lv),
        "touches_truck_or_bus": len(truck),
        "no_family": len(none),
        "families_seen": dict(Counter(f for r in rows for f in (r.get("families") or [])).most_common()),
        "final": str(FINAL),
        "missing_first10": missing[:10],
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
