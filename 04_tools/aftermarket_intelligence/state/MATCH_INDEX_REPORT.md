# Match index build report

Built 2026-09-24T14:26:13+00:00 by `04_tools/aftermarket_intelligence/build_match_index.py`

One row = our part number x competitor brand and number x source file x source date.

- ranked list: 16511 lines; 57 are not parts (lubricant, tool, fee) and carry EUR 217,898 of billed value
- Eucon crossref 2026-03: 822 rows, 45 Isuzu numbers, 432 competitor numbers
- Eucon Online 2025-07: 5081 rows. Two price columns, different meanings: 'RRP' + a declared currency is a real competitor price on 904 rows (18%), covering 59 of 88 part numbers. 'OE RRP' is a price for OUR part number on 4652 rows (92%) - loaded as MATCH rows with no competitor price (RULE 1).
  - distinct Isuzu numbers 88; competitor numbers 2204; brand+number pairs 2322
- Eucon March online 2024-03: 894 rows, 42 Isuzu numbers, 278 competitor numbers, 894 priced
- Eucon March RRP 2024-03: 552 rows, 97 Isuzu numbers, our-number RRP only
- Eucon UK IAM survey [LCV]: 66 rows
- Eucon UK IAM survey [HCV]: 170 rows
- Isuzu genuine to BVP (our OWN cheaper line, not a rival): 544 rows, 431 Isuzu numbers, 356 BVP numbers
- peer-maker map (the CARRIER's own number, not an aftermarket rival): 329 rows, 120 Isuzu numbers, 123 peer numbers, 41 NOT COMPARABLE excluded
- KS shop listings: 0 shop SKU tokens added as searchable objects

## Match index
- rows: 7701
- distinct Isuzu numbers matched: 647
- distinct competitor numbers: 3197
- distinct competitor brands: 537
- rows carrying a usable competitor price: 1694 (22.0%)
- competitor numbers under more than one brand (RULE 2 flag): 183
- Isuzu numbers still with no competitor number: 16109 of 16511

## Tier A reach, graded
(price_now = a real competitor price exists today; rival_number_no_price = a rival's number exists but no price; inside_the_brand_only = only our own value line or our own number; peer_number_only = only a peer CARRIER's own number, which is not an aftermarket rival; none = nothing to search with)
- inside_the_brand_only: 57 parts, EUR 1,783,251 (8.4% of Tier A)
- none: 342 parts, EUR 13,543,552 (63.5% of Tier A)
- price_now: 77 parts, EUR 5,628,518 (26.4% of Tier A)
- rival_number_no_price: 15 parts, EUR 357,204 (1.7% of Tier A)

## Whole book: 402 of 16511 parts carry SOME number (rival, our own, or a peer carrier), EUR 8,897,806 (25.7% of billed). Parts carrying an actual RIVAL number: 181.

## Corrections to the 2026-09-24 state note
- The note said 4,652 rows in the July file carried our own list price. Wrong. 4,652 rows carry 'OE RRP', a price for our part number that is NOT our list (2.46x-3.14x our list on the 8 numbers where both exist) and is NOT an aftermarket price either. What it is has not been established.
- The note said the mislabelled rows were worth EUR 3.70M. There is no such figure in the file. 3.70M was the billed value of all 88 part numbers; the EUR 3.70M in the 2024 RRP sheet is a different figure entirely.
- The note said the ranked list had duplicate part numbers. It does not: 16,511 rows, 16,511 distinct numbers. The duplicate was in the PRICE LIST (165,366 rows, 165,366 distinct numbers) and was a different thing.
- Three of the four 'defects' in that note did not survive checking. The brand variants are real (108 numbers under two spellings, mostly 'BOSCH' vs 'KGK (BOSCH)' and 'GMB' vs 'GMB OCEANIA').
