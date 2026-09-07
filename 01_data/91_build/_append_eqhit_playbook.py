"""APPEND-ONLY EQ-HIT rows into playbook-schema extract CSV. Never truncates existing rows."""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\eqhit_extract_priority_cy2025.csv")
FIELDS = [
    "pull_date",
    "rank",
    "pms_category",
    "part_number",
    "description",
    "vehicle_model",
    "engine_code",
    "chassis_family",
    "lcv_generation",
    "bucket",
    "applicable",
    "eqhit_source",
    "status",
    "notes",
]

RANK = {
    "clutch_disc": 1,
    "brake_shoe": 2,
    "brake_pad": 3,
    "clutch_pressure_plate": 4,
    "blower_filter": 5,
    "brake_rotor": 6,
    "fuel_filter": 7,
}

SEED_DESC = {}
_seed = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\eqhit_priority_top_pns_cy2025.csv")
if _seed.exists():
    with _seed.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            SEED_DESC[r["part_number"]] = r.get("description", "")


def classify(family: str, text: str) -> tuple[str, str, str]:
    fam = (family or "").upper()
    t = (text or "").upper()
    if "PASSENGER VEHICLE" in fam or "TFR" in t or "TFS" in t or "D-MAX" in t or "DMAX" in t:
        gen = "dmax_rt" if any(y in t for y in ("2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019")) else "unknown"
        if "SUV" in fam:
            return "TFR/TFS", gen, "lcv"
        return "TFR/TFS", gen, "lcv"
    if "TRUCKS N" in fam or re.search(r"\bN[HJKLPQRMS]", t):
        return "N-series", "unknown", "cv_std"
    if "TRUCKS F" in fam or re.search(r"\bF[A-Z]{2}", t):
        return "F-series", "unknown", "f_series"
    if "BUSES" in fam:
        return "Buses", "unknown", "unknown"
    return "unknown", "unknown", "unknown"


def existing_pns() -> set[str]:
    if not OUT.exists():
        return set()
    with OUT.open(encoding="utf-8", newline="") as f:
        return {(r.get("part_number") or "").strip() for r in csv.DictReader(f) if r.get("part_number")}


def existing_catalog_keys() -> set[tuple[str, str]]:
    """(part_number, catalog_id) already on disk. Empty catalog_id kept as ''."""
    if not OUT.exists():
        return set()
    keys: set[tuple[str, str]] = set()
    with OUT.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pn = (r.get("part_number") or "").strip()
            if not pn:
                continue
            notes = r.get("notes") or ""
            m = re.search(r"catalog_id=([^;]+)", notes)
            cid = m.group(1).strip() if m else ""
            keys.add((pn, cid))
    return keys


def rows_from_scrape(scrape: dict, pms_category: str, description: str = "") -> list[dict]:
    pn = str(scrape.get("pn") or "").strip()
    pull = date.today().isoformat()
    rank = RANK.get(pms_category, "")
    desc = description or SEED_DESC.get(pn, "")
    total = scrape.get("total")
    if scrape.get("error"):
        return [
            {
                "pull_date": pull,
                "rank": rank,
                "pms_category": pms_category,
                "part_number": pn,
                "description": desc,
                "vehicle_model": "",
                "engine_code": "",
                "chassis_family": "unknown",
                "lcv_generation": "unknown",
                "bucket": "unknown",
                "applicable": "unknown",
                "eqhit_source": "part_search_across_catalogues",
                "status": "partial",
                "notes": f"error={scrape.get('error')}",
            }
        ]
    if total == 0 or scrape.get("found") is False:
        return [
            {
                "pull_date": pull,
                "rank": rank,
                "pms_category": pms_category,
                "part_number": pn,
                "description": desc,
                "vehicle_model": "",
                "engine_code": "",
                "chassis_family": "unknown",
                "lcv_generation": "unknown",
                "bucket": "unknown",
                "applicable": "false",
                "eqhit_source": "part_search_across_catalogues",
                "status": "partial",
                "notes": f"EQ-HIT global search Total Results: 0",
            }
        ]
    out: list[dict] = []
    by_fam = scrape.get("byFamily") or {}
    harvested = sum(len(v) for v in by_fam.values())
    for fam, items in by_fam.items():
        for it in items:
            text = it.get("text") or ""
            cid = it.get("id") or ""
            chassis, gen, bucket = classify(fam, text)
            out.append(
                {
                    "pull_date": pull,
                    "rank": rank,
                    "pms_category": pms_category,
                    "part_number": pn,
                    "description": desc,
                    "vehicle_model": text,
                    "engine_code": "",
                    "chassis_family": chassis,
                    "lcv_generation": gen,
                    "bucket": bucket,
                    "applicable": "true",
                    "eqhit_source": "part_search_across_catalogues",
                    "status": "ok",
                    "notes": f"catalog_id={cid}; parent={fam}; total_results={total}; harvested={harvested}",
                }
            )
    if not out:
        out.append(
            {
                "pull_date": pull,
                "rank": rank,
                "pms_category": pms_category,
                "part_number": pn,
                "description": desc,
                "vehicle_model": "",
                "engine_code": "",
                "chassis_family": "unknown",
                "lcv_generation": "unknown",
                "bucket": "unknown",
                "applicable": "unknown",
                "eqhit_source": "part_search_across_catalogues",
                "status": "partial",
                "notes": f"total={total}; no edition rows harvested",
            }
        )
    return out


def append_only(new_rows: list[dict], *, by_catalog: bool = True) -> tuple[int, int]:
    """APPEND-ONLY. Never truncates.

    by_catalog=True (default): append rows whose (pn, catalog_id) is not yet present.
    by_catalog=False: skip entire PNs already present (legacy new-seed mode).
    """
    have_pn = existing_pns()
    have_cat = existing_catalog_keys() if by_catalog else set()
    to_add: list[dict] = []
    skipped = 0
    for r in new_rows:
        pn = r["part_number"]
        if not by_catalog:
            if pn in have_pn:
                skipped += 1
                continue
        else:
            notes = r.get("notes") or ""
            m = re.search(r"catalog_id=([^;]+)", notes)
            cid = m.group(1).strip() if m else ""
            # zero-hit / error rows: only add if PN has no rows yet
            if not cid:
                if pn in have_pn:
                    skipped += 1
                    continue
            elif (pn, cid) in have_cat:
                skipped += 1
                continue
        to_add.append(r)
        if by_catalog and cid:
            have_cat.add((pn, cid))
        have_pn.add(pn)
    if not to_add:
        print(f"appended_rows=0 skipped={skipped} unique_pns={len(existing_pns())}")
        return 0, len(existing_pns())
    write_header = not OUT.exists() or OUT.stat().st_size == 0
    with OUT.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        for r in to_add:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    after = existing_pns()
    print(f"appended_rows={len(to_add)} skipped_dup={skipped} unique_pns={len(after)}")
    return len(to_add), len(after)


def main() -> None:
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    cat = sys.argv[2] if len(sys.argv) > 2 else ""
    desc = sys.argv[3] if len(sys.argv) > 3 else ""
    if isinstance(raw, list):
        scrapes = raw
    else:
        scrapes = [raw]
    rows: list[dict] = []
    for s in scrapes:
        c = cat or s.get("pms_category") or ""
        rows.extend(rows_from_scrape(s, c, desc))
    append_only(rows)


if __name__ == "__main__":
    main()
