# -*- coding: utf-8 -*-
"""
Chart builders for the kickback management deck, 2026-10-07.

One function per slide. Every series is euro; no axis, series or label carries
pieces or units. Sourced euro only - nothing is derived that the source does not
already state.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
spec = importlib.util.spec_from_file_location("cl", HERE / "_build" / "_charts_lib_20261007.py")
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)

RED, INK, MUTED, GOLD, TEAL = cl.RED, cl.INK, cl.MUTED, cl.GOLD, cl.TEAL
TRACK = RGBColor(0x44, 0x44, 0x44)


def bar(slide, x, y, w, h, frac, rgb, name="ValueBar", track=True):
    """A filled euro/quantity bar with an optional dark track behind it."""
    if track:
        t = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        t.name = name + "Track"
        t.fill.solid(); t.fill.fore_color.rgb = TRACK
        t.line.fill.background()
        t.shadow.inherit = False
    b = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                               Inches(w * max(0.02, min(1.0, frac))), Inches(h))
    b.name = name
    b.fill.solid(); b.fill.fore_color.rgb = rgb
    b.line.fill.background()
    b.shadow.inherit = False
    return b


def tick(slide, x, y, h, rgb=GOLD):
    t = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y - 0.02), Inches(0.022), Inches(h + 0.04))
    t.name = "TargetTick"
    t.fill.solid(); t.fill.fore_color.rgb = rgb
    t.line.fill.background()
    t.shadow.inherit = False
    return t


# ------------------------------------------------------------------ slide 9
def slide9(prs):
    s = prs.slides[8]
    cl.drop(s, "Chart 0", "Chart 1", "Chart 2", "Chart 3", "Picture 7", "Picture 9",
            "Picture 24", "Picture 28", "ValueBarA", "ValueBarATrack", "ValueBarB",
            "ValueBarBTrack", "ValueBarC", "ValueBarCTrack", "TargetTick",
            "MiniLabel", "MiniLabel2")

    rows = cl.load_csv("portugal_billing_vs_sales_to_dealer.csv")
    cats = [r[""] for r in rows]

    # (a) the divergence: two lines, euro per month, in the slot Picture 7 held
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("ISZE billed", tuple(round(float(r["ISZE_billed_eur"])) for r in rows))
    cd.add_series("iMotors sales to dealer", tuple(round(float(r["iMotors_sales_to_dealer_eur"])) for r in rows))
    gf = s.shapes.add_chart(XL_CHART_TYPE.LINE, Inches(0.42), Inches(1.86),
                            Inches(6.20), Inches(2.28), cd)
    gf.name = "Chart 0"
    ch = gf.chart
    cl.style_chart(ch, base=7.0, legend=True, legend_pos=XL_LEGEND_POSITION.TOP,
                   plot_layout=(0.100, 0.155, 0.870, 0.660))
    cl.series_color(ch.plots[0].series[0], RED, width=2.25)
    cl.series_color(ch.plots[0].series[1], INK, width=1.5)
    for ser in ch.plots[0].series:
        cl.smooth_off(ser)
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 200000
    ch.value_axis.major_unit = 50000
    cl.tick_skip(ch.category_axis, 1)

    # (b) the family build in euro, in the slot Picture 9 held
    fam = [r for r in cl.load_csv("portugal_family_stock_build.csv") if float(r["build"]) > 0]
    fam.sort(key=lambda r: -float(r["build"]))
    top = fam[:6]
    cd2 = CategoryChartData()
    cd2.categories = [r["family"] for r in top]
    cd2.add_series("Net build", tuple(round(float(r["build"])) for r in top))
    gf2 = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(6.62), Inches(1.86),
                             Inches(6.01), Inches(2.28), cd2)
    gf2.name = "Chart 1"
    ch2 = gf2.chart
    cl.style_chart(ch2, base=7.0, legend=False, plot_layout=(0.150, 0.090, 0.825, 0.665))
    cl.series_color(ch2.plots[0].series[0], RED)
    ch2.value_axis.minimum_scale = 0
    ch2.value_axis.maximum_scale = 50000
    ch2.value_axis.major_unit = 10000

    # (c) the two lines again as a small native chart, in the slot Picture 24 held
    cd3 = CategoryChartData()
    cd3.categories = cats
    cd3.add_series("Billed", tuple(round(float(r["ISZE_billed_eur"])) for r in rows))
    cd3.add_series("Sales to dealer", tuple(round(float(r["iMotors_sales_to_dealer_eur"])) for r in rows))
    gf3 = s.shapes.add_chart(XL_CHART_TYPE.LINE, Inches(4.83), Inches(4.96),
                             Inches(3.86), Inches(0.96), cd3)
    gf3.name = "Chart 2"
    ch3 = gf3.chart
    cl.style_chart(ch3, base=5.4, legend=False, plot_layout=(0.105, 0.080, 0.880, 0.900))
    cl.series_color(ch3.plots[0].series[0], RED, width=1.75)
    cl.series_color(ch3.plots[0].series[1], MUTED, width=1.25)
    for ser in ch3.plots[0].series:
        cl.smooth_off(ser)
    ch3.value_axis.minimum_scale = 0
    ch3.value_axis.maximum_scale = 200000
    ch3.value_axis.major_unit = 200000
    ch3.value_axis.has_major_gridlines = False
    ch3.value_axis.delete = True
    ch3.category_axis.delete = True
    cl.label(s, 4.83, 5.99, 3.90, 0.30,
             ["Red = ISZE billed, grey = sales to dealer.",
              "Euro a month, 2025-01 to 2026-08. Full detail on the left."],
             6.2, MUTED)

    # (d) the single brake part: the campaign window against the four months after
    cl.label(s, 9.06, 4.76, 3.80, 0.17,
             ["One brake part: EUR 46,426 billed in the campaign window,"],
             6.2, MUTED)
    cl.label(s, 9.06, 4.93, 3.80, 0.17,
             ["EUR 17,109 in the four months after."], 6.2, MUTED)
    bar(s, 9.06, 5.16, 3.66, 0.15, 1.0, RED, name="ValueBarC")
    bar(s, 9.06, 5.38, 3.66, 0.15, 17109.0 / 46426.0, MUTED, name="ValueBarA")
    cl.label(s, 9.06, 5.58, 3.80, 0.16,
             ["campaign window = 100%, four months after = 37%"],
             6.2, MUTED)
    print("slide 9: 3 native charts + brake-part euro bars")


# ------------------------------------------------------------------ slide 10
def slide10(prs):
    s = prs.slides[9]
    cl.drop(s, "ValueBarA", "ValueBarATrack", "ValueBarB", "ValueBarBTrack",
            "ValueBarC", "ValueBarCTrack", "TargetTick")
    # three cards, each with a euro bar showing the card's figure against the
    # largest of the three, so the three cases are comparable at a glance
    bar(s, 0.60, 4.06, 3.68, 0.17, 225744.0 / 764436.0, RED, name="ValueBarA")
    bar(s, 4.83, 4.06, 3.68, 0.17, 764436.0 / 764436.0, RED, name="ValueBarB")
    bar(s, 9.06, 4.06, 3.68, 0.17, 678464.0 / 764436.0, GOLD, name="ValueBarC")
    cl.label(s, 0.60, 4.26, 3.68, 0.16, ["bar scale: the largest of the three cases"], 6.4, MUTED)
    print("slide 10: 3 euro bars")


# ------------------------------------------------------------------ slide 12
def slide12(prs):
    s = prs.slides[11]
    cl.drop(s, "Chart 0", "Chart 1", "RunRateLine", "PriceMarker", "PriceMarkerLabel")
    rows = [r for r in cl.load_csv("billing_monthly_by_distributor.csv")
            if r["distributor"] == "ITUK" and r["ym"] >= "2025-04" and r["ym"] <= "2026-04"]
    cats = [r["ym"] for r in rows]
    vals = [round(float(r["net_sales_value"])) for r in rows]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("ITUK billed", tuple(vals))
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.42), Inches(3.06),
                            Inches(12.49), Inches(2.42), cd)
    gf.name = "Chart 0"
    ch = gf.chart
    cl.style_chart(ch, base=7.5, legend=False, plot_layout=(0.075, 0.130, 0.905, 0.740))
    cl.series_color(ch.plots[0].series[0], RED)
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 1000000
    ch.value_axis.major_unit = 250000

    # run-rate reference line and the February column highlight
    # plot area runs x 0.42+0.075*12.49 .. and y 3.06+0.130*2.42 ..
    px0 = 0.42 + 0.075 * 12.49
    px1 = 0.42 + (0.075 + 0.905) * 12.49
    py1 = 3.06 + (0.130 + 0.740) * 2.42
    n = len(rows)
    slot = (px1 - px0) / n
    def xc(i):
        return px0 + slot * (i + 0.5)
    def yv(v):
        return py1 - (v / 1000000.0) * (py1 - (3.06 + 0.130 * 2.42))
    # run rate 515,524 and Feb 861,719
    yrun = yv(515523.96)
    cl.hline(s, px0, yrun, px1 - px0, GOLD, 1.5)
    cl.label(s, px1 - 2.55, yrun - 0.20, 2.55, 0.20,
             ["run rate EUR 515,524 / month"], 6.8, GOLD, align=PP_ALIGN.RIGHT)
    ifeb = cats.index("2026-02")
    xfeb = xc(ifeb)
    cl.label(s, xfeb - 1.55, yv(861719) - 0.24, 1.55, 0.22,
             ["EUR 861,719"], 7.4, INK, bold=True, align=PP_ALIGN.LEFT)
    # the price change happened between 2026-03 and 2026-04, i.e. at the boundary
    imar = cats.index("2026-03")
    xmar = px0 + slot * (imar + 1)
    cl.vline(s, xmar, 3.06 + 0.130 * 2.42, py1, RED, 1.75)
    cl.label(s, max(7.30, xmar - 4.06), 3.10, min(4.00, xmar - 7.24), 0.36,
             ["price list changed 13 March 2026",
              "March EUR 940,567; April EUR 529,085"], 6.8, RED, align=PP_ALIGN.RIGHT)
    print("slide 12: column chart + run-rate line + 13 March marker")


# ------------------------------------------------------------------ slide 13
def slide13(prs):
    s = prs.slides[12]
    cl.drop(s, "Chart 0", "RunRateLine", "PriceMarker", "PriceMarkerLabel")
    rows = [r for r in cl.load_csv("billing_monthly_by_distributor.csv")
            if r["distributor"] == "ITUK" and r["ym"] >= "2025-04" and r["ym"] <= "2026-04"]
    cats = [r["ym"] for r in rows]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("ITUK billed", tuple(round(float(r["net_sales_value"])) for r in rows))
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.42), Inches(3.06),
                            Inches(12.49), Inches(2.42), cd)
    gf.name = "Chart 0"
    ch = gf.chart
    cl.style_chart(ch, base=7.5, legend=False, plot_layout=(0.075, 0.130, 0.905, 0.740))
    cl.series_color(ch.plots[0].series[0], RED)
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 1000000
    ch.value_axis.major_unit = 250000
    px0 = 0.42 + 0.075 * 12.49
    px1 = 0.42 + (0.075 + 0.905) * 12.49
    py1 = 3.06 + (0.130 + 0.740) * 2.42
    py0 = 3.06 + 0.130 * 2.42
    n = len(rows)
    slot = (px1 - px0) / n
    yrun = py1 - (515523.96 / 1000000.0) * (py1 - py0)
    cl.hline(s, px0, yrun, px1 - px0, GOLD, 1.5)
    cl.label(s, px1 - 2.55, yrun - 0.20, 2.55, 0.20,
             ["run rate EUR 515,524 / month"], 6.8, GOLD, align=PP_ALIGN.RIGHT)
    imar = cats.index("2026-03")
    xmar = px0 + slot * (imar + 0.72)
    cl.vline(s, xmar, py0, py1, RED, 1.75)
    cl.label(s, max(6.60, xmar - 4.42), 3.10, min(4.36, xmar - 6.54), 0.36,
             ["13 March 2026: old EUR 517,104 in 1-12 March,",
              "new EUR 423,463 in 13-31 March. Volume 2.32x -> 0.60x"],
             6.8, RED, align=PP_ALIGN.RIGHT)
    print("slide 13: column chart + run-rate line + intra-month marker")


# ------------------------------------------------------------------ slide 8
def slide8(prs):
    s = prs.slides[7]
    cl.drop(s, "ValueBarA", "ValueBarATrack", "ValueBarB", "ValueBarBTrack",
            "ValueBarC", "ValueBarCTrack", "TargetTick", "DataBar")
    # data bars under the billed figure in the "Billed FY2026" column: the same
    # euro is already printed, so the bar adds magnitude without a second number
    rows = [("IUK", 5.40, 6.05), ("UTI", 2.93, 3.24), ("UMI", 2.71, 3.08),
            ("Germany", 2.59, 2.73), ("Benelux", 2.22, 2.20), ("Portugal", 1.72, 1.85),
            ("Sweden", 1.30, 1.44), ("Norway", 1.55, 1.65), ("Ireland", 1.16, 1.15)]
    ys = [2.29, 2.66, 3.03, 3.40, 3.77, 4.14, 4.51, 4.88, 5.25]
    biggest = max(b for _, _, b in rows)
    for (name, plan, billed), y in zip(rows, ys):
        rgb = cl.RED if billed >= plan else cl.MUTED
        b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.76), Inches(y + 0.245),
                               Inches(1.45 * billed / biggest), Inches(0.048))
        b.name = "DataBar"
        b.fill.solid(); b.fill.fore_color.rgb = rgb
        b.line.fill.background(); b.shadow.inherit = False
    # the nine-distributor total, in gold, on its own row
    b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.76), Inches(5.865),
                           Inches(1.45), Inches(0.048))
    b.name = "DataBar"
    b.fill.solid(); b.fill.fore_color.rgb = cl.GOLD
    b.line.fill.background(); b.shadow.inherit = False
    print("slide 8: 10 euro data bars in the billed column")


# ------------------------------------------------------------------ slide 12
def _kill_table(s, keep_names=()):
    """Remove the small value table on 12/13: its figures are re-printed on the chart."""
    kill = []
    for sh in list(s.shapes):
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if sh.name in keep_names:
            continue
        if t in ("ITUK, FY2026", "Billed", "Position / comparison",
                 "Period", "vs its own run rate"):
            kill.append(sh)
        elif t.startswith(("Run rate, Apr 2025", "January 2026 position", "February 2026",
                           "March 2026", "1–12 March 2026", "13–31 March 2026", "April 2026")):
            kill.append(sh)
        elif any(sh.text_frame.text.strip() == v for v in
                 ("EUR 515,523.96 per month", "EUR 5,155,239.59 accumulated",
                  "5.6% behind plan", "EUR 861,719.17", "EUR 940,566.54",
                  "+EUR 346,195.21 over run rate", "+EUR 425,042.58 over run rate",
                  "—", "EUR 517,104", "EUR 423,463", "EUR 529,085",
                  "+EUR 346,195.21 (1.67×)", "2.54× euro, 2.32× volume",
                  "Volume fell to 0.60×", "Returned towards its run rate")):
            kill.append(sh)
    for sh in kill:
        sh._element.getparent().remove(sh._element)
    return len(kill)


def slide12(prs):
    s = prs.slides[11]
    cl.drop(s, "Chart 0", "RunRateLine", "PriceMarker", "PriceMarkerLabel", "TopNote")
    n = _kill_table(s)
    rows = [r for r in cl.load_csv("billing_monthly_by_distributor.csv")
            if r["distributor"] == "ITUK" and "2025-04" <= r["ym"] <= "2026-04"]
    cats = [r["ym"] for r in rows]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("ITUK billed", tuple(round(float(r["net_sales_value"])) for r in rows))
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.42), Inches(2.80),
                            Inches(12.49), Inches(2.56), cd)
    gf.name = "Chart 0"
    ch = gf.chart
    # a reserved band at the top of the chart carries the annotations, so no
    # inline label has to sit on top of the tall February and March columns
    cl.style_chart(ch, base=7.5, legend=False, plot_layout=(0.068, 0.205, 0.918, 0.680))
    cl.series_color(ch.plots[0].series[0], cl.RED)
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 1000000
    ch.value_axis.major_unit = 250000
    px0 = 0.42 + 0.068 * 12.49
    px1 = 0.42 + (0.068 + 0.918) * 12.49
    py0 = 2.80 + 0.205 * 2.56
    py1 = 2.80 + (0.205 + 0.680) * 2.56
    slot = (px1 - px0) / len(cats)
    def yv(v):
        return py1 - (v / 1000000.0) * (py1 - py0)
    # run-rate reference line only; its meaning is stated in the band above
    cl.hline(s, px0, yv(515523.96), px1 - px0, cl.GOLD, 1.5)
    # the price change landed between March and April
    imar = cats.index("2026-03")
    xmar = px0 + slot * (imar + 1)
    cl.vline(s, xmar, py0, py1, cl.RED, 1.75)
    # the annotation band, left / centre / right, no overlap
    cl.label(s, px0, 2.88, 4.05, 0.40,
             ["Gold dashed line: the run rate,",
              "EUR 515,524 per month, Apr 2025 to Jan 2026."], 7.2, cl.GOLD)
    cl.label(s, px0 + 4.20, 2.88, 3.10, 0.40,
             ["February EUR 861,719, the highest month,",
              "+EUR 346,195 over its own run rate."], 7.2, cl.INK, bold=True)
    cl.label(s, px1 - 4.05, 2.88, 4.05, 0.40,
             ["Red line: price list changed 13 March 2026.",
              "March EUR 940,567, April EUR 529,085."], 7.2, cl.RED, align=PP_ALIGN.RIGHT)
    cl.label(s, 0.42, 5.44, 12.49, 0.22,
             ["January 2026 position: EUR 5,155,239.59 accumulated, 5.6% behind plan.  "
              "The former value table was removed because the chart above now plots its rows."],
             7.4, cl.MUTED)
    print("slide 12: table of %d boxes replaced by column chart + run-rate line" % n)


# ------------------------------------------------------------------ slide 13
def slide13(prs):
    s = prs.slides[12]
    cl.drop(s, "Chart 0", "RunRateLine", "PriceMarker", "PriceMarkerLabel", "TopNote")
    n = _kill_table(s)
    rows = [r for r in cl.load_csv("billing_monthly_by_distributor.csv")
            if r["distributor"] == "ITUK" and "2025-04" <= r["ym"] <= "2026-04"]
    cats = [r["ym"] for r in rows]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("ITUK billed", tuple(round(float(r["net_sales_value"])) for r in rows))
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.42), Inches(2.80),
                            Inches(12.49), Inches(2.52), cd)
    gf.name = "Chart 0"
    ch = gf.chart
    cl.style_chart(ch, base=7.5, legend=False, plot_layout=(0.068, 0.200, 0.918, 0.685))
    cl.series_color(ch.plots[0].series[0], cl.RED)
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 1000000
    ch.value_axis.major_unit = 250000
    px0 = 0.42 + 0.068 * 12.49
    px1 = 0.42 + (0.068 + 0.918) * 12.49
    py0 = 2.80 + 0.200 * 2.52
    py1 = 2.80 + (0.200 + 0.685) * 2.52
    slot = (px1 - px0) / len(cats)
    def yv(v):
        return py1 - (v / 1000000.0) * (py1 - py0)
    cl.hline(s, px0, yv(515523.96), px1 - px0, cl.GOLD, 1.5)
    # the change is inside March, so the marker splits the March column
    imar = cats.index("2026-03")
    xmar = px0 + slot * (imar + 0.62)
    cl.vline(s, xmar, py0, py1, cl.RED, 1.75)
    cl.label(s, px0, 2.88, 4.05, 0.40,
             ["Gold dashed line: the run rate,",
              "EUR 515,524 per month, Apr 2025 to Jan 2026."], 7.2, cl.GOLD)
    cl.label(s, px0 + 4.20, 2.88, 3.10, 0.40,
             ["February EUR 861,719, +EUR 346,195",
              "(1.67x its own run rate)."], 7.2, cl.INK, bold=True)
    cl.label(s, px1 - 4.05, 2.88, 4.05, 0.40,
             ["Red line splits March at 13 March 2026:",
              "1-12 March EUR 517,104 (2.32x volume);"],
             7.2, cl.RED, align=PP_ALIGN.RIGHT)
    cl.label(s, px1 - 4.05, 3.30, 4.05, 0.20,
             ["13-31 March EUR 423,463 (volume 0.60x)."], 7.2, cl.RED, align=PP_ALIGN.RIGHT)
    cl.label(s, 0.42, 5.40, 12.49, 0.22,
             ["April 2026 EUR 529,085, returned towards its run rate.  "
              "The former value table was removed because the chart above now plots its rows."],
             7.4, cl.MUTED)
    print("slide 13: table of %d boxes replaced by column chart + run-rate line" % n)


# ------------------------------------------------------------------ slide 21
def slide21(prs):
    s = prs.slides[20]
    # The slide already carries a visual chain: four large chevron panels
    # (Chevron 8/13/18/23) with a down arrow under each landing on the tension
    # block. Adding more arrow furniture to that would be filler, so the only
    # job here is to remove the earlier pass's clutter.
    cl.drop(s, "FlowArrow", "FlowRule", "FlowStep", "StageBar")
    print("slide 21: left as designed (chevron chain + arrows into the tension block)")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "9"
    prs = Presentation(str(cl.DECK))
    {"8": slide8, "9": slide9, "10": slide10, "12": slide12,
     "13": slide13, "21": slide21}[which](prs)
    prs.save(str(cl.DECK))
    import hashlib
    b = open(cl.DECK, "rb").read()
    print("bytes", len(b), "sha", hashlib.sha256(b).hexdigest().upper()[:16])
