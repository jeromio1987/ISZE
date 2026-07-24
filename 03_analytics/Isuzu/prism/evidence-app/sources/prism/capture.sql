select distributor_code, year, line_type, actual_qty, expected_qty
from read_csv_auto('data/derived/pms_capture_by_db_year.csv')
