from modules.fiscal import (
    gps_fy,
    gps_fy_dates,
    sales_fiscal_from_gps_fy,
    sales_fiscal_year,
)


def test_april_starts_sales_fiscal_in_that_calendar_year() -> None:
    assert sales_fiscal_year(2025, 4) == 2025
    assert sales_fiscal_year(2026, 3) == 2025
    assert sales_fiscal_year(2026, 4) == 2026


def test_gps_fy_is_march_close_year() -> None:
    assert gps_fy(2025) == 2026
    assert sales_fiscal_from_gps_fy(2026) == 2025
    assert gps_fy_dates(2026) == ("2025-04-01", "2026-03-31")
    assert gps_fy_dates(2027) == ("2026-04-01", "2027-03-31")
