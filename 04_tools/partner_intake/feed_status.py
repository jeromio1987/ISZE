"""Feed status for the monthly sales-to-dealer file.

One row per distributor we might receive a file from. Every row starts as
"no file yet". This module does not decide who already sends a file, does not
read a ledger, and does not carry euro amounts.

Distributor ids and names are read from the dimension file when that file is
usable. The id column is ``distributor_code`` (IUK and ITUK stay apart; UTI and
UMI stay apart). ``payer_code`` is never the id, because UTI and UMI share one.
``sold_to_sap`` is used only when the file has no ``distributor_code`` column.
The name is ``customer_name`` when that cell is filled, otherwise
``gps_db_label``, otherwise the id itself.

When a ``network_role`` column is present, only ``network_db`` rows are kept.
Several sold-to numbers can share one distributor code (Germany, Portugal,
Denmark). Those stay one row, because one distributor drops one monthly file.
"""

from __future__ import annotations

import csv
import warnings
from pathlib import Path

# Columns in distributor_dimension.csv. payer_code is listed so it is obvious
# it is refused as an id.
ID_COLUMN = "distributor_code"
ID_COLUMN_IF_CODE_MISSING = "sold_to_sap"
NAME_COLUMN = "customer_name"
NAME_COLUMN_FALLBACK = "gps_db_label"
ROLE_COLUMN = "network_role"
NETWORK_ROLE = "network_db"
REFUSED_ID_COLUMN = "payer_code"

STATUS_NO_FILE = "no file yet"
STATUS_ACCEPTED = "accepted"
STATUS_NOT_ACCEPTED = "not accepted"
STATUS_UNCHANGED = "unchanged"
STATUS_LATE = "late"

_ACCEPTED_STATES = {"accepted", "accept"}
_NOT_ACCEPTED_STATES = {"not accepted", "rejected", "refused"}
_UNCHANGED_STATES = {
    "unchanged",
    "same fingerprint",
    "same fingerprint resent",
    "duplicate",
}


def load_distributors(path: str | Path) -> list[dict]:
    """One register row per distributor.

    Returns an empty list when the file is missing or unusable, and warns so
    the empty register is not mistaken for a real list of no distributors.
    Does not invent distributors, and does not mark any of them as already
    sending a file.
    """
    source = Path(path)
    try:
        if not source.is_file():
            _say_empty(source, "missing")
            return []
        with source.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            raw_rows = list(reader)
    except (OSError, csv.Error, UnicodeError):
        _say_empty(source, "unusable")
        return []

    columns = {(name or "").strip() for name in fieldnames}
    if ID_COLUMN in columns:
        id_column = ID_COLUMN
    elif ID_COLUMN_IF_CODE_MISSING in columns:
        id_column = ID_COLUMN_IF_CODE_MISSING
    else:
        _say_empty(source, "unusable")
        return []

    # A header-only file, or a file whose id cells are all blank, is a usable
    # file with no distributors. That is not the missing-file fallback.
    return _rows_from_dimension(raw_rows, id_column, ROLE_COLUMN in columns)


def apply_events(rows: list[dict], events: list[dict] | None) -> list[dict]:
    """Set each period's status from ledger events the caller already has.

    Does not open a ledger file. The latest event for a distributor and a
    period wins (``received_at``, then position in the list). A distributor
    who is not already on the register is ignored. Pass the whole event list
    each time; periods are rebuilt from that list.
    """
    incoming = list(events or [])
    result: list[dict] = []
    by_id: dict[str, dict] = {}
    for row in rows:
        distributor_id = str(row.get("distributor_id") or "").strip()
        if not distributor_id or distributor_id in by_id:
            continue
        fresh = {
            "distributor_id": distributor_id,
            "name": str(row.get("name") or distributor_id),
            "status": STATUS_NO_FILE,
            "months_received": 0,
            "periods": {},
            "accepted_periods": [],
        }
        result.append(fresh)
        by_id[distributor_id] = fresh

    latest: dict[tuple[str, str], tuple] = {}
    for index, event in enumerate(incoming):
        if not isinstance(event, dict):
            continue
        distributor_id = str(event.get("distributor_id") or "").strip()
        period = _normalize_period(event.get("period"))
        if not distributor_id or period is None or distributor_id not in by_id:
            continue
        status = _status_from_event(event)
        if status is None:
            continue
        stamp = (str(event.get("received_at") or ""), index)
        key = (distributor_id, period)
        previous = latest.get(key)
        if previous is not None and stamp <= previous[0]:
            continue
        latest[key] = (stamp, status, _state_is_accepted(event.get("state")))

    for distributor_id, period in sorted(latest, key=lambda item: (item[0], item[1])):
        _stamp, status, accepted = latest[(distributor_id, period)]
        row = by_id[distributor_id]
        row["periods"][period] = status
        if accepted:
            row["accepted_periods"].append(period)

    for row in result:
        row["accepted_periods"].sort()
        row["months_received"] = len(row["accepted_periods"])
    return result


def status_for(row: dict, period: str) -> str:
    """Status of one distributor in one month. Missing month is "no file yet"."""
    normalized = _normalize_period(period)
    if normalized is None:
        return STATUS_NO_FILE
    return (row.get("periods") or {}).get(normalized, STATUS_NO_FILE)


def consecutive_accepted_ending(row: dict, period: str) -> int:
    """Accepted months in a row, ending at ``period``, walking back one month.

    The ending month counts only when the latest event for it is an accepted
    state. A late flag does not remove that acceptance and is not worked out
    from the calendar. A missing month, a refusal, or an unchanged resend
    stops the run.
    """
    normalized = _normalize_period(period)
    if normalized is None:
        return 0
    accepted = set(row.get("accepted_periods") or [])
    for stored, status in (row.get("periods") or {}).items():
        if status == STATUS_ACCEPTED:
            accepted.add(stored)
    count = 0
    current: str | None = normalized
    while current is not None and current in accepted:
        count += 1
        current = _previous_month(current)
    return count


def _rows_from_dimension(raw_rows: list[dict], id_column: str, filter_role: bool) -> list[dict]:
    ordered: list[dict] = []
    by_id: dict[str, dict] = {}
    for raw in raw_rows:
        if filter_role and (raw.get(ROLE_COLUMN) or "").strip() != NETWORK_ROLE:
            continue
        distributor_id = (raw.get(id_column) or "").strip()
        if not distributor_id:
            continue
        name, rank = _name_from(raw, distributor_id)
        existing = by_id.get(distributor_id)
        if existing is None:
            row = {
                "distributor_id": distributor_id,
                "name": name,
                "status": STATUS_NO_FILE,
                "months_received": 0,
                "periods": {},
                "accepted_periods": [],
                "_name_rank": rank,
            }
            ordered.append(row)
            by_id[distributor_id] = row
            continue
        if rank > existing["_name_rank"]:
            existing["name"] = name
            existing["_name_rank"] = rank
    for row in ordered:
        row.pop("_name_rank", None)
    return ordered


def _name_from(raw: dict, distributor_id: str) -> tuple[str, int]:
    customer = (raw.get(NAME_COLUMN) or "").strip()
    if customer:
        return customer, 2
    label = (raw.get(NAME_COLUMN_FALLBACK) or "").strip()
    if label:
        return label, 1
    return distributor_id, 0


def _say_empty(source: Path, reason: str) -> None:
    warnings.warn(
        f"Distributor file is {reason} ({source}). The register is empty. "
        "No distributors were invented.",
        UserWarning,
        stacklevel=3,
    )


def _status_from_event(event: dict) -> str | None:
    # Late is taken only from the event. The calendar is not recomputed here.
    if event.get("late") is True:
        return STATUS_LATE
    token = _state_token(event.get("state"))
    if token in _ACCEPTED_STATES:
        return STATUS_ACCEPTED
    if token in _NOT_ACCEPTED_STATES:
        return STATUS_NOT_ACCEPTED
    if token in _UNCHANGED_STATES:
        return STATUS_UNCHANGED
    return None


def _state_is_accepted(state: object) -> bool:
    return _state_token(state) in _ACCEPTED_STATES


def _state_token(state: object) -> str:
    text = str(state or "").strip().lower().replace("_", " ").replace("-", " ")
    return " ".join(text.split())


def _normalize_period(period: object) -> str | None:
    text = str(period or "").strip()
    pieces = text.split("-")
    if len(pieces) < 2:
        return None
    try:
        year = int(pieces[0])
        month = int(pieces[1])
    except ValueError:
        return None
    if year < 1 or not 1 <= month <= 12:
        return None
    return f"{year:04d}-{month:02d}"


def _previous_month(period: str) -> str | None:
    normalized = _normalize_period(period)
    if normalized is None:
        return None
    year_text, month_text = normalized.split("-", 1)
    year = int(year_text)
    month = int(month_text)
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"
