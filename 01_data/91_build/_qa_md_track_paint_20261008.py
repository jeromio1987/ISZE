# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
HTML = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.html"
CMD = OUT / "OPEN_ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.cmd"
QA = OUT / "_qa"
QA.mkdir(exist_ok=True)
SHOT = QA / "md_track_business_plan_20261008.png"

t = HTML.read_text(encoding="utf-8")
checks = {
    "bar_rows": t.count("bar-row"),
    "kpi_blocks": t.count('class="kpi'),
    "trs": t.count("<tr>"),
    "payload": 'id="payload"' in t,
    "pilot_stack": "Pilot stack for next week" in t,
    "measurement": "Board measurement" in t,
    "no_script_src": "<script src=" not in t.lower(),
    "cmd_crlf": b"\r\n" in CMD.read_bytes(),
}
print("CHECKS", json.dumps(checks))

chrome_candidates = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
]
chrome = next((p for p in chrome_candidates if p.exists()), None)
if chrome:
    uri = HTML.resolve().as_uri()
    subprocess.run(
        [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            f"--window-size=1400,1800",
            f"--screenshot={SHOT}",
            uri,
        ],
        check=False,
        capture_output=True,
    )
    print("SHOT", SHOT.exists(), SHOT.stat().st_size if SHOT.exists() else 0)
else:
    print("NO_CHROME")

receipt = {
    "ok": all(
        [
            checks["bar_rows"] >= 5,
            checks["kpi_blocks"] >= 6,
            checks["trs"] >= 5,
            checks["payload"],
            checks["no_script_src"],
            checks["cmd_crlf"],
        ]
    ),
    "artifact": str(HTML),
    "checks": checks,
    "screenshot": str(SHOT) if SHOT.exists() else None,
    "as_of": "2026-10-08",
}
(OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.SHIP_RECEIPT.json").write_text(
    json.dumps(receipt, indent=2), encoding="utf-8"
)
print("RECEIPT", receipt["ok"])
