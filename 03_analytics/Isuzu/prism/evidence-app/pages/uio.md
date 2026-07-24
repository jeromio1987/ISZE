---
title: UIO — Units in Operation
---

[← Command Centre](/) · Layer 1 · the parc that sets the demand ceiling (UIO v18). Offline HTML: `Dashboards/ISUZU_UIO_Dashboard_2026_v18.html`.

```sql uio_kpi
select
  sum(uio_units)::double as units,
  count(distinct distributor_code)::double as dists,
  count(distinct country)::double as countries
from prism.uio where year = (select max(year) from prism.uio) and uio_units > 0
```

<Grid cols=3>
  <BigValue data={uio_kpi} value=units fmt=num0 title="🚛 Units in operation" />
  <BigValue data={uio_kpi} value=dists fmt=num0 title="🏢 Distributors with parc" />
  <BigValue data={uio_kpi} value=countries fmt=num0 title="🌍 Countries" />
</Grid>

## Parc by distributor (latest year)

```sql uio_db
select distributor_code, uio_units::double as uio_units
from prism.uio
where year = (select max(year) from prism.uio) and uio_units > 0
order by uio_units desc
```

<BarChart data={uio_db} x=distributor_code y=uio_units swapXY=true yFmt=num0 xAxisTitle="Units in operation" />

## Parc trend

```sql uio_trend
select year, sum(uio_units)::double as units
from prism.uio where uio_units > 0 group by 1 order by 1
```

<LineChart data={uio_trend} x=year y=units yFmt=num0 yAxisTitle="Total UIO" />

<Alert status=info>
Distributors with no verified UIO actuals are excluded from the counts above and show as “unverified” on the Command Centre.
</Alert>
