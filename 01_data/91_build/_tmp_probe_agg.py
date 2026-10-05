"""Probe 4: network and customer level tie-out of the recomputed aggregation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
FX = 163.7
UNCLASSIFIED = "UNCLASSIFIED"

pn = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
aim = pd.read_csv(D / "aim_pn_classification.csv", dtype={"part_number": str})
aim["part_number"] = aim["part_number"].astype(str).str.strip()
ins = pn[pn["in_scope"] == True].copy()  # noqa: E712
m = ins.merge(aim[["part_number", "catalog_l1", "catalog_l2"]], on="part_number", how="left")
for c in ("catalog_l1", "catalog_l2"):
    m[c] = m[c].where(m[c].notna(), UNCLASSIFIED)
m["paired"] = m.bp_new_jpy.notna() & m.bp_prior_revised.notna() & m.billed_qty.notna()
m["paired_basket_eur"] = ((m.billed_qty * m.bp_prior_revised) / FX).where(m.paired, 0.0)
m["step"] = m.value_eur_step.fillna(0.0)
m["q_term"] = m.billed_qty.where(m.paired, 0.0)
m["eur_term"] = m.net_sales_value.where(m.paired, 0.0)
m["prows"] = m.paired.astype(int)


def agg(keys):
    g = m.groupby(keys, dropna=False)
    out = g.agg(n_pn=("part_number", "nunique"), qty=("billed_qty", "sum"),
                billed=("net_sales_value", "sum"), step=("step", "sum"),
                paired_basket=("paired_basket_eur", "sum"),
                priced_qty=("q_term", "sum"), priced_eur=("eur_term", "sum"),
                priced_rows=("prows", "sum")).reset_index()
    out["rate"] = out.step / out.paired_basket * 100
    out["qty_cov"] = out.priced_qty / out.qty * 100
    return out


mx = pd.read_csv(D / "aim_catalog_db_matrix.csv")
mx = mx[(mx.level_id == "L2") & (mx.scheme_basis == "catalog_full")]

net = agg(["catalog_l1", "catalog_l2"])
jn = mx[mx.distributor_code == "__NETWORK__"].merge(
    net, on=["catalog_l1", "catalog_l2"], how="outer", indicator=True)
print("network merge:", jn._merge.value_counts().to_dict())
for a, b in [("step_eur", "step"), ("l12m_billed_eur", "billed"),
             ("weighted_increase_pct", "rate"), ("n_pn_x", "n_pn_y"),
             ("l12m_qty", "qty"), ("qty_coverage_pct", "qty_cov"),
             ("priced_qty_both_sides", "priced_qty"),
             ("priced_rows_both_sides", "priced_rows")]:
    print(f"  max |{a} - {b}| = {(jn[a] - jn[b]).abs().max()}")

cust = agg(["distributor_code", "catalog_l1", "catalog_l2"])
jc = mx[mx.distributor_code != "__NETWORK__"].merge(
    cust, on=["distributor_code", "catalog_l1", "catalog_l2"], how="outer", indicator=True)
print("customer merge:", jc._merge.value_counts().to_dict())
for a, b in [("step_eur", "step"), ("l12m_billed_eur", "billed"),
             ("weighted_increase_pct", "rate"), ("n_pn_x", "n_pn_y"),
             ("l12m_qty", "qty"), ("qty_coverage_pct", "qty_cov")]:
    print(f"  max |{a} - {b}| = {(jc[a] - jc[b]).abs().max()}")

print()
print("NaN rate rows (no price pair either side):")
nan = cust[cust.paired_basket == 0]
print(len(nan), "rows")
print(nan[["distributor_code", "catalog_l1", "catalog_l2", "billed", "step", "n_pn"]].to_string(index=False))
print()
print("cust step sum", round(cust.step.sum(), 2), "| net step", round(net.step.sum(), 2))
print("cust billed sum", round(cust.billed.sum(), 2), "| net billed", round(net.billed.sum(), 2))
print()
print("labels per distributor (from the pn base):")
lab = m.groupby("distributor_code")["gps_db_label"].agg(lambda s: sorted(set(s.dropna())))
print(lab.to_string())
