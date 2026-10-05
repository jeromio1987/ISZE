"""Detail behind each jp_vin_shipments share: series x gvw_t crosstab per market."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
v = pd.read_csv(ROOT / "01_data" / "07_UIO" / "vin" / "VIN_register.csv", low_memory=False)
v["code"] = v["db_code"].astype(str).str.upper().str.strip()
v["ser"] = v["series"].astype(str).str.upper().str.strip()
v["gvw"] = pd.to_numeric(v["gvw_t"], errors="coerce")

for c in ["PT", "MT", "CY", "BE", "GR", "IE", "DE"]:
    g = v[v.code == c]
    if g.empty:
        continue
    print("=" * 70)
    print(f"{c}   rows={len(g)}   gvw_t_source={g.gvw_t_source.value_counts().to_dict()}")
    ct = pd.crosstab(g.ser, g.gvw, dropna=False)
    print(ct.to_string())
    print("  iszJ model names:", g.iszj_model_name.value_counts(dropna=False).head(8).to_dict())
    print()
