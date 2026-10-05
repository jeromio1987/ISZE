"""Append EQ-Hit overnight hits into RESULTS csv/json. No AIM apply."""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
INBOX = ROOT / "01_data" / "90_INBOX"
STAMP = "20260919"
QUEUE = INBOX / f"_EQ_HIT_SESSION_{STAMP}_queue.json"
RESULTS_CSV = INBOX / f"_EQ_HIT_SESSION_{STAMP}_RESULTS.csv"
RESULTS_JSON = INBOX / f"_EQ_HIT_SESSION_{STAMP}_RESULTS.json"
RESULTS_JSONL = INBOX / f"_EQ_HIT_SESSION_{STAMP}_RESULTS.jsonl"
LOG = INBOX / f"_EQ_HIT_SESSION_{STAMP}_log.txt"
STATE = INBOX / f"_EQ_HIT_SESSION_{STAMP}_overnight_state.json"

FIELDS = [
    "pn", "eq_status", "eq_total", "eq_fig_name", "eq_part_name", "eq_catalog",
    "verdict", "proposed_l1", "proposed_l2", "proposed_l3", "notes", "looked_up_at",
    "rank", "billed_eur", "description", "queue_status", "session_view",
]


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def fig_to_aim(fig: str, part: str) -> tuple[str, str, str]:
    t = f"{fig} {part}".upper()
    rules = [
        (("SLAVE", "CLUTCH", "CLU"), ("Powertrain", "Clutch", "Slave cylinder")),
        (("CLUTCH",), ("Powertrain", "Clutch", "Clutch parts")),
        (("INJ", "COMMON RAIL", "C/R", "FUEL INJ"), ("Powertrain", "Fuel system", "Injection pipe / rail")),
        (("FUEL", "INJECTION"), ("Powertrain", "Fuel system", "Fuel system parts")),
        (("BRAKE", "CALIPER", "PAD"), ("Chassis", "Brakes", "Brake parts")),
        (("AIR CLEANER", "AIR FILTER"), ("Filters", "Engine air filtration", "Air cleaner element")),
        (("OIL FILTER",), ("Filters", "Engine oil filtration", "Oil filter")),
        (("STEERING",), ("Chassis", "Steering", "Steering parts")),
        (("SUSPENSION",), ("Chassis", "Suspension", "Suspension parts")),
        (("AXLE",), ("Chassis", "Axle", "Axle parts")),
        (("BUMPER",), ("Body", "Bumper", "Bumper")),
        (("RADIATOR", "COOLING"), ("Powertrain", "Cooling", "Cooling parts")),
        (("TURBO",), ("Powertrain", "Turbo", "Turbo parts")),
        (("GASKET",), ("Powertrain", "Gaskets / seals", "Gasket")),
        (("HARNESS", "WIRE"), ("Electrical", "Wiring", "Harness")),
        (("PIPE", "HOSE"), ("Powertrain", "Pipes / hoses", "Pipe / hose")),
        (("BATTERY",), ("Repair parts", "Battery", "Battery")),
        (("STARTER",), ("Electrical", "Starting / charging", "Starter")),
        (("ALTERNATOR",), ("Electrical", "Starting / charging", "Alternator")),
    ]
    for keys, aim in rules:
        if any(k in t for k in keys):
            return aim
    return ("", "", "")


def enrich(hit: dict, qrow: dict, view_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    status = hit.get("eq_status") or ("ERROR" if hit.get("error") else "UNKNOWN")
    fig = hit.get("eq_fig_name") or ""
    part = hit.get("eq_part_name") or ""
    pl1 = qrow.get("proposed_aim_l1") or ""
    pl2 = qrow.get("proposed_aim_l2") or ""
    pl3 = qrow.get("proposed_aim_l3") or ""
    if status == "NOT_FOUND" or hit.get("eq_total") == 0:
        verdict, notes = "NO_EQ_HIT", hit.get("error") or "Total Results 0"
    elif status == "ERROR":
        verdict, notes = "NEEDS_HUMAN", hit.get("error") or "lookup error"
    elif status == "FOUND":
        fl1, fl2, fl3 = fig_to_aim(fig, part)
        if fl1:
            pl1, pl2, pl3 = fl1, fl2, fl3
            verdict, notes = "PROPOSE_PATCH", f"EQ FIG={fig}; leaf mapped from figure"
        elif pl1:
            verdict, notes = "PROPOSE_PATCH", f"EQ FIG={fig}; using queue proposal"
        else:
            verdict, notes = "NEEDS_HUMAN", f"EQ FIG={fig}; no safe leaf yet"
    else:
        verdict, notes = "NEEDS_HUMAN", str(hit.get("error") or status)
    return {
        "pn": hit.get("pn") or qrow.get("pn"),
        "eq_status": status,
        "eq_total": hit.get("eq_total", ""),
        "eq_fig_name": fig,
        "eq_part_name": part,
        "eq_catalog": hit.get("eq_catalog") or "",
        "verdict": verdict,
        "proposed_l1": pl1,
        "proposed_l2": pl2,
        "proposed_l3": pl3,
        "notes": notes,
        "looked_up_at": now,
        "rank": qrow.get("rank", ""),
        "billed_eur": qrow.get("billed_eur", ""),
        "description": qrow.get("description", ""),
        "queue_status": qrow.get("status", ""),
        "session_view": view_id,
    }


def main() -> int:
    payload = json.loads(sys.stdin.read() if len(sys.argv) < 2 else Path(sys.argv[1]).read_text(encoding="utf-8"))
    hits = payload.get("hits") if isinstance(payload, dict) else payload
    view_id = payload.get("view_id", "") if isinstance(payload, dict) else ""
    if not isinstance(hits, list):
        print("bad payload", file=sys.stderr)
        return 2

    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    by_pn = {r["pn"]: r for r in q["rows"]}
    done = set()
    if RESULTS_JSONL.exists():
        for line in RESULTS_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["pn"])

    new_rows = []
    for h in hits:
        pn = h.get("pn")
        if not pn or pn in done:
            continue
        new_rows.append(enrich(h, by_pn.get(pn, {"pn": pn}), view_id))
        done.add(pn)

    if new_rows:
        write_header = not RESULTS_CSV.exists()
        with RESULTS_CSV.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            if write_header:
                w.writeheader()
            for r in new_rows:
                w.writerow(r)
        with RESULTS_JSONL.open("a", encoding="utf-8") as f:
            for r in new_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # rebuild summary
    all_rows = []
    if RESULTS_JSONL.exists():
        for line in RESULTS_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                all_rows.append(json.loads(line))
    by = {r["pn"]: r for r in all_rows}
    ordered = sorted(by.values(), key=lambda r: (r.get("rank") if r.get("rank") != "" else 10**9, r["pn"]))
    summary = {
        "session": f"EQ_HIT_SESSION_{STAMP}",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "aim_apply": False,
        "n_looked_up": len(ordered),
        "n_found": sum(1 for r in ordered if r.get("eq_status") == "FOUND"),
        "n_not_found": sum(1 for r in ordered if r.get("eq_status") == "NOT_FOUND"),
        "n_error": sum(1 for r in ordered if r.get("eq_status") == "ERROR"),
        "by_verdict": {},
        "rows": ordered,
    }
    for r in ordered:
        v = r.get("verdict") or "?"
        summary["by_verdict"][v] = summary["by_verdict"].get(v, 0) + 1
    RESULTS_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    STATE.write_text(
        json.dumps(
            {
                "status": "RUNNING",
                "at": datetime.now().isoformat(),
                "n_looked_up": summary["n_looked_up"],
                "n_found": summary["n_found"],
                "n_not_found": summary["n_not_found"],
                "by_verdict": summary["by_verdict"],
                "open_remaining": len(q["rows"]) - summary["n_looked_up"],
                "aim_apply": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log(f"harvest +{len(new_rows)} total={summary['n_looked_up']} FOUND={summary['n_found']} NOT_FOUND={summary['n_not_found']} {summary['by_verdict']}")
    print(json.dumps({"added": len(new_rows), "total": summary["n_looked_up"], "by_verdict": summary["by_verdict"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
