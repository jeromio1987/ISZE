"""Tests for billing reconciliation.

Every euro in this module is made-up. These rows are not invoices, not a
distributor's sales, and not a company result.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reconcile import compare  # noqa: E402


def _row(result, distributor_id, period):
    found = [
        row
        for row in result["rows"]
        if row["distributor_id"] == distributor_id and row["period"] == period
    ]
    assert len(found) == 1
    return found[0]


def test_warranty_separated_and_the_remainder_is_stock():
    billed = [
        {"distributor_id": "DIST-A", "period": "2026-04", "order_type": "SOR", "euros": "100.00"},
        {"distributor_id": "DIST-A", "period": "2026-04", "order_type": "SOR", "euros": "1.005"},
        {"distributor_id": "DIST-A", "period": "2026-04", "order_type": "VOR", "euros": "10.00"},
        {"distributor_id": "DIST-A", "period": "2026-04", "order_type": "STOCK", "euros": "5.00"},
        {"distributor_id": "DIST-A", "period": "2026-05", "order_type": "SOR", "euros": "1.00"},
        {"distributor_id": "DIST-B", "period": "2026-04", "order_type": "SOR", "euros": 8},
    ]
    sales_to_dealer = [
        {"distributor_id": "DIST-A", "period": "2026-04", "euros": "70.00"},
        {"distributor_id": "DIST-A", "period": "2026-05", "euros": "2.50"},
        {"distributor_id": "DIST-B", "period": "2026-04", "euros": "3.00"},
    ]
    warranty = [
        {"distributor_id": "DIST-A", "period": "2026-04", "euros": 20},
        {"distributor_id": "DIST-B", "period": "2026-04", "euros": "1.00"},
    ]

    result = compare(billed, sales_to_dealer, warranty)

    april = _row(result, "DIST-A", "2026-04")
    assert april["billed_eur"] == {
        "SOR": Decimal("101.01"),
        "STOCK": Decimal("5.00"),
        "VOR": Decimal("10.00"),
    }
    assert april["billed_eur_total"] == Decimal("116.01")
    assert sum(april["billed_eur"].values(), Decimal("0.00")) == Decimal("116.01")
    assert april["warranty_eur"] == Decimal("20.00")
    assert april["sales_to_dealer_eur"] == Decimal("70.00")
    assert april["stock_eur"] == Decimal("26.01")
    assert april["stock_eur"] == (
        april["billed_eur_total"] - april["warranty_eur"] - april["sales_to_dealer_eur"]
    )
    assert april["reading"] == "stock, not lost sales"
    assert result["reading"] == "stock, not lost sales"
    assert april["match"] == "tolerance not set"
    assert april["notes"] == []
    assert "credit" not in april
    assert "posting" not in april

    may = _row(result, "DIST-A", "2026-05")
    assert may["warranty_eur"] == Decimal("0.00")
    assert may["sales_to_dealer_eur"] == Decimal("2.50")
    assert may["stock_eur"] == Decimal("-1.50")
    assert may["reading"] == "stock, not lost sales"

    other = _row(result, "DIST-B", "2026-04")
    assert other["billed_eur_total"] == Decimal("8.00")
    assert other["warranty_eur"] == Decimal("1.00")
    assert other["stock_eur"] == Decimal("4.00")

    on_the_line = compare(billed, sales_to_dealer, warranty, tolerance=Decimal("26.01"))
    assert _row(on_the_line, "DIST-A", "2026-04")["match"] == "inside"
    assert _row(on_the_line, "DIST-A", "2026-04")["reading"] == "stock, not lost sales"

    just_under = compare(billed, sales_to_dealer, warranty, tolerance=Decimal("26.00"))
    assert _row(just_under, "DIST-A", "2026-04")["match"] == "outside"
    assert _row(just_under, "DIST-A", "2026-04")["stock_eur"] == Decimal("26.01")

    negative_gap = compare(billed, sales_to_dealer, warranty, tolerance=Decimal("1.50"))
    assert _row(negative_gap, "DIST-A", "2026-05")["match"] == "inside"
    tighter = compare(billed, sales_to_dealer, warranty, tolerance=Decimal("1.49"))
    assert _row(tighter, "DIST-A", "2026-05")["match"] == "outside"


def test_warranty_unknown_leaves_stock_uncomputed():
    billed = [
        {"distributor_id": "DIST-W", "period": "2026-07", "order_type": "STOCK", "euros": "50.00"},
        {"distributor_id": "DIST-W", "period": "2026-07", "order_type": "SOR", "euros": "10.00"},
    ]
    sales_to_dealer = [
        {"distributor_id": "DIST-W", "period": "2026-07", "euros": "12.00"},
    ]

    result = compare(billed, sales_to_dealer, None)

    row = _row(result, "DIST-W", "2026-07")
    assert row["billed_eur"]["STOCK"] == Decimal("50.00")
    assert row["billed_eur_total"] == Decimal("60.00")
    assert row["sales_to_dealer_eur"] == Decimal("12.00")
    assert row["warranty_eur"] is None
    assert row["stock_eur"] is None
    assert row["notes"] == ["warranty split unknown, stock not computed"]
    assert result["notes"] == ["warranty split unknown, stock not computed"]
    assert row["match"] == "tolerance not set"
    assert row["reading"] == "stock, not lost sales"

    scored = compare(billed, sales_to_dealer, None, tolerance=100)
    scored_row = _row(scored, "DIST-W", "2026-07")
    assert scored_row["warranty_eur"] is None
    assert scored_row["stock_eur"] is None
    assert scored_row["match"] not in ("inside", "outside")
    assert scored_row["billed_eur"]["STOCK"] == Decimal("50.00")


def test_prd_stays_prd():
    billed = [
        {"distributor_id": "DIST-P", "period": "2026-01", "order_type": "PRD", "euros": "11.60"},
        {"distributor_id": "DIST-P", "period": "2026-01", "order_type": "SOR", "euros": "3.40"},
        {"distributor_id": "DIST-P", "period": "2026-01", "order_type": "Z9", "euros": "1.00"},
    ]
    sales_to_dealer = [
        {"distributor_id": "DIST-P", "period": "2026-01", "euros": "4.00"},
    ]

    result = compare(billed, sales_to_dealer, [], tolerance=Decimal("12.00"))

    row = _row(result, "DIST-P", "2026-01")
    assert row["billed_eur"]["PRD"] == Decimal("11.60")
    assert set(row["billed_eur"]) == {"PRD", "SOR", "Z9"}
    assert "STOCK" not in row["billed_eur"]
    assert row["billed_eur_total"] == Decimal("16.00")
    assert row["warranty_eur"] == Decimal("0.00")
    assert row["sales_to_dealer_eur"] == Decimal("4.00")
    assert row["stock_eur"] == Decimal("12.00")
    assert row["match"] == "inside"
    assert row["reading"] == "stock, not lost sales"


def test_sales_to_dealer_line_without_euros_is_skipped():
    billed = [
        {"distributor_id": "DIST-M", "period": "2026-06", "order_type": "SOR", "euros": "40.00"},
    ]
    sales_to_dealer = [
        {"distributor_id": "DIST-M", "period": "2026-06", "euros": "15.50"},
        {
            "distributor_id": "DIST-M",
            "period": "2026-06",
            "quantity": 9,
            "part_number": "MADE-UP-PN",
        },
        {"distributor_id": "DIST-M", "period": "2026-06", "euros": "4.25"},
    ]
    warranty = [
        {"distributor_id": "DIST-M", "period": "2026-06", "euros": "5.00"},
    ]

    result = compare(billed, sales_to_dealer, warranty)

    row = _row(result, "DIST-M", "2026-06")
    assert row["sales_to_dealer_eur"] == Decimal("19.75")
    assert row["warranty_eur"] == Decimal("5.00")
    assert row["stock_eur"] == Decimal("15.25")
    assert row["notes"] == ["sales-to-dealer line had no euro amount"]
    assert result["notes"] == ["sales-to-dealer line had no euro amount"]
    assert row["reading"] == "stock, not lost sales"
