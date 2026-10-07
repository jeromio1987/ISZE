# -*- coding: utf-8 -*-
"""Work package D - write tried.csv and status.json from the finished analysis."""
import json
from pathlib import Path

import pandas as pd

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = Path(__file__).resolve().parent


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


mo = pd.read_csv(OUT / "missing_observations.csv", dtype=str)

w = pd.read_csv(MAIN / "01_data" / "90_INBOX" / "MARKET_SCRAPE_WORKLIST_20261007.csv", dtype=str)
w["pn"] = z(w["part_number"])
wpn = set(w["pn"])
fam = w.drop_duplicates("pn").set_index("pn")["pms_category"].to_dict()

led = pd.read_parquet(MAIN / "01_data" / "00_derived" / "price_observations.parquet")
led["pn"] = z(led["part_no"])
led_all = set(led.pn)
eucon_pns = set(led[led.loader.astype(str).str.startswith("eucon", na=False)].pn)
empty = sorted(p for p in wpn if p not in led_all)

sup1 = json.load(open(OUT / "_sup_counts.json", encoding="utf-8"))
sup2 = json.load(open(OUT / "_sup_counts2.json", encoding="utf-8"))

# ---- tried.csv -------------------------------------------------------------
ROWS = [
 ("01_data/01_Pricing/_raw/eucon_pricing_partspool_20260329.xlsx", "local raw file", "read; read only",
  "Eucon_Pricing_Clean (1,364) + Summary_by_PN (44) + Metadata",
  "45 PNs, 492 competitor pairs; 6 pairs on the 123. Its rows reach the ledger only through the derived crossref csv."),
 ("01_data/Eucon_Online28072025.xlsx", "local raw file", "read; read only", "Fresh list_Export_28072025_0932 (5,081)",
  "1,146 rows reach 10 of the 123 PNs; 'Additional Part Numbers' is non-empty on 358 rows and never becomes a ledger key."),
 ("01_data/Fresh list_Export_28072025_0932.txt", "local raw file", "read; read only",
  "raw text export, latin-1, ';' separated (13,314 rows)",
  "keeps the 'Supersession Info ID' column the xlsx dropped. For the 123, competitor-priced rows are identical to the xlsx (217, key by key) and all 27 Portugal rows are already in the ledger."),
 ("01_data/Eucon_March.xlsx", "local raw file", "read; read only", "Online 15032024 (894) + RRP MODE (552)",
  "RRP MODE has no loader at all; 81 rows on the 123 are absent from the ledger."),
 ("01_data/01_Pricing/_raw/Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx", "local raw file", "read; read only",
  "LCV (66) + HCV (170)", "2 rows on the 123 absent; 1 peer-number-only row cannot be joined."),
 ("01_data/01_Pricing/_raw/Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx", "local raw file", "read; read only",
  "Isuzu UK (212)", "3 rows on the 123 absent; no loader."),
 ("01_data/01_Pricing/_raw/Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx", "local raw file", "read; read only",
  "Sheet1 (138)", "1 row on the 123 absent; no loader."),
 ("01_data/00_derived/price_observations.parquet", "ledger", "read; read only", "6,597 rows, 21 columns",
  "1,246 PNs; 34 of the 123 carry any row."),
 ("04_tools/aftermarket_intelligence/state/crossref_graded.csv", "graded crossref", "read; read only",
  "7,163 edges", "the Eucon edges are graded doubtful on Eucon alone."),
 ("01_data/00_derived/pn_supersession_map.csv", "supersession map", "read; read only", "925 pairs",
  "6 pairs touch the 123."),
 ("01_data/00_derived/pricing_pr00_ie40.parquet", "price list", "read; read only", "part_number -> newest_pn",
  "90,823 supersession pairs; 191 relations touch the 123."),
 ("01_data/91_build/_tmp_eucon_coverage_20260924.py", "existing probe", "read; reused",
  "coverage probe", "its crossref pair set and coverage method reused."),
 ("01_data/91_build/_tmp_eucon_prices_20260924.py", "existing probe", "read; reused",
  "price probe", "its documented loader rules reused: Currency (RRP) gate and RRP > 2.34."),
 ("01_data/91_build/_tmp_eucon_newmat_20260924.py", "existing probe", "read; reused",
  "Additional Part Numbers probe", "its Additional Part Numbers test reused."),
 ("01_data/91_build/_tmp_eucon_survey_crossref_20260924.py", "existing probe", "read; reused",
  "survey crossref probe", "its survey-as-crossref check reused."),
 ("01_data/91_build/_tmp_supersession_lift_20260924.py", "existing probe", "read; reused",
  "supersession lift probe", "its newest_pn chain test reused."),
]
pd.DataFrame(ROWS, columns=["source", "kind", "status", "what", "outcome"]).to_csv(
    OUT / "tried.csv", index=False, encoding="utf-8")

# ---- status.json -----------------------------------------------------------
status = dict(
 agent="D",
 job="mine what we already hold - no new scraping, no network calls at all",
 read_only_on="everything outside _u26/D",
 raw_files_read=7,
 rows_examined=9772 + 13314 - 5081,   # xlsx/survey rows + raw txt, the xlsx counted once
 rows_examined_note="9,772 rows across the six xlsx/survey files, plus 13,314 rows in the raw text export",
 rows_linked_to_123=1658,
 distinct_raw_observations_on_123=1203,
 observations_missing=int(len(mo)),
 reasons_by_count=mo.why_missing.value_counts().to_dict(),
 missing_by_file=mo.groupby("raw_file").size().to_dict(),
 missing_by_family=mo.groupby("family").size().to_dict(),
 missing_distinct_pns=int(mo.part_no.nunique()),
 supersessions_found=dict(
   map_rows=sup1["map_pairs"],
   price_list_chain_pairs=sup1["chain_pairs"],
   worklist_pns_in_supersession_graph=sup1["worklist_pns_in_map"],
   empty_worklist_pns=len(empty),
   empty_pns_unlocked_by_a_successor=sup2["empty_unlocked"],
   pairs=[["5876100310", "1876102890"], ["5876150531", "5876150530"],
          ["8978279600", "8978279601"], ["8983282071", "8983282070"]],
   file="01_data/00_derived/pricing_pr00_ie40.parquet (part_number -> newest_pn) and 01_data/00_derived/pn_supersession_map.csv",
   eucon_column="Supersession Info ID (code 0-3) in Eucon_March.xlsx/RRP MODE and in the raw txt export; a code, not a successor part number",
 ),
 portugal_2025_online=dict(
   file="01_data/Fresh list_Export_28072025_0932.txt (the raw export behind Eucon_Online28072025.xlsx)",
   pt_rows_in_file=int(2589),
   pt_rows_with_a_competitor_price=265,
   pt_competitor_rows=100,
   of_which_on_the_123=27,
   already_in_ledger=27,
   missing=0,
   note="all 27 Portugal rows are already in the ledger as eucon_online_2025 price_type aftermarket_rrp; the xlsx carries only 100 of the 265 Portugal priced rows",
 ),
 worklist_123=dict(
   total=len(wpn),
   with_any_ledger_row=len(wpn & led_all),
   with_any_eucon_row=len(wpn & eucon_pns),
   still_empty=len(empty),
   empty_unlocked_by_supersession=sup2["empty_unlocked"],
 ),
 second_generation=dict(
   rows_carrying_a_second_generation_number=58,
   distinct_pns=8,
   note="'Additional Part Numbers' in Eucon_Online28072025.xlsx holds a second-generation Isuzu number with its own RRP; the ledger keys only on the searched number, so a search on the second number finds nothing",
 ),
 could_not_do=[
   "no new scraping: work package D is read-only on files already on disk",
   "the 89 empty numbers need external sources (work packages A/B/C); this package cannot fill them",
   "the Eucon Supersession Info ID is a code, not a part number, so it cannot be turned into an old->new map",
   "no Portugal 2025 file separate from the raw text export was found; the export is where the 27 rows live",
 ],
 withdrawn=[
   "an earlier version of missing_observations.csv claimed 136 competitor rows were lost between the raw export and the xlsx. Checked key by key (PN, brand, competitor number, country, price): both files carry the same 217 competitor-priced rows for the 123, and all 27 Portugal rows are in the ledger. That claim is withdrawn.",
 ],
)
json.dump(status, open(OUT / "status.json", "w"), indent=2)
print(json.dumps({k: status[k] for k in ["observations_missing", "reasons_by_count",
                                         "worklist_123", "second_generation"]}, indent=2))
