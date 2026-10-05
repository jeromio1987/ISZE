"""Deck and slide drawing helpers.

The older I Motors builders each carried their own copy of these functions, and the copies
had drifted apart (one `rect()` raised on a None fill, the other did not). This module is the
single copy; slides call it and never touch python-pptx colours directly.

Every helper takes the active Palette so one slide body works in charcoal and in light.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import (
    XL_CHART_TYPE,
    XL_LABEL_POSITION,
    XL_LEGEND_POSITION,
    XL_MARKER_STYLE,
    XL_TICK_MARK,
)
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from .palette import Palette

SLIDE_W = 13.333
SLIDE_H = 7.5

# Layout grid, in inches. Panels and rules line up against these.
MARGIN = 0.25
BODY_LEFT = 0.40
BODY_W = 9.20
PANEL_X = 9.86
PANEL_Y = 1.46
PANEL_W = 3.25
PANEL_H = 5.58
FOOTER_Y = 7.18
SOURCE_Y = 7.24


def rgb(hex_no_hash: str) -> RGBColor:
    return RGBColor.from_string(hex_no_hash)


def chart_values(values) -> list:
    """Values ready for a PowerPoint chart series.

    A chart cannot be written with a NaN or an infinity in it: python-pptx fails deep inside
    xlsxwriter with an error that says nothing about which slide. Non-finite values become None,
    which the chart renders as a gap. Every series goes through here.
    """
    out: list = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            out.append(None)
            continue
        if number != number or number in (float("inf"), float("-inf")):
            out.append(None)
        else:
            out.append(number)
    return out


@dataclass
class Slide:
    """One slide plus its palette, so callers do not pass colours around."""

    obj: object                 # pptx.slide.Slide
    pal: Palette
    section: str = ""
    title: str = ""

    # ------------------------------------------------------------------ shapes
    def text(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str | Sequence[str],
        size: float = 10,
        color: str | None = None,
        bold: bool = False,
        align: PP_ALIGN = PP_ALIGN.LEFT,
        anchor: MSO_ANCHOR = MSO_ANCHOR.TOP,
        spacing: float | None = None,
    ):
        tb = self.obj.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        lines = text if isinstance(text, (list, tuple)) else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            if spacing is not None:
                p.space_after = Pt(spacing)
            run = p.add_run()
            run.text = str(line)
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.name = self.pal.font
            run.font.color.rgb = rgb(color or self.pal.ink)
        return tb

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str | None = None,
        line: str | None = None,
        shape: MSO_SHAPE = MSO_SHAPE.RECTANGLE,
    ):
        s = self.obj.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if fill:
            s.fill.solid()
            s.fill.fore_color.rgb = rgb(fill)
        else:
            s.fill.background()
        if line:
            s.line.color.rgb = rgb(line)
            s.line.width = Pt(0.75)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        return s

    def hline(self, x: float, y: float, w: float, color: str | None = None, width: float = 0.75):
        c = self.obj.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y)
        )
        c.line.color.rgb = rgb(color or self.pal.rule)
        c.line.width = Pt(width)
        return c

    # ------------------------------------------------------------------ composites
    def panel(self, points: Sequence[str], x: float = PANEL_X, y: float = PANEL_Y,
              w: float = PANEL_W, h: float = PANEL_H, heading: str = "OBSERVATIONS / QUESTIONS"):
        """Our observations and questions. First point red, the rest amber."""
        self.rect(x, y, w, h, self.pal.panel, self.pal.border or None)
        self.text(x + 0.28, y + 0.26, w - 0.5, 0.2, heading, 7.5, self.pal.accent, True)
        if not points:
            return
        yy = y + 0.72
        step = (h - 0.95) / max(len(points), 1)
        for i, point in enumerate(points):
            self.rect(x + 0.28, yy + 0.07, 0.09, 0.09,
                      self.pal.accent if i == 0 else self.pal.amber, shape=MSO_SHAPE.OVAL)
            self.text(x + 0.52, yy, w - 0.8, max(step - 0.08, 0.2), point, 8.6, self.pal.ink)
            yy += step

    def tile(self, x: float, y: float, w: float, h: float, label: str, big: str,
             sub: str | Sequence[str], color: str | None = None, big_size: float = 24):
        self.rect(x, y, w, h, self.pal.panel, self.pal.border or None)
        self.text(x + 0.18, y + 0.16, w - 0.3, 0.2, label.upper(), 7, self.pal.accent, True)
        self.text(x + 0.18, y + 0.42, w - 0.3, 0.5, big, big_size, color or self.pal.ink, True)
        self.text(x + 0.18, y + 0.98, w - 0.3, max(h - 1.05, 0.3), sub, 7.8, self.pal.muted)

    def table(self, x: float, y: float, col_widths: Sequence[float], header: Sequence[str],
              rows: Iterable[Sequence[str]], row_h: float = 0.38, head_h: float = 0.36,
              bold_cols: Sequence[int] = (0,), zebra: bool = True):
        """A simple ruled table. Column x positions are cumulative from x."""
        xs: list[tuple[float, float]] = []
        cx = x
        for w in col_widths:
            xs.append((cx, w))
            cx += w
        for (cxx, ww), head in zip(xs, header):
            self.rect(cxx, y, ww, head_h, self.pal.header_fill)
            self.text(cxx + 0.06, y, ww - 0.1, head_h, head, 7.5, self.pal.on_header, True,
                      anchor=MSO_ANCHOR.MIDDLE)
        yy = y + head_h
        for i, row in enumerate(rows):
            for j, ((cxx, ww), value) in enumerate(zip(xs, row)):
                fill = self.pal.row2 if (zebra and i % 2 == 0) else self.pal.panel
                self.rect(cxx, yy, ww, row_h, fill)
                self.text(cxx + 0.06, yy, ww - 0.1, row_h, str(value), 8.5, self.pal.ink,
                          j in bold_cols, anchor=MSO_ANCHOR.MIDDLE)
            yy += row_h
        return yy

    def banner(self, text: str, x: float = BODY_LEFT, y: float = 1.85, w: float = BODY_W, h: float = 1.1):
        """The amber 'we cannot show this' panel. Used instead of a blank area."""
        self.rect(x, y, w, h, self.pal.panel, self.pal.border or None)
        self.rect(x, y, 0.08, h, self.pal.amber)
        self.text(x + 0.25, y + 0.16, w - 0.5, 0.25, "DATA UNAVAILABLE", 9, self.pal.amber, True)
        self.text(x + 0.25, y + 0.48, w - 0.5, h - 0.6, text, 9.5, self.pal.ink)

    # ------------------------------------------------------------------ charts
    def chart(self, kind: XL_CHART_TYPE, data: CategoryChartData,
              x: float, y: float, w: float, h: float):
        return self.obj.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), data).chart

    @staticmethod
    def chart_values(values) -> list:
        """Values ready for a chart series: a NaN or an infinity becomes a gap.

        python-pptx fails deep inside xlsxwriter if a chart series holds a non-finite number,
        and the error says nothing about which slide. Every series goes through here.
        """
        out: list = []
        for value in values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                out.append(None)
                continue
            if number != number or number in (float("inf"), float("-inf")):
                out.append(None)
            else:
                out.append(number)
        return out

    def style_chart(self, ch, num_fmt: str = "#,##0", legend: bool = True, axis_fmt: str | None = None):
        ch.font.name = self.pal.font
        ch.font.size = Pt(8)
        ch.font.color.rgb = rgb(self.pal.muted)
        ch.has_title = False
        if legend:
            ch.has_legend = True
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
            ch.legend.font.color.rgb = rgb(self.pal.muted)
            ch.legend.font.size = Pt(8)
        else:
            ch.has_legend = False
        try:
            va = ch.value_axis
            va.has_major_gridlines = True
            va.major_gridlines.format.line.color.rgb = rgb(self.pal.grid)
            va.major_gridlines.format.line.width = Pt(0.5)
            va.format.line.fill.background()
            va.tick_labels.font.color.rgb = rgb(self.pal.muted)
            va.tick_labels.font.size = Pt(7.5)
            va.tick_labels.number_format = num_fmt if axis_fmt is None else axis_fmt
            va.tick_labels.number_format_is_linked = False
            ca = ch.category_axis
            ca.format.line.color.rgb = rgb(self.pal.grid)
            ca.tick_labels.font.color.rgb = rgb(self.pal.muted)
            ca.tick_labels.font.size = Pt(7.5)
        except Exception:
            # Axis formatting is cosmetic. Never let it stop a build.
            pass

    def labels(self, series, fmt: str, color: str | None = None,
               pos: XL_LABEL_POSITION = XL_LABEL_POSITION.OUTSIDE_END, size: float = 7.5):
        dl = series.data_labels
        dl.show_value = True
        dl.number_format = fmt
        dl.number_format_is_linked = False
        dl.font.size = Pt(size)
        dl.font.color.rgb = rgb(color or self.pal.ink)
        dl.font.bold = True
        try:
            dl.position = pos
        except Exception:
            pass

    def bar_fill(self, series, color: str):
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = rgb(color)
        series.format.line.fill.background()

    def line_fmt(self, series, color: str, width: float = 2.25, marker: bool = True, dash: bool = False):
        series.smooth = False
        series.format.line.color.rgb = rgb(color)
        series.format.line.width = Pt(width)
        if dash:
            series.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        try:
            if marker:
                series.marker.style = XL_MARKER_STYLE.CIRCLE
                series.marker.size = 6
                series.marker.format.fill.solid()
                series.marker.format.fill.fore_color.rgb = rgb(color)
                series.marker.format.line.color.rgb = rgb(color)
            else:
                series.marker.style = XL_MARKER_STYLE.NONE
        except Exception:
            pass

    def axis_bounds(self, ch, lo: float | None = None, hi: float | None = None, unit: float | None = None):
        try:
            va = ch.value_axis
            if hi is not None:
                va.maximum_scale = hi
            if lo is not None:
                va.minimum_scale = lo
            if unit is not None:
                va.major_unit = unit
                va.has_major_unit = True
        except Exception:
            pass

    def axis_percent(self, ch):
        try:
            ch.value_axis.tick_labels.number_format = "0%"
            ch.value_axis.tick_labels.number_format_is_linked = False
        except Exception:
            pass


@dataclass
class Deck:
    """A presentation plus the running state a build needs."""

    pal: Palette
    db_display: str
    period_label: str
    footer_note: str = ""
    prs: Presentation = field(default_factory=Presentation)
    slides: list[Slide] = field(default_factory=list)
    _page: int = 0

    def __post_init__(self) -> None:
        self.prs.slide_width = Inches(SLIDE_W)
        self.prs.slide_height = Inches(SLIDE_H)

    @property
    def blank_layout(self):
        return self.prs.slide_layouts[6]

    # ------------------------------------------------------------------ slides
    def cover(self, title_lines: Sequence[str], subtitle: str, note: str, logo: Path | None = None) -> Slide:
        s = self.add(None, None, footer=False)
        s.rect(0, 0, 0.12, SLIDE_H, self.pal.accent)
        s.text(0.85, 1.30, 3.9, 0.2, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 8.5, self.pal.ink, True)
        y = 2.35
        for i, line in enumerate(title_lines):
            s.text(0.85, y, 9.5, 0.85, line, 30 if i else 34, self.pal.ink if i == 0 else self.pal.muted, True)
            y += 0.78
        s.hline(0.85, y + 0.15, 2.2, self.pal.accent, 1.5)
        s.text(0.85, y + 0.42, 9.5, 0.3, subtitle, 11.5, self.pal.muted)
        s.text(0.85, y + 0.95, 9.5, 0.3, note, 9, self.pal.faint)
        if logo is not None and Path(logo).is_file():
            try:
                self.prs.slides[len(self.slides) - 1].shapes.add_picture(
                    str(logo), Inches(11.3), Inches(0.55), height=Inches(0.78)
                )
            except Exception:
                pass
        return s

    def add(self, section: str | None, title: str | None, sub: str | None = None,
            source: str | None = None, footer: bool = True) -> Slide:
        self._page += 1
        raw = self.prs.slides.add_slide(self.blank_layout)
        raw.background.fill.solid()
        raw.background.fill.fore_color.rgb = rgb(self.pal.bg)
        s = Slide(obj=raw, pal=self.pal, section=section or "", title=title or "")
        if footer:
            s.text(MARGIN, 0.10, 4.2, 0.18, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 6.6, self.pal.ink, True)
            if section:
                s.text(MARGIN, 0.43, 6.5, 0.22, section.upper(), 7.5, self.pal.accent, True)
            if title:
                s.text(MARGIN, 0.68, 9.45, 0.66, title,
                       20 if len(title) <= 60 else 16.5, self.pal.ink, True)
            if sub:
                s.text(MARGIN, 1.42, 9.45, 0.24, sub, 8.5, self.pal.muted)
            s.hline(MARGIN, FOOTER_Y, 12.85)
            s.text(MARGIN, SOURCE_Y, 11.5, 0.16, source or self.footer_note, 6.5, self.pal.faint)
            if self._page > 1:
                s.text(12.55, SOURCE_Y, 0.55, 0.16, str(self._page), 7, self.pal.muted, align=PP_ALIGN.RIGHT)
        self.slides.append(s)
        return s

    # ------------------------------------------------------------------ output
    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(path))
        return path

    def slide_count(self) -> int:
        return len(self.prs.slides)
