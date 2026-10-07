# Work package D — mine what we already hold

No new scraping, no network call. Read-only on everything outside this folder.

## Files

| File | What |
|---|---|
| `missing_observations.csv` | Every raw observation on the 123 worklist numbers that is NOT in the ledger, with a specific why-missing code and the evidence for it. |
| `supersession_map.csv` | For all 123 numbers: the number each supersedes into, and the older numbers that supersede into it. Names the source file per row and says whether the related number already carries a ledger row or a raw observation. |
| `tried.csv` | Every file and probe touched, what it was, and what it returned. |
| `status.json` | Counts: files read, rows examined, observations missing, reasons by count, supersessions found. |

Working scripts: `_d_mine.py`, `_d_refine.py`, `_d_add2.py`, `_d_consolidate.py`, `_d_super.py`, `_d_super2.py`, `_d_supmap.py`, `_d_final.py`.
Intermediate: `_counts.json`, `_sup_counts.json`, `_sup_counts2.json`, `_supersession_gain.csv`, `_supersession_reach.csv`.

## Why-missing codes

| Code | Meaning |
|---|---|
| `NO_COMPETITOR_PRICE_ON_THE_ROW` | The row states no competitor price (RRP blank). It does state `OE RRP` for our own number, which `build_price_ledger.py` is not allowed to load. |
| `SECOND_GENERATION_NUMBER_NOT_A_LEDGER_KEY` | The row the ledger already holds also carries a second-generation Isuzu number in `Additional Part Numbers`, with its own RRP. The ledger keys the row on the searched number alone, so a search on the second number finds nothing. |
| `DUPLICATE_NOT_IN_LEDGER` | The pair is in the raw file, but the ledger holds it under a different loader or as a median, so it is not missing — it was counted twice by the naive compare. |
| `FILE_SHEET_NEVER_LOADED` | The sheet has no loader in `build_price_ledger.py` at all (`Eucon_March.xlsx` / `RRP MODE`, 552 rows). |
| `FILE_NEVER_LOADED` | The raw survey file has no loader. |
| `LOADER_DROPS_MATCHING_LEVEL` | `Eucon_March.xlsx` / `Online 15032024`: `Matching Level` is `Very Low` or `Unknown Part`, and the loader keeps only `Medium`. |

## Reused rather than rewritten

`_tmp_eucon_coverage_20260924.py`, `_tmp_eucon_prices_20260924.py`, `_tmp_eucon_newmat_20260924.py`,
`_tmp_eucon_survey_crossref_20260924.py`, `_tmp_supersession_lift_20260924.py` — read first, and their
documented rules (Currency (RRP) gate, RRP > 2.34, `EUCON_MARCH_MATCH_OK`, the `newest_pn` chain,
the `Additional Part Numbers` test) are the rules used here. No new parser was written.

## Withdrawn

An earlier version of `missing_observations.csv` claimed 136 competitor rows were lost between the
raw text export and the xlsx. Checked key by key (PN, brand, competitor number, country, price):
both files carry the same 217 competitor-priced rows for the 123, and all 27 Portugal rows are
already in the ledger. That claim is withdrawn.
