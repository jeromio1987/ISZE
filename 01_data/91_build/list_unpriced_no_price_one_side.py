"""Extract the 'Parts with no matching price on one side' bucket as a readable list.

Read-only. Writes CSV + XLSX under 01_data/00_derived/ and a sibling launcher.
No rebuild of any shipped pack.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
REVIEW = ISZE / "01_data" / "01_Pricing"
OUT_CSV = DERIVED / "unpriced_no_price_one_side_list.csv"
OUT_XLSX = REVIEW / "Unpriced_lines_no_matching_price.xlsx"
OUT_META = DERIVED / "unpriced_no_price_one_side_list.meta.json"
OUT_CMD = REVIEW / "OPEN_Unpriced_lines_no_matching_price.cmd"

pn = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
pn["part_number"] = pn["part_number"].str.zfill(10)

# The shipped pack reports this bucket on in-scope rows only, so the list must
# use the same scope or it will not tie to the published figure.
pn = pn[pn["in_scope"] == True]  # noqa: E712

b = pn[pn["unpriced_reason"] == "no_price_on_one_side"].copy()

# Which side is missing - the only thing a reader needs to act on it.
def side(r):
    n_missing = pd.isna(r["bp_new_jpy"])
    p_missing = pd.isna(r["bp_prior_revised"])
    if n_missing and p_missing:
        return "Neither list has it"
    if n_missing:
        return "New price file has no entry"
    return "Prior price file has no entry"

b["missing_side"] = b.apply(side, axis=1)

# Description from the billing text - the fullest source (present on every PN).
sf = pd.read_parquet(
    DERIVED / "sales_fact.parquet",
    columns=["part_number", "description"],
)
sf["part_number"] = sf["part_number"].astype(str).str.zfill(10)
desc = sf.drop_duplicates("part_number").set_index("part_number")["description"]
b["description"] = b["part_number"].map(desc).fillna("")

# Tidy labels
b["customer"] = (
    b["distributor_code"].fillna("").astype(str).str.strip()
    + " ("
    + b["customer_code"].astype(str).str.split(".").str[0]
    + ")"
)

detail = b[
    [
        "part_number",
        "description",
        "missing_side",
        "customer",
        "customer_code",
        "distributor_code",
        "country",
        "billed_qty",
        "net_sales_value",
        "bp_prior_revised",
        "bp_new_jpy",
    ]
].copy()
detail = detail.rename(
    columns={
        "part_number": "Part number",
        "description": "Description",
        "missing_side": "What is missing",
        "customer": "Customer",
        "customer_code": "Sold-to code",
        "distributor_code": "Distributor",
        "country": "Country",
        "billed_qty": "L12M qty",
        "net_sales_value": "L12M billed (EUR)",
        "bp_prior_revised": "Prior base price (JPY)",
        "bp_new_jpy": "New base price (JPY)",
    }
)
detail = detail.sort_values("L12M billed (EUR)", ascending=False)

# Grouped by part number - the actionable view
grp = (
    b.groupby(["part_number", "missing_side"], as_index=False)
    .agg(
        **{
            "Description": ("description", "first"),
            "L12M qty": ("billed_qty", "sum"),
            "L12M billed (EUR)": ("net_sales_value", "sum"),
            "Customers billing it": ("customer_code", "nunique"),
            "Distributors billing it": ("distributor_code", "nunique"),
        }
    )
    .sort_values("L12M billed (EUR)", ascending=False)
)

# By customer
bycust = (
    b.groupby(["distributor_code", "customer_code"], as_index=False)
    .agg(
        **{
            "Part numbers": ("part_number", "nunique"),
            "Lines": ("part_number", "size"),
            "L12M qty": ("billed_qty", "sum"),
            "L12M billed (EUR)": ("net_sales_value", "sum"),
        }
    )
    .sort_values("L12M billed (EUR)", ascending=False)
)

# By which side is missing
byside = (
    b.groupby("missing_side", as_index=False)
    .agg(
        **{
            "Lines": ("part_number", "size"),
            "Part numbers": ("part_number", "nunique"),
            "L12M qty": ("billed_qty", "sum"),
            "L12M billed (EUR)": ("net_sales_value", "sum"),
        }
    )
    .sort_values("L12M billed (EUR)", ascending=False)
)

total_eur = b["net_sales_value"].sum()
for f in (byside, bycust, grp):
    f["Share of this bucket"] = (100 * f["L12M billed (EUR)"] / total_eur).round(1)

detail.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
    intro = pd.DataFrame(
        {
            "Item": [
                "What this is",
                "Window",
                "Lines",
                "Part numbers",
                "L12M quantity",
                "L12M billed",
                "Share of everything excluded",
                "Why it is excluded",
                "Missing on the prior list only",
                "Missing on the new list only",
                "Missing on both lists",
            ],
            "Value": [
                "Parts with no matching price on one side",
                "1 Jul 2025 to 30 Jun 2026",
                len(b),
                b["part_number"].nunique(),
                int(b["billed_qty"].sum()),
                round(total_eur, 2),
                "46.3%",
                "Genuine parts, but the two price lists do not both cover the number, so there is no pair to compare.",
                *[
                    f"{int(byside.loc[byside['missing_side'] == s, 'Lines'].iloc[0])} lines, "
                    f"EUR {byside.loc[byside['missing_side'] == s, 'L12M billed (EUR)'].iloc[0]:,.0f}"
                    if (byside["missing_side"] == s).any()
                    else "none"
                    for s in [
                        "Prior price file has no entry",
                        "New price file has no entry",
                        "Neither list has it",
                    ]
                ],
            ],
        }
    )
    intro.to_excel(xl, sheet_name="What this is", index=False)
    byside.to_excel(xl, sheet_name="By what is missing", index=False)
    bycust.to_excel(xl, sheet_name="By customer", index=False)
    grp.to_excel(xl, sheet_name="By part number", index=False)
    detail.to_excel(xl, sheet_name="Line detail", index=False)

meta = {
    "source": str(DERIVED / "price_bp_weighted_compare_pn.csv"),
    "bucket": "no_price_on_one_side",
    "scope": "in_scope rows only, to tie to the shipped pack",
    "lines": int(len(b)),
    "part_numbers": int(b["part_number"].nunique()),
    "qty": float(b["billed_qty"].sum()),
    "eur": round(float(total_eur), 2),
    "customers": int(b["customer_code"].nunique()),
    "by_side": {
        str(r["missing_side"]): {
            "lines": int(r["Lines"]),
            "part_numbers": int(r["Part numbers"]),
            "eur": round(float(r["L12M billed (EUR)"]), 2),
        }
        for _, r in byside.iterrows()
    },
    "outputs": [str(OUT_CSV), str(OUT_XLSX)],
}
OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

# Launcher beside the workbook, CRLF, so it opens from Explorer.
OUT_CMD.write_bytes(
    (
        "@echo off\r\n"
        'start "" "%~dp0Unpriced_lines_no_matching_price.xlsx"\r\n'
    ).encode("ascii")
)

print(f"lines            : {len(b)}")
print(f"part numbers     : {b['part_number'].nunique()}")
print(f"L12M qty         : {int(b['billed_qty'].sum()):,}")
print(f"L12M billed EUR  : {total_eur:,.2f}")
print(f"customers        : {b['customer_code'].nunique()}")
print()
print("--- by what is missing ---")
print(byside.to_string(index=False))
print()
print("--- top 20 part numbers ---")
print(grp.head(20).to_string(index=False))
print()
print("--- top 12 customers ---")
print(bycust.head(12).to_string(index=False))
print()
print("wrote:", OUT_CSV.name, "|", OUT_XLSX.name)
