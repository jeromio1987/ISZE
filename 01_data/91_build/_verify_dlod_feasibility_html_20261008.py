# -*- coding: utf-8 -*-
from pathlib import Path
import json
import re

html_path = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\DLOD_NETWORK_FEASIBILITY_2026-10-08.html"
)
cmd_path = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\OPEN_DLOD_NETWORK_FEASIBILITY_2026-10-08.cmd"
)
text = html_path.read_text(encoding="utf-8")
cmd = cmd_path.read_bytes()
print("HTML bytes", html_path.stat().st_size)
print("CMD bytes", len(cmd), "CRLF", b"\r\n" in cmd)
print("CMD text:", cmd.decode("ascii").replace("\r", "\\r").replace("\n", "\\n"))

checks = {
    "payload script": 'id="payload"' in text,
    "Chart.js inline": ").Chart=e()" in text or "self).Chart=e()" in text,
    "chartRegion": 'id="chartRegion"' in text,
    "chartPilot": 'id="chartPilot"' in text,
    "chartEnv": 'id="chartEnv"' in text,
    "scorecard table": 'id="scorecard"' in text,
    "envTable": 'id="envTable"' in text,
    "programme name": "Don't Lose the Deal" in text,
    "no Deal of the Day": "Deal of the Day" not in text,
    "EUR 30k": "30000" in text,
    "218 cases": "218" in text,
    "GBP support": "54921" in text,
    "amber unknowns": 'id="unknowns"' in text,
    "kpi tips": 'class="info"' in text,
    "no Mode A/B": "Mode A" not in text and "Mode B" not in text,
    "no sell-out": "sell-out" not in text.lower() and "sellout" not in text.lower(),
    "no CDN": "cdn.jsdelivr" not in text and "cdnjs" not in text,
    "new Chart x3": text.count("new Chart(") == 3,
    "canvas x3": text.count("<canvas") == 3,
}
failed = 0
for k, v in checks.items():
    print(("PASS" if v else "FAIL"), k)
    if not v:
        failed += 1

m = re.search(
    r'<script type="application/json" id="payload">(.*?)</script>', text, re.S
)
assert m, "payload missing"
payload = json.loads(m.group(1))
print(
    "payload envelopes",
    len(payload["envelopes"]),
    "scorecard",
    len(payload["scorecard"]),
    "unknowns",
    len(payload["unknowns"]),
)
print(
    "pilot",
    payload["kpis"]["pilot_envelope_eur_lo"],
    payload["kpis"]["pilot_envelope_eur_hi"],
)
print("network 0.5%", payload["kpis"]["pct05_network_eur"])
print("competitor", payload["kpis"]["competitor_price_filled"])
raise SystemExit(failed)
