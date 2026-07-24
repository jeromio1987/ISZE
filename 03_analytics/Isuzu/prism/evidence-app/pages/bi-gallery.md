---
title: PRISM — BI Gallery
---

Fifteen views off the same pipeline: **5 classics · 5 cross-data offsets · 5 picks.** Everything here is computed from invoicing — inference legs are labelled. [← back to Offset Insights](/)

<Alert status=info>
All figures are network-wide unless a chart names a distributor. Latest year shown is the most recent in each source.
</Alert>

---

## Classics

### 1 · Revenue trend, 2023–2025

```sql rev_trend
select year, net_sales::double as net_sales from prism.network_revenue order by year
```

<LineChart data={rev_trend} x=year y=net_sales yFmt=eur0 yAxisTitle="Network parts revenue" />

### 2 · Revenue concentration (top-10 part share)

How dependent each distributor is on a handful of parts — high bar = fragile revenue base.

```sql concentration
select distributor_code, top10_rev_share::double as top10_rev_share
from prism.revenue_concentration
where year = (select max(year) from prism.revenue_concentration) and line_type = 'total'
order by top10_rev_share desc
```

<BarChart data={concentration} x=distributor_code y=top10_rev_share yFmt=pct0 swapXY=true xAxisTitle="Top-10 parts as % of revenue" />

### 3 · Top-15 distributors by revenue

```sql top_db
select distributor_code, total_revenue_eur::double as revenue
from prism.revenue_concentration
where year = (select max(year) from prism.revenue_concentration) and line_type = 'total'
order by revenue desc limit 15
```

<BarChart data={top_db} x=distributor_code y=revenue yFmt=eur0 swapXY=true />

### 4 · Genuine vs BVP mix, by family

```sql mix_stack
select product_family,
  sum(genuine_eur)::double as genuine_eur,
  sum(bvp_eur)::double as bvp_eur
from prism.mix_family
where year = (select max(year) from prism.mix_family)
group by 1
order by (sum(genuine_eur)+sum(bvp_eur)) desc
```

<BarChart data={mix_stack} x=product_family y={['genuine_eur','bvp_eur']} type=stacked yFmt=eur0 swapXY=true />

### 5 · YoY revenue bridge (volume / price / mix)

What moved revenue into the latest year — decomposed into volume, price and mix effects.

```sql bridge
with w as (select * from prism.revenue_waterfall where year_to = (select max(year_to) from prism.revenue_waterfall))
select 'Volume' as component, sum(delta_volume_eur)::double as eur from w
union all select 'Price', sum(delta_price_eur)::double from w
union all select 'Mix', sum(delta_mix_eur)::double from w
```

<BarChart data={bridge} x=component y=eur yFmt=eur0 />

---

## Cross-data offsets

### 6 · Capture × GPS quadrant

Low spend per vehicle **and** low capture = the grow list. Sort by capture ascending, then scan for high TAM = biggest upside.

```sql cap_gps
with cap as (
  select distributor_code,
    sum(least(capture_rate_total,1.0)*tam_eur)/nullif(sum(tam_eur),0) as capture,
    sum(tam_eur) as tam
  from prism.opportunity_matrix
  where year = (select max(year) from prism.opportunity_matrix)
  group by 1
)
select g.distributor_code,
  g.spend_per_unit_eur::double as gps,
  cap.capture::double as capture,
  cap.tam::double as tam
from prism.gps g join cap on g.distributor_code = cap.distributor_code
where g.year = (select max(year) from prism.gps) and cap.tam > 0
```

<DataTable data={cap_gps} rows=10 rowShading=true search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=gps title="GPS / spend per unit (€)" fmt=eur0 contentType=colorscale />
  <Column id=capture title="Total capture" fmt=pct0 contentType=colorscale />
  <Column id=tam title="TAM (€)" fmt=eur0 contentType=colorscale />
</DataTable>

### 7 · Demand class × family

Where revenue is hard-to-forecast (lumpy/intermittent) vs smooth, by family.

```sql dc_family
select product_family, demand_class, rev from prism.dc_family
```

<BarChart data={dc_family} x=product_family y=rev series=demand_class type=stacked yFmt=eur0 swapXY=true />

### 8 · Substitution timeline

Genuine unit share over time, by family — falling lines = aftermarket eating in.

```sql subs
select product_family, year,
  (sum(genuine_units)::double / nullif(sum(genuine_units)+sum(bvp_units),0)) as genuine_share
from prism.substitution_timeline
group by 1,2 order by year
```

<LineChart data={subs} x=year y=genuine_share series=product_family yFmt=pct0 yAxisTitle="Genuine unit share" />

### 9 · VOR seasonality

When vehicles go off-road — month × year, share of orders that are VOR. Rolled up from week-of-year so the pattern reads instead of a 52-column smear. Pre-stock ahead of the hot weeks below.

```sql vor_season
select
  cast(least(12, greatest(1, ceil(week_of_year / 4.345))) as int) as month,
  year::varchar as year,
  (sum(vor_count)::double / nullif(sum(total_order_count),0)) as vor_pct
from prism.vor_seasonality
group by 1,2
```

<LineChart data={vor_season} x=month y=vor_pct series=year yFmt=pct1 xAxisTitle="Month" yAxisTitle="VOR share of orders" />

**Top-5 hottest weeks (network, all years)** — the spikes to pre-stock against.

```sql vor_hot
select week_of_year,
  (sum(vor_count)::double / nullif(sum(total_order_count),0)) as vor_pct,
  sum(vor_count)::double as vor_orders
from prism.vor_seasonality
group by 1
having sum(total_order_count) > 0
order by vor_pct desc limit 5
```

<DataTable data={vor_hot} rows=5>
  <Column id=week_of_year title="Week #" />
  <Column id=vor_pct title="VOR share of orders" fmt=pct1 />
  <Column id=vor_orders title="VOR orders" fmt=num0 />
</DataTable>

### 10 · Part lifecycle — and the intake gap

Revenue by lifecycle stage, **emerging → mature → zombie**. The point isn't the mature bar — it's how thin **emerging** is. The parc is in its Golden Window now, but only ~3% of revenue sits in parts new enough to refill the funnel. As the mature base ages into zombie, there's almost nothing behind it.

```sql lifecycle
select stage,
  sum(total_revenue_eur)::double as rev,
  count(*)::double as parts
from (
  select case when first_billing_year >= 2024 then 'emerging' else lifecycle_stage end as stage,
    total_revenue_eur
  from prism.part_lifecycle
)
group by 1
order by array_position(['emerging','mature','zombie'], stage)
```

<BarChart data={lifecycle} x=stage y=rev series=stage yFmt=eur0 sort=false
  seriesColors={{ emerging: "#2E8B57", mature: "#1F2A44", zombie: "#9AA0A6" }}
  title="Revenue by lifecycle stage — emerging is the intake funnel" />

<Alert status=warning>
<b>Emerging</b> = parts first invoiced in 2024–25, inside our 2023-start data window. It <b>undercounts</b>: anything genuinely new in 2023 is invisible (left-censored). Treat it as a floor — the real intake gap is no smaller than this.
</Alert>

---

## Picks

### 11 · Distributor percentile benchmark (genuine capture)

Where each distributor sits vs the network on genuine capture — percentile rank, latest year.

```sql pctile
select distributor_code, percentile_rank::double as percentile_rank
from prism.network_percentile
where metric = 'genuine_capture' and year = (select max(year) from prism.network_percentile)
order by percentile_rank desc
```

<BarChart data={pctile} x=distributor_code y=percentile_rank yFmt=pct0 swapXY=true xAxisTitle="Percentile vs network" />

### 12 · Basket co-occurrence

Which maintenance categories get ordered together — top rows = cross-sell / kit candidates.

```sql basket
select pms_cat_a, pms_cat_b, avg(correlation)::double as corr
from prism.basket_correlation
where year = (select max(year) from prism.basket_correlation)
  and pms_cat_a < pms_cat_b
group by 1,2
order by corr desc
```

<DataTable data={basket} rows=12 rowShading=true search=true>
  <Column id=pms_cat_a title="Category A" />
  <Column id=pms_cat_b title="Category B" />
  <Column id=corr title="Co-occurrence" fmt=num2 contentType=colorscale />
</DataTable>

### 13 · Recoverable-€ opportunity list

Top BVP parts by current revenue, with the genuine substitution PRISM suggests — the action queue.

```sql gaps
select pn, description,
  revenue_cy25_eur::double as revenue_eur,
  current_l1, sug1_l1,
  confidence::double as confidence
from prism.gap_suggestions
order by revenue_eur desc limit 20
```

<DataTable data={gaps} rows=20>
  <Column id=pn title="Part" />
  <Column id=description title="Description" />
  <Column id=revenue_eur title="CY25 revenue" fmt=eur0 />
  <Column id=current_l1 title="Current" />
  <Column id=sug1_l1 title="Suggest" />
  <Column id=confidence title="Conf." fmt=pct0 />
</DataTable>

### 14 · BVP family risk matrix

High BVP revenue **and** high AIM-risk share = defend genuine here first. Sort by either column; genuine € at stake shown alongside.

```sql risk
select product_family,
  sum(bvp_eur)::double as bvp_eur,
  (sum(aim_high_risk_rev_eur)::double / nullif(sum(genuine_eur)+sum(bvp_eur),0)) as risk_pct,
  sum(genuine_eur)::double as genuine_eur
from prism.bvp_family_risk
where year = (select max(year) from prism.bvp_family_risk)
group by 1
having sum(bvp_eur) > 100000
```

<DataTable data={risk} rows=10 rowShading=true>
  <Column id=product_family title="Family" />
  <Column id=bvp_eur title="BVP revenue" fmt=eur0 contentType=colorscale />
  <Column id=risk_pct title="High-risk rev share" fmt=pct0 contentType=colorscale />
  <Column id=genuine_eur title="Genuine € at stake" fmt=eur0 contentType=colorscale />
</DataTable>

### 15 · Capture-recovery by gap type (network)

Network recoverable € split by gap type, per category — the network version of the ITUK ceiling.

```sql recovery
select pms_category, gap_type, sum(gap_revenue_at_genuine)::double as eur
from prism.capture_recovery
group by 1,2 order by 1
```

<BarChart data={recovery} x=pms_category y=eur series=gap_type type=stacked yFmt=eur0 swapXY=true />
