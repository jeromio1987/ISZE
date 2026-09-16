"""Unit tests for P4 account-health calculators — no live mailbox, no billing lines."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from build_account_health import (
    THRESHOLDS,
    _breach,
    activity,
    classify_commitment,
    commitment_rates,
    escalation,
    latency_hours,
    route_alerts,
    shannon_norm,
    signal_to_order,
    topic_entropy_by_db,
)


def test_shannon_one_topic_is_zero():
    assert shannon_norm([10]) == 0.0


def test_shannon_two_equal_is_one():
    assert math.isclose(shannon_norm([5, 5]), 1.0)


def test_met_rate_low_is_red():
    spec = {"amber": 0.60, "red": 0.40, "direction": "low"}
    assert _breach(0.20, spec) == "RED"
    assert _breach(0.50, spec) == "AMBER"
    assert _breach(0.80, spec) is None


def test_latency_days_amber():
    spec = {"amber": 7.0, "red": 14.0}
    assert _breach(8.0, spec) == "AMBER"
    assert _breach(14.0, spec) == "RED"
    assert _breach(2.0, spec) is None


def test_classify_open_vs_missed():
    as_of = pd.Timestamp("2026-08-01", tz="UTC")
    due = pd.Timestamp("2026-09-01", tz="UTC")
    times = {"t1": pd.Series([pd.Timestamp("2026-07-01", tz="UTC")])}
    assert classify_commitment(due, None, "t1", times, as_of) == "open"
    due_past = pd.Timestamp("2026-06-01", tz="UTC")
    times_miss = {"t1": pd.Series([pd.Timestamp("2026-05-15", tz="UTC")])}
    assert classify_commitment(due_past, None, "t1", times_miss, as_of) == "missed"
    times2 = {"t1": pd.Series([
        pd.Timestamp("2026-05-01", tz="UTC"),
        pd.Timestamp("2026-06-15", tz="UTC"),
    ])}
    assert classify_commitment(due_past, pd.Timestamp("2026-05-01", tz="UTC"), "t1", times2, as_of) == "met"


def test_escalation_uses_n_cc():
    as_of = pd.Timestamp("2026-08-12", tz="UTC")
    idf = pd.DataFrame({
        "db_code": ["UMI", "UMI", "UTI", "UTI"],
        "thread_id": ["a", "a", "b", "c"],
        "n_cc": [4, 1, 0, 1],
        "occurred_at": [as_of - pd.Timedelta(days=2)] * 4,
        "direction": ["in"] * 4,
        "stakeholder_id": ["x"] * 4,
        "topics": [""] * 4,
        "part_numbers": [""] * 4,
        "n_part_numbers": [0] * 4,
    })
    esc = escalation(idf, as_of).set_index("db_code")["escalation_cadence"]
    assert math.isclose(esc["UMI"], 1.0)
    assert math.isclose(esc["UTI"], 0.0)


def test_umi_uti_not_blended_in_activity():
    as_of = pd.Timestamp("2026-08-12", tz="UTC")
    rows = []
    for db, n in [("UMI", 30), ("UTI", 10)]:
        for i in range(n):
            rows.append({
                "db_code": db,
                "occurred_at": as_of - pd.Timedelta(days=i % 10),
                "thread_id": f"{db}-{i}",
                "direction": "in",
                "stakeholder_id": "s",
                "n_cc": 0,
                "topics": "pricing",
                "part_numbers": "",
                "n_part_numbers": 0,
            })
    idf = pd.DataFrame(rows)
    act = activity(idf, as_of).set_index("db_code")
    assert act.loc["UMI", "n_30d"] == 30
    assert act.loc["UTI", "n_30d"] == 10


def test_signal_to_order_uses_mention_in_window():
    as_of = pd.Timestamp("2026-08-12", tz="UTC")
    idf = pd.DataFrame({
        "db_code": ["ITUK"] * 12,
        "occurred_at": [as_of - pd.Timedelta(days=5)] * 12,
        "thread_id": ["t"] * 12,
        "direction": ["in"] * 12,
        "part_numbers": ["ABC"] * 12,
        "n_part_numbers": [1] * 12,
        "n_cc": [0] * 12,
        "topics": [""] * 12,
        "stakeholder_id": ["s"] * 12,
    })
    orders = pd.DataFrame({
        "db_code": ["ITUK"],
        "part_number": ["ABC"],
        "billing_date": [as_of - pd.Timedelta(days=1)],
    })
    out = signal_to_order(idf, as_of, orders)
    assert out["n_pn_mentions"].iloc[0] == 12
    assert pd.notna(out["signal_to_order_days"].iloc[0])
    assert out["signal_to_order_days"].iloc[0] == 4.0


def test_signal_to_order_null_below_evidence():
    as_of = pd.Timestamp("2026-08-12", tz="UTC")
    idf = pd.DataFrame({
        "db_code": ["ITUK"] * 3,
        "occurred_at": [as_of - pd.Timedelta(days=5)] * 3,
        "thread_id": ["t"] * 3,
        "direction": ["in"] * 3,
        "part_numbers": ["ABC", "ABC", "ABC"],
        "n_part_numbers": [1, 1, 1],
        "n_cc": [0] * 3,
        "topics": [""] * 3,
        "stakeholder_id": ["s"] * 3,
    })
    orders = pd.DataFrame({
        "db_code": ["ITUK"],
        "part_number": ["ABC"],
        "billing_date": [as_of - pd.Timedelta(days=1)],
    })
    out = signal_to_order(idf, as_of, orders)
    assert out["n_pn_mentions"].iloc[0] == 3
    assert pd.isna(out["signal_to_order_days"].iloc[0])


def test_latency_hours_p50():
    as_of = pd.Timestamp("2026-08-12", tz="UTC")
    idf = pd.DataFrame({
        "db_code": ["ITUK"] * 4,
        "thread_id": ["t1"] * 4,
        "occurred_at": [
            as_of - pd.Timedelta(days=10),
            as_of - pd.Timedelta(days=9),
            as_of - pd.Timedelta(days=8),
            as_of - pd.Timedelta(days=7),
        ],
        "direction": ["in", "out", "in", "out"],
        "stakeholder_id": ["s"] * 4,
        "n_cc": [0] * 4,
        "topics": [""] * 4,
        "part_numbers": [""] * 4,
        "n_part_numbers": [0] * 4,
    })
    lat = latency_hours(idf, as_of).iloc[0]
    assert lat["n_replies"] == 2
    assert lat["response_latency_p50"] == 24.0  # 1 day in hours


def test_commitment_met_rate():
    as_of = pd.Timestamp("2026-08-15", tz="UTC")
    cdf = pd.DataFrame({
        "db_code": ["UMI", "UMI", "UTI"],
        "owner_side": ["db", "db", "db"],
        "due_date": [
            "2026-07-01",
            "2026-07-15",
            "2026-07-20",
        ],
        "made_at": [None, None, None],
        "thread_id": ["a", "b", "c"],
        "status": ["open", "open", "open"],
    })
    idf = pd.DataFrame({
        "db_code": ["UMI", "UMI", "UTI"],
        "thread_id": ["a", "b", "c"],
        "occurred_at": [
            pd.Timestamp("2026-07-05", tz="UTC"),
            pd.Timestamp("2026-06-01", tz="UTC"),
            pd.Timestamp("2026-07-25", tz="UTC"),
        ],
        "direction": ["out"] * 3,
        "stakeholder_id": ["s"] * 3,
        "n_cc": [0] * 3,
        "topics": [""] * 3,
        "part_numbers": [""] * 3,
        "n_part_numbers": [0] * 3,
    })
    out = commitment_rates(cdf, idf, as_of).set_index("db_code")
    assert math.isclose(out.loc["UMI", "commitment_met_rate"], 0.5)
    assert out.loc["UTI", "commitment_met_rate"] == 1.0


def test_topic_entropy_single_topic_is_zero():
    as_of = pd.Timestamp("2026-08-12", tz="UTC")
    rows = [{
        "db_code": "ITUK",
        "occurred_at": as_of - pd.Timedelta(days=1),
        "thread_id": "t",
        "direction": "in",
        "topics": "pricing",
        "stakeholder_id": "s",
        "n_cc": 0,
        "part_numbers": "",
        "n_part_numbers": 0,
    }] * 15
    ent = topic_entropy_by_db(pd.DataFrame(rows), as_of).iloc[0]["topic_entropy"]
    assert ent == 0.0
    assert ent < THRESHOLDS["topic_entropy"]["amber"]


def test_topic_entropy_balanced_is_high():
    as_of = pd.Timestamp("2026-08-12", tz="UTC")
    rows = []
    for topic in ("pricing", "delivery", "stock", "warranty"):
        for _ in range(5):
            rows.append({
                "db_code": "ITUK",
                "occurred_at": as_of - pd.Timedelta(days=1),
                "thread_id": f"t-{topic}",
                "direction": "in",
                "topics": topic,
                "stakeholder_id": "s",
                "n_cc": 0,
                "part_numbers": "",
                "n_part_numbers": 0,
            })
    ent = topic_entropy_by_db(pd.DataFrame(rows), as_of).iloc[0]["topic_entropy"]
    assert ent >= THRESHOLDS["topic_entropy"]["amber"]


def test_thresholds_dict_complete():
    required = {
        "latency_p50_days",
        "commitment_met_rate",
        "signal_to_order_lift",
        "stakeholder_churn_pct",
        "escalation_cadence",
        "topic_entropy",
        "activity_drop_pct",
        "overdue_commitments",
    }
    assert required <= set(THRESHOLDS.keys())


def test_route_alerts_activity_drop():
    row = pd.Series({
        "response_latency_p50": 2.0,
        "n_replies": 20,
        "commitment_met_rate": 0.80,
        "signal_to_order_lift": np.nan,
        "stakeholder_churn_pct": 0.05,
        "n_stakeholder_pool": 20,
        "escalation_cadence": 0.05,
        "n_threads_30d": 20,
        "topic_entropy": 0.80,
        "activity_drop_pct": 0.40,
        "n_commitments_scored": 10,
        "n_30d": 20,
        "overdue_commitments": 0,
    })
    level, reasons = route_alerts(row)
    assert level == "AMBER"
    assert any("mail volume" in r for r in reasons)
