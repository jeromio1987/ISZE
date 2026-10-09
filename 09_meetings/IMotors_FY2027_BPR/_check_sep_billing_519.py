from pptx import Presentation
from pathlib import Path
import re

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IMotors_FY2027_BPR\I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx")
prs = Presentation(str(p))
print("slides", len(prs.slides), p.name, p.stat().st_mtime)
for i, slide in enumerate(prs.slides, 1):
    texts = []
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            texts.append(sh.text_frame.text.strip().replace("\n", " | "))
    blob = " ".join(texts)
    # sales-related
    if any(x in blob.lower() for x in ["plan", "billing", "sales", "fy2027", "august", "september", "apr", "ytd", "order", "€"]):
        # flag if mentions Aug without Sep on plan/billing slides
        head = texts[1] if len(texts) > 1 else texts[0]
        print(f"\n=== {i:02d} {head[:70]} ===")
        for t in texts[2:6]:
            print(" ", t[:160])
        # chart categories if any
        for sh in slide.shapes:
            if sh.has_chart:
                try:
                    plot = sh.chart.plots[0]
                    cats = [c.label for c in sh.chart.plots[0].categories] if hasattr(sh.chart.plots[0], 'categories') else None
                except Exception:
                    cats = None
                try:
                    from pptx.chart.data import CategoryChartData
                    # read via xml
                    cats = []
                    for pt in sh.chart._chartSpace.xpath('.//c:cat//c:pt'):
                        v = pt.find('{http://schemas.openxmlformats.org/drawingml/2006/chart}v')
                        if v is not None and v.text:
                            cats.append(v.text)
                    if cats:
                        print("  CHART_CATS", cats[:16], "..." if len(cats)>16 else "", f"n={len(cats)}")
                except Exception as e:
                    print("  chart err", e)
