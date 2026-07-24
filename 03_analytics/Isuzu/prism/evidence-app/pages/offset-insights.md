---
title: PRISM — Offset Insights
---

<div class="prism-hero">
  <div class="prism-hero-tag">PARTS REVENUE INTELLIGENCE &amp; SALES MONITOR</div>
  <div class="prism-hero-line">The decision-intelligence layer over Isuzu Europe's parts business.</div>
  <div class="prism-hero-sub">Raw ledger in &nbsp;→&nbsp; a short, honest decision list out.</div>
</div>

**PRISM** reads the raw ledger — **€97.4M across 2023–2025, 24,532 active parts, 30 accounts (18 named distributors), 16 countries** — and turns it into a handful of moves a sales leader can make *this* quarter.

This is **diagnostic, not descriptive, BI**. A reporting tool tells you *what happened*; PRISM isolates *where the money is leaking and what to do about it* — which distributors are drifting, which parts to stock forward, where genuine loses to the value line, and how hard we can price before units defect. It gets there by anchoring every euro of demand to the **vehicle parc on the road**, so "opportunity" is measured against a real ceiling, never a guess. Numbers are computed straight from invoicing; the few inferences are labelled as such.

```sql net
select year, net_sales::double as net_sales, parts, accounts from prism.network_revenue order by year
```

<Grid cols=3>
  <BigValue data={net} value=net_sales fmt=eur0 title="💶 Network parts revenue (2025)" />
  <BigValue data={net} value=parts fmt=num0 title="🔩 Active part numbers" />
  <BigValue data={net} value=accounts fmt=num0 title="🏢 Billing accounts" />
</Grid>

The network turns over **€32M+ of parts a year**. PRISM doesn't try to model all 24,532 parts — it focuses on the maintenance-service demand that ties back to the vehicle parc, where capture is *measurable*.

<style>
  .prism-hero {
    background: #222018; border-left: 3px solid #c9a227;
    border-radius: 14px; padding: 1.7rem 1.9rem; margin: 0.4rem 0 1.4rem;
    box-shadow: 0 24px 60px -34px rgba(34,32,24,0.7);
  }
  .prism-hero-tag {
    color: #c9a227; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.22em;
    margin-bottom: 0.5rem;
  }
  .prism-hero-line { color: #fff; font-size: 1.55rem; font-weight: 800; line-height: 1.2; }
  .prism-hero-sub  { color: #b8b4a8; font-size: 0.95rem; margin-top: 0.45rem; }

  .prism-pillars {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.9rem; margin: 1rem 0 1.5rem;
  }
  .prism-pillar {
    border: 1px solid #E3E8F0; border-top: 4px solid #1B3A6B; border-radius: 12px;
    background: #fff; padding: 1rem 1.05rem; transition: transform .12s ease, box-shadow .12s ease;
  }
  .prism-pillar:hover { transform: translateY(-3px); box-shadow: 0 8px 22px rgba(27,58,107,0.14); }
  .prism-pillar:nth-child(4) { border-top-color: #E87722; }
  .prism-pillar .ico { font-size: 1.7rem; line-height: 1; }
  .prism-pillar .lyr { font-weight: 800; color: #1B3A6B; margin: 0.5rem 0 0.1rem; font-size: 1rem; }
  .prism-pillar .q   { color: #4A5568; font-size: 0.85rem; line-height: 1.35; margin: 0; }
  @media (max-width: 820px) { .prism-pillars { grid-template-columns: repeat(2, 1fr); } }
</style>

> **→ [Open the full BI Gallery](/bi-gallery)** — 15 views: 5 classics, 5 cross-data offsets, 5 picks.
> **→ [AIM & BVP Leakage](/aim-leakage)** — 15 boards: where genuine loses to BVP, by distributor, family and order type.

### The spine

PRISM stacks four layers, each built on the one before:

<div class="prism-pillars">
  <div class="prism-pillar">
    <div class="ico">🚛</div>
    <div class="lyr">UIO — Parc</div>
    <p class="q">How many Isuzu vehicles are on the road, by market? The demand ceiling.</p>
  </div>
  <div class="prism-pillar">
    <div class="ico">📊</div>
    <div class="lyr">GPS — Spend / unit</div>
    <p class="q">What does each distributor actually spend per vehicle on genuine parts?</p>
  </div>
  <div class="prism-pillar">
    <div class="ico">🔧</div>
    <div class="lyr">PMS — Capture</div>
    <p class="q">Of the maintenance demand we <em>should</em> see, how much do we capture?</p>
  </div>
  <div class="prism-pillar">
    <div class="ico">⚡</div>
    <div class="lyr">BVP — Mix</div>
    <p class="q">Where genuine loses to the value line — and where we can win it back.</p>
  </div>
</div>

```sql kpi
select
  (select sum(tam_eur) from prism.opportunity_matrix
     where year=(select max(year) from prism.opportunity_matrix))::double as tam,
  ((select sum(least(capture_rate_genuine,1.0)*tam_eur) from prism.opportunity_matrix
     where year=(select max(year) from prism.opportunity_matrix))
   / nullif((select sum(tam_eur) from prism.opportunity_matrix
     where year=(select max(year) from prism.opportunity_matrix)),0))::double as genuine_capture,
  ((select count(*) from prism.demand_classification where demand_class in ('intermittent','lumpy'))::double
   / nullif((select count(*) from prism.demand_classification),0)::double) as hard_share,
  (select sum(premium_pct*expedited_revenue_eur)/nullif(sum(expedited_revenue_eur),0)
     from prism.vor_wtp where expedited_revenue_eur>0)::double as vor_premium
```

<Grid cols=4>
  <BigValue data={kpi} value=tam fmt=eur0 title="🎯 Max potential revenue" />
  <BigValue data={kpi} value=genuine_capture fmt=pct1 title="✅ Genuine capture of it" />
  <BigValue data={kpi} value=hard_share fmt=pct0 title="🌊 Lumpy / intermittent lines" />
  <BigValue data={kpi} value=vor_premium fmt=pct1 title="🚨 VOR premium paid (raw)" />
</Grid>

**Read that row as the thesis:** within the addressable lens we capture under a fifth in genuine, almost none of the demand is smooth enough to forecast naively, and customers already pay a premium when a vehicle is off the road. The six visuals below turn each of those facts into a move.

| # | Visual | The decision it drives |
| --- | --- | --- |
| 2 | Lumpiness → Airfreight | Which families to *stock forward* vs. let run on airfreight |
| 3 | Demand-Flow Sankey | Where genuine € leaks to aftermarket / under-service, by category |
| 4 | VOR Pricing Power | The repricing call-list: high expedited revenue, low premium today |
| 5 | Premium vs Defection | How hard we can price genuine before units defect to BVP |
| 1 | Distributor Movement | Which distributors are drifting on spend × capture year-on-year |
| 6 | Capture-Ceiling | ITUK's recoverable € on the path from today to the max-potential-revenue ceiling |

<Alert status=warning>
The Sankey "Leakage" leg and the max-potential-revenue ceiling are <b>INFERENCES</b> (under-service gap), not measured competitor figures — internal use only. All capture, premium and demand-class numbers above are computed directly from invoicing, not estimated.
</Alert>

## 2 · Spiky demand → urgent orders

**What this is:** every row is a parts family — its **spiky-demand revenue share**, its **urgent (VOR) line share**, and the **revenue** behind it (latest year). Sort any column.

**What it says:** demand is spiky almost everywhere — every family sits at **86–100%** spiky-share, so forecastability isn't the lever. The lever is **where urgent orders pile up on big money** (top-right, large bubble). **PMS Filters** is the one to act on: €6.7M family, a quarter of its lines arrive urgent. **Belts/Cooling** looks alarming at 29% VOR but it's a €78K family — a small bubble, ignore it.

```sql lumpy_vor
select product_family, rev, spiky_share, vor_pct
from prism.lumpy_vor order by rev desc
```

<DataTable data={lumpy_vor} rows=10 rowShading=true>
  <Column id=product_family title="Family" />
  <Column id=rev title="Revenue" fmt=eur0 contentType=colorscale />
  <Column id=spiky_share title="Spiky-demand share" fmt=pct0 contentType=colorscale />
  <Column id=vor_pct title="Urgent (VOR) line share" fmt=pct1 contentType=colorscale />
</DataTable>

**Pre-stock priority — urgent (VOR) € at risk, latest year.** This is the actionable cut: not the scary % but the actual money flowing through urgent orders. Buffer stock pays back fastest at the top.

```sql vor_priority
select product_family,
  sum(vor_revenue_eur)::double as vor_eur,
  (sum(vor_line_count)::double / nullif(sum(total_line_count),0)) as vor_pct
from prism.vor_airfreight
where year = (select max(year) from prism.vor_airfreight)
group by 1
order by vor_eur desc
```

<DataTable data={vor_priority} rows=7>
  <Column id=product_family title="Family" />
  <Column id=vor_eur title="Urgent € at risk" fmt=eur0 />
  <Column id=vor_pct title="VOR line share" fmt=pct1 />
</DataTable>

## 3 · Demand flow — genuine / BVP / leakage by category

Parc-implied demand (max potential revenue) split into genuine captured, BVP captured, and inferred leakage, per category. Tall stacks with a big grey leg = the biggest recoverable pools.

```sql sankey
with o as (
  select pms_category,
    least(capture_rate_genuine, 1.0) * tam_eur as genuine_eur,
    greatest(least(capture_rate_total,1.0) - least(capture_rate_genuine,1.0), 0) * tam_eur as bvp_eur,
    greatest(1 - least(capture_rate_total,1.0), 0) * tam_eur as leak_eur
  from prism.opportunity_matrix
  where year = (select max(year) from prism.opportunity_matrix)
)
select pms_category as source, 'Genuine' as target, sum(genuine_eur) as value from o group by 1
union all
select pms_category, 'BVP', sum(bvp_eur) from o group by 1
union all
select pms_category, 'Leakage (INFERRED)', sum(leak_eur) from o group by 1
```

<BarChart data={sankey} x=source y=value series=target type=stacked swapXY=true yFmt=eur0 xAxisTitle="Parc-implied demand (€)"
  seriesColors={{ Genuine: "#1f9d6b", BVP: "#c9a227", "Leakage (INFERRED)": "#9aa0aa" }} />

## 4 · VOR Pricing Power

High expedited revenue **and** low premium = the repricing call-list (we rush parts out but barely charge for the urgency). Sort by expedited revenue, then scan for low premium.

```sql vor_power
select distributor_code,
  sum(expedited_revenue_eur)::double as exp_rev,
  (sum(premium_pct * expedited_revenue_eur) / nullif(sum(expedited_revenue_eur),0))::double as wpremium,
  count(*)::double as pairs
from prism.vor_wtp
group by 1
having sum(expedited_revenue_eur) > 0
```

<DataTable data={vor_power} rows=10 rowShading=true search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=exp_rev title="Expedited revenue" fmt=eur0 contentType=colorscale />
  <Column id=wpremium title="VOR premium (rev-wtd)" fmt=pct1 contentType=colorscale />
  <Column id=pairs title="Pairs" fmt=num0 />
</DataTable>

## 5 · Premium vs Defection

Does a higher genuine premium correlate with lower genuine unit share? (latest year)

```sql prem_def
select distributor_code, pms_category,
  price_premium_pct::double as price_premium_pct,
  genuine_unit_share::double as genuine_unit_share,
  least(genuine_units, bvp_units)::double as units
from prism.price_premium
where year = (select max(year) from prism.price_premium)
  and price_premium_pct between -0.5 and 5
  and genuine_units >= 20 and bvp_units >= 20
```

<DataTable data={prem_def} rows=10 rowShading=true search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=pms_category title="Category" />
  <Column id=price_premium_pct title="Genuine ASP premium" fmt=pct0 contentType=colorscale />
  <Column id=genuine_unit_share title="Genuine unit share" fmt=pct0 contentType=colorscale />
  <Column id=units title="Min units" fmt=num0 />
</DataTable>

<Alert status=info>
Each point needs <b>≥20 genuine and ≥20 BVP units</b> — without that floor, cells like Kazakhstan fuel_filter (4 genuine units → a meaningless −48% "premium") plotted as real outliers. Bubble size = the <b>smaller</b> of the two legs, so a point only looks big when both sides have real volume.
</Alert>

## 1 · Distributor Movement

GPS spend-per-unit and PMS capture per distributor-year. Sort by distributor to read drift across years; deeper colour = higher value.

```sql traj
with cap as (
  select distributor_code, year,
    least(sum(actual_qty) / nullif(sum(expected_qty),0), 1.05) as capture
  from prism.capture where line_type = 'total' group by 1,2
)
select g.distributor_code, g.year::varchar as year, g.spend_per_unit_eur as gps, cap.capture
from prism.gps g
join cap on g.distributor_code = cap.distributor_code and g.year = cap.year
```

<DataTable data={traj} rows=10 rowShading=true search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=year title="Year" />
  <Column id=gps title="GPS / SPU (€)" fmt=eur0 contentType=colorscale />
  <Column id=capture title="PMS capture" fmt=pct0 contentType=colorscale />
</DataTable>

## 6 · Capture-Ceiling  _(degraded — recoverable bars, not a waterfall)_

ITUK current genuine € and the recoverable layers up to max potential revenue.

```sql ceiling
with om as (
  select sum(least(capture_rate_genuine,1.0) * tam_eur) as cur_genuine
  from prism.opportunity_matrix
  where distributor_code = 'ITUK' and year = (select max(year) from prism.opportunity_matrix)
),
r as (
  select
    sum(case when gap_type='under_service' then gap_revenue_at_genuine else 0 end) as under_service,
    sum(case when gap_type='substitution' then gap_revenue_at_genuine else 0 end) as substitution,
    sum(case when gap_type='catalog_gap' then gap_revenue_at_genuine else 0 end) as catalog_gap
  from prism.capture_recovery where distributor_code = 'ITUK'
)
select 'a · Current genuine' as layer, cur_genuine as eur from om
union all select 'b · Recover under-service', under_service from r
union all select 'c · Win back from BVP', substitution from r
union all select 'd · Close catalog gap', catalog_gap from r
order by layer
```

<BarChart data={ceiling} x=layer y=eur yFmt=eur0 swapXY=true title="ITUK — recoverable € to max-potential-revenue ceiling" />
