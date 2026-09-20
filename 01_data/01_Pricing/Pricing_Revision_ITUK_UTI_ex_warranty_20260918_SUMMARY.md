# ITUK / UTI price revision — exclude warranty parts

**Side study only.** The published network weighted increase (**5.9616%**, step **EUR 1,652,140.71**) is unchanged.

## Verdict

**ITUK:** excluding warranty parts lowers the weighted increase from 6.6695% to 5.7639% (-0.9056 percentage points). Warranty PNs carry EUR 174,966.82 of that DB’s priced step (49.2% of step; 41.7% of billed).

**UTI:** excluding warranty parts lowers the weighted increase from 5.5808% to 5.4605% (-0.1203 percentage points). Warranty PNs carry EUR 68,848.42 of that DB’s priced step (38.2% of step; 38.0% of billed).

## Numbers

| DB | Slice | Weighted % | Step € | Billed € | PNs |
|---|---|---:|---:|---:|---:|
| ITUK | all_in_scope_priced | 6.6695% | 355,797.80 | 6,249,953.73 | 4077 |
| ITUK | ex_warranty | 5.7639% | 180,830.98 | 3,641,507.86 | 3798 |
| ITUK | warranty_only | 7.9625% | 174,966.82 | 2,608,445.87 | 279 |
| UTI | all_in_scope_priced | 5.5808% | 180,312.25 | 3,400,405.39 | 1869 |
| UTI | ex_warranty | 5.4605% | 111,463.83 | 2,108,041.74 | 1766 |
| UTI | warranty_only | 5.7872% | 68,848.42 | 1,292,363.65 | 103 |

## Warranty file used

- File: `C:\Users\jerom\Desktop\claude\ISZE\01_data\CV_Warranty_01-08_2026.xlsx`
- Claim window (BILLYMD all file): 20251219 → 20260817
- **ITUK:** 2,816 claim lines; 345 unique PNs (PARTNBR + PARTNBR2); BILLYMD 20260112 → 20260817; part amount sum EUR 277,988.64.
- **UTI:** 1,506 claim lines; 118 unique PNs (PARTNBR + PARTNBR2); BILLYMD 20251225 → 20260817; part amount sum EUR 594,517.87.

## Caveats

- Warranty file is CV warranty **01–08 2026** claim lines. Excluding means “PN ever on a claim for that DST in this file,” not a perfect match to the Jul25–Jun26 sales window of the price exercise.
- **PARTNBR2** is included in the warranty PN set.
- Separate exercise; published **5.9616%** network figure unchanged.
- ITUK ≠ IUK; UTI ≠ UMI — never blended.

## Outputs

- Excel: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Pricing_Revision_ITUK_UTI_ex_warranty_20260918.xlsx`
- Open: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OPEN_Pricing_Revision_ITUK_UTI_ex_warranty_20260918.cmd`
