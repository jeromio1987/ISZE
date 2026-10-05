"""Block D - lock the headline numbers for the report, on the corrected parts base."""
from pathlib import Path

import pandas as pd

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
REL = D / "_releases" / "aim_pn_classification_release_2026-09-20.csv"
LIVE = D / "aim_pn_classification_20260920.csv"
NON = {"REBATE", "TRANSPORT", "LATE PAYMENT INTEREST", "SERVICE",
       "SERVICE FEE OUTSIDE EUROPE", "SERVICE FEE WITHIN EUROPE",
       "20MTGKIT", "60MTGKIT", "BOXES_ASC", "TOWEL_ASC", "BACKPACK", "NOTEBOOK",
       "PEN", "DISRACK01", "CORE_7.5", "CORE_9", "CORE_9.5"}
RESID = {"", "Unknown", "Unknown Review", "Unclassified"}

sf = pd.read_parquet(D / "sales_fact.parquet",
                     columns=["billing_date", "part_number", "net_sales_value"])
sf["d"] = pd.to_datetime(sf["billing_date"], errors="coerce")
sf["pn"] = sf["part_number"].astype(str).str.strip()
w = sf[(sf["d"] >= "2025-01-01") & (sf["d"] <= "2025-12-31")]
w = w[~w["pn"].isin(NON)]
w = w[~w["pn"].str.lstrip("0").str.startswith("5500")]
w = w[w["pn"].str[0].str.isdigit()]
e25 = w.groupby("pn")["net_sales_value"].sum()
tot = float(w["net_sales_value"].sum())
print(f"parts base 2025 EUR {tot:,.2f} on {e25.size:,} part numbers")


def rd(p, cols):
    t = pd.read_csv(p, dtype=str, keep_default_na=False, low_memory=False,
                    usecols=["part_number"] + cols)
    t["pn"] = t["part_number"].astype(str).str.strip()
    return t.drop_duplicates("pn").set_index("pn")[cols]


rel = rd(REL, ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
rel.columns = ["l1", "l2", "l3"]
live = rd(LIVE, ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
live.columns = ["l1", "l2", "l3"]
for lbl, t in (("release", rel), ("live overlay", live)):
    e = e25.reindex(t.index).fillna(0.0)
    res = e[t["l1"].isin(RESID)]
    named = e[~t["l1"].isin(RESID)]
    print(f"{lbl:<13} rows {len(t):>8,} | 2025 euro on a named family "
          f"EUR {named.sum():>14,.2f} ({100 * named.sum() / tot:.2f}%) | residual "
          f"EUR {res.sum():>12,.2f} ({100 * res.sum() / tot:.2f}%)")

j = rel.join(live, how="outer", lsuffix="_r", rsuffix="_l").fillna("")
j["e"] = e25.reindex(j.index).fillna(0.0)
ch = j[(j["l1_r"] != j["l1_l"]) | (j["l2_r"] != j["l2_l"]) | (j["l3_r"] != j["l3_l"])]
print()
print(f"changed rows {len(ch):,}   euro on them EUR {ch['e'].sum():,.2f}")
print(f"  euro moving from a residual label to a named family: "
      f"EUR {ch.loc[ch['l1_r'].isin(RESID) & ~ch['l1_l'].isin(RESID), 'e'].sum():,.2f}")
print(f"  euro moving from a named family to a residual label: "
      f"EUR {ch.loc[~ch['l1_r'].isin(RESID) & ch['l1_l'].isin(RESID), 'e'].sum():,.2f}")

# maintenance families, the ones the board and the paper use
MAINT = {"Brakes", "Clutch", "Maintenance Service"}
for lbl, t in (("release", rel), ("live overlay", live)):
    e = e25.reindex(t.index).fillna(0.0)
    m = e[t["l1"].isin(MAINT)]
    print(f"{lbl:<13} maintenance families (Brakes / Clutch / Maintenance Service) "
          f"2025 EUR {m.sum():>12,.2f} ({100 * m.sum() / tot:.2f}%)")
