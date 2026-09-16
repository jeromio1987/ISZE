"""P2a task 2a.5 — build `stakeholder_dim` and the response-latency rollup.

Reads   : 01_data/17_interactions/interaction_fact.parquet  (derived fields only)
Writes  : 01_data/17_interactions/stakeholder_dim.parquet
          01_data/17_interactions/db_response_latency.parquet

No mailbox access. No network. Operates purely on what the collector already derived,
so it can be re-run freely and cheaply as the extractor improves.

ROLE, NOT PERSONALITY
    `role_inferred` is a functional label derived from the topic mix a stakeholder
    appears on — parts / finance / commercial / technical / management. It is a guess
    about what someone works on, never about who they are. It carries a confidence and
    an interaction count, and it is suppressed below the evidence threshold.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
IN_DIR = os.path.join(ROOT, "01_data", "17_interactions")
SRC = os.path.join(IN_DIR, "interaction_fact.parquet")

MIN_EVIDENCE = 10          # below this: no role, no latency figure, nothing displayed
ACTIVE_WINDOW_DAYS = 180
BUILDER_VERSION = "dim-v1"

# Functional role from topic mix. Order is tie-break order.
ROLE_BY_TOPIC = {
    "payment": "finance",
    "availability": "parts_manager",
    "order": "parts_manager",
    "logistics": "parts_manager",
    "pricing": "parts_manager",
    "tender": "md",
    "technical": "workshop",
    "pms": "workshop",
    "warranty": "workshop",
}

# Roadmap decision_authority lens (economic / technical / user / gate)
AUTHORITY_BY_ROLE = {
    "finance": "economic",
    "parts_manager": "economic",
    "md": "gate",
    "workshop": "technical",
}


def _topic_frame(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (interaction, topic). Messages with no topic are dropped here only."""
    t = df.loc[df["topics"].astype(str) != "", ["stakeholder_id", "topics"]].copy()
    t["topic"] = t["topics"].str.split(",")
    return t.explode("topic").query("topic != ''")


def infer_roles(df: pd.DataFrame) -> pd.DataFrame:
    t = _topic_frame(df)
    if t.empty:
        return pd.DataFrame(columns=["stakeholder_id", "role_inferred", "role_confidence"])
    t["role"] = t["topic"].map(ROLE_BY_TOPIC)
    t = t.dropna(subset=["role"])
    counts = t.groupby(["stakeholder_id", "role"]).size().rename("n").reset_index()
    total = counts.groupby("stakeholder_id")["n"].transform("sum")
    counts["share"] = counts["n"] / total
    best = counts.sort_values(["stakeholder_id", "n"], ascending=[True, False]).drop_duplicates(
        "stakeholder_id"
    )
    return best.rename(columns={"role": "role_inferred", "share": "role_confidence"})[
        ["stakeholder_id", "role_inferred", "role_confidence"]
    ]


def response_latency(df: pd.DataFrame) -> pd.DataFrame:
    """Hours from an inbound message to our next outbound in the same thread.

    Only pairs where the outbound follows the inbound are counted; a thread that we
    never answered contributes to `n_unanswered`, not to the median.
    """
    d = df.dropna(subset=["occurred_at"]).sort_values("occurred_at")
    pairs, unanswered = [], 0

    for (db_code, thread), grp in d.groupby(["db_code", "thread_id"], dropna=False):
        if not thread:
            continue
        events = grp[["occurred_at", "direction"]].to_records(index=False)
        pending = None
        for occurred, direction in events:
            if direction == "in" and pending is None:
                pending = occurred
            elif direction == "out" and pending is not None:
                hours = (pd.Timestamp(occurred) - pd.Timestamp(pending)).total_seconds() / 3600.0
                if hours >= 0:
                    pairs.append({"db_code": db_code, "hours": hours})
                pending = None
        if pending is not None:
            unanswered += 1

    if not pairs:
        return pd.DataFrame(
            columns=["db_code", "n_replies", "p50_hours", "p90_hours", "sufficient_evidence"]
        )

    p = pd.DataFrame(pairs)
    out = (
        p.groupby("db_code")["hours"]
        .agg(n_replies="size", p50_hours=lambda s: s.quantile(0.5), p90_hours=lambda s: s.quantile(0.9))
        .reset_index()
    )
    out["p50_hours"] = out["p50_hours"].round(1)
    out["p90_hours"] = out["p90_hours"].round(1)
    out["sufficient_evidence"] = out["n_replies"] >= MIN_EVIDENCE
    out.attrs["threads_never_answered"] = unanswered
    return out.sort_values("p50_hours", ascending=False)


def build_stakeholder_dim(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["stakeholder_id"].astype(str) != ""].copy()
    if d.empty:
        return pd.DataFrame()

    latest = d["occurred_at"].max()

    agg = (
        d.groupby("stakeholder_id")
        .agg(
            db_code=("db_code", lambda s: s.mode().iat[0] if not s.mode().empty else ""),
            counterparty_domain=(
                "counterparty_domain",
                lambda s: s[s != ""].mode().iat[0] if not s[s != ""].mode().empty else "",
            ),
            n_interactions=("interaction_id", "size"),
            n_inbound=("direction", lambda s: int((s == "in").sum())),
            n_outbound=("direction", lambda s: int((s == "out").sum())),
            first_seen=("occurred_at", "min"),
            last_seen=("occurred_at", "max"),
            n_threads=("thread_id", "nunique"),
            mean_cc=("n_cc", "mean"),
            attachment_rate=("has_attachments", "mean"),
        )
        .reset_index()
    )

    # Consensus width: how many distinct stakeholders share the threads this person is on.
    per_thread = d.groupby("thread_id")["stakeholder_id"].nunique().rename("thread_width")
    width = (
        d.join(per_thread, on="thread_id")
        .groupby("stakeholder_id")["thread_width"]
        .median()
        .rename("consensus_width")
        .reset_index()
    )

    out = agg.merge(width, on="stakeholder_id", how="left").merge(
        infer_roles(d), on="stakeholder_id", how="left"
    )

    out["days_since_last_seen"] = (latest - out["last_seen"]).dt.days
    out["active"] = out["days_since_last_seen"] <= ACTIVE_WINDOW_DAYS
    out["sufficient_evidence"] = out["n_interactions"] >= MIN_EVIDENCE

    # Below the evidence threshold we publish no role at all, rather than a weak one.
    thin = ~out["sufficient_evidence"]
    out.loc[thin, ["role_inferred", "role_confidence"]] = [None, np.nan]

    out["decision_authority"] = out["role_inferred"].map(AUTHORITY_BY_ROLE)
    out.loc[thin, "decision_authority"] = None

    out["mean_cc"] = out["mean_cc"].round(2)
    out["attachment_rate"] = out["attachment_rate"].round(3)
    out["role_confidence"] = out["role_confidence"].round(3)
    out["builder_version"] = BUILDER_VERSION

    # Churn signal: this contact went quiet while the distributor kept talking to us.
    db_last = d.groupby("db_code")["occurred_at"].max().rename("db_last_seen")
    out = out.join(db_last, on="db_code")
    out["stakeholder_churn_flag"] = (~out["active"]) & (
        (latest - out["db_last_seen"]).dt.days <= ACTIVE_WINDOW_DAYS
    )
    return out.sort_values("n_interactions", ascending=False)


def main() -> int:
    if not os.path.exists(SRC):
        print(f"MISSING: {SRC}\nRun collect_mapi.py first.", file=sys.stderr)
        return 1

    df = pd.read_parquet(SRC)
    print(f"read {len(df):,} interactions · {df['db_code'].nunique()} distributors")

    dim = build_stakeholder_dim(df)
    lat = response_latency(df)

    if dim.empty:
        print("no stakeholders derived")
        return 1

    dim.to_parquet(os.path.join(IN_DIR, "stakeholder_dim.parquet"), index=False)
    lat.to_parquet(os.path.join(IN_DIR, "db_response_latency.parquet"), index=False)

    n_ok = int(dim["sufficient_evidence"].sum())
    print(f"\nstakeholder_dim: {len(dim):,} rows · {n_ok} above the {MIN_EVIDENCE}-interaction bar")
    print(f"  active: {int(dim['active'].sum()):,} · churn-flagged: {int(dim['stakeholder_churn_flag'].sum()):,}")
    if n_ok:
        print("  roles (evidenced only):")
        print(dim.loc[dim["sufficient_evidence"], "role_inferred"].value_counts().to_string())

    shown = lat[lat["sufficient_evidence"]] if "sufficient_evidence" in lat else lat
    print(f"\ndb_response_latency: {len(lat)} distributors · {len(shown)} above the bar")
    if len(shown):
        print(shown[["db_code", "n_replies", "p50_hours", "p90_hours"]].to_string(index=False))
    print("\nDistributors below the evidence bar are written but flagged — do not display them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
