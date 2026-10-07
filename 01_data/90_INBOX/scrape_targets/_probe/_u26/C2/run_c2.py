# -*- coding: utf-8 -*-
"""U26 / agent C2 â€” dated day-2 Spareto pass + corroboration arithmetic.

WHY THIS EXISTS
---------------
The U26 brief asks for a SECOND-DAY reading of the same 123 Isuzu numbers. C1 does
day 1 in `passes/u26_c1_spareto_20261007/`. This runner waits until C1's pass is
COMPLETE (a `fetch_spareto.jsonl` with ~123 lines), then takes the day-2 reading in
its own pass folder with its own label, so the per-pass disk cache is empty and the
pages are genuinely re-read from Spareto rather than replayed from C1's cache.

Both passes go through `run_dated_pass.PassFetcher` -> `fetch_polite.PoliteFetcher`:
the robots/consent gate first, >= 2.2 s between requests to one host, cache bytes to
disk, stop (never retry) on 403/429 or a bot-challenge page. The declared bot
identity is untouched.

Then `measure_arithmetic.py` reads both passes and reports the corroboration counts.
It writes ONLY inside `_u26/C2/` (plus this pass folder) and never touches
`crossref_graded.csv`, `spareto_crossref.csv` or the ledger â€” the merge step owns those.

Usage
-----
    python .../_u26/C2/run_c2.py status   # where C1 is, and which labels are free
    python .../_u26/C2/run_c2.py wait     # poll C1 to ~123 lines, then fetch day 2
    python .../_u26/C2/run_c2.py fetch    # fetch day 2 now
    python .../_u26/C2/run_c2.py measure  # arithmetic only
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent                 # .../_probe/_u26/C2
WORKTREE = HERE.parents[5]
PROBE = WORKTREE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe"
PASSES = PROBE / "passes"
SEED = HERE / "seed_oe_pns.csv"
C1_LABEL = "u26_c1_spareto_20261007"
C1_MIN_LINES = 120                                     # brief: ~123 lines

# The brief's first choice, then its own fallback. Whichever is used must have an
# empty cache when the fetch starts; the label is reported either way.
LABEL_CANDIDATES = ["u26_c2_spareto_20261008", "u26_c2_spareto_day2"]
RUNNER = WORKTREE / "04_tools" / "delegation" / "parsers" / "run_dated_pass.py"


def c1_line_count() -> int:
    log = PASSES / C1_LABEL / "fetch_spareto.jsonl"
    if not log.exists():
        return 0
    return sum(1 for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip())


def cache_count(label: str) -> int:
    d = PASSES / label / "cache" / "spareto.com"
    return len(list(d.iterdir())) if d.exists() else 0


def pick_label() -> str:
    """First candidate whose pass log is absent or whose cache is empty."""
    for lbl in LABEL_CANDIDATES:
        if not (PASSES / lbl / "fetch_spareto.jsonl").exists():
            return lbl
        if cache_count(lbl) == 0:
            return lbl                                     # empty cache: safe to start
    return LABEL_CANDIDATES[-1]


def wait_for_c1(max_minutes: int, poll_s: int) -> bool:
    deadline = time.time() + max_minutes * 60
    print(f"waiting for C1 ({C1_LABEL}) to reach >= {C1_MIN_LINES} log lines ...", flush=True)
    while time.time() < deadline:
        n = c1_line_count()
        if n >= C1_MIN_LINES:
            print(f"C1 pass complete: {n} lines", flush=True)
            return True
        print(f"  {datetime.now(timezone.utc):%H:%M:%S}  C1 lines={n}  waiting ...", flush=True)
        time.sleep(poll_s)
    print(f"C1 did not finish within {max_minutes} min (lines={c1_line_count()})", flush=True)
    return False


def run_fetch(label: str) -> int:
    cmd = [sys.executable, str(RUNNER), "fetch", "--label", label, "--site", "spareto",
           "--pns-from-csv", str(SEED), "--online"]
    print("RUN:", " ".join(cmd), flush=True)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    p = subprocess.run(cmd, cwd=str(WORKTREE), text=True, errors="replace")
    (HERE / f"_fetch_{label}.returncode").write_text(str(p.returncode), encoding="utf-8")
    print(f"fetch finished rc={p.returncode}  started={started}", flush=True)
    return p.returncode


def run_measure() -> int:
    p = subprocess.run([sys.executable, str(HERE / "measure_arithmetic.py")],
                       cwd=str(WORKTREE), text=True, errors="replace")
    print(f"measure rc={p.returncode}", flush=True)
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["wait", "fetch", "measure", "status"])
    ap.add_argument("--label", default="")
    ap.add_argument("--max-minutes", type=int, default=60)
    ap.add_argument("--poll", type=int, default=20)
    a = ap.parse_args()

    if a.cmd == "status":
        print(f"C1 lines: {c1_line_count()}")
        for lbl in LABEL_CANDIDATES:
            print(f"  {lbl:<34} cache_files={cache_count(lbl)}  "
                  f"log={'yes' if (PASSES / lbl / 'fetch_spareto.jsonl').exists() else 'no'}")
        print(f"would use label: {pick_label()}")
        return 0

    if a.cmd == "wait" and not wait_for_c1(a.max_minutes, a.poll):
        print("STOP: C1 not complete; not starting a parallel Spareto run.", flush=True)
        return 1
    if a.cmd == "wait":
        time.sleep(5)                                      # let C1's last flush land

    if a.cmd in ("wait", "fetch"):
        label = a.label or pick_label()
        print(f"using label: {label}", flush=True)
        rc = run_fetch(label)
        (HERE / "label_used.txt").write_text(label + "\n", encoding="utf-8")
        if rc != 0:
            print(f"fetch returned {rc} (a refusal is recorded, not worked around)", flush=True)
        mrc = run_measure()
        return rc or mrc

    return run_measure()


if __name__ == "__main__":
    raise SystemExit(main())
