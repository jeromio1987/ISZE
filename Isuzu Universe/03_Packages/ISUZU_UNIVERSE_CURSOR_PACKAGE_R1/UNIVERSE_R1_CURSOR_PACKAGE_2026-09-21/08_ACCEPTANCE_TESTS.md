# R1 acceptance tests

**Status:** Prescribed tests, not results. Cursor records actual outcomes against exact pinned sources or synthetic fixtures. A successful negative test means the invalid input was rejected as intended. `blocked` and `not_run` never count as pass.

Run relevant tests in isolation using existing dependencies. No production refresh is authorised. Record input hashes, exact command, expected/observed result and evidence reference. Return all failures and blockers.

| ID | Test | Valid condition | Intentional counterexample | Expected rejection |
|---|---|---|---|---|
| T01 | Source pin | Hashes, lineage, cutoff and consumer refer to exact inputs. | Alter a checksum or silently use another AIM file. | Input/version check rejects the altered input. |
| T02 | Commercial level | Upstream billing and downstream quantities are separate facts. | Add downstream valuation to billing as one revenue total. | Metric contract rejects mixed-level total. |
| T03 | Row grain and controls | Monthly facts reconcile to compatible annual/dealer controls. | Include annual summary and month rows in the same sum. | Double counting is detected; controls excluded from observations. |
| T04 | Keys and join conservation | Raw part/account identifiers preserved; one classification or unmatched result per fact. | Introduce duplicate canonical PN labels or a normalisation collision. | Join amplification/collision is reported and blocked. |
| T05 | Signed quantities | Returns and adjustments follow documented source convention. | Drop negative rows or flip their sign. | Reconciliation fails with a signed-value exception. |
| T06 | Period completeness | Complete periods established from source coverage; CY and FY separate. | Treat missing month as zero or sum CY and FY. | Unknown state preserved; mixed-clock calculation rejected. |
| T07 | Historical scope | CY2025 dealer panel identified as historical; network history separate. | Allocate 2026 network totals into 2025 dealers to imply current activity. | Unsupported dealer history is rejected. |
| T08 | Reference valuation | Eligible signed quantity times documented price/unit/currency; unpriced remains unknown. | Use missing price as zero or label reference value as dealer invoices. | Unpriced coverage/semantic failure visible; no revenue label. |
| T09 | Fleet denominator | Only verified appropriate fleet supports a per-truck metric. | Copy or sales-allocate market UIO into dealer rows. | Dealer euro-per-truck unavailable; field quarantined. |
| T10 | Classification-only adapter | No accidental AIM billing values enter dealer facts/payload. | Add l12m_billed_eur from full AIM master to a dealer view. | Unscoped commercial field rejected and totals unchanged. |
| T11 | Mix and alternatives | Category mix and approved part alternatives have separate contracts. | Treat same family as fitment approval or undefined capture as market share. | Part-alternative/capture assertion blocked. |
| T12 | Unit and denominator | Mix uses compatible units or a declared value basis with valid denominator. | Aggregate pads and kits as service counts, or render share with zero/negative denominator. | Unsupported total/share withheld with explanation. |
| T13 | Identity | Approved relationship used only at supported account/site grain. | Fuzzy-match an account to IDS or duplicate an account across sites. | Link remains unresolved; account totals not duplicated. |
| T14 | Geography | Verified account location represented; unmapped still in totals/list. | Infer distributor from country, invent a location or rank underperformance without fleet. | Invalid mapping/performance claim rejected. |
| T15 | IDS scope/date | Available round, totals/detail and unknown date shown faithfully. | Create question scores or use file timestamp as assessment date. | Unsupported detail/date rejected; no distributor audit label. |
| T16 | Tonnage v2 | Exclusive purchasing, modelled demand and market actuals remain distinct. | Sum also_fits_band, allocate shared parts or multiply repeated market actuals. | Non-additive/allocated result blocked without reopening resolved v1 issues. |
| T17 | PRISM parity | Same pinned inputs/basis produce matching reused metric or documented blocker. | Substitute another model vintage or account-allocate a market output. | Parity/scope failure identified; no false validation. |
| T18 | Context navigation | Distributor/family/period/basis persist; account change clears incompatible IDS link. | Leave old account/assessment filter in hidden state. | Stale association cleared or blocked with explicit state. |
| T19 | Action evidence | Draft links to exact source snapshot and permitted account/market scope. | Create an action using another account or unapproved IDS question. | Invalid evidence link blocked; optional IDS relationship stays optional. |
| T20 | Boundary and privacy | All writes inside fresh work root; returned prototype is synthetic. | Embed dealer-named detail, broader billing or private identity table. | Payload/export inspection fails; excluded material is not returned. |
| T21 | Empty and unavailable modules | Tender/price/IDS absence is visibly labelled and no current fact invented. | Show synthetic notices/prices as current observations. | Synthetic/unavailable state enforced. |
| T22 | Usability | Keyboard/list alternative and readable essential labels support the review task. | Require hover/colour/map-only interpretation to understand a limitation. | Scenario fails usability until textual/keyboard alternative is available. |

## Gate interpretation

Data eligibility requires its applicable T01-T17 checks and review of every residual; not all tests apply to every optional module. A blocked tonnage model blocks the model-dependent feature, not all independent commercial quantities. Synthetic interaction acceptance uses T18-T22 and relevant semantic fixtures; it does not close real-data eligibility. Cross-distributor production isolation, persistent action permissions, recurring feed operation and recovery remain later release tests and cannot be certified by a synthetic static page.

## Minimum recorded result

Each `DATA_CHECKS.json` entry includes `id`, `scope`, `status` (`pass`, `fail`, `blocked`, `not_run` or `not_applicable`), `expected`, `actual`, `command`, `input_hashes`, `evidence_refs` and `reason` when not passed. State whether a test is positive or negative. A screenshot is supporting evidence, not an arithmetic or interaction proof by itself.

## Required JSON wrappers

Use `{"work_order": "R1", "tests": [...]}` for `DATA_CHECKS.json`, `{"sources": [...]}` for `SOURCE_MANIFEST.json`, and `{"tasks": [...]}` for `TASK_DISPOSITION.json`. `MANIFEST.json` contains `files` entries with `path` and `sha256`, plus `redactions` and `missing_items` arrays. The manifest does not hash itself.
