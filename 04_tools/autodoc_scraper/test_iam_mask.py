"""scrape_error must not be scored as an IAM price gap."""

from __future__ import annotations

import pandas as pd

from iam_scoring import mask_scrape_error_prices


def test_mask_scrape_error_not_a_price_gap() -> None:
    df = pd.DataFrame(
        {
            "PN": ["1", "2", "3"],
            "PR00_EUR": [100.0, 100.0, 100.0],
            "KS_AM_min_eur": [10.0, 20.0, 30.0],
            "KS_AM_status": ["error", "no_results", "ok"],
            "KS_AM_scrape_error": ["HTTP 500", "", ""],
            "MEK_min_eur": [11.0, 21.0, 31.0],
            "MEK_status": ["ok", "ok", "ok"],
        }
    )
    out = mask_scrape_error_prices(df)
    assert pd.isna(out.loc[0, "KS_AM_min_eur"])
    assert out.loc[1, "KS_AM_min_eur"] == 20.0
    assert out.loc[1, "KS_AM_status"] == "no_results"
    assert out.loc[2, "KS_AM_min_eur"] == 30.0
    assert out.loc[0, "best_price_eur"] == 11.0
    assert out.loc[2, "best_price_eur"] == 30.0
