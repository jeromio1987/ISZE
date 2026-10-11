"""Vault and ledger behaviour. Made-up bytes only. No sales files."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ledger import Ledger
from vault import Vault

WHEN = "2027-02-04T09:00:00Z"
LATER = "2027-03-04T09:00:00Z"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_store_original(tmp_path: Path) -> None:
    data = b"made-up,2027-01,v1\n"
    vault = Vault(tmp_path / "vault")
    record = vault.store("IUK", "2027-01", 1, data, received_at=WHEN)

    assert record.added is True
    assert record.version == 1
    assert record.sha256 == _sha(data)
    assert record.byte_size == len(data)
    assert record.path.read_bytes() == data

    side = json.loads(record.path.with_suffix(".json").read_text(encoding="utf-8"))
    assert side["received_at"] == WHEN
    assert side["declared_version"] == 1
    assert side["period"] == "2027-01"
    assert side["sha256"] == record.sha256
    assert side["byte_size"] == len(data)
    assert record.path.parent == (tmp_path / "vault" / "IUK" / "originals").resolve()
    assert record.path.name == f"2027-01_v1_{record.sha256[:12]}.bin"


def test_second_store_of_same_bytes_is_unchanged(tmp_path: Path) -> None:
    data = b"same-bytes-no-new-version"
    vault = Vault(tmp_path / "vault")
    first = vault.store("IUK", "2027-01", 1, data, received_at=WHEN)
    second = vault.store("IUK", "2027-01", 2, data, received_at=LATER)

    assert second.added is False
    assert second.sha256 == first.sha256
    assert second.version == 1
    assert second.received_at == WHEN
    assert second.path == first.path
    bins = list((tmp_path / "vault" / "IUK" / "originals").glob("*.bin"))
    assert len(bins) == 1
    assert bins[0].read_bytes() == data


def test_original_bytes_on_disk_equal_what_was_stored(tmp_path: Path) -> None:
    data = b"\x00\x01made-up-original\xff"
    vault = Vault(tmp_path / "vault")
    record = vault.store("UMI", "2027-04", 1, data, received_at=WHEN)
    copy_path = vault.copy_for_check(record, tmp_path / "check" / "copy.bin")

    assert record.path.read_bytes() == data
    assert copy_path.read_bytes() == data

    copy_path.write_bytes(b"checker-edited-the-copy")
    assert record.path.read_bytes() == data

    again = vault.store("UMI", "2027-04", 4, data, received_at=LATER)
    assert again.added is False
    assert record.path.read_bytes() == data


def test_accepted_v3_supersedes_v2_but_v2_event_remains(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.json")
    rows_v2 = [{"part_number": "FILTER", "quantity": 2}]
    rows_v3 = [{"part_number": "FILTER", "quantity": 3}]
    ledger.record(
        "IUK", "2027-01", 2, "hash-v2", "ACCEPTED", WHEN, "checks passed", rows_v2
    )
    ledger.record(
        "IUK", "2027-01", 3, "hash-v3", "ACCEPTED", LATER, "correction", rows_v3
    )

    events = ledger.events()
    v2_events = [event for event in events if event["version"] == 2]
    assert any(event["state"] == "ACCEPTED" for event in v2_events)
    assert any(event["state"] == "SUPERSEDED" for event in v2_events)
    assert ledger.current_state("IUK", "2027-01", 2) == "SUPERSEDED"
    assert ledger.current_state("IUK", "2027-01", 3) == "ACCEPTED"
    assert ledger.canonical_rows("IUK", "2027-01") == rows_v3

    stored = json.loads((tmp_path / "ledger.rows.json").read_text(encoding="utf-8"))
    assert stored["IUK|2027-01|2"] == rows_v2
    assert stored["IUK|2027-01|3"] == rows_v3


def test_not_accepted_v1_does_not_become_canonical(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.json")
    rejected = [{"part_number": "NOPE", "quantity": 9}]
    ledger.record(
        "IUK",
        "2027-01",
        1,
        "hash-v1",
        "NOT ACCEPTED",
        WHEN,
        "price column",
        rejected,
    )

    assert ledger.canonical_rows("IUK", "2027-01") is None
    assert ledger.current_state("IUK", "2027-01", 1) == "NOT ACCEPTED"
    if (tmp_path / "ledger.rows.json").is_file():
        stored = json.loads((tmp_path / "ledger.rows.json").read_text(encoding="utf-8"))
        assert "IUK|2027-01|1" not in stored

    accepted = [{"part_number": "PAD", "quantity": 4}]
    ledger.record(
        "IUK", "2027-01", 2, "hash-v2", "ACCEPTED", LATER, "checks passed", accepted
    )
    ledger.record(
        "IUK",
        "2027-01",
        3,
        "hash-v3",
        "NOT ACCEPTED",
        "2027-03-06T09:00:00Z",
        "price column again",
        rejected,
    )

    assert ledger.canonical_rows("IUK", "2027-01") == accepted
    assert ledger.current_state("IUK", "2027-01", 2) == "ACCEPTED"
    assert ledger.current_state("IUK", "2027-01", 3) == "NOT ACCEPTED"
    stored = json.loads((tmp_path / "ledger.rows.json").read_text(encoding="utf-8"))
    assert "IUK|2027-01|1" not in stored
    assert "IUK|2027-01|3" not in stored
    assert stored["IUK|2027-01|2"] == accepted


def test_identical_reimport_does_not_bump_version(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.json")
    rows = [{"part_number": "DISC", "quantity": 1}]
    ledger.record("IUK", "2027-01", 2, "same-hash", "ACCEPTED", WHEN, "checks passed", rows)
    note = ledger.record(
        "IUK", "2027-01", 3, "same-hash", "ACCEPTED", LATER, "resend", rows
    )

    assert note["state"] == "UNCHANGED"
    assert note["version"] == 2
    assert note["reason"] == "same fingerprint"
    versions = {event["version"] for event in ledger.events() if event["state"] != "UNCHANGED"}
    assert versions == {2}
    assert ledger.canonical_rows("IUK", "2027-01") == rows
    assert ledger.current_state("IUK", "2027-01", 2) == "ACCEPTED"
