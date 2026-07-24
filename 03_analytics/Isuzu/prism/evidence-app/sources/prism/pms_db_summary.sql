select
  distributor_code,
  country,
  year,
  uio_units::double as uio_units,
  capture_rate_total_wtd::double as capture_rate_total_wtd,
  capture_rate_genuine_wtd::double as capture_rate_genuine_wtd,
  revenue_gap_eur_sum::double as revenue_gap_eur_sum,
  oil_filter_capture::double as oil_filter_capture,
  top_gap_categories
from read_csv_auto('data/derived/pms_summary_by_db.csv')
