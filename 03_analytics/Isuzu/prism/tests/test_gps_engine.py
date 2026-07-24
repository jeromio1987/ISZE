"""Unit tests for gps_engine — synthetic data only."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from modules.data_prep import UIO_PROXY_YEAR
from modules.gps_engine import (
    GPS_TARGET_EUR_PER_UNIT,
    add_gps_pct_of_target,
    build_uio_lookup,
    calculate_sales_by_distributor,
    calculate_spend_per_unit,
    flag_pdi_parts,
    get_summary_kpis,
    weight_uio_by_age,
)


@pytest.fixture
def df_sales() -> pd.DataFrame:
    """15 synthetic sales rows across two distributors and two calendar years."""
    return pd.DataFrame(
        [
            # D001 — 2024 parts revenue
            {"distributor_code": "D001", "year": 2024, "net_sales_value": 500.0, "billed_qty": 2,
             "is_credit_note": False, "description": "FILTER ELEMENT", "line_kind": "part"},
            {"distributor_code": "D001", "year": 2024, "net_sales_value": 500.0, "billed_qty": 1,
             "is_credit_note": False, "description": "BRAKE PAD SET", "line_kind": "part"},
            # D001 — 2025 parts + warranty credit (negative qty)
            {"distributor_code": "D001", "year": 2025, "net_sales_value": 800.0, "billed_qty": 4,
             "is_credit_note": False, "description": "OIL FILTER", "line_kind": "part"},
            {"distributor_code": "D001", "year": 2025, "net_sales_value": -120.0, "billed_qty": 0,
             "is_credit_note": True, "description": "WARRANTY CREDIT NOTE", "line_kind": "part"},
            # D001 — freight line (excluded by line_kind)
            {"distributor_code": "D001", "year": 2025, "net_sales_value": 999.0, "billed_qty": 1,
             "is_credit_note": False, "description": "FREIGHT CHARGE", "line_kind": "freight"},
            # D002 — 2024
            {"distributor_code": "D002", "year": 2024, "net_sales_value": 300.0, "billed_qty": 1,
             "is_credit_note": False, "description": "GASKET KIT", "line_kind": "part"},
            {"distributor_code": "D002", "year": 2024, "net_sales_value": 200.0, "billed_qty": 1,
             "is_credit_note": False, "description": "CLUTCH DISC", "line_kind": "part"},
            # D002 — 2025
            {"distributor_code": "D002", "year": 2025, "net_sales_value": 450.0, "billed_qty": 2,
             "is_credit_note": False, "description": "AIR FILTER", "line_kind": "part"},
            # D003 — 2025 only (no UIO in fixture)
            {"distributor_code": "D003", "year": 2025, "net_sales_value": 600.0, "billed_qty": 3,
             "is_credit_note": False, "description": "BELT TENSIONER", "line_kind": "part"},
            # D004 — zero UIO distributor
            {"distributor_code": "D004", "year": 2025, "net_sales_value": 400.0, "billed_qty": 2,
             "is_credit_note": False, "description": "WATER PUMP", "line_kind": "part"},
            # Extra 2024 rows for multiyear coverage
            {"distributor_code": "D001", "year": 2024, "net_sales_value": 100.0, "billed_qty": 1,
             "is_credit_note": False, "description": "BOLT KIT", "line_kind": "part"},
            {"distributor_code": "D002", "year": 2025, "net_sales_value": 50.0, "billed_qty": 1,
             "is_credit_note": False, "description": "SEAL RING", "line_kind": "part"},
            {"distributor_code": "D001", "year": 2025, "net_sales_value": 200.0, "billed_qty": 1,
             "is_credit_note": False, "description": "PDI ACCESSORY KIT", "line_kind": "part"},
            {"distributor_code": "D002", "year": 2024, "net_sales_value": -30.0, "billed_qty": -1,
             "is_credit_note": True, "description": "CREDIT ADJUSTMENT", "line_kind": "part"},
            {"distributor_code": "D003", "year": 2024, "net_sales_value": 150.0, "billed_qty": 1,
             "is_credit_note": False, "description": "SPARK PLUG", "line_kind": "part"},
        ]
    )


@pytest.fixture
def df_uio() -> pd.DataFrame:
    """Synthetic UIO: matched years, proxy year, zero-UIO, and missing distributor."""
    return pd.DataFrame(
        [
            {"distributor_code": "D001", "year": 2024, "uio_units": 10.0},
            {"distributor_code": "D001", "year": 2025, "uio_units": 12.0},
            {"distributor_code": "D002", "year": 2024, "uio_units": 5.0},
            {"distributor_code": "D002", "year": 2025, "uio_units": 6.0},
            # Proxy-only: no 2026 row — D001/D002 should proxy from UIO_PROXY_YEAR
            {"distributor_code": "D001", "year": UIO_PROXY_YEAR, "uio_units": 12.0},
            {"distributor_code": "D002", "year": UIO_PROXY_YEAR, "uio_units": 6.0},
            # Zero UIO — must not produce finite spend/unit
            {"distributor_code": "D004", "year": 2025, "uio_units": 0.0},
            # D003 intentionally absent
        ]
    )


@pytest.fixture
def df_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"distributor_code": "D001", "country": "DE", "region": "EU"},
            {"distributor_code": "D002", "country": "FR", "region": "EU"},
            {"distributor_code": "D003", "country": "IT", "region": "EU"},
            {"distributor_code": "D004", "country": "ES", "region": "EU"},
        ]
    )


def test_build_uio_lookup_and_proxy(df_uio: pd.DataFrame) -> None:
    lookup, proxy = build_uio_lookup(df_uio)
    assert lookup[("D001", 2024)] == 10.0
    assert lookup[("D002", 2025)] == 6.0
    assert proxy["D001"] == 12.0
    assert proxy["D002"] == 6.0
    assert ("D003", 2025) not in lookup


def test_calculate_sales_by_distributor_groups_and_excludes_freight(
    df_sales: pd.DataFrame,
) -> None:
    result = calculate_sales_by_distributor(df_sales, year=2024)
    d001 = result.loc[result["distributor_code"] == "D001"].iloc[0]
    # 500 + 500 + 100 = 1100 (freight excluded)
    assert d001["total_sales_eur"] == pytest.approx(1100.0)
    d002 = result.loc[result["distributor_code"] == "D002"].iloc[0]
    assert d002["total_sales_eur"] == pytest.approx(470.0)  # 300+200-30


def test_calculate_sales_excludes_warranty_when_flagged(df_sales: pd.DataFrame) -> None:
    result = calculate_sales_by_distributor(
        df_sales, year=2025, exclude_warranty=True,
    )
    d001 = result.loc[result["distributor_code"] == "D001"].iloc[0]
    # 800 + 200 parts; warranty -120 and freight 999 excluded
    assert d001["total_sales_eur"] == pytest.approx(1000.0)
    assert d001["warranty_credits_eur"] == pytest.approx(-120.0)


def test_spend_per_unit_uses_sales_over_uio(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
) -> None:
    result = calculate_spend_per_unit(
        df_sales, df_uio, df_metadata, year=2024,
    )
    d001 = result.loc[result["distributor_code"] == "D001"].iloc[0]
    assert d001["total_sales_eur"] == pytest.approx(1100.0)
    assert d001["uio_units"] == 10.0
    assert d001["spend_per_unit_eur"] == pytest.approx(110.0)
    assert bool(d001["uio_available"]) is True
    assert bool(d001["uio_proxy"]) is False


def test_missing_uio_yields_nan_spend_per_unit(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
) -> None:
    result = calculate_spend_per_unit(
        df_sales, df_uio, df_metadata, year=2025,
    )
    d003 = result.loc[result["distributor_code"] == "D003"].iloc[0]
    assert d003["total_sales_eur"] == pytest.approx(600.0)
    assert d003["uio_units"] == 0
    assert np.isnan(d003["spend_per_unit_eur"])
    assert bool(d003["uio_available"]) is False


def test_zero_uio_yields_nan_not_infinite(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
) -> None:
    result = calculate_spend_per_unit(
        df_sales, df_uio, df_metadata, year=2025,
    )
    d004 = result.loc[result["distributor_code"] == "D004"].iloc[0]
    assert d004["uio_units"] == 0
    assert np.isnan(d004["spend_per_unit_eur"])
    assert not np.isfinite(d004["spend_per_unit_eur"])


def test_uio_proxy_fallback_for_later_year(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
) -> None:
    sales_2026 = pd.concat(
        [
            df_sales,
            pd.DataFrame(
                [{
                    "distributor_code": "D001",
                    "year": 2026,
                    "net_sales_value": 1200.0,
                    "billed_qty": 2,
                    "is_credit_note": False,
                    "description": "RADIATOR",
                    "line_kind": "part",
                }]
            ),
        ],
        ignore_index=True,
    )
    result = calculate_spend_per_unit(
        sales_2026, df_uio, df_metadata, year=2026,
    )
    d001 = result.loc[result["distributor_code"] == "D001"].iloc[0]
    assert bool(d001["uio_proxy"]) is True
    assert d001["uio_year"] == UIO_PROXY_YEAR
    assert d001["spend_per_unit_eur"] == pytest.approx(1200.0 / 12.0)


def test_output_contains_expected_columns(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
) -> None:
    result = calculate_spend_per_unit(
        df_sales, df_uio, df_metadata, year=2025, exclude_warranty=True,
    )
    expected = {
        "distributor_code", "country", "region", "total_sales_eur", "uio_units",
        "spend_per_unit_eur", "uio_year", "uio_proxy", "uio_available",
        "warranty_credits_eur",
    }
    assert expected.issubset(set(result.columns))


def test_add_gps_pct_of_target(df_sales: pd.DataFrame, df_uio: pd.DataFrame, df_metadata: pd.DataFrame) -> None:
    spu = calculate_spend_per_unit(df_sales, df_uio, df_metadata, year=2024)
    with_pct = add_gps_pct_of_target(spu)
    d001 = with_pct.loc[with_pct["distributor_code"] == "D001"].iloc[0]
    assert d001["gps_pct"] == pytest.approx((110.0 / GPS_TARGET_EUR_PER_UNIT) * 100)


def test_get_summary_kpis_ignores_missing_uio(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
) -> None:
    spu = calculate_spend_per_unit(df_sales, df_uio, df_metadata, year=2025)
    kpis = get_summary_kpis(spu)
    assert kpis["n_distributors"] == 4
    assert kpis["n_with_uio"] == 2  # D001, D002 only
    assert kpis["avg_spend_per_unit"] > 0


def test_flag_pdi_parts_detects_accessory_description(df_sales: pd.DataFrame) -> None:
    flagged = flag_pdi_parts(df_sales)
    pdi_row = flagged.loc[flagged["description"] == "PDI ACCESSORY KIT"].iloc[0]
    assert bool(pdi_row["is_pdi"]) is True
    normal = flagged.loc[flagged["description"] == "OIL FILTER"].iloc[0]
    assert bool(normal["is_pdi"]) is False


def test_weight_uio_by_age_applies_decay(df_uio: pd.DataFrame) -> None:
    uio_with_old = pd.concat(
        [
            df_uio,
            pd.DataFrame(
                [{"distributor_code": "D001", "year": 2018, "uio_units": 10.0}]
            ),
        ],
        ignore_index=True,
    )
    weighted = weight_uio_by_age(
        uio_with_old, reference_year=2025, peak_age_years=5, decay_factor=0.85,
    )
    recent = weighted.loc[
        (weighted["distributor_code"] == "D001") & (weighted["year"] == 2025)
    ].iloc[0]
    old = weighted.loc[
        (weighted["distributor_code"] == "D001") & (weighted["year"] == 2018)
    ].iloc[0]
    assert recent["age_weighted_uio"] == pytest.approx(12.0)
    # age 7 → two years beyond peak → 0.85^2
    assert old["age_weighted_uio"] == pytest.approx(10.0 * (0.85 ** 2))
