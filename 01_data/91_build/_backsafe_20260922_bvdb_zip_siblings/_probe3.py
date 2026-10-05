#!/usr/bin/env python3
"""READ-ONLY: builder inputs' mtimes, and whether the pipeline already flags a
part-year revenue gap as not quotable."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

for n in ("gps_spu_by_distributor.csv", "aim_exposure_by_db_year.csv",
          "pms_capture_by_db_year.csv", "aim_gps_matrix.csv", "aim_gps_matrix.parquet",
          "distributor_dimension.csv", "uio_by_market_type_year.csv"):
    p = DER / n
    if p.exists():
        st = p.stat()
        print(f"{n:42s} {st.st_size:>9} bytes  {pd.Timestamp(st.st_mtime, unit='s', tz='UTC').tz_convert('Europe/Amsterdam')}")

cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
c = cap[cap["line_type"] == "total"]
print("\nrevenue_gap_quotable by year (line_type=total):")
print(c.groupby("year")["revenue_gap_quotable"].value_counts(dropna=False).to_string())
print("\n2026 sample shapes:")
print(c[c["year"] == 2026][["distributor_code", "pms_category", "expected_qty", "actual_qty",
                            "capture_rate", "revenue_gap_eur", "revenue_gap_quotable"]]
      .head(4).to_string(index=False))
