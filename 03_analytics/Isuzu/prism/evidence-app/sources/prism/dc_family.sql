-- Precomputed at build time: revenue by product family × demand class.
-- Same heavy demand_classification × bvp_dim join as lumpy_vor, aggregated to a
-- few dozen rows so the BI Gallery page doesn't join 177K rows in the browser.
select d.product_family, c.demand_class,
  sum(c.total_revenue_eur)::double as rev
from read_csv_auto('data/derived/demand_classification.csv') c
join read_csv_auto('data/derived/bvp_pn_dimension.csv') d
  on cast(cast(c.part_number as bigint) as varchar) = cast(d.part_number as varchar)
group by 1, 2
