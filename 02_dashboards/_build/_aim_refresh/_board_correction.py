"""Append one correction row recording the DELEGATOR_BOARD encoding damage.

Written as raw bytes, ASCII only, so no encoder can touch the file again.
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

ROW = (
    "| 2026-09-24 18:20 | cursor (AIM dashboard refresh) | "
    "**I damaged DELEGATOR_BOARD.md and repaired it. 69 characters were destroyed, all 69 restored.** "
    "A one-word PowerShell replacement used [IO.File]::WriteAllText, which read the file as the local ANSI code page instead of UTF-8, so 69 single-byte characters that are not in CP1252 failed to decode and were written back as the 3-byte replacement character. "
    "The tell was arithmetic: my replacement string was the same length as the one it replaced, yet the file grew by 138 bytes, and 138 is 69 times 2. "
    "The 69 sites were 45 em dashes and 24 euro signs, in rows belonging to other agents, not just mine. "
    "Repaired by classifying each of the 69 sites from its own context under three stated rules: a space either side means em dash, before a digit means euro, default em dash. "
    "Verified by normalising the repaired file back and comparing it to the damaged copy - identical, so no other byte moved. "
    "45 em dashes and 24 euro signs are back, the file now decodes as valid UTF-8, and my own row is present once, last, with 5 cells. "
    "The damaged copy is kept as DELEGATOR_BOARD.md.dmg_fffd_20260924_1819 and the repair script is retained. "
    "Cause of cause: I should have used a UTF-8 safe write or a byte-level append, which is what my first appended row did correctly. | "
    "`00_docs/agent/DELEGATOR_BOARD.md` (repaired), `00_docs/agent/DELEGATOR_BOARD.md.dmg_fffd_20260924_1819` (damaged copy kept), `02_dashboards/_build/_aim_refresh/_board_repair.py` | "
    "No action needed from anyone. Anyone holding a copy of this board from before 18:19 should say so and it can be diffed against the repair. "
    "This row and the AIM refresh row above are the only rows I added. |\n"
)

P = "00_docs/agent/DELEGATOR_BOARD.md"
for ch in ROW:
    if ord(ch) > 127:
        raise SystemExit("non-ascii: " + repr(ch))
if ROW.count("|") != 6:
    raise SystemExit(f"expected 6 pipes, got {ROW.count('|')}")

raw = open(P, "rb").read()
if b"\r\n" in raw:
    raise SystemExit("unexpected CRLF")
if not raw.endswith(b"\n"):
    raise SystemExit("no trailing newline")
if b"cursor (AIM dashboard refresh)" not in raw:
    raise SystemExit("my earlier row is missing - refusing to append")

open(P, "ab").write(ROW.encode("ascii"))
print("appended correction row")
print("pipes:", ROW.count("|"), " new bytes:", len(open(P, "rb").read()))
