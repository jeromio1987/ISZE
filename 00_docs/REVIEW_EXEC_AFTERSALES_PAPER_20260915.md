# Critical review — ISZE Exec Aftersales Paper (opportunity & commercialisation lens)

> **Corrections applied 2026-09-16 — read these before quoting any figure below.**
> Two figures in this review were wrong and are corrected in place, marked `[corrected 2026-09-16]`.
>
> 1. **The flat-rate placeholder is 8 markets, not 9, and holds 37.0% of the ceiling, not 37.3%.** Re-derived
>    from `01_data/00_derived/wallet_waterfall.csv` (CY2025 `theoretical_wallet_eur ÷ uio_units`): exactly
>    **8** of 18 markets sit at €250.00 per truck — IUK, UMI, Sweden, Norway, Hungary, Finland, Romania,
>    Iceland — totalling **€22,278,000 of €60,217,570 = 37.0%**. The review's §1 and §3.3 listed **Denmark**
>    as the ninth. Denmark is **€250.57 per truck** (€213,239 ÷ 851), so it is not flat and counting it in
>    overstated both the count and the euro (the review printed €22.49M). The old **37.3%** is what nine
>    markets would give; eight gives 37.0%.
> 2. **Germany and Belgium are the other way round in §3.7 and §4.5.** From `gps_spu_by_distributor.csv`
>    2025 `total_sales_eur`: Germany **€2,535,932**, Belgium **€2,109,332**. The review printed Germany
>    €2.54M and Belgium €2.11M, swapped. The combined **€6.36M** and the **75.1%** target are correct.
> 3. **The 54.4% coverage figure was correct at the time of review.** A fifth dealer-level file for
>    Portugal landed 2026-09-15 08:43, after the paper was built, so the measured coverage would rise on
>    a rebuild. That is a state change, not an error.
>
> The exec paper's builder now derives the placeholder count and share from the CSV at build time, so this
> class of error cannot be typed back in. The published HTML still carries the old wording until it is rebuilt.

**Artifact reviewed:** `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Exec_Aftersales_Paper.html` (274,327 bytes, built 2026-09-15 07:02)
**Brief it was written against:** `00_docs/PROMPT_ISZE_EXEC_SALES_PAPER.md`
**Review date:** 2026-09-15 · **Reviewer stance:** ISZE aftersales strategy / commercialisation
**Reconciliation anchor:** `01_data/00_derived/_verification_report.json` → `metrics_snapshot.json` → `FACTS.md` (verify **116 pass / 0 fail**, 2026-08-25T17:19:54Z; billing through **2026-06-30**)

**Rules / hooks updated from this review (same day):**  
`.cursor/rules/isze-exec-aftersales-paper.mdc` · `02_dashboards/_build/verify_exec_aftersales_paper.py` · `.cursor/hooks/exec-aftersales-*.mjs` · brief revised in `PROMPT_ISZE_EXEC_SALES_PAPER.md`. Next rebuild must pass the verify gate — HTML not re-cut in the rules-only pass.

---

## 0. Brief vs review — honest comparison

The first paper largely **obeyed the original brief**. The review holds it to a **higher commercialisation bar** the brief had not locked. That is why the rules/prompt were updated — so the next build is judged against one contract.

| Dimension | Original `PROMPT_ISZE_EXEC_SALES_PAPER.md` (pre-update) | First HTML | This review’s bar (now in prompt + rule) |
|---|---|---|---|
| Job | Grade-A aftersales **diagnostic** + SWOT | Strong diagnostic | **Opportunity + commercialisation** case |
| Scope (Phase 0 #2) | GPS, PMS, mix, pricing, IDS, tenders, UIO | Matched | + margin, warranty, telematics sized or UNKNOWN |
| Opportunity matrix | In source spine; **not** a page must-show | €18.22M computed; not ranked on a page | Must drive heroes / page 4 |
| Oil filter | ITUK **worked example** (correct) | Also became cover + 90-day lead | Method only; euro lead = clutch/brake |
| Ceiling | “Ceiling not forecast” in hover/SWOT OK | No page-1 placeholder share | Disclose flat €250 share + sensitivity |
| Gap types | Not required | One residual pool | Print substitution / under-service / catalogue |
| Margin / warranty / telematics | Not in locked scope | Absent (warranty aside only) | Quantify or UNKNOWN |
| Book B / NO_LIST | Not ranked as ready levers | Buried | Highest return-per-effort up front |
| Tenders | Portal coverage; keys done | Stale counts; no aftersales € sizing | Live feed; footprint vs parts € |

**Takeaway:** do not blame the builder for “missing” margin/telematics against the old Phase 0 lock. Blame the brief for underspecifying commercialisation — now fixed. Do blame the builder for computing the opportunity matrix and then leading with oil filter, and for a silent ceiling placeholder.

---

## 1. Executive summary

- **Verdict: the paper is a strong diagnostic and a weak opportunity case.** It is audit-grade on *what we billed against a modelled ceiling* and *where the holes are*. It is not the paper the brief asked for: it contains **no margin**, **no warranty**, **no telematics or subscription** content, and it **never uses its own best opportunity data** — a named €18.22M component gap it computed but did not put on a page. Treat it as the evidence annex to an opportunity paper, not the opportunity paper.
- **The paper leads with the wrong part.** Oil filters are its hero (page 1 tile, page 4 worked example, €2.04M UK gap). In its own quotable gap table oil filter is **€0.32M = 1.8%** of an €18.22M gap. Clutch disc (**€3.14M**), brake pad (**€2.78M**) and brake shoe (**€2.47M**) are **46%** of it. The recommended first move is a re-cut, not more analysis.
- **There is no gross margin anywhere in the paper.** The workspace already holds gross-profit data on exactly the contested part numbers: Eucon UK 2023 flags **€2.21M GP at risk** across 44 PNs, with rotor gross margin **40.8%** and brake pad kit **32.2%**. An after-sales commercialisation paper that cannot state margin cannot prioritise.
- **The 51.1% headline denominator is 37% placeholder.** **Eight** of eighteen markets are priced at a flat **€250/UIO** ceiling `[corrected 2026-09-16 — the review previously said nine; see the correction block at the top]`. Under defensible alternatives the same billed book reads **43.6%** (non-flat median €364), **40.6%** (Portugal €423) or **29.4%** (ITUK €745). Page 1 does not disclose this. That is the single largest presentational risk in the document.
- **The paper cannot see half the business.** Dealer sell-out exists for 5 of 18 GPS markets = **54.4%** of billed euro (Germany, Belgium, Portugal would take it to **75.1%**). Replenishment exceptions (**€4.17M**, €2.68M of it visible leakage) are therefore a *half-the-book* fact presented as a network operational fact. Adding three sell-out files materially changes the story.
- **The commercial levers that are actually ready are under-played.** A price revision pack covering **6,326 part numbers** and **€12.76M L12M** has been built and sitting unsigned since 2026-08-19 (no allocation ambition = no price move). The paper parks it in a SWOT cell and one 90-day ask instead of leading with it.
- **Warranty is both a distortion and an unexploited annuity.** Warranty parts are **€4.72M = 14.6%** of the CY2025 billed book, but **54% of UMI's** — the paper correctly flags the traffic-light distortion and then drops the subject. Warranty claim expense fell **€4.22M → €3.18M (-25%)** between 2024 and 2025 with no commentary.
- **Page 10 is factually stale against the live feed.** The paper prints 226 opportunities / 18 due in 14 days / 248 of 249 rows missing value / 16 of 29 national portals live. The live feed (generated 2026-09-15T04:20Z, twelve hours before the build) reads **376 / 28 / 374 of 402 / 14 portals reporting**. Fix required.

---

## 2. Strengths — what the paper does well for after-sales strategy

- **Two-lane ITUK discipline is enforced, not asserted.** Page 4 quotes the IML service-schedule lane (oil filter 35.1%, UIO 22,389, gap €2.04M) as the worked example and isolates the network-comparable lane (100% cap / 116% raw, UIO 23,068) to ranking only, with an explicit "different denominator" footnote. Page 6 repeats the warning in the table header. This is the hardest trap in the workspace and the paper does not fall into it.
- **Entity separation holds throughout.** UTI and UMI are two rows everywhere; IDS Israel is UMI only; IUK ≠ ITUK; Ireland ≠ IUK ≠ IMIE. No blended "Israel" figure appears in any hero, chart or table.
- **The UNKNOWN register is real, not decorative.** Page 11 is a first-class hole table (independent volume, list-to-pocket euro, air interval, brake factor, sell-out coverage, Apr–Jun credits, UMI warranty framing, LCV intervals, forecast G1, CIS/MIDI rows). Page 15 converts eight of them into falsifiers. A sceptic can attack the paper productively.
- **KM1 "chart-first, chart titles as sentences" brief is honoured.** 83 CSS bar-rows and 9 canvases across 16 pages; zero CDN references; print CSS with 16 `data-page` blocks; inline Chart.js — verified to paint from `file://`.
- **Number discipline is verifiable, and verifies.** I re-derived the page 3 and page 6 leagues from `gps_spu_by_distributor.csv` and `wallet_waterfall.csv`: all twelve distributor rows match to the stated precision (spend per truck €389/€322/€249/€220/€209/€197/€179/€179/€151/€139/€128/€88 and cover 124.2/40.3/32.4/86.0/56.0/66.6/71.6/71.5/60.6/54.6/51.3/35.4%). The paper is not quoting memory or a deck.
- **"What you should see" is honest.** The paper tells the reader it bills about half a modelled ceiling, that the UK-truck IML gap is €2.04M, that independent volume is unknown, and that five decisions are the bottleneck. It does not cheerlead.
- **Forbidden-vocabulary discipline is clean.** Zero occurrences of "wallet", "street", "IML v7", "Model B", "PRISM lane", "sold-to" or "SaTy" in the artifact. "Book B" appears three times, each glossed as "the price list we might change".

---

## 3. Weaknesses and gaps — evidence-based critique

### 3.1 It is an opportunity paper with no margin, no warranty and no telematics

The brief asked for opportunity identification and quantification across **parts, service, warranties, telematics, subscriptions**, with **revenue and margin**. Page-by-page, the artifact covers parts (fully), service (as capture, partially), and nothing else:

| Brief requirement | Paper coverage | Evidence |
|---|---|---|
| Parts opportunity — revenue | **Yes**, strong (pages 3, 4, 6, 8) | €29.23M residual; €18.22M component gap |
| Parts opportunity — **margin** | **None** | zero GP/margin figures in 16 pages |
| Service / workshop | **Partial** — as cover %, not as a P&L line | pages 4, 6 |
| **Warranties** | **Absent** | UMI warranty distortion on p3; no warranty page |
| **Telematics** | **Absent** | not mentioned in 16 pages |
| **Subscriptions** | **Absent** | not mentioned in 16 pages |
| Service contracts | **Absent** | not mentioned |
| TAM / SAM / SOM | **Partial** — TAM only, unnamed as such | €60.22M ceiling, no SAM/SOM framing |

The workspace does hold meaningful warranty data (`warranty_by_db_year.csv`: €3.18M claims CY2025, 14,300 claim rows; `gps_spu_by_distributor.csv` warranty-part split per distributor). It holds no telematics or subscription data at all — telematics is explicitly recorded in the roadmap as "data we do not have". The correct treatment is therefore: **quantify warranty, size telematics as a modelled option with a named data gap, and say so** — not silence.

### 3.2 The opportunity table exists but is not in the paper

`pms_opportunity_matrix.csv` carries a per-distributor × per-category TAM and gap for CY2025. I aggregated it. The paper shows none of it as a ranking. The consequence:

| Category | SAM TAM | Gap | Gap/TAM | Distributor |
|---|---:|---:|---:|---|
| Clutch disc | €3.32M | **€3.14M** | 95% | IUK (concentrated) |
| Brake pad | €4.03M | **€2.78M** | 69% | IUK, UTI, UMI |
| Brake shoe | €2.70M | **€2.47M** | 92% | IUK, BELGIUM |
| Clutch pressure plate | €2.12M | **€1.98M** | 93% | IUK |
| Blower filter | €1.78M | **€1.42M** | 80% | IUK |
| Brake rotor | €2.52M | €1.39M | 55% | IUK |
| Fuel filter | €1.58M | €1.02M | 64% | IUK, ITUK |
| Urea filter | €0.97M | €0.92M | 95% | ITUK (11.3% cover) |
| Air filter | €1.38M | €0.66M | 47% | network |
| **Oil filter** | €0.85M | **€0.32M** | 38% | — |

Three categories (clutch disc + brake pad + brake shoe) hold **€8.39M = 46%** of the €18.22M gap. Oil filter holds **1.8%**. The paper's page 4 chart ranks *categories by gap* correctly (air €736k, brake €642k, clutch €393k on the IML schedule) but its hero tile, worked example and 90-day narrative all point at filters. A director will leave the room thinking filters; the euro is in clutch and brake.

### 3.3 The "maximum ceiling" denominator is a quarter assumption

`wallet_waterfall.csv` carries an `assumption_note` on every CY2025 row, identical: *"wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age"*. **Eight** of eighteen rows sit at **exactly €250.00/UIO** (IUK, UMI, Sweden, Norway, Hungary, Finland, Romania, Iceland) = **€22.28M = 37.0% of the €60.22M ceiling** `[corrected 2026-09-16 — the review previously listed Denmark as a ninth market and printed €22.49M / 37.3%; Denmark is €250.57/UIO]`.

| Ceiling assumption for the 9 flat markets | Network ceiling | Network cover |
|---|---:|---:|
| As published (€250/UIO) | €60.2M | **51.1%** |
| Non-flat median (€364/UIO) | €70.5M | 43.6% |
| Portugal (€423/UIO) | €75.8M | 40.6% |
| ITUK (€745/UIO) | €104.7M | 29.4% |

A **€29.1M swing in the residual** and a **21.7-point swing in the headline** turn on a placeholder. The paper discloses "ceiling, not a forecast" in a hover panel and "max-spend, not a forecast" in the SWOT — but it labels page 3 "target spend per truck" and page 1 "target-spend ceiling" without ever saying that a third of it is a flat placeholder, not a per-market target. That is a presentational gap with real consequence: the €29.46M residual is the paper's central opportunity number and it inherits the assumption silently.

### 3.4 Gap type is not decomposed — and the paper's own file already does it

The paper treats the €29.46M target-spend residual as one pool. `capture_recovery_model.csv` already splits the modelled component gap by cause:

| Gap type | Value | Share | Rows | Commercial meaning |
|---|---:|---:|---:|---|
| **Substitution** | €11.40M | 49% | 91 | Volume arrives but not as our part — a price/value fight |
| **Under-service** | €9.56M | 41% | 143 | The job never happens in the dealer — a traffic/coverage fight |
| **Catalogue gap** | €2.18M | 9% | 18 | No number to sell — a data fight |

Substitution and under-service need **opposite commercial responses** (a price/value defence vs. a workshop-demand-generation programme). The paper's single residual pool cannot support either. Notably, the specific high-substitution lines are visible — UTI air filter runs **116.1% cover** while its brake pad is **7.0%**; IUK oil filter **37.7%** against oil-filter BVP availability; ITUK urea **11.3%**, brake shoe **12.0%**, clutch disc **13.7%**.

### 3.5 The "no list price" hole is invisible

`pricing_history_findings.json` carries a network figure the paper never uses: CY2025 **NO_LIST ≈ €4,955,737 = 15.08% of parts** across 251 part numbers (216 "on list, no usable price" = €4.36M; 35 "absent from list" = €0.60M). That is a directly addressable, pre-priced opportunity sitting inside the paper's own €18.22M gap — the cheapest euro on the table — and it is absent from pages 4, 8, 11 and 13.

### 3.6 Price evidence is thinner and older than the page implies

Page 8 is methodologically honest but the headline "130 unique part numbers" needs the same treatment:

- **180 scrape points** across **130 PNs** = **0.77%** of the 16,837 part numbers billed in CY2025. Billed euro on the set is **€7.47M = 22.2%** of the €33.71M CY2025 parts book — so the set is euro-relevant but not volume-representative.
- **50 of 180 points (28%) come from an undated Autodoc file** ("Autodoc min (undated file; j…"). The paper cites it in the table and calls the set "dated quotes" in the median statement.
- **21%** of points are UK, on a UK 2023 workshop survey plus an August 2026 UK shop scrape — the vintage range across the set is **2023–2026**.
- `iam_ks_price_gap.csv` implies a **median price index of 0.57** on 374 rows; the paper quotes **0.42** on the deduplicated 130-PN set. Both can be right on different sets, but the paper does not say which aggregation it used.

None of this invalidates the price finding. It does mean the paper should print the undated share and the UK/euro weight next to the 130, or a sceptic will find them.

### 3.7 Sell-out coverage is quantified as rows, not as share of book

Page 9 reports **1,595 exception rows on five distributors**. It does not report that those five distributors are **€16.74M of €30.76M billed in the 18 GPS markets = 54.4%**. Germany (**€2,535,932**), Belgium (**€2,109,332**) `[corrected 2026-09-16 — the two were swapped in this section]` and Portugal (€1.71M) = **€6.36M, 20.7 points** — a three-file exercise away from taking visibility to **75.1%**. Framing the gap as rows rather than euro makes the fix look larger than it is. A second framing error sits next to it: page 9's own sentence *"Everywhere else, 'no exception' would mean 'no file'"* is correct but loses force without the euro share. Separately, `capture_recovery_model.csv` is a **2026 model year** file; the paper implies the gap-type framing is CY2025-aligned. Label the vintage.

### 3.8 Page 10 is stale, and the tender opportunity is small

| Metric | Paper | Live feed (2026-09-15T04:20Z) |
|---|---|---|
| Opportunities | 226 | **376** |
| Due in 14 days | 18 | **28** |
| Rows missing value | 248 of 249 | **374 of 402** |
| National portals | 16 of 29 | **14 reporting** |

Twelve hours of drift, but all four figures moved in one direction and the direction matters. Beyond accuracy: the same feed already contains an after-sales sizing the paper ignores — of 376 opportunities only **11 carry a `gps_addressable_per_year_eur`**, totalling **€55,786/yr**, with **41 holding an R&M contract**. The modelled uplift from converting to R&M is **€44,692/yr** — roughly **1/48th** of the visible replenishment leakage (€2.68M). Conclusion the paper should state plainly: **the tender channel is a relationship and footprint play, not a parts-revenue play.** That is a useful finding and it is missing.

### 3.9 Forecast honesty is good; forecast evaluation is incomplete

The paper reports median **WAPE 49.4%** on 548 series and calls it "a surface, not a signed live forecast". Verified against `forecast_baseline.meta.json` (builder p5.2-v1, backtest_series 548, backtest_wape_median 49.44, models `ets/arima/naive/parc`, note: *arima = linear trend proxy, no statsmodels*). External practice says:

- 40–70% WAPE at item level for industrial/spare parts is normal, and ~50% "can be excellent" for highly intermittent demand (Umbrex; Prospeo). So 49.4% is **defensible, not alarming** — the paper slightly over-apologises.
- But WAPE alone is insufficient. Practice requires **bias (%)** alongside WAPE, **Forecast Value Added vs a naive baseline**, and linkage to **service level / fill rate / stockouts**, with targets segmented by ABC/XYZ. The model list already includes `naive`, so the comparison is computable. The paper reports none of it. Also: 548 of 636 series (**86%**) — state the denominator.

### 3.10 Account-health and defection queues are used as if calibrated

The paper's ask #5 says flags "already fire on most of the book (10 red / 6 amber of 17 distributors)" and correctly says "not a call list". Verified in `account_health.meta.json`: latest 2026-08 RED 10 / AMBER 6 / NONE 1 of 17 — **and `thresholds_calibrated: false`** with the note *"Draft thresholds. Do not treat RED as a validated KPI. Early Warning remains the sales call list."* The paper does not print the uncalibrated flag. Similarly the defection queue is **25 rows across 14 distributors, of which 9 carry zero trailing-12-month revenue** — no recoverable base — while the paper presents it as "25 active alerts". Both need the qualifier inline, not in a footnote.

### 3.11 Smaller items

- **The IML lane's own weakness is omitted.** The IML service-schedule constants assume **1.25 services/year** on filters (40,000 km ÷ 50,000 km/yr) while the network lane applies **0.5**. For the whole GPS league (163,198 UIO) that is **203,998 vs 81,599 modelled service events** — a 2.5× difference. Both lanes are footnote-flagged in the bridge document, but the paper presents 35.1% as "the standard IML signed off" without exposing that the denominator is 2.5× the network convention. This is the difference between a 35% and a 116% reading, and it deserves one sentence of honesty because it cuts the other way from the paper's argument.
- **UMI ex-warranty is flagged but not applied.** Page 3 gives UMI as "green €179, red €82 without warranty" and page 6 footnotes it. The paper declines to pick, which is right — but it also declines to say which one it would recommend the room adopt, which the brief asked for.
- **Defection and account-health sit on stale horizons.** Account health latest month is 2026-08 but its meta notes *"sales_fact billing ends 2026-03-31; mail-to-order is NULL when the 90d window sits after that"* while the paper's own as-of is 2026-06-30. Two different horizons in one document, neither reconciled.
- **CIS billed book is excluded from the league but not from the paper's scope statement.** Ukraine (€1.16M), Armenia (€0.27M), Kazakhstan (€0.16M) and Palestine (€0.03M) bill parts with no GPS parc — **€1.62M in CY2025**. The paper omits them correctly on page 3 and never totals them anywhere.

---

## 4. Opportunity assessment — quantified

All figures CY2025 unless marked. Sources are numbered at §9.

### 4.1 TAM / SAM / SOM ladder

| Layer | Value | Basis | Confidence |
|---|---:|---|---|
| **TAM** — modelled max-spend ceiling | **€60.22M** | GPS target spend/truck × UIO, 18 markets, 163,198 units | Medium — **37% of ceiling is a flat €250/UIO placeholder** |
| Billed (captured) | **€30.76M** | `sales_fact` parts, ex credit notes | High — verify green |
| Over-target distributors | €0.23M | 2 rows | High |
| **TAM residual** | **€29.23M** | ceiling − billed − over-target | Medium — inherits the ceiling |
| **SAM** — 14-category service basket | **€23.58M** | PMS expected demand × observed avg SP | High — quotable, interval-based |
| **SAM unfilled** — component gap | **€18.22M** | SAM − actual, all rows quotable | High |
| **SOM** — 36-month realistic recovery | **€1.46M – €4.55M** | 8% / 15% / 25% penetration scenarios below | Modelled |
| **SOM gross profit @ 26% blended** | **€0.38M – €1.18M** | ATD/NADA composite GP rate | Modelled — GP rate is external, not ISZE |

**SOM build (36 months, penetration of the €18.22M SAM gap):**

| Scenario | Penetration | Recovered revenue | GP @ 26% | GP @ 34% (mechanical) |
|---|---:|---:|---:|---:|
| Downside | 8% | €1.46M | €0.38M | €0.50M |
| **Base** | **15%** | **€2.73M** | **€0.71M** | €0.93M |
| Upside | 25% | €4.55M | €1.18M | €1.55M |
| Theoretical maximum | 100% | €18.22M | €4.74M | €6.19M |

Anchors for the SOM rate: no IAM volume data exists to defend a share, and three of the top gaps (clutch disc, brake shoe, clutch pressure plate) sit at **92–95% unfilled**, which is a *structural* (fitment/part-number/coverage) hole rather than a marginal share fight. 15% in 36 months is therefore ambitious-but-defensible **if** the pilot in §6 works; 8% is the honest base case for a network where sell-out visibility covers 54% of the book.

### 4.2 Component opportunity (the part the paper owns but does not use)

€18.22M gap, all quotable, ranked by euro at stake:

| Rank | Category | Gap | Concentration | First action |
|---:|---|---:|---|---|
| 1 | Clutch disc | €3.14M | IUK | Fitment/coverage audit vs IAM parts |
| 2 | Brake pad | €2.78M | IUK, UTI, UMI | Price index already 0.25–0.41 vs reference — substitution defence |
| 3 | Brake shoe | €2.47M | IUK, Belgium | Same |
| 4 | Clutch pressure plate | €1.98M | IUK | Bundle with clutch disc as a kit |
| 5 | Blower filter | €1.42M | IUK | Listing/attribution fix (low ASP, high unit) |
| 6 | Brake rotor | €1.39M | IUK | GM 40.8% on Eucon set — highest-value defended line |
| 7 | Fuel filter | €1.02M | IUK, ITUK | Already 65% on IML lane — low marginal return |
| 8 | Urea filter | €0.92M | ITUK (11.3%) | SCR parc fitment + service-interval alignment |

### 4.3 Warranty — the unexploited annuity

| Metric | CY2024 | CY2025 | Source |
|---|---:|---:|---|
| Warranty parts billed | — | **€4.72M** = **14.6%** of billed book | `gps_spu_by_distributor.csv` |
| Warranty claim expense | €4.22M | **€3.18M** (**−25%**) | `warranty_by_db_year.csv` |
| Mean parts value per claim | — | ~€222 (LCV+CV) | derived |
| UMI warranty parts | — | **€1.79M = 54% of UMI's billed book** | derived |
| UMI spend per truck | €179 incl. warranty | **€82 ex-warranty** | `gps_spu_by_distributor.csv` |

Two commercial readings the paper misses:

1. **A 25% claim-expense decline with parts bills flat is either improving quality or tightening authorisation.** Both need the same follow-up: is the decline being absorbed by dealers who then push the work into customer-pay at a lower capture? Not knowable from the current extract — a legitimate, cheap data ask.
2. **Warranty is a demand stream, not just a distortion.** 14.6% of billed euro arrives on a claim. Dealer warranty visits are the highest-frequency, highest-compliance workshop touch in the network, and they are not used as a capture channel anywhere in the paper.

External anchor for the annuity: extended-warranty / service-contract attach is thin and under-managed in truck retail — ATD data shows new-truck F&I penetration of only **11.3–11.8%** — while service, parts and body are **34.2% of dealer sales and 73.8% of dealer gross profit** ([ATD via CDK](https://www.cdkglobalheavytruck.com/insights/beyond-truck-sale-selling-other-dealership-services)). Contract attach is the mechanism that converts that gross into an annuity.

### 4.4 Telematics and subscriptions — a modelled option with a named data gap

The workspace holds **no telematics data**; `00_docs/ISZE_ROADMAP.md` records "Telematics / VIN usage as the next ask — data we do not have". The brief nonetheless asks for quantification, so size it externally and label it as external:

- Commercial-vehicle telematics: **OEM channels held 58.71% of revenue in 2025**; aftermarket retrofit growing at **15.1% CAGR**; managed services at **15.11% CAGR to 2031**; SaaS priced **USD 15–120/vehicle/month** by tier ([Mordor](https://www.mordorintelligence.com/industry-reports/commercial-vehicle-telematics-market); [IndexBox](https://www.indexbox.io/store/united-states-commercial-vehicle-telematics-market-analysis-forecast-size-trends-and-insights/)).
- Predictive-maintenance subscriptions: **USD 4.8bn globally in 2025 → USD 22.6bn by 2034 (18.8% CAGR)**; enterprise fleets >500 units pay **USD 12–38/vehicle/month** ([ResearchIntelo](https://researchintelo.com/report/telematics-based-predictive-maintenance-subscription-services-aftermarket-market)).

**Modelled on the ISZE GPS-league parc of 163,198 units** (flag: this parc is not all addressable — attach rates below are illustrative, not forecast):

| Attach rate | @ €15/unit/month | @ €20/unit/month | @ €40/unit/month |
|---|---:|---:|---:|
| 5% (8,160 units) | €1.47M/yr | €1.96M/yr | €3.92M/yr |
| 10% (16,320 units) | €2.94M/yr | €3.92M/yr | €7.83M/yr |
| 20% (32,640 units) | €5.88M/yr | €7.83M/yr | €15.67M/yr |
| 30% (48,959 units) | €8.81M/yr | €11.75M/yr | €23.50M/yr |

At a conservative 5% attach × €20, telematics is **€1.96M/yr of gross revenue — comparable to the base-case 36-month SOM from the entire component gap (€2.73M)**. That ranking is the single most important strategic finding this review adds. The paper's silence on it is its largest opportunity cost.

**Dependency, stated plainly:** this requires a data decision (VIN/connected-vehicle feed) and an IML/Isuzu Motors position on who owns the customer data. It is not a distributor-level pilot.

### 4.5 Ready-to-pull commercial levers (0–12 months, already built)

| # | Lever | Size | Status | Blocked by |
|---:|---|---:|---|---|
| 1 | **Price revision pack (Book B)** | 6,326 PNs · **€12.76M L12M** · €14.52M weighted | Built 2026-08-19, `no_alloc_run: true` | Allocation ambition (+4%/+5%/launch-only) |
| 2 | **Replenishment leakage** | **€2.68M** visible (of €4.17M exceptions) | 5 DBs only | Sell-out files |
| 3 | **No-list-price part numbers** | **€4.96M = 15.08% of parts** (251 PNs) | Ranked, unpriced | List/price governance |
| 4 | **Breakdown/defection recovery** | 16 of 25 alerts carry trailing revenue | 14 DBs flagged | Threshold calibration |
| 5 | **Warranty as a capture channel** | €4.72M flow · 14.6% of book | No programme | Data ask (see §8) |
| 6 | **Tender R&M conversion** | €55.8k/yr addressable → €44.7k uplift | 41 opportunities hold R&M | Not worth a programme |

**Book B sensitivity** (all eight are "HOLD_DEFAULT" today, so any move is net-new):

| Allocation ambition | On L12M basis | On forecast-weight basis |
|---|---:|---:|
| +3% | **€383k/yr** | €436k/yr |
| +4% | **€510k/yr** | €581k/yr |
| +5% | **€638k/yr** | €726k/yr |

A signed allocation ambition is worth roughly **€0.4–0.7M of price per year** — materially larger than the base-case 36-month component recovery, on data that is already built and validated by a green verify spine. **This is the highest return-per-unit-of-effort action available to ISZE today, and the paper ranks it fifth.**

---

## 5. Prioritized recommendations

Effort: S = ≤2 weeks, 1 analyst · M = 1–2 months, cross-functional · L = quarter+, needs IML/ITUK.

### Short term — 0 to 3 months

| # | Action | Impact | Effort | Dependencies |
|---:|---|---|---|---|
| S1 | **Fix page 10 against the live feed** (376/28/374-of-402/14 portals) and add the 11-opportunity, €55.8k/yr after-sales sizing | Removes a factual error; kills a false revenue expectation | **S** | none |
| S2 | **Correct the hero: re-cut page 1 and page 4 around the category gap** — lead with clutch disc + brake pad + brake shoe (€8.39M, 46% of gap), demote oil filter to a footnote | Reframes the entire paper onto 46% of the euro | **S** | none — data already in the matrix |
| S3 | **Disclose the ceiling assumption on page 1.** Print "37% of this ceiling is a flat €250/UIO placeholder" and show the 29.4–43.6% sensitivity band | Removes the largest presentational risk in the document | **S** | none |
| S4 | **Add a gross-margin layer** using Eucon (€2.21M GP at risk, rotor 40.8%, brake pad kit 32.2%) and label it as scraped-set evidence | Converts prioritisation from euro-billed to euro-margin | **S** | none |
| S5 | **Sign the Book B allocation ambition** (+4% / +5% / launch-only) | **€383–638k/yr** on data already validated | **S** (one decision) | Jerome + IML |
| S6 | **Print the gap-type split** (substitution €11.40M / under-service €9.56M / catalogue €2.18M) on page 4 or 11 | Separates the price fight from the coverage fight | **S** | label the 2026 model vintage |
| S7 | **Re-issue the report with warranty, telematics and service-contract sections** — an annex if the 16-page limit is binding | Makes the artifact answer the brief it was written for | **M** | telematics = external-only sizing |
| S8 | **Add the NO_LIST €4.96M / 251 PN block** to the opportunity register | Cheapest euro on the table — a data fix, not a demand fight | **S** | pricing owner |

### Mid term — 3 to 12 months

| # | Action | Impact | Effort | Dependencies |
|---:|---|---|---|---|
| M1 | **Close the sell-out gap on Germany, Belgium, Portugal** (€6.36M = 20.7 pts) | Lifts network visibility **54.4% → 75.1%**; converts replenishment from a 5-DB fact to a network fact | **M** | DB IT cooperation; the format already exists |
| M2 | **Run a brake & clutch capture pilot in IUK + Belgium** (§6) — the two markets with the largest measured gap and the least explanatory noise | Tests whether the €8.39M is addressable | **M** | M1 (Belgium sell-out), price index |
| M3 | **Segment the price response.** Publish a price-index-vs-share view for the 12 highest-billed contested PNs | Tells the room where to defend on price vs where to hold | **M** | current scrapes are 0.77% of the billed PN universe |
| M4 | **Warranty-defect and authorisation review** — explain the −25% claim expense against flat parts bills | Either releases a quality story or finds hidden customer-pay exposure | **M** | SAP claim extract; DPO route |
| M5 | **Calibrate the account-health thresholds and defection queue**, then separate "recoverable" from "zero-base" rows | Turns 10 RED / 6 AMBER and 25 alerts into a call list | **M** | P4 calibration decision; a routing fix for the stale mail window |
| M6 | **Add bias % and Forecast Value Added vs the `naive` baseline** to the forecast evaluation, with ABC/XYZ segment targets | Turns a 49.4% apology into a decision-grade measurement | **S–M** | models already include `naive` |
| M7 | **Complete OEM-peer retail coverage on a material share of billed euro** (today 0.77% of PNs / 22% of euro; 28% of points undated) | Makes the price conclusion weight-bearing | **M** | scraping route; vintage stamps |

### Long term — 12 to 36 months

| # | Action | Impact | Effort | Dependencies |
|---:|---|---|---|---|
| L1 | **Decide the connected-vehicle position.** Either build a telematics/subscription offer or state in writing that ISZE will not | €1.5–7.8M/yr gross at 5–10% attach — comparable to or larger than the whole component SOM | **L** | IML / Isuzu Motors data ownership; VIN feed |
| L2 | **Launch a service-contract / extended-warranty product with the strong distributors** (attach today ~11–12% on comparable truck retail) | Converts 14.6% warranty flow into a contracted annuity and raises parts attachment above 50% | **L** | IML underwriting; distributor sign-up |
| L3 | **Move the price system from annual books to an interval-and-index model** (list × reference sell-out × price index, monitored) | Removes the €4.96M no-list hole structurally rather than annually | **L** | L1-style data spine; MVBER compliance review (§7) |
| L4 | **Structural fitment programme** on the 92–95% unfilled categories (clutch disc, brake shoe, pressure plate, urea) | Attacks the part of the gap that is not a price fight | **L** | BVP/alternative-source catalogue; LCV chassis cutoffs |
| L5 | **Publish an external benchmark position** using IAM channel share (55–65% of EU CV replacement-parts volume) rather than an internal residual | Replaces "independent share UNKNOWN" with an industry-sourced frame the room can act on | **M–L** | third-party data subscription; **never** quote 100%−PMS |

---

## 6. Implementation roadmap and pilot design

### 6.1 Phase plan

| Phase | Window | Objective | Exit gate |
|---|---|---|---|
| **P0 — Correct the record** | Weeks 1–2 | S1–S4, S6, S8 land in the artifact | Re-issued paper; page 1 shows the placeholder share |
| **P1 — Unlock the ready levers** | Weeks 2–8 | Book B ambition signed; no-list block assigned | Signed ambition; owners named for 251 PNs |
| **P2 — Close the visibility gap** | Months 2–5 | DE/BE/PT sell-out in; network visibility ≥70% | Three files verified against billed book |
| **P3 — Pilot** | Months 3–9 | Brake & clutch capture pilot, IUK + Belgium | Pre-registered success criteria met or pilot killed |
| **P4 — Scale or stop** | Months 9–18 | Scale the pilot markets that cleared the gate | Go/no-go per market on measured lift |
| **P5 — Structural** | Months 12–36 | Connected-vehicle decision; contract product; index-based pricing | Board decision recorded either way |

### 6.2 Pilot design — brake & clutch capture, IUK + Belgium

**Hypothesis.** The measured brake/clutch gap is addressable with (a) competitive price positioning on the top billed part numbers and (b) workshop demand generation at the dealer, without a change to the parts themselves.

**Why these two markets.** Largest measured clutch/brake gaps outside the UK-truck IML frame (IUK clutch disc €1.34M, brake pad €0.81M, brake shoe €0.69M; Belgium brake shoe €0.34M) and both have a different demand structure from ITUK, so the result generalises or fails cleanly. Belgium already has the surrounding data; IUK has sell-out.

**Design.** Cluster-randomised at dealer level, 2:1 treatment:control, 12 months, staggered entry to allow seasonality control.

| Item | Value | Basis |
|---|---:|---|
| Target categories | Brake pad, brake shoe, brake disc/rotor, clutch disc, clutch pressure plate | §4.2 ranking |
| Expected volume at stake | IUK brake pad 19,113 + brake shoe 23,892 + clutch disc 9,557 units/yr; Belgium 3,820 + 4,768 + 1,907 | `pms_capture_by_db_year.csv` |
| Sample size (dealers) | **~36 treatment, ~18 control** (54 total) | See power note |
| Primary metric | **Capture rate** (total, `line_type=total`) per category per dealer-month | existing pipeline |
| Secondary metrics | Billed €/active truck (UIO); BVP share of units (quality, not a headline); replenishment exception rate; warranty claim rate | existing pipeline |
| Guardrail metrics | Price index vs reference sell-out (must not degrade); dealer net margin; customer-pay share (no demand cannibalisation); no increase in `overstock_*` exceptions | pricing + replenishment files |
| Baseline | Rolling 12 months pre-pilot per dealer | required — cohort variance is high |
| Duration | 12 months, with a pre-registered 6-month interim look | brake/clutch are ~0.5–1.0 services/yr, so a short window under-powers |

**Power note (flagged honesty).** Per-category dealer volumes are small (Belgium brake shoe = 322 units across the market in CY2025) and the capture distribution is skewed. I have **not** run a formal power calculation, because per-dealer per-month variance is not yet available in the derived layer — it must be computed from the sell-out long files before locking the sample size. The 36:18 split above is a working figure, not a validated one. **Do not open the pilot on this number.**

**Pre-registered success criteria (agreed before launch):**

| Outcome | Threshold | Decision |
|---|---|---|
| Clear win | ≥ +8 pts capture on brake pad **and** ≥ +3 pts on clutch, no price-index degradation | Scale to next 4 markets |
| Partial | ≥ +8 pts on one category family only | Scale that family only |
| Null | Within ±3 pts, CIs overlapping | **Stop.** Reclassify the gap as structural (fitment/coverage), not commercial |
| Adverse | Price index worsens or overstock exceptions rise | Stop and revert |

**KPI set to instrument before launch:** capture rate by category (total first, genuine as a second lens); billed € per active truck; BVP unit share as a quality lens only; replenishment exception count and euro; price index (shop ÷ reference sell-out); warranty claims per 100 units; dealer parts GP where available.

**Explicitly excluded from this pilot:** dealer service labour, oil and lubricants, telematics, tender/R&M conversion. One hypothesis per pilot.

---

## 7. Risk analysis and mitigation

### 7.1 Operational

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Pilot under-powered; null result misread as "no opportunity" | High | High | Pre-register the ≥8 pt threshold; compute dealer-level variance from sell-out longs **before** launching; kill/scale rules agreed in writing |
| Belgium enters without a baseline | Medium | Medium | M1 gates the pilot — no sell-out file, no baseline, no entry |
| Book B price move (S5) lands on part numbers already losing share to independent brands | Medium | High | Cross-check the 6,326 PNs against the price-index set before publishing; exclude lines where index < 0.5 |
| No-list €4.96M assigned to nobody | High | Medium | Named owner per the 251-PN list; it is the cheapest euro on the table and will otherwise stay unowned |
| Sell-out format drift across DE/BE/PT | Medium | Medium | Reuse the existing long-file schema; validate each against its billed book before use |

### 7.2 Regulatory

- **Competition / MVBER.** Regulation (EU) 461/2010, extended by 2023/822, remains in force **until 31 May 2028**; the 2026 evaluation (SWD published 25 June 2026) found the framework broadly effective with no immediate replacement adopted ([Commission review](https://competition-policy.ec.europa.eu/sectors/manufacturing-basic-industries/review-motor-vehicle-block-exemption-regulation_en), [EUR-Lex](https://eur-lex.europa.eu/EN/legal-content/summary/motor-vehicles-block-exemption-from-european-competition-law.html)). **Hardcore restrictions remain prohibited**, specifically **blocking sales to independent repairers**, restricting suppliers' sales to distributors/repairers/end users, and **preventing component branding**. *Mitigation:* any programme that ties parts discounts to service exclusivity, or that penalises dealers for selling to independents, must be reviewed against Article 5 before launch. The pricing work in S5/M3 should carry a one-line competition note. Note also the 2028 expiry creates a **review window** — a legitimate strategic reason to put the commercial position on record in 2026–2027 rather than 2029.
- **Data protection / connected vehicle.** L1 (telematics/VIN) triggers DPO involvement. The workspace already carries an open governance ask (DPO for ISZE or via IML legal) with a 2-week vs 8-week consequence. *Mitigation:* do not open a telematics build before the DPO route is named; scope the pilot to aggregate vehicle-health signals, not driver data. The 2023 SGL amendments specifically addressed **vehicle-generated data**, so this is live regulatory territory, not a formality.
- **Credit and return netting.** The parts base excludes SaTy `CR`/`RE` lines as a **documented judgment call, not an ERP-confirmed rule**. If the next SAP extract reverses it, GPS and capture both move. *Mitigation:* every externally-shared figure that depends on it should be re-derived after the next extract; the paper already flags this on page 11 and 15 — keep it.

### 7.3 Customer experience

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Price revision (Book B) raises counter price on lines where the independent offer is 60–75% below reference | High | High | Sequence by price index: defend value on the lowest-index lines, take price only where index > 0.6 |
| Capture push raises dealer workload on low-margin, low-ASP categories (blower filter, oil filter) | Medium | Medium | Prioritise by gross margin, not billed euro — rotor at 40.8% GM, not filter at ~5 EUR ASP |
| Warranty authorisation tightening (if the −25% claim expense is that) pushes cost to the truck owner | Medium | High | Resolve M4 first; do not run a capture programme on top of an unexplained warranty decline |
| Uncalibrated RED flags reach a distributor as an accusation | Medium | High | Publish the `thresholds_calibrated: false` label inline; use the sales call list until calibrated |
| Telematics offer without an OEM data position creates a customer-visible service split | Medium | Medium | L1 is a decision, not a pilot — resolve ownership before any customer-facing commitment |

---

## 8. Data needs and assumptions

### 8.1 Assumptions currently load-bearing

| Assumption | Where it lives | What it moves | Validation needed |
|---|---|---|---|
| 9 of 18 markets ceiling = flat **€250/UIO** | `wallet_waterfall.csv` `assumption_note` | Headline 51.1% → 29.4–43.6%; residual ±€29M | Per-market target spend; age-band uplift |
| Targets **flat across vehicle age** | same note | Whole TAM and residual | Age-spend curve from IML (already listed as pending) |
| Addressable = **100%** | `wallet_waterfall.csv` | Residual (structural pool currently **€0**) | Real addressability split incl. export/other-OEM |
| Filter intervals **1.25/yr** (IML) vs **0.5** (network) | `ITUK_PRISM_LANE_BRIDGE.md` | ITUK cover 35% vs 116% | IML confirmation on the network convention |
| Air-filter factor **0.5** | provisional | Air gap €0.66M and its category ranking | IML confirmation |
| UK-truck brake factor **0.4 vs 0.8** | unresolved | Brake cover on the comparable path | IML/ITUK decision |
| Credit/return exclusion is **sign-based** for Apr–Jun 2026 | `FACTS.md` flag H | GPS and capture for that quarter | SAP re-export with SaTy |
| Book B growth factors **1.24 / 1.25** unsigned | roadmap B3 | Weighted basis €14.52M vs L12M €12.76M | Sign-off |
| Blended GP **26%** | external (ATD/NADA) | Every GP figure in §4 | ISZE realised GP by category — **not in workspace** |

### 8.2 Data that would change decisions (in priority order)

| # | Data need | Unlocks | Cost |
|---:|---|---|---|
| 1 | **ISZE realised gross margin by category and part number** | The whole prioritisation: it converts €18.22M billed-gap into margin-at-stake | Medium — SAP CO-PA extract; highest value item on this list |
| 2 | **One family of independent unit counts** (oil or air, one large market) | Retires "IAM volume UNKNOWN"; converts residual from a mystery blend into a share | High — requires a third-party data subscription (e.g. the Wolk & Nikolic CV module already sized country-level IAM/OES) |
| 3 | **Dealer sell-out for Germany, Belgium, Portugal** | Network visibility 54.4% → 75.1%; makes replenishment a network fact | Medium — format exists |
| 4 | **Per-dealer per-month capture variance** (from existing sell-out longs) | Enables the pilot power calculation — **gating item for §6** | Low — derived arithmetic |
| 5 | **Warranty claim reason × parts × labour extract** | Explains the −25% claim expense; tests warranty-as-capture-channel | Medium — SAP claim extract + DPO route |
| 6 | **Age-spend curve by market** | Removes the flat-target placeholder; fixes the residual | Medium — IML |
| 7 | **Bias % and FVA vs naive on the forecast** | Turns WAPE 49.4% into a decision-grade measurement | Low — `naive` already modelled |
| 8 | **Signed list-to-pocket realisation** | Releases the pocket euro to an external audience | Decision, not data (year-matched joins already ran as validation) |
| 9 | **Price coverage on a material share of billed euro** (today 0.77% of PNs) | Makes the price conclusion weight-bearing | Medium–High — scraping route + vintage stamps |
| 10 | **Connected-vehicle / VIN feed position** | Enables or closes L1 | High — IML / Isuzu Motors |

### 8.3 Explicit non-assumptions

- **`100% − PMS` is not independent-garage share.** Residual = lost service + DIY + other-OEM + export + interval error + parc error + IAM. The paper says so; keep it.
- **Price evidence is not volume evidence.** Scrapes are price only; the paper says so and must keep saying so.
- **UTI and UMI are never blended.** Neither are IUK and ITUK.
- **No telematics, subscription or service-contract data exists in the workspace.** Any figure in §4.4 is externally sourced and labelled as such — it must never be merged into an internal KPI.

---

## 9. Sources and references

**Internal (all under `C:\Users\jerom\Desktop\claude\ISZE\`)**

1. `02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html` — artifact reviewed (16 pages, 83 bar-rows, 9 canvases, no CDN)
2. `00_docs/PROMPT_ISZE_EXEC_SALES_PAPER.md` — the brief
3. `01_data/00_derived/_verification_report.json` — 116 pass / 0 fail, 2026-08-25T17:19:54Z
4. `01_data/00_derived/metrics_snapshot.json` — headline figures
5. `FACTS.md` — §1 IML lane, §1b network lane, §4 revenue base, open integrity flags
6. `00_docs/ITUK_PRISM_LANE_BRIDGE.md` — two-lane bridge, UIO 22,389 vs 23,068
7. `01_data/00_derived/wallet_waterfall.csv` — ceiling, captured, over-target, `assumption_note`
8. `01_data/00_derived/pms_opportunity_matrix.csv` — per-DB × category TAM and gap
9. `01_data/00_derived/pms_summary_by_db.csv` — per-DB capture and gap league
10. `01_data/00_derived/capture_recovery_model.csv` — substitution / under-service / catalogue split
11. `01_data/00_derived/gps_spu_by_distributor.csv` — spend per truck, warranty split
12. `01_data/00_derived/warranty_by_db_year.csv` — claim expense by year, DB, segment
13. `01_data/00_derived/replenishment_exceptions_cy2025.csv` — 1,595 rows, €4.17M
14. `01_data/00_derived/book_b_bucket_summary.csv` + `revision_book_b_pack.meta.json` — 6,326 PNs, €12.76M L12M, no alloc run
15. `01_data/00_derived/eucon_price_gap.csv` — €2.21M GP at risk, rotor 40.8% GM
16. `02_dashboards/pricing/pricing_history_findings.json` + `pricing_full_analysis_pack.json` — NO_LIST €4.96M / 251 PNs, realization 96.29%
17. `01_data/14_dashboards/tender_data.json` — live feed, 2026-09-15T04:20Z
18. `01_data/17_interactions/account_health.meta.json` — `thresholds_calibrated: false`, 10 RED / 6 AMBER
19. `01_data/00_derived/forecast_baseline.meta.json` — WAPE 49.44, 548 of 636 series
20. `01_data/00_derived/ids_dealer_network.csv` — 519 rows, 20 country tabs, Israel LCV mean 60.9
21. `00_docs/ISZE_ROADMAP.md` §2 — open decisions; §5 do-not-reopen
22. `03_analytics/Isuzu/prism/docs/metric_dictionary.md` — PMS / BVP / GPS definitions

**External**

23. Frost & Sullivan, *Growth Opportunities for the 2026 Medium- and Heavy-Duty Commercial Vehicle Aftermarket* — global MD/HD aftermarket USD 167.01bn 2026; Europe ~6.3% growth — https://store.frost.com/growth-opportunities-for-the-2026-medium-and-heavy-duty-commercial-vehicle-aftermarket.html
24. IndexBox, *Commercial Vehicles and Coach Market in the European Union* — aftermarket/service parts 45–55% of market value; IAM 55–65% of replacement-parts volume; EU CV parc >30m units — https://www.indexbox.io/store/european-union-commercial-vehicles-and-coach-market-analysis-forecast-size-trends-and-insights/
25. Wolk & Nikolic, *Commercial Vehicles Aftermarket in Europe* — ~22,200 CV workshops; brand-affiliated 34%; OEM parts share in CV IAM relatively high vs passenger car — https://wolk-aftersales.com/commercial-vehicles-aftermarket-in-europe-navigating-through-consolidation-and-change/
26. ATD / NADA composites via CDK Global — service/parts/body 34.2% of sales, 73.8% of gross profit; F&I penetration 11.8%; service+parts GP 37.6% — https://www.cdkglobalheavytruck.com/insights/beyond-truck-sale-selling-other-dealership-services
27. Pulse RevOps, heavy-truck dealer KPIs — parts GP 28–34% mechanical, 18–24% commodity; absorption benchmarks; F&I penetration 11.3% (2020 ATD) — https://pulserevops.com/industry-kpis/ik0041 and https://www.truckpartsandservice.com/business/finance/article/15290551/importance-of-improving-fi-penetration-for-equipment-sales
28. Umbrex, *Demand Forecast Accuracy Guide* — industrial spares item-customer weekly WAPE 40–70%; bias and FVA vs naive required alongside WAPE — https://umbrex.com/resources/company-analysis/supply-chain-logistics/demand-forecast-accuracy/
29. Prospeo, *Forecast Accuracy Metrics: 2026 Practitioner Guide* — spare parts 40–60%+ WMAPE; ~50% can be excellent for intermittent demand — https://prospeo.io/s/forecast-accuracy-metrics
30. Mordor Intelligence, *Commercial Vehicle Telematics Market* — OEM channels 58.71% of 2025 revenue; aftermarket retrofit 15.1% CAGR; managed services 15.11% CAGR to 2031 — https://www.mordorintelligence.com/industry-reports/commercial-vehicle-telematics-market
31. IndexBox, *US Commercial Vehicle Telematics Market* — SaaS USD 15–120/vehicle/month by tier — https://www.indexbox.io/store/united-states-commercial-vehicle-telematics-market-analysis-forecast-size-trends-and-insights/
32. ResearchIntelo, *Telematics-Based Predictive Maintenance Subscription Services Aftermarket* — USD 4.8bn 2025 → USD 22.6bn 2034 (18.8% CAGR); enterprise fleets USD 12–38/vehicle/month — https://researchintelo.com/report/telematics-based-predictive-maintenance-subscription-services-aftermarket-market
33. European Commission, *Review of the Motor Vehicle Block Exemption Regulation* — Reg 461/2010 in force to 31 May 2028; 2026 evaluation published 25 June 2026; Article 5 hardcore restrictions incl. sales to independent repairers and component branding — https://competition-policy.ec.europa.eu/sectors/manufacturing-basic-industries/review-motor-vehicle-block-exemption-regulation_en
34. EUR-Lex, *Motor vehicles — block exemption* — Reg 2023/822 extension; vehicle-generated data addressed in the 2023 SGL amendments — https://eur-lex.europa.eu/EN/legal-content/summary/motor-vehicles-block-exemption-from-european-competition-law.html

---

*Review prepared 2026-09-15. All internal figures reconciled to the green verify spine of 2026-08-25. Every derived calculation in §4 is reproducible from the named CSV; the two external-sourced blocks (telematics/subscription sizing, blended gross-margin rates) are labelled as external and must not be merged into an internal KPI.*
