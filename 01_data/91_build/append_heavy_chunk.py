"""Append one drained CDP row-array to the heavy catalogue JSONL.

usage: append_heavy_chunk.py <cdp_response.json> <system_label>
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
JSONL = DER / "epc_catalogue_heavy_rows_20260919.jsonl"


def find_array(obj):
    """Accept either a CDP envelope wrapping our array, or a plain array file."""
    if isinstance(obj, list):
        # a top-level array of row dicts is already what we want
        if obj and isinstance(obj[0], dict) and "part_number" in obj[0]:
            return json.dumps(obj)
        for x in obj:
            got = find_array(x)
            if got:
                return got
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k == "value" and isinstance(v, str) and v.strip().startswith("["):
                return v
            got = find_array(v)
            if got:
                return got
    return None


def main(argv):
    if len(argv) < 3:
        print("usage: append_heavy_chunk.py <cdp_response.json> <system_label>")
        return 2
    cdp = Path(argv[1])
    label = argv[2]

    rows = json.loads(find_array(json.loads(cdp.read_text(encoding="utf-8"))))
    with open(JSONL, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    lines = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    pns = {r["part_number"] for r in lines if r.get("part_number")}
    import re
    # ANCHORED whole-token series match. Guards against a bare 'F*' style marker that would
    # also match 'TF*' (D-Max light pickup) - the error that inflated a heavy figure by EUR 1.8M.
    tok = {}
    for r in lines:
        path = (r.get("systems_path") or "") + " " + (r.get("part_name") or "")
        for m in re.finditer(r"(?:^|[\s,/\(\)])(FRR|FSR|FTR|FVR|FVM|FVZ|FSS|FTS|FVD|FXZ|GVR|CXH|CXZ|CVR|CYH)(?=[\s,/\(\)\-]|$)", path):
            tok[m.group(1)] = tok.get(m.group(1), 0) + 1

    print(f"{label}: +{len(rows)} rows")
    print(f"JSONL now {len(lines)} rows, {len(pns)} distinct part numbers")
    print("systems covered so far:")
    for s in sorted({(r.get('systems_path') or '').split(' > ')[0] for r in lines}):
        print("   ", s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
