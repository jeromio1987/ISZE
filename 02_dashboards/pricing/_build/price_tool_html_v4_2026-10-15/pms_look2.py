import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE"); H = Path(__file__).parent
DER = ISZE / "01_data/00_derived"
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 40)
P = pd.read_pickle(H / "_pms_parts.pkl")
enq = pd.read_parquet(DER / "pricing_pn_enquiry.parquet", columns=["part_number", "source"]); enq["pn"] = enq.part_number.astype(str).str.strip(); enq = enq.drop_duplicates("pn").set_index("pn")
P["src"] = P.pn.map(enq.source)
flt = P[P.cat.isin(["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter"])].copy()
print("FILTER PARTS", len(flt), "billed", round(flt.b.sum()))
print(flt.groupby(["cat", "src"], dropna=False).apply(lambda d: pd.Series({"parts": len(d), "billed": d.b.sum(), "own_step": (d.b * d.cp).sum() / d.b.sum(), "move": d.x.sum() / d.b.sum()}), include_groups=False).round(4).to_string())
fb = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str)
fb["eur"] = pd.to_numeric(fb.eur_all_markets, errors="coerce")
m = flt.merge(fb[["pn", "family", "resolution", "confidence", "family_label"]], on="pn", how="left")
print("\nfilter parts with a vehicle family:", int(m.family.notna().sum()), "of", len(m), "| billed with family:", round(m.b[m.family.notna()].sum()), "of", round(m.b.sum()))
print(m.groupby(["cat", "resolution"], dropna=False).apply(lambda d: pd.Series({"parts": len(d), "billed": d.b.sum()}), include_groups=False).round(0).to_string())
print(m.groupby(["cat", "family"], dropna=False).apply(lambda d: pd.Series({"parts": len(d), "billed": d.b.sum(), "own_step": (d.b * d.cp).sum() / d.b.sum()}), include_groups=False).round(4).to_string())
va = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str)
va = va[va.pn.isin(flt.pn)]
print("\nband applicability rows for filter parts:", len(va)); print(va.groupby(["pms_category", "band_status"], dropna=False).size().to_string())
print(va[["pn", "pms_category", "vehicle_bands", "band_status", "exclusivity_established"]].head(8).to_string(index=False))
cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
c = cap[(cap.year == 2025) & (cap.line_type == "total") & cap.pms_category.isin(["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter"])]
print("\ncapture 2025 total by market, filters:"); print(c.pivot_table(index="distributor_code", columns="pms_category", values="capture_rate").round(2).to_string())
dr = pd.read_csv(ISZE / "02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29/room_to_raise_2026-10-02/dealer_response_by_category_2026-10-02.csv")
print("\ndealer response, Maintenance Service:"); print(dr[dr.aim_l1.str.contains("Maintenance", na=False)].round(3).to_string(index=False))
print("\nbiggest filter parts:"); print(flt.sort_values("b", ascending=False)[["pn", "desc", "cat", "src", "b", "cp", "x"]].head(12).round(3).to_string(index=False))
