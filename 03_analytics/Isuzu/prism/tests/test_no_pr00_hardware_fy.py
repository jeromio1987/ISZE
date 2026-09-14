"""No-list leftover table is FY grain, euros only, no piece KPIs."""

from __future__ import annotations

import pandas as pd

from scripts.build_no_pr00_hardware_table import aggregate_no_list, family_of


def test_family_groups_cabs_not_piece_counts() -> None:
    assert family_of("CAB ASM; SERVICE,WO/ELEC") == "Cab assemblies"
    assert family_of("STEERING UNIT") == "Steering units"


def test_aggregate_is_euros_by_part_no_qty_columns() -> None:
    sales = pd.DataFrame(
        {
            "part_number": ["A", "A", "B"],
            "fiscal_year": [2025, 2025, 2025],
            "distributor_code": ["UTI", "UTI", "UMI"],
            "net_sales_value": [100.0, 50.0, 20.0],
            "billed_qty": [4, 2, 100],
        }
    )
    residual = pd.DataFrame(
        {
            "part_number": ["A", "B"],
            "description": ["CAB ASM; SERVICE,WO/ELEC", "HANDLE; OUTSIDE,BACK DOOR"],
        }
    )
    out = aggregate_no_list(sales, residual, 2025)
    assert list(out.columns) == [
        "part_number",
        "description",
        "part_in_words",
        "family",
        "billed_eur",
        "billed_to",
    ]
    assert "billed_qty" not in out.columns
    assert "std_qty" not in out.columns
    assert float(out.loc[out["part_number"] == "A", "billed_eur"].iloc[0]) == 150.0
    assert "UTI" in out.loc[out["part_number"] == "A", "billed_to"].iloc[0]
    assert out.loc[out["part_number"] == "A", "part_in_words"].iloc[0].startswith("Cab")
    assert out.iloc[0]["part_number"] == "A"
