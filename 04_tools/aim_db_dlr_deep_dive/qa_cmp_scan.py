"""Scan the two built pages: is the data embedded, is anything non-finite, is any CDN referenced."""
import json
import re
from pathlib import Path

DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")

for run in ("PORTUGAL", "ALL"):
    p = DASH / f"ISZE_AIM_Comparison_{run}.html"
    t = p.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', t, re.S)
    raw = m.group(1)
    print(f"== {run}  file {len(t)/1024/1024:.2f} MB  data block {len(raw)/1024/1024:.2f} MB")
    for tok in ("NaN", "Infinity", "undefined", "null,null"):
        print(f"     {tok!r}: {raw.count(tok)}")
    d = json.loads(raw.replace("<\\/", "</"))
    print(f"     facts rows {len(d['facts']):,} | part numbers {len(d['pn']['n']):,} | "
          f"AIM L1 {len(d['aim']['l1'])} L2 {len(d['aim']['l2'])} L3 {len(d['aim']['l3'])}")
    print(f"     views {[x['code'] for x in d['views']]}")
    print(f"     pairs {list(d['pairs'].keys())}")
    bad = 0
    for r in d["facts"]:
        for v in r:
            if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
                bad += 1
    print(f"     non-finite numbers in every fact row: {bad}")
    print(f"     http(s) src attribute present: {bool(re.search(chr(39) + 'src=\"https?://' + chr(39), t))}")
    print(f"     fetch() call present: {'fetch(' in t}")
    print(f"     new Chart( calls: {t.count('new Chart(')}")
    print(f"     GM divisor advertised: {d['gm_divisor']}")
    print(f"     min side months: {d['min_side_months']}")
