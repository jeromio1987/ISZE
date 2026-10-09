"""Inspect the built payload of the backlog page."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\ISZE_Backlog_IML_WK41.html")
s = p.read_text(encoding="utf-8")
m = re.search(r'<script type="application/json" id="payload">(.*?)</script>', s, re.S)
d = json.loads(m.group(1).replace("<\\/", "</"))

print("build stamp :", d["build"])
k = d["kpi"]
print("cov_wh      :", json.dumps(d["cov_wh"]))
print("cov_bo      :", json.dumps(d["cov_bo"]))
print("aim_master  :", json.dumps(d["aim_master"]))
print("iml lines   :", k["iml_lines"], "| over30:", k["over30_lines"], "| bo lines:", k["bo_lines"])
print()
for dim in ["noun", "aim", "aim2"]:
    w = d["wait"][dim]
    print(f"=== wait groups by {dim}: {len(w)} ===")
    for g in w[:6]:
        ex = g["examples"][0]["part"][:26] if g["examples"] else ""
        print(f"   {str(g['key'])[:20]:22s} lines {g['lines']:4d} pcs {g['pcs']:6d} "
              f"oldest {g['oldest']:4d} custs {g.get('n_customers', 0):2d} "
              f"matched {g.get('matched_pns', 0):3d}  {ex}")
print()
k = d["kpi"]
print("wait lines/pcs  :", k["wait_lines"], k["wait_pcs"])
print("wait groups     :", k["wait_groups"], "| worst:", k["wait_worst_group"], k["wait_worst_group_pcs"])
print("groups with no customer:", k["wait_groups_no_customer"])
print()
print("facets: iml_facts has noun:", "noun" in d["iml_facts"][0])
print("kpi iml lines   :", k["iml_lines"], "| over30:", k["over30_lines"])
print("bo lines        :", k["bo_lines"], "| bo pcs:", k["bo_pcs"])
