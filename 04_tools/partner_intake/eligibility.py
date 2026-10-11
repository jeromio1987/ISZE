"""Quarterly eligibility check for partner intake.

The caller passes the evidence. This module does not fetch files, does not
read billing, and does not post a credit or an invoice condition.

A fiscal year starts on 1 April. FY2028Q1 is April, May and June 2027.
"""

from __future__ import annotations

GATE_NAMES = (
    "sales to dealer on time",
    "quality",
    "dealer detail",
    "dealer list current",
    "monthly KPIs",
    "IDS assessed",
    "training done",
)

# Dealer detail is a target in FY2028Q1 and FY2028Q2. It is a condition from
# FY2028Q3 (October 2027) onward.
_DEALER_DETAIL_CONDITION_FROM = (2027, 10)

_NO_DEALER_LIST = "no dealer-list date"
_KPI_OPEN = "KPI file location is still open"
_IDS_OPEN = "no IDS round planned"
_TRAINING_OPEN = "training register owner is still open"

# A person may later turn a met condition into a credit. This check never does.
_DISCOUNT_CREDIT_PROPOSED = False


def evaluate(distributor_id: str, quarter: str, evidence: dict) -> dict:
    """Judge one distributor for one quarter.

    Each gate is yes, no, or n/a, with an evidence string. n/a does not fail
    the quarter. Dealer detail does not fail it while condition is false.
    """
    if not isinstance(evidence, dict):
        raise TypeError("evidence must be a dict")
    months = quarter_months(quarter)
    accepted = _period_set(evidence, "accepted_periods")
    late = _period_set(evidence, "late_periods")
    rejected = _period_set(evidence, "rejected_periods")
    detail = _period_set(evidence, "dealer_detail_periods")
    gates = [
        _on_time(months, accepted, late),
        _quality(months, accepted, rejected),
        _dealer_detail(months, detail),
        _dealer_list(months, evidence.get("dealer_list_as_of")),
        _open_bool(
            "monthly KPIs",
            evidence.get("kpi_received"),
            _KPI_OPEN,
            "monthly KPIs received",
            "monthly KPIs not received",
        ),
        _open_bool(
            "IDS assessed",
            evidence.get("ids_assessed"),
            _IDS_OPEN,
            "IDS assessed",
            "IDS not assessed",
        ),
        _open_bool(
            "training done",
            evidence.get("training_done"),
            _TRAINING_OPEN,
            "training done",
            "training not done",
        ),
    ]
    return {
        "distributor_id": distributor_id,
        "quarter": quarter.strip() if isinstance(quarter, str) else quarter,
        "months": months,
        "gates": gates,
        "universe_data_condition_met": _condition_met(gates),
        "discount_credit_proposed": _DISCOUNT_CREDIT_PROPOSED,
    }


def write_proposal(result: dict) -> str:
    """Plain-text proposal. It does not post, and it does not choose the instrument."""
    if result.get("discount_credit_proposed") is not False:
        raise ValueError(
            "discount_credit_proposed must stay false. This code does not propose a credit."
        )
    gates = result["gates"]
    if tuple(gate["name"] for gate in gates) != GATE_NAMES:
        raise ValueError("the seven gates must be present in order")
    lines = [
        f"Distributor: {result['distributor_id']}",
        f"Quarter: {result['quarter']}",
        "Months: " + ", ".join(result["months"]),
        "",
    ]
    for index, gate in enumerate(gates, start=1):
        answer = gate["answer"]
        if answer not in ("yes", "no", "n/a"):
            raise ValueError(f"bad answer for {gate['name']}")
        lines.append(f"{index}. {gate['name']}: {answer}")
        lines.append(f"Evidence: {gate['evidence']}")
        lines.append("")
    met = result["universe_data_condition_met"]
    if not isinstance(met, bool):
        raise TypeError("universe_data_condition_met must be true or false")
    lines.append("Universe data condition met: " + ("yes" if met else "no"))
    lines.append("Discount credit proposed: no")
    lines.append("A person could turn a met condition into a credit later.")
    lines.append("Credit note or invoice condition: not decided.")
    lines.append("This is a proposal. Nothing is posted.")
    text = "\n".join(lines)
    if "**" in text or "__" in text:
        raise RuntimeError("proposal must not use markdown bold")
    return text


def quarter_months(quarter: str) -> list[str]:
    """Three YYYY-MM months. FY2028Q1 is 2027-04, 2027-05, 2027-06."""
    if not isinstance(quarter, str):
        raise TypeError("quarter must be a string like FY2028Q1")
    text = quarter.strip()
    if len(text) != 8 or not text.startswith("FY") or text[6] != "Q":
        raise ValueError(f"quarter must look like FY2028Q1, got {quarter!r}")
    year_text, quarter_digit = text[2:6], text[7]
    if not year_text.isdigit() or quarter_digit not in "1234":
        raise ValueError(f"quarter must look like FY2028Q1, got {quarter!r}")
    fiscal_year = int(year_text)
    quarter_number = int(quarter_digit)
    if quarter_number == 1:
        year, month = fiscal_year - 1, 4
    elif quarter_number == 2:
        year, month = fiscal_year - 1, 7
    elif quarter_number == 3:
        year, month = fiscal_year - 1, 10
    else:
        year, month = fiscal_year, 1
    months = []
    for _ in range(3):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def _condition_met(gates: list[dict]) -> bool:
    """True only when every condition gate is yes.

    An n/a gate is ignored. Dealer detail is ignored while its condition is false.
    """
    for gate in gates:
        if gate["answer"] == "n/a":
            continue
        if not gate["condition"]:
            continue
        if gate["answer"] != "yes":
            return False
    return True


def _on_time(months: list[str], accepted: set[str], late: set[str]) -> dict:
    # Late is its own gate. Rejection is quality, not on time.
    missing = [month for month in months if month not in accepted]
    late_months = [month for month in months if month in late]
    if not missing and not late_months:
        return _gate(
            "sales to dealer on time",
            "yes",
            f"{', '.join(months)} accepted and not late",
            True,
        )
    parts = []
    if missing:
        parts.append(f"{', '.join(missing)} missing from accepted periods")
    if late_months:
        parts.append(f"{', '.join(late_months)} late")
    return _gate("sales to dealer on time", "no", "; ".join(parts), True)


def _quality(months: list[str], accepted: set[str], rejected: set[str]) -> dict:
    # A late month is not a quality failure.
    missing = [month for month in months if month not in accepted]
    rejected_months = [month for month in months if month in rejected]
    if not missing and not rejected_months:
        return _gate(
            "quality",
            "yes",
            f"{', '.join(months)} accepted and none rejected",
            True,
        )
    parts = []
    if missing:
        parts.append(f"{', '.join(missing)} not accepted")
    if rejected_months:
        parts.append(f"{', '.join(rejected_months)} rejected")
    return _gate("quality", "no", "; ".join(parts), True)


def _dealer_detail(months: list[str], present: set[str]) -> dict:
    missing = [month for month in months if month not in present]
    year, month = _split(months[0])
    condition = (year, month) >= _DEALER_DETAIL_CONDITION_FROM
    if not missing:
        text = f"dealer id present for {', '.join(months)}"
        answer = "yes"
    else:
        text = f"dealer id missing for {', '.join(missing)}"
        answer = "no"
    if not condition:
        text += ". Target, not a condition"
    return _gate("dealer detail", answer, text, condition)


def _dealer_list(months: list[str], as_of: object) -> dict:
    if as_of is None:
        return _gate("dealer list current", "no", _NO_DEALER_LIST, True)
    if not _is_period(as_of):
        return _gate("dealer list current", "no", "dealer list date is not a month", True)
    window = {_month_before(months[0]), *months}
    if as_of in window:
        return _gate(
            "dealer list current",
            "yes",
            f"dealer list dated {as_of}, inside the quarter or the month before",
            True,
        )
    return _gate(
        "dealer list current",
        "no",
        f"dealer list dated {as_of}, outside the quarter and the month before",
        True,
    )


def _open_bool(name: str, value: object, open_evidence: str, yes_text: str, no_text: str) -> dict:
    if value is None:
        return _gate(name, "n/a", open_evidence, True)
    if value is True:
        return _gate(name, "yes", yes_text, True)
    if value is False:
        return _gate(name, "no", no_text, True)
    return _gate(name, "no", f"{name} was not yes, no, or open", True)


def _gate(name: str, answer: str, evidence: str, condition: bool) -> dict:
    return {
        "name": name,
        "answer": answer,
        "evidence": evidence,
        "condition": condition,
    }


def _period_set(evidence: dict, key: str) -> set[str]:
    raw = evidence.get(key)
    if raw is None:
        return set()
    if isinstance(raw, (str, bytes)) or not isinstance(raw, (list, tuple, set)):
        raise TypeError(f"{key} must be a list of YYYY-MM")
    found = set()
    for item in raw:
        if not _is_period(item):
            raise ValueError(f"{key} has a value that is not YYYY-MM: {item!r}")
        found.add(item)
    return found


def _is_period(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 7 or value[4] != "-":
        return False
    year, month = value[:4], value[5:]
    if not (year.isdigit() and month.isdigit()):
        return False
    return 1 <= int(month) <= 12


def _split(period: str) -> tuple[int, int]:
    return int(period[:4]), int(period[5:7])


def _month_before(period: str) -> str:
    year, month = _split(period)
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"
