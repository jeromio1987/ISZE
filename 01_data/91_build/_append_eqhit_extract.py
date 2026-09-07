"""Append EQ-HIT scrape JSON rows into extract CSV."""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\eqhit_extract_priority_cy2025.csv")
META = {
    "8982120690": "clutch_disc",
    "5876100771": "clutch_disc",
    "8982551391": "clutch_disc",
    "8981649171": "clutch_disc",
    "5876100920": "clutch_disc",
    "8978293170": "clutch_disc",
    "8973319320": "brake_shoe",
    "5878320440": "brake_shoe",
    "8982447940": "brake_pad",
    "8982169210": "brake_pad",
    "8982169220": "brake_pad",
    "8982831940": "clutch_pressure_plate",
    "8970388314": "clutch_pressure_plate",
    "5876100910": "clutch_pressure_plate",
    "5876101040": "clutch_pressure_plate",
    "8980400932": "clutch_pressure_plate",
    "8981596930": "fuel_filter",
    "5876150170": "fuel_filter",
    "8981941190": "fuel_filter",
    "8975425400": "fuel_filter",
    "5876101570": "fuel_filter",
    "8980374810": "fuel_filter",
    "1876102860": "fuel_filter",
    "5876150240": "fuel_filter",
}
FIELDS = [
    "part_number",
    "pms_category",
    "vehicle_models_generations",
    "engine",
    "notes",
    "source",
    "pulled_at",
]


def row_from_result(r: dict) -> dict:
    pn = str(r.get("pn") or "")
    cat = META.get(pn, "")
    pulled = datetime.now(timezone(timedelta(hours=2))).isoformat(timespec="seconds")
    if r.get("error"):
        return {
            "part_number": pn,
            "pms_category": cat,
            "vehicle_models_generations": "",
            "engine": "",
            "notes": f"error={r.get('error')}; got={r.get('got','')}",
            "source": "EQ-HIT",
            "pulled_at": pulled,
        }
    by_fam = r.get("byFamily") or {}
    chunks = []
    for fam, items in by_fam.items():
        texts = "; ".join(f"{it.get('id')} {it.get('text')}" for it in items[:40])
        chunks.append(f"{fam}: {texts}")
    models = " | ".join(chunks) if chunks else ""
    if r.get("found") is False and r.get("total") == 0:
        models = ""
        notes = "total=0; no global search results in EQ-HIT"
    else:
        notes = (
            f"total={r.get('total')}; editions={r.get('editions')}; "
            f"families={','.join(r.get('families') or [])}; found={r.get('found')}"
        )
    return {
        "part_number": pn,
        "pms_category": cat,
        "vehicle_models_generations": models,
        "engine": "",
        "notes": notes,
        "source": "EQ-HIT",
        "pulled_at": pulled,
    }


def clean_row(r: dict) -> dict:
    return {k: ("" if r.get(k) is None else r.get(k, "")) for k in FIELDS}


def upsert(rows: list[dict]) -> int:
    existing: dict[str, dict] = {}
    if OUT.exists():
        with OUT.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                pn = (r.get("part_number") or "").strip()
                if not pn:
                    continue
                existing[pn] = clean_row(r)
    for r in rows:
        existing[r["part_number"]] = clean_row(r)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for pn in sorted(existing):
            w.writerow(existing[pn])
    return len(existing)


def main() -> None:
    raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]
    rows = [row_from_result(r) for r in data if r.get("pn")]
    n = upsert(rows)
    print(f"upserted {len(rows)} -> {OUT} total_pns={n}")


if __name__ == "__main__":
    main()
