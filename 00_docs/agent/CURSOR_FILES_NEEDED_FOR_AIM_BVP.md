# Files needed for the next AIM Parts Universe version

Prepared: 20 September 2026.
Recipient: Cursor, for packaging existing data and assets only.
Implementation owner: ChatGPT will implement the interface, comparisons, image treatment and browser tests.

## The request

Prepare one ZIP named `AIM_BVP_SOURCE_PACK.zip`. This is an input request, not an instruction to build a dashboard or redesign a data process. Copy the existing authoritative files where possible. Keep their original names and describe them in a short README. Proposed column names below describe the information needed; they are not a requirement to rename working sources.

Do not hold the whole package while resolving tonnage or locating photography. Include the available files, state what is missing, and identify provisional inputs. A new build does not establish business approval of a source.

## Already available to ChatGPT: do not resend unchanged

- `AIM_Parts_Universe_v2.1.html`.
- `AIM_Cursor_Handoff_v2.1.zip`, including editable application source, aggregate data, build script and tests.
- `04_original_vs_value_parts_mix.csv`, historical distributor fleet summaries and the supplied dealer-sales summaries.
- The dated ISZE-to-distributor billing file already uploaded. Do not send another raw copy.
- The previously uploaded tonnage files and both tonnage briefs.
- `CURSOR_TONNAGE_FEEDBACK_2026-09-20.md` and `CURSOR_AIM_BVP_VISUAL_DIRECTION.md`.

Only include newer application source or changed datasets if Cursor has made changes after that delivery. Identify the preferred starting version and briefly describe the changes. ChatGPT cannot see files merely because they exist on the Windows machine; include actual files in the ZIP rather than shortcuts or local links.

## Essential data: complete AIM structure and the part master

Provide the authoritative AIM hierarchy and part-number classification, not only the service-part subset. The hierarchy should include defined categories even when no purchases are recorded.

For the hierarchy, provide stable codes, parent codes, display names and the actual levels used by AIM. Do not force it into an invented number of levels.

For each part number, provide its description, hierarchy assignment, Genuine/BVP classification where established, mapping version and status. Include effective dates where maintained. Keep part numbers as text and preserve leading zeros. Keep unclassified and unresolved records explicit. Explain whether the mapping is current and applied retrospectively or historical by period.

Existing files such as `bvp_pn_dimension.csv` and `pms_capture_supplement.csv` can help, but are not a substitute for the complete hierarchy and its wider part mapping. Include the existing authoritative master under its real filename; do not fabricate a consolidated classification to satisfy this request.

This enables the full portfolio overview and genuine family-to-category-to-part navigation. An incomplete catalogue can still be used, but its scope must remain labelled.

## Essential data: Genuine/BVP relationships

Provide the existing `genuine_bvp_crossref.csv`, or its authoritative successor, with relevant metadata. Remove price-list columns from a copy if the source includes them; do not attach a full price list.

The useful fields are the Genuine part number, BVP part number, relationship type, applicable range/market or qualifications, evidence source, validation status and effective dates if maintained. Keep multiple alternatives where they exist.

A supersession, predecessor, similar description or shared family is not automatically a Genuine/BVP alternative. Unvalidated candidates may be supplied if their status is explicit; they will not be shown as approved pairs. The application must not duplicate billing when a part has several relationships.

If a distributor-specific BVP range or availability file already exists, include it with its effective period. Otherwise state that eligibility by distributor is unavailable. A global catalogue relationship alone must not be treated as proof that a distributor could order that part in a particular month.

This enables authentic product pairings and a distinction between all-family mix and mix within a confirmed eligible range.

## Essential data definitions: billing basis, coverage and controls

ChatGPT already has dated billing and can derive monthly summaries. Do not ask Cursor to build a new reporting process or resend transaction lines.

Provide the exact existing inclusion/exclusion rules or the relevant extraction/aggregation code, the distributor-code mapping used by that code, and available approved control totals. Explain the treatment of returns, credits, transport, rebates, administrative items, excluded entities, currency and rounding.

The current application has category summaries on an exclusion-filtered basis and documented example histories on a signed-billing basis. They must not be quietly joined and represented as one reconciled book. Identify the intended basis and the known differences.

Provide a coverage note or existing coverage table by distributor and month, stating source completeness, date boundaries and the part population included. Distinguish months with a complete source and no purchases from months with no source. Do not infer source completeness from the presence of at least one invoice or twelve months with activity.

Provide the available current verification report and relevant reconciliation results, including failed or provisional checks. Do not declare the wider data verified merely because one subtotal reconciles. Do not silently substitute old control totals for a changed snapshot.

An already approved monthly aggregate is welcome instead of asking ChatGPT to reproduce the aggregation. Preferred detail is one row per distributor, calendar month and part number on one named billing basis. Include recorded euros, currency and coverage references; quantities are optional and need consistent unit definitions. The part master supplies the hierarchy and tier without multiplying rows.

A family/category-by-tier monthly summary is sufficient for ribbons and movement comparisons, but not exact part-level histories. Clearly state when finer detail is unavailable. Include unmapped amounts in reconciliation rather than dropping them.

Use the actual approved billing horizon. The currently supplied material ends on 30 June 2026. Any later data needs its own coverage and verification information. No annualisation or invented monthly allocation from annual totals.

## Product assets already held in the workspace

Include original, highest-resolution Genuine and BVP photographs available in internal catalogues, marketing folders, approved media libraries or supplier-provided material. Start with a coherent photographed pair or a few well-supported categories rather than delaying the package for the whole catalogue.

Useful initial subjects include filters, brake components and clutch parts, where real assets and documented relationships exist. This is a production preference, not a claim that every such pair exists.

Prefer original JPG/PNG/TIFF/WebP files over slide screenshots, thumbnails or enlarged low-resolution images. Include real alternate angles, macro photographs and turntable sequences if already available. Do not manufacture extra angles or internal geometry.

Provide a simple image index, for example:

`filename | exact_part_number_or_category | tier_if_known | exact_or_representative | source | owner_or_permission_status | permitted_edits | notes`

Unknown ownership, uncertain identity and unavailable permissions should be stated, not presumed. Link a family-representative image to the family rather than to an exact selected part. A product label or packaging photograph can help establish identity but does not alone establish permission to reuse an image.

Only include approved 3D source assets if already available with documented identity and rights. A model search, purchase or new CAD exercise is not required for this package. The sales cube is being removed; photographic product comparisons are the priority.

ChatGPT will handle public-source image research and browser-ready image preparation. Cursor only needs to package internal assets already available. If none are available, write 'No original product assets found' in the README and send the rest. New real studio photography requires a physical shoot; it is not replaced by generated images labelled as exact parts.

## Brand assets

Provide the exact red, blue and white colour values used in the approved presentation, plus the applicable Isuzu and BVP logo artwork. Preferred logo assets are SVG or original transparent PNG.

A theme export or a clean representative presentation file is acceptable when the colour values are not separately documented. Avoid unnecessary commercially sensitive slides. State the font name only; no font files are needed. No new brand guide needs to be produced.

The design will use Genuine and BVP labels. BVP can be expanded once as Best Value Parts. Internal legacy field names need not be renamed just to change the visible wording.

## Optional later inputs: not blockers for this version

- Corrected tonnage evidence, after the separate feedback is addressed: authoritative applicability mapping, disjoint billing aggregates, historical fleet references, coverage definitions and any applicable schedule evidence. Do not split shared parts or market actuals using fleet proportions.
- ZKK-to-part mapping, only if already authoritative and approved. Otherwise its comparison remains unavailable.
- An approved matching cost basis, only for a separately requested profit feature. Do not send the full price list or derive profit from assumed margins.
- More extensive photography or validated vehicle assets. Do not delay a useful photographed pair while seeking a complete vehicle model.

## README and packaging

The README should identify the snapshot date, application starting version, files included, source paths for traceability, scope, mapping versions, billing basis, coverage, permission status and missing items. Source paths document provenance; they do not replace actual attachments.

Existing names and folders are fine. A possible organisation is:

```text
AIM_BVP_SOURCE_PACK.zip
  README.md
  classification/
  relationships/
  billing_definitions_and_controls/
  monthly_aggregates/          # Only if already available and approved
  brand/
  product_images/
  updated_app/                # Only if changed after v2.1
  tonnage_updates/             # Only when ready; not required now
```

Do not include raw billing, invoice-level data, customer personal information, credentials, the full price list, unrelated historical dashboard copies or an entire workspace archive. Required monthly or annual derived summaries are distinct from raw line-level billing and must be approved for this use.

## Work ChatGPT will implement

ChatGPT will remove the sales cube, apply BVP wording throughout, retain the full portfolio navigator, implement linked Genuine/BVP ribbons and product comparisons, and add purchasing-change views where the supplied definitions support them. It will prepare suitable image derivatives, retain missing/zero/negative distinctions, reconcile view totals and test navigation, exports and offline behaviour.

No tonnage performance claim, exact product identity, full-catalogue claim or historical comparison will be added merely because the interface can display it.

## Source basis

This request builds on the actual contents of `AIM_Cursor_Handoff_v2.1.zip` inspected on 20 September 2026, the existing `CURSOR_AIM_BVP_VISUAL_DIRECTION.md`, and the project rules in `00_READ_ME_FIRST.md` and `04_GLOSSARY_AND_HOW_TO_WRITE.md`. It asks for missing inputs; it does not claim those inputs exist or have been approved.
