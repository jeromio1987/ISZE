"""Extract the page's own script block (not Chart.js) and syntax-check it."""
import io
import os
import re
import subprocess

HTML = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Truck_Catalogue_2026-09-18.html"
out = io.open(HTML, encoding="utf-8").read()

# the application script is the last plain <script> block in the document
blocks = re.findall(r"<script>(.*?)</script>", out, re.S)
print("plain script blocks:", [len(b) for b in blocks])
app = blocks[-1]
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_app_check.js")
io.open(p, "w", encoding="utf-8").write(app)
r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
print("returncode", r.returncode)
print(r.stderr[:3000])
