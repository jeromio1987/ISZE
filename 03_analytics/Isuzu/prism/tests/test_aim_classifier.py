"""Unit tests for aim_pn_classifier — synthetic data only."""

from __future__ import annotations

import pandas as pd
import pytest

from modules.aim_pn_classifier import (
    FILTER_SUBGROUPS,
    build_aim_pn_classification,
    filter_report_subgroup,
    infer_filter_part_role,
    pms_capture_eligible,
)
from modules.bvp_analytics import normalize_pn_value


def test_infer_filter_part_role_element_from_description() -> None:
    role = infer_filter_part_role(
        description="OIL FILTER ELEMENT",
        product_subgroup="oil_filter",
    )
    assert role == "element"


def test_infer_filter_part_role_assembly_from_description() -> None:
    role = infer_filter_part_role(
        description="FUEL FILTER ASM",
        product_subgroup="fuel_filter",
    )
    assert role == "assembly"


def test_infer_filter_part_role_kit_from_description() -> None:
    role = infer_filter_part_role(
        description="AIR FILTER KIT",
        product_subgroup="air_filter",
    )
    assert role == "kit"


def test_infer_filter_part_role_hose_filter_excluded() -> None:
    """HOSE + FILTER combination is explicitly excluded."""
    assert infer_filter_part_role(description="FUEL FILTER HOSE") is None


def test_infer_filter_part_role_fig_key_element() -> None:
    role = infer_filter_part_role(
        description="FILTER",
        fig_key="041-002",
        product_subgroup="oil_filter",
    )
    assert role == "element"


def test_infer_filter_part_role_fig_key_assembly() -> None:
    role = infer_filter_part_role(
        description="FILTER",
        fig_key="041-001",
        product_subgroup="oil_filter",
    )
    assert role == "assembly"


def test_infer_filter_part_role_non_filter_subgroup_returns_none() -> None:
    assert infer_filter_part_role(
        description="BRAKE PAD",
        product_subgroup="brake_pad",
    ) is None


def test_filter_report_subgroup_suffixes() -> None:
    assert filter_report_subgroup("oil_filter", "assembly") == "oil_filter_asm"
    assert filter_report_subgroup("oil_filter", "kit") == "oil_filter_kit"
    assert filter_report_subgroup("oil_filter", "element") == "oil_filter"
    assert filter_report_subgroup("brake_pad", "element") == "brake_pad"


def test_pms_capture_eligible_filter_roles() -> None:
    assert pms_capture_eligible("oil_filter", "element") is True
    assert pms_capture_eligible("oil_filter", "assembly") is False
    assert pms_capture_eligible("oil_filter", "assembly", from_registry=True) is True
    assert pms_capture_eligible("oil_filter", "kit") is False
    assert pms_capture_eligible("brake_pad", None) is True
    assert pms_capture_eligible(None, "element") is True


def test_normalize_pn_value_leading_zeros_and_spacing() -> None:
    assert normalize_pn_value(" 08983282071 ") == "8983282071"
    assert normalize_pn_value("8983282071") == "8983282071"
    assert normalize_pn_value(8983282071) == "8983282071"


def test_build_aim_pn_classification_pr00_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    pr00 = pd.DataFrame(
        {
            "_pn": ["8983282071", "1234567890"],
            "pn_norm": ["8983282071", "1234567890"],
            "family": ["Filters", "Other"],
            "group": ["Oil Filter", "Misc"],
            "level3_type": ["oil filter", "other"],
            "fig_key": ["041-002", None],
        }
    ).set_index("_pn", drop=False)

    monkeypatch.setattr("modules.aim_pn_classifier.resolve_aim_workbook", lambda: None)
    monkeypatch.setattr("modules.aim_pn_classifier.load_pr00_index", lambda: pr00)
    monkeypatch.setattr("modules.aim_pn_classifier.load_gap_suggestions", lambda: pd.DataFrame())

    result = build_aim_pn_classification(
        pd.Series(["8983282071", "1234567890", " 08983282071 "]),
        pd.Series(["OIL FILTER ELEMENT", "UNKNOWN WIDGET", "OIL FILTER ELEMENT"]),
    )
    assert len(result) == 3
    known = result.loc[result["part_number"] == "8983282071"].iloc[0]
    assert known["aim_l1"] == "Filters"
    assert known["aim_l2"] == "Oil Filter"
    assert known["aim_source"] == "pr00_catalog"
    assert known["filter_part_role"] == "element"
    unknown = result.loc[result["part_number"] == "1234567890"].iloc[0]
    assert unknown["aim_l1"] == "Other"
    assert unknown["aim_source"] == "pr00_catalog"


def test_build_aim_pn_classification_unmatched_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("modules.aim_pn_classifier.resolve_aim_workbook", lambda: None)
    monkeypatch.setattr("modules.aim_pn_classifier.load_pr00_index", lambda: pd.DataFrame())
    monkeypatch.setattr("modules.aim_pn_classifier.load_gap_suggestions", lambda: pd.DataFrame())

    result = build_aim_pn_classification(
        pd.Series(["9999999999"]),
        pd.Series(["MYSTERY PART"]),
    )
    row = result.iloc[0]
    assert row["part_number"] == "9999999999"
    assert row["aim_l1"] is None
    assert row["aim_source"] is None
    assert row["filter_part_role"] is None


def test_build_aim_pn_classification_gap_suggestion_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    gap = pd.DataFrame(
        {
            "_pn": ["5555555555"],
            "pn": ["5555555555"],
            "sug1_l1": ["Wear Parts"],
            "sug1_l2": ["Brake"],
            "confidence": [4.0],
        }
    ).set_index("_pn", drop=False)

    monkeypatch.setattr("modules.aim_pn_classifier.resolve_aim_workbook", lambda: None)
    monkeypatch.setattr("modules.aim_pn_classifier.load_pr00_index", lambda: pd.DataFrame())
    monkeypatch.setattr("modules.aim_pn_classifier.load_gap_suggestions", lambda: gap)

    result = build_aim_pn_classification(
        pd.Series(["5555555555"]),
        pd.Series(["BRAKE PAD SET"]),
    )
    row = result.iloc[0]
    assert row["aim_l1"] == "Wear Parts"
    assert row["aim_l2"] == "Brake"
    assert row["aim_source"] == "gap_suggestion"


def test_build_aim_pn_classification_output_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("modules.aim_pn_classifier.resolve_aim_workbook", lambda: None)
    monkeypatch.setattr("modules.aim_pn_classifier.load_pr00_index", lambda: pd.DataFrame())
    monkeypatch.setattr("modules.aim_pn_classifier.load_gap_suggestions", lambda: pd.DataFrame())

    result = build_aim_pn_classification(pd.Series(["1111111111"]), pd.Series([""]))
    expected = {
        "part_number", "description_norm", "aim_l1", "aim_l2", "aim_l3",
        "catalog_l1", "catalog_l2", "catalog_l3", "fig_key",
        "filter_part_role", "aim_source",
    }
    assert expected.issubset(set(result.columns))


def test_filter_subgroups_frozen_set() -> None:
    assert "oil_filter" in FILTER_SUBGROUPS
    assert "urea_filter" in FILTER_SUBGROUPS
