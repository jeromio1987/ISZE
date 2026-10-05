"""F02 payload surgery — inspect the forward blocks precisely. Read-only."""
P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\02_ISZE_Leakage_Cockpit.html"
with open(P, encoding="utf-8", newline="") as f:
    t = f.read()
lines = t.split("\n")
hits = [i for i, l in enumerate(lines, start=1) if '"forward": {' in l]
print("forward start lines:", hits[:25], "count", len(hits))
for n in list(range(hits[0] - 4, hits[0] + 9)) + list(range(hits[1] - 4, hits[1] + 8)) + list(range(hits[-1] - 4, hits[-1] + 8)):
    print(f"L{n}: {lines[n-1]!r}")
