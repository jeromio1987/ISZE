"""Audit our workbook against Jerome's, side by side, and assert the same regime."""
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

OURS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing"
            r"\ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx")
HIS = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw"
           r"\pricing_simulation_2026_5pct.xlsx")


def audit(p, label):
    z = zipfile.ZipFile(p)
    bad = z.testzip()
    names = z.namelist()
    total_unzip = sum(z.getinfo(n).file_size for n in names)
    sheets = [n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
    sizes = {n: z.getinfo(n).file_size for n in sheets}
    largest = max(sizes.items(), key=lambda kv: kv[1]) if sizes else ("", 0)
    workbook_xml = z.read("xl/workbook.xml").decode("utf-8", "replace")
    # the name attribute is not always first, so parse the sheet elements properly
    declared = re.findall(r"<sheet[^>]*\bname=\"([^\"]+)\"", workbook_xml)

    # formulas and function usage, counted from the sheet XML
    count = {"formula": 0, "SUMPRODUCT": 0, "VLOOKUP": 0, "SUMIF": 0, "COUNTIF": 0,
             "SUM": 0, "ROUND": 0}
    per_sheet_formulas = {}
    for n in sheets:
        body = z.read(n).decode("utf-8", "replace")
        f = body.count("<f>") + body.count("<f ")
        per_sheet_formulas[n] = f
        count["formula"] += f
        for k in ("SUMPRODUCT", "VLOOKUP", "SUMIF", "COUNTIF", "SUM", "ROUND"):
            if k == "SUM":
                count[k] += len(re.findall(r"[^A-Z]SUM\(", body))
            elif k == "ROUND":
                count[k] += body.count("ROUND(")
            else:
                count[k] += body.count(k + "(")
    # the workbook-level SUM count would double-count SUMIF/SUMIFS, so subtract those
    count["SUM"] = max(0, count["SUM"] - count["SUMIF"])

    macro = any("vbaProject" in n for n in names)
    # external links appear as a part and/or in the rels
    ext = any("externalLink" in n for n in names)
    pivot = any("pivotCache" in n or "pivotTable" in n for n in names)
    calc = "xl/calcChain.xml" in names

    xml_ok = xml_bad = 0
    for n in names:
        if n.endswith(".xml") or n.endswith(".rels"):
            try:
                ElementTree.fromstring(z.read(n))
                xml_ok += 1
            except ElementTree.ParseError:
                xml_bad += 1
    ct = z.read("[Content_Types].xml").decode("utf-8", "replace")
    return {
        "label": label, "zipped": p.stat().st_size, "unzipped": total_unzip,
        "largest_name": largest[0].split("/")[-1], "largest": largest[1],
        "sheets": declared, "sheet_parts": len(sheets), "per_sheet": per_sheet_formulas,
        "count": count, "macro": macro, "external": ext, "pivot": pivot,
        "calcChain": calc, "zip_ok": bad is None, "xml_ok": xml_ok, "xml_bad": xml_bad,
        "content_types": ct.count("<Override") + ct.count("<Default"),
    }


A = audit(HIS, "HIS (opens)")
B = audit(OURS, "OURS (rebuilt)")

print("=" * 100)
print("ARCHITECTURE AUDIT - OURS AGAINST HIS")
print("=" * 100)
rows = [
    ("zipped bytes", f"{A['zipped']:,}", f"{B['zipped']:,}"),
    ("unzipped bytes", f"{A['unzipped']:,}", f"{B['unzipped']:,}"),
    ("largest sheet part", f"{A['largest_name']} {A['largest']:,}",
     f"{B['largest_name']} {B['largest']:,}"),
    ("sheet parts", A["sheet_parts"], B["sheet_parts"]),
    ("sheets declared", len(A["sheets"]), len(B["sheets"])),
    ("names", ", ".join(A["sheets"]), ", ".join(B["sheets"])),
    ("", "", ""),
    ("formulas, all sheets", f"{A['count']['formula']:,}",
     f"{B['count']['formula']:,}"),
    ("SUMPRODUCT", A["count"]["SUMPRODUCT"], B["count"]["SUMPRODUCT"]),
    ("VLOOKUP", A["count"]["VLOOKUP"], B["count"]["VLOOKUP"]),
    ("SUMIF", A["count"]["SUMIF"], B["count"]["SUMIF"]),
    ("COUNTIF", A["count"]["COUNTIF"], B["count"]["COUNTIF"]),
    ("SUM", A["count"]["SUM"], B["count"]["SUM"]),
    ("ROUND", A["count"]["ROUND"], B["count"]["ROUND"]),
    ("", "", ""),
    ("macros (vbaProject)", A["macro"], B["macro"]),
    ("external links", A["external"], B["external"]),
    ("pivot caches/tables", A["pivot"], B["pivot"]),
    ("calcChain.xml", A["calcChain"], B["calcChain"]),
    ("zip integrity ok", A["zip_ok"], B["zip_ok"]),
    ("XML parts well-formed", f"{A['xml_ok']} ok / {A['xml_bad']} bad",
     f"{B['xml_ok']} ok / {B['xml_bad']} bad"),
    ("content-type entries", A["content_types"], B["content_types"]),
]
print(f"  {'measure':<28}{'HIS':<34}{'OURS'}")
for a, b, c in rows:
    print(f"  {a:<28}{str(b):<34}{c}")
print()
print("  formulas per sheet part:")
for n in sorted(set(A["per_sheet"]) | set(B["per_sheet"])):
    print(f"    {n:<26} his {A['per_sheet'].get(n, 0):>8,}   "
          f"ours {B['per_sheet'].get(n, 0):>8,}")

print()
print("=" * 100)
print("STRUCTURAL ASSERTIONS")
print("=" * 100)
fails = []
def check(lab, ok):
    print(f"  {'PASS' if ok else 'FAIL'}  {lab}")
    if not ok:
        fails.append(lab)

check("zero SUMPRODUCT", B["count"]["SUMPRODUCT"] == 0)
check("zero VLOOKUP", B["count"]["VLOOKUP"] == 0)
check("no macros (plain .xlsx)", not B["macro"])
check("no external links", not B["external"])
check("no pivot caches or tables", not B["pivot"])
check("zip integrity ok", B["zip_ok"])
check("every XML part well-formed", B["xml_bad"] == 0)
check("five sheets declared", len(B["sheets"]) == 5)
check("sheets are the five asked for",
      B["sheets"] == ["Legends", "PR00", "UTI", "UMI", "CIS"])
# the size regime: no part disproportionately large. His largest is 14.7 MB.
check(f"largest sheet part under 20 MB (his {A['largest']/1e6:.1f} MB, "
      f"ours {B['largest']/1e6:.1f} MB)", B["largest"] < 20_000_000)
check(f"unzipped under his by no more than 2x "
      f"(his {A['unzipped']/1e6:.1f} MB, ours {B['unzipped']/1e6:.1f} MB)",
      B["unzipped"] <= A["unzipped"] * 2)
check("the file is far smaller than the one that would not open (55.2 MB unzipped)",
      B["unzipped"] < 20_000_000)

print()
if fails:
    print(f"ARCHITECTURE_AUDIT_FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
else:
    print("ARCHITECTURE_AUDIT_OK")
