import re, os
OPS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(OPS, "ISZE_OS_Console.html"), encoding="utf-8").read()
tbl = s.split('id="queue"', 1)[1]
body = tbl.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
rows = re.findall(r"<tr>(.*?)</tr>", body, re.S)
print("queue rows:", len(rows))
for r in rows:
    cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
    txt = re.sub(r"<[^>]+>", " ", cells[1] if len(cells) > 1 else "")
    txt = re.sub(r"\s+", " ", txt).strip()
    owner = re.sub(r"<[^>]+>", " ", cells[3]) if len(cells) > 3 else "?"
    print("  -", txt[:90], "| owner:", owner.strip()[:40])
srcs = re.findall(r'class="qsrc">(.*?)</span>', body)
print("sources used:", sorted(set(srcs)))
