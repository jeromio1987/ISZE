"""sold_to_sap wins over ship-to / wrong legal name in sold_to."""

from __future__ import annotations

import pandas as pd

from modules.data_prep import apply_distributor_codes, load_distributor_mapping
from config import resolve_mapping_path


def _map() -> pd.DataFrame:
    return load_distributor_mapping(str(resolve_mapping_path()))


def test_iuk_ship_to_89_does_not_override_sap_2574() -> None:
    df = pd.DataFrame(
        {
            "sold_to_sap": [2574, 2574],
            "sold_to": [89.0, "I.M. PARTS & SERVICE Limited"],
        }
    )
    out = apply_distributor_codes(df, _map())
    assert list(out["distributor_code"]) == ["IUK", "IUK"]


def test_ituk_sold_to_2194_does_not_become_midi() -> None:
    df = pd.DataFrame(
        {
            "sold_to_sap": [2575],
            "sold_to": [2194.0],
        }
    )
    out = apply_distributor_codes(df, _map())
    assert out.iloc[0]["distributor_code"] == "ITUK"


def test_uti_1799_not_umi_even_when_name_says_motors() -> None:
    df = pd.DataFrame(
        {
            "sold_to_sap": [1799, 1799, 1797],
            "sold_to": [1797.0, "UNIVERSAL MOTORS ISRAEL LTD", "UNIVERSAL MOTORS ISRAEL LTD"],
        }
    )
    out = apply_distributor_codes(df, _map())
    assert list(out["distributor_code"]) == ["UTI", "UTI", "UMI"]


def test_name_only_without_sap_still_maps() -> None:
    df = pd.DataFrame(
        {
            "sold_to": ["ISUZU IRELAND", "ISUZU TRUCK (UK) LIMITED"],
        }
    )
    out = apply_distributor_codes(df, _map())
    assert list(out["distributor_code"]) == ["IRELAND", "ITUK"]
