"""EQ-Hit evidence session 2026-10-07 — one Snap-on tab, no AIM apply.

Uses cursor glass-browser view via cdp_eval.js (same session MCP locked).
Writes RESULTS csv/json under 01_data/00_derived/.
"""
from __future__ import annotations

import base64
import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
BUILD = ISZE / "01_data" / "91_build"
STAMP = "20261007"
VIEW_ID = "glass-browser-be21a977-deb6-47a7-b500-bf6871c58a71"
CDP = BUILD / "epc_batch2" / "cdp_eval.js"
SCRAPER = BUILD / "eq_inject_tmp" / "decoded_scraper.js"
QUEUE = DER / f"_eq_hit_queue_{STAMP}.json"
RESULTS_CSV = DER / f"_eq_hit_results_{STAMP}.csv"
RESULTS_JSON = DER / f"_eq_hit_results_{STAMP}.json"
RESULTS_JSONL = DER / f"_eq_hit_results_{STAMP}.jsonl"
STATE = DER / f"_eq_hit_state_{STAMP}.json"
LOG = DER / f"_eq_hit_session_{STAMP}.log"

GAP_MS = 1800
BATCH = 40  # in-page batch size via __eqDoubtRun
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


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def cdp(expr: str, await_promise: bool = False, timeout_s: int = 120) -> object:
    cmd = [
        "node",
        str(CDP),
        VIEW_ID,
        expr,
        "1" if await_promise else "0",
        str(timeout_s),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if r.returncode != 0:
        raise RuntimeError(f"cdp rc={r.returncode} err={err[:400]} out={out[:400]}")
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def js_string(s: str) -> str:
    return json.dumps(s)


def inject_scraper() -> None:
    src = SCRAPER.read_text(encoding="utf-8")
    b64 = base64.b64encode(src.encode("utf-8")).decode("ascii")
    loader = (
        "(function(){"
        f"var s=atob({js_string(b64)});"
        "var el=document.createElement('script');"
        "el.textContent=s;"
        "document.documentElement.appendChild(el);"
        "return typeof window.__eqDoubtLookup;"
        "})()"
    )
    got = cdp(loader, timeout_s=60)
    if got != "function":
        raise RuntimeError(f"scraper inject failed: {got}")
    log("scraper injected")


def login_wall() -> bool:
    got = cdp(
        "(function(){return !!document.querySelector('input[placeholder=Username]') "
        "|| !!document.querySelector('input[type=password]');})()"
    )
    return bool(got)


def session_ok() -> bool:
    got = cdp(
        "(function(){"
        "var inp=document.querySelector('input[placeholder=\"Part Number\"]');"
        "var logout=[...document.querySelectorAll('*')].some(e=>(e.textContent||'').trim()==='Logout');"
        "return {hasPn:!!inp, logout:logout, href:location.href};"
        "})()"
    )
    if not isinstance(got, dict):
        return False
    return bool(got.get("hasPn")) and "snaponepc" in str(got.get("href") or "")


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
        (("EXHAUST", "SCR", "DPF", "DPD", "MUFFLER"), ("Powertrain", "Exhaust / aftertreatment", "Exhaust parts")),
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


def map_status(raw: str, total: object) -> str:
    if raw in ("FOUND", "HIT"):
        return "HIT"
    if raw in ("NOT_FOUND", "NO_HIT"):
        return "NO_HIT"
    if raw == "AMBIGUOUS":
        return "AMBIGUOUS"
    if raw == "ERROR" or not raw:
        return "ERROR"
    if total == 0:
        return "NO_HIT"
    return raw


def variants(pn: str) -> list[str]:
    pn = str(pn).strip()
    out = [pn]
    if pn.isdigit():
        stripped = pn.lstrip("0") or "0"
        if stripped != pn:
            out.append(stripped)
        # pad to 10 if short
        if len(pn) < 10:
            padded = pn.zfill(10)
            if padded not in out:
                out.append(padded)
    return out


def enrich(hit: dict, meta: dict) -> dict:
    status = map_status(hit.get("eq_status") or "", hit.get("eq_total"))
    if hit.get("error") and status != "HIT":
        status = "ERROR" if status != "NO_HIT" else status
    fig = hit.get("eq_fig_name") or ""
    part = hit.get("eq_part_name") or ""
    cat = hit.get("eq_catalog") or ""
    l1, l2, l3 = ("", "", "")
    if status == "HIT":
        l1, l2, l3 = fig_to_aim(fig, part)
    notes = "; ".join(x for x in [fig, part, cat] if x)
    return {
        "pn": meta["pn"],
        "description_if_any": meta.get("description") or meta.get("description_if_any") or "",
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


def load_done() -> set[str]:
    done: set[str] = set()
    if RESULTS_JSONL.exists():
        for line in RESULTS_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["pn"])
            except Exception:
                pass
    if RESULTS_CSV.exists():
        with RESULTS_CSV.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("pn"):
                    done.add(row["pn"])
    return done


def append_results(rows: list[dict]) -> None:
    if not rows:
        return
    new_file = not RESULTS_CSV.exists()
    with RESULTS_CSV.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new_file:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    with RESULTS_JSONL.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_summary(queue_meta: dict, all_rows: list[dict], stopped: str) -> None:
    by_q: dict[str, dict] = {}
    for qname in ("live_order", "billed_residual", "sample"):
        subset = [r for r in all_rows if r.get("source_queue") == qname]
        planned = queue_meta.get(f"n_{qname}", 0)
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
        "view_id": VIEW_ID,
        "stopped": stopped,
        "attempted": len(all_rows),
        "hit": sum(1 for r in all_rows if r["eq_status"] == "HIT"),
        "no_hit": sum(1 for r in all_rows if r["eq_status"] == "NO_HIT"),
        "ambiguous": sum(1 for r in all_rows if r["eq_status"] == "AMBIGUOUS"),
        "errors": sum(1 for r in all_rows if r["eq_status"] == "ERROR"),
        "by_queue": by_q,
        "results_csv": str(RESULTS_CSV),
        "queue_json": str(QUEUE),
        "note": "Evidence only. No aim_master_v2 write. No classification release apply.",
    }
    RESULTS_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    STATE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log(f"summary attempted={summary['attempted']} hit={summary['hit']} no_hit={summary['no_hit']} err={summary['errors']} stopped={stopped}")


def lookup_one(pn: str) -> dict:
    expr = f"(async function(){{ return await window.__eqDoubtLookup({js_string(pn)}); }})()"
    got = cdp(expr, await_promise=True, timeout_s=45)
    if isinstance(got, dict):
        return got
    return {"pn": pn, "eq_status": "ERROR", "error": f"bad_return:{got}"}


def start_batch(pns: list[str]) -> None:
    arr = json.dumps(pns)
    expr = (
        "(function(){"
        f"window.__EQ_DOUBT_OPEN_PNS={arr};"
        "window.__eqDoubtResults=window.__eqDoubtResults||[];"
        "window.__eqDoubtResults.length=0;"
        f"window.__eqDoubtRun(window.__EQ_DOUBT_OPEN_PNS,{GAP_MS});"
        "return {started:true,n:" + str(len(pns)) + "};"
        "})()"
    )
    cdp(expr, timeout_s=30)


def poll_state() -> dict:
    got = cdp(
        "(function(){"
        "var s=window.__eqDoubtState||{};"
        "var r=window.__eqDoubtResults||[];"
        "return {"
        "running:!!s.running,"
        "done:s.done||0,"
        "total:s.total||0,"
        "n_results:r.length,"
        "last:s.last||null,"
        "login:!!document.querySelector('input[placeholder=Username]')"
        "};"
        "})()",
        timeout_s=30,
    )
    return got if isinstance(got, dict) else {"error": str(got)}


def harvest_results() -> list[dict]:
    got = cdp("JSON.stringify(window.__eqDoubtResults||[])", timeout_s=60)
    if isinstance(got, str):
        try:
            return json.loads(got)
        except json.JSONDecodeError:
            return []
    if isinstance(got, list):
        return got
    return []


def load_all_rows() -> list[dict]:
    rows: list[dict] = []
    if RESULTS_JSONL.exists():
        for line in RESULTS_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
        return rows
    if RESULTS_CSV.exists():
        with RESULTS_CSV.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    return rows


def meta_by_pn(queue: list[dict]) -> dict[str, dict]:
    return {r["pn"]: r for r in queue}


def process_hits(hits: list[dict], meta_map: dict[str, dict], done: set[str]) -> list[dict]:
    """Map batch hits to rows; retry NO_HIT with PN variants one-by-one."""
    out: list[dict] = []
    for hit in hits:
        pn_tried = str(hit.get("pn") or "")
        # find original meta: exact or strip-match
        meta = meta_map.get(pn_tried)
        if meta is None:
            for orig, m in meta_map.items():
                if pn_tried in variants(orig) or orig in variants(pn_tried):
                    meta = m
                    break
        if meta is None:
            meta = {"pn": pn_tried, "description": "", "source_queue": "unknown"}
        orig = meta["pn"]
        if orig in done:
            continue
        st = map_status(hit.get("eq_status") or "", hit.get("eq_total"))
        if st == "NO_HIT":
            for v in variants(orig):
                if v == pn_tried:
                    continue
                hit2 = lookup_one(v)
                st2 = map_status(hit2.get("eq_status") or "", hit2.get("eq_total"))
                if st2 == "HIT":
                    hit = hit2
                    break
                if st2 != "NO_HIT":
                    hit = hit2
                    break
        row = enrich(hit, meta)
        out.append(row)
        done.add(orig)
    return out


def main() -> int:
    if not QUEUE.exists():
        log(f"missing queue {QUEUE}")
        return 2
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    queue = payload["queue"]
    mmap = meta_by_pn(queue)
    log(
        f"queue unique={len(queue)} live={payload['n_live_order']} "
        f"billed={payload['n_billed_residual']} sample={payload['n_sample']}"
    )

    if login_wall():
        log("LOGIN_WALL — stop")
        write_summary(payload, load_all_rows(), "login_wall")
        return 3
    if not session_ok():
        log("SESSION_NOT_OK — stop")
        write_summary(payload, load_all_rows(), "session_dead")
        return 4

    inject_scraper()
    done = load_done()
    log(f"already done {len(done)}")

    pending = [r for r in queue if r["pn"] not in done]
    stopped = "completed"
    try:
        for bi in range(0, len(pending), BATCH):
            if login_wall():
                stopped = "login_wall"
                log(f"login wall before batch {bi}")
                break
            if not session_ok():
                stopped = "session_dead"
                log(f"session dead before batch {bi}")
                break

            chunk = pending[bi : bi + BATCH]
            pns = [r["pn"] for r in chunk]
            log(f"batch start i={bi} n={len(pns)} first={pns[0]}")
            start_batch(pns)

            # wait for in-page run (~gap * n + lookup time)
            deadline = time.time() + max(90, len(pns) * (GAP_MS / 1000.0 + 8))
            while time.time() < deadline:
                st = poll_state()
                if st.get("login"):
                    stopped = "login_wall"
                    log("login wall during batch")
                    break
                if st.get("error"):
                    log(f"poll error {st}")
                if not st.get("running") and int(st.get("n_results") or 0) >= len(pns):
                    break
                if not st.get("running") and int(st.get("done") or 0) >= len(pns):
                    break
                time.sleep(3)
            else:
                log("batch poll timeout — harvest what we have")

            if stopped == "login_wall":
                break

            hits = harvest_results()
            rows = process_hits(hits, mmap, done)
            append_results(rows)
            write_summary(payload, load_all_rows(), "in_progress")
            log(
                f"batch done i={bi} harvested={len(hits)} wrote={len(rows)} "
                f"cum={len(done)}/{len(queue)}"
            )
    except KeyboardInterrupt:
        stopped = "interrupted"
    except Exception as e:
        stopped = f"error:{e}"
        log(stopped)

    write_summary(payload, load_all_rows(), stopped)
    return 0 if stopped == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())

