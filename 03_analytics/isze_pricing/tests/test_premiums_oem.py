"""Unit tests — OEM peer premium gates + street resolve (no invent)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ENGINE = Path(__file__).resolve().parents[1]
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from ingest_oem_peer_street import resolve_street_eur  # noqa: E402
from premiums import (  # noqa: E402
    apply_oem_benchmark_to_config_block,
    load_oem_benchmark_from_basket,
)


def test_resolve_street_prefers_eur():
    row = pd.Series(
        {
            "peer_street_eur": 12.5,
            "peer_street_native": 10.0,
            "fx_rate_to_eur": 1.2,
            "currency": "GBP",
            "fx_as_of": "2026-08-10",
        }
    )
    eur, how = resolve_street_eur(row)
    assert eur == 12.5
    assert how == "peer_street_eur"


def test_resolve_street_native_fx():
    row = pd.Series(
        {
            "peer_street_eur": "",
            "peer_street_native": 10.0,
            "fx_rate_to_eur": 1.167208,
            "currency": "GBP",
            "fx_as_of": "2026-08-10",
        }
    )
    eur, how = resolve_street_eur(row)
    assert eur == pytest.approx(11.67208)
    assert "GBP→EUR" in how


def test_resolve_street_blank():
    row = pd.Series({"peer_street_eur": "", "peer_street_native": ""})
    eur, how = resolve_street_eur(row)
    assert eur is None
    assert how == ""


def test_oem_benchmark_requires_min_n(tmp_path: Path):
    basket = tmp_path / "b.csv"
    pd.DataFrame(
        [
            {
                "isze_pn": "1",
                "pms_category": "air_filter",
                "peer_market": "LCV",
                "peer_street_eur": 10.0,
            },
            {
                "isze_pn": "2",
                "pms_category": "air_filter",
                "peer_market": "LCV",
                "peer_street_eur": 11.0,
            },
            # only 2 priced → stay below gate
            {
                "isze_pn": "3",
                "pms_category": "oil_filter",
                "peer_market": "LCV",
                "peer_street_eur": 5.0,
            },
            {
                "isze_pn": "4",
                "pms_category": "oil_filter",
                "peer_market": "LCV",
                "peer_street_eur": 6.0,
            },
            {
                "isze_pn": "5",
                "pms_category": "oil_filter",
                "peer_market": "IUK",
                "peer_street_eur": 7.0,
            },
        ]
    ).to_csv(basket, index=False)

    oem = load_oem_benchmark_from_basket(basket)
    air = oem.loc[oem["cat"] == "air_filter"].iloc[0]
    oil = oem.loc[oem["cat"] == "oil_filter"].iloc[0]
    assert int(air["n_priced_peers"]) == 2
    assert int(oil["n_priced_peers"]) == 3

    by_cat = {
        "air_filter": {"value": 1.30, "basis": "iam_derived", "max_premium_pct": 30},
        "oil_filter": {"value": 1.30, "basis": "iam_derived", "max_premium_pct": 30},
    }
    out = apply_oem_benchmark_to_config_block(by_cat, path=basket)
    assert out["air_filter"]["basis"] == "iam_derived"
    assert out["oil_filter"]["basis"] == "oem_benchmark"
    assert out["oil_filter"]["evidence_n_oem_peers"] == 3


def test_live_basket_air_oil_unlocked():
    """Regression: current basket keeps air_filter + oil_filter at n≥3."""
    path = ENGINE / "oem_peer_basket.csv"
    if not path.is_file():
        pytest.skip("basket missing")
    oem = load_oem_benchmark_from_basket(path)
    unlocked = set(oem.loc[oem["n_priced_peers"] >= 3, "cat"])
    assert "air_filter" in unlocked
    assert "oil_filter" in unlocked
