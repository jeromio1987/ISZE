---
title: PMS — Capture Rate
---

[← Command Centre](/) · Layer 2 methodology · of the maintenance demand the parc implies, how much we capture.

```sql pms_kpi
with o as (select * from prism.opportunity_matrix where year = (select max(year) from prism.opportunity_matrix))
select
  (sum(least(capture_rate_genuine,1.0)*tam_eur)/nullif(sum(tam_eur),0))::double as gen_cap,
  (sum(least(capture_rate_total,1.0)*tam_eur)/nullif(sum(tam_eur),0))::double as tot_cap,
  sum(tam_eur)::double as tam
from o
```

<Grid cols=3>
  <BigValue data={pms_kpi} value=tot_cap fmt=pct0 title="🔧 Total capture (capped)" />
  <BigValue data={pms_kpi} value=gen_cap fmt=pct0 title="✅ Genuine-only capture" />
  <BigValue data={pms_kpi} value=tam fmt=eur0 title="🎯 Addressable demand (TAM)" />
</Grid>

## Capture by service category (latest year)

Total (genuine + BVP) vs genuine-only. Categories at the 100% ceiling are demand-served — the lever there is mix, not capture.

```sql pms_cat
select pms_category,
  (sum(least(capture_rate_genuine,1.0)*tam_eur)/nullif(sum(tam_eur),0))::double as genuine,
  (sum(least(capture_rate_total,1.0)*tam_eur)/nullif(sum(tam_eur),0))::double as total
from prism.opportunity_matrix
where year = (select max(year) from prism.opportunity_matrix)
group by 1 order by sum(tam_eur) desc
```

<BarChart data={pms_cat} x=pms_category y={['genuine','total']} type=grouped yFmt=pct0 yAxisTitle="Capture rate" />

## Capture trend — genuine vs total

```sql pms_trend
select year, line_type,
  least(sum(actual_qty)/nullif(sum(expected_qty),0), 1.2)::double as capture
from prism.capture where line_type in ('genuine','total') group by 1,2 order by 1
```

<LineChart data={pms_trend} x=year y=capture series=line_type yFmt=pct0 yAxisTitle="Capture rate" />

## PMS capture by distributor (latest year)

Full **PMS exercise** for all 18 ISZE GPS-base distributors in `pms_capture_by_db_year.csv` (N75/LCV parc config per DB). Weighted capture = demand-weighted across 13 service categories.

```sql pms_db
select distributor_code, country,
  capture_rate_total_wtd::double as total_cap,
  capture_rate_genuine_wtd::double as genuine_cap,
  oil_filter_capture::double as oil_cap,
  revenue_gap_eur_sum::double as gap_eur,
  uio_units::double as uio
from prism.pms_db_summary
where year = (select max(year) from prism.pms_db_summary)
order by gap_eur desc
```

<BarChart data={pms_db} x=distributor_code y={['total_cap','genuine_cap']} type=grouped swapXY=true yFmt=pct0 xAxisTitle="Weighted capture rate" />

<DataTable data={pms_db} rows=18 rowShading=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=country title="Country" />
  <Column id=uio fmt=num0 title="UIO" />
  <Column id=oil_cap fmt=pct0 title="Oil filter" contentType=colorscale />
  <Column id=total_cap fmt=pct0 title="Total capture" contentType=colorscale />
  <Column id=gap_eur fmt=eur0 title="Revenue gap" />
</DataTable>
