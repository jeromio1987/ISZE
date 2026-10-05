# Project 1 — Price revision (multi-hour brief)

Read with `04_DATA_TABLES.csv` rows where `table` starts with `pricing_`.
Block-1 checklist is in `00_ASK.md`.

---

## A. Measured stack write-up

# The weighted increase of all prices

*Built 2026-09-19T10:45:44+00:00 · window 1 Jul 2025 to 30 Jun 2026 · recipe in_scope and unpriced_reason null, 47,617 rows, index 5.961599%*

## The method

**weighted increase = SUM(quantity x change in yen base price) / SUM(quantity x previous yen base price) - 1.** It is read off the price comparison itself. Nothing is multiplied in.

This replaces a chain of three factors. Two of them were wrong, because both changes are already in force. The exchange rate of 178.5 is what we pay now, and the 67.3% purchase discount took effect on 5 January 2026. Multiplying by 163.7/178.5 treats a settled rate as a move to come, and multiplying by 0.673/0.620 adds a discount increase that is already inside today's prices.

## The headline

| | Rows | Share of weight | Weighted increase |
|---|---:|---:|---:|
| Japan (IML) | 22,731 | 47.71% | **+6.2081%** |
| Thailand (IMIT) | 23,085 | 43.08% | **+6.3088%** |
| no source label | 1,801 | 9.21% | **+3.0601%** |
| **All prices** | **47,617** | **100.00%** | **+5.9616%** |

The share of weight is the quantity-weighted share of the previous yen base price. The two source rows do not sum to 100% because 1,801 rows carry no source label in the price list.

## Figures replaced

| Measure | Earlier factor chain | Measured weighted increase |
|---|---:|---:|
| Whole priced book | +1.80% | **+5.9616%** |
| Japan (IML) | +5.74% | **+6.2081%** |
| Thailand (IMIT) | -2.45% | **+6.3088%** |

## Each market

The same measure, taken on the rows that belong to each market, so each market sheet carries a measured figure rather than a ratio of two constructed prices.

| Market | Rows | Part numbers | Billed EUR | Weighted increase | Japan | Thailand |
|---|---:|---:|---:|---:|---:|---:|
| PR00 | 32,434 | 10,968 | 12,831,246 | **+5.9211%** | +6.3925% | +6.4001% |
| UTI | 1,869 | 1,869 | 3,400,405 | **+5.5808%** | +5.6312% | +9.2395% |
| UMI | 2,428 | 2,428 | 2,429,160 | **+5.6370%** | +6.2140% | +6.2725% |
| CIS | 3,090 | 2,674 | 1,455,811 | **+4.8455%** | +4.6445% | +6.3769% |

UTI is sold-to 1799 and UMI is sold-to 1797. They are separate Israel distributors and are never combined.

## The exchange rate is applied, not decided

The rate is issued by ISZJ and applied. It is a corporate rate, not a commercial choice, and no part of it is handed to a distributor or held back as a decision. An earlier version of this analysis presented that as a dial with a five-point scale and a claim that one setting could not satisfy both sources. All of that was invented and has been removed.

## How the IML base price works - source documentation

**1. The Export Base Price is built up from IML's own costs, and our purchase price is a discount off it.**

*Source: Masumi Hayakawa (IML), 10 November 2025, "FW: ISZE 移転価格対応 10/30打ち合わせメモ・今後の対応事項につきまして"*

The factors are 62% on vehicle parts and 73.5% on industrial engines, applied to IML's Export Base Price. Worked example: an Export Base Price of 1,000 JPY gives a purchase price of 620 JPY on vehicle parts. The Export Base Price therefore sits above our purchase cost by construction, and it is not a restatement of any single cost line of ours.

**2. IML builds its offer price from supplier cost plus a target gross profit.**

*Source: Hideya Kondou (ISZJ), 24 November 2020, "ITUK向けMMU新規ハーネスの価格設定について"*

Normal at 25% gross profit, Best at 17%. So the Export Base Price is a supplier cost plus a stated margin - a build-up, not a rebilling of anyone else's cost.

**3. The discount change and the base-price revision happen at the same moment.**

*Source: Takayoshi Suzuki, 22 December 2025, "discount/whole sales ratio revisoin from Jan 5th 2026"*

Valid from 5 January 2026, and the mail states it is "the same timing with annual EBP revision". This is why the discount cannot be treated as a forward move: it was applied when the base price was last revised.

**4. The base price and the class letter arrive together from Japan.**

*Source: Peeraya Sawangsaensuk (IMIT), 29 April 2026, "RE: base price class"*

"Please find the B/P, Price Class, and remark as detailed below." The class letter is issued with the base price, so the class factor and the base price move on the same cycle.

## Two open items - flagged, not resolved

**Our configuration carries only the vehicle-parts rate**

03_analytics/isze_pricing/config.yaml holds J: 0.673, which is the vehicle-parts rate - 1 minus the 32.7% discount in Masumi Hayakawa's mail of 10 November 2025. The industrial-engine rate is different: 73.5% in 2025, moving to 79.7% in 2026 (1 minus 20.3%). Our configuration applies that rate to every Japan-sourced part, so an industrial-engine part is priced on the vehicle-parts rate.

*Next step: config.yaml is left alone, exactly as it stands. Question for IML: confirm the current industrial-engine rate and which part families it covers.*

**IML states a different revision size from ours**

Masumi Hayakawa's mail of 10 November 2025 says the CY2026 IML base price revision has an impact of "around 3% increase for ISZE (weighted average)". We measure 5.9616% on the published recipe. These are probably different revisions or different scopes - theirs may be a purchase-cost impact over a different window.

*Next step: Open reconciliation item, and it is left open rather than closed by choosing an explanation. Ask IML for the window, the scope and the weighting behind the 3%.*

## What could not be verified

- The weighted increase is measured on the price comparison itself. No exchange rate and no discount is multiplied into it.
- Rows with no source label carry no source split. Their weighted increase is reported separately rather than being assigned to Japan or Thailand.
- Volume and mix are held flat. This is the arithmetic of the price move, not a forecast.


---

## B. Pricing roadmap — decisions, queue, closed traps

## 2. The decisions

Seven items. Each is a decision, not effort — the analysis behind each is already done.

### 2.1 The result against the 4–6% band

**There is no band decision to make on this measurement.** The weighted increase is **+5.96%**, and every market lands between **+4.85% and +5.92%** — inside 4–6% without any further action.

| | |
|---|---|
| **Blocked on** | nothing — measured |
| **What to watch** | CIS is the lowest at +4.85%, so it has the least headroom if anything moves |
| **Evidence** | `01_data/00_derived/pricing_stack_applied_2026-09-19.json` |

This replaces an earlier section that proposed a "pass-through dial" for the corporate exchange rate. **The rate is not a decision** — ISZJ gives it and we apply it. There was never a choice to make, and presenting one was an error.

### 2.2 The industrial-engine discount rate

**The question.** Our configuration applies **67.3%** to everything Japan-sourced. That is the **vehicle-parts** rate. IML's own mail of 10 November 2025 states the industrial-engine rate separately: **73.5% in 2025, moving to 79.7% in 2026**. If industrial-engine parts flow through the Japan discount, they are being priced on the vehicle-parts rate.

**Where it came from.** Masumi Hayakawa, `FW: ISZE 移転価格対応 10/30打ち合わせメモ・今後の対応事項につきまして`, 10 November 2025: *"Currently the factors used are 62% on VP and 73.5% on IE, which are applied to IML's Export Base Price (EBP). (ex. EBP 1,000 JPY, ISZE's purchase price for VP is 620 JPY and 735 JPY for IE)."*

| | |
|---|---|
| **Blocked on** | **Jerome** — does any IE volume flow through the pricing stack, and on which rate |
| **Consequence of no answer** | A slice of the book may be priced on the wrong purchase rate |
| **Evidence** | `03_analytics/isze_pricing/config.yaml` → `source_discount.J: 0.673` |

### 2.3 The 3% versus 5.96% gap

**The question.** IML's mail of 10 November 2025 says *"CY2026 IML EBP revision has an impact around 3% increase for ISZE (weighted average)."* We measure **5.9616%** on our own revision base.

**Why it is not explained away.** These are probably different revisions or different scopes — theirs may be a purchase-cost impact over a different window. But guessing which is how the last two days went, so both figures and both sources are recorded and the reconciliation is open.

| | |
|---|---|
| **Blocked on** | **IML** — which revision and which window the 3% refers to |
| **Consequence of no answer** | Two figures circulate for one year's revision and nobody knows which applies |
| **Evidence** | Hayakawa mail 10 Nov 2025, against `aim_pricing_recalc_2026-09-17.json` |

### 2.3 The CIS basis

**The question.** CIS currently prices on the **class factors**, but [`config.yaml`](../../03_analytics/isze_pricing/config.yaml) specifies a **flat 60% margin, class-independent** (`factor_flat: 0.40`, `class_dependent: false`). The configuration also carries a 45% margin where a Chinese equivalent exists and 60% where it cannot be followed.

**This is not a rounding difference.** Measured on the CIS population (CIS-KTK, CBC, GA — 3,090 rows, €1,455,811):

| Basis | Weighted increase |
|---|---:|
| Class factors (current) | **+4.8455%** |
| Flat 60% margin | **+31.2946%** |

**About 26 points apart**, on the same rows. Both are on the sheet because the question is unresolved. Source: `pricing_stack_applied_2026-09-19.json` → `markets.CIS`, and the CIS sheet's own basis-change row.

**A separate blocker inside this one:** the 45%/60% split cannot be segmented today because no part-level file maps a Chinese equivalent to a part number. Until one exists, the split stays a labelled scenario rather than a fact.

| | |
|---|---|
| **Blocked on** | **Jerome** — which basis is real; plus an overlap file for the 45/60 split (does not exist) |
| **Consequence of no answer** | The CIS sheet carries two numbers 28 points apart and neither is authoritative |
| **Evidence** | `03_analytics/isze_pricing/config.yaml` → `markets.CIS` |

### 2.4 The override rows

**The question.** About **12.84%** of rows do not reproduce the price formula — the price on the list was set deliberately rather than derived. Measured: `chain_sp_within_1c_pct_prior_163_7` = 87.16% reproduce, **12.84% do not**, over 275,210 tested rows. Source: [`pricing_framework_maths_proof.json`](../../01_data/00_derived/pricing_framework_maths_proof.json).

**Why it matters.** Nobody has identified who set those prices or on what basis. They are the rows where the computed-margin cross-check is weakest, and where any formula-driven policy is least reliable. The current method reads them correctly — that is the point of reading the price instead of rebuilding it — but the *reason* they exist is unknown.

**Note the label conflict to settle with it.** The framework meta describes the share as **catalogue-wide**; the stack paper describes it as **Japan-specific**. Those are two different measurements using one number. One of them is wrong.

| | |
|---|---|
| **Blocked on** | **Jerome** — data-integrity investigation, or accepted practice |
| **Consequence of no answer** | The weakest eighth of the book stays unexplained |
| **Evidence** | `01_data/00_derived/pricing_framework_maths_proof.json` · `01_data/01_Pricing/_framework_meta.json` line 97 |

### 2.5 Competitor evidence — fund it, or accept 16.5%

**The question.** Only **16.47%** of the priced book has a usable competitor price, and at the +8% cap that supports at most **1.32 points** on the whole book. Funding wider collection is a resourcing question, not a technical one — brakes proves it is achievable at 82.6% within one family.

**What we have.** 307 distinct part numbers across every independent source we hold. Brakes is the dense exception. Sources and their vintages: [`competitor_evidence_inventory.csv`](../../01_data/00_derived/competitor_evidence_inventory.csv).

**What we cannot fix by collecting more.** Coverage tells us the competing *price*, not the volume response to ours. Elasticity is not identified on this data at all — IQR 0.69pp and 70.6% of parts within ±1pp of no response. The paper's decision 10 (below) is the only route to that answer, and it is a conversation.

| | |
|---|---|
| **Blocked on** | **Jerome** — fund, or accept 16.5% and say so |
| **Consequence of no answer** | Every policy keeps being argued on a fifth of the book |
| **Evidence** | `02_dashboards/pricing/_build/_spec_basis_meta.json` |

### 2.7 The pass-through question with ITUK

**The question.** What actually happens to the dealer price when our price moves. Policy-paper decision **10**.

**Not to be confused with a pass-through dial.** There is no choice about applying the exchange rate. This is a different question: how our movement propagates along the chain to the dealer. The external review names the risk — a move that protects our margin but destroys the dealer's **converts the dealer into a competitor**, invisibly for one to three years. No model can settle it; it needs a conversation.

| | |
|---|---|
| **Blocked on** | **Jerome** — the conversation |
| **Consequence of no answer** | The whole chain in the paper's section 4 stays arithmetic at a stated assumption |
| **Evidence** | `01_data/90_INBOX/PRICING_POLICY_PAPER_2026-09-17_REV2.md` §11 decision 10 |

### 2.7 Class assignment

**The question.** Whether we have a voice in class assignment and in the base price. Policy-paper decision **6**, and the external review calls it the **single highest-leverage item**.

**Why.** The margin is set by a class letter, so **class assignment is margin assignment** and it fixes the margin for the life of a part. For a new part number it is a one-time decision worth more than several years of percentage increases. 80% of a catalogue is priced by a rule, so whoever assigns the class assigns the price.

| | |
|---|---|
| **Blocked on** | **Jerome** — whether we have a voice, and with whom |
| **Consequence of no answer** | We keep negotiating percentages on a margin somebody else set |
| **Evidence** | `PRICING_POLICY_PAPER_2026-09-17_REV2.md` §11 decision 6 |

### Also open from the policy paper

Decisions 1–5, 7–9, 11, 12 in [`PRICING_POLICY_PAPER_2026-09-17_REV2.md`](../../01_data/90_INBOX/PRICING_POLICY_PAPER_2026-09-17_REV2.md) §11. Not repeated above because they are stated there in full. The two that most change what happens next are **decision 3** (settle the FY2027 ambition before or after the 20% distributor support payment — it flips a +4% headline to +3.2% net) and **decision 8** (top 200 part numbers by revenue against criticality and competition, which needs no new data).

---

## 3. Open queue

Numbered from **16**, continuing the hub's sequence. Only buildable work belongs here.

| # | Item | State | Blocked on |
|---|---|---|---|
| 16 | **This roadmap** — the pricing programme | Live 2026-09-19 | Jerome on items 2.2, 2.3, 2.4, 2.5, 2.7, 2.8 |
| 17 | **The industrial-engine discount rate** | Our config applies the vehicle-parts rate (67.3%) to everything Japan-sourced; IML states the IE rate separately (73.5% → 79.7%) | Jerome — does IE volume flow through the stack |
| 18 | **Reconcile the 3% against our 5.9616%** | IML's own figure for the CY2026 revision is "around 3%"; we measure 5.9616%. Different scope, or different revision | IML — which window the 3% covers |
| 19 | **Re-derive the brakes 82.6%** | Prose only in the policy-paper builder; no CSV or builder computes "311 of 334, €2,596,458" | nothing — re-derive or cite as unsourced |
| 20 | **Settle the FX stamp on published packs** | Policy-paper decision 9 — every competitive comparison without a rate stamp is against a moving floor | nothing, once the rate is fixed |
| 21 | **The no-source-label rows** | 1,801 rows, 9.21% of index weight, €2.94M billed, 656 part numbers. They carry a weighted increase of +3.06%, well below both sources | nothing — resolve the labels or keep reporting them separately |

**Not on this list on purpose:** anything in section 5.

**Not on this list on purpose:** anything in section 5.

---

## 4. Stale artefacts to correct first

Cheap, and each currently misleads anyone who reads it.

| Artefact | What is wrong |
|---|---|
| [`PRICING_STACK_APPLIED_2026-09-19.md`](../../01_data/90_INBOX/PRICING_STACK_APPLIED_2026-09-19.md) | Describes a `Provenance` column and `J99`/`T99`/`X99`/`CIS` codes. Both were removed at Jerome's instruction — the workbook carries his `J`/`T` in the `Source` column. The document contradicts the workbook |
| [`DECISIONS.md`](../../DECISIONS.md) | No entry for this session. The 2026-09-17 entry still says the exchange-rate fork "stays open" at 163.7, which is superseded |
| [`build_pricing_policy_paper.py`](../../02_dashboards/pricing/_build/build_pricing_policy_paper.py) lines 1293–1318, 1396 | The brakes 82.6% / "311 of 334" / €2,596,458 is authored prose with no deriving source |
| [`_framework_meta.json`](../../01_data/01_Pricing/_framework_meta.json) line 97 vs the stack paper | The override share is stated catalogue-wide in one and Japan-specific in the other |

---

## 5. Closed — do not reopen

All closed in [`ISZE_ROADMAP.md`](../ISZE_ROADMAP.md) §5 or `DECISIONS.md`. Re-proposing one of these costs credibility.

| Closed | Reason |
|---|---|
| **Gross / SPA / condition columns on the billing extract** | `sales_fact` is net-only forever. Do not re-ask |
| **AIM pricing-risk as a decision surface**, and any new 0–100 score | Gate never fired; fitted replacements failed holdout. 2026-07-17 / 2026-08-18 |
| **`db_aftersales_risk`** as its replacement | Parked 2026-08-18 |
| **ISZE→DB `price_volume_elasticity.csv`** | Deferred. Resumes only as DB→DLR when dealer sales-to-dealer coverage improves |
| **Autodoc / Oscaro scraping** | Cloudflare-blocked, permanently. 2026-07-14 |
| **Auto365 as a part-number price index** | No OEM part-number join exists |
| **An external "healthy capture %" as an ISZE target** | Three different metrics; none is an ISZE target |
| **The AIM attribute layer** | On hold per Jerome 2026-09-17. Hub open-queue item 15 |

---

*Created 2026-09-19. Every figure in this file was computed from the file named beside it. The position and the per-market weighted increases reproduce from `01_data/00_derived/price_bp_weighted_compare_pn.csv` filtered to `in_scope == True` AND `unpriced_reason IS NULL`, and are verified independently. The evidence tiers reproduce from `02_dashboards/pricing/_build/_spec_basis_meta.json`. Nothing was rebuilt, published or mailed to write this roadmap.*


---

## C. Claims to CONFIRM / REJECT / UNKNOWN

1. Whole-book weighted increase **+5.9616%** on 47,617 priced in-scope rows (Jul 2025–Jun 2026).
2. Factor-chain Thailand **−2.45%** was wrong; measured Thailand **+6.31%**.
3. Flat +5% paper (€1.75M) and filed step (€1.65M at 5.9616%) are two proposals — never add.
4. Competitor evidence ~**16.47%** of priced book; +8% cap → at most ~**1.32 points** on whole book.
5. CIS class-factor **+4.85%** vs flat-60%-margin scenario **+31.3%** on same rows — unresolved.
6. ~**12.84%** override rows do not reproduce the price formula.
7. Config JP discount **67.3%** vehicle-parts applied to all Japan; IE may be **73.5%→79.7%**.
8. IML “around **3%**” vs our **5.9616%** is open reconciliation.
9. Margins reading for reference dealer price decided; packs not rewritten; ~**+22.6%** arithmetic consequence.
10. FX **178.5** is applied, not chosen.

---

## D. Full pricing policy paper (REV3)

# A parts pricing policy for ISZE — revision 3

**What we should charge, on what basis, what has to be true before we can say it, and what we propose to move**

**Audience:** shared / external · prepared for management · revision 3 · 19 September 2026
Prepared for: Jerome Van der Pluym

**Version.** This is `PRICING_POLICY_PAPER_2026-09-19_REV3.md`, revision 3. It supersedes
`PRICING_POLICY_PAPER_2026-09-17_REV2.md` (revision 2, 17 September 2026, corrected 18 September 2026) and
`PRICING_POLICY_PAPER_2026-09-17.md` (revision 1). Both earlier revisions are kept on disk unchanged so the three
can be compared. Nothing in this revision overwrites them.

**Status:** proposal and design. **Nothing in this document changes a price, a list, or a published number.** No
price has been issued, moved or published, and no allocation has been run. Every movement proposed here is a
proposal for a decision.

---

## What changed in revision 3, and why

Revision 3 folds five pieces of work completed on 19 September 2026 into the existing paper. It does not replace
revision 2's argument; it extends it, and where today's work changes a conclusion, the change is stated in place.

| Revision 2 said | Revision 3 says | Where |
|---|---|---|
| Move from one flat percentage to a policy that changes different parts by different amounts — described as a design intention | The policy is **built and measured**: a two-tier system with six tiers on a single management dial, carrying €20.14M of last-twelve-months revenue across 17,939 lines | §8 |
| Collision and bodywork parts were one family carrying one rate | **Lighting is separated from bodywork and cut from a 0.90 share to 0.80**, because 0.90 puts every lighting line above the +8% per-line ceiling the engine itself sets. The Israeli insurance mechanism that makes this necessary is set out in full | §9, §15 |
| The pickup sat in the light commercial channel, unexamined as a pricing market | **The UK operator's licence does not bind the D-Max buyer** — twice over. Ireland, not the UK, is the market with the real compliance burden. Portugal sells the pickup as a tax instrument | §10 |
| New part numbers were a pricing wedge because they had no prior price to compare against | **That premise was wrong for roughly twelve parts in thirteen.** 1,048 of the 1,132 new numbers carry four consecutive published prices. The wedge is the **zero index weight**, not the absence of a reference price. The 13 functional SCR parts sit at the class-implied price and no higher — free pricing nobody has claimed | §11 |
| The competitive set in a wear family was the independent brand | **A third price level exists below the independent brands** — remanufactured and refurbished units, and in Israel the law explicitly permits the refurbishment trade. The D-Max DPF is the most exposed single part in the portfolio | §12 |
| The policy described a method | The policy now **states the proposed movements**, each with its one-line reason, and **discloses a defect in the system as built**: it does not enforce the +8% per-line cap, and 4,903 of 17,230 priced lines sit above it | §15 |

Two things did **not** change and are worth saying before anything else. The verdict is the same: we should price
by tier rather than by one annual percentage. And the honesty requirements are the same but stronger, because this
version is going to someone else to check: every factual claim carries a source, every claim carries a grade, and
no number is invented anywhere. Where a figure is a judgment, the line says so.

---

## 0. How to read this paper

The paper proposes a priced policy for the parts book and the cycles after it. It is built from work that already
exists and does not invent a method.

| Source | What it gives us | File |
|---|---|---|
| **The AIM classification paper** | The product tree: what a part is, in three levels, and how much of the book each family carries | `02_dashboards/sales/ISZE_AIM_Classification_Paper.html` |
| **The price revision** | The money already filed: +5.9616% weighted, €1,652,140.71 of step on the in-scope base | `01_data/00_derived/price_bp_weighted_compare_pn.csv` |
| **The pricing specification and its live model** | The decision rules: position, evidence tiers, and what may move a price | `00_docs/ISZE_Pricing_Spec_v1.md`, `ISZE_Pricing_Simulation_Spec_Basis.xlsx` |
| **The margin mechanism** | The class letter, the margin it sets, and the cost basis under every price | `03_analytics/isze_pricing/config.yaml`, `01_data/00_derived/pricing_list_pn.parquet` |
| **The two-tier pricing system** (new in revision 3) | Six tiers, one dial, every line classified, every movement computed | `01_data/90_INBOX/PRICING_SYSTEM_STRATEGY_20260919.md`, `pricing_system_by_market_2026-09-19.xlsx`, `pricing_system_lines_2026-09-19.csv`, `pricing_system_figures_2026-09-19.json` |
| **The lamps and insurance work** (new in revision 3) | The Israeli write-off threshold, the court finding, and what lighting earns against collision | `01_data/90_INBOX/LAMPS_INSURANCE_MANAGEMENT_20260919.md`, `UTI_LIGHTING_COLLISION_MANAGEMENT_20260919.csv` |
| **The pickup market research** (new in revision 3) | Whether the licensing and tax regimes bind the pickup buyer, in four markets | `01_data/90_INBOX/MARKET_PICKUP_PRICING_POWER_20260919.md`, `MARKET_PICKUP_PRICING_POWER_20260919.csv` |
| **The launch pricing work** (new in revision 3) | The P700 and D-Max 2.2L list: what is new, what is carryover, and where the price sits against class | `01_data/90_INBOX/P700_2P2L_LAUNCH_PRICING_20260919.md`, `p700_2p2l_launch_pricing_20260919.csv` |
| **The remanufacturing and DPF work** (new in revision 3) | The third price level below the independent brands, and the DPF position per market | `01_data/90_INBOX/REMAN_DPF_RESEARCH_20260919.md`, `REMAN_DPF_MEASURED_LINES_20260919.csv` |
| **The external operator review** | How other manufacturers price, every figure graded | `01_data/90_INBOX/_ANON_OEM_IAM_PRICING_REVIEW_20260917.md` |
| **The dealer purchase panel** | Volume by part number by year, for five distributors | `01_data/00_derived/dealer_*_long_*.csv` |

### 0.1 The grading key, used on every factual claim

| Grade | What it means |
|---|---|
| **[MEASURED]** | Read out of a primary source — legislation, a regulator, a named study, or our own file with a path. It can be checked. |
| **[TRADE]** | Trade press, an industry body, or a supplier's published commercial material. |
| **[INFERENCE]** | Our reasoning from the facts above, not a measurement. |
| **[NOT FOUND]** | We looked and could not establish it. Carried as a gap, not dropped. |
| **[REPORTED — NOT VERIFIED]** | Legal or internet research carried from another document that this paper did **not** independently re-open. It is reported because it matters to the decision, and it is labelled because it has not been re-checked here. |

**A judgment is never presented as a measurement.** Where this paper proposes a specific rate, the same line says
whether the rate is measured or chosen.

### 0.2 The stated assumptions, which are dials and not measurements

| Dial | Value | What it is | Where |
|---|---:|---|---|
| Distributor markup on their buy price | **1.40** | the commercial stack in use. At a markup on cost this is a **28.6% margin on their selling price**, not 35% | `config.yaml`, `DB_DLR_COMMERCIAL_STACK.md` |
| Dealer markup on their buy price | **1.275** | the same stack, one tier further out → a 21.6% margin on their selling price | same |
| Distributor margin, the working assumption for this paper | **35%** | **a stated assumption, not a measurement.** ISZE does not hold dealer purchase prices and will not get them; no distributor will share their resale price | this paper |
| Our own book margin | **51.09%** | measured on the priced book — the one number in this list that is not an assumption | `pricing_list_pn.parquet` |
| The dial | **5%** | **a placeholder.** Management sets it. At 3% / 5% / 7% the four markets yield €576,301 / €960,503 / €1,344,705 | §8, §15 |
| The tier multipliers | **seven values** | **choices, not measurements.** Four of the seven are pure judgment; see §15.1 | §8, §15.1 |

**On the two distributor numbers, which are close but are not the same thing, and are never conflated.** A markup
of 1.40 on what the distributor paid is a **28.6% margin on their selling price** (1 − 1 ÷ 1.40). The **35%** is a
margin on the selling price too. The two differ by about 6.4 points, and the difference is not an error: it is the
difference between the stack we have been modelling and the margin we are now told to assume. **This paper uses
1.40 for the chain arithmetic in §4, because that is what builds the reference dealer price in use, and states 35%
as the working assumption for distributor margin wherever the distributor's own economics matter.** Do not put the
two in the same column, and do not convert one into the other and quote the result as measured.

**These two are thresholds, not observations, and they are worth being blunt about.** A margin on price sits on a
turnover that moves with volume, and a margin on cost does not, so the two are not the same quantity and no
re-arrangement of the arithmetic makes them comparable. They are two different market positions, seen from two
different chairs.

### 0.3 The three windows, which are never mixed

| Basis | Window | What it is for |
|---|---|---|
| **A — in-scope revision base** | 1 Jul 2025 → 30 Jun 2026 | the price revision readout. €34,993,609 billed in scope; €32,595,853 priced on both sides |
| **B — full billed window** | 1 Jan 2025 → 30 Jun 2026 | the classification audit and coverage checks. €52,414,408 |
| **C — the response panel** | CY2023 vs CY2025 | the volume-response measurement in §7 |
| **D — the pricing system basis** (new in revision 3) | 1 Jul 2025 → 30 Jun 2026 | the two-tier system in §8 and the movements in §15. €20,140,903 across four markets |

Window D and window A cover the same twelve months but are not the same population: window A is the revision base
on the AIM spine, and window D is the four-market line list that the pricing system can actually price. Where a
figure comes from window D the line says so.

### 0.4 The entities, which are never blended

**Israel is two distributors, UMI (1797) and UTI (1799), reported as two rows throughout and never blended.** UMI
carries the pickup and the light commercial business; UTI carries the trucks and buses. **IUK and ITUK are likewise
separate networks** — IUK is the light commercial network (models coded TF), ITUK is the truck network (N and F
series) — and the two are never mixed. Where a figure is measured on one of the four, the line names which.

---

## 1. The verdict

**We should move from one annual percentage applied to the whole book to a priced policy that changes different
parts by different amounts — and that policy is now built, measured and costed, not described. It puts a service
basket of 816 lines down by €18,664 and takes €570,990 from a commercial tier of 10,698 lines, at a 5% dial that
management sets.**

The system is new in this revision and it is the centrepiece (§8). It is not a proposal to raise more. It is a
proposal to raise the *right* things: the parts a customer cannot buy elsewhere carry the increase, and the parts
they buy at every service are held or cut, because those are the lines where volume is at risk.

Four findings underneath it change the shape of the argument, and two of them cut against the way the question is
usually put.

**First: our gross margin is not a decision. It is a lookup.** The list price is built as `SP_EUR = BP_JPY ÷ FX ÷
divisor`, where the divisor is one minus the intended margin. So the margin is set in advance by a letter on the
part: class C means 53.0% margin, class V means 45.0%. Across the eight letters in use the margin varies by at most
4.6 points, and for most of them by under one point. Nothing about the part, the market, the competitor or the
demand enters it. So "what margin should this part earn" is not currently a question anyone at ISZE answers — and
that is the real content of the request to price more dynamically. **[MEASURED]** — `pricing_list_pn.parquet`.

**Second: on the parts where we can see the competing price, the margin available to give away is roughly one
point, not thirty.** On 41 part numbers with an observed same-shop competing price, the median margin needed to
*match* that price is **52%**, and the median margin we hold today is **53%**. Our reference dealer price sits at a
median **1.64×** the independent retail price. On **12 of those 41 parts our landed cost is already above the
competing retail price**, so no margin target reaches them at all. **[MEASURED]** — `pricing_cost_floor_reach.csv`.

Cutting to 15% margin on the whole book would take gross profit from €15.15M to **€2.56M** — a **€12.6M
give-away**, on arithmetic, before any volume response — and would still leave our net price at 0.57× the
independent price, below the competitor and below the dealer's ability to defend the brand. That is not a
competitive move. It is a transfer. **[MEASURED]** — cost held fixed.

**Third: the volume question cannot be answered from the data we hold, and we can now show why rather than assert
it.** We have a genuine two-year, part-number-level panel — ITUK dealer purchases, CY2023 against CY2025, with the
IE40 list price on both sides. 3,662 part numbers with computable elasticity on both. The problem is not the data
volume, it is the price variation: **70.6% of parts had their list price move within one percentage point of the
median move.** The index changes almost every part by almost the same amount, so it contains almost no price
variation to measure a response against. Within that band the elasticity has a standard deviation of 22. The 226
parts that did move differently have a median elasticity of exactly zero. **The current pricing method is, by
construction, unmeasurable.** **[MEASURED]** — §7.

**Fourth, and new: a third price level exists below the independent brands, and in one market the law protects
it.** Remanufactured and refurbished units run at roughly 3% to 30% of the price of the new part they compete with
depending on the market and the vehicle class, and Israel's air-quality regulations explicitly permit removing a
particulate filter for "cleaning, repair or replacement" — which is a statutory licence for a refurbishment trade
that already exists there. **The D-Max particulate filter is the most exposed single part in the portfolio**: it
sits in our lowest margin band at a 48% margin, and our own warranty files show we pay 1.65× to 1.78× our own list
price for it in the two Israeli books. **[MEASURED]** for the ratios and the claims; **[INFERENCE]** for the
exposure ranking. — §12.

So the paper has five parts. Sections 2 to 7 set out what a price decision actually contains — cost, margin, chain,
currency, evidence — and report the measurement attempt honestly, including that it failed and why. Sections 8 to
12 are the new work: the two-tier system, the insurance write-off mechanism, the pickup market, the launch, and the
remanufacturing position. Sections 13 to 17 build the policy on top, work one family end to end, state the proposed
movements, and set out the decisions.

---

## 2. Where the margin actually comes from

### 2.1 The identity

```
SP_EUR = BP_JPY ÷ FX ÷ divisor
```

The divisor is one minus the gross margin. So:

**gross margin = 100% − the divisor. Nothing else.**

Worked in margins, which is how the business talks:

| Class letter | Divisor | **Margin** | Measured margin | Spread within the class |
|---|---:|---:|---:|---:|
| C | 0.47 | **53.0%** | 53.00% | 2.4pp |
| V | 0.55 | **45.0%** | 45.00% | 0.9pp |
| D | 0.48 | **52.0%** | 52.00% | 3.9pp |
| F | 0.525 | **47.5%** | 47.50% | 4.6pp |
| P | 0.44 | **56.0%** | 56.00% | 0.1pp |
| M | 0.50 | **50.0%** | 50.00% | 0.0pp |
| J | 0.555 | **44.5%** | 44.50% | 0.6pp |
| T | 0.80 | **20.0%** | 40.00% | 0.0pp |

Read straight off `pricing_list_pn.parquet`. **[MEASURED]** Two things in that table matter.

**The margin is the same for every part number in a class.** Within C, V, D, F, P, M and J the variation is a
couple of points at most, and for most of them under one point; it comes from which source file a row was read
from, not from a commercial judgement. There is no competitive information in the margin at all.

**And the margin is close to flat across the book.** The eight classes span 45% to 56% — one margin band, 11 points
wide — and **84.3% of the priced book earns inside it.** There is no second band, no high-margin set of parts and no
low-margin set. The policy we argue about annually is a five-point band around 51%.

That is worth sitting with, because it reframes the question. We are not choosing margins. We have a cost, a
currency rate and a letter, and the letter sets the margin. Asking for brakes at 15% and sensors at 65% is asking
for a mechanism that does not exist inside the formula — it would have to be built as an ISZE adjustment on top of
the list price, and the specification already provides for exactly that. **The two-tier system in §8 is that
mechanism, built.**

**One thing the table also says, and it is the strongest argument in this paper for changing the mechanism.** There
is a part number in the book earning **69.3% gross profit** — materially above the 56% that our most aggressive
class gives — and it is a sensor. The margin is there to be taken on captive parts, and today it is taken only by
accident, on the parts where IML happened to assign class P. **[MEASURED]** — `ISZE_Pricing_Spec_v1.md` §9, DPF
sensor `8978808270`.

### 2.2 What the book earns

On the in-scope priced book, 45,816 lines carry a usable margin — **96.2% of the priced lines**, €29,653,732 of
billed value, and **€15,150,306 of gross profit at a weighted margin of 51.09%.** **[MEASURED]**

| AIM family | Part numbers | Billed € | Weighted margin | Gross profit € |
|---|---:|---:|---:|---:|
| Intake Exhaust Emission | 458 | 5,039,284 | 52.8% | 2,660,441 |
| Not on AIM spine | 5,129 | 4,652,749 | 51.9% | 2,415,979 |
| Accident & Body | 2,196 | 4,152,901 | 53.9% | 2,238,667 |
| **Brakes** | **325** | **3,055,792** | **48.9%** | **1,493,110** |
| **Maintenance Service** | **309** | **2,916,040** | **46.9%** | **1,368,939** |
| Fuel System | 430 | 1,704,206 | 50.8% | 864,850 |
| Lighting | 650 | 1,593,119 | 48.3% | 770,084 |
| Electrical | 675 | 1,250,512 | 52.0% | 650,024 |
| Wheels Hub | 570 | 1,127,950 | 50.4% | 568,464 |
| 13 further families | 4,383 | 2,860,411 | — | 1,376,417 |

The two families where the request for dynamic pricing points — brakes and the service parts — are already the two
lowest-margin large families in the book, at **48.9%** and **46.9%** against a book average of 51.1%. That is not
because someone decided brakes should be cheap. It is because brakes are disproportionately class V (45% margin)
and the service parts are class M and F. **[MEASURED]**

So the position management wants — brakes low, sensors high — is *partly what already happens*, by accident of class
assignment. The mechanism produces something close to the shape being asked for, for reasons that have nothing to
do with the aftermarket.

---

## 3. The cost floor

A price has to clear two tests, not one. It has to be defensible against the competing product, and it has to leave
enough margin to be worth selling.

### 3.1 What "cost" means here, and its limit

The cost basis on disk is the **landed cost implied by the margin the class sets** — the FOB euro on each row of
the price file. It is the only cost basis the workspace holds, and it is an important caveat rather than a
measurement: where the assigned margin is generous the implied cost is understated and the apparent headroom is
overstated, and where it is aggressive the reverse. **The direction of that error is not known part by part.**
Where we need a firmer number we use the cost we actually billed per unit, per distributor, per part number — the
method in §3.3 — rather than an implied one.

**We do not hold a dealer purchase price and we are not going to get one.** State that plainly, because the rest of
this section depends on it. A distributor's resale price to their dealer is commercially confidential and no
distributor will share it. So every dealer-level figure in this paper is **built**, not observed: official list ×
1.40 × 1.275, inflated by a distributor margin that is a stated assumption, and labelled as a construction wherever
it appears.

### 3.2 Can a margin target reach the competing price?

On the part numbers where we have an observed same-shop competing price, with the cost held fixed:

| | Part numbers |
|---|---:|
| Where we can see the competing price | **41** |
| Cost already **above** the competing retail price — no margin reaches it | **12** |
| Reachable only at under 20% margin — inside the dealer's own margin | **3** |
| Reachable at 20% margin or better | **26** |

- Median margin needed to **match** the competing price: **52%**
- Median margin we hold today: **53%**
- Median ratio, our reference dealer price to the competing price: **1.64×**

**[MEASURED]** — `pricing_cost_floor_reach.csv`, `iam_ks_price_gap.csv`

And the price implied by a uniform margin target, as a multiple of the competing price:

| Margin target | Our net price vs the competing price |
|---|---:|
| 15% | **0.57×** |
| 20% | 0.60× |
| 30% | 0.69× |
| 40% | 0.80× |
| 50% | 0.96× |

Read the top row. **At a 15% margin our net price is 57% of the competing price.** That is not a competitive
position; that is a price below the competitor with margin thrown away to achieve it, and the dealer then adds
their own margin on top of a cost we have just destroyed.

The marquee case is not a margin problem at all. Part number `8975546610`, front brake pad kit, class V, 45%
margin: our list is €82.25, our implied cost €45.24, and the cheapest observed same-shop listing is **€17.55**.
**Our cost is 2.6 times their retail price.** Moving our margin from 45% to 15% changes nothing about that ratio.
The lever on that part is sourcing, not price. **[MEASURED]**

### 3.3 The aftermarket is below our own distributor's cost

Everything above compares us to a competing price. This is a different and harder comparison: on the part numbers
where we can translate our number into an aftermarket one, **the aftermarket equivalent is often priced below what
our own distributor paid us for the genuine part.**

For each distributor and part number, take what the distributor actually paid per unit — the CY2025 billed euro
divided by the billed quantity — and hold it against the cheapest aftermarket price the multi-brand coverage file
carries for the same number. The floors are per distributor, and no distributor is blended with another.
**[MEASURED]**

| | Count |
|---|---:|
| Part numbers the bridge resolves | **35** |
| Distributor floors available on those numbers | 106 (part number × distributor) |
| **Part numbers where the aftermarket is below at least one of our distributor's floors** | **26 of 33 testable** |
| Median ratio, aftermarket price ÷ our distributor's cost | **0.66×** |
| Median ratio against the *lowest* floor on that part number | 0.73× |
| Part numbers below **every** floor we hold | **24 of 33** |
| Part numbers above every floor we hold | 9 of 33 |

The four clearest cases, each with the floor it is measured against:

| Part number | Part | Distributor floor € | Aftermarket € | Ratio | Cheapest brand |
|---|---|---:|---:|---:|---|
| `8982924331` | SENSOR; SPD,FRT WHEEL | 147.48 (IRELAND) | 21.96 | **0.15×** | BLUE PRINT |
| `8982924321` | front wheel speed sensor | 145.83 (IRELAND) | 21.90 | **0.15×** | BLUE PRINT |
| `8983034680` | CALIPER; RR DISC BRK | 179.90 (ITUK) | 28.34 | **0.16×** | FRENKIT |
| `8980094180` | SENSOR; MAP | 105.02 (GREECE) | 17.17 | **0.16×** | NTY |

**The reason this matters is that it does not need a margin decision at all.** A margin target is a decision about
the gap between our cost and our price. Here there is no gap to decide: the alternative product is selling at
roughly one sixth of what our distributor pays for the genuine article. Cutting our margin, at any level, cannot
change a relationship between two numbers that are both below our price already. That is a sourcing conclusion,
not a pricing one.

**The caveat is essential and it cuts the size of the finding hard.** This compares an **aftermarket part against a
genuine assembly**. The two may not be the same article at the same specification, and the ratio therefore
overstates the gap between like-for-like products. Read it as a **landing-price fact** — what a buyer can actually
pay for an equivalent — and not as a like-for-like price comparison.

**And the coverage limit has to be stated with the finding, because a conclusion from 33 part numbers must say it
is 33.** The bridge resolves **76 of the 15,273 priced part numbers — 0.50%** — as the union of two sources that
share no part numbers between them: a licensed cross-reference of 41 priced part numbers and a third-party
multi-brand lookup of 35. It was assembled from parts we already knew had a named competitor, so 0.50% is an
**optimistic** rate over the whole catalogue, not a conservative one. It is a warrant to go and look at the rest,
not a rate that can be applied to the book.

### 3.4 What a margin-differentiated policy does

Holding cost fixed and pricing the arithmetic of each target:

| Scenario | Lines moved | Price level | Margin before → after | Gross profit change |
|---|---:|---:|---|---:|
| Brakes 15%, sensors/emissions 65% | 2,845 | ×1.018 | 51.1% → 52.0% | **+€540,066** |
| Brakes 25%, emissions 60% | 2,845 | ×0.998 | 51.1% → 51.0% | −€64,394 |
| Whole competitive book to 30% | 6,417 | ×0.916 | 51.1% → 46.6% | **−€2,484,145** |
| Whole book to 40% | 45,816 | ×0.815 | 51.1% → 40.0% | **−€5,481,356** |

**[MEASURED]** — `pricing_cost_floor_meta.json`

The top row nets **+€540k** — because the 65% on emissions more than pays for the 15% on brakes. That is worth
knowing before the idea is dismissed. But it is a composite of two opposite moves, and the second one is fragile:

- the **brakes leg alone costs €1,034,741** of gross profit and takes the family margin from 48.9% to 15.0%;
- the **emissions leg alone gains €615,093** and takes that family from 52.8% to 65.0%, which is a **price increase
  of about 35%** on €5.04M of billed value.

An increase of that size on the second-largest family in the book, on lines where the current evidence says we sit
*above* the competing price, is not a policy. It is a bet that the parts cannot be substituted. And §9 of the
external review, confirmed again in §12, finds that the emissions family is contested rather than captive: the
independent suppliers publish near-complete sensor coverage and aftertreatment assemblies with original-equipment
endorsement. **[MEASURED]** for the arithmetic, **[INFERENCE]** for the substitution risk.

**The honest reading: the request as stated nets positive, but it nets positive by raising prices where we have no
evidence we can, in order to fund a cut where we have evidence we cannot win.**

### 3.5 What this does to the conclusion of the section

§3.2 ended on the 12 part numbers where our cost is already above the competing retail price: a sourcing problem,
not a pricing one. §3.3 makes that stronger and larger. On the parts where we can bridge at all, the competing
price is often below our distributor's cost rather than merely below our price, and the ratios there are not 1.1×
or 1.3× — they are around **0.15×**. There is no margin target, at any level above zero, that reaches a price
sitting at one seventh of what the distributor paid.

So the cost floor does not merely constrain the margin idea. On this subset it removes the price lever entirely,
and it moves the question from *what should we charge* to *what is actually in the box, and what does it cost us to
put one there*.

---

## 4. The chain: what the customer actually faces

There are three margins stacked on a part: ours, the distributor's, and the dealer's. The reference dealer price
uses **1.40** for the distributor and **1.275** for the dealer, so the chain multiplies by **1.785**.

**What is measured here and what is assumed, said once so it is not read past.** Two things are real, and they are
ours: our own list price, and the reference dealer price as it is constructed, which is our list × 1.40 × 1.275.
Everything downstream of our invoice is a **stated assumption**, and the two assumptions in play are not the same
quantity:

| Step | Basis | Margin on their selling price |
|---|---|---:|
| Distributor markup of 1.40 (the stack in use) | markup on **cost** | **28.6%** |
| Distributor margin of 35% (the working assumption) | margin on **price** | **35.0%** |

On the 41 part numbers with an observed competing price, at today's margin, indexed to the competing retail price
= 1.00:

| Step | Multiple of the competing price |
|---|---:|
| Our net price to the distributor | 1.09× |
| Distributor price to the dealer | 1.53× |
| **Dealer price to the customer** | **1.95×** |

And if we cut **our** margin only, holding the two downstream percentages:

| Our margin | Our price vs competitor | Dealer price vs competitor |
|---|---:|---:|
| 15% | 0.58× | **1.03×** |
| 25% | 0.66× | 1.17× |
| 35% | 0.76× | 1.35× |
| 45% | 0.89× | 1.59× |
| 52% (today) | 1.02× | 1.83× |

**[MEASURED]** — `pricing_chain_and_fx.csv`

This is the most important practical finding in the paper.

**A 34-point give-away on our margin moves the price a customer is quoted from 1.83× the independent price to
1.03× — barely to parity.** Because the distributor's markup and the dealer's markup are percentages of *their* buy
price, a reduction in ours is multiplied by 1.785 before it reaches the customer. To become genuinely cheaper than
the independent market at the point of sale, we would have to go below cost.

Two consequences follow, and both are uncomfortable.

**We cannot buy competitiveness at our level alone.** If a brake pad needs to be 30% cheaper at the counter, we
cannot deliver that from our margin. Either the distributor and the dealer give up part of theirs, or the cost
comes down, or we accept the position.

**And there is no evidence on disk about pass-through.** Whether a distributor actually reduces the dealer price
when we reduce ours, or simply widens their own margin, is unknown, and it will stay unknown: it can only be
answered by ITUK and the other distributors telling us what they do, which is a conversation, not a data
collection. The table above is arithmetic, not behaviour.

---

## 5. Currency: the lever nobody is holding

The price is set in yen and converted. Because the margin is fixed by the letter and applied *after* the
conversion, **FX moves the euro price and the euro gross profit, and never moves the margin percentage at all.**

| Period | JPY/EUR | EUR price index | EUR gross profit index | Margin |
|---|---:|---:|---:|---|
| October 2023 | 146.6 | 111.7 | 111.7 | unchanged |
| October 2024 | 159.4 | 102.7 | 102.7 | unchanged |
| October 2025 (in use now) | 163.7 | 100.0 | 100.0 | unchanged |
| Stress, weak yen | 175.0 | 93.5 | 93.5 | unchanged |
| Stress, strong yen | 150.0 | 109.1 | 109.1 | unchanged |

**[MEASURED]** — `config.yaml`, `pricing_chain_and_fx_meta.json`

From the rate in use in 2023 to the rate in use today, the euro price of an **unchanged yen base price fell
11.7%**, and so did the euro gross profit per part.

And because our margin does not respond, FX moves our position against the independent market silently, with no
decision taken and no line in any pack:

| FX | Our net price vs the competing price |
|---|---:|
| 146.6 | 0.98× |
| 163.7 (today) | **1.09×** |
| 175.0 | 1.17× |

Two things follow.

**Every competitive comparison we hold is FX-stamped and none of them says so.** The index in the AIM dashboard,
the reference dealer price, the ratios in this paper — all of them move with a rate that was set on 1 October 2025.
A 7% currency move is larger than the difference between the ambition options we spend months debating.

**The yen base price and the class letter are IML's, and the rate is IML's.** So the two largest inputs to our
competitive position are both outside our control, and neither appears in any ISZE pricing discussion. That is not
a criticism of IML. It is an argument that ISZE should carry an FX sensitivity on every price pack it publishes,
because otherwise we will keep explaining a currency move as a pricing outcome.

---

## 6. Evidence: what we know and what we do not

### 6.1 Where the evidence sits

| Position | Lines | Billed € | Share |
|---|---:|---:|---:|
| Contested | 2,772 | 16,460,061 | 50.5% |
| Captive, measured | 190 | 956,100 | 2.9% |
| Captive by catalogue proxy | 41,829 | 12,963,455 | 39.8% |
| Lost | 277 | 1,275,211 | 3.9% |
| No position on file | 2,549 | 941,025 | 2.9% |

The **€12.96M** in "captive by catalogue proxy" is not a measured position. It is parts that appear in a governed
catalogue node with no competing alternative on file, and the build was corrected on 17 September precisely because
it had been rolling those up as a moat. Almost every billed part number appears in that catalogue. Read it as a
proxy and nothing more. **[MEASURED]** — `02_dashboards/pricing/_build/_spec_basis_meta.json`

| Evidence tier | Lines | Billed € |
|---|---:|---:|
| T1 — observed, same shop, same part number | 385 | 2,778,871 |
| T2 — published listing | 49 | 94,908 |
| T3 — Eucon, network level | 446 | 2,495,438 |
| T4 — category median | 461 | 1,554,429 |
| **T5 — no benchmark price** (evidence tier; 46,276 lines = 97.2% of the 47,617 priced lines, €25,672,208 = 78.8% of the priced euro) | **46,276** | **25,672,208** |

**83.5% of the priced book by euro has no same-shop and no Eucon benchmark** — that is the T4 and T5 tiers
together: 78.8% with no benchmark price at all, plus 4.8% carried only by a category median. **880 lines carrying
€5,369,216 — 16.5% of the priced euro — do have a benchmark.** Add the category-median tier back and it is **1,341
lines and €6,923,645, 21.2% of the priced euro.** **[MEASURED]**

Of the T5 block, 43,815 lines do have a captured-demand position, so the first gate works on them; only the second
is missing. **2,461 lines and €942,291 have neither.**

### 6.2 A correction to revision 1, and a data quality warning

**Revision 1 said the evidence base covers 307 part numbers and that the Autodoc file was one of the three
sources.** The part-number statement is right; treating Autodoc as a price source is not.

**`competitiveness_autodoc_risk.csv` cannot be used as a competitor price.** Its `autodoc_min_eur` column carries
the value **2.34 on 277 of its 298 rows** — a single constant. The `ratio` column is therefore 2.34 divided by the
list price, which makes a €4,834 engine assembly look 0.05% of list and produces a 1,435× "exposure". **The `ratio`
column is not an exposure measure and must not be quoted.** The part numbers and the cheapest-brand names in that
file are still useful — they tell us an alternative exists and who makes it — but the prices are not.
**[MEASURED]** — inspected.

**Revision 1's 83.5% and the model's 78.8% are two different measures, and the difference between them is the
category median, not a disagreement.** Both are shares **by euro** of the priced book €32,595,853, not shares of
lines. The **78.8%** is T5 alone — €25,672,208, no benchmark price of any kind on file. The **83.5%** is T4 and T5
together — €27,226,636, no same-shop and no Eucon benchmark — which adds the €1,554,429 that only a category median
carries. 83.5% − 78.8% = 4.8 points, exactly the T4 share.

### 6.3 Coverage is not uniform, and that is the opening

The evidence is badly distributed across families, and the least-evidenced families are the largest. But **brakes
are the exception** — and that is why brakes should be the pilot:

| Family | Part numbers | Billed € | With any competitor reference |
|---|---:|---:|---:|
| Brakes | 334 | 3,142,066 | **82.6% of the family's billed euro** |
| All families | 15,872 | 32,595,853 | 16.5% of the book's billed euro |

**[MEASURED]** — union of the three competitor files

### 6.4 Israel is not a discount channel, and the question is closed as a no-finding

On the twenty Israeli shop lines we could record, thirteen have any official purchase floor in our data to test
against — five distributors' floors, **no Israeli one among them**. **Nothing is below the floor. Not one line.**
The cheapest sits at **2.41×** its floor, the median at **5.95×**, the highest at **12.20×**, and **not a single
line is even as low as 2×**. **[MEASURED]**

| Shop price ÷ our distributor's floor | Lines |
|---|---:|
| below 1.00× — below the floor | **0** |
| 1.00–2.00× | **0** |
| 2.00–3.00× | **6** |
| 3.00–5.00× | 0 |
| 5.00–10.00× | **6** |
| above 10.00× | 1 |

**The earlier empty join was not a numbering problem, and this matters because the wrong diagnosis points at the
wrong fix.** The shops list our own Isuzu numbers. The join came back empty for two other reasons: the
replenishment bridge holds **zero UMI purchase rows**, and UTI prices only **2,201 part numbers — 14.4% of the
catalogue** — which intersects those shop lines **zero times**.

**So read the levels, not the multiples.** Israeli shops are **not winning on price**. Whatever they are winning
on, a cheaper genuine part is not it.

**And the lawful explanation must not be ruled out.** Buying genuine parts trade-to-trade is lawful and protected
by the motor vehicle block exemption, and no evidence of an unlawful route was found. A shop price sitting above a
floor does not identify a supply route, any more than a price below one would. The only Israeli rows that cross any
purchase floor are a dismantler selling **used**, dismantled parts, tagged as such on the listing. **The question
of how Israeli shops buy is therefore closed as a no-finding**, which is the honest result and not a clean bill of
health.

---

## 7. The volume question: what we tried, and what it says

### 7.1 What the panel is

ITUK dealer purchases by part number, CY2023 and CY2025, joined to the IE40 list price at the 2023 and 2025
vintage. Both quantities are measured. There is no proxy and no fitted demand curve. **[MEASURED]**

- 7,127 part numbers with both quantity and both prices
- 3,707 positive on both sides
- **3,662 with a computable arc elasticity**

### 7.2 What it says

| | |
|---|---:|
| Weighted quantity change, 2023 → 2025 | **−1.9%** |
| Median list price change on the same parts | **+3.3%** |
| Weighted arc elasticity | **−0.69** |
| Parts whose elasticity is below −1 | 41.3% |

A naive reading of that is an elasticity of −0.69: a 3.3% list increase is associated with a 1.9% volume fall.
**That reading is wrong, and the reason is the finding.**

### 7.3 Why the number is not identified

| | |
|---|---:|
| Interquartile range of the price change | **0.69 percentage points** |
| Parts whose price moved within ±1pp of the median | **70.6%** |
| Parts within ±0.5pp of the median | **55.4%** |
| Standard deviation of the elasticity inside that band | **22.4** |
| Parts that moved more than 5pp away from the median | 226 |
| Median elasticity of those 226 | **0.00** |
| Weighted elasticity of those 226 | **+2.64** |

Read the top row. **The index moves three quarters of the book by the same amount, to within two-thirds of a
percentage point.** There is almost no price variation in the data to measure a response against. And when we look
only at the 226 parts that did move differently, the median elasticity is exactly zero and the volume-weighted
figure is **positive** — those parts sold *more* when their price went up.

That is not evidence that demand rises with price. It is evidence that the parts which moved differently did so for
reasons correlated with their own demand: model changes, supersessions, new generations replacing old part numbers,
promotions, and a list re-cut that repriced parts whose volumes were already moving. **A single difference across
two periods cannot separate a price response from parc, mix, model change or competitive entry.**

### 7.4 Why this measurement is impossible, and what it means

This is not a data shortfall. It is a property of the method.

**Our pricing method changes almost every part by almost the same amount.** And it has to: a Laspeyres index solved
to a single weighted target, with per-line caps and floors, produces exactly that. **A uniform increase is, by
construction, unmeasurable.**

To make the question answerable we would need something the current method never produces: **the same part, in
comparable markets, at materially different prices, with nothing else changed.** That can be created deliberately —
a matched-pair trial across a group of distributors and a group of families — but it cannot be read out of history.

### 7.5 The choice is made before the counter

**Most dealers only sell Isuzu parts.** And the decision to use a genuine part or an independent one is usually
taken *before* anyone quotes a price — in the workshop's supplier relationship, in the factor's van that already
calls at the door, in what the technician trusts, in whether the part is on the shelf tonight. **[INFERENCE]**

If that is where the choice is made, then a price move at our level is not competing for a sale. It is competing
with a decision already taken. And that produces a specific, testable prediction: **volume should have no
relationship to where our price sits, because the customers who stay were never comparing.**

Tested on the family level, on the same commercial axis both times:

| Commercial posture | Billed € | Weighted price move | ITUK units 2023 | ITUK units 2025 | Units change |
|---|---:|---:|---:|---:|---:|
| Competitive parts | 14,001,293 | +5.36% | 180,644 | 192,692 | **+6.7%** |
| Accident parts | 6,664,468 | +6.56% | 68,656 | 65,971 | **−3.9%** |
| Repair parts | 6,485,059 | +6.77% | 59,808 | 65,136 | **+8.9%** |
| High value repair | 3,235,364 | +5.28% | 51,560 | 49,860 | **−3.3%** |
| Hardware & consumables | 487,265 | **+7.23%** | 65,244 | 61,876 | **−5.2%** |
| Comfort parts | 809,320 | +6.82% | 3,436 | 4,490 | **+30.7%** |

Across the families with both readings, **the correlation between the size of the price move and the size of the
volume move is 0.06.** There is no relationship. The family that took the largest increase lost volume, and so did
the family that took the smallest; the family that grew fastest took an above-average increase. **[MEASURED]**

**So the correct conclusion is stronger than "we cannot measure elasticity". It is that at this level in the chain
there may be very little of it to measure.** The customers who stay are not comparing, and the customers who leave
do not announce it. What a price move does here is change margin, not volume — which is exactly why the margin work
in §2 and the cost floor in §3 matter more than any elasticity estimate would.

### 7.6 What is actually known about elasticity, from outside

**There is one serious empirical study of automotive aftermarket parts demand**: a US specialty retailer, 3,400
stores, two years of weekly data from 800 stores, demand models across 23 hard-part subclasses, with recommended
prices field-tested across 500 stores. It is peer-reviewed and it establishes that the elasticity *is* estimable
and that the resulting prices beat the existing ones. **[MEASURED]** via the external review

**Its numeric elasticity table could not be obtained from any accessible copy.** So the study establishes
feasibility, not a coefficient.

Two of its structural findings are useful, though, and they match our situation:

- **Customers substitute within a quality tier, not between functions.** The relevant choice is a good part against
  a better part against a best part for the same job — which is precisely the genuine-versus-tier-4-versus-tier-2
  choice inside a brake pad. **So the elasticity that would matter to us is the cross-tier one, not the cross-family
  one.** Since the tier is chosen at the counter by someone who has already decided not to compare, that is the
  least measurable version of the question.
- **Within a subclass, price and market share are not positively correlated** — higher price does not signal higher
  quality in hard parts the way it does in groceries.

**And the closest thing to a usable number in the whole literature is a threshold, not a slope:** a 2025 survey
across 13 markets and 6,000 consumers found that **most consumers need more than a 10% discount before they will
even consider switching** from a genuine part to an unbranded one. That is a switching threshold, and it says that
at less than a ten-point gap there is no reason for anyone to move — and nothing at all about what happens at 30%.

**Two published price cuts that were studied in this work published no outcome data**, which is why the review's
conclusion is a negative one: the evidence base does not support any claim about the volume response to a price
change on automotive parts. That matches our own finding, arrived at independently. **[MEASURED]** via the review

### 7.7 The honest conclusion

**We should stop trying to estimate elasticity and start measuring something we can measure — whether the customer
compared at all.** The question worth answering is not "what does a 5% cut buy" but **"for how much of our volume
was there no decision to lose?"**

**One route does exist to a real number, and it is a field test, not an analysis.** The US study's method was to
model the parts, then test recommended prices across a subset of stores and measure the gross profit against a
control. That works here too: pick a family with evidence, agree a price change with a group of distributors, hold
a matched control group, and read the difference. It is the only method in the literature that produces a measured
coefficient, and it is the only one I would defend.

---

---

## 8. The pricing system: where we increase, where we drop

**This section is new in revision 3 and it is the centrepiece.** It replaces the description of an intention, which
is what revision 2 had, with a system that is built, that classifies every line, and that re-derives every movement
from a single number.

### 8.1 The system in one paragraph

There is one dial: the overall increase against today's prices, in euro or percent. **Management sets it.**
Everything else is a distribution rule that responds to the dial, so setting it to 3% or 7% re-derives every line.
The corporate exchange rate is applied, not chosen; it is not a dial and there is nothing to tune there.
**[MEASURED]** — `build_pricing_system_20260919.py`, `pricing_system_figures_2026-09-19.json`

### 8.2 The six tiers, and what each one means

| Tier | What it covers | Why it is priced this way |
|---|---|---|
| **SERVICE BASKET (PMS)** | The 14 PMS service categories — the parts a customer pays for at every service: oil, fuel, air and AdBlue filters, brake pads, discs, drums and shoes, clutch disc, kit, pressure plate, release bearing and booster | Held or cut. This is the customer's repeated running cost and the part of the book where a price move is felt most often, so it is defended for turnover. |
| **COMMERCIAL** | An independent alternative is freely available at a comparable price | Carries the increase at a damped rate. **This tier was called CONTESTED in the earlier work; it was renamed COMMERCIAL on 19 September 2026.** The name was changed because "contested" described the evidence position (a rival exists) while the tier's commercial content is that the customer has a freely available alternative. Anyone holding revision 2 should read CONTESTED as COMMERCIAL. |
| **CAPTIVE / GATED** | No substitute exists — the part can be made but not commissioned without our access | Carries the largest share of the increase. A control unit has no alternative on any shelf; a brake disc has three. |
| **CLOSING WINDOW** | Parts in families where a regulatory opening arrives on a timetable — ADAS and calibration content | Priced now, expected to erode. EU Delegated Regulation 2026/699 opens ADAS repair and calibration information to independent operators from 23 December 2026. |
| **BODY / LEGAL** | Crash-driven parts and parts carrying design protection in some member states | Damped, and — new in this revision — **lighting is separated inside it**, because §9 shows a specific and measured risk in raising lamp prices. |
| **UNCLASSIFIED** | No catalogue node could be assigned | Neutral. Left out of the family totals rather than guessed, and named as a residual. |

**[MEASURED]** — `PRICING_SYSTEM_STRATEGY_20260919.md` §2, `pricing_system_figures_2026-09-19.json`

### 8.3 What each tier carries, on every line

| Tier | Lines | L12M revenue | Share of the book | Price gain at the 5% dial |
|---|---:|---:|---:|---:|
| Service basket (PMS) | 816 | €3,332,334 | 16.5% | **−€18,664** |
| Commercial | 10,698 | €10,838,823 | 53.8% | +€570,990 |
| Captive / gated | 928 | €660,814 | 3.3% | +€61,283 |
| Closing window | 21 | €137,285 | 0.7% | +€13,906 |
| Body / legal | 4,477 | €4,252,793 | 21.1% | +€274,178 |
| Unclassified | 999 | €918,854 | 4.6% | +€58,944 |
| **Whole book** | **17,939** | **€20,140,903** | **100%** | **≈€960,600** |

**[MEASURED]** — `pricing_system_figures_2026-09-19.json`. The tier movements sum to €960,637 and the market
normalisation lands the four markets on €960,503; the €134 difference is the per-market normalisation described in
§8.5, not a measurement disagreement.

Three things in that table are the whole argument.

**The service basket is 16.5% of the revenue and comes down.** 816 lines on €3.33M of last-twelve-months revenue
move **down by €18,664** in total at the 5% dial. **The filters are cut hardest** — the four filter categories,
which the external review places at the most competitive end and which a distributor's customers feel most often.
Oil filters come down across every market; UTI's oil filter comes down by €2,051 and its AdBlue filter by €3,140.
**[MEASURED]**

**The commercial tier is 53.8% of the revenue and takes the bulk of the increase**, at a damped rate, because it is
also the tier where a customer can leave.

**And the captive tier — 3.3% of revenue — carries the steepest rate in the book**, because it is the only tier
where a price move cannot be answered by buying something else.

**A flat increase would have put the same percentage on an oil filter as on a software-coded control unit.** That is
what this system exists to stop, and the line list shows it is now stopped. **[MEASURED]**

### 8.4 Turnover, not margin

Every line is weighted by its last-twelve-months quantity, so the sheet shows, per line, the euro of price gained
against the revenue exposed. **Within the top 10% of a market's revenue the movement is damped to three quarters of
the tier rate, and inside the top quarter to nine tenths**, because on a turnover line the volume lost costs more
than the price earns. The objective is turnover, so the increase is carried where volume is least likely to move:
on parts a customer cannot buy elsewhere. **[MEASURED]** — `build_pricing_system_20260919.py`, `volume_damp`

### 8.5 The dial, at three levels

| Market | 3% | 5% | 7% |
|---|---:|---:|---:|
| PR00 (the mainland European distributors) | €353,236 | €588,727 | €824,218 |
| UTI (Israel, commercial vehicles) | €108,687 | €181,145 | €253,603 |
| UMI (Israel, light commercial) | €76,468 | €127,447 | €178,426 |
| CIS | €37,910 | €63,184 | €88,458 |
| **Total** | **€576,301** | **€960,503** | **€1,344,705** |

**[MEASURED]** — `pricing_system_figures_2026-09-19.json`. UTI and UMI are separate distributors and are never
blended; they appear as two rows here as they do everywhere in this paper.

The system normalises so that the quantity-weighted outcome lands on the dial. At 5% the achieved weighted movement
across the four markets is 5.00%. The market figures differ from a clean 5% each because the mix of tiers differs by
market: **UTI carries an unusually large filter basket and CIS almost none**, so the same rule produces a different
total in each. **[MEASURED]**

### 8.6 Where a family average is really one part number

This is a warning the external review makes and our own data reproduces, and the sheet flags it on the line. Where a
family's revenue is concentrated in one part number, the family average describes that part and not the family.
**[MEASURED]**

| Market — family | Family revenue | Largest part number | Its share |
|---|---:|---|---:|
| UTI — brake pads | €82,264 | `8982447940` | **97%** |
| UTI — oil filters | €154,475 | `8982984040` | 71% |
| UMI — aftertreatment | €146,087 | `8975359391` | 90% |
| UMI — turbochargers | €95,729 | `8974985741` | 73% |
| UTI — clutch kits | €90,141 | `5876102320` | 100% |
| PR00 — brake discs | €628,493 | `8983767550` | 63% |

**64 market-by-family leaves carry more than 40% of their revenue in a single part number, on at least €25,000 of
revenue.** Reading a family movement as a market movement on those leaves will mislead. There is a connection to §13:
the brake pad number that is 97% of UTI's brake pad family is the same part number carrying the family's largest
step in the brakes pilot, and the same number ITUK and UTI are both locked into.

### 8.7 The new models, held outside the dial

**P700 and D-Max 2.2L (RG21) are held as their own block, not folded into the dial.** **[MEASURED]**

| Block | Lines | New part numbers | Carryover | L12M revenue | Ramp factor (median) |
|---|---:|---:|---:|---:|---:|
| P700 | 2,029 | 1,132 | 897 | €2,300,319 | 1.05 |
| D-Max 2.2L (RG21) | 3,605 | 1,707 | 1,898 | €4,538,718 | 1.00 |

Two reasons. **New part numbers carry no prior-period volume, so they carry no weight in the index and the dial
does not bind on them at all** — their price is a launch decision, taken separately (§11). And the ramp adds volume
as the fleet grows, which moves turnover in the opposite direction to a price rise.

### 8.8 What could not be classified or priced

Stated as residuals, because a line left out of a total must be named.

- **999 lines are UNCLASSIFIED**, €918,854 of revenue, 4.6% of the book. The bulk is the catalogue's own
  `Review needed` residual — 962 lines, €908,188 — plus the accessory tail. They take the neutral dial rate and are
  left out of the family totals rather than guessed. **[MEASURED]**
- **709 lines carry no current price** on the price list and cannot be repriced. They are marked and excluded from
  the euro. **[MEASURED]**
- **Cabin and blower filters could not be separated.** The catalogue puts the blower motor and the cabin filter in
  one node, `Blower / fan`. The house convention treats the blower filter as a service-basket part, so the node sits
  in the service basket, but the separation is not clean and the sheets flag it. **[MEASURED]**
- **ADAS is effectively absent from the catalogue.** Only a handful of lines carry a radar or camera description, so
  the closing-window tier is **21 lines on €137,285** of revenue. The regulatory opening from late 2026 has almost
  nothing listed against it yet. **[MEASURED]**

### 8.9 What this section does not do

It does not set the increase — the dial is management's, and the 5% used throughout is a placeholder. It does not
model volume response to a price change: the review is explicit that no usable elasticity exists in the evidence
base, and §7 shows why our own data cannot supply one. The switching threshold of about 10% is a threshold and not
a slope, and it is used here only to frame the commercial tier as genuinely commercial.

**And one warning on a number that is in circulation.** The pricing action map used in earlier work reports roughly
**€96K of headroom against €16.0M at risk on CY2025 — a 1:167 ratio**. Its own notes say `at_risk` is the full
theoretical gap and the addressable base is modelled. **Treat that as direction, not as a fact to build on:** it says
the at-risk base is far larger than the pricing headroom, which is the same conclusion this section reaches from the
other side. Do not quote the ratio as a measurement. **[INFERENCE]** on a modelled input

---

## 9. Collision parts, insurance write-off thresholds, and the risk in raising lamp prices

**This section is new in revision 3, and it is one of the strongest things in the paper, because the mechanism is
not a theory — a court has recorded it and our own distributor has documented it.**

### 9.1 The finding

**Collision and bodywork parts carry a risk that mechanical parts do not.** In Israel a vehicle is declared a total
loss at a fixed proportion of its pre-accident value, and the repair estimate that is compared against that value is
built from our parts prices. A high enough parts line can therefore push a repairable truck over the threshold and
lose the entire repair — which is worth considerably more than the margin earned on the parts. **Filters, brakes and
other routine service parts are not affected, because the write-off regime exists for accident repairs, not for
service.** **[MEASURED]** for the mechanism; see §9.2 and §9.4.

**One wording correction, recorded because it changes how the section is read.** The concern as it was first put was
that the distributor asked us not to price lamps too high. What the correspondence actually contains is the
distributor showing us the price gap in the market and asking for relief, and it was Isuzu's own parts operations
that first resisted a reduction, on the grounds that these parts faced "not so much competition" — while conceding
that lamps were the exception, because non-original lamps were already being imported. So the direction of the
concern is right and it is the distributor's, but the words in the file are Isuzu's, and the route proposed in 2018
was a funded rebate rather than a lower price (§9.7). **[MEASURED]**

### 9.2 Why — the Israeli thresholds

Two thresholds apply in Israel, and they are hard numbers rather than commercial practice:

- A vehicle is a **total loss** when the damage reaches **60% of its pre-accident value**.
- The insurer may settle as a **constructive total loss from 55%**, at the assessor's determination.

**[MEASURED]** — management note of 19 September 2026, reading the policy wordings directly

**The pickup research of the same date records the same clause at 50% rather than 55%**, reading an insurer's policy
wording titled "Insurance policy for private and commercial vehicles up to 3.5 tons", which allows the individual
schedule to set its own rate **"however, no more than 60%"** for a total loss and **"no more than 50%"** for a
constructive total loss. **Both readings are of real documents and they differ.** The most likely reconciliation is
that the cap in the policy wording is 50% and the 55% figure is a schedule rate within it, but **this paper does not
assert which, and a reader checking the clause should expect to find either number.** The conclusion does not depend
on which is used: both are far below the 100% at which a repair is straightforwardly economic.
**[MEASURED]** for both readings, **[NOT FOUND]** for the reconciliation

**The assessor decides which parts are used in the repair**, and the parts appear in the estimate at their list
prices. The assessor does not set the market price of the parts. The Israeli Supreme Court, sitting as the High
Court of Justice, records in terms that *"the inflated parts prices caused many vehicles to be declared a 'total
loss' or 'constructive total loss' even without need, because the cost of their repair was high relative to their
value."* **[REPORTED — NOT VERIFIED]** — carried from the research paper of 19 September 2026, which read the
decision directly (published 2026-03-09) and which the management note did **not** independently re-open

The same litigation establishes that the assessor's role *"is limited to determining the type of parts required for
the repair and estimating labour cost, but not the final market price of the parts."* **[REPORTED — NOT VERIFIED]**,
same source and same limit.

**The state's own audit gives the scale of the market problem**: of 144 parts examined, 60% carried a price gap
above 50% and 43% above 100% against other importers; and parts prices to the public were in most cases about 50%
above what was actually paid for them. **[REPORTED — NOT VERIFIED]** — State Comptroller, March 2022, carried from
the same research paper

### 9.3 What it means commercially

**A price rise on a collision part can be self-defeating.** Three things happen at once when the parts line pushes a
repair over the threshold: the repair is not carried out and is settled at the vehicle's value instead; the parts
are never sold; and for a fleet on a repair-and-maintenance contract the parts consumption for the remaining
contract years is lost as well.

**UTI runs 1,700 trucks on five-year repair-and-maintenance contracts and sells the parts to maintain them**
**[MEASURED]** — UTI's own presentation, July 2026, page 8 — so a written-off truck removes a stream of consumption,
not a single sale.

**What the arithmetic looks like on UTI's own numbers. [INFERENCE]** UTI's presentation compares the old model with
the P700 for two weight classes. The collision package for the N/7.5 series moves from €679.21 to €2,144.48
(**+215%**), and for the F/10 series from €923.66 to €2,314.14 (**+150%**). **[MEASURED]** — UTI's presentation,
page 27. The lamps inside those packages move substantially more than the package as a whole:

| Series | Lamps, old model | Lamps, P700 | Increase |
|---|---:|---:|---:|
| N/7.5 (rear light, head lamp, signal) | €142.92 | €906.26 | €763.34 |
| F/10 (rear lamp, head lamp, turn signal) | €149.27 | €528.75 | €379.48 |

And at the individual part level, from the same deck:

| Item | Old model | P700 | Increase |
|---|---:|---:|---:|
| Head lamp (F/10) | €85.93 | €370.80 | **+332%** |
| Rear light (N/7.5) | €30.42 | €404.09 | **+1,228%** |
| Turn signal (F/10) | €30.31 | €131.37 | **+333%** |
| Signal (N/7.5) | €26.57 | €131.37 | **+394%** |

**[MEASURED]** — UTI's presentation, pages 30 and 31. Note that these are two model generations, and part of the lamp
gap may reflect a **different lamp** rather than a pure list-price increase. **We have not separated the two**, and
that limit is carried in §9.5.

**And the bumper, which is the clearest single example of list engineering rather than technology.** The bumper
assembly was split **from one part at €143.37 into four parts at €320.00**, which UTI's deck describes as inflating
the total repair cost by **123%** with no material change to the part. **[MEASURED]** — UTI's presentation

On those figures the lamp increase is 36% of the N/7.5 package and 16% of the F/10 package, so the lamp increase
destroys more margin than it earns once roughly **one job in four (N/7.5)** or **one job in seven (F/10)** is lost
because the assessment crossed the threshold. **[INFERENCE]** — a break-even calculation on the deck's numbers, not
an observed loss rate.

### 9.4 What we measured in our own business

The figures below are for **UTI**, measured on the last twelve months of billed parts sales. The selection is
stated so the numbers can be reproduced:

- **Lighting** — the six catalogue nodes: Headlamp, Tail / combination lamp, Marker / signal lamp, Fog lamp, Other
  lighting, Lens / reflector.
- **Collision and bodywork** — the Body parts group less the three nodes that are not bodywork (Step / guard,
  Handle / lock, Interior / exterior cover). That leaves Panel, Door, Bumper, Grille, Fender, Glass / window, Other
  body, Body structure, Trim / molding and Interior trim.

| Measure | Lighting | Collision and bodywork |
|---|---:|---:|
| Lines | 86 | 244 |
| Units | 3,213 | 7,168 |
| Revenue, last twelve months | **€133,667** | **€218,147** |
| Share of the two families together | **38.0%** | 62.0% |
| Weighted margin | **48.2%** | **55.0%** |
| Revenue in the lowest-margin class (47.5% margin) | **73.9%** | **0.0%** |

**[MEASURED]** — all figures, `UTI_LIGHTING_COLLISION_MANAGEMENT_20260919.csv`

**Lighting is therefore the smaller and the thinner-margin half of the two families, and it is already priced
defensively:** three-quarters of its revenue sits in the lowest-margin class we publish, against none of the
collision revenue. Collision revenue sits mainly in the 56% margin class (69.5%). Lighting is **3.9% of UTI's entire
parts book** (€133,667 of €3,400,405). **[MEASURED]**

**The share depends on whether the mirror nodes are counted, so both figures are given.** The three mirror nodes
(Mirror assembly €25,560, Mirror arm / bracket €3,565, Mirror cover €929, in total €30,054) sit in a separate
catalogue group from body parts. Counting them in the collision side gives lighting **35.0%** of the two families;
leaving them out gives **38.0%**, which is the figure in the table above. Both are correct and the difference is
only definitional. The recommendation in §15 does not depend on which is used. **[MEASURED]** for both figures;
**[INFERENCE]** for the choice to report the bodywork-only basis as the headline, because a mirror is a bodywork
item damaged in the same accidents and quoted on the same repair estimate as a panel or a bumper.

**An earlier internal review gave lighting as 30.8% of the two families**, against 38.0% here. That figure rests on
a keyword split of the parts descriptions rather than on the catalogue grouping, and its collision pool was
€299,002. For comparison, the bodywork nodes named above total €218,147 and the whole body-parts group including the
mirror nodes totals €314,344. **We could not reproduce the 30.8% from the method as it was written down, nor
determine which items made up the difference.** A figure this far apart should not be quoted to management without
settling the definition first, which is why the selection is stated above in full. **[MEASURED]**

**Four lighting lines, €17,469 or 13% of lighting revenue, have no price-list entry at all** and could not be given
a margin. **[MEASURED]**

### 9.5 What we do not know

Stated plainly, because it decides how far this finding should be allowed to move a price.

1. **The threshold for vehicles above 3.5 tonnes is not established. [NOT FOUND]** The thresholds come from the
   policy for private and commercial vehicles **up to 3.5 tonnes.** Heavier vehicles run under a separate policy,
   and we could not retrieve its total-loss clause.
2. **UTI's fleet sits exactly in that gap. [MEASURED] / [INFERENCE]** The 1,700 trucks on repair-and-maintenance
   contracts are all above 3.5 tonnes — the weight classes in UTI's own presentation run from 4.5 tonnes upward. So
   our write-off exposure for the fleet in question is **unverified.** If the heavier-vehicle thresholds are higher
   or absent, the case for pricing defensively weakens; if they are the same or lower, it strengthens.
3. **No measured rate at which a parts line tips a repair. [NOT FOUND]** The court states the causation; no one
   publishes the frequency. Without it, the break-even in §9.3 is arithmetic on an assumed loss rate, not a
   measured loss rate.
4. **No parts-price elasticity study. [NOT FOUND]** No published study, in Israel or the UK, of how much repair
   volume is lost per point of parts price. This is the single measurement that would turn the recommendation below
   from a judgment into a calculation.
5. **No record in our own files of a repair actually lost. [NOT FOUND]** No lost repair, declined quotation or
   insurance ceiling is recorded anywhere in the estate. The mechanism is documented in principle; it is not
   observed in our business.
6. **No UK statutory threshold; UK practice is roughly 60–70% by trade report. [TRADE]**
7. **The presentation's own price table does not reconcile. [MEASURED]** Its per-part columns sum to €917.76 for the
   F/10 old model against a stated €923.66, and to €881.68 for the N/7.5 old model against a stated €679.21. **We
   therefore quote the package totals and the item-level lamp movements separately and never add the two
   together.**
8. **The quoted package is only about 4% to 11% of the truck's value**, so on its own it cannot push a whole vehicle
   over a threshold set at 55–60% of value; it can only do so alongside a substantially larger repair.
   **[INFERENCE]**

### 9.6 The precedent that already exists

**In 2018 the answer proposed was a funded rebate to the insurer, not a lower list price.**

In that correspondence UTI's parts management set out how insurance-funded body repair works in Israel and showed
the price gap against the aftermarket; Isuzu's parts operations asked whether genuine body-part sales were being
lost and named doors, lamps, grilles, side steps and body panels; and ISZE's aftersales management proposed **a
funded rebate to the insurance company, split 50:50 between Isuzu in Japan and ISZE**, paid where the insurer used
genuine parts and settled against results at the end of a year. **[REPORTED — NOT VERIFIED]** — 2018 correspondence
of 30 May 2018 and 17 September 2018, forwarded on 4 October 2018, carried from the research paper; the mailbox was
not independently re-opened for this section

**Why it matters as a precedent.** That route protects the published price rather than discounting it, it is
budgetable, and it can be made conditional on genuine-part usage. Where a write-off risk is real, it should be
tested before any further reduction of a list price — including the one proposed in §15.

### 9.7 The loading on a lamp line, and the case for the pickup

**The exception that inverts the truck picture.** The 60% and 55% thresholds were verified against the policy for
vehicles **up to 3.5 tonnes**, and the above-3.5-tonne clause was never found (§9.5 item 1). **The pickup sits
squarely inside the policy we did verify** — it is registered as a commercial vehicle (N1) in Israel, including the
double cab — so **the collision write-off mechanism applies to the pickup more cleanly than it does to the trucks.**
**[MEASURED]** — policy wording read directly; see §10.5

Two further clauses in the same policy matter commercially:

- For part replacement, where the repair requires a chassis part **or a light**, the part is replaced with one of
  **"similar description or characteristic"**. **[MEASURED]** That is the policy text itself setting a quality
  standard that does not insist on a genuine part. It is the cleanest statement of a ceiling on lamp pricing that we
  hold.
- New or genuine parts are required for vehicles **up to two years old**, unless the schedule provides original-parts
  coverage. **[MEASURED]** The genuine-part pull is therefore strongest in the first two years and weakens after.

---

## 10. The pickup market: does the compliance regime bind the buyer?

**This section is new in revision 3.** It covers the pickup — the light commercial vehicle — in four markets only:
the United Kingdom, Ireland, Portugal and Israel. It matters because the pickup buyer is a different commercial
animal from the truck buyer, and because the answer to the licensing question turned out to be the opposite of what
the brief for this work assumed.

### 10.1 The finding in one page

**The framework we set out to research does not govern our main UK customer, and that is the finding.**

The UK Operator's Licence exists to control goods vehicles above 3.5 tonnes gross plated weight. The D-Max is plated
at **3,100 kg**, so it is not caught. It is also exempt as a **dual-purpose vehicle**, which the regulations list as
a class for which no licence is required. Two independent reasons, and the same conclusion. **The pickup buyer is not
locked into a compliance regime, so roadworthiness risk does not make them pay more for a part.** **[MEASURED]** —
GOV.UK licensing guide; Goods Vehicles (Licensing of Operators) Act 1995; Goods Vehicles (Licensing of Operators)
Regulations 1995, Schedule 3 paragraph 2; Road Vehicles (Construction and Use) Regulations 1986 regulation 3;
manufacturer's own weight figures

The computation: the 4×4 double cab has a published kerb weight of **2,045 kg**, and kerb weight includes a full
tank; the tank is 72 litres and diesel is about 0.83 kg per litre, so the fuel is about 60 kg. The implied unladen
weight is therefore about **1,985 kg**, against the **2,040 kg** limit — roughly 55 kg of headroom. **If a specific
variant were to exceed 2,040 kg unladen, the dual-purpose exemption would fail and the vehicle would fall back on
the ordinary goods-vehicle test, where it still passes because 3,100 kg is below 3,500 kg. Both routes lead to the
same answer.** **[MEASURED]** on inputs and definition; **[INFERENCE]** on the subtraction. The 1,985 kg figure is a
computation from published weights, **not a weighbridge certificate**, and it does not need to be.

**And there is one real exception, which is stated in §10.3 because it is the counter-argument to everything above.**

### 10.2 Who we are actually selling to

| Market | Distributor carrying the pickup | Buyer, and the consequence for price |
|---|---|---|
| **United Kingdom** | **IUK** — the light commercial network (models coded TF). **ITUK is the separate truck network** (N and F series). Never blend. | Tradesmen, construction, farming, plus a lifestyle tail. A market of very small operators: **more than 46,000 of 64,448 licensed operators run five vehicles or fewer.** The buyer is a one- or two-vehicle business, and is price-sensitive and able to switch. **[MEASURED]/[TRADE]** |
| **Ireland** | **One distributor** — Isuzu Ireland 2020 Unlimited Company, part of the Harris Group, 25 dealer locations after five appointments in 2025. | Farmers, contractors, utility workers and tradespeople. **Nearly half (48.85%) of Irish light commercial registrations in 2025 were business or company, 18.9% leasing or contract hire, and 12.6% private.** Two-thirds institutional. **[MEASURED]** |
| **Portugal** | **Imotors** | A small business or self-employed buyer, and the purchase is tax-driven. **More than 90% of pickups sold in Portugal are homologated with three seats** — the left rear seat is replaced with a toolbox to secure goods-vehicle tax treatment, deductibility of VAT and exemption from the autonomous taxation. The three-seat version is about **€5,500 cheaper at retail** for that reason. **[MEASURED]** |
| **Israel** | **UMI** carries the pickup (the official D-Max importer). **UTI is the separate truck and bus importer.** Never blend. | Two different answers depending on whether you look at new sales or the installed fleet. **Of the 1,602 D-Maxes sold in 2025, the single best-selling trim (697 units) went mostly to leasing companies.** But **66.4% of all D-Maxes on the road are in private ownership** against 26.4% company. New sales are fleet; the fleet in service is private. **[MEASURED]/[TRADE]** |

### 10.3 Duty cycle, which drives how often the customer buys

**Measured annual distance for the D-Max and equivalent light vehicles:**

| Market | Vehicles in sample | Measured annual distance |
|---|---:|---:|
| **Israel (UMI)** | 13,611 | **34,443 km** |
| Ireland | 426 | **27,998 km** |
| United Kingdom | 29,646 | **24,481 km** |
| Portugal (Imotors) | 1,596 | **22,742 km** |
| Europe, all markets | 76,208 | **25,600 km** |

**[MEASURED]** — `01_data/08_Distributor/EU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx`, service data for light
vehicles. These are measured distances, not assumptions.

**One correction that must travel with that table, because it is easy to misread.** The Israeli row is **UMI alone**
— 13,611 VINs, and the file's own distributor label on that row is `UMI`. **UTI is not in that file at all**, and
neither distributor is blended with the other anywhere in this paper. So **34,443 km/yr is UMI's measured mileage,
not "the Israeli market figure"**, and a reader should not apply it to UTI or to the truck fleet. **The equivalent
measured figure for UTI is not in this source. [NOT FOUND]** This matters in a paper that also discusses UTI,
because an "Israel" mileage number sitting beside UTI material would read as the truck fleet's — and it is neither
UTI's nor a truck figure.

Israel runs a third further than Portugal. The same part number is bought roughly half again as often per vehicle
in Israel, so a price move there is felt more often and a lost sale costs more. This is the single most useful
measured input we hold for the pickup question.

**The vehicle fleet is very unevenly distributed.** Vehicles in service, 2025:

| Market | Pickup and light commercial base | Truck base |
|---|---:|---:|
| United Kingdom — IUK / ITUK | **47,783** (IUK) | 22,191 light + 877 F-series (ITUK) |
| Israel — UMI / UTI | **18,542** (UMI) | 6,059 + 4,277 (UTI) |
| Portugal — Imotors | **4,733** | 2,206 + 269 |
| Ireland | **1,338** | 731 + 92 |

**[MEASURED]** — `01_data/00_derived/uio_by_market_type_year.csv`

**And one disclosure on that table that matters for anything expressed per vehicle.** The UK pickup base of
**47,783 light commercial vehicles is flagged `is_estimate`, not `is_actual`, in our own fleet data** — as is every
row in that table for 2025. **[MEASURED]** — the `is_estimate` column is `True` and `is_actual` is `False` on those
rows; the source is `ISUZU_UIO_Overview_2026.xlsx`. So the UK base is our own modelled figure, and **any per-vehicle
rate built on it inherits that.** It is not a registration count.

**In the UK the fiscal ground moved under the buyer in April 2025.** From 6 April 2025, the tax authority no longer
treats a double-cab pickup as a van for benefit-in-kind purposes; most are now expected to be treated as cars. The
one-tonne payload test survives only for VAT. Transitional protection runs to 5 April 2029. **[MEASURED]** — HMRC,
internal manual EIM23151.

The market reacted. UK pickup registrations were **37,308 in 2025, down 0.7%**, after a spike in early 2025 as
buyers moved ahead of the change; in **August 2026 they were 404 units, down 61.2% year on year.**
**[MEASURED]** — SMMT.

> **Pricing consequence:** in the UK the working buyer has just been made to pay more tax for the same vehicle.
> That is not a market in which to raise the visible service-part basket.

### 10.4 Where the pickup is serviced, and who pays

**Servicing goes outside the dealer network, and it is openly advertised.** This is the most important difference
from the truck business, and it is not a theory — independent garages market against the dealer on exactly this
point.

- In the UK, independent garages advertise fixed-price D-Max servicing "up to 50% less than the Isuzu dealer", and
  state explicitly that the manufacturer's warranty is preserved. **[TRADE]** — garage service pages, read
  19 September 2026
- Under EU competition rules the customer may use an independent workshop and matching-quality parts without
  affecting the warranty. A warranty claim can only be refused where the independent work or a defective
  third-party part **caused** the fault. **[MEASURED]** — Regulation 461/2010 and the accompanying guidelines
- The same rules mean a parts maker supplying the vehicle manufacturer can sell the identical part into the
  aftermarket under its own brand.

**The practical effect:** the customer has a lawful, cheaper route that preserves the warranty. The genuine part must
therefore be defensible on quality and availability, not on the warranty. In the truck channel the maintenance
contract does more of that work for us; on the pickup it does much less.

**And the pickup aftermarket is retail-visible in a way the truck aftermarket is not.** Representative UK listings,
read 19 September 2026:

| Part | Listing | Price |
|---|---|---|
| Genuine Isuzu oil filter `8982705240` | specialist parts retailer | **£16.99** |
| Cross-referenced alternative oil filter | Blue Print `ADZ92130` | **£30.00–£36.00** |
| Genuine Isuzu air filter `5876150020` | agricultural/parts retailer | **£31.25 inc VAT** |
| Blue Print fuel filter (D-Max 2.5) | motor factor | **£14.57** |
| Blue Print air filter (D-Max 2.5) | motor factor | **£29.40** |
| Blue Print cabin filter (D-Max 2.5) | motor factor | **£21.16** |
| Brembo front brake pads (D-Max) | price-comparison site | **£45.99–£49.49**, with a published price history |

**[MEASURED]** — retailer product pages and a price-comparison listing

Two things follow. First, the parts are visible to the end customer in a way truck parts are not — the buyer can look
up the number and compare. Second, **a published price history on a consumer site means our price and our
competitors' prices are compared automatically, without anyone in this company being asked.**

**Who pays, by market:**

| Market | Funding of the repair |
|---|---|
| **Israel** | For collision and bodywork, the insurer, through an assessor. **The total-loss thresholds sit in the policy for private and commercial vehicles up to 3.5 tonnes. The pickup is inside that policy.** The insurer's estimate is built from our parts prices. **[MEASURED]** |
| **Israel — the exception** | The same policy notes that owners of older, lower-value vehicles often drop comprehensive cover and carry third-party only. For those vehicles a repair is owner-funded, and the buyer is then a private individual paying cash and free to shop. **[MEASURED]** |
| **United Kingdom** | Bodywork is insurer-funded through approved repairer networks, and some specialist commercial policies promise genuine parts and a five-year repair warranty. But that is a **policy promise, not a legal requirement** — no UK rule requires genuine parts. Mechanical repair is usually self-funded or inside a contract-hire package. **[MEASURED]/[TRADE]** |
| **Ireland** | In practice a mixture: business-funded for mechanical work, insurer-funded for collision. No Irish rule requiring genuine parts was found. **[INFERENCE]** |
| **Portugal** | Business-funded for mechanical work through leasing or the operator; insurer-funded for collision. **[INFERENCE]** |

**Leasing matters, because a lessor buys on cost.** In the UK a D-Max leases at roughly **£542–£637 per month**,
with maintenance cover as an option at **£27.74–£49.74 per month** covering servicing, tyres, exhausts and
batteries; where the maintenance option is taken, the finance provider chooses where the vehicle is repaired and
buys on cost. In Ireland, **leasing and contract hire is 18.9% of all light commercial registrations.**
**[MEASURED]** — leasing broker listings; SIMI. **The consequence is the same in all three: the more of the pickup
fleet that is leased with maintenance included, the more of our parts demand is bought by a lessor on cost rather
than by a driver on need.**

### 10.5 The licensing and compliance test, market by market

| Market | Does an operator licence bind the pickup? | What does bind it | Grade |
|---|---|---|---|
| **United Kingdom** | **No, twice over** — 3,100 kg plated against a 3,500 kg threshold, and exempt as a dual-purpose vehicle at about 1,985 kg unladen against a 2,040 kg limit | **Only towing.** A combination is licensed when vehicle and trailer together exceed 3.5 tonnes, and the D-Max has a **6,000 kg gross train weight**. See §10.6 | **[MEASURED]** |
| **Ireland** | **No.** An Irish road transport operator's licence applies above 3.5 tonnes for national operations (2.5 tonnes international); a pickup used within Ireland does not need one | **An annual commercial roadworthiness test plus a statutory maintenance duty** — see below. **Ireland is the strictest of the four, not the lightest** | **[MEASURED]** |
| **Portugal** | **No** — the European framework threshold applies above 3.5 tonnes and the pickup sits below it | **The tax classification, not a compliance regime.** The certificate of conformity decides whether the pickup is a goods vehicle (N1) or a passenger vehicle (M1), and the tax difference between the two routes can be **€4,000–€8,000** | **[MEASURED]** for the tax structure; **[NOT FOUND]** for a Portuguese-language primary source on the licensing threshold — the position is an inference from the European framework and is recorded as a gap, not asserted |
| **Israel** | **No** operator licence; the pickup is registered as a commercial vehicle (N1), including double cabs, and takes an annual test | **The insurance mechanism.** The pickup sits inside the verified up-to-3.5-tonne policy (§9.7) | **[MEASURED]** |

**Ireland, in full, because it is the sharpest contrast in this section:**

- Any light commercial vehicle **must pass a commercial vehicle roadworthiness test one year after first
  registration and every year after that**, whether taxed commercially or privately. It does not take the car test
  regardless of how it is taxed. **[MEASURED]** — Road Safety Authority and CVRT
- The test definition of a goods vehicle is **"a vehicle constructed or adapted primarily for the conveyance of
  goods or a burden of any description, whether or not it is used for such a purpose."** A pickup is inside it.
  **[MEASURED]** — CVRT
- Owners and operators of light commercial vehicles have a statutory duty under the Commercial Vehicle
  Roadworthiness (Vehicle Maintenance) Regulations 2013 to **"develop and maintain in place a system for the regular
  inspection and maintenance of the vehicle"** and to review it periodically. **[MEASURED]** — quoted on the RSA's
  light commercial vehicle page
- To use the vehicle commercially at the €333 goods rate, the owner must sign a Goods Only Declaration confirming
  the vehicle is used solely for business and **not at any time for social, domestic or pleasure purposes.**
  **[MEASURED]** — local authority motor tax guidance

> **Pricing consequence:** the Irish pickup owner is not licensed, but he is on an annual test cycle with a
> documented maintenance obligation and he may have signed away private use of the vehicle. He is a committed
> commercial owner with an annual compliance event. **That is a marginally more captive buyer than the UK's — but he
> is also a small operator who can buy the same Blue Print filter from the same factor.**

**Portugal, in full, because the mechanism there is fiscal rather than regulatory:**

- A double-cab pickup may be homologated either as a goods vehicle (N1) or a passenger vehicle (M1), and **the
  individual certificate of conformity decides which** — not the model. The tax difference between the two routes
  can be **€4,000–€8,000**. **[MEASURED]**
- **More than 90% of pickups sold in Portugal are homologated with three seats.** Manufacturers have adjusted their
  ranges accordingly, including Isuzu, which offers three-seat derivatives of the double cab including with
  four-wheel drive. The engineering is fiscal: the two rear seats are removed and replaced with a small toolbox.
  **[MEASURED]**
- Three-seat homologation makes the vehicle a light goods vehicle, which **allows businesses and self-employed
  people to deduct the VAT**, and **exempts them from the autonomous taxation**. The three-seat version was quoted
  at almost **€5,500 below** the equivalent five-seat version. **[MEASURED]**
- A pickup below 3.5 tonnes takes the N1 inspection cycle: **first inspection two years after first registration,
  then annually** — lighter than the truck cycle of annual inspection from the first year. **[MEASURED]**

> **Pricing consequence:** the Portuguese pickup is bought as a tax instrument by a business that has already been
> pushed into a three-seat commercial homologation to save money. That buyer is rational and cost-aware by
> construction. It is not a lifestyle buyer, and it is not a truck operator. It is a small business that has already
> chosen the cheaper route once, and will do so again.

### 10.6 The exception that does bite: towing

There is one real exposure in the UK and it is worth stating, because it is the counter-argument to the rest of this
section.

For a vehicle and trailer combination, a licence is required when **the maximum laden weight or unladen weight of
the vehicle and trailer combined exceeds 3.5 tonnes.** The D-Max has a **gross train weight of 6,000 kg** and a
3,500 kg braked towing capacity. A D-Max towing a plant trailer or a mini-digger at or near capacity is a combination
of up to 6,000 kg — far above the threshold. **[MEASURED]** — GOV.UK licensing guide; manufacturer's train weight
and towing figures.

> **Pricing consequence, and it is a real one.** The tradesman who uses the pickup as a car and a van is not
> licensed and is not captive. **The tradesman who tows plant is licensed, keeps records, has safety inspection
> intervals, and has his licence on the line.** Those are different customers for the same vehicle, and the second
> is materially less price-sensitive on anything that keeps the vehicle legal and moving. **We cannot currently tell
> them apart in our sales data.** That is an internal data gap, not an internet one, and it is the one worth closing
> first.

### 10.7 Where we can take more, and where we can lose more

**Where we can take more money — ranked:**

1. **United Kingdom — the D-Max 2.2L launch, on the strength of the warranty window.** The UK pickup base is our
   largest of the four at **47,783 vehicles** (estimated, not actual — see §10.3), and the warranty is the longest we
   offer — **five years or 125,000 miles**, made up of a three-year/60,000-mile manufacturer term that the importer
   extends to the full five years. **[MEASURED]** A part that cannot be substituted during that window can carry a
   launch price. §11 found that 13 functional aftertreatment parts sit **exactly at their class-implied price and no
   higher**, with a published price history showing the upstream NOx sensor held down from €272.53 in 2023 to
   €261.11 today. **The constraint is that no competitive benchmark exists for any of these parts, so the case rests
   on class and role, not on a measured gap — and it must be presented that way.**
2. **Israel — service parts on the leasing double cab, inside a genuine-part-first window.** The modal new unit is
   a fleet or leasing double cab, and the Israeli policy requires new or genuine parts for the first two years.
   **UMI's measured distance is the highest of our four markets at 34,443 km a year** — a third more than Portugal —
   so the same part is bought most often here. A fleet buyer on a full-maintenance contract buys on total cost and
   uptime, not on the price of one filter. This is the best-evidenced place to take money on routine service parts.
   **[MEASURED]** on the mileage, the ownership mix and the policy clause.
3. **Ireland — the most defensible price position, on the smallest base.** The importer is vertically integrated:
   the Harris Group runs an ISO-accredited assembly plant, workshop facilities and a parts distribution centre, and
   the network grew to 25 locations on the back of a 41% registration surge in 2025. With the annual commercial
   test, a statutory maintenance duty and a distributor that controls both vehicle and aftersales, Ireland offers
   the most control of the four — but on a base of only **1,338 light commercial vehicles**, so the absolute euro is
   small. **Rank this third on size, first on defensibility.**

**Where a price rise costs more than it earns — ranked:**

1. **Israel — collision and lighting, and the pickup is more exposed than the truck.** This is the strongest
   negative finding, and it is the inverse of what a truck-led view would predict. The write-off threshold, the
   assessor who builds the estimate from our parts prices, and the policy's own allowance for a part of "similar
   description or characteristic" for lamps all apply to a vehicle **up to 3.5 tonnes** — which is the pickup. The
   installed base is **66.4% privately owned**, and privately owned older pickups are the ones most likely to have
   dropped comprehensive cover, which makes the buyer a cash-paying individual who can shop. **A lamp line that tips
   a modest pickup into a write-off loses the whole repair and every future part on that vehicle; the margin on the
   lamp is worth a fraction of that.**
2. **United Kingdom — the visible service basket, into a market that has just been taxed harder.** The pickup is
   exempt from operator licensing, so there is no compliance reason for the buyer to stay. Independent garages
   advertise warranty-preserving servicing at up to 50% less. The parts are on consumer sites with price histories.
   And the buyer was hit in April 2025 with the double-cab benefit-in-kind change, with the market down 0.7% in 2025
   and down 61.2% year on year in August 2026. **A rise on filters or brakes here moves the customer out rather than
   earning more from them.**
3. **Portugal — a tax-driven buyer who has already optimised once.** The buyer chose the three-seat homologation to
   save tax and is by construction cost-aware. The pickup is on the light N1 inspection cycle with no annual
   compliance pressure. It is the lowest-mileage of our four markets at **22,742 km**, so parts are bought least
   often, and the base is small at **4,733 vehicles**. Nothing here supports a premium on visible service parts.

### 10.8 What we still do not know

1. **No buyer-type split for pickups in any of the four markets.** Registration bodies publish light commercial
   totals and a private/business/leasing split at the light-commercial level, but not at pickup level. **Tradesman
   versus farmer versus fleet versus lifestyle is not published anywhere we looked. [NOT FOUND]**
2. **No pickup leasing penetration figure for any market.** Ireland gives 18.9% for light commercial vehicles as a
   whole; that is the closest available proxy and it is not pickup-specific. **[NOT FOUND]**
3. **No measured elasticity for pickup parts**, and no study of how much parts price moves repair retention. The
   same gap as the truck work. The 10% switching threshold is a threshold, not a slope. **[NOT FOUND]** for a
   coefficient.
4. **Portugal: no Portuguese-language primary source retrieved** on operator licensing for light commercial
   vehicles. Portugal-specific D-Max warranty terms were also not confirmed. **[NOT FOUND]**
5. **Portuguese sales figures for 2024 are internally inconsistent in the source** — one line reports +52.4% and
   another +52.8% for the same year. The 972 units and the 31.8% segment share are consistent across the article;
   the growth rate is not. **Treat the growth rate as unverified.**
6. **Whether the Israeli "up to 3.5 tonnes" total-loss clause is identical across all insurers.** The wordings we
   read agree on the caps, but each also permits the individual schedule to set its own rate up to those caps — so
   individual policies differ. **[MEASURED]** on the wording, unverified on the distribution across the market.
7. **No pickup-specific servicing-location data.** We know independent garages compete hard on D-Max servicing and
   we have the block-exemption rules, but we do not have the share of D-Max servicing that actually happens outside
   the dealer network in any of the four markets. **[NOT FOUND]**
8. **We cannot identify the towing customer in our own sales data.** §10.6.
9. **The UK unladen weight of 1,985 kg is a computation, not a weighbridge figure.**
10. **Whether any UK policy in practice requires genuine parts.** Vendors advertise genuine parts and a five-year
    repair warranty, but no regulatory requirement and no general insurer rule was found. **[NOT FOUND]**

### 10.9 Three things that contradict the brief as set

Stated plainly, because they change the shape of the work:

1. **The Operator's Licence does not bind the UK pickup customer** — twice over, on the 3,500 kg threshold and on
   the dual-purpose exemption. The only UK exposure is the towing combination, which is a different customer for the
   same vehicle.
2. **The Israeli collision mechanism applies to the pickup more cleanly than to the trucks.** The brief treated it
   as a truck finding resting on the threshold. In fact the thresholds were verified in the policy for vehicles up
   to 3.5 tonnes — the pickup's policy — while the above-3.5-tonne truck clause was never found.
3. **UTI does not carry the pickup. UMI does.** And in the UK, the pickup sits with IUK, not ITUK. The split must be
   respected in both cases. **Ireland is one distributor, not more.**
4. **Ireland is the market with the *most* compliance burden on the pickup, not the least.**
5. **The pickup aftermarket is retail-visible, and that is not a minor point.** The premium the genuine part can
   carry is constrained by something the customer can see without asking us.

---

## 11. The P700 and D-Max 2.2L launch: what the earlier premise got wrong

**This section is new in revision 3, and its first job is to correct an earlier claim in our own work.**

### 11.1 The headline, before the detail

**The premise that the launch book is the pricing wedge because the new part numbers "carry no old price for a
distributor to compare against" does not survive contact with the price files. On this list that is true for
roughly one part in thirteen.**

1,132 part numbers are flagged `NEED_SEED`, which means **no 12-month billing history**. **It does not mean no old
price.** Of those 1,132: **[MEASURED]**

- **1,072 (94.7%) already carry a base price and a current 2026 selling price** in the 2026 price file
- **1,048 (92.6%) carry a price in 2023 and 2024 and 2025 and 2026** — four consecutive published lists
- **all 41** parts in the SCR / AdBlue chain carry a 2023 price

Worked example, the upstream NOx sensor `8975074480`:

| List | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|
| Selling price € | 272.53 | 259.32 | 263.00 | 261.11 |

A distributor has been able to compare that line against four published prices. That is not a wedge; it is a normal
line with a stable history.

**The part of the earlier claim that does hold is the index argument:** these parts have no prior-period volume, so
they carry **zero weight** in the weighted calculation and the dial genuinely does not bind on them (§8.7). What
does not hold is the second half of the sentence — the commercial claim that there is no reference price. **The
wedge is the index weight, not the absence of an old price.** The two were bundled together in the earlier work and
they need separating, because the pricing latitude they imply is completely different. **[MEASURED]**

### 11.2 Classifying the 1,132 part numbers properly

The original labels for this list came from **text search on the description**, and the meta file for that list says
plainly they are description heuristics and not official categories. **They also do not survive a check: a text
search for "SCR" matches SCREW.** That is not a small error — it is the difference between a part family and the
fasteners that hold it on. Classification here uses the AIM catalogue identity tree, which is the approved grouping
axis. **[MEASURED]**

| | Part numbers |
|---|---:|
| New-only total | **1,132** |
| Matched in the AIM classification | 896 |
| **Not matched — no AIM row at all** | **236** |
| Have a real catalogue node | 819 |
| Sit in the named `Other / review` residual | 77 |
| **Commercial posture unclassified** | **236** |

**The 236 unmatched are the honest limit.** They are not a family and are reported as a residual. Because posture
hangs off identity, they are 236 in posture too — **20.9% of the list.** The 77 `Other / review` rows are a separate,
smaller problem: they have an AIM row but the classifier could not place them either. They include accessory items.

**Commercial posture across the 1,132:**

| Posture | Part numbers | Share |
|---|---:|---:|
| Captive — price to margin | 408 | 36.0% |
| Body / hardware — follow the panel logic | 396 | 35.0% |
| Wear / service — price below class to build the habit | 92 | 8.1% |
| **Unclassified** | **236** | **20.9%** |

**[MEASURED]**

**And the shape matters more than the total.** The largest blocks on this list are **body panels, hardware and
interior trim — not the SCR system.** Across the whole list the euro is a **price-book total** (the sum of current
2026 list prices on the parts where a price exists, €88,986), not revenue and not a gap: these parts have no fleet
denominator because there is no billed history to divide by. The genuinely new technology is a small tail on a list
that is mostly ordinary truck furniture. **[MEASURED]**

**One commercial fact that matters and is easy to miss: 922 of the 1,071 classed parts sit in class C**, which is a
53% margin, and **only 2 of the 1,132 parts are in class P**, our most aggressive class. That is the finding the
rest of this section develops. **[MEASURED]**

### 11.3 What price the SCR and AdBlue families can carry

Using the AIM family rather than a keyword, the SCR / AdBlue chain is **41 part numbers** in the P700-only new set:

| | Parts |
|---|---:|
| Total in the chain | 41 |
| Low-value fixing and plumbing (bracket, screw, bolt, clip, hose, cover, retainer) | 28 |
| **Functional parts — sensors, pumps, control units, catalyst, DPD assembly** | **13** |
| With a base price | 41 |
| **With an aftermarket equivalent** | **0** |

**[MEASURED]** — checked against five comparator files

**The 28 brackets and screws are not a pricing opportunity.** The case turns on the 13 functional parts. Against the
class-implied price:

| Scenario | Wear | Captive | Body | SCR functional total € | Versus class-implied |
|---|---|---:|---:|---:|---:|
| `class_only` — class as issued | 1.00 | 1.00 | 1.00 | 7,433.53 | — |
| `habit` | 0.85 | 1.00 | 0.95 | 7,429.66 | −0.1% |
| `split` — habit on wear, harvest on captive | 0.85 | 1.25 | 1.00 | 9,291.92 | +25.0% |
| `warranty_load` — at the policy ceiling | 0.85 | 1.35 | 1.00 | 10,035.27 | **+35.0%** |

**The last line is the point. The class-implied price is the current 2026 listed price — within 0.45%, and slightly
below it.** The pricing rule that captive parts may be priced to margin and above class-implied **has not been
applied to a single one of these 13 parts. There is no premium in the launch book today.**

**These are sums of unit prices, not a revenue forecast.** They carry no volume and no fleet denominator, so under
the house rule on quantifying gaps they must not be presented as a value at stake. What they do show is the headroom
on the price book: the policy ceiling is +35%, and the current list sits at +0%.

**The evidence for the case, separated honestly:**

*Measured:*
- These 13 parts have **no aftermarket equivalent in any comparator on disk** — checked against Eucon, the
  competitor panel, KS International and Mekonomen.
- Their current list price equals their class-implied price. There is no embedded premium today.
- Their base prices carry a published 2023–2026 price history. The old price for the upstream NOx sensor was
  €272.53 in 2023 against €261.11 today — **the line has been held down, not raised.**
- The precedent: the DPF sensor `8978808270` realises **69.3% gross margin** against the 56% implied by its class.
  Aftertreatment content is already earning above its class elsewhere in the business.

*Assumed — do not present as measurement:*
- The `warranty_load` and `split` results are driven by behavioural parameters that are all marked as assumptions:
  the aftermarket entry year by role, the price-to-entry sensitivity, the erosion floor and decay rate, and a
  three-year warranty term. The model's own note says it "has no observed elasticity behind it and must not be
  presented as if it does. Its value is in ranking tactics against each other, not in forecasting a number."
- **Every scenario total above inherits those assumptions.**

**So: on the price book, the SCR families can carry +25% to +35% over the class-implied price, which is +25% to +35%
over where they are listed today. The binding constraint is the policy ceiling, not the competitive position,
because there is no competitive benchmark on any of them. The evidence that they are under-priced is the 69.3%
precedent. The evidence that they should sit at the ceiling is an assumption, not a measurement.**
**[MEASURED]** on the prices; the case for the level is judgment.

### 11.4 The dependency that should stop a number being committed

Every price in §11.3 is derived from **the base price in the price file**. **If IML's base price already contains a
premium or a margin load over a pure transfer cost, then the class-implied price is already above a neutral
reference, and the +25% to +35% headroom is measured from a base that is not itself neutral.** In that case the true
headroom could be materially smaller. **We cannot tell from the files we read whether that premium exists, and this
is a genuine dependency: a launch number should not be committed until that question reports.** **[NOT FOUND]**

### 11.5 The urea filter, and the interval nobody measures

The recurring part is `FILTER KIT; PUMP ASM,DEF DCM SPLY`, part number **8983507160**, and it is **carryover, not
new** — it has billing history: €32,529.41 billed in the last twelve months, class C (53% margin), base price 8,752
JPY, class-implied €70.21 against a **current 2026 list of €70.53.** Same finding as the SCR parts: priced at class,
no premium. Two of its siblings (`8981694030`, `8983507161`) sit at the identical €70.53, which is what you would
expect of a carried-over line. **[MEASURED]**

**The service interval is the gap.** The on-disk schedules disagree, and the D-Max schedule is silent:

| Source | Vehicle | AdBlue filter interval |
|---|---|---|
| D-Max 2.2L (RG21 / RZ4F-TC) schedule | D-Max 2.2L | **No AdBlue or urea row exists in the document** |
| N-series maintenance schedule, MY24 | NPR75 4HK1 (the P700-era N series) | **200,000 km** or 124,000 miles |
| N-series schedule, MY24 | NLR88 / NMR88 / NPR88 4JZ1 | No AdBlue filter row |
| F-series schedule, MY24 | F-series 4HK1-TCH | **80,000 km** or 50,000 miles |

So the launch part carries a **200,000 km** published interval from the P700-era N-series schedule. **The D-Max
schedule does not state one — which is a gap**, because the urea filter becoming a standard service item on the new
generation is an earlier claim in our own work and it is not documented in the schedule for that vehicle.
**[MEASURED]** for the schedules; **[NOT FOUND]** for a D-Max interval

**And nothing on disk measures how often a urea filter is actually changed.** What exists is a capture denominator,
and it must not be used as an interval: **[MEASURED]**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Filter units billed, network | 1,393 | 1,540 | 1,988 |
| Vehicles in service | 163,199 | 163,199 | 163,199 |
| **Billed per vehicle per year** | **0.0085** | **0.0094** | **0.0122** |
| Assumed expected units per vehicle | 0.809 | 0.809 | 0.809 |

At a 200,000 km interval and a 20,000 km per year assumption, the correct rate would be **0.10 per vehicle per
year**. The model assumes 0.809 — eight times too high, and it is a per-vehicle constant rather than an observation.
The measured paid rate of 0.0085 to 0.0122 against the 200,000 km interval implies roughly **1.6 to 2.4 million km
per vehicle**, longer than any vehicle will run — because it measures **how little of the available paid demand we
capture**, most of it sitting inside the warranty window. **Both numbers are wrong for the interval question, in
opposite directions.** UTI billed **82 units in 2025 against 10,336 vehicles in service** — 0.0079 per vehicle,
consistent with the network and equally unusable as a frequency. **[MEASURED]**

### 11.6 Israel as a benchmark, restated to the selling basis we use

Earlier work said Israel prices on its own export list, "presently around 10% below" the standard list and
class-dependent. **Measured against the current lists, the gap is about 14%, not 10%, and it is tight.**
**[MEASURED]** — UTI's export file joined to the standard list on **134,896 matched part numbers**, both sides
non-zero

| Statistic | Export list versus standard list |
|---|---:|
| **Median** | **−13.95%** |
| 25th percentile | −13.96% |
| 75th percentile | −12.63% |

The interquartile range is 1.3 points, which means it really is applied as a flat discount roughly as described,
just deeper than our records show. **To restate an Israeli price to the standard basis: divide by (1 − 0.1395), i.e.
multiply by 1.1621.** Our configuration carries a **1.10** uplift for the P700 model, which **understates the
uplift by about 5.6%**: any P700 Israel price read across with the config's 10% will land roughly 5.6% too low.
**[MEASURED]**

**This is a configuration value and it was not changed.** It is a recording of a measured correction, so the change
can be made deliberately.

**What the restatement changes is the price level, and it does not change the limitation.** UTI billed 82 urea
filter units in 2025 against 10,336 vehicles in service, and UTI's observed price is 14% below the standard list, so
**every demand rate read from the Israeli data is attached to a price that is not ours.** Two things follow, and
they point the same way: do not read a launch price across from Israel without the restatement; and **even restated,
the Israeli price tells you nothing useful about the paid channel**, because 15 months of a three-year warranty
means the observations are of the warranty channel. Both the pricing reference and the demand rate are the wrong
vintage for the decision. **[INFERENCE]**

### 11.7 What the launch work could not verify

1. **Whether IML's base price embeds a premium.** Bears directly on §11.3. **Do not commit to a launch number until
   that investigation reports.**
2. **No fleet or volume denominator** for P700 or D-Max 2.2L. Nothing derived from this work can be expressed per
   vehicle in service, which the house rule on gaps requires before a figure is presented as a finding. **This is
   the single input that would move the work furthest, and it is a Jerome or IML question, not a data-mining one.**
3. **The 800 → 1,000 ramp market.** Cannot be established from the files; the recommended list mixes two networks'
   sources (1,109 of 1,885 part numbers are on ITUK's list as well).
4. **The preferred price basis** — accessory/EXW or the standard list. The data supports both; the choice is
   commercial.
5. **The P700 model and gearbox mix is a production plan, not registrations.** IML's plan of May 2026, **2,585
   units**: 3.5t 1,405 (54.4%), 7.5t 979 (37.9%), 13.5t 135 (5.2%), 11.0t 37 (1.4%); and by transmission **MT 1,215
   (47.0%), AMT 1,029 (39.8%), AT 341 (13.2%)**. It should be confirmed as current before it weights anything.
   **[MEASURED]** as a plan, not as registrations
6. **The D-Max urea filter interval.** §11.5.
7. **No P700 part-level demand evidence from Israel was reachable.**
8. **Competitor evidence is effectively absent for the whole launch book** — **1 part in 1,132**. Under the spec's
   own tiering that means the whole launch book has no benchmark, and therefore **no permitted positional move**.
   This is not a gap that can be closed by working harder; it needs a model-keyed scrape or a distributor quotation.

---

## 12. Remanufacturing and refurbishment: the third price level

**This section is new in revision 3.** It answers a question the earlier paper did not ask: what competes with our
part when the customer does not have to buy a new one.

### 12.1 The one thing to read first

**"DPD" is DPF, and our own catalogue already calls it DPD.** The part numbers in the warranty claims are described
in our 2026 price list as **`DPD ASM`**, and the operation text in the claim file reads **"DIESEL PARTICULATE
DEFUSER FILTER - R&R"**. The same part is called DPF in the industry, DPD in our catalogue, and "particulate
defuser" in the claim file. **There is no separate DPD product distinct from the DPF.** **[MEASURED]** —
`pricing_list_pn.parquet` and `01_data/06_Warranty/*.xlsx`

**And the headline mechanism is regulatory, and it is the opposite of what one would expect.** Israel is not a
marginal refurbishment market — it is a regulated one, and **the regulation protects refurbishment and only
refurbishment.** The Israeli Air Quality Regulations make it a criminal offence to remove a particulate filter
**unless "the removal is intended for cleaning, repair or replacement of the filter or for scrapping the vehicle."**
**[REPORTED — NOT VERIFIED]** — Air Quality (Vehicle Air Pollution) Regulations amendment 7986, regulation 8, with a
penalty of six months' imprisonment or a fine; carried from the research paper of 19 September 2026

**In the UK, Ireland, Portugal and Spain the legal pressure runs the other way: the filter must be *present* and
*untampered*, and any replacement on a Euro 5 or later vehicle must be type-approved. A cleaned original is the
only legal path in all four markets.** That asymmetry, not a quality difference, is what makes the Israeli market
different. **[INFERENCE]** on the comparison; **[MEASURED]** on each market's rule as recorded in §12.3.

### 12.2 How hard is the competition, per market

**The short answer: hard, per market, in this order — Israel hardest, then Portugal, then Ireland, then the UK
truck channel — and the D-Max particulate filter is the most exposed single part in the whole portfolio.**

| Market | Clean / refurbish | New genuine equivalent | Ratio, clean ÷ new | Grade |
|---|---|---|---|---|
| **UK — car / van (D-Max class)** | £150–£500 professional clean; £250–£450 typical off-car | £1,000–£3,500 genuine | **~0.10–0.30** | [TRADE] |
| **UK — truck class** | £180 + VAT standard off-car cleaning; £250–£600 off-car refurbishment | HGV DPF £2,500–£6,000+ | **~0.03–0.10** | [TRADE] |
| **UK — truck, reconditioned exchange unit** | £565.44 + £500 exchange surcharge = £1,065.44; Dinex Volvo £1,017.56 incl. £517.50 refundable; Dinex DAF £1,826.90 incl. £840 refundable | New original-equipment truck DPF several thousand £ | **~0.20–0.40**, and the surcharge is refundable so the net is the lower figure | [MEASURED] — published supplier catalogues |
| **Israel — car / van** | ₪500–1,500 forced regeneration; ₪1,500–3,000 professional off-car clean. In euro at about ₪3.9/€: **€128–€385** regeneration, **€385–€770** full clean | ₪5,000–15,000 | **~0.10–0.20** | [TRADE] |
| **Israel — truck** | No published truck price list found | not published | **not established** | [NOT FOUND] |
| **Portugal / Ireland** | No published market-specific cleaning price table found for either market | — | **not established** | [NOT FOUND] |

Two cautions on these ratios. First, the cleaning price is **not** the whole cost — removal and refitting are billed
separately by the garage, so the true fitted comparison is a few hundred pounds higher than the cleaning charge
alone. Second, **the low ratio is the point: at 3–30% of the price of the part it competes with, a cleaned filter is
not a marginal alternative, it is the default rational choice for any operator who is not forced to buy new.**

**What a cleaned filter is worth afterwards — the number that decides the economics. [MEASURED]** — a professional
off-car hydrodynamic wash removes 90–98% of build-up, and after a wash where the only problem was natural ash
accumulation the filter lasts **another 80,000–150,000 km**. Academic work finds cleaning removes up to **92% of
filter weight** but only **65% of the pressure drop** across the filter, and notes that back-pressure "does not
provide a complete quantification for off-board cleaning effectiveness, as back pressure may be decreased while
DPFs may still retain significant levels of ash."

**Read together: the technology genuinely works, and it is genuinely measured. The reason it wins is not that it is
a con. It restores most of the function at a tenth of the price, and the supplier carries a year of risk while our
part carries a three-year warranty.** A 12-month warranty is the norm on off-car cleaning; six months is common on
cheaper operations; there is no warranty on on-car cleaning.

### 12.3 The regulatory position, market by market

| Market | Is a cleaned / non-genuine filter legal? | What the test checks | Grade |
|---|---|---|---|
| **UK — cars & light commercial** | Cleaning and refitting the original: **yes** — the MOT manual says a cut-and-rewelded filter should be accepted *when the presenter can show a valid reason such as filter cleaning*. Non-type-approved replacement DPFs are **illegal to supply** for Euro 5+ vehicles, punishable by a fine up to **£5,000**. Missing or obviously modified DPF = **a major defect**. | Visual presence and tamper check, plus the metered smoke test. **No particle-number test yet** — the agency is piloting one. | **[MEASURED]** — DVSA and legislation |
| **UK — truck** | Same principle: emission-control equipment absent, obviously defective or showing signs of tampering = **major**. Removal breaches construction-and-use rules. | **Opacity only.** The agency is **piloting particulate-number testing explicitly "to identify removed or damaged DPFs"**. | **[MEASURED]** |
| **Ireland** | Removing a DPF is an offence under the Road Traffic (Construction, Equipment and Use) Regulations. The authority states this plainly. | **The test is a visual inspection and does not dismantle.** Visible removal or bypass is treated as a defect and, per 2026 guidance, as a **dangerous** defect. Removal also creates an insurance non-disclosure exposure. | **[MEASURED]** for the rule; **[TRADE]** for the guidance commentary |
| **Portugal** | Removing or software-deleting the DPF is illegal and fails the test automatically; it also invalidates the certificate of conformity. Fines €250–€1,250 plus possible seizure. | **Opacity only today.** Portugal is **regulating the introduction of particle-number measurement** in test centres, with a **250,000 particles/cm³** threshold, applicable to Euro 5b and above; the motoring authority says it is "in a phase of implementation" with no official date yet. | **[MEASURED]** — via the Portuguese motoring press |
| **Israel** | **The opposite of the other four.** A criminal offence to remove a filter fitted at manufacture or required by regulation — *unless the removal is for cleaning, repair or replacement of the filter, or scrapping*. Operating a heavy diesel without its required filter is separately prohibited. | Annual licensing test requires **opacity ≤ 0.2 m⁻¹** for filter-equipped vehicles; failure can **prevent licence renewal**. The environment ministry has stated its intention to add a **particle-number measurement at idle to detect removed or damaged filters**. | **[REPORTED — NOT VERIFIED]** — carried from the research paper |

**The asymmetry in one sentence:** in the UK, Ireland, Portugal and Spain a filter must be *there* and *untampered*,
so cleaning your own unit is the only legal economy and buying a cheap non-approved replacement is a crime. In
**Israel the law names cleaning, repair and replacement as the permitted reasons for removal** — which is precisely
a statutory licence for the refurbishment trade that market already has. **[INFERENCE]**

**Who actually does it.** In Israel there is a real, named, specialised industry — at least five firms, one of them
describing itself as a licensed parts importer and supplier approved by the Ministry of Transport, serving garages
across the country, **insurance companies, leasing and rental companies and vehicle importers**, with field
diagnosis and warranty on its products. In the UK, specialist off-car cleaners operate as a trade service for
garages and fleets, not consumer-facing retail. In Ireland one operator is documented. In Portugal the evidence is
thinner. **[MEASURED]** — company sites and an Israeli ministry tender document

### 12.4 What our own warranty book says about the filter

**Verified: Israel refurbs. But the interesting result is not that. It is that Israel's filter claim profile is
completely different in shape from everywhere else, and one clean explanation fits all of it. [MEASURED]**

| Market | Truck filter lines | Filter parts cost | Median odometer at claim | Median age | Cost per claiming vehicle |
|---|---:|---:|---:|---:|---:|
| **ISRAEL (UTI)** | **436** | **€696,907** | **129,200 km** | 3.1 yr | **€1,696** |
| UK (ITUK) | 119 | €116,272 | 103,912 km | 3.3 yr | €985 |
| Spain | 62 | €57,007 | 135,429 km | 3.8 yr | €950 |
| Italy | 46 | €50,604 | 108,429 km | 5.4 yr | €1,100 |
| France | 14 | €13,690 | 71,242 km | 4.5 yr | €978 |
| **PORTUGAL** | **24** | **€12,182** | **66,588 km** | 2.7 yr | **€530** |

Israel is **37.0% of the entire truck parts claim book by value** on **10.2% of its claim lines** — because the
average Israeli truck claim is €508 of parts against €134 in the UK. And **40.4% of Israel's truck parts claim cost
is the filter alone** (€696,907 of €1,723,492). Truck-wide, the filter is 7.2% of claim lines but **20.8% of claim
cost** (€965,904 of €4,655,881).

**The decisive split: Israel's filter liability is mostly *outside* warranty.**

| Market | Inside 3 yr / 100,000 km | Over distance limit | Over age limit | **Share outside the stated limits** |
|---|---:|---:|---:|---:|
| **ISRAEL** | €168,934 | **€455,633** (273 lines) | €72,340 | **76%** |
| **UK** | €28,075 | €64,099 | €24,098 | **76%** |
| Portugal | €6,656 | €3,805 | €8,329 | 65% |
| Whole truck book, all markets | €236,230 | €600,232 | €129,442 | **76%** |

**[MEASURED]** — recomputed from the warranty files. Of 719 truck filter lines, **434 are over 100,000 km and 127
are over 200,000 km.** In Israel specifically the "filter remove and refit" line has a **median odometer of
167,807 km** on the over-distance group.

**This is the answer to the question "why so much in warranty", and it is not the one either party assumed. Israel
is not running an unusual *failure* rate. Israel is running an unusual *age and mileage* of truck, and the filter is
what fails at high mileage. 76% of the filter cost we are absorbing is on vehicles that our own stated terms place
outside the 3-year / 100,000 km warranty.** **[MEASURED]**

**And Israel's own refurbishment shows up inside our warranty claim file.** This is measured, not inferred:

> **"DIESEL PARTICULATE DEFUSER - RECONDITION AND/" — 6 lines, €5,689, median odometer 79,087 km, one market
> (Israel), zero other markets.**

Across the entire 33,416-line truck claim book the only recondition-type operations that appear at all are 41 lines
totalling €20,631 — Israel 18 lines (6 of them filter reconditioning), Italy 3, Portugal 10, UK 7, France 4 — and
they are almost all transmission or carrier work, not filters. **[MEASURED]**

**So we have direct evidence that an Israeli distributor reconditions filters and claims it under warranty, and no
evidence of anybody else doing it anywhere in our book.**

### 12.5 The counter-finding that matters more than any ranking

**We pay substantially more for these parts under warranty than our own catalogue list price. [MEASURED]** — claim
cost per unit from the warranty files divided by the list price from the price list

| Book | Part | Description | Our 2026 list | Claim cost per unit | Claim ÷ list |
|---|---|---|---:|---:|---:|
| UMI (light commercial) | 8975359391 | DPD assembly | €2,162 | €3,777 | **1.75** |
| UMI (light commercial) | 8981776324 | DPD assembly | €1,282 | €2,278 | **1.78** |
| UMI (light commercial) | 8978808250 | PM sensor | €242 | €413 | **1.71** |
| IUK (light commercial) | 8975359391 | DPD assembly | €2,162 | €2,615 | **1.21** |
| ITUK (truck) | 8982878080 | Filter assembly | €1,130 | €1,473 | **1.30** |
| **UTI (truck)** | **8982878080** | **Filter assembly** | **€1,130** | **€1,874** | **1.66** |
| UTI (truck) | 8982049420 | Filter assembly | €1,152 | €1,904 | 1.65 |
| UTI (truck) | 8983528481 | NOx sensor | €258 | €431 | 1.67 |
| UTI (truck) | 8983300950 | PM sensor | €387 | €662 | 1.71 |

Every book pays above list; the pattern is consistent across parts and markets, which points to a systematic
structure rather than a data artefact. **We have not established the mechanism, and we are flagging it rather than
explaining it.** **[NOT FOUND]**

**Why this matters commercially: the filter is a class D part — our own price architecture assigns it the *lowest*
margin band, 48%, because a high-value part is where a distributor's margin is most exposed to an undercut. So the
part where we earn our thinnest percentage is also the part where we are paying out between 1.2× and 1.8× our own
list, on the largest single warranty line, in the market with the densest refurbishment trade.** **[MEASURED]** for
each figure; **[INFERENCE]** for the juxtaposition

**And one counter-veiling point that matters most of all: we already run two different answers, and one of them is
the market differentiator. [MEASURED]**

- **North America — remanufactured.** Isuzu's own published material describes filters "reconditioned to meet the
  same specifications and quality of a new DPF", inspected, thermally checked, **flow tested and benchmarked**,
  media blasted, with a **12-month / unlimited-mile warranty**. Its parts catalogue lists **the very part number
  that is our largest Israeli warranty line** as "remanufactured", with no core charge.
- **UK — brand new, "new in lieu".** Isuzu Truck UK announced on 14 December 2017 that it would supply **brand new**
  units for its most common filters at prices comparable to remanufactured ones, on a new-in-lieu basis with the
  failed unit returned. Its stated reasons are a direct argument *against* cleaning: no vehicle downtime while
  waiting for cleaning, and it "**removes the uncertainty of the success of cleaning, or future longevity**".

**The UK answer — beat the clean with a new part priced like a remanufactured one — is a strategic play that already
exists inside our own manufacturer, argued in our own words, with the cleaning-and-longevity argument ready-made.
It is not on our radar for Israel, and it should be the first question asked: why does Israel get the reman answer
and not the new-in-lieu answer?** **[INFERENCE]**

### 12.6 Where refurbishment can and cannot take money

**Where it is taking money:**

1. **Israel trucks, over 100,000 km.** 273 Israel filter lines, €455,633, median odometer 167,807 km — entirely
   outside our stated terms and entirely inside the window where a cleaned filter is a rational purchase. Every one
   of these is a genuine part we did not sell to a dealer and a refurbisher did. **[MEASURED]**
2. **The D-Max filter, everywhere.** UMI's two DPD assemblies are **€1.10m** of warranty cost; IUK has nine of them
   at a unit cost of €2,615 against a €2,162 list. **The D-Max filter is class D, a 48% margin — the lowest margin
   band we have — on a part with a live independent rebuilder market in Israel. That is the most exposed single part
   in the portfolio, and it is not close.** **[MEASURED]** for each figure; **[INFERENCE]** for the ranking

**Where it cannot:**

1. **Anything inside warranty.** No substitute exists in the warranty channel by rule. That is why we see so much
   filter volume there and so little anywhere else. **[INFERENCE]**
2. **Anywhere particle-number testing is switched on.** Israel already requires opacity at licence renewal and has
   stated its intent to add a particle-number measurement at idle; Portugal is regulating a particles/cm³ test; the
   UK is piloting particle-number testing for both light and heavy vehicles explicitly to detect removed or damaged
   filters. **A particle-number test measures function, not presence — it is the one test a badly cleaned or emptied
   filter cannot pass. This is the single largest structural protection available to the genuine part, and it is
   coming in three of the four markets.** **[MEASURED]** for the programmes, **[INFERENCE]** for the consequence
3. **The UK replacement market.** Only a type-approved unit may be supplied for Euro 5 or later vehicles, it must be
   permanently marked, and supplying a non-approved one is punishable by a fine up to £5,000. **Reconditioned units
   from established suppliers are type-approved and priced against us, so we are competing with a *compliant* rival
   there rather than with a grey one.** **[MEASURED]**

### 12.7 What this means for pricing, stated as margins

- **The filter assemblies sit in class D, a 48% margin, deliberately, because high-value parts are where margin is
  most exposed. That logic is correct, and in the UK it is working — the UK multiple over list is the lowest in the
  book.**
- **In Israel the same logic is not working:** the same parts come back at **1.65–1.71× list**, on a 48% margin, in
  the market with the densest refurbishment trade. **Either the price is being set below the level at which the
  market clears, or the claim valuation is carrying costs the list does not. Those are very different problems and
  the files on disk do not separate them. [NOT FOUND]**
- **The strongest pricing lever is not to cut the part.** It is the one already modelled elsewhere in the workspace:
  **hold the aftertreatment price flat once each vehicle's own warranty ends**, so that the paid channel is not
  competing with a refurbisher on a part we have just priced at a thin margin. **That is a timing decision about
  when our price stops being a claim price, not a discount.** **[INFERENCE]**
- **And we are the only party in this story without a core loop.** A refurbisher's raw material is our customer's
  used filter, and today we take it back for nothing under a warranty claim and give nothing back for it. The entire
  33,416-line truck claim book contains **24 core lines totalling €3,646** and every one is an evaporator, heater or
  fuel-cooler core — zero surcharges, zero exchange lines, zero reman. Meanwhile a European supplier runs a full
  reconditioned exchange programme with all Euro VI units available as reconditioned and core refunds on return.
  **[MEASURED]**

### 12.8 Two market details worth carrying

**Portugal looks like the opposite of Israel, on the same part.** 24 filter lines, €12,182, median odometer
66,588 km, median age 2.7 years, €530 per claiming vehicle — the lowest cost per vehicle of any market in the book.
**This is a market with the newest trucks, the fewest filter claims, and — per §12.3 — a regulator actively
regulating a particle-number test. If the particle-number test lands there first, Portugal is the natural place to
watch whether genuine filter volume moves.** **[MEASURED]** for the figures; **[INFERENCE]** for the read

**Ireland is nearly invisible, for a reason worth knowing.** **Zero truck filter lines.** Ireland's whole truck
book is **48 lines, €18,789**. What Ireland does claim is sensors. **That is not a market with no filter problem.
It is a market where either the fleet is small and young, or the work is happening outside our claim book. We cannot
tell which, and it should not be read as "no exposure". [NOT FOUND]**

### 12.9 What this work could not establish

1. **Israel's truck-tier refurbishment price.** No published Israeli price for truck or commercial filter
   cleaning, so the Israel truck ratio is **[NOT FOUND]**. Passenger-car prices are not a proxy for a truck unit.
2. **The paid filter channel by volume.** The only paid file usable for this is a modelled comparison value,
   present/absent only. There is no sales-to-dealer series we could put a share on, **so we cannot quantify how much
   refurbishment is taking.**
3. **The warranty versus paid split on the filter specifically.** Not derivable from the files on disk.
4. **The mechanism behind the 1.2–1.8× claim-over-list multiple.** Consistent across parts and markets; could not be
   attributed to currency, claim valuation basis, or list-versus-transfer pricing. **This is the number that most
   needs a second opinion, because it changes whether the Israeli filter price is wrong or the claim valuation is.**
5. **Whether the PM-sensor campaign caused any filter assembly claims.** 941 PM-sensor claim lines at €253,024 in
   the light commercial book against 43 filter lines at €50,376 is the kind of ratio that means either the sensors
   fail far more often than the filters, or the two are the same job billed twice. **One of those is a price
   question; the other is a quality question.**
6. **The filter warranty term in each of the four markets**, and what share of claims fall just inside it. The
   3-year / 100,000 km used here is the workspace's stated constant, not a measured market term.
7. **Whether there is any technical bulletin, campaign or recall on the filter.** We searched the warranty folder
   and the documentation. **We did not find one, and we cannot rule one out** — the search covered the files in this
   workspace, not Isuzu's systems.
8. **Israeli dealer claim concentration and failure coding.** One dealer carries 100% of Israel's claim lines and
   425 of Israel's 436 filter lines carry a single failure code. **That is a recording convention we could not
   verify, and it limits how confidently the Israeli pattern can be read as a fleet pattern.**
9. **Ireland's and Portugal's filter cleaning prices and provider base.** Both searched; neither returned a usable
   published price.
10. **Unit quantities on truck filter lines beyond the first quantity field.** That field reads 1 on 695 of 719
    lines — plausible for a filter assembly, but it was not cross-checked against a second quantity field before
    unit prices were quoted from it.

---

---

## 13. Brakes, end to end

Because brakes are the most-evidenced family and the one the request names, they should be the pilot. Everything
below is measured except where marked.

**The family.** 1,267 lines, **334 part numbers**, **€3,142,066** billed on the revision base, **€215,508** of
step, and a **weighted base-price move of 7.36%** — well above the network's 5.96%. **Brakes are being repriced
harder than the book, without anyone having decided that.** **[MEASURED]**

**Inside it:**

| Level 2 | Part numbers | Billed € | Share of family | Step € |
|---|---:|---:|---:|---:|
| Discs & Drums | 99 | 1,736,892 | 55.3% | 88,542 |
| Pads & Shoes | 164 | 1,177,861 | 37.5% | 113,822 |
| Caliper | 53 | 205,388 | 6.5% | 12,506 |
| ABS control, repair kits, booster, hydraulic | 18 | 21,925 | 0.7% | 638 |

**Pads & Shoes carries 37.5% of the money but 52.8% of the step.** Pads and shoes are being repriced nearly one and
a half times as hard as discs and drums. **[MEASURED]**

**Concentration — and this is the actionable part:**

| Concentration | Share of family billed euro |
|---|---:|
| Largest single part number | **22.4%** |
| Top 5 | 48.3% |
| **Top 10** | **61.0%** |
| Top 20 | 76.2% |

**Twenty part numbers carry three quarters of the family.** A pricing decision on brakes is a decision about twenty
part numbers, not 334. That is a manageable conversation, and it is the single strongest argument for family-by-family
work over a catalogue-wide run. **[MEASURED]**

**The head of the list:**

| Part number | Description | Billed € | Qty | Step € | Base move |
|---|---|---:|---:|---:|---:|
| `8983767550` | ROTOR; DISC BRK,FRT | 703,041 | 9,147 | 39,058 | +7.0% |
| `8982447940` | PAD KIT; CALIPER,DISC BRK,FRT | 342,394 | 4,168 | **81,934** | **+24.9%** |
| `8975056801` | PAD KIT; CALIPER,DISC BRK,FRT | 233,750 | 3,027 | 6,731 | +3.0% |
| `8978279610` | PAD KIT; DISC BRK,W/O SHIM & CLIP | 145,942 | 2,146 | 3,972 | +3.0% |
| `8981919560` | ROTOR; DISC BRK,RR | 92,275 | 661 | 5,685 | +7.0% |

The second row is the distributor complaint in one line. **A €342k pad kit with a +24.9% base move, and it is the
largest single step in the family.** **[MEASURED]**

**Evidence coverage, which is why brakes is the pilot:**

| Source | Part numbers | Billed € | Share of family |
|---|---:|---:|---:|
| Same-shop listings | 51 | 992,031 | 31.6% |
| Eucon benchmark | 178 | 1,583,069 | 50.4% |
| **Any competitor reference** | **311** | **2,596,458** | **82.6%** |
| No reference at all | 23 | 545,608 | 17.4% |

**82.6% of the brakes family's billed euro has a competitor reference**, against 16.5% of the book's billed euro.
That is the difference between a pilot that can produce a priced answer and one that cannot. **[MEASURED]**

### 13.1 Four live front pad kits, one function, a 25% spread

**Four live front pad kits, one description, four prices, and nearly disjoint distributor bases. [MEASURED]**

| Part number | Base price JPY | List € | Who buys it |
|---|---:|---:|---|
| `8975056801` | 12,120 | **82.25** | IUK €74,025 · ISD €37,836 · Sverige €33,118 · IBX €27,069 · Norway €11,988 · RSA €10,710 · AutoWallis €8,062 · UMI €7,826 · 9 more |
| `8975546610` | 12,120 | **82.25** | Norway €55,932 · IBX €9,367 · Ireland €7,381 · ISD €5,704 · 5 more |
| `8982169210` | 14,906 | **102.65** | ITUK €74,146 · Imotors €2,473 · Ireland €1,655 |
| `8982447940` | 12,940 | **89.11** | **ITUK €228,730 · UTI €65,234** · Imotors €20,103 · Ireland €18,912 · 6 more |

**The same function is supplied under four part numbers at prices spanning €82.25 to €102.65 — a 25% spread — and
each network is effectively locked to its own.** IUK buys only the cheapest and Norway mostly the second; ITUK and
UTI buy only the two most expensive. **The part carrying the +24.9% at €89.11 is the one ITUK and UTI are locked
into, and it is the largest single step in the family.**

All four point to themselves as their newest part number, none is marked superseded, and each carries its own base
price — **so this is not a supersession chain.** We cannot confirm from the price file whether the four are
**interchangeable**: different part numbers for one function usually mean different model applications, different
gross vehicle weight or a different brake system, and the description is identical for all four so it does not
settle it. **That is exactly what the manufacturer's electronic parts catalogue would answer, and it is the first
question in the pilot rather than a footnote. [NOT FOUND]**

**And this is the connection to §8.6 and §9.** The part number carrying the +24.9% is the same number that is 97%
of UTI's brake pad family and the same number on the fascia of the Israeli collision deck. Three separate strands of
this revision meet on `8982447940`.

### 13.2 What the pilot would produce — four questions, not one

1. **On the 12 parts where cost is above the competing retail price** — a sourcing list, not a pricing list. What
   does it actually cost us to make or buy that part, and can it move?
2. **On the parts reachable at 20% margin or better** — a price position, with the dealer price shown alongside our
   own.
3. **On the €545,608 with no reference** — hold the line, and name the gap.
4. **On `8982447940`, the +24.9%** — the first job is identity, not pricing. Are the four kits interchangeable?

### 13.3 The strongest argument for wanting a frozen price

**The parts where we sit furthest above the independent price are the parts where the case for raising is weakest,
and they are also the parts on repair estimates that decide whether a collision repair happens at all.** §9 gives
the mechanism, §13.1 gives the part number, and §15 gives the movement. That is the whole reason the pilot is worth
running before a catalogue-wide rate is set: **on this family the price question and the volume question meet on
about twenty part numbers, and they can be settled by looking at twenty part numbers.**

---

## 14. How other operators do it

*From `01_data/90_INBOX/_ANON_OEM_IAM_PRICING_REVIEW_20260917.md` — a full review, 795 lines, with an internal
source list so every figure can be verified. In that review every figure carries a grade. **Nothing in this section
is [MEASURED] unless it says so**, and several of the numbers most often repeated in this field are consultancy
models or survey figures without a disclosed sample.*

### 14.1 What the review establishes

**Cost-plus by class is what nearly every manufacturer actually does**, and the class *is* the pricing decision. A
widely used practitioner description is that the markup follows cost inversely — low-cost manufactured parts get
the highest margins, high-cost bought-in goods the lowest. A European study of plant and machinery manufacturers
found an average markup implying about **60% margin**, ranging from about **63% on manufactured parts to 50% on
purchased parts** — and, the diagnosis, **the same margin was applied to parts the maker could defend and parts with
three competitors.** **[TRADE] / [INFERENCE]**

**About 80% of a catalogue is priced by rule and 20% by a person** — and it is the 20% that carries 80% of the
revenue. A US manufacturer with about 1.5 million spare parts automated the pricing of "the 80 percent of parts that
produce 20 percent of revenue". **[TRADE]** **The consequence for us: the parts a distributor feels most are the
ones where someone chose the price, and those are the only lines where a conversation can change anything.**

**Nobody publishes a like-for-like genuine-versus-independent price comparison at scale.** The widely repeated
"genuine parts cost 30–50% more" has no method or sample behind it. **[NOT FOUND]** used as a benchmark. **There is
no external benchmark we can adopt; our own index is the instrument.**

**Distributor margin in the independent channel is high-20s, not 40%+.** A listed European broad-line distributor
reports **29.3%** gross margin and management attributed a dip to price competition and supplier price cuts
**[MEASURED]**; a second listed distributor reports **27.4%** for FY2024 **[MEASURED]**; large European distributors
convert **4–5%** of revenue to EBITDA **[TRADE]**. **A negotiation over price is a negotiation over a couple of
points of a two-point structure.**

**The genuine margin is a step, not a slope.** A historical European Commission-commissioned study puts manufacturer
gross margin on resold parts at **60–65%**, on parts of which **75–80% are bought in** — that structural fact is what
makes the margin possible. Truck-makers now disclose service revenue at **22–26% of group sales** **[MEASURED]**, and
one truck group's parts operation earned a **≈24% pre-tax margin** against a group truck margin in the high single
digits **[MEASURED]**. **So the defensible band for a genuine-parts margin is 30–50%, with aftersales at roughly a
quarter of manufacturer profit; the "40% of profits" claim is a top-end figure and should be bounded if quoted.**

**The independent tier structure is the price ceiling, and it is legal, not a quality claim.** The key category is
the **tier-4 "OE/premium" brand — the same tier-one supplier, same tooling, same line, in its own box without the
vehicle brand.** European law recognises these as "spare parts of matching quality". Indicative positions against a
genuine part: tier 4 at roughly **60–80%**, tier 3 at **40–60%**, tier 2 at **20–40%**, tier 1 not priceable.
**[TRADE]**, with our own internal brand register agreeing on the classification. **Our reference dealer price sits
at a median 1.64× the independent price — inside the tier-4 band. On the parts where we can see the competitor, we
are priced against exactly the box our own supplier sells.**

### 14.2 Which families the independent market follows, and which it cannot

**"Electronics is captive" is wrong.** Independent suppliers publish NOx, EGT, O2, pressure and speed sensor ranges
for European trucks, one claiming **over 90% coverage in sensors**, and they publish DPF, DOC, SCR and one-box
assemblies with **original-equipment-endorsed manufacturing and three-year warranties**, including dosing modules and
supply modules. **[MEASURED]** via published catalogues — a seller's coverage claim, but the product lines are real.
**The sensor and aftertreatment families are contested. They are not the captive pool.**

**The real limit is the software and calibration gate, and it is a regulatory boundary being opened on a
timetable.** Control units are frequently VIN-paired or component-protected; some can be disabled until unlocked with
proprietary software, including genuine used ones. **[TRADE]** **ADAS calibration is the commercial chokepoint** — a
2025 survey found **47% of independent shops had turned down ADAS work in the past year, 58% of those for lack of
calibration equipment.** **[MEASURED]** And **EU Delegated Regulation 2026/699 of 23 March 2026** now requires
manufacturers to give independent operators ADAS repair, diagnosis and calibration information, tool specifications
and instructions, with a permanent online connection **prohibited** for calibration-only work, phasing in from
**23 December 2026**. **[MEASURED]** — primary legislation.

**So the family that is genuinely captive is narrower and more specific than "electronics":** it is the VIN-paired
and software-coded modules, variant coding and reprogramming, and — for another year — ADAS calibration.
**Everything else on the list is contestable, and the direction of travel is against us.** This is why the
closing-window tier in §8 exists, and why it is only 21 lines.

| What the independent market genuinely follows | What it genuinely does not |
|---|---|
| Filters, belts, wipers, bulbs — fastest and deepest | VIN-paired and component-protected control units |
| Pads & Shoes, discs and drums — deeply, with original-equipment-heritage brands | Variant coding and software reprogramming |
| Clutch, suspension and steering wear | ADAS calibration — until late 2026 |
| Rotating electrics, with strong remanufacturing | Diagnostics requiring security access |
| Cooling, sensors, and diesel aftertreatment in the truck channel | Visible body panels where design protection applies, in several member states |

**Two more findings worth carrying.** Remanufactured exchange runs **about 30% below new** on the makers' own
published figures — at the *bottom* of the 30–70% band that earlier trade reporting used, though one maker reaches
50% on engines and gearboxes — and every truck maker is expanding it. **So there is a third price level below the
independent brands that we do not occupy** — which §12 now measures in our own business. And **the manufacturer's
own second brand is the competitor in the wear families**, not the genuine part at full price: **every one of the
seven European truck makers runs a lower-priced own parts line** — four are true all-makes aimed at mixed fleets,
the rest are own-brand second lines aimed at their own ageing fleet. **The competitive set in a wear family is at
least three-way.**

**And the second-brand price is not obtainable by scraping.** Every major catalogue indexes by original part number
and returns a price, but **none of the seven is public** — all sit behind a dealer-approved login. What *is*
obtainable is **coverage**: several of these programmes publish genuine-to-second-brand part-number tables as
documents, so which part numbers are contested can be mapped without any price at all. **[MEASURED]** via the
review's source list

### 14.3 What the review says about price cutting, which is the uncomfortable part

**Two published price cuts were studied and neither published outcome data.** The review's conclusion is the one
that matters for us: **the evidence base does not support any claim about the volume response to a price change on
automotive parts.** That is the same negative result we reached independently in §7.

**And the arithmetic constrains it.** The review works the case: if a genuine part is sold at a margin implying 55%
and the independent price sits 35% below it, matching that price takes the margin to roughly **31%** — a **43%
reduction in gross profit per unit**. Volume would have to rise about **1.8×** to stand still, before any channel
consequence. **Our own numbers are harsher, because our chain multiplies a reduction by 1.785 before a customer
sees it.**

**The channel consequence is the sharpest point in the review, and it is worth stating in its own words:** *"A price
that protects the manufacturer's margin against the independent channel but destroys the dealer's margin converts
the dealer into a competitor."* The vehicle maker is not choosing between margin and channel integrity; it is
trading one for the other, and **the trade is invisible for one to three years.** **[INFERENCE]** That is the risk
our own §4 chain points at.

### 14.4 Where the money actually is

The review's own recommendation, and it is the opposite of a defensive price cut:

> **The money in pricing is on the captive side, and the evidence for that is stronger than the evidence for any
> defensive price cut.**

The basis: every source in its segmentation section says captiveness should drive a **higher** margin and most
manufacturers do not differentiate — and our own data contains the worked example, the sensor at **69.3% gross
profit** against the 56% our most aggressive class allows. The published practitioner banding is **competitive parts
25–35% margin, captive parts 55–75%**. **Our whole book sits at 51%, one band, for both.**

And the published segmentation guidance is operationally specific enough to act on: **take the top 200 parts by
revenue, map them against criticality and competition, and the high-criticality / low-competition cluster is where
you are most likely under-pricing. That is where to start testing.** **[TRADE]** With one execution diagnostic worth
running immediately: **pull twelve months of transactions and compare realised margin to list margin by segment; if
the gap exceeds three points, the problem is execution as much as structure.**

The published uplift from better segmentation is a consultancy figure of **2–6% of sales** in margin, and adjacent
published cases range from **2–4%** to an aerospace case reporting a **25% margin increase over three years.** Those
are aggregate consultancy numbers, not our expectation.

### 14.5 The three routes the review ranks

1. **Differentiate the margin by how captive the part is, using a measured score.** The method is published, the
   dimensions are published, our own data already shows the 69.3% example, and **it needs no new data source.**
   §8 is this route, built.
2. **For genuinely contested wear families, establish a second price level with a different product identity and
   warranty — not a cut on the existing line.** Every manufacturer that has attacked its own captive price did it
   this way. It avoids anchoring the genuine price, avoids destroying the dealer margin, and preserves the
   architecture for the captive families. **§12.5 finds that our own manufacturer already runs this play in the UK,
   and it is not on our radar for Israel.**
3. **Where the gap is structural, decide the sourcing, not the price.** Should-cost modelling and a re-sourcing
   decision against a defined quality standard. Re-pricing to cover a structural cost gap spends margin permanently
   for no volume.

**Two things the review says the paper must not claim, and both are adopted:** do not claim a volume response to a
price change, and do not transplant passenger-car evidence into the truck channel without saying so — the
manufacturer holds more of the truck independent channel than of the car one, and the truck aftermarket is more
consolidated. **[TRADE]**

**And one legal point that closes a door we might otherwise walk through:** the EU/EEA operates regional
exhaustion, and the motor vehicle block exemption protects parallel trade. **Parallel trade in parts is a permanent
feature of the European market and cannot be closed by agreement.** A pricing policy that assumes grey supply can be
shut down is built on a legal position that does not exist. **[MEASURED]** — block exemption regulation

---

## 15. The policy, and the proposed movements

The decision rules are unchanged from revision 2. What is new is that **the rules now produce a number**, the tier
multipliers are stated as choices, and a defect in the system as built is disclosed rather than hidden.

### 15.1 The tier multipliers — and which of them are judgment

These are the shares of the dial that each tier carries. **They are choices, not measurements.** **[CHOICE]**

| Tier | Multiplier | What it means | Basis |
|---|---:|---|---|
| Service basket (PMS) | **0.00** | Held flat | The customer's repeated running cost; defended for turnover |
| — of which, the four filter categories | **−0.20** | Cut, not merely held | The most competitive end of the basket, and the part a customer feels most often |
| Captive / gated | **1.60** | Carries the steepest rate in the book | No substitute exists |
| Closing window | **1.40** | Priced now, expected to erode | ADAS and calibration content, opened by regulation from late 2026 |
| **Body / legal** | **0.90** | Carries about 1.6× an average part | Crash-driven, and legally protected in some markets |
| — of which, **lighting** | **0.80** | **Separated from bodywork in this revision** | See §15.2 |
| Commercial | **0.80** | Damped below the average | A customer can freely buy an alternative |
| Unclassified | **1.00** | Neutral | No catalogue node; a named residual |

**Four of these seven values are pure judgment and should be read as such.** The **0.00 on the service basket** and
the **−0.20 on filters** are judgment about how much of the basket to defend. The **1.60 on captive** is judgment
about how much a customer with no alternative will bear, and it is anchored on nothing measured — the only measured
anchor we hold is the 69.3% gross margin precedent on a sensor (§2.1), which suggests there is room above the class
but does not size it. The **1.40 on the closing window** is judgment about how fast the regulatory opening erodes the
position. **The remaining three — 0.90, 0.80 on lighting, and 1.00 — are derived: 0.90 is the existing body rate,
0.80 on lighting follows from the cap arithmetic in §15.2, and 1.00 is by definition neutral.**

**The honest statement in one line: this system is honest about the shape of the answer and candid that the levels
are set by judgment, and the judgment should be revisited before any of them is used to price a line.**

### 15.2 Lighting moves to 0.80, not 0.90 — and this is arithmetic, not preference

**This is the specific movement §9 requires, and it is the one place where a rate follows from a mechanical
constraint rather than from preference. [MEASURED] for the arithmetic; [INFERENCE] for the choice of 0.80.**

The engine that applies the increase sets its own **+8% per-line ceiling**. At a 5% dial, lighting's current share of
**0.90 puts every lighting line at 8.07% — above the ceiling the engine itself sets.** **[MEASURED]**

| | Today | Proposed |
|---|---:|---:|
| Share of the overall increase carried by lighting | 0.90 | **0.80** |
| Resulting increase at a 5% dial | **8.07%** | **7.17%** |
| Same figure for collision and bodywork | 0.90 | 0.90 (unchanged) |

**And the break-even share is 0.8921** — that is the value at which the lighting rate lands exactly on 8.00% at a 5%
dial. So 0.80 is inside the ceiling with room, and any value above 0.8921 breaches it. **[MEASURED]** — arithmetic
on the system's own normalisation factor

**OF UTI'S 86 LIGHTING LINES, 82 CARRY A MOVEMENT, AND 62 SIT ABOVE THE CEILING TODAY.** At 0.80, **none do.**

**Reason in one line:** 0.80 is the rate at which every lighting line comes back inside the +8% ceiling the engine
already sets — UTI's applied increase falls from 8.07% to 7.17% — so lighting still rises, which is right for the
thinnest-margin family in collision (§9.4 shows it at a 48.2% weighted margin against collision's 55.0%), but it no
longer rises faster than the engine itself permits, and it answers the distributor's complaint.

*If management prefers the smallest possible change, 0.85 also clears the ceiling, at 7.62%. If management prefers a
single number for all collision business, leaving lighting at 0.90 alongside bodywork is defensible — but it keeps
62 UTI lighting lines above the engine's own ceiling and it leaves the distributor's complaint unanswered. What
should **not** be adopted is an increase in the lighting share above 0.90.*

**For the record.** An internal draft of this analysis proposed moving lighting to **0.97** — that is, a *larger*
share of the increase than bodywork carries. **That is the wrong direction**, and on today's numbers it would put
UTI's lighting lines at **8.70%**, still further above the engine's own ceiling. **The direction in this paper
replaces it.** **[INFERENCE]**

**And a caveat that must travel with the movement: this is a reduction in an *increase*, not a price cut.** Lighting
still rises by 7.17% at a 5% dial. The movement buys compliance with the engine's own ceiling and a defensible
answer to the distributor. **It does not buy back the write-off risk, because that risk is not measured (§9.5 items
2, 3 and 5).**

### 15.3 A defect in the system as built, stated plainly

**The system does not enforce its own +8% per-line ceiling.**

| | Lines |
|---|---:|
| Priced lines in the four markets | **17,230** |
| **Lines above the +8% ceiling** | **4,903** |
| Worst line in the book | **14.35%** |

**[MEASURED]** — computed on `pricing_system_lines_2026-09-19.csv`, the system's own output

**This is a defect in the system as built, not a design intention, and it should not be glossed.** The concentration
explains it without excusing it: 3,139 of the 4,903 are Body / legal lines (which carry 0.90), 873 are Captive /
gated (1.60), 872 are Unclassified (1.00), and 19 are Closing window (1.40). **The tiers with a multiplier above
1.00, combined with the per-market normalisation, put whole tiers above a ceiling that the engine applies per
line.** The worst values in the book are Captive / gated lines at 14.35% in one market. **[MEASURED]**

**The cap question is therefore a decision for management, and it is a real one with two legitimate answers:**

1. **The system should respect the cap** — which means either scaling every tier so that no line breaches 8%, or
   applying the cap as a hard per-line clamp and re-normalising the remaining lines upward. Either changes the euro
   totals in §8.3, so it cannot be done without re-running the build.
2. **The cap should be revised**, on the argument that a per-line cap set for a flat index is the wrong instrument
   once tiers exist — a captive part with no substitute is precisely the line where a rate above 8% is defensible.

**What is not defensible is shipping the current state without saying so.** A reader who takes the 8% ceiling as
binding and reads the tier table beside it would draw a false conclusion about what the system does.
**[MEASURED]** for the counts; the two answers are **[INFERENCE]**.

### 15.4 The dial remains management's

**The dial is a placeholder at 5% until management sets it.** At 3% / 5% / 7% the four markets yield **€576,301 /
€960,503 / €1,344,705**. The dial re-derives every line, so setting it is the only control needed. **[MEASURED]** —
§8.5

**And it should not be confused with the revision already filed.** The **+5.9616%** weighted base-price move in
§0.2, worth €1,652,140.71 of step, is a *different* thing: it is the base-price change already applied in the price
file, on the in-scope revision base. **The dial is a movement on top of today's listed prices.** The two are not
additive and must not be presented as though they were.

### 15.5 The decision sequence

Every priced line is tested in this order. The order matters, because each test can end the decision.

**1. Is there a competing price?** No benchmark, no move beyond the tier rate. *(46,276 lines — 97.2% of the 47,617
priced lines and 78.8% of the priced euro — this test ends the positional question for most of the book.)*

**2. Does the price clear cost?** Compare our landed cost to the competing price. If cost is already above it, the
line is a **sourcing** question and it leaves the pricing queue. *(12 of the 41 observed parts today — and on 26 of
the 33 bridged part numbers in §3.3 the competing price is below our own distributor's cost.)*

**3. Does the price clear the chain?** Compute the dealer price, not just ours, and label every dealer-level figure
as the construction it is. If a move does not change what the customer sees, it is not a competitive move and should
not be justified as one.

**4. Then the tier**, from §8, which sets the rate the line carries.

**5. Then the two brakes on the rate**, which are the ones that matter and are specific to this book: **the +8%
per-line ceiling** (§15.3, currently unenforced) and **the insurance write-off risk on collision parts** (§9). A
line in Body / legal that is also a lamp is a line where the second brake applies.

**6. Then the margin floor**, expressed as a minimum contribution rather than a margin percentage, because a
percentage floor at 15% will authorise a price below cost on the parts where cost is highest.

### 15.6 The proof that this is not the old policy

One test of whether a policy is real: **can it name a part that moves differently from the others, and say why?**
Under the current method the answer is no — every part in a class moves by the same percentage. **Under this policy
the answer is a list, and §16 states it.**

### 15.7 What the policy still cannot do

- It cannot price 78.8% of the book by euro, because there is no benchmark — 46,276 lines, 97.2% of the priced lines.
- It cannot decompose the price we actually charged, because the extract is net-only. There is no realisation
  waterfall and there will not be one.
- It cannot tell you what a price cut buys in volume. §7 explains why the data cannot answer that.
- It cannot buy competitiveness at our level alone. The chain in §4 means our margin is multiplied by 1.785 before a
  customer sees it.
- **It cannot express the write-off risk it has identified**, because the loss rate is unmeasured. §15.2 reduces an
  increase in response to that risk; it does not price it.

---

## 16. The proposed movements, stated

**This is the page the brief asked for: the policy section must state the proposed movements, not only describe a
method. Each movement carries its one-line reason and its grade.** **[CHOICE]** means a judgment; **[MEASURED]** means
arithmetic on our own files. No live price is moved by this paper.

### 16.1 The basket that comes down

| Movement | Lines | On revenue | Effect at the 5% dial | Reason | Grade |
|---|---:|---:|---:|---|---|
| **Service basket held flat, then cut on filters** | **816** | **€3,332,334** | **−€18,664** | This is the customer's repeated running cost and the tier where a price move is felt most often. It is defended for turnover, not for margin. | **[CHOICE]** on the rate, **[MEASURED]** on the euro |
| — the four filter categories, cut hardest (share −0.20) | within the above | — | oil filters down in every market; UTI's oil filter −€2,051 and AdBlue filter −€3,140 | Filters are the most competitive end of the basket and the part a customer prices most often. | **[MEASURED]** the euro, **[CHOICE]** the rate |
| **Lighting share 0.90 → 0.80** | 86 UTI lines (82 carrying a movement) | €133,667 UTI lighting | UTI lighting 8.07% → **7.17%**; 62 lines come back inside the +8% ceiling | 0.90 breaches the engine's own per-line ceiling; 0.80 does not, and it answers the distributor's complaint without yielding on the insurance mechanism. | **[MEASURED]** the arithmetic; **[INFERENCE]** the choice |
| **Collision and bodywork unchanged at 0.90** | 244 UTI collision lines | €218,147 | unchanged | Crash-driven and legally protected in places; the panel logic is not the problem, the lamp logic was. | **[CHOICE]** |

### 16.2 The tiers that carry the increase

| Movement | Lines | On revenue | Effect at the 5% dial | Reason | Grade |
|---|---:|---:|---:|---|---|
| **Commercial carries the increase at 0.80** | **10,698** | **€10,838,823** | **+€570,990** | 53.8% of the book by revenue and the tier where a customer can freely buy an alternative, so the rate is damped below the average. | **[CHOICE]** on 0.80, **[MEASURED]** on the euro |
| **Captive / gated takes 1.60, the steepest rate in the book** | **928** | **€660,814** | **+€61,283** | The only tier where a price move cannot be answered by buying something else. A control unit has no alternative on any shelf. | **[CHOICE]** on 1.60; anchored only on the 69.3% sensor precedent |
| **Closing window takes 1.40** | **21** | **€137,285** | **+€13,906** | Priced now because the regulatory opening from 23 December 2026 will erode it. Almost nothing is listed against it yet, which is itself the finding. | **[CHOICE]** |
| **Unclassified takes the neutral rate, 1.00** | **999** | **€918,854** | **+€58,944** | No catalogue node could be assigned. Left out of the family totals rather than guessed, and named as a residual. | **[MEASURED]** the count, **[CHOICE]** the rate |

### 16.3 The launches, held outside the dial

| Movement | Scope | Effect | Reason | Grade |
|---|---|---|---|---|
| **Price the 13 functional SCR / AdBlue parts at the top of the policy band, and hold them flat once each vehicle's own warranty ends** | 13 part numbers, P700 / D-Max 2.2L | price book +25% (to €9,291.92) or +35% (to €10,035.27) against €7,433.53 class-implied | No aftermarket equivalent exists on any evidence on disk, and the current list sits exactly at the class-implied price — **there is no premium in the launch book today.** This is free pricing nobody has claimed. | **[MEASURED]** the prices; **[CHOICE]** the level |
| **Hold the aftertreatment price flat once each vehicle's own warranty ends** | the filter family | a timing decision, not a discount | The paid channel should not compete with a refurbisher on a part we have just priced at our thinnest margin. §12.7. | **[INFERENCE]** |
| **Do not extend the launch treatment to the other 1,033 parts** | 1,033 part numbers | no change | 1,048 of them carry four consecutive published prices. A distributor can and will compare those lines. | **[MEASURED]** |
| **Restate Israeli prices on the measured 14%, not the recorded 10%** | any Israel-to-standard-basis read-across | price level moves about 5.6% | The measured median discount is −13.95% on 134,896 matched part numbers, with a 1.3-point interquartile range. | **[MEASURED]** |
| **Ask why Israel gets the reman answer and the UK gets the new-in-lieu answer** | the filter family, Israel | a question, not a movement | Our own manufacturer already runs the play that beats cleaning, in the UK, argued in our own words. It is not on our radar for Israel. | **[INFERENCE]** |

### 16.4 What is proposed to be *asked*, and not moved

| Ask | Of whom | Why it is an ask and not a movement | Grade |
|---|---|---|---|
| **Is the +8% per-line ceiling binding, or should it be revised?** | management | 4,903 of 17,230 priced lines sit above it today. Either answer re-derives the euro totals. §15.3. | **[MEASURED]** the defect; **[CHOICE]** the answer |
| **Are the four front pad kits interchangeable?** | the electronic parts catalogue | If they are, a 25% price spread across networks on a safety-critical wear part is a commercial finding. If not, the +24.9% stands. §13.1. | **[NOT FOUND]** |
| **Does the base price embed a premium over transfer cost?** | IML, under separate investigation | If it does, the launch headroom is measured from a non-neutral base and could be materially smaller. §11.4. | **[NOT FOUND]** |
| **What is the write-off threshold above 3.5 tonnes, and what is the loss rate?** | the insurers, and the market | Without them the write-off risk is documented in principle and unmeasured in fact. §9.5. | **[NOT FOUND]** |
| **What does a distributor actually do with a cut?** | ITUK and the other distributors | A conversation, not a data collection. It is the one finding that would reverse this paper. §4. | **[NOT FOUND]** |

### 16.5 The movements in one paragraph

**We propose to hold the service basket flat and cut the four filter categories, to separate lighting from bodywork
and take it to 0.80, to leave the rest of collision at 0.90, to carry the increase on the commercial tier at 0.80
and take the steepest rate in the book from the captive tier at 1.60, to price the 13 functional SCR parts at the top
of the policy band because they are currently priced at class and no higher, to hold aftertreatment flat once
warranty ends, and to restate Israeli read-across on the measured 14% rather than the recorded 10%.** At the 5%
placeholder dial that produces a book movement of about €960,500, of which the service basket gives back €18,664.
**Every level in that sentence is a choice; the arithmetic underneath it is measured. And four of the choices need
management's answer before any of them prices a line: the cap question, the interchangeability question, the base
price question, and the write-off loss rate.**

---

## 17. Decisions

**1. Adopt the two-tier system, and decide the cap question with it.** §8 is built and §15.3 discloses that it does
not enforce its own +8% per-line ceiling. Either the system respects the cap or the cap is revised, and either answer
requires a re-run. **This is the first decision, because it determines every number after it.**

**2. Set the dial.** The 5% used throughout is a placeholder. At 3% / 5% / 7% the four markets yield €576,301 /
€960,503 / €1,344,705. **This is management's number and nothing else in the paper substitutes for it.**

**3. Decide whether brakes is the pilot.** Everything needed is on disk: 82.6% evidence coverage, twenty part numbers
carrying three-quarters of the family, and a live complaint case on `8982447940`. **One family, done properly, would
answer the questions the whole-book argument cannot** — and §13.1's first question is not a price question at all.

**4. Confirm lighting at 0.80, or take 0.85, or explain why 0.90 stays.** §15.2 gives the arithmetic and the
break-even share of 0.8921. **Whatever is decided, the number should be recorded with its reason, because this is the
one rate in the system that follows from a mechanical constraint rather than a preference.**

**5. Settle the FY2027 ambition on a stated basis.** Before or after the distributor support payment. Before support
the full amount lands; after support, at the 20% figure the specification uses, €1.00 of headline lands as €0.80, so
a headline of +4% nets +3.2%. The options are +4% (€581k a year on forecast weights), +5% (€726k), or an open
increase on the launch families with the legacy book at +3%.

**6. Decide whether the brakes-low / emissions-high shape is a target or a consequence — and read it against §9 and
§14.** As computed it adds €540k of gross profit, by raising emissions prices 35% to fund a brakes cut. **The external
evidence says the emissions family is contested, not captive** — independent suppliers publish near-complete sensor
and aftertreatment coverage with original-equipment endorsement — and on the bridged part numbers the aftermarket
equivalent is often below our own distributor's cost. **The raise is funding a cut by betting on a captiveness the
evidence contradicts.** The cut and the raise should be decided separately, and the raise should be aimed at the
families that are genuinely gated: VIN-paired modules, variant coding, and until December 2026, ADAS calibration.

**7. Fund the competitive price index, or accept 16.5% of billed euro.** Every independent source we hold covers 307
distinct part numbers. Brakes is the proof that dense coverage is achievable — 82.6% of that family by billed euro.
Doing the same for two or three more families is a resourcing question, not a technical one. **And the launch book
makes the point sharper: competitor evidence is present on 1 part in 1,132, so the entire launch book has no
permitted positional move.**

**8. Establish whether we have a voice in class assignment and in the base price.** This is now sharper than in
revision 2. The margin is set by a letter, so **class assignment is margin assignment** and it fixes the margin for
the life of a part. **The launch work makes it concrete: 922 of the 1,071 classed new part numbers sit in class C and
only 2 sit in class P**, which is the reason €660,814 of captive-tier revenue is as small as it is. **Whoever assigns
the class assigns the price**, and 80% of a catalogue is priced by a rule.

**9. Aim the margin increase at what is genuinely gated, not at what is merely unfamiliar.** Our instinct is to treat
sensors and electronics as captive, and the evidence says the opposite. The genuinely gated families are narrow: the
VIN-paired and component-protected modules, variant coding and reprogramming, and ADAS calibration until the December
2026 rule bites. **The system's closing-window tier is 21 lines on €137,285 — the whole regulatory opening, and almost
nothing is listed against it.** That is the cheapest real margin in the book and nobody has looked.

**10. Decide whether our own second brand is priced as a competitor or as a cost.** Every one of the seven European
truck makers runs a lower-priced own parts line against the independent market, and we run one too — our BVP
catalogue, with **356 part numbers** already cross-referenced to **431 genuine numbers**. That file also carries
`vehicle_model` and `engine_type` on 453 and 292 pairs, which is the fitment attribute this paper says we lack — but
on only **213 part numbers of 15,273**, or 7.1% of billed value. **Is BVP deliberately priced against the brands in
front of those part numbers, and should that cross-reference be extended to the whole catalogue?**

**11. Decide the filter position, and decide it as terms and timing rather than as price.** §12.7 gives the reason:
the strongest lever is not to cut the part but to hold the aftertreatment price flat once each vehicle's own
warranty ends. **And the question to ask first is why Israel gets the reman answer and the UK gets the new-in-lieu
answer**, when we invented the second one ourselves.

**12. Take the review's starting point — the top 200 parts by revenue, mapped against criticality and competition.**
The high-criticality / low-competition cluster is where we are most likely under-pricing. It needs no new data
source. Run it alongside the brakes pilot; the two answer different questions.

**13. Put currency on every price pack.** The rate in use fell the euro price of an unchanged yen base price by 11.7%
since 2023 and does not move our margin at all. Any competitive comparison without a currency stamp is a comparison
against a moving floor.

**14. Answer the pass-through question with ITUK, as a conversation and not as a data request.** What actually
happens to the dealer price when we reduce ours. No model can answer it, and no file will either — a distributor's
resale price is not something we hold or will obtain. Until ITUK tells us, the chain in §4 is arithmetic at a stated
assumption and nothing more.

**15. Confirm the warranty term and mileage cap, market by market.** The load-then-hold tactic on failure-driven
parts pays above roughly three years and costs money below it.

**16. Decide the CIS competitor profile** — Chinese genuine-equivalent, Chinese independent, or EU re-export. The
three call for different responses. **And note the legal constraint: parallel trade inside the EEA cannot be closed
by agreement**, so re-export monitoring is a detection tool, not a cure.

---

## 18. What would make this paper wrong

**If the cost basis is materially wrong.** The cost floor rests on the cost implied by the assigned margin. Where
that margin is generous the headroom is overstated. If a true purchase cost showed the 26 "reachable" brake parts
are actually 5, the sourcing list becomes the whole answer and the pricing policy for brakes collapses. **This is the
single largest uncertainty in the paper**, and it resolves from our own landed cost per part on an evidenced sample —
not from a dealer price, which we do not have and are not going to get. §3.3 is the method already working on 35 part
numbers.

**If the captured-demand measure is biased.** It is already the reason 46,893 of the 47,617 lines fall through to the
fallback ladder — 46,893 being the lines with no service category on the captured-demand measure, which is a
different count from the 46,276 lines with no benchmark price. A systematic bias at distributor level would
invalidate the first gate of every rule.

**If the pass-through is not what the chain assumes.** If distributors hold their absolute margin rather than their
percentage, a cut in our price moves the dealer price much further than §4 shows, and the case for cutting gets
stronger. **That is the one scenario that would reverse this paper's conclusion on margins**, and it is testable —
but only by asking the distributors what they do.

**If the cap question is answered the other way.** If the +8% ceiling is revised rather than enforced, the captive
and body tiers can carry more than §8.3 shows and the book movement rises; if it is enforced as a hard clamp, those
tiers carry less and the movement falls. **Every euro in §16 moves with that answer.**

**If the write-off risk is real and the loss rate is not small.** §9 documents the mechanism and §15.2 reduces an
increase in response. **If a lost-repair rate of one in ten turned out to be one in four, the correct response on
lamp lines would not be a smaller increase but no increase at all** — and the 2018 funded-rebate route would be the
better instrument. **This is the finding that would most change the collision numbers, and it is unmeasured.**

**If the base price already embeds a premium.** §11.4. If it does, the +25% to +35% launch headroom is measured from
a base that is not neutral and could be materially smaller.

**If the pickup compliance reading is wrong.** §10 rests on two independent UK grounds and on reading the
regulations directly, so it is robust. **But §10.5 records that the Portuguese licensing position is an inference
from the European framework and not a Portuguese-language primary source**, and that the Israeli policy threshold is
read by two documents as 55% and 50%. Neither changes the conclusion; both should be settled before either number is
quoted outside this paper.

**And if the argument is that we should simply raise less**, that is a real position. This paper is about *where*
price goes and what margin is available, not how large the increase should be.

**One external finding that would invert §14, if it holds in parts.** A formal assessment tested on 128 certified
pricing professionals found that pricing power *"has little to do with pricing; it mostly concerns innovation and
differentiation"*, and specifically that **the relationship between competitive intensity and pricing power was not
statistically significant.** **[MEASURED]**, on a non-automotive sample. If that holds for parts, then the "how many
competitors exist" dimension that the tier logic rests on is doing less work than assumed, and criticality and
differentiation are doing more. **One study, wrong industry, so it is a caution rather than a refutation.**

**And if the brand label is the real problem rather than the price.** §12 finds that in a contested family the
genuine part's competitor is usually the manufacturer's own second brand, and behind that the remanufactured exchange
market. **Every one of the seven European truck makers runs such a line**, and none publishes its price to the open
web. **If the customer's actual alternative is our own group's lower tier or a reconditioned unit, then a margin
discussion at our level is aimed at the wrong competitor, and the answer is a product decision rather than a price
one.**

---

## Appendix A — Where every figure comes from

| Figure | Value | Source | Grade |
|---|---|---|---|
| In-scope billed / priced | €34,993,609.39 / €32,595,852.63, 47,617 lines | `price_bp_weighted_compare_pn.csv`, `in_scope == True` | [MEASURED] |
| Weighted base-price move and step | 5.9616%, €1,652,140.71 | same; ties to `aim_pricing_recalc_2026-09-17.json` | [MEASURED] |
| Book with a usable margin | 45,816 lines, €29,653,732, 51.09% GM, €15,150,306 GP | `pricing_aim_source_lines.parquet` + `pricing_list_pn.parquet`; `pricing_cost_floor_meta.json` | [MEASURED] |
| Whole book at 15% / 20% margin | €2.56M / €3.63M gross profit (−€12.6M / −€11.5M) | same, cost held fixed | [MEASURED] |
| 84.3% of the book inside the 45–56% margin band | computed | same | [MEASURED] |
| Margin by class letter | C 53.0% / D 52.0% / F 47.5% / J 44.5% / M 50.0% / P 56.0% / V 45.0% / T 20.0% | `03_analytics/isze_pricing/config.yaml`, `pricing_list_pn.parquet` | [MEASURED] |
| Cost-reach analysis | 41 part numbers, 12 unreachable, 3 under 20%, 26 at 20%+; median margin to match 52% | `pricing_cost_floor_reach.csv`; `iam_ks_price_gap.csv` | [MEASURED] |
| Margin-target scenarios | +€540,066 / −€64,394 / −€2,484,145 / −€5,481,356 | `pricing_cost_floor_meta.json` | [MEASURED] |
| Channel chain | ×1.40 distributor, ×1.275 dealer, ×1.785 reference | `config.yaml`; `DB_DLR_COMMERCIAL_STACK.md` | [MEASURED] the stack; [CHOICE] the 35% |
| Aftermarket below our own distributor's cost | 26 of 33 testable bridge part numbers; median 0.66×; 24 of 33 below every floor; four worked cases at 0.15–0.16× | `oe_bridge_coverage.csv` × `replenishment_bridge.parquet` (floor = billed euro ÷ billed quantity per distributor) | [MEASURED] |
| Bridge coverage | 76 of 15,273 priced part numbers = 0.50% | `eucon_crossref_iam_20260329.csv`, `oe_bridge_coverage.csv` | [MEASURED] |
| Israeli shop lines vs the floor | 13 of 20 have a floor; 0 below it; min 2.41×, median 5.95×, max 12.20× | `replenishment_bridge.parquet` + the 2026-09-18 shop sweep in `01_data/90_INBOX/scrape_targets/israel.md` | [MEASURED] |
| Chain at today's margin | ours 1.09×, dealer 1.95× vs the competing price | `pricing_chain_and_fx.csv` | [MEASURED] |
| Currency history and effect | 146.6 (2023-10), 159.4 (2024-10), 163.7 (2025-10); −11.7% euro price; position 0.98× → 1.09× | `config.yaml`, `pricing_chain_and_fx_meta.json` | [MEASURED] |
| Position and tier tables | §6.1 | `02_dashboards/pricing/_build/_spec_basis_meta.json` | [MEASURED] |
| Lines with no service category | 46,893 of 47,617 priced lines | same file, `no_service_category_lines` | [MEASURED] |
| T5, no benchmark price at all | 46,276 lines; €25,672,208 = 78.8% of the €32,595,853 priced euro | same file | [MEASURED] |
| T4 + T5 | €27,226,636 = 83.5% of the priced euro | same file, `tier_eur.T4` + `tier_eur.T5` | [MEASURED] |
| With a benchmark price | 880 lines, €5,369,216 = 16.5% of the priced euro; 21.2% with the category-median tier | same file | [MEASURED] |
| Autodoc data fault | 277 of 298 rows carry €2.34 | `competitiveness_autodoc_risk.csv`, inspected | [MEASURED] |
| Response panel | 3,662 part numbers, −1.9% volume, +3.3% price, weighted elasticity −0.69 | `ituk_price_volume_response.csv` | [MEASURED] |
| Price variation | IQR 0.69pp; 70.6% within ±1pp; SD 22.4; 226 outliers, median 0.00 | same | [MEASURED] |
| Family price move vs volume move | correlation **0.06** | ITUK dealer purchase panel (CY2023/CY2025) + `price_bp_weighted_compare_pn.csv` + `aim_pn_classification_v2.csv` | [MEASURED] |
| **Two-tier system: tiers, lines, revenue, movements** | service basket 816 lines / €3,332,334 / −€18,664; commercial 10,698 / €10,838,823 / +€570,990; captive 928 / €660,814 / +€61,283; closing window 21 / €137,285 / +€13,906; body 4,477 / €4,252,793 / +€274,178; unclassified 999 / €918,854 / +€58,944; whole book 17,939 / €20,140,903 | `pricing_system_figures_2026-09-19.json`, `pricing_system_lines_2026-09-19.csv`, `build_pricing_system_20260919.py` | [MEASURED] |
| The dial at three levels | PR00 €353,236 / €588,727 / €824,218; UTI €108,687 / €181,145 / €253,603; UMI €76,468 / €127,447 / €178,426; CIS €37,910 / €63,184 / €88,458; total €576,301 / €960,503 / €1,344,705 | same | [MEASURED] |
| Tier multipliers | service basket 0.00, filters −0.20, captive 1.60, closing window 1.40, commercial 0.80, body 0.90, unclassified 1.00 | `build_pricing_system_20260919.py`, `MULT` / `MULT_FILTER` | **[CHOICE]** |
| The +8% ceiling defect | 4,903 of 17,230 priced lines above it; worst 14.35%; 3,139 body, 873 captive, 872 unclassified, 19 closing window | computed on `pricing_system_lines_2026-09-19.csv`, fields `dial_movement_pct`, `tier` | [MEASURED] |
| Lighting share arithmetic | 0.90 → 8.07%; 0.80 → 7.17%; break-even share **0.8921**; UTI 86 lighting lines, 82 carrying a movement, 62 above the ceiling at 0.90 | same file, UTI lighting nodes, with the system's normalisation factor 0.557593 | [MEASURED] |
| UTI lighting and collision | lighting 86 lines, €133,667, 48.2% weighted margin, 38.0% of the two families, 73.9% of revenue in the 47.5% class; collision 244 lines, €218,147, 55.0%, 0.0% | `UTI_LIGHTING_COLLISION_MANAGEMENT_20260919.csv` | [MEASURED] |
| Lighting as a share of UTI's parts book | 3.9% (€133,667 of €3,400,405) | same | [MEASURED] |
| Mirror-node alternative share | 35.0% counting the mirror nodes (€30,054) as collision | same | [MEASURED] |
| The earlier 30.8% | not reproducible from the method as written | `LAMPS_INSURANCE_RESEARCH_20260919.md` | [MEASURED] for the discrepancy |
| Israeli write-off thresholds | 60% total loss; 55% constructive (management note) / 50% (pickup research) | `LAMPS_INSURANCE_MANAGEMENT_20260919.md`; `MARKET_PICKUP_PRICING_POWER_20260919.md` | [MEASURED], **[NOT FOUND]** on the reconciliation |
| UTI presentation figures | collision package €679.21 → €2,144.48 (+215%) N/7.5 and €923.66 → €2,314.14 (+150%) F/10; head lamp +332%; rear light +1,228%; turn signal +333%; signal +394%; bumper split one part €143.37 into four at €320.00 (+123%); 1,700 trucks on five-year repair-and-maintenance contracts | UTI presentation, July 2026, pages 8, 27, 30, 31 | [MEASURED] |
| Court text, State Comptroller audit, 2018 rebate correspondence | quoted and carried | `LAMPS_INSURANCE_RESEARCH_20260919.md` | **[REPORTED — NOT VERIFIED]** |
| Pickup licensing: UK two grounds | 3,100 kg plated against 3,500; dual-purpose exemption with ~1,985 kg unladen against 2,040 | GOV.UK licensing guide; Goods Vehicles (Licensing of Operators) Act 1995; Regulations 1995 Schedule 3 para 2; Construction and Use Regulations 1986 reg 3; manufacturer's weights | [MEASURED] / [INFERENCE] on the subtraction |
| Pickup licensing: UK towing | gross train weight 6,000 kg against a 3.5 tonne combination threshold | GOV.UK licensing guide; manufacturer's figures | [MEASURED] |
| Pickup: Ireland | annual commercial test one year after first registration and annually after; statutory maintenance duty; Goods Only Declaration at the €333 rate | RSA and CVRT; Commercial Vehicle Roadworthiness (Vehicle Maintenance) Regulations 2013 | [MEASURED] |
| Pickup: Portugal | >90% three-seat homologation; ~€5,500 retail difference; €4,000–€8,000 tax difference between N1 and M1; N1 inspection at two years then annually | Portuguese import and tax guidance; motoring press; manufacturer's own campaign page | [MEASURED]; **[NOT FOUND]** on the Portuguese licensing primary source |
| Pickup: Israel | registered commercial (N1); 280,849 M1 against 10,671 N1 registrations in 2025; 1,602 D-Maxes sold in 2025 of which 697 in the best-selling trim; 66.4% private ownership | policy wording read directly; Israel Vehicle Importers Association | [MEASURED] |
| Mileage by market | UMI 34,443 km (13,611 VINs); Ireland 27,998 (426); UK 24,481 (29,646); Portugal 22,742 (1,596); Europe 25,600 (76,208) | `EU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx` | [MEASURED]; **UMI only, UTI absent** |
| Fleet base | UK 47,783 (IUK); Israel 18,542 (UMI); Portugal 4,733; Ireland 1,338 | `uio_by_market_type_year.csv` | [MEASURED], **all rows `is_estimate`, not `is_actual`** |
| UK market and tax change | 37,308 registrations in 2025, −0.7%; August 2026 404 units, −61.2% YoY; benefit-in-kind reclassification from 6 April 2025 | SMMT; HMRC EIM23151 | [MEASURED] |
| UK pickup parts listings | genuine oil filter £16.99; Blue Print alternative £30.00–£36.00; air filter £31.25; fuel filter £14.57; air filter £29.40; cabin filter £21.16; Brembo pads £45.99–£49.49 | retailer and price-comparison pages, read 19 September 2026 | [MEASURED] |
| Launch: new against carryover | 1,132 new part numbers, 897 carryover; 1,072 (94.7%) with a base price and a 2026 price; 1,048 (92.6%) with four consecutive published prices; all 41 SCR parts with a 2023 price | `P700_2P2L_LAUNCH_PRICING_20260919.md`, `p700_2p2l_launch_pricing_20260919.csv` | [MEASURED] |
| Launch: class distribution | 922 of 1,071 classed parts in class C (53% margin); 2 in class P | same | [MEASURED] |
| Launch: posture | captive 408, body/hardware 396, wear 92, unclassified 236 | same | [MEASURED] |
| Launch: 13 functional SCR parts | class-implied total €7,433.53 against a current list of €7,467.31 — within 0.45%; `split` +25.0%; `warranty_load` +35.0% | `p700_2p2l_scr_functional_20260919.csv` | [MEASURED] the prices; **[CHOICE]** the level |
| Launch: NOx sensor price history | 2023 €272.53, 2024 €259.32, 2025 €263.00, 2026 €261.11 | same | [MEASURED] |
| Launch: competitor evidence | 1 part in 1,132 has a competing price | same | [MEASURED] |
| Launch: Israel discount restated | median −13.95%, IQR 1.3 points, on 134,896 matched part numbers; restate by ×1.1621, against a configured ×1.10 | UTI export list × standard list | [MEASURED] |
| Launch: model and gearbox mix | 2,585 planned units; 3.5t 1,405 (54.4%), 7.5t 979 (37.9%), 13.5t 135 (5.2%), 11.0t 37 (1.4%); MT 1,215 (47.0%), AMT 1,029 (39.8%), AT 341 (13.2%) | `2026-05-18_UTI_P700_UK_model.xlsx` | [MEASURED] as a plan |
| Urea filter interval and rate | 200,000 km (P700-era N-series schedule); no D-Max interval; billed per vehicle per year 0.0085 / 0.0094 / 0.0122 against an assumed 0.809 | schedules; the capture denominator | [MEASURED]; **[NOT FOUND]** on a D-Max interval |
| Reman: price ratios | UK car/van ~0.10–0.30; UK truck clean ~0.03–0.10; UK truck reconditioned exchange ~0.20–0.40; Israel car/van ~0.10–0.20; Israel truck **[NOT FOUND]**; Portugal/Ireland **[NOT FOUND]** | supplier catalogues; trade price guides | [TRADE] / [MEASURED] per row |
| Reman: cleaning effectiveness | 90–98% of build-up removed; 80,000–150,000 km further life; 92% of weight but only 65% of pressure drop; 96% of deposits removed (SAE 2023-01-0376) | DPFpro; Fox, Yang & Hunsicker 2019; SAE | [MEASURED] |
| Reman: warranty norms | 12-month norm on off-car cleaning; 6 months on cheaper operations; none on on-car | published supplier terms | [MEASURED] |
| Reman: Israel regulation | removal lawful only for cleaning, repair, replacement or scrapping; penalty six months or a fine | Air Quality (Vehicle Air Pollution) Regulations amendment 7986, reg. 8 | **[REPORTED — NOT VERIFIED]** |
| Reman: per-market legality | UK non-type-approved supply illegal, fine up to £5,000; Ireland removal an offence, dangerous defect; Portugal illegal, fails the test, fines €250–€1,250, particle-number test being regulated at 250,000 particles/cm³ for Euro 5b+; Israel opacity ≤ 0.2 m⁻¹ with particle-number measurement stated as intended | DVSA and legislation; RSA; Portuguese motoring press and the motoring authority; Israeli regulations | [MEASURED] per market |
| Reman: Israeli provider base | at least five named specialist firms, one a Ministry-of-Transport-approved parts supplier serving insurers, leasing and rental companies and importers | company sites; ministry tender document | [MEASURED] |
| Reman: warranty book by market | Israel 436 truck filter lines / €696,907 / median 129,200 km / €1,696 per claiming vehicle; UK 119 / €116,272; Spain 62 / €57,007; Italy 46 / €50,604; France 14 / €13,690; Portugal 24 / €12,182 | `REMAN_DPF_MEASURED_LINES_20260919.csv`, from `01_data/06_Warranty/*.xlsx` | [MEASURED] |
| Reman: the filter in the claim book | truck-wide €965,904 of €4,655,881 = 20.8% of claim cost on 7.2% of lines; Israel 40.4% of its truck parts claim cost | same | [MEASURED] |
| Reman: warranty boundary | Israel 76% outside the stated limits (€455,633 over distance, €72,340 over age); UK 76%; Portugal 65%; whole book 76%; 434 of 719 lines over 100,000 km | same | [MEASURED] |
| Reman: reconditioning found in warranty | "DIESEL PARTICULATE DEFUSER - RECONDITION AND/" 6 lines, €5,689, median 79,087 km, Israel only | `warranty_cv_top_repair_lines.csv` and the raw sheets | [MEASURED] |
| Reman: claim over list | UMI 1.71–1.78×; IUK 1.21×; ITUK 1.30×; UTI 1.65–1.71× | warranty files ÷ `pricing_list_pn.parquet` | [MEASURED]; **[NOT FOUND]** the mechanism |
| Reman: two existing answers | North America reman with 12-month/unlimited-mile warranty; UK new-in-lieu announced 14 December 2017 | Isuzu's own published material | [MEASURED] |
| Reman: core loops | 24 core lines totalling €3,646 in the whole truck claim book, all evaporator/heater/fuel-cooler; 2 core lines in the light commercial book | warranty files | [MEASURED] |
| Brakes family | 334 part numbers, €3,142,066, €215,508 step, 7.36% move; discs 55.3% of euro but pads 52.8% of step | `pricing_aim_source_lines.parquet` | [MEASURED] |
| Brake concentration | top 1 22.4%, top 10 61.0%, top 20 76.2% | same | [MEASURED] |
| Brakes evidence coverage | 311 part numbers, €2,596,458, 82.6% | union of the three competitor files | [MEASURED] |
| The four front pad kits | €82.25 / €82.25 / €89.11 / €102.65; none superseded; ITUK+UTI on the two most expensive | `pricing_list_pn.parquet` + `pricing_aim_source_lines.parquet` | [MEASURED] |
| Ambition euros | €383k / €581k / €726k a year | `forecast_weight_sensitivity_provisional_20260812.csv` | [MEASURED] |
| Our own second brand | BVP: 544 pairs, 431 genuine to 356 BVP part numbers, `vehicle_model` on 453 pairs, covering 213 priced part numbers / 7.1% of billed value | `genuine_bvp_crossref.csv`, `bvp_pn_dimension.csv` | [MEASURED] |
| Sensor at 69.3% GP vs 56% class | the worked captiveness example | `ISZE_Pricing_Spec_v1.md` §9, DPF sensor `8978808270` | [MEASURED] |
| External operator review | tier positions, margin structures, family contestability, the calibration gate, Regulation 2026/699, the 1.8× volume break-even | `_ANON_OEM_IAM_PRICING_REVIEW_20260917.md` | mixed; graded inline in §14 |
| All-makes and reman programmes | all 7 European truck makers run one; none publishes a price to the open web; reman ≈30% below new | `scrape_targets/all_makes_programmes.md` | [MEASURED] / [TRADE] |
| Warranty tactic | €23.51M against €23.55M over ten years | `ISZE_Pricing_Spec_v1.md` §9.3 | [MEASURED] |

**Builders and scripts behind this revision** (all rerunnable; the new ones print their own checks):
`01_data/90_INBOX/build_pricing_system_20260919.py` · `check_pricing_system_20260919.py` ·
`_build_p700_2p2l_launch_20260919.py` · `build_lamps_insurance_review_20260919.py` ·
`measure_uti_lighting_collision_20260919.py` · `build_market_pickup_pricing_power_20260919.py` ·
`measure_reman_dpf_20260919.py` · `build_reman_dpf_measured_csv_20260919.py` ·
`01_data/91_build/build_ituk_price_volume_response.py` · `build_pricing_cost_floor.py` ·
`build_pricing_chain_and_fx.py` ·
`02_dashboards/pricing/_build/build_pricing_policy_paper_rev3.py` (the HTML builder for this revision).

**Corrections carried from revision 2, still standing:** the dealer-value item is not an open data request (§0.2,
§3.1, §4); the aftermarket sits below our own distributor's cost on the bridged sample (§3.3); Israel is not a
discount channel, closed as a no-finding (§6.4).

## Appendix B — Terms used once, then abbreviated

**arc elasticity** — the change in quantity divided by the change in price, both taken as percentages of their
midpoints. −1 means volume falls in proportion to price.

**capture rate** — what dealers actually bought, as a share of the demand the vehicles in service should generate,
by distributor and service category. Total sales, not genuine only.

**class letter** — the letter on a part number (C, D, F, J, M, P, T, V) that sets the margin. **Class C is a 53%
margin, class V a 45% margin.** Say the margin, not the letter.

**DPD / DPF** — the same part. DPF (diesel particulate filter) is the industry term; **our own catalogue calls it
DPD**, `DPD ASM`, and the claim file calls it a "particulate defuser". There is no second product.

**FOB** — free on board, the landed cost of the part before the margin is applied.

**figure number** — Isuzu's own parts-catalogue illustration group, in the form X-XX. On our extract as `fig_key`,
e.g. `411-025`.

**gross margin** — price minus landed cost, over price. In the formula this is fixed by the class letter; it is not
currently a commercial decision per part.

**IUK / ITUK** — the two UK networks. IUK is light commercial (models coded TF); ITUK is trucks (N and F series).
**Never blended.**

**Laspeyres index** — a weighted average of price changes using last period's quantities as weights. This is what the
annual increase is solved to.

**OES / tier 4** — the same component from the same tier-one supplier, in the supplier's own box without the vehicle
brand. European law calls these "spare parts of matching quality". **This is the price ceiling our index measures
against.**

**OPD / particulate filter** — see DPD / DPF.

**price index** — our reference dealer price divided by the competing price. Below 0.95 we are cheap, above 1.15
expensive.

**reference dealer price** — the official list price × 1.40 × 1.275, i.e. ×1.785. What a dealer would show a
customer. **A construction, not an observation.**

**remanufactured / refurbished / reconditioned** — a used unit restored to working order rather than replaced with a
new one. Priced far below new; the third price level in §12.

**step euro** — the euro value of a base-price change on the volume actually billed.

**tier (T1–T5)** — the quality of the competing-price evidence, and therefore how far the line may move.

**tier (the six)** — in §8, the commercial posture a line carries: service basket, commercial, captive / gated,
closing window, body / legal, unclassified. **Two different uses of the word "tier" appear in this paper** — the
evidence tiers T1–T5 and the commercial tiers in §8. Where the paper means the commercial tiers it says so; where it
means evidence it uses T1–T5.

**UMI / UTI** — the two Israeli distributors. UMI is the light commercial and pickup importer; UTI is the truck and
bus importer. **Never blended**, and the same rule holds for the two UK networks.

**vehicles in service** — the fleet count used as the denominator for every per-vehicle rate. In this paper every
2025 row in that data is flagged `is_estimate`, not `is_actual`.

**write-off threshold** — the proportion of a vehicle's pre-accident value at which an insurer declares it a total
loss rather than repairing it. In Israel for vehicles up to 3.5 tonnes, 60% for a total loss and 50–55% for a
constructive total loss. See §9.

