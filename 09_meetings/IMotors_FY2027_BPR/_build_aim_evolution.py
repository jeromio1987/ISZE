# -*- coding: utf-8 -*-
"""I-Motors AIM evolution: ISZE billing (519) vs sales to dealer, same list €, all levels.

Overlap window forced by sellout MONTH rows: 2025-01 .. 2026-08.
Billing parquet for 519 currently ends 2026-08-31 (Sep not in sales_fact yet).
Sep 2026 KPI euros exist but have no PN grain → excluded from AIM cuts.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT = ROOT / "09_meetings" / "IMotors_FY2027_BPR" / "_aim_evolution_20261006"
OUT.mkdir(parents=True, exist_ok=True)

AIM = DER / "_releases" / "aim_pn_classification_release_2026-10-04.csv"
OVERLAP_START = "2025-01-01"
OVERLAP_END = "2026-08-31"


def norm(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.lstrip("0")
        .replace("", "0")
        .replace("nan", "")
        .replace("None", "")
    )


def load_aim() -> pd.DataFrame:
    a = pd.read_csv(
        AIM,
        dtype=str,
        usecols=[
            "part_number",
            "catalog_l1",
            "catalog_l2",
            "catalog_l3",
            "aim_l1_fixed",
            "aim_l2_fixed",
            "aim_l3_fixed",
            "line_kind",
            "fig_key",
        ],
    )
    a["pn"] = norm(a.part_number)
    a["aim_l1"] = a["aim_l1_fixed"].fillna(a["catalog_l1"]).fillna("(unclassified)")
    a["aim_l2"] = a["aim_l2_fixed"].fillna(a["catalog_l2"]).fillna("(unclassified)")
    a["aim_l3"] = a["aim_l3_fixed"].fillna(a["catalog_l3"]).fillna("(unclassified)")
    a["line_kind"] = a["line_kind"].fillna("part")
    a = a.drop_duplicates("pn")
    return a[["pn", "aim_l1", "aim_l2", "aim_l3", "line_kind", "fig_key"]]


def load_bvp() -> pd.Series:
    p = DER / "bvp_pn_dimension.parquet"
    d = pd.read_parquet(p) if p.exists() else pd.read_csv(DER / "bvp_pn_dimension.csv")
    cols = {c.lower(): c for c in d.columns}
    pn_c = cols.get("part_number") or cols.get("pn")
    lt_c = cols.get("line_type") or cols.get("genuine_bvp") or cols.get("type")
    d = d[[pn_c, lt_c]].copy()
    d.columns = ["pn", "line_type"]
    d["pn"] = norm(d.pn)
    d["line_type"] = d.line_type.astype(str).str.lower().str.strip()
    return d.drop_duplicates("pn").set_index("pn")["line_type"]


def load_price() -> pd.Series:
    p = pd.read_parquet(DER / "pricing_pr00_ie40.parquet", columns=["part_number", "newest_pn", "sp_eur"])
    p["pn"] = norm(p.part_number)
    p["new"] = norm(p.newest_pn)
    p = p[p.sp_eur > 0]
    own = p.drop_duplicates("pn").set_index("pn").sp_eur
    newest = p.set_index("pn").sp_eur.reindex(p.new.values)
    newest.index = p.pn.values
    newest = newest[~newest.index.duplicated()].dropna()
    return own.combine_first(newest)


def load_pms() -> pd.DataFrame:
    cat = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str, usecols=["part_number", "pms_category"])
    cat["pn"] = norm(cat.part_number)
    return cat.drop_duplicates("pn")[["pn", "pms_category"]]


def billing() -> pd.DataFrame:
    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value", "saty"],
    )
    b = sf[(sf.sold_to_sap == 519) & ~sf.saty.isin(["CR", "RE"])].copy()
    b["pn"] = norm(b.part_number)
    b["date"] = pd.to_datetime(b.billing_date)
    b["ym"] = b.date.dt.to_period("M").astype(str)
    b["qty"] = pd.to_numeric(b.billed_qty, errors="coerce").fillna(0)
    b["net_eur"] = pd.to_numeric(b.net_sales_value, errors="coerce").fillna(0)
    return b[["date", "ym", "pn", "qty", "net_eur"]]


def sellout() -> pd.DataFrame:
    so = pd.concat(
        [
            pd.read_csv(DER / f"dealer_sellout_long_PORTUGAL_{p}.csv", dtype={"part_number": str, "period": str})
            for p in ("CY2025", "CY2026YTD")
        ]
    )
    so = so[so.period_grain == "month"].copy()
    so["ym"] = so.period
    so["date"] = pd.to_datetime(so.period + "-01")
    so["pn"] = norm(so.part_number)
    so["qty"] = pd.to_numeric(so.qty, errors="coerce").fillna(0)
    return so[["date", "ym", "pn", "qty"]]


def enrich(df, aim, price, bvp, pms):
    d = df.merge(aim, on="pn", how="left")
    d["aim_l1"] = d["aim_l1"].fillna("(unclassified)")
    d["aim_l2"] = d["aim_l2"].fillna("(unclassified)")
    d["aim_l3"] = d["aim_l3"].fillna("(unclassified)")
    d["line_kind"] = d["line_kind"].fillna("unknown")
    d["list_eur_unit"] = d["pn"].map(price)
    d["list_eur"] = d["qty"] * d["list_eur_unit"].fillna(0)
    d["priced"] = d["list_eur_unit"].notna() & (d["list_eur_unit"] > 0)
    d["line_type"] = d["pn"].map(bvp).fillna("unknown")
    d = d.merge(pms, on="pn", how="left")
    d["pms_category"] = d["pms_category"].fillna("(no PMS)")
    return d


def period_tag(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    return f"FY{y+1}" if m >= 4 else f"FY{y}"


def main():
    aim = load_aim()
    price = load_price()
    bvp = load_bvp()
    pms = load_pms()
    bill = enrich(billing(), aim, price, bvp, pms)
    so = enrich(sellout(), aim, price, bvp, pms)

    b_ov = bill[(bill.date >= OVERLAP_START) & (bill.date <= OVERLAP_END)].copy()
    s_ov = so[(so.date >= OVERLAP_START) & (so.date <= OVERLAP_END)].copy()
    s_ov["net_eur"] = np.nan

    meta = {
        "sold_to": 519,
        "accessory_92_excluded": True,
        "overlap": f"{OVERLAP_START} .. {OVERLAP_END}",
        "aim_release": AIM.name,
        "price_basis": "PR00 IE40 list 2026-08-10",
        "billing_rows_overlap": int(len(b_ov)),
        "sellout_rows_overlap": int(len(s_ov)),
        "billing_net_eur_overlap": round(float(b_ov.net_eur.sum()), 2),
        "billing_list_eur_overlap": round(float(b_ov.list_eur.sum()), 2),
        "sellout_list_eur_overlap": round(float(s_ov.list_eur.sum()), 2),
        "billing_qty_overlap": round(float(b_ov.qty.sum()), 2),
        "sellout_qty_overlap": round(float(s_ov.qty.sum()), 2),
        "billing_aim_match_list_eur_pct": round(
            float(b_ov.loc[b_ov.aim_l1 != "(unclassified)", "list_eur"].sum() / max(b_ov.list_eur.sum(), 1) * 100), 2
        ),
        "sellout_aim_match_list_eur_pct": round(
            float(s_ov.loc[s_ov.aim_l1 != "(unclassified)", "list_eur"].sum() / max(s_ov.list_eur.sum(), 1) * 100), 2
        ),
        "billing_priced_qty_pct": round(float(b_ov.loc[b_ov.priced, "qty"].sum() / max(b_ov.qty.sum(), 1) * 100), 2),
        "sellout_priced_qty_pct": round(float(s_ov.loc[s_ov.priced, "qty"].sum() / max(s_ov.qty.sum(), 1) * 100), 2),
        "gaps": [
            "sales_fact sold-to 519 ends 2026-08-31 — no Sep PN billing in parquet",
            "dealer_sellout_long PORTUGAL month rows end 2026-08 — no Sep PN StD",
            "Sep 2026 KPI StD €416.8k has no part numbers → out of AIM cuts",
            "sold-to 92 accessory excluded",
            "list € is ISZE list, not I-Motors net or dealer price",
            "no dealer grain on sales to dealer",
        ],
    }

    m_b = b_ov.groupby("ym", as_index=False).agg(bill_qty=("qty", "sum"), bill_list_eur=("list_eur", "sum"), bill_net_eur=("net_eur", "sum"))
    m_s = s_ov.groupby("ym", as_index=False).agg(std_qty=("qty", "sum"), std_list_eur=("list_eur", "sum"))
    wide = m_b.merge(m_s, on="ym", how="outer").sort_values("ym")
    wide["list_gap_bill_minus_std"] = wide["bill_list_eur"] - wide["std_list_eur"]
    wide["qty_gap_bill_minus_std"] = wide["bill_qty"] - wide["std_qty"]
    wide["fy"] = wide.ym.map(period_tag)
    wide["destock_month"] = wide["std_list_eur"] > wide["bill_list_eur"]
    wide.to_csv(OUT / "monthly_billing_vs_std_list.csv", index=False)

    l1_b = b_ov.groupby(["ym", "aim_l1"], as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum"), net_eur=("net_eur", "sum")).assign(stage="billing_isze_db")
    l1_s = s_ov.groupby(["ym", "aim_l1"], as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum")).assign(stage="sales_to_dealer", net_eur=np.nan)
    pd.concat([l1_b, l1_s], ignore_index=True).to_csv(OUT / "monthly_aim_l1.csv", index=False)

    def stage_l1(df):
        g = df.groupby("aim_l1", as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum"))
        if "net_eur" in df.columns and df["net_eur"].notna().any():
            g["net_eur"] = df.groupby("aim_l1")["net_eur"].sum().reindex(g.aim_l1).values
        tot = g.list_eur.sum()
        g["list_share"] = g.list_eur / tot if tot else 0
        return g.sort_values("list_eur", ascending=False)

    l1_tot_b = stage_l1(b_ov).assign(stage="billing_isze_db")
    l1_tot_s = stage_l1(s_ov).assign(stage="sales_to_dealer")
    pd.concat([l1_tot_b, l1_tot_s]).to_csv(OUT / "overlap_aim_l1_totals.csv", index=False)

    cmp_l1 = l1_tot_b[["aim_l1", "list_eur", "list_share", "qty"]].rename(
        columns={"list_eur": "bill_list_eur", "list_share": "bill_share", "qty": "bill_qty"}
    ).merge(
        l1_tot_s[["aim_l1", "list_eur", "list_share", "qty"]].rename(
            columns={"list_eur": "std_list_eur", "list_share": "std_share", "qty": "std_qty"}
        ),
        on="aim_l1",
        how="outer",
    ).fillna(0)
    cmp_l1["share_gap_pp"] = (cmp_l1.bill_share - cmp_l1.std_share) * 100
    cmp_l1["list_gap"] = cmp_l1.bill_list_eur - cmp_l1.std_list_eur
    cmp_l1 = cmp_l1.sort_values("std_list_eur", ascending=False)
    cmp_l1.to_csv(OUT / "overlap_aim_l1_billing_vs_std.csv", index=False)

    l2_b = b_ov.groupby(["aim_l1", "aim_l2"], as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum")).assign(stage="billing_isze_db")
    l2_s = s_ov.groupby(["aim_l1", "aim_l2"], as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum")).assign(stage="sales_to_dealer")
    pd.concat([l2_b, l2_s]).to_csv(OUT / "overlap_aim_l1_l2_totals.csv", index=False)
    cmp_l2 = l2_b.rename(columns={"list_eur": "bill_list_eur", "qty": "bill_qty"}).merge(
        l2_s.rename(columns={"list_eur": "std_list_eur", "qty": "std_qty"}),
        on=["aim_l1", "aim_l2"],
        how="outer",
    ).fillna(0)
    cmp_l2["list_gap"] = cmp_l2.bill_list_eur - cmp_l2.std_list_eur
    cmp_l2.sort_values("std_list_eur", ascending=False).head(100).to_csv(OUT / "overlap_aim_l2_top_billing_vs_std.csv", index=False)

    def mix(df, stage):
        g = df.groupby("line_type", as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum"))
        tot = g.list_eur.sum()
        g["list_share"] = g.list_eur / tot if tot else 0
        g["stage"] = stage
        return g

    mix_all = pd.concat([mix(b_ov, "billing_isze_db"), mix(s_ov, "sales_to_dealer")])
    mix_all.to_csv(OUT / "overlap_genuine_bvp_mix.csv", index=False)
    pd.concat([
        b_ov.groupby(["ym", "line_type"], as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum")).assign(stage="billing_isze_db"),
        s_ov.groupby(["ym", "line_type"], as_index=False).agg(qty=("qty", "sum"), list_eur=("list_eur", "sum")).assign(stage="sales_to_dealer"),
    ]).to_csv(OUT / "monthly_genuine_bvp.csv", index=False)

    pms_cmp = b_ov.groupby("pms_category", as_index=False).agg(bill_qty=("qty", "sum"), bill_list_eur=("list_eur", "sum")).merge(
        s_ov.groupby("pms_category", as_index=False).agg(std_qty=("qty", "sum"), std_list_eur=("list_eur", "sum")),
        on="pms_category",
        how="outer",
    ).fillna(0)
    pms_cmp["list_gap"] = pms_cmp.bill_list_eur - pms_cmp.std_list_eur
    pms_cmp.sort_values("std_list_eur", ascending=False).to_csv(OUT / "overlap_pms_category_billing_vs_std.csv", index=False)

    blocks = {
        "CY2025": [f"2025-{m:02d}" for m in range(1, 13)],
        "2026_JanAug": [f"2026-{m:02d}" for m in range(1, 9)],
        "FY27_AprAug": [f"2026-{m:02d}" for m in range(4, 9)],
        "FY26_AprAug": [f"2025-{m:02d}" for m in range(4, 9)],
        "FY26_Apr_to_Mar26": [f"2025-{m:02d}" for m in range(4, 13)] + [f"2026-{m:02d}" for m in range(1, 4)],
    }

    def slice_ym(df, yms):
        return df[df.ym.isin(yms)]

    block_rows = []
    for name, yms in blocks.items():
        bb, ss = slice_ym(b_ov, yms), slice_ym(s_ov, yms)
        block_rows.append({
            "block": name,
            "months": len(yms),
            "bill_net_eur": round(float(bb.net_eur.sum()), 2),
            "bill_list_eur": round(float(bb.list_eur.sum()), 2),
            "std_list_eur": round(float(ss.list_eur.sum()), 2),
            "bill_qty": round(float(bb.qty.sum()), 2),
            "std_qty": round(float(ss.qty.sum()), 2),
            "list_gap": round(float(bb.list_eur.sum() - ss.list_eur.sum()), 2),
        })
    pd.DataFrame(block_rows).to_csv(OUT / "block_totals.csv", index=False)

    fy27, fy26aa = blocks["FY27_AprAug"], blocks["FY26_AprAug"]
    evol = []
    for stage, df in [("billing_isze_db", b_ov), ("sales_to_dealer", s_ov)]:
        a = slice_ym(df, fy26aa).groupby("aim_l1", as_index=False).agg(list_eur_fy26_apr_aug=("list_eur", "sum"), qty_fy26_apr_aug=("qty", "sum"))
        b = slice_ym(df, fy27).groupby("aim_l1", as_index=False).agg(list_eur_fy27_apr_aug=("list_eur", "sum"), qty_fy27_apr_aug=("qty", "sum"))
        m = a.merge(b, on="aim_l1", how="outer").fillna(0)
        m["stage"] = stage
        m["list_delta"] = m.list_eur_fy27_apr_aug - m.list_eur_fy26_apr_aug
        m["list_delta_pct"] = np.where(m.list_eur_fy26_apr_aug > 0, m.list_delta / m.list_eur_fy26_apr_aug, np.nan)
        evol.append(m)
    evol_df = pd.concat(evol, ignore_index=True)
    evol_df.to_csv(OUT / "aim_l1_fy26_apr_aug_vs_fy27_apr_aug.csv", index=False)

    def l2_block(df, yms):
        return slice_ym(df, yms).groupby(["aim_l1", "aim_l2"], as_index=False).agg(list_eur=("list_eur", "sum"), qty=("qty", "sum"))

    movers = (
        l2_block(s_ov, fy26aa).rename(columns={"list_eur": "std_fy26", "qty": "qty_fy26"})
        .merge(l2_block(s_ov, fy27).rename(columns={"list_eur": "std_fy27", "qty": "qty_fy27"}), on=["aim_l1", "aim_l2"], how="outer")
        .merge(l2_block(b_ov, fy26aa).rename(columns={"list_eur": "bill_fy26", "qty": "bq_fy26"}), on=["aim_l1", "aim_l2"], how="outer")
        .merge(l2_block(b_ov, fy27).rename(columns={"list_eur": "bill_fy27", "qty": "bq_fy27"}), on=["aim_l1", "aim_l2"], how="outer")
        .fillna(0)
    )
    movers["std_delta"] = movers.std_fy27 - movers.std_fy26
    movers["bill_delta"] = movers.bill_fy27 - movers.bill_fy26
    movers["gap_fy27"] = movers.bill_fy27 - movers.std_fy27
    movers["gap_fy26"] = movers.bill_fy26 - movers.std_fy26
    movers.sort_values("std_delta", ascending=False).head(40).to_csv(OUT / "top_std_l2_growth_fy27_vs_fy26.csv", index=False)
    movers.sort_values("gap_fy27").head(40).to_csv(OUT / "top_destock_l2_fy27_apr_aug.csv", index=False)
    movers.sort_values("bill_delta").head(40).to_csv(OUT / "top_billing_drop_l2_fy27_vs_fy26.csv", index=False)

    b_long = bill[(bill.date >= "2023-01-01") & (bill.date <= OVERLAP_END)].copy()
    (
        b_long.assign(year=b_long.date.dt.year)
        .groupby(["year", "aim_l1"], as_index=False)
        .agg(net_eur=("net_eur", "sum"), list_eur=("list_eur", "sum"), qty=("qty", "sum"))
        .to_csv(OUT / "billing_only_aim_l1_by_year_2023_2026.csv", index=False)
    )

    findings = {
        **meta,
        "destock_months_of_20": int(wide.destock_month.sum()),
        "destock_months": wide.loc[wide.destock_month, "ym"].tolist(),
        "top_std_aim_l1": cmp_l1.head(10)[["aim_l1", "std_list_eur", "bill_list_eur", "share_gap_pp"]].round(2).to_dict("records"),
        "blocks": block_rows,
    }
    (OUT / "summary.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")

    print("=== META ===")
    print(json.dumps(meta, indent=2))
    print("\n=== BLOCKS ===")
    print(pd.DataFrame(block_rows).to_string(index=False))
    print("\n=== AIM L1 billing vs StD (list €) ===")
    print(cmp_l1.head(15).to_string(index=False))
    print("\n=== Genuine/BVP ===")
    print(mix_all.to_string(index=False))
    print("\n=== Destock months ===")
    print(wide.loc[wide.destock_month, ["ym", "bill_list_eur", "std_list_eur", "list_gap_bill_minus_std"]].to_string(index=False))
    print("\n=== StD AIM L1 growth FY27 Apr-Aug vs FY26 Apr-Aug ===")
    print(evol_df[evol_df.stage == "sales_to_dealer"].sort_values("list_delta", ascending=False).head(12).to_string(index=False))
    print("\n=== Billing AIM L1 drop FY27 Apr-Aug vs FY26 Apr-Aug ===")
    print(evol_df[evol_df.stage == "billing_isze_db"].sort_values("list_delta").head(12).to_string(index=False))
    print("\n=== Top destock L2 FY27 Apr-Aug (bill - std most negative) ===")
    print(movers.sort_values("gap_fy27").head(15)[["aim_l1", "aim_l2", "bill_fy27", "std_fy27", "gap_fy27", "std_delta", "bill_delta"]].to_string(index=False))
    print("\nOUT", OUT)


if __name__ == "__main__":
    main()
