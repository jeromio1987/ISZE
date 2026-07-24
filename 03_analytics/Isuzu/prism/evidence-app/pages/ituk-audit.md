---
title: ITUK PMS PN Audit
---

[← Command Centre](/) · The line-level part-number evidence behind the [ITUK PMS Story](/ituk-story) — actual genuine sales by service PN.

```sql aud_kpi
select
  count(distinct part_number)::double as pns,
  sum(actual_rev_eur)::double as rev,
  count(distinct category_label)::double as cats
from prism.ituk_audit where year = (select max(year) from prism.ituk_audit)
```

<Grid cols=3>
  <BigValue data={aud_kpi} value=pns fmt=num0 title="🔩 Part numbers" />
  <BigValue data={aud_kpi} value=rev fmt=eur0 title="💶 Audited revenue" />
  <BigValue data={aud_kpi} value=cats fmt=num0 title="🗂️ Service categories" />
</Grid>

## Revenue by service category (latest year)

```sql aud_cat
select category_label, sum(actual_rev_eur)::double as rev
from prism.ituk_audit where year = (select max(year) from prism.ituk_audit)
group by 1 order by rev desc
```

<BarChart data={aud_cat} x=category_label y=rev swapXY=true yFmt=eur0 xAxisTitle="Genuine revenue (€)" />

## Top part numbers

```sql aud
select category_label, part_number, pms_model,
  actual_qty::double as qty,
  actual_rev_eur::double as rev,
  share_of_category_qty::double as share
from prism.ituk_audit where year = (select max(year) from prism.ituk_audit)
order by rev desc limit 40
```

<DataTable data={aud} rows=15 rowShading=true search=true>
  <Column id=category_label title="Category" />
  <Column id=part_number title="Part №" />
  <Column id=pms_model title="Model" />
  <Column id=qty title="Qty" fmt=num0 />
  <Column id=rev title="Revenue" fmt=eur0 contentType=colorscale />
  <Column id=share title="% of cat qty" fmt=pct0 />
</DataTable>
