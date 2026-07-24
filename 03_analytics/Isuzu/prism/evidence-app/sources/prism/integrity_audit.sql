select
  distributor_code,
  year,
  spend_per_unit_eur::double as spend_per_unit_eur,
  spend_per_unit_ex_warranty_eur::double as spend_per_unit_ex_warranty_eur,
  warranty_parts_eur::double as warranty_parts_eur,
  gps_capture_vs_max::double as gps_capture_vs_max,
  gps_capture_ex_warranty_vs_max::double as gps_capture_ex_warranty_vs_max,
  traffic_light_v9,
  traffic_light_v9_ex_warranty,
  contested_bvp_capture::double as contested_bvp_capture,
  contested_eur::double as contested_eur,
  bvp_low_capture_verdict,
  oil_filter_capture::double as oil_filter_capture,
  pms_revenue_gap_eur::double as pms_revenue_gap_eur,
  traffic_light_shift_ex_warranty
from read_csv_auto('data/derived/_gps_integrity_audit_rows.csv')
