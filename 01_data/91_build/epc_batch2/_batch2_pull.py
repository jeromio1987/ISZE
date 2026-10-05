"""Walk the EPC tab and pull the whole result array out in slices, via the browser tool.

The page cannot reach a local sink and no local DevTools port is reachable, so the transport is the
session's browser tool. This prints the slices that still need reading; each Runtime.evaluate
response over ~25 KB is written to a file by the tool, which _batch2_ingest.py then reads.

usage: python _batch2_pull.py [--done <n>]
"""
from __future__ import annotations

import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
STATE = BUILD / "_pull_state.txt"
SLICE = 50
TOTAL = 250


def main() -> int:
    done = 0
    if "--done" in sys.argv:
        done = int(sys.argv[sys.argv.index("--done") + 1])
    elif STATE.is_file():
        done = int(STATE.read_text().strip() or "0")

    remaining = list(range(done, TOTAL, SLICE))
    print(f"total={TOTAL} already_read={done} slices_remaining={len(remaining)}")
    for start in remaining:
        end = min(start + SLICE, TOTAL)
        print(f"window.__slice({start},{end})")
    if not remaining:
        print("all slices read; run _batch2_finalize.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
