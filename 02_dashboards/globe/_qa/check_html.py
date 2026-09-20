"""Extract the inline <script> blocks from index.html and syntax-check them.

A mismatched quote in a panel string broke the whole page once (see QA_NOTE.md,
bug 5), and a builder exit code of 0 does not catch that. `node --check` does.

Also a small structural check on the HTML: the ids the script looks up must
actually exist in the markup, because a missing one throws at load.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
HTML = HERE / "index.html"

html = HTML.read_text(encoding="utf-8")

blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
print(f"inline script blocks found: {len(blocks)}")
failures = []

for i, block in enumerate(blocks):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(block)
        tmp = fh.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"  block {i}: {len(block):,} chars  ->  {'OK' if ok else 'SYNTAX ERROR'}")
    if not ok:
        failures.append(f"block {i}")
        print(r.stderr.strip()[:800])

# --- ids referenced by getElementById must exist ---------------------------
print()
print("element ids the script looks up:")
referenced = sorted(set(re.findall(r'getElementById\("([^"]+)"\)', html)))
declared = set(re.findall(r'\bid="([^"]+)"', html))
missing = [x for x in referenced if x not in declared]
print(f"  referenced: {len(referenced)}   declared in markup: {len(declared)}")
for x in referenced:
    mark = "ok  " if x in declared else "MISSING"
    print(f"    [{mark}] {x}")
if missing:
    failures.append("missing ids: " + ", ".join(missing))

# --- no esri tile service anywhere ----------------------------------------
# The comment block in index.html names Esri on purpose, to record why the
# source was removed. What must not come back is the tile URL itself.
print()
for pat in ("arcgisonline", "/MapServer/tile/", "World_Street_Map/MapServer",
            "basemaps.cartocdn.com"):
    n = html.count(pat)
    print(f"  occurrences of {pat!r}: {n}")
ESRI_URL_MARKERS = ["arcgisonline", "/MapServer/tile/", "World_Street_Map/MapServer"]
for pat in ESRI_URL_MARKERS:
    if html.count(pat):
        failures.append(f"Esri tile URL still referenced: {pat}")

# --- banned words / agent slang -------------------------------------------
print()
BANNED = ["sell-out", "sell out", "sellout", "wallet", "Mode A", "Mode B",
          "ship-gate", "receipt", "harness", "street index", "class factor"]
body = html.lower()
for w in BANNED:
    n = body.count(w.lower())
    print(f"  banned phrase {w!r}: {n}")
    if n:
        failures.append(f"banned phrase present: {w} ({n})")

# "Live streets" is map geography and is an explicit, documented exception.
print("  (note: 'streets' as map geography is allowed; see README)")

print()
if failures:
    print("FAILED:")
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("index.html structure checks passed")
