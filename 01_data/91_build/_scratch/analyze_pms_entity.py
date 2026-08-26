import pandas as pd
import numpy as np
import sys, io

sys.stdout.reconfigure(encoding="utf-8")

main = "c:/Users/jerom/Downloads/UMIUTI_Logistics_Study_v2.xlsx"
bo = "C:/Users/jerom/Desktop/claude/ISZE/01_data/08_Distributor/BO OVERVIEW - UNIVERSAL TRUCKS ISRAEL LTD 01-07-2026 (1).xlsx"
cat_path = "C:/Users/jerom/Desktop/claude/ISZE/01_data/00_derived/parts_catalog_dimension.csv"
bvp_path = "C:/Users/jerom/Desktop/claude/ISZE/01_data/00_derived/bvp_pn_dimension.csv"

out = []

def p(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)

# ---------- load ----------
df = pd.read_excel(main, sheet_name="Data (joined)", header=3)

def norm(s):
    s = str(s).strip()
    if s == "" or s.lower() == "nan":
        return None
    t = s.replace(".", "", 1)
    if t.isdigit():
        return str(int(float(s)))
    return s

df["mat"] = df["Material"].map(norm)

cat = pd.read_csv(cat_path, dtype=str)
bvp = pd.read_csv(bvp_path, dtype=str)
cat["pn"] = cat["part_number"].map(norm)
bvp["pn"] = bvp["part_number"].map(norm)
cat_pms = set(cat.loc[cat["pms_category"].fillna("").astype(str).str.strip().ne(""), "pn"])
bvp_pms = set(bvp.loc[bvp["pms_category"].fillna("").astype(str).str.strip().ne(""), "pn"])
all_pms = cat_pms | bvp_pms

# PMS category map (union)
cat_map = cat.dropna(subset=["pms_category"]).set_index("pn")["pms_category"].to_dict()
bvp_map = bvp.dropna(subset=["pms_category"]).set_index("pn")["pms_category"].to_dict()
pms_map = {**bvp_map, **cat_map}

# ---------- filter genuine + exclude rebate + entity known ----------
g = df[(df["BillT"] == "F2")
       & (~df["mat"].str.upper().str.contains("REBATE", na=False))
       & (df["Entity"].isin(["UMI", "UTI"]))].copy()
g["is_pms"] = g["mat"].isin(all_pms)

# line-level air/sea
air = g[g["MoT"] == "Air"]
sea = g[g["MoT"] == "Sea"]

# per part per entity metrics
def part_metrics(sub):
    agg = sub.groupby(["mat", "Entity"]).agg(
        air_bookings=("Bill.Doc.", lambda s: s.nunique()),
        air_value=("EUR Amount", "sum"),
        air_qty=("Qty", "sum"),
        air_weight=("Gross weight (kg)", "sum"),
    ).reset_index()
    return agg

air_agg = part_metrics(air)
sea_agg = sub_sea = sea.groupby(["mat", "Entity"]).agg(
    sea_bookings=("Bill.Doc.", "nunique"),
    sea_value=("EUR Amount", "sum"),
    sea_qty=("Qty", "sum"),
    sea_weight=("Gross weight (kg)", "sum"),
).reset_index()

# per part totals (both entities)
air_tot = air.groupby("mat").agg(
    air_bookings=("Bill.Doc.", "nunique"),
    air_value=("EUR Amount", "sum"),
).reset_index()
sea_tot = sea.groupby("mat").agg(
    sea_bookings=("Bill.Doc.", "nunique"),
    sea_value=("EUR Amount", "sum"),
).reset_index()

part = air_tot.merge(sea_tot, on="mat", how="outer").fillna(0)
part["air_bookings"] = part["air_bookings"].astype(int)
part["sea_bookings"] = part["sea_bookings"].astype(int)
part["avg_goods_per_air"] = part["air_value"] / part["air_bookings"].replace(0, np.nan)
part["is_pms"] = part["mat"].isin(all_pms)

# ---------- reproduce 250 cheap parts ----------
cheap = part[(part["air_bookings"] >= 5) & (part["avg_goods_per_air"] < 50)].copy()
cheap = cheap.sort_values(["air_bookings", "mat"], ascending=[False, True])
p("CHEAP PARTS count:", len(cheap), " PMS among them:", cheap["is_pms"].sum())

# ---------- reproduce top 80 flyers ----------
top80 = part.sort_values(["air_bookings", "mat"], ascending=[False, True]).head(80).copy()
p("TOP80: PMS among them:", top80["is_pms"].sum())

known9 = ["8983418670","1096750371","8980377310","8981240801","8980062550","1095833460","8975065390","8980781920","8983418610"]
known5 = ["8983418690","1471704851","1095833810","8983418620","8973652790"]

p("\n=== verification: known 9 in cheap list ===")
for m in known9:
    r = cheap[cheap["mat"] == m]
    if len(r):
        row = r.iloc[0]
        p(f"  {m}: air={row['air_bookings']} sea={row['sea_bookings']} air_val={row['air_value']:.2f} avg={row['avg_goods_per_air']:.2f}")
    else:
        p(f"  {m}: NOT IN CHEAP LIST  (air={part[part['mat']==m]['air_bookings'].values} avg={part[part['mat']==m]['avg_goods_per_air'].values})")

p("\n=== verification: known 5 in top80 ===")
for m in known5:
    r = top80[top80["mat"] == m]
    if len(r):
        row = r.iloc[0]
        p(f"  {m}: rank? air={row['air_bookings']} sea={row['sea_bookings']} air_val={row['air_value']:.2f}")
    else:
        ab = part[part["mat"]==m]["air_bookings"].values
        p(f"  {m}: NOT IN TOP80  (air_bookings={ab})")

# what's the cutoff for top 80 air bookings
p("\nTop80 air_bookings range:", top80["air_bookings"].min(), "-", top80["air_bookings"].max())

# ---------- entity splits ----------
def entity_split(part_list, label):
    p(f"\n===== ENTITY SPLIT: {label} =====")
    mats = part_list
    rows = []
    for m in mats:
        a = air_agg[air_agg["mat"] == m]
        s = sea_agg[sea_agg["mat"] == m]
        umi_air = a[a["Entity"]=="UMI"]["air_bookings"].sum()
        uti_air = a[a["Entity"]=="UTI"]["air_bookings"].sum()
        umi_air_val = a[a["Entity"]=="UMI"]["air_value"].sum()
        uti_air_val = a[a["Entity"]=="UTI"]["air_value"].sum()
        umi_sea = s[s["Entity"]=="UMI"]["sea_bookings"].sum()
        uti_sea = s[s["Entity"]=="UTI"]["sea_bookings"].sum()
        umi_sea_val = s[s["Entity"]=="UMI"]["sea_value"].sum()
        uti_sea_val = s[s["Entity"]=="UTI"]["sea_value"].sum()
        ent = "both" if (umi_air>0 and uti_air>0) else ("UMI" if umi_air>0 else ("UTI" if uti_air>0 else "none"))
        rows.append((m, ent, umi_air, uti_air, umi_sea, uti_sea,
                     umi_air_val, uti_air_val, umi_sea_val, uti_sea_val))
    for r in rows:
        m, ent, ua, ta, us, ts, uav, tav, usv, tsv = r
        p(f"{m}: entity={ent} | air: UMI={ua} UTI={ta} | sea: UMI={us} UTI={ts} | airval UMI={uav:.2f} UTI={tav:.2f} | seaval UMI={usv:.2f} UTI={tsv:.2f}")
    return rows

# entity split of full 250 and 9 PMS
full_air_entity = air.groupby("mat")["Entity"].apply(lambda s: set(s)).to_dict()
def ent_label(m):
    e = full_air_entity.get(m, set())
    if "UMI" in e and "UTI" in e: return "both"
    if "UMI" in e: return "UMI"
    if "UTI" in e: return "UTI"
    return "none"

cheap_ents = cheap["mat"].map(ent_label)
p("\nEntity split of 250 cheap parts (by air-booking entity):")
p(cheap_ents.value_counts().to_dict())

pms9 = cheap[cheap["mat"].isin(known9)]["mat"].tolist()
p("\nEntity split of 9 PMS cheap parts:")
p(pd.Series(pms9).map(ent_label).value_counts().to_dict())

entity_split(known9, "9 PMS cheap parts")

# top 5 PMS flyers entity split
entity_split(known5, "5 PMS top flyers")

# entity split of full 80 top flyers
p("\nEntity split of 80 top flyers (by air-booking entity):")
p(top80["mat"].map(ent_label).value_counts().to_dict())

# ================= WRITE =================
with open("C:/Users/jerom/Desktop/claude/ISZE/01_data/90_INBOX/_pms_entity_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("WROTE _pms_entity_report.txt")
print("\n".join(out))
