import hashlib
import json
import re

js = open("PASTE_INTO_EQ_CONSOLE_EPC_ONLY_20260924.js", encoding="utf-8").read()
m = re.search(r"window\.__eqh\.pns = (\[.*?\]);", js, re.S)
pns = json.loads(m.group(1))
wl = json.load(open("open_worklist_epc_only_20260924.json", encoding="utf-8"))
print("embedded pns:", len(pns), "unique:", len(set(pns)))
print("matches worklist order:", pns == wl)
print("bytes:", len(js.encode("utf-8")))
print("sha256:", hashlib.sha256(js.encode("utf-8")).hexdigest())
print("download name:", re.search(r"a\.download = '([^']+)'", js).group(1))
print("gap ms:", re.search(r"window\.__eqh\.gapMs = (\d+);", js).group(1))
print("localStorage key:", re.search(r"localStorage\.setItem\('([^']+)'", js).group(1))
print("header parts:", re.search(r"It runs about (\d+) parts", js).group(1))
print("placeholders left:", re.findall(r"%[A-Z]+%", js))

# cross-check the CSV against the classified list
import csv

with open("open_worklist_epc_only_20260924.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
print("csv rows:", len(rows), "unique k:", len({r["k"] for r in rows}))
print("csv order == json order:", [r["k"] for r in rows] == wl)
print("all k in json:", set(r["k"] for r in rows) == set(pns))
eur = sum(float(r["eur"]) for r in rows)
print("sum list eur: %.2f" % eur)
print("top 5:", [(r["rank"], r["k"], r["Description"][:28], r["eur"]) for r in rows[:5]])
