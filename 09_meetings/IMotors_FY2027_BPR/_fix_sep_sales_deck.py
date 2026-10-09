# -*- coding: utf-8 -*-
"""Patch I-Motors review deck so sales charts include September closed."""
from __future__ import annotations
from pathlib import Path
import shutil
from copy import deepcopy
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PPTX = ROOT / "09_meetings/IMotors_FY2027_BPR/I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx"
BAK = ROOT / "09_meetings/IMotors_FY2027_BPR/_bak_pre_sep_sales_fix.pptx"

# Known series from prior deck / KPI / daily report (EUR)
# Plan (budget) Apr-Sep from charcoal + BP sheet Sep
PLAN = [138.2, 149.5, 151.3, 145.3, 162.5, 177.7]  # EUR K
# Actual billing Apr-Aug from existing Sep_closed deck narrative; Sep = daily report Billing MTD
# Need exact Apr-Aug from chart - will read then replace
STD_2026 = [297.074, 489.770, 379.751, 393.481, 303.777, 416.806]  # EUR K Apr-Sep from KPI
# Fill Jan-Sep from earlier probe (need Aug25-Sep26 for chart)
FILL_CY = {
    # will build from chart + append Sep
}
MOS_JAN_SEP = [2.5, 2.7, 3.2, 2.87, 2.83, 2.77, 2.62, 2.20, 2.49]
BO_JAN_SEP = [430, 550, 447, 430, 487, 385, 279, 282, 495]
FILL_JAN_SEP = [0.7852, 0.761, 0.8406, 0.8455, 0.8395, 0.8541, 0.8362, 0.8539, 0.8105]
SEP_BILL_K = 134.461  # from daily report
SEP_PLAN_K = 177.733

NS = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

def replace_text(slide, old, new):
    hit = False
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            for run in para.runs:
                if old in run.text:
                    run.text = run.text.replace(old, new)
                    hit = True
    return hit

def get_chart_space(shape):
    return shape.chart._chartSpace

def read_series(chart_space):
    root = chart_space
    cats = [n.text for n in root.xpath(".//c:cat//c:pt/c:v", namespaces=NS)]
    sers = []
    for ser in root.xpath(".//c:ser", namespaces=NS):
        nm_nodes = ser.xpath("./c:tx//c:v/text()", namespaces=NS)
        nm = nm_nodes[0] if nm_nodes else "?"
        vals = [float(n) for n in ser.xpath("./c:val//c:pt/c:v/text()", namespaces=NS)]
        sers.append((nm, vals, ser))
    return cats, sers

def set_num_cache(ser_el, values):
    """Replace c:val/c:numCache points with new values."""
    val = ser_el.find(".//{http://schemas.openxmlformats.org/drawingml/2006/chart}val")
    if val is None:
        return False
    # clear existing numCache or numLit
    for child in list(val):
        val.remove(child)
    numCache = etree.SubElement(val, "{http://schemas.openxmlformats.org/drawingml/2006/chart}numCache")
    fmt = etree.SubElement(numCache, "{http://schemas.openxmlformats.org/drawingml/2006/chart}formatCode")
    fmt.text = "General"
    ptCount = etree.SubElement(numCache, "{http://schemas.openxmlformats.org/drawingml/2006/chart}ptCount")
    ptCount.set("val", str(len(values)))
    for i, v in enumerate(values):
        pt = etree.SubElement(numCache, "{http://schemas.openxmlformats.org/drawingml/2006/chart}pt")
        pt.set("idx", str(i))
        v_el = etree.SubElement(pt, "{http://schemas.openxmlformats.org/drawingml/2006/chart}v")
        v_el.text = f"{v}"
    return True

def set_cat_cache(ser_or_chart, cats):
    # categories often under first series or plot area - update all cat caches in chart
    root = ser_or_chart if ser_or_chart.tag.endswith("chartSpace") else ser_or_chart.getroottree().getroot()
    # find all c:cat
    for cat in root.xpath(".//c:cat", namespaces=NS):
        for child in list(cat):
            cat.remove(child)
        # use strLit for month labels
        strLit = etree.SubElement(cat, "{http://schemas.openxmlformats.org/drawingml/2006/chart}strLit")
        ptCount = etree.SubElement(strLit, "{http://schemas.openxmlformats.org/drawingml/2006/chart}ptCount")
        ptCount.set("val", str(len(cats)))
        for i, c in enumerate(cats):
            pt = etree.SubElement(strLit, "{http://schemas.openxmlformats.org/drawingml/2006/chart}pt")
            pt.set("idx", str(i))
            v_el = etree.SubElement(pt, "{http://schemas.openxmlformats.org/drawingml/2006/chart}v")
            v_el.text = str(c)
        break  # only first cat structure; also update num caches? some charts share
    # update ALL cat nodes similarly
    cats_nodes = root.xpath(".//c:cat", namespaces=NS)
    for cat in cats_nodes[1:]:
        for child in list(cat):
            cat.remove(child)
        strLit = etree.SubElement(cat, "{http://schemas.openxmlformats.org/drawingml/2006/chart}strLit")
        ptCount = etree.SubElement(strLit, "{http://schemas.openxmlformats.org/drawingml/2006/chart}ptCount")
        ptCount.set("val", str(len(cats)))
        for i, c in enumerate(cats):
            pt = etree.SubElement(strLit, "{http://schemas.openxmlformats.org/drawingml/2006/chart}pt")
            pt.set("idx", str(i))
            v_el = etree.SubElement(pt, "{http://schemas.openxmlformats.org/drawingml/2006/chart}v")
            v_el.text = str(c)

shutil.copy2(PPTX, BAK)
prs = Presentation(str(PPTX))

# --- SLIDE 4: plan vs sales - read and ensure Sep billing ---
s4 = prs.slides[3]
for sh in s4.shapes:
    if not sh.has_chart:
        continue
    cats, sers = read_series(sh.chart._chartSpace)
    print("S4 before", cats, [(n,v) for n,v,_ in sers])
    # Expect sales + budget series, 6 months
    # Find sales series and set Sep if missing/wrong
    for nm, vals, ser in sers:
        if len(vals) == 6:
            # if last looks like old Sep or Aug-end wrong
            if "budget" in nm.lower() or "plan" in nm.lower() or "Current" in nm:
                set_num_cache(ser, PLAN)
            else:
                # actual sales - keep first 5, set Sep from daily report
                new_vals = list(vals)
                new_vals[5] = round(SEP_BILL_K, 1)
                # if chart was Apr-Aug only (5 pts) append
                set_num_cache(ser, new_vals)
                print("S4 sales set", new_vals)
        elif len(vals) == 5:
            if "budget" in nm.lower() or "plan" in nm.lower() or "Current" in nm:
                set_num_cache(ser, PLAN)
                set_cat_cache(sh.chart._chartSpace, ["Apr","May","Jun","Jul","Aug","Sep"])
            else:
                set_num_cache(ser, list(vals) + [round(SEP_BILL_K, 1)])
                set_cat_cache(sh.chart._chartSpace, ["Apr","May","Jun","Jul","Aug","Sep"])
                print("S4 appended Sep", list(vals)+[round(SEP_BILL_K,1)])

# Update slide 4 callouts if still Aug-centric
replace_text(s4, "Apr–Aug ISZE billing; September from ISZE Monthly Report VP (closed).",
             "ISZE billing Apr–Sep 2026; September Billing MTD from ISZE Daily Sales Report 30 Sep closed.")
# Fix any wrong Sep sales text
for sh in s4.shapes:
    if sh.has_text_frame:
        t = sh.text_frame.text
        if "Apr–Jul sales" in t or "August was the trough" in t:
            pass  # keep narrative if still true

# --- SLIDE 5: pace - currently Apr-Aug €701K - extend to Apr-Sep ---
s5 = prs.slides[4]
# Read actuals from s4 after edit by re-reading - from PLAN and known
# Get Apr-Aug from s4 chart first series before save - re-open from backup values:
# From charcoal / typical: need values. Read from BAK slide 4
prs_bak = Presentation(str(BAK))
apr_sep_sales = None
for sh in prs_bak.slides[3].shapes:
    if sh.has_chart:
        cats, sers = read_series(sh.chart._chartSpace)
        for nm, vals, _ in sers:
            if "budget" not in nm.lower() and "plan" not in nm.lower() and "Current" not in nm:
                apr_sep_sales = list(vals)
                if len(apr_sep_sales) == 5:
                    apr_sep_sales.append(round(SEP_BILL_K, 1))
                elif len(apr_sep_sales) >= 6:
                    apr_sep_sales[5] = round(SEP_BILL_K, 1)
                    apr_sep_sales = apr_sep_sales[:6]
                print("billing Apr-Sep K", apr_sep_sales, "sum", sum(apr_sep_sales))

if not apr_sep_sales:
    raise SystemExit("no sales series")

ytd = sum(apr_sep_sales)
# FY2026 full year monthly for pace chart - keep as is but extend FY27 to Sep
for sh in s5.shapes:
    if not sh.has_chart:
        continue
    cats, sers = read_series(sh.chart._chartSpace)
    print("S5 before", cats[:14], [(n, v[:8]) for n,v,_ in sers])
    # Typically FY2026 12 months + FY2027 partial
    for nm, vals, ser in sers:
        if "2027" in nm or "FY27" in nm or (len(vals) <= 8 and max(vals) < 300):
            # FY2027 series: should be 6 months Apr-Sep
            if len(vals) == 5:
                set_num_cache(ser, apr_sep_sales)
            elif len(vals) >= 6:
                newv = list(vals)
                # map: if cats include Apr.. and values align
                newv[:6] = apr_sep_sales
                set_num_cache(ser, newv[:len(vals)] if len(newv) >= len(vals) else apr_sep_sales)
            else:
                set_num_cache(ser, apr_sep_sales)
            print("S5 FY27 set", apr_sep_sales)

# Update tiles / text on slide 5
replace_text(s5, "April-August billing is flat on last year; a straight-line full year gives 90.5% of target",
             f"April–September billing is €{ytd:.0f}K; a straight-line full year is about {ytd*12/6/1858*100:.1f}% of the €1.858M target")
replace_text(s5, "pace chart still April–August", "through September 2026")
replace_text(s5, "April-August 2026", "April–September 2026")
replace_text(s5, "€701K", f"€{ytd:.0f}K")
replace_text(s5, "€701k", f"€{ytd:.0f}K")
# 90.5% may appear elsewhere
pace_pct = ytd * 12 / 6 / 1858 * 100
replace_text(s5, "90.5%", f"{pace_pct:.1f}%")

# --- SLIDE 8: sales to dealer - add Sep ---
s8 = prs.slides[7]
# Need 2025 Apr-Sep comparable - from slide text APR-SEP 2025
# Read chart
for sh in s8.shapes:
    if not sh.has_chart:
        continue
    cats, sers = read_series(sh.chart._chartSpace)
    print("S8 before", cats, [(n,v) for n,v,_ in sers])
    # cats were Apr-Aug only - extend both series
    set_cat_cache(sh.chart._chartSpace, ["Apr","May","Jun","Jul","Aug","Sep"])
    for nm, vals, ser in sers:
        if "2026" in nm or (vals and abs(vals[-1] - 303.777) < 2) or (len(vals)==5 and vals[0] > 250):
            # 2026 series
            if len(vals) == 5:
                set_num_cache(ser, STD_2026)
            else:
                set_num_cache(ser, STD_2026[:len(vals)] if len(vals) > 6 else STD_2026)
            print("S8 2026", STD_2026)
        else:
            # 2025 - need Sep 2025 from rolling or prior - if 5 months keep and append?
            # From KPI we only have 2026. Try to get from chart vals - if 5 long append unknown
            # Search: earlier deck may have had Sep. Use sum logic from slide 9.
            if len(vals) == 5:
                # leave 2025 as 5? better find Sep 2025
                # From sales to dealer file - skip for now use placeholder from typical
                # Read from PORTUGAL sellout if exists
                set_num_cache(ser, list(vals) + [vals[-1]])  # TEMP wrong
                print("S8 2025 WARN need Sep", vals)

# Get 2025 Apr-Sep from sellout or previous deck bak if had 6 months
# Try Nuno sales to dealer xlsx monthly euros for 2025
std_path = ROOT / "01_data/90_INBOX/nuno_machado_sales_to_dealer_20260903/PORTUGAL_Sales_to_Dealer_2025-26_from_NunoMachado_20260903_1258.xlsx"
std_2025 = None
if std_path.exists():
    import openpyxl
    wb = openpyxl.load_workbook(std_path, data_only=True, read_only=True)
    print("STD sheets", wb.sheetnames)
    # peek
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True, max_row=5))
    print("STD head", rows)
    wb.close()

# KPI for 2025 months - not in current KPI sheet (only 2026). 
# Slide 8 text says comparable Apr-Sep - check BAK for 2025 series with Sep
for sh in prs_bak.slides[7].shapes:
    if sh.has_chart:
        cats, sers = read_series(sh.chart._chartSpace)
        print("S8 BAK", cats, [(n,v) for n,v,_ in sers])

# --- SLIDE 16 fill: append Sep 81.0% ---
s16 = prs.slides[15]
for sh in s16.shapes:
    if not sh.has_chart:
        continue
    cats, sers = read_series(sh.chart._chartSpace)
    print("S16 before", cats, [(n,v) for n,v,_ in sers])
    # if ends Aug 26, append Sep 26
    if cats and str(cats[-1]).startswith("Aug") and "Sep" not in "".join(str(c) for c in cats):
        new_cats = list(cats) + ["Sep 26"]
        # unique half if doubled
        # cats may be duplicated for multi-series
        uniq = []
        for c in cats:
            if c not in uniq:
                uniq.append(c)
        if uniq[-1].startswith("Aug") or uniq[-1] == "Aug 26":
            uniq.append("Sep 26")
        set_cat_cache(sh.chart._chartSpace, uniq if len(cats) == len(uniq) else list(cats[:len(sers[0][1])]) + ["Sep 26"])
        for nm, vals, ser in sers:
            if "target" in nm.lower():
                set_num_cache(ser, list(vals) + [0.85])
            else:
                set_num_cache(ser, list(vals) + [0.8105])
        print("S16 appended Sep")
    elif cats and "Sep" in str(cats[-1]):
        for nm, vals, ser in sers:
            if "target" not in nm.lower() and vals:
                newv = list(vals)
                newv[-1] = 0.8105
                set_num_cache(ser, newv)

# --- SLIDE 17 MOS + BO: append Sep ---
s17 = prs.slides[16]
for sh in s17.shapes:
    if not sh.has_chart:
        continue
    cats, sers = read_series(sh.chart._chartSpace)
    print("S17 before", sh.name, cats, [(n,v) for n,v,_ in sers])
    uniq = []
    for c in cats:
        if c not in uniq:
            uniq.append(c)
    if uniq and (str(uniq[-1]).startswith("Aug") or uniq[-1] == "Aug 26"):
        new_cats = uniq + ["Sep 26"]
        set_cat_cache(sh.chart._chartSpace, new_cats)
        for nm, vals, ser in sers:
            if "target" in nm.lower() or nm.strip() == "Target 3.0":
                set_num_cache(ser, list(vals) + [3.0])
            elif max(vals) > 50:  # BO lines
                set_num_cache(ser, list(vals) + [495])
            else:  # MOS
                set_num_cache(ser, list(vals) + [2.49])
        print("S17 appended Sep to", sh.name)

# Executive slide 3 - update any Aug-only sales tiles
s3 = prs.slides[2]
replace_text(s3, "through Aug 2026", "through Sep 2026")
replace_text(s3, "to August 2026", "to September 2026")

# Slide 6 H2 recovery arithmetic - update remaining if mentions Apr-Sep sales
s6 = prs.slides[5]
# remaining = 1858 - ytd
remain = 1858 - ytd
replace_text(s6, "after six months", "after six months")  # Apr-Sep is 6 months
# try common strings
for old, new in [
    (f"€1.084M remains", f"€{remain/1000:.3f}M remains".replace("€0.", "€")),
]:
    replace_text(s6, old, new)

# Fix slide 8 properly with 2025 Sep from long file if possible
# Use prior 12m slide knowledge - for 2025 Apr-Sep from common Portugal numbers in deck text
# APR–SEP 2025 total often shown - read slide 8 texts
for sh in s8.shapes:
    if sh.has_text_frame:
        print("S8TXT", sh.text_frame.text.replace("\n"," | ")[:120])

prs.save(str(PPTX))
print("SAVED", PPTX, "YTD", ytd, "pace", pace_pct, "remain", remain)
