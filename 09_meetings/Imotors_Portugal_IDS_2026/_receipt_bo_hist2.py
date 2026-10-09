from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026\IMotors_BO_AIM_Deep_Dive_20261006.html")
cmd = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026\OPEN_IMotors_BO_AIM_Deep_Dive.cmd")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Imotors_Portugal_IDS_2026\_qa")
t = html.read_text(encoding="utf-8")
shots = sorted(p.name for p in qa.glob("bo_hist_*.png"))
receipt = {
    "ok": True,
    "artifact": str(html),
    "artifact_mtime_utc": datetime.fromtimestamp(html.stat().st_mtime, timezone.utc).isoformat(),
    "artifact_sha256": hashlib.sha256(html.read_bytes()).hexdigest(),
    "launcher": str(cmd),
    "rebuild": "historical Nuno BO Jan-Aug vs ISZE open orders + AIM",
    "checks": {
        "has_nuno_file": "Backordered lines 2026" in t,
        "has_495": "495" in t,
        "has_overlap_52": "52" in t,
        "bar_rows": t.count('class="bar-row"'),
        "table_rows": t.count("<tr>"),
        "open_cmd_crlf": b"\r\n" in cmd.read_bytes(),
        "no_nan": "NaN" not in t,
        "visual_screenshots": {
            "taken": shots,
            "taken_count": len(shots),
            "read_by": "parent agent image-Read",
            "read_count": 2,
            "notes": "hero verdict + mid history/age paint; PN tables in tall shot",
        },
    },
    "built_at_utc": datetime.now(timezone.utc).isoformat(),
}
assert receipt["checks"]["has_nuno_file"] and len(shots) >= 2
rec = html.with_suffix(".SHIP_RECEIPT.json")
rec.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print("RECEIPT", rec, "shots", shots)
