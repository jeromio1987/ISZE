import os
import win32com.client as win32
src = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_PMS_Coverage_2026-09-21.pptx"
out = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\_qa_pms_coverage"
os.makedirs(out, exist_ok=True)
app = win32.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(src, WithWindow=False)
print("slides:", pres.Slides.Count)
for i in range(1, pres.Slides.Count + 1):
    pres.Slides(i).Export(os.path.join(out, "slide-%02d.png" % i), "PNG", 1600, 900)
pres.Close(); app.Quit()
print("done")
