"""Phase 5 — durable tender outcome store. Survives weekly rebuilds."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

OUTCOMES_PATH = Path(__file__).with_name("tender_outcomes.json")

# Minimum sample before a win rate is shown
MIN_WIN_RATE_SAMPLE = 20

EMPTY_STORE = {
    "version": 1,
    "outcomes": {},
    # outcomes keyed by opportunity_id:
    # status, decision_date, loss_reason, competitor_if_known, actual_parts_revenue_12m, notes
}


def load_outcomes() -> Dict[str, Any]:
    if not OUTCOMES_PATH.exists():
        OUTCOMES_PATH.write_text(json.dumps(EMPTY_STORE, indent=2), encoding="utf-8")
        return json.loads(json.dumps(EMPTY_STORE))
    try:
        data = json.loads(OUTCOMES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return json.loads(json.dumps(EMPTY_STORE))
    if "outcomes" not in data:
        data = {"version": 1, "outcomes": data if isinstance(data, dict) else {}}
    return data


def save_outcomes(store: Dict[str, Any]) -> None:
    OUTCOMES_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")


def upsert_outcome(opportunity_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    store = load_outcomes()
    entry = store["outcomes"].setdefault(opportunity_id, {})
    for k, v in fields.items():
        if v is not None:
            entry[k] = v
    save_outcomes(store)
    return entry


def summary(store: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    store = store or load_outcomes()
    outcomes = store.get("outcomes") or {}
    statuses: Dict[str, int] = {}
    for o in outcomes.values():
        st = (o.get("status") or "unset").lower()
        statuses[st] = statuses.get(st, 0) + 1
    decided = sum(statuses.get(s, 0) for s in ("won", "lost", "no-bid", "bid", "not pursued"))
    won = statuses.get("won", 0)
    lost = statuses.get("lost", 0)
    closed = won + lost
    win_rate = None
    win_rate_label = "insufficient data"
    if closed >= MIN_WIN_RATE_SAMPLE:
        win_rate = round(100.0 * won / closed, 1)
        win_rate_label = f"{win_rate}%"
    return {
        "recorded": len(outcomes),
        "by_status": statuses,
        "decided": decided,
        "won": won,
        "lost": lost,
        "closed_sample": closed,
        "min_sample_for_win_rate": MIN_WIN_RATE_SAMPLE,
        "win_rate_pct": win_rate,
        "win_rate_display": win_rate_label,
    }


def merge_outcomes_into_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    store = load_outcomes()
    outcomes = store.get("outcomes") or {}
    for opp in payload.get("opportunities") or []:
        oid = opp.get("opportunity_id")
        if oid and oid in outcomes:
            opp["outcome"] = outcomes[oid]
        else:
            opp.setdefault("outcome", None)
    meta = payload.setdefault("meta", {})
    meta["outcomes_summary"] = summary(store)
    # Keep a copy reference for the dashboard editor (path relative to tool folder)
    meta["outcomes_store"] = str(OUTCOMES_PATH.name)
    return payload


if __name__ == "__main__":
    print(json.dumps(summary(), indent=2))
