"""Read-only probe 2: columns and family content of both AIM pairs, on the part numbers the pages use."""
import os

import pandas as pd

DER = r"01_data\00_derived"


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


PLACE = {"", "nan", "none", "unknown", "unknown review", "null"}

for name in ["AIM_Master_PN_Categories_Figkey_20260921.csv",
             "AIM_Master_PN_Categories_Figkey_20260924.csv"]:
    p = os.path.join(DER, name)
    head = pd.read_csv(p, dtype=str, low_memory=False, nrows=5)
    print("=" * 100)
    print(name)
    print("columns:", list(head.columns))
    print(head[["part_number", "aim_level_1", "aim_level_2", "aim_level_3", "line_kind"]].to_string())
    full = pd.read_csv(p, dtype=str, low_memory=False)
    print("rows:", len(full))
    l1 = full["aim_level_1"].fillna("").astype(str).str.strip()
    print("distinct aim_level_1 (raw, top 15):")
    print(l1.value_counts().head(15).to_string())

# the part numbers the deep dive / comparison pages actually plot:
# everything in the sales-to-dealer month rows for the six distributors in scope
stems = ["_PORTUGAL_CY2025", "_PORTUGAL_CY2026YTD", "_IRELAND_CY2025", "_IRELAND_CY2026YTD",
         "_ITUK_CY2023", "_ITUK_CY2024", "_ITUK_network_CY2025", "_ITUK_CY2026YTD",
         "_IUK_CY2025", "_IUK_CY2026YTD", "_UTI_CY2025", "_UTI_CY2026YTD", "_GREECE_CY2025"]
pns = set()
for st in stems:
    f = os.path.join(DER, f"dealer_sellout_long{st}.csv")
    if not os.path.exists(f):
        print("missing", f)
        continue
    df = pd.read_csv(f, dtype=str, low_memory=False, usecols=["part_number", "period_grain"])
    df = df[df["period_grain"] == "month"]
    pns |= set(norm(df["part_number"]).unique())
print(f"\n== part numbers on the sales-to-dealer month rows: {len(pns):,}")

pr = pd.read_parquet(os.path.join(DER, "pricing_pr00_ie40.parquet"))
priced = set(norm(pr["part_number"]).unique())
print(f"== of those, also on the IE40 price extract: {len(pns & priced):,}")

for name in ["AIM_Master_PN_Categories_Figkey_20260921.csv",
             "AIM_Master_PN_Categories_Figkey_20260924.csv"]:
    a = pd.read_csv(os.path.join(DER, name), dtype=str, low_memory=False, usecols=[
        "part_number", "aim_level_1", "line_kind"])
    a["pn"] = norm(a["part_number"])
    a = a.drop_duplicates("pn")
    sub = a[a["pn"].isin(pns)]
    l1 = sub["aim_level_1"].fillna("").astype(str).str.strip().str.lower()
    real = int((~l1.isin(PLACE)).sum())
    print(f"{name}: of {len(sub):,} matched sales pns, {real:,} carry a real aim_level_1")
