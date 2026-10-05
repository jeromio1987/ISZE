"""Repair the 69 U+FFFD sites in DELEGATOR_BOARD.md, classified from context.

Two files of evidence establish both the count and the cause:
  * the file is 138 bytes longer than it should be, and 138 = 69 x 2
  * all 69 sites are U+FFFD, and every FFFD here is 1-byte CP1252 -> 3-byte FFFD
    (a PowerShell [IO.File]::WriteAllText round trip read ANSI, wrote UTF-8)

Classification rules, applied in this order:
  1. FFFD with a space either side -> em dash (the file's dash convention)
  2. FFFD immediately before a digit / 0. -> euro
  3. FFFD immediately after a digit and before a space -> euro
  4. otherwise -> em dash

Dry run by default. Writes only with --write. Prints every site for review.
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

P = "00_docs/agent/DELEGATOR_BOARD.md"
FFFD = b"\xef\xbf\xbd"
WRITE = "--write" in sys.argv

raw = open(P, "rb").read()
out = bytearray()
i = 0
sites = []
while True:
    j = raw.find(FFFD, i)
    if j < 0:
        out += raw[i:]
        break
    out += raw[i:j]
    prev = raw[j - 1:j]
    nxt = raw[j + 3:j + 4]
    nxt2 = raw[j + 3:j + 5]
    if prev == b" " and nxt == b" ":
        ch, why = "\u2014", "space both sides"
    elif nxt.isdigit() or nxt2 == b"0.":
        ch, why = "\u20ac", "before a number"
    elif prev.isdigit() and nxt == b" ":
        ch, why = "\u20ac", "after a number"
    else:
        ch, why = "\u2014", "default dash"
    sites.append((len(sites) + 1, j, why, ch,
                  raw[max(0, j - 45):j + 48].decode("utf-8", "replace")))
    out += ch.encode("utf-8")
    i = j + 3

print(f"sites found: {len(sites)}")
print(f"em dash: {sum(1 for s in sites if s[3] == chr(0x2014))}   "
      f"euro: {sum(1 for s in sites if s[3] == chr(0x20ac))}")
print()
for n, off, why, ch, ctx in sites:
    label = "EM " if ch == "\u2014" else "EUR"
    print(f"{n:3} {label} {why:18} ...{ctx.strip()}...")

print()
print(f"new size would be {len(out):,} bytes (now {len(raw):,}, delta {len(out)-len(raw)})")
print(f"remaining U+FFFD after repair: {bytes(out).count(FFFD)}")
# em dash and euro are both 3 bytes in UTF-8, exactly what the FFFD sites cost,
# so the file length is unchanged by the repair
assert bytes(out).count(FFFD) == 0, "leftover FFFD"
assert len(out) == len(raw), f"unexpected delta {len(out)-len(raw)}"
# every non-FFFD byte must be preserved exactly
after_text = bytes(out).decode("utf-8")  # raises if anything else is broken
assert after_text.count("\ufffd") == 0
before_ok = raw.replace(FFFD, b"").decode("utf-8")
assert after_text.replace("\u2014", "").replace("\u20ac", "") == \
       before_ok.replace("\u2014", "").replace("\u20ac", ""), "a non-FFFD byte changed"

if WRITE:
    import shutil
    shutil.copy2(P, P + ".dmg_fffd_20260924_1819")
    open(P, "wb").write(out)
    print("WRITTEN (damaged copy kept as *.dmg_fffd_20260924_1819)")
else:
    print("dry run - pass --write to apply")
