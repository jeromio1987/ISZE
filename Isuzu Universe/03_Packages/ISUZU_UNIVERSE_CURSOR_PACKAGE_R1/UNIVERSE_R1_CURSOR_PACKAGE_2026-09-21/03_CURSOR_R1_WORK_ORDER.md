# Cursor R1 | ITUK certification + connected-review prototype

**Authority:** This work order only.  
**Input:** R0 return dated 21 September 2026; roadmap R2 and attached contracts.  
**Output:** `R1_RETURN_2026-09-21_01.zip`, no application release.

## Mission and limits

Advance from an asset inventory to a testable ITUK commercial slice. Work on two independent streams: certify data/reuse, and demonstrate the proposed interaction using synthetic data. Do not make a production application change merely because the expected application directory is absent.

Do not install dependencies, commit, push, reset, clean the working tree, deploy, open a public link, initiate external scraping, change authentication, start customer-facing services, alter source datasets or refresh production derived data. Do not email participants. Do not change stored Cursor rules, workspace policies or other projects. The wider ISZE working tree is already dirty; preserve unrelated work.

### Authorised local boundary

Starting inspection folder:
`C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe`

Verify it locally. Do not recreate the absent `Isuzu Universe\UNIVERSE` path to make an old work order appear correct. Resolve relevant local `.lnk` targets and `INDEX.md`; inspect known atlas builders and PRISM paths. Scope discovery to these known ISZE assets, not all private folders or the entire Desktop.

Create a fresh work directory:
`C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_STRATEGY\_ORCHESTRATION\R1_2026-09-21_01`

If it exists, use the next unused suffix and record it. All code, temporary files, logs, caches, local derived audit output, browser profiles and prototype files must remain inside that fresh directory. Read existing assets without modifying them. Set temporary/cache/output paths explicitly. A command that cannot respect that boundary must be reported as blocked or replaced by an isolated check, not run anyway.

## Stream A | exact sources, measurements and reuse

### R1-A | Resolve the host and build provenance

Reuse R0's file inventory. Inspect the reported shortcut targets, `INDEX.md`, build scripts and relevant app entry points to explain which source generates which output. Search for the claimed build identity only in those bounded assets. Return the actual source revision and dirty-file snapshot at start/end. Separate existing source, generated HTML copies and potential hosts.

Deliver `EVIDENCE/HOST_AND_REUSE.md` with actual paths, hashes, entry commands, existing dependencies, side effects, observed version labels and recommended smallest adaptation. 'Host not located' is a legitimate result; it does not block data certification or the synthetic prototype. No architecture decision or framework migration is delegated here.

Legacy coverage: residual C01, C05, C06; inspection-only portion of C41.

### R1-B | Pin and profile the actual inputs

Read the local ITUK pack notes/manifest and actual data, AIM export and corrected tonnage-v2 readme/log/evidence. Do not start from column names alone. At minimum inventory:

- ITUK CY2025 dealer quantities and dealer aggregates; network-only history; pricing/context and replenishment files.
- `AIM_Master_PN_Categories_Figkey_20260921.csv` as a candidate classification release, with actual lineage and live consumer paths.
- Relevant PRISM modules, documentation, metric inputs and existing verification entry points.
- IDS ITUK populations/round metadata and potential commercial-account location sources; no approval inferred from overlaps.
- Current tender source metadata and existing Kaizen/DLOD artefact locations only, without importing sensitive records into the return.

Return file checksum, record grain, raw/canonical keys, period coverage, complete-month evidence, commercial level, pricing basis, row counts and limitations. Preserve reference paths for the raw fact where allowed; no source-data rewrite. Candidate pins stay candidates until tests support their use.

Legacy coverage: C08-C09, C11-C12 and C13.

### R1-C | Reconcile ITUK quantities before interpretation

Profile `grain`, `period_grain`, `year`, `period`, flags and signed quantities. Establish which rows are observations and which are year/network controls. Reconcile monthly facts to annual controls, dealer totals and network totals where compatible. Check whether returns/credits, zero rows, duplicate keys, aliases or unvalued records explain differences. A mismatch must remain visible with an explicit explanation; never force agreement by dropping records silently.

Reconcile before and after the classification join. Every eligible fact retains exactly one classification result or one unmatched status; detect one-to-many amplification. Part-number normalisation preserves raw values, leading zeros and collisions. Stable dealer identifiers distinguish commercial accounts from sites. Account-name normalisation creates candidate aliases, not approved relationships.

Use the 64 aggregate rows and 101,341 detail rows only as reported control expectations to investigate, not assumed exact accepted facts. Quantities use exact comparison where the source definition permits it; document any justified numerical tolerance before applying it.

### R1-D | Audit monetary, fleet and comparison fields

Trace `uio_units`, `sellout_spu_eur`, `contested_bvp_capture`, `total_eur`, `eur_basis`, `qty_unvalued_share` and the Genuine/BVP components. Provide a field disposition: usable as recorded quantity, usable as documented reference valuation, market context only, excluded or unresolved.

No dealer euro-per-truck unless a genuine dealer fleet denominator is independently established and approved. No allocation of market fleet to make that measure available. Do not label a reference-valued amount dealer turnover, invoice revenue, actual gross profit, market capture or savings.

Keep the AIM `l12m_billed_eur` field outside the default classification adapter and customer payload. Test that it cannot multiply into dealer values or disclose wider-market billing. Validate category-mix eligibility separately from documented part-level Genuine/BVP alternatives.

Reconcile reference values only against the same price basis, period and currency. Show signed amount plus priced/unpriced coverage and exceptions; never multiply missing prices by zero. Do not subtract dealer reference valuation from upstream invoicing and call the difference stock movement or revenue loss.

Legacy coverage: C10-C14. The attached metric contract governs interpretation.

### R1-E | Prove a reusable PRISM boundary and identity state

Inspect actual PRISM loaders and one relevant selected metric path. Prefer calling an existing pure calculation in an isolated environment. Where import triggers writes, network traffic or app startup, document the risk and use a narrow local adapter only after isolating those side effects; do not rewrite production algorithms. Return lineage and a bounded parity check against the same input/basis, or `blocked` with the exact missing dependency.

Keep national GPS/PMS/expected-demand context national. Do not allocate it to dealers without a justified source. Reusing PRISM does not authorise adopting it as the multi-distributor application host.

Create a private local candidate identity table with account ID, source name, candidate site, relationship type, evidence, validity and approval status. Unapproved mappings remain unresolved. Include only redacted counts and synthetic examples in the return. Location validity and IDS responsibility are separate relationships. An account serving multiple sites remains an account-level purchase measure.

Legacy coverage: bounded C15 and C41; no full C19 implementation.

### R1-F | Preserve tonnage v2 and run targeted regression checks

Start with v2 correction evidence. Mark each prior issue as corrected, blocked, not applicable or a reproduced regression. Do not repeat v1 complaints already addressed. Re-run only safe, relevant checks against exact pins; do not rebuild a model just to turn a warning green. Keep stale/blocked model states visible. The three tonnage views and non-additive fields remain separate.

Use `08_ACCEPTANCE_TESTS.md`. Return both valid cases and intentional counterexamples. Distinguish a successful negative test (bad input correctly rejected) from a failing application check. The historical 153-pass report is context, not the result of this run.

## Stream B | isolated synthetic interaction prototype

### R1-G | Demonstrate one useful end-to-end review

Create a self-contained HTML prototype and small source files under this work directory, reusing the existing visual language where available. Do not fork or overwrite an existing dashboard. No framework/package installation. No image-generation assets, photography or sales cube.

Use exclusively synthetic labels, quantities, map coordinates and records, conspicuously labelled **SYNTHETIC INTERACTION PROTOTYPE - NOT ITUK RESULTS**. A schematic map is acceptable; no fake real dealer locations. Include three synthetic commercial accounts: a validated link case, an unresolved account and a multi-site account that cannot be allocated. Include an unknown period, unpriced row and market-only PRISM measure.

Implement the single journey in `05_PILOT_STORY_AND_CONTEXT.md`: portfolio -> family -> map/list -> dealer commercial detail -> PRISM context -> independent or linked IDS pane -> action draft. Preserve the valid context and expose incompatible levels. Draft actions stay session-local; do not imply operational persistence or authentication. An explicit export may contain synthetic data only.

Tenders and Market references may appear as clearly labelled future/empty panels. Do not invent current notices, prices, outcomes or source permissions. Home remains the monthly commercial review.

Use existing installed browser tooling where available, with profile/cache files inside the work directory and no external connections. Otherwise return the prototype and mark browser checks `not_run`. Screenshots alone do not close interaction acceptance.

Legacy coverage: prototype-only subsets of C29, C32 and C33. Existing product preservation is mandatory; this does not close full G4.

## Return contract

`R1_RETURN/` must contain:

| Path | Required content |
|---|---|
| `R1_REVIEW.md` | Decision summary; source eligibility; failures/blockers; exact scope; smallest R2 recommendation |
| `MANIFEST.json` | Relative paths and SHA-256 for every returned file except the manifest itself; redactions; missing items |
| `SOURCE_MANIFEST.json` | Actual pins, lineage, scope, field meanings and exclusions; no fabricated approvals |
| `TASK_DISPOSITION.json` | Per-subtask evidence and full/partial scope; no whole-task completion from a partial prototype |
| `DATA_CHECKS.json` | Test IDs, status, expected/actual result, exact command, input hashes and evidence references |
| `EVIDENCE/HOST_AND_REUSE.md` | Host discovery result, exact reusable metric, side effects and implementation recommendation |
| `EVIDENCE/RECONCILIATION.md` | Aggregate arithmetic, controls, residuals and field quarantine; names removed |
| `EVIDENCE/IDENTITY_AND_COVERAGE.md` | Account/site/IDS distinctions, approved/unresolved counts, period coverage and unmapped treatment |
| `EVIDENCE/TONNAGE_V2_DELTA.md` | Only unresolved checks or reproduced regressions; preserved corrections |
| `EVIDENCE/COMMANDS_AND_RESULTS.md` | What actually ran, timestamps, exit states, dependency blockers and historical-only checks |
| `EVIDENCE/INTERACTION_TESTS.md` | Scenario steps and observed results; screenshots labelled synthetic; unrun tests visible |
| `EVIDENCE/PRIVACY_AND_CHANGE_REVIEW.md` | Before/after changed-file boundary, archive/payload inspection and excluded private artefacts |
| `PROTOTYPE/index.html` | Self-contained synthetic prototype; no real account payload |
| `PROTOTYPE/context_contract.json` | The implemented state model and unsupported-scope rules |

A failed or blocked data check still belongs in the return; do not omit the package until every item is green. If a source is unavailable, keep its manifest record and state the affected feature. A synthetic prototype can still pass its interaction scope independently.

Run the supplied structural validator. Report separately: package integrity, numerical correctness, interaction correctness and privacy/change review. None substitutes for another.

## R1 completion and R2 stop line

R1 completes when the evidence is reproducible and candid, the synthetic flow is available or its blocker documented, and the exact next build boundary is proposed. It does not require all missing sources to be invented or all business decisions to be resolved.

Stop before real-data UI binding, production loader changes, persistent action storage, external pilot access, customer exports, release or a new application host. ChatGPT reviews the return; Jerome/ISZE retains business approvals. A later R2 order will authorise only the accepted slice.
