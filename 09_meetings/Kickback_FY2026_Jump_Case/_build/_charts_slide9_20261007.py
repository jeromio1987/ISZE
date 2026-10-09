# -*- coding: utf-8 -*-
"""Build every chart for the kickback management deck."""
import importlib.util
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
spec = importlib.util.spec_from_file_location("cl", HERE / "_build" / "_charts_lib_20261007.py")
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)

R, I, M, G, T, P, BG, FONT = cl.RED, cl.INK, cl.MUTED, cl.GOLD, cl.TEAL, cl.PANEL, cl.BG, cl.FONT


# ---------------------------------------------------------------- slide 9
def slide9(prs):
    s = prs.slides[8]
    cl.drop(s, "Chart 0", "Chart 1", "Picture 7", "Picture 9", "Picture 24", "Picture 28",
            "ValueBar01", "ValueBar02", "ValueBar03")
    # (a) two-line divergence
    rows = cl.load_csv("portugal_billing_vs_sales_to_dealer.csv")
    cats = [r[""] for r in rows]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("ISZE billed", tuple(round(float(r["ISZE_billed_eur"])) for r in rows))
    cd.add_series("iMotors sales to dealer", tuple(round(float(r["iMotors_sales_to_dealer_eur"])) for r in rows))
    gf = s.shapes.add_chart(XL_CHART_TYPE.LINE, Inches(0.42), Inches(1.86), Inches(6.20), Inches(2.30), cd)
    gf.name = "Chart 0"
    ch = gf.chart
    cl.style_chart(ch, base=7.5, legend=True, legend_pos=XL_LEGEND_POSITION.BOTTOM,
                   plot_layout=(0.105, 0.075, 0.865, 0.700))
    cl.series_color(ch.plots[0].series[0], cl.RED, width=2.25)
    cl.series_color(ch.plots[0].series[1], cl.INK, width=1.5)
    for ser in ch.plots[0].series:
        cl.smooth_off(ser)
        ser.smooth = False
    ch.value_axis.tick_labels.number_format = '#,##0'
    ch.value_axis.major_unit = 50000
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 200000

    # (b) family build in euro
    fam = cl.load_csv("portugal_family_stock_build.csv")
    fam = [r for r in fam if float(r["build"]) > 0]
    fam.sort(key=lambda r: -float(r["build"]))
    top = fam[:6]
    cd2 = CategoryChartData()
    cd2.categories = [r["family"] for r in top]
    cd2.add_series("Net build", tuple(round(float(r["build"])) for r in top))
    gf2 = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(6.62), Inches(1.86),
                             Inches(6.01), Inches(2.30), cd2)
    gf2.name = "Chart 1"
    ch2 = gf2.chart
    cl.style_chart(ch2, base=7.5, legend=False, plot_layout=(0.145, 0.100, 0.830, 0.660))
    cl.series_color(ch2.plots[0].series[0], cl.RED)
    ch2.value_axis.major_unit = 10000
    ch2.value_axis.minimum_scale = 0
    ch2.value_axis.maximum_scale = 60000

    # (c1) 2.2 of 3.0 months against target
    cl.label(s, 4.36, 4.82, 2.90, 0.22, ["reported 2.2 of a 3.0-month target"],
             6.6, cl.MUTED, align=PP_ALIGN.RIGHT)
    bar_bg = s.shapes.add_shape(1, Inches(4.36), Inches(5.06), Inches(2.56), Inches(0.20))
    bar_bg.name = "ValueBar01"
    bar_bg.fill.solid(); bar_bg.fill.fore_color.rgb = RGB_DARK()
    bar_bg.line.fill.background()
    bar = s.shapes.add_shape(1, Inches(4.36), Inches(5.06), Inches(2.56 * 2.2 / 3.0), Inches(0.20))
    bar.name = "ValueBar01"
    bar.fill.solid(); bar.fill.fore_color.rgb = cl.TEAL
    bar.line.fill.background()

    # (c2) brake part: billed 468 vs sold on 254, in euro terms is not possible,
    # so the two bars are labelled as euro values from the source part file.
    cl.label(s, 4.83, 5.05, 3.90, 0.18, ["EUR 16,923 held, of the EUR 30,900 billed"], 7.0, cl.MUTED)
    b1 = s.shapes.add_shape(1, Inches(4.83), Inches(5.26), Inches(3.90), Inches(0.17))
    b1.fill.solid(); b1.fill.fore_color.rgb = cl.RED; b1.line.fill.background()
    b2 = s.shapes.add_shape(1, Inches(4.83), Inches(5.50), Inches(3.90 * 0.454), Inches(0.17))
    b2.name = "ValueBar03"
    b2.fill.solid(); b2.fill.fore_color.rgb = cl.MUTED; b2.line.fill.background()


def RGB_DARK():
    from pptx.dml.color import RGBColor
    return RGBColor(0x44, 0x44, 0x44)


if __name__ == "__main__":
    prs = Presentation(str(cl.DECK))
    slide9(prs)
    prs.save(str(cl.DECK))
    print("slide 9 charts built")

    # restore zero-state: sizes and hash
    import hashlib
    b = open(cl.DECK, "rb").read()
    print("bytes", len(b), hashlib.sha256(b).hexdigest().upper()[:16])
