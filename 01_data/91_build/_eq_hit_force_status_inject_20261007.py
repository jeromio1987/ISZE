import base64
import json
import re
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
p = DER / "_eq_hit_inject_expr_20261007.js"
src = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\eq_inject_tmp\decoded_scraper_status_20261007.js"
).read_text(encoding="utf-8")
b64 = base64.b64encode(src.encode()).decode()
iexpr = (
    "(function(){var s=atob("
    + json.dumps(b64)
    + "); var el=document.createElement('script'); el.textContent=s; "
    "document.documentElement.appendChild(el); return typeof window.__eqDoubtLookup;})()"
)
p.write_text(iexpr, encoding="utf-8")
m = re.search(r'atob\("([^"]+)"\)', p.read_text(encoding="utf-8"))
decoded = base64.b64decode(m.group(1)).decode("utf-8")
print(decoded.splitlines()[0])
print("inject_len", len(iexpr))
