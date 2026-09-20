from pathlib import Path
import json
import re

t = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
    r"\ISZE_Pricing_Revision_AIM_Source.html"
).read_text(encoding="utf-8")
print("Parts billed (in scope)", "Parts billed (in scope)" in t)
print("rollupCustomers([2])", "rollupCustomers([2])" in t)
print("rollupCustomers([0,2])", "rollupCustomers([0,2])" in t)
print("fmtEur(t.all)", "fmtEur(t.all)" in t)
print("fmtEur(t.billed) count", t.count("fmtEur(t.billed)"))
i = t.find("function drawLeague")
print("--- drawLeague ---")
print(t[i : i + 600])

m = re.search(r"var D=(\{.*?\});\s*var P=", t, re.S)
d = json.loads(m.group(1))
ituk = d["pool"]["db"].index("ITUK")
gs = [r for r in d["groups"] if r[0] == ituk]
print("ITUK all", round(sum(r[12] for r in gs), 2), "billed", round(sum(r[8] for r in gs), 2))
