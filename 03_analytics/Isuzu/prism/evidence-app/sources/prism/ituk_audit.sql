select
  year, distributor_code, pms_category, category_label,
  cast(part_number as varchar)   as part_number,
  pms_type, pms_model,
  actual_qty::double             as actual_qty,
  actual_rev_eur::double         as actual_rev_eur,
  share_of_category_qty::double  as share_of_category_qty,
  scope
from read_csv_auto('data/derived/ituk_pms_pn_audit.csv')
