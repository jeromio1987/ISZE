"""Append-only ledger for partner intake.

Each file leaves a line: when, what, and why. A later accepted version
supersedes the previous accepted version for that distributor and period.
The superseded line stays. A file that is not accepted does not enter the
shared table and does not supersede an accepted version. The same fingerprint
does not create a new version.
"""

from __future__ import annotations

import json
from pathlib import Path

ACCEPTED = "ACCEPTED"
NOT_ACCEPTED = "NOT ACCEPTED"
SUPERSEDED = "SUPERSEDED"
UNCHANGED = "UNCHANGED"

_CALLER_STATES = {ACCEPTED, NOT_ACCEPTED}


class Ledger:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.rows_path = self.path.with_suffix(".rows.json")

    def record(
        self,
        distributor_id: str,
        period: str,
        version: int,
        sha256: str,
        state: str,
        received_at: str,
        reason: str,
        rows: list | None = None,
    ) -> dict:
        distributor_id = _text(distributor_id, "distributor_id")
        period = _text(period, "period")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise ValueError("version must be a positive integer")
        sha256 = _text(sha256, "sha256")
        if state not in _CALLER_STATES:
            raise ValueError("state must be ACCEPTED or NOT ACCEPTED")
        received_at = _text(received_at, "received_at")
        reason = _text(reason, "reason")
        if rows is not None and not isinstance(rows, list):
            raise TypeError("rows must be a list")

        original = self._original_for_sha(distributor_id, sha256)
        if original is not None:
            note = _event(
                distributor_id=original["distributor_id"],
                period=original["period"],
                version=original["version"],
                sha256=sha256,
                state=UNCHANGED,
                received_at=received_at,
                reason="same fingerprint",
            )
            self._append([note])
            return note

        extra: list[dict] = []
        if state == ACCEPTED:
            previous = self._current_accepted(distributor_id, period)
            if previous is not None and previous["version"] != version:
                extra.append(
                    _event(
                        distributor_id=previous["distributor_id"],
                        period=previous["period"],
                        version=previous["version"],
                        sha256=previous["sha256"],
                        state=SUPERSEDED,
                        received_at=received_at,
                        reason=f"replaced by version {version}",
                    )
                )

        event = _event(
            distributor_id=distributor_id,
            period=period,
            version=version,
            sha256=sha256,
            state=state,
            received_at=received_at,
            reason=reason,
        )
        self._append(extra + [event])
        if state == ACCEPTED:
            self._put_rows(distributor_id, period, version, [] if rows is None else rows)
        return event

    def events(self) -> list[dict]:
        if not self.path.is_file():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("ledger file must be a list of events")
        return list(data)

    def current_state(self, distributor: str, period: str, version: int) -> str | None:
        state = None
        for event in self.events():
            if event["distributor_id"] != distributor or event["period"] != period:
                continue
            if event["version"] != version or event["state"] == UNCHANGED:
                continue
            state = event["state"]
        return state

    def canonical_rows(self, distributor: str, period: str) -> list | None:
        """Rows of the latest accepted version for this distributor and period."""
        accepted: dict | None = None
        for event in self.events():
            if event["distributor_id"] != distributor or event["period"] != period:
                continue
            if event["state"] == UNCHANGED:
                continue
            if event["state"] == ACCEPTED:
                accepted = event
            elif (
                accepted is not None
                and event["state"] == SUPERSEDED
                and event["version"] == accepted["version"]
            ):
                accepted = None
        if accepted is None:
            return None
        stored = self._load_rows()
        key = _row_key(accepted["distributor_id"], accepted["period"], accepted["version"])
        rows = stored.get(key)
        if rows is None:
            return None
        return json.loads(json.dumps(rows))

    def _original_for_sha(self, distributor_id: str, sha256: str) -> dict | None:
        for event in self.events():
            if event["state"] == UNCHANGED:
                continue
            if event["distributor_id"] == distributor_id and event["sha256"] == sha256:
                return event
        return None

    def _current_accepted(self, distributor_id: str, period: str) -> dict | None:
        current: dict[int, dict] = {}
        for event in self.events():
            if event["distributor_id"] != distributor_id or event["period"] != period:
                continue
            if event["state"] == UNCHANGED:
                continue
            current[event["version"]] = event
        accepted = [event for event in current.values() if event["state"] == ACCEPTED]
        if not accepted:
            return None
        return max(accepted, key=lambda event: event["version"])

    def _append(self, new_events: list[dict]) -> None:
        if not new_events:
            return
        existing = self.events()
        existing.extend(new_events)
        _dump(self.path, existing)

    def _put_rows(self, distributor_id: str, period: str, version: int, rows: list) -> None:
        stored = self._load_rows()
        stored[_row_key(distributor_id, period, version)] = json.loads(json.dumps(rows))
        _dump(self.rows_path, stored)

    def _load_rows(self) -> dict:
        if not self.rows_path.is_file():
            return {}
        data = json.loads(self.rows_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("accepted rows file must be an object")
        return data


def _event(
    distributor_id: str,
    period: str,
    version: int,
    sha256: str,
    state: str,
    received_at: str,
    reason: str,
) -> dict:
    return {
        "distributor_id": distributor_id,
        "period": period,
        "version": version,
        "sha256": sha256,
        "state": state,
        "received_at": received_at,
        "reason": reason,
    }


def _row_key(distributor_id: str, period: str, version: int) -> str:
    return f"{distributor_id}|{period}|{version}"


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
