"""Drive the chart-matrix harness against the built page and write _qa_charts/matrix.csv.

The probe script itself lives in _qa_charts/matrix_probe.js so the page context can fetch it.
This runner expects the page already loaded in the browser tab identified by CURSOR_TAB via CDP,
so it is invoked from the agent, not from here. Kept as the record of the method.

Read the page's own constants so the runner cannot drift from it.
"""
import re
from pathlib import Path

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\ISZE_Backlog_IML_WK41.html")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\_qa_charts")

s = HTML.read_text(encoding="utf-8")
print("page size KB:", round(len(s) / 1024, 1))
print("build stamp in payload:", (re.search(r'"build":"([^"]+)"', s) or ["", "?"])[1])
print("tabs:", len(re.findall(r'class="tab(?: on)?"', s)))
print("canvases:", len(re.findall(r"<canvas", s)))
print("drill bars:", len(re.findall(r'class="drillbar"', s)))
print("probe present:", (OUT / "matrix_probe.js").exists())
