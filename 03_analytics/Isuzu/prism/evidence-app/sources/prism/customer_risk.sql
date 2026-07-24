select
  rank, year, distributor_code,
  risk_score::double            as risk_score,
  net_sales_eur::double         as net_sales_eur,
  eucon_undercut_pct::double    as eucon_undercut_pct,
  high_risk_rev_pct::double     as high_risk_rev_pct,
  contested_bvp_capture::double as contested_bvp_capture,
  vor_urgent_share::double      as vor_urgent_share,
  eucon_undercut_rev_eur::double as eucon_undercut_rev_eur,
  contested_eur::double         as contested_eur
from read_csv_auto('data/derived/db_aftersales_risk.csv')
