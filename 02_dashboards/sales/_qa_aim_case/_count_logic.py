from pathlib import Path
t = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_New_Logic.html").read_text(encoding="utf-8")
print("bytes", len(t.encode("utf-8")))
print("sections", t.count('class="page"'))
print("aim_meaning", "Aftermarket Intelligence Model" in t)
print("banned_ModeA", "Mode A" in t or "Mode B" in t)
