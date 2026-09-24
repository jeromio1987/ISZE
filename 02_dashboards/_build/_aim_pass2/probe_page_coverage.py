"""Read-only probe 3: what the four pages actually plot, and the AIM coverage under each pair.

Reproduces just enough of the two builders' part-number dimension (the union of billing rows and
sales-to-dealer rows after the supersession and scope rules) to measure the coverage change from
swapping AIM_Master_PN_Categories_Figkey_20260921.csv for the 2026-09-24 file.
"""
import os

import numpy as np
import pandas as pd

DER = r"01_data\00_derived"

SELLOUT = {
    "PORTUGAL": ["_PORTUGAL_CY2025", "_PORTUGAL_CY2026YTD"],
    "IRELAND": ["_IRELAND_CY2025", "_IRELAND_CY2026YTD"],
    "ITUK": ["_ITUK_CY2023", "_ITUK_CY2024", "_ITUK_network_CY2025", "_ITUK_CY2026YTD"],
    "IUK": ["_IUK_CY2025", "_IUK_CY2026YTD"],
    "UTI": ["_UTI_CY2025", "_UTI_CY2026YTD"],
    "GREECE": ["_GREECE_CY2025"],
}
EXCLUDE_SATY = ["CR", "RE", "DR", "ZDR", "FD"]


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


PLACE = {"", "nan", "none", "unknown", "unknown review", "null"}

# distributor map
dd = pd.read_csv(os.path.join(DER, "distributor_dimension.csv"), dtype=str, low_memory=False)
dd = dd[dd["distributor_code"].notna()].copy()
dd["sap"] = dd["sold_to_sap"].str.replace(r"\.0$", "", regex=True).str.strip()
dd = dd.drop_duplicates("sap")
sap2db = dd.set_index("sap")["distributor_code"].to_dict()

# price / supersession
pr = pd.read_parquet(os.path.join(DER, "pricing_pr00_ie40.parquet"))
pr["pn"] = norm(pr["part_number"])
pr["new"] = norm(pr["newest_pn"])
pr["sp"] = pd.to_numeric(pr["sp_eur"], errors="coerce")
pr.loc[pr["sp"] <= 0, "sp"] = np.nan
pr = pr.drop_duplicates("pn")
sup_map = pr.set_index("pn")["new"]
priced = set(pr["sp"].dropna().index)

AIM_FILES = ["AIM_Master_PN_Categories_Figkey_20260921.csv",
             "AIM_Master_PN_Categories_Figkey_20260924.csv"]

AIMS = {}
for name in AIM_FILES:
    a = pd.read_csv(os.path.join(DER, name), dtype=str, low_memory=False)
    a["pn"] = norm(a["part_number"])
    a = a.drop_duplicates("pn")
    AIMS[name] = a.set_index("pn")

# billing, scoped to the six distributors
sf = pd.read_parquet(os.path.join(DER, "sales_fact.parquet"),
                     columns=["sold_to_sap", "part_number", "saty"])
sf["sap"] = sf["sold_to_sap"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
sf["db"] = sf["sap"].map(sap2db)
sf = sf[sf["db"].isin(SELLOUT)].copy()
sf = sf[~sf["saty"].isin(EXCLUDE_SATY) & sf["saty"].notna()]
sf["pn_raw"] = norm(sf["part_number"])

# sales to dealer, month rows only
frames = []
for db, stems in SELLOUT.items():
    for st in stems:
        f = os.path.join(DER, f"dealer_sellout_long{st}.csv")
        df = pd.read_csv(f, dtype=str, low_memory=False,
                         usecols=["part_number", "period_grain"])
        df = df[df["period_grain"] == "month"]
        df["db"] = db
        df["pn_raw"] = norm(df["part_number"])
        frames.append(df)
so = pd.concat(frames, ignore_index=True)

for aim_name in AIM_FILES:
    aim = AIMS[aim_name]
    aim_pns = set(aim.index)
    for run, dbs in (("PORTUGAL", ["PORTUGAL"]), ("ALL", sorted(SELLOUT))):
        b = sf[sf["db"].isin(dbs)]["pn_raw"]
        s = so[so["db"].isin(dbs)]["pn_raw"]
        raw = pd.concat([b, s], ignore_index=True)
        nw = raw.map(sup_map)
        take = nw.notna() & (nw != raw) & nw.isin(aim_pns) & nw.isin(priced)
        canon = np.where(take, nw, raw)
        pns = pd.Index(sorted(set(canon)))
        sub = aim.reindex(pns)
        l1 = sub["aim_level_1"].fillna("").astype(str).str.strip().str.lower()
        real = int((~l1.isin(PLACE)).sum())
        kind = sub["line_kind"].fillna("").astype(str).str.strip()
        parts = pns[kind.eq("part").values]
        l1p = l1[kind.eq("part").values]
        real_part = int((~l1p.isin(PLACE)).sum())
        print(f"{run:<9} {aim_name}: part numbers in use {len(pns):>6,} | "
              f"real aim_level_1 {real:>6,} | of the {len(parts):>6,} line_kind=part rows, "
              f"{real_part:>6,} carry a real aim_level_1")
    print()
