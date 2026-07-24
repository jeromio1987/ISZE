"""Unit tests for pms_engine — synthetic data only."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from modules.pms_engine import (
    CATEGORY_LABELS,
    DEFAULT_PARC_CONFIG,
    classify_pms_sales,
    expected_addressable_services,
    filter_pms_by_scope,
    get_dealer_capture_detail,
    get_pms_summary_by_distributor,
    get_seasonal_weights,
    parc_config_for_distributor,
    pms_models_for_scope,
    pms_scope_for_distributor,
    split_genuine_vs_bvp,
)


# Registry PNs (imported module constant — not externalized)
PN_GENUINE_OIL = "8983282071"       # N75_4HK1 oil_filter genuine
PN_BVP_OIL = "1876102890"           # N75_4HK1 oil_filter bvp
PN_MULTI_OIL = "8975439050"         # N75_4JZ1 + N35_4JZ1 oil_filter
PN_GENUINE_BRAKE = "8982447940"     # N75 brake_pad genuine (multi-model)
PN_NON_PMS = "1234567890"           # not in registry


@pytest.fixture
def df_sales() -> pd.DataFrame:
    """Synthetic PMS + non-PMS rows across ITUK/IUK and two years."""
    return pd.DataFrame(
        [
            # ITUK — N75 genuine oil filter
            {"distributor_code": "ITUK", "year": 2025, "part_number": PN_GENUINE_OIL,
             "description": "OIL FILTER ELEMENT", "billed_qty": 10, "net_sales_value": 500.0},
            # ITUK — N75 BVP oil filter
            {"distributor_code": "ITUK", "year": 2025, "part_number": PN_BVP_OIL,
             "description": "BVP OIL FILTER", "billed_qty": 5, "net_sales_value": 200.0},
            # ITUK — multi-model PN (leading-zero form)
            {"distributor_code": "ITUK", "year": 2025, "part_number": f"0{PN_MULTI_OIL}",
             "description": "OIL FILTER SHARED", "billed_qty": 3, "net_sales_value": 150.0},
            # ITUK — non-PMS part
            {"distributor_code": "ITUK", "year": 2025, "part_number": PN_NON_PMS,
             "description": "RANDOM BOLT", "billed_qty": 20, "net_sales_value": 80.0},
            # IUK — LCV-scope distributor (N35 RZ4E oil filter — single-model PN)
            {"distributor_code": "IUK", "year": 2025, "part_number": "8983214130",
             "description": "LCV AIR FILTER", "billed_qty": 8, "net_sales_value": 320.0},
            # ITUK — prior year baseline
            {"distributor_code": "ITUK", "year": 2024, "part_number": PN_GENUINE_OIL,
             "description": "OIL FILTER ELEMENT", "billed_qty": 6, "net_sales_value": 300.0},
            # ITUK — brake pad (wear category)
            {"distributor_code": "ITUK", "year": 2025, "part_number": PN_GENUINE_BRAKE,
             "description": "BRAKE PAD FRONT", "billed_qty": 4, "net_sales_value": 400.0},
            # FR01 — second distributor for summary aggregation
            {"distributor_code": "FR01", "year": 2025, "part_number": PN_GENUINE_OIL,
             "description": "OIL FILTER ELEMENT", "billed_qty": 2, "net_sales_value": 100.0},
        ]
    )


def test_classify_pms_sales_genuine_and_bvp(df_sales: pd.DataFrame) -> None:
    result = classify_pms_sales(df_sales)
    genuine = result.loc[result["part_number"] == PN_GENUINE_OIL].iloc[0]
    bvp = result.loc[result["part_number"] == PN_BVP_OIL].iloc[0]
    assert bool(genuine["is_pms"]) is True
    assert genuine["pms_category"] == "oil_filter"
    assert genuine["pms_model"] == "N75_4HK1"
    assert genuine["pms_type"] == "genuine"
    assert bool(bvp["is_pms"]) is True
    assert bvp["pms_type"] == "bvp"


def test_classify_pms_sales_multi_model_and_leading_zeros(df_sales: pd.DataFrame) -> None:
    result = classify_pms_sales(df_sales)
    multi = result.loc[result["part_number"].str.endswith(PN_MULTI_OIL)].iloc[0]
    assert multi["pms_model"] == "multi"
    assert multi["pms_category"] == "oil_filter"
    non_pms = result.loc[result["part_number"] == PN_NON_PMS].iloc[0]
    assert bool(non_pms["is_pms"]) is False
    assert pd.isna(non_pms["pms_category"])


def test_classify_pms_sales_output_columns(df_sales: pd.DataFrame) -> None:
    result = classify_pms_sales(df_sales)
    for col in ("is_pms", "pms_category", "pms_model", "pms_type"):
        assert col in result.columns
    assert len(result) == len(df_sales)


def test_pms_scope_for_distributor_n75_and_lcv() -> None:
    assert pms_scope_for_distributor("ITUK") == "N75_only"
    assert pms_scope_for_distributor("UTI") == "N75_only"
    assert pms_scope_for_distributor("IUK") == "LCV_only"
    assert pms_scope_for_distributor("UMI") == "LCV_only"
    assert pms_scope_for_distributor("FR01") == DEFAULT_PARC_CONFIG["scope"]


def test_filter_pms_by_scope_n75_excludes_n35(df_sales: pd.DataFrame) -> None:
    classified = classify_pms_sales(df_sales)
    pms_only = classified[classified["is_pms"]]
    n75 = filter_pms_by_scope(pms_only, "N75_only")
    lcv = filter_pms_by_scope(pms_only, "LCV_only")
    n75_models = set(n75["pms_model"])
    lcv_models = set(lcv["pms_model"])
    assert "N75_4HK1" in n75_models
    assert "N35_RZ4E" not in n75_models
    assert "N35_RZ4E" in lcv_models
    assert "N75_4HK1" not in lcv_models
    assert "multi" in n75_models  # shared PN counted in N75 scope


def test_pms_models_for_scope() -> None:
    n75 = pms_models_for_scope("N75_only")
    lcv = pms_models_for_scope("LCV_only")
    assert "N75_4HK1" in n75
    assert "N35_RZ4E" in lcv
    assert "LCV_DMax" in lcv


def test_expected_addressable_services() -> None:
    cfg = DEFAULT_PARC_CONFIG.copy()
    # 100 trucks × 0.5 services/yr × 100% addressable = 50
    result = expected_addressable_services(100.0, "N75_only", cfg)
    assert result == pytest.approx(50.0)
    assert expected_addressable_services(0.0, "N75_only", cfg) == 0.0


def test_parc_config_for_distributor_sets_scope() -> None:
    cfg = parc_config_for_distributor("IUK")
    assert cfg["scope"] == "LCV_only"
    cfg_ituk = parc_config_for_distributor("ITUK")
    assert cfg_ituk["scope"] == "N75_only"


def test_split_genuine_vs_bvp(df_sales: pd.DataFrame) -> None:
    split = split_genuine_vs_bvp(df_sales[df_sales["distributor_code"] == "ITUK"])
    assert set(split.keys()) == {"genuine", "bvp", "all_pms"}
    assert (split["genuine"]["pms_type"] == "genuine").all()
    assert (split["bvp"]["pms_type"] == "bvp").all()
    assert len(split["all_pms"]) == len(split["genuine"]) + len(split["bvp"])


def test_get_pms_summary_by_distributor(df_sales: pd.DataFrame) -> None:
    summary = get_pms_summary_by_distributor(df_sales, year=2025)
    expected_cols = {
        "distributor_code", "category", "category_label",
        "model", "qty", "revenue_eur", "avg_sp_eur",
    }
    assert expected_cols.issubset(set(summary.columns))
    ituk_oil = summary[
        (summary["distributor_code"] == "ITUK") & (summary["category"] == "oil_filter")
    ]
    assert not ituk_oil.empty
    assert ituk_oil["category_label"].iloc[0] == CATEGORY_LABELS["oil_filter"]


def test_get_dealer_capture_detail(df_sales: pd.DataFrame) -> None:
    detail = get_dealer_capture_detail(df_sales, "ITUK", year=2025)
    expected_cols = {
        "part_number", "description", "pms_category", "pms_model",
        "pms_type", "total_qty", "total_revenue_eur", "avg_sp_eur",
    }
    assert expected_cols.issubset(set(detail.columns))
    oil_rows = detail[detail["pms_category"] == "oil_filter"]
    assert oil_rows["total_qty"].sum() >= 10


def test_get_seasonal_weights_april_peak() -> None:
    assert get_seasonal_weights(4) == pytest.approx(1.15)
    with pytest.raises(ValueError):
        get_seasonal_weights(13)


def test_calculate_pms_capture_synthetic(monkeypatch: pytest.MonkeyPatch, df_sales: pd.DataFrame) -> None:
    """Capture rate uses scoped actuals vs parc-based expected demand."""
    from modules import pms_engine

    def _tag(df: pd.DataFrame, df_dim=None, fill_catalog_pms=True):
        return classify_pms_sales(df)

    monkeypatch.setattr("modules.pms_tagging.tag_pms_sales", _tag)

    parc = {
        "N75_surviving_parc": 100,
        "N75_services_per_year": 0.5,
        "addressable_pct": 1.00,
        "uio_units": 100,
    }
    result = pms_engine.calculate_pms_capture(
        df_sales,
        year=2025,
        distributor_code="ITUK",
        parc_config=parc,
        df_dim=None,
        fill_catalog_pms=False,
    )
    assert "summary_df" in result
    assert "capture_rate_by_category" in result
    oil_actual = result["actual_by_category"].get("oil_filter", {}).get("qty", 0.0)
    assert oil_actual == pytest.approx(18.0)  # 10 + 5 + 3
    oil_expected = result["expected_by_category"]["oil_filter"]["qty"]
    assert oil_expected == pytest.approx(50.0)  # 100 × 0.5 × 1.00
    assert result["capture_rate_by_category"]["oil_filter"] == pytest.approx(18.0 / 50.0)
    summary = result["summary_df"]
    assert "capture_rate" in summary.columns
    assert "category_label" in summary.columns
