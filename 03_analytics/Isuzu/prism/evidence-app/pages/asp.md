---
title: Street-Price Exposure
---

[← Command Centre](/) · Pricing lens · where genuine list price sits versus the external aftermarket street, probed via Eucon.

<Alert status=warning>
Competitor figures are <b>listed aftermarket prices captured by Eucon</b> (Blue Print, Febi, Delphi, etc.), not our invoicing and not a measured wallet share. A positive delta means our genuine list price sits <i>above</i> the competitor average — exposure, not realised loss. Internal use only.
</Alert>

```sql asp_kpi
select
  count(*)::double as parts,
  sum(rev_eur)::double as rev_probed,
  sum(case when isze_exposed then rev_eur else 0 end)::double as rev_exposed,
  median(avg_delta_pct)::double as med_delta
from prism.eucon_gap
```

<Grid cols=4>
  <BigValue data={asp_kpi} value=parts fmt=num0 title="🔍 Parts probed" />
  <BigValue data={asp_kpi} value=rev_probed fmt=eur0 title="💶 Revenue probed" />
  <BigValue data={asp_kpi} value=rev_exposed fmt=eur0 title="📉 Exposed revenue" />
  <BigValue data={asp_kpi} value=med_delta fmt=pct1 title="Δ Median price gap" />
</Grid>

## Most-exposed parts by revenue

Ranked by the revenue behind each part. A high positive delta on a big-revenue line is the repricing call-list.

```sql asp_top
select
  description,
  subgroup,
  rev_eur::double            as rev_eur,
  isze_ie40_price_eur::double as isze_price,
  avg_competitor_eur::double  as comp_avg,
  avg_delta_pct::double       as delta,
  competitor_count::double    as competitors
from prism.eucon_gap
where rev_eur is not null
order by rev_eur desc limit 25
```

<DataTable data={asp_top} rows=12 rowShading=true search=true>
  <Column id=description title="Part" />
  <Column id=subgroup title="Subgroup" />
  <Column id=rev_eur title="Revenue" fmt=eur0 contentType=colorscale />
  <Column id=isze_price title="ISZE list €" fmt=eur2 />
  <Column id=comp_avg title="Comp. avg €" fmt=eur2 />
  <Column id=delta title="Δ vs comp" fmt=pct0 contentType=colorscale />
  <Column id=competitors title="# comp" fmt=num0 />
</DataTable>
