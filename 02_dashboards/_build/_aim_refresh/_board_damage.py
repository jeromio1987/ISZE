import re, sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

P = "00_docs/agent/DELEGATOR_BOARD.md"
raw = open(P, "rb").read()
print("bytes:", len(raw))
print("U+FFFD sequences (EF BF BD):", raw.count(b"\xef\xbf\xbd"))
print("non-ASCII bytes:", sum(1 for b in raw if b > 127))
print()

t = raw.decode("utf-8", errors="replace")
lines = t.split("\n")
for i, ln in enumerate(lines, 1):
    if "\ufffd" in ln:
        n = ln.count("\ufffd")
        # show each site with context
        for m in re.finditer("\ufffd", ln):
            s, e = max(0, m.start() - 70), min(len(ln), m.end() + 70)
            print(f"line {i:4} x{n}  ...{ln[s:e]}...")
        print()
