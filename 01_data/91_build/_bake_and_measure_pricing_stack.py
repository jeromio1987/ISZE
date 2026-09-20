# -*- coding: utf-8 -*-
"""Bake the pricing workbook with Excel and MEASURE the cached values before and after.

openpyxl writes a formula but cannot compute it, so a formula-only workbook shows blank
totals until someone opens it in Excel. Excel COM through pywin32 recalculates and
re-saves, which stores the calculated value beside the formula.

This script counts the cached values in the container XML before and after, so the
result is measured rather than assumed. It also re-validates the container: zip
integrity, every XML part well-formed, and the five sheets declared.

Run: python 01_data/91_build/_bake_and_measure_pricing_stack.py
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

XL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing"
          r"\ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def say(m: str = "") -> None:
    print(m)
    sys.stdout.flush()


def counts(path: Path) -> dict:
    z = zipfile.ZipFile(path)
    out = {}
    for n in sorted(x for x in z.namelist()
                    if re.match(r"xl/worksheets/sheet\d+\.xml$", x)):
        root = ElementTree.fromstring(z.read(n))
        f = sum(1 for _ in root.iter(f"{NS}f"))
        v = sum(1 for _ in root.iter(f"{NS}v"))
        out[n] = {"formulas": f, "values": v}
    return out


def container(path: Path) -> dict:
    z = zipfile.ZipFile(path)
    xml_bad = []
    for n in z.namelist():
        if n.endswith(".xml") or n.endswith(".rels"):
            try:
                ElementTree.fromstring(z.read(n))
            except ElementTree.ParseError as exc:
                xml_bad.append((n, str(exc)))
    names = re.findall(r"<sheet[^>]*\bname=\"([^\"]+)\"", z.read("xl/workbook.xml").decode())
    return {
        "zip_ok": z.testzip() is None,
        "xml_bad": xml_bad,
        "sheets": names,
        "macro": any("vbaProject" in n for n in z.namelist()),
        "external": any("externalLink" in n for n in z.namelist()),
        "pivot": any("pivotCache" in n or "pivotTable" in n for n in z.namelist()),
    }


say("=" * 98)
say("BEFORE BAKING - what openpyxl wrote")
say("=" * 98)
before = counts(XL)
tot_f = sum(d["formulas"] for d in before.values())
tot_v = sum(d["values"] for d in before.values())
for n, d in before.items():
    say(f"  {n:<26} formulas {d['formulas']:>8,}   cached values {d['values']:>8,}")
say(f"  {'TOTAL':<26} formulas {tot_f:>8,}   cached values {tot_v:>8,}")

say()
say("=" * 98)
say("BAKING WITH EXCEL COM")
say("=" * 98)
try:
    import win32com.client as w
except Exception as exc:                                            # pragma: no cover
    say(f"  pywin32 unavailable: {exc}")
    raise SystemExit(2)
app = None
book = None
try:
    app = w.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    book = app.Workbooks.Open(str(XL), UpdateLinks=0)
    say(f"  opened: {book.Name}")
    say(f"  sheets: {[s.Name for s in book.Sheets]}")
    try:
        app.Calculation = -4105                                     # xlCalculationAutomatic
    except Exception:
        pass
    app.CalculateFullRebuild()
    book.Save()
    say("  CalculateFullRebuild + Save: OK")
finally:
    if book is not None:
        try:
            book.Close(SaveChanges=False)
        except Exception:
            pass
    if app is not None:
        try:
            app.Quit()
        except Exception:
            pass

say()
say("=" * 98)
say("AFTER BAKING - the cached values, measured")
say("=" * 98)
after = counts(XL)
tot_f2 = sum(d["formulas"] for d in after.values())
tot_v2 = sum(d["values"] for d in after.values())
for n, d in after.items():
    say(f"  {n:<26} formulas {d['formulas']:>8,}   cached values {d['values']:>8,}")
say(f"  {'TOTAL':<26} formulas {tot_f2:>8,}   cached values {tot_v2:>8,}")
say()
say(f"  cached values before: {tot_v:>8,}")
say(f"  cached values after : {tot_v2:>8,}")
say(f"  {'CACHE IS ZERO - the file would show blank totals' if tot_v2 == 0 else 'CACHE POPULATED'}")

say()
say("=" * 98)
say("CONTAINER VALIDATION")
say("=" * 98)
c = container(XL)
say(f"  zip integrity          : {'OK' if c['zip_ok'] else 'FAIL'}")
say(f"  XML parts well-formed  : {'OK' if not c['xml_bad'] else 'FAIL ' + str(c['xml_bad'][:3])}")
say(f"  sheets declared        : {c['sheets']}")
say(f"  macro part             : {'present - FAIL' if c['macro'] else 'none'}")
say(f"  external link part     : {'present - FAIL' if c['external'] else 'none'}")
say(f"  pivot cache            : {'present - FAIL' if c['pivot'] else 'none'}")
say(f"  file size              : {XL.stat().st_size:,} bytes")

ok = (c["zip_ok"] and not c["xml_bad"]
      and c["sheets"] == ["Legends", "PR00", "UTI", "UMI", "CIS"]
      and not c["macro"] and not c["external"] and not c["pivot"]
      and tot_v2 > 0)
say()
say("BAKE_AND_MEASURE_OK" if ok else "BAKE_AND_MEASURE_FAIL")
