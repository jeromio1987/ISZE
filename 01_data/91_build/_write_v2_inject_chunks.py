import json
from pathlib import Path

d = json.loads(
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_inject_chunks_v2.json").read_text(
        encoding="utf-8"
    )
)
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_cdp_steps")
out.mkdir(exist_ok=True)
(out / "v2_reset.js").write_text("window.__EQB64=''; 'reset'", encoding="utf-8")
for i, c in enumerate(d["chunks"]):
    expr = "window.__EQB64=(window.__EQB64||'')+" + json.dumps(c) + "; window.__EQB64.length"
    (out / f"v2_chunk_{i}.js").write_text(expr, encoding="utf-8")
    print(i, len(c))
(out / "v2_eval.js").write_text(
    "(function(){try{eval(atob(window.__EQB64)); return typeof window.__eqDoubtLookup;}"
    "catch(e){return 'ERR:'+e.message;}})()",
    encoding="utf-8",
)
print("ok", out)
