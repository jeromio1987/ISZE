import json
from pathlib import Path

d = json.loads(
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_eq_inject_chunks.json").read_text(
        encoding="utf-8"
    )
)
b64 = "".join(d["chunks"])
# Use eval instead of script tag — more reliable across Glass tabs
expr = (
    "(function(){try{eval(atob("
    + json.dumps(b64)
    + ")); return typeof window.__eqDoubtLookup;}catch(e){return 'ERR:'+e.message;}})()"
)
Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_cdp_steps\inject_eval.js").write_text(
    expr, encoding="utf-8"
)
print(len(expr))
