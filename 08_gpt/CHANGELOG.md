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
