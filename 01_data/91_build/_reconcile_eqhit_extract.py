"""One-shot reconcile: merge live EQ-HIT cache into playbook-schema extract CSV.

Prefer richer fitment rows. Dedupe by part_number + vehicle_model + catalog_id.
Do not wipe existing rows. Does not call browser.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "01_data" / "00_derived"
OUT = DERIVED / "eqhit_extract_priority_cy2025.csv"
LIVE = DERIVED / "_eqhit_live_results.json"
TOP = DERIVED / "eqhit_priority_top_pns_cy2025.csv"

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
    "clutch_disc": "1",
    "brake_shoe": "2",
    "brake_pad": "3",
    "clutch_pressure_plate": "4",
    "blower_filter": "5",
    "brake_rotor": "6",
    "fuel_filter": "7",
}

CATALOG_RE = re.compile(r"catalog_id=(\d+)")


def load_desc_cat() -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    if not TOP.exists():
        return out
    with TOP.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            pn = (r.get("part_number") or "").strip()
            if pn:
                out[pn] = (
                    (r.get("description") or "").strip(),
                    (r.get("pms_category") or "").strip(),
                )
    return out


def infer_chassis_bucket(vehicle: str, family: str) -> tuple[str, str, str]:
    t = f"{vehicle} {family}".upper()
    if any(x in t for x in ("TFR", "TFS", "D-MAX", "DMAX", "PICK UP", "PICKUP", "SUV")):
        return "TFR/TFS", "unknown", "lcv"
    if any(x in t for x in ("NJR", "NKR", "NLR", "NMR", "NNR", "NPR", "NQR", "NPS", "ELF", "TRUCKS N")):
        return "N-series", "unknown", "cv_std"
    if "BUS" in t or "LR" == family.upper():
        return "BUS", "unknown", "cv_std"
    if family:
        return "unknown", "unknown", "unknown"
    return "unknown", "unknown", "unknown"


def dedupe_key(r: dict) -> tuple[str, str, str]:
    notes = r.get("notes") or ""
    m = CATALOG_RE.search(notes)
    cat_id = m.group(1) if m else ""
    veh = (r.get("vehicle_model") or "").strip()
    pn = (r.get("part_number") or "").strip()
    return (pn, cat_id or veh, veh if cat_id else "")


def richness(r: dict) -> int:
    score = 0
    if (r.get("vehicle_model") or "").strip():
        score += 10
    if CATALOG_RE.search(r.get("notes") or ""):
        score += 5
    if (r.get("description") or "").strip():
        score += 1
    if (r.get("chassis_family") or "") not in ("", "unknown"):
        score += 1
    if (r.get("bucket") or "") not in ("", "unknown"):
        score += 1
    if (r.get("status") or "") == "ok":
        score += 2
    return score


def expand_live(item: dict, desc_cat: dict[str, tuple[str, str]]) -> list[dict]:
    pn = str(item.get("pn") or "").strip()
    if not pn:
        return []
    desc, cat = desc_cat.get(pn, ("", ""))
    if not cat:
        cat = "clutch_disc"  # live cache is clutch/brake session; fallback
    rank = RANK.get(cat, "")
    total = item.get("total")
    by_fam = item.get("byFamily") or {}
    rows: list[dict] = []

    if item.get("found") is False and (total == 0 or not by_fam):
        return [
            {
                "pull_date": "2026-09-05",
                "rank": rank,
                "pms_category": cat,
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
                "notes": "EQ-HIT global search Total Results: 0; reconciled_from=_eqhit_live_results.json",
            }
        ]

    harvested = 0
    for family, editions in by_fam.items():
        for ed in editions:
            veh = (ed.get("text") or "").strip()
            cat_id = str(ed.get("id") or "").strip()
            chassis, gen, bucket = infer_chassis_bucket(veh, family)
            harvested += 1
            rows.append(
                {
                    "pull_date": "2026-09-05",
                    "rank": rank,
                    "pms_category": cat,
                    "part_number": pn,
                    "description": desc,
                    "vehicle_model": veh,
                    "engine_code": "",
                    "chassis_family": chassis,
                    "lcv_generation": gen,
                    "bucket": bucket,
                    "applicable": "true",
                    "eqhit_source": "part_search_across_catalogues",
                    "status": "ok" if (total and harvested >= int(total)) else "partial",
                    "notes": (
                        f"catalog_id={cat_id}; parent={family}; "
                        f"total_results={total}; harvested_live={len(editions)}; "
                        f"reconciled_from=_eqhit_live_results.json"
                    ),
                }
            )

    # fix status once we know harvested vs total
    if total is not None:
        for r in rows:
            r["status"] = "ok" if harvested >= int(total) else "partial"
            # refresh harvested count in notes
            r["notes"] = re.sub(
                r"harvested_live=\d+",
                f"harvested_live={harvested}",
                r["notes"],
            )
    return rows


def main() -> None:
    desc_cat = load_desc_cat()
    existing: list[dict] = []
    if OUT.exists():
        with OUT.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames or []
            # If old collapsed schema, convert to playbook schema stubs
            if cols and "vehicle_models_generations" in cols and "vehicle_model" not in cols:
                for r in reader:
                    pn = (r.get("part_number") or "").strip()
                    cat = (r.get("pms_category") or "").strip()
                    desc = desc_cat.get(pn, ("", ""))[0]
                    models = (r.get("vehicle_models_generations") or "").strip()
                    notes = (r.get("notes") or "").strip()
                    if not models:
                        existing.append(
                            {
                                "pull_date": "2026-09-05",
                                "rank": RANK.get(cat, ""),
                                "pms_category": cat,
                                "part_number": pn,
                                "description": desc,
                                "vehicle_model": "",
                                "engine_code": (r.get("engine") or ""),
                                "chassis_family": "unknown",
                                "lcv_generation": "unknown",
                                "bucket": "unknown",
                                "applicable": "false" if "total=0" in notes else "true",
                                "eqhit_source": (r.get("source") or "EQ-HIT"),
                                "status": "partial",
                                "notes": notes or "migrated_from_collapsed_schema",
                            }
                        )
                    else:
                        # keep one partial summary row; live expand will add fitment
                        existing.append(
                            {
                                "pull_date": "2026-09-05",
                                "rank": RANK.get(cat, ""),
                                "pms_category": cat,
                                "part_number": pn,
                                "description": desc,
                                "vehicle_model": models[:500],
                                "engine_code": (r.get("engine") or ""),
                                "chassis_family": "unknown",
                                "lcv_generation": "unknown",
                                "bucket": "unknown",
                                "applicable": "true",
                                "eqhit_source": (r.get("source") or "EQ-HIT"),
                                "status": "partial",
                                "notes": (notes + "; migrated_collapsed_summary").strip("; "),
                            }
                        )
            else:
                for r in reader:
                    existing.append({k: (r.get(k) or "") for k in FIELDS})

    live_items = []
    if LIVE.exists():
        raw = json.loads(LIVE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = [raw]
        live_items = [x for x in raw if isinstance(x, dict) and x.get("pn")]

    merged: dict[tuple[str, str, str], dict] = {}
    for r in existing:
        k = dedupe_key(r)
        if k not in merged or richness(r) > richness(merged[k]):
            merged[k] = r

    added = 0
    for item in live_items:
        for r in expand_live(item, desc_cat):
            k = dedupe_key(r)
            if k not in merged:
                merged[k] = r
                added += 1
            elif richness(r) > richness(merged[k]):
                merged[k] = r

    # Drop collapsed summary-only rows when richer catalog rows exist for same PN
    by_pn: dict[str, list[tuple[tuple[str, str, str], dict]]] = defaultdict(list)
    for k, r in merged.items():
        by_pn[r["part_number"]].append((k, r))

    drop: set[tuple[str, str, str]] = set()
    for pn, items in by_pn.items():
        rich = [
            (k, r)
            for k, r in items
            if CATALOG_RE.search(r.get("notes") or "") and (r.get("vehicle_model") or "").strip()
        ]
        if not rich:
            continue
        for k, r in items:
            notes = r.get("notes") or ""
            veh = (r.get("vehicle_model") or "")
            # collapsed migration summaries are long blobs with " | " or "PASSENGER VEHICLE"
            if "migrated_collapsed" in notes or (" | " in veh and not CATALOG_RE.search(notes)):
                drop.add(k)

    for k in drop:
        merged.pop(k, None)

    rows = sorted(
        merged.values(),
        key=lambda r: (
            int(r.get("rank") or 99),
            r.get("pms_category") or "",
            r.get("part_number") or "",
            r.get("vehicle_model") or "",
        ),
    )

    # backup before write
    if OUT.exists():
        bak = OUT.with_suffix(".csv.bak_pre_reconcile")
        if not bak.exists():
            bak.write_bytes(OUT.read_bytes())

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    pns = sorted({r["part_number"] for r in rows})
    cats = Counter(r["pms_category"] for r in rows)
    pn_rows = Counter(r["part_number"] for r in rows)
    print("rows", len(rows))
    print("unique_pns", len(pns))
    print("pns", pns)
    print("cats", dict(cats))
    print("added_from_live", added)
    print("dropped_collapsed", len(drop))
    for pn in pns:
        print(f"  {pn}: {pn_rows[pn]}")


if __name__ == "__main__":
    main()
