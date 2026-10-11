"""Pair a dealer name with an account name inside one distributor.

Match is exact after normalize_name. There is no fuzzy score and no phonetic
match. A partial name is a different name. UTI and UMI are different
distributor ids, and so are IUK and ITUK: the same spelling in two
distributors is two identities.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TypedDict


class DealerRow(TypedDict):
    dealer_id: str
    dealer_name: str
    distributor_id: str


class AccountRow(TypedDict):
    account_id: str
    account_name: str
    distributor_id: str


class MatchedPair(TypedDict):
    dealer_id: str
    account_id: str
    name: str


class AmbiguousDealer(TypedDict):
    dealer_id: str
    account_ids: list[str]
    name: str


class MatchResult(TypedDict):
    matched: list[MatchedPair]
    ambiguous: list[AmbiguousDealer]
    unmatched_dealers: list[DealerRow]
    unmatched_accounts: list[AccountRow]


class Decision(TypedDict):
    dealer_id: str
    account_id: str


def normalize_name(name: str) -> str:
    """Strip, casefold, collapse internal whitespace, drop one trailing period.

    Nothing else. Inner punctuation stays. A second trailing period stays.
    """
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    text = name.strip().casefold()
    text = " ".join(text.split())
    if text.endswith("."):
        text = text[:-1]
    return text


def match(dealer_rows: list[DealerRow], account_rows: list[AccountRow]) -> MatchResult:
    """Pair dealers to accounts that share a distributor id and a normalized name.

    Two accounts that normalize to the same name inside one distributor are not
    a match. The dealer goes to ambiguous with those account ids. This function
    does not choose one of them.
    """
    accounts_by_name: dict[str, dict[str, list[AccountRow]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for account in account_rows:
        key = normalize_name(account["account_name"])
        accounts_by_name[account["distributor_id"]][key].append(account)

    matched: list[MatchedPair] = []
    ambiguous: list[AmbiguousDealer] = []
    unmatched_dealers: list[DealerRow] = []
    held_accounts: set[tuple[str, str]] = set()

    for dealer in dealer_rows:
        distributor_id = dealer["distributor_id"]
        key = normalize_name(dealer["dealer_name"])
        candidates = accounts_by_name.get(distributor_id, {}).get(key, [])
        if len(candidates) == 1:
            account = candidates[0]
            matched.append(
                {
                    "dealer_id": dealer["dealer_id"],
                    "account_id": account["account_id"],
                    "name": key,
                }
            )
            held_accounts.add((distributor_id, account["account_id"]))
        elif len(candidates) > 1:
            account_ids = [account["account_id"] for account in candidates]
            ambiguous.append(
                {
                    "dealer_id": dealer["dealer_id"],
                    "account_ids": account_ids,
                    "name": key,
                }
            )
            for account_id in account_ids:
                held_accounts.add((distributor_id, account_id))
        else:
            unmatched_dealers.append(dict(dealer))

    unmatched_accounts = [
        dict(account)
        for account in account_rows
        if (account["distributor_id"], account["account_id"]) not in held_accounts
    ]
    return {
        "matched": matched,
        "ambiguous": ambiguous,
        "unmatched_dealers": unmatched_dealers,
        "unmatched_accounts": unmatched_accounts,
    }


def confirm(match_result: MatchResult, decisions: list[Decision]) -> list[MatchedPair]:
    """Return only the pairs in decisions.

    A pair is accepted when it is already in matched, or when that dealer is
    ambiguous and the account id is one of its candidates. Any other pair
    raises ValueError. Matched pairs that are not in decisions are left out.
    """
    allowed: dict[tuple[str, str], str] = {}
    for pair in match_result["matched"]:
        allowed[(pair["dealer_id"], pair["account_id"])] = pair["name"]
    for row in match_result["ambiguous"]:
        for account_id in row["account_ids"]:
            allowed[(row["dealer_id"], account_id)] = row["name"]

    confirmed: list[MatchedPair] = []
    for decision in decisions:
        dealer_id = decision["dealer_id"]
        account_id = decision["account_id"]
        name = allowed.get((dealer_id, account_id))
        if name is None:
            raise ValueError(
                f"refused pair dealer_id={dealer_id!r} account_id={account_id!r}: "
                "not in matched or ambiguous"
            )
        confirmed.append(
            {
                "dealer_id": dealer_id,
                "account_id": account_id,
                "name": name,
            }
        )
    return confirmed
