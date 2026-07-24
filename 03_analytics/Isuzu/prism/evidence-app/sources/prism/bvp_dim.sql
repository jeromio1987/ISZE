select cast(part_number as varchar) as part_number, product_family
from read_csv_auto('data/derived/bvp_pn_dimension.csv')
