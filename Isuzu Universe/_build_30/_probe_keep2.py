import re

h = open(r"_build_30\ISUZU_UNIVERSE_3_0.html", encoding="utf-8").read()
print("keep blocks:", h.count('<div class="keep">'), " tbl-flow:", h.count("tbl-flow"), " chapter-start:", h.count("chapter-start"))
i = 0
n = 0
while True:
    s = h.find('<div class="keep">', i)
    if s < 0:
        break
    depth = 1
    j = s + len('<div class="keep">')
    while j < len(h) and depth:
        if h.startswith("<div", j):
            depth += 1
        elif h.startswith("</div>", j):
            depth -= 1
            if depth == 0:
                break
        j += 1
    inner = h[s + len('<div class="keep">'):j]
    tags = re.findall(r"<(h[234]|p|table|figure|ul|ol|blockquote)[ >]", inner)
    first = re.search(r"<h[234]>(.*?)</h[234]>", inner)
    label = first.group(1)[:40] if first else "(no heading)"
    print(f"{n:2d} {label:<42} tags={tags} rows={inner.count('<tr>')} chars={len(inner)}")
    i = j + 6
    n += 1
