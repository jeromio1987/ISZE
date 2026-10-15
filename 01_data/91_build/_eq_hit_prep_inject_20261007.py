import base64
import json
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
src = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\eq_inject_tmp\decoded_scraper_fast_20261007.js"
).read_text(encoding="utf-8")
b64 = base64.b64encode(src.encode()).decode()
(DER / "_eq_hit_scraper_b64_20261007.txt").write_text(b64, encoding="utf-8")
expr = (
    "(function(){var s=atob("
    + json.dumps(b64)
    + "); var el=document.createElement('script'); el.textContent=s; "
    "document.documentElement.appendChild(el); return typeof window.__eqDoubtLookup;})()"
)
(DER / "_eq_hit_inject_expr_20261007.js").write_text(expr, encoding="utf-8")
print("b64_len", len(b64), "expr_len", len(expr))
