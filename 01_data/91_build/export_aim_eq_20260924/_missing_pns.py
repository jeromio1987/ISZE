"""Which classified part numbers are absent from the AIM master, and are they
present in the PR00 catalogue (so they belong on the spine)?"""
import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
c = pd.read_csv(ROOT + r"\01_data\91_build\export_aim_eq_20260924\classified.csv", dtype=str)
c["pn"] = c["pn"].str.strip().str.upper()
f = c[c["aim_level_1"].fillna("") != ""].drop_duplicates("pn")

m = pd.read_csv(ROOT + r"\01_data\00_derived\aim_master_v2.csv", dtype=str, low_memory=False)
on_master = set(m["part_number"].str.strip().str.upper())

meta = pd.read_csv(ROOT + r"\01_data\91_build\export_aim_eq_20260924\queue.meta.json") if False else None
pr = pd.read_csv(ROOT + r"\01_data\00_derived\pr00_classification.csv", dtype=str, low_memory=False)
pr["pn"] = pr["pn_norm"].str.strip().str.upper().str.zfill(10)
in_pr00 = set(pr["pn"])

missing = f[~f["pn"].isin(on_master)].copy()
missing["in_pr00_catalogue"] = missing["pn"].isin(in_pr00)
print(f"classified part numbers absent from the master: {len(missing)}")
print(missing["in_pr00_catalogue"].value_counts().to_string())
print()
print(missing[["pn", "Description", "aim_level_1", "aim_level_2", "aim_level_3",
               "in_pr00_catalogue"]].to_string(index=False))
