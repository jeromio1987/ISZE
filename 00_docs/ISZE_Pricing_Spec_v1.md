# ISZE Pricing Engine — Specification v1

**Status:** draft for review · **Author:** pricing analysis · **Date:** 2026-08-05
**Scope:** FY2027 price revision — PR00, ZPR1 (Israel), CIS
**Supersedes:** nothing. First formal spec.

> Numbers convention: `FACTS.md` wins over this document. Where this spec cites a
> figure it is tagged with its source file so it can be re-verified.

---

## 0. Purpose

Replace the uniform weighted increase with a **rule-based, line-traceable allocation**
that hits the same declared weighted target while directing the increase toward parts
where demand is growing and away from parts already lost to IAM.

The IML formula is untouched:

```
FOB_EUR = BP_JPY / FX × source_discount
SP_EUR  = FOB_EUR / class_factor
```

V1 adds an ISZE-owned adjustment on top of `SP_EUR`. Class factors are not modified.

---

## 1. Constraints this spec is built around

These are binding facts from `00_docs/ISZE_ROADMAP.md` (2026-07-14) and
`01_data/00_derived/`, not assumptions. **The spec is designed so that none of the
blocked items are on its critical path.**

| # | Constraint | Consequence for V1 |
|---|---|---|
| C1 | Elasticity is not quotable — "only possible with DB → DLR sales, ISZE is too far from the market" (Jerome, 2026-08-01). `price_volume_elasticity.csv` measures distributor *stocking*, not end-market response. | **V1 uses no elasticity coefficient.** Capture rate and street index are the proxies. |
| C2 | No dated PR00 history. One snapshot only (`IE40 … 13.03.2026`, 164,380 rows). Applying it backwards gives realization 0.8865 → 0.8956 → 0.9185 → 0.9416, which is the 2026 increase applied backwards, not leakage. | **No realization/pocket-price waterfall in V1.** Must not be presented as leakage. |
| C3 | ~~`sales_fact.parquet` carries only `net_sales_value` — no gross, no discount, no SPA condition.~~ **Resolved 2026-08-10** — Jerome confirmed SPA discounting is negligible: almost no order lines run under an SPA, and 99.99% of order lines bill at straight PR00 (or ZPR1 in Israel) list. | `net_sales_value` ≈ list price already for the working population. No gross/condition decomposition needed; V1's net-to-DB is effectively list-to-DB. Purchase price (`FOB_EUR = BP_JPY/FX × source_discount`) is already wired from the same PR00 list — no separate purchase-price ask either. |
| C4 | 522 PNs billed with no PR00 entry = **€4.96M, 15.1% of CY2025 revenue**. Plus 800 PNs / €1.82M on superseded numbers. | ~15% of the book is **outside the reach of any list-price action**. Data fix, not a pricing lever. |
| C5 | Distributors react to the **worst single line**, not the weighted average. Some large increases are IML BP_JPY corrections or out-of-mass-production parts, not ISZE decisions. | Per-line cap + mandatory reason code separating ISZE action from IML pass-through. |
| C6 | Weighted increase is Laspeyres on L12M volume. | Index cost ∝ **past** revenue; cash return ∝ **future** volume. This asymmetry is the engine's main lever. |

---

## 2. The prize — why the allocation matters more than the rate

From `02_dashboards/pricing/_build/pricing_action_map.json` (built 2026-07-16, CY2025,
213 cells = 18 distributors × 14 PMS categories):

| Zone (capture rate) | Cells | Captured | Headroom @ +5% | At risk |
|---|---|---|---|---|
| raise (≥0.80) | 34 | €1.92M | **€96K** | — |
| contested (0.45–0.80) | 33 | €1.26M | — | €0.96M |
| defend (<0.45) | 146 | €2.59M | — | **€16.05M** |

**Identified price headroom €96K. PMS wallet sitting at IAM: €16.0M. Ratio 1:167.**

Caveats, stated so the number is not misused: `at_risk` = TAM − captured, i.e. the full
theoretical gap, not what is winnable; TAM is modelled; these 14 categories are PMS only,
not the whole book. Discount heavily and the asymmetry survives.

**Design implication:** V1's objective is not to maximise the increase. It is to spend the
increase — funded from the 34 raise cells — buying back defend-zone volume.

---

## 3. Architecture

```
Layer 0   Eligibility gate        → can this PN be repriced at all?
Layer 1   Segmentation            → where does it sit? (wallet × street)
Layer 2   Momentum (θ)            → where is demand going?
Layer 3   Allocation              → Δ per line, solved to the index target
Layer 4   Market lists            → PR00 / ZPR1 / CIS treatment
Layer 5   Output & governance     → reason codes, caps, GPS bridge
```

---

## 4. Layer 0 — Eligibility gate

Every billed PN is assigned exactly one status **before** any pricing logic runs.

| Status | Rule | Treatment |
|---|---|---|
| `PRICEABLE` | Has active PR00 entry, not superseded | Full engine |
| `NO_LIST` | Billed, absent from PR00 (522 PNs, €4.96M) | **Excluded.** Raise as data-integrity action |
| `SUPERSEDED` | Billed under a number the list marks superseded (800 PNs, €1.82M) | Route to successor; exclude from Δ |
| `IML_CORRECTION` | \|ΔBP_JPY\| above threshold vs prior revision | Mechanical pass-through. `Δ` reported separately, **excluded from the ISZE-decision narrative** |
| `EOL` | Out of mass production | Pass-through + flag; expect low volume, high % moves |

Rationale for `IML_CORRECTION` and `EOL` being separate statuses: these produce the large
per-line increases distributors complain about, and the answer to that complaint
("here is the BP_JPY before/after") is entirely different from the answer to a
repositioning. Mixing them in one number is what makes the conversation unwinnable.

---

## 5. Layer 1 — Segmentation

Two axes. Both computable from files that exist today.

### Axis A — Wallet position (`capture_rate`)

Source: `pms_capture_by_db_year.csv`, `line_type = total` (genuine + BVP; BVP downtrade is
never counted as a loss). Existing classification in `build_pricing_action_map.py` is
retained unchanged:

- **Captive** ≥ 0.80
- **Contested** 0.45 – 0.80
- **Lost** < 0.45

*Coverage limit:* capture is defined only for the 14 PMS categories. For the rest of the
book, use this fallback ladder as a binary contested/captive proxy:
`competitiveness_autodoc_risk.csv` → `bvp_pn_dimension.csv` (a BVP alternative existing
means the part is contested by definition) → `aim_pn_classification.csv`.

> Do **not** use AIM pricing risk as a discriminator — per `DECISIONS.md` it was removed
> from the AIM×GPS matrix x-axis on 2026-07-17 because it never separated anyone.

### Axis B — Street position (`street_index`)

```
street_index = PR00_EUR × 1.785 / IAM_street_price
```
where 1.785 = 1.40 (DB margin) × 1.275 (dealer margin), per the existing channel
normalisation. Scraper prices are already retail/street.

Evidence tiers, highest first. **The tier sets how far the line is allowed to move:**

| Tier | Source | Max \|δ_pos\| |
|---|---|---|
| T1 | KS observed — same shop, genuine vs IAM, same PN | ±10pp |
| T2 | KS derived — PR00×1.785 vs KS IAM listing | ±6pp |
| T3 | Eucon (`eucon_price_gap.csv`, 44 PNs, network) | ±6pp |
| T4 | Category median (Tranzparts/TMC UK, Auto365 IL, Mekonomen SE) | ±3pp |
| T5 | No benchmark | **0pp — never move blind** |

---

## 6. Layer 2 — Momentum (θ)

**θ = expected forward volume ÷ L12M volume.** The one number the current process has no
view of. Under C6, index cost is charged on last year's volume while cash accrues on next
year's, so euros returned per basis point of index spent scale with θ.

```
θ = θ_parc × θ_interval × θ_cohort × θ_warranty
```

| Component | Meaning | Source | Status |
|---|---|---|---|
| θ_parc | Parc growth, market × model | `UIO_carpark_for_GPS_recalc_2026-07-30.csv`, UIO V19/V20 | **WIRED** — `theta.py` |
| θ_interval | Service-frequency shift as generation mix changes | OEM maintenance schedules (4 read 2026-07-15) | **Blocked** — see below |
| θ_cohort | First-replacement wave by registration cohort × part-family replacement age | DVLA/SMMT cohorts (UK), `attach_rates.csv` | Partial |
| θ_warranty | Cohorts crossing out of warranty → warranty-billed becomes paid-billed | `distributor_warranty_expense_fiscal.csv` | Partial |

### θ_interval is the D-Max lever and it is worth unblocking first

Per the roadmap's LCV bucket item, from OEM schedules:

- Standard / older D-Max (4JJ3, RZ4E; incl. RT56 "2013 TF series"): **20,000 km** oil
  interval → 1.0 svc/yr
- Newest generation (**RG21, RZ4F-TC with SCR**, Europe/Israel): **15,000 km** → ~1.33 svc/yr

**As the parc mix shifts to new-generation D-Max, oil-interval-linked demand rises ~33%
per vehicle per year.** That is a structural θ > 1 on filters, oil and everything on the
oil interval — sourced from OEM documentation, not modelled.

It is blocked only on the chassis-code → model-year / SCR mapping
(RG / RG21 / RT56 / RT88_93). PDF metadata carries no build year. **This single mapping is
the highest-value unblock in the whole spec** — it converts the D-Max generation change
from a qualitative story into a quantified demand forecast.

### V1 simplification

Until θ_interval and θ_cohort are wired, bucket rather than compute:

| Bucket | Definition | δ_θ |
|---|---|---|
| Declining | θ < 0.95 | −2pp |
| Stable | 0.95 – 1.10 | 0 |
| Growing | > 1.10 | +3pp |

### Implementation status (θ_parc, wired 2026-08-06)

`03_analytics/isze_pricing/theta.py`. θ_parc only; the other three components
stay at 1.0 rather than carrying an unsourced number, so **the D-Max interval
effect above is not yet in any engine output.**

θ_parc is the wallet-weighted CY2026-corrected ÷ CY2025 ratio, which reconciles
to the car park's own network totals (€60,218,250 / €60,785,305, −4.91% against
its stated −4.9%). Weighting by wallet rather than units is deliberate: an LCV
unit at €250/yr should not swing the answer as hard as an MD unit at €887.

Joined distributor-first, then country — the action map mixes the two, and
ITUK/IUK/UMI/UTI are €3.27M of €5.77M captured. IUK LCV −6.0% against ITUK CV
+4.8% means a single `U KING` θ would cancel both signals out.

Each θ carries a basis mirroring `allocation.require_basis`. `uio_locked` (IUK
44,926), `uio_cohort_model` (ITUK) and `uio_constant_hazard` may move a price;
`uio_known_defect` (UTI, ~23% low on missing weight classes) may not. That gate
is inert today — UTI's θ is 1.045, already stable — and exists against a future
car park revision.

**Caveat that governs how this should be read:** no category has a benchmarked
premium, so all 213 cells are `NO_EVIDENCE_HOLD` with `d_pos = 0`, and θ_parc is
currently the only differentiator in the allocation. It moves 60 cells —
declining +1.3%, stable +3.4%, growing +6.3%, index still exactly 3.00%. €1.17M
of the €1.75M declining bucket is the locked figure; all €0.59M of the growing
bucket is constant-hazard estimate that the V20 cohort rebuild will move.

θ is per market, not per category: categories sell across LD/MD/LCV in different
proportions and no category → `model_type` mapping exists.

---

## 7. Layer 3 — Allocation

```
Δ(pn) = Δ_base + δ_pos + δ_θ + δ_life + δ_mkt

subject to:
  Δ_floor ≤ Δ(pn) ≤ Δ_cap                        per-line political guardrail
  Σ(w · Δ) = Δ_target                            w = L12M net-to-DB revenue share
  Δ_base solved to satisfy the above
```

Every term is signed, named and traceable to a source file — that is the whole point.
A distributor query on any line resolves to a reason code, not a judgement call.

### Sign discipline (the two-gate rule)

| Wallet | Street index | Action | Note |
|---|---|---|---|
| Captive | any | **+** | The 34 raise cells. This funds everything else |
| Contested | < 0.95 | + | Below market, room to take |
| Contested | > 1.15 | − | |
| Lost | > 1.15 | **− −** | The €16M defend zone. Brakes live here (1.9–2.3×) |
| Lost | < 0.95 | **0 — investigate** | Cheap *and* losing ⇒ not a price problem. Availability, lead time or dealer behaviour. Cutting further burns margin for nothing |
| any | T5 (no evidence) | 0 | |

The "cheap and still losing" row exists to stop the engine spending margin on a problem
price cannot solve.

### Guardrails (V1 starting values, to be tuned)

- `Δ_cap` = **+8pp** on any `PRICEABLE` line
- `Δ_cap` = **+5pp** for any PN in a distributor's top-50 basket by L12M revenue
- `Δ_floor` = **−12pp**
- `IML_CORRECTION` / `EOL` lines are exempt from the cap but reported on a separate schedule

---

## 8. Layer 4 — Market lists

### 8.1 PR00

Full engine as above.

### 8.2 ZPR1 — Israel (UMI 1797, UTI 1799)

Currently class-dependent, ~10% below PR00, applied flat.

Israel is €5.74M CY2024, **17.6% of network revenue, at 40.8% GP vs network 44.3%** — the
flat discount is applied even in categories where it isn't needed to win the sale.

**V1 action:** replace the blanket −10% with a per-category differential derived from
`auto365_results.csv` (IL street). Where Israeli street prices show ISZE already
comfortably below IAM, the discount is buying nothing and should narrow. Expect net margin
recovery on captive categories, deeper cuts on genuinely contested ones — same engine,
Israeli benchmark data.

### 8.3 CIS — GA (Armenia), CBC (Kazakhstan)

Currently `SP = FOB / 0.40` → **60% GM, class-independent**. The highest margin in the
entire system, applied to the markets most exposed to grey import, with **no ability to
differentiate** because the factor ignores class.

#### On dropping CIS prices (the China grey-import question)

The competitor is not primarily IAM. It is **Qingling Isuzu** (Chongqing JV) — licensed
N-series / F-series production with substantially overlapping part numbers, plus Chinese
IAM. Kazakhstan shares a land border with China, and Kazakhstan and Armenia are both
inside the **EAEU customs union** — so goods landing in Kazakhstan circulate to Armenia
without a further customs event. Both CIS distributors sit inside the same customs area as
the leak.

**Recommendation: do not make a blanket CIS price cut.** Reasoning:

1. **You cannot reach the price.** If Qingling-source parts land at 30–50% of ISZE price, a
   15% cut does not win the sale. It gives up margin without changing behaviour — cutting
   against a competitor you cannot reach.
2. **Small base, so the upside is small too.** 690 CIS lines vs 15,355 PR00. Getting this
   wrong in either direction is not material; getting it *structurally* wrong is.
3. **Re-export arbitrage.** A 25% CIS cut creates an arbitrage back into EU. CIS is
   class-independent and trivially simple to price — the easiest list in the system to
   arbitrage. A blanket cut risks funding a grey channel into your own primary market.

**Instead:**

| Action | Detail |
|---|---|
| **Make CIS class-dependent** | End the flat 0.40. This is the structural fix — without it there is no ability to differentiate at all |
| **Segment by Qingling overlap** | Chinese equivalent exists (wear, PMS, mechanical) → cut to 40–45% GM; 60% is fictional margin on volume you don't have. No Chinese equivalent (Euro 6/7 aftertreatment, electronics, safety) → hold 60%+ |
| **Gate on evidence** | Scrape Kazakh/Russian marketplaces (Emex.kz, Exist.kz, Satu.kz, Kolesa.kz, Avtoto) for actual ISZE PNs before setting any number. Incremental target for the existing scraper stack, not a new build |
| **Re-export control first** | Monitor CIS purchase volume against CIS UIO. Spend/unit materially above plausible parc demand = product leaving the market. Put this in place *before* any cut |

The governing sentence: **you cannot beat Qingling on price. You can stop pretending to
compete on parts they have already won, and protect margin on parts they cannot follow.**

---

## 9. New model launches — P700 and D-Max 2.2L (RG21 / RZ4F-TC)

### Why this is the wedge

New PNs have **q₀ = 0**, so they carry **zero weight in the Laspeyres index**. The 3%
constraint does not bind on them at all. They are also the only parts with no old price for
a distributor to compare against — so the full role-based method can be implemented at
launch with zero pushback, proven, and only then extended to the legacy book.

### What changes technically — previous generation vs new

Sourced from `00_docs/ISZE_ROADMAP.md` (4 OEM maintenance schedules read 2026-07-15)
and confirmed displacement from Jerome. Items marked *inferred* are standard SCR
architecture, not read from an Isuzu document, and should be confirmed against the
parts catalogue before use.

| | Previous generation | New generation |
|---|---|---|
| Chassis / engine | RT56 ("2013 TF series"), 4JJ3, RZ4E | **RG21, RZ4F-TC, 2.2L** |
| Aftertreatment | DPF only | **DPF + SCR / AdBlue** |
| Oil interval | 20,000 km → 1.0 svc/yr | **15,000 km → ~1.33 svc/yr** |
| Market | — | Europe / Israel |

**Three commercial consequences, in order of value:**

1. **The SCR system is an entirely new set of part families with no predecessor.**
   DEF pump, DEF injector, SCR catalyst, NOx sensors up/downstream, DEF level
   sensor and heater (*inferred*). There is no old part number, therefore no old
   price, therefore no distributor reference point and no aftermarket
   equivalent. This is the single largest block of genuinely free pricing in the
   FY2027 cycle, and it is available only once.
2. **+33% service events per vehicle per year** on everything tied to the oil
   interval. This is volume growth that requires no commercial action at all —
   but it also means the *filter* lines are where distributors will feel any
   price move most often. Treat filter pricing as the visible basket.
3. **The urea filter is a new recurring consumable.** The category already exists
   in the capture model with a small base; on the new generation it becomes a
   standard service item.

Carryover PNs (brakes, suspension, body) *do* carry index weight and gain θ from
the added parc — treat them under the normal engine, not the launch book.

| P700 | New platform | Effectively an all-new parts set; treat entirely under launch rules. **See §9.4 — Israel provides a live benchmark** |

Emissions content shifts the mix toward **captive, electronic, high-value** parts — exactly
where the class factor under-monetises. Evidence: DPF sensor 8978808270 realises **69.3%
GP**, above the 56% implied by class P, the most aggressive class in the table.

### Launch pricing rules

| Part role | Rule | Why |
|---|---|---|
| Wear / PMS (filters, urea filter, brakes, belts) | Price **below** class-implied, to establish the dealer habit | IAM arrives years 3–4. The habit has to exist before it does. These are the traffic drivers |
| Captive (SCR, NOx sensors, DPF, ECU, injectors) | Price **to margin**, above class-implied | No substitute will exist. Under-pricing here is permanent forgone margin |
| Carryover PNs | Run the normal engine, with θ uplift from added parc | These carry index weight; treat as legacy |

**The timing trap:** there is no IAM alternative for roughly the first 3–4 years — but that
is also the warranty period, when paid volume is low. The money arrives years 4–7, which is
exactly when IAM arrives. Pricing high in the empty window mainly buys an earlier IAM entry.

### 9.3 Warranty-phase pricing, then holding flat

*This subsection describes a sequencing option. It carries an internal cost that
is set out explicitly below, and it should not be adopted without the agreement
of the warranty function.*

**The observation.** Two features of the warranty period are relevant to price:

- Parts fitted under warranty are still supplied and invoiced by ISZE. An earlier
  version of the launch model treated warranty demand as revenue that simply did
  not occur, which understated launch-phase volume substantially. That has been
  corrected.
- An aftermarket part cannot be fitted to a warranty repair. In that channel
  there is therefore no competitive substitution at any price point.

A further structural point: warranty runs three years **from each vehicle's own
registration**, not from model launch. Once registrations reach a steady rate, a
rolling share of the parc — on current assumptions roughly a third — is
permanently inside its warranty window. The warranty channel is a standing
feature of the parts business, not a launch-phase artefact.

**The sequencing option.** For failure-driven parts only (aftertreatment,
sensors, injectors — not scheduled service items, which the customer pays for
regardless), set the launch price toward the upper end of the policy band, and
then hold that price flat once the warranty period ends rather than applying the
annual increase.

The commercial logic is one of timing rather than of who pays. Price is set at
the point where volume is lowest and no substitute exists; it is then held while
volume grows and the aftermarket arrives. A line held flat while the rest of the
book rises becomes progressively more competitive, and does so at approximately
the moment an aftermarket alternative appears.

**Modelled outcome** (D-Max 2.2L, `runs/…__launch__dmax_22`, assumptions per
`config.yaml`):

| Tactic | 10y discounted GP | Captive share retained y10 | Captive price vs IAM y10 |
|---|---|---|---|
| Split (launch high, then normal increases) | €23.51M | 0.477 | 2.22× |
| **Load then hold flat** | **€23.55M** | **0.508** | **2.01×** |

Broadly neutral on gross profit, with a better competitive position at the end of
the period. The result is not driven by the share of demand that is
warranty-claimed — varying that between 40% and 80% barely moves it. It is driven
almost entirely by **warranty duration**:

| Warranty term | Effect on 10y GP vs holding the split tactic |
|---|---|
| 2 years | −2.3% |
| 3 years | +0.2% |
| 5 years | +4.6% |

**The point to confirm before proceeding is therefore the applicable warranty
term and mileage cap, market by market.** Below roughly three years the option
does not pay.

**Costs and cautions, stated plainly:**

- The approach raises warranty expense per vehicle during the covered period.
  That figure is visible to IML and is read partly as a product-quality
  indicator. It should be quantified and presented alongside the pricing
  proposal, not left to emerge later.
- ISZE and the warranty function sit within the same group result. The gain is in
  competitive position and timing, not in the transfer itself, and the proposal
  should be made on that basis.
- The tactic requires a multi-year commitment to hold price. If the freeze is
  abandoned after two years the position is worse than not having started.
- Every behavioural parameter behind the modelled outcome is an assumption. The
  table above ranks options against each other; it does not forecast a result.

### 9.4 P700 — Israel as a live benchmark

P700 launched in Israel approximately 15 months ago. This is the only real
demand evidence available for the model and it should replace the placeholder
assumptions in `launch_parts.csv` before any P700 conclusion is used.

**What Israel can tell us:** actual part-level demand rates per vehicle, the real
parts split between wear and failure-driven, warranty claim mix by part, and the
early competitive response in a market with an active local aftermarket
(`auto365_results.csv` already provides IL street prices).

**What it cannot tell us, and this is the limitation that matters:** 15 months
sits entirely inside the warranty period. It gives the launch and warranty phase
only. It says nothing about paid-channel behaviour in years 4–7, which is where
the money and the aftermarket competition both arrive.

**Basis adjustment required:** Israel prices on ZPR1, presently around 10% below
PR00 and class-dependent. Any read-across to UK and mainland Europe must be
restated to a PR00 basis, and the Israeli competitive environment differs from
the UK one.

**Recommended use:** treat Israel as evidence for *demand structure* — which
parts move, how often, and in what mix — and not as evidence for *price level*.

### The highest-leverage decision nobody is watching

**Class assignment for new PNs.** It sets margin for the entire life of the model and is
invisible to distributors because there is no old price to compare. *Open question: does
ISZE have any input into how IML classes P700 / D-Max 2.2L parts, or is it dictated?* If
there is a voice there, it is worth more than the entire FY2027 increase exercise.

---

## 10. Layer 5 — Output and governance

### Output schema (one row per PN × market)

```
pn · market · status · class · source · category
p0_net_to_db · q0_l12m · rev_l12m · w
capture_rate · zone · street_index · evidence_tier
theta · theta_bucket
delta_base · d_pos · d_theta · d_life · d_mkt · delta_total · delta_capped
reason_code · index_contribution_bp · p1_net_to_db
```

`reason_code` is mandatory and is what makes the run defensible line by line to HT, MH and
to a distributor.

### GPS bridge (required output)

GPS = net sales ÷ UIO. A price increase **mechanically** raises GPS with no real
improvement, so the engine must emit its own expected GPS impact per distributor,
decomposed:

```
ΔGPS = price effect + volume effect + mix effect + parc effect
```

Without this, FY2027 GPS improvement cannot be distinguished from FY2027 price increase —
and the GPS thresholds (>€150 healthy / €50–150 at risk / <€50 critical) become
self-congratulatory. Source: `gps_spu_by_distributor.csv`.

### Cadence

| Cycle | Owner | Action |
|---|---|---|
| Annual | IML | Class factors, BP_JPY, FX |
| Annual | ISZE | Δ allocation run (this spec) |
| Quarterly | ISZE | Street index refresh — `ISZE_PMS_IAM_Refresh` already live |
| Launch-triggered | ISZE | New model price setting, off-cycle, outside the index |

### Distributor communication

The frame inverts. Not "3% across the board" but:

> "Your top 50 service lines are flat or down. Your L12M basket moves +2.6%, below the
> 3% network figure. Separately, N lines carry IML base-price corrections — listed here
> with BP_JPY before and after."

Checkable line by line, and it stops the pricing round from working against the PMS
programme.

---

## 11. What V1 explicitly does not do

Stated so reviewers do not assume otherwise:

- **No elasticity coefficient.** Not measurable at ISZE level (C1)
- **No full θ.** θ_parc is wired; θ_interval, θ_cohort and θ_warranty are 1.0.
  The D-Max 15,000 km interval effect is documented in §6 but is in no output
- **No per-category θ.** Per market only — needs a category → `model_type` map
- **No realization / pocket-price waterfall.** Blocked on dated price history (C2) — the block is now purely the second dated snapshot; no discount noise to filter out (C3 resolved)
- **No action on the 522 no-list PNs** (€4.96M, 15.1%). Data fix precedes pricing (C4)
- **No change to class factors.** IML-owned
- **No CIS blanket cut.** See §8.3

---

## 12. Data asks, ranked by unlock value

**2026-08-10:** gross value / condition types dropped from this list — Jerome confirmed SPA
discounting is negligible (~0% of order lines), 99.99% bill at straight PR00/ZPR1 list, so
`net_sales_value` already ≈ list price. See C3. Purchase price is also not an open ask —
`FOB_EUR = BP_JPY/FX × source_discount` is already wired from the same PR00 list `config.yaml`
reads today.

| # | Ask | Unlocks |
|---|---|---|
| 1 | **OEM competitor genuine-price benchmark** (not IAM), at least for the 14 PMS categories | Allocation basis — every category premium is currently `basis: placeholder`, so all 213 cells hold flat (`NO_EVIDENCE_HOLD`) regardless of the target rate. The live blocker, independent of any billing-data question |
| 2 | **Chassis code → model year / SCR mapping** (RG, RG21, RT56, RT88_93) | θ_interval — the D-Max 2.2L demand forecast. Cheapest high-value unblock |
| 3 | **Dated IE40 PR00 / ZPR1 snapshots**, one per revision | Clean price-only vs volume/mix bridge — low-noise now that C3 is resolved; separates IML pass-through from an ISZE decision, line by line |
| 4 | **DB → dealer sell-out beyond ITUK** | The only route to real elasticity. Ties to the FY2027 20% KPI support-payment condition |
| 5 | **PR00 entries for the 522 billed PNs** | Brings 15.1% of revenue into scope of any pricing action |

---

## 13. Open questions for Jerome

1. Does ISZE have any input into **class assignment for new PNs** (P700, D-Max 2.2L)?
2. Is the FY2027 3% target measured on **net-to-DB after** the 20% KPI support payment?
   If support scales with purchases, a 3% increase nets ~2.4%. Any distributor on a fixed
   net-price SPA takes 0% and the rest absorb the difference.
3. What per-line cap is politically survivable — is +8pp right, or lower?
4. Confirm the CIS competitor profile: is the leak primarily **Qingling genuine-equivalent**,
   Chinese IAM, or EU re-export? The three call for different responses.
