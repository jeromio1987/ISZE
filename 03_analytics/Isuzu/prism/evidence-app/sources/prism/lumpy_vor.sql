-- Precomputed at build time: spiky-demand share × urgent (VOR) line share × revenue,
-- per product family. Heavy 177K-row join lives here (Node DuckDB), so the page
-- reads only ~7 rows instead of joining demand_classification in the browser.
with dc as (
  select d.product_family,
    sum(c.total_revenue_eur) as rev,
    sum(case when c.demand_class in ('lumpy','intermittent') then c.total_revenue_eur else 0 end) as spiky_rev
  from read_csv_auto('data/derived/demand_classification.csv') c
  join read_csv_auto('data/derived/bvp_pn_dimension.csv') d
    on cast(cast(c.part_number as bigint) as varchar) = cast(d.part_number as varchar)
  group by 1
),
v as (
  select product_family, sum(vor_line_count) as vl, sum(total_line_count) as tl
  from read_csv_auto('data/derived/vor_airfreight_risk.csv')
  where year = (select max(year) from read_csv_auto('data/derived/vor_airfreight_risk.csv'))
  group by 1
)
select dc.product_family,
  dc.rev::double as rev,
  (spiky_rev / nullif(rev,0))::double as spiky_share,
  (v.vl / nullif(v.tl,0))::double as vor_pct
from dc join v on dc.product_family = v.product_family
where rev > 0
order by rev desc
