---
title: BVP Intelligence
---

[← Command Centre](/) · Product line · BVP is Isuzu's **Best Value Parts** budget OEM range — the second line to defend the contested basket on price. This board is the genuine-vs-BVP mix, not loss to a rival.

```sql bvp_kpi
select
  (sum(bvp_eur)/nullif(sum(total_eur),0))::double as bvp_share,
  (sum(bvp_eur)/nullif(sum(contested_eur),0))::double as contested_capture,
  sum(contested_eur)::double as contested
from prism.db_parts_mix where year = (select max(year) from prism.db_parts_mix)
```

<Grid cols=3>
  <BigValue data={bvp_kpi} value=bvp_share fmt=pct1 title="⚡ BVP share of total" />
  <BigValue data={bvp_kpi} value=contested_capture fmt=pct0 title="⚔️ BVP share of contested" />
  <BigValue data={bvp_kpi} value=contested fmt=eur0 title="🎯 Contested revenue" />
</Grid>

## Genuine vs BVP by product family (latest year)

```sql bvp_family
select product_family,
  sum(genuine_eur)::double as genuine_eur,
  sum(bvp_eur)::double as bvp_eur
from prism.mix_family where year = (select max(year) from prism.mix_family)
group by 1 order by (sum(genuine_eur)+sum(bvp_eur)) desc
```

<BarChart data={bvp_family} x=product_family y={['genuine_eur','bvp_eur']} type=stacked swapXY=true yFmt=eur0 xAxisTitle="Revenue (€)" />

## BVP share of contested, by distributor

Where the value line is winning the conquerable basket. High bar = genuine ceding ground at that distributor.

```sql bvp_db
select distributor_code,
  contested_bvp_capture::double as contested_capture,
  bvp_pct::double as bvp_pct,
  total_eur::double as total_eur
from prism.db_parts_mix where year = (select max(year) from prism.db_parts_mix)
order by contested_capture desc
```

<BarChart data={bvp_db} x=distributor_code y=contested_capture swapXY=true yFmt=pct0 xAxisTitle="BVP share of contested basket" />

<Alert status=info>
<b>Read the bar correctly.</b> This is <b>not</b> “is there a BVP alternative?” — it is “of revenue on PNs that <i>do</i> have a catalogue BVP twin, what share went BVP?”
<b>High bar</b> (e.g. UTI ~92%) = alternatives exist and BVP is winning.
<b>Low bar</b> (e.g. Denmark, Iceland ~0%) = alternatives still exist in the crossref, but distributors buy <b>genuine on those PNs</b> — not that the basket is uncontested.
External aftermarket brands are on <a href="/aim-leakage">AIM &amp; BVP Leakage → Section D</a>.
</Alert>

## High vs low — do BVP alternatives exist?

Contested € = conquerable basket size. <b>Pairs both sold</b> = PMS subgroups where genuine <i>and</i> BVP both invoiced in CY2025. <b>Genuine-only pairs</b> = catalogue has a BVP twin, but only genuine sold.

```sql bvp_alt
with sub as (
  select distributor_code,
    sum(pairs_both)::int          as pairs_both_sold,
    sum(pairs_genuine_only)::int  as pairs_genuine_only,
    sum(pairs_bvp_only)::int      as pairs_bvp_only
  from prism.substitution_db
  where year = (select max(year) from prism.substitution_db)
  group by 1
)
select
  m.distributor_code,
  m.contested_bvp_capture::double as contested_capture,
  m.contested_eur::double         as contested_eur,
  m.genuine_contested_eur::double as genuine_contested_eur,
  m.bvp_eur::double               as bvp_eur,
  coalesce(s.pairs_both_sold, 0)::int       as pairs_both_sold,
  coalesce(s.pairs_genuine_only, 0)::int    as pairs_genuine_only,
  coalesce(s.pairs_bvp_only, 0)::int         as pairs_bvp_only,
  case
    when m.contested_eur < 1000 then 'Tiny contested basket'
    when m.contested_bvp_capture >= 0.70 then 'BVP winning — alt exists & used'
    when coalesce(s.pairs_both_sold, 0) = 0 and m.contested_eur > 0
      then 'Alt in catalogue — genuine only sold (room to push BVP)'
    else 'Mixed — some paired selling'
  end as interpretation
from prism.db_parts_mix m
left join sub s on m.distributor_code = s.distributor_code
where m.year = (select max(year) from prism.db_parts_mix)
  and m.contested_eur > 0
order by m.contested_bvp_capture desc
```

### Capture vs contested basket size

Bubble size = contested € at stake. Top-right = large basket + BVP winning. Bottom-left = alternatives exist but genuine still defends.

```sql bvp_bubble
with sub as (
  select distributor_code, sum(pairs_both)::int as pairs_both_sold
  from prism.substitution_db
  where year = (select max(year) from prism.substitution_db)
  group by 1
)
select
  m.distributor_code,
  m.contested_eur::double as contested_eur,
  m.contested_bvp_capture::double as contested_capture,
  coalesce(s.pairs_both_sold, 0)::int as pairs_both_sold
from prism.db_parts_mix m
left join sub s on m.distributor_code = s.distributor_code
where m.year = (select max(year) from prism.db_parts_mix) and m.contested_eur > 5000
```

<BubbleChart data={bvp_bubble} x=contested_eur y=contested_capture size=pairs_both_sold series=distributor_code
  xFmt=eur0 yFmt=pct0 xAxisTitle="Contested revenue (€)" yAxisTitle="BVP capture of contested" />

<DataTable data={bvp_alt} rows=22 search=true>
  <Column id=distributor_code title="Distributor" />
  <Column id=contested_capture title="BVP capture" fmt=pct0 contentType=colorscale />
  <Column id=contested_eur title="Contested €" fmt=eur0 />
  <Column id=genuine_contested_eur title="Genuine on contested" fmt=eur0 />
  <Column id=bvp_eur title="BVP €" fmt=eur0 />
  <Column id=pairs_both_sold title="Pairs both sold" fmt=num0 />
  <Column id=pairs_genuine_only title="Genuine-only pairs" fmt=num0 />
  <Column id=interpretation title="Readout" />
</DataTable>

For PN-level down-trade margin (oil filter etc.), see <a href="/aim-leakage">AIM &amp; BVP Leakage → Section C+</a>.
