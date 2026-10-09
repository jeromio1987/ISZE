"""OOXML package validation: zip integrity, content-type coverage, xml well-formedness."""
import sys, zipfile
from lxml import etree

DECK = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Japan_Pack_20261007.pptx"
z = zipfile.ZipFile(DECK)
bad = z.testzip()
print("zip testzip:", bad if bad else "OK (no CRC failures)")
names = z.namelist()
print("parts:", len(names))

ct = etree.fromstring(z.read("[Content_Types].xml"))
defaults = {d.get("Extension").lower() for d in ct.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Default")}
overrides = {o.get("PartName") for o in ct.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Override")}
missing = []
for n in names:
    if n == "[Content_Types].xml":
        continue
    ext = n.rsplit(".", 1)[-1].lower()
    if ("/" + n) in overrides or ext in defaults:
        continue
    missing.append(n)
print("content-type gaps:", missing if missing else "none")

xmlfail = []
for n in names:
    if not n.lower().endswith((".xml", ".rels")):
        continue
    try:
        etree.fromstring(z.read(n))
    except Exception as e:
        xmlfail.append((n, str(e)[:120]))
print("xml parse failures:", len(xmlfail))
for n, e in xmlfail:
    print("  -", n, e)

# slide count + relationship integrity
slides = sorted(n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
print("slide parts:", len(slides), slides)
pres = z.read("ppt/presentation.xml").decode("utf-8")
print("sldId count:", pres.count("<p:sldId "))

ok = (bad is None) and not missing and not xmlfail and len(slides) == 9
print("VALID" if ok else "INVALID")
sys.exit(0 if ok else 1)
