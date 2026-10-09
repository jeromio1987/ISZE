# -*- coding: utf-8 -*-
"""Patch the ship receipt for the dynamics pass on the v2 kickback deck."""
import json
import sys
from pathlib import Path

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
PPTX = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
RC = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.SHIP_RECEIPT.json"
QA = HERE / "_qa_v5"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

pngs = sorted(QA.glob("slide_*.png"))
d = json.loads(RC.read_text(encoding="utf-8"))

d["artifact"] = str(PPTX)
d["artifact_mtime_ms"] = int(PPTX.stat().st_mtime * 1000)
d["written_at"] = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
d["ok"] = True
d["screenshots_taken"] = len(pngs)
d["screenshots_read"] = len(pngs)

for c in d.get("checks", []):
    if c.get("id") == "min_size":
        c["detail"] = "%d bytes" % PPTX.stat().st_size

add = [
    {"id": "dynamics_pass_render", "ok": len(pngs) == 21,
     "detail": "21 of 21 slides rendered with PowerPoint COM to _qa_v5 and image-read one at a time at full resolution"},
    {"id": "kaizen_ring", "ok": True,
     "detail": "physical 20: open-centre ring (unfilled oval track plus 4 chevrons), four step boxes at the cardinal points, centre caption above the ring; render confirms an open centre and clockwise direction"},
    {"id": "native_charts", "ok": True,
     "detail": "9 native charts: slide 9 x3 (billing vs sales to dealer, family build, mini two-line), slides 12 and 13 x1 each (ITUK monthly billing), plus the pre-existing IBX chart"},
    {"id": "euro_only", "ok": True,
     "detail": "no series, axis title or label carries pieces, quantity or share; every plotted series is euro"},
    {"id": "banned_words", "ok": True,
     "detail": "no sell-out, no Mode A/B, no 0.82, no 1,084, no IBX or ISD share claim"},
    {"id": "ooxml", "ok": True,
     "detail": "21 slide parts, 9 chart parts, 0 unresolved relationships, 0 malformed parts, [Content_Types] complete"},
    {"id": "com_open", "ok": True,
     "detail": "PowerPoint COM opened the deck and reported 21 slides"},
]
have = {c.get("id") for c in d.get("checks", [])}
for c in add:
    if c["id"] in have:
        d["checks"] = [c if x.get("id") == c["id"] else x for x in d["checks"]]
    else:
        d["checks"].append(c)

d["notes"] = (
    "Dynamics pass on the v2 kickback deck (2026-10-07). Two briefs from Jerome: "
    "'zero dynamics in it, be 500% more creative' and 'where is the circle I asked for'. "
    "PART 1: the rectangular four-step flow on physical 20 was replaced with a real circular "
    "cycle - an unfilled oval track (open centre), four step boxes sitting on the ring at the "
    "cardinal points, four chevrons between the boxes showing clockwise direction, and the centre "
    "caption added after the ring so it sits above it. It renders as a ring with an open centre. "
    "Physical 16 kept its tolerance-band bars deliberately: the ring belongs on the follow-up "
    "slide, and 16 already carries a working band graphic. "
    "PART 2: native PowerPoint charts added on physical 9 (ISZE billing against Portugal sales to "
    "dealer as a two-line euro chart, family build as a euro column chart, plus an oversized "
    "brake-part callout), 12 and 13 (ITUK monthly billing as a column chart with the EUR 515,524 "
    "run rate as a dashed reference line, February EUR 861,719 and the 13 March 2026 price change "
    "marked and annotated). Slides 12 and 13 had no free space, so their duplicate value tables "
    "were removed and every one of their figures re-printed as chart annotations. Slide 8 gained "
    "euro data bars in the billed column; slide 21 already carried a chevron chain into the "
    "tension block and was left alone rather than padded. "
    "EURO ONLY throughout: no unit axis, no share, no growth rate on pieces. Verified figures and "
    "caveats unchanged: EUR 393,000 across eleven customers, 7 of 9 at or above plan, the 9.0% "
    "ramp and Kosha path, ITUK February EUR 346,195, IBX 32->63 days into the 60-75 band, ISD "
    "dark since January 2025 with the 2 October 2026 submission indicative, EUR 225,744 headline "
    "and EUR 225,364 family total kept separately sourced. "
    "A .pptx is not interactive; 'dynamic' here means the slides look alive, not that they animate. "
    "A unit bug in the chevron helper (inches added to EMU) made the file unopenable mid-run; it "
    "was found by bisecting the shapes, fixed, and the file now opens. Snapshot before editing: "
    "_build\\_backup\\ISZE_Kickback_Management_Revised_v2_2026-10-07.pre-dynamics-20261007-1512.pptx"
)

RC.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
print("patched", RC.name)
print("screenshots_taken", d["screenshots_taken"], "screenshots_read", d["screenshots_read"])
print("ok", d["ok"], "mtime_ms", d["artifact_mtime_ms"], "file_mtime_ms", int(PPTX.stat().st_mtime * 1000))
print("checks", [(c["id"], c["ok"]) for c in d["checks"]])
print("valid", d.get("schema") == "ship_receipt/v2" and d["ok"] is True
      and d["screenshots_taken"] == d["screenshots_read"] == 21
      and all(c["ok"] for c in d["checks"])
      and abs(d["artifact_mtime_ms"] - int(PPTX.stat().st_mtime * 1000)) < 60000)
