import json
from pathlib import Path

d = json.loads(
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\pricing_dashboard_data.json")
    .read_text(encoding="utf-8")
)
ituk = d["pool"]["db"].index("ITUK")
iuk = d["pool"]["db"].index("IUK")
print("ITUK", ituk, "IUK", iuk)
for r in d["customers"]:
    if r[2] == ituk:
        print("ITUK cust", d["pool"]["cust"][r[0]], d["pool"]["cname"][r[1]],
              "db", d["pool"]["db"][r[2]], "src", d["pool"]["src"][r[3]],
              "billed", r[7], "all", r[11])
for r in d["customers"]:
    if r[2] == iuk:
        print("IUK cust", d["pool"]["cust"][r[0]], "db", d["pool"]["db"][r[2]],
              "billed", r[7], "all", r[11])

# Simulate rollupCustomers([2]) with state.db=ITUK
from collections import defaultdict
m = defaultdict(lambda: {"all": 0, "billed": 0, "step": 0, "prior": 0, "new": 0, "kk": None})
for r in d["customers"]:
    if r[2] != ituk:
        continue
    o = m[r[2]]
    o["kk"] = [r[2]]
    o["billed"] += r[7]
    o["prior"] += r[8]
    o["new"] += r[9]
    o["step"] += r[10]
    o["all"] += r[11]
print("simulated league for ITUK:")
for k, v in m.items():
    print("  label", d["pool"]["db"][v["kk"][0]], "all", round(v["all"], 2), "billed", round(v["billed"], 2))
