import re

h = open(r"_build_30\ISUZU_UNIVERSE_3_0.html", encoding="utf-8").read()
i = h.find("Executive summary")
print(repr(h[i - 400:i + 700]))
print()
print("=== keep divs and what they contain ===")
for m in re.finditer(r'<div class="keep">(.*?)</div>\s*(?=<div class="keep">|<h|<p|<table|<figure|$)', h, re.S):
    inner = m.group(1)
    first = re.search(r"<h[234]>(.*?)</h[234]>", inner)
    tag = first.group(1) if first else "(no heading)"
    print(f"  {tag[:46]:<48} contains: " + ", ".join(re.findall(r"<(h[234]|p|table|figure|ul|ol)[ >]", inner)))
