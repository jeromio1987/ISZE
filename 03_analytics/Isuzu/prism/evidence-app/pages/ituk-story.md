---
title: ITUK PMS Story
---

[← Command Centre](/) · The narrative: ITUK's PMS book is **not** a capture-deficit story. The big service categories sit at the 100% ceiling — demand is served. The lever is **mix** (genuine vs BVP), and the only genuine *capture* gaps are availability-driven (air filter, clutch).

```sql ituk_kpi
with o as (select * from prism.opportunity_matrix where distributor_code='ITUK' and year=(select max(year) from prism.opportunity_matrix))
select
  (sum(least(capture_rate_total,1.0)*tam_eur)/nullif(sum(tam_eur),0))::double   as tot_cap,
  (sum(least(capture_rate_genuine,1.0)*tam_eur)/nullif(sum(tam_eur),0))::double as gen_cap,
  sum(tam_eur)::double as tam
from o
```

<Grid cols=3>
  <BigValue data={ituk_kpi} value=tot_cap fmt=pct0 title="🔧 Total capture (capped)" />
  <BigValue data={ituk_kpi} value=gen_cap fmt=pct0 title="✅ Genuine-only capture" />
  <BigValue data={ituk_kpi} value=tam fmt=eur0 title="🎯 ITUK addressable demand" />
</Grid>

## Capture by category — genuine vs total

Where total sits at the ceiling but genuine trails, the gap is **BVP mix**, not lost demand.

```sql ituk_cat
select pms_category,
  least(capture_rate_genuine,1.0)::double as genuine,
  least(capture_rate_total,1.0)::double   as total
from prism.opportunity_matrix
where distributor_code='ITUK' and year=(select max(year) from prism.opportunity_matrix)
order by tam_eur desc
```

<BarChart data={ituk_cat} x=pms_category y={['genuine','total']} type=grouped yFmt=pct0 yAxisTitle="Capture rate" />

## BVP share by family — the mix lever

```sql ituk_mix
select product_family,
  bvp_share_eur::double as bvp_share,
  bvp_share_eur_yoy_pp::double as yoy_pp
from prism.mix_family
where distributor_code='ITUK' and year=(select max(year) from prism.mix_family)
order by bvp_share desc
```

<BarChart data={ituk_mix} x=product_family y=bvp_share swapXY=true yFmt=pct0 xAxisTitle="BVP share of revenue" />

<Alert status=info>
Capture rates are capped at 100% (a category can't be more than fully served). Genuine-only capture below total means the residual demand is met by the BVP value line — a mix decision, recoverable on price and availability, not a missing-customer problem.
</Alert>
