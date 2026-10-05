"""Extract the heavy-catalogue evidence the browser captured, and write the deliverables.

Input:  the CDP response file the browser wrote for the F&G edition-list call
Output: 01_data/00_derived/epc_catalogue_heavy_20260919.json
        01_data/00_derived/epc_catalogue_heavy_20260919.csv
        01_data/00_derived/epc_heavy_editions_20260919.json
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
CDP_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else None

# ANCHORED whole-token match. The defect this guards against: a marker list containing a bare
# 'F*' (or a plain "contains F" test) also matches 'TF*', the D-Max light pickup. That error
# inflated a heavy-truck figure by EUR 1.8M. Every alternative below is anchored with ^...(\b|$)
# so a token must START with it as a whole token, never appear mid-token.
SERIES_RE = re.compile(
    r"(?:^|[\s,/\(\)])((?:FRR|FSR|FTR|FVR|FVM|FVZ|FSS|FTS|FVD|FXZ|GVR|CXH|CXZ|CVR|CYH)"
    r"(?=[\s,/\(\)\-]|$))"
)


def find_payload(obj):
    """Walk the CDP envelope for the JSON string our expression returned."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "value" and isinstance(v, str) and "editions" in v:
                return v
            got = find_payload(v)
            if got:
                return got
    elif isinstance(obj, list):
        for x in obj:
            got = find_payload(x)
            if got:
                return got
    return None


def series_tokens(text):
    return sorted({m.group(1) for m in SERIES_RE.finditer(text or "")})


def main():
    if not CDP_FILE or not CDP_FILE.is_file():
        print("need the CDP response file as argv[1]")
        return 2

    payload = find_payload(json.loads(CDP_FILE.read_text(encoding="utf-8")))
    if not payload:
        print("no payload found in", CDP_FILE)
        return 3

    j = json.loads(payload)
    editions = j.get("editions") or []
    print(f"branches        : {j.get('branches')}")
    print(f"session invalid : {j.get('sessionInvalid')}")
    print(f"editions read   : {len(editions)}")

    # An edition name looks like "11395 - 2011- FRR (RHD)EURO1 11.0 - "
    rows = []
    for i, name in enumerate(editions, start=1):
        m = re.match(r"^\s*(\d{3,6})\s*-\s*(.*)$", name)
        ed_id = m.group(1) if m else None
        ed_text = m.group(2).strip() if m else name.strip()
        rows.append({
            "part_number": None,
            "figkey": None,
            "part_name": None,
            "edition_id": ed_id,
            "edition_text": name.strip(),
            "catalogue_family": "TRUCKS F&G",
            "systems_path": None,
            "series_tokens": "|".join(series_tokens(name)),
        })

    tok = {}
    for r in rows:
        for t in (r["series_tokens"].split("|") if r["series_tokens"] else []):
            tok[t] = tok.get(t, 0) + 1
    print(f"distinct series tokens seen: {len(tok)}")
    for k, v in sorted(tok.items(), key=lambda kv: -kv[1]):
        print(f"   {v:5d}  {k}")

    DER.mkdir(parents=True, exist_ok=True)

    # The edition inventory (real data, saved)
    (DER / "epc_heavy_editions_20260919.json").write_text(
        json.dumps({
            "catalogue_family": "TRUCKS F&G",
            "source": "EQ-Hit EPC, /epc-services navigation call read from the live page",
            "captured": "2026-09-19T10:52Z",
            "edition_count": len(rows),
            "editions": rows,
        }, indent=1, ensure_ascii=False), encoding="utf-8")

    csv_path = DER / "epc_catalogue_heavy_20260919.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "part_number", "figkey", "part_name", "edition_id", "edition_text",
            "catalogue_family", "systems_path", "series_tokens"])
        w.writeheader()
        w.writerows(rows)

    (DER / "epc_catalogue_heavy_20260919.json").write_text(
        json.dumps({
            "catalogue_family": "TRUCKS F&G",
            "collection_status": "PARTIAL - editions only, no part rows",
            "reason": ("The EPC session was invalidated before part-row extraction, and this "
                       "session has no route for bulk CDP results to reach disk. Editions are "
                       "genuine captured data; the part_number/figkey/part_name columns are "
                       "empty because no FIG page was ever read."),
            "edition_count": len(rows),
            "distinct_part_numbers": 0,
            "rows": rows,
        }, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\nwrote {csv_path}")
    print(f"wrote {DER / 'epc_catalogue_heavy_20260919.json'}")
    print(f"wrote {DER / 'epc_heavy_editions_20260919.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
