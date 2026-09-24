"""One merged I Motors FY2027 business performance review deck (charcoal layout).

Runs the two existing builds into one presentation, adds the slides that only exist in the charcoal draft,
adds the programme and closing slides, then puts everything in one storyline order.

  first 7 + PMS : ../../charcoal_first7/_build/build_first7_charcoal.py   (content of the 685 KB base deck, slides 1-7)
  analysis      : ../../supporting_slides/_build/build_supporting_slides.py (fleet, genuine parts share, stock movement)
  charcoal draft: ISZE/I_Motors_FY2027_Business_Performance_Review_CHARCOAL_v8.pptx slides 3 and 5 (copied as they are)
  base deck     : ISZE/I_Motors_FY2027_Business_Performance_Review_DRAFT.pptx slides 12-14 (Genuine/BVP, priorities,
                  actions: figures kept, wording aligned with the stock finding)
  R&M / lubricants / extended target: 09_meetings/IMotors_FY2027_BPR/_HANDOVER_2026-09-24/HANDOVER.md §3-4 and the
                  29 July 2026 minutes and transcript
"""
import copy, io, pathlib
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt, Emu

HERE = pathlib.Path(__file__).resolve().parent
BPR = HERE.parent.parent
R = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE")
import os
OUT = pathlib.Path(os.environ.get("MERGED_OUT") or HERE.parent / "I_Motors_FY2027_Business_Performance_Review_MERGED_2026-09-24.pptx")
V8 = R / "I_Motors_FY2027_Business_Performance_Review_CHARCOAL_v8.pptx"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

def run_build(path):
    ns = {"PRS": prs, "__file__": str(path), "__name__": "merged_child"}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), ns)
    return ns

n0 = len(prs.slides)
SUP = run_build(BPR / "supporting_slides" / "_build" / "build_supporting_slides.py")
sup = list(prs.slides)[n0:]
n1 = len(prs.slides)
F7 = run_build(BPR / "charcoal_first7" / "_build" / "build_first7_charcoal.py")
f7 = list(prs.slides)[n1:]
S_COVER, S_FLEET, S_BRIDGE, S_COHORT, S_GPS, S_PACE, S_PADS, S_OILFUEL, S_AIRROT, S_TABLE, S_METHOD = sup
F_COVER, F_EXEC, F_PLAN, F_H2, F_STD, F_FILL, F_MOS, F_PMS = f7

# helpers from the first-7 build (same charcoal style)
g = F7
txt, rect, panel, tile, base, chart = g["txt"], g["rect"], g["panel"], g["tile"], g["base"], g["chart"]
style_chart, labels, col_fill = g["style_chart"], g["labels"], g["col_fill"]
RED, AMBER, GREY, GREEN, WHITE, MUTED, PANEL, BORDER, BG, ROW2 = (g[k] for k in
    ["RED", "AMBER", "GREY", "GREEN", "WHITE", "MUTED", "PANEL", "BORDER", "BG", "ROW2"])
rgb, BLANK, FONT = g["rgb"], g["BLANK"], g["FONT"]
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

tot, gps, g27 = SUP["tot"], SUP["gps"], SUP["g27"]

def replace_text(slide, old, new):
    hit = 0
    for sh in slide.shapes:
        if not sh.has_text_frame: continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if old in r.text:
                    r.text = r.text.replace(old, new); hit += 1
    assert hit, f"text not found: {old!r}"

# ------------------------------------------------------------------ make slide 2 consistent with the fiscal-year analysis
replace_text(F_EXEC, "commercial potential calendar 2025.", "genuine parts share and fleet FY2026 (April 2025 to March 2026).")
replace_text(F_EXEC, "TARGET-SPEND COVER", "GENUINE PARTS SHARE")
replace_text(F_EXEC, "56.0%", f"{gps[2026][0]*100:.1f}%")
replace_text(F_EXEC, "CY2025 parts billed against modelled target spend", "FY2026, warranty included, on the scrap-rate model")
replace_text(F_EXEC, "€1.710M / €3.052M", f"{gps[2026][1]*100:.1f}% on the 10-year car park")
replace_text(F_EXEC, "2025 FLEET BASE", "FY2026 FLEET")
replace_text(F_EXEC, "7,208", f"{tot(2026,'scrap'):,.0f}")
replace_text(F_EXEC, "Current fleet workbook: 2025 estimate", "Scrap-rate model on I Motors registrations")
replace_text(F_EXEC, "2024 actual was 6,903", f"{tot(2026,'ten'):,.0f} on the 10-year car park")

# ------------------------------------------------------------------ copy the two charcoal-draft slides that exist nowhere else
v8 = Presentation(str(V8))
def clone(src, source_line):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
    for shp in src.shapes:
        if shp.shape_type == 13:
            s.shapes.add_picture(io.BytesIO(shp.image.blob), shp.left, shp.top, shp.width, shp.height)
        else:
            s.shapes._spTree.insert_element_before(copy.deepcopy(shp._element), "p:extLst")
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    for xfrm in s.shapes._spTree.iter(A + "xfrm"):   # the draft has lines with negative height; PowerPoint rejects them
        off, ext = xfrm.find(A + "off"), xfrm.find(A + "ext")
        if off is None or ext is None: continue
        for d, o, flip in (("cx", "x", "flipH"), ("cy", "y", "flipV")):
            v = int(ext.get(d))
            if v < 0:
                ext.set(d, str(-v)); off.set(o, str(int(off.get(o)) + v))
                if xfrm.get(flip) == "1": xfrm.attrib.pop(flip)
                else: xfrm.set(flip, "1")
    for sh in s.shapes:   # the draft titles were 22.5 pt and ran into the subtitle
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and abs(r.font.size.pt - 22.5) < 0.1: r.font.size = Pt(15)
    txt(s, 0.25, 7.24, 11.5, 0.16, source_line, 6.5, "8C8C8C")
    return s
N_ROLL = clone(v8.slides[2], "Source: KPI Master File.xlsx, Parts Handling – Parts Sales DB to DLR in EUR; latest reported month Aug 2026.")
# ------------------------------------------------------------------ fill rate I Motors -> dealer (KPI Master File, First Fill Rate)
from pptx.enum.chart import XL_LABEL_POSITION as _LP
line_fmt = g["line_fmt"]
N_FFR = base("Fill rate  ·  I Motors → dealer", "Fill rate from I Motors to its dealers has recovered to the 85% target",
             "I Motors supplying its dealers  |  first fill rate  |  Aug 2025 – Aug 2026  |  latest 85.4%",
             "Source: KPI Master File.xlsx, Parts Handling – First Fill Rate (I Motors); latest reported month Aug 2026. Target 85% for I Motors to dealer.")
m13 = ["Aug 25", "Sep 25", "Oct 25", "Nov 25", "Dec 25", "Jan 26", "Feb 26", "Mar 26", "Apr 26", "May 26", "Jun 26", "Jul 26", "Aug 26"]
ffr = [0.8240, 0.8200, 0.8050, 0.8370, 0.7870, 0.7852, 0.7610, 0.8406, 0.8455, 0.8395, 0.8541, 0.8362, 0.8539]
cd = CategoryChartData(); cd.categories = m13
cd.add_series("Fill rate I Motors → dealer", ffr); cd.add_series("Target 85%", [0.85] * 13)
ch = chart(N_FFR, XL_CHART_TYPE.LINE_MARKERS, cd, 0.4, 1.8, 9.2, 4.3)
style_chart(ch, '0%'); ch.value_axis.minimum_scale = 0.70; ch.value_axis.maximum_scale = 0.95; ch.value_axis.major_unit = 0.05
a, t = ch.plots[0].series
line_fmt(a, RED, 2.5); line_fmt(t, AMBER, 1.75, marker=False, dash=True)
labels(a, '0.0%', WHITE, _LP.ABOVE, 7.5)
rect(N_FFR, 0.4, 6.25, 9.2, 0.75, PANEL, BORDER)
txt(N_FFR, 0.65, 6.25, 8.8, 0.75, "I Motors → dealer   |   Latest: 85.4%   |   Low: 76.1% (Feb 2026)   |   Target: 85%", 11, "55C271", True, anchor=MSO_ANCHOR.MIDDLE)
panel(N_FFR, [
    "This is I Motors' own service to its dealers, a different stage from ISZE's supply to I Motors on the previous slide.",
    "It improved from 76.1% in February 2026 to 85.4% in June and August 2026, at the 85% target. April, May and July were just below (83.6% to 84.6%).",
    "The recovery held while stock fell from 3.2 months (March) to 2.2 (August). Deeper stock cuts are the main risk to holding the target.",
    "Question: which part numbers make up the remaining misses, and how many are waiting on ISZE supply?"])

# ------------------------------------------------------------------ how we used your data
so, regs = SUP["so"], SUP["regs"]
fam_units = so.merge(SUP["cat"], on="pn").qty.sum()
N_DATA = base("Your data", "How we use the data I Motors shares, and what it can do for I Motors",
              "Sales to dealer by part number and month  |  vehicle registrations  |  quantities; euro values at the ISZE price list",
              "Sources: I Motors sales-to-dealer file (January 2025 to August 2026); I Motors registration file (to June 2026); ISZE billing to I Motors; ISZE PR00 price list of 10 August 2026.")
cols = [("WHAT YOU SHARED", [
            f"Sales to dealer: {len(so):,} lines, {so.pn.nunique():,} part numbers, {so.qty.sum():,.0f} units, January 2025 to August 2026 (month × part number × quantity).",
            f"Registrations: {len(regs):,} vehicles with chassis, model and first-registration date, 2005 to June 2026."]),
        ("WHAT WE DID WITH IT", [
            "Grouped part numbers into PMS families with the ISZE parts catalogue.",
            "Compared units sold to dealers with units ISZE billed to I Motors, family by family and month by month.",
            "Measured PMS cover on both stages against the same fleet demand."]),
        ("WHAT WE DID NOT ASSUME", [
            "No dealer prices and no I Motors margins: euro values use the ISZE list price, the same for both stages.",
            "No split by dealer: the file is at network level.",
            "Nothing sold outside the dealer file."])]
cw = (9.2 - 2 * 0.2) / 3
for k, (h, pts) in enumerate(cols):
    x = 0.4 + k * (cw + 0.2)
    rect(s := N_DATA, x, 1.85, cw, 2.95, PANEL, BORDER)
    txt(s, x + 0.2, 2.0, cw - 0.4, 0.25, h, 8, RED, True)
    txt(s, x + 0.2, 2.34, cw - 0.4, 2.4, [f"•  {p}" for p in pts], 8.8, WHITE)
    for para in s.shapes[-1].text_frame.paragraphs: para.space_after = Pt(6)
rect(N_DATA, 0.4, 4.98, 9.2, 2.02, PANEL, "F5A000")
txt(N_DATA, 0.6, 5.1, 8.8, 0.25, "WHAT IT DOES FOR I MOTORS, IF THE FILE KEEPS COMING EVERY MONTH", 8, AMBER, True)
hw = (8.8 - 0.3) / 2
txt(N_DATA, 0.6, 5.45, hw, 0.25, "Replenishment", 9.5, WHITE, True)
txt(N_DATA, 0.6, 5.75, hw, 1.2, "ISZE can size supply on what your dealers actually buy, not on past orders: fewer back orders on fast movers, stock kept at the 3.0 MOS target, and an early warning when a family runs low.", 8.8, MUTED)
txt(N_DATA, 0.9 + hw, 5.45, hw, 0.25, "SPA on selected part numbers", 9.5, WHITE, True)
txt(N_DATA, 0.9 + hw, 5.75, hw, 1.2, "Where dealer demand lags the fleet, ISZE can lower its price for a period, provided I Motors lowers its price to dealers as well. The monthly file is how both sides measure whether dealer sales grew.", 8.8, MUTED)
panel(N_DATA, [
    "Sales to dealer is the closest measure of real demand we have. Distributor purchases also include stock decisions.",
    "Comparing the two shows when I Motors bought ahead and when it ran stock down, family by family.",
    "The next slides use this to separate stock timing from real changes in dealer demand.",
    "Request: keep the monthly file coming, ideally with a monthly stock snapshot. It is the basis for both replenishment and any SPA."])

# ------------------------------------------------------------------ PMS cover and Genuine / BVP: billing against sales to dealer
import importlib.util as _ilu
_sp = _ilu.spec_from_file_location("sto_compare", str(HERE / "sto_compare.py"))
STO = _ilu.module_from_spec(_sp); _sp.loader.exec_module(STO)
PMS_T, PMS_FLEET = STO.pms_compare()
BVP_T, BVP_COVER = STO.bvp_compare()
assert all(v > 0.97 for v in BVP_COVER.values()), BVP_COVER   # share of units with a list price
P26, P27 = "FY2026", "FY2027 Apr-Aug"
def pv(fam, per, col): return float(PMS_T[(PMS_T.fam == fam) & (PMS_T.period == per)][col].iloc[0])
def pc_(v): return f"{v*100:.0f}%" if v >= 0.015 else f"{v*100:.1f}%"
def pcol(v): x = v * 100; return GREEN if x >= 50 else (AMBER if x >= 25 else RED)

N_PMS = base("PMS cover", "PMS cover on sales to dealer: filters hold around 50%; brake shoes and cabin filters stay low on both stages",
             f"ISZE billing and I Motors sales to dealer, same periods, same PMS demand  |  units  |  fleet FY2026: {PMS_FLEET:,.0f} vehicles (scrap-rate model)",
             "Sources: ISZE billing to I Motors (credit notes excluded); I Motors sales to dealer (month rows); ISZE PMS model on the I Motors registration file; ISZE parts catalogue.")
READ = {"oil_filter": "Dealers take more than I Motors buys: stock running down",
        "fuel_filter": "In step in FY2026; running down in FY2027",
        "air_filter": "Built ahead in FY2026, now running down",
        "blower_filter": "Low on both stages: room to develop (SPA)",
        "urea_filter": "Almost no volume on either stage: check fitment and demand (SPA)",
        "brake_pad": "Dealer demand steady; billing swing is stock",
        "brake_shoe": "About 10% on both stages: lasting gap (SPA)",
        "brake_rotor": "Built ahead in FY2026; dealer cover about 35% (SPA once stock is used)",
        "clutch_kit": "Stable, about 25–30%",
        "clutch_disc": "Low, about 12–16%, on both stages",
        "clutch_pressure_plate": "Low, about 11–14%, on both stages",
        "release_bearing": "Very low on both stages",
        "pilot_bearing": "Very low on both stages",
        "clutch_booster": "Very low on both stages"}
cols = [(0.4, 1.75), (2.15, 0.78), (2.93, 0.78), (3.71, 0.78), (4.49, 0.78), (5.27, 4.33)]
hdrs = ["PMS family", "FY2026\nbilled", "FY2026\nto dealer", "FY27 Apr–Aug\nbilled", "FY27 Apr–Aug\nto dealer", "Reading"]
y = 1.8
for k, ((x, w), h) in enumerate(zip(cols, hdrs)):
    rect(N_PMS, x, y, w, 0.42, RED if k in (0, 5) else ("8A0A10" if k % 2 == 1 else "B00510"))
    txt(N_PMS, x + 0.05, y, w - 0.1, 0.42, h.split("\n"), 7, WHITE, True, PP_ALIGN.LEFT if k in (0, 5) else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
y += 0.44
rh = 0.305
for i, f in enumerate(STO.FAMS):
    vals = [STO.LAB[f], pv(f, P26, "cov_billed"), pv(f, P26, "cov_sold"), pv(f, P27, "cov_billed"), pv(f, P27, "cov_sold"), READ[f]]
    for j, ((x, w), v) in enumerate(zip(cols, vals)):
        rect(N_PMS, x, y, w, rh - 0.02, ROW2 if i % 2 == 0 else PANEL)
        if j in (1, 2, 3, 4):
            txt(N_PMS, x, y, w, rh - 0.02, pc_(v), 9.5, pcol(v) if j in (2, 4) else MUTED, j in (2, 4), PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        else:
            txt(N_PMS, x + 0.08, y, w - 0.14, rh - 0.02, v, 8 if j == 0 else 7.5, WHITE if j == 0 else MUTED, j == 0, anchor=MSO_ANCHOR.MIDDLE)
    y += rh
txt(N_PMS, 0.4, y + 0.05, 9.2, 0.55, [
    "PMS cover = units ÷ expected PMS replacement units of the fleet. Same numerator rules and same denominator for both stages; FY2027 Apr–Aug uses 5/12 of the FY2026 yearly demand (the registration file ends June 2026). Sales to dealer is in bold.",
    "* Clutch families: the percentage may not be accurate. We do not know how many vehicles have a manual or an AMT gearbox, so clutch demand in the model is uncertain."], 6.8, MUTED)
panel(N_PMS, [
    f"Sales to dealer is the real demand. Oil filters sit at {pc_(pv('oil_filter', P26, 'cov_sold'))} and {pc_(pv('oil_filter', P27, 'cov_sold'))} there, above billing, because I Motors is using up the 2024–2025 bulk purchases.",
    f"Brake pads: dealers take a steady {pc_(pv('brake_pad', P26, 'cov_sold'))} in both periods, while billing fell from {pc_(pv('brake_pad', P26, 'cov_billed'))} to {pc_(pv('brake_pad', P27, 'cov_billed'))}. That is stock, not lost business.",
    f"Brake shoes (about {pc_(pv('brake_shoe', P26, 'cov_sold'))}), cabin filters (about {pc_(pv('blower_filter', P26, 'cov_sold'))}) and AdBlue filters (about 1%) are low on sales to dealer too. That is lasting room to grow, and where we propose an SPA.",
    "Question: can I Motors share the manual / AMT split of its fleet, so the clutch percentages can be made reliable?"])

N_BVP = base("Genuine & BVP", "On one price basis, dealers buy a steady Genuine / BVP mix; ISZE billing swings with the 2025 brake stock",
             "Filters, brakes and clutch  |  calendar years  |  EUR K at the ISZE price list of 10 August 2026  |  BVP = Best Value Parts",
             "Sources: ISZE billing to I Motors; I Motors sales to dealer (month rows); ISZE Genuine / BVP part-number list; units valued at the IE40 PR00 price list of 10 August 2026 (Price_file_PR00_IE40_20260810.xlsx).")
def bv(stage, per, grp=None, lt=None):
    x = BVP_T[(BVP_T.stage == stage) & (BVP_T.period == per)]
    if grp: x = x[x.grp == grp]
    if lt: x = x[x.line_type == lt]
    return float(x.list_eur.sum()) / 1000
BP = ["2023", "2024", "2025", "2026 Jan-Aug"]
SP = ["2025", "2026 Jan-Aug"]
txt(N_BVP, 0.5, 1.8, 4.3, 0.22, "ISZE BILLING TO I MOTORS", 8, RED, True)
cd = CategoryChartData(); cd.categories = ["2023", "2024", "2025", "2026 Jan–Aug"]
cd.add_series("Genuine", [round(bv("billed", p, lt="genuine")) for p in BP]); cd.add_series("BVP", [round(bv("billed", p, lt="bvp")) for p in BP])
ch = chart(N_BVP, XL_CHART_TYPE.COLUMN_STACKED, cd, 0.4, 2.02, 5.0, 2.75)
style_chart(ch, '€#,##0"K"'); ch.plots[0].gap_width = 55; ch.value_axis.maximum_scale = 250; ch.value_axis.minimum_scale = 0
for se, c in zip(ch.plots[0].series, [RED, GREY]): col_fill(se, c); labels(se, '#,##0', "1A1A1A" if c == GREY else WHITE, XL_LABEL_POSITION.CENTER, 8)
txt(N_BVP, 5.7, 1.8, 3.9, 0.22, "I MOTORS SALES TO DEALER", 8, RED, True)
cd = CategoryChartData(); cd.categories = ["2025", "2026 Jan–Aug"]
cd.add_series("Genuine", [round(bv("sold", p, lt="genuine")) for p in SP]); cd.add_series("BVP", [round(bv("sold", p, lt="bvp")) for p in SP])
ch = chart(N_BVP, XL_CHART_TYPE.COLUMN_STACKED, cd, 5.6, 2.02, 4.0, 2.75)
style_chart(ch, '€#,##0"K"'); ch.plots[0].gap_width = 55; ch.value_axis.maximum_scale = 250; ch.value_axis.minimum_scale = 0
for se, c in zip(ch.plots[0].series, [RED, GREY]): col_fill(se, c); labels(se, '#,##0', "1A1A1A" if c == GREY else WHITE, XL_LABEL_POSITION.CENTER, 8)
def bshare(stage, per, grp=None): t = bv(stage, per, grp); return bv(stage, per, grp, "bvp") / t if t else 0
hdr = ["Family", "Billed 2025", "To dealer 2025", "Billed 2026 Jan–Aug", "To dealer 2026 Jan–Aug"]
cx = [(0.4, 1.6), (2.0, 1.9), (3.9, 1.9), (5.8, 1.9), (7.7, 1.9)]
y = 4.9
for (x, w), h in zip(cx, hdr):
    rect(N_BVP, x, y, w, 0.32, "3A3A3A"); txt(N_BVP, x + 0.08, y, w - 0.12, 0.32, h, 7.5, MUTED, True, anchor=MSO_ANCHOR.MIDDLE)
for i, grp in enumerate(["Filters", "Brakes", "Clutch", None]):
    y += 0.34
    vals = [grp or "Total"] + [f"€{bv(st, p, grp):,.1f}K  ·  BVP {bshare(st, p, grp)*100:.0f}%" for st, p in
                               (("billed", "2025"), ("sold", "2025"), ("billed", "2026 Jan-Aug"), ("sold", "2026 Jan-Aug"))]
    for j, ((x, w), v) in enumerate(zip(cx, vals)):
        rect(N_BVP, x, y, w, 0.32, ROW2 if i % 2 == 0 else PANEL)
        txt(N_BVP, x + 0.08, y, w - 0.12, 0.32, v, 8, WHITE, j == 0 or grp is None, anchor=MSO_ANCHOR.MIDDLE)
b25, s25, b26, s26 = bv("billed", "2025"), bv("sold", "2025"), bv("billed", "2026 Jan-Aug"), bv("sold", "2026 Jan-Aug")
panel(N_BVP, [
    f"On one price basis the two stages can be compared in euros: in 2025 I Motors bought €{b25:,.0f}K and sold €{s25:,.0f}K to dealers in these families; in 2026 to August €{b26:,.0f}K against €{s26:,.0f}K.",
    f"Brakes carry the stock swing: bought €{bv('billed','2025','Brakes'):,.0f}K against €{bv('sold','2025','Brakes'):,.0f}K sold in 2025, then €{bv('billed','2026 Jan-Aug','Brakes'):,.0f}K against €{bv('sold','2026 Jan-Aug','Brakes'):,.0f}K in 2026.",
    f"Dealers take a steady BVP share ({bshare('sold','2025')*100:.0f}% in 2025, {bshare('sold','2026 Jan-Aug')*100:.0f}% in 2026). The billed share moved from {bshare('billed','2025')*100:.0f}% to {bshare('billed','2026 Jan-Aug')*100:.0f}% because of the Genuine brake stock bought in 2025, not because the dealer mix changed.",
    "Euro values are units × the ISZE list price of 10 August 2026. They are not I Motors' purchase prices or its prices to dealers."])

# ------------------------------------------------------------------ SPA proposal
avg_price = {}
_pl = STO.price_list()
_cat = pd.read_csv(STO.DER / "parts_catalog_dimension.csv", dtype=str, usecols=["part_number", "pms_category"])
_cat["pn"] = STO.norm(_cat.part_number); _cat["fam"] = _cat.pms_category.map(STO.fam_of)
_so = STO.in_period(STO.sellout(), P26).merge(_cat.drop_duplicates("pn")[["pn", "fam"]], on="pn")
_so["eur"] = _so.qty * _so.pn.map(_pl)
for f, gdf in _so.groupby("fam"):
    ok = gdf[gdf.eur.notna()]
    avg_price[f] = ok.eur.sum() / ok.qty.sum() if ok.qty.sum() else float("nan")
SPA_F = ["brake_shoe", "blower_filter", "urea_filter", "brake_rotor", "clutch_disc", "clutch_pressure_plate", "clutch_kit"]
N_SPA = base("SPA proposal", "SPA proposal: a lower ISZE price where dealer demand lags the fleet, passed on to dealer prices",
             "PMS families with low cover on sales to dealer  |  what +10 points of PMS cover means per year  |  units and EUR at the ISZE price list",
             "Sources: PMS cover on sales to dealer (previous slides); ISZE PMS model on the FY2026 fleet; average list price of the part numbers dealers bought in FY2026 (IE40 PR00, 10 August 2026).")
cols = [(0.4, 2.1), (2.5, 1.35), (3.85, 1.35), (5.2, 1.4), (6.6, 1.5), (8.1, 1.5)]
hdr = ["PMS family", "To dealer FY2026", "To dealer FY27 Apr–Aug", "PMS demand / year (units)", "+10 pts cover (units / year)", "+10 pts cover (EUR / year, list)"]
y = 1.8
for k, ((x, w), h) in enumerate(zip(cols, hdr)):
    rect(N_SPA, x, y, w, 0.44, RED); txt(N_SPA, x + 0.06, y, w - 0.1, 0.44, h, 7.3, WHITE, True, PP_ALIGN.LEFT if k == 0 else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
y += 0.46
for i, f in enumerate(SPA_F):
    dem = pv(f, P26, "demand"); add = dem * 0.10
    vals = [STO.LAB[f] + ("  (after stock is used)" if f == "brake_rotor" else ""), pc_(pv(f, P26, "cov_sold")), pc_(pv(f, P27, "cov_sold")),
            f"{dem:,.0f}", f"+{add:,.0f}", f"+€{add * avg_price.get(f, float('nan')) / 1000:,.0f}K"]
    for j, ((x, w), v) in enumerate(zip(cols, vals)):
        rect(N_SPA, x, y, w, 0.34, ROW2 if i % 2 == 0 else PANEL)
        txt(N_SPA, x + 0.08, y, w - 0.14, 0.34, v, 8 if j == 0 else 9, WHITE if j != 1 and j != 2 else pcol(pv(f, P26 if j == 1 else P27, "cov_sold")), j in (0, 5),
            PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    y += 0.36
txt(N_SPA, 0.4, y + 0.02, 9.2, 0.3, "* Clutch families: the percentage may not be accurate (manual / AMT split of the fleet unknown). AdBlue filter: check fitment and the model before setting a volume.", 6.8, MUTED)
y += 0.36
rect(N_SPA, 0.4, y, 9.2, 7.0 - y, PANEL, "F5A000")
txt(N_SPA, 0.6, y + 0.1, 8.8, 0.22, "HOW THE SPA WOULD WORK", 8, AMBER, True)
txt(N_SPA, 0.6, y + 0.38, 8.8, 7.0 - y - 0.45, [
    "1.  ISZE lowers its price to I Motors on a short list of part numbers in these families, for a fixed period.",
    "2.  I Motors lowers its price to dealers on the same part numbers, so the reduction reaches the workshop and turnover can grow.",
    "3.  Success is measured on monthly sales to dealer against the FY2026 level, not on ISZE billing, so stock bought at the lower price does not count as growth.",
    "4.  Review after six months: extend, adjust or stop."], 9.5, WHITE)
panel(N_SPA, [
    "The SPA targets families where sales to dealer are low against the fleet, not families where billing is low only because of stock.",
    "Oil, fuel and air filters and brake pads are not on the list: dealer demand there is steady, and billing will follow once stock is used up.",
    "Rotors join once the FY2026 stock build is sold through. Clutch families can be included, but with a caution on the percentages.",
    "Question: which dealers and part numbers should be in a first wave, and what dealer price reduction can I Motors pass on?"])

# ------------------------------------------------------------------ extended target (July 2026 proposal)
gs, gt = tot(2026, "scrap") / tot(2025, "scrap") - 1, tot(2026, "ten") / tot(2025, "ten") - 1
N_EXT = base("Extended target", "The extended FY2027 target rests on three components; the fleet growth assumption needs checking",
             "As presented on 29 July 2026  |  on top of the FY2027 target already agreed  |  parts only, accessories excluded",
             "Sources: 29 July 2026 meeting; I Motors registration file (fleet growth FY2025 → FY2026).")
for k, (lab, big, sub, c) in enumerate([
        ("PRICE ADJUSTMENT", "+5%", ["Average price increase applied in March 2026"], WHITE),
        ("FLEET GROWTH", "+9%", ["Fleet growth used in the July proposal"], AMBER),
        ("GENUINE PARTS SHARE", "+1.8 pts", ["Additional share on top of the current level"], RED)]):
    tile(N_EXT, 0.4 + k * (cw + 0.2), 1.85, cw, 1.75, lab, big, sub, c, 28)
rect(N_EXT, 0.4, 3.85, 9.2, 2.55, PANEL, BORDER)
txt(N_EXT, 0.6, 4.0, 8.8, 0.22, "FLEET GROWTH MEASURED IN THE REGISTRATION FILE, FY2025 → FY2026", 8, RED, True)
txt(N_EXT, 0.6, 4.35, 4.2, 0.6, f"{gs*100:+.1f}%", 30, WHITE, True)
txt(N_EXT, 0.6, 5.0, 4.2, 0.3, f"Scrap-rate model ({tot(2025,'scrap'):,.0f} → {tot(2026,'scrap'):,.0f} vehicles)", 9, MUTED)
txt(N_EXT, 4.9, 4.35, 4.2, 0.6, f"{gt*100:+.1f}%", 30, WHITE, True)
txt(N_EXT, 4.9, 5.0, 4.2, 0.3, f"10-year car park ({tot(2025,'ten'):,.0f} → {tot(2026,'ten'):,.0f} vehicles)", 9, MUTED)
txt(N_EXT, 0.6, 5.55, 8.8, 1.1, "Both counts are below the +9% used in July. If the fleet grows less, the fleet component of the extended target should come down with it, whichever fleet base is agreed.", 9.5, WHITE)
panel(N_EXT, [
    "In July I Motors asked ISZE to revisit the genuine parts share stretch, then agreed to try once the second incentive was explained.",
    f"The registration file shows fleet growth of {gs*100:.1f}% to {gt*100:.1f}%, not 9%. We propose to restate the fleet component on the agreed fleet base.",
    "The second incentive was pending approval at the time of the July meeting.",
    "Question: with the fleet component restated, is the +1.8-point genuine parts share step still the right ambition for FY2027?"])

# ------------------------------------------------------------------ R&M
N_RM = base("Repair & maintenance contracts", "R&M contracts: where the programme stands and what we need from I Motors",
            "History of the programme  |  last known contract numbers  |  no contract conditions shown",
            "Sources: programme documentation shared with ISZE (December 2024 onwards); 29 July 2026 meeting.")
steps = [("DEC 2024", "Programme documented", "Maintenance contracts sold with new vehicles, covering scheduled and corrective maintenance, with national coverage through the official Isuzu network."),
         ("2024–2025", "Programme update", "Isuzu Easy Maintenance being updated; sales plans and presentations prepared; an insurer-backed LCV offer explored; pricing for new N- and F-Series contracts."),
         ("LATE 2025", "Ownership", "Contact moved to the Parts & Accessories team, with aftersales closely involved."),
         ("JULY 2026", "Last known position", "12 active CV and 29 active LCV contracts. Insurer not interested at current volume; an alternative partner suggested. Leasing tenders often include R&M.")]
y = 1.85
for k, (when, head, body) in enumerate(steps):
    rect(N_RM, 0.4, y, 9.2, 1.15, ROW2 if k % 2 == 0 else PANEL, BORDER)
    rect(N_RM, 0.4, y, 0.08, 1.15, RED if k == 3 else AMBER)
    txt(N_RM, 0.65, y + 0.14, 1.5, 0.3, when, 11, RED if k == 3 else AMBER, True)
    txt(N_RM, 2.2, y + 0.12, 7.2, 0.25, head, 10, WHITE, True)
    txt(N_RM, 2.2, y + 0.42, 7.2, 0.7, body, 9, MUTED)
    y += 1.25
panel(N_RM, [
    "Please share an update on the number of active contracts since July, split CV and LCV.",
    "How is the current programme performing: contracts sold, share of new registrations covered, and claims experience?",
    "Please send the written list of obstacles and weak points in the current offer, as agreed in July.",
    "What is the status of the insurer track and the alternative partner, and where can ISZE help, for example in larger tenders?"])

# ------------------------------------------------------------------ lubricants
N_LUB = base("Lubricants", "Centralised lubricant purchasing is postponed while more areas are added",
             "Programme for ISZE, Africa and Middle East markets", "Source: ISZE programme status, September 2026.")
for k, (lab, big, sub, c) in enumerate([
        ("STATUS", "Postponed", ["The centralised purchasing programme will not start as first planned."], AMBER),
        ("WHY", "More volume", ["More areas are being added to the programme to raise the combined volume."], WHITE),
        ("AIM", "Better prices", ["A larger combined volume gives a stronger position to negotiate prices."], "55C271")]):
    tile(N_LUB, 0.4 + k * (cw + 0.2), 1.85, cw, 2.2, lab, big, sub, c, 26)
rect(N_LUB, 0.4, 4.35, 9.2, 1.4, PANEL, BORDER)
txt(N_LUB, 0.6, 4.5, 8.8, 0.22, "WHAT THIS MEANS FOR I MOTORS", 8, RED, True)
txt(N_LUB, 0.6, 4.85, 8.8, 0.8, "No change to current lubricant supply for now. ISZE will come back with the revised scope and timing once the additional areas are confirmed.", 10, WHITE)
panel(N_LUB, [
    "The programme is postponed, not cancelled.",
    "Adding more areas is meant to raise volume and secure better prices for all participants.",
    "ISZE will share the revised scope and timing when confirmed."])

# ------------------------------------------------------------------ discussion priorities (base deck slide 13, aligned)
N_PRIO = base("Discussion priorities", "Three commercial questions should drive the I Motors review",
              "Use measured dealer activity and operational KPIs to explain the category movements before changing terms",
              "Sources: FY27 plan, KPI Master File, ISZE billing to I Motors, I Motors sales to dealer, PMS model and Genuine/BVP files.")
cards = [("1  RESTART REPLENISHMENT", "6 of 7 families  |  MOS 2.2", RED,
          "In FY2027 I Motors buys less than it sells to dealers in six of seven PMS families, and stock is below the 3.0 target.\n\nDiscuss: stock on hand by family, when normal orders restart, and how that lands in the Oct–Mar recovery."),
         ("2  SPA ON LAGGING PMS FAMILIES", f"Shoe {pv('brake_shoe', P26, 'cov_sold')*100:.0f}%  |  Cabin filter {pv('blower_filter', P26, 'cov_sold')*100:.0f}%", AMBER,
          "Low PMS cover on sales to dealer, year after year, is room to grow, not stock timing.\n\nDiscuss: a lower ISZE price passed on to dealer prices, measured on the monthly sales-to-dealer file. Clutch percentages with caution."),
         ("3  HOLD SERVICE LEVELS", "ISZE 87%  |  Dealer 85.4%", "55C271",
          "I Motors → dealer fill rate is at its 85% target; ISZE → I Motors is below 93%.\n\nDiscuss: the part numbers behind the ISZE misses, and a stock floor so dealer fill rate holds.")]
for k, (h, big, c, body) in enumerate(cards):
    x = 0.4 + k * (cw + 0.2)
    rect(N_PRIO, x, 1.85, cw, 4.1, PANEL, BORDER); rect(N_PRIO, x, 1.85, cw, 0.1, c)
    txt(N_PRIO, x + 0.2, 2.12, cw - 0.4, 0.5, h, 9.5, WHITE, True)
    txt(N_PRIO, x + 0.2, 2.75, cw - 0.4, 0.5, big, 14, c, True)
    txt(N_PRIO, x + 0.2, 3.45, cw - 0.4, 3.2, body.split("\n"), 9, MUTED)
panel(N_PRIO, [
    "Agree the explanation before the action: low billing caused by stock needs replenishment, low dealer demand needs an SPA.",
    "An SPA only works if the lower price reaches the dealers, and it is measured on sales to dealer, not on ISZE billing.",
    "Set the next review around a short list of families and part numbers, with fill rate and MOS shown beside the commercial result.",
    "Track whether the action changes repeat dealer purchases and ISZE contribution, not only whether one large order lands."])

# ------------------------------------------------------------------ action points (base deck slide 14, extended)
N_ACT = base("Action points", "A monthly review should connect plan recovery, dealer demand and service availability",
             "Proposed discussion output for I Motors and ISZE", "Proposed action structure based on the evidence in this review.")
acts = [("FY27 plan recovery", "Explain the August–September shortfall and confirm category-based recovery actions for October–March.", "I Motors parts management + ISZE"),
        ("Sales to dealer", "Continue the monthly file (invoice month, part number, quantity) and add a monthly stock snapshot.", "I Motors"),
        ("Stock policy", "Bring MOS back to the 3.0 target; confirm stock on hand for brake pads, air filters and rotors and when normal orders restart.", "I Motors"),
        ("Fill rate", "ISZE → I Motors: find the part numbers behind the gap to 93%. I Motors → dealer: hold 85% while stock is rebuilt.", "ISZE + I Motors"),
        ("Fleet base", "Agree one fleet base (scrap-rate model or 10-year car park) for targets and genuine parts share; share the manual / AMT split.", "Joint"),
        ("SPA", "Agree a first-wave part-number list (brake shoes, cabin and AdBlue filters), the dealer price pass-through and the six-month review.", "Joint"),
        ("Extended target", "Restate the fleet component on the agreed fleet base and confirm the genuine parts share ambition.", "ISZE"),
        ("R&M contracts", "Send the contract update, programme performance and the written list of obstacles.", "I Motors"),
        ("Next review", "Recheck sales to dealer, fill rate, MOS and the selected service families on the next monthly cycle.", "Joint")]
cx = [(0.4, 1.75), (2.15, 5.45), (7.6, 2.0)]
y = 1.85
for (x, w), h in zip(cx, ["Topic", "Action", "Owner"]):
    rect(N_ACT, x, y, w, 0.36, "3A3A3A"); txt(N_ACT, x + 0.12, y, w - 0.2, 0.36, h, 8, MUTED, True, anchor=MSO_ANCHOR.MIDDLE)
for i, r in enumerate(acts):
    y += 0.39 if i == 0 else 0.53
    for j, ((x, w), v) in enumerate(zip(cx, r)):
        rect(N_ACT, x, y, w, 0.5, ROW2 if i % 2 == 0 else PANEL)
        txt(N_ACT, x + 0.12, y, w - 0.2, 0.5, v, 8.5 if j else 9, RED if j == 0 else WHITE, j == 0, anchor=MSO_ANCHOR.MIDDLE)
panel(N_ACT, [
    "The review should leave with an explanation and owner for each KPI, not only a list of red/green results.",
    "Keep the three sales stages separate: ISZE billing, sales to dealer and dealer-to-customer sales where available.",
    "Read the PMS family figures together with stock movement; a fall in purchases can be stock being used up.",
    "The first success measure is whether the weak categories recover while fill rate improves without rebuilding unnecessary stock."])

# ------------------------------------------------------------------ storyline order
ORDER = [F_COVER, "AGENDA", F_EXEC,
         F_PLAN, S_PACE, F_H2,
         F_STD, N_ROLL,
         N_DATA, S_TABLE, S_PADS, S_OILFUEL, S_AIRROT,
         F_FILL, N_FFR, F_MOS,
         S_FLEET, S_GPS, N_PMS, N_BVP, N_SPA, N_EXT,
         N_RM, N_LUB,
         N_PRIO, N_ACT,
         S_BRIDGE, S_COHORT, S_METHOD]
SECTIONS = [("FY2027 performance against plan", F_PLAN, F_H2), ("Demand in the dealer network", F_STD, N_ROLL),
            ("Why billing lags dealer demand: stock", N_DATA, S_AIRROT), ("Availability: fill rate and MOS", F_FILL, F_MOS),
            ("Fleet, genuine parts share, PMS and SPA", S_FLEET, N_EXT), ("Programmes: R&M and lubricants", N_RM, N_LUB),
            ("Priorities and actions", N_PRIO, N_ACT), ("Appendix", S_BRIDGE, S_METHOD)]
pos = {id(s): i + 1 for i, s in enumerate(ORDER) if s != "AGENDA"}
agenda_pos = ORDER.index("AGENDA") + 1
N_AG = base("Agenda", "Review structure", "I Motors FY2027 business performance review", " ")
y = 1.85
for k, (name, a, b) in enumerate(SECTIONS):
    rect(N_AG, 0.4, y, 9.2, 0.56, ROW2 if k % 2 == 0 else PANEL)
    txt(N_AG, 0.65, y, 0.6, 0.56, f"{k+1}", 15, RED, True, anchor=MSO_ANCHOR.MIDDLE)
    txt(N_AG, 1.3, y, 6.3, 0.56, name, 11.5, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
    txt(N_AG, 7.6, y, 1.8, 0.56, f"slides {pos[id(a)]}–{pos[id(b)]}", 10, MUTED, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    y += 0.62
panel(N_AG, [
    "We work in fiscal years (April to March) unless a slide says calendar year.",
    "Sales to dealer figures are I Motors' own reporting; ISZE billing is ISZE to I Motors. The two are different sales stages.",
    "The storyline: plan, then dealer demand, then why billing lags it (stock), then availability, fleet and PMS, and the SPA proposal.",
    "Each insight slide ends with our observations and questions for I Motors."])
ORDER[ORDER.index("AGENDA")] = N_AG

# appendix labels
for s in (S_BRIDGE, S_COHORT, S_METHOD):
    for sh in s.shapes:
        if sh.has_text_frame and abs(sh.top - Inches(0.43)) < Inches(0.02) and sh.text_frame.text.strip() in ("FLEET", "METHOD"):
            sh.text_frame.paragraphs[0].runs[0].text = "APPENDIX  ·  " + sh.text_frame.text

# one word for it: PMS (no "service-demand" wording left anywhere)
WORDING = [("service-demand cover", "PMS cover"), ("Service-demand cover", "PMS cover"), ("service-demand model", "PMS model"),
           ("service-demand", "PMS"), ("Service-demand", "PMS"), ("service demand", "PMS demand"), ("service families", "PMS families"),
           ("service family", "PMS family"), ("service-family", "PMS family")]
for s in ORDER:
    for sh in s.shapes:
        if not sh.has_text_frame: continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                for a_, b_ in WORDING:
                    if a_ in r.text: r.text = r.text.replace(a_, b_)

# sources for the analysis slides (their build has no footer line text)
FLEET_SRC = "Source: I Motors registration file (vehicle level, to June 2026); ISZE fleet model survival curves."
STOCK_SRC = "Source: ISZE billing to I Motors; I Motors sales to dealer (part number × month, January 2025 to August 2026)."
SRC = [(S_FLEET, FLEET_SRC), (S_BRIDGE, FLEET_SRC), (S_COHORT, FLEET_SRC),
       (S_GPS, "Source: ISZE billing to I Motors, invoice level, to 31 August 2026; I Motors registration file; ISZE target-spend rates."),
       (S_PACE, "Source: ISZE billing to I Motors, invoice level, to 31 August 2026; FY2027 target €1.858M."),
       (S_PADS, STOCK_SRC), (S_OILFUEL, STOCK_SRC), (S_AIRROT, STOCK_SRC), (S_TABLE, STOCK_SRC)]
for s, t in SRC:
    txt(s, 0.25, 7.24, 11.5, 0.16, t, 6.5, "8C8C8C")

# drop the analysis pack's own cover and the old billing-only PMS slide (replaced by N_PMS)
sldIdLst = prs.slides._sldIdLst
def sld_id(slide):
    for e in sldIdLst:
        if prs.slides.part.related_part(e.rId) is slide.part: return e
for _drop in (S_COVER, F_PMS):
    _el = sld_id(_drop)
    prs.part.drop_rel(_el.rId); sldIdLst.remove(_el)

# reorder
els = [sld_id(s) for s in ORDER]
assert len(els) == len(ORDER) == len(set(map(id, els))) and all(e is not None for e in els)
for e in list(sldIdLst): sldIdLst.remove(e)
for e in els: sldIdLst.append(e)

# one footer style everywhere: line at 7.18, page number bottom right
for i, s in enumerate(prs.slides, 1):
    for sh in list(s.shapes):
        if sh.has_text_frame and sh.text_frame.text.strip().isdigit() and sh.left >= Inches(12.3) and sh.top >= Inches(7.15):
            sh._element.getparent().remove(sh._element)
        elif sh.shape_type in (9,) or (sh.height == 0 and sh.top >= Inches(7.2) and sh.width > Inches(12)):
            if sh.top >= Inches(7.2): sh.top = Inches(7.18)
    if i > 1:
        txt(s, 12.55, 7.24, 0.55, 0.16, str(i), 7, MUTED, align=PP_ALIGN.RIGHT)

prs.save(OUT)
print("saved", OUT, "slides", len(prs.slides))
for i, s in enumerate(prs.slides, 1):
    t = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    print(i, "|", (t[2] if len(t) > 2 else t[0])[:95].replace("\n", " "))
