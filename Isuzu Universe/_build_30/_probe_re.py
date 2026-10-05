import re

p1 = r"^<(h[234])>(.*?)</h\1>$"
p2 = r"^<h([234])>(.*?)</h\1>$"
p3 = r"^<h(?P<lvl>[234])>(?P<txt>.*?)</h(?P=lvl)>$"
for s in ["<h2>Chapter schedule</h2>", "<h3>1.1 The promise</h3>"]:
    print(repr(s))
    print("  p1", re.match(p1, s))
    print("  p2", re.match(p2, s))
    print("  p3", re.match(p3, s))
