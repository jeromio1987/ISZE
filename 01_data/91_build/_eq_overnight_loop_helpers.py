"""Dump EQ CDP hits (with pad to force browser-logs) harvest helper note — use via MCP dumps."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
INBOX = ROOT / "01_data" / "90_INBOX"
HARVEST = ROOT / "01_data" / "91_build" / "harvest_eq_hit_session_20260919.py"
STATE = INBOX / "_EQ_HIT_SESSION_20260919_overnight_state.json"
LOG = INBOX / "_EQ_HIT_SESSION_20260919_log.txt"
RESULTS = INBOX / "_EQ_HIT_SESSION_20260919_RESULTS.json"
QUEUE = INBOX / "_EQ_HIT_SESSION_20260919_queue.json"


def unwrap(raw):
    val = raw
    for _ in range(4):
        if isinstance(val, dict) and "result" in val:
            val = val["result"]
            continue
        break
    if isinstance(val, dict) and "value" in val:
        val = val["value"]
    if isinstance(val, str):
        val = json.loads(val)
    return val


def harvest_file(path: Path, view: str) -> int:
    val = unwrap(json.loads(path.read_text(encoding="utf-8")))
    hits = []
    if isinstance(val, dict):
        hits = val.get("hits") or val.get("chunk") or []
    elif isinstance(val, list):
        hits = val
    if not hits:
        print(f"no hits in {path.name}")
        return 0
    payload = {"view_id": view, "hits": hits}
    tmp = ROOT / "01_data" / "91_build" / "_eq_harvest_payload_tmp.json"
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    r = subprocess.run([sys.executable, str(HARVEST), str(tmp)], check=False)
    print(f"harvested {len(hits)} from {path.name} rc={r.returncode}")
    return len(hits)


def open_pns():
    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    rows = q.get("rows", q) if isinstance(q, dict) else q
    pns = [r["pn"] if isinstance(r, dict) else r for r in rows]
    res = json.loads(RESULTS.read_text(encoding="utf-8"))
    done = {r["pn"] for r in res.get("rows", [])}
    return [p for p in pns if p not in done], res


def write_state(extra: dict) -> None:
    open_list, res = open_pns()
    state = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "aim_apply": False,
        "n_looked_up": res.get("n_looked_up"),
        "n_found": res.get("n_found"),
        "n_not_found": res.get("n_not_found"),
        "n_error": res.get("n_error"),
        "by_verdict": res.get("by_verdict"),
        "queue_total": 744,
        "open_remaining": len(open_list),
        **extra,
    }
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] state looked_up={state['n_looked_up']} open={state['open_remaining']} {extra.get('note','')}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "harvest":
        view = sys.argv[2]
        for p in sys.argv[3:]:
            harvest_file(Path(p), view)
        write_state({"note": "post-harvest"})
    elif cmd == "open":
        open_list, res = open_pns()
        out = INBOX / "_eq_remaining_open_20260919.json"
        out.write_text(json.dumps(open_list), encoding="utf-8")
        print(json.dumps({"open": len(open_list), "looked_up": res.get("n_looked_up"), "sample": open_list[:5]}))
    elif cmd == "state":
        write_state(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
    else:
        raise SystemExit("usage: harvest|open|state")
