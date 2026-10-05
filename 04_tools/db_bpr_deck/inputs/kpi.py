"""Reader for 01_data/KPI Master File.xlsx, sheet 'Parts Handling'.

This file has never had a reader. Every deck so far had its numbers typed in by hand,
which is where the MOS "3.7 in Sep 2025" against "2.2 in Aug 2026" confusion came from.

Layout of the sheet: the blocks are stacked, one after another.

    row 1   "Days of Parts in Stock"          <- block title
    row 2   (blank)
    row 3   "Distributor" | "Apr 24" | ...    <- header row, months from column B
    row 4+  distributor name | value | ...    <- data, ends at a blank row
    row 28  "First Fill Rate"                 <- next block title
    ...

So the reader does not carry row numbers. It finds the title rows, then the header row that
follows each one. If the file is reorganised the reader still works; if a title or a month
column is renamed we stop with E202 or E204 rather than reading the wrong numbers.

Cells that are not numbers are kept as markers, not silently dropped: "N/D" (no report sent),
"N/A" (not tracked), and stray text like "IBX" or "Internal only" that leaked into a numeric
column in this file. They are reported so a slide can say "not reported" honestly.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from ..errors import BprError, BprWarn
from ..paths import KPI_MASTER
from .kpi_types import KpiBlock

SHEET = "Parts Handling"

# Block title prefix (normalised to lower case) -> our key and unit.
# Prefix matching, because the file's own titles carry a euro sign that can arrive mangled.
BLOCK_SPECS: list[tuple[str, str, str]] = [
    ("days of parts in stock", "mos_days", "days"),
    ("first fill rate", "fill_rate", "ratio"),
    ("back order lines", "back_orders", "lines"),
    ("parts sales db to dlr", "sales_to_dealer_eur", "EUR"),
    ("parts sales per unit", "sales_per_unit_eur", "EUR"),
]

MONTH_FORMATS = ("%b %y", "%b %Y", "%B %y", "%B %Y")

# The header row mixes languages: "... Sep 24, Okt 24, Nov 24, Dez 24, Jan 25, Feb 25, Mrz 25,
# Apr 25, Mai 25, Jun 25 ...". German and English abbreviations sit in the same row, so the
# month name goes through a map rather than relying on strptime alone.
MONTH_NAMES = {
    "jan": 1, "january": 1, "januar": 1,
    "feb": 2, "february": 2, "februar": 2,
    "mar": 3, "march": 3, "mrz": 3, "maerz": 3, "märz": 3,
    "apr": 4, "april": 4,
    "may": 5, "mai": 5,
    "jun": 6, "june": 6, "juni": 6,
    "jul": 7, "july": 7, "juli": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "okt": 10, "october": 10, "oktober": 10,
    "nov": 11, "november": 11,
    "dec": 12, "dez": 12, "december": 12, "dezember": 12,
}

# Values that mean "no number here". Anything else that is not numeric is a marker we report.
NULL_TOKENS = {"n/d", "n/a", "na", "-", "--", "", "none", "null", "tbd", ""}


def coerce_value(value) -> tuple[float | None, str | None]:
    """Return (number, None) or (None, marker_text).

    Handles the mixed formats this file actually contains:
      0.85  -> 0.85
      67    -> 67.0
      '80,5%'  -> 0.805      (European decimal comma, given as a percentage)
      '78,52%' -> 0.7852
      'N/D' / 'N/A' / 'IBX' / 'Internal only' -> (None, marker)
    """
    if value is None:
        return None, None
    if isinstance(value, bool):
        return (1.0 if value else 0.0), None
    if isinstance(value, (int, float)):
        return float(value), None

    text = str(value).strip()
    if text.lower() in NULL_TOKENS:
        return None, None

    is_pct = text.endswith("%")
    body = text[:-1].strip() if is_pct else text
    body = body.replace(" ", "")
    # European decimal comma only when there is a single comma and no dot.
    if "," in body and "." not in body:
        body = body.replace(",", ".")
    else:
        body = body.replace(",", "")
    try:
        number = float(body)
    except ValueError:
        return None, text
    if is_pct:
        # A percentage in this file is either 0.805 meaning 80.5%, or 80.5 meaning the same.
        number = number / 100 if number > 1.5 else number
    return number, None



def _norm_title(value) -> str:
    return str(value or "").strip().lower()


def _parse_month(label) -> pd.Timestamp | None:
    text = str(label or "").strip()
    if not text:
        return None
    for fmt in MONTH_FORMATS:
        try:
            return pd.Timestamp(datetime.strptime(text, fmt))
        except ValueError:
            continue
    # German / English mixed abbreviations, e.g. "Mai 25", "Okt 24", "Mrz 25".
    parts = text.replace(",", " ").split()
    if len(parts) >= 2:
        month = MONTH_NAMES.get(parts[0].strip().lower().rstrip("."))
        year_text = parts[1].strip()
        if month is not None and year_text.isdigit():
            year = int(year_text)
            if year < 100:
                year += 2000
            try:
                return pd.Timestamp(year=year, month=month, day=1)
            except ValueError:
                return None
    return None


def _looks_like_header(row: tuple) -> bool:
    first = _norm_title(row[0] if row else None)
    return first == "distributor"


def _is_title_row(row: tuple) -> bool:
    first = row[0] if row else None
    if first is None or not str(first).strip():
        return False
    second = row[1] if len(row) > 1 else None
    # A block title has text in column A and nothing in column B.
    return second is None or not str(second).strip()


def load(path: Path | None = None) -> dict[str, KpiBlock]:
    """Read every block. Returns {key: KpiBlock}. Missing blocks are simply absent."""
    path = Path(path or KPI_MASTER)
    if not path.is_file():
        raise BprError("E102", "The KPI Master File is not where we expect it.", path=path,
                       expected="01_data/KPI Master File.xlsx")

    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover
        raise BprError("E501", "openpyxl is not installed, so Excel files cannot be read.",
                       detail=str(exc)) from exc

    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    if SHEET not in wb.sheetnames:
        wb.close()
        raise BprError("E201", f"The tab '{SHEET}' is not in the KPI Master File.", path=path,
                       expected=SHEET, found=", ".join(wb.sheetnames))
    ws = wb[SHEET]

    grid: list[tuple] = []
    for row in ws.iter_rows(values_only=True):
        grid.append(row)
    wb.close()

    # ---- find title rows and the header row that follows each one
    found: list[tuple[int, str, str]] = []      # (title row idx, key, unit)
    for i, row in enumerate(grid):
        if not _is_title_row(row):
            continue
        title = _norm_title(row[0])
        for prefix, key, unit in BLOCK_SPECS:
            if title.startswith(prefix):
                found.append((i, key, unit))
                break

    blocks: dict[str, KpiBlock] = {}
    for row_idx, key, unit in found:
        header_idx = None
        for scan in range(row_idx + 1, min(row_idx + 6, len(grid))):
            if _looks_like_header(grid[scan]):
                header_idx = scan
                break
        if header_idx is None:
            raise BprError(
                "E202",
                "A block in the KPI Master File has no 'Distributor' header row under it, "
                "so we cannot tell which numbers belong to which month.",
                path=path,
                expected=f"a 'Distributor' header row within 5 rows below row {row_idx + 1}",
                found=f"row {row_idx + 1}: {str(grid[row_idx][0])[:60]}",
            )

        header = grid[header_idx]
        month_cols: list[tuple[int, pd.Timestamp]] = []
        for col in range(1, len(header)):
            month = _parse_month(header[col])
            if month is not None:
                month_cols.append((col, month))
        if not month_cols:
            raise BprError(
                "E204",
                "No month headings were recognised in the KPI Master File.",
                path=path,
                expected="month labels such as 'Apr 24' in the header row",
                found=", ".join(str(v) for v in header[1:6] if v is not None),
            )

        data: dict[str, dict[pd.Timestamp, object]] = {}
        row_map: dict[str, int] = {}
        for scan in range(header_idx + 1, len(grid)):
            row = grid[scan]
            label = row[0] if row else None
            if label is None or not str(label).strip():
                break                      # blank row ends the block
            if _is_title_row(row):
                break                      # next block started
            label = str(label).strip()
            row_map[label] = scan + 1      # 1-based for a person reading the file
            data[label] = {month: (row[col] if col < len(row) else None) for col, month in month_cols}

        # index = months, columns = distributor labels (so frame["Imotors"] is one series)
        frame = pd.DataFrame(data)
        if not frame.empty:
            frame = frame.sort_index()
        frame.index.name = "month"
        months = pd.DatetimeIndex(sorted({m for _, m in month_cols}))

        markers: dict[str, list[str]] = {}
        for label in data:
            bad: list[str] = []
            for value in data[label].values():
                number, marker = coerce_value(value)
                if marker and marker not in bad:
                    bad.append(marker)
            if bad:
                markers[label] = bad

        blocks[key] = KpiBlock(
            name=str(grid[row_idx][0]).strip(),
            key=key,
            unit=unit,
            header_row=header_idx + 1,
            rows=row_map,
            frame=frame,
            months=months,
            markers=markers,
        )

    if "sales_to_dealer_eur" not in blocks:
        raise BprError(
            "E202",
            "The KPI Master File no longer has a 'Parts Sales DB to DLR' block, "
            "which is where sales to dealer in euros comes from.",
            path=path,
            expected="a block titled 'Parts Sales DB to DLR in EUR'",
            found="blocks found: " + ", ".join(sorted(blocks.keys())) or "none",
        )
    return blocks


def series_of(block: KpiBlock, label: str) -> pd.Series:
    """A distributor's numeric series, with the file's mixed formats resolved."""
    if label not in block.frame.columns:
        return pd.Series(dtype="float64")
    raw = block.frame[label]
    values: dict[pd.Timestamp, float] = {}
    for month, value in raw.items():
        number, _marker = coerce_value(value)
        if number is not None:
            values[pd.Timestamp(month)] = number
    if not values:
        return pd.Series(dtype="float64")
    s = pd.Series(values, dtype="float64").sort_index()
    s.name = label
    return s


def notes_for(block: KpiBlock, label: str) -> list[BprWarn]:
    """Plain notes about one distributor's cells in one block, for the run log."""
    out: list[BprWarn] = []
    if label in block.markers:
        out.append(BprWarn(
            f"{label}: {block.key} has non-numeric entries ({', '.join(block.markers[label])}); "
            "those months are treated as not reported.",
        ))
    if not block.has_label(label):
        out.append(BprWarn(f"{label} has no row in the '{block.name}' block."))
    latest = block.latest(label)
    if latest is not None:
        month, value = latest
        out.append(BprWarn(f"{label}: {block.key} latest is {value:,.2f} at {month:%b %Y}."))
    return out


def stale_by(block: KpiBlock, label: str, months: int = 3) -> int | None:
    """How many months behind the newest month that any distributor actually reported.

    The file's header carries future months with nothing under them, so comparing against the
    header would mark every distributor as late. Compare against the last month that has a
    number for anyone.
    """
    latest = block.latest(label)
    if latest is None:
        return None
    reported = []
    for other in block.frame.columns:
        s = block.series(other)
        if not s.empty:
            reported.append(s.index[-1])
    if not reported:
        return None
    newest = max(reported)
    gap = (newest.year - latest[0].year) * 12 + (newest.month - latest[0].month)
    return gap if gap >= months else None
