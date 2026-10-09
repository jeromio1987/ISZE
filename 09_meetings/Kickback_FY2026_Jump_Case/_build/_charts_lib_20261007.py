# -*- coding: utf-8 -*-
"""
Native charts for the kickback management deck, 2026-10-07.

Everything is euro: no series, axis or label carries pieces or units. The chart
frame gets an explicit manual plot-area layout so a run-rate line and a vertical
event marker can be placed on the exact euro value rather than eyeballed.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import lxml.etree as E
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
DECK = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_stock_insights_20261007")

RED = RGBColor(0xE3, 0x06, 0x13)
INK = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
GOLD = RGBColor(0xC8, 0x9B, 0x3C)
TEAL = RGBColor(0x4E, 0x9A, 0x9A)
PANEL = RGBColor(0x30, 0x30, 0x30)
BG = RGBColor(0x26, 0x26, 0x26)
FONT = "Aptos"

C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


# ---------------------------------------------------------------- helpers
def _sub(parent, tag, **attrs):
    el = E.SubElement(parent, C + tag)
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


def font_el(parent, size, rgb, bold=False):
    rpr = _sub(parent, "txPr")
    body = _sub(rpr, "bodyPr", rot="0", spcFirstLastPara="1", vertOverflow="ellipsis",
                horzOverflow="ellipsis", vert="horz", wrap="square", anchor="ctr",
                anchorCtr="0")
    _sub(body, "noAutofit")
    p = _sub(rpr, "p")
    ppr = _sub(p, "pPr", marL="0", marR="0", marT="0", marB="0", indent="0", algn="ctr")
    for tag in ("defRPr",):
        d = _sub(ppr, tag, sz=int(size * 100), b="1" if bold else "0", i="0", u="none",
                 strike="noStrike", kern="1200", baseline="0")
        fill = _sub(d, "solidFill")
        _sub(fill, "srgbClr", val="%02X%02X%02X" % (rgb[0], rgb[1], rgb[2]))
        latin = _sub(d, "latin", typeface=FONT)
        _sub(d, "ea", typeface="")
        _sub(d, "cs", typeface="")
    return rpr


def style_chart(chart, base=8.0, legend=False, legend_pos=XL_LEGEND_POSITION.BOTTOM,
                plot_layout=(0.085, 0.075, 0.875, 0.760), chart_fill=None):
    chart.font.name = FONT
    chart.font.size = Pt(base)
    chart.font.color.rgb = MUTED
    chart.has_title = False
    chart.has_legend = legend
    if legend:
        chart.legend.position = legend_pos
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(base)
        chart.legend.font.color.rgb = MUTED

    sp = chart._chartSpace

    # the chart frame needs its own solid fill: without it the chart is
    # transparent and the slide text underneath shows through the plot, which
    # is what made the first cut of these charts unreadable. c:spPr must sit
    # after c:chart and before c:txPr in c:chartSpace.
    fill_rgb = chart_fill if chart_fill is not None else BG
    old = sp.find(C + "spPr")
    if old is not None:
        sp.remove(old)
    spPr = E.Element(C + "spPr")
    xfrm = _sub(spPr, "xfrm")
    _sub(xfrm, "off", x="0", y="0")
    _sub(xfrm, "ext", cx="0", cy="0")
    geom = _sub(spPr, "prstGeom", prst="rect")
    _sub(geom, "avLst")
    sf = _sub(spPr, "solidFill")
    _sub(sf, "srgbClr", val="%02X%02X%02X" % (fill_rgb[0], fill_rgb[1], fill_rgb[2]))
    ln = _sub(spPr, "ln")
    _sub(ln, "noFill")
    _sub(spPr, "effectLst")
    anchor_el = sp.find(C + "txPr")
    if anchor_el is not None:
        anchor_el.addprevious(spPr)
    else:
        sp.append(spPr)

    # the plot area also gets an explicit fill so gridlines and labels sit on
    # the same charcoal rather than on the slide behind
    cs = sp.find(C + "chart")
    if cs is not None:
        plot_area = cs.find(C + "plotArea")
        if plot_area is not None:
            oldpa = plot_area.find(C + "spPr")
            if oldpa is not None:
                plot_area.remove(oldpa)
            psp = E.Element(C + "spPr")
            g2 = _sub(psp, "prstGeom", prst="rect")
            _sub(g2, "avLst")
            s2 = _sub(psp, "solidFill")
            _sub(s2, "srgbClr", val="%02X%02X%02X" % (fill_rgb[0], fill_rgb[1], fill_rgb[2]))
            l2 = _sub(psp, "ln")
            _sub(l2, "noFill")
            _sub(psp, "effectLst")
            plot_area.append(psp)
            for old in plot_area.findall(C + "layout"):
                plot_area.remove(old)
            lay = E.Element(C + "layout")
            ml = _sub(lay, "manualLayout")
            _sub(ml, "layoutTarget", val="inner")
            for tag, val in (("xMode", "edge"), ("yMode", "edge"),
                             ("wMode", "factor"), ("hMode", "factor")):
                _sub(ml, tag, val=val)
            _sub(ml, "x", val=str(plot_layout[0]))
            _sub(ml, "y", val=str(plot_layout[1]))
            _sub(ml, "w", val=str(plot_layout[2]))
            _sub(ml, "h", val=str(plot_layout[3]))
            plot_area.insert(0, lay)

    ca = chart.category_axis
    ca.has_major_gridlines = False
    ca.has_minor_gridlines = False
    ca.format.line.color.rgb = RGBColor(0x55, 0x55, 0x55)
    ca.major_tick_mark = XL_TICK_MARK.NONE
    ca.tick_labels.font.size = Pt(base)
    ca.tick_labels.font.color.rgb = MUTED
    ca.tick_labels.font.name = FONT
    va = chart.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = RGBColor(0x3C, 0x3C, 0x3C)
    va.major_gridlines.format.line.width = Pt(0.5)
    va.major_tick_mark = XL_TICK_MARK.NONE
    va.tick_labels.font.size = Pt(base)
    va.tick_labels.font.color.rgb = MUTED
    va.tick_labels.font.name = FONT
    va.tick_labels.number_format = '#,##0'
    va.tick_labels.number_format_is_linked = False
    va.format.line.fill.background()
    return chart


def series_color(ser, rgb, width=None, dash=None):
    if width:
        ser.format.line.color.rgb = rgb
        ser.format.line.width = Pt(width)
    else:
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = rgb
        ser.format.line.fill.background()


def smooth_off(ser):
    sp = ser._element
    for tag in ("smooth",):
        old = sp.find(C + tag)
        if old is not None:
            sp.remove(old)
    _sub(sp, "smooth", val="0")


def tick_skip(axis, skip):
    """Show every (skip+1)-th tick label on a category axis."""
    ax = axis._element
    for tag in ("tickLblSkip", "tickMarkSkip"):
        for old in ax.findall(C + tag):
            ax.remove(old)
    # both must appear, in this order, right after c:delete/c:axId block
    _sub(ax, "tickLblSkip", val=str(skip))
    _sub(ax, "tickMarkSkip", val=str(skip))
    return axis


def euro_tick(chart, unit=250000, maxv=None):
    va = chart.value_axis
    va.minimum_scale = 0
    if maxv:
        va.maximum_scale = maxv
    va.major_unit = unit
    va.tick_labels.number_format = '#,##0'
    va.tick_labels.number_format_is_linked = False


def hline(slide, x, y, w, rgb=GOLD, width=1.5, dash=True):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                   Inches(x + w), Inches(y))
    c.line.color.rgb = rgb
    c.line.width = Pt(width)
    if dash:
        ln = c.line._get_or_add_ln()
        for old in ln.findall(A + "prstDash"):
            ln.remove(old)
        d = E.SubElement(ln, A + "prstDash")
        d.set("val", "dash")
    return c


def vline(slide, x, y0, y1, rgb=RED, width=1.5):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y0),
                                   Inches(x), Inches(y1))
    c.line.color.rgb = rgb
    c.line.width = Pt(width)
    return c


def label(slide, x, y, w, h, lines, size, rgb, bold=False, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP):
    sh = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
    first = True
    for line in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = rgb
    return sh


def drop(slide, *names):
    for sh in list(slide.shapes):
        if sh.name in names:
            sh._element.getparent().remove(sh._element)


# ---------------------------------------------------------------- data
def load_csv(name):
    with open(DATA / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    print("import me")
