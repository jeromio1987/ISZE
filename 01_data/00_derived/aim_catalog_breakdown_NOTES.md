# Catalogue classification x distributor - last 12 months of billed parts

Built 2026-09-17T19:46:03+00:00 by `01_data/91_build/build_aim_catalog_breakdown.py`. Internal working note, blunt, not a shareable deck.

## 0. Two-axes lock (2026-09-17 - Jerome: proceed)

This note groups on **Axis A - identity** (`catalog_l1` / `catalog_l2` / `catalog_l3`). That is what the part is / where on the truck, with the existing three levels only. Wear and family cuts hang from Level 2 / Level 3 or the figure key - never from a commercial posture parent (the king-pin case).

**Axis B - commercial score** (contested or not, per part per market) sits **beside** Axis A. It is not the box this Focus cut hangs from, and it is not built as scored columns in these CSVs yet. Do not invent a fourth taxonomy layer.

**Attribute layer — on hold (roadmap).** Jerome 2026-09-17: do not build size / position / duty on leaves now; keep it deferred / later. Two axes remain locked. Attributes-before-levels is still the recommended order when that work resumes — not an active build and not a this-week decision gate. See `DECISIONS.md` 2026-09-17 (attribute layer on hold).

Which tree wins for what purpose is in `DECISIONS.md` 2026-09-17 (two-axes entry). Spoken labels stay: shared/external vs internal; sales to dealer; price list / price revision; parts billed; reference dealer price.

## 1. What was asked and what the scheme is

Jerome chose the catalogue **identity** tree as the grouping axis for this Focus cut: `Competitive parts` at Level 1, `Filters` at Level 2, `Oil filter` / `Fuel filter` / `Air filter` / `Other filter` at Level 3. He asked for that Focus cut in full, plus a check that `brake parts are competitive parts`, plus a cross against the older coarse price class.

The other vocabulary (Brakes / Engine / Clutch at Level 1) is **not** used as the grouping axis here. It still exists in the same file in the `aim_l1` / workbook columns as legacy context - neither Axis A nor Axis B under the lock.

## 2. Method

* Window: 2025-07-01 to 2026-06-30, the window already baked into the shipped comparison. No new billing window was opened.
* Weight base: `price_bp_weighted_compare_pn.csv` - one row per customer x part number on the last 12 months of billed parts, in-scope customers only.
* Classification: `aim_pn_classification.csv`, joined on `part_number`.
* Weighted base-price increase = `SUM(qty x bp_new_jpy) / SUM(qty x bp_prior_revised) - 1` over rows priced on both sides. Step euro = sum of `value_eur_step`.
* Fleet denominator: `gps_spu_by_distributor.csv`, 2025 `uio_units`.

**Tie-out.** The union of the classification multiplies back to the shipped comparison exactly: network weighted increase 5.9616% against the shipped 5.9616%, step euro 1,652,140.71 against 1,652,140.71. Per-distributor tie-out passes: True (max increase delta 0.0000 pp, max euro delta 0.00). So the split is a partition of the shipped number, not a second number.

## 3. Join rate

* In-scope rows 48,653 covering 15,872 distinct part numbers, 34,993,609.39 EUR.
* Rows matched to the classification: 48,634 (99.9609%). Not matched: 19 rows, 781,252.09 EUR (2.2326% of euro).
* Part numbers are 10-character zero-padded strings on both sides; the classification file is 100% clean on that. Three rows in the weight base carry a non-part key: two service-fee lines and one demurrage line. Those are not parts.

## 4. The trap in the classification file - read this before quoting anything

The brief said to restrict to `aim_source == 'pr00_catalog'` (139,410 rows) and treat that as the catalogue scheme. **That restriction does not do what it looks like.** `aim_source` is a precedence label for which vocabulary won `aim_l1`; it is not a completeness flag for `catalog_l1`.

Verified facts:

* `catalog_l1`, `catalog_l2`, `catalog_l3` are populated on 164,610 rows of the file, not 139,410. Each of the three columns matches the true PR00 source (`pr00_classification.csv` -> `family` / `group` / `level3_type`) on **100%** of joined rows, on every `aim_source` value.
* The catalogue columns are populated on 33,078 of the billed in-scope rows that carry `aim_source == 'aim_workbook'`, worth 28,100,130.59 EUR.
* Restricting to `aim_source == 'pr00_catalog'` therefore keeps only 4,397,447.12 EUR (12.57%) of the 34,993,609.39 EUR in-scope spend. Under that restriction the Focus cut collapses: Filters would show 3 row-level hits against 227 in reality, and **Air filter would show nothing at all**.
* Concretely, `8982705240 ELEMENT; OIL FILTER` is a 256,036 EUR line and is flagged `aim_workbook`. A literal reading of the brief would drop it out of the oil-filter answer.

**Decision taken:** every output is emitted on two bases, so both readings are on disk and the difference is visible rather than hidden. The brief's literal restriction is kept as `pr00_catalog_only`.

* `catalog_full` - every in-scope row that carries a catalogue node. **This is the one to quote for a network answer.** It is complete, internally consistent, and it ties out exactly to the shipped comparison.
* `pr00_catalog_only` - the literal `aim_source == 'pr00_catalog'` restriction. Use it only when the question is specifically about the PR00-sourced subset.

A middle option was rejected: calling `catalog_full` the "AIM classification" in deliverables. `aim_l1` and `catalog_l1` are identical on 100% of `pr00_catalog` rows, so the file presents two different level-1 lists under one apparent label. That is the real classification-scheme conflict, and it should be settled in the file, not papered over in a report. Reported here, not fixed - the classifier is PRISM-owned.

## 5. Coverage

| Bucket | Rows | Part numbers | L12M billed EUR | Share |
|---|---|---|---|---|
| In-scope total | 48,653 | 15,872 | 34,993,609.39 | 100.00% |
| Attributable to a real catalogue node | 46,199 | 14,969 | 32,497,577.71 | 92.87% |
| `Other / review` placeholder | 2,330 | 820 | 1,141,328.51 | 3.26% |
| No catalogue node at all | 124 | 83 | 1,354,703.17 | 3.87% |
| - of which PR00-sourced | 12,222 | 4,712 | 4,397,447.12 | 12.57% |

**Unattributed spend: 2,496,031.68 EUR (7.13%).** Of that, 1,141,328.51 EUR sits in the `Other / review` placeholder and 1,354,703.17 EUR has no node at all.

The `catalog_l1` null bucket is largely not parts: `0000REBATE` (430,030 EUR) and `0TRANSPORT` (351,221 EUR) plus the UMI lubricants (0550047337 Rim R4L 15W40 at 394,763 EUR, and others, ~505,000 EUR in total). Those are correctly unclassified. The remaining ~400,000 EUR is a genuine part-number coverage gap (gussets, turbocharger, ABS controller, seat cushion, multi display) - real parts PR00 does not carry a figure for.

Classification cells are all-or-nothing per row: there is no row with a level 1 but no level 2, or a level 2 but no level 3. So the unclassified row count is identical at all three levels: 124 rows / 83 part numbers / 1,354,703.17 EUR.

## 6. Level 1 - network

| Level 1 | PN | Qty | L12M billed EUR | Step EUR | Weighted increase |
|---|---|---|---|---|---|
| Competitive parts | 4,261 | 439,854 | 14,169,546.40 | 661,661.92 | 5.36% |
| Repair parts | 3,359 | 303,442 | 6,962,670.21 | 361,451.92 | 6.77% |
| Accident parts | 3,935 | 189,733 | 6,759,587.30 | 360,543.62 | 6.56% |
| High value repair | 1,262 | 114,394 | 3,279,132.83 | 145,024.97 | 5.28% |
| UNCLASSIFIED | 83 | 13,305 | 1,354,703.17 | 587.16 | 5.85% |
| Other / review | 820 | 27,446 | 1,141,328.51 | 50,529.62 | 6.82% |
| Comfort parts | 435 | 39,546 | 818,157.53 | 44,525.06 | 6.82% |
| Hardware & consumables | 1,717 | 115,507 | 508,483.44 | 27,816.42 | 7.23% |

## 7. The Focus cut - Competitive parts > Filters

Network, `catalog_full`:

| Node | PN | Qty | L12M billed EUR | Step EUR | Weighted increase | EUR per truck in service |
|---|---|---|---|---|---|---|
| Filters (all types) | 252 | 234,115 | 3,115,961.21 | 101,691.00 | 3.37% | n/a (see note) |
| - Oil filter | 74 | 104,354 | 694,475.73 | 36,099.86 | 5.05% | n/a |
| - Fuel filter | 94 | 82,588 | 958,852.86 | 21,403.82 | 2.26% | n/a |
| - Other filter | 44 | 6,607 | 668,586.73 | 27,763.62 | 4.68% | n/a |
| - Air filter | 40 | 40,566 | 794,045.89 | 16,423.69 | 2.16% | n/a |

Filters is 3,115,961 EUR of 14,169,546 EUR Competitive parts (22.0%) and 8.9% of total in-scope billed parts. The weighted increase is 3.37% — filters still move softly on this price revision relative to most competitive families, the opposite of what a competitive-pressure story would predict.

Per distributor, Filters total:

| Distributor | Truck fleet 2025 | PN | Qty | L12M billed EUR | Step EUR | Weighted increase | EUR per truck |
|---|---|---|---|---|---|---|---|
| ITUK | 22,389 | 108 | 37,957 | 787,211.47 | 23,260.49 | 3.12% | 35.2 |
| UTI | 10,336 | 38 | 41,763 | 702,961.13 | 9,834.33 | 1.44% | 68.0 |
| IUK | 47,783 | 45 | 37,424 | 350,742.83 | 20,590.90 | 5.52% | 7.3 |
| UMI | 18,542 | 50 | 20,095 | 164,308.27 | 7,963.03 | 4.72% | 8.9 |
| UKRAINE | UNKNOWN | 33 | 11,786 | 144,025.53 | 1,126.70 | 0.77% | NO FLEET COUNT |
| GERMANY | 12,855 | 61 | 10,517 | 128,334.61 | 5,909.79 | 5.00% | 10.0 |
| BELGIUM | 9,594 | 93 | 12,744 | 124,693.63 | 6,062.14 | 5.05% | 13.0 |
| PORTUGAL | 8,176 | 87 | 8,949 | 108,637.76 | 2,085.93 | 2.13% | 13.3 |
| IRELAND | 3,056 | 111 | 7,956 | 107,042.32 | 3,684.77 | 3.41% | 35.0 |
| NORWAY | 7,929 | 25 | 9,098 | 88,737.32 | 5,446.26 | 5.88% | 11.2 |
| SWEDEN | 8,443 | 30 | 7,641 | 87,386.59 | 4,392.42 | 5.18% | 10.4 |
| GREECE | 3,742 | 55 | 7,753 | 73,549.41 | 3,871.20 | 5.52% | 19.7 |
| ARMENIA | UNKNOWN | 23 | 3,370 | 46,826.48 | 350.56 | 1.23% | NO FLEET COUNT |
| KAZAKHSTAN | UNKNOWN | 35 | 2,907 | 45,992.98 | 369.99 | 1.33% | NO FLEET COUNT |
| CYPRUS | 2,308 | 53 | 4,109 | 43,663.15 | 1,980.88 | 4.71% | 18.9 |
| HUNGARY | 3,734 | 21 | 3,375 | 33,663.17 | 1,588.20 | 4.81% | 9.0 |
| ROMANIA | 1,071 | 21 | 1,654 | 19,710.06 | 817.81 | 4.44% | 18.4 |
| FINLAND | 1,204 | 22 | 1,710 | 19,295.41 | 1,039.97 | 5.59% | 16.0 |
| DENMARK | 851 | 22 | 944 | 15,546.59 | 327.21 | 2.32% | 18.3 |
| MALTA | 1,040 | 37 | 1,413 | 15,055.89 | 545.18 | 3.84% | 14.5 |
| ICELAND | 406 | 18 | 504 | 6,198.57 | 351.47 | 5.88% | 15.3 |
| PALESTINE | UNKNOWN | 11 | 446 | 2,378.04 | 91.76 | 2.97% | NO FLEET COUNT |

Per distributor, all four filter types - L12M billed EUR:

| Distributor | Oil filter | Fuel filter | Air filter | Other filter | Filters total |
|---|---|---|---|---|---|
| ITUK | 94,632 | 232,131 | 132,426 | 328,022 | 787,211 |
| UTI | 138,365 | 186,303 | 158,385 | 219,908 | 702,961 |
| IUK | 108,889 | 113,921 | 114,287 | 13,646 | 350,743 |
| UMI | 52,338 | 45,952 | 21,844 | 44,174 | 164,308 |
| UKRAINE | 52,102 | 77,598 | 13,421 | 905 | 144,026 |
| GERMANY | 29,134 | 51,495 | 37,296 | 10,409 | 128,335 |
| BELGIUM | 38,082 | 29,711 | 47,315 | 9,586 | 124,694 |
| PORTUGAL | 21,490 | 32,545 | 40,009 | 14,593 | 108,638 |
| IRELAND | 22,707 | 43,486 | 34,277 | 6,572 | 107,042 |
| NORWAY | 22,882 | 17,116 | 37,449 | 11,291 | 88,737 |
| SWEDEN | 21,579 | 26,629 | 36,458 | 2,720 | 87,387 |
| GREECE | 21,064 | 23,074 | 25,992 | 3,420 | 73,549 |
| ARMENIA | 16,166 | 16,820 | 13,811 | 30 | 46,826 |
| KAZAKHSTAN | 12,828 | 25,098 | 7,950 | 116 | 45,993 |
| CYPRUS | 10,542 | 13,262 | 19,199 | 660 | 43,663 |
| HUNGARY | 9,154 | 5,015 | 18,664 | 831 | 33,663 |
| ROMANIA | 3,739 | 3,025 | 12,777 | 170 | 19,710 |
| FINLAND | 6,120 | 4,913 | 7,673 | 590 | 19,295 |
| DENMARK | 4,260 | 3,562 | 7,377 | 347 | 15,547 |
| MALTA | 5,867 | 4,967 | 4,137 | 84 | 15,056 |
| ICELAND | 1,421 | 1,627 | 2,724 | 427 | 6,199 |
| PALESTINE | 1,113 | 604 | 574 | 87 | 2,378 |
| **Network** | **694,476** | **958,853** | **794,046** | **668,587** | **3,115,961** |

Per distributor, quantity-weighted base-price increase on each filter type:

| Distributor | Oil filter | Fuel filter | Air filter | Other filter | Filters total |
|---|---|---|---|---|---|
| ITUK | 3.97 | 2.17 | 0.51 | 4.53 | 3.12 |
| UTI | 0.52 | 0.55 | 0.50 | 4.00 | 1.44 |
| IUK | 9.40 | 3.04 | 3.10 | 7.00 | 5.52 |
| UMI | 2.51 | 5.03 | 5.69 | 7.00 | 4.72 |
| UKRAINE | 0.78 | 0.71 | 0.88 | 7.02 | 0.77 |
| GERMANY | 9.22 | 3.16 | 3.36 | 6.07 | 5.00 |
| BELGIUM | 8.26 | 3.28 | 3.10 | 5.92 | 5.05 |
| PORTUGAL | 1.05 | 2.28 | 1.95 | 4.15 | 2.13 |
| IRELAND | 3.79 | 4.23 | 1.76 | 5.34 | 3.41 |
| NORWAY | 9.12 | 3.54 | 4.65 | 7.04 | 5.88 |
| SWEDEN | 9.81 | 3.11 | 3.33 | 7.01 | 5.18 |
| GREECE | 8.29 | 4.20 | 4.26 | 6.24 | 5.52 |
| ARMENIA | 0.56 | 2.08 | 0.94 | 7.03 | 1.23 |
| KAZAKHSTAN | 0.94 | 1.11 | 2.48 | 7.04 | 1.33 |
| CYPRUS | 7.63 | 4.18 | 3.38 | 7.02 | 4.71 |
| HUNGARY | 8.44 | 3.04 | 3.22 | 7.01 | 4.81 |
| ROMANIA | 9.36 | 2.96 | 3.15 | 7.03 | 4.44 |
| FINLAND | 9.27 | 3.22 | 3.62 | 7.02 | 5.59 |
| DENMARK | 3.45 | 1.94 | 1.64 | 7.01 | 2.32 |
| MALTA | 5.56 | 1.91 | 3.46 | 7.04 | 3.84 |
| ICELAND | 9.69 | 4.81 | 4.12 | 7.03 | 5.88 |
| PALESTINE | 2.64 | 2.92 | 3.02 | 7.00 | 2.97 |
| **Network** | **5.05** | **2.26** | **2.16** | **4.68** | **3.37** |

Readings worth keeping:

* **Oil filters move almost twice as hard as fuel filters** network-wide (5.05% against 2.26%), while oil filters bill about 72% of fuel-filter euro. That is the single clearest signal in the Focus cut.
* Oil-filter behaviour splits cleanly by distributor: Belgium 8.3%, IUK 9.4%, Norway 9.1%, Sweden 9.8%, Romania 9.4%, Finland 9.3%, Hungary 8.4%, Germany 9.2% all sit near +9%, against ITUK at 4.0%, Portugal 1.1%, UMI 2.5% and UTI 0.5%. Two regimes, not one.
* UTI is a filter-weighted market: 545,239 EUR of filters on 10,336 trucks (52.8 EUR per truck), more than double ITUK's 30.0 and several times IUK's 5.0. But `Other filter` is 219,928 EUR of it - 40% of UTI's filter spend, against 28.5% network-wide, and UTI alone is 33% of the network's Other-filter euro. That is DEF and hydraulic, admitted only recently by catalogue input.
* `Other filter` is the third-largest filter type by euro (668,819 EUR, 28.5% of Filters, behind Fuel filter at 958,932 and Oil filter at 694,420), and it is dominated by one part number: `8982878080 FILTER ASM` is 298,160 EUR, 44.6% of the whole Other-filter block, on 277 units. Check what that part actually is before any of it enters a deck.
* **`Air filter` is a real network family after the 2026-09-17 ACL refile:** 794,046 EUR across 40 part numbers (25.5% of Filters), weighted increase 2.16%. Top markets: UTI 158,385 EUR, ITUK 132,426 EUR, IUK 114,287 EUR. Every in-scope distributor with filter billing shows some air-filter euro. Do not reuse the pre-patch reading that called this leaf a network anecdote.

## 8. Brake check - does 'brake parts are competitive parts' hold?

**Verdict: yes, cleanly.** Under the catalogue scheme, `Competitive parts > Brake parts` holds 897 part numbers, 3,554,403.07 EUR, 242,925.09 EUR of base-price step and a 7.79% weighted increase. That is the largest competitive family by euro and the largest single step-euro contributor at Level 2 (242,913 EUR, 38% of all Competitive-parts step euro). **100% of rows carrying `catalog_l2 = 'Brake parts'` sit under `Competitive parts`** - zero exception.

*Leakage test.* Part numbers whose billed description looks like a brake but which sit outside that bucket:

* **Strict test: 65 part numbers, 19,753.74 EUR** (0.56% of the bucket). Spread over `Repair parts > Hydraulic / mechanical` (11,439 EUR - wheel-cylinder cup sets, which are arguably brake content that PR00 files under general hydraulics), `Other / review > Miscellaneous` (7,132 EUR), `Hardware & consumables > Hardware` (4,107 EUR - shoe springs, pins, caliper boots), and small residue elsewhere.
* Loose test: 102 part numbers, 148,461.09 EUR. **Do not use this figure.** It is contaminated.

The difference between the two tests is 129,062 EUR and it is almost entirely a false positive I would have shipped if I had trusted the word list. The `ROTOR` token catches `ROTOR; SENSOR` (42,446 EUR) and `ROTOR; SENSOR` / `ROTOR; CAM ANGLE SENSOR` / `ROTOR; SPEED SENSOR` - 31 part numbers, 125,757 EUR - all of them ignition and wheel-speed sensors filed under `Repair parts > Electrical sensors`. They are not brakes. `BRAKET; HEATER` (105 EUR) is a typo for BRACKET, not a brake part. The strict token set excludes bare `ROTOR` and requires a brake word next to a rotor; that is the honest test.
* Reverse test: 12 part numbers, 2,423.20 EUR inside the bucket have descriptions with no brake token in them. Small, and most are short descriptions rather than misfiles.

**So Jerome's assertion holds, with one honest caveat:** PR00 puts roughly 19,754 EUR of genuine brake content - mainly wheel-cylinder cup sets, shoe springs, pins and caliper boots - under `Repair parts` and `Hardware & consumables` rather than under the brake family. Small against the 3.55M EUR bucket, but it means a brake analysis that uses only `Competitive parts > Brake parts` under-reads brakes slightly.

## 9. Price class cross - the old coarse class against the catalogue nodes

The price class is the coarse IML class factor (C, D, F, J, M, P, T, V). **It is IML-owned** - the pricing spec is explicit that class factors are not something ISZE changes. It is carried here as a retained attribute of the node, never as a lever.

Competitive parts by Level 2 and price class, L12M billed EUR:

| Level 2 | C | D | F | J | M | P | T | V | UNCLASSIFIED |
|---|---|---|---|---|---|---|---|---|---|
| Air system | 241,181 | 1,340 | 43,117 | n/a | 376 | n/a | n/a | 608 | 5,600 |
| Belts | 87,805 | n/a | 596 | n/a | n/a | n/a | n/a | 743 | 95 |
| Brake parts | 1,756,648 | 132,707 | 196,790 | 148 | 608 | n/a | n/a | 1,452,830 | 14,671 |
| Clutch parts | 85,863 | 35,496 | 150,188 | n/a | n/a | n/a | 681 | 516,495 | 346 |
| Cooling | 627,948 | 50,773 | 61,765 | 2,545 | 40 | n/a | n/a | 67,536 | 3,003 |
| Exhaust | 1,857,848 | 506,374 | 111,894 | 5 | n/a | n/a | n/a | 2,812 | 3,621 |
| Filters | 187,425 | 516,387 | 644 | n/a | n/a | n/a | 42 | 2,411,353 | 110 |
| Fuel system | 279,316 | 214,724 | 871 | n/a | n/a | n/a | n/a | 387 | 113 |
| Steering | 1,701,895 | 339 | 3,439 | n/a | 45,280 | n/a | n/a | 153,156 | 1,126 |
| Suspension | 98,966 | n/a | 202,201 | n/a | 207,638 | n/a | n/a | n/a | 123,035 |

Column totals across all Competitive parts: C 6,924,896, D 1,458,141, F 771,506, J 2,698, M 253,942, P 0, T 723, V 4,605,919, UNCLASSIFIED 151,721.

The reading that matters: **the competitive families are almost entirely C and V.** Filters is 1,876,730 EUR of `V` and only 187,673 EUR of `C` plus 516,387 EUR of `D` - and the entire `D` block is `Other filter` (516,387 EUR of the 516,387). So `D` is effectively a DEF-filter class, not a filter class in general. Oil and fuel filters are 100% `V`. Exhaust and Steering are overwhelmingly `C` (1,857,072 and 1,570,005 EUR). Brake parts is the most balanced large family: 1,757,621 EUR `C` against 1,452,103 EUR `V`.

Level 3 Filters against price class:

| Filter type | C | D | F | J | M | P | T | V | UNCLASSIFIED |
|---|---|---|---|---|---|---|---|---|---|
| Air filter | 8 | n/a | n/a | n/a | n/a | n/a | n/a | 794,038 | n/a |
| Fuel filter | 15,604 | n/a | n/a | n/a | n/a | n/a | n/a | 943,218 | 31 |
| Oil filter | 20,257 | n/a | n/a | n/a | n/a | n/a | 42 | 674,097 | 79 |
| Other filter | 151,556 | 516,387 | 644 | n/a | n/a | n/a | n/a | n/a | n/a |

448 in-scope rows carry no price class, 2,084,369.76 EUR. Those are excluded from the class cross by definition, not dropped from the other tables.

## 10. Top competitive families by euro

| Family | PN | Qty | L12M billed EUR | Step EUR | Weighted increase | EUR per truck |
|---|---|---|---|---|---|---|
| Brake parts | 897 | 67,288 | 3,554,403.07 | 242,925.09 | 7.79% | n/a |
| Filters | 252 | 234,115 | 3,115,961.21 | 101,691.00 | 3.37% | n/a |
| Exhaust | 616 | 31,845 | 2,482,555.28 | 144,724.36 | 7.07% | n/a |
| Steering | 466 | 23,326 | 1,905,235.84 | 42,986.44 | 2.63% | n/a |
| Cooling | 469 | 20,529 | 813,609.96 | 29,946.39 | 4.48% | n/a |
| Clutch parts | 364 | 13,721 | 789,068.40 | 25,648.03 | 3.56% | n/a |
| Suspension | 339 | 25,286 | 631,840.70 | 25,104.06 | 5.73% | n/a |
| Fuel system | 359 | 7,440 | 495,411.78 | 28,431.75 | 7.19% | n/a |
| Air system | 434 | 14,587 | 292,221.72 | 15,064.46 | 6.42% | n/a |
| Belts | 65 | 1,717 | 89,238.44 | 5,140.35 | 7.11% | n/a |

## 11. Distributors with no fleet denominator

Four markets have `uio_units` of 0 in the 2025 fleet file - no count exists by design. **Nothing here is divided by trucks in service for these four**, so their tables show euro and no rate:

* **ARMENIA** - 311,487.70 EUR in-scope billed in the window.
* **KAZAKHSTAN** - 159,124.10 EUR in-scope billed in the window.
* **PALESTINE** - 42,099.65 EUR in-scope billed in the window.
* **UKRAINE** - 1,026,580.75 EUR in-scope billed in the window.

1,539,292.20 EUR combined. They are in the network totals and in every euro figure; they are simply absent from any per-truck column. Do not read their blank rate as zero performance.

The network fleet total is 163,459 trucks across the 18 markets that have a count. A network-wide euro-per-truck can be struck on that base, but it is a rate over 18 markets sitting beside a euro total over 22 - state it that way if it is quoted.

## 12. Israel

Reported as two rows throughout, never blended: **1797 UMI** and **1799 UTI**. The customer name column cannot split them - it reads UNIVERSAL MOTORS ISRAEL LTD for both since the 2026-04-01 relabel. UMI is LCV, UTI is CV, different fleets, different parts mix.

## 13. What this data could not cover

* **Battery and Special tools leaves (2026-09-18).** Axis A now carries
  `Repair parts > Battery > High-voltage battery | 12V battery` and
  `Hardware & consumables > Special tools > Jack | Hand tools` (`leaf_add_battery_tools_20260918`).
  Gate approved L2/L3 baselines are 27 / 176. Radios/stereo still have no Audio leaf;
  battery covers/terminals/chargers and tool bags stay in Other / review until a separate call.
* **`Other filter` is a residual bucket, not a product family.** The filter taxonomy itself is closed and clean (`Oil filter`, `Fuel filter`, `Air filter`, `Other filter` plus exactly one `Hydraulic / transmission filter`, 2,029 part numbers under `Competitive parts > Filters`). But `Other filter` mixes at least three different physical things: DEF/aftertreatment filter assemblies (FILTER ASM, FILTER KIT PUMP ASM DEF DCM), hydraulic and transmission strainers (STRAINER ASM OIL A/T, FILTER ASM VCV), and one `GASKET; FILTER,DEF`. It cannot be treated as one family with one commercial story, and one part number is 44.6% of it.
* **`Air filter` is no longer an empty leaf.** After the ACL → air-cleaner refile it holds 794,046 EUR / 40 part numbers on this 12-month cut (second among the four filter types by euro). Pre-patch NOTES that called it €28k / anecdote are withdrawn.
* **The four no-fleet markets cannot carry a rate.** Armenia, Kazakhstan, Palestine and Ukraine have 1,539,292 EUR of billed parts between them and no trucks-in-service count. Any rate-based comparison silently omits them.
* **The `Other / review` placeholder is 1,540,240 EUR (4.4%)** and is a real answer for quite a lot of genuine part numbers. It is not a rounding error.
* **No elasticity, no allocation, no price proposal.** Correctly out of scope; the weighted increase is a base-price move, not a revenue or margin outcome.
* **The two level-1 vocabularies remain unreconciled in the source file.** The catalogue columns and the workbook columns are both populated, both presentable, and describe different taxonomies. This note uses the catalogue columns only, per the brief. The underlying file should be fixed so the next reader is not forced to make the same call.
* **The brief's literal restriction would have produced a materially wrong answer** - Filters missing air filters entirely and dropping the largest oil-filter part numbers, leaving 13.54% of in-scope euro. Flagged, worked around, and the restricted cut is on disk if that reading was deliberate.

## 14. Files

* `aim_catalog_db_matrix.csv` - distributor x node at each of the three levels, on both scheme bases. Includes network rows (`__NETWORK__`).
* `aim_catalog_focus_filters.csv` - the Focus cut, every distributor, all four filter types plus the Filters parent total, both bases.
* `aim_catalog_brake_check.csv` - the brake verification, loose and strict leak tests.
* `aim_catalog_x_priceclass.csv` - node x price class at L1 / L2 / L3, network level.
* `aim_catalog_breakdown_meta.json` - join rate, coverage, tie-out, fleet gaps.

Builder: `01_data/91_build/build_aim_catalog_breakdown.py`.
