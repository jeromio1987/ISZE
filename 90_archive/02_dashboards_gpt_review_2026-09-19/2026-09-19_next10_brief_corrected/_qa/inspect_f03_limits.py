import json, re
P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\03_Warranty_Commercial_Review.html"
t = open(P, encoding="utf-8", newline="").read()
m = re.search(r"window\.__WARRANTY__\s*=\s*", t)
b = t.index("{", m.end())
depth = 0; i = b; in_str = False; esc = False
while i < len(t):
    ch = t[i]
    if in_str:
        if esc: esc = False
        elif ch == "\\": esc = True
        elif ch == '"': in_str = False
    else:
        if ch == '"': in_str = True
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: break
    i += 1
blob = t[b:i + 1]
d = json.loads(blob)
print("parses: yes, keys:", list(d.keys()))
print("limits:", json.dumps(d["limits"], indent=1))
print("cv_family sample:", json.dumps(d["cv_family"][:2], indent=1))
print("n who_pays:", len(d["who_pays"]))
tot = sum(r["parts_turnover_eur"] for r in d["who_pays"])
print("who_pays total eur:", tot)
print("limits total eur:", sum(r["parts_turnover_eur"] for r in d["limits"]))
for r in d["limits"]:
    print("   ", r["position"], r["parts_turnover_eur"], round(100 * r["parts_turnover_eur"] / sum(x["parts_turnover_eur"] for x in d["limits"]), 1))
print("script end offset", i, "of", len(t))
