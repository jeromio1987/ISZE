"""Phase 5 — durable tender outcome store. Survives weekly rebuilds.

Also the loader for the weekly digest: `python tender_outcomes.py <digest-folder>` reads every
distributor CSV's outcome column into the store, so loading a reply is a command rather than a
snippet copied out of a readme.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class RunErrorLike(RuntimeError):
    """Raised for a bad input path or a malformed digest file."""


OUTCOMES_PATH = Path(__file__).with_name("tender_outcomes.json")

# Minimum sample before a win rate is shown
MIN_WIN_RATE_SAMPLE = 20

# ---------------------------------------------------------------- the one word list
#
# The digest page asks the distributor for five words. Earlier versions of this module
# counted a row as decided only if it read "won", "lost", "no-bid", "bid" or "not pursued",
# so the two words that actually arrive first every week - "pursue" and "pass" - were stored
# and then never counted. The summary read zero while the answers piled up underneath it.
#
# Every word anyone might reasonably type is mapped to one of these canonical values on the
# way in, so the count can no longer depend on which spelling arrived.
STATUS_PURSUE = "pursue"          # we will bid
STATUS_PASS = "pass"              # we will not bid
STATUS_NO_DECISION = "no decision"  # looked at, nothing decided yet (a holding word)
STATUS_WON = "won"                # a bid was made and the buyer awarded it to us
STATUS_LOST = "lost"              # a bid was made and the buyer awarded it elsewhere
STATUS_WITHDRAWN = "withdrawn"    # the buyer cancelled or never awarded - not a win or a loss

CANONICAL_STATUSES = (
    STATUS_PURSUE, STATUS_PASS, STATUS_NO_DECISION,
    STATUS_WON, STATUS_LOST, STATUS_WITHDRAWN,
)

# Human words -> canonical value. Keys are lower-cased with surrounding space trimmed.
STATUS_ALIASES = {
    # we will bid
    "pursue": STATUS_PURSUE,
    "pursued": STATUS_PURSUE,
    "bid": STATUS_PURSUE,
    "will bid": STATUS_PURSUE,
    # we will not bid
    "pass": STATUS_PASS,
    "passed": STATUS_PASS,
    "no-bid": STATUS_PASS,
    "no bid": STATUS_PASS,
    "not pursued": STATUS_PASS,
    "will not bid": STATUS_PASS,
    # holding word
    "no decision": STATUS_NO_DECISION,
    "not decided yet": STATUS_NO_DECISION,
    "not decided": STATUS_NO_DECISION,
    "undecided": STATUS_NO_DECISION,
    "no decision yet": STATUS_NO_DECISION,
    # decided
    "won": STATUS_WON,
    "win": STATUS_WON,
    "lost": STATUS_LOST,
    "loss": STATUS_LOST,
    "lose": STATUS_LOST,
    # neither won nor lost
    "withdrawn": STATUS_WITHDRAWN,
    "cancelled": STATUS_WITHDRAWN,
    "canceled": STATUS_WITHDRAWN,
    "withdrawn/cancelled": STATUS_WITHDRAWN,
}


def normalise_status(word: Any) -> Optional[str]:
    """Map any human word to a canonical status. Returns None for an empty value.

    An unrecognised word is returned lower-cased and stripped rather than dropped, so it
    still shows up in `by_status` and in `unrecognised_statuses`. A word nobody taught this
    module must never disappear silently.
    """
    if word is None:
        return None
    key = str(word).strip().lower()
    if not key:
        return None
    return STATUS_ALIASES.get(key, key)


EMPTY_STORE = {
    "version": 2,
    "outcomes": {},
    # outcomes keyed by opportunity_id. `status` holds a canonical value from CANONICAL_STATUSES:
    # status, decision_date, loss_reason, competitor_if_known, actual_parts_revenue_12m, notes
}


def load_outcomes(create: bool = True) -> Dict[str, Any]:
    """Read the store.

    `create=False` reads without any side effect: the file is not written if it is missing,
    and a default empty store is returned instead. A dry run must use that, otherwise a
    dry run would create the very file it promised not to touch.
    """
    if not OUTCOMES_PATH.exists():
        if not create:
            return json.loads(json.dumps(EMPTY_STORE))
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
        if v is None:
            continue
        # Fold any recognised word onto its canonical value on the way in.
        entry[k] = normalise_status(v) if k == "status" else v
    save_outcomes(store)
    return entry


def summary(store: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Counts the store, on the one word list above.

    `decided` is deliberately NOT the count of `pursue` plus `pass`. Those answer "does anyone
    act on this list?", which is a different and much earlier question, and they are reported
    as `engaged`. `decided` counts only tenders that reached a result: won or lost. Mixing the
    two would let a pile of unanswered-weeks show up as a decision.
    """
    store = store or load_outcomes()
    outcomes = store.get("outcomes") or {}
    statuses: Dict[str, int] = {}
    for o in outcomes.values():
        st = normalise_status(o.get("status")) or "unset"
        statuses[st] = statuses.get(st, 0) + 1

    pursue = statuses.get(STATUS_PURSUE, 0)
    passed = statuses.get(STATUS_PASS, 0)
    undecided = statuses.get(STATUS_NO_DECISION, 0)
    won = statuses.get(STATUS_WON, 0)
    lost = statuses.get(STATUS_LOST, 0)
    withdrawn = statuses.get(STATUS_WITHDRAWN, 0)

    # a result is known only for won / lost; the win rate divides by that, nothing else
    closed = won + lost
    decided = closed

    # "does anyone act on this list?" - readable weeks before any result exists
    answered = pursue + passed
    engaged_pct = round(100.0 * pursue / answered, 1) if answered else None

    win_rate = None
    win_rate_label = "insufficient data"
    if closed >= MIN_WIN_RATE_SAMPLE:
        win_rate = round(100.0 * won / closed, 1)
        win_rate_label = f"{win_rate}%"

    # anything the parser did not recognise, so it can never vanish quietly
    unrecognised = {s: n for s, n in statuses.items()
                    if s not in CANONICAL_STATUSES and s != "unset"}

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
        # the early signal: has the list been read at all
        "engaged": answered,
        "pursue": pursue,
        "pass": passed,
        "undecided": undecided,
        "withdrawn": withdrawn,
        "pursue_rate_pct": engaged_pct,
        "unrecognised_statuses": unrecognised,
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


def load_digest_csv(path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Read one digest outcome CSV into the store, folding every word onto the canonical set.

    Writes only rows whose outcome column holds something. Blank rows are left alone, so this
    is safe to run repeatedly as answers trickle in - it never clears a row that already has
    an answer, and only ever writes the fields below.

    With dry_run=True nothing is written at all: the store is not opened for writing, so a
    dry run cannot even create the file.
    """
    import csv as _csv

    path = Path(path)
    if not path.exists():
        raise RunErrorLike(f"digest file not found: {path}")

    # the page asks for `outcome`; the store's field is `status`. Accept either column.
    ADDED, UPDATED, SKIPPED = 0, 0, 0
    words: Dict[str, int] = {}
    unknown: List[Dict[str, str]] = []

    store = load_outcomes(create=not dry_run)

    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in _csv.DictReader(fh):
            raw = (row.get("outcome") or row.get("status") or "").strip()
            oid = (row.get("opportunity_id") or "").strip()
            if not oid or not raw:
                SKIPPED += 1
                continue
            canon = normalise_status(raw)
            if canon not in CANONICAL_STATUSES:
                unknown.append({"opportunity_id": oid, "word": raw})
            words[canon] = words.get(canon, 0) + 1

            entry = store["outcomes"].setdefault(oid, {})
            existed = bool(entry)
            entry["status"] = canon
            for src in ("decision_date", "loss_reason", "competitor_if_known", "notes"):
                val = (row.get(src) or "").strip()
                if val:
                    entry[src] = val
            if existed:
                UPDATED += 1
            else:
                ADDED += 1

    if not dry_run:
        save_outcomes(store)
    return {
        "file": path.name,
        "dry_run": dry_run,
        "rows_read": ADDED + UPDATED + SKIPPED,
        "added": ADDED,
        "updated": UPDATED,
        "blank_skipped": SKIPPED,
        "words_seen": words,
        "unrecognised": unknown,
    }


def load_digest_folder(folder: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Load every distributor CSV in a digest folder. `index.html` is ignored by extension.

    Each file's rows are collected first and written once at the end, so a folder with ten
    CSVs does ten reads and one write rather than ten separate writes.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise RunErrorLike(f"not a folder: {folder}")
    files = sorted(folder.glob("*.csv"))
    if not files:
        raise RunErrorLike(f"no distributor CSV files in {folder}")

    # one shared store for the whole folder; a dry run reads without creating anything
    store = load_outcomes(create=not dry_run)
    per_file = []
    for f in files:
        per_file.append(load_digest_csv_into(store, f))

    if not dry_run:
        save_outcomes(store)

    return {
        "dry_run": dry_run,
        "files": len(files),
        "per_file": per_file,
        "totals": {
            "added": sum(o["added"] for o in per_file),
            "updated": sum(o["updated"] for o in per_file),
            "unrecognised": sum(len(o["unrecognised"]) for o in per_file),
        },
    }


def load_digest_csv_into(store: Dict[str, Any], path: Path) -> Dict[str, Any]:
    """Read one CSV into an already-loaded store. Does not write."""
    import csv as _csv

    ADDED, UPDATED, SKIPPED = 0, 0, 0
    words: Dict[str, int] = {}
    unknown: List[Dict[str, str]] = []

    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        for row in _csv.DictReader(fh):
            raw = (row.get("outcome") or row.get("status") or "").strip()
            oid = (row.get("opportunity_id") or "").strip()
            if not oid or not raw:
                SKIPPED += 1
                continue
            canon = normalise_status(raw)
            if canon not in CANONICAL_STATUSES:
                unknown.append({"opportunity_id": oid, "word": raw})
            words[canon] = words.get(canon, 0) + 1

            entry = store["outcomes"].setdefault(oid, {})
            existed = bool(entry)
            entry["status"] = canon
            for src in ("decision_date", "loss_reason", "competitor_if_known", "notes"):
                val = (row.get(src) or "").strip()
                if val:
                    entry[src] = val
            if existed:
                UPDATED += 1
            else:
                ADDED += 1

    return {
        "file": Path(path).name,
        "rows_read": ADDED + UPDATED + SKIPPED,
        "added": ADDED,
        "updated": UPDATED,
        "blank_skipped": SKIPPED,
        "words_seen": words,
        "unrecognised": unknown,
    }


def _main(argv: List[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Load a weekly tender digest's outcome column into the durable store.")
    ap.add_argument("digest", nargs="?",
                    help="path to a digest folder (all CSVs) or a single distributor CSV")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change and write nothing")
    ap.add_argument("--summary", action="store_true",
                    help="print the current store summary and exit")
    args = ap.parse_args(argv)

    if args.summary or not args.digest:
        print(json.dumps(summary(), indent=2, ensure_ascii=False))
        return 0

    p = Path(args.digest)
    try:
        result = (load_digest_folder(p, dry_run=args.dry_run) if p.is_dir()
                  else load_digest_csv(p) if not args.dry_run
                  else {"dry_run": True, "per_file": [load_digest_csv(p)]})
    except RunErrorLike as e:
        print("ERROR:", e)
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not args.dry_run:
        print()
        print(json.dumps(summary(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
