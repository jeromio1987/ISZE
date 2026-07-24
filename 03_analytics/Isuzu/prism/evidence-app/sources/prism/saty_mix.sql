select saty,
  count(*) as line_count,
  sum(net_sales_value) as revenue_eur,
  sum(billed_qty) as qty
from read_parquet('data/derived/sales_fact.parquet')
where net_sales_value > 0 and saty is not null
group by 1
order by revenue_eur desc
