"""Incremental CSV writer for scraper resume / append workflows."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import overload


class IncrementalCsvWriter:
    """Append-only CSV writer with resume key tracking."""

    def __init__(
        self,
        path: Path,
        fieldnames: list[str],
        *,
        key_field: str = "PN",
        key_fields: tuple[str, ...] | list[str] | None = None,
        done_statuses: frozenset[str] | None = frozenset({"ok", "no_results"}),
        encoding: str = "utf-8",
    ) -> None:
        self.path = Path(path)
        self.fieldnames = list(fieldnames)
        self.key_fields: tuple[str, ...] | None = (
            tuple(key_fields) if key_fields is not None else None
        )
        self.key_field = key_field
        self.done_statuses = done_statuses
        self.encoding = encoding

    def ensure_columns(self) -> None:
        """Add any missing fieldnames onto an existing CSV (empty values)."""
        if not self.path.exists():
            return
        with self.path.open(newline="", encoding=self.encoding) as fh:
            reader = csv.DictReader(fh)
            existing = list(reader.fieldnames or [])
            rows = list(reader)
        missing = [name for name in self.fieldnames if name not in existing]
        if not missing:
            return
        union = list(dict.fromkeys([*existing, *self.fieldnames]))
        self.fieldnames = union
        with self.path.open("w", newline="", encoding=self.encoding) as fh:
            writer = csv.DictWriter(fh, fieldnames=union)
            writer.writeheader()
            for row in rows:
                writer.writerow({name: row.get(name, "") for name in union})

    @property
    def composite(self) -> bool:
        return self.key_fields is not None

    def _row_key(self, row: dict) -> str | tuple[str, ...] | None:
        if self.composite:
            assert self.key_fields is not None
            parts = tuple((row.get(name) or "").strip() for name in self.key_fields)
            if any(not part for part in parts):
                return None
            return parts
        key = (row.get(self.key_field) or "").strip()
        return key if key else None

    def _row_done(self, row: dict) -> bool:
        if self.done_statuses is None:
            return True
        status = (row.get("Status") or "").lower()
        return status in self.done_statuses

    def ensure_header(self) -> None:
        """Create file with header row if path does not exist; add missing columns if it does."""
        if self.path.exists():
            self.ensure_columns()
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="", encoding=self.encoding) as fh:
            csv.DictWriter(fh, fieldnames=self.fieldnames).writeheader()

    @overload
    def done_keys(self) -> set[str]: ...

    @overload
    def done_keys(self) -> set[tuple[str, ...]]: ...

    def done_keys(self) -> set[str] | set[tuple[str, ...]]:
        """
        Return key values already present in CSV.

        Single-key mode: set[str] from key_field.
        Composite-key mode: set[tuple[str, ...]] from key_fields.

        If done_statuses is None: every non-empty key row counts.
        Else: only rows whose Status (case-insensitive) is in done_statuses.
        """
        if not self.path.exists():
            return set()
        done: set[str] | set[tuple[str, ...]] = set()
        with self.path.open(newline="", encoding=self.encoding) as fh:
            for row in csv.DictReader(fh):
                key = self._row_key(row)
                if key is None:
                    continue
                if not self._row_done(row):
                    continue
                done.add(key)
        return done

    def append(self, row: dict) -> None:
        """Append one row; extras ignored, missing keys filled with empty string."""
        out = {name: row.get(name, "") for name in self.fieldnames}
        with self.path.open("a", newline="", encoding=self.encoding) as fh:
            csv.DictWriter(fh, fieldnames=self.fieldnames).writerow(out)

    def remove_keys(self, keys: set[str] | set[tuple[str, ...]]) -> None:
        """Rewrite CSV excluding rows whose key is in keys."""
        if not self.path.exists() or not keys:
            return
        kept: list[dict] = []
        with self.path.open(newline="", encoding=self.encoding) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                key = self._row_key(row)
                if key is None or key not in keys:
                    kept.append(row)
        with self.path.open("w", newline="", encoding=self.encoding) as fh:
            writer = csv.DictWriter(fh, fieldnames=self.fieldnames)
            writer.writeheader()
            for row in kept:
                writer.writerow({name: row.get(name, "") for name in self.fieldnames})

    def delete_file(self) -> None:
        """Remove output file (--force). Safe if missing."""
        if self.path.exists():
            self.path.unlink()
