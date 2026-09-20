"""EQ-Hit overnight — 3 parallel Snap-on sessions. Results only; no AIM apply.

Uses the three logged-in Cursor browser viewIds. Writes inbox RESULTS.* only.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
INBOX = ROOT / "01_data" / "90_INBOX"
BUILD = ROOT / "01_data" / "91_build" / "epc_batch2"
STAMP = "20260919"

QUEUE = INBOX / f"_EQ_HIT_SESSION_{STAMP}_queue.json"
SCRAPER = INBOX / "_eq_hit_doubt_console_scraper_20260918.js"
CDP = BUILD / "cdp_eval.js"
RESULTS_CSV = INBOX / f"_EQ_HIT_SESSION_{STAMP}_RESULTS.csv"
RESULTS_JSON = INBOX / f"_EQ_HIT_SESSION_{STAMP}_RESULTS.json"
RESULTS_JSONL = INBOX / f"_EQ_HIT_SESSION_{STAMP}_RESULTS.jsonl"
LOG = INBOX / f"_EQ_HIT_SESSION_{STAMP}_log.txt"
STATE = INBOX / f"_EQ_HIT_SESSION_{STAMP}_overnight_state.json"

# Three logged-in EQ tabs (2026-09-19 evening). Login-wall tab excluded.
VIEW_IDS = [
    "glass-browser-0e130666-253b-4020-879e-7a5a0517b0e3",
    "glass-browser-e0d4a8d2-b3ab-4032-a5f6-51ace5b38115",
    "glass-browser-b9f05f9e-5c49-4dd1-b5f5-0efd2765f840",
]

GAP_MS = 2200
POLL_S = 20
RESULT_FIELDS = [
    "pn",
    "eq_status",
    "eq_total",
    "eq_fig_name",
    "eq_part_name",
    "eq_catalog",
    "verdict",
    "proposed_l1",
    "proposed_l2",
    "proposed_l3",
    "notes",
    "looked_up_at",
    "rank",
    "billed_eur",
    "description",
    "queue_status",
    "session_view",
]


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def cdp(view_id: str, expr: str, await_promise: bool = False, timeout_s: int = 120) -> object:
    cmd = [
        "node",
        str(CDP),
        view_id,
        expr,
        "1" if await_promise else "0",
        str(timeout_s),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if r.returncode != 0:
        raise RuntimeError(f"cdp fail view={view_id[:12]} rc={r.returncode} err={err[:300]} out={out[:300]}")
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def js_string(s: str) -> str:
    return json.dumps(s)


def inject_scraper(view_id: str) -> None:
    src = SCRAPER.read_text(encoding="utf-8")
    # Wrap as IIFE so paste-style top-level is fine inside evaluate
    expr = f"(function(){{ {src}\n return 'scraper_ok'; }})()"
    # Avoid giant argv issues on Windows: write temp and evaluate via Function from file content length check
    tmp = INBOX / f"_eq_scraper_inject_{view_id[-8:]}.js"
    tmp.write_text(expr, encoding="utf-8")
    # Load via reading file in node wrapper — pass path through a tiny eval that reads? cdp_eval takes expression.
    # Chunk: base64
    import base64

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
    got = cdp(view_id, loader, await_promise=False, timeout_s=60)
    if got != "function":
        raise RuntimeError(f"scraper inject failed on {view_id}: {got}")


def start_batch(view_id: str, pns: list[str], gap_ms: int = GAP_MS) -> None:
    arr = json.dumps(pns)
    expr = (
        "(function(){"
        f"window.__EQ_DOUBT_OPEN_PNS={arr};"
        "window.__eqDoubtResults=window.__eqDoubtResults||[];"
        "window.__eqDoubtResults.length=0;"
        f"window.__eqDoubtRun(window.__EQ_DOUBT_OPEN_PNS,{gap_ms});"
        "return {started:true,n:" + str(len(pns)) + "};"
        "})()"
    )
    cdp(view_id, expr, await_promise=False, timeout_s=30)


def poll_state(view_id: str) -> dict:
    expr = (
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
        "})()"
    )
    got = cdp(view_id, expr, await_promise=False, timeout_s=30)
    return got if isinstance(got, dict) else {"error": str(got)}


def harvest_results(view_id: str) -> list[dict]:
    expr = "JSON.stringify(window.__eqDoubtResults||[])"
    got = cdp(view_id, expr, await_promise=False, timeout_s=60)
    if isinstance(got, str):
        try:
            return json.loads(got)
        except json.JSONDecodeError:
            return []
    if isinstance(got, list):
        return got
    return []


def fig_to_aim(fig: str, part: str) -> tuple[str, str, str]:
    """Best-effort Axis A leaf from EQ FIG / part name. Empty = no safe leaf."""
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
    notes = ""
    if status == "NOT_FOUND" or hit.get("eq_total") == 0:
        verdict = "NO_EQ_HIT"
        notes = hit.get("error") or "Total Results 0"
    elif status == "ERROR":
        verdict = "NEEDS_HUMAN"
        notes = hit.get("error") or "lookup error"
    elif status == "FOUND":
        fl1, fl2, fl3 = fig_to_aim(fig, part)
        if fl1:
            pl1, pl2, pl3 = fl1, fl2, fl3
            verdict = "PROPOSE_PATCH"
            notes = f"EQ FIG={fig}; leaf mapped from figure"
        elif pl1:
            verdict = "PROPOSE_PATCH"
            notes = f"EQ FIG={fig}; using queue proposal"
        else:
            verdict = "NEEDS_HUMAN"
            notes = f"EQ FIG={fig}; no safe leaf yet"
    else:
        verdict = "NEEDS_HUMAN"
        notes = str(hit.get("error") or status)

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


def append_rows(rows: list[dict]) -> None:
    if not rows:
        return
    write_header = not RESULTS_CSV.exists()
    with RESULTS_CSV.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    with RESULTS_JSONL.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def rewrite_json_summary() -> dict:
    rows: list[dict] = []
    if RESULTS_JSONL.exists():
        for line in RESULTS_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    # de-dupe by pn keeping last
    by: dict[str, dict] = {}
    for r in rows:
        by[r["pn"]] = r
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
    return summary


def shard_pns(open_rows: list[dict], n: int) -> list[list[dict]]:
    shards: list[list[dict]] = [[] for _ in range(n)]
    for i, r in enumerate(open_rows):
        shards[i % n].append(r)
    return shards


def main() -> int:
    if not QUEUE.exists():
        log(f"MISSING queue {QUEUE}")
        return 2
    if not CDP.exists():
        log(f"MISSING cdp_eval {CDP}")
        return 2

    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    rows = q["rows"]
    by_pn = {r["pn"]: r for r in rows}
    done = load_done()
    open_rows = [r for r in rows if r["pn"] not in done]
    log(
        f"START overnight 3-session | queue={len(rows)} done={len(done)} open={len(open_rows)} "
        f"billed_open≈{sum(float(r.get('billed_eur') or 0) for r in open_rows):.0f}"
    )
    if not open_rows:
        summary = rewrite_json_summary()
        log(f"Queue exhausted. looked_up={summary['n_looked_up']} found={summary['n_found']}")
        STATE.write_text(json.dumps({"status": "COMPLETE", **{k: summary[k] for k in summary if k != 'rows'}}, indent=2), encoding="utf-8")
        return 0

    # Probe login wall
    live_views: list[str] = []
    for vid in VIEW_IDS:
        try:
            st = poll_state(vid)
            if st.get("login"):
                log(f"SKIP login wall {vid}")
                continue
            inject_scraper(vid)
            live_views.append(vid)
            log(f"READY session {vid}")
        except Exception as e:
            log(f"SKIP session {vid}: {e}")

    if not live_views:
        log("STOP — no live EQ sessions")
        STATE.write_text(json.dumps({"status": "NO_SESSION", "at": datetime.now().isoformat()}, indent=2), encoding="utf-8")
        return 3

    shards = shard_pns(open_rows, len(live_views))
    for vid, shard in zip(live_views, shards):
        pns = [r["pn"] for r in shard]
        log(f"START batch view={vid[-12:]} n={len(pns)} top={pns[:3]}")
        start_batch(vid, pns, GAP_MS)

    harvested: dict[str, set[str]] = {vid: set() for vid in live_views}
    idle_rounds = 0
    while True:
        time.sleep(POLL_S)
        any_running = False
        new_rows: list[dict] = []
        for vid in live_views:
            try:
                st = poll_state(vid)
            except Exception as e:
                log(f"poll error {vid[-12:]}: {e}")
                continue
            if st.get("login"):
                log(f"LOGIN WALL mid-run {vid[-12:]}")
                continue
            if st.get("running"):
                any_running = True
            log(
                f"progress {vid[-12:]} done={st.get('done')}/{st.get('total')} "
                f"results={st.get('n_results')} running={st.get('running')}"
            )
            try:
                hits = harvest_results(vid)
            except Exception as e:
                log(f"harvest error {vid[-12:]}: {e}")
                continue
            for h in hits:
                pn = h.get("pn")
                if not pn or pn in harvested[vid] or pn in done:
                    continue
                harvested[vid].add(pn)
                done.add(pn)
                new_rows.append(enrich(h, by_pn.get(pn, {"pn": pn}), vid))

        if new_rows:
            append_rows(new_rows)
            summary = rewrite_json_summary()
            idle_rounds = 0
            log(
                f"WROTE +{len(new_rows)} | total={summary['n_looked_up']} "
                f"FOUND={summary['n_found']} NOT_FOUND={summary['n_not_found']} "
                f"verdicts={summary['by_verdict']}"
            )
            STATE.write_text(
                json.dumps(
                    {
                        "status": "RUNNING" if any_running else "DRAINING",
                        "at": datetime.now().isoformat(),
                        "n_looked_up": summary["n_looked_up"],
                        "n_found": summary["n_found"],
                        "n_not_found": summary["n_not_found"],
                        "by_verdict": summary["by_verdict"],
                        "open_remaining": len(rows) - summary["n_looked_up"],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        else:
            idle_rounds += 1

        if not any_running:
            # final harvest
            time.sleep(2)
            final_new: list[dict] = []
            for vid in live_views:
                try:
                    for h in harvest_results(vid):
                        pn = h.get("pn")
                        if not pn or pn in done:
                            continue
                        done.add(pn)
                        final_new.append(enrich(h, by_pn.get(pn, {"pn": pn}), vid))
                except Exception as e:
                    log(f"final harvest error: {e}")
            if final_new:
                append_rows(final_new)
            summary = rewrite_json_summary()
            log(
                f"COMPLETE looked_up={summary['n_looked_up']}/{len(rows)} "
                f"FOUND={summary['n_found']} NOT_FOUND={summary['n_not_found']} "
                f"verdicts={summary['by_verdict']} | AIM apply=NO"
            )
            STATE.write_text(
                json.dumps(
                    {
                        "status": "COMPLETE",
                        "at": datetime.now().isoformat(),
                        "n_looked_up": summary["n_looked_up"],
                        "n_found": summary["n_found"],
                        "n_not_found": summary["n_not_found"],
                        "by_verdict": summary["by_verdict"],
                        "open_remaining": len(rows) - summary["n_looked_up"],
                        "aim_apply": False,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            return 0

        if idle_rounds >= 30:
            log("STOP — 30 idle polls with batches still marked running (likely hung)")
            summary = rewrite_json_summary()
            STATE.write_text(
                json.dumps(
                    {
                        "status": "HUNG",
                        "at": datetime.now().isoformat(),
                        "n_looked_up": summary.get("n_looked_up", 0),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            return 4


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FATAL {e}")
        raise
