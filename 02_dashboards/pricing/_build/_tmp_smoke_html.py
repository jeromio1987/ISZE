from pathlib import Path
import json
import re

html_path = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html")
html = html_path.read_text(encoding="utf-8")
assert "cdnjs" not in html.lower()
assert 'id="cust"' in html
assert "c-cust-mix" in html
assert "cust_pn" in html
m = re.search(r'id="payload">(.*?)</script>', html, re.S)
d = json.loads(m.group(1))
assert len(d["cust_pn"]) > 1000
assert "pn" in d["pool"]
print("HTML OK")
print("cust_pn", len(d["cust_pn"]))
print("MB", round(html_path.stat().st_size / 1024 / 1024, 2))
