import re
s = open(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\ISZE_OS_Console.html", encoding="utf-8").read()
svg = s.split("<svg", 1)[1].split("</svg>", 1)[0]
print("svg bytes:", len(svg))
print("BREAK labels:", re.findall(r"BREAK \d+[^<]*", svg))
print("arrow/box labels:", [t for t in re.findall(r">([^<>]{3,46})</text>", svg)][:40])
print("sensor break headings:", re.findall(r'class="bx">break</span><div><b>([^<]+)', s))
print("sensor abbr:", re.findall(r'class="sabbr">([^<]+)', s))
print("state chips:", re.findall(r'class="chip ([a-z]+)"', s))
print("chart card ids:", re.findall(r"<h3>Chart (\d)", s))
