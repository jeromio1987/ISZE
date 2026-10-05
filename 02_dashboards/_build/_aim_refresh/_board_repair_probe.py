"""Repair the 69 U+FFFD sites in DELEGATOR_BOARD.md.

Cause: a PowerShell [IO.File]::WriteAllText round trip read the file as the local
ANSI code page, so 69 single-byte CP1252 characters (em dash, en dash, arrow,
middle dot, euro) failed to decode and were written back as the 3-byte U+FFFD.
138 extra bytes = 69 x 2, which is how the site count was established.

Repair: count the surviving intact multi-byte characters, and replace the FFFD
sites with the same character. Refuse to write unless the counts match exactly.
Surgical byte-level edit; every other byte is preserved.
"""
import re, sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

P = "00_docs/agent/DELEGATOR_BOARD.md"
FFFD = b"\xef\xbf\xbd"

raw = open(P, "rb").read()
n_fffd = raw.count(FFFD)
print(f"file bytes          : {len(raw):,}")
print(f"U+FFFD count        : {n_fffd}")
print(f"expected to replace : {n_fffd}")

# surviving intact characters, in order of count
counts = {}
for ch, enc in (("\u2014 euro-dash?", "x"),):
    pass
for name, ch in (("em dash", "\u2014"), ("en dash", "\u2013"),
                 ("right arrow", "\u2192"), ("middle dot", "\u00b7"),
                 ("euro", "\u20ac")):
    counts[ch] = raw.count(ch.encode("utf-8"))
print("surviving intact counts:", {k: v for k, v in counts.items()})
