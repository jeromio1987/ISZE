import json
from pathlib import Path

d = json.loads(
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_eq_inject_chunks.json").read_text(
        encoding="utf-8"
    )
)
b64 = "".join(d["chunks"])
expr = (
    "(function(){var s=atob("
    + json.dumps(b64)
    + "); var el=document.createElement('script'); el.textContent=s; "
    "document.documentElement.appendChild(el); return typeof window.__eqDoubtLookup;})()"
)
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_cdp_steps\inject_oneshot.js")
out.write_text(expr, encoding="utf-8")
print(len(expr))
print(expr[:80])
print(expr[-60:])
