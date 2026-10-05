# -*- coding: utf-8 -*-
"""Patch the benchmark JSON with the independent cross-check basis for the C claim."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "01_data" / "90_INBOX" / "_classification_benchmark_20260920.json"
d = json.loads(P.read_text(encoding="utf-8"))
pc = d["price_class_concentration"]
pc["basis_4_cross_check_2026_price_file"] = {
    "basis": ("01_data/00_derived/pricing_list_pn.parquet, built 10 Aug 2026 from "
              "Price_file_2026_full.xlsx (file dated 9 Aug 2026). Distinct part numbers by class."),
    "current_rows_distinct_pn": 275992,
    "current_rows_C_pn": 206598,
    "current_rows_C_pct": 74.86,
    "all_rows_distinct_pn": 526368,
    "all_rows_C_pn": 383680,
    "all_rows_C_pct": 72.89,
    "note": ("This is the closest any measured basis comes to the 79% figure, and it is a part-number "
             "count, not a euro share."),
}
pc["verdict"]["claim_79pct_class_C"] = (
    "Not reproduced on any basis measured here. The highest class C share found is 74.9% (distinct "
    "current part numbers in the 2026 full price file); the money-weighted share is 46.0%."
)
pc["verdict"]["basis_recommendation"] = (
    "Quote class C as 46.0% of priced billed euro (or 50.1% of the whole book) when the point is "
    "margin exposure, and as 74.9% of distinct current part numbers when the point is catalogue "
    "policy. Never quote a single 'C share' without the basis."
)
pc["verdict"]["closest_basis_to_the_claim"] = (
    "Two bases come close: the 2026 full price file counts 74.9% of distinct current part numbers "
    "in class C, and the Japan price CD collapsed to a single letter is 72.3% of all rows (72.8% of "
    "classed rows). Both are part-number counts. Neither is a euro share."
)
P.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
print("patched", P)
print(json.dumps(pc["verdict"], indent=2)[:1400])
