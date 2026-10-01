#!/usr/bin/env python3
"""Append or update validated milestone entries in the durable IDS milestone store.

Companion script to ``build_ids_development_progress.py``. The development
progress page lets a user log milestones (date / note / evidence / done) for a
chosen dealer, but as a static HTML file with no server it cannot save them
anywhere itself -- it can only download a small text file
("dealer-development-plan.txt", produced by the page's "Save my plan to a
file" button). This script is the other half of that pattern: it reads a
downloaded plan file (or a single milestone given on the command line),
validates it, and writes it into the on-disk store at

    01_data/00_derived/ids_milestones/ids_milestones_store.json

so that a later run of ``build_ids_development_progress.py`` can embed it in
the page and previously-logged milestones show up on load. Writing here is a
manual step (run this script after downloading a plan file) -- this is the
accepted v1 given the no-server constraint. See 00_docs/IDS_MILESTONE_STORE.md
for the full format and workflow.

This script only ever touches milestone bookkeeping (date / note / evidence /
done). It must never write an assessment score, an assessment date, or a
commercial-improvement figure -- per the Universe 3.0 strategy paper (Sec. 6):
a milestone completion, a re-assessment, and a commercial-improvement
measurement are three separate things and never update one another.

Usage:
    # Import a plan file downloaded from the page (replaces that dealer's
    # stored milestone list and priority with what is in the file):
    python append_ids_milestone.py from-plan-file "dealer-development-plan.txt"

    # Append a single milestone without going through a plan file:
    python append_ids_milestone.py add-one --market "UK LCV" --dealer "Example Dealer" \
        --date 2026-03-01 --note "Agreed to restock core lines" \
        --evidence "Order confirmation emailed 2026-03-01" --done
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
STORE_PATH = REPO / "01_data" / "00_derived" / "ids_milestones" / "ids_milestones_store.json"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_date(s: str) -> bool:
    if not s:
        return True  # a blank date is allowed (mirrors the page: "leave a row blank")
    if not _DATE_RE.match(s):
        return False
    try:
        y, m, d = (int(x) for x in s.split("-"))
        date(y, m, d)
    except ValueError:
        return False
    return True


def dealer_key(market: str, dealer: str) -> str:
    return f"{market}::{dealer}"


def load_store() -> dict[str, Any]:
    if not STORE_PATH.is_file():
        raise SystemExit(f"Store not found: {STORE_PATH}")
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def save_store(store: dict[str, Any]) -> None:
    """Atomic write: never leaves a half-written store file on disk."""
    tmp = STORE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STORE_PATH)


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    """Return a list of human-readable problems; empty list = all rows valid."""
    problems: list[str] = []
    for i, row in enumerate(rows):
        d = str(row.get("date") or "").strip()
        if not _valid_date(d):
            problems.append(f"row {i + 1}: date {d!r} is not blank and not a valid YYYY-MM-DD date")
        if not isinstance(row.get("done"), bool):
            problems.append(f"row {i + 1}: 'done' must be true/false, got {row.get('done')!r}")
    return problems


def upsert_dealer(
    store: dict[str, Any],
    market: str,
    dealer: str,
    priority: str | None,
    rows: list[dict[str, Any]],
) -> None:
    problems = validate_rows(rows)
    if problems:
        raise SystemExit("Refusing to write -- invalid milestone row(s):\n  " + "\n  ".join(problems))
    key = dealer_key(market, dealer)
    store.setdefault("dealers", {})[key] = {
        "market": market,
        "dealer": dealer,
        "priority": priority or None,
        "milestones": [
            {
                "date": str(r.get("date") or ""),
                "note": str(r.get("note") or ""),
                "evidence": str(r.get("evidence") or ""),
                "done": bool(r.get("done")),
            }
            for r in rows
        ],
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def parse_plan_file(text: str) -> tuple[str, str, str | None, list[dict[str, Any]]]:
    """Mirror the page's own loadText() parser for 'dealer-development-plan|1' files."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines or not lines[0].startswith("dealer-development-plan"):
        raise SystemExit("Not a plan file saved from the development-progress page (bad header).")
    market = dealer = ""
    priority: str | None = None
    rows: list[dict[str, Any]] = []
    header_seen = False
    for line in lines[1:]:
        parts = line.split("|")
        key = parts[0].strip().lower()
        if key == "market":
            market = parts[1] if len(parts) > 1 else ""
            continue
        if key == "dealer":
            dealer = parts[1] if len(parts) > 1 else ""
            continue
        if key == "priority":
            priority = (parts[1] if len(parts) > 1 else "") or None
            continue
        if not header_seen and key == "date":
            header_seen = True
            continue
        rows.append(
            {
                "date": parts[0] if len(parts) > 0 else "",
                "note": parts[1] if len(parts) > 1 else "",
                "evidence": parts[2] if len(parts) > 2 else "",
                "done": (parts[3] if len(parts) > 3 else "").strip().lower() == "done",
            }
        )
    if not market or not dealer:
        raise SystemExit("Plan file is missing a market or dealer line -- refusing to write.")
    return market, dealer, priority, rows


def cmd_from_plan_file(args: argparse.Namespace) -> None:
    path = Path(args.path)
    if not path.is_file():
        raise SystemExit(f"Plan file not found: {path}")
    text = path.read_text(encoding="utf-8")
    market, dealer, priority, rows = parse_plan_file(text)
    store = load_store()
    before = len((store.get("dealers", {}).get(dealer_key(market, dealer)) or {}).get("milestones", []))
    upsert_dealer(store, market, dealer, priority, rows)
    save_store(store)
    print(f"Wrote {STORE_PATH}")
    print(f"  dealer: {market} :: {dealer}")
    print(f"  priority: {priority or '(none)'}")
    print(f"  milestones: {before} -> {len(rows)}")
    print(f"  dealers now in store: {len(store.get('dealers', {}))}")


def cmd_add_one(args: argparse.Namespace) -> None:
    row = {"date": args.date or "", "note": args.note or "", "evidence": args.evidence or "", "done": bool(args.done)}
    problems = validate_rows([row])
    if problems:
        raise SystemExit("Refusing to write -- invalid milestone:\n  " + "\n  ".join(problems))
    store = load_store()
    key = dealer_key(args.market, args.dealer)
    existing = store.get("dealers", {}).get(key)
    rows = list(existing["milestones"]) if existing else []
    priority = args.priority or (existing.get("priority") if existing else None)
    rows.append(row)
    upsert_dealer(store, args.market, args.dealer, priority, rows)
    save_store(store)
    print(f"Wrote {STORE_PATH}")
    print(f"  dealer: {args.market} :: {args.dealer}")
    print(f"  milestones for this dealer: {len(rows)}")
    print(f"  dealers now in store: {len(store.get('dealers', {}))}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("from-plan-file", help="Import a plan .txt file downloaded from the page")
    p1.add_argument("path", help="Path to the downloaded dealer-development-plan.txt")
    p1.set_defaults(func=cmd_from_plan_file)

    p2 = sub.add_parser("add-one", help="Append a single milestone without a plan file")
    p2.add_argument("--market", required=True, help="Market key, e.g. 'UK LCV' (must match the assessment extract)")
    p2.add_argument("--dealer", required=True, help="Dealer display name, e.g. as shown in the page's dealer picker")
    p2.add_argument("--priority", default=None, help="Section id A-E (optional; keeps existing if omitted)")
    p2.add_argument("--date", default="", help="YYYY-MM-DD, or blank")
    p2.add_argument("--note", default="", help="What will be done")
    p2.add_argument("--evidence", default="", help="What was sent / what happened")
    p2.add_argument("--done", action="store_true", help="Mark this milestone done")
    p2.set_defaults(func=cmd_add_one)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
