import json
from pathlib import Path

d = json.loads(
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_eq_inject_chunks.json").read_text(
        encoding="utf-8"
    )
)
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_cdp_steps")
out.mkdir(exist_ok=True)
(out / "step_00_reset.js").write_text("window.__EQB64=''; 'reset'", encoding="utf-8")
for i, c in enumerate(d["chunks"]):
    expr = f"window.__EQB64=(window.__EQB64||'')+{json.dumps(c)}; window.__EQB64.length"
    (out / f"step_{i+1:02d}_append.js").write_text(expr, encoding="utf-8")
final = (
    "(function(){var s=atob(window.__EQB64); var el=document.createElement('script'); "
    "el.textContent=s; document.documentElement.appendChild(el); "
    "return typeof window.__eqDoubtLookup;})()"
)
(out / "step_99_eval.js").write_text(final, encoding="utf-8")

# also write start exprs into 91_build
INBOX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
for i in range(3):
    pns = json.loads((INBOX / f"_eq_shard_{i}.json").read_text(encoding="utf-8"))
    start = (
        "(function(){window.__EQ_DOUBT_OPEN_PNS="
        + json.dumps(pns)
        + "; window.__eqDoubtResults=[]; "
        "window.__eqDoubtRun(window.__EQ_DOUBT_OPEN_PNS,2200); "
        "return {started:true,n:"
        + str(len(pns))
        + "};})()"
    )
    (out / f"start_shard_{i}.js").write_text(start, encoding="utf-8")

print("OK", out)
for p in sorted(out.glob("*.js")):
    print(p.name, p.stat().st_size)
