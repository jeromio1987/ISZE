# ISZE parts classification: independent review and management recommendation

**Review date:** 20 September 2026. **Audience:** internal technical and commercial review.  
**Snapshot:** the supplied full classification is declared in its companion workbook as a master-derived export at 06:30 UTC on 20 September 2026. EQ-Hit observations are from 19 September 2026.  
**Decision:** approve the classification approach and a bounded validation pilot, but do not adopt the current master or the untested separated file as the general reporting source.

## Conclusion

The separation of the catalogue product tree from the AIM parts family is useful. The supplied data does not, however, support the brief's suggestion that the latest master is a safe fallback merely because it includes the latest patches.

The independent checks found malformed part-type fields and current labels that contradict the recorded technical evidence. Refreshing another file from this master without first resolving these assignments would copy the defects rather than fix them. No original file has been changed in this review.

The immediate management request should therefore be for a controlled technical validation and a small, explicitly reviewed commercial use case, not unrestricted use or blanket price changes. Product definitions, reporting scope and approval responsibilities matter more than the filename.

## What was actually examined

The full supplied classification was checked across all 165,213 literal identifiers. The two summary workbooks were inspected. All 744 EQ session records were joined one-to-one to the master; the 9,164-row residual list was reconciled exactly to its stated intersection; the earlier PowerPoint was inspected through its slide text. Counts and key totals were independently recounted using a second CSV/Decimal calculation. File hashes were checked again to establish that the inputs were unchanged.

This is a structural and cross-file audit with targeted identity challenges. It is not a live EQ-Hit inspection, a replay of the absent original classification scripts, or a statistically representative technical accuracy certification. The actual separated classification, approved category dictionary, original validation script and output, and complete application/change history are not in the uploaded package. Source-PC timestamps cannot be reconstructed from the mounted copies.

Counts below are classification records, not units sold or service-demand gaps. A fleet denominator does not apply to these structural checks. Source record numbers in the evidence workbook exclude the CSV header; they are not physical text-line numbers, because some malformed fields contain newlines.

## The most important finding: the latest assignments are not automatically safe

The following are direct comparisons between the uploaded master and the descriptions or EQ details supplied with this review. They are not conclusions inferred from low sales.

| Part number | Supplied product evidence | Stored AIM part type | Review conclusion |
|---|---|---|---|
| 8979490060 | Clutch slave cylinder; EQ figure 2-06, proposed Slave cylinder | Pivot | Contradiction in the literal product type. Retain clutch context, but do not approve Pivot. |
| 8980485080 | EQ figure 8-60 Heater Unit; supplied proposal Heater core / heater | Water Pipe | The current product type does not preserve the heater-core identity. |
| 8980475290 | Caliper guide pin on EQ figure 3-02 | Brake Caliper | Correct broad system does not make a component a complete caliper. |
| 8980069570 | Front suspension stabilizer bar | Axle Shaft | The broad figure context has not preserved the item's own identity. |
| 8982986320 | Injection pipe number 1; no retained EQ identity detail | Nut | A precise but unsupported and contradictory label. |
| 8975435900 | Clutch disc | Clutch Kit | Broad clutch correction is supported, but the component is not identified separately from a kit. |

A narrow full-file search finds 27 records explicitly described as clutch slave cylinders but assigned to Pivot. The 43 EQ proposals called Slave cylinder should not all be counted as 43 cylinder errors: that proposal group also contains push rods, pins and other items. This is evidence that review is needed both before and after vocabulary translation, not only when an EQ lookup fails.

The current master contains 384 of 384 proposed-session parts with named AIM families and a source tag referencing that EQ session. Only 59 proposals have the same literal three-level path as the current master; 325 differ. Some differences may be legitimate vocabulary translations, so 325 is not an error count. The examples above establish that at least some translations do not preserve the supplied product identity. The mapping code is needed to establish the mechanism conclusively.

The targeted Identity review worksheet records 169 distinct parts. It includes 109 clutch component-versus-kit cases that require a definition decision, alongside clear product-description contradictions. This is a review list, not a random sample or an estimate of the total error rate.

## Malformed labels are a separate, confirmed defect

There are 299 records whose third-level AIM field contains a programming representation rather than a single category name. A representative stored value reads:

```text
aim_l3    Not classified at L3
aim_l3                  Filter
Name: 1085, dtype: object
```

All 299 carry a source tag from the 19 September residual application. This shared tag is an observed association; the exact code defect remains unverified because the application script was not supplied.

The defect also inflates the apparent vocabulary: the file contains 508 distinct nonblank L3 strings, including 299 such malformed strings. Removing those strings leaves 209 distinct nonblank strings, including unresolved labels. Neither 508 nor 209 is an approved taxonomy size.

The required response is to reject these values as invalid category labels and recover the intended assignment from the source evidence and approved rules. Selecting the second line of each string automatically would conceal rather than resolve the ambiguity.

## Coverage is being discussed with incompatible denominators

The full-file recomputation is:

| Measure | Records | Share of 165,213 master rows | Interpretation |
|---|---:|---:|---|
| Named catalogue top-level group | 154,860 | 93.7% | Catalogue group present, excluding Other / review and blank. |
| Catalogue Other / review | 9,935 | 6.0% | Residual within the catalogue tree. |
| Catalogue top level blank | 418 | 0.3% | No catalogue top-level assignment in this extract. |
| Named AIM top-level family | 19,636 | 11.9% | Named aftersales family; not necessarily correct. |
| AIM top level blank or unknown | 145,577 | 88.1% | Global AIM assignment gap on the full catalogue/master population. |
| Well-formed named AIM path | 19,269 | 11.7% | Three non-placeholder labels, excluding serialization defects; still not verified correctness. |

The workbook's 24,723 nonblank AIM L1 values include 5,087 Unknown or Unknown Review values. Nonblank is therefore not equivalent to a meaningful classification.

The 9,164-row true-open export is exactly the intersection of catalogue Other / review and AIM blank/unknown. It is not the complete global AIM-unknown list. A further 771 catalogue-Other records already have named AIM families. This proves why catalogue residual and AIM assignment coverage must not be substituted for one another.

The brief's 5.74% refers to another classification snapshot with 164,667 rows. The uploaded master instead has 9,935 / 165,213 = 6.0134% catalogue Other / review. A master-to-separated synchronization could change that other file again. Do not average these rates or replace the denominator silently.

These findings also do not mean that 88.1% of the parts revenue lacks an AIM family. Much of the full catalogue may not have recent billing. A supplementary mapping diagnostic on positive-value numeric-part rows dated 1 January to 31 December 2025 in the supplied billing extract finds named AIM L1 on 13,905 of 16,838 distinct raw part numbers, covering 97.3% of that diagnostic's positive billed value. Well-formed named paths cover 95.9%. This is not the certified ISZE parts-revenue population: it includes all supplied entities and applies a positive-value numeric-part filter rather than a fully signed-off revenue policy. It is retained only to demonstrate the distinction between catalogue coverage and billed-value coverage. It is not a management-ready revenue or accuracy claim.

## EQ-Hit's recorded outcomes need an evidence check

The session has exactly 744 unique part numbers, all marked FOUND. There are 384 PROPOSE_PATCH records and 360 NEEDS_HUMAN records. Those historical counts are confirmed.

However, 26 FOUND records have no retained figure name, part name or catalogue. Ten are in PROPOSE_PATCH and carry an EQ-session source tag in the current master. The proper finding is that their technical evidence is not retained in this export, not that the parts were definitely absent from EQ-Hit. The 718 records with all three fields populated are also not automatically independently verified correct; they merely retain more evidence.

The NEEDS_HUMAN list is not a current open-state count. Of those 360 session parts, 19 now have named AIM L1 and 341 remain blank or unknown. A current named label is not proof of an approved resolution or of when that resolution happened. The supplied approval/change history is insufficient to certify those 19 as closed.

Only 91 of the 360 original human-session parts fall within the 9,164-row catalogue-Other/AIM-unknown intersection. The session queue and catalogue residual are overlapping selections with different scopes, not two independent opportunities to add together.

The explanation that every unresolved EQ result is caused by a missing approved leaf is too strong. Some records lack retained evidence, and Head Cover already appears as an assigned path in the master while some head-cover EQ outcomes still say no safe leaf. That is consistent with a missing mapping rule or incomplete dictionary access; it does not prove which cause applies without the dictionary and mapper. Wiper linkage, engine mounts, gearbox components and audio equipment remain specific areas for a category-definition review.

## Better family placement can still destroy component detail

The 126 records tagged as the 20 September figure correction reproduce the reported total: 17 air-cleaner records and 109 clutch records. The clutch records comprise 53 disc descriptions and 56 pressure-plate descriptions. All 109 end in Clutch Kit.

Moving a clutch disc out of Brakes is an improvement at the broad family level. Calling it a kit at the detailed level does not complete the technical correction. If Clutch Kit is deliberately a commercial basket, it must be described as a basket and kept separate from literal part type and pack quantity. It cannot safely support a kit-versus-component quantity comparison without that distinction.

The intentional placement of oil, fuel and air filters under Maintenance Service is not flagged as an error here. The current source explicitly treats it as a service-basket choice. It needs a consistent definition, not a forced move based only on a broad engine figure.

## Identifier and flag controls also need attention

The full master has no duplicate literal part-number strings. Nevertheless, 612 numeric identifiers form 306 groups after leading zeros are removed; 131 groups carry different AIM paths. These are conditional alias conflicts, not proof that all pairs are the same approved identifier. Preserve raw identifiers and require explicit equivalence and replacement rules before merging them. No normalised many-to-many billing join was allowed in this review.

The figure key equals figure number plus position key on all 161,129 rows where all three fields are present. This confirms arithmetic consistency on that subset, not correct application or complete catalogue coverage. Missing figure keys remain outside that result. Some rows with separate components but no combined key use non-numeric position values, so a blind fill would need its own specification.

Twenty records differ between has_aim and the operational test of a named current L1. This is a definition/refresh question until the flag's contract is supplied, rather than an assumption that every flag is broken. A further 68 named L1 records retain an unresolved lower level. A single presence flag should not certify the entire path.

The file also assigns the administrative identifier 0000REBATE to Logistics Packaging / Packaging / Label. Administrative exclusions need an explicit policy; a valid-looking physical-parts path is not enough.

## Answers to the review brief

| Requested challenge | Verdict | What the upload establishes |
|---|---|---|
| Original 18 September versus 20 September file timestamps | UNKNOWN | Mounted upload times do not establish source-PC modification times. |
| Four current-master versus separated-file discrepancies | UNKNOWN for the comparison | All four master-side values are reproduced; the separated file is not supplied. The two clutch examples are still insufficient at component level. |
| 360 of 744 NEEDS_HUMAN | CONFIRM for the session | Not a current open-state total: 341 remain blank/unknown and 19 currently have named labels. |
| Which live reports fail after a source replacement | UNKNOWN | Actual reader code, input configuration and complete report inventory are missing. |
| 5.74% as the general management residual | REJECT | Current master catalogue Other / review is 6.0134%; global AIM unknown is a different measure. |
| Existing management decks imply a fused first level | UNKNOWN across all packs | The supplied deck separates identity and market evidence, but does not faithfully describe the actual parallel trees and overstates readiness. |
| Latest master is automatically the safe fallback | REJECT | Current identity contradictions and 299 malformed L3 cells are enough to reject blanket reliance. |

The statement that the other file passed its 18 checks is a claim in the brief. It was not independently rerun, and the supplied master is not the file to which that reported result applies.

## What to improve, in priority order

**First, stop unsupported specificity.** An EQ figure can establish a system without establishing whether an item is a complete assembly, a pin, a seal, a hose or a kit. Preserve the supported levels and leave the unsupported level explicitly unresolved. Do not force a match into the nearest available label.

**Second, resolve the product-type definitions needed by current evidence.** Separate clutch discs, pressure plates and slave cylinders from kits and pivots; caliper components from complete calipers; heater cores from water pipes; stabilizer bars and coil springs from axle shafts and bushings. The category owner must approve these definitions and mapping examples before any application.

**Third, eliminate corrupt values and reconcile identifier policy.** Acceptance checks should reject multi-line programming output and conflicting numeric aliases, and make partial classification visible. Each applied change needs a traceable old value, proposed value, accepted value, technical basis, approver and date.

**Fourth, make the evidence stages explicit.** Retain separate states for lookup attempted, result found, detail retained, identity assessed, mapping approved and change applied. Restore evidence for the 26 incomplete recorded results, prioritising the ten already in the proposed/applied group. This is targeted evidence work, not a request to rescrape the whole catalogue.

**Fifth, define which tree each analysis uses.** Preserve the catalogue product tree and the AIM parts family as parallel three-level classifications. Preserve the separate figure-based service model. Market-specific competitor evidence is a further analytical dimension, not the second of these two trees. Keep comprehensive physical attributes on their existing deferred roadmap.

**Finally, demonstrate a bounded commercial use.** Choose reviewed categories and one participating distributor, declare the sales stage, period and fleet basis, and show how the classification changes the diagnosis or action. Reclassification moves existing billing between categories; it does not itself generate turnover. A market action must separately demonstrate repeat business and achieved contribution.

No new dashboard, price list, presentation or production data flow was built in this review. The proposed acceptance criteria specify what must be true before wider use; implementation belongs with the existing owners.

## Changes needed in the earlier presentation

The earlier deck I produced followed the paper's identity-live description too literally. The row-level evidence now requires a narrower claim. In particular, slides 1, 2, 4, 17 and 26 should not suggest that a live file is already a technically dependable catalogue-wide identity base.

The material also needs to distinguish two different ideas: two parallel product trees, and product identity versus local market evidence. The supplied catalogue top level still includes Competitive parts and Repair parts; those values cannot be described as a purely functional hierarchy or as measured local competition. The management language should be Catalogue product tree and AIM parts family, with market evidence and product comparability described separately. File versions and internal build names add nothing to the approval decision.

The Deck wording worksheet records specific slide changes. No revised deck has been issued, and existing historical corrections are not indiscriminately relabelled as unresolved. The findings here concern the supplied current records and clearly identified gaps in the implementation evidence.

## What management should approve

Approve a technical/category owner, a bounded review of affected assignments and definitions, and a pilot that uses only reviewed parts. Require evidence that the classification used by each relevant analysis is the accepted one, that quantities and billing do not multiply when identifiers are linked, and that component-versus-kit identity is preserved. Approve general use only after those conditions are met.

Success should be demonstrated with reliable category interpretation and a better distributor decision. Any incremental revenue or contribution claim needs a separate measured commercial test. The supplied files do not establish a financial return attributable to AIM.

A suitable approval statement is:

> We propose to retain two separate three-level classifications: the catalogue product tree and the aftersales parts family. Before broader use, we will validate the affected assignments, preserve the distinction between components and kits, and make unresolved items explicit. A limited distributor pilot will then test whether the improved classification supports clearer sales analysis and better commercial decisions. Wider adoption will follow demonstrated data reliability and commercial usefulness.

## Exact evidence still needed

The next review needs the price-free separated classification from the same documented snapshot; the approved category definitions and full allowed paths; the existing classification builder, vocabulary translation and validation logic; the actual validation output tied to the input file hash; and the EQ/figure change history showing old, proposed and accepted values. Selected authorised catalogue extracts are needed where detail was not retained. A list of the actual input fields used by the affected analyses would resolve the dependency questions. Raw billing, full price lists and credentials are not required.

## Source and calculation notes

- S1: 01_AIM_classification_FULL_no_price_cost.csv. Full 165,213-row master-derived export, declared snapshot 20 Sep 2026 06:30 UTC. Used for all current paths and classification counts.
- S2: 01_AIM_classification_SUMMARY_and_sample.xlsx. Summary date, scope and sample records; full-file counts recomputed rather than inferred from the sample.
- S3: 02_EQ_Hit_session_20260919_RESULTS.csv. 744 unique session PNs; retained catalogue details and proposals. Session amounts are weights with no explicit billing-window declaration in the supplied fields.
- S4: 02_EQ_Hit_evidence_SUMMARY.xlsx. Historical outcome summary checked against S3; it does not certify current applied labels.
- S5: 03_catalogue_Other_review_TRUE_OPEN_AIM.csv. Exactly 9,164 records. The supplied L12M column sums to EUR 114,515.68, with 398 positive-value records and 8,766 zero-value records; 7,607 have a figure key. Exact billing-window dates are not supplied. This is classification workload weighting, not a commercial gap.
- S6: GPT_REVIEW_classification_switch_20260920.md. Claims challenged rather than treated as verified results.
- S7: 01_all_sales_isze_to_distributor.csv. Supplementary positive-value numeric-PN coverage diagnostic for calendar 2025 only; no transaction rows reproduced and no official revenue restatement.
- S8: ISZE_AIM_Extended_v1.0.pptx. Slide text inspected for readiness and terminology claims.

The historical EQ weights sum to EUR 82,109.07 for NEEDS_HUMAN and EUR 172,111.26 for PROPOSE_PATCH. These are verified sums of the supplied column, not independently verified dated turnover and not gains. They must not be added to service-demand gaps or used as a management benefit. Original file hashes and record-level evidence are retained in the workbook.
