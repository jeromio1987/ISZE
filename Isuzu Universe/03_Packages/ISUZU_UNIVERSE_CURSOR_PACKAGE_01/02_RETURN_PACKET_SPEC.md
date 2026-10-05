# R0 return package specification

Return one ZIP with the following structure. Prefer one explanatory report over many overlapping notes.

```text
R0_RETURN/
  R0_REVIEW.md
  SOURCE_MANIFEST.json
  TASK_DISPOSITION.json
  MANIFEST.json
  ORIGINALS/       # Permitted original paper/critique or clearly labelled extracts.
  EVIDENCE/        # Labelled screenshots, bounded snippets, actual test results.
```

The two directories may be empty if inputs are unavailable or copying is not permitted. Say why in the report and manifest. The mandatory files may not be replaced by generic completion messages.

## R0_REVIEW.md

Include these exact headings, in this order:

- Executive summary
- Inspected baseline
- Original paper and critique
- Protected feature baseline
- Source packs and data eligibility
- Code reuse and PRISM
- Executed checks
- Backlog disposition
- Open questions and next work order

The summary contains ten complete, unnumbered lines. Each substantive finding refers to a source path, section, screenshot or test record. Distinguish observed, reported, inferred and unverified statements. Explicitly state whether any safe-run temporary files were created and where.

The critique index states original location, criticized claim, supporting reference, affected roadmap task and evidence status. The actual accept/partly accept/rebut/defer decision belongs to the subsequent ChatGPT review. Do not fill that decision column speculatively.

Feature status uses present, partial, absent or unverified. Source findings must include transaction direction, value basis and period, not just file names. Numerical observations stay tied to the source's actual scope.

## SOURCE_MANIFEST.json

Top-level keys: `work_order`, `inspected_at`, `sources`, `missing_inputs`.

Each source records `source_id`, `path`, `kind`, `version`, `sha256`, `modified_at`, `commercial_level`, `row_grain`, `period_start`, `period_end`, `reporting_clock`, `row_count`, `schema`, `value_basis`, `supersedes`, `status`, `limitations`, and `evidence_refs`.

Use null for an unknown value and explain it in `limitations`. Record a hash for actual inspected files where feasible; a directory is not a file hash. Commercial level may be isze_to_distributor, distributor_to_dealer, dealer_to_customer, reference_price, fleet, assessment, part_applicability, documentation or mixed_or_unknown. A convenient filename does not prove the level.

If no required source is available, leave `sources` empty and record the missing inputs; never supply fictional example sources as real findings.

## TASK_DISPOSITION.json

Top-level keys: `work_order`, `tasks`, `next_work_order_recommendation`.

Include at least C01-C07. Each task has `id`, `inspection_status`, `product_disposition`, `evidence_refs`, `finding`, `blocked_on`, and `next_action`.

`inspection_status`: evidence_returned, blocked, or not_run.

`product_disposition`: already_satisfied, required, blocked, conditional, not_relevant, or not_reviewed.

An already-satisfied or evidence-returned claim requires an evidence reference. Do not mark a later task required solely because its implementation has not been inspected. Do not mark ChatGPT's review or ISZE's approval as completed by Cursor.

## MANIFEST.json

Top-level keys: `work_order`, `inspected_build`, `files`, `missing_items`, `redactions`, `privacy_review`.

Each file entry contains a safe relative `path`, `sha256` and `purpose`. Include every return file except MANIFEST.json itself. Paths must remain within the return directory. Exclude original restricted records, full price lists, credentials, browser profiles, caches and unrelated source code.

`privacy_review` records an actual inspection, not an automatic assertion: `status` is completed or incomplete and `notes` explains redactions or residual restrictions.

## Structural validation

From a location containing Python, use:

```text
python VALIDATE_RETURN.py <path-to-R0_RETURN>
```

The script reads the package and checks required files, headings, IDs, dispositions and hashes. It does not modify files. It does not certify the business analysis, completeness of the critique review or permission to share. A structural pass does not close G0.
