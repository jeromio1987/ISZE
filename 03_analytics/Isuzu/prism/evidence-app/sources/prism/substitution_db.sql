-- TURKEY excluded by design: not an ISZE distributor (stray billing lines only)
select * from read_csv_auto('data/derived/substitution_by_db_year.csv')
where upper(distributor_code) <> 'TURKEY'
