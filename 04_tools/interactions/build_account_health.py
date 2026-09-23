"""P4 — account-health from live P2a tables (deterministic, no model, no 0–100).

Reads  : 01_data/17_interactions/{interaction,commitment,stakeholder}_*.parquet
         01_data/00_derived/sales_fact.parquet (PN + billing_date + sold_to_sap only)
         01_data/00_derived/distributor_dimension.csv (sold_to_sap → distributor_code)
Writes : 01_data/17_interactions/account_health.parquet  (+ .meta.json)

One row per distributor × month. Alert level is NONE | AMBER | RED from the
draft thresholds in 00_docs/P4_DETERMINISTIC_SIGNALS.md — uncalibrated.
Jerome still owns the 1-day threshold pass (task 4.9). Do not put this on a
shared pack.

CC-depth: interaction_fact.n_cc (already collected). Not a new MAPI field.
UTI and UMI stay separate rows. Own mailbox only (G0a).
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
IN_DIR = os.path.join(ROOT, "01_data", "17_interactions")
DERIVED = os.path.join(ROOT, "01_data", "00_derived")
INTER_SRC = os.path.join(IN_DIR, "interaction_fact.parquet")
COMMIT_SRC = os.path.join(IN_DIR, "commitment_fact.parquet")
SALES_SRC = os.path.join(DERIVED, "sales_fact.parquet")
DIM_SRC = os.path.join(DERIVED, "distributor_dimension.csv")
OUT_PARQUET = os.path.join(IN_DIR, "account_health.parquet")
OUT_META = os.path.join(IN_DIR, "account_health.meta.json")

BUILDER_VERSION = "p4-v2"
MIN_LATENCY_REPLIES = 10
MIN_PN_MENTIONS = 10
ACTIVE_DAYS = 90

# Staleness guard: if the newest message in interaction_fact is more than this
# many days older than the newest usable billing_date, the meta gets
# inputs_stale = true. 14 days is a convention, not a calibrated number: the
# mail layer is refreshed by hand, and a monthly refresh keeps the newest
# message within a few days of the newest billing month. 14 days absorbs a
# collector run in the first half of the following month, and fires once a whole
# refresh cycle has been skipped. Override with ISZE_MAIL_LAG_GUARD_DAYS.
MAIL_LAG_GUARD_DAYS = int(os.environ.get("ISZE_MAIL_LAG_GUARD_DAYS", "14"))

# Draft — 00_docs/P4_DETERMINISTIC_SIGNALS.md §2. Not calibrated.
THRESHOLDS = {
    "latency_p50_days": {"amber": 7.0, "red": 14.0},
    "commitment_met_rate": {"amber": 0.60, "red": 0.40, "direction": "low"},
    "signal_to_order_lift": {"amber": 0.50, "red": 1.00},
    "stakeholder_churn_pct": {"amber": 0.25, "red": 0.50},
    "escalation_cadence": {"amber": 0.20, "red": 0.40},
    "topic_entropy": {"amber": 0.40, "red": 0.30, "direction": "low"},
    "activity_drop_pct": {"amber": 0.30, "red": 0.50},
    "overdue_commitments": {"amber": 2, "red": 4},
}


def _ts(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, utc=True, errors="coerce")


def order_coverage(orders: pd.DataFrame | None, as_of: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """Usable billing coverage for an as_of month, derived from the order table.

    Billing is monthly: `billing_date` is materialised as the period end. For a
    partial month (as_of before that period end) the file's max date would sit in
    the future and nothing could join, so the upper bound is clipped to as_of.
    """
    if orders is None or orders.empty or "billing_date" not in orders.columns:
        return None
    b = pd.to_datetime(orders["billing_date"], utc=True, errors="coerce").dropna()
    if b.empty:
        return None
    return b.min(), min(b.max(), as_of)


def mail_lag_exceeds_guard(bill_max, mail_max, guard_days: int = MAIL_LAG_GUARD_DAYS) -> bool:
    """True when the mail layer is stale relative to the billing layer.

    Missing either date counts as stale: an unknown input must never be silent.
    """
    if bill_max is None or mail_max is None or pd.isna(bill_max) or pd.isna(mail_max):
        return True
    return bool((pd.Timestamp(bill_max) - pd.Timestamp(mail_max)).days > guard_days)


def _window(df: pd.DataFrame, as_of: pd.Timestamp, days: int, col: str = "occurred_at") -> pd.DataFrame:
    start = as_of - pd.Timedelta(days=days)
    t = _ts(df[col])
    return df.loc[(t > start) & (t <= as_of)].copy()


def shannon_norm(counts: list[int]) -> float:
    """Normalized Shannon entropy in [0, 1]. One topic → 0; uniform → 1."""
    vals = [c for c in counts if c > 0]
    if len(vals) <= 1:
        return 0.0
    total = float(sum(vals))
    h = -sum((c / total) * math.log(c / total) for c in vals)
    return float(h / math.log(len(vals)))


def classify_commitment(due, made, thread_id: str, thread_times: dict, as_of: pd.Timestamp) -> str:
    if pd.isna(due) or not thread_id:
        return "unknown"
    due_ts = pd.Timestamp(due)
    if due_ts.tzinfo is None:
        due_ts = due_ts.tz_localize("UTC")
    else:
        due_ts = due_ts.tz_convert("UTC")
    times = thread_times.get(thread_id)
    later = times[times >= due_ts] if times is not None and len(times) else pd.Series(dtype="datetime64[ns, UTC]")
    if made is not None and not pd.isna(made):
        made_ts = pd.Timestamp(made)
        if made_ts.tzinfo is None:
            made_ts = made_ts.tz_localize("UTC")
        later = later[later > made_ts]
    if len(later) > 0:
        return "met"
    if due_ts.normalize() >= as_of.tz_convert("UTC").normalize():
        return "open"
    return "missed"


def latency_hours(idf: pd.DataFrame, as_of: pd.Timestamp, days: int = 30) -> pd.DataFrame:
    w = _window(idf, as_of, days)
    w = w.dropna(subset=["occurred_at"]).sort_values("occurred_at")
    rows = []
    for (db, thread), grp in w.groupby(["db_code", "thread_id"], dropna=False):
        if not thread:
            continue
        pending = None
        for occurred, direction in grp[["occurred_at", "direction"]].itertuples(index=False):
            if direction == "in" and pending is None:
                pending = occurred
            elif direction == "out" and pending is not None:
                hours = (pd.Timestamp(occurred) - pd.Timestamp(pending)).total_seconds() / 3600.0
                if hours >= 0:
                    rows.append({"db_code": db, "hours": hours})
                pending = None
    if not rows:
        return pd.DataFrame(columns=["db_code", "n_replies", "response_latency_p50", "response_latency_p90"])
    p = pd.DataFrame(rows)
    out = (
        p.groupby("db_code")["hours"]
        .agg(n_replies="size", response_latency_p50="median", response_latency_p90=lambda s: s.quantile(0.9))
        .reset_index()
    )
    out["response_latency_p50"] = out["response_latency_p50"].round(1)
    out["response_latency_p90"] = out["response_latency_p90"].round(1)
    return out


def commitment_rates(cdf: pd.DataFrame, idf: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """db→ISZE promises with due_date in the last 90d, reclassified at as_of."""
    if cdf.empty:
        return pd.DataFrame(columns=["db_code", "commitment_met_rate", "overdue_commitments", "n_commitments_scored"])
    thread_times = {
        tid: _ts(g["occurred_at"]).dropna().sort_values()
        for tid, g in idf.groupby("thread_id")
        if tid
    }
    c = cdf[cdf["owner_side"].astype(str) == "db"].copy()
    c["due_date"] = pd.to_datetime(c["due_date"], utc=True, errors="coerce")
    start = as_of - pd.Timedelta(days=90)
    due_in = c[(c["due_date"] > start) & (c["due_date"] <= as_of)].copy()
    if due_in.empty:
        return pd.DataFrame(columns=["db_code", "commitment_met_rate", "overdue_commitments", "n_commitments_scored"])
    due_in["status_at"] = [
        classify_commitment(r["due_date"], r.get("made_at"), r.get("thread_id") or "", thread_times, as_of)
        for r in due_in.to_dict("records")
    ]
    scored = due_in[due_in["status_at"].isin(["met", "missed"])]
    met = (
        scored.groupby("db_code")["status_at"]
        .apply(lambda s: float((s == "met").mean()) if len(s) else np.nan)
        .rename("commitment_met_rate")
    )
    n_scored = scored.groupby("db_code").size().rename("n_commitments_scored")
    last30 = as_of - pd.Timedelta(days=30)
    overdue = (
        due_in[(due_in["status_at"] == "missed") & (due_in["due_date"] > last30)]
        .groupby("db_code")
        .size()
        .rename("overdue_commitments")
    )
    out = pd.concat([met, n_scored, overdue], axis=1).reset_index()
    out["overdue_commitments"] = out["overdue_commitments"].fillna(0).astype(int)
    out["n_commitments_scored"] = out["n_commitments_scored"].fillna(0).astype(int)
    return out


def stakeholder_churn(idf: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    hist = idf[( _ts(idf["occurred_at"]) <= as_of) & (idf["stakeholder_id"].astype(str) != "")].copy()
    if hist.empty:
        return pd.DataFrame(columns=["db_code", "stakeholder_churn_pct"])
    last = hist.groupby(["db_code", "stakeholder_id"])["occurred_at"].max()
    first = hist.groupby(["db_code", "stakeholder_id"])["occurred_at"].min()
    db_last = hist.groupby("db_code")["occurred_at"].max()
    recs = []
    cutoff = as_of - pd.Timedelta(days=ACTIVE_DAYS)
    for (db, sid), last_seen in last.items():
        last_seen = pd.Timestamp(last_seen)
        if last_seen.tzinfo is None:
            last_seen = last_seen.tz_localize("UTC")
        first_seen = pd.Timestamp(first.loc[(db, sid)])
        if first_seen.tzinfo is None:
            first_seen = first_seen.tz_localize("UTC")
        db_ls = pd.Timestamp(db_last.loc[db])
        if db_ls.tzinfo is None:
            db_ls = db_ls.tz_localize("UTC")
        active = last_seen > cutoff
        seen_before = first_seen <= cutoff
        db_still = db_ls > cutoff
        churn = (not active) and seen_before and db_still
        recs.append({"db_code": db, "active": active, "churn": churn})
    s = pd.DataFrame(recs)
    g = s.groupby("db_code")
    pool = g["active"].sum() + g["churn"].sum()
    pct = (g["churn"].sum() / pool.replace(0, np.nan)).rename("stakeholder_churn_pct")
    n_pool = pool.rename("n_stakeholder_pool")
    return pd.concat([pct, n_pool], axis=1).reset_index()


def escalation(idf: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    w = _window(idf, as_of, 30)
    w = w[w["thread_id"].astype(str) != ""]
    if w.empty:
        return pd.DataFrame(columns=["db_code", "escalation_cadence"])
    thr = w.groupby(["db_code", "thread_id"])["n_cc"].max().reset_index()
    n_thr = thr.groupby("db_code").size().rename("n_threads_30d")
    cad = (
        thr.groupby("db_code")["n_cc"]
        .apply(lambda s: float((s >= 3).mean()))
        .rename("escalation_cadence")
    )
    return pd.concat([cad, n_thr], axis=1).reset_index()


def topic_entropy_by_db(idf: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    w = _window(idf, as_of, 90)
    w = w[w["topics"].astype(str) != ""]
    if w.empty:
        return pd.DataFrame(columns=["db_code", "topic_entropy"])
    t = w.assign(topic=w["topics"].astype(str).str.split(",")).explode("topic")
    t["topic"] = t["topic"].str.strip()
    t = t[t["topic"] != ""]
    rows = []
    for db, g in t.groupby("db_code"):
        counts = g["topic"].value_counts().tolist()
        rows.append({"db_code": db, "topic_entropy": round(shannon_norm(counts), 3)})
    return pd.DataFrame(rows)


def activity(idf: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    now = _window(idf, as_of, 30)
    prev = _window(idf, as_of - pd.Timedelta(days=30), 30)
    n_now = now.groupby("db_code").size().rename("n_30d")
    n_prev = prev.groupby("db_code").size().rename("n_prev_30d")
    out = pd.DataFrame({"n_30d": n_now, "n_prev_30d": n_prev}).fillna(0)
    out.index.name = "db_code"
    out = out.reset_index()
    out["activity_volume_per_day"] = (out["n_30d"] / 30.0).round(2)
    prev_n = out["n_prev_30d"].replace(0, np.nan)
    out["activity_drop_pct"] = ((prev_n - out["n_30d"]) / prev_n).round(3)
    return out[["db_code", "activity_volume_per_day", "activity_drop_pct", "n_30d"]]


def _norm_pn(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.upper().str.replace(" ", "", regex=False)


def signal_to_order(
    idf: pd.DataFrame,
    as_of: pd.Timestamp,
    orders: pd.DataFrame | None,
    coverage: tuple[pd.Timestamp, pd.Timestamp] | None = None,
) -> pd.DataFrame:
    """Median days from first mail PN mention to first later ISZE billing, 90d.

    NULL unless >= MIN_PN_MENTIONS interactions with a PN in the window.

    ``coverage`` is the billing coverage of the order table as (min, max). The
    90-day window becomes [max(as_of - 90d, cov_min), min(as_of, cov_max)], so it
    never reaches past the last month the file actually bills. The upper bound is
    clipped to ``as_of`` even when coverage is None: a month's metric must not see
    billing dated after the month it is measuring (the p4-v1 code had no upper
    bound at all, which let later orders join an earlier month).
    """
    w = _window(idf, as_of, 90)
    n_pn = (
        w[w["n_part_numbers"].fillna(0) > 0]
        .groupby("db_code")
        .size()
        .rename("n_pn_mentions")
    )
    empty = pd.DataFrame(columns=["db_code", "signal_to_order_days", "n_pn_mentions"])
    if orders is None or orders.empty or w.empty:
        return n_pn.reset_index().assign(signal_to_order_days=np.nan) if len(n_pn) else empty

    mail = w[w["part_numbers"].astype(str) != ""].copy()
    mail["pn"] = mail["part_numbers"].astype(str).str.split(",")
    mail = mail.explode("pn")
    mail["pn"] = _norm_pn(mail["pn"])
    mail = mail[mail["pn"] != ""]
    mail["occurred_at"] = _ts(mail["occurred_at"])
    first_mail = (
        mail.groupby(["db_code", "pn"])["occurred_at"].min().rename("first_mail")
    )

    o = orders.copy()
    o["pn"] = _norm_pn(o["part_number"])
    o["billing_date"] = pd.to_datetime(o["billing_date"], utc=True, errors="coerce")
    o = o.dropna(subset=["billing_date", "pn", "db_code"])
    start = as_of - pd.Timedelta(days=90)
    end = as_of
    if coverage is not None:
        # Use the file's real coverage instead of a hardcoded belief about it.
        start = max(start, coverage[0])
        end = min(as_of, coverage[1])
    if start >= end:
        out = n_pn.reset_index()
        out["signal_to_order_days"] = np.nan
        return out
    o = o[
        (o["billing_date"] >= start)
        & (o["billing_date"] <= end)
        & (o["db_code"].isin(mail["db_code"].unique()))
    ]
    # First mention *in this window*, then first ISZE billing at/after that mail.
    joined = first_mail.reset_index().merge(o, on=["db_code", "pn"], how="inner")
    joined = joined[joined["billing_date"] >= joined["first_mail"]]
    if joined.empty:
        out = n_pn.reset_index()
        out["signal_to_order_days"] = np.nan
        return out
    first_hit = (
        joined.groupby(["db_code", "pn"], as_index=False)
        .agg(first_mail=("first_mail", "min"), first_order=("billing_date", "min"))
    )
    first_hit["days"] = (
        first_hit["first_order"] - first_hit["first_mail"]
    ).dt.total_seconds() / 86400.0
    med = first_hit.groupby("db_code")["days"].median().rename("signal_to_order_days")
    out = pd.concat([n_pn, med], axis=1)
    out.index.name = "db_code"
    out = out.reset_index()
    out["n_pn_mentions"] = out["n_pn_mentions"].fillna(0).astype(int)
    out.loc[out["n_pn_mentions"] < MIN_PN_MENTIONS, "signal_to_order_days"] = np.nan
    return out


def load_orders() -> pd.DataFrame | None:
    if not os.path.exists(SALES_SRC) or not os.path.exists(DIM_SRC):
        return None
    dim = pd.read_csv(DIM_SRC)
    dim = dim[dim["network_role"].astype(str) == "network_db"][["sold_to_sap", "distributor_code"]]
    dim = dim.dropna(subset=["distributor_code"])
    dim["sold_to_sap"] = pd.to_numeric(dim["sold_to_sap"], errors="coerce")
    cols = ["billing_date", "sold_to_sap", "part_number"]
    extra = []
    # billed_qty optional — exclude zero/credit noise when present
    import pyarrow.parquet as pq
    names = pq.read_schema(SALES_SRC).names
    if "billed_qty" in names:
        extra.append("billed_qty")
    sf = pd.read_parquet(SALES_SRC, columns=cols + extra)
    sf["sold_to_sap"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    if extra:
        sf = sf[sf["billed_qty"].fillna(0) != 0]
    sf = sf.merge(dim, on="sold_to_sap", how="inner")
    sf = sf.rename(columns={"distributor_code": "db_code"})
    return sf[["db_code", "part_number", "billing_date"]]


def _breach(value, spec: dict) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    direction = spec.get("direction", "high")
    amber, red = spec["amber"], spec["red"]
    if direction == "low":
        if value < red:
            return "RED"
        if value < amber:
            return "AMBER"
        return None
    if value >= red:
        return "RED"
    if value >= amber:
        return "AMBER"
    return None


def route_alerts(row: pd.Series) -> tuple[str, list[str]]:
    reasons: list[str] = []
    worst = "NONE"
    checks = [
        (
            "latency",
            (row["response_latency_p50"] / 24.0)
            if pd.notna(row.get("response_latency_p50")) and row.get("n_replies", 0) >= MIN_LATENCY_REPLIES
            else np.nan,
            THRESHOLDS["latency_p50_days"],
            lambda v: f"response p50 {v:.1f}d",
        ),
        (
            "met_rate",
            row.get("commitment_met_rate")
            if row.get("n_commitments_scored", 0) >= 5
            else np.nan,
            THRESHOLDS["commitment_met_rate"],
            lambda v: f"db keep-rate {v:.0%}",
        ),
        (
            "order_lift",
            row.get("signal_to_order_lift"),
            THRESHOLDS["signal_to_order_lift"],
            lambda v: f"mail-to-order +{v:.0%} vs 6mo",
        ),
        (
            "churn",
            row.get("stakeholder_churn_pct")
            if row.get("n_stakeholder_pool", 0) >= MIN_LATENCY_REPLIES
            else np.nan,
            THRESHOLDS["stakeholder_churn_pct"],
            lambda v: f"stakeholder quiet {v:.0%}",
        ),
        (
            "escalation",
            row.get("escalation_cadence")
            if row.get("n_threads_30d", 0) >= MIN_LATENCY_REPLIES
            else np.nan,
            THRESHOLDS["escalation_cadence"],
            lambda v: f"CC>=3 threads {v:.0%}",
        ),
        (
            "entropy",
            row.get("topic_entropy")
            if row.get("n_30d", 0) >= 10
            else np.nan,
            THRESHOLDS["topic_entropy"],
            lambda v: f"topic entropy {v:.2f} (narrow)",
        ),
        (
            "activity",
            row.get("activity_drop_pct"),
            THRESHOLDS["activity_drop_pct"],
            lambda v: f"mail volume −{v:.0%}",
        ),
        (
            "overdue",
            float(row["overdue_commitments"]) if pd.notna(row.get("overdue_commitments")) else np.nan,
            THRESHOLDS["overdue_commitments"],
            lambda v: f"{int(v)} missed dues in 30d",
        ),
    ]
    rank = {"NONE": 0, "AMBER": 1, "RED": 2}
    for _name, val, spec, fmt in checks:
        hit = _breach(val if pd.notna(val) else np.nan, spec)
        if hit:
            reasons.append(fmt(val))
            if rank[hit] > rank[worst]:
                worst = hit
    return worst, reasons


def month_ends(idf: pd.DataFrame) -> list[tuple[str, pd.Timestamp, bool]]:
    t = _ts(idf["occurred_at"]).dropna()
    data_min, data_max = t.min(), t.max()
    periods = pd.period_range(
        data_min.tz_convert("UTC").tz_localize(None).to_period("M"),
        data_max.tz_convert("UTC").tz_localize(None).to_period("M"),
        freq="M",
    )
    out = []
    for p in periods:
        end = pd.Timestamp(p.end_time, tz="UTC")
        as_of = min(end, data_max)
        partial = as_of < end - pd.Timedelta(hours=12)
        # first month also partial if collection didn't start on day 1
        if p == periods[0] and data_min.day > 1:
            partial = True
        out.append((str(p), as_of, bool(partial)))
    return out


def build(
    idf: pd.DataFrame,
    cdf: pd.DataFrame,
    orders: pd.DataFrame | None,
) -> pd.DataFrame:
    dbs = sorted(idf["db_code"].dropna().unique().tolist())
    rows = []
    extractor = ""
    if "extractor_version" in idf.columns and len(idf):
        extractor = str(idf["extractor_version"].mode().iat[0])
    produced = datetime.now(timezone.utc)

    for year_month, as_of, partial in month_ends(idf):
        # Billing coverage clipped to this month, so a partial month cannot look
        # for orders after the last date it is allowed to see.
        cov = order_coverage(orders, as_of)
        lat = latency_hours(idf, as_of)
        com = commitment_rates(cdf, idf, as_of)
        chu = stakeholder_churn(idf, as_of)
        esc = escalation(idf, as_of)
        ent = topic_entropy_by_db(idf, as_of)
        act = activity(idf, as_of)
        s2o = signal_to_order(idf, as_of, orders, cov)

        # 6-month baseline for signal→order lift (complete prior months only)
        base_end = as_of - pd.Timedelta(days=30)
        hist = None
        if orders is not None and not orders.empty:
            hist = signal_to_order(idf, base_end, orders, order_coverage(orders, base_end))
            hist = hist.rename(columns={"signal_to_order_days": "s2o_baseline", "n_pn_mentions": "n_pn_base"})

        pieces = [lat, com, chu, esc, ent, act, s2o]
        if hist is not None:
            pieces.append(hist[["db_code", "s2o_baseline"]] if "s2o_baseline" in hist.columns else hist)
        merged = dbs_frame(dbs)
        for p in pieces:
            if p is None or p.empty or "db_code" not in p.columns:
                continue
            merged = merged.merge(p, on="db_code", how="left")

        if "signal_to_order_days" in merged.columns and "s2o_baseline" in merged.columns:
            b = merged["s2o_baseline"].replace(0, np.nan)
            merged["signal_to_order_lift"] = (merged["signal_to_order_days"] - merged["s2o_baseline"]) / b
        else:
            merged["signal_to_order_lift"] = np.nan

        for db in dbs:
            r = merged.loc[merged["db_code"] == db].iloc[0]
            n_30 = int(r["n_30d"]) if "n_30d" in merged.columns and pd.notna(r.get("n_30d")) else 0
            if n_30 == 0 and _window(idf[idf["db_code"] == db], as_of, 90).empty:
                continue
            level, reasons = route_alerts(r)
            rows.append(
                {
                    "db_code": db,
                    "year_month": year_month,
                    "response_latency_p50": r.get("response_latency_p50"),
                    "response_latency_p90": r.get("response_latency_p90"),
                    "n_replies": int(r["n_replies"]) if pd.notna(r.get("n_replies")) else 0,
                    "commitment_met_rate": r.get("commitment_met_rate"),
                    "n_commitments_scored": int(r["n_commitments_scored"]) if pd.notna(r.get("n_commitments_scored")) else 0,
                    "signal_to_order_days": r.get("signal_to_order_days"),
                    "signal_to_order_lift": r.get("signal_to_order_lift"),
                    "n_pn_mentions": int(r["n_pn_mentions"]) if pd.notna(r.get("n_pn_mentions")) else 0,
                    "stakeholder_churn_pct": r.get("stakeholder_churn_pct"),
                    "n_stakeholder_pool": int(r["n_stakeholder_pool"]) if pd.notna(r.get("n_stakeholder_pool")) else 0,
                    "escalation_cadence": r.get("escalation_cadence"),
                    "n_threads_30d": int(r["n_threads_30d"]) if pd.notna(r.get("n_threads_30d")) else 0,
                    "topic_entropy": r.get("topic_entropy"),
                    "activity_volume_per_day": r.get("activity_volume_per_day"),
                    "activity_drop_pct": r.get("activity_drop_pct"),
                    "n_30d": n_30,
                    "overdue_commitments": int(r["overdue_commitments"]) if pd.notna(r.get("overdue_commitments")) else 0,
                    "alert_level": level,
                    "alert_reasons": "|".join(reasons),
                    "is_partial_month": partial,
                    "as_of": as_of.date().isoformat(),
                    "produced_at": produced.isoformat(timespec="seconds"),
                    "extractor_version": extractor,
                    "builder_version": BUILDER_VERSION,
                    "thresholds_calibrated": False,
                }
            )
    return pd.DataFrame(rows)


def dbs_frame(dbs: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"db_code": dbs})


def main() -> int:
    if not os.path.exists(INTER_SRC):
        print(f"MISSING: {INTER_SRC}\nRun collect_mapi.py first.", file=sys.stderr)
        return 1
    idf = pd.read_parquet(INTER_SRC)
    cdf = pd.read_parquet(COMMIT_SRC) if os.path.exists(COMMIT_SRC) else pd.DataFrame()
    print(f"interactions {len(idf):,} | commitments {len(cdf):,} | dbs {idf['db_code'].nunique()}")
    if "UMI" in set(idf["db_code"]) and "UTI" in set(idf["db_code"]):
        print("UMI and UTI both present - kept as separate rows (never blended).")

    print("loading ISZE billing for mail-to-order (PN + date + sold-to only)...")
    orders = load_orders()
    mail_max = _ts(idf["occurred_at"]).max()
    if orders is None:
        print("sales_fact or distributor_dimension missing - mail-to-order will be NULL")
        coverage = None
        bill_min = bill_max = None
        stale = True
        lag_days = None
    else:
        print(f"order rows mapped to a network DB: {len(orders):,}")
        b = pd.to_datetime(orders["billing_date"], utc=True, errors="coerce").dropna()
        bill_min, bill_max = b.min(), b.max()
        coverage = (bill_min, bill_max)
        # Guard: mail older than billing by more than MAIL_LAG_GUARD_DAYS.
        lag_days = int((bill_max - mail_max).days) if pd.notna(mail_max) else None
        stale = mail_lag_exceeds_guard(bill_max, mail_max)
        print(f"billing coverage {bill_min.date()} .. {bill_max.date()} | "
              f"newest mail {mail_max.date() if pd.notna(mail_max) else 'n/a'} | "
              f"mail lag {lag_days}d (guard {MAIL_LAG_GUARD_DAYS}d) -> inputs_stale={stale}")

    out = build(idf, cdf, orders)
    if out.empty:
        print("no account_health rows")
        return 1

    out.to_parquet(OUT_PARQUET, index=False)
    latest = out["year_month"].max()
    snap = out[out["year_month"] == latest]
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder_version": BUILDER_VERSION,
        "rows": int(len(out)),
        "distributors": int(out["db_code"].nunique()),
        "months": sorted(out["year_month"].unique().tolist()),
        "latest_month": latest,
        "latest_alert_counts": snap["alert_level"].value_counts().to_dict(),
        "thresholds": THRESHOLDS,
        "thresholds_calibrated": False,
        "cc_depth_proxy": "n_cc (P2a already collected; P2a.9 not required)",
        "commitment_side": "owner_side=db (db→ISZE promises) for met-rate",
        "overdue_definition": "db-side missed with due_date in last 30d (state machine has no open+overdue)",
        "latency_alert_unit": "spec §2 is days; observed p50 is hours so latency rarely trips until 4.9",
        "billing_coverage_note": "derived at build time from sales_fact.parquet billing_date; the 90d mail-to-order window is intersected with this range",
        "sales_fact_note_removed": "p4-v1 claimed billing ends 2026-03-31. That was false and was never implemented in the windowing code; see P4_TIMESTAMP_FIX_2026-09-22.md",
        "uti_umi": "separate rows, never blended",
        "mailbox_scope": "G0a own mailbox only",
        "contains_message_content": False,
        "inputs_stale": stale,
        "internal_only": True,
        "note": "Draft thresholds. Do not treat RED as a validated KPI. Early Warning remains the sales call list.",
    }
    if orders is not None and bill_min is not None:
        meta["billing_coverage"] = {
            "min": bill_min.date().isoformat(),
            "max": bill_max.date().isoformat(),
            "source": "01_data/00_derived/sales_fact.parquet",
            "derived": True,
        }
        meta["billing_window_guard"] = {
            "rule": "signal_to_order 90d window is intersected with billing coverage",
            "lower_bound": "max(as_of - 90d, billing min)",
            "upper_bound": "min(as_of, billing max)",
        }
    meta["mail_coverage"] = {
        "min": mail_max.date().isoformat() if pd.notna(mail_max) else None,
        "max": mail_max.date().isoformat() if pd.notna(mail_max) else None,
        "newest_message": mail_max.isoformat() if pd.notna(mail_max) else None,
        "source": "01_data/17_interactions/interaction_fact.parquet",
        "derived": True,
    }
    meta["mail_vs_billing_lag_days"] = lag_days
    meta["staleness_guard"] = {
        "rule": "inputs_stale = newest mail older than newest billing by more than the guard window",
        "guard_days": MAIL_LAG_GUARD_DAYS,
        "override_env": "ISZE_MAIL_LAG_GUARD_DAYS",
        "why": "14 days is a convention: the mail layer is refreshed by hand and a monthly refresh keeps the newest message within days of the newest billing month. 14 days absorbs a run in the first half of the following month and fires once a full refresh cycle is skipped.",
        "refresh_command": "python -u %ISZE_ROOT%\\04_tools\\interactions\\collect_mapi.py --since 2024-08-01 --folders inbox,sent --dry-run  (then without --dry-run; mailbox must be open in the agent browser), then build_commitment_status.py, build_stakeholder_dim.py, build_account_health.py",
    }
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    if stale:
        print(f"\n** INPUT STALE: newest mail {meta['mail_coverage']['max']} vs newest billing "
              f"{meta['billing_coverage']['max'] if 'billing_coverage' in meta else 'n/a'} "
              f"(lag {lag_days}d > guard {MAIL_LAG_GUARD_DAYS}d). See meta.inputs_stale **")

    print(f"\nwrote {OUT_PARQUET} ({len(out):,} rows)")
    print(f"latest {latest}  partial={bool(snap['is_partial_month'].iloc[0])}")
    print("alert_level:\n", snap["alert_level"].value_counts().to_string())
    flagged = snap[snap["alert_level"] != "NONE"].sort_values(
        ["alert_level", "db_code"], ascending=[True, True]
    )
    if len(flagged):
        print("\nflagged (draft thresholds - not calibrated):")
        show = flagged[["db_code", "alert_level", "alert_reasons", "commitment_met_rate", "activity_drop_pct"]]
        print(show.to_string(index=False))

    triage_path = os.path.join(IN_DIR, "ACCOUNT_HEALTH_OPS_TRIAGE.md")
    csv_path = os.path.join(IN_DIR, "account_health_ops_triage.csv")
    flagged_csv = os.path.join(IN_DIR, "account_health_latest_flagged.csv")
    export_cols = [
        "db_code",
        "year_month",
        "alert_level",
        "alert_reasons",
        "commitment_met_rate",
        "activity_drop_pct",
        "stakeholder_churn_pct",
        "overdue_commitments",
        "n_30d",
    ]
    keep = [c for c in export_cols if c in snap.columns]
    snap[keep].to_csv(csv_path, index=False)
    flagged[keep].to_csv(flagged_csv, index=False)
    lines = [
        "# Account health ops triage (internal · draft · not a KPI)",
        "",
        f"Latest month: **{latest}** · flagged: **{len(flagged)}** distributors",
        "",
        "Uncalibrated thresholds. Jerome owns calibration (4.9). Do not put this on a Monday pack.",
        "",
        "| DB | Level | Reasons | Activity drop |",
        "|----|-------|---------|---------------|",
    ]
    for _, r in flagged.iterrows():
        drop = r.get("activity_drop_pct")
        drop_s = f"{float(drop)*100:.0f}%" if pd.notna(drop) else "—"
        lines.append(
            f"| {r['db_code']} | {r['alert_level']} | {str(r.get('alert_reasons') or '').replace('|', '/')} | {drop_s} |"
        )
    if flagged.empty:
        lines.append("| — | NONE | No draft flags this month | — |")
    lines += [
        "",
        "Full export: `account_health_ops_triage.csv` · calibration: `account_health_calibration.csv`",
        "",
        "Went quiet = activity drop and/or stakeholder churn on draft thresholds. Not a meeting KPI.",
    ]
    with open(triage_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {triage_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
