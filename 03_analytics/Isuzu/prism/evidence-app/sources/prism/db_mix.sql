-- TURKEY excluded by design: not an ISZE distributor (stray billing lines only)
select * from read_csv_auto('data/derived/db_parts_mix_classification.csv')
where upper(distributor_code) <> 'TURKEY'
