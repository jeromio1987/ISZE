from pathlib import Path
import json

INBOX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
b64 = INBOX.joinpath("_eq_scraper_b64.txt").read_text().strip()
inject = (
    "(function(){var s=atob("
    + json.dumps(b64)
    + "); var el=document.createElement('script'); el.textContent=s; "
    "document.documentElement.appendChild(el); return typeof window.__eqDoubtLookup;})()"
)
INBOX.joinpath("_eq_inject_expr.js").write_text(inject, encoding="utf-8")
print("inject_len", len(inject))
for i in range(3):
    pns = json.loads(INBOX.joinpath(f"_eq_shard_{i}.json").read_text())
    start = (
        "(function(){window.__EQ_DOUBT_OPEN_PNS="
        + json.dumps(pns)
        + "; window.__eqDoubtResults=[]; "
        "window.__eqDoubtRun(window.__EQ_DOUBT_OPEN_PNS,2200); "
        "return {started:true,n:"
        + str(len(pns))
        + "};})()"
    )
    INBOX.joinpath(f"_eq_start_expr_{i}.js").write_text(start, encoding="utf-8")
    print(i, "start_len", len(start), "n", len(pns))
