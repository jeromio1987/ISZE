---
title: Customer Risk Ranking
---

[← Command Centre](/) · Distributor lens · a weighted aftersales-risk index blending four signals — Eucon street-undercut exposure, AIM high-risk revenue, contested-BVP capture, and VOR/urgent share.

```sql cr_kpi
select
  sum(contested_eur)::double as contested,
  sum(eucon_undercut_rev_eur)::double as undercut,
  count(*)::double as ranked
from prism.customer_risk where year = (select max(year) from prism.customer_risk)
```

```sql cr_top
select distributor_code from prism.customer_risk
where year = (select max(year) from prism.customer_risk) order by rank limit 1
```

Highest-risk distributor this year: **<Value data={cr_top} column=distributor_code/>**.

<Grid cols=3>
  <BigValue data={cr_kpi} value=ranked fmt=num0 title="🏢 Distributors ranked" />
  <BigValue data={cr_kpi} value=contested fmt=eur0 title="⚔️ Contested revenue" />
  <BigValue data={cr_kpi} value=undercut fmt=eur0 title="📉 Street-undercut revenue" />
</Grid>

## Risk score by distributor (latest year)

```sql cr_bar
select distributor_code, risk_score::double as risk_score
from prism.customer_risk where year = (select max(year) from prism.customer_risk)
order by risk_score desc
```

<BarChart data={cr_bar} x=distributor_code y=risk_score swapXY=true xAxisTitle="Weighted risk index" />

## Full ranking — components

```sql cr
select rank, distributor_code,
  risk_score::double as risk_score,
  net_sales_eur::double as net_sales,
  eucon_undercut_pct::double as undercut_pct,
  high_risk_rev_pct::double as high_risk_pct,
  contested_bvp_capture::double as contested_capture,
  vor_urgent_share::double as vor_share
from prism.customer_risk where year = (select max(year) from prism.customer_risk) order by rank
```

<DataTable data={cr} rows=15 rowShading=true>
  <Column id=rank title="#" />
  <Column id=distributor_code title="Distributor" />
  <Column id=risk_score title="Risk" fmt=num1 contentType=colorscale />
  <Column id=net_sales title="Net sales" fmt=eur0 />
  <Column id=undercut_pct title="Street undercut" fmt=pct1 contentType=colorscale />
  <Column id=high_risk_pct title="AIM high-risk" fmt=pct1 contentType=colorscale />
  <Column id=contested_capture title="BVP of contested" fmt=pct0 contentType=colorscale />
  <Column id=vor_share title="VOR/urgent" fmt=pct1 contentType=colorscale />
</DataTable>
