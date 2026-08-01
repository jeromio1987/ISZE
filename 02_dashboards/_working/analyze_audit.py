import json
from collections import Counter
from pathlib import Path

r = json.loads(Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_working\audit\report.json").read_text(encoding="utf-8"))
err_pat = Counter()
for item in r["results"]:
    if item.get("status") not in ("broken", "error"):
        continue
    probe = item.get("probe") or {}
    errs = probe.get("consoleErrors") or []
    print("\n==", item["file"], item.get("issues"))
    for e in errs[:6]:
        print("  ", e[:240])
        key = e.split(":", 1)[-1].strip()[:100]
        err_pat[key] += 1
    if not errs:
        print(
            "  (no console) blankCanvases=",
            probe.get("blankCanvases"),
            "blankSvgs=",
            probe.get("blankSvgs"),
            "typeofChart=",
            probe.get("typeofChart"),
            "typeofEcharts=",
            probe.get("typeofEcharts"),
            "bodyLen=",
            probe.get("bodyLen"),
        )
print("\n==== TOP ERROR PATTERNS ====")
for k, v in err_pat.most_common(25):
    print(v, k)
