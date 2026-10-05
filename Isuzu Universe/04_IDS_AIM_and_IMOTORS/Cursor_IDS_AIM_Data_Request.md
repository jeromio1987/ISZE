# Request to Cursor: real data for the IDS x AIM connection

## Objective and scope

Prepare one verified data pack so ChatGPT can replace the synthetic content in the existing IDS x AIM prototype with actual information.

IDS means Isuzu Dealer Standards: dealer self-assessments, not distributor audits. AIM means Aftermarket Intelligence Model: the approved parts-classification and commercial-analysis model.

This is a data-export task, not an application rebuild. Do not change Universe, its design, existing calculations, dashboards or production source files. Use a separate export folder. Do not create sample dealers, invented assessments or guessed classifications.

Start with ITUK, the UK truck distributor, and calendar-year 2025 purchasing. Use the latest usable IDS assessment round, with its actual assessment dates displayed separately. Search the workspace and correction history before asking questions. Export everything supported now; report genuinely missing inputs without blocking the usable data.

## Existing inputs: reuse rather than resend

ChatGPT already has these files:

- `03_all_sales_to_dealer.csv`.
- `dealer_sellout_aim_mix_2025.csv`, `05_sales_to_dealer_by_dealer.csv`, `sales_to_dealer_by_dealer_year.csv` and `sales_to_dealer_network_by_db_year.csv`.
- `06_dealer_master_geo.csv`.
- Existing ISZE billing, market fleet, service-demand, mileage, warranty and Genuine/BVP summary extracts, plus the business-context documents.

The dealer transaction extract has quantities but no actual dealer prices or stable dealer-account ID field. The participant master has names and locations but blank assessment-score, rank and distributor fields. The euro mix summaries do not establish their price source or effective date.

Check those observations against the authoritative workspace sources. Send missing mappings, source explanations and corrected derived extracts where needed, not another unrestricted billing export. Existing filenames may use older terminology; use "sales to dealer" in descriptions.

## Dealer identities and purchasing-account links - required

Supply a dealer/site master and a separate purchasing-account-to-site mapping. Keep purchasing accounts, legal dealer businesses and physical assessed sites distinct.

Include source-native purchasing-account ID, account name, distributor code, stable dealer/site ID, site name, relevant location fields, active dates and assessment-participation status. Preserve original source identifiers and names. Where a native ID does not exist, document a reproducible surrogate and its limitations; do not present it as a validated source ID.

For each account-to-site relationship, include its type, validity dates, validation status, supporting source and validation date. Identify one-to-one, multiple-account and shared-account relationships. The mapping must also explain how account names in the existing ChatGPT extract attach to these IDs.

Do not treat matching country, assessment cohort, similar name or proximity as proof of distributor responsibility or site identity. Keep unconfirmed candidates separate. A shared purchasing account must not have all its purchasing copied onto every associated site. Do not invent allocation percentages.

## Actual IDS assessments and questionnaire - required

Export the approved questionnaire and the recorded responses, not just a dealer list or a final rank.

The questionnaire needs its version, section ID and name, question ID, wording, response options, applicability rules and existing scoring method. Where scoring exists, supply weights, maximum scores, treatment of unanswered/not-applicable responses and any documented grade thresholds. Do not create a new score.

Responses need assessment ID, assessed site ID, round, questionnaire version, assessment/submission date, question ID, recorded answer, existing score where applicable and submission status. Include relevant comments or evidence references only where approved for this export; remove unnecessary personal information.

Distinguish self-reported answers from any separately reviewed findings. Identify the authoritative submission when a dealer has submitted more than once. Preserve revision history or explain which record is current.

Confirm whether ITUK has a usable assessed population that can be linked to its purchasing accounts. If no validated overlap exists, state that explicitly. Export the purchasing data anyway and identify another evidenced overlap only if one actually exists. Do not invent ITUK assessment results to complete the demonstration.

## Authoritative AIM part classification - required

Supply the current approved AIM mapping, stripped of unrelated sensitive fields. It must cover all part numbers in the pilot purchasing population and their linked Genuine/BVP alternatives, rather than selected top-selling examples. A full classification-only master is acceptable where permitted.

Include part number, description, AIM family/group/subgroup IDs and labels, Genuine/BVP/other/unclassified status, relevant service category where approved, classification version, source, effective dates and validation status. Include existing vehicle-applicability evidence where available; leave unknown applicability unknown.

Provide the approved rules for normalizing part numbers, handling superseded numbers, classifying kits and excluding administrative/non-part lines. Preserve original part numbers alongside normalized identifiers.

Keep ambiguous or unclassified parts visible in an exceptions table. Do not classify from description alone to fill gaps. A part's price class is not automatically its AIM family, and sharing an AIM family is not proof of technical interchangeability.

## Validated Genuine/BVP relationships - required for substitute comparisons

Export the authoritative Genuine-to-BVP relationships, including both part numbers, relationship type, direction where relevant, market applicability, vehicle/engine restrictions where documented, unit/pack basis, validity dates, technical source and approval status.

Distinguish a validated alternative from a supersession, a kit/component relationship or a general family association. Preserve multiple alternatives and one-to-many relationships; do not reduce them to a misleading single pair.

Identify whether the alternative is available in the relevant market where the source supports it. Distinguish confirmed absence of an alternative from missing catalogue coverage. Unknown stock or availability must not be treated as "available".

Explain the membership rules behind the existing Genuine-only, Genuine-with-BVP-alternative and BVP summary categories. Supply enough evidence to reproduce those categories, without treating all same-family parts as substitutes.

## Monthly purchasing and completeness - required, derived only

Reuse the existing transaction data when it is sufficient. Otherwise supply a clean derived table at distributor x purchasing account x month x part-number level, with a separate indicator for channel or scope where the source genuinely distinguishes it.

Include stable account ID, source account name, month, original and normalized part number, quantity, unit of measure, return/credit treatment, source reference and data-quality flags. Describe the represented activity explicitly as distributor-to-dealer sales. Identify wholesale or other account types where documented rather than silently combining them with assessed sites.

Provide all supported months in calendar 2025. Additional comparable dealer-level history is useful only if genuinely available; do not manufacture monthly history from annual totals or distribute network totals among dealers.

Supply a completeness table by account and month: complete, partial, not supplied, not applicable or unknown, supported by source evidence. A missing row does not automatically mean zero. Explain when a genuine zero can be inferred from a complete submission.

Explain overlapping files, replacement submissions, cumulative-versus-monthly records and deduplication. Keep network totals separate from their component dealer rows.

## Euro values and prices - document the basis; do not make costs mandatory

No additional ISZE supplier purchase-cost file or dealer selling-price file is required for the first connection.

For the euro values already present in the dealer summaries, establish precisely which price was used, its position in the supply chain, currency, market, effective date, tax basis, conversion method and treatment of missing prices. Provide the formula and source reference.

Where permitted, supply derived monthly/part valuations and a valuation-basis identifier so euro views can be reproduced. Any supporting price lookup must be approved and limited to the relevant parts and purpose; never attach a full price list. Do not send raw invoice lines.

Keep actual ISZE-to-distributor billing, actual distributor-to-dealer invoice values where available, and reference-price valuations separate. Do not present a reference-price valuation as dealer expenditure, dealer revenue or profit.

A single price snapshot applied to historical quantities is a constant-price valuation, not historical invoiced revenue or proof of pricing losses. Report unvalued quantities; a missing valuation is not zero euros. If the basis cannot be established, leave the euro view unavailable and retain the quantity evidence.

Keep supplier costs, margins and negotiated confidential conditions out of this first pack and out of browser files. Profitability can be a separately authorized internal addition.

## Meaningful IDS-to-AIM links and existing actions

Supply any existing approved mapping between IDS questions/sections and the commercial analysis they legitimately support. Include the IDS criterion ID, relevant AIM family or analysis type, rationale, supporting source and approval status.

Do not force a link from every IDS question to a parts family. A general staffing or premises question may have no direct parts-family interpretation. When an association is only proposed, mark it as proposed and keep it out of confirmed findings.

The connection may support a review question, not a causal conclusion. A self-assessment answer does not prove why purchasing changed, and no purchase of a part does not prove a missed repair or competitor sale.

If existing IDS follow-up actions are available, export action ID, linked site/criterion, action description, owner role, status, due date and source. Otherwise report that no existing actions are connected. Do not invent actions or write anything back to IDS.

## Context and comparison rules

Keep the commercial period, assessment round and source refresh dates distinct. Comparing calendar-2025 purchases with a later assessment is historical context, not evidence that the assessment improved or worsened sales. Supply period start/end dates and the approved fiscal-year labels; report inconsistent labels rather than silently reconciling them.

ITUK and IUK remain separate. UMI and UTI remain separate; UTI must not enter comparisons for the 2026 IDS round in which it did not participate.

Define the eligible dealer population for every network comparison. Do not rank partial submissions as poor performance. Do not assign a distributor an "audit score" or create a combined IDS/commercial score.

Existing PRISM fleet and service-demand information may be supporting market context. It is not a dealer fleet. Do not allocate market fleets or service gaps to dealers by purchasing share. Do not use the unusable fleet forecast beyond 2025. Keep measured purchases separate from modelled expected demand.

Do not use warranty as evidence of scheduled maintenance or purchasing losses. Keep non-quotable service-demand euro totals out of shared outputs. Do not add optional market, warranty, tender or competitor datasets merely to make the pack larger.

## Checks and delivery

Use the current approved sources and correction history, not whichever file happens to have the latest modification date. State which source/version governs each dataset and disclose unresolved conflicts.

Validate account/site links, questionnaire references, assessment revisions, part-number joins, duplicate keys, periods and units. Reconcile purchasing before and after classification so joins cannot multiply quantities. Report the quantities excluded or left unclassified and, only where a verified valuation exists, the associated value and valuation coverage. Confirm that dealer rows and network totals are not added together.

Show actual matching and exception coverage, not a fabricated pass rate. List failing checks, their impact and the specific outputs they prevent. Unresolved IDS links may block an assessment connection without blocking a valid purchasing view.

Return one ZIP with UTF-8 CSV or JSON tables, a README/data dictionary, source/version and coverage information, a valuation-method note, unresolved mappings and a validation report. Preserve identifiers as text and use unambiguous dates. Include no credentials, unnecessary personal data, raw line-level billing or full price lists.

In the README, give one worked journey using real, validated records: purchasing account -> assessed site -> recorded IDS item -> approved related AIM analysis -> actual monthly purchases -> validated BVP alternative, where applicable. Omit unsupported steps and explain why. An honest partial connection is preferable to an invented complete one.

Finish with a brief statement of what is ready to load, what remains disconnected and exactly which missing source or decision would enable each remaining function. Do not claim that the application has been updated.
