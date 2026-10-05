"""Lint the state packet: length, banned words, and whether the paths it names exist.

Run: python 02_dashboards/pricing/_build/lint_state_packet.py
"""
from __future__ import annotations

import re
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
P = ISZE / "00_docs" / "agent" / "STATE_PACKET.md"
t = P.read_text(encoding="utf-8")
lines = t.splitlines()
def safe(s: str) -> str:
    """The Windows console is cp1252; arrows and dashes in the packet break print."""
    return s.encode("ascii", "replace").decode("ascii")


print(f"lines: {len(lines)}   chars: {len(t):,}")

BANNED = ["sell-out", "sell out", "sellout", "street", "book b", "mode a", "mode b",
          "ship-gate", "harness", "lane", "surface", "artefact", "artifact"]
print("\nbanned-word scan:")
found = False
for w in BANNED:
    hits = [(i + 1, safe(l.strip()[:100])) for i, l in enumerate(lines) if w in l.lower()]
    if hits:
        found = True
        print(f"  {w}: {len(hits)}")
        for h in hits[:3]:
            print(f"      line {h[0]}: {h[1]}")
if not found:
    print("  clean")

print("\n'wallet' occurrences (banned in shared labels, tolerated in internal paths):")
for i, l in enumerate(lines):
    if "wallet" in l.lower():
        print(f"  line {i+1}: {safe(l.strip()[:130])}")

print("\nreferenced paths that do not resolve:")
pat = re.compile(r"`([^`]+)`")
missing, ok = [], 0
for m in set(pat.findall(t)):
    if not re.match(r"^[0-9]", m):
        continue
    cand = m.split(" · ")[0].strip().rstrip(".")
    q = ISZE / cand.replace("\\", "/")
    if q.exists():
        ok += 1
    else:
        missing.append(m)
print(f"  resolve: {ok}")
for m in sorted(missing):
    print(f"  MISSING: {m}")

print("\nsections:")
for i, l in enumerate(lines):
    if l.startswith("## "):
        print(f"  {l[3:]}")
