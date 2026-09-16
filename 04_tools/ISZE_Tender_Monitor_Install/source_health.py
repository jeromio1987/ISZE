"""Source health tracking for tender fetchers — Phase 1 Task A."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_HEALTH_PATH = Path(__file__).with_name("_source_health.json")

# Intentional non-failure states — must NOT render as red BROKEN in the dashboard.
INACTIVE_STATUSES = frozenset({"RETIRED", "AWAITING_KEY", "SKIPPED", "WONTFIX", "CODE_READY", "BLOCKED"})
ALARM_STATUSES = frozenset({"BROKEN"})
WARN_STATUSES = frozenset({"SUSPECT", "AWAITING_KEY", "CODE_READY", "BLOCKED"})


def _load_health() -> dict:
    if _HEALTH_PATH.exists():
        try:
            return json.loads(_HEALTH_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_health(state: dict) -> None:
    _HEALTH_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def validate_feed(
    name: str,
    resp,
    *,
    expect_feed: bool = True,
    expect_json: bool = False,
    min_bytes: int = 500,
) -> Optional[str]:
    """Return an error string if the response is clearly not usable, else None."""
    if resp is None:
        return "no response"
    try:
        status = int(resp.status_code)
    except Exception:
        return "invalid response object"
    if status >= 400:
        return f"HTTP {status}"
    ctype = (resp.headers.get("Content-Type") or "").lower()
    body = resp.content or b""
    if len(body) < min_bytes:
        return f"body too small ({len(body)} bytes) — endpoint likely retired"
    head = body[:8000].lower()
    if expect_json:
        if not (body[:1] in (b"{", b"[") or b'"releases"' in head or b'"notices"' in head or b'"result"' in head):
            if b"<html" in head or "html" in ctype:
                return f"HTML returned where JSON expected (ctype={ctype})"
            return f"no JSON payload found (ctype={ctype})"
        return None
    if expect_feed:
        # Accept RSS <item>, Atom <entry>, or namespaced Atom <atom:entry> / *:entry
        has_feed = (
            b"<item" in head
            or b"<entry" in head
            or b":entry" in head
            or b"<atom:entry" in head
        )
        if not has_feed:
            if b"<html" in head or "html" in ctype:
                return f"HTML returned where feed expected (ctype={ctype}) — endpoint retired or moved"
            return f"no item/entry elements found (ctype={ctype})"
    return None


def record_source_result(state: dict, name: str, count: int, error: Optional[str]) -> None:
    """Record an active fetch: OK / SUSPECT / BROKEN."""
    entry = state.setdefault(name, {"zero_runs": 0, "last_error": None})
    if error:
        entry["status"] = "BROKEN"
        entry["last_error"] = error
        entry["zero_runs"] = int(entry.get("zero_runs", 0)) + 1
    elif count == 0:
        entry["zero_runs"] = int(entry.get("zero_runs", 0)) + 1
        entry["status"] = "SUSPECT" if entry["zero_runs"] >= 3 else "OK"
        entry["last_error"] = None
    else:
        entry["zero_runs"] = 0
        entry["status"] = "OK"
        entry["last_error"] = None
    entry["last_count"] = count


def record_source_status(
    state: dict,
    name: str,
    status: str,
    *,
    count: int = 0,
    last_error: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    """Set an intentional status (RETIRED / AWAITING_KEY / SKIPPED / WONTFIX / SUSPECT).

    Does not treat the source as a failed active endpoint — dashboard banners
    must not list these under BROKEN.
    """
    entry = state.setdefault(name, {"zero_runs": 0, "last_error": None})
    entry["status"] = status
    entry["last_count"] = count
    if last_error is not None:
        entry["last_error"] = last_error
    if note is not None:
        entry["note"] = note
    # Keep zero_runs stable for inactive / awaiting — not a failure streak.
    if status in INACTIVE_STATUSES:
        entry["zero_runs"] = int(entry.get("zero_runs", 0))


def print_health_report(state: dict) -> None:
    interesting = {
        k: v
        for k, v in state.items()
        if v.get("status") in (ALARM_STATUSES | WARN_STATUSES | INACTIVE_STATUSES)
    }
    print("\n" + "=" * 60)
    if not interesting:
        print("SOURCE HEALTH: all sources OK")
    else:
        print("SOURCE HEALTH: issues / non-active notes")
        for name, v in sorted(interesting.items()):
            err = v.get("last_error") or v.get("note") or ""
            print(
                f"  [{v.get('status')}] {name}: count={v.get('last_count', 0)} "
                f"zero_runs={v.get('zero_runs', 0)} {err}"
            )
    print("=" * 60)


def persist_and_report(state: dict) -> None:
    _save_health(state)
    print_health_report(state)


def load_health() -> dict:
    return _load_health()
