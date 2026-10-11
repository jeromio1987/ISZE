"""Open a deck in PowerPoint itself, export every slide to PNG and measure text fit.

usage: python qa_render.py <deck.pptx> <out_dir>
A text box fails when PowerPoint's own rendered text is taller than the box (clipping / spill) or a single-line
label is wider than its box. Shapes outside the slide also fail. Writes slide_NN.png and fit_report.json.
Exit code 1 if anything fails.
"""
import json
import sys
from pathlib import Path

import win32com.client

deck = Path(sys.argv[1]).resolve()
qa = Path(sys.argv[2]).resolve()
qa.mkdir(parents=True, exist_ok=True)
for old in qa.glob("slide_*.png"):
    old.unlink()

app = win32com.client.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(str(deck), True, False, False)  # read-only, no window
W, H = pres.PageSetup.SlideWidth, pres.PageSetup.SlideHeight
fails, checked = [], 0
TOL = 1.5  # points
for slide in pres.Slides:
    n = slide.SlideIndex
    slide.Export(str(qa / f"slide_{n:02d}.png"), "PNG", 1920, 1080)
    for shp in slide.Shapes:
        l, t, w, h = shp.Left, shp.Top, shp.Width, shp.Height
        if l < -TOL or t < -TOL or l + w > W + TOL or t + h > H + TOL:
            fails.append({"slide": n, "shape": shp.Name, "issue": "outside slide"})
        if not shp.HasTextFrame or not shp.TextFrame.HasText:
            continue
        checked += 1
        tf = shp.TextFrame2
        rng = tf.TextRange
        inner_h = h - tf.MarginTop - tf.MarginBottom
        inner_w = w - tf.MarginLeft - tf.MarginRight
        if rng.BoundHeight > inner_h + TOL:
            fails.append({"slide": n, "shape": shp.Name, "issue": "text taller than box",
                          "text_pt": round(rng.BoundHeight, 1), "box_pt": round(inner_h, 1), "text": rng.Text[:60]})
        if rng.BoundWidth > inner_w + TOL:
            legacy = shp.TextFrame.TextRange
            widest, i = 0.0, 1
            while i < 60:
                ln = legacy.Lines(i, 1)
                if ln.Length == 0:
                    break
                widest = max(widest, ln.TrimText().BoundWidth)
                i += 1
            if widest > inner_w + TOL:
                fails.append({"slide": n, "shape": shp.Name, "issue": "text wider than box",
                              "text_pt": round(widest, 1), "box_pt": round(inner_w, 1), "text": rng.Text[:60]})
slides = pres.Slides.Count
pres.Close()
report = {"deck": str(deck), "slides": slides, "text_shapes_checked": checked, "failures": fails}
(qa / "fit_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"slides": slides, "text_shapes_checked": checked, "failures": len(fails)}))
for f in fails:
    print(f)
sys.exit(1 if fails else 0)
