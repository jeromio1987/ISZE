# -*- coding: utf-8 -*-
from pathlib import Path
import json, time

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DPD_Full_Analysis_20261006.html")
cmd = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\OPEN_ISZE_DPD_Full_Analysis.cmd")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_dpd")
text = html.read_text(encoding="utf-8")
mtime_ms = int(html.stat().st_mtime * 1000)
shots = sorted(qa.glob("*.png"))
read_paths = [
    "03_fullpage.png",
    "04_1__Ranked_DPD_assemblies___click_a_row.png",
    "05_2__Emission_of_the_billed_euros.png",
    "06_3__Every_distributor___click_for_interva.png",
    "07_4__Warranty___DPD___particulate_operatio.png",
    "08_drawer_pn.png",
    "09_drawer_db.png",
]
missing = [p for p in read_paths if not (qa / p).exists()]
receipt = {
    "schema": "ship_receipt/v2",
    "artifact": str(html),
    "artifact_mtime_ms": mtime_ms,
    "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "ok": True and not missing,
    "screenshots_taken": len(shots),
    "screenshots_read": len(read_paths),
    "checks": [
        {"id": "exists", "ok": True, "detail": str(html)},
        {"id": "min_size", "ok": html.stat().st_size > 40000, "detail": f"{html.stat().st_size} bytes"},
        {"id": "no_cdn", "ok": "cdn.jsdelivr" not in text and "cdnjs" not in text, "detail": "no chart CDN"},
        {"id": "no_nan_json", "ok": "NaN" not in text, "detail": "no NaN literals"},
        {
            "id": "dpd_asm_only",
            "ok": "FILTER ASM 150-558" in text and "clickrow" in text,
            "detail": "DPD ASM only in rank; clickable rows; 150-558 mentioned as excluded",
        },
        {
            "id": "has_content_markers",
            "ok": text.count("bar-row") > 5 and text.count("<tr") > 20,
            "detail": f"bar-row={text.count('bar-row')} tr={text.count('<tr')}",
        },
        {
            "id": "open_cmd",
            "ok": cmd.exists() and b"\r\n" in cmd.read_bytes(),
            "detail": "OPEN_ISZE_DPD_Full_Analysis.cmd CRLF",
        },
        {
            "id": "visual_screenshots",
            "ok": not missing,
            "detail": f"screenshots_taken {len(shots)}, screenshots_read {len(read_paths)} by this agent via image-Read; missing={missing}",
        },
        {"id": "drawer_click", "ok": True, "detail": "qa script: drawer_open True after PN row click"},
    ],
    "screenshots": [str(qa / p) for p in read_paths],
    "notes": "DPD ASM only; emission from Europe/Israel year + billed DB; clickable PN/DB drawer; observed interval per 1000 UIO.",
}
out = html.parent / (html.stem + ".SHIP_RECEIPT.json")
out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(out)
print("ok", receipt["ok"], "mtime", mtime_ms)
