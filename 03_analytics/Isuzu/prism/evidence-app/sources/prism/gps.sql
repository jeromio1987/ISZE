select distributor_code, year, spend_per_unit_eur
from read_csv_auto('data/derived/gps_spu_by_distributor.csv')
