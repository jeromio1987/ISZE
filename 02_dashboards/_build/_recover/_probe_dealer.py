"""Read-only probe: why does only one distributor carry a DB->dealer leg?

Replicates just the dealer-file loading from the builder and prints what it
finds per distributor, without writing anything.
"""
import os
import sys

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
D = os.path.join(ROOT, "01_data", "00_derived")
PRISM = os.path.join(ROOT, "03_analytics", "Isuzu", "prism")
if PRISM not in sys.path:
    sys.path.insert(0, PRISM)

FYMON = ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
         "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]

DEALER_FILES = {
    "IUK": "dealer_sellout_long_IUK_CY2025.csv",
    "ITUK": "dealer_sellout_long_ITUK_CY2025.csv",
    "IRELAND": "dealer_sellout_long_IRELAND_CY2025.csv",
    "GREECE": "dealer_sellout_long_GREECE_CY2025.csv",
    "PORTUGAL": "dealer_sellout_long_PORTUGAL_CY2025.csv",
    "UTI": "dealer_sellout_long_UTI_CY2025.csv",
}
DEALER_FILES_2026 = {
    "IUK": "dealer_sellout_long_IUK_CY2026YTD.csv",
    "ITUK": "dealer_sellout_long_ITUK_CY2026YTD.csv",
    "IRELAND": "dealer_sellout_long_IRELAND_CY2026YTD.csv",
    "PORTUGAL": "dealer_sellout_long_PORTUGAL_CY2026YTD.csv",
    "UTI": "dealer_sellout_long_UTI_CY2026YTD.csv",
    "ROMANIA": "dealer_sellout_long_ROMANIA_CY2026YTD.csv",
}

dealer_files = {}
for _db, _f in {**DEALER_FILES, **DEALER_FILES_2026}.items():
    dealer_files.setdefault(_db, []).append(_f)

for db, files in dealer_files.items():
    for f in files:
        p = os.path.join(D, f)
        if not os.path.exists(p):
            print(f"{db:10s} {f}: MISSING")
            continue
        d = pd.read_csv(p, usecols=["period", "period_grain", "part_number", "qty"])
        grains = d.period_grain.astype(str).value_counts().to_dict()
        dm = d[d.period_grain == "month"]
        months = sorted(dm.period.astype(str).unique())[:4]
        tail = sorted(dm.period.astype(str).unique())[-3:]
        cy = dm[dm.period.astype(str).str.startswith("2025")]
        fy = dm[dm.period.astype(str).isin(FYMON)]
        print(f"{db:10s} {f}")
        print(f"           grains={grains} month_rows={len(dm)} first={months} last={tail}")
        print(f"           cy_rows={len(cy)} fy_rows={len(fy)}")
