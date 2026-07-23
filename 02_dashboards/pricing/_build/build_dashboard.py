"""Assemble the self-contained Pricing Action Map HTML (no CDN — Regel 0)."""
from pathlib import Path
import json
import re

HERE = Path(__file__).parent
OUT = HERE.parent / "ISZE_Pricing_Action_Map.html"
CHARTJS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Preparation Meetings\PMS_Top10\assets\chart.umd.min.js")

tpl = (HERE / "template.html").read_text(encoding="utf-8")
lib = CHARTJS.read_text(encoding="utf-8")
lib = re.sub(r"//# sourceMappingURL=\S+", "", lib)
data = json.dumps(json.loads((HERE / "pricing_action_map.json").read_text(encoding="utf-8")),
                  separators=(",", ":"))
# JSON inside <script type="application/json"> — escape closing tags
data = data.replace("</", "<\\/")

html = tpl.replace("/*CHARTJS*/", lib).replace("/*DATA*/", data)
OUT.write_text(html, encoding="utf-8")

ext = re.findall(r'(?:src|href)\s*=\s*["\']https?://', html)
print(f"written {OUT} ({len(html)/1e6:.2f} MB) | external src/href refs: {len(ext)}")
assert not ext, "CDN reference found — must be zero"
