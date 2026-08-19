import json, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IML_ITUK_Meeting_20260813")
NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

def first_slides(name, n=6):
    path = ROOT / name
    with zipfile.ZipFile(path) as z:
        names = sorted(x for x in z.namelist() if x.startswith("ppt/slides/slide") and x.endswith(".xml"))
        print("====", name, "slides", len(names))
        for i, fn in enumerate(names[:n], 1):
            root = ET.fromstring(z.read(fn))
            texts = [t.text.strip() for t in root.iter(NS + "t") if t.text and t.text.strip()]
            print(f"S{i}: {' | '.join(texts[:12])}")

first_slides("iFORS_Project.pptx")
first_slides("MDI_-_TVS_Project.pptx")
