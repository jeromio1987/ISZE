"""P2a task 2a.7 — commitment open/met/missed state machine (deterministic).

Reads  : commitment_fact.parquet + interaction_fact.parquet
Writes : commitment_fact.parquet (enriched) + commitment_fact.meta.json

Rules (explicit dated promises only — implicit prose is P2b):
  - open   : due_date >= as_of, no later same-thread message from either side after made_at
  - met    : a later message exists on the same thread with occurred_at >= due_date
             (proxy: the conversation continued past the promised date)
  - missed : due_date < as_of AND no later same-thread message after due_date
  - unknown: missing due_date or thread_id

No bodies. No names. Evidence is interaction_id / thread_id only.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
IN_DIR = os.path.join(ROOT, "01_data", "17_interactions")
COMMIT_SRC = os.path.join(IN_DIR, "commitment_fact.parquet")
INTER_SRC = os.path.join(IN_DIR, "interaction_fact.parquet")
BUILDER_VERSION = "commit-v1"


def classify(row, thread_times: dict[str, pd.Series], as_of: pd.Timestamp) -> str:
    due = row.get("due_date")
    thread = row.get("thread_id") or ""
    made = row.get("made_at")
    if pd.isna(due) or not thread:
        return "unknown"
    due_ts = pd.Timestamp(due)
    if due_ts.tzinfo is None and as_of.tzinfo is not None:
        due_ts = due_ts.tz_localize(as_of.tzinfo)
    times = thread_times.get(thread)
    if times is None or times.empty:
        return "open" if due_ts >= as_of.normalize() else "missed"

    # Any interaction on the thread at/after the due date → treated as met (conversation continued)
    later = times[times >= due_ts]
    # Exclude the originating message itself if timestamps equal made_at
    if made is not None and not pd.isna(made):
        made_ts = pd.Timestamp(made)
        later = later[later > made_ts]

    if len(later) > 0:
        return "met"
    if due_ts.normalize() >= as_of.normalize():
        return "open"
    return "missed"


def main() -> int:
    if not os.path.exists(COMMIT_SRC):
        print(
            f"MISSING: {COMMIT_SRC}\n"
            "Re-run collect_mapi.py (it writes commitment rows during extract).",
            file=sys.stderr,
        )
        return 1
    if not os.path.exists(INTER_SRC):
        print(f"MISSING: {INTER_SRC}", file=sys.stderr)
        return 1

    cdf = pd.read_parquet(COMMIT_SRC)
    idf = pd.read_parquet(INTER_SRC)
    print(f"commitments: {len(cdf):,} · interactions: {len(idf):,}")

    if cdf.empty:
        print("no commitments to classify")
        return 0

    as_of = pd.Timestamp(idf["occurred_at"].max())
    if pd.isna(as_of):
        as_of = pd.Timestamp(datetime.now(timezone.utc))

    thread_times = {
        tid: g["occurred_at"].dropna().sort_values()
        for tid, g in idf.groupby("thread_id")
        if tid
    }

    cdf = cdf.copy()
    cdf["status"] = [
        classify(row, thread_times, as_of) for row in cdf.to_dict(orient="records")
    ]
    cdf["status_as_of"] = as_of.date()
    cdf["builder_version"] = BUILDER_VERSION

    # Keep-rate by owner_side (only met+missed in denominator)
    scored = cdf[cdf["status"].isin(["met", "missed"])]
    keep = (
        scored.groupby("owner_side")["status"]
        .apply(lambda s: float((s == "met").sum()) / len(s) if len(s) else float("nan"))
        .rename("keep_rate")
        .reset_index()
    )

    out = os.path.join(IN_DIR, "commitment_fact.parquet")
    cdf.to_parquet(out, index=False)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder_version": BUILDER_VERSION,
        "rows": int(len(cdf)),
        "status_counts": cdf["status"].value_counts().to_dict(),
        "by_owner": cdf.groupby("owner_side")["status"].value_counts().unstack(fill_value=0).to_dict()
        if "owner_side" in cdf.columns
        else {},
        "keep_rate": keep.to_dict(orient="records"),
        "as_of": str(as_of.date()),
        "contains_message_content": False,
        "note": "met = later same-thread activity at/after due_date (proxy). Not LLM-judged.",
    }
    with open(os.path.join(IN_DIR, "commitment_fact.meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, default=str)

    print(f"\nwrote {out}")
    print("status:\n", cdf["status"].value_counts().to_string())
    if not keep.empty:
        print("keep_rate:\n", keep.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
