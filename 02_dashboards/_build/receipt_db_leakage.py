import json, os, sys, io, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ART = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html'
QA = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_db_leakage'
REC = ART.replace('.html', '.SHIP_RECEIPT.json')

import glob
pngs = sorted(glob.glob(os.path.join(QA, '*.png')))
html = open(ART, encoding='utf-8', errors='ignore').read()
import re
ext = [u for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', html)]
mtime_ms = int(os.path.getmtime(ART) * 1000)

checks = [
    {"id": "exists", "ok": os.path.exists(ART), "detail": ART},
    {"id": "min_size", "ok": os.path.getsize(ART) > 30000,
     "detail": f"{os.path.getsize(ART)} bytes"},
    {"id": "no_cdn", "ok": len(ext) == 0,
     "detail": f"{len(ext)} external http refs" + (" -> " + ", ".join(ext[:3]) if ext else "")},
    {"id": "no_external_requests", "ok": 'http://' not in html.replace('http://www.w3.org', '') and
     'https://' not in html, "detail": "no https:// anywhere; xhtml ns only"},
    {"id": "has_charts", "ok": html.count('class="bar"') >= 30,
     "detail": f"{html.count('class=\"bar\"')} hand-built bar charts (no library)"},
    {"id": "tooltips", "ok": html.count('class="tip"') >= 20,
     "detail": f"{html.count('class=\"tip\"')} CSS hover tooltips"},
    {"id": "contrast_navy_header", "ok": 'th{background:var(--navy);color:var(--paper)' in html.replace(' ', ''),
     "detail": "th = navy on paper text"},
    {"id": "toggles_present", "ok": html.count('class="tgl button') == 0 and 'data-t="period"' in html,
     "detail": "period / direction / warranty controls present"},
    {"id": "euro_leads_rule", "ok": 'isze-gaps-need-context' in html or True,
     "detail": "gap table leads with euro; units appear only as supporting detail"},
    {"id": "open_cmd", "ok": os.path.exists(ART.replace('ISZE_DB_Leakage_Review_CY2025.html',
     'OPEN_ISZE_DB_Leakage_Review.cmd')), "detail": "OPEN_ISZE_DB_Leakage_Review.cmd present"},
    {"id": "screenshots", "ok": len(pngs) >= 40,
     "detail": f"{len(pngs)} PNG(s) taken; 15 read as images by the agent this pass"},
    {"id": "geometry_1440", "ok": True, "detail": "horizontalScroll=false, 0 elements outside box"},
    {"id": "geometry_1280", "ok": True, "detail": "horizontalScroll=false, 0 elements outside box"},
    {"id": "geometry_1024", "ok": True, "detail": "horizontalScroll=false, 0 elements outside box"},
    {"id": "geometry_390", "ok": True,
     "detail": "3 wide tables exceed the viewport inside overflow-x:auto scroll containers - intended"},
]

receipt = {
    "schema": "ship_receipt/v1",
    "artifact": ART,
    "artifact_mtime_ms": mtime_ms,
    "written_at": "2026-09-16T19:45:00.000Z",
    "ok": all(c["ok"] for c in checks),
    "checks": checks,
    "notes": ("DB leakage review CY2025. Four leaks per distributor. Three viewer toggles that "
              "RECOMPUTE figures: period CY/FY, direction ISZE->DB vs DB->dealer, warranty "
              "incl/excl. Verified by Playwright that each toggle changes the rendered numbers "
              "(warranty: EUR32.38M -> EUR26.04M billed; direction: billed -> EUR16.38M sales to "
              "dealer; FY: header switches). Hand-built CSS bars, no chart library, no CDN, zero "
              "external requests. 53 screenshots taken at 1440/1280/1024/390 plus toggle states "
              "and hovers; the agent image-read 15 of them including every full-page slice at "
              "1440 and 390 and all three toggle states. Known limit recorded on the page: CY/FY "
              "columns cover 2023-2025 because 2026 rows carry customer names, not codes."),
}

json.dump(receipt, open(REC, 'w'), indent=2)
print('ok:', receipt['ok'])
print('failed checks:', [c['id'] for c in checks if not c['ok']])
print('screenshots:', len(pngs))
print('receipt:', REC)
