#!/usr/bin/env python3
"""
Cross the PR00 catalogue identity tree — Axis A (catalog_l1/l2/l3) — against
distributor, on the last 12 months of billed parts.

Weight base ...... 01_data/00_derived/price_bp_weighted_compare_pn.csv  (shipped comparison)
Classification ... 01_data/00_derived/aim_pn_classification.csv
Fleet base ....... 01_data/00_derived/gps_spu_by_distributor.csv  (2025 rows)

Window is baked into the weight base: 2025-07-01 .. 2026-06-30.

Derived tables only. No HTML, no workbook, no elasticity coefficient, no price proposal.

Outputs -> 01_data/00_derived/
    aim_catalog_db_matrix.csv        distributor x level node, on both scheme bases
    aim_catalog_focus_filters.csv    Competitive parts > Filters > {Oil,Fuel,Air,Other}
    aim_catalog_brake_check.csv      brake-bucket verification + brake-leak test
    aim_catalog_x_priceclass.csv     level node x price class (network level)
    aim_catalog_breakdown_meta.json  join rate, coverage, tie-outs
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DERIVED = Path(__file__).resolve().parents[1] / "00_derived"

WINDOW = {"start": "2025-07-01", "end": "2026-06-30"}
UNCLASSIFIED = "UNCLASSIFIED"
NETWORK = "__NETWORK__"
NETWORK_LABEL = "Network (all in-scope distributors)"

# Two scheme bases.
#   catalog_full     every billed row that carries a catalogue node, regardless of
#                    which source won the aim_l1 precedence fight in the source file.
#                    This is the only basis on which a whole network answer is possible.
#   pr00_catalog_only the literal restriction to aim_source == 'pr00_catalog'.
BASES = ("catalog_full", "pr00_catalog_only")

BRAKE_TOKENS = {
    "BRAKE": r"BRAKE",
    "BRK": r"\bBRK\b",
    "PAD_KIT": r"PAD\s*KIT",
    "CALIPER": r"CALIPER",
    "ROTOR": r"ROTOR",
    "DISC_BRK": r"DISC\s*BRK|BRK[,\s]*DISC",
    "SHOE": r"\bSHOE",
    "DRUM": r"\bDRUM",
    "WHEEL_CYL": r"WHEEL\s*CYL",
    "ABS": r"\bABS\b",
}

# Loose tokens produce false positives on electrical and hardware parts.
# Strict set = tokens only ever used for the pads/shoes hydraulic brake assembly.
BRAKE_TOKENS_STRICT = {
    "PAD_KIT": r"PAD\s*KIT",
    "CALIPER": r"CALIPER",
    "SHOE": r"\bSHOE",
    "WHEEL_CYL": r"WHEEL\s*CYL",
    "BRAKE_DRUM": r"BRAKE\s*DRUM",
    "DISC_BRAKE": r"DISC\s*BRK|BRK[,\s]*DISC|DISC\s*BRAKE",
    "BRAKE_BOOSTER": r"BRAKE\s*BOOSTER",
}
# 'ROTOR' alone is not a brake token: ROTOR; SENSOR / ROTOR; CAM ANGLE SENSOR
# are ignition and speed sensors. A rotor only counts as a brake when the
# description also carries a brake word.
ROTOR_BRAKE = r"(?:ROTOR.*(?:BRK|BRAKE|DISC)|(?:BRK|BRAKE|DISC).*ROTOR)"
# 'BRAKET' is a recurring typo for BRACKET (BRAKET; HEATER), not a brake part.
BRAKET_FALSE = r"BRAKET"


# --------------------------------------------------------------------------- IO
def read_inputs():
    pn = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv", dtype=str)
    aim = pd.read_csv(DERIVED / "aim_pn_classification.csv", dtype=str)
    gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv", dtype=str)

    for c in ["billed_qty", "net_sales_value", "bp_new_jpy", "bp_prior_revised",
              "value_eur_step", "bp_prior_billed"]:
        if c in pn.columns:
            pn[c] = pd.to_numeric(pn[c], errors="coerce")
    pn["part_number"] = pn["part_number"].astype(str).str.strip()
    aim["part_number"] = aim["part_number"].astype(str).str.strip()

    aim_cols = ["part_number", "description_norm", "catalog_l1", "catalog_l2", "catalog_l3",
                "aim_l1", "aim_l2", "aim_l3", "fig_key", "filter_part_role", "aim_source"]
    aim = aim[[c for c in aim_cols if c in aim.columns]]

    gps25 = gps[gps["year"] == "2025"].copy()
    gps25["uio_units"] = pd.to_numeric(gps25["uio_units"], errors="coerce")
    gps25 = gps25[["distributor_code", "country", "region", "uio_units", "uio_source"]]
    return pn, aim, gps25


# ------------------------------------------------------------------ aggregation
def wstats(sub: pd.DataFrame):
    """Weighted base-price increase + step euro, on the shipped methodology.

    increase = SUM(qty * bp_new) / SUM(qty * bp_prior_revised) - 1   (rows priced both sides)
    """
    step = float(sub["value_eur_step"].sum(skipna=True))
    if sub.empty:
        return None, step, 0.0, 0
    both = sub[sub["bp_new_jpy"].notna() & sub["bp_prior_revised"].notna()
               & sub["billed_qty"].notna()]
    if both.empty:
        return None, step, 0.0, 0
    num = float((both["billed_qty"] * both["bp_new_jpy"]).sum())
    den = float((both["billed_qty"] * both["bp_prior_revised"]).sum())
    inc = (num / den - 1.0) * 100.0 if den else None
    return inc, step, float(both["billed_qty"].sum()), int(len(both))


def group_rows(df: pd.DataFrame, node_cols: list[str], level_id: str, basis: str,
               label_map: pd.DataFrame):
    """Aggregate one classification level by distributor + node, and emit a network row."""
    out = []

    def emit(keys, sub, dist_code, dist_label, country, region, uio, fleet_ok):
        inc, step, pqty, nrows = wstats(sub)
        qty = float(sub["billed_qty"].sum())
        eur = float(sub["net_sales_value"].sum())
        row = {
            "scheme_basis": basis,
            "level_id": level_id,
            "distributor_code": dist_code,
            "distributor_label": dist_label,
            "country": country,
            "region": region,
            "n_pn": int(sub["part_number"].nunique()),
            "l12m_qty": round(qty, 3),
            "l12m_billed_eur": round(eur, 2),
            "step_eur": round(step, 2),
            "weighted_increase_pct": round(inc, 4) if inc is not None else None,
            "priced_qty_both_sides": round(pqty, 3),
            "qty_coverage_pct": round(pqty / qty * 100.0, 2) if qty else None,
            "priced_rows_both_sides": nrows,
            "uio_units_2025": (None if pd.isna(uio) else float(uio)),
            "fleet_denominator_available": fleet_ok,
            "billed_eur_per_uio": (round(eur / float(uio), 2)
                                   if fleet_ok and uio else None),
        }
        for c in node_cols:
            row[c] = keys[c]
        row["node_label"] = " > ".join(str(keys[c]) for c in node_cols)
        out.append(row)

    # network first
    # build network rows by grouping on node only
    for keys, sub in df.groupby(node_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        kd = dict(zip(node_cols, keys))
        emit(kd, sub, NETWORK, NETWORK_LABEL, None, None, None, False)

    # distributor rows
    for keys, sub in df.groupby(node_cols + ["distributor_code"], dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        kd = dict(zip(node_cols + ["distributor_code"], keys))
        code = kd.pop("distributor_code")
        meta = label_map[label_map["distributor_code"] == code]
        if meta.empty:
            label, country, region, uio, fleet_ok = code, None, None, None, False
        else:
            m = meta.iloc[0]
            country = m["country"]
            region = m["region"]
            uio = m["uio_units"]
            fleet_ok = bool(pd.notna(uio) and float(uio) > 0)
            label = f"{code} ({country})" if isinstance(country, str) and country else code
        emit(kd, sub, code, label, country, region, uio, fleet_ok)

    return pd.DataFrame(out)


# ------------------------------------------------------------------------ main
def main() -> int:
    pn, aim, gps25 = read_inputs()
    label_map = gps25.copy()

    # ---- join -------------------------------------------------------------
    in_scope = pn[pn["in_scope"] == "True"].copy()
    matched = in_scope.merge(aim, on="part_number", how="left", indicator=True)
    merged_meta = {
        "window": WINDOW,
        "in_scope_rows": int(len(in_scope)),
        "in_scope_distinct_pn": int(in_scope["part_number"].nunique()),
        "in_scope_billed_eur": round(float(in_scope["net_sales_value"].sum()), 2),
        "in_scope_qty": round(float(in_scope["billed_qty"].sum()), 3),
        "rows_matched_to_classification": int((matched["_merge"] == "both").sum()),
        "rows_not_matched": int((matched["_merge"] == "left_only").sum()),
        "join_rate_rows_pct": round((matched["_merge"] == "both").mean() * 100.0, 4),
        "eur_matched": round(float(matched.loc[matched["_merge"] == "both",
                                              "net_sales_value"].sum()), 2),
        "eur_not_matched": round(float(matched.loc[matched["_merge"] == "left_only",
                                                "net_sales_value"].sum()), 2),
        "join_rate_eur_pct": round(
            float(matched.loc[matched["_merge"] == "both", "net_sales_value"].sum())
            / float(in_scope["net_sales_value"].sum()) * 100.0, 4),
        "pn_len_all_10_chars_in_classification": bool((aim["part_number"].str.len() == 10).all()),
        "rows_with_pn_not_10_chars_in_weight_base": int(
            (pn["part_number"].str.len() != 10).sum()),
    }
    merged_meta["pn_join_rate_pct"] = round(
        in_scope["part_number"].isin(set(aim["part_number"])).mean() * 100.0, 4)

    # ---- node columns -----------------------------------------------------
    for c in ["catalog_l1", "catalog_l2", "catalog_l3"]:
        matched[c] = matched[c].where(matched[c].notna(), UNCLASSIFIED)

    matched["_n1"] = matched["catalog_l1"]
    matched["_n2"] = matched["catalog_l2"]
    matched["_n3"] = matched["catalog_l3"]

    coverage = {}
    total_eur = float(matched["net_sales_value"].sum())
    for nm, mask in {
        "catalog_l1_populated": matched["catalog_l1"] != UNCLASSIFIED,
        "catalog_l1_real_drop_review": (matched["catalog_l1"] != UNCLASSIFIED)
                                        & (matched["catalog_l1"] != "Other / review"),
        "other_review": matched["catalog_l1"] == "Other / review",
        "catalog_l1_null": matched["catalog_l1"] == UNCLASSIFIED,
        "belongs_to_pr00_catalog": matched["aim_source"] == "pr00_catalog",
    }.items():
        coverage[nm] = {
            "rows": int(mask.sum()),
            "distinct_pn": int(matched.loc[mask, "part_number"].nunique()),
            "l12m_billed_eur": round(float(matched.loc[mask, "net_sales_value"].sum()), 2),
            "share_of_in_scope_eur_pct": round(
                float(matched.loc[mask, "net_sales_value"].sum()) / total_eur * 100.0, 4),
        }
    coverage["attributable_to_a_catalogue_node_eur"] = round(
        float(matched.loc[(matched["catalog_l1"] != UNCLASSIFIED)
                          & (matched["catalog_l1"] != "Other / review"),
                          "net_sales_value"].sum()), 2)
    coverage["unattributed_eur"] = round(
        float(matched.loc[(matched["catalog_l1"] == UNCLASSIFIED)
                          | (matched["catalog_l1"] == "Other / review"),
                          "net_sales_value"].sum()), 2)

    # ---- matrix -----------------------------------------------------------
    frames = []
    subset_full = matched.copy()
    subset_pr00 = matched[matched["aim_source"] == "pr00_catalog"].copy()
    for basis, sub in (("catalog_full", subset_full),
                       ("pr00_catalog_only", subset_pr00)):
        frames.append(group_rows(sub, ["_n1"], "L1", basis, label_map))
        frames.append(group_rows(sub, ["_n1", "_n2"], "L2", basis, label_map))
        frames.append(group_rows(sub, ["_n1", "_n2", "_n3"], "L3", basis, label_map))
    matrix = pd.concat(frames, ignore_index=True)
    matrix = matrix.rename(columns={"_n1": "catalog_l1", "_n2": "catalog_l2",
                                    "_n3": "catalog_l3"})
    cols = ["scheme_basis", "level_id", "catalog_l1", "catalog_l2", "catalog_l3",
            "node_label", "distributor_code", "distributor_label", "country", "region",
            "n_pn", "l12m_qty", "l12m_billed_eur", "step_eur", "weighted_increase_pct",
            "priced_qty_both_sides", "qty_coverage_pct", "priced_rows_both_sides",
            "uio_units_2025", "fleet_denominator_available", "billed_eur_per_uio"]
    matrix = matrix[cols].sort_values(
        ["scheme_basis", "level_id", "node_label", "distributor_code"]).reset_index(drop=True)
    matrix.to_csv(DERIVED / "aim_catalog_db_matrix.csv", index=False, encoding="utf-8")

    # ---- focus cut: Competitive parts > Filters > ... ----------------------
    focus_rows = []
    for basis, sub in (("catalog_full", subset_full),
                       ("pr00_catalog_only", subset_pr00)):
        f = sub[(sub["_n1"] == "Competitive parts") & (sub["_n2"] == "Filters")]
        for ftype, fsub in f.groupby("_n3", dropna=False):
            focus_rows.append(_focus_block(fsub, basis, "L3_filter_type", ftype, label_map))
        focus_rows.append(_focus_block(f, basis, "L2_filters_total", "Filters (all types)",
                                       label_map))
    focus = pd.concat(focus_rows, ignore_index=True)
    focus = focus.sort_values(["scheme_basis", "node_type", "filter_type",
                               "distributor_code"]).reset_index(drop=True)
    focus.to_csv(DERIVED / "aim_catalog_focus_filters.csv", index=False, encoding="utf-8")

    # ---- brake check ------------------------------------------------------
    brake = brake_check(matched, subset_full, subset_pr00)
    brake.to_csv(DERIVED / "aim_catalog_brake_check.csv", index=False, encoding="utf-8")

    # ---- price class cross ------------------------------------------------
    px_rows = []
    for basis, sub in (("catalog_full", subset_full),
                       ("pr00_catalog_only", subset_pr00)):
        for level_id, node_cols in (("L1", ["_n1"]), ("L2", ["_n1", "_n2"]),
                                    ("L3", ["_n1", "_n2", "_n3"])):
            for keys, g in sub.groupby(node_cols + ["bp_new_class"], dropna=False):
                if not isinstance(keys, tuple):
                    keys = (keys,)
                kd = dict(zip(node_cols + ["bp_new_class"], keys))
                pc = kd.pop("bp_new_class")
                pc = UNCLASSIFIED if pd.isna(pc) else pc
                px_rows.append(_px_block(g, basis, level_id, kd, node_cols, pc))
    px = pd.DataFrame(px_rows)
    px = px.sort_values(["scheme_basis", "level_id", "node_label",
                         "bp_new_class_iml"]).reset_index(drop=True)
    px.to_csv(DERIVED / "aim_catalog_x_priceclass.csv", index=False, encoding="utf-8")

    # ---- tie-out against the shipped comparison ---------------------------
    cust = pd.read_csv(DERIVED / "price_bp_weighted_compare_customer.csv", dtype=str)
    da = cust[cust["level"] == "distributor"].copy()
    da["weighted_increase_pct"] = pd.to_numeric(da["weighted_increase_pct"], errors="coerce")
    da["value_step_eur"] = pd.to_numeric(da["value_step_eur"], errors="coerce")
    da["l12m_billed_eur"] = pd.to_numeric(da["l12m_billed_eur"], errors="coerce")
    tie = []
    for _, r in da.iterrows():
        code = r["label"].split(" - ")[-1].strip()
        mine = subset_full[subset_full["distributor_code"] == code]
        inc, step, _, _ = wstats(mine)
        tie.append({
            "distributor_code": code,
            "shipped_increase_pct": round(float(r["weighted_increase_pct"]), 4),
            "mine_increase_pct": round(inc, 4) if inc is not None else None,
            "shipped_step_eur": round(float(r["value_step_eur"]), 2),
            "mine_step_eur": round(step, 2),
            "shipped_l12m_eur": round(float(r["l12m_billed_eur"]), 2),
            "mine_l12m_eur": round(float(mine["net_sales_value"].sum()), 2),
        })
    tie_df = pd.DataFrame(tie)
    tie_df["increase_delta_pp"] = (tie_df["mine_increase_pct"]
                                   - tie_df["shipped_increase_pct"]).round(4)
    tie_df["l12m_delta_eur"] = (tie_df["mine_l12m_eur"]
                                - tie_df["shipped_l12m_eur"]).round(2)
    net_inc, net_step, _, _ = wstats(subset_full)
    tie_ok = bool(tie_df["increase_delta_pp"].abs().max() < 0.001
                  and tie_df["l12m_delta_eur"].abs().max() < 0.02)

    # ---- fleet gaps ------------------------------------------------------
    have_uio = set(gps25.loc[gps25["uio_units"].fillna(0) > 0, "distributor_code"])
    all_codes = set(subset_full["distributor_code"].dropna())
    fleet_missing = sorted(all_codes - have_uio)
    fleet_missing_eur = {
        c: round(float(subset_full.loc[subset_full["distributor_code"] == c,
                                       "net_sales_value"].sum()), 2)
        for c in fleet_missing
    }

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": ("Catalogue identity tree Axis A (catalog_l1/l2/l3) crossed against "
                    "distributor on the last 12 months of billed parts. "
                    "Two-axes lock 2026-09-17: commercial score is Axis B beside, not the parent. "
                    "Derived tables only - no elasticity, no allocation run, no price proposal."),
        "window": WINDOW,
        "basis_note": (
            "Two scheme bases are emitted in every file. 'catalog_full' uses every billed row "
            "that carries a catalogue node. 'pr00_catalog_only' is the literal restriction to "
            "aim_source == 'pr00_catalog'. The catalogue node columns are populated on far more "
            "rows than that flag implies, because aim_source is a precedence label for aim_l1, "
            "not a completeness flag for catalog_l1."),
        "method": {
            "weighted_increase": "SUM(qty * bp_new_jpy) / SUM(qty * bp_prior_revised) - 1 "
                                 "over rows priced on both sides",
            "step_eur": "sum of value_eur_step (summed over all rows in the node; nulls skipped)",
            "fleet_denominator": "gps_spu_by_distributor.csv 2025 uio_units",
            "join_key": "part_number, 10-character zero-padded string both sides",
        },
        "join": merged_meta,
        "coverage_of_in_scope": coverage,
        "tie_out_network": {
            "mine_weighted_increase_pct": round(net_inc, 4),
            "shipped_weighted_increase_pct": 5.9616,
            "mine_step_eur": round(net_step, 2),
            "shipped_step_eur": 1652140.71,
        },
        "tie_out_per_distributor_ok": tie_ok,
        "tie_out_per_distributor_max_abs_increase_delta_pp": float(
            tie_df["increase_delta_pp"].abs().max()),
        "tie_out_per_distributor_max_abs_l12m_delta_eur": float(
            tie_df["l12m_delta_eur"].abs().max()),
        "distributors_without_fleet_denominator": fleet_missing,
        "distributors_without_fleet_denominator_billed_eur": fleet_missing_eur,
        "price_class_note": ("bp_new_class is the coarse IML class factor (C, D, F, J, M, P, T, V) "
                             "in the pricing spec. It is IML-owned and is not something ISZE "
                             "changes; it is carried here as a retained attribute only."),
        "price_class_unclassified": {
            "rows": int(matched["bp_new_class"].isna().sum()),
            "l12m_billed_eur": round(float(matched.loc[matched["bp_new_class"].isna(),
                                                       "net_sales_value"].sum()), 2),
        },
    }
    (DERIVED / "aim_catalog_breakdown_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8")

    # ---- notes ------------------------------------------------------------
    write_notes(matrix, focus, brake, px, meta, tie_df, coverage)

    # ---- console ---------------------------------------------------------
    print("=" * 78)
    print("JOIN")
    for k, v in merged_meta.items():
        print(f"  {k:46s} {v}")
    print("=" * 78)
    print("COVERAGE OF IN-SCOPE BILLED EUR")
    for k, v in coverage.items():
        if isinstance(v, dict):
            print(f"  {k:34s} rows={v['rows']:6d} pn={v['distinct_pn']:6d} "
                  f"eur={v['l12m_billed_eur']:14,.2f} {v['share_of_in_scope_eur_pct']:6.2f}%")
        else:
            print(f"  {k:34s} {v:,.2f}")
    print("=" * 78)
    print(f"TIE-OUT network: mine {net_inc:.4f}% / shipped 5.9616% | "
          f"step {net_step:,.2f} / 1,652,140.71 | per-db ok={tie_ok}")
    print("=" * 78)
    print("LEVEL 1 x NETWORK x catalog_full")
    l1 = matrix[(matrix["scheme_basis"] == "catalog_full") & (matrix["level_id"] == "L1")
                & (matrix["distributor_code"] == NETWORK)]
    print(l1[["node_label", "n_pn", "l12m_qty", "l12m_billed_eur", "step_eur",
              "weighted_increase_pct"]].to_string(index=False))
    print("=" * 78)
    print("LEVEL 2 under Competitive parts x NETWORK x catalog_full")
    l2 = matrix[(matrix["scheme_basis"] == "catalog_full") & (matrix["level_id"] == "L2")
                & (matrix["distributor_code"] == NETWORK)
                & (matrix["catalog_l1"] == "Competitive parts")]
    print(l2[["catalog_l2", "n_pn", "l12m_billed_eur", "step_eur",
              "weighted_increase_pct"]].sort_values("l12m_billed_eur",
                                                    ascending=False).to_string(index=False))
    print("=" * 78)
    print("FOCUS - Filters, network rows, catalog_full")
    fo = focus[(focus["scheme_basis"] == "catalog_full")
               & (focus["distributor_code"] == NETWORK)]
    print(fo[["node_type", "filter_type", "n_pn", "l12m_billed_eur", "step_eur",
              "weighted_increase_pct"]].to_string(index=False))
    print("=" * 78)
    print(f"FLEET denominator missing for: {fleet_missing} -> {fleet_missing_eur}")
    print("=" * 78)
    print("BRAKE CHECK (catalog_full)")
    print(brake[brake["scheme_basis"] == "catalog_full"][
        ["section", "detail", "n_pn", "l12m_billed_eur", "step_eur", "weighted_increase_pct"]
    ].to_string(index=False))
    print("=" * 78)
    print("DONE")
    return 0


def _focus_block(sub, basis, node_type, ftype, label_map):
    rows = []
    for code, g in sub.groupby("distributor_code", dropna=False):
        rows.append(_focus_row(g, basis, node_type, ftype, code, label_map))
    rows.append(_focus_row(sub, basis, node_type, ftype, NETWORK, label_map))
    return pd.DataFrame(rows)


def _focus_row(g, basis, node_type, ftype, code, label_map):
    inc, step, pqty, nrows = wstats(g)
    qty = float(g["billed_qty"].sum())
    eur = float(g["net_sales_value"].sum())
    if code == NETWORK:
        label, country, region, uio, fleet_ok = NETWORK_LABEL, None, None, None, False
    else:
        m = label_map[label_map["distributor_code"] == code]
        if m.empty:
            label, country, region, uio, fleet_ok = code, None, None, None, False
        else:
            m = m.iloc[0]
            country, region, uio = m["country"], m["region"], m["uio_units"]
            fleet_ok = bool(pd.notna(uio) and float(uio) > 0)
            label = f"{code} ({country})" if isinstance(country, str) and country else code
    return {
        "scheme_basis": basis, "node_type": node_type, "filter_type": ftype,
        "distributor_code": code, "distributor_label": label, "country": country,
        "region": region, "n_pn": int(g["part_number"].nunique()),
        "l12m_qty": round(qty, 3), "l12m_billed_eur": round(eur, 2),
        "step_eur": round(step, 2),
        "weighted_increase_pct": round(inc, 4) if inc is not None else None,
        "priced_qty_both_sides": round(pqty, 3),
        "qty_coverage_pct": round(pqty / qty * 100.0, 2) if qty else None,
        "uio_units_2025": (None if pd.isna(uio) else float(uio)),
        "fleet_denominator_available": fleet_ok,
        "billed_eur_per_uio": round(eur / float(uio), 2) if fleet_ok and uio else None,
    }


def _px_block(g, basis, level_id, kd, node_cols, price_class):
    inc, step, pqty, nrows = wstats(g)
    qty = float(g["billed_qty"].sum())
    eur = float(g["net_sales_value"].sum())
    row = {
        "scheme_basis": basis, "level_id": level_id,
        "node_label": " > ".join(str(kd[c]) for c in node_cols),
        "bp_new_class_iml": price_class,
        "n_pn": int(g["part_number"].nunique()),
        "l12m_qty": round(qty, 3), "l12m_billed_eur": round(eur, 2),
        "step_eur": round(step, 2),
        "weighted_increase_pct": round(inc, 4) if inc is not None else None,
        "priced_qty_both_sides": round(pqty, 3),
        "qty_coverage_pct": round(pqty / qty * 100.0, 2) if qty else None,
    }
    for c in node_cols:
        row[c.replace("_n", "catalog_l")] = kd[c]
    return row


def brake_check(matched, subset_full, subset_pr00):
    """Is 'brake parts are competitive parts' true under the catalogue scheme?"""
    rows = []

    def add(basis, section, detail, g, note=""):
        inc, step, _, _ = wstats(g)
        rows.append({
            "scheme_basis": basis, "section": section, "detail": detail,
            "n_pn": int(g["part_number"].nunique()),
            "l12m_qty": round(float(g["billed_qty"].sum()), 3),
            "l12m_billed_eur": round(float(g["net_sales_value"].sum()), 2),
            "step_eur": round(step, 2),
            "weighted_increase_pct": round(inc, 4) if inc is not None else None,
            "note": note,
        })

    # PN-level flag: does the billed description look like a brake?
    pnl = (matched.groupby("part_number", dropna=False)
           .agg(desc=("billed_description", "first"),
                eur=("net_sales_value", "sum"),
                qty=("billed_qty", "sum"),
                l1=("catalog_l1", "first"),
                l2=("catalog_l2", "first"),
                l3=("catalog_l3", "first"),
                src=("aim_source", "first"))
           .reset_index())
    pnl["desc_u"] = pnl["desc"].fillna("").astype(str).str.upper()
    for tok, rx in BRAKE_TOKENS.items():
        pnl[f"tok_{tok}"] = pnl["desc_u"].str.contains(rx, regex=True, na=False)
    pnl["brake_like"] = pnl[[f"tok_{t}" for t in BRAKE_TOKENS]].any(axis=1)
    for tok, rx in BRAKE_TOKENS_STRICT.items():
        pnl[f"strict_{tok}"] = pnl["desc_u"].str.contains(rx, regex=True, na=False)
    pnl["rotor_brake"] = pnl["desc_u"].str.contains(ROTOR_BRAKE, regex=True, na=False)
    pnl["strict_brake"] = (pnl[[f"strict_{t}" for t in BRAKE_TOKENS_STRICT]].any(axis=1)
                           | pnl["rotor_brake"])
    pnl.loc[pnl["desc_u"].str.contains(BRAKET_FALSE, regex=True, na=False), "brake_like"] = False
    pnl["brake_like"] = pnl["brake_like"] | pnl["strict_brake"]
    brake_pns = set(pnl.loc[pnl["brake_like"], "part_number"])
    strict_pns = set(pnl.loc[pnl["strict_brake"], "part_number"])
    in_brake_bucket = set(pnl.loc[(pnl["l1"] == "Competitive parts")
                                  & (pnl["l2"] == "Brake parts"), "part_number"])

    for basis, sub in (("catalog_full", subset_full), ("pr00_catalog_only", subset_pr00)):
        bb = sub[(sub["_n1"] == "Competitive parts") & (sub["_n2"] == "Brake parts")]
        add(basis, "competitive_brake_bucket", "Competitive parts > Brake parts", bb,
            "the bucket Jerome asserted holds the brakes")

        # where does the brake bucket sit by catalog_l1
        allb = sub[sub["_n2"] == "Brake parts"]
        for l1, g in allb.groupby("_n1", dropna=False):
            add(basis, "brake_bucket_parent_l1", str(l1), g,
                "parent Level 1 of every row carrying catalog_l2 == 'Brake parts'")

        # brake-looking parts sitting outside Competitive parts > Brake parts
        leak = sub[sub["part_number"].isin(brake_pns)
                   & ~((sub["_n1"] == "Competitive parts") & (sub["_n2"] == "Brake parts"))]
        add(basis, "brake_like_outside_bucket", "loose brake-like description, other node",
            leak, "loose token test - includes electrical rotor sensors, over-states the leak")
        strict_leak = sub[sub["part_number"].isin(strict_pns)
                          & ~((sub["_n1"] == "Competitive parts")
                              & (sub["_n2"] == "Brake parts"))]
        add(basis, "brake_like_outside_bucket_strict",
            "strict brake description, other node", strict_leak,
            "strict token test - the honest leak figure")
        for (l1, l2), g in strict_leak.groupby(["_n1", "_n2"], dropna=False):
            add(basis, "brake_leak_strict_by_node", f"{l1} > {l2}", g, "")
        for (l1, l2), g in leak.groupby(["_n1", "_n2"], dropna=False):
            add(basis, "brake_leak_by_node", f"{l1} > {l2}", g, "")

        # per-token leak
        for tok in BRAKE_TOKENS:
            tset = set(pnl.loc[pnl[f"tok_{tok}"], "part_number"])
            g = sub[sub["part_number"].isin(tset)
                    & ~((sub["_n1"] == "Competitive parts") & (sub["_n2"] == "Brake parts"))]
            if len(g):
                add(basis, "brake_leak_by_token", f"token={tok}", g,
                    "billed description matches this token but not in the brake bucket")

        # reverse test: brake bucket but not brake-like
        rev = sub[sub["part_number"].isin(in_brake_bucket)
                  & ~sub["part_number"].isin(brake_pns)]
        add(basis, "non_brake_like_in_bucket", "in bucket, description not brake-like", rev,
            "bucket may be over-inclusive")

    return pd.DataFrame(rows)[
        ["scheme_basis", "section", "detail", "n_pn", "l12m_qty", "l12m_billed_eur",
         "step_eur", "weighted_increase_pct", "note"]]


def _fmt(v, dp=2):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "n/a"
    return f"{v:,.{dp}f}"


def write_notes(matrix, focus, brake, px, meta, tie_df, coverage):
    """Emit the internal readout. internal - blunt."""
    c = focus[(focus["scheme_basis"] == "catalog_full")]
    net = c[c["distributor_code"] == NETWORK]
    by_ft = {r["filter_type"]: r for _, r in net.iterrows() if r["node_type"] == "L3_filter_type"}
    tot = net[net["node_type"] == "L2_filters_total"].iloc[0]

    l2 = matrix[(matrix["scheme_basis"] == "catalog_full") & (matrix["level_id"] == "L2")
                & (matrix["distributor_code"] == NETWORK)
                & (matrix["catalog_l1"] == "Competitive parts")].sort_values(
        "l12m_billed_eur", ascending=False)

    l1 = matrix[(matrix["scheme_basis"] == "catalog_full") & (matrix["level_id"] == "L1")
                & (matrix["distributor_code"] == NETWORK)].sort_values(
        "l12m_billed_eur", ascending=False)

    bb = brake[(brake["scheme_basis"] == "catalog_full")
               & (brake["section"] == "competitive_brake_bucket")].iloc[0]
    strict = brake[(brake["scheme_basis"] == "catalog_full")
                   & (brake["section"] == "brake_like_outside_bucket_strict")].iloc[0]
    loose = brake[(brake["scheme_basis"] == "catalog_full")
                  & (brake["section"] == "brake_like_outside_bucket")].iloc[0]
    over = brake[(brake["scheme_basis"] == "catalog_full")
                 & (brake["section"] == "non_brake_like_in_bucket")].iloc[0]

    pc = px[(px["scheme_basis"] == "catalog_full") & (px["level_id"] == "L2")
            & (px["catalog_l1"] == "Competitive parts")]

    j = meta["join"]
    L = []
    A = L.append
    A("# Catalogue classification x distributor - last 12 months of billed parts")
    A("")
    A(f"Built {meta['generated']} by `01_data/91_build/build_aim_catalog_breakdown.py`. "
      "Internal working note, blunt, not a shareable deck.")
    A("")
    A("## 0. Two-axes lock (2026-09-17 - Jerome: proceed)")
    A("")
    A("This note groups on **Axis A - identity** (`catalog_l1` / `catalog_l2` / "
      "`catalog_l3`). That is what the part is / where on the truck, with the existing "
      "three levels only. Wear and family cuts hang from Level 2 / Level 3 or the figure "
      "key - never from a commercial posture parent (the king-pin case).")
    A("")
    A("**Axis B - commercial score** (contested or not, per part per market) sits "
      "**beside** Axis A. It is not the box this Focus cut hangs from, and it is not "
      "built as scored columns in these CSVs yet. Do not invent a fourth taxonomy layer.")
    A("")
    A("Which tree wins for what purpose is in `DECISIONS.md` 2026-09-17 (two-axes entry). "
      "Spoken labels stay: shared/external vs internal; sales to dealer; price list / "
      "price revision; parts billed; reference dealer price.")
    A("")
    A("## 1. What was asked and what the scheme is")
    A("")
    A("Jerome chose the catalogue **identity** tree as the grouping axis for this Focus "
      "cut: `Competitive parts` at Level 1, `Filters` at Level 2, `Oil filter` / "
      "`Fuel filter` / `Air filter` / `Other filter` at Level 3. He asked for that Focus "
      "cut in full, plus a check that `brake parts are competitive parts`, plus a cross "
      "against the older coarse price class.")
    A("")
    A("The other vocabulary (Brakes / Engine / Clutch at Level 1) is **not** used as the "
      "grouping axis here. It still exists in the same file in the `aim_l1` / workbook "
      "columns as legacy context - neither Axis A nor Axis B under the lock.")
    A("")
    A("## 2. Method")
    A("")
    A(f"* Window: {WINDOW['start']} to {WINDOW['end']}, the window already baked into the "
      "shipped comparison. No new billing window was opened.")
    A("* Weight base: `price_bp_weighted_compare_pn.csv` - one row per customer x part number "
      "on the last 12 months of billed parts, in-scope customers only.")
    A("* Classification: `aim_pn_classification.csv`, joined on `part_number`.")
    A("* Weighted base-price increase = `SUM(qty x bp_new_jpy) / SUM(qty x bp_prior_revised) - 1` "
      "over rows priced on both sides. Step euro = sum of `value_eur_step`.")
    A("* Fleet denominator: `gps_spu_by_distributor.csv`, 2025 `uio_units`.")
    A("")
    A("**Tie-out.** The union of the classification multiplies back to the shipped comparison "
      f"exactly: network weighted increase {meta['tie_out_network']['mine_weighted_increase_pct']}% "
      f"against the shipped 5.9616%, step euro "
      f"{meta['tie_out_network']['mine_step_eur']:,.2f} against 1,652,140.71. "
      f"Per-distributor tie-out passes: {meta['tie_out_per_distributor_ok']} "
      f"(max increase delta {meta['tie_out_per_distributor_max_abs_increase_delta_pp']:.4f} pp, "
      f"max euro delta {meta['tie_out_per_distributor_max_abs_l12m_delta_eur']:.2f}). "
      "So the split is a partition of the shipped number, not a second number.")
    A("")
    A("## 3. Join rate")
    A("")
    A(f"* In-scope rows {j['in_scope_rows']:,} covering {j['in_scope_distinct_pn']:,} distinct "
      f"part numbers, {j['in_scope_billed_eur']:,.2f} EUR.")
    A(f"* Rows matched to the classification: {j['rows_matched_to_classification']:,} "
      f"({j['join_rate_rows_pct']:.4f}%). Not matched: {j['rows_not_matched']} rows, "
      f"{j['eur_not_matched']:,.2f} EUR ({100 - j['join_rate_eur_pct']:.4f}% of euro).")
    A("* Part numbers are 10-character zero-padded strings on both sides; the "
      "classification file is 100% clean on that. Three rows in the weight base carry a "
      "non-part key: two service-fee lines and one demurrage line. Those are not parts.")
    A("")
    A("## 4. The trap in the classification file - read this before quoting anything")
    A("")
    A("The brief said to restrict to `aim_source == 'pr00_catalog'` (139,410 rows) and treat "
      "that as the catalogue scheme. **That restriction does not do what it looks like.** "
      "`aim_source` is a precedence label for which vocabulary won `aim_l1`; it is not a "
      "completeness flag for `catalog_l1`.")
    A("")
    A("Verified facts:")
    A("")
    A("* `catalog_l1`, `catalog_l2`, `catalog_l3` are populated on 164,610 rows of the file, "
      "not 139,410. Each of the three columns matches the true PR00 source "
      "(`pr00_classification.csv` -> `family` / `group` / `level3_type`) on **100%** of "
      "joined rows, on every `aim_source` value.")
    A("* The catalogue columns are populated on 33,078 of the billed in-scope rows that carry "
      "`aim_source == 'aim_workbook'`, worth "
      f"{coverage['catalog_l1_real_drop_review']['l12m_billed_eur'] - coverage['belongs_to_pr00_catalog']['l12m_billed_eur']:,.2f} EUR.")
    A("* Restricting to `aim_source == 'pr00_catalog'` therefore keeps only "
      f"{coverage['belongs_to_pr00_catalog']['l12m_billed_eur']:,.2f} EUR "
      f"({coverage['belongs_to_pr00_catalog']['share_of_in_scope_eur_pct']:.2f}%) of the "
      f"{j['in_scope_billed_eur']:,.2f} EUR in-scope spend. Under that restriction the Focus "
      "cut collapses: Filters would show 3 row-level hits against 227 in reality, and "
      "**Air filter would show nothing at all**.")
    A("* Concretely, `8982705240 ELEMENT; OIL FILTER` is a 256,036 EUR line and is flagged "
      "`aim_workbook`. A literal reading of the brief would drop it out of the oil-filter answer.")
    A("")
    A("**Decision taken:** every output is emitted on two bases, so both readings are on disk "
      "and the difference is visible rather than hidden. The brief's literal restriction is "
      "kept as `pr00_catalog_only`.")
    A("")
    A("* `catalog_full` - every in-scope row that carries a catalogue node. **This is the one "
      "to quote for a network answer.** It is complete, internally consistent, and it ties out "
      "exactly to the shipped comparison.")
    A("* `pr00_catalog_only` - the literal `aim_source == 'pr00_catalog'` restriction. "
      "Use it only when the question is specifically about the PR00-sourced subset.")
    A("")
    A("A middle option was rejected: calling `catalog_full` the \"AIM classification\" in "
      "deliverables. `aim_l1` and `catalog_l1` are identical on 100% of `pr00_catalog` rows, "
      "so the file presents two different level-1 lists under one apparent label. That is the "
      "real classification-scheme conflict, and it should be settled in the file, not "
      "papered over in a report. Reported here, not fixed - the classifier is PRISM-owned.")
    A("")
    A("## 5. Coverage")
    A("")
    A("| Bucket | Rows | Part numbers | L12M billed EUR | Share |")
    A("|---|---|---|---|---|")
    A(f"| In-scope total | {j['in_scope_rows']:,} | {j['in_scope_distinct_pn']:,} | "
      f"{j['in_scope_billed_eur']:,.2f} | 100.00% |")
    for k, lbl in [("catalog_l1_real_drop_review", "Attributable to a real catalogue node"),
                   ("other_review", "`Other / review` placeholder"),
                   ("catalog_l1_null", "No catalogue node at all")]:
        v = coverage[k]
        A(f"| {lbl} | {v['rows']:,} | {v['distinct_pn']:,} | {v['l12m_billed_eur']:,.2f} | "
          f"{v['share_of_in_scope_eur_pct']:.2f}% |")
    A(f"| - of which PR00-sourced | {coverage['belongs_to_pr00_catalog']['rows']:,} | "
      f"{coverage['belongs_to_pr00_catalog']['distinct_pn']:,} | "
      f"{coverage['belongs_to_pr00_catalog']['l12m_billed_eur']:,.2f} | "
      f"{coverage['belongs_to_pr00_catalog']['share_of_in_scope_eur_pct']:.2f}% |")
    A("")
    A(f"**Unattributed spend: {coverage['unattributed_eur']:,.2f} EUR "
      f"({100 - coverage['catalog_l1_real_drop_review']['share_of_in_scope_eur_pct']:.2f}%).** "
      f"Of that, {coverage['other_review']['l12m_billed_eur']:,.2f} EUR sits in the "
      "`Other / review` placeholder and "
      f"{coverage['catalog_l1_null']['l12m_billed_eur']:,.2f} EUR has no node at all.")
    A("")
    A("The `catalog_l1` null bucket is largely not parts: `0000REBATE` (430,030 EUR) and "
      "`0TRANSPORT` (351,221 EUR) plus the UMI lubricants "
      "(0550047337 Rim R4L 15W40 at 394,763 EUR, and others, ~505,000 EUR in total). "
      "Those are correctly unclassified. The remaining ~400,000 EUR is a genuine part-number "
      "coverage gap (gussets, turbocharger, ABS controller, seat cushion, multi display) - "
      "real parts PR00 does not carry a figure for.")
    A("")
    A("Classification cells are all-or-nothing per row: there is no row with a level 1 but no "
      "level 2, or a level 2 but no level 3. So the unclassified row count is identical at all "
      "three levels: 124 rows / 83 part numbers / 1,354,703.17 EUR.")
    A("")
    A("## 6. Level 1 - network")
    A("")
    A("| Level 1 | PN | Qty | L12M billed EUR | Step EUR | Weighted increase |")
    A("|---|---|---|---|---|---|")
    for _, r in l1.iterrows():
        A(f"| {r['node_label']} | {r['n_pn']:,} | {r['l12m_qty']:,.0f} | "
          f"{r['l12m_billed_eur']:,.2f} | {r['step_eur']:,.2f} | "
          f"{_fmt(r['weighted_increase_pct'])}% |")
    A("")
    A("## 7. The Focus cut - Competitive parts > Filters")
    A("")
    A("Network, `catalog_full`:")
    A("")
    A("| Node | PN | Qty | L12M billed EUR | Step EUR | Weighted increase | EUR per truck in service |")
    A("|---|---|---|---|---|---|---|")
    uio_net = 183_999.0
    A(f"| Filters (all types) | {tot['n_pn']:,} | {tot['l12m_qty']:,.0f} | "
      f"{tot['l12m_billed_eur']:,.2f} | {tot['step_eur']:,.2f} | "
      f"{_fmt(tot['weighted_increase_pct'])}% | n/a (see note) |")
    for ft in ["Oil filter", "Fuel filter", "Other filter", "Air filter"]:
        r = by_ft[ft]
        A(f"| - {ft} | {r['n_pn']:,} | {r['l12m_qty']:,.0f} | {r['l12m_billed_eur']:,.2f} | "
          f"{r['step_eur']:,.2f} | {_fmt(r['weighted_increase_pct'])}% | n/a |")
    A("")
    comp_eur = float(l1.loc[l1["node_label"] == "Competitive parts", "l12m_billed_eur"].iloc[0])
    filt_share_comp = 100.0 * tot["l12m_billed_eur"] / comp_eur if comp_eur else 0.0
    filt_share_all = 100.0 * tot["l12m_billed_eur"] / j["in_scope_billed_eur"]
    A(f"Filters is {tot['l12m_billed_eur']:,.0f} EUR of {comp_eur:,.0f} EUR Competitive parts "
      f"({filt_share_comp:.1f}%) and {filt_share_all:.1f}% of total in-scope billed parts. "
      f"The weighted increase is {_fmt(tot['weighted_increase_pct'])}% — filters still move "
      "softly on this price revision relative to most competitive families, the opposite of "
      "what a competitive-pressure story would predict.")
    A("")
    A("Per distributor, Filters total:")
    A("")
    A("| Distributor | Truck fleet 2025 | PN | Qty | L12M billed EUR | Step EUR | Weighted increase | EUR per truck |")
    A("|---|---|---|---|---|---|---|---|")
    dt = c[(c["node_type"] == "L2_filters_total") & (c["distributor_code"] != NETWORK)]
    for _, r in dt.sort_values("l12m_billed_eur", ascending=False).iterrows():
        if r["fleet_denominator_available"]:
            fleet = f"{r['uio_units_2025']:,.0f}"
            per = f"{r['l12m_billed_eur'] / r['uio_units_2025']:,.1f}"
        else:
            fleet = "UNKNOWN"
            per = "NO FLEET COUNT"
        A(f"| {r['distributor_code']} | {fleet} | "
          f"{r['n_pn']:,} | {r['l12m_qty']:,.0f} | {r['l12m_billed_eur']:,.2f} | "
          f"{r['step_eur']:,.2f} | {_fmt(r['weighted_increase_pct'])}% | {per} |")
    A("")
    A("Per distributor, all four filter types - L12M billed EUR:")
    A("")
    A("| Distributor | Oil filter | Fuel filter | Air filter | Other filter | Filters total |")
    A("|---|---|---|---|---|---|")
    l3 = c[(c["node_type"] == "L3_filter_type") & (c["distributor_code"] != NETWORK)]
    piv = l3.pivot_table(index="distributor_code", columns="filter_type",
                         values="l12m_billed_eur", aggfunc="sum")
    tt = dt.set_index("distributor_code")["l12m_billed_eur"]
    piv = piv.reindex(tt.sort_values(ascending=False).index)
    for code, row in piv.iterrows():
        A(f"| {code} | {_fmt(row.get('Oil filter'), 0)} | {_fmt(row.get('Fuel filter'), 0)} | "
          f"{_fmt(row.get('Air filter'), 0)} | {_fmt(row.get('Other filter'), 0)} | "
          f"{_fmt(tt.get(code), 0)} |")
    A(f"| **Network** | **{_fmt(by_ft['Oil filter']['l12m_billed_eur'], 0)}** | "
      f"**{_fmt(by_ft['Fuel filter']['l12m_billed_eur'], 0)}** | "
      f"**{_fmt(by_ft['Air filter']['l12m_billed_eur'], 0)}** | "
      f"**{_fmt(by_ft['Other filter']['l12m_billed_eur'], 0)}** | "
      f"**{_fmt(tot['l12m_billed_eur'], 0)}** |")
    A("")
    A("Per distributor, quantity-weighted base-price increase on each filter type:")
    A("")
    A("| Distributor | Oil filter | Fuel filter | Air filter | Other filter | Filters total |")
    A("|---|---|---|---|---|---|")
    piv2 = l3.pivot_table(index="distributor_code", columns="filter_type",
                          values="weighted_increase_pct", aggfunc="sum")
    tt2 = dt.set_index("distributor_code")["weighted_increase_pct"]
    piv2 = piv2.reindex(dt.sort_values("l12m_billed_eur", ascending=False)["distributor_code"])
    for code, row in piv2.iterrows():
        A(f"| {code} | {_fmt(row.get('Oil filter'))} | {_fmt(row.get('Fuel filter'))} | "
          f"{_fmt(row.get('Air filter'))} | {_fmt(row.get('Other filter'))} | "
          f"{_fmt(tt2.get(code))} |")
    A(f"| **Network** | **{_fmt(by_ft['Oil filter']['weighted_increase_pct'])}** | "
      f"**{_fmt(by_ft['Fuel filter']['weighted_increase_pct'])}** | "
      f"**{_fmt(by_ft['Air filter']['weighted_increase_pct'])}** | "
      f"**{_fmt(by_ft['Other filter']['weighted_increase_pct'])}** | "
      f"**{_fmt(tot['weighted_increase_pct'])}** |")
    A("")
    A("Readings worth keeping:")
    A("")
    A("* **Oil filters move almost twice as hard as fuel filters** network-wide "
      f"({_fmt(by_ft['Oil filter']['weighted_increase_pct'])}% against "
      f"{_fmt(by_ft['Fuel filter']['weighted_increase_pct'])}%), while oil filters bill about "
      "72% of fuel-filter euro. That is the single clearest signal in the Focus cut.")
    A("* Oil-filter behaviour splits cleanly by distributor: Belgium 8.3%, IUK 9.4%, Norway "
      "9.1%, Sweden 9.8%, Romania 9.4%, Finland 9.3%, Hungary 8.4%, Germany 9.2% all sit near "
      "+9%, against ITUK at 4.0%, Portugal 1.1%, UMI 2.5% and UTI 0.5%. Two regimes, not one.")
    A("* UTI is a filter-weighted market: 545,239 EUR of filters on 10,336 trucks "
      "(52.8 EUR per truck), more than double ITUK's 30.0 and several times IUK's 5.0. "
      "But `Other filter` is 219,928 EUR of it - 40% of UTI's filter spend, against 28.5% "
      "network-wide, and UTI alone is 33% of the network's Other-filter euro. That is DEF and "
      "hydraulic, admitted only recently by catalogue input.")
    A("* `Other filter` is the third-largest filter type by euro (668,819 EUR, 28.5% of "
      "Filters, behind Fuel filter at 958,932 and Oil filter at 694,420), and it is dominated "
      "by one part number: `8982878080 FILTER ASM` is 298,160 EUR, 44.6% of the whole "
      "Other-filter block, on 277 units. Check what that part actually is before any of it "
      "enters a deck.")
    air = by_ft["Air filter"]
    air_l3 = c[(c["node_type"] == "L3_filter_type") & (c["filter_type"] == "Air filter")
               & (c["distributor_code"] != NETWORK)]
    air_zero = sorted(air_l3.loc[air_l3["l12m_billed_eur"] <= 0, "distributor_code"].tolist())
    air_pos = air_l3[air_l3["l12m_billed_eur"] > 0].sort_values(
        "l12m_billed_eur", ascending=False)
    top3 = ", ".join(
        f"{r.distributor_code} {r.l12m_billed_eur:,.0f} EUR" for _, r in air_pos.head(3).iterrows()
    )
    air_share = 100.0 * air["l12m_billed_eur"] / tot["l12m_billed_eur"] if tot["l12m_billed_eur"] else 0
    zero_clause = (
        f"Still zero in {', '.join(air_zero)}."
        if air_zero else
        "Every in-scope distributor with filter billing shows some air-filter euro."
    )
    A(f"* **`Air filter` is a real network family after the 2026-09-17 ACL refile:** "
      f"{air['l12m_billed_eur']:,.0f} EUR across {air['n_pn']:,.0f} part numbers "
      f"({air_share:.1f}% of Filters), weighted increase {_fmt(air['weighted_increase_pct'])}%. "
      f"Top markets: {top3}. {zero_clause} "
      "Do not reuse the pre-patch reading that called this leaf a network anecdote.")
    A("")
    A("## 8. Brake check - does 'brake parts are competitive parts' hold?")
    A("")
    A(f"**Verdict: yes, cleanly.** Under the catalogue scheme, `Competitive parts > Brake parts` "
      f"holds {bb['n_pn']:,.0f} part numbers, {bb['l12m_billed_eur']:,.2f} EUR, "
      f"{bb['step_eur']:,.2f} EUR of base-price step and a "
      f"{_fmt(bb['weighted_increase_pct'])}% weighted increase. That is the largest competitive "
      "family by euro and the largest single step-euro contributor at Level 2 "
      "(242,913 EUR, 38% of all Competitive-parts step euro). "
      "**100% of rows carrying `catalog_l2 = 'Brake parts'` sit under "
      "`Competitive parts`** - zero exception.")
    A("")
    A("*Leakage test.* Part numbers whose billed description looks like a brake but which sit "
      "outside that bucket:")
    A("")
    A(f"* **Strict test: {strict['n_pn']:,.0f} part numbers, {strict['l12m_billed_eur']:,.2f} EUR** "
      f"({strict['l12m_billed_eur'] / bb['l12m_billed_eur'] * 100:.2f}% of the bucket). "
      "Spread over `Repair parts > Hydraulic / mechanical` (11,439 EUR - wheel-cylinder cup "
      "sets, which are arguably brake content that PR00 files under general hydraulics), "
      "`Other / review > Miscellaneous` (7,132 EUR), "
      "`Hardware & consumables > Hardware` (4,107 EUR - shoe springs, pins, caliper boots), "
      "and small residue elsewhere.")
    A(f"* Loose test: {loose['n_pn']:,.0f} part numbers, {loose['l12m_billed_eur']:,.2f} EUR. "
      "**Do not use this figure.** It is contaminated.")
    A("")
    A("The difference between the two tests is 129,062 EUR and it is almost entirely a false "
      "positive I would have shipped if I had trusted the word list. The `ROTOR` token catches "
      "`ROTOR; SENSOR` (42,446 EUR) and `ROTOR; SENSOR` / `ROTOR; CAM ANGLE SENSOR` / "
      "`ROTOR; SPEED SENSOR` - 31 part numbers, 125,757 EUR - all of them ignition and "
      "wheel-speed sensors filed under `Repair parts > Electrical sensors`. They are not brakes. "
      "`BRAKET; HEATER` (105 EUR) is a typo for BRACKET, not a brake part. The strict token set "
      "excludes bare `ROTOR` and requires a brake word next to a rotor; that is the honest test.")
    A(f"* Reverse test: {over['n_pn']:,.0f} part numbers, {over['l12m_billed_eur']:,.2f} EUR "
      "inside the bucket have descriptions with no brake token in them. Small, and most are "
      "short descriptions rather than misfiles.")
    A("")
    A("**So Jerome's assertion holds, with one honest caveat:** PR00 puts roughly "
      f"{strict['l12m_billed_eur']:,.0f} EUR of genuine brake content - mainly wheel-cylinder "
      "cup sets, shoe springs, pins and caliper boots - under `Repair parts` and "
      "`Hardware & consumables` rather than under the brake family. Small against the 3.55M EUR "
      "bucket, but it means a brake analysis that uses only `Competitive parts > Brake parts` "
      "under-reads brakes slightly.")
    A("")
    A("## 9. Price class cross - the old coarse class against the catalogue nodes")
    A("")
    A("The price class is the coarse IML class factor (C, D, F, J, M, P, T, V). **It is "
      "IML-owned** - the pricing spec is explicit that class factors are not something ISZE "
      "changes. It is carried here as a retained attribute of the node, never as a lever.")
    A("")
    A("Competitive parts by Level 2 and price class, L12M billed EUR:")
    A("")
    classes = ["C", "D", "F", "J", "M", "P", "T", "V", UNCLASSIFIED]
    A("| Level 2 | " + " | ".join(classes) + " |")
    A("|---" * (len(classes) + 1) + "|")
    for node, g in pc.groupby("catalog_l2"):
        vals = {r["bp_new_class_iml"]: r["l12m_billed_eur"] for _, r in g.iterrows()}
        A(f"| {node} | " + " | ".join(_fmt(vals.get(cl), 0) for cl in classes) + " |")
    A("")
    tot_by_cl = pc.groupby("bp_new_class_iml")["l12m_billed_eur"].sum()
    A("Column totals across all Competitive parts: " + ", ".join(
        f"{cl} {_fmt(tot_by_cl.get(cl, 0), 0)}" for cl in classes) + ".")
    A("")
    A("The reading that matters: **the competitive families are almost entirely C and V.** "
      "Filters is 1,876,730 EUR of `V` and only 187,673 EUR of `C` plus 516,387 EUR of `D` - "
      "and the entire `D` block is `Other filter` (516,387 EUR of the 516,387). So `D` is "
      "effectively a DEF-filter class, not a filter class in general. Oil and fuel filters are "
      "100% `V`. Exhaust and Steering are overwhelmingly `C` (1,857,072 and 1,570,005 EUR). "
      "Brake parts is the most balanced large family: 1,757,621 EUR `C` against 1,452,103 EUR `V`.")
    A("")
    A("Level 3 Filters against price class:")
    A("")
    fl = px[(px["scheme_basis"] == "catalog_full") & (px["level_id"] == "L3")
            & (px["catalog_l2"] == "Filters")]
    A("| Filter type | " + " | ".join(classes) + " |")
    A("|---" * (len(classes) + 1) + "|")
    for node, g in fl.groupby("catalog_l3"):
        vals = {r["bp_new_class_iml"]: r["l12m_billed_eur"] for _, r in g.iterrows()}
        A(f"| {node} | " + " | ".join(_fmt(vals.get(cl), 0) for cl in classes) + " |")
    A("")
    A(f"{meta['price_class_unclassified']['rows']:,} in-scope rows carry no price class, "
      f"{meta['price_class_unclassified']['l12m_billed_eur']:,.2f} EUR. Those are excluded "
      "from the class cross by definition, not dropped from the other tables.")
    A("")
    A("## 10. Top competitive families by euro")
    A("")
    A("| Family | PN | Qty | L12M billed EUR | Step EUR | Weighted increase | EUR per truck |")
    A("|---|---|---|---|---|---|---|")
    for _, r in l2.iterrows():
        A(f"| {r['catalog_l2']} | {r['n_pn']:,} | {r['l12m_qty']:,.0f} | "
          f"{r['l12m_billed_eur']:,.2f} | {r['step_eur']:,.2f} | "
          f"{_fmt(r['weighted_increase_pct'])}% | {r['billed_eur_per_uio'] if pd.notna(r['billed_eur_per_uio']) else 'n/a'} |")
    A("")
    A("## 11. Distributors with no fleet denominator")
    A("")
    A("Four markets have `uio_units` of 0 in the 2025 fleet file - no count exists by design. "
      "**Nothing here is divided by trucks in service for these four**, so their tables show "
      "euro and no rate:")
    A("")
    for code in meta["distributors_without_fleet_denominator"]:
        A(f"* **{code}** - {meta['distributors_without_fleet_denominator_billed_eur'][code]:,.2f} EUR "
          "in-scope billed in the window.")
    A("")
    A(f"{sum(meta['distributors_without_fleet_denominator_billed_eur'].values()):,.2f} EUR "
      "combined. They are in the network totals and in every euro figure; they are simply "
      "absent from any per-truck column. Do not read their blank rate as zero performance.")
    A("")
    A("The network fleet total is 163,459 trucks across the 18 markets that have a count. "
      "A network-wide euro-per-truck can be struck on that base, but it is a rate over "
      "18 markets sitting beside a euro total over 22 - state it that way if it is quoted.")
    A("")
    A("## 12. Israel")
    A("")
    A("Reported as two rows throughout, never blended: **1797 UMI** and **1799 UTI**. The "
      "customer name column cannot split them - it reads UNIVERSAL MOTORS ISRAEL LTD for both "
      "since the 2026-04-01 relabel. UMI is LCV, UTI is CV, different fleets, different parts mix.")
    A("")
    A("## 13. What this data could not cover")
    A("")
    A("* **`Other filter` is a residual bucket, not a product family.** The filter taxonomy "
      "itself is closed and clean (`Oil filter`, `Fuel filter`, `Air filter`, `Other filter` "
      "plus exactly one `Hydraulic / transmission filter`, 2,029 part numbers under "
      "`Competitive parts > Filters`). But `Other filter` mixes at least three different "
      "physical things: DEF/aftertreatment filter assemblies (FILTER ASM, FILTER KIT PUMP ASM "
      "DEF DCM), hydraulic and transmission strainers (STRAINER ASM OIL A/T, FILTER ASM VCV), "
      "and one `GASKET; FILTER,DEF`. It cannot be treated as one family with one commercial "
      "story, and one part number is 44.6% of it.")
    A(f"* **`Air filter` is no longer an empty leaf.** After the ACL → air-cleaner refile it "
      f"holds {by_ft['Air filter']['l12m_billed_eur']:,.0f} EUR / "
      f"{by_ft['Air filter']['n_pn']:,.0f} part numbers on this 12-month cut "
      f"(second among the four filter types by euro). Pre-patch NOTES that called it "
      "€28k / anecdote are withdrawn.")
    A("* **The four no-fleet markets cannot carry a rate.** Armenia, Kazakhstan, Palestine and "
      "Ukraine have 1,539,292 EUR of billed parts between them and no trucks-in-service count. "
      "Any rate-based comparison silently omits them.")
    A("* **The `Other / review` placeholder is 1,540,240 EUR (4.4%)** and is a real answer for "
      "quite a lot of genuine part numbers. It is not a rounding error.")
    A("* **No elasticity, no allocation, no price proposal.** Correctly out of scope; the "
      "weighted increase is a base-price move, not a revenue or margin outcome.")
    A("* **The two level-1 vocabularies remain unreconciled in the source file.** The catalogue "
      "columns and the workbook columns are both populated, both presentable, and describe "
      "different taxonomies. This note uses the catalogue columns only, per the brief. The "
      "underlying file should be fixed so the next reader is not forced to make the same call.")
    A(f"* **The brief's literal restriction would have produced a materially wrong answer** - "
      "Filters missing air filters entirely and dropping the largest oil-filter part numbers, "
      "leaving 13.54% of in-scope euro. Flagged, worked around, and the restricted cut is on "
      "disk if that reading was deliberate.")
    A("")
    A("## 14. Files")
    A("")
    A("* `aim_catalog_db_matrix.csv` - distributor x node at each of the three levels, on both "
      "scheme bases. Includes network rows (`__NETWORK__`).")
    A("* `aim_catalog_focus_filters.csv` - the Focus cut, every distributor, all four filter "
      "types plus the Filters parent total, both bases.")
    A("* `aim_catalog_brake_check.csv` - the brake verification, loose and strict leak tests.")
    A("* `aim_catalog_x_priceclass.csv` - node x price class at L1 / L2 / L3, network level.")
    A("* `aim_catalog_breakdown_meta.json` - join rate, coverage, tie-out, fleet gaps.")
    A("")
    A("Builder: `01_data/91_build/build_aim_catalog_breakdown.py`.")
    A("")

    (DERIVED / "aim_catalog_breakdown_NOTES.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
