"""Confirm the repair touched only the 69 character sites, nothing else."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

LIVE = "00_docs/agent/DELEGATOR_BOARD.md"
DMG = LIVE + ".dmg_fffd_20260924_1819"

live = open(LIVE, "rb").read().decode("utf-8")
dmg = open(DMG, "rb").read().decode("utf-8", errors="replace")

# normalise: turn the repaired characters back into the marker they replaced
norm_live = live.replace("\u2014", "\ufffd").replace("\u20ac", "\ufffd")
print("live == damaged once normalised:", norm_live == dmg)
if norm_live != dmg:
    for i, (a, b) in enumerate(zip(norm_live, dmg)):
        if a != b:
            print("first difference at", i)
            print("  live:", repr(norm_live[i-80:i+90]))
            print("  dmg :", repr(dmg[i-80:i+90]))
            break
    print("lengths", len(norm_live), len(dmg))

# my row must be present exactly once, unaltered, 5 cells
mine = [l for l in live.split("\n") if "cursor (AIM dashboard refresh)" in l]
print("my rows:", len(mine))
print("my row pipes:", mine[0].count("|") if mine else "n/a")
print("says 19 receipts:", "19 receipts written" in live)
print("says 20 receipts:", "20 receipts written" in live)

# no row was reordered: row count and my row last
rows = [l for l in live.split("\n") if l.startswith("| 2026")]
print("total dated rows:", len(rows))
print("my row is last:", "AIM dashboard refresh" in rows[-1])
