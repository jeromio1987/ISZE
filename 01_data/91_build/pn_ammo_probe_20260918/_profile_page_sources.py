"""Profile the four source files so the page is designed on facts."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

t = pd.read_csv(DER / "pms_tonnage_model.csv")
a = pd.read_csv(DER / "aim_evolution_model.csv")
g = pd.read_csv(DER / "gps_spu_by_distributor.csv")
c = pd.read_csv(DER / "pms_capture_by_db_year.csv")

print("### pms_tonnage_model")
print("markets:", sorted(t.distributor_code.unique()))
print("bands:", t[["band", "band_label"]].drop_duplicates().to_dict("records"))
print("lanes:", t.lane.value_counts().to_dict())
print("years:", sorted(t.year.unique()))
print("categories:", sorted(t.pms_category.unique()))
print("actual_is_market_level:", t.actual_is_market_level.value_counts().to_dict())
print("rows per market:")
print(t.groupby(["distributor_code", "lane"]).size().to_string())
print()
print("band x market presence (uio_units>0):")
p = t[t.uio_units > 0].pivot_table(index="distributor_code", columns="band",
                                   values="uio_units", aggfunc="max")
print(p.to_string())
print()
print("visits_per_year by band x lane:")
print(t.groupby(["lane", "band"]).visits_per_year.agg(["min", "max"]).to_string())
print()
print("### aim_evolution_model")
print("markets:", len(a.distributor_code.unique()), sorted(a.distributor_code.unique()))
print("clocks:", a.clock.value_counts().to_dict())
print("periods by clock:")
for cl, gg in a.groupby("clock"):
    print(" ", cl, sorted(gg.period.astype(str).unique()))
print("aim_l1 (%d):" % a.aim_l1.nunique(), sorted(a.aim_l1.dropna().unique()))
print("aim_l2 count:", a.aim_l2.nunique())
print("eur total by clock (EUR m):")
print((a.groupby("clock").billed_eur.sum() / 1e6).round(2).to_string())
print()
print("### gps_spu_by_distributor")
print("markets:", sorted(g.distributor_code.unique()))
print("years:", sorted(g.year.unique()))
print("has max_spend:", int(g.max_spend_eur.notna().sum()), "of", len(g))
print("has gps_capture_vs_max:", int(g.gps_capture_vs_max.notna().sum()))
print()
print("### pms_capture_by_db_year")
print("markets:", len(c.distributor_code.unique()), "years:", sorted(c.year.unique()),
      "line_types:", sorted(c.line_type.unique()))
