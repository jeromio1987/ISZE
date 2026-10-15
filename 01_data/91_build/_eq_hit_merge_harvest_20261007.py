"""Merge harvested EQ hits into results CSV/JSON. Evidence only."""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
STAMP = "20261007"
QUEUE = DER / f"_eq_hit_queue_{STAMP}.json"
HARVEST = DER / f"_eq_hit_harvest_raw_{STAMP}.json"
RESULTS_CSV = DER / f"_eq_hit_results_{STAMP}.csv"
RESULTS_JSON = DER / f"_eq_hit_results_{STAMP}.json"
RESULTS_JSONL = DER / f"_eq_hit_results_{STAMP}.jsonl"

FIELDS = [
    "pn",
    "description_if_any",
    "eq_status",
    "eq_total",
    "eq_fig_name",
    "eq_part_name",
    "eq_catalog",
    "vehicle_fig_notes",
    "suggested_aim_l1",
    "suggested_aim_l2",
    "suggested_aim_l3",
    "source_queue",
    "pn_variant_tried",
    "looked_up_at",
    "error",
]


def fig_to_aim(fig: str, part: str) -> tuple[str, str, str]:
    t = f"{fig} {part}".upper()
    rules = [
        (("AIR CLEANER", "AIR FILTER", "ACL"), ("Filters", "Engine air filtration", "Air cleaner")),
        (("OIL FILTER",), ("Filters", "Engine oil filtration", "Oil filter")),
        (("FUEL FILTER",), ("Filters", "Fuel filtration", "Fuel filter")),
        (("CLUTCH", "SLAVE"), ("Powertrain", "Clutch", "Clutch parts")),
        (("BRAKE", "CALIPER", "PAD", "SHOE"), ("Chassis", "Brakes", "Brake parts")),
        (("STEERING",), ("Chassis", "Steering", "Steering parts")),
        (("SUSPENSION", "LEAF", "SPRING"), ("Chassis", "Suspension", "Suspension parts")),
        (("AXLE", "DIFF", "FINAL DRIVE"), ("Chassis", "Axle", "Axle parts")),
        (("BUMPER",), ("Body", "Bumper", "Bumper")),
        (("RADIATOR", "COOLING", "INTERCOOLER"), ("Powertrain", "Cooling", "Cooling parts")),
        (("TURBO",), ("Powertrain", "Turbo", "Turbo parts")),
        (("GASKET", "SEAL", "OIL SEAL"), ("Powertrain", "Gaskets / seals", "Gasket / seal")),
        (("HARNESS", "WIRE"), ("Electrical", "Wiring", "Harness")),
        (("INJECT", "COMMON RAIL", "FUEL"), ("Powertrain", "Fuel system", "Fuel system parts")),
        (("EXHAUST", "SCR", "DPF", "DPD", "MUFFLER", "SILENCER"), ("Powertrain", "Exhaust / aftertreatment", "Exhaust parts")),
        (("DOOR", "GLASS", "REGULATOR"), ("Body", "Door / glass", "Door parts")),
        (("CAMERA",), ("Electrical", "Sensors / cameras", "Camera")),
        (("SEAT",), ("Body", "Interior", "Seat parts")),
        (("STARTER",), ("Electrical", "Starting / charging", "Starter")),
        (("ALTERNATOR",), ("Electrical", "Starting / charging", "Alternator")),
        (("BATTERY",), ("Electrical", "Battery", "Battery")),
        (("HOSE", "PIPE"), ("Powertrain", "Pipes / hoses", "Pipe / hose")),
        (("SENSOR",), ("Electrical", "Sensors", "Sensor")),
        (("TRANSMISSION", "GEARBOX", "SHIFT"), ("Powertrain", "Transmission", "Transmission parts")),
        (("ENGINE", "CYLINDER", "PISTON", "VALVE"), ("Powertrain", "Engine", "Engine parts")),
    ]
    for keys, aim in rules:
        if any(k in t for k in keys):
            return aim
    return ("", "", "")


def map_status(raw: str, total, fig: str = "", part: str = "") -> str:
    if raw in ("NOT_FOUND", "NO_HIT") or total == 0:
        return "NO_HIT"
    if raw == "AMBIGUOUS":
        return "AMBIGUOUS"
    if raw in ("FOUND", "HIT"):
        # status-only (catalog/total, no fig yet) still counts as HIT for existence
        return "HIT"
    if raw == "ERROR" or not raw:
        return "ERROR"
    return "ERROR"


def enrich(hit: dict, meta: dict) -> dict:
    fig = hit.get("eq_fig_name") or ""
    part = hit.get("eq_part_name") or ""
    status = map_status(hit.get("eq_status") or "", hit.get("eq_total"), fig, part)
    if hit.get("error") and status not in ("HIT", "NO_HIT", "AMBIGUOUS"):
        status = "ERROR"
    cat = hit.get("eq_catalog") or ""
    l1 = l2 = l3 = ""
    if status == "HIT":
        l1, l2, l3 = fig_to_aim(fig, part)
    notes = "; ".join(x for x in [fig, part, cat] if x)
    return {
        "pn": meta["pn"],
        "description_if_any": meta.get("description") or "",
        "eq_status": status,
        "eq_total": hit.get("eq_total", ""),
        "eq_fig_name": fig,
        "eq_part_name": part,
        "eq_catalog": cat,
        "vehicle_fig_notes": notes,
        "suggested_aim_l1": l1,
        "suggested_aim_l2": l2,
        "suggested_aim_l3": l3,
        "source_queue": meta.get("source_queue") or "",
        "pn_variant_tried": hit.get("pn") or meta["pn"],
        "looked_up_at": datetime.now(timezone.utc).isoformat(),
        "error": hit.get("error") or "",
    }


def load_done() -> dict[str, dict]:
    by: dict[str, dict] = {}
    if RESULTS_JSONL.exists():
        for line in RESULTS_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                by[r["pn"]] = r
            except Exception:
                pass
    return by


def write_summary(payload: dict, rows: list[dict], stopped: str) -> None:
    by_q = {}
    for qname in ("live_order", "billed_residual", "sample"):
        subset = [r for r in rows if r.get("source_queue") == qname]
        planned = payload.get(f"n_{qname}", 0)
        by_q[qname] = {
            "planned": planned,
            "attempted": len(subset),
            "hit": sum(1 for r in subset if r["eq_status"] == "HIT"),
            "no_hit": sum(1 for r in subset if r["eq_status"] == "NO_HIT"),
            "ambiguous": sum(1 for r in subset if r["eq_status"] == "AMBIGUOUS"),
            "error": sum(1 for r in subset if r["eq_status"] == "ERROR"),
            "progress_pct": round(100.0 * len(subset) / planned, 1) if planned else 0.0,
        }
    summary = {
        "as_of": STAMP,
        "source": "https://isuzu.snaponepc.com/epc/#/",
        "stopped": stopped,
        "attempted": len(rows),
        "hit": sum(1 for r in rows if r["eq_status"] == "HIT"),
        "no_hit": sum(1 for r in rows if r["eq_status"] == "NO_HIT"),
        "ambiguous": sum(1 for r in rows if r["eq_status"] == "AMBIGUOUS"),
        "errors": sum(1 for r in rows if r["eq_status"] == "ERROR"),
        "by_queue": by_q,
        "results_csv": str(RESULTS_CSV),
        "queue_json": str(QUEUE),
        "note": "Evidence only. No aim_master_v2 write. No classification release apply.",
    }
    RESULTS_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> int:
    stopped = sys.argv[1] if len(sys.argv) > 1 else "in_progress"
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    meta = {r["pn"]: r for r in payload["queue"]}
    hits = json.loads(HARVEST.read_text(encoding="utf-8"))
    if not isinstance(hits, list):
        print("harvest not a list", type(hits))
        return 2

    existing = load_done()
    new_rows = []
    for hit in hits:
        pn = str(hit.get("pn") or "")
        m = meta.get(pn)
        if m is None:
            # try match any queue pn that equals tried variant
            for orig, mm in meta.items():
                if pn == orig or pn.lstrip("0") == orig.lstrip("0"):
                    m = mm
                    break
        if m is None:
            m = {"pn": pn, "description": "", "source_queue": "unknown"}
        # keep first success; overwrite ERROR with later HIT
        prev = existing.get(m["pn"])
        row = enrich(hit, m)
        if prev and prev.get("eq_status") == "HIT" and row["eq_status"] != "HIT":
            continue
        existing[m["pn"]] = row
        new_rows.append(row)

    # rewrite jsonl + csv from existing dict in queue order
    ordered = []
    seen = set()
    for r in payload["queue"]:
        if r["pn"] in existing and r["pn"] not in seen:
            ordered.append(existing[r["pn"]])
            seen.add(r["pn"])
    for pn, row in existing.items():
        if pn not in seen:
            ordered.append(row)

    with RESULTS_JSONL.open("w", encoding="utf-8") as f:
        for r in ordered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with RESULTS_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in ordered:
            w.writerow(r)

    write_summary(payload, ordered, stopped)
    print(f"merged hits={len(hits)} rows={len(ordered)} newish={len(new_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
