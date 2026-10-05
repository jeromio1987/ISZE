# Pattern-part price check, 50 largest body parts (4 Oct 2026)

Internal working note. Read-only: nothing was loaded into the price ledger, and the paper, the price files, the workbook and every dashboard are untouched. No commit, no push, no mail.

## Verdict

**The data cannot show that the body share of the recovery is safe, and it cannot show that it is wrong.** Pattern (non-Isuzu) prices were found for 11 of the 50 parts (EUR 325,904 of parts billed, 17.7%), but 10 of those 11 were already carved out of the paper's recovery, so the new finding changes the EUR 143,596 by only about EUR 1,785 (1.2%). For the other 37 parts (79.3% of the EUR 1.84M) the four shops we are cleared to use show nothing, and they are weakest exactly where these parts sit (see "What the search could and could not see"). "Nothing found" is not proof that no pattern part exists.

## 1. Result in numbers

Base: segment body in `room_to_raise_by_part_2026-10-02.csv`, sorted by parts billed (July 2025 to June 2026). Top 50 = EUR 1,843,857, which is 39.7% of EUR 4,639,124 body parts billed.

| | Parts | Parts billed (EUR) | Share of the 50 |
|---|---:|---:|---:|
| Pattern price found, with fit shown on a saved page | 11 | 325,904 | 17.7% |
| plus evidence only in local Eucon rows (1 price, 1 number) | 2 | 55,344 | 3.0% |
| **Any pattern evidence (before this check or now)** | **13** | **381,248** | **20.7%** |
| Nothing found | 37 | 1,462,609 | 79.3% |

"Fit shown" means the saved page itself prints our Isuzu number as the OE / cross-reference number of the pattern product. A same-name product for another vehicle was not counted. Omega returned 19 such products (Fiat, Renault, VW, BMW and others), all rejected.

**The 11 parts with a pattern price now** (price is literally on the saved page; each row passed the verbatim check; page paths per part are in the CSV column `source_page_path`):

| Part | Description | Parts billed (EUR) | Pattern offer | Price on the page | Index |
|---|---|---:|---|---|---:|
| 8982606020 | DOOR ASM; FRT,WO/TRIM | 48,496 | Spareto, DT SPARE PARTS 15.00256 | EUR 316.71 incl VAT, dispatch 28 business days | 0.54 or lower |
| 8983621213 | BAR; FRT BUMPER | 45,126 | KS International 0707249 | GBP 90.00 excl VAT | 0.87 |
| 8974056285 | BUMPER ASM; FRT | 39,782 | KS 0012059K; Spareto DT 15.00044 also lists it (EUR 94.69 incl VAT) | GBP 110.00 excl VAT | 0.33 |
| 8974068144 | BUMPER ASM; FRT | 27,456 | KS 0012593K | GBP 120.00 excl VAT | 0.42 |
| 8981226950 | PANEL ASM; FRT | 27,432 | KS 0012647K; Spareto DT 15.00213 also lists it (EUR 189.39 incl VAT) | GBP 230.00 excl VAT | 0.49 |
| 8982410681 | GRILLE; RAD | 26,568 | KS 0013599K | GBP 145.00 excl VAT | 0.42 |
| 8981226920 | PANEL ASM; FRT | 24,233 | KS 0012596K, out of stock; Spareto DT 15.00211 also lists it (EUR 205.68 incl VAT) | GBP 175.00 excl VAT | 0.56 |
| 8981810290 | FENDER; FRT | 23,896 | KS 0703482 and 0703482-1 | GBP 55.00 excl VAT | 0.30 |
| 8980873901 | SUPPORT; FRT BUMPER | 22,000 | KS 0704200 | GBP 50.00 excl VAT | 0.56 |
| 8981032020 | PANEL; DEFLECTOR | 21,168 | Spareto, BLIC 6502-08-3053202P | EUR 181.26 incl VAT, dispatch 2 business days | 0.31 or lower |
| 8980430610 | MIRROR; UNDER | 19,747 | KS 0012741, out of stock | GBP 45.00 excl VAT | 1.08 |

Index = pattern price excl VAT in euro, divided by the reference dealer price (price list x 2.19, provisional). KS prices are converted at the ledger's ECB reference rate of 24 Sep (GBP 1 = EUR 1.16298, `04_tools/price_ledger/fx_rates.json`). Spareto prices are retail incl VAT at a rate the page does not state (its Conditions of Sale say EU prices include VAT), so no ex-VAT index is possible there; the figure shown is an upper bound. The nine KS indexes equal the `aftermarket_index` already in the by-part file, to three decimals.

What the 9 KS hits add: until today they rested on search-result cards that the ledger itself marks "relevance hit, not a confirmed exact match". The KS product pages (fetched today) print our number as "OEM Part Number" / "OE Equivalent Part Number" and the specification says Make AFTERMARKET. The maker is not named on the page. KS sells the genuine part under the same number at a higher price (e.g. GBP 145.00 against GBP 110.00 for 8974056285); that is not pattern and is only listed as context in the CSV.

Where a pattern price exists it is mostly well below our reference dealer price: KS median index 0.49, 7 of 9 below 0.6, two above (0.87, 1.08). The comparison is a UK retail price ex VAT against a derived dealer counter price, so read it as direction, not as a margin.

The 2 local-only parts (Eucon rows, keep local; not re-found on KS, Omega or Spareto): 8983303281 BUMPER ASM; FRT, EUR 35,460 (web-shop prices from March 2024, graded doubtful) and 8975512712 GRILLE; INNER,RAD, EUR 19,884 (competitor numbers only, graded doubtful, no price).

Also in the 50: 8980537880 BLADE; WIPER (EUR 20,344). It is not a body panel and is already off the recovery because of an Isuzu own value-line alternative. No pattern evidence found.

## 2. What it would change in the EUR 143,596 (indication only)

The EUR 143,596 is the body part of option B in the room-to-raise scan behind the 2 Oct paper (captive repair and non-competitive body, no UTI panels hold, factory move + 5 points). I reproduced it from `room_to_raise_by_part_market_2026-10-02.csv` with the build script's own logic: EUR 143,595.62. The per-part figure below is the extra that option B puts on that part above its proposal move. It is an indication; no scenario was rewritten and nothing was re-solved.

| | EUR | Share of 143,596 |
|---|---:|---:|
| Body recovery in the paper | 143,596 | 100% |
| carried by the top 50 (38 parts; the other 12 carry nothing because they already show competitor evidence or an own value-line alternative) | 53,145 | 37.0% |
| carried by the other 2,725 body parts (not checked) | 90,451 | 63.0% |
| **If the one part where this check adds evidence (8982606020) is taken out** | **141,810** (143,595.62 - 1,785.21) | **-1.2%** |
| ... and also 8975512712 (competitor number only, graded doubtful) | 141,069 | -1.8% |
| Carried by the 36 captive parts where nothing was found (rests on "nothing found") | 50,619 | 35.3% |
| Ceiling if every one of the 38 captive top-50 parts turned out to have a pattern part | 53,145 | 37.0% |

Taking parts out without re-solving leaves the total step short by the same euros. The solver would spread that gap over the remaining parts, so the body share would rise on the parts nobody has checked. For scale: the whole body line is 8.8% of the EUR 1.63M step, and the 38 captive top-50 parts are 3.3%.

## 3. What the search could and could not see

Only four sites are cleared (KS, Omega, Amayama, Spareto). What each can do for this question:

- **KS International** (UK): searched by Isuzu number for all 50. 9 returned a card, 41 "Your search returned no results". From the probes, its catalogue is mostly small items, plus the front-end panels and bumpers on the 9 hits. Category probes (first result page only, up to 24 cards, product pages not opened): "windscreen" 18 cards and "windshield" 24 cards, none a glass panel (washers, wipers, mouldings, seals, a pillar); "tailgate" handles, lamps, locks, strap; "rear bumper" small parts (lamps, plates, reflectors, brackets, covers, one reinforcement); "door" hinges, mirrors, regulators, glass channels; "side gate" no results; "bonnet" 12 bonnet assemblies plus hinges and stays (the search by our two engine-hood numbers returned nothing).
- **Omega**: 0 of 50. 31 empty searches, 19 answers with a product of another make.
- **Amayama**: genuine Isuzu only (31 saved pages, 19 parts not on the site). No pattern information.
- **Spareto**: 5 of 50 hold a pattern product linked to our number, one card each. 45 say "Nothing Matches". The two superseded-number checks (8983852259 for 8983852257; 8972433014 for 7552622990) found nothing on KS or Spareto.

Where the blind spot is: the hits sit on truck-tagged parts (7 of the 9 truck-tagged parts) and on 4 of the 41 D-Max-tagged parts. Of the 39 parts with no pattern price found now, 37 are D-Max-tagged (the tag comes from the band file and buyer pattern, so it is an inference). The D-Max body parts, which are most of this list, are the ones none of the four shops describes.

The 37 parts with nothing found, by type (parts billed / extra carried today):

| Type | Parts | Parts billed (EUR) | Carried (EUR) |
|---|---:|---:|---:|
| BUMPER ASM; FRT | 6 | 338,853 | 11,993 |
| GLASS; WINDSHIELD | 4 | 235,160 | 8,763 |
| BUMPER; RR | 4 | 160,986 | 5,517 |
| PANEL; SIDE GATE | 3 | 115,354 | 3,862 |
| FENDER; FRT | 3 | 96,885 | 3,422 |
| GATE ASM; RR | 2 | 87,802 | 3,122 |
| DOOR ASM; FRT,WO/TRIM | 2 | 63,660 | 2,257 |
| PANEL; ENG HOOD | 2 | 59,433 | 2,008 |
| GRILLE; INNER,RAD | 2 | 58,492 | 1,784 |
| RAIL; ROOF | 2 | 53,531 | 1,995 |
| seven single parts (rear and front bumper supports, deflector panel, bumper bar, rear body, side outer panel, wiper blade) | 7 | 192,453 | 5,894 |

Not searched at all: glass specialists, body-panel wholesalers, marketplaces and eBay (robots.txt or bot checks, see `00_docs/agent/CROSSREF_SOURCE_RECON_2026-10-01.md`), TecDoc (needs an account, Jerome's call), and any dealer or IML quote. A shop that does not list a pattern windscreen against an Isuzu number tells us the shop does not list it, not that none is sold.

## 4. Sources and counts

- Fetched in this run: **35 pages, 0 consent refusals, 0 HTTP errors, 0 bot challenges** (4 Oct 2026, 04:56 to 05:01 UTC; the consent gate also read robots.txt before each request). 25 on KS (16 product pages, 2 superseded-number searches, 7 category probes), 10 on Spareto (8 lookups for the Tier B parts that had no Spareto page yet, 2 superseded-number lookups). Same fetch layer as the earlier passes (`fetch_polite.py` through `run_dated_pass.PassFetcher`): robots check, at least 2.2 s per host, declared identity ISZE-parts-research/1.0, no login, no browser.
- Read from earlier saved passes, not re-fetched: KS and Omega 50 search pages each (Tier A pass 2 of 2 Oct, Tier B of 1 Oct), Amayama 31, Spareto 42 (2 Oct). Paths per part are in the CSV column `pages_searched_by_isuzu_number`.
- Eucon: rows were read locally only. No Eucon competitor number was used as a search term or sent to any site or service in this run. Eucon-derived text sits only in the CSV, flagged in column `eucon_derived_keep_local`; keep it out of the shared paper.
- Verbatim check: for all 11 primary offers the shop code, our Isuzu number, the price (and the "Excl. VAT" label on KS, or the "compatible with OE numbers ... (isuzu): brand" line on Spareto) were found literally in the saved HTML. 11 pass, 0 fail. One note: Spareto prints the BLIC part's OE number as 8-98103202-0, and the plain number 8981032020 is in the page title.
- One conflict recorded, not hidden: for 8981226920 the KS page title tag says "(GENUINE)" while the specification table says Make AFTERMARKET and the code ends in K like the other pattern codes. Spareto lists a DT Spare Parts product for the same number.

Files:
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\price_5pct_proposal_2026-09-29\room_to_raise_2026-10-02\body_pattern_check_2026-10-04\body_pattern_check_2026-10-04.csv`
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\price_5pct_proposal_2026-09-29\room_to_raise_2026-10-02\body_pattern_check_2026-10-04\body_pattern_check_2026-10-04.md`
- Saved pages, fetch log (`fetch_log.jsonl`) and page list with hashes (`evidence_pages_manifest.csv`): `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\scrape_targets\_probe\passes\body_pattern_check_2026-10-04\`

## 5. Decisions for Jerome

1. **Wording in the paper.** "No aftermarket alternative found" is only true for KS, Omega, Amayama and Spareto. It is already not true for 11 of these 50 parts (9 on KS, plus 8981032020 and 8983303281), which the recovery already excludes. Recommendation: keep the body line, but say "none found in four shops, D-Max body parts not covered" and do not call it safe.
2. **Take out two parts?** 8982606020 (pattern price now found, EUR 1,785 of the recovery) and 8975512712 (number only, doubtful, EUR 741). Recommendation: take out 8982606020; 8975512712 is your call because the evidence is a single doubtful local number.
3. **Search wider, or accept the gap?** EUR 50,619 of the recovery sits on 36 parts with nothing found, and EUR 90,451 on 2,725 body parts nobody has checked. A wider look needs a source we do not have: a data agreement for TecDoc, a glass or body-panel specialist cleared for automated access, or quotes from IML or a UK dealer on the ten largest uncovered parts. Which of these, if any, is your go.
