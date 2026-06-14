"""Unit tests for IncrementalCsvWriter (local tmp files only)."""

from __future__ import annotations

import csv
from pathlib import Path

from _shared.scraper_io import IncrementalCsvWriter


def test_done_keys_status_filtered(writer_factory, seeded_status_csv: Path) -> None:
    writer = writer_factory()
    writer.path = seeded_status_csv
    assert writer.done_keys() == {"0000000001", "0000000002"}


def test_done_keys_all_rows(writer_factory, seeded_all_rows_csv: Path) -> None:
    writer = writer_factory(done_statuses=None)
    writer.path = seeded_all_rows_csv
    assert writer.done_keys() == {"0000000001", "0000000002"}


def test_ensure_header_idempotent(writer_factory, tmp_path: Path) -> None:
    writer = writer_factory()
    writer.ensure_header()
    writer.ensure_header()
    text = (tmp_path / "out.csv").read_text(encoding="utf-8")
    assert text.count("PN,Status,Notes") == 1


def test_append_roundtrip(writer_factory, tmp_path: Path) -> None:
    writer = writer_factory()
    writer.ensure_header()
    writer.append({"PN": "0000000001", "Status": "ok", "Notes": "done", "Extra": "ignored"})
    with (tmp_path / "out.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1
    assert rows[0]["PN"] == "0000000001"
    assert rows[0]["Status"] == "ok"
    assert rows[0]["Notes"] == "done"


def test_remove_keys(writer_factory, tmp_path: Path) -> None:
    writer = writer_factory()
    writer.ensure_header()
    writer.append({"PN": "0000000001", "Status": "ok", "Notes": ""})
    writer.append({"PN": "0000000002", "Status": "error", "Notes": ""})
    writer.remove_keys({"0000000001"})
    with (tmp_path / "out.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["PN"] for r in rows] == ["0000000002"]


COMPOSITE_FIELDS = ["ISZE_PN", "Site", "Status"]


def test_composite_done_keys(tmp_path: Path) -> None:
    path = tmp_path / "composite.csv"
    path.write_text(
        "ISZE_PN,Site,Status\n"
        "8982705240,autodoc_eu,ok\n"
        "8982705240,mekonomen_se,no_results\n"
        "8982705241,autodoc_eu,error\n",
        encoding="utf-8",
    )
    writer = IncrementalCsvWriter(
        path,
        COMPOSITE_FIELDS,
        key_fields=("ISZE_PN", "Site"),
        done_statuses=frozenset({"ok", "no_results"}),
    )
    assert writer.done_keys() == {
        ("8982705240", "autodoc_eu"),
        ("8982705240", "mekonomen_se"),
    }


def test_composite_done_keys_all_rows(tmp_path: Path) -> None:
    path = tmp_path / "composite_all.csv"
    path.write_text(
        "ISZE_PN,Site,Status\n"
        "8982705240,autodoc_eu,ok\n"
        "8982705241,autodoc_eu,error\n",
        encoding="utf-8",
    )
    writer = IncrementalCsvWriter(
        path,
        COMPOSITE_FIELDS,
        key_fields=("ISZE_PN", "Site"),
        done_statuses=None,
    )
    assert writer.done_keys() == {
        ("8982705240", "autodoc_eu"),
        ("8982705241", "autodoc_eu"),
    }


def test_composite_remove_keys(tmp_path: Path) -> None:
    writer = IncrementalCsvWriter(
        tmp_path / "composite_remove.csv",
        COMPOSITE_FIELDS,
        key_fields=("ISZE_PN", "Site"),
        done_statuses=None,
    )
    writer.ensure_header()
    writer.append({"ISZE_PN": "8982705240", "Site": "autodoc_eu", "Status": "ok"})
    writer.append({"ISZE_PN": "8982705240", "Site": "autodoc_de", "Status": "ok"})
    writer.append({"ISZE_PN": "8982705241", "Site": "autodoc_eu", "Status": "error"})
    writer.remove_keys({("8982705240", "autodoc_eu")})
    with writer.path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [(r["ISZE_PN"], r["Site"]) for r in rows] == [
        ("8982705240", "autodoc_de"),
        ("8982705241", "autodoc_eu"),
    ]
