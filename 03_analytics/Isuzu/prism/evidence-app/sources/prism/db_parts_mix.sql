select
  distributor_code,
  year,
  total_eur,
  bvp_eur,
  genuine_contested_eur,
  genuine_only_eur,
  bvp_pct,
  genuine_contested_pct,
  genuine_only_pct,
  contested_eur,
  contested_bvp_capture
from read_parquet('data/derived/db_parts_mix_classification.parquet')
