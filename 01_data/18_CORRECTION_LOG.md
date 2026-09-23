# Correction log — v1 to v2 of the tonnage pack

**Date:** 2026-09-20. **Trigger:** an external review of the v1 pack (`01_data\CURSOR_TONNAGE_FEEDBACK_2026-09-20.md`).
**Method:** every numeric claim in that review was re-derived from the source files before anything was changed. **23 of 24 checks agreed with the reviewer.** One differed in detail only (see item 9). Nothing outside this pack folder was edited.

## Source corrections — things v1 got wrong

| # | What v1 said | What is true | Where it is fixed |
|---|---|---|---|
| 1 | Band-exclusive share of about **11%** for 2025. | **31.8%**. The v1 denominator summed every row of the band file, including the non-additive `also_fits_band` applicability views, which repeat purchasing already counted. Correct denominator: `sums_to_n_series_total == "yes"`. | `00_READ_ME_FIRST.md` §1, §3c, §4; `data_nseries_bands\01_additive_billing_partition.csv` |
| 2 | The **297** band candidates were presented as though they described the same universe as the **835** service worklist. | They overlap on **91** part numbers. **206** candidates sit outside the worklist; **744** worklist rows never got a band read. The two euro columns are on different bases and **cannot be compared or added**. | §3a; `05_part_population_bridge.csv` |
| 3 | "Nothing sits in the 5.5 t band by itself. Zero part numbers in the whole service list are exclusive to 5.5 t." | The candidate table carries **16** exclusive 5.5 t part numbers (EUR 16,834). The accurate, narrower statement is that the **strict in-scope N-series decode** carries none. | §3b, §7 |
| 4 | The 143-part-number slice and its euro quoted without qualification. | Both true, but the euro basis differs from the worklist universe. Now stated with the basis named. | §3a |
| 5 | "the flat 1.25 … overstates ITUK filter demand by about 72%, and correcting it moves ITUK oil-filter cover from about 116% down to the 70s." | **Wrong direction, withdrawn.** Cover is `actual ÷ expected`, so a lower expected **raises** cover. Worked: 35.1% → 44.5%, up about 9 points on the deck's own example. | §5; `17_BRIEF_FOR_THE_MODEL.md` §5 |
| 6 | 14,494 km/yr labelled "ITUK N35" in one place and "IUK N35" in another. | The figure is **IUK** — the UK light commercial Grafter fleet. ITUK's own measured figure differs. | §5, §10; `data_context\12_mileage_reference.csv` |
| 7 | "CY2025 is … 11 months on the PRISM basis." | The file does not support that. 2025 `months_in_period` runs across 1, 2, 3, 5, 6, 7, 9, 10, 11 and 12 by market. | §8 |
| 8 | UTI's absent 3.5 t band presented as an explained limit. | The model carries no UTI 3.5 t fleet, yet the billing records **EUR 4,135** of exclusive 3.5 t purchases (EUR 471,921 on the pooled view). A live inconsistency, now stated as one. | §3d, §12 |
| 9 | The review states the worklist rows outside the candidate table number **629**. | Re-derived as **744** (835 − 91). The reviewer's own two headline numbers — 835, 91, 206 — all reproduce exactly; this single figure does not. Differs in detail, not in substance. | §3a |

## Questions the review left open that this pass closed

| # | Open question | Answer found | Evidence |
|---|---|---|---|
| 10 | Does `months_in_period` count months in the available source extract, or months with purchases? | **Months with purchases of the selected parts.** `months = ("m", "nunique")` over the billing rows, then `period_is_complete = months_in_period >= 12`. | `03_analytics\Isuzu\prism\scripts\build_nseries_tonnage_bands.py` lines 573–584 |
| 11 | What is the cause of the 5.5 t / 3.5 t conflicts? | The older probe script hard-coded `NKR → 5.5t`; the sourced series table places `NKR` at **3.5 t** (JP VIN register) and leaves `NHR` unresolved. All six conflicts are `NKR`-evidenced. | `_tonnage_capable.py` vs `07_series_token_to_band.csv`; `06_band_by_part_number.csv` |

## Defects found in the pack that the review did not name

| # | Defect | Consequence |
|---|---|---|
| 12 | `period_is_complete` conflates purchase activity with source coverage. A complete source with no purchase of those parts in some months is labelled incomplete. | `comparable_to_previous` is conservative in the wrong way: "we did not buy" is indistinguishable from "we do not have the data". Needs a fix at source. |
| 13 | No 10 t band exists, so the 7.5 t grouping cannot separate 7.5 t from 10 t. | An ITUK-versus-UTI 7.5 t mix comparison cannot be built from this data, and the grouping must not be relabelled as a precise weight distribution. |

## Confirmed correct in v1 — no change needed

Re-derived and holding, so the corrected documents keep them: the additive partition equals the tagged N-series total (EUR 4,305,334, delta EUR 0.00); the 835 / 297 / 143 / 154 counts; the six band combinations and their euro; the 164 heavy-truck part numbers; the 53 pooled-across-families part numbers; 120 model codes with 50 unresolved; the two-lane rule; that market actuals are market-level on every row; that UTI has no 3.5 t row in the demand model; and the six named mapping conflicts.

## What was NOT done

No source file was edited. No dashboard, atlas or HTML was rebuilt or redesigned. The billing basis was not replaced. The disputed 5.5 t records were **not** resolved — they are flagged and left visible, because choosing a side is the mapping owner's decision, not this pass's. The `months_in_period` defect is documented, not patched.
