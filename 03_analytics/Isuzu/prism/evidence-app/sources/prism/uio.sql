-- Units in Operation per distributor (the parc / demand ceiling).
-- uio_units is carried on the GPS spend-per-unit derived table.
select
  distributor_code,
  year,
  country,
  region,
  uio_units::double          as uio_units,
  total_sales_eur::double    as net_sales_eur,
  spend_per_unit_eur::double as spend_per_unit_eur,
  uio_source,
  coalesce(traffic_light_v9, traffic_light) as traffic_light,
  max_spend_eur::double as max_spend_eur,
  gps_capture_vs_max::double as gps_capture_vs_max,
  warranty_parts_eur::double as warranty_parts_eur,
  sales_ex_warranty_eur::double as sales_ex_warranty_eur,
  spend_per_unit_ex_warranty_eur::double as spend_per_unit_ex_warranty_eur,
  gps_capture_ex_warranty_vs_max::double as gps_capture_ex_warranty_vs_max,
  coalesce(traffic_light_v9_ex_warranty, traffic_light_v9, traffic_light) as traffic_light_ex_warranty,
  warranty_data_gap::boolean as warranty_data_gap
from read_csv_auto('data/derived/gps_spu_by_distributor.csv')
where upper(distributor_code) <> 'TURKEY'
