"""P2a task 2a.6 — retention hard-delete + DSAR erase (local parquet only).

Modes
-----
1) Retention purge (default): drop rows where retention_expires < as_of.
2) DSAR erase: --stakeholder-id <hash> drops that person's derived rows.

G0a constraints
---------------
- Default is always dry-run. Pass --apply to write.
- Touches only 01_data/17_interactions/*.parquet (derived layer).
- Never opens Outlook, never sends mail, never touches PST/MSG.
- After --apply, re-run build_stakeholder_dim.py so latency rollups match.

Safety
------
Retention cascade only deletes rows tied to *expired* interaction_ids /
stakeholders that lose their last remaining row to this purge. It does NOT
re-sync stakeholder_dim to a partial interaction_fact (that would wipe dim
rows after a limited re-collect).
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd

ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
IN_DIR = os.path.join(ROOT, "01_data", "17_interactions")
INTER = os.path.join(IN_DIR, "interaction_fact.parquet")
COMMIT = os.path.join(IN_DIR, "commitment_fact.parquet")
STAKE = os.path.join(IN_DIR, "stakeholder_dim.parquet")
LATENCY = os.path.join(IN_DIR, "db_response_latency.parquet")
META_PATH = os.path.join(IN_DIR, "purge_expired.meta.json")


def _load(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    return pd.read_parquet(path)


def _write_if(apply: bool, path: str, df: pd.DataFrame) -> None:
    if apply:
        df.to_parquet(path, index=False)


def _sid_set(series: pd.Series) -> set[str]:
    return set(series.astype(str).replace("", pd.NA).dropna())


def _purge_retention(as_of: pd.Timestamp, apply: bool) -> dict[str, Any]:
    df = _load(INTER)
    if df is None:
        return {"ok": False, "reason": "missing interaction_fact"}
    if "retention_expires" not in df.columns:
        return {"ok": False, "reason": "no retention_expires column"}

    exp = pd.to_datetime(df["retention_expires"], errors="coerce")
    # Keep rows with null expiry (defensive) or still within retention.
    keep_mask = exp.isna() | (exp >= as_of.normalize())
    drop_mask = ~keep_mask
    dropped = int(drop_mask.sum())
    dropped_ids = set(df.loc[drop_mask, "interaction_id"].astype(str))
    dropped_sids = _sid_set(df.loc[drop_mask, "stakeholder_id"])
    remaining_sids = _sid_set(df.loc[keep_mask, "stakeholder_id"])
    # Only stakeholders whose last row in *this* file expires now.
    orphan_sids = dropped_sids - remaining_sids

    out: dict[str, Any] = {
        "ok": True,
        "mode": "retention",
        "as_of": str(as_of.date()),
        "interaction_fact": {
            "before": int(len(df)),
            "dropped": dropped,
            "after": int(keep_mask.sum()),
        },
    }
    if apply and dropped:
        _write_if(True, INTER, df.loc[keep_mask].copy())

    out["commitment_fact"] = _drop_commitments_by_interaction_ids(
        dropped_ids, apply=apply and dropped > 0
    )
    out["stakeholder_dim"] = _drop_stakeholders_by_ids(
        orphan_sids, apply=apply and dropped > 0
    )
    out["db_response_latency"] = _latency_note(LATENCY)
    return out


def _erase_stakeholder(stakeholder_id: str, apply: bool) -> dict[str, Any]:
    sid = (stakeholder_id or "").strip()
    if not sid:
        return {"ok": False, "reason": "empty stakeholder_id"}

    df = _load(INTER)
    if df is None:
        return {"ok": False, "reason": "missing interaction_fact"}
    if "stakeholder_id" not in df.columns:
        return {"ok": False, "reason": "no stakeholder_id column"}

    match = df["stakeholder_id"].astype(str) == sid
    dropped_ids = set(df.loc[match, "interaction_id"].astype(str))
    keep = ~match

    out: dict[str, Any] = {
        "ok": True,
        "mode": "dsar_erasure",
        "stakeholder_id": sid,
        "interaction_fact": {
            "before": int(len(df)),
            "dropped": int(match.sum()),
            "after": int(keep.sum()),
        },
    }
    if apply and int(match.sum()):
        _write_if(True, INTER, df.loc[keep].copy())

    out["commitment_fact"] = _drop_commitments_by_interaction_ids(
        dropped_ids, apply=apply
    )
    out["stakeholder_dim"] = _drop_stakeholders_by_ids({sid}, apply=apply)
    out["db_response_latency"] = _latency_note(LATENCY)
    return out


def _drop_commitments_by_interaction_ids(
    dropped_interaction_ids: set[str], apply: bool
) -> dict[str, Any]:
    cdf = _load(COMMIT)
    if cdf is None:
        return {"ok": False, "reason": "missing commitment_fact"}
    if not dropped_interaction_ids:
        return {
            "ok": True,
            "before": int(len(cdf)),
            "dropped": 0,
            "after": int(len(cdf)),
            "note": "No expired/targeted interaction_ids — commitments untouched.",
        }
    drop = cdf["interaction_id"].astype(str).isin(dropped_interaction_ids)
    result = {
        "ok": True,
        "before": int(len(cdf)),
        "dropped": int(drop.sum()),
        "after": int((~drop).sum()),
    }
    if apply and result["dropped"]:
        _write_if(True, COMMIT, cdf.loc[~drop].copy())
    return result


def _drop_stakeholders_by_ids(drop_ids: set[str], apply: bool) -> dict[str, Any]:
    sdf = _load(STAKE)
    if sdf is None:
        return {"ok": False, "reason": "missing stakeholder_dim"}
    if not drop_ids:
        return {
            "ok": True,
            "before": int(len(sdf)),
            "dropped": 0,
            "after": int(len(sdf)),
            "note": "No stakeholder ids targeted by this purge.",
        }
    drop = sdf["stakeholder_id"].astype(str).isin(drop_ids)
    result = {
        "ok": True,
        "before": int(len(sdf)),
        "dropped": int(drop.sum()),
        "after": int((~drop).sum()),
        "note": "Only ids that lost their last retained interaction (or DSAR target).",
    }
    if apply and result["dropped"]:
        _write_if(True, STAKE, sdf.loc[~drop].copy())
    return result


def _latency_note(path: str) -> dict[str, Any]:
    """Latency is DB-level; purge does not rewrite it in-place."""
    exists = os.path.exists(path)
    return {
        "ok": exists,
        "path": path,
        "touched": False,
        "note": (
            "Not rewritten by purge. After --apply, re-run "
            "04_tools/interactions/build_stakeholder_dim.py to refresh p50/p90."
            if exists
            else "missing db_response_latency — nothing to refresh"
        ),
    }


def _lookup_stakeholder(stakeholder_id: str) -> dict[str, Any]:
    sid = (stakeholder_id or "").strip()
    df = _load(INTER)
    cdf = _load(COMMIT)
    sdf = _load(STAKE)
    if df is None:
        return {"ok": False, "reason": "missing interaction_fact"}
    match = df["stakeholder_id"].astype(str) == sid
    ids = set(df.loc[match, "interaction_id"].astype(str))
    c_n = 0
    if cdf is not None and ids:
        c_n = int(cdf["interaction_id"].astype(str).isin(ids).sum())
    dim_hit = False
    if sdf is not None:
        dim_hit = bool((sdf["stakeholder_id"].astype(str) == sid).any())
    return {
        "ok": True,
        "mode": "dsar_lookup",
        "stakeholder_id": sid,
        "interaction_fact_rows": int(match.sum()),
        "commitment_fact_rows": c_n,
        "stakeholder_dim_row": dim_hit,
        "db_codes": sorted(df.loc[match, "db_code"].dropna().astype(str).unique().tolist()),
        "first_seen": str(pd.to_datetime(df.loc[match, "occurred_at"], errors="coerce").min())
        if int(match.sum())
        else None,
        "last_seen": str(pd.to_datetime(df.loc[match, "occurred_at"], errors="coerce").max())
        if int(match.sum())
        else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument(
        "--apply",
        action="store_true",
        help="write purged parquet (default: dry-run — no deletes)",
    )
    ap.add_argument(
        "--stakeholder-id",
        default="",
        help="DSAR erase mode: delete derived rows for this salted hash",
    )
    ap.add_argument(
        "--lookup",
        action="store_true",
        help="with --stakeholder-id: report counts only (never writes)",
    )
    args = ap.parse_args()

    if args.lookup:
        if not args.stakeholder_id:
            print(json.dumps({"ok": False, "reason": "--lookup requires --stakeholder-id"}, indent=2))
            return 1
        result = _lookup_stakeholder(args.stakeholder_id)
    elif args.stakeholder_id:
        result = _erase_stakeholder(args.stakeholder_id, apply=args.apply)
    else:
        as_of = pd.Timestamp(args.as_of)
        result = _purge_retention(as_of, apply=args.apply)

    print(json.dumps(result, indent=2, default=str))
    if not result.get("ok"):
        return 1

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder": "purge_expired.py",
        "applied": bool(args.apply) and not args.lookup,
        "dry_run": (not args.apply) or args.lookup,
        "outlook_touched": False,
        "mail_sent": False,
        **result,
        "note": (
            "Derived parquet only. Outlook untouched. G0a 2a.6. "
            "After --apply: re-run build_stakeholder_dim.py."
        ),
    }
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, default=str)
    print(f"wrote {META_PATH}")
    if args.lookup:
        print("lookup only — no deletes")
    elif not args.apply:
        print("dry-run — pass --apply to write")
    else:
        print("APPLIED — re-run build_stakeholder_dim.py to refresh latency")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
