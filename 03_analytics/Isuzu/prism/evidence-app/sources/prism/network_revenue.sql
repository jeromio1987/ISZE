select year,
  sum(net_sales_value) as net_sales,
  count(*) as lines,
  count(distinct part_number) as parts,
  count(distinct sold_to_sap) as accounts
from read_parquet('data/derived/sales_fact.parquet')
group by 1
