---
title: GPS — Spend per Unit
---

[← Command Centre](/) · Layer 2 methodology · genuine net sales € per vehicle in the parc (UIO v18). Traffic lights use GPS v9 max-spend study rates. **CY2025 warranty parts** (claim files) are subtracted for ex-warranty SPU — same basis as `ISZE_GPS_Dashboard_v9.html`.

```sql gps_kpi
select
  (sum(net_sales_eur)/nullif(sum(uio_units),0))::double as wspu,
  median(spend_per_unit_eur)::double as med_spu,
  count(*)::double as dists
from prism.uio where year = (select max(year) from prism.uio) and uio_units > 0
```

<Grid cols=3>
  <BigValue data={gps_kpi} value=wspu fmt=eur0 title="💶 Weighted € / unit" />
  <BigValue data={gps_kpi} value=med_spu fmt=eur0 title="📊 Median € / unit" />
  <BigValue data={gps_kpi} value=dists fmt=num0 title="🏢 Distributors scored" />
</Grid>

## Spend per unit by distributor (latest year)

```sql gps_db
select distributor_code, spend_per_unit_eur::double as spu, traffic_light
from prism.uio
where year = (select max(year) from prism.uio) and spend_per_unit_eur is not null and uio_units > 0
order by spu desc
```

<BarChart data={gps_db} x=distributor_code y=spu swapXY=true yFmt=eur0 xAxisTitle="€ spend per unit / year" />

## Ex-warranty spend per unit (CY2025 warranty adjustment)

Warranty parts are embedded in ERP genuine revenue — ex-warranty view isolates aftermarket GPS. **UMI** shows a data gap (Israel LCV missing from claim file), not a true zero.

```sql gps_ex_warr
select distributor_code,
  spend_per_unit_eur::double as spu_incl,
  spend_per_unit_ex_warranty_eur::double as spu_ex,
  warranty_parts_eur::double as warranty_eur,
  gps_capture_vs_max::double as capture_incl,
  gps_capture_ex_warranty_vs_max::double as capture_ex,
  warranty_data_gap
from prism.uio
where year = (select max(year) from prism.uio)
  and spend_per_unit_ex_warranty_eur is not null
order by warranty_eur desc nulls last
```

<BarChart data={gps_ex_warr} x=distributor_code y={['spu_incl','spu_ex']} type=grouped swapXY=true yFmt=eur0 xAxisTitle="€ / unit — incl vs ex warranty" />

## Weighted spend-per-unit trend

```sql gps_trend
select year, (sum(net_sales_eur)/nullif(sum(uio_units),0))::double as wspu
from prism.uio where uio_units > 0 group by 1 order by 1
```

<LineChart data={gps_trend} x=year y=wspu yFmt=eur0 yAxisTitle="Weighted € / unit" />
