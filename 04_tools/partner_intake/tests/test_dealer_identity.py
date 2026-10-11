"""Dealer identity matching. Names here are made up."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[2]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from partner_intake.dealer_identity import confirm, match, normalize_name


def test_exact_match() -> None:
    dealers = [
        {"dealer_id": "D1", "dealer_name": "North Yard Motors", "distributor_id": "CEE"},
        {"dealer_id": "D2", "dealer_name": "Hilltop Vans", "distributor_id": "CEE"},
    ]
    accounts = [
        {"account_id": "A1", "account_name": "North Yard Motors", "distributor_id": "CEE"},
        {"account_id": "A9", "account_name": "Harbour Lane", "distributor_id": "CEE"},
    ]
    result = match(dealers, accounts)
    assert result["matched"] == [
        {"dealer_id": "D1", "account_id": "A1", "name": "north yard motors"},
    ]
    assert result["ambiguous"] == []
    assert result["unmatched_dealers"] == [dealers[1]]
    assert result["unmatched_accounts"] == [accounts[1]]


def test_case_spacing_and_trailing_period() -> None:
    dealers = [
        {
            "dealer_id": "D1",
            "dealer_name": "  NORTH   yard motors.  ",
            "distributor_id": "BENELUX",
        }
    ]
    accounts = [
        {"account_id": "A1", "account_name": "north yard motors", "distributor_id": "BENELUX"},
    ]
    result = match(dealers, accounts)
    assert result["matched"] == [
        {"dealer_id": "D1", "account_id": "A1", "name": "north yard motors"},
    ]
    assert result["unmatched_dealers"] == []
    assert result["unmatched_accounts"] == []


def test_normalize_keeps_inner_punctuation_and_only_one_trailing_period() -> None:
    assert normalize_name("  H.Q.  Commercials. ") == "h.q. commercials"
    assert normalize_name("North Yard..") == "north yard."
    assert normalize_name("Straße Yard") == "strasse yard"
    assert normalize_name("STRASSE YARD") == "strasse yard"


def test_partial_name_is_not_a_match() -> None:
    dealers = [{"dealer_id": "D1", "dealer_name": "Harbour", "distributor_id": "NORD"}]
    accounts = [{"account_id": "A1", "account_name": "Harbour Lane", "distributor_id": "NORD"}]
    result = match(dealers, accounts)
    assert result["matched"] == []
    assert result["ambiguous"] == []
    assert result["unmatched_dealers"] == dealers
    assert result["unmatched_accounts"] == accounts


def test_uti_dealer_does_not_match_umi_account_with_the_same_name() -> None:
    dealers = [
        {"dealer_id": "D-UTI", "dealer_name": "Cedar Workshop", "distributor_id": "UTI"},
    ]
    accounts = [
        {"account_id": "A-UMI", "account_name": "Cedar Workshop", "distributor_id": "UMI"},
    ]
    result = match(dealers, accounts)
    assert result["matched"] == []
    assert result["ambiguous"] == []
    assert result["unmatched_dealers"] == dealers
    assert result["unmatched_accounts"] == accounts


def test_iuk_dealer_does_not_match_ituk_account_with_the_same_name() -> None:
    dealers = [
        {"dealer_id": "D-IUK", "dealer_name": "Kings Meadow Trucks", "distributor_id": "IUK"},
    ]
    accounts = [
        {
            "account_id": "A-ITUK",
            "account_name": "Kings Meadow Trucks",
            "distributor_id": "ITUK",
        },
    ]
    result = match(dealers, accounts)
    assert result["matched"] == []
    assert result["ambiguous"] == []
    assert result["unmatched_dealers"] == dealers
    assert result["unmatched_accounts"] == accounts


def test_ambiguous_twin_accounts_are_not_picked() -> None:
    dealers = [
        {"dealer_id": "D1", "dealer_name": "Riverside Commercials", "distributor_id": "PORT"},
    ]
    accounts = [
        {"account_id": "A1", "account_name": "Riverside Commercials", "distributor_id": "PORT"},
        {
            "account_id": "A2",
            "account_name": "riverside   commercials.",
            "distributor_id": "PORT",
        },
        {"account_id": "A3", "account_name": "Hilltop Vans", "distributor_id": "PORT"},
    ]
    result = match(dealers, accounts)
    assert result["matched"] == []
    assert result["ambiguous"] == [
        {
            "dealer_id": "D1",
            "account_ids": ["A1", "A2"],
            "name": "riverside commercials",
        }
    ]
    assert result["unmatched_dealers"] == []
    assert result["unmatched_accounts"] == [accounts[2]]


def test_twins_in_another_distributor_do_not_make_a_match_ambiguous() -> None:
    dealers = [
        {"dealer_id": "D-UTI", "dealer_name": "Cedar Workshop", "distributor_id": "UTI"},
    ]
    accounts = [
        {"account_id": "A-UTI", "account_name": "Cedar Workshop", "distributor_id": "UTI"},
        {"account_id": "A-UMI-1", "account_name": "Cedar Workshop", "distributor_id": "UMI"},
        {"account_id": "A-UMI-2", "account_name": "cedar workshop.", "distributor_id": "UMI"},
    ]
    result = match(dealers, accounts)
    assert result["matched"] == [
        {"dealer_id": "D-UTI", "account_id": "A-UTI", "name": "cedar workshop"},
    ]
    assert result["ambiguous"] == []
    assert [row["account_id"] for row in result["unmatched_accounts"]] == [
        "A-UMI-1",
        "A-UMI-2",
    ]


def test_two_dealers_can_share_one_account() -> None:
    dealers = [
        {"dealer_id": "D1", "dealer_name": "North Yard Motors", "distributor_id": "CEE"},
        {"dealer_id": "D2", "dealer_name": "north yard motors", "distributor_id": "CEE"},
    ]
    accounts = [
        {"account_id": "A1", "account_name": "North Yard Motors", "distributor_id": "CEE"},
    ]
    result = match(dealers, accounts)
    assert result["matched"] == [
        {"dealer_id": "D1", "account_id": "A1", "name": "north yard motors"},
        {"dealer_id": "D2", "account_id": "A1", "name": "north yard motors"},
    ]
    assert result["ambiguous"] == []
    assert result["unmatched_accounts"] == []


def test_confirm_returns_only_the_decided_pairs() -> None:
    dealers = [
        {"dealer_id": "D1", "dealer_name": "North Yard Motors", "distributor_id": "CEE"},
        {"dealer_id": "D2", "dealer_name": "Riverside Commercials", "distributor_id": "CEE"},
    ]
    accounts = [
        {"account_id": "A1", "account_name": "North Yard Motors", "distributor_id": "CEE"},
        {"account_id": "A2", "account_name": "Riverside Commercials", "distributor_id": "CEE"},
        {"account_id": "A3", "account_name": "riverside commercials", "distributor_id": "CEE"},
    ]
    result = match(dealers, accounts)
    confirmed = confirm(
        result,
        [
            {"dealer_id": "D1", "account_id": "A1"},
            {"dealer_id": "D2", "account_id": "A3"},
        ],
    )
    assert confirmed == [
        {"dealer_id": "D1", "account_id": "A1", "name": "north yard motors"},
        {"dealer_id": "D2", "account_id": "A3", "name": "riverside commercials"},
    ]
    assert result["matched"] == [
        {"dealer_id": "D1", "account_id": "A1", "name": "north yard motors"},
    ]
    assert result["ambiguous"][0]["account_ids"] == ["A2", "A3"]


def test_confirm_omits_a_matched_pair_that_was_not_decided() -> None:
    result = match(
        [
            {"dealer_id": "D1", "dealer_name": "North Yard Motors", "distributor_id": "CEE"},
            {"dealer_id": "D2", "dealer_name": "Hilltop Vans", "distributor_id": "CEE"},
        ],
        [
            {"account_id": "A1", "account_name": "North Yard Motors", "distributor_id": "CEE"},
            {"account_id": "A2", "account_name": "Hilltop Vans", "distributor_id": "CEE"},
        ],
    )
    confirmed = confirm(result, [{"dealer_id": "D2", "account_id": "A2"}])
    assert confirmed == [
        {"dealer_id": "D2", "account_id": "A2", "name": "hilltop vans"},
    ]


def test_confirm_refuses_an_invented_pair() -> None:
    result = match(
        [{"dealer_id": "D1", "dealer_name": "North Yard Motors", "distributor_id": "CEE"}],
        [{"account_id": "A1", "account_name": "North Yard Motors", "distributor_id": "CEE"}],
    )
    with pytest.raises(ValueError, match="refused"):
        confirm(
            result,
            [
                {"dealer_id": "D1", "account_id": "A1"},
                {"dealer_id": "D-made-up", "account_id": "A-made-up"},
            ],
        )


def test_confirm_refuses_a_cross_distributor_pair() -> None:
    result = match(
        [{"dealer_id": "D-UTI", "dealer_name": "Cedar Workshop", "distributor_id": "UTI"}],
        [{"account_id": "A-UMI", "account_name": "Cedar Workshop", "distributor_id": "UMI"}],
    )
    with pytest.raises(ValueError, match="refused"):
        confirm(result, [{"dealer_id": "D-UTI", "account_id": "A-UMI"}])


def test_confirm_refuses_an_account_that_is_not_a_candidate() -> None:
    result = match(
        [{"dealer_id": "D1", "dealer_name": "Riverside Commercials", "distributor_id": "PORT"}],
        [
            {"account_id": "A1", "account_name": "Riverside Commercials", "distributor_id": "PORT"},
            {"account_id": "A2", "account_name": "Riverside Commercials", "distributor_id": "PORT"},
            {"account_id": "A3", "account_name": "Hilltop Vans", "distributor_id": "PORT"},
        ],
    )
    with pytest.raises(ValueError, match="refused"):
        confirm(result, [{"dealer_id": "D1", "account_id": "A3"}])
