"""Check a monthly sales-to-dealer file and say whether it is accepted.

Only rules with stated=True in rules.py are run. The other rule ids are
returned for the receipt and do not accept or reject the file.

This module does not keep a ledger, does not match a catalogue, does not
apply a holiday calendar, and does not invent a volume-jump threshold.
A negative quantity is a return and is kept. The first worksheet is the file.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Mapping, Sequence

try:
    from . import rules
except ImportError:  # imported as a loose module from this folder
    import rules

_PERIOD = re.compile(r"\d{4}-(0[1-9]|1[0-2])")
_QUANTITY = re.compile(r"-?\d+(?:\.\d+)?")
_CURRENCY_SYMBOLS = ("€", "£", "$")
_CURRENCY_TOKENS = {"eur", "gbp", "usd", "euro"}
_PRICE_WORDS = ("price", "cost", "margin")

# Not a film rule. The brief requires a numeric quantity and says a negative
# is a return. It is not given one of the unstated V-numbers.
QUANTITY_RULE_ID = "QUANTITY"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    stops: bool
    message: str
    action: str


@dataclass
class ParsedTable:
    headers: list[str]
    raw_headers: list[str]
    rows: list[dict[str, str]]


@dataclass
class ValidationResult:
    file_version: int
    accepted: bool
    findings: list[Finding]
    not_checked: list[str]
    content_sha256: str
    drop_distributor_id: str
    received: date
    period: str | None
    rows: list[dict[str, str]]
    source_name: str | None = None
    raw_headers: list[str] = field(default_factory=list)


def sha256_hex(data: bytes) -> str:
    """Hex digest of the original file bytes. This module does not store it."""
    return hashlib.sha256(data).hexdigest()


def norm_header(header: str) -> str:
    text = header.replace("\ufeff", "").strip().lower()
    text = text.replace("-", " ").replace("/", " ")
    text = "_".join(text.split())
    return "".join(ch for ch in text if ch.isalnum() or ch == "_")


def on_time_deadline(period: str) -> date:
    """Last on-time day: ten weekdays after month-end. Weekends are skipped.

    No holiday calendar. A weekday that is a public holiday still counts.
    """
    if not _valid_period(period):
        raise ValueError(f"period must be YYYY-MM, got {period!r}")
    year_s, month_s = period.split("-", 1)
    year, month = int(year_s), int(month_s)
    day = date(year, month, monthrange(year, month)[1])
    left = 10
    while left:
        day += timedelta(days=1)
        if day.weekday() < 5:
            left -= 1
    return day


def load_declaration(path: Path | str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("The declaration must be a JSON object.")
    return data


def parse_table(path: Path | str) -> ParsedTable:
    path = Path(path)
    return parse_table_bytes(path.read_bytes(), path.suffix)


def parse_table_bytes(data: bytes, suffix: str) -> ParsedTable:
    suf = suffix.lower()
    if suf == ".csv":
        return _parse_csv(data)
    if suf == ".xlsx":
        return _parse_xlsx(data)
    raise ValueError(
        f"Unsupported file type {suffix!r}. Send a UTF-8 CSV or an xlsx file."
    )


def validate_path(
    path: Path | str,
    declaration: Mapping[str, object] | None,
    drop_distributor_id: str,
    file_version: int,
    received: date | datetime | str,
    previous_qty: object = None,
) -> ValidationResult:
    path = Path(path)
    data = path.read_bytes()
    parsed = parse_table_bytes(data, path.suffix)
    return validate(
        parsed.rows,
        declaration,
        drop_distributor_id,
        file_version,
        received,
        sha256_hex(data),
        previous_qty=previous_qty,
        headers=parsed.headers,
        raw_headers=parsed.raw_headers,
        source_name=path.name,
    )


def validate(
    rows: Sequence[Mapping[str, object]],
    declaration: Mapping[str, object] | None,
    drop_distributor_id: str,
    file_version: int,
    received: date | datetime | str,
    content_sha256: str,
    previous_qty: object = None,
    headers: Sequence[str] | None = None,
    raw_headers: Sequence[str] | None = None,
    source_name: str | None = None,
) -> ValidationResult:
    if isinstance(file_version, bool) or not isinstance(file_version, int):
        raise TypeError("file_version must be an int")
    if not isinstance(content_sha256, str) or not content_sha256:
        raise ValueError("content_sha256 must be the hex digest of the original bytes")
    if not isinstance(drop_distributor_id, str):
        raise TypeError("drop_distributor_id must be a str")

    received_on = _as_date(received)
    drop_id = drop_distributor_id.strip()
    header_norms, labels, prepared = _assemble(rows, headers, raw_headers)
    period = _single_period(prepared, header_norms)
    decl = dict(declaration) if isinstance(declaration, Mapping) else {}

    findings: list[Finding] = []
    _check_v003(findings, header_norms, labels, period)
    _check_v004(findings, prepared, header_norms, period)
    _check_v005(findings, prepared, header_norms)
    _check_v008(findings, prepared, header_norms, period)
    _check_v010(findings, decl, period)
    _check_v011(findings, period, received_on)
    _check_v012(findings, previous_qty, period)
    _check_v016(findings, prepared, drop_id, period)
    _check_v018(findings, prepared, header_norms, labels, period)
    _check_quantity(findings, prepared, header_norms)

    not_checked = [rule.id for rule in rules.RULES if not rule.stated]
    accepted = not any(item.stops for item in findings)
    return ValidationResult(
        file_version=file_version,
        accepted=accepted,
        findings=findings,
        not_checked=not_checked,
        content_sha256=content_sha256,
        drop_distributor_id=drop_id,
        received=received_on,
        period=period,
        rows=prepared,
        source_name=source_name,
        raw_headers=list(labels.values()),
    )


def _finding(
    rule_id: str,
    message: str,
    action: str,
    *,
    period: str | None,
    stops: bool | None = None,
    severity: str | None = None,
) -> Finding:
    rule = rules.RULE_BY_ID[rule_id]
    if stops is None:
        stops = rules.stops_file(rule.severity, period)
    return Finding(
        rule_id=rule.id,
        severity=rule.severity if severity is None else severity,
        stops=stops,
        message=message,
        action=action,
    )


def _check_v003(findings: list[Finding], header_norms: list[str], labels: dict[str, str], period: str | None) -> None:
    names = [labels.get(norm, norm) for norm in header_norms if _is_price_cost_margin_header(norm)]
    if not names:
        return
    findings.append(
        _finding(
            "V003",
            f"A price column was found ({_and(names)}).",
            "Remove it and send the file again as the next version.",
            period=period,
        )
    )


def _check_v004(findings: list[Finding], rows: list[dict[str, str]], header_norms: list[str], period: str | None) -> None:
    if period is not None:
        return
    if "period" not in header_norms:
        message = "The reporting period column is missing."
    elif not rows:
        message = "The file has no rows, so it has no reporting period."
    else:
        message = "The reporting period must be one YYYY-MM value on every row."
    findings.append(
        _finding(
            "V004",
            message,
            "Use one month written YYYY-MM and send the file again as the next version.",
            period=period,
        )
    )


def _check_v005(findings: list[Finding], rows: list[dict[str, str]], header_norms: list[str]) -> None:
    if "part_number" not in header_norms:
        findings.append(
            _finding(
                "V005",
                "The part number column is missing.",
                "Add the part number as text and send the file again as the next version.",
                period=None,
                stops=True,
            )
        )
    else:
        blank = [index for index, row in enumerate(rows, start=1) if not row.get("part_number", "").strip()]
        if blank:
            findings.append(
                _finding(
                    "V005",
                    f"A part number is blank ({_rows_phrase(blank)}).",
                    "Fill in the part number and send the file again as the next version.",
                    period=None,
                    stops=True,
                )
            )
    # Warning half. No catalogue is consulted, so this does not stop the file.
    findings.append(
        _finding(
            "V005",
            "catalogue match not run; no classification file is the authority",
            "No catalogue match was invented.",
            period=None,
            stops=False,
        )
    )


def _check_v008(findings: list[Finding], rows: list[dict[str, str]], header_norms: list[str], period: str | None) -> None:
    if not rows:
        return
    if "dealer_id" not in header_norms:
        blank = list(range(1, len(rows) + 1))
    else:
        blank = [index for index, row in enumerate(rows, start=1) if not row.get("dealer_id", "").strip()]
    if not blank:
        return
    # Quarter cutoff stays in rules.stops_file. The severity is read from the rule table.
    stops = rules.stops_file(rules.RULE_BY_ID["V008"].severity, period)
    if stops:
        action = "Add the dealer identifier and send the file again as the next version."
    else:
        action = "Add the dealer identifier when you can, because this period does not stop the file."
    findings.append(
        _finding(
            "V008",
            f"A dealer identifier is blank ({_rows_phrase(blank)}).",
            action,
            period=period,
            stops=stops,
        )
    )


def _check_v010(findings: list[Finding], declaration: Mapping[str, object], period: str | None) -> None:
    missing = [name for name in rules.DECLARATION_FIELDS if _declaration_missing(declaration, name)]
    if not missing:
        return
    findings.append(
        _finding(
            "V010",
            f"The coverage declaration is missing {_and(missing)}.",
            "Add the missing declaration fields and send the file again as the next version.",
            period=period,
        )
    )


def _check_v011(findings: list[Finding], period: str | None, received: date) -> None:
    if period is None:
        return
    deadline = on_time_deadline(period)
    if received <= deadline:
        return
    findings.append(
        _finding(
            "V011",
            (
                f"The file arrived on {received.isoformat()}, after {deadline.isoformat()}, "
                "which is ten weekdays after month-end, and no holiday calendar is applied."
            ),
            "No resend is required.",
            period=period,
        )
    )


def _check_v012(findings: list[Finding], previous_qty: object, period: str | None) -> None:
    # previous_qty is only a signal that a previous accepted month exists.
    # Its value is not compared. No threshold is invented.
    if previous_qty is None:
        findings.append(
            _finding(
                "V012",
                "no previous accepted month",
                "No comparison was made.",
                period=period,
                severity="I",
            )
        )
        return
    findings.append(
        _finding(
            "V012",
            "volume-jump threshold is not set",
            "No jump was judged, because no threshold is set.",
            period=period,
        )
    )


def _check_v016(findings: list[Finding], rows: list[dict[str, str]], drop_id: str, period: str | None) -> None:
    bad = [
        index
        for index, row in enumerate(rows, start=1)
        if row.get("distributor_id", "").strip() != drop_id
    ]
    if not bad:
        return
    findings.append(
        _finding(
            "V016",
            f"The distributor id does not match the drop folder ({_rows_phrase(bad)}).",
            "Correct the distributor id or the folder and send the file again as the next version.",
            period=period,
        )
    )


def _check_v018(
    findings: list[Finding],
    rows: list[dict[str, str]],
    header_norms: list[str],
    labels: dict[str, str],
    period: str | None,
) -> None:
    header_hits = [labels.get(norm, norm) for norm in header_norms if _is_v018_header(norm)]
    for raw in labels.values():
        if _has_currency_symbol(raw) and raw not in header_hits:
            header_hits.append(raw)
    cell_hits: list[str] = []
    for index, row in enumerate(rows, start=1):
        for key, value in row.items():
            if _has_currency_symbol(value):
                symbols = "".join(symbol for symbol in _CURRENCY_SYMBOLS if symbol in value)
                cell_hits.append(f"row {index} {labels.get(key, key)} {symbols}")
    if not header_hits and not cell_hits:
        return
    detail: list[str] = []
    if header_hits:
        detail.append("header " + _and(header_hits))
    if cell_hits:
        shown = cell_hits[:6]
        detail.append("cell " + _and(shown))
    findings.append(
        _finding(
            "V018",
            f"A currency symbol or a price, cost, margin or currency header was found ({_and(detail)}).",
            "Remove it and send the file again as the next version.",
            period=period,
        )
    )


def _check_quantity(findings: list[Finding], rows: list[dict[str, str]], header_norms: list[str]) -> None:
    if not rows and "quantity" in header_norms:
        return
    if "quantity" not in header_norms:
        if not rows:
            return
        findings.append(
            Finding(
                rule_id=QUANTITY_RULE_ID,
                severity="E",
                stops=True,
                message="Quantity must be a number.",
                action="Send a number. A negative quantity is a return and is kept.",
            )
        )
        return
    bad = [index for index, row in enumerate(rows, start=1) if not _valid_quantity(row.get("quantity", ""))]
    if not bad:
        return
    findings.append(
        Finding(
            rule_id=QUANTITY_RULE_ID,
            severity="E",
            stops=True,
            message=f"Quantity must be a number ({_rows_phrase(bad)}).",
            action="Send a number. A negative quantity is a return and is kept.",
        )
    )


def _is_price_cost_margin_header(norm: str) -> bool:
    if norm not in rules.PRICE_HEADERS and norm not in rules.FORBIDDEN_HEADERS:
        return False
    return any(word in norm for word in _PRICE_WORDS)


def _is_v018_header(norm: str) -> bool:
    if any(word in norm for word in _PRICE_WORDS):
        return True
    tokens = set(norm.split("_"))
    return bool(tokens & _CURRENCY_TOKENS)


def _has_currency_symbol(value: str) -> bool:
    return any(symbol in value for symbol in _CURRENCY_SYMBOLS)


def _valid_period(value: str) -> bool:
    return bool(_PERIOD.fullmatch(value.strip()))


def _valid_quantity(value: str) -> bool:
    return bool(_QUANTITY.fullmatch(value.strip()))


def _single_period(rows: list[dict[str, str]], header_norms: list[str]) -> str | None:
    if "period" not in header_norms or not rows:
        return None
    values = [row.get("period", "").strip() for row in rows]
    if not values or any(not _valid_period(value) for value in values):
        return None
    if len(set(values)) != 1:
        return None
    return values[0]


def _declaration_missing(declaration: Mapping[str, object], name: str) -> bool:
    if name not in declaration:
        return True
    value = declaration[name]
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _as_date(received: date | datetime | str) -> date:
    if isinstance(received, datetime):
        return received.date()
    if isinstance(received, date):
        return received
    if isinstance(received, str):
        return date.fromisoformat(received)
    raise TypeError("received must be a date")


def _assemble(
    rows: Sequence[Mapping[str, object]],
    headers: Sequence[str] | None,
    raw_headers: Sequence[str] | None,
) -> tuple[list[str], dict[str, str], list[dict[str, str]]]:
    raws: list[str] = []
    seen_raw: set[str] = set()

    def add_raw(value: object) -> None:
        text = str(value)
        if text in seen_raw:
            return
        seen_raw.add(text)
        raws.append(text)

    if raw_headers is not None:
        for item in raw_headers:
            add_raw(item)
    elif headers is not None:
        for item in headers:
            add_raw(item)
    for row in rows:
        for key in row:
            add_raw(key)

    labels: dict[str, str] = {}
    norms: list[str] = []
    for index, raw in enumerate(raws, start=1):
        norm = norm_header(raw)
        if not norm:
            norm = f"_column_{index}"
        if norm in labels:
            continue
        labels[norm] = raw
        norms.append(norm)

    prepared: list[dict[str, str]] = []
    for row in rows:
        mapped = {norm: "" for norm in norms}
        for key, value in row.items():
            norm = norm_header(str(key))
            if norm not in mapped:
                continue
            mapped[norm] = _text_value(value)
        if _row_is_blank(mapped):
            continue
        prepared.append(mapped)
    return norms, labels, prepared


def _row_is_blank(row: Mapping[str, str]) -> bool:
    return all(not str(value).strip() for value in row.values())


def _text_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, ".15g")
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _parse_csv(data: bytes) -> ParsedTable:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8.") from exc
    grid = list(csv.reader(text.splitlines()))
    return _grid_to_table(grid, formats=None)


def _parse_xlsx(data: bytes) -> ParsedTable:
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError(
            "This xlsx file cannot be read because openpyxl is not installed. "
            "Send the same file as UTF-8 CSV."
        ) from exc
    workbook = openpyxl.load_workbook(io.BytesIO(data), data_only=False)
    try:
        sheet = workbook.worksheets[0]
        grid: list[list[str]] = []
        formats: list[list[str]] = []
        for cells in sheet.iter_rows():
            texts: list[str] = []
            fmts: list[str] = []
            for cell in cells:
                texts.append(_excel_value(cell.value))
                fmts.append(cell.number_format or "")
            grid.append(texts)
            formats.append(fmts)
    finally:
        workbook.close()
    return _grid_to_table(grid, formats=formats)


def _excel_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, ".15g")
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _grid_to_table(grid: list[list[str]], formats: list[list[str]] | None) -> ParsedTable:
    while grid and not any(cell.strip() for cell in grid[-1]):
        grid.pop()
        if formats is not None:
            formats.pop()
    if not grid:
        return ParsedTable(headers=[], raw_headers=[], rows=[])
    raw_headers = [cell.strip() for cell in grid[0]]
    headers: list[str] = []
    used: set[str] = set()
    for index, raw in enumerate(raw_headers, start=1):
        norm = norm_header(raw)
        if not norm:
            norm = f"_column_{index}"
        if norm in used:
            suffix = 2
            while f"{norm}__{suffix}" in used:
                suffix += 1
            norm = f"{norm}__{suffix}"
        used.add(norm)
        headers.append(norm)
    rows: list[dict[str, str]] = []
    for row_index, cells in enumerate(grid[1:], start=1):
        item = {header: "" for header in headers}
        for col, header in enumerate(headers):
            text = cells[col].strip() if col < len(cells) else ""
            if header == "part_number":
                text = cells[col].strip() if col < len(cells) else ""
            if formats is not None and col < len(formats[row_index]):
                text = _apply_currency_format(text, formats[row_index][col])
            item[header] = text
        if _row_is_blank(item):
            continue
        rows.append(item)
    return ParsedTable(headers=headers, raw_headers=raw_headers, rows=rows)


def _apply_currency_format(text: str, number_format: str) -> str:
    if any(symbol in text for symbol in _CURRENCY_SYMBOLS):
        return text
    for symbol in _CURRENCY_SYMBOLS:
        if symbol in (number_format or ""):
            return f"{text}{symbol}"
    return text


def _and(items: Sequence[str]) -> str:
    names = list(items)
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _rows_phrase(numbers: Sequence[int]) -> str:
    nums = [n for n in numbers if n > 0]
    if not nums:
        return "the file"
    head = nums[:8]
    if len(head) == 1:
        listed = str(head[0])
    else:
        listed = ", ".join(str(n) for n in head[:-1]) + f" and {head[-1]}"
    if len(nums) > 8:
        listed += f", plus {len(nums) - 8} more"
    word = "row" if len(nums) == 1 else "rows"
    return f"{word} {listed}"
