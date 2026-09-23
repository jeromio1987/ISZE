"""V20 - VIN register detail by market x year x series (READ ONLY)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd

P = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\07_UIO\vin\VIN_register.parquet"
df = pd.read_parquet(P)
print("cols:", list(df.columns))
print("rows:", len(df))

key = None
for c in ('cohort_year', 'invoice_year', 'reg_year', 'year', 'cohort_date'):
    if c in df.columns:
        key = c; break
print("year column:", key)

if key:
    df['_y'] = pd.to_datetime(df[key], errors='coerce').dt.year if 'date' in key else df[key]
    piv = df.pivot_table(index=['db_label'], columns='_y', values='vin' if 'vin' in df.columns else df.columns[0],
                         aggfunc='count', fill_value=0)
    print("\n=== VIN shipments by market x year ===")
    print(piv.to_string())

    print("\n=== by market x year x series ===")
    if 'series' in df.columns:
        print(df.pivot_table(index=['db_label', 'series'], columns='_y',
                             values=df.columns[0], aggfunc='count', fill_value=0).to_string())

    print("\n=== by market x year x gvw_t ===")
    if 'gvw_t' in df.columns:
        print(df.pivot_table(index=['db_label', 'gvw_t'], columns='_y',
                             values=df.columns[0], aggfunc='count', fill_value=0).to_string())

print("\n=== Germany rows ===")
de = df[df['db_label'].astype(str).str.contains('erm', case=False, na=False)]
print(de.to_string()[:4000] if len(de) else "none")
