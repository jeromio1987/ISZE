import json
d = json.load(open(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\VERIFY_ALL.json", encoding="utf-8"))
print(f"{'distributor':<10} {'billed months':<28} {'sold-to-dealer months':<28} scope")
for c in d["coverage"]:
    b = c["billed_range"]; a = c["sold_range"]
    bs = f"{b[0]} to {b[1]} ({c['billed_months']}m)" if b else "-"
    as_ = f"{a[0]} to {a[1]} ({c['sold_months']}m)" if a else "none"
    print(f"{c['db']:<10} {bs:<28} {as_:<28} {c['sold_scope']}")
