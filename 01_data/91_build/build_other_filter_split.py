"""
Decompose the catalogue node `Competitive parts > Filters > Other filter` into real
product groups, so the filter portfolio can be presented as oil / fuel / air plus a
separately-labelled non-clean-filter block instead of a fourth filter type.

Inputs (derived tables only - no raw billing is opened):
  01_data/00_derived/price_bp_weighted_compare_pn.csv   in-scope billed parts, L12M to 2026-06-30
  01_data/00_derived/aim_pn_classification.csv          catalogue + workbook classification
  01_data/00_derived/parts_catalog_dimension.csv        fig_key label / pms_category
  01_data/00_derived/aim_catalog_focus_filters.csv      the existing Focus cut, for reconciliation
  01_data/00_derived/gps_spu_by_distributor.csv         2025 trucks-in-service denominators

Basis: `catalog_full` - the catalogue columns (catalog_l1/l2/l3) across ALL rows, not
restricted to aim_source == 'pr00_catalog'. See aim_catalog_breakdown_NOTES.md section 4.

Outputs:
  01_data/00_derived/aim_catalog_other_filter_split.csv
  01_data/00_derived/aim_catalog_other_filter_notable_pns.csv
  01_data/00_derived/aim_catalog_other_filter_meta.json

Nothing here changes the source taxonomy. Reported, not fixed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "01_data" / "00_derived"

PN = DER / "price_bp_weighted_compare_pn.csv"
CLASS = DER / "aim_pn_classification.csv"
DIM = DER / "parts_catalog_dimension.csv"
FOCUS = DER / "aim_catalog_focus_filters.csv"
FLEET = DER / "gps_spu_by_distributor.csv"

OUT_SPLIT = DER / "aim_catalog_other_filter_split.csv"
OUT_PNS = DER / "aim_catalog_other_filter_notable_pns.csv"
OUT_DIST = DER / "aim_catalog_other_filter_by_distributor.csv"
OUT_GRP_DIST = DER / "aim_catalog_other_filter_group_by_distributor.csv"
OUT_META = DER / "aim_catalog_other_filter_meta.json"

NODE_L2 = "Filters"
NODE_L3 = "Other filter"
FOCUS_LINE_EUR = 668819.46       # network line in aim_catalog_focus_filters.csv (catalog_full)
FOCUS_LINE_QTY = 6655.0

# Four markets with no trucks-in-service count by design. Never divide by fleet for these.
NO_FLEET = ["ARMENIA", "KAZAKHSTAN", "PALESTINE", "UKRAINE"]

AIM_SCOPE = {"pr00_catalog": "catalogue file (PR00)", "aim_workbook": "workbook / PR00-sourced row"}

# Figure keys that the BILLED members of each group actually used. Applied to the unbilled
# taxonomy tail as a projection, because only 14 of the 189 unbilled numbers carry a
# description at all while 182 carry a figure key. The catalogue's own figure grouping is
# therefore the strongest available signal for the tail.
FIGKEY_STRAINER = {
    "244-001", "244-002", "220-592", "220-593", "051-139", "051-140",
    "051-051", "051-042", "051-050", "051-049", "435-005",
}
FIGKEY_AFTERTREATMENT = {"150-558"}
FIGKEY_DEF = {"146-152"}
FIGKEY_VCV = {"057-018"}


# --------------------------------------------------------------------------------------
# group rules
# --------------------------------------------------------------------------------------
def classify(row) -> tuple[str, str]:
    """Return (group, rule_fired). Most specific signal first; every PN gets one group."""
    desc = str(row.get("description_norm") if pd.notna(row.get("description_norm")) else "").upper()
    billed = str(row.get("billed_description") if pd.notna(row.get("billed_description")) else "").upper()
    text = (desc + " " + billed).strip()
    fig = str(row.get("fig_key") or "")
    pms = str(row.get("pms_category") or "")
    l2 = str(row.get("aim_l2") or "")
    aim_l3 = str(row.get("aim_l3") or "")

    # 1. Urea / DEF (AdBlue) filter elements and pump-module filter kits.
    if pms == "urea_filter" or fig == "146-152" or ("FILTER KIT" in text and "DEF" in text):
        return "Urea / DEF (AdBlue) filter elements and kits", "urea_signal"

    # 2. Crankcase ventilation (VCV) filter assemblies.
    if fig == "057-018" or "VCV" in text:
        return "Crankcase ventilation (VCV) filter assemblies", "vcv_signal"

    # 3. Aftertreatment filter assemblies - the PR00 figure for the big exhaust
    #    particulate filter assemblies. All billed members are `FILTER ASM`, class D.
    if fig == "150-558":
        return "Aftertreatment filter assemblies (exhaust particulate)", "fig_150-558"

    # 4. Gaskets and seals billed against a filter or strainer.
    if "GASKET" in text or "O-RING" in text or "SEAL" in text:
        return "Gaskets and seals sold with filters", "gasket_token"

    # 5. Hydraulic / transmission strainers, screens and their covers and pipes.
    if "STRAINER" in text or "SCREEN" in text:
        return "Hydraulic / transmission strainers and screens", "strainer_token"

    # 6. A filter element the other vocabulary files as an oil filter.
    if pms == "oil_filter" or "OIL FILTER" in text or text.startswith("FILTER; OIL"):
        return "Oil-filter elements filed under Other filter", "oil_filter_signal"

    # 7. Filter housing covers, pipes, bolts and insulators sold with a filter.
    if any(t in text for t in ("COVER", "PIPE", "BOLT", "INSULATOR", "HOSE", "CLAMP")):
        return "Filter covers, pipes and fitting hardware", "hardware_token"

    # 8. Parts whose only link to filters is their name - not filtration products.
    if any(t in text for t in ("SILENCER", "WRENCH", "BUSHING", "RESERVOIR", "SPEEDOMETER")):
        return "Non-filter parts (exhaust, tools, other)", "non_filter_token"

    # 9. Genuine filter element, nothing more specific in any vocabulary.
    if "FILTER" in text or "ELEMENT" in text or l2 == "Filters":
        return "Unresolved filter parts (no product evidence)", "filter_residual"

    # 10. Tail-only projection: the unbilled part numbers mostly carry no description, so
    #     fall back to the catalogue's own figure grouping - the strongest signal left.
    if fig in FIGKEY_AFTERTREATMENT:
        return "Aftertreatment filter assemblies (exhaust particulate)", "tail_figkey_150-558"
    if fig in FIGKEY_DEF:
        return "Urea / DEF (AdBlue) filter elements and kits", "tail_figkey_146-152"
    if fig in FIGKEY_VCV:
        return "Crankcase ventilation (VCV) filter assemblies", "tail_figkey_057-018"
    if fig in FIGKEY_STRAINER or aim_l3 == "Strainer":
        return "Hydraulic / transmission strainers and screens", "tail_figkey_strainer"
    if aim_l3 == "Filter Assembly":
        return "Unresolved filter parts (no product evidence)", "tail_aim_l3_filter_assembly"

    return "Unresolved - no description at all", "no_description"


GROUP_ORDER = [
    "Aftertreatment filter assemblies (exhaust particulate)",
    "Urea / DEF (AdBlue) filter elements and kits",
    "Hydraulic / transmission strainers and screens",
    "Crankcase ventilation (VCV) filter assemblies",
    "Gaskets and seals sold with filters",
    "Filter covers, pipes and fitting hardware",
    "Oil-filter elements filed under Other filter",
    "Non-filter parts (exhaust, tools, other)",
    "Unresolved filter parts (no product evidence)",
    "Unresolved - no description at all",
]

# Groups whose euro sits only in one or two hands, so a group rate is not meaningful.
NO_FLEET_SET = set(NO_FLEET)
NETWORK_UIO_18 = 163459.0  # 18 markets with a count; the four above are excluded by design


def weighted_increase(frame: pd.DataFrame) -> tuple[float | None, float, float]:
    """qty-weighted base-price move on rows priced on both sides, plus priced qty and coverage."""
    qty_all = float(frame["billed_qty"].sum())
    ok = frame[
        frame["bp_new_jpy"].notna()
        & frame["bp_prior_revised"].notna()
        & (frame["bp_new_jpy"] > 0)
        & (frame["bp_prior_revised"] > 0)
    ]
    q = float(ok["billed_qty"].sum())
    if q <= 0:
        return None, 0.0, 0.0
    num = float((ok["billed_qty"] * ok["bp_new_jpy"]).sum())
    den = float((ok["billed_qty"] * ok["bp_prior_revised"]).sum())
    if den <= 0:
        return None, q, 0.0
    return (num / den - 1.0) * 100.0, q, (q / qty_all * 100.0 if qty_all else 0.0)


def main() -> None:
    pn = pd.read_csv(PN, dtype={"part_number": str, "customer_code": str})
    cls = pd.read_csv(CLASS, dtype={"part_number": str})
    dim = pd.read_csv(DIM, dtype={"part_number": str})
    focus = pd.read_csv(FOCUS)
    fleet = pd.read_csv(FLEET)

    # ---- merge ---------------------------------------------------------------------
    df = pn.merge(cls, on="part_number", how="left")
    df = df.merge(dim[["part_number", "fig_key_label", "pms_category"]], on="part_number", how="left")

    join_missing = df[df["catalog_l2"].isna()]
    join_note = {
        "rows": int(len(join_missing)),
        "part_numbers": int(join_missing["part_number"].nunique()),
        "l12m_billed_eur": round(float(join_missing["net_sales_value"].sum()), 2),
    }

    # ---- the bucket, three ways, so the reconciliation is visible -------------------
    all_rows = df[(df["catalog_l2"] == NODE_L2) & (df["catalog_l3"] == NODE_L3)]
    # in_scope is the network cut; `as_index` copy so the extra columns below are ours.
    in_scope = all_rows[all_rows["in_scope"] == True].copy()  # noqa: E712
    if "uio_units_2025" in in_scope.columns:
        raise SystemExit("'uio_units_2025' already exists - check the input before descending")

    out_of_scope = all_rows[all_rows["in_scope"] != True]  # noqa: E712
    oos_detail = (
        out_of_scope.groupby(["network_role"])
        .agg(rows=("part_number", "size"), part_numbers=("part_number", "nunique"),
             qty=("billed_qty", "sum"), eur=("net_sales_value", "sum"))
        .reset_index()
        .to_dict("records")
    )

    # ---- fleet denominators --------------------------------------------------------
    fl = fleet[fleet["year"] == 2025][["distributor_code", "country", "region", "uio_units"]].copy()
    fl["uio_units"] = pd.to_numeric(fl["uio_units"], errors="coerce").fillna(0.0)
    fleet_map = dict(zip(fl["distributor_code"], fl["uio_units"]))

    in_scope["uio_units_2025"] = in_scope["distributor_code"].map(fleet_map)
    in_scope["uio_units_2025"] = in_scope["uio_units_2025"].fillna(0.0)
    in_scope["fleet_denominator_available"] = in_scope["uio_units_2025"] > 0

    # ---- group assignment on the unique-PN taxonomy ---------------------------------
    cls_node = cls[(cls["catalog_l2"] == NODE_L2) & (cls["catalog_l3"] == NODE_L3)].copy()
    cls_node = cls_node.merge(dim[["part_number", "pms_category"]], on="part_number", how="left")
    grp = cls_node.apply(lambda r: classify(r), axis=1)
    cls_node["product_group"] = [g for g, _ in grp]
    cls_node["group_rule"] = [x for _, x in grp]

    billed_pns = set(in_scope["part_number"].unique())
    cls_node["billed_l12m"] = cls_node["part_number"].isin(billed_pns)

    in_scope = in_scope.merge(
        cls_node[["part_number", "product_group", "group_rule"]], on="part_number", how="left"
    )
    if in_scope["product_group"].isna().any():
        raise SystemExit("group assignment incomplete - every billed PN must receive a group")

    # ---- group table ----------------------------------------------------------------
    rows = []
    total_qty = float(in_scope["billed_qty"].sum())
    total_eur = float(in_scope["net_sales_value"].sum())

    for g in GROUP_ORDER:
        sub = in_scope[in_scope["product_group"] == g]
        if sub.empty:
            continue
        eur = float(sub["net_sales_value"].sum())
        qty = float(sub["billed_qty"].sum())
        inc, priced_qty, cov = weighted_increase(sub)

        no_fleet = sorted(set(sub["distributor_code"]) & NO_FLEET_SET)
        with_fleet = sub[~sub["distributor_code"].isin(no_fleet)]
        # Denominator must be UNIQUE markets, not the sum of customer rows: a market with
        # several billed customer codes would otherwise be counted several times.
        uio = float(sum(fleet_map.get(d, 0.0) for d in set(with_fleet["distributor_code"])))
        eur_with_fleet = float(with_fleet["net_sales_value"].sum())
        # A group rate is only meaningful when the euro is not sitting in one or two hands.
        euro_per_truck = None
        euro_per_truck_network = None
        if uio > 0 and eur_with_fleet >= 5000 and sub["distributor_code"].nunique() >= 5:
            euro_per_truck = eur_with_fleet / uio
            euro_per_truck_network = None
        elif eur >= 5000:
            euro_per_truck_network = eur / NETWORK_UIO_18

        by_dist = sub.groupby("distributor_code")["net_sales_value"].sum().sort_values(ascending=False)
        top5_share = float(by_dist.head(5).sum() / eur * 100.0) if eur else None

        rows.append(
            {
                "group": g,
                "n_pn_billed": int(sub["part_number"].nunique()),
                "n_pn_in_taxonomy": int((cls_node["product_group"] == g).sum()),
                "l12m_qty": qty,
                "l12m_billed_eur": round(eur, 2),
                "share_of_bucket_pct": round(eur / total_eur * 100.0, 2) if total_eur else None,
                "step_eur": round(float(sub["value_eur_step"].sum()), 2),
                "weighted_increase_pct": round(inc, 4) if inc is not None else None,
                "priced_qty_both_sides": priced_qty,
                "qty_coverage_pct": round(cov, 2),
                "uio_units_2025_unique_markets_in_group": uio,
                "fleet_denominator_available": bool(uio > 0),
                "billed_eur_per_truck": round(euro_per_truck, 2) if euro_per_truck is not None else None,
                "billed_eur_per_truck_network_rate": round(euro_per_truck_network, 4) if euro_per_truck_network is not None else None,
                "markets_excluded_no_fleet": ", ".join(no_fleet) or None,
                "n_distributors": int(sub["distributor_code"].nunique()),
                "top_distributor": by_dist.index[0],
                "top_distributor_share_pct": round(float(by_dist.iloc[0]) / eur * 100.0, 1) if eur else None,
                "top2_distributor_share_pct": round(float(by_dist.head(2).sum()) / eur * 100.0, 1) if eur else None,
                "top5_distributor_share_pct": round(top5_share, 1) if top5_share is not None else None,
                "eur_per_unit": round(eur / qty, 2) if qty else None,
                "group_rule_fired": ", ".join(sorted(set(sub["group_rule"].dropna()))),
                "n_pn_unbilled_in_taxonomy": int(
                    ((cls_node["product_group"] == g) & (~cls_node["billed_l12m"])).sum()
                ),
            }
        )

    out = pd.DataFrame(rows)
    tot_inc, tot_pq, tot_cov = weighted_increase(in_scope)
    tot_with_fleet = in_scope[~in_scope["distributor_code"].isin(NO_FLEET_SET)]
    tot_uio = float(sum(fleet_map.get(d, 0.0) for d in set(tot_with_fleet["distributor_code"])))
    total_row = {
        "group": "TOTAL - Other filter (catalog_full, in-scope L12M)",
        "n_pn_billed": int(in_scope["part_number"].nunique()),
        "n_pn_in_taxonomy": int(len(cls_node)),
        "l12m_qty": total_qty,
        "l12m_billed_eur": round(total_eur, 2),
        "share_of_bucket_pct": 100.00,
        "step_eur": round(float(in_scope["value_eur_step"].sum()), 2),
        "weighted_increase_pct": round(tot_inc, 4),
        "priced_qty_both_sides": tot_pq,
        "qty_coverage_pct": round(tot_cov, 2),
        "uio_units_2025_unique_markets_in_group": tot_uio,
        "fleet_denominator_available": True,
        "billed_eur_per_truck": round(float(tot_with_fleet["net_sales_value"].sum()) / tot_uio, 2),
        "billed_eur_per_truck_network_rate": round(total_eur / NETWORK_UIO_18, 4),
        "markets_excluded_no_fleet": ", ".join(NO_FLEET),
        "n_distributors": int(in_scope["distributor_code"].nunique()),
        "top_distributor": in_scope.groupby("distributor_code")["net_sales_value"].sum().idxmax(),
        "top_distributor_share_pct": round(
            in_scope.groupby("distributor_code")["net_sales_value"].sum().max() / total_eur * 100.0, 1
        ),
        "top2_distributor_share_pct": round(
            in_scope.groupby("distributor_code")["net_sales_value"].sum().nlargest(2).sum() / total_eur * 100.0, 1
        ),
        "top5_distributor_share_pct": round(
            in_scope.groupby("distributor_code")["net_sales_value"].sum().nlargest(5).sum() / total_eur * 100.0, 1
        ),
        "eur_per_unit": round(total_eur / total_qty, 2) if total_qty else None,
        "group_rule_fired": "n/a",
        "n_pn_unbilled_in_taxonomy": int((~cls_node["billed_l12m"]).sum()),
    }
    out = pd.concat([out, pd.DataFrame([total_row])], ignore_index=True)
    out.to_csv(OUT_SPLIT, index=False)

    # ---- part-number detail ---------------------------------------------------------
    pn_tbl = (
        in_scope.groupby(["part_number", "product_group"], as_index=False)
        .agg(
            qty=("billed_qty", "sum"),
            eur=("net_sales_value", "sum"),
            step_eur=("value_eur_step", "sum"),
            n_distributors=("distributor_code", "nunique"),
            n_customers=("customer_code", "nunique"),
            billed_description=("billed_description", "first"),
            description_norm=("description_norm", "first"),
            aim_l1=("aim_l1", "first"),
            aim_l2=("aim_l2", "first"),
            aim_l3=("aim_l3", "first"),
            fig_key=("fig_key", "first"),
            pms_category=("pms_category", "first"),
            filter_part_role=("filter_part_role", "first"),
            bp_new_class=("bp_new_class", "first"),
            bp_new_jpy=("bp_new_jpy", "first"),
            bp_prior_revised=("bp_prior_revised", "first"),
            delta_pct=("delta_pct", "first"),
            group_rule=("group_rule", "first"),
            aim_source=("aim_source", "first"),
        )
        .sort_values("eur", ascending=False)
    )
    pn_tbl["share_of_bucket_pct"] = (pn_tbl["eur"] / total_eur * 100.0).round(3)
    pn_tbl["eur_per_qty"] = (pn_tbl["eur"] / pn_tbl["qty"]).round(2)
    pn_tbl = pn_tbl[
        [
            "part_number", "product_group", "billed_description", "description_norm",
            "qty", "eur", "share_of_bucket_pct", "eur_per_qty", "step_eur",
            "bp_new_jpy", "bp_prior_revised", "delta_pct", "bp_new_class",
            "n_distributors", "n_customers", "aim_l1", "aim_l2", "aim_l3",
            "fig_key", "pms_category", "filter_part_role", "aim_source", "group_rule",
        ]
    ]
    pn_tbl.to_csv(OUT_PNS, index=False)

    # ---- per-distributor view of the whole bucket ----------------------------------
    dist = (
        in_scope.groupby(["distributor_code", "country", "region"], as_index=False)
        .agg(qty=("billed_qty", "sum"), eur=("net_sales_value", "sum"),
             step_eur=("value_eur_step", "sum"), n_pn=("part_number", "nunique"))
        .sort_values("eur", ascending=False)
    )
    dist["uio_units_2025"] = dist["distributor_code"].map(fleet_map).fillna(0.0)
    dist["billed_eur_per_truck"] = [
        round(r.eur / r.uio_units_2025, 2) if r.uio_units_2025 > 0 else None for r in dist.itertuples()
    ]
    dist.to_csv(OUT_DIST, index=False)

    # Group x market matrix: the only safe base for a rate or a concentration statement.
    grp_dist = (
        in_scope.groupby(["product_group", "distributor_code"], as_index=False)
        .agg(qty=("billed_qty", "sum"), eur=("net_sales_value", "sum"), n_pn=("part_number", "nunique"))
        .sort_values(["product_group", "eur"], ascending=[True, False])
    )
    grp_dist["uio_units_2025"] = grp_dist["distributor_code"].map(fleet_map).fillna(0.0)
    grp_dist["billed_eur_per_truck"] = [
        round(r.eur / r.uio_units_2025, 4) if r.uio_units_2025 > 0 else None for r in grp_dist.itertuples()
    ]
    grp_dist["no_fleet_count_by_design"] = grp_dist["distributor_code"].isin(NO_FLEET_SET)
    grp_dist.to_csv(OUT_GRP_DIST, index=False)

    # ---- big part detail ------------------------------------------------------------
    BIG = "8982878080"
    big = in_scope[in_scope["part_number"] == BIG]
    big_all = all_rows[all_rows["part_number"] == BIG]
    big_scope = big_all[big_all["in_scope"] != True]  # noqa: E712
    big_share = {
        part: {
            "distributor_code": part,
            "country": r.country,
            "qty": float(r.qty),
            "eur": round(float(r.eur), 2),
            "step_eur": round(float(r.step), 2),
            "n_customers": int(r.nc),
            "uio_units_2025": float(fleet_map.get(part, 0.0)),
            "billed_eur_per_truck": round(float(r.eur) / fleet_map[part], 2) if fleet_map.get(part, 0) else None,
        }
        for part, r in (
            big.groupby("distributor_code")
            .agg(qty=("billed_qty", "sum"), eur=("net_sales_value", "sum"),
                 step=("value_eur_step", "sum"), nc=("customer_code", "nunique"),
                 country=("country", "first"))
            .iterrows()
        )
    }
    big_meta = {
        "part_number": BIG,
        "billed_description": "FILTER ASM",
        "description_norm": "FILTER ASM",
        "aim_l1": "Maintenance Service", "aim_l2": "Filters", "aim_l3": "Filter Assembly",
        "catalog_l1": "Competitive parts", "catalog_l2": "Filters", "catalog_l3": "Other filter",
        "fig_key": "150-558", "fig_key_label": "Other filter", "filter_part_role": "assembly",
        "aim_source": "aim_workbook", "bp_new_class": "D",
        "identification_source": "external aftermarket catalogue lookups by part number",
        "identified_as": "Diesel particulate filter (DPF) assembly for Isuzu 4HK1 engines "
                         "(NPR-HD / NPR-XD / NQR / NRR / FTR). Sold new or as a remanufactured / core-exchange unit.",
        "aim_workbook_l1_is_wrong_for_this_part": True,
        "qty": float(big["billed_qty"].sum()),
        "eur": round(float(big["net_sales_value"].sum()), 2),
        "share_of_bucket_pct": round(float(big["net_sales_value"].sum()) / total_eur * 100.0, 2),
        "step_eur": round(float(big["value_eur_step"].sum()), 2),
        "step_eur_per_unit": round(float(big["value_eur_step"].sum()) / float(big["billed_qty"].sum()), 2),
        "bp_new_jpy": float(big["bp_new_jpy"].iloc[0]),
        "bp_prior_revised_jpy": float(big["bp_prior_revised"].iloc[0]),
        "delta_pct": round(float(big["delta_pct"].iloc[0]) * 100.0, 4),
        "net_billed_eur_per_unit": round(float(big["net_sales_value"].sum()) / float(big["billed_qty"].sum()), 2),
        "n_distributors": int(big["distributor_code"].nunique()),
        "by_distributor": list(big_share.values()),
        "out_of_scope_rows": {
            "rows": int(len(big_scope)),
            "qty": float(big_scope["billed_qty"].sum()),
            "eur": round(float(big_scope["net_sales_value"].sum()), 2),
            "roles": sorted(set(big_scope["network_role"].dropna())),
        },
    }

    # ---- reconciliation against the shipped Focus cut --------------------------------
    foc = focus[
        (focus["scheme_basis"] == "catalog_full")
        & (focus["node_type"] == "L3_filter_type")
        & (focus["filter_type"] == "Other filter")
        & (focus["distributor_code"] == "__NETWORK__")
    ].iloc[0]
    per_dist = focus[
        (focus["scheme_basis"] == "catalog_full")
        & (focus["node_type"] == "L3_filter_type")
        & (focus["filter_type"] == "Other filter")
        & (focus["distributor_code"] != "__NETWORK__")
    ]

    reconcile = {
        "focus_file_network_qty": float(foc["l12m_qty"]),
        "focus_file_network_eur": float(foc["l12m_billed_eur"]),
        "focus_file_network_step_eur": float(foc["step_eur"]),
        "focus_file_network_weighted_increase_pct": float(foc["weighted_increase_pct"]),
        "focus_file_network_priced_qty": float(foc["priced_qty_both_sides"]),
        "focus_file_network_n_pn": int(foc["n_pn"]),
        "focus_file_sum_of_distributor_qty": float(per_dist["l12m_qty"].sum()),
        "focus_file_sum_of_distributor_eur": round(float(per_dist["l12m_billed_eur"].sum()), 2),
        "recomputed_qty": total_qty,
        "recomputed_eur": round(total_eur, 2),
        "recomputed_step_eur": round(float(in_scope["value_eur_step"].sum()), 2),
        "recomputed_weighted_increase_pct": round(weighted_increase(in_scope)[0], 4),
        "recomputed_priced_qty": weighted_increase(in_scope)[1],
        "recomputed_n_pn": int(in_scope["part_number"].nunique()),
        "qty_delta": total_qty - float(foc["l12m_qty"]),
        "eur_delta": round(total_eur - float(foc["l12m_billed_eur"]), 2),
        "step_eur_delta": round(float(in_scope["value_eur_step"].sum()) - float(foc["step_eur"]), 2),
        "weighted_increase_delta_pp": round(weighted_increase(in_scope)[0] - float(foc["weighted_increase_pct"]), 4),
        "n_pn_delta": int(in_scope["part_number"].nunique()) - int(foc["n_pn"]),
        "ties_out": bool(
            abs(total_qty - float(foc["l12m_qty"])) < 1e-6
            and abs(total_eur - float(foc["l12m_billed_eur"])) < 0.01
            and abs(float(in_scope["value_eur_step"].sum()) - float(foc["step_eur"])) < 0.01
        ),
    }

    # ---- taxonomy tail (unbilled) ----------------------------------------------------
    tail = cls_node[~cls_node["billed_l12m"]]
    tail_tbl = {
        "n_pn_unbilled_in_taxonomy": int(len(tail)),
        "by_group": tail.groupby("product_group").size().to_dict(),
        "by_aim_l3": tail["aim_l3"].fillna("(blank)").value_counts().to_dict(),
        "with_description": int(tail["description_norm"].notna().sum()),
        "with_fig_key": int(tail["fig_key"].notna().sum()),
    }

    # ---- extra checks quoted in the notes -------------------------------------------
    # VCV: is it consumption or stocking? rate against the fleet of the markets that bill it.
    # Denominator must be unique markets, not the sum of customer rows (Denmark and Portugal
    # each bill this part on two customer codes).
    vcv = in_scope[in_scope["product_group"].str.startswith("Crankcase ventilation")]
    vcv_markets = sorted(set(vcv["distributor_code"]))
    vcv_uio = float(sum(fleet_map.get(d, 0.0) for d in vcv_markets))
    vcv_qty = float(vcv["billed_qty"].sum())
    vcv_eur = float(vcv["net_sales_value"].sum())
    vcv_checks = {
        "qty": vcv_qty,
        "eur": round(vcv_eur, 2),
        "markets": len(vcv_markets),
        "uio_of_its_markets_unique": vcv_uio,
        "uio_sum_of_customer_rows_double_counted": float(vcv["uio_units_2025"].sum()),
        "units_per_truck_per_year": round(vcv_qty / vcv_uio, 4) if vcv_uio else None,
        "implied_years_between_replacements": round(vcv_uio / vcv_qty, 1) if vcv_qty else None,
        "top_market": vcv.groupby("distributor_code")["net_sales_value"].sum().idxmax(),
        "top_market_eur": round(float(vcv.groupby("distributor_code")["net_sales_value"].sum().max()), 2),
        "top_market_share_pct": round(
            float(vcv.groupby("distributor_code")["net_sales_value"].sum().max()) / vcv_eur * 100.0, 1
        ),
        "note": "not a service interval - this is stocking behaviour. UMI is ~2/3 of the volume.",
        "by_market": vcv.groupby("distributor_code").agg(
            qty=("billed_qty", "sum"), eur=("net_sales_value", "sum")
        ).round(2).to_dict("index"),
    }

    # Where the aftertreatment parts would go if the taxonomy were corrected.
    # NOTE: "Exhaust" is a catalog_l2 value (under Competitive parts), not a catalog_l1 value.
    at_rows = in_scope[in_scope["product_group"].str.startswith("Aftertreatment")]
    target = cls[(cls["catalog_l2"] == "Exhaust") & (cls["catalog_l3"] == "Aftertreatment")]
    fig_members = cls[cls["fig_key"] == "150-558"]
    fig_members_node = fig_members["catalog_l3"].value_counts().to_dict()
    at_checks = {
        "aftertreatment_pns_billed": int(at_rows["part_number"].nunique()),
        "aftertreatment_eur": round(float(at_rows["net_sales_value"].sum()), 2),
        "aftertreatment_all_class_D": bool(set(at_rows["bp_new_class"].dropna()) == {"D"}),
        "existing_Exhaust_Aftertreatment_pns_in_taxonomy": int(len(target)),
        "fig_150_558_members_in_taxonomy": int(len(fig_members)),
        "fig_150_558_members_by_current_node": fig_members_node,
        "note": "figure key 150-558 sits inside the 150-xxx exhaust aftertreatment figure sequence; "
                "its members already split across two nodes today, so the node assignment is applied "
                "inconsistently inside one figure group. A move would be a PRISM-owned taxonomy change.",
    }

    # ---- meta ----------------------------------------------------------------------
    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_other_filter_split.py",
        "basis": "catalog_full - catalogue columns on ALL rows, not restricted to aim_source == 'pr00_catalog'",
        "window": {"start": "2025-07-01", "end": "2026-06-30", "basis": "L12M billed parts in the shipped comparison"},
        "bucket": {"catalog_l2": NODE_L2, "catalog_l3": NODE_L3},
        "in_scope_row_count": int(len(in_scope)),
        "in_scope_row_count_all_scope_incl": int(len(all_rows)),
        "out_of_scope_rows": oos_detail,
        "join_missing": join_note,
        "reconciliation": reconcile,
        "taxonomy": {
            "unique_part_numbers_in_node": int(len(cls_node)),
            "of_which_billed_l12m": int(cls_node["billed_l12m"].sum()),
            "unbilled_tail": tail_tbl,
        },
        "big_part": big_meta,
        "vcv_check": vcv_checks,
        "aftertreatment_check": at_checks,
        "no_fleet_markets": NO_FLEET,
        "network_uio_2025_18_markets": float(fl[fl["uio_units"] > 0]["uio_units"].sum()),
        "note": "report only; the source taxonomy in 03_analytics/Isuzu/prism/modules/aim_pn_classifier.py is PRISM-owned and was not touched",
    }

    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, default=str)

    # ---- console summary ------------------------------------------------------------
    print(out.to_string(index=False))
    print()
    print("RECONCILIATION:", json.dumps(reconcile, indent=2))
    print()
    print("BIG PART:", json.dumps(big_meta, indent=2, default=str))
    print()
    print("OUT OF SCOPE (excluded from the bucket):")
    print(out_of_scope.groupby(["network_role"])["net_sales_value"].agg(["size", "sum"]).to_string())
    print()
    print("UNBILLED TAXONOMY TAIL:", tail_tbl["n_pn_unbilled_in_taxonomy"], "PN")
    print(json.dumps(tail_tbl["by_group"], indent=2))
    print()
    print("WROTE:", OUT_SPLIT.name, OUT_PNS.name, OUT_META.name)


if __name__ == "__main__":
    main()
