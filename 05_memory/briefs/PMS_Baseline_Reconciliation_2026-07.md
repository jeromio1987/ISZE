# PMS Pilot — Success Criteria vs. Model B Reconciliation

**Author:** Cowork (drafted for Jérôme Van der Pluym)
**Date:** 2026-07-03
**Status:** RESOLVED 2026-07-14 — Jerome's decision: retire the 17.3% Success Criteria baseline (Model B / 35.1% is the standard), but do **not** set a new numeric Tier-1/Tier-2 target. No general target — that part of this memo is explicitly skipped, not deferred.

---

## The problem, stated precisely

Two documents currently quote two different ITUK oil-filter capture rates for the **same year** (CY2025), off the **same underlying sales data**:

| Document | Oil filter capture (CY2025, DVLA basis) | Status |
|---|---|---|
| `91_legacy/Isuzu/Divers/ISZE_ITUK_PMS_Pilot_Success_Criteria.md` (last updated 2026-05-12) | **17.3%** | Formally "locked — not to be revised," governs the pilot's 12-month go/no-go |
| `iml_v7_ituk_cy2025.yaml` / Model B (adopted 2026-07-02) | **35.1%** | Current external standard — used in all IML/ITUK decks, business case, correspondence per FACTS.md and pms-coverage.md |

This is not a case of the number improving over time. It's the same historical year measured two different ways, and both documents are still live. If IML or ITUK ever puts the Success Criteria doc and a current PMS deck side by side, they will see two different numbers for CY2025 with no explanation — which reads as either a mistake or a moving of the goalposts, whichever is worse.

**This memo exists so that doesn't happen by accident.**

## Why they differ — verified, not estimated

Two independent changes compound to roughly double the number. Confirmed by recomputing both sides from source:

**1. Service frequency assumption changed.** Success Criteria used a flat 1.5 services/year for expected demand (22,389 × 1.5 = 33,584). Model B uses IML's own schedule-derived 1.25×/yr for oil/fuel/air (40,000km ÷ 50,000km/yr mileage) and 0.5×/yr for clutch/brake (22,389 × 1.25 = 27,986). This alone shrinks the denominator by 17% (ratio 0.833) — a defensible correction, since it's now tied to an actual IML service interval rather than an assumed multiplier, but it is a real change nonetheless.

**2. Oil filter PN scope changed.** Success Criteria counted a single PN (8982705240): 5,815 units CY2025. Model B's "oil_filter" category counts 9,818 units — a broader, corrected genuine-PN set, consistent with the 2026-06-02 line_type classification fix noted in DECISIONS.md (previously-mislabelled genuine PNs were pulled back into the genuine oil-filter bucket). This raises the numerator by 69% (ratio 1.688).

**Combined effect:** 0.833⁻¹ × 1.688 ≈ 2.03× — which is exactly the jump from 17.3% to 35.1% (recomputed independently in this memo, not just quoted). Both changes are individually defensible. The compounding is what makes it look, at a glance, like performance doubled overnight. It didn't — the ruler changed.

The same pattern shows up in brake (Success Criteria 17.8% → Model B 35.3%, also ~2×) and is directionally likely in clutch, though I have not independently decomposed those the way I did oil filter — flag this as unverified if it matters for external use.

## What I'm recommending

**Retire the Success Criteria doc's locked baseline (17.3% / 37.8%) explicitly — mark it superseded, the same way DECISIONS.md already marks other pre-fix PMS figures "superseded — do not quote."** Rebuild the pilot's Tier 1/Tier 2 go/no-go targets on Model B methodology, since that's now the number ISZE is putting in front of IML and ITUK. Measuring the pilot's success against a yardstick nobody externally sees anymore is a governance gap waiting to surface at the 12-month review.

**What I'm not recommending: a specific new target number.** That's a business call, not a data one. Two honest options:

- **Option A — preserve the original relative ambition.** Success Criteria asked for +27.1% relative growth (5,815 → 7,390 units) as the Tier-1 bar. Applied to the new base: 35.1% × 1.271 ≈ **44.6%** DVLA oil-filter cover as the new Tier-1 target.
- **Option B — preserve the original absolute unit ask.** Success Criteria asked for +1,575 units/year. Applied to Model B's 9,818-unit actual: **11,393 units** as the new Tier-1 target (≈40.7% cover under Model B's denominator).

I'd lean toward Option A since it's cleaner to explain to IML in percentage-point terms, but I'm not the one who has to defend it to ITUK, and there may be a reason to want the more conservative Option B. Your call.

**One more thing worth flagging honestly:** under either option, the *starting point* just jumped from 17.3% to 35.1% purely from methodology, not from anything the pilot did. If this gets reported to ITUK/IML as "PMS capture nearly doubled," that would be misleading even though the number is real — the doubling is a definitional correction, not a pilot result. Worth being explicit about that distinction the first time Model B numbers are presented alongside anything that references the old baseline.

## Resolution (2026-07-14)

Jerome's call: **no new numeric Tier-1/Tier-2 target.** Options A (44.6%) and B (11,393 units) above are not being adopted — this memo's target-setting question is closed, not parked. What stands:

- The 17.3% Success Criteria baseline is superseded — Model B (35.1%) is the number used everywhere externally.
- The pilot continues to be tracked against Model B methodology, but without a formal go/no-go percentage threshold attached.
- If a target is wanted later, this memo (and the two options above) is still here to restart from — but it is not an open action item.

### DECISIONS.md entry logged

```
## 2026-07-14 — PMS pilot Success Criteria retired; no replacement target set

**Status:** Accepted
**Context:** The May 2026 Pilot Success Criteria doc locked a CY2025 oil-filter
capture baseline of 17.3% (DVLA) using a flat 1.5 svc/yr assumption and a
single-PN scope. Model B (adopted 2026-07-02) recomputes the same CY2025 year
at 35.1% using IML's schedule-derived 1.25×/yr frequency and a corrected
multi-PN genuine oil-filter set. Both numbers were live simultaneously,
creating a same-year, same-data discrepancy risk with IML/ITUK.
**Decision:** Success Criteria baseline superseded — CY2025 oil-filter
capture is 35.1% (DVLA) under Model B. Jerome declined to set a new formal
Tier-1/Tier-2 numeric target (no general target) — this is a deliberate
scope decision, not an open item.
**Alternatives considered:** Option A (44.6%, relative-ambition-preserving)
and Option B (11,393 units, absolute-ask-preserving) — both drafted, neither
adopted. Keep the two baseline documents on separate methodologies (rejected
— same-year comparison risk).
**Consequences:** `91_legacy/.../ISZE_ITUK_PMS_Pilot_Success_Criteria.md`
marked superseded, no replacement numeric target. Pilot tracked on Model B
methodology without a go/no-go percentage threshold.
**Docs updated:** [pms-coverage.md](../projects/pms-coverage.md), this memo.
```

---

*Grounding: `ISZE_ITUK_PMS_Pilot_Success_Criteria.md` (91_legacy, 2026-05-12), `iml_v7_ituk_cy2025.yaml`, `FACTS.md` §1, `DECISIONS.md` 2026-06-02 and 2026-07-02 entries. Recomputation done independently in this session, not just transcribed from source docs.*
