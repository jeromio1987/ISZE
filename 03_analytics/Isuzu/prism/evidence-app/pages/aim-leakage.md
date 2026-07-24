---
title: PRISM — AIM & BVP Leakage
---

Where genuine loses — by distributor, family and order type. Fifteen boards off the AIM classifier, the genuine↔BVP crossref, and the order-type (saty) split. [← back to Offset Insights](/) · [BI Gallery](/bi-gallery)

<Alert status=warning>
<b>BVP is Isuzu's own "Best Value Parts" line</b> — a budget OEM range (Isuzu-format PNs), <i>not</i> third-party aftermarket. So "genuine vs BVP" below is internal cannibalisation of premium genuine by our own value brand, not loss to a rival. (The named external aftermarket comparison lives in Section D, the Eucon/AutoDoc probe.)

<b>Read the leakage honestly.</b> The AIM scraper flags only <b>~1.0% (€313K)</b> of 2025 revenue as direct aftermarket "high-risk", and it matches ~100% of revenue — so the scraper alone is <b>not</b> the leak story. The real battleground is the <b>contested arena</b>: €3.55M of revenue where a genuine <i>and</i> a BVP equivalent both sell, of which <b>BVP already takes 36% network-wide — up to 92% at some distributors.</b> "High-risk" and "contested" are derived from invoicing + the genuine↔BVP crossref; nothing here is attributed to a named competitor.
</Alert>

```sql arena
select
  sum(genuine_only_eur)::double as genuine_only,
  sum(contested_eur)::double as contested,
  sum(bvp_eur)::double as bvp,
  (sum(bvp_eur)/nullif(sum(contested_eur),0))::double as bvp_capture_of_contested,
  (sum(contested_eur)/nullif(sum(total_eur),0))::double as contested_share
from prism.db_mix where year=(select max(year) from prism.db_mix)
```

<BigValue data={arena} value=contested fmt=eur0 title="Contested revenue (genuine vs BVP)" />
<BigValue data={arena} value=bvp_capture_of_contested fmt=pct0 title="BVP's share of the contested arena" />
<BigValue data={arena} value=bvp fmt=eur0 title="BVP revenue (retained at value tier)" />

---

## A · The contested battlefield — genuine vs BVP

### 1 · The arena: genuine-only vs contested vs BVP (network)

97% of revenue is uncontested genuine. The fight is in the thin contested slice — that's where the leverage is.

```sql arena_split
select 'Genuine — uncontested' as bucket, sum(genuine_only_eur)::double as eur from prism.db_mix where year=(select max(year) from prism.db_mix)
union all select 'Genuine — contested', sum(genuine_contested_eur)::double from prism.db_mix where year=(select max(year) from prism.db_mix)
union all select 'BVP — Isuzu own value line', sum(bvp_eur)::double from prism.db_mix where year=(select max(year) from prism.db_mix)
```

<BarChart data={arena_split} x=bucket y=eur yFmt=eur0 swapXY=true />

### 2 · Where contested money is lost — by distributor

Bubble = total revenue. Top-right = lots of contested money **and** losing most of it to BVP. That's the fix-first corner.

```sql contested_db
select distributor_code,
  contested_eur::double as contested_eur,
  contested_bvp_capture::double as bvp_capture,
  total_eur::double as total_eur
from prism.db_mix
where year=(select max(year) from prism.db_mix) and contested_eur > 20000
```

<BubbleChart data={contested_db} x=contested_eur y=bvp_capture size=total_eur series=distributor_code
  xFmt=eur0 yFmt=pct0 xAxisTitle="Contested revenue (€)" yAxisTitle="BVP capture of contested" />

### 3 · BVP capture of contested demand — ranked

Where a genuine equivalent exists, this is the share BVP still wins. UTI and Kazakhstan give away >90% of the contested money.

```sql capture_rank
select distributor_code, contested_bvp_capture::double as bvp_capture, contested_eur::double as contested_eur
from prism.db_mix
where year=(select max(year) from prism.db_mix) and contested_eur > 20000
order by bvp_capture desc
```

<BarChart data={capture_rank} x=distributor_code y=bvp_capture yFmt=pct0 swapXY=true xAxisTitle="BVP capture of contested demand" />

### 4 · BVP share of total revenue — by distributor

```sql bvp_pct_db
select distributor_code, bvp_pct::double as bvp_pct
from prism.db_mix
where year=(select max(year) from prism.db_mix)
order by bvp_pct desc
```

<BarChart data={bvp_pct_db} x=distributor_code y=bvp_pct yFmt=pct1 swapXY=true xAxisTitle="BVP % of revenue" />

### 5 · Where BVP eats — top subgroups

Subgroups with the most BVP revenue and the unit share BVP holds there. The product-side target list.

```sql subs_sub
select product_subgroup,
  sum(bvp_eur)::double as bvp_eur,
  (sum(bvp_qty)::double / nullif(sum(genuine_qty)+sum(bvp_qty),0)) as bvp_unit_share
from prism.substitution_db
where year=(select max(year) from prism.substitution_db)
group by 1
having sum(bvp_eur) > 0
order by bvp_eur desc limit 15
```

<BarChart data={subs_sub} x=product_subgroup y=bvp_eur yFmt=eur0 swapXY=true />

---

## B · AIM scraper — exposure & blind spots

### 6 · AIM high-risk revenue € — by distributor

The scraper's direct aftermarket-risk flag. Small in absolute terms (€313K network) — IUK and Germany carry the most.

```sql hr_eur
select distributor_code, high_risk_rev_eur::double as high_risk_rev_eur
from prism.aim_exposure
where year=(select max(year) from prism.aim_exposure)
order by high_risk_rev_eur desc
```

<BarChart data={hr_eur} x=distributor_code y=high_risk_rev_eur yFmt=eur0 swapXY=true />

### 7 · AIM high-risk % of revenue — by distributor

```sql hr_pct
select distributor_code, high_risk_rev_pct::double as high_risk_rev_pct
from prism.aim_exposure
where year=(select max(year) from prism.aim_exposure) and high_risk_rev_pct is not null
order by high_risk_rev_pct desc
```

<BarChart data={hr_pct} x=distributor_code y=high_risk_rev_pct yFmt=pct1 swapXY=true xAxisTitle="High-risk % of revenue" />

### 8 · Scraper coverage — effectively complete

Coverage is **not** the leak. The classifier matches **99.9%+ of revenue at every distributor** — there is no blind-spot story at the revenue level. The leak is contested price (Section A), not parts the scraper can't see. Below: network match rate, and the only thing that varies — the tiny absolute unmatched € by distributor.

```sql match_net
select
  (sum(aim_matched_rev_eur)/nullif(sum(net_sales_eur),0))::double as net_match_rate,
  sum(net_sales_eur - aim_matched_rev_eur)::double as unmatched_eur
from prism.aim_exposure
where year=(select max(year) from prism.aim_exposure)
```

<BigValue data={match_net} value=net_match_rate fmt=pct1 title="Network AIM match rate (revenue)" />
<BigValue data={match_net} value=unmatched_eur fmt=eur0 title="Total unmatched revenue (network)" />

```sql unmatched_db
select distributor_code,
  (net_sales_eur - aim_matched_rev_eur)::double as unmatched_eur
from prism.aim_exposure
where year=(select max(year) from prism.aim_exposure)
  and (net_sales_eur - aim_matched_rev_eur) > 0
order by unmatched_eur desc
limit 12
```

<BarChart data={unmatched_db} x=distributor_code y=unmatched_eur yFmt=eur0 swapXY=true xAxisTitle="Unmatched revenue (€)" />

### 9 · The blind spot — unclassified revenue, by suggested class

€1.45M of revenue-bearing parts the scraper couldn't classify. This is where the gap-closer's suggested L1 would route them.

```sql gap_l1
select coalesce(sug1_l1,'(no suggestion)') as suggested_l1,
  sum(revenue_cy25_eur)::double as revenue_eur,
  count(*)::double as parts
from prism.gap_suggestions
group by 1 order by revenue_eur desc limit 12
```

<BarChart data={gap_l1} x=suggested_l1 y=revenue_eur yFmt=eur0 swapXY=true />

### 10 · Top-20 unclassified leak parts

The biggest revenue parts AIM can't yet place — manual review priority.

```sql gap_parts
select pn, description, revenue_cy25_eur::double as revenue_eur
from prism.gap_top50
order by revenue_eur desc limit 20
```

<DataTable data={gap_parts} rows=20>
  <Column id=pn title="Part" />
  <Column id=description title="Description" />
  <Column id=revenue_eur title="CY25 revenue" fmt=eur0 />
</DataTable>

---

## C · Order-type (saty) — urgency as a leakage proxy

### 11 · Network revenue by order type (saty)

Stock orders (SOR) are healthy; VOR + RUSH are €20M+ of expedited demand — every urgent line is a stocking miss that invites an aftermarket alternative.

```sql saty_rev
select saty, revenue_eur::double as revenue_eur, line_count::double as line_count
from prism.saty_mix
order by revenue_eur desc
```

<BarChart data={saty_rev} x=saty y=revenue_eur yFmt=eur0 swapXY=true />

### 12 · VOR + urgent share of lines — by distributor vs network

```sql vor_share
select distributor_code,
  sum(case when order_type in ('vor','urgent') then pct_of_total_lines else 0 end)::double as urgent_share
from prism.vor_profile
where year=(select max(year) from prism.vor_profile)
group by 1
order by urgent_share desc
```

<BarChart data={vor_share} x=distributor_code y=urgent_share yFmt=pct0 swapXY=true xAxisTitle="VOR + urgent share of lines" />

### 13 · Order-type mix by distributor (stacked)

Standard vs urgent vs VOR, by distributor. A tall urgent/VOR stack = a network running on emergencies.

```sql saty_db
select distributor_code, order_type, sum(pct_of_total_lines)::double as share
from prism.vor_profile
where year=(select max(year) from prism.vor_profile)
group by 1,2
```

<BarChart data={saty_db} x=distributor_code y=share series=order_type type=stacked yFmt=pct0 swapXY=true />

### 14 · AIM family risk matrix

By family: BVP revenue (x) vs the AIM high-risk share (y), bubble = genuine € at stake. Top-right defends first.

```sql fam_risk
select product_family,
  sum(bvp_eur)::double as bvp_eur,
  (sum(aim_high_risk_rev_eur)::double / nullif(sum(genuine_eur)+sum(bvp_eur),0)) as risk_pct,
  sum(genuine_eur)::double as genuine_eur
from prism.bvp_family_risk
where year=(select max(year) from prism.bvp_family_risk)
group by 1 having sum(genuine_eur)+sum(bvp_eur) > 0
```

<BubbleChart data={fam_risk} x=bvp_eur y=risk_pct size=genuine_eur series=product_family
  xFmt=eur0 yFmt=pct1 xAxisTitle="BVP revenue (€)" yAxisTitle="AIM high-risk share" />

### 15 · Leakage priority quadrant — the so-what board

Every distributor on one map: contested money at stake (x) × how badly BVP is winning it (y), sized by total revenue. **Top-right = biggest, most-losing — fix these first.**

```sql priority
select distributor_code,
  contested_eur::double as contested_eur,
  contested_bvp_capture::double as bvp_capture,
  total_eur::double as total_eur,
  bvp_eur::double as bvp_eur
from prism.db_mix
where year=(select max(year) from prism.db_mix) and contested_eur > 10000
```

<BubbleChart data={priority} x=contested_eur y=bvp_capture size=bvp_eur series=distributor_code
  xFmt=eur0 yFmt=pct0 xAxisTitle="Contested revenue at stake (€)" yAxisTitle="BVP capture of contested" />

---

## C+ · The down-trade truth — BVP is retained margin, not lost €

<Alert status=info>
<b>Two different threats, never to be added together.</b> <b>BVP capture is INTERNAL down-trade</b> — the customer still buys from ISZE, just one tier down, so we keep the sale at BVP margin. The only real cost is the <b>GP delta</b> per unit (genuine GP/unit − BVP GP/unit). <b>The EXTERNAL walk-out</b> (Section D, named aftermarket brands undercutting) is the genuine-€-out-the-door risk. Sections A–C count BVP <i>revenue</i>; this section converts it to <b>profit actually eroded</b>.
</Alert>

On the contested PMS pairs that match into CY25 sell-in (genuine↔BVP crossref, SOrg IE40), BVP earns **healthy margin** — so the down-trade is far less painful than the revenue-share headline implies, and on **oil filters it is margin-*accretive*** (BVP GP/unit > genuine).

```sql downtrade
select
  sum(rev_bvp)::double as bvp_rev_retained,
  sum(gp_bvp)::double as bvp_gp_retained,
  sum(downtrade_gp_gap_eur)::double as downtrade_gp_gap
from prism.bvp_downtrade
```

<BigValue data={downtrade} value=bvp_rev_retained fmt=eur0 title="BVP revenue — retained (not lost)" />
<BigValue data={downtrade} value=bvp_gp_retained fmt=eur0 title="BVP gross profit — retained" />
<BigValue data={downtrade} value=downtrade_gp_gap fmt=eur0 title="Real down-trade GP gap (the only true cost)" />

_The GP gap assumes 1:1 unit substitution genuine↔BVP and covers only the 7 PMS categories where both sides match into CY25 (≈€0.93M of BVP revenue) — a floor, not the whole contested arena. It is dwarfed by the €2.21M external GP-at-risk in Section D._

### 15b · Down-trade GP gap by category — where down-trading actually costs margin

Bar = the genuine-minus-BVP gross-profit delta on the BVP units. **Negative = down-trading earns *more* margin than genuine** (oil filters). Positive = genuine margin genuinely forgone.

```sql downtrade_cat
select pms_category,
  downtrade_gp_gap_eur::double as gap,
  genuine_gp_per_unit::double as gen_gpu,
  bvp_gp_per_unit::double as bvp_gpu
from prism.bvp_downtrade
order by downtrade_gp_gap_eur desc
```

<BarChart data={downtrade_cat} x=pms_category y=gap yFmt=eur0 swapXY=true xAxisTitle="Genuine − BVP GP on down-traded units (€)" />

<DataTable data={downtrade_cat} rows=10>
  <Column id=pms_category title="PMS category" />
  <Column id=gen_gpu title="Genuine GP/unit €" fmt=eur2 />
  <Column id=bvp_gpu title="BVP GP/unit €" fmt=eur2 />
  <Column id=gap title="Down-trade GP gap €" fmt=eur0 contentType=colorscale />
</DataTable>

---

## D · The price layer — Eucon / AutoDoc aftermarket benchmark

Sections A–C show *where* genuine loses share. This section adds the missing dimension: **the actual price gap** to named aftermarket brands, from the Eucon + AutoDoc scrape (`eucon_pricing.xlsx` → `eucon_price_gap.csv`).

<Alert status=info>
<b>Coverage — read it straight.</b> Eucon benchmarks only <b>44 Isuzu PNs</b>. But those 44 are real volume: <b>€12.9M = 13.3% of 3-yr network revenue</b>, all sold. Of them — <b>25 PNs (€6.2M)</b> the aftermarket sells <i>cheaper</i> than ISZE genuine; <b>10</b> are the genuine side of a contested (BVP-equivalent) pair; and <b>8 PNs (€2.33M)</b> are <i>both</i> contested <b>and</b> price-undercut. Everything below is limited to these 44 benchmarked PNs; it is a price <i>probe</i>, not full network coverage. Delta is the aftermarket avg vs ISZE IE40 list: <b>negative = competitor cheaper</b>. <b>Two margin layers.</b> <b>ISZE GP%</b> is actual CY25 sell-in margin (EUR Amount − EUR Cost, <code>Sales CY25.XLSX</code>, SOrg IE40 = ISZE→distributor, 42/44 PNs matched). <b>Dealer GP</b> is a flat <b>27% assumption</b> (your input, not measured) for the downstream dealer margin — the profit the <i>dealer</i> loses when they switch to aftermarket. Loss is measured in <i>gross profit</i> at both levels, not just revenue.
</Alert>

```sql gap_kpi
select
  count(*)::double as benchmarked_pns,
  sum(rev_eur)::double as rev_covered,
  sum(case when isze_exposed then rev_eur else 0 end)::double as exposed_rev,
  sum(coalesce(gp_at_risk_eur,0))::double as gp_at_risk,
  sum(case when isze_exposed then rev_eur*0.27 else 0 end)::double as dealer_gp_at_risk,
  sum(case when contested and isze_exposed then coalesce(gp_at_risk_eur,0) else 0 end)::double as dj_gp_at_risk
from prism.eucon_gap
```

<BigValue data={gap_kpi} value=rev_covered fmt=eur0 title="Revenue on benchmarked parts (44 PNs)" />
<BigValue data={gap_kpi} value=gp_at_risk fmt=eur0 title="ISZE GP at risk (25 undercut PNs)" />
<BigValue data={gap_kpi} value=dealer_gp_at_risk fmt=eur0 title="Dealer GP at risk (27% assumed)" />

### 16 · Price position map — revenue vs the gap to aftermarket

x = our revenue on the part, y = aftermarket avg price vs ISZE (negative = they're cheaper), bubble = revenue. **Bottom-right = big money where the aftermarket badly undercuts us. Reprice or defend first.**

```sql price_map
select pn, description,
  rev_eur::double as rev_eur,
  Avg_Delta_pct::double as avg_delta,
  case when contested then 'Contested (BVP pair)' else 'No BVP pair' end as arena
from prism.eucon_gap
where Avg_Delta_pct <= 1.0
```

<BubbleChart data={price_map} x=rev_eur y=avg_delta size=rev_eur series=arena
  yMin=-1 yMax=1
  xFmt=eur0 yFmt=pct0 xAxisTitle="ISZE revenue on part (€)" yAxisTitle="Aftermarket avg vs ISZE (− = they're cheaper)" />

_Two low-revenue outliers are excluded (+250% and +560% — genuine far cheaper than aftermarket, but tiny volume). Axis clipped to ±100% so the real spread is readable._

### 17 · Where the aftermarket undercuts us most — ranked

The 25 PNs where a named aftermarket brand sells cheaper than ISZE genuine. Bar = how far below us the aftermarket average sits.

```sql undercut
select pn || ' · ' || coalesce(description,'') as part,
  Avg_Delta_pct::double as avg_delta,
  rev_eur::double as rev_eur
from prism.eucon_gap
where isze_exposed
order by avg_delta asc
```

<BarChart data={undercut} x=part y=avg_delta yFmt=pct0 swapXY=true xAxisTitle="Aftermarket avg vs ISZE (− = cheaper)" />

### 18 · Double jeopardy — contested AND undercut on price

The worst quadrant: genuine parts that have a BVP equivalent selling **and** the aftermarket is cheaper. €2.33M revenue / **€890K gross profit** at risk — losing share to a part that also wins on price. Defend list, ranked by GP at risk (the money that actually walks).

```sql double_jeopardy
select pn, description,
  rev_eur::double as rev_eur,
  gp_pct::double as gp_pct,
  gp_at_risk_eur::double as gp_at_risk,
  (rev_eur*0.27)::double as dealer_gp,
  ISZE_IE40_Price_EUR::double as isze_price,
  Avg_Competitor_EUR::double as aftermarket_avg,
  Avg_Delta_pct::double as avg_delta,
  Brands_Found as brands
from prism.eucon_gap
where contested and isze_exposed
order by gp_at_risk desc
```

<DataTable data={double_jeopardy} rows=10>
  <Column id=pn title="Part" />
  <Column id=description title="Description" />
  <Column id=rev_eur title="ISZE rev" fmt=eur0 />
  <Column id=gp_pct title="ISZE GP%" fmt=pct0 />
  <Column id=gp_at_risk title="ISZE GP at risk" fmt=eur0 />
  <Column id=dealer_gp title="Dealer GP (27%)" fmt=eur0 />
  <Column id=isze_price title="ISZE €" fmt=eur2 />
  <Column id=aftermarket_avg title="AM avg €" fmt=eur2 />
  <Column id=avg_delta title="Δ vs ISZE" fmt=pct0 />
  <Column id=brands title="Brands seen" wrap=true />
</DataTable>

### 18b · Margin-weighted defend priority — GP at risk, ranked

Revenue exposure is the wrong sort key when margins differ 8%→61%. This ranks all 25 undercut parts by **gross profit at risk** (revenue × CY25 GP%). High bar + deep undercut = defend first; a deeply undercut low-margin part may not be worth fighting.

```sql gp_risk
select pn || ' · ' || coalesce(description,'') as part,
  gp_at_risk_eur::double as gp_at_risk,
  Avg_Delta_pct::double as avg_delta
from prism.eucon_gap
where isze_exposed and gp_at_risk_eur is not null
order by gp_at_risk desc
```

<BarChart data={gp_risk} x=part y=gp_at_risk yFmt=eur0 swapXY=true xAxisTitle="Gross profit at risk (€)" />

### 19 · Counter-narrative — where genuine already wins on price

Not all bad news: on **19 of the 44** benchmarked PNs, ISZE genuine is *cheaper* than the aftermarket average. These are parts to push hard — price is on our side.

```sql genuine_wins
select pn || ' · ' || coalesce(description,'') as part,
  Avg_Delta_pct::double as avg_delta,
  rev_eur::double as rev_eur
from prism.eucon_gap
where Avg_Delta_pct > 0
order by avg_delta desc
limit 15
```

<BarChart data={genuine_wins} x=part y=avg_delta yFmt=pct0 swapXY=true xAxisTitle="Aftermarket avg vs ISZE (+ = genuine cheaper)" />

### 20 · Full benchmarked-parts table

All 44 Eucon-benchmarked PNs with revenue, price position, competitor count and brands. The raw probe.

<Alert status=info>
<b>Apples-to-apples:</b> our <code>ISZE €</code> is the <b>IE40 list price to the distributor</b> — not what the customer pays. To compare against aftermarket at the counter we gross it up through the channel: <b>distributor +40%</b>, then <b>dealer +27.5%</b> (street = list × 1.40 × 1.275 = <b>×1.785</b>). The <b>Δ</b> column is aftermarket avg vs that <b>street genuine</b> price — negative = aftermarket undercuts genuine at the counter. AM = Eucon aftermarket trade benchmark.
</Alert>

```sql gap_full
select pn, description,
  rev_eur::double as rev_eur,
  ISZE_IE40_Price_EUR::double as isze_price,
  (ISZE_IE40_Price_EUR * 1.40)::double as db_price,
  (ISZE_IE40_Price_EUR * 1.40 * 1.275)::double as street_price,
  Min_Competitor_EUR::double as am_min,
  Avg_Competitor_EUR::double as am_avg,
  ((Avg_Competitor_EUR - ISZE_IE40_Price_EUR * 1.40 * 1.275)
     / nullif(ISZE_IE40_Price_EUR * 1.40 * 1.275, 0))::double as delta_vs_street,
  Competitor_Count::double as n_offers,
  case when contested then 'Y' else '' end as contested
from prism.eucon_gap
order by rev_eur desc
```

<DataTable data={gap_full} rows=15 rowShading=true>
  <Column id=pn title="Part" />
  <Column id=description title="Description" />
  <Column id=rev_eur title="ISZE rev" fmt=eur0 />
  <Column id=isze_price title="ISZE list €" fmt=eur2 />
  <Column id=db_price title="+DB 40% €" fmt=eur2 />
  <Column id=street_price title="+DLR 27.5% (street) €" fmt=eur2 />
  <Column id=am_avg title="AM avg €" fmt=eur2 />
  <Column id=delta_vs_street title="Δ AM vs street" fmt=pct0 contentType=delta />
  <Column id=n_offers title="# offers" />
  <Column id=contested title="Contested" />
</DataTable>

---

## E · Tender / R&M channel — opportunity pipeline

The fourth leakage channel is fleet tender & R&M contracts (parts bundled into maintenance deals, priced outside list). **520 scored public-tender opportunities** are live in the pipeline — every one carries a decision, fit/win/econ scores, a suggested owner and parts/R&M signal.

```sql tender_head
select count(*)::double as total,
  sum(case when actionable then 1 else 0 end)::double as actionable,
  (sum(case when parts_signal then 1 else 0 end)::double / count(*)) as parts_share,
  (sum(case when rm_contract then 1 else 0 end)::double / count(*)) as rm_share
from prism.tender_pipeline
```

<Grid cols=4>
  <BigValue data={tender_head} value=total title="📋 Opportunities" />
  <BigValue data={tender_head} value=actionable title="🎯 Actionable (Attack/Selective/Watch)" />
  <BigValue data={tender_head} value=parts_share fmt=pct0 title="🔩 Carry parts signal" />
  <BigValue data={tender_head} value=rm_share fmt=pct0 title="🔧 R&M contract" />
</Grid>

<Alert status=info>
This is a <b>qualified-pipeline</b> view — counts and scores are real for every row. <b>Value is present on only 12 of 520</b> opportunities and deadlines on 55, so we deliberately do <b>not</b> chart € pipeline or award prices. Awarded line items (the <code>tenders_output.xlsx</code> sheet) are still empty; when they land, win/loss-vs-aftermarket pricing slots on top of this.
</Alert>

### E1 · Qualification funnel

How the 520 sort out after scoring — most are noise, the work is the Attack + Selective band.

```sql tender_decision
select decision, count(*)::double as opps
from prism.tender_pipeline
group by 1
order by array_position(['Attack','Selective','Watch','Ignore'], decision)
```

<BarChart data={tender_decision} x=decision y=opps series=decision sort=false
  seriesColors={{ Attack: "#E2231A", Selective: "#E87722", Watch: "#1F2A44", Ignore: "#9AA0A6" }}
  title="Opportunities by decision" />

### E2 · Where the live opportunities are

Actionable (Attack/Selective/Watch) opportunities by country — where the bid effort should point.

```sql tender_country
select country, count(*)::double as opps
from prism.tender_pipeline
where actionable
group by 1 order by opps desc limit 12
```

<BarChart data={tender_country} x=country y=opps swapXY=true yFmt=num0
  title="Actionable opportunities by country (top 12)" />

### E3 · Owner workload

Actionable opportunities by suggested regional lead — who is carrying the load.

```sql tender_owner
select owner_suggested, count(*)::double as opps
from prism.tender_pipeline
where actionable
group by 1 order by opps desc
```

<BarChart data={tender_owner} x=owner_suggested y=opps swapXY=true yFmt=num0
  title="Actionable opportunities by owner" />

### E4 · Fit × Win — the qualification map

Every non-ignored opportunity placed on fit (do we suit it) vs win-probability. Bubble = overall opportunity score, colour = decision. **Top-right = pursue.**

```sql tender_scatter
select opportunity_id, fit_score::double as fit_score,
  win_score::double as win_score, opportunity_score::double as opportunity_score, decision
from prism.tender_pipeline
where decision <> 'Ignore' and fit_score is not null and win_score is not null
```

<BubbleChart data={tender_scatter} x=fit_score y=win_score size=opportunity_score series=decision
  seriesColors={{ Attack: "#E2231A", Selective: "#E87722", Watch: "#1F2A44" }}
  xAxisTitle="Fit score" yAxisTitle="Win-probability score" />

### E5 · Action queue

Top Attack/Selective opportunities by overall score — the bid desk's queue. Deadline shown where the notice carried one.

```sql tender_queue
select title, country, owner_suggested,
  opportunity_score::double as score, decision, deadline_date, url
from prism.tender_pipeline
where decision in ('Attack','Selective')
order by opportunity_score desc limit 15
```

<DataTable data={tender_queue} rows=15 link=url>
  <Column id=title title="Opportunity" wrap=true />
  <Column id=country title="Country" />
  <Column id=owner_suggested title="Owner" />
  <Column id=score title="Score" fmt=num0 />
  <Column id=decision title="Decision" />
  <Column id=deadline_date title="Deadline" />
</DataTable>
