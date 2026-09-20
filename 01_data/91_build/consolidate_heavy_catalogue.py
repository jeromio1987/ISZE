"""Consolidate the heavy-catalogue JSONL into the two required deliverables.

Input : 01_data/00_derived/epc_catalogue_heavy_rows_20260919.jsonl
Output: 01_data/00_derived/epc_catalogue_heavy_20260919.json
        01_data/00_derived/epc_catalogue_heavy_20260919.csv

Columns required by the brief:
  part_number, figkey, part_name, edition_id, edition_text, catalogue_family,
  systems_path, series_tokens

series_tokens uses an ANCHORED whole-token match. The defect this guards against: a marker
list containing a bare 'F*', or a plain "contains F" test, also matches 'TF*' - the D-Max
light pickup. That error inflated a heavy-truck figure by EUR 1.8M. Every alternative is
anchored so the token must stand alone.
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
JSONL = DER / "epc_catalogue_heavy_rows_20260919.jsonl"
EDITION_ID = "11395"
EDITION_TEXT = "11395 - 2011- FRR (RHD)EURO1 11.0 -"
FAMILY = "TRUCKS F&G"

# ANCHORED. Must be preceded by a boundary/space and stand alone as a token.
SERIES_ANCHORED = re.compile(
    r"(?:^|[\s>/,\(\)\-])"
    r"(FRR|FSR|FTR|FVR|FVM|FVZ|FSS|FTS|FVD|FXZ|GVR|CXH|CXZ|CVR|CYH)"
    r"(?=[\s>/,\(\)\-]|$)"
)


def main():
    rows_in = [json.loads(l) for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"rows in JSONL : {len(rows_in)}")

    out = []
    for r in rows_in:
        hay = f"{EDITION_TEXT} {r.get('systems_path') or ''}"
        toks = sorted({m.group(1) for m in SERIES_ANCHORED.finditer(hay)})
        out.append({
            "part_number": r.get("part_number"),
            "figkey": r.get("figkey"),
            "part_name": r.get("part_name"),
            "edition_id": EDITION_ID,
            "edition_text": EDITION_TEXT,
            "catalogue_family": FAMILY,
            "systems_path": r.get("systems_path"),
            "series_tokens": "|".join(toks),
            # extras kept for traceability
            "part_number_formatted": r.get("part_number_formatted"),
            "page_id": r.get("page_id"),
        })

    pns = {r["part_number"] for r in out if r["part_number"]}
    print(f"distinct part numbers : {len(pns)}")

    tok = Counter()
    for r in out:
        for t in (r["series_tokens"].split("|") if r["series_tokens"] else []):
            tok[t] += 1
    print("series tokens (anchored):")
    for k, v in tok.most_common():
        print(f"   {v:5d}  {k}")

    # guard: prove the anchored match did NOT pick up D-Max 'TF' tokens
    bad = [r for r in out if "TF" in (r["series_tokens"] or "").split("|")]
    print(f"rows with a TF* (D-Max) token in series_tokens: {len(bad)}  (must be 0)")

    (DER / "epc_catalogue_heavy_20260919.json").write_text(
        json.dumps({
            "catalogue_family": FAMILY,
            "collection_status": "PARTIAL - one complete edition, all 10 systems",
            "editions_in_family": 635,
            "editions_crawled": 1,
            "edition_id": EDITION_ID,
            "edition_text": EDITION_TEXT,
            "systems_crawled": 10,
            "subsections_crawled": 165,
            "rows": len(out),
            "distinct_part_numbers": len(pns),
            "series_token_rule": SERIES_ANCHORED.pattern,
            "rows_data": out,
        }, indent=1, ensure_ascii=False), encoding="utf-8")

    csv_path = DER / "epc_catalogue_heavy_20260919.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "part_number", "figkey", "part_name", "edition_id", "edition_text",
            "catalogue_family", "systems_path", "series_tokens",
            "part_number_formatted", "page_id"])
        w.writeheader()
        w.writerows(out)

    print(f"\nwrote {DER / 'epc_catalogue_heavy_20260919.json'}")
    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
