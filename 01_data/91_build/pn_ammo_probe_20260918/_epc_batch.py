"""Build the EPC decode batch: which part numbers to look up, in what order, and what it buys.

The EPC returns, per part number, the vehicle families and model series it fits
('TRUCKS N' -> N-series, 'TRUCKS F&G' -> F-series). That is the tonnage link the billing
has no column for. The scraper already in the workspace drives the lookup; this decides
which part numbers are worth the time.
"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")

sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["_pn"] = sf.part_number.map(norm)
cy = int(pd.Timestamp.today().year) - 1
sf["is_cy"] = sf["year"] == cy
dimmap = pd.read_csv(DER + r"\distributor_dimension.csv")
sf["db"] = sf.sold_to_sap.map(dict(zip(dimmap.sold_to_sap, dimmap.distributor_code)))

book = sf.groupby("_pn").agg(
    pn=("part_number", "first"),
    eur_all=("net_sales_value", "sum"),
    units_all=("billed_qty", "sum"),
    markets=("db", "nunique"),
).reset_index()
cyb = sf[sf.is_cy].groupby("_pn").agg(eur_cy=("net_sales_value", "sum"),
                                      units_cy=("billed_qty", "sum")).reset_index()
book = book.merge(cyb, on="_pn", how="left").fillna({"eur_cy": 0, "units_cy": 0})
tot = book.eur_all.sum()

# Axis: PMS service category where we have one, else AIM L1.
dim = pd.read_csv(DER + r"\aim_master_v2.csv", dtype=str,
                  usecols=["part_number", "aim_l1", "aim_l2"], low_memory=False)
dim["_pn"] = dim.part_number.map(norm)
dim = dim.drop_duplicates("_pn")
pms = pd.read_csv(DER + r"\bvp_pn_dimension.csv", dtype=str, low_memory=False)
pms["_pn"] = pms.part_number.map(norm)
pms = pms[pms.pms_category.notna()].drop_duplicates("_pn")[["_pn", "pms_category"]]

book = book.merge(dim[["_pn", "aim_l1", "aim_l2"]], on="_pn", how="left")
book = book.merge(pms, on="_pn", how="left")

# Already resolved by the cross-reference? Then it may not need the EPC.
xref = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", dtype=str, low_memory=False)
xref["_pn"] = xref.genuine_pn.map(norm)
vm = xref.vehicle_model.astype(str).str.strip()
clean = xref[(vm.ne("") & vm.ne("nan") & vm.ne("-"))]
already = set(clean._pn) | set(xref.bvp_pn.map(norm).dropna())
book["known_vehicle"] = book._pn.isin(already)

print("=" * 100)
print("JOB SIZE — the book, and how much of it needs an EPC lookup")
print("=" * 100)
print(f"  distinct part numbers billed      : {len(book):,}")
print(f"  with any vehicle evidence already : {book.known_vehicle.sum():,} "
      f"(EUR {book[book.known_vehicle].eur_all.sum():,.0f})")
need = book[~book.known_vehicle]
print(f"  needing an EPC lookup             : {len(need):,} "
      f"(EUR {need.eur_all.sum():,.0f}, {100*need.eur_all.sum()/tot:.1f}% of the book)")
print()
print("  at the scraper's 12 s per part number:")
for n in (100, 250, 500, 1000, len(need)):
    mins = n * 12 / 60
    print(f"    {n:6,} PNs  ->  {mins:8,.0f} min  ({mins/60:5.1f} h)")
print()

print("=" * 100)
print("PAYOFF BY SERVICE CATEGORY — where a lookup buys the most euro")
print("=" * 100)
bycat = (need.groupby(need.pms_category.fillna("(not a PMS part)"), dropna=False)
         .agg(pns=("_pn", "count"), eur=("eur_all", "sum"), units=("units_all", "sum"))
         .sort_values("eur", ascending=False))
bycat["pct_of_book"] = (100 * bycat.eur / tot).round(2)
bycat["hours_at_12s"] = (bycat.pns * 12 / 3600).round(1)
print(bycat.round(0).to_string())
print()

print("=" * 100)
print("BATCH 1 — the 250 part numbers worth decoding first")
print("=" * 100)
top = need.sort_values("eur_all", ascending=False).head(250).copy()
print(f"  these 250 cover EUR {top.eur_all.sum():,.0f} "
      f"({100*top.eur_all.sum()/tot:.1f}% of the book) "
      f"and take about {len(top)*12/3600:.1f} h of EPC time")
print()
print("  by category:")
print(top.groupby(top.pms_category.fillna("(not a PMS part)"))
      .agg(pns=("_pn", "count"), eur=("eur_all", "sum")).round(0).to_string())
print()
print("  top 25 as an example:")
show = top.head(25)[["pn", "aim_l1", "aim_l2", "pms_category",
                     "eur_all", "units_all", "markets"]]
print(show.to_string(index=False))

# The deliverable: the batch the scraper consumes. Placeholder non-part lines (REBATE,
# TRANSPORT, and similar) are not real part numbers, so the EPC cannot resolve them.
placeholder = sf.part_number.astype(str).str.strip()
is_placeholder = placeholder.str.match(r"^[A-Z][A-Z0-9\- ]{2,}$", na=False)
bad_pns = set(sf.loc[is_placeholder, "_pn"])
out = need[~need._pn.isin(bad_pns)].sort_values("eur_all", ascending=False).copy()
out["epc_rank"] = range(1, len(out) + 1)
out["batch_250"] = out.epc_rank <= 250
cols = ["epc_rank", "pn", "pms_category", "aim_l1", "aim_l2", "eur_all", "units_all",
        "markets", "batch_250"]
out[cols].to_csv(DER + r"\epc_decode_worklist.csv", index=False)
print()
print(f"  written -> {DER}\\epc_decode_worklist.csv  ({len(out):,} real part numbers)")
print(f"  excluded {len(need) - len(out):,} placeholder non-part lines "
      f"(REBATE, TRANSPORT and similar — not part numbers)")
print(f"  batch 1 (250 PNs) covers EUR {out[out.batch_250].eur_all.sum():,.0f}")

# A plain PN list for the scraper call.
out[out.batch_250][["pn"]].to_csv(DER + r"\epc_decode_batch_250.txt", index=False, header=False)
print(f"  plain list for the scraper -> {DER}\\epc_decode_batch_250.txt")
