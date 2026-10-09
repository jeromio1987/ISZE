"""Shard C — residual-method inventory after tranche1 cat_map (proposal only).

Does NOT apply families. Does NOT touch tranche1 proposal content.
Does NOT open EQ. Uses master + tranche1 proposal CSV + any EQ evidence already on disk.

Finding that drives the split: ~98.8% of residual true blanks have an EMPTY
description. Desc-norm therefore barely moves the needle. Most residual rows
already carry cat_l1 but failed the tranche1 90%/n>=5 path bar (contested or
thin known). EQ is required only where catalogue evidence is also too weak.

Output:
  01_data/91_build/_aim_full_class_residual_methods_20261007.json
  01_data/91_build/_aim_full_class_residual_methods_samples_20261007.csv
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
BUILD = ISZE / "01_data" / "91_build"
MASTER = DER / "aim_master_v2.csv"
TRANCHE1 = DER / "_releases" / "next_release_proposal_full_class_tranche1_catmap_2026-10-07.csv"
OUT_JSON = BUILD / "_aim_full_class_residual_methods_20261007.json"
OUT_SAMPLE = BUILD / "_aim_full_class_residual_methods_samples_20261007.csv"

MARKERS = {"", "Unknown", "Unknown Review", "nan", "None"}
UNKNOWN_MARKERS = {"Unknown", "Unknown Review"}

NON_PART_RULE = {
    "TRANSPORT": "freight",
    "REBATE": "rebate",
    "LATEPAYMENTINTEREST": "finance",
    "5874123810": "tool",
    "5874123811": "tool",
    "5874123812": "tool",
    "SERVICE": "service_fee",
    "SERVICEFEEOUTSIDEEUROPE": "service_fee",
    "SERVICEFEEWITHINEEUROPE": "service_fee",
    "COSTDEMURRAGE": "demurrage",
    "COMPENSATIONSSALEE-CREDIT": "e_credit",
    "20MTGKIT": "marketing_item",
    "60MTGKIT": "marketing_item",
    "BOXES_ASC": "merchandise",
    "TOWEL_ASC": "merchandise",
    "BACKPACK": "merchandise",
    "NOTEBOOK": "merchandise",
    "PEN": "merchandise",
    "DISRACK01": "display",
    "CORE_7.5": "core_deposit",
    "CORE_9": "core_deposit",
    "CORE_9.5": "core_deposit",
}
NON_PART_KEYS = {
    "EA2200143",
    "EA530156",
    "EA530160",
    "EA530162",
    "EA530165",
    "EA530170",
    "F4640",
    "F4740",
    "INST00001",
}
NON_PART_NORM = {k.strip().upper().replace(" ", ""): v for k, v in NON_PART_RULE.items()}

DESC_MIN_N = 3  # final_tier unanimity rail
DESC_WEAK_N = 1  # single-family but thin evidence
# Cat-path near-miss: close to tranche1 but under the bar (Shard A follow-on, not EQ)
CAT_NEAR_SHARE = 0.80
CAT_NEAR_N = 5
# Cat-path too weak for a defendable map without EQ / hand
CAT_WEAK_SHARE = 0.50


def clean(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def norm_desc(s: pd.Series) -> pd.Series:
    return (
        s.fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )


def norm_pn(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def non_part_reason(pn: str, desc: str) -> str:
    k = (pn or "").strip().upper().replace(" ", "")
    if not k:
        return "empty_key"
    if k in NON_PART_NORM:
        return f"named_rule:{NON_PART_NORM[k]}"
    if k in {x.upper() for x in NON_PART_KEYS}:
        return "named_non_part_key"
    stripped = k.lstrip("0")
    if stripped and stripped in NON_PART_NORM:
        return f"zero_pad_placeholder:{NON_PART_NORM[stripped]}"
    if k and not k[0].isdigit():
        return "alpha_key_no_leading_digit"
    d = (desc or "").upper()
    if re.search(r"\b(REBATE|FREIGHT|TRANSPORT|DEMURRAGE|SERVICE\s*FEE|LATE\s*PAYMENT)\b", d):
        return "desc_non_part_token"
    return ""


def eur_sum(s: pd.Series) -> float:
    return float(pd.to_numeric(s, errors="coerce").fillna(0).sum())


def pack(sub: pd.DataFrame, residual_n: int) -> dict:
    return {
        "rows": int(len(sub)),
        "distinct_pn": int(sub["pn"].nunique()),
        "l12m_billed_eur": round(eur_sum(sub["l12m_eur"]), 2),
        "rows_with_l12m_bill": int((sub["l12m_eur"] > 0).sum()),
        "share_of_residual_rows": round(len(sub) / max(residual_n, 1), 4),
        "with_cat_l1": int(sub["has_cat"].sum()),
        "empty_desc": int((sub["desc_norm"] == "").sum()),
        "never_billed": int(sub["never_billed"].sum()),
    }


def main() -> None:
    aim = pd.read_csv(MASTER, dtype=str, low_memory=False)
    aim["pn"] = norm_pn(aim["part_number"])
    for c in ("cat_l1", "cat_l2", "cat_l3", "fig_key", "aim_l1", "aim_l1_fixed", "description"):
        if c not in aim.columns:
            aim[c] = ""
    a1 = aim["aim_l1"].map(clean)
    a1f = aim["aim_l1_fixed"].map(clean)
    fam = a1f.where(~a1f.isin(MARKERS) & (a1f != ""), other="")
    fam = fam.where(fam != "", other=a1.where(~a1.isin(MARKERS) & (a1 != ""), other=""))
    aim["family"] = fam
    aim["desc_norm"] = norm_desc(aim["description"])
    aim["l12m_eur"] = pd.to_numeric(aim.get("l12m_billed_eur", 0), errors="coerce").fillna(0.0)
    if "eur" in aim.columns:
        aim["eur_any"] = pd.to_numeric(aim["eur"], errors="coerce").fillna(0.0)
    else:
        aim["eur_any"] = 0.0
    aim["cat_path"] = (
        aim["cat_l1"].map(clean) + " > " + aim["cat_l2"].map(clean) + " > " + aim["cat_l3"].map(clean)
    )
    aim["has_cat"] = aim["cat_l1"].map(clean) != ""

    marked_mask = a1.isin(UNKNOWN_MARKERS) | a1f.isin(UNKNOWN_MARKERS)
    true_blank = aim[(aim["family"] == "") & (~marked_mask)].copy()
    unknown_rows = aim[marked_mask].copy()

    t1 = pd.read_csv(TRANCHE1, dtype=str, low_memory=False)
    t1_pns = set(norm_pn(t1["part_number"]))
    residual = true_blank[~true_blank["pn"].isin(t1_pns)].copy()
    residual["never_billed"] = (residual["l12m_eur"] <= 0) & (residual["eur_any"] <= 0)

    # --- known-family dictionaries ---
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
    unan = desc_tab[(desc_tab["n_l1"] == 1) & (desc_tab["n_parts"] >= DESC_MIN_N)]
    weak_desc = desc_tab[(desc_tab["n_l1"] == 1) & (desc_tab["n_parts"] >= DESC_WEAK_N) & (desc_tab["n_parts"] < DESC_MIN_N)]

    # Cat-path stats on known (why tranche1 missed these residuals)
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
        non_part_reason(p, d) for p, d in zip(residual["pn"], residual["description"].fillna(""))
    ]
    residual["is_non_part"] = residual["non_part_reason"] != ""
    residual["propose_desc_l1"] = residual["desc_norm"].map(unan["top_l1"])
    residual["desc_n"] = residual["desc_norm"].map(unan["n_parts"])
    residual["desc_unan"] = residual["propose_desc_l1"].notna()
    residual["propose_desc_weak_l1"] = residual["desc_norm"].map(weak_desc["top_l1"])
    residual["desc_weak"] = residual["propose_desc_weak_l1"].notna() & (~residual["desc_unan"])
    residual["desc_seen_any"] = residual["desc_norm"].isin(desc_tab.index) & (residual["desc_norm"] != "")
    residual["has_desc"] = residual["desc_norm"] != ""

    residual = residual.merge(
        cat_tab.add_prefix("cat_"),
        left_on="cat_path",
        right_index=True,
        how="left",
    )
    residual["cat_known_n"] = residual["cat_known_n"].fillna(0).astype(int)
    residual["cat_top_share"] = residual["cat_top_share"].fillna(0.0)
    residual["cat_near_miss"] = (
        residual["has_cat"]
        & (residual["cat_known_n"] >= CAT_NEAR_N)
        & (residual["cat_top_share"] >= CAT_NEAR_SHARE)
        & (residual["cat_top_share"] < 0.90)  # under tranche1 bar
    )
    residual["cat_contested"] = (
        residual["has_cat"]
        & (residual["cat_known_n"] >= CAT_NEAR_N)
        & (residual["cat_top_share"] < CAT_NEAR_SHARE)
        & (residual["cat_top_share"] >= CAT_WEAK_SHARE)
    )
    residual["cat_too_weak"] = residual["has_cat"] & (
        (residual["cat_known_n"] < CAT_NEAR_N) | (residual["cat_top_share"] < CAT_WEAK_SHARE)
    )
    residual["cat_review_bucket"] = residual["cat_path"].str.contains(
        r"Review needed|Miscellaneous|Other / review", case=False, na=False
    )

    # --- primary method (mutually exclusive peel order) ---
    method = pd.Series("", index=residual.index)

    # d) non-part / junk
    method[residual["is_non_part"]] = "d_non_part_junk"

    # a) desc-norm unanimity (final_tier rail)
    method[(method == "") & residual["desc_unan"]] = "a_desc_norm_unanimity"

    # a-weak) single family but n<3
    method[(method == "") & residual["desc_weak"]] = "a_desc_norm_weak_n_lt3"

    # a-new) has description text never seen on a known family
    method[(method == "") & residual["has_desc"] & (~residual["desc_seen_any"])] = (
        "a_desc_present_unseen_on_known"
    )

    # cat near-miss: empty/no-desc-map but cat almost tranche1 — NOT EQ; Shard A follow-on
    method[(method == "") & residual["cat_near_miss"]] = "e_cat_path_near_miss_relax_bar"

    # contested cat (50–80%): needs hand / EQ sample, not blind map
    method[(method == "") & residual["cat_contested"] & (~residual["cat_review_bucket"])] = (
        "b_cat_contested_needs_eq_or_hand"
    )

    # review-needed / misc catch-all catalogue bucket
    method[(method == "") & residual["cat_review_bucket"]] = "b_cat_review_bucket_needs_eq_or_hand"

    # weak / thin cat + empty desc → EQ / EPC
    method[(method == "") & residual["cat_too_weak"] & (~residual["has_desc"])] = (
        "b_needs_eq_epc_empty_desc_weak_cat"
    )

    # no catalogue at all
    method[(method == "") & (~residual["has_cat"])] = "b_needs_eq_epc_no_catalogue"

    # leftover (has desc contested on multi-family, etc.)
    method[method == ""] = "b_needs_eq_epc_other"

    residual["method"] = method
    n_res = len(residual)

    by_method = {m: pack(sub, n_res) for m, sub in residual.groupby("method", sort=True)}

    # Grouped EQ-required vs not
    eq_methods = {
        "b_cat_contested_needs_eq_or_hand",
        "b_cat_review_bucket_needs_eq_or_hand",
        "b_needs_eq_epc_empty_desc_weak_cat",
        "b_needs_eq_epc_no_catalogue",
        "b_needs_eq_epc_other",
        "a_desc_present_unseen_on_known",  # text alone not enough; EQ or hand to name family
    }
    no_eq_methods = {
        "a_desc_norm_unanimity",
        "a_desc_norm_weak_n_lt3",
        "d_non_part_junk",
        "e_cat_path_near_miss_relax_bar",
    }
    eq_slice = residual[residual["method"].isin(eq_methods)]
    no_eq_slice = residual[residual["method"].isin(no_eq_methods)]

    # Existing EQ evidence on disk
    eq_files = {
        "validation": str(DER / "_eq_hit_validation_20260917.json"),
        "probe_pns": str(DER / "_eq_hit_probe_pns.json"),
        "batch_tmp": str(DER / "_eq_hit_batch_tmp.json"),
    }
    eq_on_disk = {k: Path(v).exists() for k, v in eq_files.items()}
    probed_pns: set[str] = set()
    if Path(eq_files["probe_pns"]).exists():
        try:
            raw = json.loads(Path(eq_files["probe_pns"]).read_text(encoding="utf-8"))
            if isinstance(raw, list):
                probed_pns = {str(x).strip().upper() for x in raw}
            elif isinstance(raw, dict):
                for key in ("pns", "probe_pns", "parts"):
                    if key in raw and isinstance(raw[key], list):
                        probed_pns = {str(x).strip().upper() for x in raw[key]}
                        break
        except Exception:
            probed_pns = set()
    eq_overlap = int(eq_slice["pn"].isin(probed_pns).sum()) if probed_pns else 0

    # Samples
    samples = []
    for mlabel, sub in residual.groupby("method"):
        top = sub.sort_values(["l12m_eur", "pn"], ascending=[False, True]).head(20)
        for _, r in top.iterrows():
            samples.append(
                {
                    "method": mlabel,
                    "part_number": r["pn"],
                    "description": clean(r.get("description")),
                    "desc_norm": r["desc_norm"],
                    "cat_path": r["cat_path"],
                    "cat_known_n": int(r["cat_known_n"]),
                    "cat_top_share": round(float(r["cat_top_share"]), 4),
                    "cat_top_l1": clean(r.get("cat_top_l1")),
                    "propose_desc_l1": clean(r.get("propose_desc_l1"))
                    or clean(r.get("propose_desc_weak_l1")),
                    "l12m_billed_eur": round(float(r["l12m_eur"]), 2),
                    "non_part_reason": r.get("non_part_reason") or "",
                }
            )
    pd.DataFrame(samples).to_csv(OUT_SAMPLE, index=False)

    # Top desc proposals
    desc_hits = residual[residual["method"] == "a_desc_norm_unanimity"]
    top_desc = (
        desc_hits.groupby(["desc_norm", "propose_desc_l1"], dropna=False)
        .agg(rows=("pn", "size"), eur=("l12m_eur", "sum"), n_evidence=("desc_n", "max"))
        .reset_index()
        .sort_values("rows", ascending=False)
        .head(20)
    )
    top_desc_list = [
        {
            "desc_norm": str(r["desc_norm"])[:80],
            "propose_aim_l1": str(r["propose_desc_l1"]),
            "residual_rows": int(r["rows"]),
            "l12m_billed_eur": round(float(r["eur"]), 2),
            "known_evidence_n": int(r["n_evidence"]) if pd.notna(r["n_evidence"]) else None,
        }
        for _, r in top_desc.iterrows()
    ]

    # Top near-miss cat paths
    near = residual[residual["method"] == "e_cat_path_near_miss_relax_bar"]
    top_near = (
        near.groupby(["cat_path", "cat_top_l1"], dropna=False)
        .agg(rows=("pn", "size"), eur=("l12m_eur", "sum"), known_n=("cat_known_n", "max"), share=("cat_top_share", "max"))
        .reset_index()
        .sort_values("rows", ascending=False)
        .head(25)
    )
    top_near_list = [
        {
            "cat_path": str(r["cat_path"])[:100],
            "propose_aim_l1": str(r["cat_top_l1"]),
            "residual_rows": int(r["rows"]),
            "known_n": int(r["known_n"]),
            "agree_share": round(float(r["share"]), 4),
            "l12m_billed_eur": round(float(r["eur"]), 2),
        }
        for _, r in top_near.iterrows()
    ]

    junk = residual[residual["method"] == "d_non_part_junk"]
    junk_reasons = junk["non_part_reason"].value_counts().head(20).astype(int).to_dict() if len(junk) else {}

    # Billed euro inside EQ-required slices
    eq_billed = eq_slice[eq_slice["l12m_eur"] > 0]

    attack_order = [
        {
            "order": 1,
            "method": "d_non_part_junk",
            "why": "Peel rebate / freight / alpha keys out of the parts denominator. Tiny row count, most of the residual billed euro.",
            "rows": by_method.get("d_non_part_junk", {}).get("rows", 0),
            "l12m_billed_eur": by_method.get("d_non_part_junk", {}).get("l12m_billed_eur", 0),
            "needs_eq": False,
        },
        {
            "order": 2,
            "method": "e_cat_path_near_miss_relax_bar",
            "why": (
                f"Catalogue path already leans one family at {CAT_NEAR_SHARE:.0%}–90% with n>={CAT_NEAR_N}. "
                "Same idea as tranche1, slightly softer bar. Hand to Shard A — no EQ."
            ),
            "rows": by_method.get("e_cat_path_near_miss_relax_bar", {}).get("rows", 0),
            "l12m_billed_eur": by_method.get("e_cat_path_near_miss_relax_bar", {}).get("l12m_billed_eur", 0),
            "needs_eq": False,
        },
        {
            "order": 3,
            "method": "a_desc_norm_unanimity + a_desc_norm_weak_n_lt3",
            "why": (
                f"Normalised description names one known family (unanimity n>={DESC_MIN_N}, "
                f"or weak n={DESC_WEAK_N}–{DESC_MIN_N - 1}). Small because ~99% of residual blanks have no description text."
            ),
            "rows": (
                by_method.get("a_desc_norm_unanimity", {}).get("rows", 0)
                + by_method.get("a_desc_norm_weak_n_lt3", {}).get("rows", 0)
            ),
            "needs_eq": False,
        },
        {
            "order": 4,
            "method": "b_* EQ slices with billed euro first",
            "why": "Contested / review / weak-catalogue residual that already bills — EQ (or hand on a sample) earns its keep.",
            "rows": int(len(eq_billed)),
            "l12m_billed_eur": round(eur_sum(eq_billed["l12m_eur"]), 2),
            "needs_eq": True,
        },
        {
            "order": 5,
            "method": "a_desc_present_unseen_on_known",
            "why": "Has text, but that text never appears on a known family — EQ or hand to name the family once, then reuse.",
            "rows": by_method.get("a_desc_present_unseen_on_known", {}).get("rows", 0),
            "needs_eq": True,
        },
        {
            "order": 6,
            "method": "b_cat_contested + b_cat_review_bucket (never billed)",
            "why": "Large empty-description pile on contested or Review-needed catalogue paths. Batch EQ / hand sampling, not a blind map.",
            "rows": (
                by_method.get("b_cat_contested_needs_eq_or_hand", {}).get("rows", 0)
                + by_method.get("b_cat_review_bucket_needs_eq_or_hand", {}).get("rows", 0)
            ),
            "needs_eq": True,
        },
        {
            "order": 7,
            "method": "b_needs_eq_epc_empty_desc_weak_cat + no_catalogue",
            "why": "Weak or missing catalogue and no description — true EQ/EPC work. Park never-billed until a live need.",
            "rows": (
                by_method.get("b_needs_eq_epc_empty_desc_weak_cat", {}).get("rows", 0)
                + by_method.get("b_needs_eq_epc_no_catalogue", {}).get("rows", 0)
            ),
            "needs_eq": True,
        },
        {
            "order": 8,
            "method": "c_unknown_markers",
            "why": "Separate clear-up of deliberate Unknown / Unknown Review — size only in this shard.",
            "rows": int(len(unknown_rows)),
            "needs_eq": False,
        },
    ]

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "shard": "C",
        "bar": "residual methods after tranche1 cat_map proposal — inventory only, no apply",
        "inputs": {
            "master": str(MASTER),
            "tranche1_proposal": str(TRANCHE1),
            "desc_norm_rule": (
                f"unanimity: n_l1==1 and n_parts>={DESC_MIN_N} on known master families "
                f"(export_aim_tiering_20260924/final_tier.py rail); weak: n_l1==1 and n<{DESC_MIN_N}"
            ),
            "cat_near_miss_rule": (
                f"known_n>={CAT_NEAR_N} and {CAT_NEAR_SHARE:.0%}<=top_share<90% "
                "(under tranche1 bar; Shard A follow-on, not EQ)"
            ),
        },
        "master_rows": int(len(aim)),
        "with_family": int((aim["family"] != "").sum()),
        "without_family": int((aim["family"] == "").sum()),
        "true_blank_rows": int(len(true_blank)),
        "unknown_marker_rows": int(len(unknown_rows)),
        "tranche1_proposed_rows": int(len(t1_pns)),
        "residual_true_blank_after_tranche1": int(n_res),
        "residual_shape": {
            "empty_description": int((residual["desc_norm"] == "").sum()),
            "has_description": int((residual["desc_norm"] != "").sum()),
            "with_cat_l1": int(residual["has_cat"].sum()),
            "without_cat_l1": int((~residual["has_cat"]).sum()),
            "l12m_billed_eur": round(eur_sum(residual["l12m_eur"]), 2),
            "rows_with_l12m_bill": int((residual["l12m_eur"] > 0).sum()),
            "headline": (
                "Almost all residual blanks already have a catalogue node and an EMPTY description. "
                "Desc-norm barely applies. The real fork is softer cat_map (Shard A) vs EQ/hand on contested paths."
            ),
        },
        "by_method": by_method,
        "method_labels_plain": {
            "a_desc_norm_unanimity": "Same description text as known parts, all one family, >=3 examples — propose without EQ",
            "a_desc_norm_weak_n_lt3": "Same description, one family, but fewer than 3 known examples — review, still no EQ",
            "a_desc_present_unseen_on_known": "Has description text never seen on a known family — needs EQ or hand once",
            "e_cat_path_near_miss_relax_bar": "Catalogue path almost meets tranche1 bar (80–90%) — softer cat_map, no EQ",
            "b_cat_contested_needs_eq_or_hand": "Catalogue path split across families (50–80%) — EQ sample or hand",
            "b_cat_review_bucket_needs_eq_or_hand": "Catalogue parked under Review needed / Miscellaneous — EQ or hand",
            "b_needs_eq_epc_empty_desc_weak_cat": "No description and weak catalogue evidence — EQ/EPC",
            "b_needs_eq_epc_no_catalogue": "No catalogue node — EQ/EPC",
            "b_needs_eq_epc_other": "Other leftover needing more evidence",
            "d_non_part_junk": "Rebate / freight / alpha keys — leave the parts denominator",
            "c_unknown_markers": "Unknown / Unknown Review markers — size only, do not clear here",
        },
        "can_proceed_without_eq": {
            m: by_method.get(m, {})
            for m in sorted(no_eq_methods)
        },
        "can_proceed_without_eq_totals": {
            "rows": int(len(no_eq_slice)),
            "l12m_billed_eur": round(eur_sum(no_eq_slice["l12m_eur"]), 2),
        },
        "requires_eq_access": {
            "methods": sorted(eq_methods),
            "rows": int(len(eq_slice)),
            "l12m_billed_eur": round(eur_sum(eq_slice["l12m_eur"]), 2),
            "rows_with_l12m_bill": int(len(eq_billed)),
            "billed_eur_only": round(eur_sum(eq_billed["l12m_eur"]), 2),
            "never_billed_rows": int(eq_slice["never_billed"].sum()),
            "existing_eq_probe_overlap_rows": eq_overlap,
            "eq_evidence_on_disk": eq_on_disk,
            "eq_evidence_paths": eq_files,
            "note": (
                "EQ / Snap-on EPC is required for the b_* slices (and unseen descriptions) "
                "before a defensible family. No live EQ session in this shard. On-disk EQ files "
                f"are validation/probe only ({eq_overlap} residual EQ-bucket rows overlap known probe PNs)."
            ),
        },
        "c_unknown_markers_size_only": {
            "rows": int(len(unknown_rows)),
            "note": "size only — do not clear in this shard",
        },
        "top_desc_norm_unanimity_proposals": top_desc_list,
        "top_cat_path_near_miss": top_near_list,
        "non_part_reason_breakdown": junk_reasons,
        "recommended_attack_order": attack_order,
        "outputs": {
            "inventory_json": str(OUT_JSON),
            "samples_csv": str(OUT_SAMPLE),
        },
        "apply": "NO — inventory only. Wait for Jerome OK before any release or EQ session.",
        "notes": [
            "Shard A owns tranche1 cat_map; residual excludes those PNs. Near-miss (e_) is flagged for Shard A, not reworked here.",
            "Shard B owns live warehouse/backlog; this inventory is master-wide.",
            "Unknown / Unknown Review counted under c — size only, not cleared.",
            "89.8k of 90.9k residual blanks have empty description text on the master.",
        ],
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("residual", n_res)
    print("by_method rows:")
    for k, v in sorted(by_method.items(), key=lambda kv: -kv[1]["rows"]):
        print(f"  {k:45s} {v['rows']:6d}  eur={v['l12m_billed_eur']:,.0f}")
    print("no_eq", len(no_eq_slice), "eq", len(eq_slice), "unknown", len(unknown_rows))
    print("wrote", OUT_JSON)
    print("wrote", OUT_SAMPLE)


if __name__ == "__main__":
    main()
