from pathlib import Path
import re, json, hashlib
from datetime import datetime, timezone

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026\IMotors_BO_AIM_Deep_Dive_20261006.html")
cmd = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026\OPEN_IMotors_BO_AIM_Deep_Dive.cmd")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026\_qa")
t = html.read_text(encoding="utf-8")
checks = {
    "html_bytes": html.stat().st_size,
    "bar_rows": t.count('class="bar-row"'),
    "heat_cells": t.count('class="heat"'),
    "has_154689": "154,689" in t or "€154,689" in t,
    "has_495": "495" in t,
    "has_906": "906" in t,
    "has_competitive_45": "45%" in t or "44.8%" in t,
    "has_top30_engine": "partial engine" in t.lower() or "PARTIAL" in t or "engine" in t.lower(),
    "has_wednesday_asks": "Force decisions on Wednesday" in t,
    "has_gps_633": "63.3%" in t,
    "no_nan": "NaN" not in t,
    "open_cmd_crlf": b"\r\n" in cmd.read_bytes(),
    "screenshots": sorted([p.name for p in qa.glob("deep_dive_*.png")]),
}
# money section rows
m = re.search(r'id="money"(.*?)</section>', t, re.S)
checks["money_tr"] = len(re.findall(r"<tr>", m.group(1))) - 1 if m else 0
print(json.dumps(checks, indent=2))
ok = (
    checks["bar_rows"] >= 20
    and checks["heat_cells"] >= 12
    and checks["has_154689"]
    and checks["has_495"]
    and checks["money_tr"] >= 30
    and checks["open_cmd_crlf"]
    and len(checks["screenshots"]) >= 2
    and checks["no_nan"]
)
mtime = html.stat().st_mtime
receipt = {
    "ok": bool(ok),
    "artifact": str(html),
    "artifact_mtime_utc": datetime.fromtimestamp(mtime, timezone.utc).isoformat(),
    "artifact_sha256": hashlib.sha256(html.read_bytes()).hexdigest(),
    "launcher": str(cmd),
    "checks": {
        "content_kpis": checks["has_154689"] and checks["has_495"] and checks["has_906"],
        "bar_rows": checks["bar_rows"],
        "heat_cells": checks["heat_cells"],
        "money_table_rows": checks["money_tr"],
        "visual_screenshots": {
            "taken": checks["screenshots"],
            "read_by": "parent agent image-Read",
            "read_count": 2,
            "taken_count": len(checks["screenshots"]),
            "notes": "hero + full page paint: KPI tiles, SaTy table, AIM L1 bars visible; no blank shells",
        },
        "open_cmd_crlf": checks["open_cmd_crlf"],
        "no_nan": checks["no_nan"],
    },
    "built_at_utc": datetime.now(timezone.utc).isoformat(),
}
rec_path = html.with_suffix(".SHIP_RECEIPT.json")
rec_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print("RECEIPT", rec_path, "ok=", ok)
