# ISZE Lubricants Potential Model — Context for Cowork

## What This Is

This document provides context for working with the ISZE Lubricants Potential Model (`ISZE_Lubricants_Potential_v1.xlsx`). The model was built in April 2026 to quantify the total engine oil volume opportunity across ISZE's European and international markets, as part of a strategic evaluation of launching a Shell/Total Isuzu-branded lubricant programme to replace the current BESCO offering.

---

## Background

ISZE currently sells BESCO-branded lubricants to its distributor network, but the product is considered too expensive and commercially uncompetitive. The strategic direction is to partner with a major oil brand (Shell or Total) under an Isuzu-branded label and build a programme that reaches end customers either through distributors or via a direct-to-dealer delivery model.

The current BESCO sales are almost entirely **gear oil, axle oil, and LLC** — not engine oil. Engine oil capture is effectively zero today. This model quantifies the theoretical engine oil demand based on the vehicle parc (UIO) across active markets.

---

## Scope

- **Markets included:** All active ISZE markets except Italy (excluded by VP Sales decision — separate commercial structure)
- **Segments covered:**
  - LCV = D-Max (6L per service × 2 services/year = 12L/vehicle/year)
  - LD = N-Series (10L per service × 2 services/year = 20L/vehicle/year)
  - MD = F-Series (12.5L per service × 2 services/year = 25L/vehicle/year)
- **HD excluded** — not in ISZE/ITUK/Israel scope
- **UIO basis:** 2025 estimates from `ISUZU_UIO_Overview_2026_v16b.xlsx`
- **No price per litre included** — volume model only; no verified sell-in price available at time of build

---

## Key Numbers (from the model)

- **Grand Total addressable volume (all markets excl. Italy):** see `Country Summary` tab, Grand Total row
- **Reachable volume (Approach A distributors only):** see `Country Summary` tab, Reachable Total row
- **Israel (UTI + UMI) explicitly excluded from reachable potential** — both distributors confirmed unwilling to change supplier
- **UK (ITUK/IUK) is by far the largest single market** — dominant share of total addressable volume
- **Current L12M Besco revenue:** ~€167K (gear/axle oil only — see `Besco Baseline` tab)

---

## Distributor Willingness Classification

Each market is classified based on the lubricants survey data collected from distributors (source: `overview_13022026.xlsx`):

| Status | Meaning |
|---|---|
| ✅ Approach A | Distributor confirmed willing to engage with a lubricants programme |
| ❌ Not Willing | Distributor explicitly declined (Israel: UTI + UMI) |
| ⚠️ No Data / Uncertain | No survey response, or engagement uncertain |

**Approach A markets:** UK, Belgium, Sweden, Portugal, Norway, Ireland  
**Not Willing:** Israel (UTI + UMI)  
**No Data / Uncertain:** Germany, Greece, Hungary, Cyprus, Finland, Romania, Malta, Denmark, Iceland, Poland

---

## Key Switching Conditions by Market

These are the conditions distributors indicated they would need in order to commit to an Isuzu-branded lubricant programme:

- **UK (ITUK/IUK):** Direct dealer delivery capability + competitive price. Previously failed due to cost and absence of dealer-direct option.
- **Sweden (IM Nordic):** Scheme 1+2 preferred; dealer-direct delivery strongly preferred. Current supplier: Midland (~200,000L total dealer network, all brands).
- **Portugal (Imotors):** Target price below €4/L; scheme 1+2; current supplier GALP. Oil spec: 10W40 ACEA E11.
- **Norway (RSA):** Scheme 2 (DB invoices, oil company delivers); current supplier Total.
- **Belgium (IBX):** No current DB involvement in oil distribution; dealers buy independently. Programme would need to create DB role.
- **Ireland (Isuzu Ireland):** Scheme 2; direct delivery preferred. Currently minimal oil sales.
- **Germany (ISD):** Not currently involved in oil distribution. Dealers have independent agreements at ~€3.63–3.67/L. Engagement status unclear.

---

## Adoption Rate Scenarios

Three scenarios are modelled in the `Total Potential` and `Country Summary` tabs:

| Scenario | Rate | Description |
|---|---|---|
| Conservative | 10% | Pilot phase — 2–3 DBs, limited rollout, Year 1 |
| Base | 25% | Active programme — majority of Approach-A DBs engaged, Year 2–3 |
| Optimistic | 50% | Full programme — dedicated DB infrastructure, Year 4–5 |

---

## File Structure

| Tab | Contents |
|---|---|
| `Assumptions` | Demand framework inputs, scenario rates, exclusion flags |
| `Total Potential` | Full detail: every country × segment row with volumes and scenario columns |
| `Country Summary` | Aggregated by country — cleaner view for stakeholder conversations |
| `Besco Baseline (Current)` | L12M actual Besco sales by distributor (reference baseline) |

---

## What Is Not Yet In the Model

- **Price per litre / revenue:** No verified sell-in price to distributor available. Model is volume-only.
- **Margin:** Not modelled. Needs confirmed product cost and target sell-in price.
- **Italy:** Excluded. Would need separate treatment given scale and distributor structure.
- **Pilot sizing:** Not yet built. Next step would be a 3–5 DB pilot tab with 6-month targets.
- **DB headcount / logistics cost:** Direct-to-dealer delivery requirement has operational cost implications not yet quantified.

---

## People & Governance Context

- **Owner:** Jérôme Van der Pluym, VP Sales Parts & Aftersales, ISZE (Antwerp)
- **Approval required:** Yoshimoto (MD) — any commercial programme commitment requires his sign-off
- **Key internal stakeholder:** Masumi Hayakawa (Director) — involved in SPA and aftersales programme approvals
- **Distributor contacts used:** Survey responses collected from ITUK, IM Nordic, Imotors, RSA, Isuzu Ireland, IBX, UTI, UMI, Autowallis, Grand Avto, Loutsios, ISD, and others

---

## Next Steps (as of April 2026)

1. Confirm sell-in price per litre with Shell/Total — needed before this becomes a business case
2. Select pilot markets (likely UK + 1–2 smaller Approach-A markets)
3. Resolve dealer-direct delivery logistics requirement — this is the primary structural blocker for UK
4. Build revenue/margin tab once price is confirmed
5. Prepare Yoshimoto briefing — volume potential + pilot proposal
