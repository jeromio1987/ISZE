"""Merge the drained F&G part-row halves and append them to the heavy catalogue files.

Input:  the two CDP response files holding window.__rowsX.slice(0,420) and .slice(420)
Output: 01_data/00_derived/epc_heavy_fg_system0_rows_20260919.json  (this chunk)
        01_data/00_derived/epc_catalogue_heavy_rows_20260919.jsonl (append-only accumulation)
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
JSONL = DER / "epc_catalogue_heavy_rows_20260919.jsonl"


def find_array(obj):
    """The CDP envelope wraps our array in result.value as a JSON string."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "value" and isinstance(v, str) and v.strip().startswith("["):
                return v
            got = find_array(v)
            if got:
                return got
    elif isinstance(obj, list):
        for x in obj:
            got = find_array(x)
            if got:
                return got
    return None


def main(argv):
    if len(argv) < 3:
        print("usage: merge_heavy_rows.py <cdp1> <cdp2> ...")
        return 2

    rows = []
    for p in argv[1:]:
        payload = find_array(json.loads(Path(p).read_text(encoding="utf-8")))
        if not payload:
            print(f"  no array in {Path(p).name}")
            continue
        got = json.loads(payload)
        print(f"  {Path(p).name}: {len(got)} rows")
        rows.extend(got)

    # de-dup on (part_number, figkey, systems_path) - the same PN legitimately repeats
    # under different FIGKEYs, that is catalogue structure, not duplication.
    seen = set()
    out = []
    for r in rows:
        k = (r.get("part_number"), r.get("figkey"), r.get("systems_path"))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)

    print(f"total rows read : {len(rows)}")
    print(f"distinct rows   : {len(out)}")
    pns = {r["part_number"] for r in out if r.get("part_number")}
    print(f"distinct part numbers: {len(pns)}")

    DER.mkdir(parents=True, exist_ok=True)
    chunk = DER / "epc_heavy_fg_system0_rows_20260919.json"
    chunk.write_text(json.dumps({
        "catalogue_family": "TRUCKS F&G",
        "edition": "11395 - 2011- FRR (RHD)EURO1 11.0 -",
        "system": "0 - ENGINE,EMISSION,ENGINE ELECTRICAL",
        "subsections_crawled": 36,
        "rows": out,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {chunk}")

    with open(JSONL, "a", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"appended to {JSONL}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
