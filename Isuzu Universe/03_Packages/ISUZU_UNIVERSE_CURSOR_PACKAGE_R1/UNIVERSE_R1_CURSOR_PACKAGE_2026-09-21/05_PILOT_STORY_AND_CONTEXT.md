# Connected review | interaction and action contract

**R1 status:** Synthetic prototype only. No user-facing ITUK results or persistent production action store.

## The first useful story

Start in **Monthly review**, not in a tender feed or animated map alone. The page shows the selected distributor, commercial period, source coverage and measurement basis. Three persistent destinations make the pillars explicit: Parts / AIM, Dealer standards / IDS, and Commercial analysis / PRISM. Network and Actions connect them. Market references and Tenders are supporting destinations.

A user selects a family in the portfolio. The same family filters the eligible commercial purchasing list; verified-location accounts appear on a map, and unmapped accounts remain in a visible tray included in the correct totals. Selecting an account exposes its measured quantities and separately labelled reference values. A time trace breaks across missing months rather than drawing a decline to zero.

A PRISM panel shows the supported commercial comparison. If it has only market data, its badge says **ITUK market context - not this account**. It does not silently accept a dealer filter or apportion market demand.

The IDS panel is either linked through an approved relationship, not available, or independent. A synthetic unresolved case must explicitly show **No approved commercial-to-IDS link**. Allow an independent assessment selection, but do not imply a merged record. Show round/version and **assessment date not supplied** where appropriate; a file timestamp is not the assessment date. A total-only record must not generate question or section scores.

The user drafts one action with its originating observation, source pin, family/account scope, owner, due date and next review question. The action references the evidence snapshot, not a mutable 'latest' URL alone. The next comparable observation is a separate item; the old evidence remains attributable.

## Shared context model

```json
{
  "distributor_id": "ITUK",
  "commercial_clock": "CY",
  "commercial_period_start": "2025-01",
  "commercial_period_end": "2025-12",
  "source_snapshot_id": "synthetic-r1",
  "aim_release_id": "synthetic-aim",
  "aim_family_id": null,
  "measurement_basis": "quantity",
  "commercial_account_id": null,
  "site_id": null,
  "identity_link_state": "unresolved",
  "ids_selection": {
    "assessment_id": null,
    "round": null,
    "assessment_date": null,
    "selection_mode": "independent"
  },
  "prism_scope": "market",
  "tender_as_of": null,
  "market_reference_vintage": null
}
```

Commercial and IDS selections are deliberately separate. Valid context persists between views and back navigation. Changing the account must clear an incompatible site/assessment association; changing the distributor must clear unauthorised or incompatible subordinate selections. Market-level metrics may retain the distributor context but must visibly ignore an unsupported account filter. No action or export may carry a stale hidden selection from another account.

## Synthetic acceptance scenarios

Use a validated one-account/one-site example, an unresolved account, and a multi-site account with no allocation. Make map labels synthetic and do not use real dealer names, coordinates or commercial history. Include a missing month, an unpriced part, an unclassified part and a market-only model. Use a representative small family for a meaningful unit-compatible quantity comparison.

Test account selection, family change, period change, back navigation, measurement-basis change, unlinked IDS behaviour, multi-site behaviour and action draft creation. Verify that the selected source snapshot survives into the draft and that blocked calculations explain why they are blocked. Provide keyboard-focus order and a list/table equivalent to the map.

## Minimum action schema (C37, brought forward)

`action_id`, `origin_pillar`, `distributor_id`, `commercial_account_id` when supported, `site_id` only when approved, `aim_family_id`, `observation`, `source_snapshot_id`, `evidence_reference`, `action_text`, `owner`, `created_at`, `due_date`, `status`, `last_evidence_date`, `completion_evidence`, `review_outcome`, `visibility_scope`.

An IDS question/section reference is optional and requires actual question-level evidence. A parts-review action is not invalid because it lacks an IDS reference. R1 drafts are synthetic/session-local, visibly non-persistent. Production persistence and permissions need a later work order.

## DLOD extension (C43)

Minimum optional fields: case ID, account, family/part and unit/quantity if available, source date, competitor-evidence reference and product-match state, requested support, approved support, decision date, reported outcome, follow-up period and supporting observation. Separate requested, approved and paid amounts. Do not collect dealer resale margin as an entry requirement or set a required resale price. Historic annual support is not a reconstructed case outcome.

## Tender extension (C44)

A notice records source/identifier, title, country, actual product/contract scope, publication date, deadline, last check, source link, relevance explanation and optional status. Unknown freshness is visible. No synthetic notice is presented as live; no count is monetised. A missing feed is a useful empty state, not an invented tender.

## Visual direction

Use the existing dark navy/charcoal and restrained Isuzu-red direction, with strong type hierarchy and clear unit/basis labels. The signature behaviour is coordinated exploration with retained context, not decoration. Keep the broad portfolio accessible; no sales cube or product photography. Do not use colour alone for evidence states or map 'performance'. An absent denominator is a textual limitation, not a red failing dealer.
