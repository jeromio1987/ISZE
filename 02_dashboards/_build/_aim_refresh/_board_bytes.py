import sys, os, re
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

LIVE = "00_docs/agent/DELEGATOR_BOARD.md"
BAK = "00_docs/agent/DELEGATOR_BOARD.md.bak_pre_row_repair_20260924_141304"

for lbl, p in (("LIVE", LIVE), ("BACKUP", BAK)):
    raw = open(p, "rb").read()
    fffd = raw.count(b"\xef\xbf\xbd")
    non = sum(1 for b in raw if b > 127)
    # which high bytes, and how many are valid UTF-8 lead bytes
    from collections import Counter
    c = Counter(b for b in raw if b > 127)
    print(f"=== {lbl}  {p}")
    print(f"    bytes={len(raw)}  U+FFFD={fffd}  non-ASCII bytes={non}")
    print(f"    high-byte histogram: {sorted(c.items())}")
    print()
