# Competitor-to-list ratio — model and back-test (task card 4.1)

Built 2026-09-24T16:46:25+00:00 by `04_tools/aftermarket_intelligence/build_ratio_model.py`

Every error figure is out-of-sample, one part number held out at a time. The model is only refitted on parts it has not seen.

- priced rival edges (our own line, our own number, peer carrier removed): 1418
- price types left: {'online_median': 800, 'online_retail': 521, 'survey_workshop': 97}
- converted to EUR: 97 rows (GBP at ECB 2023 average, 1 GBP = EUR 1.149707)
- VAT status per price type (blank = not recorded): {'online_median': {'not recorded': 800}, 'online_retail': {'not recorded': 521}, 'survey_workshop': {'excl': 97}}
- with a list price on both sides: 1417 edges, 93 part numbers
- observations (part number x price type): 123
- by price type: {'online_median': 44, 'online_retail': 42, 'survey_workshop': 37}
- clusters among modelled parts: 74; parts sharing a cluster with another modelled part: 31

## out-of-sample error, by price type
Miss is a factor: x1.25 means the prediction was 25% too high OR the truth 25% higher than predicted. 'Constant' = one median ratio for every part, same hold-out.
### online_median
- hold-out by part (44 parts): typical miss x1.48 (off by 48%); 9 in 10 within x2.75 (off by 175%); constant typical miss x1.50 (off by 50%); inside 10-90 band 61%; old measure median 36.3%
- hold-out by cluster (44 parts): typical miss x1.57 (off by 57%); 9 in 10 within x2.75 (off by 175%); constant typical miss x1.52 (off by 52%); inside 10-90 band 61%; old measure median 36.6%
- where the cluster-hold-out answer came from: {'whole price type': 20, 'category': 15, 'category x price class': 9}
### online_retail
- hold-out by part (42 parts): typical miss x1.38 (off by 38%); 9 in 10 within x3.67 (off by 267%); constant typical miss x1.45 (off by 45%); inside 10-90 band 60%; old measure median 28.8%
- hold-out by cluster (42 parts): typical miss x1.38 (off by 38%); 9 in 10 within x3.73 (off by 273%); constant typical miss x1.45 (off by 45%); inside 10-90 band 64%; old measure median 29.7%
- where the cluster-hold-out answer came from: {'whole price type': 31, 'category': 7, 'category x price class': 4}
### survey_workshop
- hold-out by part (37 parts): typical miss x1.43 (off by 43%); 9 in 10 within x2.44 (off by 144%); constant typical miss x1.36 (off by 36%); inside 10-90 band 68%; old measure median 35.3%
- hold-out by cluster (37 parts): typical miss x1.36 (off by 36%); 9 in 10 within x2.44 (off by 144%); constant typical miss x1.36 (off by 36%); inside 10-90 band 68%; old measure median 32.7%
- where the cluster-hold-out answer came from: {'whole price type': 20, 'category': 13, 'category x price class': 4}

## does the model beat one constant? (cluster hold-out, all price types)
- identical to the constant (the model fell back to it or matched it): 58% of parts; model closer 20%; constant closer 22%
- typical miss, typical miss model x1.46 (off by 46%) vs constant x1.48 (off by 48%)

## error by price band, against where the long tail sits (tier C: 14211 parts, 14153 with a list price)
| our list band | long-tail share | tested parts (cluster hold-out) | typical miss |
|---|---|---|---|
| <10 | 38% | 9 | x1.51 (off by 51%) |
| 10-25 | 20% | 19 | x1.47 (off by 47%) |
| 25-50 | 14% | 13 | x1.25 (off by 25%) |
| 50-100 | 12% | 30 | x1.54 (off by 54%) |
| 100-250 | 11% | 31 | x1.48 (off by 48%) |
| 250-1000 | 5% | 19 | x1.35 (off by 35%) |
| >1000 | 0% | 2 | x1.70 (off by 70%) |
- share of the long tail sitting in a band with 10+ tested parts: 62%

## check: pack-size mismatch
- rows tested (parts with 3+ rival prices in one price type): 1346
- rows within ~5% of 2x or 0.5x their part's median: 43; same-width windows just below and above (~1.7x and ~2.3x): 85 and 23
- read: a clear bump at 2x over its neighbours means per-piece vs per-set confusion. No bump says nothing either way.

## is the category model actually a category model? (cluster hold-out)
- whole price type: 71 of 123 (58%)
- category: 35 of 123 (28%)
- category x price class: 17 of 123 (14%)

## fitted cells with 3 or more parts: 16

## How to use this, honestly
NOT for per-part estimates of unmatched parts. At most, quote the observed range per price type as a description of matched parts. The ratio is what a competitor price TENDS to be, as a multiple of our list, in that category and price band. It is not a price. A cell with two parts in it is two parts, not a market.

## What would make it wrong
- Time: rival prices are 2023-2025; our list is today's. A list price change since then moves every ratio.
- VAT: not recorded for the online price types, so whether they include VAT is unknown; DE and NO carry different VAT rates.
- One price type fitted across a country mix: EUcon's online medians span five countries.
- Pack-size differences: a pad set per axle against per wheel is a factor of two, and it shows up as a whole-number multiple in the ratio distribution.
- A category whose competitors are all premium brands, against one where budget brands set the median.
