---
title: Cross-Module Insights
---

[← Command Centre](/) · Layer 3 · GPS × PMS × BVP, fused across distributors and time.

## Distributor position — spend per unit × capture

GPS spend-per-unit against PMS total capture, per distributor-year. Deeper colour = higher value; sort either column to rank. High spend **and** high capture (top of both) is the healthy quadrant.

```sql gc
with cap as (
  select distributor_code, year,
    least(sum(actual_qty)/nullif(sum(expected_qty),0), 1.05) as capture
  from prism.capture where line_type = 'total' group by 1,2
)
select u.distributor_code,
  'FY' || cast(cast(u.year as integer) as varchar) as fy,
  u.spend_per_unit_eur as gps, cap.capture, u.net_sales_eur as sales
from prism.uio u
join cap on u.distributor_code = cap.distributor_code and u.year = cap.year
where u.spend_per_unit_eur is not null and cap.capture is not null
```

<DataTable data={gc} rows=10 rowShading=true search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=fy title="Year" />
  <Column id=gps title="€/unit" fmt=eur0 contentType=colorscale />
  <Column id=capture title="Capture" fmt=pct0 contentType=colorscale />
  <Column id=sales title="Net sales" fmt=eur0 />
</DataTable>

## Where each distributor sits vs the network (latest year)

Percentile rank against the network on each metric — deeper colour = stronger relative position.

```sql pct
select distributor_code, metric,
  percentile_rank::double as percentile_rank,
  raw_value::double as raw_value,
  vs_median::double as vs_median
from prism.network_percentile
where year = (select max(year) from prism.network_percentile)
order by distributor_code, metric
```

<DataTable data={pct} rows=15 search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=metric title="Metric" />
  <Column id=percentile_rank title="Percentile (0–100)" fmt=num0 contentType=colorscale />
  <Column id=raw_value title="Value" fmt=num1 />
</DataTable>
