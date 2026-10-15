"""Resume EQ-Hit 20261007 — append-only. Evidence only; no AIM apply."""
from __future__ import annotations

import base64
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build")
REL = DER / "_releases"
STAMP = "20261007"
QUEUE = DER / f"_eq_hit_queue_{STAMP}.json"
RESULTS_CSV = DER / f"_eq_hit_results_{STAMP}.csv"
RESULTS_JSON = DER / f"_eq_hit_results_{STAMP}.json"
RESULTS_JSONL = DER / f"_eq_hit_results_{STAMP}.jsonl"
SCRAPER_STATUS = BUILD / "eq_inject_tmp" / "decoded_scraper_status_20261007.js"
SCRAPER_FAST = BUILD / "eq_inject_tmp" / "decoded_scraper_fast_20261007.js"
PROPOSAL = REL / "next_release_proposal_eq_hit_live_order_2026-10-07.csv"

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
        (("BRAKE", "CALIPER", "PAD", "SHOE", "ANTI LOCK"), ("Chassis", "Brakes", "Brake parts")),
        (("STEERING",), ("Chassis", "Steering", "Steering parts")),
        (("SUSPENSION", "LEAF", "SPRING"), ("Chassis", "Suspension", "Suspension parts")),
        (("AXLE", "DIFF", "FINAL DRIVE", "PROP"), ("Chassis", "Axle", "Axle parts")),
        (("BUMPER",), ("Body", "Bumper", "Bumper")),
        (("RADIATOR", "COOLING", "INTERCOOLER", "THERMOSTAT"), ("Powertrain", "Cooling", "Cooling parts")),
        (("TURBO",), ("Powertrain", "Turbo", "Turbo parts")),
        (("GASKET", "SEAL", "OIL SEAL"), ("Powertrain", "Gaskets / seals", "Gasket / seal")),
        (("HARNESS", "WIRE", "CONNECTOR", "CABLE"), ("Electrical", "Wiring", "Harness")),
        (("INJECT", "COMMON RAIL", "FUEL", "NOZZLE", "FEED PUMP"), ("Powertrain", "Fuel system", "Fuel system parts")),
        (("EXHAUST", "SCR", "DPF", "DPD", "MUFFLER", "SILENCER", "EGR", "DEF ", "EMISSION"), ("Powertrain", "Exhaust / aftertreatment", "Exhaust parts")),
        (("DOOR", "GLASS", "REGULATOR", "LOCK"), ("Body", "Door / glass", "Door parts")),
        (("CAMERA", "METER", "SENSOR", "DISPLAY"), ("Electrical", "Sensors / instruments", "Sensor / meter")),
        (("SEAT", "BELT", "SUN VISOR", "MAT", "CARPET", "LINING", "TRIM"), ("Body", "Interior", "Interior parts")),
        (("STARTER",), ("Electrical", "Starting / charging", "Starter")),
        (("ALTERNATOR",), ("Electrical", "Starting / charging", "Alternator")),
        (("BATTERY",), ("Electrical", "Battery", "Battery")),
        (("HOSE", "PIPE", "DUCT"), ("Powertrain", "Pipes / hoses", "Pipe / hose")),
        (("TRANSMISSION", "GEARBOX", "SHIFT"), ("Powertrain", "Transmission", "Transmission parts")),
        (("ENGINE", "CYLINDER", "PISTON", "VALVE", "CAMSHAFT", "OIL PAN", "MANIFOLD"), ("Powertrain", "Engine", "Engine parts")),
        (("MIRROR", "GRILLE", "HANDLE", "TAIL GATE", "BODY"), ("Body", "Body exterior", "Body parts")),
        (("HEATER", "A/C", "AIR CONDITION"), ("Comfort", "HVAC", "Heater / A/C")),
        (("RADIO", "ANTENNA", "TV"), ("Electrical", "Audio / entertainment", "Audio parts")),
    ]
    for keys, aim in rules:
        if any(k in t for k in keys):
            return aim
    return ("", "", "")


def map_status(raw: str, total) -> str:
    if raw in ("NOT_FOUND", "NO_HIT") or total == 0:
        return "NO_HIT"
    if raw in ("FOUND", "HIT"):
        return "HIT"
    if raw == "AMBIGUOUS":
        return "AMBIGUOUS"
    if raw == "ERROR" or not raw:
        return "ERROR"
    return "ERROR"


def enrich(hit: dict, meta: dict) -> dict:
    fig = hit.get("eq_fig_name") or ""
    part = hit.get("eq_part_name") or ""
    status = map_status(hit.get("eq_status") or "", hit.get("eq_total"))
    if hit.get("error") and status not in ("HIT", "NO_HIT"):
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
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                by[r["pn"]] = r
            except Exception:
                pass
    if RESULTS_CSV.exists():
        with RESULTS_CSV.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("pn") and row["pn"] not in by:
                    by[row["pn"]] = row
    return by


def write_all(payload: dict, by: dict[str, dict], stopped: str) -> None:
    ordered = []
    seen = set()
    for r in payload["queue"]:
        if r["pn"] in by and r["pn"] not in seen:
            ordered.append(by[r["pn"]])
            seen.add(r["pn"])
    for pn, row in by.items():
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

    by_q = {}
    for qname in ("live_order", "billed_residual", "sample"):
        subset = [r for r in ordered if r.get("source_queue") == qname]
        planned = payload.get(f"n_{qname}", 0)
        by_q[qname] = {
            "planned": planned,
            "attempted": len(subset),
            "hit": sum(1 for r in subset if r.get("eq_status") == "HIT"),
            "no_hit": sum(1 for r in subset if r.get("eq_status") == "NO_HIT"),
            "ambiguous": sum(1 for r in subset if r.get("eq_status") == "AMBIGUOUS"),
            "error": sum(1 for r in subset if r.get("eq_status") == "ERROR"),
            "progress_pct": round(100.0 * len(subset) / planned, 1) if planned else 0.0,
        }
    with_fig = sum(1 for r in ordered if r.get("eq_fig_name"))
    with_aim = sum(1 for r in ordered if r.get("suggested_aim_l1"))
    summary = {
        "as_of": STAMP,
        "source": "https://isuzu.snaponepc.com/epc/#/",
        "stopped": stopped,
        "attempted": len(ordered),
        "hit": sum(1 for r in ordered if r.get("eq_status") == "HIT"),
        "no_hit": sum(1 for r in ordered if r.get("eq_status") == "NO_HIT"),
        "ambiguous": sum(1 for r in ordered if r.get("eq_status") == "AMBIGUOUS"),
        "errors": sum(1 for r in ordered if r.get("eq_status") == "ERROR"),
        "by_queue": by_q,
        "with_fig_detail": with_fig,
        "with_suggested_aim": with_aim,
        "results_csv": str(RESULTS_CSV),
        "queue_json": str(QUEUE),
        "proposal_csv": str(PROPOSAL),
        "note": "Evidence only. No aim_master_v2 write. No classification release apply.",
    }
    RESULTS_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def write_proposal(by: dict[str, dict]) -> int:
    REL.mkdir(parents=True, exist_ok=True)
    rows = []
    for pn, r in by.items():
        if r.get("eq_status") != "HIT":
            continue
        if not r.get("suggested_aim_l1"):
            continue
        # prefer live_order; include billed_residual if present
        conf = "high" if r.get("eq_fig_name") else "medium"
        if r.get("source_queue") == "sample":
            conf = "medium"
        path = " > ".join(
            x
            for x in [
                r.get("suggested_aim_l1") or "",
                r.get("suggested_aim_l2") or "",
                r.get("suggested_aim_l3") or "",
            ]
            if x
        )
        rows.append(
            {
                "pn": pn,
                "description_if_any": r.get("description_if_any") or "",
                "source_queue": r.get("source_queue") or "",
                "eq_status": r.get("eq_status") or "",
                "eq_total": r.get("eq_total") or "",
                "eq_fig_name": r.get("eq_fig_name") or "",
                "eq_part_name": r.get("eq_part_name") or "",
                "eq_catalog": r.get("eq_catalog") or "",
                "eq_notes": r.get("vehicle_fig_notes") or "",
                "proposed_aim_l1": r.get("suggested_aim_l1") or "",
                "proposed_aim_l2": r.get("suggested_aim_l2") or "",
                "proposed_aim_l3": r.get("suggested_aim_l3") or "",
                "proposed_aim_path": path,
                "confidence": conf,
                "apply": "NO",
            }
        )
    # live_order first, then billed, then sample
    order = {"live_order": 0, "billed_residual": 1, "sample": 2}
    rows.sort(key=lambda x: (order.get(x["source_queue"], 9), x["pn"]))
    fields = list(rows[0].keys()) if rows else [
        "pn",
        "description_if_any",
        "source_queue",
        "eq_status",
        "eq_notes",
        "proposed_aim_path",
        "confidence",
        "apply",
    ]
    with PROPOSAL.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("proposal_rows", len(rows), PROPOSAL)
    return len(rows)


def inject_expr(scraper_path: Path) -> str:
    src = scraper_path.read_text(encoding="utf-8")
    b64 = base64.b64encode(src.encode()).decode()
    return (
        "(function(){var s=atob("
        + json.dumps(b64)
        + "); var el=document.createElement('script'); el.textContent=s; "
        "document.documentElement.appendChild(el); return typeof window.__eqDoubtLookup;})()"
    )


def start_expr(pns: list[str], gap_ms: int = 400) -> str:
    arr = json.dumps(pns)
    return (
        "(function(){window.__EQ_DOUBT_OPEN_PNS="
        + arr
        + ";window.__eqDoubtResults=window.__eqDoubtResults||[];"
        "window.__eqDoubtResults.length=0;"
        f"window.__eqDoubtRun(window.__EQ_DOUBT_OPEN_PNS,{gap_ms});"
        f"return {{started:true,n:{len(pns)}}};"
        + "})()"
    )


def remain_lists(payload: dict, done: set[str]) -> dict[str, list[dict]]:
    out = {"live_order": [], "billed_residual": [], "sample": []}
    for r in payload["queue"]:
        if r["pn"] in done:
            continue
        q = r.get("source_queue") or "live_order"
        if q not in out:
            out[q] = []
        out[q].append(r)
    return out


def merge_hits(hits: list[dict], meta_map: dict[str, dict], by: dict[str, dict]) -> int:
    n = 0
    for hit in hits:
        pn_tried = str(hit.get("pn") or "")
        meta = meta_map.get(pn_tried)
        if meta is None:
            for orig, m in meta_map.items():
                if pn_tried == orig or pn_tried.lstrip("0") == orig.lstrip("0"):
                    meta = m
                    break
        if meta is None:
            meta = {"pn": pn_tried, "description": "", "source_queue": "unknown"}
        row = enrich(hit, meta)
        old = by.get(meta["pn"])
        # keep richer fig detail if status-only would overwrite
        if old and (old.get("eq_fig_name") or old.get("eq_part_name")) and not (
            row.get("eq_fig_name") or row.get("eq_part_name")
        ):
            continue
        by[meta["pn"]] = row
        n += 1
    return n


def write_helpers() -> None:
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    done = set(load_done())
    rem = remain_lists(payload, done)
    flat = rem["live_order"] + rem["billed_residual"] + rem["sample"]
    pns = [r["pn"] for r in flat]
    (DER / "_eq_hit_remain_pns_20261007.json").write_text(json.dumps(pns), encoding="utf-8")
    (DER / "_eq_hit_remain_meta_20261007.json").write_text(
        json.dumps({r["pn"]: r for r in flat}), encoding="utf-8"
    )
    # live_order status-only first
    lo = [r["pn"] for r in rem["live_order"]]
    (DER / "_eq_hit_inject_status_expr_20261007.js").write_text(
        inject_expr(SCRAPER_STATUS), encoding="utf-8"
    )
    (DER / "_eq_hit_inject_fast_expr_20261007.js").write_text(
        inject_expr(SCRAPER_FAST), encoding="utf-8"
    )
    (DER / "_eq_hit_start_live_remain_expr_20261007.js").write_text(
        start_expr(lo, 400), encoding="utf-8"
    )
    billed = [r["pn"] for r in rem["billed_residual"]]
    (DER / "_eq_hit_start_billed_expr_20261007.js").write_text(
        start_expr(billed, 700), encoding="utf-8"
    )
    sample = [r["pn"] for r in rem["sample"]]
    (DER / "_eq_hit_start_sample_expr_20261007.js").write_text(
        start_expr(sample, 700), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "done": len(done),
                "remain_live": len(lo),
                "remain_billed": len(billed),
                "remain_sample": len(sample),
                "remain_total": len(pns),
            }
        )
    )


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "prep"
    if cmd == "prep":
        write_helpers()
    elif cmd == "merge_harvest":
        harvest_path = Path(sys.argv[2])
        stopped = sys.argv[3] if len(sys.argv) > 3 else "in_progress"
        payload = json.loads(QUEUE.read_text(encoding="utf-8"))
        meta_map = {r["pn"]: r for r in payload["queue"]}
        by = load_done()
        hits = json.loads(harvest_path.read_text(encoding="utf-8"))
        n = merge_hits(hits, meta_map, by)
        write_all(payload, by, stopped)
        write_proposal(by)
        print("merged_newish", n)
    elif cmd == "proposal_only":
        by = load_done()
        write_proposal(by)
    else:
        raise SystemExit(f"unknown cmd {cmd}")
