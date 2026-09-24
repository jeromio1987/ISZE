"""Final precise check of the board edit: my row, and the pre-existing oddities."""
import subprocess
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"00_docs\agent\DELEGATOR_BOARD.md"
BAK = r"02_dashboards\_build\_aim_pass2\DELEGATOR_BOARD.bak_before_pass3_20260924.md"

head = subprocess.run(["git", "show", "HEAD:00_docs/agent/DELEGATOR_BOARD.md"],
                      capture_output=True, cwd=r"C:\Users\jerom\Desktop\claude\ISZE").stdout
bak = open(BAK, "rb").read()
now = open(P, "rb").read()
ht, nt, bt = head.decode("utf-8"), now.decode("utf-8"), bak.decode("utf-8")

print("byte identity")
print("  my backup identical to HEAD :", bak == head)
print()

MYROW = [l for l in nt.split("\n") if l.startswith("| 2026-09-24 20:20")][0]
print("my row")
print("  appears in the file exactly      :", nt.count(MYROW), "time(s)")
print("  cells                            :", len(MYROW.strip().strip("|").split("|")))
print("  ASCII only                       :", MYROW.isascii())
print()

for label, text in (("HEAD", ht), ("now", nt)):
    lines = text.split("\n")
    dashes = Counter(l for l in lines if l.startswith("| 2026-09-18 21:05"))
    print(f"{label}: rows starting '| 2026-09-18 21:05' -> {sum(dashes.values())}")
    for l, n in dashes.items():
        print(f"   x{n} cells={len(l.strip().strip('|').split('|'))}: {l[:200]}")
print()

# the three rows that look duplicated
for probe in ["| 2026-09-24 16:58 |", "| 2026-09-24 16:56 |", "| 2026-09-24 17:05 |",
              "| 2026-09-24 17:35 |", "| 2026-09-24 18:13 |", "| 2026-09-24 19:55 |"]:
    print(f"count in HEAD {ht.count(probe):>3}  count now {nt.count(probe):>3}   {probe}")
print()
print("total lines HEAD:", len(ht.split("\n")), "  now:", len(nt.split("\n")))
print("bytes HEAD:", len(head), " backup:", len(bak), " now:", len(now), " added:", len(now) - len(head))
print("U+FFFD in now:", nt.count("\ufffd"))
