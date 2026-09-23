"""Annual sales-to-dealer loader must not add year total + months."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from modules.dealer_sales_loader import load_sellout_long_pn


def test_load_sellout_long_pn_does_not_double_count_year_and_months(tmp_path: Path) -> None:
    rows = [
        {
            "distributor_code": "IUK",
            "year": 2025,
            "period": "2025",
            "period_grain": "year",
            "part_number": "8983767550",
            "qty": 3821,
        },
        {
            "distributor_code": "IUK",
            "year": 2025,
            "period": "2025-07",
            "period_grain": "month",
            "part_number": "8983767550",
            "qty": 411,
        },
        {
            "distributor_code": "IUK",
            "year": 2025,
            "period": "2025-12",
            "period_grain": "month",
            "part_number": "8983767550",
            "qty": 266,
        },
    ]
    path = tmp_path / "dealer_sellout_long_IUK_CY2025.csv"
    pd.DataFrame(rows).to_csv(path, index=False)

    out = load_sellout_long_pn("IUK", 2025, tmp_path)
    assert len(out) == 1
    assert float(out.iloc[0]["qty_year"]) == 3821.0


def test_load_sellout_long_pn_months_only_sums_months(tmp_path: Path) -> None:
    rows = [
        {
            "distributor_code": "IUK",
            "year": 2025,
            "period": "2025-01",
            "period_grain": "month",
            "part_number": "7552348280",
            "qty": 10,
        },
        {
            "distributor_code": "IUK",
            "year": 2025,
            "period": "2025-02",
            "period_grain": "month",
            "part_number": "7552348280",
            "qty": 14,
        },
    ]
    path = tmp_path / "dealer_sellout_long_IUK_CY2025.csv"
    pd.DataFrame(rows).to_csv(path, index=False)

    out = load_sellout_long_pn("IUK", 2025, tmp_path)
    assert float(out.iloc[0]["qty_year"]) == 24.0
