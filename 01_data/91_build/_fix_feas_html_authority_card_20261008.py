# -*- coding: utf-8 -*-
from pathlib import Path
import re
import runpy

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_build_dlod_feasibility_html_20261008.py")
t = p.read_text(encoding="utf-8")
card = """
<div class="card" style="margin-bottom:18px">
  <h2>Authority — MOA and margin layers</h2>
  <p class="q">Signed agreement vs mail vs Duncan register — do not blend</p>
  <table>
    <thead><tr><th>Layer</th><th>Figure / rule</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Signed MOA</td><td>EUR 30,000 if ITUK provides the activity record. <b>No margin / %GM</b> in the agreement.</td><td>FY26_ITUK_DLOD_2026-03.docx.pdf</td></tr>
      <tr><td>ISZE GP on programme deals</td><td>~50%</td><td>Jerome → Yoshimoto (Mar 2026 DocuSign thread)</td></tr>
      <tr><td>ITUK normal / retained</td><td>~47% before offer · ~41–43% median after</td><td>Duncan deal file</td></tr>
    </tbody>
  </table>
</div>
"""
marker = "<h2>How the money moves</h2>"
if "Authority — MOA and margin layers" not in t:
    if marker not in t:
        raise SystemExit("marker missing")
    t = t.replace(marker, card + marker, 1)
    p.write_text(t, encoding="utf-8")
    print("builder card inserted")
else:
    print("already present")

runpy.run_path(str(p), run_name="__main__")
html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\DLOD_NETWORK_FEASIBILITY_2026-10-08.html").read_text(encoding="utf-8")
for k in ["Authority — MOA", "FY26_ITUK_DLOD", "activity record", "~50%", "Yoshimoto", "41–43%", "~47%"]:
    print(k, k in html)
print("CDN", bool(re.search(r"(?i)cdn\.|unpkg|jsdelivr|googleapis", html)))
print("Chart", "Chart" in html)
print("tbody tr", len(re.findall(r"<tr", html)))
