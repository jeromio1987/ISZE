"""Snapshot or diff the page's embedded payload.

    python _tmp_nmr_payload_20260923.py save   <out.json>
    python _tmp_nmr_payload_20260923.py diff   <before.json>

The diff walks every leaf and prints what changed, so "only the NMR wording moved" is proved rather
than asserted. Keys that always change on a rebuild are listed separately.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ALWAYS = {"generated"}
HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales"
            r"\ISZE_PMS_Family_Evolution_v2.html")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def payload() -> dict:
    h = HTML.read_text(encoding="utf-8")
    return json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                                h, re.S).group(1))


def walk(a, b, path=""):
    out = []
    if type(a) is not type(b):
        return [(path, a, b)]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((f"{path}.{k}", "(absent)", b[k]))
            elif k not in b:
                out.append((f"{path}.{k}", a[k], "(absent)"))
            else:
                out += walk(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((f"{path}[len]", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out += walk(x, y, f"{path}[{i}]")
    elif a != b:
        out.append((path, a, b))
    return out


def main() -> int:
    mode, target = sys.argv[1], Path(sys.argv[2])
    if mode == "save":
        d = payload()
        target.write_text(json.dumps(d, indent=1, sort_keys=True), encoding="utf-8")
        print(f"saved {target}  {target.stat().st_size:,} bytes  keys {len(d)}")
        return 0

    now, was = payload(), json.loads(target.read_text(encoding="utf-8"))
    diffs = walk(was, now)
    real = [d for d in diffs if d[0].split(".")[1] not in ALWAYS and d[0] not in ALWAYS]
    print("=" * 100)
    print("PAYLOAD DIFF")
    print("=" * 100)
    print(f"  leaf changes total {len(diffs):,}   excluding {'/'.join(sorted(ALWAYS))}: {len(real):,}")
    for path, a, b in real:
        print(f"  {path}")
        print(f"      was {str(a)[:170]}")
        print(f"      now {str(b)[:170]}")
    if not real:
        print("  NOTHING ELSE MOVED")
    print()
    print("=" * 100)
    print("FIGURE GUARD: did any NUMBER move?")
    print("=" * 100)
    def leaves(o, p=""):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from leaves(v, f"{p}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from leaves(v, f"{p}[{i}]")
        else:
            yield p, o
    a_map = dict(leaves(was))
    b_map = dict(leaves(now))
    nums_moved = []
    for k in sorted(set(a_map) | set(b_map)):
        x, y = a_map.get(k), b_map.get(k)
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            if x != y:
                nums_moved.append((k, x, y))
    print(f"  numeric leaves that moved: {len(nums_moved)}")
    for k, x, y in nums_moved:
        print(f"      {k}: {x} -> {y}")
    strs_moved = [k for k in sorted(set(a_map) | set(b_map))
                  if isinstance(a_map.get(k), str) and a_map.get(k) != b_map.get(k)]
    print(f"  string leaves that moved : {len(strs_moved)}")
    for k in strs_moved:
        print(f"      {k}")
        print(f"          was {str(a_map.get(k))[:150]}")
        print(f"          now {str(b_map.get(k))[:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
