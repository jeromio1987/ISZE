"""Partner intake phase 0. Rule ids and severities are taken from the internal
film (film_a.js, 9 October 2026). A rule is "stated" only when that film or the
Plan B white paper gives the words. Unstated rules keep their severity and do
not fire.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str  # E, W, I, EW, IE
    label: str
    stated: bool
    text: str


# Index in the film is id-1. SEV and VNAME are copied from film_a.js.
RULES: tuple[Rule, ...] = (
    Rule("V001", "E", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule("V002", "E", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule(
        "V003",
        "E",
        "no prices",
        True,
        "A price column is rejected. The column is not stripped. The receipt says to remove it and resend as the next version.",
    ),
    Rule(
        "V004",
        "E",
        "month",
        True,
        "Reporting period is YYYY-MM. One period per file.",
    ),
    Rule(
        "V005",
        "EW",
        "part numbers",
        True,
        "Part number is text, leading zeros kept. A blank part number stops the file. A part number with no catalogue match is a warning, because no classification file is declared the authority yet.",
    ),
    Rule("V006", "E", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule("V007", "E", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule(
        "V008",
        "EW",
        "dealer list",
        True,
        "Dealer identifier is required on each line. For the first two quarters of the programme it is a warning. From the third quarter it stops the file.",
    ),
    Rule("V009", "E", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule(
        "V010",
        "E",
        "control record",
        True,
        "The file carries a coverage declaration: dealer sites included, known exclusions, date range, and whether returns are included.",
    ),
    Rule(
        "V011",
        "I",
        "on time?",
        True,
        "On time means within ten working days after month-end, Monday to Friday, no holiday calendar. Late is information. It does not stop the file.",
    ),
    Rule(
        "V012",
        "W",
        "volume jump",
        True,
        "A jump against the previous accepted month is a warning. No threshold is set, so the check records that and does not invent one.",
    ),
    Rule("V013", "W", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule("V014", "IE", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule("V015", "W", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule(
        "V016",
        "E",
        "right distributor",
        True,
        "The distributor id inside the file matches the drop folder the file arrived in.",
    ),
    Rule("V017", "W", "", False, "Severity only. The rule text is not in the local film or the Plan B paper."),
    Rule(
        "V018",
        "E",
        "hidden price",
        True,
        "A currency symbol in a cell, or a header that means price, cost, margin or a currency, stops the file even when the column is not named price.",
    ),
)

RULE_BY_ID = {r.id: r for r in RULES}

# Programme start is 1 April 2027 (FY2028). Dealer detail is a target in the
# first two quarters and a condition from the third (Plan B paper).
PROGRAMME_START = (2027, 4)  # year, month
DEALER_DETAIL_CONDITION_FROM = (2027, 10)  # FY2028 Q3

PRICE_HEADERS = {
    "price",
    "prices",
    "unit_price",
    "unitprice",
    "net_price",
    "list_price",
    "cost",
    "costs",
    "margin",
    "margins",
    "gm",
    "discount",
    "euro",
    "eur",
    "gbp",
    "usd",
    "amount",
    "value",
}

# Headers the standard asks for. Prices are refused, not stored.
REQUIRED_LINE_FIELDS = (
    "distributor_id",
    "dealer_id",
    "part_number",
    "quantity",
    "period",
)
OPTIONAL_LINE_FIELDS = (
    "site_id",
    "transaction_date",
    "transaction_type",
    "line_id",
    "file_version",
)
DECLARATION_FIELDS = (
    "sites_included",
    "known_exclusions",
    "date_from",
    "date_to",
    "returns_included",
)

# Asked never. Presence of these headers is V003 or V018.
FORBIDDEN_HEADERS = {
    "price",
    "prices",
    "unit_price",
    "net_price",
    "list_price",
    "cost",
    "margin",
    "customer_name",
    "customer",
    "chassis",
    "chassis_number",
    "vin",
    "workshop_order",
    "dealer_stock",
    "stock_qty",
}


def stops_file(severity: str, period: str | None) -> bool:
    """True when this severity refuses the file for that reporting period."""
    if severity == "E":
        return True
    if severity in {"W", "I"}:
        return False
    if severity == "IE":
        # Error half is unstated. Do not stop the file on an unstated rule.
        return False
    if severity == "EW":
        return _dealer_detail_is_condition(period)
    return False


def _dealer_detail_is_condition(period: str | None) -> bool:
    if not period or len(period) < 7:
        return False
    year_s, month_s = period.split("-", 1)
    try:
        year, month = int(year_s), int(month_s)
    except ValueError:
        return False
    cy, cm = DEALER_DETAIL_CONDITION_FROM
    return (year, month) >= (cy, cm)
