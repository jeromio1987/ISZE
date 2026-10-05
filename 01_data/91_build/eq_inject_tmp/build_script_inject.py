import base64
import json
from pathlib import Path

src_path = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_eq_hit_overnight_scraper_20260919.js")
src = src_path.read_text(encoding="utf-8")
# Drop trailing string literal; keep functions only
if src.rstrip().endswith('"scraper_v2_ok";'):
    src = src.rstrip()[: -len('"scraper_v2_ok";')].rstrip() + "\n"
b64 = base64.b64encode(src.encode("utf-8")).decode("ascii")
# Prefer script-tag inject (worked on session 0 earlier)
expr = (
    "(function(){var s=atob("
    + json.dumps(b64)
    + "); var el=document.createElement('script'); el.textContent=s; "
    "document.documentElement.appendChild(el); return typeof window.__eqDoubtLookup;})()"
)
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\eq_inject_tmp\oneshot_script.js")
out.write_text(expr, encoding="utf-8")
print("src_len", len(src), "b64", len(b64), "expr", len(expr))
print("decoded_ok", base64.b64decode(b64).decode("utf-8")[:40])
