"""Shared pytest fixtures for 04_tools/_shared tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from _shared.scraper_io import IncrementalCsvWriter

FIELDNAMES = ["PN", "Status", "Notes"]


@pytest.fixture
def csv_fieldnames() -> list[str]:
    return list(FIELDNAMES)


@pytest.fixture
def writer_factory(tmp_path: Path):
    """Build IncrementalCsvWriter instances against tmp_path/out.csv."""

    def _factory(
        *,
        done_statuses: frozenset[str] | None = frozenset({"ok", "no_results"}),
        key_field: str = "PN",
        filename: str = "out.csv",
    ) -> IncrementalCsvWriter:
        return IncrementalCsvWriter(
            tmp_path / filename,
            FIELDNAMES,
            key_field=key_field,
            done_statuses=done_statuses,
        )

    return _factory


@pytest.fixture
def seeded_status_csv(tmp_path: Path) -> Path:
    """CSV with ok, no_results, and error rows for resume semantics tests."""
    path = tmp_path / "out.csv"
    path.write_text(
        "PN,Status,Notes\n"
        "0000000001,ok,\n"
        "0000000002,no_results,\n"
        "0000000003,error,failed\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def seeded_all_rows_csv(tmp_path: Path) -> Path:
    """CSV where error row should count as done when done_statuses=None."""
    path = tmp_path / "out.csv"
    path.write_text(
        "PN,Status,Notes\n"
        "0000000001,ok,\n"
        "0000000002,error,failed\n",
        encoding="utf-8",
    )
    return path
