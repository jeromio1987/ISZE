"""Smoke tests for gps_reconcile.py — pure-function checks, no raw Excel loads.

Run: python -m pytest 04_tools/tests/test_gps_reconcile.py -q
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import gps_reconcile as gr  # noqa: E402


def test_parse_dashboard_vars_roundtrip():
    html = (
        'var BASE25=[["ITUK", 22389, 11834592.0, 5769867.82]];\n'
        'var WARR={"ITUK": 374426.05};\n'
        'var RATES=[296, 739, 887];\n'
    )
    out = gr._parse_dashboard_vars(html)
    assert out["BASE25"] == [["ITUK", 22389, 11834592.0, 5769867.82]]
    assert out["WARR"]["ITUK"] == 374426.05
    assert out["RATES"] == [296, 739, 887]


def test_num_eq_tolerance():
    assert gr._num_eq(100.0, 100.005)
    assert not gr._num_eq(100.0, 100.5)
    assert gr._num_eq({"a": [1.0, 2.0]}, {"a": [1.001, 2.0]})
    assert not gr._num_eq({"a": 1}, {"b": 1})


def test_waterfall_stages_partition_gross():
    df = pd.DataFrame({
        "billing_date": pd.to_datetime(["2025-05-01"] * 6),
        "billt": ["F2", "G2", "F2", "F2", "F2", "F2"],
        "saty": ["SOR", "SOR", "CR", "VOR", "SOR", "SOR"],
        "material": ["8971234560", "8971234560", "8971234560", "TRANSPORT", "5500471234", "SERVICE FEE X"],
        "net_value": [100.0, 50.0, 30.0, 20.0, 10.0, 5.0],
    })
    wf = gr._waterfall(df, neutralise=False)[2026]
    assert wf["gross"] == pytest.approx(215.0)
    assert wf["excl_billt"] == pytest.approx(50.0)
    assert wf["excl_saty_cr"] == pytest.approx(30.0)
    # TRANSPORT line has SaTy VOR but transport bucket comes after billt/saty
    assert wf["excl_transport"] == pytest.approx(20.0)
    assert wf["excl_shell"] == pytest.approx(10.0)
    assert wf["excl_other"] == pytest.approx(5.0)
    assert wf["clean"] == pytest.approx(100.0)
    total = sum(v for k, v in wf.items() if k not in ("gross",))
    assert total == pytest.approx(wf["gross"])


def test_waterfall_neutralise_divides_surcharge():
    df = pd.DataFrame({
        "billing_date": pd.to_datetime(["2025-05-01"]),
        "billt": ["F2"],
        "saty": ["VOR"],
        "material": ["8971234560"],
        "net_value": [107.0],
    })
    wf = gr._waterfall(df, neutralise=True)[2026]
    assert wf["clean"] == pytest.approx(100.0)


def test_payer_db_covers_known_payers():
    """Every payer that carries real money must be mapped (no UNK buckets)."""
    from rebuild_gps_billing_and_surcharge_check import PAYER_DB
    for code in ("2733", "2734", "373", "2194", "1576", "66", "86"):
        assert code in PAYER_DB, f"payer {code} missing from PAYER_DB"


def test_snapshot_and_report_schema():
    snap = gr.SNAPSHOT
    if not snap.exists():
        pytest.skip("snapshot not present")
    payload = json.loads(snap.read_text(encoding="utf-8"))
    assert {"base25", "warranty", "uio26", "uio27_max", "bp27", "rates"} <= set(payload)
    for row in payload["base25"]:
        assert len(row) == 4 and isinstance(row[0], str)
