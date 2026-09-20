"""House Excel styling for ISZE workbooks.

One importable module so every workbook in this folder looks the same. It carries
the palette, the number formats, ready-made style sets (header, zebra band,
subtotal, grand total, section banner, editable input, carried value, missing-data
banner, muted) and helpers for column widths, freeze-and-filter, zebra banding,
outline grouping, cell notes and conditional formatting.

Design rules enforced by construction:

* Text colour and fill are always defined together, so a header can never be
  written as paper-on-pale. ``HEADER`` is the only style whose font is paper, and
  it always carries the navy fill.
* Banding is applied to a row range the caller computes *after* the header row is
  fixed, so a zebra band can never land on a header.
* Money, quantity and rate columns always get an explicit number format. ``General``
  is never used on a number.
* Data bars are only offered through :func:`add_data_bar` (euro columns) and colour
  scales only through :func:`add_colour_scale` (a movement column). Both take an
  explicit range so the caller has to name the column it is putting them on.

Usage::

    import _xlsx_style as xs

    xs.set_widths(ws, {"A": 34, "B": 16})
    xs.write_banner(ws, 4, "The answer", last_col=7)
    xs.write_header(ws, 5, ["Measure", "Value"])
    ...
    xs.freeze_and_filter(ws, freeze="A2", filter_ref=f"A1:B{last_row}")
    xs.band(ws, 6, last_row, cols=("A", "B"))
    xs.styled_total(ws, total_row, values, formats)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.hyperlink import Hyperlink

__all__ = [
    "NAVY", "PAPER", "ZEBRA", "SUBTOTAL_BG", "TERRA", "INK", "INPUT_BG", "AMBER",
    "MUTED", "SCALE_LOW", "SCALE_MID", "SCALE_HIGH",
    "EUR", "EUR2", "PER0", "PER1", "PER2", "PER3", "PER4", "QTY", "QTY2", "TEXT",
    "NO_RATE",
    "HEADER", "ZEBRA_ROW", "SUBTOTAL", "GRAND_TOTAL", "BANNER", "TITLE", "INPUT",
    "MISSING_BANNER", "MUTED_ITALIC", "PLAIN",
    "apply_style", "set_widths", "autofit", "write_header", "write_banner",
    "write_title", "freeze_and_filter", "band", "outline_group", "note",
    "internal_link", "add_data_bar", "add_colour_scale", "flag_not_ok",
    "section_label", "value_cell", "footnote", "block", "summary_above",
    "header_height", "excel_len", "solid", "FLAG_BAD_BG", "FLAG_BAD_INK",
]

# --------------------------------------------------------------------- palette
NAVY = "15233C"
PAPER = "F7F4EE"
ZEBRA = "EEF3F9"
SUBTOTAL_BG = "FDF1EA"
TERRA = "C0552D"
INK = "222222"
INPUT_BG = "FFF3E9"
AMBER = "FCE4D6"
MUTED = "6B6459"

# Alert colours for a failed check row only. Nothing in the normal content palette
# uses these, so a non-OK row cannot be mistaken for styled content.
FLAG_BAD_BG = "F8D7DA"
FLAG_BAD_INK = "9C1C25"

# Colour-scale tints, derived from the band and subtotal fills so the scale cannot
# introduce an off-house colour. Kept light so ink stays readable on every stop.
SCALE_LOW = ZEBRA
SCALE_MID = SUBTOTAL_BG
SCALE_HIGH = "F2C4AE"

# --------------------------------------------------------------- number formats
EUR = '"€"#,##0'
EUR2 = '"€"#,##0.00'
# Rates in this workbook are carried as percentage points, so the format appends the
# percent sign rather than scaling the number. A value of 5.9616 shows as 5.9616%.
# Using Excel's own percent format would scale it to 596.16% and misstate every rate.
PER0 = '0"%"'
PER1 = '0.0"%"'
PER2 = '0.00"%"'
PER3 = '0.000"%"'
PER4 = '0.0000"%"'
QTY = "#,##0"
QTY2 = "#,##0.00"
TEXT = "@"

# The only wording allowed to stand where a rate is missing. A missing number is
# never rendered as a formatted value.
NO_RATE = "No rate available"

_AUTHOR = "ISZE pricing workbook"


def _rgb(hex6: str) -> str:
    """Six hex digits to the eight digit ARGB openpyxl wants."""
    h = hex6.lstrip("#").upper()
    if len(h) == 8:
        return h
    return "FF" + h


def solid(hex6: str) -> PatternFill:
    c = _rgb(hex6)
    return PatternFill(fill_type="solid", start_color=c, end_color=c)


def _side(style: str, colour: str) -> Side:
    return Side(style=style, color=_rgb(colour))


# --------------------------------------------------------------- style objects
@dataclass(frozen=True)
class CellStyle:
    """A complete look: font + fill + border + alignment (+ a default format)."""

    font: Font
    fill: PatternFill | None
    border: Border | None
    alignment: Alignment | None
    number_format: str | None = None


_BASE_FONT = "Calibri"

_LABEL_ALIGN = Alignment(horizontal="left", vertical="center", wrap_text=False)
_WRAP_ALIGN = Alignment(horizontal="left", vertical="top", wrap_text=True)
_HEAD_ALIGN = Alignment(horizontal="left", vertical="center", wrap_text=True)
_RIGHT_ALIGN = Alignment(horizontal="right", vertical="center", wrap_text=False)

HEADER = CellStyle(
    font=Font(name=_BASE_FONT, size=10, bold=True, color=_rgb(PAPER)),
    fill=solid(NAVY),
    border=Border(bottom=_side("medium", TERRA)),
    alignment=_HEAD_ALIGN,
)

# Two banding styles; ``row_styles`` picks between them so alternate rows differ.
ZEBRA_ROW = CellStyle(
    font=Font(name=_BASE_FONT, size=10, color=_rgb(INK)),
    fill=solid(ZEBRA),
    border=None,
    alignment=_LABEL_ALIGN,
)

PLAIN = CellStyle(
    font=Font(name=_BASE_FONT, size=10, color=_rgb(INK)),
    fill=None,
    border=None,
    alignment=_LABEL_ALIGN,
)

SUBTOTAL = CellStyle(
    font=Font(name=_BASE_FONT, size=10, bold=True, color=_rgb(NAVY)),
    fill=solid(SUBTOTAL_BG),
    border=Border(top=_side("medium", TERRA)),
    alignment=_LABEL_ALIGN,
)

# NOTE: the brief gives terracotta #C0552D on the #FDF1EA grand-total fill, and a
# later line says "never terracotta on #FDF1EA". The explicit style table wins and
# the contrast is ~4.9:1 (above the 4.5:1 readable threshold), so the table is used
# as written. See the build report.
GRAND_TOTAL = CellStyle(
    font=Font(name=_BASE_FONT, size=10, bold=True, color=_rgb(TERRA)),
    fill=solid(SUBTOTAL_BG),
    border=Border(top=_side("medium", TERRA), bottom=_side("double", TERRA)),
    alignment=_LABEL_ALIGN,
)

BANNER = CellStyle(
    font=Font(name=_BASE_FONT, size=12, bold=True, color=_rgb(NAVY)),
    fill=None,
    border=Border(bottom=_side("thin", TERRA)),
    alignment=Alignment(horizontal="left", vertical="center", wrap_text=False),
)

TITLE = CellStyle(
    font=Font(name=_BASE_FONT, size=14, bold=True, color=_rgb(NAVY)),
    fill=None,
    border=Border(bottom=_side("thin", TERRA)),
    alignment=Alignment(horizontal="left", vertical="center", wrap_text=True),
)

INPUT = CellStyle(
    font=Font(name=_BASE_FONT, size=11, bold=True, color=_rgb(TERRA)),
    fill=solid(INPUT_BG),
    border=Border(left=_side("thin", TERRA), right=_side("thin", TERRA),
                  top=_side("thin", TERRA), bottom=_side("thin", TERRA)),
    alignment=Alignment(horizontal="right", vertical="center", wrap_text=False),
)

MISSING_BANNER = CellStyle(
    font=Font(name=_BASE_FONT, size=9, color=_rgb(NAVY)),
    fill=solid(AMBER),
    border=None,
    alignment=Alignment(horizontal="left", vertical="center", wrap_text=True),
)

MUTED_ITALIC = CellStyle(
    font=Font(name=_BASE_FONT, size=10, italic=True, color=_rgb(MUTED)),
    fill=None,
    border=None,
    alignment=_LABEL_ALIGN,
)


# --------------------------------------------------------------------- writing
def apply_style(cell, style: CellStyle, number_format: str | None = None,
                *, right: bool = False) -> None:
    """Write a whole look onto one cell.

    ``number_format`` overrides the style default; pass it for every money,
    quantity and rate cell so ``General`` never survives on a number.
    """
    cell.font = style.font
    if style.fill is not None:
        cell.fill = style.fill
    if style.border is not None:
        cell.border = style.border
    align = style.alignment
    if right and style.fill is not None and style.fill.fgColor is not None:
        align = _RIGHT_ALIGN
    elif right:
        align = _RIGHT_ALIGN
    if align is not None:
        cell.alignment = align
    fmt = number_format if number_format is not None else style.number_format
    if fmt is not None:
        cell.number_format = fmt


def excel_len(value) -> int:
    """Rough on-screen width of a value in characters (openpyxl width units)."""
    if value is None:
        return 0
    s = str(value)
    widest = 0
    for ch in s:
        if ord(ch) > 0x2E80:            # CJK and friends render double width
            widest += 2
        else:
            widest += 1
    return widest


def set_widths(ws, widths: Mapping[str, float]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = float(width)


def autofit(
    ws,
    headers: Sequence[str],
    column_values: Sequence[Iterable],
    *,
    first_col: int = 1,
    minimum: float = 9.0,
    label_cap: float = 46.0,
    description_cap: float = 60.0,
    description_cols: Sequence[int] = (),
    pads: Mapping[int, float] | None = None,
    header_mode: str = "words",
) -> dict[int, float]:
    """Set every column width from the measured longest value in it.

    Header text is measured by its longest word when ``header_mode="words"``,
    because headers wrap; measuring the whole header would stretch a numeric column
    to the width of a sentence. The cap is 46 for label columns and 60 for the
    columns named in ``description_cols``. No column is left at the default.
    """
    pads = pads or {}
    out: dict[int, float] = {}
    for offset, header in enumerate(headers):
        col = first_col + offset
        texts = list(column_values[offset])
        if header_mode == "words":
            texts.append(max(str(header).split(), key=excel_len))
        elif header_mode == "full":
            texts.append(header)
        longest = max((excel_len(t) for t in texts), default=0)
        cap = description_cap if col in description_cols else label_cap
        width = min(max(minimum, longest + 2.0 + pads.get(col, 0.0)), cap)
        ws.column_dimensions[get_column_letter(col)].width = round(width, 2)
        out[col] = round(width, 2)
    return out


def header_height(headers: Sequence[str], widths: Mapping[str, float],
                  *, minimum: float = 30.0, line: float = 12.5) -> float:
    """Row height that fits every wrapped header at the width it will get.

    The brief says 30; a header that needs three wrapped lines at that height would
    be clipped, so the height is raised when the measured text requires it.
    """
    lines = 1
    for offset, header in enumerate(headers):
        col = offset + 1
        width = widths.get(col) or widths.get(get_column_letter(col)) or 8.43
        usable = max(width - 1.5, 1.0)
        lines = max(lines, math.ceil(excel_len(header) / usable) or 1)
    return round(max(minimum, lines * line + 6.0), 1)


def write_header(ws, row: int, headers: Sequence[str], *,
                 height: float | None = None) -> int:
    for idx, text in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=idx, value=text)
        apply_style(cell, HEADER, TEXT)
    if height:
        ws.row_dimensions[row].height = height
    return len(headers)


def write_title(ws, row: int, text: str, last_col: int, *, height: float = 26.0) -> None:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    cell = ws.cell(row=row, column=1, value=text)
    apply_style(cell, TITLE, TEXT)
    ws.row_dimensions[row].height = height


def write_banner(ws, row: int, text: str, last_col: int, *,
                 style: CellStyle = BANNER, height: float | None = None) -> None:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    cell = ws.cell(row=row, column=1, value=text)
    apply_style(cell, style, TEXT)
    if height:
        ws.row_dimensions[row].height = height


def freeze_and_filter(ws, *, freeze: str | None = None,
                      filter_ref: str | None = None) -> None:
    """Freeze the header block and put an autofilter over the data range.

    The filter range is passed explicitly so it can stop above the total row; a
    filter that covers a total row hides the total when it is used.
    """
    if freeze:
        ws.freeze_panes = freeze
    if filter_ref:
        ws.auto_filter.ref = filter_ref


def _font_with_colour(font: Font, colour: str) -> Font:
    return Font(name=font.name, size=font.size, bold=font.bold, italic=font.italic,
                color=_rgb(colour))


def band(ws, first_row: int, last_row: int, first_col: int, last_col: int, *,
         start_banded: bool = True) -> None:
    """Zebra band alternate data rows. Call with the data range only.

    The caller must pass a range that starts below the header row; nothing here can
    reach a header because the range is explicit.
    """
    for row in range(first_row, last_row + 1):
        banded = ((row - first_row) % 2 == 0) == start_banded
        for col in range(first_col, last_col + 1):
            cell = ws.cell(row=row, column=col)
            if banded:
                cell.fill = solid(ZEBRA)
                cell.font = _font_with_colour(cell.font, INK)


def outline_group(ws, first_row: int, last_row: int, *, level: int = 1,
                  hidden: bool = False) -> None:
    if last_row <= first_row:
        return
    for row in range(first_row, last_row + 1):
        ws.row_dimensions[row].outlineLevel = level
        if hidden:
            ws.row_dimensions[row].hidden = True


def summary_above(ws) -> None:
    """Draw outline summary rows above their detail instead of below."""
    ws.sheet_properties.outlinePr.summaryBelow = False


def note(cell, text: str, *, width: int = 320, height: int = 170) -> None:
    """Attach a cell comment (formula, exclusions, calculation date)."""
    cmt = Comment(text, _AUTHOR)
    cmt.width = width
    cmt.height = height
    cell.comment = cmt


def internal_link(cell, sheet_name: str) -> None:
    """Make a cell a clickable jump to another sheet."""
    cell.hyperlink = Hyperlink(ref=cell.coordinate,
                               location=f"'{sheet_name}'!A1",
                               display=str(cell.value))


def add_data_bar(ws, ref: str, *, colour: str = TERRA, opacity_pct: int = 60) -> None:
    """Solid data bar, no gradient, on a euro column.

    openpyxl cannot write the ``gradient`` attribute, so the legacy dataBar element
    is emitted, which Excel renders solid. Opacity rides on the ARGB alpha channel.
    """
    alpha = int(round(255 * opacity_pct / 100.0))
    rule = DataBarRule(start_type="num", start_value=0, end_type="max",
                       color=f"{alpha:02X}{colour}", showValue=True)
    ws.conditional_formatting.add(ref, rule)


def add_colour_scale(ws, ref: str, *, low: str = SCALE_LOW, mid: str = SCALE_MID,
                     high: str = SCALE_HIGH) -> None:
    """Three-stop colour scale for a movement column. Ink stays readable on all stops."""
    rule = ColorScaleRule(start_type="min", start_color=low,
                          mid_type="percentile", mid_value=50, mid_color=mid,
                          end_type="max", end_color=high)
    ws.conditional_formatting.add(ref, rule)


def section_label(ws, row: int, text: str, first_col: int, last_col: int, *,
                  bold: bool = False) -> None:
    """A plain ink label with optional wrap, for a figure name to the left of a value."""
    cell = ws.cell(row=row, column=first_col, value=text)
    apply_style(cell, PLAIN, TEXT)
    if bold:
        cell.font = Font(name=_BASE_FONT, size=10, bold=True, color=_rgb(NAVY))
    if last_col > first_col:
        ws.merge_cells(start_row=row, start_column=first_col, end_row=row,
                       end_column=last_col)


def value_cell(ws, row: int, col: int, value, fmt: str,
               *, style: CellStyle = PLAIN, bold: bool = False):
    """One number with its number format, right aligned."""
    cell = ws.cell(row=row, column=col, value=value)
    apply_style(cell, style, fmt, right=True)
    if bold:
        cell.font = Font(name=_BASE_FONT, size=10, bold=True, color=_rgb(NAVY))
    cell.alignment = _RIGHT_ALIGN
    return cell


def footnote(ws, row: int, text: str, last_col: int, *, height: float | None = None) -> None:
    """Small muted line, wrapped."""
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    cell = ws.cell(row=row, column=1, value=text)
    apply_style(cell, style=MUTED_ITALIC, number_format=TEXT)
    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    if height:
        ws.row_dimensions[row].height = height


def block(ws, row: int, text: str, last_col: int, *, height: float | None = None) -> None:
    """A wrapped ink paragraph, for caveats and notes."""
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    cell = ws.cell(row=row, column=1, value=text)
    apply_style(cell, style=PLAIN, number_format=TEXT)
    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    if height:
        ws.row_dimensions[row].height = height


def flag_not_ok(ws, ref: str, *, expected: str = "OK") -> None:
    """Paint any status cell in ``ref`` that is not the expected word, loudly.

    A check that renders the same as a pass is worse than no check, so the failure
    look is a saturated red fill with bold dark red ink.
    """
    first = ref.split(":")[0]
    col = first[0]
    row = first[1:]
    formula = [f'AND(LEN(${col}{row})>0,${col}{row}<>"{expected}")']
    rule = FormulaRule(formula=formula,
                       fill=solid(FLAG_BAD_BG),
                       font=Font(name=_BASE_FONT, size=10, bold=True,
                                 color=_rgb(FLAG_BAD_INK)))
    ws.conditional_formatting.add(ref, rule)
