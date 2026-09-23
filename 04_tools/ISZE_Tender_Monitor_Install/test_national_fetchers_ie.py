"""Ireland eTenders open-data filter — vehicle rows only."""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO

import pandas as pd

from national_fetchers_ie import rows_from_etenders_frame


def test_keeps_truck_cpv_and_drops_it() -> None:
    csv = (
        "Tender ID,Contracting Authority,Tender/Contract Name,"
        "Notice Published Date / Contract Created Date,Main Cpv Code,"
        "Main Cpv Code Description,TED Notice Link,Tender Submission Deadline,"
        "Sum of Notice Estimated Value (€)\n"
        "1,Dublin City Council,Supply of 7.5 tonne trucks,15/05/2026,34130000,"
        "Goods vehicles,https://ted.example/1,01/06/2026,250000\n"
        "2,OGP,ICT support services,15/05/2026,72000000,"
        "IT services,https://ted.example/2,01/06/2026,100000\n"
    )
    df = pd.read_csv(StringIO(csv))
    rows = rows_from_etenders_frame(df, from_dt=datetime(2026, 4, 1, tzinfo=timezone.utc))
    assert len(rows) == 1
    assert "truck" in rows[0]["Title"].lower()
    assert rows[0]["Country Code"] == "IRL"
