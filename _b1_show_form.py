import re
import sys
from pathlib import Path

p = Path(sys.argv[1])
h = p.read_text(encoding="utf-8", errors="replace")
pat = sys.argv[2] if len(sys.argv) > 2 else r'<form[^>]*id="search".*?</form>'
m = re.search(pat, h, re.S | re.I)
blk = m.group(0) if m else ""
print(re.sub(r"\s+", " ", blk)[:1600])
print("---- inputs ----")
for i in re.finditer(r"<input[^>]*>", blk, re.I):
    print(re.sub(r"\s+", " ", i.group(0)))
print("---- search-ish hrefs ----")
for i in sorted(set(re.findall(r'href="([^"]*(?:search|zoek|buscar)[^"]*)"', h, re.I)))[:25]:
    print(" ", i)
