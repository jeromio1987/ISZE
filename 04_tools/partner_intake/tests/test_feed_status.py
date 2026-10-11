"""Feed status, with a made-up dimension file and made-up ledger events."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import feed_status as fs

DIMENSION = """\
sold_to_sap,payer_code,distributor_code,gps_db_label,customer_name,network_role,fy2026_net_sales_eur
1799,1797,UTI,UTI,UNIVERSAL TRUCKS ISRAEL LTD,network_db,3242540
1797,1797,UMI,UMI,UNIVERSAL MOTORS ISRAEL LTD,network_db,3079678
2574,89,IUK,IUK,,network_db,6048309
2575,2194,ITUK,ITUK,ISUZU TRUCK (UK) LIMITED,network_db,6957525
88,88,MIDI,MIDI,MIDI Europe,not_a_customer,365704
2516,93,GERMANY,ISD,,network_db,1848131
601,93,GERMANY,ISD,ISUZU SALES DEUTSCHLAND GMBH,network_db,883819
"""


def _dimension(tmp_path: Path, text: str = DIMENSION) -> Path:
    path = tmp_path / "distributor_dimension.csv"
    path.write_text(text, encoding="utf-8")
    return path


def _ids(rows: list[dict]) -> list[str]:
    return [row["distributor_id"] for row in rows]


def test_missing_file_is_an_empty_register(tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rows = fs.load_distributors(tmp_path / "no-such-file.csv")
    assert rows == []
    assert any("register is empty" in str(item.message) for item in caught)


def test_file_without_an_id_column_is_empty(tmp_path: Path) -> None:
    path = _dimension(tmp_path, "payer_code,fy2026_net_sales_eur\n1797,10\n")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rows = fs.load_distributors(path)
    assert rows == []
    assert any("register is empty" in str(item.message) for item in caught)


def test_register_keeps_uti_umi_and_iuk_ituk_apart(tmp_path: Path) -> None:
    rows = fs.load_distributors(_dimension(tmp_path))
    assert _ids(rows) == ["UTI", "UMI", "IUK", "ITUK", "GERMANY"]
    by_id = {row["distributor_id"]: row for row in rows}
    assert by_id["UTI"]["name"] == "UNIVERSAL TRUCKS ISRAEL LTD"
    assert by_id["UMI"]["name"] == "UNIVERSAL MOTORS ISRAEL LTD"
    assert by_id["IUK"]["name"] == "IUK"
    assert by_id["ITUK"]["name"] == "ISUZU TRUCK (UK) LIMITED"
    assert by_id["GERMANY"]["name"] == "ISUZU SALES DEUTSCHLAND GMBH"
    assert all(row["status"] == "no file yet" for row in rows)
    assert all(row["months_received"] == 0 for row in rows)
    assert all(row["periods"] == {} for row in rows)
    assert all("eur" not in key.lower() for row in rows for key in row)


def test_header_only_file_is_usable_and_empty(tmp_path: Path) -> None:
    path = _dimension(
        tmp_path,
        "distributor_code,customer_name,network_role\n",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rows = fs.load_distributors(path)
    assert rows == []
    assert caught == []


def test_sold_to_is_the_id_only_when_the_code_column_is_absent(tmp_path: Path) -> None:
    path = _dimension(
        tmp_path,
        "sold_to_sap,payer_code,customer_name\n"
        "1799,1797,UNIVERSAL TRUCKS ISRAEL LTD\n"
        "1797,1797,UNIVERSAL MOTORS ISRAEL LTD\n",
    )
    rows = fs.load_distributors(path)
    assert _ids(rows) == ["1799", "1797"]


def test_events_do_not_add_distributors_or_euros(tmp_path: Path) -> None:
    rows = fs.load_distributors(_dimension(tmp_path))
    updated = fs.apply_events(
        rows,
        [
            {
                "distributor_id": "MIDI",
                "period": "2027-04",
                "state": "ACCEPTED",
                "received_at": "2027-05-01T00:00:00",
            },
            {
                "distributor_id": "SOMEONE_ELSE",
                "period": "2027-04",
                "state": "ACCEPTED",
                "received_at": "2027-05-01T00:00:00",
            },
        ],
    )
    assert _ids(updated) == ["UTI", "UMI", "IUK", "ITUK", "GERMANY"]
    assert all(row["status"] == "no file yet" for row in updated)
    assert rows[0]["periods"] == {}


def test_latest_event_for_a_period_wins() -> None:
    rows = [
        {"distributor_id": "IUK", "name": "IUK", "status": "no file yet"},
        {"distributor_id": "ITUK", "name": "ISUZU TRUCK (UK) LIMITED", "status": "no file yet"},
    ]
    updated = fs.apply_events(
        rows,
        [
            {
                "distributor_id": "IUK",
                "period": "2027-04",
                "state": "ACCEPTED",
                "received_at": "2027-05-20T00:00:00",
            },
            {
                "distributor_id": "IUK",
                "period": "2027-04",
                "state": "NOT ACCEPTED",
                "received_at": "2027-05-02T00:00:00",
            },
            {
                "distributor_id": "IUK",
                "period": "2027-05",
                "state": "unchanged",
                "received_at": "2027-06-03T00:00:00",
            },
            {
                "distributor_id": "ITUK",
                "period": "2027-04",
                "state": "ACCEPTED",
                "received_at": "2027-05-04T00:00:00",
            },
        ],
    )
    iuk = updated[0]
    assert fs.status_for(iuk, "2027-04") == "accepted"
    assert fs.status_for(iuk, "2027-05") == "unchanged"
    assert fs.status_for(iuk, "2027-06") == "no file yet"
    assert iuk["months_received"] == 1
    assert updated[1]["months_received"] == 1
    assert fs.status_for(updated[1], "2027-04") == "accepted"


def test_late_comes_only_from_the_event_flag() -> None:
    rows = [{"distributor_id": "UTI", "name": "UNIVERSAL TRUCKS ISRAEL LTD"}]
    updated = fs.apply_events(
        rows,
        [
            {
                "distributor_id": "UTI",
                "period": "2027-04",
                "state": "ACCEPTED",
                "received_at": "2027-06-01T00:00:00",
            },
            {
                "distributor_id": "UTI",
                "period": "2027-05",
                "state": "ACCEPTED",
                "received_at": "2027-06-02T00:00:00",
                "late": True,
            },
        ],
    )
    row = updated[0]
    assert fs.status_for(row, "2027-04") == "accepted"
    assert fs.status_for(row, "2027-05") == "late"
    assert row["months_received"] == 2
    assert row["accepted_periods"] == ["2027-04", "2027-05"]


def test_same_fingerprint_replaces_an_earlier_acceptance() -> None:
    rows = [{"distributor_id": "UMI", "name": "UNIVERSAL MOTORS ISRAEL LTD"}]
    updated = fs.apply_events(
        rows,
        [
            {
                "distributor_id": "UMI",
                "period": "2027-04",
                "state": "ACCEPTED",
                "received_at": "2027-05-01T00:00:00",
            },
            {
                "distributor_id": "UMI",
                "period": "2027-04",
                "state": "same fingerprint",
                "received_at": "2027-05-09T00:00:00",
            },
        ],
    )
    row = updated[0]
    assert fs.status_for(row, "2027-04") == "unchanged"
    assert row["months_received"] == 0


def test_consecutive_accepted_months_walk_backward() -> None:
    rows = [{"distributor_id": "IUK", "name": "IUK"}]
    updated = fs.apply_events(
        rows,
        [
            {"distributor_id": "IUK", "period": "2026-11", "state": "ACCEPTED", "received_at": "2026-12-01"},
            {"distributor_id": "IUK", "period": "2026-12", "state": "ACCEPTED", "received_at": "2027-01-04"},
            {"distributor_id": "IUK", "period": "2027-01", "state": "ACCEPTED", "received_at": "2027-02-02"},
            {"distributor_id": "IUK", "period": "2027-03", "state": "NOT ACCEPTED", "received_at": "2027-04-02"},
            {"distributor_id": "IUK", "period": "2027-04", "state": "ACCEPTED", "received_at": "2027-05-02"},
            {"distributor_id": "IUK", "period": "2027-06", "state": "ACCEPTED", "received_at": "2027-07-02"},
        ],
    )
    row = updated[0]
    assert fs.consecutive_accepted_ending(row, "2027-01") == 3
    assert fs.consecutive_accepted_ending(row, "2027-02") == 0
    assert fs.consecutive_accepted_ending(row, "2027-03") == 0
    assert fs.consecutive_accepted_ending(row, "2027-04") == 1
    assert fs.consecutive_accepted_ending(row, "2027-06") == 1
    assert row["months_received"] == 5


def test_a_late_accepted_month_still_continues_the_run() -> None:
    rows = [{"distributor_id": "GREECE", "name": "GREECE"}]
    updated = fs.apply_events(
        rows,
        [
            {"distributor_id": "GREECE", "period": "2027-04", "state": "ACCEPTED", "received_at": "2027-05-02"},
            {
                "distributor_id": "GREECE",
                "period": "2027-05",
                "state": "ACCEPTED",
                "received_at": "2027-06-20",
                "late": True,
            },
            {"distributor_id": "GREECE", "period": "2027-06", "state": "ACCEPTED", "received_at": "2027-07-03"},
        ],
    )
    row = updated[0]
    assert fs.status_for(row, "2027-05") == "late"
    assert fs.consecutive_accepted_ending(row, "2027-06") == 3


def test_equal_timestamp_uses_the_later_event_in_the_list() -> None:
    rows = [{"distributor_id": "IUK", "name": "IUK"}]
    updated = fs.apply_events(
        rows,
        [
            {
                "distributor_id": "IUK",
                "period": "2027-04",
                "state": "ACCEPTED",
                "received_at": "2027-05-02T00:00:00",
            },
            {
                "distributor_id": "IUK",
                "period": "2027-04",
                "state": "NOT ACCEPTED",
                "received_at": "2027-05-02T00:00:00",
            },
        ],
    )
    assert fs.status_for(updated[0], "2027-04") == "not accepted"
    assert updated[0]["months_received"] == 0
