#!/usr/bin/env python3
"""King-pin PMS rule: BEFORE / AFTER, read-only (Jerome 2 Oct 2026: show first, do not apply).

Rule today (03_analytics/Isuzu/prism/data/fig_key_taxonomy.yaml, pr00_pms_category_rules):
    match_group "Suspension", level3_contains {king: king_pin, ...}
AFTER (simulated only, the yaml is NOT edited): one added rule
    match_group "Steering", level3_contains {"knuckle / arm": king_pin}
i.e. the king-pin category pointed at Steering > Knuckle / arm, where the approved release
(2026-10-02-chassis-frame) and the settled pr00 file king-pin parts.

Both runs use the real dimension builder (modules.fig_key_catalog.build_parts_catalog_dimension)
on today's pr00_classification.csv + bvp_pn_dimension.csv, so BVP / registry / override
precedence is the pipeline's own. The BEFORE run is checked against the dimension on disk.

Then, per part that changes: parts billed (sales_fact net_sales_value, L12M 2025-09..2026-08,
and calendar 2025), units, per market (sold_to_sap -> distributor_dimension.distributor_code),
and what each consumer of pms_category does with king_pin:
  - AIM pages (build_aim_db_dlr / build_aim_comparison): fam_of() keeps 14 PMS families only
  - PMS capture (pms_capture_by_db_year.csv): categories present in the file
  - lost_sales_build.load_part_taxonomy(): registry first, catalogue fills; family_7 from
    pms_category when filled (king_pin -> "Other"), else from AIM level 1.
Writes kingpin_rule_before_after_20261002.json beside itself. Nothing else.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
PRISM = ISZE / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
sys.path.insert(0, str(ISZE / "04_tools" / "aim_db_dlr_deep_dive"))

import yaml  # noqa: E402
from modules import fig_key_catalog as fkc  # noqa: E402

OUT = Path(__file__).with_suffix(".json")
TAX = PRISM / "data" / "fig_key_taxonomy.yaml"


def norm(k) -> str:
    s = str(k).strip()
    return s.lstrip("0") if s.isdigit() else s


def main() -> int:
    tax_before = fkc.load_taxonomy(TAX)
    tax_after = copy.deepcopy(tax_before)
    tax_after["pr00_pms_category_rules"].append(
        {"match_group": "Steering", "level3_contains": {"knuckle / arm": "king_pin"}})
    scratch = OUT.parent / "_kingpin_tax_after_tmp.yaml"
    scratch.write_text(yaml.safe_dump(tax_after, sort_keys=False), encoding="utf-8")
    try:
        kw = dict(pr00_csv=DER / "pr00_classification.csv",
                  bvp_dimension_csv=DER / "bvp_pn_dimension.csv")
        before = fkc.build_parts_catalog_dimension(taxonomy_path=TAX, **kw)
        after = fkc.build_parts_catalog_dimension(taxonomy_path=scratch, **kw)
    finally:
        scratch.unlink(missing_ok=True)

    disk = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str, keep_default_na=False)
    b = before.copy()
    b["_k"] = b.part_number.map(norm)
    a = after.copy()
    a["_k"] = a.part_number.map(norm)
    disk["_k"] = disk.part_number.map(norm)
    bm = b.set_index("_k").pms_category.fillna("")
    am = a.set_index("_k").pms_category.fillna("")
    dm = disk.drop_duplicates("_k").set_index("_k").pms_category
    common = bm.index.intersection(dm.index)
    rebuild_vs_disk = int((bm.reindex(common) != dm.reindex(common)).sum())

    chg = am[am != bm]
    moved = pd.DataFrame({"before": bm.reindex(chg.index), "after": chg})
    pr = pd.read_csv(DER / "pr00_classification.csv", dtype=str, keep_default_na=False,
                     usecols=["pn_norm", "description", "group", "level3_type", "fig_key"]
                     if "description" in pd.read_csv(DER / "pr00_classification.csv", nrows=0).columns
                     else ["pn_norm", "group", "level3_type", "fig_key"])
    pr["_k"] = pr.pn_norm.map(norm)
    pr = pr.drop_duplicates("_k").set_index("_k")
    moved = moved.join(pr, how="left")
    rel = pd.read_csv(DER / "_releases" / "aim_pn_classification_release_2026-10-02-chassis-frame.csv",
                      dtype=str, keep_default_na=False,
                      usecols=["part_number", "description_norm", "aim_l1_fixed", "aim_l2_fixed",
                               "aim_l3_fixed"])
    rel["_k"] = rel.part_number.map(norm)
    rel = rel.drop_duplicates("_k").set_index("_k")
    moved = moved.join(rel[["description_norm", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]],
                       how="left")
    desc = moved["description_norm"].fillna("")
    moved["is_king_pin_text"] = desc.str.contains("KING PIN|KINGPIN|KING-PIN", regex=True)

    # ---- billing
    sf = pd.read_parquet(DER / "sales_fact.parquet",
                         columns=["billing_date", "sold_to_sap", "part_number", "billed_qty",
                                  "net_sales_value"])
    sf["_k"] = sf.part_number.map(norm)
    dd = pd.read_csv(DER / "distributor_dimension.csv", dtype=str)
    mk = dict(zip(pd.to_numeric(dd.sold_to_sap, errors="coerce"), dd.distributor_code))
    sf["market"] = sf.sold_to_sap.map(mk).fillna("other sold-to")
    l12 = sf[(sf.billing_date >= "2025-09-01") & (sf.billing_date <= "2026-08-31")]
    cy25 = sf[(sf.billing_date >= "2025-01-01") & (sf.billing_date <= "2025-12-31")]
    tot_l12 = float(l12.net_sales_value.sum())

    def billed(df, keys):
        x = df[df._k.isin(keys)]
        return x

    keys = set(moved.index)
    kp = billed(l12, keys)
    by_market = (kp.groupby("market").agg(eur=("net_sales_value", "sum"), units=("billed_qty", "sum"),
                                          parts=("_k", "nunique"))
                 .sort_values("eur", ascending=False).round(2))
    mk_tot = l12.groupby("market").net_sales_value.sum()
    by_market["share_of_market_parts_billed_pct"] = (100 * by_market.eur / mk_tot.reindex(by_market.index)).round(3)
    kp25 = billed(cy25, keys)

    # ---- consumers
    import build_aim_db_dlr as aimb  # noqa: E402
    aim_fam_before_after = {"fam_of(king_pin)": aimb.fam_of("king_pin"),
                            "PMS_FAMS": aimb.PMS_FAMS}
    cap = pd.read_csv(DER / "pms_capture_by_db_year.csv", dtype=str)
    cap_cats = sorted(cap.pms_category.unique())

    bvp = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str)
    bvp["_k"] = bvp.part_number.map(norm)
    reg_cat = bvp.dropna(subset=["pms_category"]).drop_duplicates("_k").set_index("_k").pms_category
    master = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, usecols=["part_number", "aim_l1_fixed"])
    master["_k"] = master.part_number.map(norm)
    ml1 = master.drop_duplicates("_k").set_index("_k").aim_l1_fixed
    sys.path.insert(0, str(PRISM / "modules"))
    from modules.lost_sales_build import AIM_L1_TO_FAMILY_7, _family_for_pms_category  # noqa: E402
    fam_rows = []
    for k in moved.index:
        reg = reg_cat.get(k)
        l1 = ml1.get(k)
        fam_b = (_family_for_pms_category(str(reg)) if isinstance(reg, str) else
                 (AIM_L1_TO_FAMILY_7.get(l1) if isinstance(l1, str) else None) or "unclassified_pn")
        cat_a = reg if isinstance(reg, str) else moved.at[k, "after"]
        fam_a = _family_for_pms_category(str(cat_a)) if cat_a else fam_b
        fam_rows.append({"_k": k, "registry_cat": reg, "master_aim_l1": l1,
                         "family7_before": fam_b, "family7_after": fam_a})
    fam = pd.DataFrame(fam_rows).set_index("_k")
    eur_k = kp.groupby("_k").net_sales_value.sum()
    fam["l12m_eur"] = eur_k.reindex(fam.index).fillna(0.0)
    fam_moves = (fam.groupby(["family7_before", "family7_after"]).agg(parts=("l12m_eur", "size"),
                                                                     eur=("l12m_eur", "sum"))
                 .round(2).reset_index().to_dict("records"))

    # coverage of pms_category in the lost-sales view: share of L12M billed euro with a category
    cat_cov_b = set(bm[bm != ""].index) | set(reg_cat.index)
    cat_cov_a = set(am[am != ""].index) | set(reg_cat.index)
    cov_b = float(l12[l12._k.isin(cat_cov_b)].net_sales_value.sum())
    cov_a = float(l12[l12._k.isin(cat_cov_a)].net_sales_value.sum())

    kp_eur = kp.groupby("_k").net_sales_value.sum()
    txt = moved["is_king_pin_text"]
    split_text = {"king_pin_in_description": {"parts": int(txt.sum()), "parts_billed": int(kp_eur.index.isin(moved.index[txt]).sum()),
                                              "l12m_eur": round(float(kp_eur[kp_eur.index.isin(moved.index[txt])].sum()), 2)},
                  "other_description_or_blank": {"parts": int((~txt).sum()), "parts_billed": int(kp_eur.index.isin(moved.index[~txt]).sum()),
                                                 "l12m_eur": round(float(kp_eur[kp_eur.index.isin(moved.index[~txt])].sum()), 2)}}
    # fig keys: how clean is each key that carries king-pin parts (a match_fig_key alternative)
    fk = moved.groupby("fig_key").agg(parts=("is_king_pin_text", "size"), king_pin_text=("is_king_pin_text", "sum"))
    fk["l12m_eur"] = kp_eur.groupby(moved["fig_key"].reindex(kp_eur.index)).sum().reindex(fk.index).fillna(0).round(2)
    fk = fk[fk.king_pin_text > 0].sort_values("l12m_eur", ascending=False)
    res = {
        "eur_split_by_description": split_text,
        "fig_keys_with_king_pin_parts": fk.reset_index().to_dict("records"),
        "rule_after_simulated": {"match_group": "Steering",
                                 "level3_contains": {"knuckle / arm": "king_pin"}},
        "dimension_rebuild_vs_disk_pms_category_mismatches": rebuild_vs_disk,
        "parts_tagged_king_pin": {"before": int((bm == "king_pin").sum()),
                                  "after": int((am == "king_pin").sum())},
        "parts_changing_pms_category": int(len(moved)),
        "moves": moved.groupby(["before", "after"]).size().reset_index(name="parts").to_dict("records"),
        "changing_by_pr00_node": moved.groupby(["group", "level3_type"]).size().reset_index(name="parts").to_dict("records"),
        "changing_with_king_pin_in_text": int(moved.is_king_pin_text.sum()),
        "changing_without_king_pin_text_examples": moved.loc[~moved.is_king_pin_text, "description_norm"].fillna("").value_counts().head(15).to_dict(),
        "changing_aim_l1_in_release": moved.aim_l1_fixed.fillna("(not in release)").value_counts().to_dict(),
        "l12m_window": "2025-09-01..2026-08-31",
        "l12m_total_parts_billed_eur_all": round(tot_l12, 2),
        "l12m_changing_parts_billed": {"eur": round(float(kp.net_sales_value.sum()), 2),
                                       "units": round(float(kp.billed_qty.sum()), 0),
                                       "parts_billed": int(kp._k.nunique()),
                                       "billed_parts_with_king_pin_text": int(moved.loc[moved.index.isin(kp._k.unique()), "is_king_pin_text"].sum())},
        "cy2025_changing_parts_billed": {"eur": round(float(kp25.net_sales_value.sum()), 2),
                                         "units": round(float(kp25.billed_qty.sum()), 0),
                                         "parts_billed": int(kp25._k.nunique())},
        "l12m_by_market": by_market.reset_index().to_dict("records"),
        "consumers": {
            "aim_pages": aim_fam_before_after,
            "pms_capture_by_db_year_categories": cap_cats,
            "king_pin_in_pms_capture": "king_pin" in cap_cats,
            "lost_sales_family7_moves_l12m": fam_moves,
            "lost_sales_pms_category_coverage_l12m_eur": {
                "before": round(cov_b, 2), "after": round(cov_a, 2),
                "before_pct": round(100 * cov_b / tot_l12, 3), "after_pct": round(100 * cov_a / tot_l12, 3),
                "note": "share of L12M parts billed whose part carries a pms_category (registry or catalogue dimension)"},
        },
        "top_changing_parts_l12m": (kp.groupby("_k").agg(eur=("net_sales_value", "sum"), units=("billed_qty", "sum"))
                                    .sort_values("eur", ascending=False).head(12)
                                    .join(moved[["description_norm"]]).round(2).reset_index().to_dict("records")),
    }
    OUT.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
