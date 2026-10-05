# Cross-reference graph — build report (task card 2.1)

Built 2026-09-24T16:44:41+00:00 by `04_tools/aftermarket_intelligence/build_crossref_graph.py`

Acceptance rule for 2.1: every edge carries a source and a date, or it is refused.

- match index rows read: 7701
- edges refused for a missing source or date: 0
- edges written: 7443 (parquet + csv)
- distinct Isuzu numbers on an edge: 647
- distinct competitor numbers: 3023
- of those, already carrying a price: 734

- rival edges only (our own BVP line and the peer-carrier map excluded): 6455
- competitor numbers, written form as the key: 2627
- competitor numbers, spelling normalised      : 2461
- numbers written in more than one form       : 166
- evidence seed rows written: 2461
  - 1 source FILE only      : 2004
  - 2 source FILES or more  : 457
  - 3 source FILES or more  : 168
  - INDEPENDENT witnesses (source families, own catalogue and peer map count 0):
      1 witness(es): 2439
      2 witness(es): 22
  - already carry a price: 637

### check: brand written two ways
- brand pairs where one name contains the other: 36; of which sharing a competitor number (near-certain alias): 24
- listed in check_brand_alias_candidates.csv - NOT merged; merging needs sign-off

### check: matches a newer Eucon file no longer lists (same Isuzu part still covered)
- such matches: 981 (distinct Isuzu parts 41) - check_eucon_dropped_matches.csv. Not removed: absence may be a narrower cut, not a withdrawal. Put five of them into the next manual check.

### all rival numbers
- competitor numbers: 2461
- Isuzu part numbers reached: 131 of 16511
- billed value of those parts: EUR 5,639,298
- of which Tier A: 74 parts, EUR 5,172,315

### 2+ sources
- competitor numbers: 457
- Isuzu part numbers reached: 69 of 16511
- billed value of those parts: EUR 4,085,099
- of which Tier A: 46 parts, EUR 3,855,475

### 3+ sources
- competitor numbers: 168
- Isuzu part numbers reached: 43 of 16511
- billed value of those parts: EUR 3,241,483
- of which Tier A: 33 parts, EUR 3,167,267

### 2+ INDEPENDENT witnesses
- competitor numbers: 22
- Isuzu part numbers reached: 18 of 16511
- billed value of those parts: EUR 1,256,258
- of which Tier A: 14 parts, EUR 1,255,123

### what is actually worth fetching
- 2+ source numbers with NO price yet: 43
- they reach 22 Isuzu parts, EUR 911,916 billed; Tier A 13 parts, EUR 818,668

## Files
- `crossref_edges.parquet` / `.csv` — the graph, one edge per Isuzu number x competitor number x source x country
- `evidence_seed.csv` — the fetch list, ranked by independent confirmation

## Caution
`n_sources` counts distinct FILES, not independent verifications. `n_witnesses` counts SOURCE FAMILIES: all Eucon catalogue files are one witness; our own catalogue and the peer-carrier map count zero. The UK workshop survey is also a Eucon product; it is counted as its own family because it was collected by survey, not re-cut from the catalogue. That is a judgement, not a proven fact. Rank on `n_witnesses`.
