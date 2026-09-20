import json
from pathlib import Path

d = json.loads(
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_inject_chunks_v2.json").read_text(
        encoding="utf-8"
    )
)
b64 = "".join(d["chunks"])
expr = (
    "(function(){try{eval(atob("
    + json.dumps(b64)
    + ")); return typeof window.__eqDoubtLookup;}catch(e){return 'ERR:'+e.message;}})()"
)
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\eq_inject_tmp\oneshot_eval.js")
out.write_text(expr, encoding="utf-8")
print(len(b64), len(expr), out)
