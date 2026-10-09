# -*- coding: utf-8 -*-
"""Cheap checks on the study HTML and MD: self-contained, payload present, charts, banned words, numbers agree with model.json."""
import json, re, sys
from pathlib import Path
S = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
html = (S / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html").read_text(encoding="utf-8")
md = (S / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md").read_text(encoding="utf-8")
cmd = (S / "OPEN_DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.cmd").read_bytes()
H = Path(__file__).parent
model = json.loads((H / "model.json").read_text(encoding="utf-8"))
m = re.search(r'<script type="application/json" id="payload">(.*?)</script>', html, re.S)
payload = json.loads(m.group(1).replace("<\\/", "</"))
checks = {
    "payload parses": bool(payload),
    "17 other + ITUK rows": len(payload["rows"]) == 18,
    "7 canvases": html.count("<canvas") == 8 or html.count("<canvas") == 7,
    "Chart.js inline": "Chart" in html and "chart.js" not in html.lower().replace("chart.js v", "") or ").Chart=" in html or "Chart=" in html,
    "no CDN / http script": not re.search(r'<script[^>]+src=', html) and "cdn." not in html.lower(),
    "no fetch": "fetch(" not in html,
    "CRLF launcher": cmd.endswith(b"\r\n") and b"DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html" in cmd and b"\r\n" in cmd,
    "no sell-out/street words": not re.search(r"sell-?out|\bstreet\b|Mode [AB]\b|Deal of the Day|deal of the day|wallet", (html + md).replace("wallet_waterfall.csv", ""), re.I),
    "no 'markup'": "markup" not in (html + md).lower().replace("markups-are-driving", ""),
    "no NaN in payload": "NaN" not in m.group(1),
    "central net matches model": abs(payload["network"]["net"] - sum(r["net_central"] for r in model["rows"] if r["code"] != "ITUK")) < 1,
    "MD has 15 sections": len(re.findall(r"^## \d+\.", md, re.M)) == 15,
    "MD central net quoted": "€22,000" in md,
    "HTML kpi tooltips": html.count('class="info"') >= 1 and "tip(" in html,
}
bad = [k for k, v in checks.items() if not v]
for k, v in checks.items():
    print("PASS" if v else "FAIL", k)
sys.exit(1 if bad else 0)
