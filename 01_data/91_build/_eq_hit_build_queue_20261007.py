"""Build EQ-Hit priority queues 2026-10-07. Matches residual-methods peel. Evidence only."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
BUILD = ISZE / "01_data" / "91_build"
LIVE = DER / "_releases" / "next_release_proposal_live_order_unclassified_2026-10-07.csv"
OUTQ = DER / "_eq_hit_queue_20261007.json"
RES_PY = BUILD / "_aim_full_class_residual_methods_20261007.py"


def load_residual_module():
    spec = importlib.util.spec_from_file_location("aim_residual", RES_PY)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def build_residual_frame(mod):
    """Replicate residual script frame + method peel without writing inventory."""
    aim = pd.read_csv(mod.MASTER, dtype=str, low_memory=False)
    aim["pn"] = mod.norm_pn(aim["part_number"])
    for c in ("cat_l1", "cat_l2", "cat_l3", "fig_key", "aim_l1", "aim_l1_fixed", "description"):
        if c not in aim.columns:
            aim[c] = ""
    a1 = aim["aim_l1"].map(mod.clean)
    a1f = aim["aim_l1_fixed"].map(mod.clean)
    fam = a1f.where(~a1f.isin(mod.MARKERS) & (a1f != ""), other="")
    fam = fam.where(fam != "", other=a1.where(~a1.isin(mod.MARKERS) & (a1 != ""), other=""))
    aim["family"] = fam
    aim["desc_norm"] = mod.norm_desc(aim["description"])
    aim["l12m_eur"] = pd.to_numeric(aim.get("l12m_billed_eur", 0), errors="coerce").fillna(0.0)
    if "eur" in aim.columns:
        aim["eur_any"] = pd.to_numeric(aim["eur"], errors="coerce").fillna(0.0)
    else:
        aim["eur_any"] = 0.0
    aim["cat_path"] = (
        aim["cat_l1"].map(mod.clean) + " > " + aim["cat_l2"].map(mod.clean) + " > " + aim["cat_l3"].map(mod.clean)
    )
    aim["has_cat"] = aim["cat_l1"].map(mod.clean) != ""

    marked_mask = a1.isin(mod.UNKNOWN_MARKERS) | a1f.isin(mod.UNKNOWN_MARKERS)
    true_blank = aim[(aim["family"] == "") & (~marked_mask)].copy()

    t1 = pd.read_csv(mod.TRANCHE1, dtype=str, low_memory=False)
    t1_pns = set(mod.norm_pn(t1["part_number"]))
    residual = true_blank[~true_blank["pn"].isin(t1_pns)].copy()
    residual["never_billed"] = (residual["l12m_eur"] <= 0) & (residual["eur_any"] <= 0)

    known = aim[aim["family"] != ""].copy()
    known_desc = known[known["desc_norm"] != ""]
    gd = known_desc.groupby("desc_norm")["family"]
    desc_tab = pd.DataFrame(
        {
            "n_parts": gd.size(),
            "n_l1": gd.nunique(),
            "top_l1": gd.agg(lambda s: s.value_counts().index[0]),
            "top_share": gd.agg(lambda s: float(s.value_counts().iloc[0] / len(s))),
        }
    )
    unan = desc_tab[(desc_tab["n_l1"] == 1) & (desc_tab["n_parts"] >= mod.DESC_MIN_N)]
    weak_desc = desc_tab[
        (desc_tab["n_l1"] == 1)
        & (desc_tab["n_parts"] >= mod.DESC_WEAK_N)
        & (desc_tab["n_parts"] < mod.DESC_MIN_N)
    ]

    gk = known.groupby("cat_path")["family"]
    cat_tab = pd.DataFrame(
        {
            "known_n": gk.size(),
            "n_l1": gk.nunique(),
            "top_l1": gk.agg(lambda s: s.value_counts().index[0]),
            "top_share": gk.agg(lambda s: float(s.value_counts().iloc[0] / len(s))),
        }
    )

    residual["non_part_reason"] = [
        mod.non_part_reason(p, d) for p, d in zip(residual["pn"], residual["description"].fillna(""))
    ]
    residual["is_non_part"] = residual["non_part_reason"] != ""
    residual["propose_desc_l1"] = residual["desc_norm"].map(unan["top_l1"])
    residual["desc_unan"] = residual["propose_desc_l1"].notna()
    residual["propose_desc_weak_l1"] = residual["desc_norm"].map(weak_desc["top_l1"])
    residual["desc_weak"] = residual["propose_desc_weak_l1"].notna() & (~residual["desc_unan"])
    residual["desc_seen_any"] = residual["desc_norm"].isin(desc_tab.index) & (residual["desc_norm"] != "")
    residual["has_desc"] = residual["desc_norm"] != ""

    residual = residual.merge(cat_tab.add_prefix("cat_"), left_on="cat_path", right_index=True, how="left")
    residual["cat_known_n"] = residual["cat_known_n"].fillna(0).astype(int)
    residual["cat_top_share"] = residual["cat_top_share"].fillna(0.0)
    residual["cat_near_miss"] = (
        residual["has_cat"]
        & (residual["cat_known_n"] >= mod.CAT_NEAR_N)
        & (residual["cat_top_share"] >= mod.CAT_NEAR_SHARE)
        & (residual["cat_top_share"] < 0.90)
    )
    residual["cat_contested"] = (
        residual["has_cat"]
        & (residual["cat_known_n"] >= mod.CAT_NEAR_N)
        & (residual["cat_top_share"] < mod.CAT_NEAR_SHARE)
        & (residual["cat_top_share"] >= mod.CAT_WEAK_SHARE)
    )
    residual["cat_too_weak"] = residual["has_cat"] & (
        (residual["cat_known_n"] < mod.CAT_NEAR_N) | (residual["cat_top_share"] < mod.CAT_WEAK_SHARE)
    )
    residual["cat_review_bucket"] = residual["cat_path"].str.contains(
        r"Review needed|Miscellaneous|Other / review", case=False, na=False
    )

    method = pd.Series("", index=residual.index)
    method[residual["is_non_part"]] = "d_non_part_junk"
    method[(method == "") & residual["desc_unan"]] = "a_desc_norm_unanimity"
    method[(method == "") & residual["desc_weak"]] = "a_desc_norm_weak_n_lt3"
    method[(method == "") & residual["has_desc"] & (~residual["desc_seen_any"])] = (
        "a_desc_present_unseen_on_known"
    )
    method[(method == "") & residual["cat_near_miss"]] = "e_cat_path_near_miss_relax_bar"
    method[(method == "") & residual["cat_contested"] & (~residual["cat_review_bucket"])] = (
        "b_cat_contested_needs_eq_or_hand"
    )
    method[(method == "") & residual["cat_review_bucket"]] = "b_cat_review_bucket_needs_eq_or_hand"
    method[(method == "") & residual["cat_too_weak"] & (~residual["has_desc"])] = (
        "b_needs_eq_epc_empty_desc_weak_cat"
    )
    method[(method == "") & (~residual["has_cat"])] = "b_needs_eq_epc_no_catalogue"
    method[method == ""] = "b_needs_eq_epc_other"
    residual["method"] = method
    return residual


def main() -> None:
    mod = load_residual_module()
    residual = build_residual_frame(mod)

    unseen = residual[residual["method"] == "a_desc_present_unseen_on_known"].copy()
    billed = unseen[unseen["l12m_eur"] > 0].sort_values("l12m_eur", ascending=False)
    print(
        "unseen_method",
        len(unseen),
        "billed",
        len(billed),
        "eur",
        round(float(billed["l12m_eur"].sum()), 2),
    )

    q2 = [
        {
            "pn": r["pn"],
            "description": str(r["description"] or ""),
            "source_queue": "billed_residual",
            "l12m_billed_eur": float(r["l12m_eur"]),
            "cat_path": r["cat_path"],
        }
        for _, r in billed.iterrows()
    ]

    contested = residual[residual["method"] == "b_cat_contested_needs_eq_or_hand"].copy()
    contested = contested.sort_values("pn").head(50)
    q3 = [
        {
            "pn": r["pn"],
            "description": str(r["description"] or ""),
            "source_queue": "sample",
            "cat_path": r["cat_path"],
            "cat_top_share": float(r["cat_top_share"]),
            "cat_top_l1": str(r.get("cat_top_l1") or ""),
        }
        for _, r in contested.iterrows()
    ]

    q1 = []
    with LIVE.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if (r.get("suggested_next_method") or "") == "needs_EQ":
                q1.append(
                    {
                        "pn": str(r["pn"]).strip(),
                        "description": (r.get("description") or "").strip(),
                        "source_queue": "live_order",
                        "lines": r.get("lines"),
                    }
                )

    seen: set[str] = set()
    queue = []
    for block in (q1, q2, q3):
        for r in block:
            if r["pn"] in seen:
                continue
            seen.add(r["pn"])
            queue.append(r)

    payload = {
        "as_of": "2026-10-07",
        "n_live_order": len(q1),
        "n_billed_residual": len(q2),
        "n_sample": len(q3),
        "n_unique": len(queue),
        "queue": queue,
        "by_queue": {"live_order": q1, "billed_residual": q2, "sample": q3},
    }
    OUTQ.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", OUTQ, "unique", len(queue), "q1", len(q1), "q2", len(q2), "q3", len(q3))


if __name__ == "__main__":
    main()
