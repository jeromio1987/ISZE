# ITUK / UTI — ex-warranty by billing code vs claim-qty haircut

Side study only. Published network **5.9616%** (step EUR 1,652,140.71) is unchanged.

## Verdict

**Cut A (billing SaTy):** there is no warranty / FOC / claim SaTy on ITUK or UTI billing in the L12M window. Observed codes are only SOR, blank, PRD, VOR, RUSH, CR, DR. Warranty parts still bill as normal genuine lines; PRISM subtracts warranty expense at fiscal GPS level, not via a SaTy flag. So Cut A removes **zero** rows and the weighted % is **unchanged** vs the published priced-both basis. This cut cannot move the number.

**Cut B (ITUK, claim-qty haircut, window):** raises the weighted increase from 6.6695% to 6.6774% (+0.0079 pts). Step euro moves from EUR 355,797.80 to EUR 348,593.92. Full-file claim sensitivity: 6.6828% (step EUR 345,665.17).

**Cut C (ITUK, PN-flag reference):** lowers from 6.6695% to 5.7635% (-0.9061 pts). Reference only — not the primary answer.

**Cut B (UTI, claim-qty haircut, window):** raises the weighted increase from 5.5808% to 5.5821% (+0.0013 pts). Step euro moves from EUR 180,312.25 to EUR 169,556.54. Full-file claim sensitivity: 5.5892% (step EUR 166,043.60).

**Cut C (UTI, PN-flag reference):** lowers from 5.5808% to 5.4605% (-0.1203 pts). Reference only — not the primary answer.

### Why Cut B can move the other way from Cut C

Cut C drops the **entire** billed quantity of any PN that ever appears on a claim. That removes high-step (or low-step) parts completely, so the remaining basket’s weighted % can fall even when commercial reality is only a partial warranty share.

Cut B only subtracts **claim quantity** from billed quantity. The PN stays in the basket at its residual commercial volume. If the haircut removes relatively more volume from parts with a **below-average** price step (or leaves parts with an above-average step), the weighted % can rise — Jerome’s intuition that “strip out warranty and the commercial increase looks different” — even when the blunt PN-flag cut moved the other way.

## Numbers

| DB | Cut | Weighted % | Step € | Billed € (weight basis) | Qty |
|---|---|---:|---:|---:|---:|
| ITUK | published_priced_both | 6.6695% | 355,797.80 | 6,249,953.73 | 220,189.0 |
| ITUK | A_billing_saty_ex_warranty | 6.6695% | 355,797.80 | 6,249,953.73 | 220,189.0 |
| ITUK | B_claim_qty_haircut_window | 6.6774% | 348,593.92 | 6,110,162.29 | 219,585.0 |
| ITUK | B_claim_qty_haircut_fullfile_sens | 6.6828% | 345,665.17 | 6,051,391.90 | 219,278.0 |
| ITUK | C_pn_flag_ex_warranty_REF | 5.7635% | 180,767.45 | 3,640,522.48 | 183,517.0 |
| ITUK | C_pn_flag_warranty_only_REF | 7.9623% | 175,030.35 | 2,609,431.25 | 36,672.0 |
| UTI | published_priced_both | 5.5808% | 180,312.25 | 3,400,405.39 | 127,067.0 |
| UTI | A_billing_saty_ex_warranty | 5.5808% | 180,312.25 | 3,400,405.39 | 127,067.0 |
| UTI | B_claim_qty_haircut_window | 5.5821% | 169,556.54 | 3,173,322.65 | 126,492.0 |
| UTI | B_claim_qty_haircut_fullfile_sens | 5.5892% | 166,043.60 | 3,094,629.35 | 126,320.0 |
| UTI | C_pn_flag_ex_warranty_REF | 5.4605% | 111,463.83 | 2,108,041.74 | 112,456.0 |
| UTI | C_pn_flag_warranty_only_REF | 5.7872% | 68,848.42 | 1,292,363.65 | 14,611.0 |

## SaTy observed (L12M, sold_to_sap 2575 / 1799)

| DB | SaTy | Rows |
|---|---|---:|
| ITUK | SOR | 9,360 |
| ITUK | (blank) | 4,509 |
| ITUK | VOR | 1,970 |
| ITUK | PRD | 1,315 |
| ITUK | RUSH | 816 |
| ITUK | CR | 4 |
| ITUK | DR | 1 |
| UTI | SOR | 5,547 |
| UTI | (blank) | 1,956 |
| UTI | RUSH | 552 |
| UTI | VOR | 256 |
| UTI | PRD | 40 |
| UTI | CR | 1 |

## Warranty file

- File: `C:\Users\jerom\Desktop\claude\ISZE\01_data\CV_Warranty_01-08_2026.xlsx`
- BILLYMD all file: 20251219 → 20260817
- Preferred window for Cut B: 20250701–20260630
- **ITUK:** 2,816 claim lines (2,126 in window); claim qty sum window 766.0 / full file 1,114.0; BILLYMD 20260112 → 20260817.
- **UTI:** 1,506 claim lines (1,157 in window); claim qty sum window 621.0 / full file 805.0; BILLYMD 20251225 → 20260817.

## Caveats

- Cut A is empty by construction of the billing extract — not a modelling choice.
- Warranty file CV claims 01–08 2026; first BILLYMD is mid-L12M, so the window haircut is partial vs a full Jul25–Jun26 claim extract.
- Cut C is the earlier “PN ever on a claim” study, kept as reference only.
- ITUK ≠ IUK; UTI ≠ UMI.

## Outputs

- Excel: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Pricing_Revision_ITUK_UTI_ex_warranty_billing_20260918.xlsx`
- Open: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OPEN_Pricing_Revision_ITUK_UTI_ex_warranty_billing_20260918.cmd`
