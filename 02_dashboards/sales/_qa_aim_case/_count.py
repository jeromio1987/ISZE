from pathlib import Path
t = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_vs_Price_Class_Case.html").read_text(encoding="utf-8")
print("bar-row", t.count("bar-row"))
print("pages", sum(1 for i in range(1, 11) if f'id="p{i}"' in t))
print("shared", "shared" in t)
print("internal", "internal" in t)
print("sellout", "sellout" in t.lower() or "sell-out" in t.lower())
print("bytes", len(t.encode("utf-8")))
