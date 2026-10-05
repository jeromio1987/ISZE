"""I Motors: ISZE billed vs sales-to-dealer — full comparison (read-only)."""
from __future__ import annotations
import pathlib
import pandas as pd
import numpy as np

R = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = R / "01_data" / "00_derived"

def norm(s):
    return (
        s.astype(str).str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.lstrip("0")
        .replace("", "0")
    )

def fam(c):
    c = str(c)
    if c.startswith("brake_pad"):
        return "brake_pad"
    if c.startswith("brake_rotor") or c.startswith("brake_disc"):
        return "brake_rotor"
    if c.startswith("brake_shoe") or c.startswith("brake_lining"):
        return "brake_shoe"
    if c in ("oil_filter", "fuel_filter", "air_filter", "clutch_kit"):
        return c
    return None

FAMS = [
    "oil_filter", "fuel_filter", "air_filter",
    "brake_pad", "brake_rotor", "brake_shoe", "clutch_kit",
]
LABEL = {
    "oil_filter": "Oil filters",
    "fuel_filter": "Fuel filters",
    "air_filter": "Air filters",
    "brake_pad": "Brake pads",
    "brake_rotor": "Brake rotors",
    "brake_shoe": "Brake shoes",
    "clutch_kit": "Clutch kits",
}

cat = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str, usecols=["part_number", "pms_category"])
cat["pn"] = norm(cat.part_number)
cat = cat[cat.pms_category.notna() & (cat.pms_category != "not_a_service_family")].drop_duplicates("pn")
cat["fam"] = cat.pms_category.map(fam)
cat_f = cat[cat.fam.notna()][["pn", "fam"]]

# Genuine / BVP
gb = None
for cand in ("genuine_bvp_crossref.csv", "genuine_bvp_crossref.parquet"):
    p = DER / cand
    if p.exists():
        gb = pd.read_csv(p, dtype=str) if cand.endswith(".csv") else pd.read_parquet(p)
        break

# Billing
cols = ["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value"]
sf = pd.read_parquet(DER / "sales_fact.parquet", columns=cols)
# try saty if present
try:
    sf2 = pd.read_parquet(DER / "sales_fact.parquet", columns=cols + ["saty"])
    sf = sf2
    has_saty = True
except Exception:
    has_saty = False

pt = sf[sf.sold_to_sap.isin([519, 92])].copy()
if has_saty:
    pt = pt[~pt.saty.isin(["CR", "RE"])].copy()
pt["pn"] = norm(pt.part_number)
pt["billing_date"] = pd.to_datetime(pt.billing_date)
pt["m"] = pt.billing_date.dt.to_period("M")
pt["fy"] = pt.billing_date.dt.year + (pt.billing_date.dt.month >= 4).astype(int)

# Sales to dealer
so = pd.concat([
    pd.read_csv(DER / f"dealer_sellout_long_PORTUGAL_{p}.csv", dtype={"part_number": str})
    for p in ("CY2025", "CY2026YTD")
])
so = so[so.period_grain == "month"].copy()
so["pn"] = norm(so.part_number)
so["m"] = pd.PeriodIndex(so.period, freq="M")
so["fy"] = so["m"].map(lambda p: p.year + (1 if p.month >= 4 else 0))
so["qty"] = pd.to_numeric(so.qty, errors="coerce").fillna(0)

print("=" * 72)
print("COVERAGE / WINDOWS")
print("=" * 72)
print(f"Billed max date: {pt.billing_date.max().date()}")
print(f"Billed min date: {pt.billing_date.min().date()}")
print(f"STD months: {so.m.min()} .. {so.m.max()}")
print(f"Billed rows (519+92): {len(pt):,}")
print(f"STD rows: {len(so):,}")

# Overlap windows
windows = {
    "CY2025": ("2025-01", "2025-12"),
    "CY2026 Jan-Aug": ("2026-01", "2026-08"),
    "FY2026 (Apr25-Mar26)": ("2025-04", "2026-03"),
    "FY2027 YTD (Apr-Aug26)": ("2026-04", "2026-08"),
    "Apr-Aug 2025": ("2025-04", "2025-08"),
    "Apr-Aug 2026": ("2026-04", "2026-08"),
}

def slice_m(df, start, end, col="m"):
    s, e = pd.Period(start, "M"), pd.Period(end, "M")
    return df[(df[col] >= s) & (df[col] <= e)]

print("\n" + "=" * 72)
print("HEADLINE: billed euros vs sales-to-dealer pieces (pieces are not a KPI)")
print("=" * 72)
print(f"{'Window':<28} {'Billed EUR':>14} {'Billed qty':>12} {'STD qty':>12} {'qty ratio B/STD':>14}")
for name, (a, b) in windows.items():
    bi = slice_m(pt, a, b)
    so_i = slice_m(so, a, b)
    be = bi.net_sales_value.sum()
    bq = bi.billed_qty.sum()
    sq = so_i.qty.sum()
    ratio = (bq / sq) if sq else float("nan")
    print(f"{name:<28} {be:14,.0f} {bq:12,.0f} {sq:12,.0f} {ratio:14.3f}")

# Monthly series for Apr25-Aug26
print("\n" + "=" * 72)
print("MONTHLY: billed EUR + qty vs STD qty (2025-01 .. 2026-08)")
print("=" * 72)
months = pd.period_range("2025-01", "2026-08", freq="M")
bm = pt.groupby("m").agg(billed_eur=("net_sales_value", "sum"), billed_qty=("billed_qty", "sum"))
sm = so.groupby("m").agg(std_qty=("qty", "sum"))
mon = pd.DataFrame(index=months).join(bm, how="left").join(sm, how="left").fillna(0)
mon["ratio"] = np.where(mon.std_qty > 0, mon.billed_qty / mon.std_qty, np.nan)
print(f"{'Month':<10} {'Billed EUR':>12} {'Billed qty':>12} {'STD qty':>12} {'B/STD':>8}")
for m, r in mon.iterrows():
    print(f"{str(m):<10} {r.billed_eur:12,.0f} {r.billed_qty:12,.0f} {r.std_qty:12,.0f} {r.ratio:8.3f}")

# Family comparison in overlapping windows
print("\n" + "=" * 72)
print("SERVICE FAMILIES: billed units vs STD units")
print("=" * 72)

def fam_table(a, b, title):
    bi = slice_m(pt, a, b).assign(pn=lambda d: d.pn).merge(cat_f, on="pn")
    so_i = slice_m(so, a, b).merge(cat_f, on="pn")
    b_agg = bi.groupby("fam").agg(billed_qty=("billed_qty", "sum"), billed_eur=("net_sales_value", "sum"))
    s_agg = so_i.groupby("fam").agg(std_qty=("qty", "sum"))
    t = pd.DataFrame(index=FAMS).join(b_agg, how="left").join(s_agg, how="left").fillna(0)
    t["ratio"] = np.where(t.std_qty > 0, t.billed_qty / t.std_qty, np.nan)
    t["gap_qty"] = t.std_qty - t.billed_qty  # positive = dealers offtake > ISZE billed (destock or other source)
    print(f"\n--- {title} ({a} .. {b}) ---")
    print(f"{'Family':<14} {'Billed EUR':>12} {'Billed qty':>12} {'STD qty':>12} {'B/STD':>8} {'STD-Billed':>12}")
    for fam_k, r in t.iterrows():
        print(f"{LABEL[fam_k]:<14} {r.billed_eur:12,.0f} {r.billed_qty:12,.0f} {r.std_qty:12,.0f} {r.ratio:8.3f} {r.gap_qty:12,.0f}")
    return t

t_fy26 = fam_table("2025-04", "2026-03", "FY2026")
t_fy27 = fam_table("2026-04", "2026-08", "FY2027 YTD Apr-Aug")
t_aa25 = fam_table("2025-04", "2025-08", "Apr-Aug 2025")
t_aa26 = fam_table("2026-04", "2026-08", "Apr-Aug 2026")
t_cy25 = fam_table("2025-01", "2025-12", "CY2025")

# PN overlap: sold to dealers but not billed / billed but not sold
print("\n" + "=" * 72)
print("PN SET OVERLAP (FY2026 Apr25-Mar26)")
print("=" * 72)
a, b = "2025-04", "2026-03"
bi = slice_m(pt, a, b)
so_i = slice_m(so, a, b)
b_pn = set(bi.pn.unique())
s_pn = set(so_i.pn.unique())
both = b_pn & s_pn
only_b = b_pn - s_pn
only_s = s_pn - b_pn
print(f"PNs billed: {len(b_pn):,} | PNs in STD: {len(s_pn):,} | both: {len(both):,} | billed-only: {len(only_b):,} | STD-only: {len(only_s):,}")

# Value of billed-only and qty of STD-only
be_only = bi[bi.pn.isin(only_b)].net_sales_value.sum()
bq_only = bi[bi.pn.isin(only_b)].billed_qty.sum()
sq_only = so_i[so_i.pn.isin(only_s)].qty.sum()
print(f"Billed-only EUR: {be_only:,.0f} ({bq_only:,.0f} pcs) — stocked / not yet sold to dealers, or not in their file")
print(f"STD-only qty: {sq_only:,.0f} pcs across {len(only_s):,} PNs — dealers sold parts we did not bill in-window (prior stock / other source)")

# Top STD-only by qty (with family if known)
so_only = so_i[so_i.pn.isin(only_s)].groupby("pn").qty.sum().sort_values(ascending=False).head(15)
so_only = so_only.reset_index().merge(cat[["pn", "pms_category"]], on="pn", how="left")
print("\nTop 15 STD-only PNs by qty (FY2026):")
for _, r in so_only.iterrows():
    print(f"  {r.pn:<14} {r.qty:8,.0f}  {r.pms_category}")

# Top billed families overall EUR FY2026
print("\n" + "=" * 72)
print("TOP BILLED FAMILIES BY EUR (FY2026) — all catalog families with spend")
print("=" * 72)
bi = slice_m(pt, "2025-04", "2026-03").merge(cat[["pn", "pms_category"]], on="pn", how="left")
bi["fam_raw"] = bi.pms_category.fillna("unclassified")
top = bi.groupby("fam_raw").agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum")).sort_values("eur", ascending=False).head(20)
for fam_k, r in top.iterrows():
    print(f"{str(fam_k)[:40]:<40} {r.eur:12,.0f} EUR  {r.qty:10,.0f} pcs")

# Align with order_vs_sales_to_dealer already on disk
print("\n" + "=" * 72)
print("EXISTING order_vs_sales_to_dealer_summary (Portugal 2026 Jan-Aug)")
print("=" * 72)
ovs = pd.read_csv(DER / "order_vs_sales_to_dealer_summary.csv")
row = ovs[ovs.db == "PORTUGAL"].iloc[0]
print(f"order_eur={row.order_eur:,.0f}  sell_eur_est={row.sell_eur_est_at_order_price:,.0f}")
print(f"order_qty={row.order_qty:,.0f}  sell_qty={row.sell_qty:,.0f}  ratio={row.order_over_sell_qty:.3f}")
print(f"pn_both={row.pn_both} pn_order_only={row.pn_order_only} pn_sell_only={row.pn_sell_only}")
print(f"urgent_eur_share={row.urgent_eur_share:.1%}")

# Genuine/BVP in STD if available
if gb is not None:
    print("\n" + "=" * 72)
    print("GENUINE vs BVP in sales-to-dealer (if crossref joins)")
    print("=" * 72)
    print("crossref columns:", list(gb.columns)[:20])
    # try common column names
    pn_col = next((c for c in gb.columns if c.lower() in ("part_number", "pn", "material")), None)
    flag_col = next((c for c in gb.columns if "bvp" in c.lower() or "line" in c.lower() or "genuine" in c.lower() or "mix" in c.lower()), None)
    print(f"pn_col={pn_col} flag_col={flag_col}")
    if pn_col:
        gbx = gb.copy()
        gbx["pn"] = norm(gbx[pn_col])
        # pick a type column
        type_col = None
        for c in gb.columns:
            cl = c.lower()
            if cl in ("line_type", "part_line", "genuine_bvp", "classification", "bvp_flag", "is_bvp"):
                type_col = c
                break
        if type_col is None:
            # peek unique-ish columns
            for c in gb.columns:
                u = gbx[c].nunique()
                if 2 <= u <= 8 and c != pn_col:
                    print(f"  candidate {c}: {gbx[c].value_counts().head(6).to_dict()}")
        else:
            so_g = so.merge(gbx[["pn", type_col]].drop_duplicates("pn"), on="pn", how="left")
            for name, (a, b) in [("FY2026", ("2025-04", "2026-03")), ("FY2027 YTD", ("2026-04", "2026-08"))]:
                s = slice_m(so_g, a, b)
                print(f"\n{name} STD qty by {type_col}:")
                print(s.groupby(type_col, dropna=False).qty.sum().sort_values(ascending=False).head(10))

print("\nDONE")
