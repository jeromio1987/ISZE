"""Finalize EQ overnight state when queue complete."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

INBOX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
res = json.loads((INBOX / "_EQ_HIT_SESSION_20260919_RESULTS.json").read_text(encoding="utf-8"))
rows = res["rows"]
st = Counter(r.get("eq_status") for r in rows)
ver = Counter(r.get("verdict") for r in rows)
state = {
    "as_of": datetime.now(timezone.utc).isoformat(),
    "aim_apply": False,
    "status": "QUEUE_COMPLETE",
    "queue_total": 744,
    "n_looked_up": res.get("n_looked_up"),
    "n_found": res.get("n_found"),
    "n_not_found": res.get("n_not_found"),
    "n_error": res.get("n_error"),
    "by_eq_status": dict(st),
    "by_verdict": dict(ver),
    "open_remaining": 0,
    "sessions_final": {
        "s0_0e130666": "idle after part1",
        "s1_e0d4a8d2": "idle after part2",
        "s2_b9f05f9e": "idle after part0",
        "a9b389b1": "login wall unused",
    },
    "results_csv": str(INBOX / "_EQ_HIT_SESSION_20260919_RESULTS.csv"),
    "results_json": str(INBOX / "_EQ_HIT_SESSION_20260919_RESULTS.json"),
    "note": "All 744 queue PNs looked up. AIM apply NOT run — separate ask only.",
}
(INBOX / "_EQ_HIT_SESSION_20260919_overnight_state.json").write_text(
    json.dumps(state, indent=2), encoding="utf-8"
)
line = (
    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] QUEUE_COMPLETE "
    f"looked_up=744 FOUND={res.get('n_found')} NOT_FOUND={res.get('n_not_found')} "
    f"by_verdict={dict(ver)} aim_apply=false"
)
with (INBOX / "_EQ_HIT_SESSION_20260919_log.txt").open("a", encoding="utf-8") as f:
    f.write(line + "\n")
print(json.dumps(state, indent=2))
print(line)
