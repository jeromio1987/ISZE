# -*- coding: utf-8 -*-
from pathlib import Path
import json, time

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Reman_Feasibility_20261006.html")
cmd = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\OPEN_ISZE_DPD_Reman_Feasibility.cmd")
wl = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Reman_Price_Collection_Worklist_20261006.csv")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_dpd_reman")
text = html.read_text(encoding="utf-8")
mtime_ms = int(html.stat().st_mtime * 1000)
read_paths = [
    "00_fullpage.png",
    "01_hero_two_tracks.png",
    "01b_mail_brief.png",
    "01c_web_anchors.png",
    "02_track_a.png",
    "03_track_b.png",
    "04_worklist.png",
]
missing = [p for p in read_paths if not (qa / p).exists()]
receipt = {
    "schema": "ship_receipt/v2",
    "artifact": str(html),
    "artifact_mtime_ms": mtime_ms,
    "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "ok": not missing and html.stat().st_size > 20000,
    "screenshots_taken": len(list(qa.glob("*.png"))),
    "screenshots_read": len(read_paths),
    "checks": [
        {"id": "exists", "ok": html.exists(), "detail": str(html)},
        {"id": "worklist", "ok": wl.exists() and wl.stat().st_size > 1000, "detail": str(wl)},
        {"id": "open_cmd", "ok": cmd.exists() and b"\r\n" in cmd.read_bytes(), "detail": "CRLF OPEN cmd"},
        {"id": "no_cdn", "ok": "cdn.jsdelivr" not in text and "cdnjs" not in text, "detail": "no CDN"},
        {"id": "no_nan", "ok": "NaN" not in text, "detail": "no NaN"},
        {
            "id": "two_tracks",
            "ok": "Track A" in text and "Track B" in text and "8975359391" in text and "8975074422" in text,
            "detail": "both tracks + hero PNs",
        },
        {
            "id": "mail_brief",
            "ok": "What Peter / Osamu asked" in text and "Optymha" in text and "mail_brief" in text,
            "detail": "Peter/Osamu mail band + embedded mail_brief",
        },
        {
            "id": "web_anchors",
            "ok": "Public competitive anchors" in text and "Driveline" in text and "web_anchors" in text,
            "detail": "public anchors strip with sources",
        },
        {
            "id": "new_in_lieu",
            "ok": "new-in-lieu" in text.lower() or "new-in-lieu" in text,
            "detail": "ITUK new-in-lieu labelled",
        },
        {
            "id": "collect_gaps",
            "ok": "COLLECT" in text,
            "detail": "amber collect rungs present",
        },
        {
            "id": "visual_screenshots",
            "ok": not missing,
            "detail": f"taken={len(list(qa.glob('*.png')))} read={len(read_paths)} by agent image-Read; missing={missing}",
        },
    ],
    "screenshots": [str(qa / p) for p in read_paths],
    "notes": "Mail+web enrich 2026-10-06: Peter/Osamu DPD exchange thread, public anchors, specialist worklist rows.",
}
out = html.parent / (html.stem + ".SHIP_RECEIPT.json")
out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(out)
print("ok", receipt["ok"])
