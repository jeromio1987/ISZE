import base64
import json
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
q = json.loads((DER / "_eq_hit_queue_20261007.json").read_text(encoding="utf-8"))
done = set()
for line in (DER / "_eq_hit_results_20261007.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        done.add(json.loads(line)["pn"])
remain = [r["pn"] for r in q["queue"] if r["pn"] not in done]
(DER / "_eq_hit_remain_pns_20261007.json").write_text(json.dumps(remain), encoding="utf-8")
arr = json.dumps(remain)
expr = (
    "(function(){window.__EQ_DOUBT_OPEN_PNS="
    + arr
    + ";window.__eqDoubtResults=window.__eqDoubtResults||[];"
    "window.__eqDoubtResults.length=0;"
    "window.__eqDoubtRun(window.__EQ_DOUBT_OPEN_PNS,400);"
    f"return {{started:true,n:{len(remain)}}};" + "})()"
)
(DER / "_eq_hit_start_remain_expr_20261007.js").write_text(expr, encoding="utf-8")

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
(DER / "_eq_hit_inject_expr_20261007.js").write_text(iexpr, encoding="utf-8")
print("done", len(done), "remain", len(remain), "inject", len(iexpr), "start", len(expr))
