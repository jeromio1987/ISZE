"""Scrape worklist for the market-data gap (ITUK + Portugal, brake pads + oil filters).
Reads: price_observations.parquet (Eucon loaders only), U19b coverage/empty-PN csvs.
Writes: 01_data/90_INBOX/MARKET_SCRAPE_WORKLIST_20261007.csv (+ _pn_summary csv). Eucon rows stay local."""
import pandas as pd
R='C:/Users/jerom/Desktop/claude/ISZE/'
U='C:/Users/jerom/Desktop/claude/_worktrees/ISZE_u19b/01_data/00_derived/'
d=pd.read_parquet(R+'01_data/00_derived/price_observations.parquet'); d['part_no']=d.part_no.astype(str)
emp=pd.read_csv(U+'market_data_gap_empty_pns_20261006.csv',dtype=str)
cov=pd.read_csv(U+'market_data_gap_coverage_20261006.csv',dtype=str)
base=pd.concat([emp[['part_number','market','distributor','pms_category','eur_all_billed_all_markets']],
  cov[['part_number','market','distributor','pms_category']].assign(eur_all_billed_all_markets=None)]).drop_duplicates(['part_number','market'])
eur=emp.drop_duplicates('part_number').set_index('part_number').eur_all_billed_all_markets.astype(float)
eu=d[d.loader.str.startswith('eucon')&d.competitor_pn.notna()&d.competitor_brand.notna()]
eu=eu[eu.loader!='eucon_survey_2023']
cp=(eu.groupby(['part_no','competitor_brand','competitor_pn'])
      .agg(eucon_sources=('loader',lambda s:'|'.join(sorted(set(s)))),eucon_countries=('country',lambda s:'|'.join(sorted(set(s))))).reset_index())
w=base.merge(cp,left_on='part_number',right_on='part_no',how='left').drop(columns='part_no')
w['has_eucon_competitor_pn']=w.competitor_pn.notna()
w['family_billed_eur_all_markets']=w.part_number.map(eur)
w=w.sort_values(['market','family_billed_eur_all_markets','part_number'],ascending=[True,False,True])
w.to_csv(R+'01_data/90_INBOX/MARKET_SCRAPE_WORKLIST_20261007.csv',index=False)
s=(w.groupby(['market','pms_category','has_eucon_competitor_pn']).agg(pns=('part_number','nunique'),pairs=('competitor_pn','count')).reset_index())
print(s.to_string()); print(len(w),'rows;',w.part_number.nunique(),'PNs;',w.competitor_pn.nunique(),'distinct competitor PNs')
