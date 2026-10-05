"""The FY2027 plan by distributor, monthly, April to March.

Read from the BP workbook (01_data/11_planning/FY2027  BP VP&ACC.xlsx, sheet 'VP FY27').
That sheet has one row per SAP sold-to: row 1 the label ("92 - IMOTORS"), row 2 the heading
("Turnover (000 EUR)"), then the twelve monthly figures.

Two things this replaces:
  * the I Motors deck had its plan numbers typed in from a report that arrived by mail and is
    not filed anywhere, so nobody could re-derive them;
  * the Power BI budget bars in db_profiles.yaml were read off a browser and have no file behind
    them for several markets.

Notes are in thousands of euro in the workbook and are returned in euro here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from ..errors import BprError, BprWarn
from ..paths import BP_WORKBOOK, PLANNING_DIR

SHEET = "VP FY27"
_CACHE: pd.DataFrame | None = None

MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


@dataclass
class Plan:
    db_key: str
    label: str
    months: pd.DatetimeIndex
    amounts_eur: list[float]
    source: str

    def total(self) -> float:
        return float(sum(self.amounts_eur))

    def window(self, start, end) -> tuple[list[str], list[float]]:
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        labels, values = [], []
        for month, value in zip(self.months, self.amounts_eur):
            if start <= month <= end:
                labels.append(f"{month:%b}")
                values.append(value)
        return labels, values

    def month_map(self) -> dict[pd.Timestamp, float]:
        return {m: v for m, v in zip(self.months, self.amounts_eur)}


def _parse_sheet() -> pd.DataFrame:
    """Read the FY plan sheet.

    Layout as it actually is (verified 2026-09-24):
        row 1  'BP 2027 (FY)' | 'PLAN' | 'PLAN' ...     <- a banner row
        row 2  'Vehicle Parts' | 'Apr' | 'May' | ...    <- the month names, no year
        row 3  'Turnover (000 EUR)' | numbers           <- figures already in euro
        row 4+ '2194 - ITUK (IC)' | numbers             <- one row per SAP sold-to
    Rows are offset by one column, so read column B as the label. The month names carry no
    year; the fiscal year start is therefore taken from an argument, not guessed.
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    if not BP_WORKBOOK.is_file():
        raise BprError("E102", "The FY2027 plan workbook is missing, so plan-against-actual cannot be shown.",
                       path=BP_WORKBOOK, expected="01_data/11_planning/FY2027  BP VP&ACC.xlsx")

    import openpyxl
    wb = openpyxl.load_workbook(BP_WORKBOOK, data_only=True, read_only=True)
    if SHEET not in wb.sheetnames:
        wb.close()
        raise BprError("E201", f"The tab '{SHEET}' is not in the plan workbook.", path=BP_WORKBOOK,
                       expected=SHEET, found=", ".join(wb.sheetnames))
    ws = wb[SHEET]
    rows = [r for r in ws.iter_rows(values_only=True)]
    wb.close()

    # the month row: twelve or more month names in a row
    month_idx = None
    for i, row in enumerate(rows[:10]):
        names = [str(v).strip() for v in row if isinstance(v, str)]
        hits = sum(1 for n in names if n[:3].lower() in ("jan", "feb", "mar", "apr", "may",
                                                          "jun", "jul", "aug", "sep", "oct",
                                                          "nov", "dec"))
        if hits >= 10:
            month_idx = i
            break
    if month_idx is None:
        raise BprError(
            "E202",
            "Could not find the monthly plan columns in the plan workbook.",
            path=BP_WORKBOOK, expected="a row with the twelve month names",
            found="first rows: " + " | ".join(
                ", ".join(str(v) for v in r[:6] if v is not None) for r in rows[:3])[:300],
        )

    month_row = rows[month_idx]
    label_col = month_idx if False else 1        # labels sit in column B
    month_cols: list[tuple[int, int]] = []        # (column index, month number)
    for col, value in enumerate(month_row):
        if not isinstance(value, str):
            continue
        number = MONTH_NAMES.get(value.strip()[:3].lower())
        if number:
            month_cols.append((col, number))
    if len(month_cols) < 10:
        raise BprError("E204", "The plan workbook's month names were not recognised.",
                       path=BP_WORKBOOK, expected="twelve month names",
                       found=f"{len(month_cols)} recognised")

    records = []
    for row in rows[month_idx + 1:]:
        if row is None or len(row) <= label_col:
            continue
        label = row[label_col]
        if label is None or not str(label).strip():
            continue
        label = str(label).strip()
        if " - " not in label and "Turnover" not in label:
            continue
        amounts = {}
        for col, number in month_cols:
            value = row[col] if col < len(row) else None
            if isinstance(value, (int, float)):
                amounts[number] = float(value)      # the sheet is already in euro
        if amounts:
            records.append({"label": label, **{f"m{n:02d}": v for n, v in amounts.items()}})

    if not records:
        raise BprError("E301", "The plan workbook has month columns but no rows of figures.",
                       path=BP_WORKBOOK)

    _CACHE = pd.DataFrame(records)
    return _CACHE


def _sold_to_code(label: str) -> str | None:
    match = re.match(r"\s*(\d{2,4})\s*-", label)
    return match.group(1) if match else None


def _token_hit(label: str, tokens: list[str]) -> bool:
    """Does the plan row label name this distributor?

    The plan workbook carries its own sold-to code set, which does not always match the billing
    codes (it shows '2194 - ITUK (IC)' and '89 - IUK' where billing uses 2575 and 2574). So the
    name is matched as well as the code. Longest token first, and only as a whole word, so 'BL'
    cannot match inside another label.
    """
    haystack = str(label).upper()
    for token in sorted({t.upper() for t in tokens if t}, key=len, reverse=True):
        if re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", haystack):
            return True
    return False


def load(db_key: str, sold_to_codes: list[float] | None = None, *, fy_start_year: int | None = None,
         name_tokens: list[str] | None = None) -> Plan:
    """This distributor's plan row, matched on the SAP sold-to code, then on the name.

    The workbook names months without a year, so the plan year is passed in. Without it the
    window stays ambiguous and callers cannot place the months on a timeline.
    """
    frame = _parse_sheet()
    codes = {str(int(c)) for c in (sold_to_codes or []) if pd.notna(c)}
    tokens = [t for t in (name_tokens or []) if t]

    hit = None
    for _, row in frame.iterrows():
        code = _sold_to_code(str(row["label"]))
        if code and codes and code in codes:
            hit = row
            break
    if hit is None and tokens:
        for _, row in frame.iterrows():
            if _token_hit(str(row["label"]), tokens):
                hit = row
                break

    if hit is None:
        labels = ", ".join(sorted(frame.label.astype(str))[:40])
        raise BprError(
            "E203",
            f"No plan row in the plan workbook matches {db_key}, by sold-to code or by name.",
            db=db_key, path=BP_WORKBOOK,
            expected=("a row for sold-to " + ", ".join(sorted(codes)) if codes else "a row by code")
            + (" or named like: " + ", ".join(tokens) if tokens else ""),
            found="rows present: " + labels[:400],
        )

    # The plan year runs April to March. Default to the financial year that is running now.
    start_year = fy_start_year or (pd.Timestamp.today().year - (1 if pd.Timestamp.today().month < 4 else 0))
    months, amounts = [], []
    for slot in range(1, 13):
        month_number = ((3 + slot - 1) % 12) + 1              # Apr, May, ... Mar
        year = start_year if month_number >= 4 else start_year + 1
        key = f"m{month_number:02d}"
        value = hit.get(key)
        months.append(pd.Timestamp(year=year, month=month_number, day=1))
        amounts.append(float(value) if pd.notna(value) else 0.0)

    return Plan(db_key=db_key, label=str(hit["label"]), months=pd.DatetimeIndex(months),
                amounts_eur=amounts,
                source=f"{BP_WORKBOOK.name} sheet '{SHEET}', row '{hit['label']}' "
                       f"(April {start_year} to March {start_year + 1}, figures already in euro)")


def probe(db_key: str, sold_to_codes: list[float] | None, name_tokens: list[str] | None = None) -> list[BprWarn]:
    try:
        plan = load(db_key, sold_to_codes, name_tokens=name_tokens)
    except BprError as exc:
        return [BprWarn(exc.message, path=exc.path)]
    return [BprWarn(f"plan for {db_key}: row '{plan.label}', FY total EUR {plan.total():,.0f} "
                    f"across {len(plan.months)} months")]


def workbooks_on_disk() -> list[str]:
    """Other plan-like workbooks, so preflight can say what else is available."""
    if not PLANNING_DIR.is_dir():
        return []
    return [p.name for p in sorted(PLANNING_DIR.glob("*.xlsx")) if "BP" in p.name or "plan" in p.name.lower()]
