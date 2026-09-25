---
title: Tender Pipeline
---

[← Command Centre](/) · Pipeline · fleet R&M tender opportunities scored for fit, winnability and economics.

```sql tnd_kpi
select
  count(*)::double as n,
  sum(value_amount)::double as val,
  sum(case when actionable then 1 else 0 end)::double as act
from prism.tender_pipeline
```

<Grid cols=3>
  <BigValue data={tnd_kpi} value=n fmt=num0 title="📋 Opportunities" />
  <BigValue data={tnd_kpi} value=val fmt=eur0 title="💶 Pipeline value" />
  <BigValue data={tnd_kpi} value=act fmt=num0 title="✅ Actionable" />
</Grid>

> **Superseded:** this page used to read a flattened table built on 29 May 2026. It now reads the
> weekly live tender feed through PRISM's single reader. The old table said 400 actionable and 352
> R&M; the live feed says 281 and 279. It and its builder are kept on disk but nothing reads them.

## Opportunities by country

Most tenders list no headline value, so volume is the cleaner read; value (where published) drives the KPI above.

```sql tnd_country
select country, count(*)::double as opportunities
from prism.tender_pipeline
where country is not null
group by 1 order by opportunities desc limit 15
```

<BarChart data={tnd_country} x=country y=opportunities swapXY=true yAxisTitle="Opportunities" xAxisTitle="Opportunities" />

## Top opportunities by score

```sql tnd
select title, buyer, country,
  value_amount::double as value,
  deadline_date,
  opportunity_score::double as score,
  decision
from prism.tender_pipeline
order by opportunity_score desc nulls last limit 25
```

<DataTable data={tnd} rows=12 rowShading=true search=true>
  <Column id=title title="Opportunity" wrap=true />
  <Column id=buyer title="Buyer" />
  <Column id=country title="Country" />
  <Column id=value title="Value" fmt=eur0 contentType=colorscale />
  <Column id=deadline_date title="Deadline" />
  <Column id=score title="Score" fmt=num1 contentType=colorscale />
  <Column id=decision title="Decision" />
</DataTable>
