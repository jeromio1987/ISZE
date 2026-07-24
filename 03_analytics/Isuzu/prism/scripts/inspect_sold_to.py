import pandas as pd
df = pd.read_parquet(r"C:\Users\jerom\Desktop\claude\ISZE\Data\derived\sales_fact.parquet")
print("columns:", list(df.columns))
print("\nsold_to dtype:", df["sold_to"].dtype)
print("\ntop sold_to:")
print(df["sold_to"].astype(str).str.strip().value_counts().head(20))
