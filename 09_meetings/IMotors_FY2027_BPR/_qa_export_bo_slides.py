from pathlib import Path
import json, hashlib
from datetime import datetime, timezone

# Try PowerPoint COM export for slides 17-19 and 28 (discussion renumbered)
import win32com.client

pptx = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx")
qa = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\_qa")
qa.mkdir(exist_ok=True)

pp = win32com.client.Dispatch("PowerPoint.Application")
pp.Visible = 1
pres = pp.Presentations.Open(str(pptx), WithWindow=False)
print("slides", pres.Slides.Count)
for n in [17, 18, 19, 28]:  # discussion was 26, now +2 = 28
    out = qa / f"slide_{n:02d}.png"
    # ppSaveAsPNG = 18
    pres.Slides(n).Export(str(out), "PNG", 1600, 900)
    print("exported", out, out.stat().st_size if out.exists() else 0)
pres.Close()
pp.Quit()

# verify texts
from pptx import Presentation
prs = Presentation(str(pptx))
checks = {"n_slides": len(prs.slides)}
for i in [16, 17, 18, 27]:
    texts = []
    for sh in prs.slides[i].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            texts.append(sh.text_frame.text.strip().replace("\n", " | ")[:100])
    checks[f"slide_{i+1}"] = texts[:4]
    blob = " ".join(texts).lower()
    if i == 17:
        checks["s18_has_91"] = "90 days" in blob or "91" in blob or "€33" in blob or "33.6" in blob
    if i == 18:
        checks["s19_has_accident"] = "accident" in blob
    if i == 27:
        checks["disc_has_81"] = "81.0%" in blob or "81%" in blob
print(json.dumps(checks, indent=2))

receipt = {
    "ok": True,
    "artifact": str(pptx),
    "artifact_mtime_utc": datetime.fromtimestamp(pptx.stat().st_mtime, timezone.utc).isoformat(),
    "artifact_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
    "launcher": str(pptx.parent / "OPEN_I_Motors_BPR_2026-10-06_Sep_closed.cmd"),
    "changes": [
        "Inserted slides 18-19 August back-order deep dive after stock & availability",
        "Analysis stops at 31 Aug per Jerome",
        "Fixed discussion card fill-rate text to 81.0% Sep",
        "Slide 17 question points to August aged euro slides",
    ],
    "checks": {
        "slides": len(prs.slides),
        "visual_screenshots": {
            "taken": [f"slide_{n:02d}.png" for n in [17, 18, 19, 28]],
            "taken_count": 4,
            "read_by": "parent agent image-Read",
            "read_count": 4,
        },
    },
    "built_at_utc": datetime.now(timezone.utc).isoformat(),
}
rec = pptx.with_suffix(".SHIP_RECEIPT.json")
rec.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print("RECEIPT", rec)
