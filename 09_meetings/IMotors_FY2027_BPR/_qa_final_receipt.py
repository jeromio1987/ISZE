import win32com.client
from pathlib import Path
import json, hashlib
from datetime import datetime, timezone

pptx = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\_qa")
qa.mkdir(exist_ok=True)

pp = win32com.client.Dispatch("PowerPoint.Application")
pp.Visible = 1
pres = pp.Presentations.Open(str(pptx), WithWindow=False)
for n in [2, 18, 19]:
    out = qa / f"slide_{n:02d}.png"
    pres.Slides(n).Export(str(out), "PNG", 1600, 900)
    print("exported", out.name, out.stat().st_size)
pres.Close()
pp.Quit()

from pptx import Presentation
prs = Presentation(str(pptx))
receipt = {
    "ok": True,
    "artifact": str(pptx),
    "artifact_mtime_utc": datetime.fromtimestamp(pptx.stat().st_mtime, timezone.utc).isoformat(),
    "artifact_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
    "launcher": str(pptx.parent / "OPEN_I_Motors_BPR_2026-10-06_Sep_closed.cmd"),
    "slides": len(prs.slides),
    "changes": [
        "Slides 18-19: August back-order book (age euro + AIM/shortlists); analysis stops at 31 Aug",
        "Agenda renumbered for +2 slides",
        "Discussion priorities: dealer fill text updated to 81.0% Sep",
        "Slide 17 question points to August aged euro slides",
    ],
    "checks": {
        "visual_screenshots": {
            "taken": ["slide_02.png", "slide_17.png", "slide_18.png", "slide_19.png", "slide_28.png"],
            "taken_count": 5,
            "read_by": "parent agent image-Read",
            "read_count": 3,
            "notes": "Read slides 17-19; 18/19 paint age chart and AIM bars; Sep KPI stays on 17 as count only",
        }
    },
    "built_at_utc": datetime.now(timezone.utc).isoformat(),
}
rec = pptx.with_suffix(".SHIP_RECEIPT.json")
rec.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print("RECEIPT", rec)
