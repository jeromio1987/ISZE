import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.data_prep import load_distributor_mapping
from modules.sales_loader import load_prism_sales

m = load_distributor_mapping("data/distributor_master_mapping.csv")
df, src = load_prism_sales(m)
print("source:", src)
print("distributors:", df["distributor_code"].value_counts().head(15))
print("unmapped:", (df["distributor_code"] == "UNMAPPED").sum())
