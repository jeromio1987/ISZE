# -*- coding: utf-8 -*-
"""Consolidate missing_observations.csv so every raw row appears once, under one code."""
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
mo = pd.read_csv(OUT / "missing_observations.csv", dtype=str)

# the own-number-price fact belongs in the evidence of the no-competitor-price row,
# not as a second row for the same raw line
mo = mo[mo.why_missing != "OWN_NUMBER_PRICE_NOT_LOADED"]

mo["why_missing"] = mo["why_missing"].replace({
    "NO_COMPETITOR_PRICE_BUT_OUR_NUMBER_PRICED": "NO_COMPETITOR_PRICE_ON_THE_ROW",
    "ROW_HAS_NO_PRICE_AT_ALL": "NO_COMPETITOR_PRICE_ON_THE_ROW",
})
mo["why_missing"] = mo["why_missing"].replace({
    "NO_COMPETITOR_PRICE_ON_THE_ROW": "NO_COMPETITOR_PRICE_ON_THE_ROW",
})
mo.loc[mo.why_missing == "NO_COMPETITOR_PRICE_ON_THE_ROW", "evidence"] = (
    "the row states no competitor price (RRP blank); it does state OE RRP for our own number, "
    "which build_price_ledger.py is not allowed to load")

order = ["DUPLICATE_NOT_IN_LEDGER", "LOADER_DROPS_MATCHING_LEVEL", "FILE_SHEET_NEVER_LOADED",
         "FILE_NEVER_LOADED", "PEER_NUMBER_ONLY_NO_OWN_NUMBER", "NO_COMPETITOR_PRICE_ON_THE_ROW",
         "SECOND_GENERATION_NUMBER_NOT_A_LEDGER_KEY"]
mo["_o"] = mo.why_missing.map({c: i for i, c in enumerate(order)}).fillna(99)
mo = mo.sort_values(["_o", "part_no", "raw_file"]).drop(columns=["_o"])
mo.to_csv(OUT / "missing_observations.csv", index=False, encoding="utf-8")

print("rows:", len(mo), " distinct PNs:", mo.part_no.nunique())
print(mo.why_missing.value_counts().to_dict())
print()
print(mo.groupby(["why_missing", "raw_file"]).size().to_string())
