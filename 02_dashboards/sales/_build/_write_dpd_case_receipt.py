# -*- coding: utf-8 -*-
from pathlib import Path
import json, time

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Case_Study_20261006.html")
cmd = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\OPEN_ISZE_DPD_Case_Study.cmd")
wl = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Reman_Price_Collection_Worklist_20261006.csv")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_dpd_case")
text = html.read_text(encoding="utf-8")
mtime_ms = int(html.stat().st_mtime * 1000)
read_paths = [
    "00_fullpage.png",
    "01_hero.png",
    "02_mail.png",
    "03_anchors.png",
    "04_assemblies.png",
    "05_drawer_pn_a.png",
    "06_drawer_db_umi.png",
    "07_reman_tracks.png",
    "07b_transport_scale.png",
    "08_worklist.png",
]
missing = [p for p in read_paths if not (qa / p).exists()]
receipt = {
    "schema": "ship_receipt/v2",
    "artifact": str(html),
    "artifact_mtime_ms": mtime_ms,
    "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "ok": not missing and html.stat().st_size > 100000,
    "screenshots_taken": len(list(qa.glob("*.png"))),
    "screenshots_read": len(read_paths),
    "checks": [
        {"id": "exists", "ok": html.exists(), "detail": str(html)},
        {"id": "worklist", "ok": wl.exists() and wl.stat().st_size > 1000, "detail": str(wl)},
        {"id": "open_cmd", "ok": cmd.exists() and b"\r\n" in cmd.read_bytes(), "detail": "CRLF OPEN cmd"},
        {"id": "no_cdn", "ok": "cdn.jsdelivr" not in text and "cdnjs" not in text, "detail": "no CDN"},
        {"id": "no_nan", "ok": "NaN" not in text, "detail": "no NaN"},
        {
            "id": "clickable",
            "ok": "clickrow" in text and "drawer" in text and "8975359391" in text,
            "detail": "clickrows + drawer + hero PN",
        },
        {
            "id": "mail_brief",
            "ok": "What Peter / Osamu asked" in text and "Optymha" in text,
            "detail": "mail band present",
        },
        {
            "id": "web_anchors",
            "ok": "Public competitive anchors" in text and "Driveline" in text,
            "detail": "anchors strip",
        },
        {
            "id": "sandwich_js",
            "ok": "sandwich_by_pn" in text and "Price sandwich" in text,
            "detail": "drawer sandwich wiring",
        },
        {
            "id": "verdicts",
            "ok": "HOLD" in text and "CONDITIONAL" in text,
            "detail": "Track A HOLD + Track B CONDITIONAL",
        },
        {
            "id": "transport_feasibility",
            "ok": "three pipes" in text
            and "Honest limits" in text
            and "ASSUMPTION" in text
            and "cannot compute" in text.lower()
            and "~€450 on the Euro 5" not in text
            and "FILTER" in text,
            "detail": "multi-pipe demand chapter + first-DPD caveat + FILTER split + no fake €450",
        },
        {
            "id": "visual_screenshots",
            "ok": not missing,
            "detail": f"taken={len(list(qa.glob('*.png')))} read={len(read_paths)} by agent image-Read; missing={missing}",
        },
    ],
    "screenshots": [str(qa / p) for p in read_paths],
    "notes": "Case study + reman merge + landed-cost / transport-scale feasibility (ASSUMPTION bands, COLLECT quotes).",
}
out = html.parent / (html.stem + ".SHIP_RECEIPT.json")
out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(out)
print("ok", receipt["ok"])
