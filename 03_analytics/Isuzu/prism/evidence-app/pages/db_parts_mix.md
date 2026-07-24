---
title: Parts Mix per Distributor
---

Genuine / contested / BVP split of **total** parts revenue, per distributor. Computed from invoicing + the genuine↔BVP catalogue crossref — **not** competitor wallet share. Non-Isuzu aftermarket brands never touch our invoice and are not shown here.

```sql net
select
  sum(total_eur)::double as net,
  (sum(bvp_eur)/nullif(sum(total_eur),0))::double as bvp_share,
  (sum(bvp_eur)/nullif(sum(contested_eur),0))::double as contested_capture
from prism.db_parts_mix
where year = (select max(year) from prism.db_parts_mix)
```

<BigValue data={net} value=net fmt=eur0 title="Network parts revenue" />
<BigValue data={net} value=bvp_share fmt=pct1 title="BVP share of total" />
<BigValue data={net} value=contested_capture fmt=pct1 title="BVP share of contested basket" />

**Contested** = genuine parts that have a BVP equivalent in the catalogue — the conquerable basket. **Genuine only** has no BVP alternative.

## Mix per distributor

```sql mix
select distributor_code,
  bvp_pct, genuine_contested_pct, genuine_only_pct, total_eur
from prism.db_parts_mix
where year = (select max(year) from prism.db_parts_mix)
order by total_eur desc
```

<BarChart data={mix} x=distributor_code y={["bvp_pct","genuine_contested_pct","genuine_only_pct"]}
  type=stacked yFmt=pct0 swapXY=true
  title="Parts mix per distributor (latest year)"
  seriesColors={{ bvp_pct: "#E2231A", genuine_contested_pct: "#E87722", genuine_only_pct: "#1B3A6B" }} />

## Where the value line is winning

BVP share of the conquerable (contested) basket — high = BVP already taking the swappable demand.

```sql capture
select distributor_code, contested_bvp_capture, contested_eur
from prism.db_parts_mix
where year = (select max(year) from prism.db_parts_mix) and contested_eur > 0
order by contested_bvp_capture desc
```

<BarChart data={capture} x=distributor_code y=contested_bvp_capture
  yFmt=pct0 swapXY=true title="Contested-basket BVP capture (latest year)" />

<DataTable data={mix} rows=25>
  <Column id=distributor_code title="Distributor" />
  <Column id=total_eur fmt=eur0 title="Parts revenue" />
  <Column id=bvp_pct fmt=pct1 title="BVP %" />
  <Column id=genuine_contested_pct fmt=pct1 title="Contested %" />
  <Column id=genuine_only_pct fmt=pct1 title="Genuine only %" />
</DataTable>
