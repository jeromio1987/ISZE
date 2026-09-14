"""ISZE fiscal year labels.

Billing integer ``sales_fact.fiscal_year`` is the calendar year of April.
GPS and Power BI name the same window by the March close year.

    1 Apr 2025 – 31 Mar 2026  →  billing fiscal_year 2025  →  GPS/PBI FY2026
    1 Apr 2026 – 31 Mar 2027  →  billing fiscal_year 2026  →  GPS/PBI FY2027

Never brief Jerome with the billing integer as "FY2025" for Apr 2025–Mar 2026.
That window is FY2026 in GPS and Power BI.
"""

from __future__ import annotations


def sales_fiscal_year(year: int, month: int) -> int:
    """April-start integer stored on sales_fact (Apr 2025 → 2025)."""
    if int(month) >= 4:
        return int(year)
    return int(year) - 1


def gps_fy(sales_fiscal: int) -> int:
    """GPS / Power BI FY number for a sales_fact.fiscal_year integer."""
    return int(sales_fiscal) + 1


def sales_fiscal_from_gps_fy(gps_year: int) -> int:
    """sales_fact.fiscal_year integer for a GPS/PBI FY number."""
    return int(gps_year) - 1


def gps_fy_dates(gps_year: int) -> tuple[str, str]:
    """Inclusive calendar bounds for a GPS/PBI FY (Apr–Mar)."""
    start_year = int(gps_year) - 1
    return f"{start_year}-04-01", f"{gps_year}-03-31"
