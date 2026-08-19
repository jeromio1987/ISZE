# Pricing engine vs class / uniform — Mode B notes

**Audience:** Jerome only.  
**Alloc:** `20260810T171626Z__alloc__t3pct` (+3.0000% exact).  
**Dashboard (Mode A):** `02_dashboards/pricing/ISZE_Pricing_Engine_Readiness_Dashboard.html`  
**JSON:** `01_data/14_dashboards/pricing_engine_readiness.json`  
**Tab:** **Why the engine** (deep Before vs Engine) · sticky next to Readiness.

---

## Comparison headline

Same **+3% weighted** and same **€173,041** revenue Δ under **constant units**. Engine redistributes **~€94,886** of incidence vs charging every cell +3%. IUK is the big beneficiary (defend cuts on brakes); ITUK / UTI / Ireland fund the raise. UTI ≠ UMI — UTI takes the raise share; UMI is slightly under uniform.

Deep tab adds: zone×DB stacks, from→to redistribution, Δ histogram vs flat +3% spike, blind-weight donut, evidence tiers, brand ceiling ladder, class-factor “level ≠ revision” chart, D-Max launch bars, distributor callouts.

---

## What “previously” means (be precise)

Not “we never used class factors.” Class factors **still** set `SP = FOB / class_factor` (IML formula). The contrast is the **revision**:

| Piece | Prior typical | Engine |
|-------|---------------|--------|
| Level | Class factors from FOB | Same formula for SP level |
| Move to hit +3% | Uniform / near-uniform % on much of the book | Rule-based alloc to same weighted index |
| Capture / street / θ | Not driving the revision | Zones + evidence + θ_parc |
| IML BP vs ISZE Δ | Often blurred on the list move | Pass-through vs decision separated in narrative |
| Street point | Often list (Eucon wrong-point lesson) | PR00 × **1.785** |
| Brand ceilings | Flat premium instinct | +30 / +60 / +150 / +250 ladder |
| OEM gate | None | oem_benchmark ≥3 priced peers |
| Audit | No run registry | Reason codes + run IDs |

Strict cost-plus re-derive alone is **not** a +3% machine (FX/BP can cut). Ops when told “+3%” was **uniform_target**. Dashboard compares that vs engine. Counterfactual: `03_analytics/isze_pricing/counterfactual.py`.

---

## Engine traps (blunt)

1. **NO_EVIDENCE_HOLD ≈ 23.8% of € weight** (125 cells) still takes ~**+6.15%** base lift. Differentiation is real on evidenced cells and fake-uniform on the rest. Do not pitch “fully differentiated +3%” yet — the dashboard says this out loud on the Why tab.
2. **Placeholder premium basis (107 cells)** — `require_basis` blocks position moves, but the **index base** still lands on that weight. Unbenchmarked euros still pay.
3. **θ_parc-only** — D-Max interval story (+33% svc/yr at 15k vs 20k) is **not in any alloc number**. Launch book does not fix it.
4. **DB→DLR proxy is theatre if treated as β.** Soft diagnostic, not joined to Δ.
5. **oem_benchmark = 2 cats** (air/oil). Street 15/22. Near-gate brakes/fuel need one real DAF quote — Autodoc is 403; FEBI ≠ OEM.
6. **Launch book +32.7% GP NPV vs class_only** is **[ASSUMPTION]** erosion. Ranking tactics ≠ forecasting volume under +3%.
7. **Constant units** — both paths “look equal” on total €. The prize is mix / complaint surface / future θ, not a bigger invoice today.
8. **17 cells at +8% cap** — visible in histogram; prior flat +3% never showed that shape.

---

## Redistribution anatomy (measured)

| Reason | vs uniform € |
|--------|--------------|
| DEFEND_CUT | **−64,145** |
| CONTESTED_ABOVE_MARKET | **−30,742** |
| CAPTIVE_RAISE | **+51,678** |
| NO_EVIDENCE_HOLD | **+43,208** |

~Half the “fund” still comes from blind base lift — that is the honest partial-differentiation story.

Zone wtd Δ (engine): raise **~6.3%**, defend **~1.5%**, contested **~1.0%**. Uniform would have been **3%** on all three.

---

## Sales / mix evolution (what we can and cannot say)

| Claim | OK? |
|-------|-----|
| Same +3% index € under constant L12M weights | Yes — measured from alloc |
| Who pays more/less vs uniform | Yes — from `alloc_detail.csv` |
| Volume will grow/shrink under engine | **No** — no elasticity |
| PMS total capture zones drive raise/defend | Yes — `line_type=total` |
| D-Max will deliver +33% filter demand next year | Only after θ_interval map — today qualitative |
| “Fully differentiated” while 24% blind | **No** — overclaim |

---

## External one-liners (Mode A — from Why tab)

1. Same +3% weighted bill; different lines carry it (~€95k reallocated).
2. Defend / above-market wear is cut or held — not loaded like captive filters.
3. Street on PR00 × 1.785; hold when blind; oem_benchmark needs real peer OEs.
4. Brand ceilings by quality (+30…+250), not one flat premium.
5. Blind weight ~24% still on base lift — differentiation is partial and logged.

---

## Readiness

Composite **61.5%** (equal-weight layers 0–5). Full launch ≠ waiting for elasticity. Full launch = trusted bases on in-scope cats, street gates filled, θ_interval, eligibility narrative, list rules. Top unlock: one genuine DAF street quote.
