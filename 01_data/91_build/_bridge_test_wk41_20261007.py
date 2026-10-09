"""Bridge test: can a per-distributor WK41 BO overview be joined to IML's Order No?"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MAIL = ROOT / "01_data" / "90_INBOX" / "_iml_delay_wk41_20261007" / "bo_overview"
DELAY = ROOT / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"


def norm(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


# ---- IML order numbers ----
dly = pd.read_excel(DELAY, sheet_name="isze", dtype=str)
dly.columns = [str(c).strip() for c in dly.columns]
iml_orders = set(dly["Order No"].fillna("").str.strip()) - {""}
iml_pn = set(dly["PN"].fillna("").map(norm)) - {""}
print(f"IML Order No values: {len(iml_orders)} | sample {sorted(iml_orders)[:4]}")
print(f"IML part numbers   : {len(iml_pn)}")
print()

SAMPLE = "20261006_BO OVERVIEW - ISUZU IRELAND 06-10-2026.xlsx"
p = MAIL / SAMPLE
wb = pd.ExcelFile(p)
print("sheets:", wb.sheet_names)

for sh in wb.sheet_names:
    df = pd.read_excel(p, sheet_name=sh, header=None, dtype=str, nrows=14)
    nonempty = df.dropna(how="all").dropna(axis=1, how="all")
    if nonempty.empty:
        continue
    print(f"\n=== sheet {sh!r} (first rows) ===")
    print(nonempty.head(10).to_string(max_colwidth=18))
