"""Exactly what changed in DELEGATOR_BOARD.md: HEAD, my pre-edit backup, and the file now."""
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


def rows(b: bytes):
    t = b.decode("utf-8")
    L = t.split("\n")
    out = []
    for i, l in enumerate(L):
        if l.strip() == "| Time | Agent | What changed | Files touched | Next step |":
            j = i + 2
            while j < len(L) and L[j].strip().startswith("|"):
                out.append(L[j])
                j += 1
    return t, out


ht, hr = rows(head)
bt, br = rows(bak)
nt, nr = rows(now)

print(f"HEAD    : {len(head):>7,} bytes, {len(hr)} change-log rows")
print(f"backup  : {len(bak):>7,} bytes, {len(br)} change-log rows")
print(f"now     : {len(now):>7,} bytes, {len(nr)} change-log rows")
print()

hs, bs, ns = set(hr), set(br), set(nr)
print(f"rows in now but not in HEAD : {len(ns - hs)}")
for r in sorted(ns - hs):
    print("   +", r[:170])
print(f"rows in HEAD but not in now : {len(hs - ns)}")
for r in sorted(hs - ns):
    print("   -", r[:170])
print()
print(f"rows in now but not in my backup: {len(ns - bs)}")
for r in sorted(ns - bs):
    print("   +", r[:170])
print(f"rows in my backup but not in now: {len(bs - ns)}")
for r in sorted(bs - ns):
    print("   -", r[:170])
print()

# the byte prefix before the tables must be identical
def prefix(t: str) -> bytes:
    i = t.index("| Time | Agent |")
    return t[:i].encode("utf-8")


print("prefix to the first change-log header identical HEAD vs now  :", prefix(ht) == prefix(nt))
print("prefix to the first change-log header identical backup vs now:", prefix(bt) == prefix(nt))
print()
print("non-5-cell rows now:")
for r in nr:
    if len(r.strip().strip("|").split("|")) != 5:
        print("   ", r[:200])
print()
print("duplicate rows now:", [k for k, v in Counter(nr).items() if v > 1])
