"""Check the Evidence app's built tender data matches the live feed.

Reads the source the app built under ``.evidence/``, not the CSV it was built
from, so this proves what the app itself will serve.
"""
from __future__ import annotations

import glob
from pathlib import Path

import duckdb

APP = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\evidence-app")
found = sorted(glob.glob(str(APP / ".evidence" / "**" / "tender_pipeline*"), recursive=True))
print("built files found:")
for f in found:
    print("   ", f, Path(f).stat().st_size if Path(f).is_file() else "")

pq = [f for f in found if f.endswith(".parquet")]
if not pq:
    raise SystemExit("no tender_pipeline parquet was built")

con = duckdb.connect()
for path in pq:
    p = Path(path).as_posix()
    q = (
        "select count(*) as rows, "
        "sum(case when actionable then 1 else 0 end) as actionable, "
        "sum(case when rm_contract then 1 else 0 end) as rm_contract, "
        "sum(case when value_amount is not null and value_amount > 0 then 1 else 0 end) as with_value, "
        "sum(case when deadline_date is not null and cast(deadline_date as varchar) <> '' then 1 else 0 end) as with_deadline "
        f"from read_parquet('{p}')"
    )
    cols = [c[0] for c in con.execute(q).description]
    vals = con.execute(q).fetchone()
    print()
    print(p)
    print("   " + ", ".join(f"{c}={v}" for c, v in zip(cols, vals)))

print()
print("expected from the live feed: rows=619, actionable=281, rm_contract=279, "
      "with_value=31, with_deadline=128")
