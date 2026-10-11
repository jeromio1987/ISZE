"""Made-up periods for distributor id DEMO. Not a real distributor result."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[1] / "eligibility.py"
_spec = importlib.util.spec_from_file_location("partner_intake_eligibility", _PATH)
eligibility = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eligibility)

evaluate = eligibility.evaluate
write_proposal = eligibility.write_proposal

_Q1 = ["2027-04", "2027-05", "2027-06"]


def _base(months, **overrides):
    evidence = {
        "accepted_periods": list(months),
        "late_periods": [],
        "rejected_periods": [],
        "dealer_detail_periods": list(months),
        "dealer_list_as_of": months[0],
        "kpi_received": True,
        "ids_assessed": True,
        "training_done": True,
    }
    evidence.update(overrides)
    return evidence


def _by_name(result, name):
    for gate in result["gates"]:
        if gate["name"] == name:
            return gate
    raise AssertionError(name)


def _assert_shape(result):
    assert result["distributor_id"] == "DEMO"
    assert [gate["name"] for gate in result["gates"]] == [
        "sales to dealer on time",
        "quality",
        "dealer detail",
        "dealer list current",
        "monthly KPIs",
        "IDS assessed",
        "training done",
    ]
    for gate in result["gates"]:
        assert gate["answer"] in ("yes", "no", "n/a")
        assert isinstance(gate["evidence"], str) and gate["evidence"]
        assert isinstance(gate["condition"], bool)
    assert result["discount_credit_proposed"] is False
    assert isinstance(result["universe_data_condition_met"], bool)


def test_fiscal_year_starts_in_april_not_january():
    first = evaluate("DEMO", "FY2026Q1", {})
    assert first["months"] == ["2025-04", "2025-05", "2025-06"]
    last = evaluate("DEMO", "FY2026Q4", {})
    assert last["months"] == ["2026-01", "2026-02", "2026-03"]
    opening = evaluate("DEMO", "FY2028Q1", {})
    assert opening["months"] == ["2027-04", "2027-05", "2027-06"]


def test_bad_quarter_raises():
    for bad in ("2028Q1", "FY2028Q5", "FY28Q1", "FY2028", "", "fy2028q1"):
        with pytest.raises(ValueError):
            evaluate("DEMO", bad, {})


def test_empty_evidence_records_gaps_and_leaves_open_gates():
    result = evaluate("DEMO", "FY2028Q1", {})
    _assert_shape(result)
    assert _by_name(result, "sales to dealer on time")["answer"] == "no"
    assert _by_name(result, "quality")["answer"] == "no"
    detail = _by_name(result, "dealer detail")
    assert detail["answer"] == "no"
    assert detail["condition"] is False
    dealer_list = _by_name(result, "dealer list current")
    assert dealer_list["answer"] == "no"
    assert dealer_list["evidence"] == "no dealer-list date"
    assert _by_name(result, "monthly KPIs")["answer"] == "n/a"
    assert _by_name(result, "monthly KPIs")["evidence"] == "KPI file location is still open"
    assert _by_name(result, "IDS assessed")["answer"] == "n/a"
    assert _by_name(result, "IDS assessed")["evidence"] == "no IDS round planned"
    assert _by_name(result, "training done")["answer"] == "n/a"
    assert _by_name(result, "training done")["evidence"] == "training register owner is still open"
    assert result["universe_data_condition_met"] is False


def test_on_time_requires_every_month_accepted_and_not_late():
    clean = evaluate("DEMO", "FY2028Q1", _base(_Q1))
    assert _by_name(clean, "sales to dealer on time")["answer"] == "yes"

    late = evaluate("DEMO", "FY2028Q1", _base(_Q1, late_periods=["2027-05"]))
    late_gate = _by_name(late, "sales to dealer on time")
    assert late_gate["answer"] == "no"
    assert "2027-05 late" in late_gate["evidence"]
    assert _by_name(late, "quality")["answer"] == "yes"
    assert late["universe_data_condition_met"] is False
    assert late["discount_credit_proposed"] is False

    missing = evaluate(
        "DEMO",
        "FY2028Q1",
        _base(_Q1, accepted_periods=["2027-04", "2027-06"]),
    )
    assert _by_name(missing, "sales to dealer on time")["answer"] == "no"
    assert _by_name(missing, "quality")["answer"] == "no"
    assert "2027-05 missing from accepted periods" in _by_name(missing, "sales to dealer on time")["evidence"]
    assert "2027-05 not accepted" in _by_name(missing, "quality")["evidence"]


def test_rejected_fails_quality_and_does_not_by_itself_fail_on_time():
    result = evaluate("DEMO", "FY2028Q1", _base(_Q1, rejected_periods=["2027-05"]))
    _assert_shape(result)
    assert _by_name(result, "sales to dealer on time")["answer"] == "yes"
    quality = _by_name(result, "quality")
    assert quality["answer"] == "no"
    assert "2027-05 rejected" in quality["evidence"]
    assert result["universe_data_condition_met"] is False


def test_periods_outside_the_quarter_do_not_count():
    result = evaluate(
        "DEMO",
        "FY2028Q1",
        _base(
            _Q1,
            late_periods=["2027-03", "2027-07"],
            rejected_periods=["2026-12"],
        ),
    )
    assert _by_name(result, "sales to dealer on time")["answer"] == "yes"
    assert _by_name(result, "quality")["answer"] == "yes"
    assert result["universe_data_condition_met"] is True


def test_a_bad_period_string_is_not_silently_dropped():
    with pytest.raises(ValueError):
        evaluate("DEMO", "FY2028Q1", {"accepted_periods": ["April 2027"]})


def test_evidence_dict_is_not_mutated():
    evidence = _base(_Q1)
    snapshot = {key: (list(value) if isinstance(value, list) else value) for key, value in evidence.items()}
    evaluate("DEMO", "FY2028Q1", evidence)
    assert evidence == snapshot


def test_dealer_detail_condition_switches_at_fy2028q3():
    cases = [
        ("FY2028Q1", ["2027-04", "2027-05", "2027-06"], False),
        ("FY2028Q2", ["2027-07", "2027-08", "2027-09"], False),
        ("FY2028Q3", ["2027-10", "2027-11", "2027-12"], True),
        ("FY2028Q4", ["2028-01", "2028-02", "2028-03"], True),
        ("FY2029Q1", ["2028-04", "2028-05", "2028-06"], True),
    ]
    for quarter, months, condition in cases:
        result = evaluate("DEMO", quarter, _base(months, dealer_detail_periods=[]))
        _assert_shape(result)
        gate = _by_name(result, "dealer detail")
        assert result["months"] == months
        assert gate["answer"] == "no"
        assert gate["condition"] is condition
        if condition:
            assert "Target, not a condition" not in gate["evidence"]
            assert result["universe_data_condition_met"] is False
        else:
            assert gate["evidence"].endswith("Target, not a condition")
            assert result["universe_data_condition_met"] is True
        assert result["discount_credit_proposed"] is False


def test_dealer_detail_yes_when_every_month_has_a_dealer_id():
    early = evaluate("DEMO", "FY2028Q1", _base(_Q1))
    early_gate = _by_name(early, "dealer detail")
    assert early_gate["answer"] == "yes"
    assert early_gate["condition"] is False
    assert early["universe_data_condition_met"] is True

    later_months = ["2027-10", "2027-11", "2027-12"]
    later = evaluate("DEMO", "FY2028Q3", _base(later_months))
    later_gate = _by_name(later, "dealer detail")
    assert later_gate["answer"] == "yes"
    assert later_gate["condition"] is True
    assert later["universe_data_condition_met"] is True
    assert later["discount_credit_proposed"] is False


def test_dealer_detail_does_not_inherit_lateness_or_rejection():
    result = evaluate(
        "DEMO",
        "FY2028Q3",
        _base(
            ["2027-10", "2027-11", "2027-12"],
            late_periods=["2027-10"],
            rejected_periods=["2027-11"],
        ),
    )
    assert _by_name(result, "dealer detail")["answer"] == "yes"
    assert _by_name(result, "sales to dealer on time")["answer"] == "no"
    assert _by_name(result, "quality")["answer"] == "no"


def test_dealer_list_is_current_only_inside_the_quarter_or_the_month_before():
    for as_of in ("2027-03", "2027-04", "2027-05", "2027-06"):
        result = evaluate("DEMO", "FY2028Q1", _base(_Q1, dealer_list_as_of=as_of))
        gate = _by_name(result, "dealer list current")
        assert gate["answer"] == "yes", as_of
        assert as_of in gate["evidence"]

    for as_of in ("2027-02", "2027-07", "2026-03"):
        result = evaluate("DEMO", "FY2028Q1", _base(_Q1, dealer_list_as_of=as_of))
        gate = _by_name(result, "dealer list current")
        assert gate["answer"] == "no", as_of
        assert "outside the quarter and the month before" in gate["evidence"]

    missing = evaluate("DEMO", "FY2028Q1", _base(_Q1, dealer_list_as_of=None))
    missing_gate = _by_name(missing, "dealer list current")
    assert missing_gate["answer"] == "no"
    assert missing_gate["evidence"] == "no dealer-list date"
    assert missing["universe_data_condition_met"] is False


def test_dealer_list_month_before_crosses_the_calendar_year():
    months = ["2028-01", "2028-02", "2028-03"]
    inside = evaluate("DEMO", "FY2028Q4", _base(months, dealer_list_as_of="2027-12"))
    assert _by_name(inside, "dealer list current")["answer"] == "yes"
    outside = evaluate("DEMO", "FY2028Q4", _base(months, dealer_list_as_of="2027-11"))
    assert _by_name(outside, "dealer list current")["answer"] == "no"


def test_open_gates_are_not_applicable_and_do_not_fail():
    result = evaluate(
        "DEMO",
        "FY2028Q1",
        _base(_Q1, kpi_received=None, ids_assessed=None, training_done=None),
    )
    _assert_shape(result)
    assert _by_name(result, "monthly KPIs")["answer"] == "n/a"
    assert _by_name(result, "monthly KPIs")["evidence"] == "KPI file location is still open"
    assert _by_name(result, "IDS assessed")["answer"] == "n/a"
    assert _by_name(result, "training done")["evidence"] == "training register owner is still open"
    assert result["universe_data_condition_met"] is True
    assert result["discount_credit_proposed"] is False


def test_a_false_open_gate_is_a_no_and_fails_the_quarter():
    for key, gate_name in (
        ("kpi_received", "monthly KPIs"),
        ("ids_assessed", "IDS assessed"),
        ("training_done", "training done"),
    ):
        result = evaluate("DEMO", "FY2028Q1", _base(_Q1, **{key: False}))
        assert _by_name(result, gate_name)["answer"] == "no"
        assert _by_name(result, gate_name)["answer"] != "n/a"
        assert result["universe_data_condition_met"] is False
        assert result["discount_credit_proposed"] is False


def test_met_condition_still_does_not_propose_a_credit():
    months = ["2027-10", "2027-11", "2027-12"]
    result = evaluate("DEMO", "FY2028Q3", _base(months, dealer_list_as_of="2027-09"))
    _assert_shape(result)
    assert all(gate["answer"] == "yes" for gate in result["gates"])
    assert all(gate["condition"] is True for gate in result["gates"])
    assert result["universe_data_condition_met"] is True
    assert result["discount_credit_proposed"] is False
    text = write_proposal(result)
    assert result["discount_credit_proposed"] is False
    assert "Discount credit proposed: no" in text
    assert "A person could turn a met condition into a credit later." in text
    assert "Universe data condition met: yes" in text


def test_proposal_states_each_answer_and_posts_nothing():
    result = evaluate(
        "DEMO",
        "FY2028Q1",
        _base(
            _Q1,
            late_periods=["2027-06"],
            dealer_detail_periods=[],
            dealer_list_as_of=None,
            kpi_received=None,
            ids_assessed=None,
            training_done=None,
        ),
    )
    text = write_proposal(result)
    for gate in result["gates"]:
        assert f"{gate['name']}: {gate['answer']}" in text
        assert gate["evidence"] in text
    assert "sales to dealer on time: no" in text
    assert "quality: yes" in text
    assert "dealer detail: no" in text
    assert "monthly KPIs: n/a" in text
    assert "monthly KPIs: no" not in text
    assert "KPI file location is still open" in text
    assert "training register owner is still open" in text
    assert "no dealer-list date" in text
    assert "Credit note or invoice condition: not decided." in text
    assert "A person could turn a met condition into a credit later." in text
    assert text.splitlines()[-1] == "This is a proposal. Nothing is posted."
    assert "**" not in text
    assert "__" not in text
    assert "DEMO" in text
    assert result["discount_credit_proposed"] is False


def test_proposal_does_not_choose_credit_note_or_invoice():
    result = evaluate("DEMO", "FY2028Q1", _base(_Q1, kpi_received=None))
    text = write_proposal(result).lower()
    assert "credit note or invoice condition: not decided." in text
    for phrase in (
        "issue a credit note",
        "raise a credit note",
        "post a credit",
        "invoice condition applies",
        "choose a credit note",
        "choose an invoice",
        "credit note rather",
        "invoice condition rather",
    ):
        assert phrase not in text


def test_module_imports_nothing_but_future():
    tree = ast.parse(_PATH.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module)
    assert modules == ["__future__"]
