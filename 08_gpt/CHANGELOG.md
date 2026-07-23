---
sensitivity: internal
upload-to-gpt: false
---
# GPT Enterprise Context Pack — CHANGELOG

Tracks every change to the 6 Knowledge MDs and 2 Templates.  
Use this before each upload batch to identify what changed since the last sync.

---

## How to use

1. Before uploading to GPT Enterprise: compare `last-updated` in each file's YAML tag against `last-synced-to-gpt`.  
2. Only re-upload files where `last-updated > last-synced-to-gpt`.  
3. After uploading: update `last-synced-to-gpt` in the YAML tag and add an entry here.

---

## v1.1 — July 2026 (FACTS.md reconciliation)

**Author:** Claude (Cowork) on behalf of Jérôme Van der Pluym
**Date:** 2026-07-09

### What changed (vs May 2026 upload state)

| File | Change | Sensitivity | Upload now? |
|------|--------|-------------|-------------|
| `Active_Projects_Apr2026.md` | Rewritten: PMS section replaced stale 9.8%→17.3% capture figures with adopted IML v7 "Model B" (35.1% oil filter, €2.04M gap). Lubricants section split into live Shell/UMI channel vs unsanctioned BESCO scale-up (was conflated, wrongly said "FY2027 launch confirmed"). AIM section updated to current ~98.2–98.4% classification / €1.12M open residual (was stale ~87%). UIO bumped to v19 label with an explicit caveat that headline totals are unconfirmed against v19. Competitiveness Dashboard flagged stale (last calibrated March, refresh never happened in June as this changelog's own prior entry planned). | confidential | ✅ Upload after Jerome reviews the caveats (esp. UIO figures, AIM revenue/GP figures) |
| `Pricing_Logic.md` | No factual changes — formulas, FX table, ITUK "Key Numbers" all re-checked against `pricing-basket-2026.md` (verified 2026-06-29) and still correct. Added caveat that a newer price file (`Price file 2026_full.xlsx`, 16 Jun) exists and line-item PR00 prices haven't been checked against it. | confidential | ✅ Re-upload if not synced |
| Other 6 files | Not reviewed this pass | — | — |

### Known gaps / things NOT done in this pass
- Did not verify `Price file 2026_full.xlsx` against the line-item PR00 prices in `Pricing_Logic.md` — flagged, not resolved.
- Did not re-verify UIO v19 grand totals — flagged, not resolved.
- Did not re-verify AIM network revenue/GP figures (€32.4M/€14.6M/45.0%) or Rev/Vehicle benchmarks — flagged, not resolved.
- Competitiveness Dashboard content itself not yet refreshed (separate in-progress task) — this pack now says so explicitly instead of implying it's current.
- `UIO_V17_File_Guide.md`, `ISZE_Company_Context.md`, `Glossary_and_Terms.md`, `Jerome_Working_Style.md`, `Email_Templates.md`, `Analysis_Frameworks.md` not reviewed — unknown drift status.

**Manual upload to GPT Enterprise still required — Claude cannot do this step.**

---

## v1.0 — May 2026 (initial CHANGELOG created)

**Author:** Claude (Cowork) on behalf of Jérôme Van der Pluym  
**Date:** 2026-05-12

### What changed (vs April 2026 upload state)

| File | Change | Sensitivity | Upload now? |
|------|--------|-------------|-------------|
| `Active_Projects_Apr2026.md` | ⚠️ STALE — UIO v9 listed (current: v17), lubricants still "Awaiting IML" (IML signed off May 2026), AIM listed as "Live CY2025" without noting classification complete. Needs rewrite before next upload. | confidential | ❌ Hold — refresh first |
| `UIO_V13_File_Guide.md` | ⚠️ STALE — describes v13 structure. Canonical is v17 (May 2026, 9 sheets, cohort model, 90% override fix). Needs replacement with v17 guide. | internal | ❌ Hold — replace with v17 guide |
| `Pricing_Logic.md` | No content change. YAML tag added. | confidential | ✅ Re-upload if not synced |
| `ISZE_Company_Context.md` | No content change. YAML tag added. | internal | ✅ Re-upload if not synced |
| `Glossary_and_Terms.md` | No content change. YAML tag added. | internal | ✅ Re-upload if not synced |
| `Jerome_Working_Style.md` | No content change. YAML tag added. | internal | ✅ Re-upload if not synced |
| `Email_Templates.md` | No content change. YAML tag added. | internal | ✅ Re-upload if not synced |
| `Analysis_Frameworks.md` | No content change. YAML tag added. | internal | ✅ Re-upload if not synced |

### Sensitivity tag summary (all files tagged May 2026)

| File | Sensitivity | Rationale |
|------|-------------|-----------|
| `ISZE_Company_Context.md` | internal | Org chart, entity structure — no financial details |
| `Glossary_and_Terms.md` | internal | Terminology only |
| `Active_Projects_Apr2026.md` | **confidential** | Contains ITUK pricing details, negotiation context (James Marsh reference) |
| `Pricing_Logic.md` | **confidential** | Class factors, FOB formula, SPA mechanics — commercially sensitive |
| `Jerome_Working_Style.md` | internal | Communication preferences, no business data |
| `UIO_V13_File_Guide.md` | internal | Model guide — no distributor financials |
| `Email_Templates.md` | internal | Generic templates |
| `Analysis_Frameworks.md` | internal | Generic frameworks |

### Rule enforced from this date

Per `AI_Stack_Architecture_Apr2026.md` §Governance:  
**Claude must not include `confidential` or `restricted` material in Context Pack updates unless `upload-to-gpt: true` is explicitly set AND content does not contain line-item SPA or active legal correspondence.**

---

## Next scheduled refresh

**June 2026 (first working Monday)**  
Priority items:
1. Rewrite `Active_Projects_Apr2026.md` → `Active_Projects_May2026.md` with current state
2. Replace `UIO_V13_File_Guide.md` with v17 guide
3. Add AIM CY2025 classification rate (~87% revenue-weighted) to context pack
4. Update Rev/Vehicle benchmark (Ireland €390/vehicle, ITUK €244, network avg €216) to company context
5. Competitiveness: update D-Max AM prices (oil filter €16.6, brake pads €73 — May 2026 scrape)

---

## Upload log

| Date | Files uploaded | GPT target | Uploaded by |
|------|---------------|-----------|-------------|
| April 2026 | All 6 MDs + 2 templates (v0) | All 4 Custom GPTs | Jérôme VdP |
| 2026-05-12 | CHANGELOG created — no new upload yet | — | Claude/Cowork |
