"""FY billed vs sales to dealer: monthly grain, warranty line, no street."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import DASHBOARDS_DIR, DERIVED_DIR, ISZE_ROOT
from scripts.build_billed_vs_std_warranty_fy import (
    IUK_DISC_PN,
    YEAR_PLUS_MONTHS_TRAP_QTY,
    filter_commercial_billed,
    keep_monthly_std_rows,
    load_warranty_fy,
    std_qty_for_pn,
)


def _visible_html(text: str) -> str:
    return re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)


def test_keep_monthly_does_not_add_year_total() -> None:
    df = pd.DataFrame(
        {
            "part_number": ["8983767550"] * 3,
            "period": ["2025", "2025-07", "2025-12"],
            "period_grain": ["year", "month", "month"],
            "qty": [3821.0, 411.0, 266.0],
        }
    )
    out = keep_monthly_std_rows(df)
    assert float(out["qty"].sum()) == 677.0
    assert 3821.0 not in set(out["qty"])
    assert float(out["qty"].sum()) != YEAR_PLUS_MONTHS_TRAP_QTY


def test_keep_monthly_drops_ytd_period() -> None:
    df = pd.DataFrame(
        {
            "year_month": ["2026-YTD", "2026-01", "2026-02"],
            "period_grain": ["ytd", "month", "month"],
            "sellout_qty": [2065.0, 255.0, 306.0],
        }
    )
    out = keep_monthly_std_rows(df)
    assert sorted(out["year_month"].tolist()) == ["2026-01", "2026-02"]
    assert float(out["sellout_qty"].sum()) == 561.0


def test_iuk_disc_fy_qty_is_not_year_plus_months() -> None:
    long_2025 = DERIVED_DIR / "dealer_sellout_long_IUK_CY2025.csv"
    if not long_2025.exists():
        return
    qty = std_qty_for_pn("IUK", IUK_DISC_PN)
    assert qty != YEAR_PLUS_MONTHS_TRAP_QTY
    assert qty != 3821.0
    assert qty > 0


def test_warranty_maps_ireland_and_greece() -> None:
    w = load_warranty_fy()
    assert w["IUK"] == 1335647
    assert w["ITUK"] == 375552
    assert w["IRELAND"] == 49673
    assert w["GREECE"] == 70926
    assert w["UTI"] == 260152
    assert "UMI" not in w or w.get("UMI") != w["UTI"]


def test_filter_drops_freight_and_service_fee_keeps_tools() -> None:
    sales = pd.DataFrame(
        {
            "part_number": [
                "8983767550",
                "TRANSPORT",
                "SERVICE FEE OUTSIDE EUROPE",
                "5874123812",
            ],
            "is_credit_note": [False, False, False, False],
            "line_kind": ["part", "freight", "part", "tool"],
            "net_sales_value": [100.0, 19441.0, 17600.0, 50.0],
        }
    )
    out = filter_commercial_billed(sales)
    pns = set(out["part_number"])
    assert "8983767550" in pns
    assert "5874123812" in pns
    assert "TRANSPORT" not in pns
    assert all("SERVICE" not in str(p) for p in pns)


def test_warranty_not_prorated_when_months_incomplete() -> None:
    """Warranty stays full FY even if the dealer file is 9 months."""
    w = load_warranty_fy()
    assert w["ITUK"] == 375552
    assert w["GREECE"] == 70926


def test_html_has_warranty_column_tbody_no_street() -> None:
    path = DASHBOARDS_DIR / "sales" / "Dealer_Billed_vs_Sales_to_Dealer_FY2026.html"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    visible = _visible_html(text).lower()
    assert "warranty" in visible
    assert "<tbody>" in text
    assert text.count("<tr>") >= 6
    assert "street" not in visible
    assert "sell-out" not in visible
    assert "sellout" not in visible
    assert "iml v7" not in visible
    assert "model b" not in visible
    assert "cdn.jsdelivr" not in text.lower()
    assert "cdnjs.cloudflare" not in text.lower()
    assert "NaN" not in text.split('<script type="application/json" id="chart-data">')[-1][:500]
    assert "€" in visible
    assert "business-review" in visible or "business review" in visible
    json_blob = re.search(
        r'<script type="application/json" id="chart-data">(.*?)</script>',
        text,
        re.S,
    )
    assert json_blob is not None
    assert "NaN" not in json_blob.group(1)


def test_launcher_sits_next_to_html() -> None:
    html = DASHBOARDS_DIR / "sales" / "Dealer_Billed_vs_Sales_to_Dealer_FY2026.html"
    cmd = DASHBOARDS_DIR / "sales" / "OPEN_Billed_vs_Sales_to_Dealer_FY2026.cmd"
    if not html.exists():
        return
    assert cmd.exists()
    body = cmd.read_text(encoding="utf-8")
    assert "Dealer_Billed_vs_Sales_to_Dealer_FY2026.html" in body
    mix = DASHBOARDS_DIR / "sales" / "Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"
    assert mix.exists()


def test_locked_fy_euros_on_built_csv() -> None:
    path = DERIVED_DIR / "billed_vs_std_warranty_fy2026.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    locked = {
        "IUK": (5_951_968, 1_335_647, 5_983_188, -31_220),
        "ITUK": (6_810_869, 375_552, 4_126_594, 483_444),
        "IRELAND": (1_122_097, 49_673, 966_126, 155_971),
        "UTI": (3_208_540, 260_152, 1_823_076, 362_463),
        "GREECE": (471_586, 70_926, 323_411, 72_432),
    }
    for code, (billed, warr, std, stock) in locked.items():
        row = df.loc[df["distributor_code"] == code].iloc[0]
        assert int(row["billed_fy_eur"]) == billed
        assert int(row["warranty_fy_eur"]) == warr
        assert int(row["std_eur"]) == std
        assert int(row["stock_eur"]) == stock
        assert "warranty_fy_eur" in df.columns


def test_html_uk_pickup_warranty_is_gps_hole() -> None:
    path = DASHBOARDS_DIR / "sales" / "Dealer_Billed_vs_Sales_to_Dealer_FY2026.html"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    visible = _visible_html(text)
    assert "€1,335,647" in visible
    assert "UK pickup" in visible
    assert "GPS hole" in visible
    assert "UK truck" in visible
    assert "class=\"bar-row\"" in text
    assert "Jan" in visible or "January" in visible or "Apr 2025" in visible
    src = (ISZE_ROOT / "03_analytics/Isuzu/prism/scripts/build_billed_vs_std_warranty_fy.py").read_text(
        encoding="utf-8"
    )
    assert "Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html" not in src
    assert "Do not stuff FY + warranty into the calendar mix builder" in src
