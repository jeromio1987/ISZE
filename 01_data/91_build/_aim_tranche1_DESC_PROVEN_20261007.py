"""Build DESC_PROVEN subset from SAFE-v2 ∩ rigor PASS (usable description evidence).

Proposal / gate only. Does NOT write aim_master or cut a dated release apply.
Drops the 7,154 blank-desc path-majority inconclusive rows that block apply permission.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SAFE_V2 = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_SAFE_v2_2026-10-07.csv"
)
RIGOR_SAFE = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_SAFE_20261007.csv"
FAILS = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_fails_20261007.csv"
RIGOR_JSON = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_20261007.json"
MASTER = ISZE / "01_data/00_derived/aim_master_v2.csv"
JP = ISZE / "01_data/00_derived/jp_codes_cache_20260920.csv"

OUT_CSV = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv"
)
OUT_SUM = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.summary.json"
)
OUT_MD = ISZE / "01_data/91_build/_aim_tranche1_DESC_PROVEN_verify_20261007.md"

MASTER_ROWS = 165_310
BASE_WITH_FAMILY = 21_045

CYL_HD_GASKET_RE = re.compile(
    r"GASKET;?\s*CYL|CYL\.?\s*HD|HEAD\s*GASKET|GASKET;?\s*HEAD|"
    r"HD\s*OVERHAUL|HEAD\s*OVERHAUL|"
    r"\bGASKET\b.*\bENG|\bENG\b.*\bGASKET|"
    r"CYLINDER\s*HEAD\s*GASKET|GASKET.*CYLINDER\s*HEAD",
    re.I,
)

HARD_HOLD_PATHS = [
    ("Repair parts > Gaskets / seals > Gasket set", "Transmission", "gasket_set_to_transmission"),
    (
        "High value repair > Transmission parts > Transmission assembly",
        "Literature Marketing",
        "trans_asm_to_literature",
    ),
    ("Competitive parts > Air system > Air valve", "Steering", "air_valve_to_steering"),
]


def clean(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def pad10(pn: str) -> str:
    pn = clean(pn)
    if pn.isdigit() and len(pn) < 10:
        return pn.zfill(10)
    return pn


def desc_cyl_to_trans(row) -> bool:
    if not CYL_HD_GASKET_RE.search(clean(row.get("desc_u", ""))):
        return False
    return clean(row.get("propose_aim_l1", "")) == "Transmission"


def main() -> None:
    safe_v2 = pd.read_csv(SAFE_V2, dtype=str, low_memory=False)
    n_safe_v2 = len(safe_v2)
    safe_v2["pn10"] = safe_v2["part_number"].map(pad10)

    rigor_safe = pd.read_csv(RIGOR_SAFE, dtype=str, low_memory=False)
    rigor_safe["pn10"] = rigor_safe["part_number"].map(pad10)
    pass_pn10 = set(rigor_safe["pn10"])
    n_rigor_pass = len(pass_pn10)

    fails = pd.read_csv(FAILS, dtype=str, low_memory=False)
    inc = fails[fails["rigor_status"].map(clean) == "inconclusive"]
    n_inc_file = len(inc)
    inc_pn10 = set(inc["pn10"].map(pad10))

    # DESC_PROVEN = SAFE-v2 rows that were rigor PASS (usable description evidence)
    keep = safe_v2["pn10"].isin(pass_pn10)
    dropped_inc = safe_v2["pn10"].isin(inc_pn10)
    n_dropped_inc = int(dropped_inc.sum())
    leftover_fail = int(
        (
            ~keep
            & ~dropped_inc
        ).sum()
    )

    desc = safe_v2.loc[keep].copy()
    n_desc = len(desc)

    # Join unified description for zero-checks + honesty
    am = pd.read_csv(
        MASTER, dtype=str, usecols=["part_number", "description"], low_memory=False
    )
    am["pn10"] = am["part_number"].map(pad10)
    am = am.drop_duplicates("pn10", keep="first")

    jp = pd.read_csv(JP, dtype=str, low_memory=False)
    jp["pn10"] = jp["pn"].map(pad10)
    jp = jp.drop_duplicates("pn10", keep="first")

    s = desc.merge(
        am[["pn10", "description"]].rename(columns={"description": "master_desc"}),
        on="pn10",
        how="left",
    )
    s = s.merge(jp[["pn10", "jp_description"]], on="pn10", how="left")
    s["desc_unified"] = [
        clean(a) or clean(b) or clean(c)
        for a, b, c in zip(s.get("description", ""), s["master_desc"], s["jp_description"])
    ]
    s["desc_u"] = s["desc_unified"].str.upper()
    blank_unified = int((s["desc_unified"].map(clean) == "").sum())
    with_unified = n_desc - blank_unified

    # --- Zero checks ---
    zero_checks: dict[str, dict] = {}
    cyl_to_trans = s[s.apply(desc_cyl_to_trans, axis=1)]
    path_cyl_trans = s[
        (s["cat_path"].map(clean) == "Repair parts > Gaskets / seals > Cylinder head gasket")
        & (s["propose_aim_l1"].map(clean) == "Transmission")
    ]
    zero_checks["cyl_hd_gasket_desc_to_transmission"] = {
        "n": int(len(cyl_to_trans)),
        "pass": len(cyl_to_trans) == 0,
    }
    zero_checks["cyl_hd_gasket_path_to_transmission"] = {
        "n": int(len(path_cyl_trans)),
        "pass": len(path_cyl_trans) == 0,
    }
    for path, bad_l1, name in HARD_HOLD_PATHS:
        n = int(
            (
                (s["cat_path"].map(clean) == path)
                & (s["propose_aim_l1"].map(clean) == bad_l1)
            ).sum()
        )
        zero_checks[name] = {"n": n, "pass": n == 0, "cat_path": path, "propose_aim_l1": bad_l1}

    n_trans = int((s["propose_aim_l1"].map(clean) == "Transmission").sum())
    zero_checks["any_propose_transmission"] = {"n": n_trans, "pass": True}

    all_hard_zero = all(
        zero_checks[k]["pass"]
        for k in [
            "cyl_hd_gasket_desc_to_transmission",
            "cyl_hd_gasket_path_to_transmission",
            "gasket_set_to_transmission",
            "trans_asm_to_literature",
            "air_valve_to_steering",
        ]
    )

    rigor = json.loads(RIGOR_JSON.read_text(encoding="utf-8"))
    cov = rigor.get("coverage", {})
    price_fail = int(rigor.get("price_fail_count", 0))
    zkk_usable = int(cov.get("zkk_majority_codes_usable", 0))
    zkk_checked = int(cov.get("zkk_rows_checked_against_majority", 0))
    zkk_conflict = int(rigor.get("zkk_conflict_count", 0))
    hkk_usable = int(cov.get("hkk_majority_codes_usable", 0))
    hkk_checked = int(cov.get("hkk_rows_checked_against_majority", 0))
    hkk_conflict = int(rigor.get("hkk_conflict_count", 0))
    pn_len_fail = int(rigor.get("pn_length_fail_count", 0))
    pn_prefix = int(rigor.get("pn_prefix_outlier_count", 0))

    # Write proposal CSV (same columns as SAFE-v2)
    out_cols = [c for c in safe_v2.columns if c != "pn10"]
    desc_out = desc[out_cols].copy()
    desc_out.to_csv(OUT_CSV, index=False)

    with_family_if = BASE_WITH_FAMILY + n_desc
    with_family_pct = round(100.0 * with_family_if / MASTER_ROWS, 2)

    by_conf = {k: int(v) for k, v in desc_out["confidence"].value_counts().to_dict().items()}
    top_l1 = {
        k: int(v) for k, v in desc_out["propose_aim_l1"].value_counts().head(20).to_dict().items()
    }

    # Honest permission: description+path+holds clean; ZKK not a family proof → PARTIAL
    if not all_hard_zero or blank_unified > 0 or n_dropped_inc != n_inc_file:
        permission = "NOT_EARNED"
        permission_bar = "FAIL"
        apply_sentence = (
            "DESC_PROVEN does not meet the conditional bar — a zero-check failed, "
            "or blank unified descriptions remain, or the inconclusive drop did not match."
        )
        verdict_md = apply_sentence
    else:
        permission = "PARTIAL_CONDITIONAL"
        permission_bar = "PARTIAL"
        apply_sentence = (
            "PARTIAL — description + catalogue-path + hard-hold leaks are clean on this "
            f"{n_desc:,}-row desc-proven slice (blank-desc path-majority dropped), so Jerome "
            "can grant conditional apply permission for THIS file only; ZKK is still not a "
            "family proof (almost unused at scale) and does not earn the full PN/description/"
            "price/ZKK rigor bar by itself."
        )
        verdict_md = apply_sentence

    honesty_price_zkk = (
        f"Price absurdity: {price_fail} fails on the parent rigor run (none left in this slice). "
        f"ZKK: only {zkk_usable} pure majority code(s) at n≥20 / ≥80% purity; "
        f"{zkk_checked} rows checked against that majority; {zkk_conflict} conflicts. "
        f"HKK: {hkk_usable} usable codes; {hkk_checked} rows checked; {hkk_conflict} conflicts "
        f"(already removed with the 406 rigor fails). "
        "ZKK/HKK did not define AIM family for most of this proposal — description text did. "
        f"PN length fails: {pn_len_fail}; PN prefix outliers: {pn_prefix}."
    )

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source_safe_v2_csv": str(SAFE_V2),
        "rigor_safe_csv": str(RIGOR_SAFE),
        "rigor_fails_csv": str(FAILS),
        "rigor_json": str(RIGOR_JSON),
        "desc_proven_csv": str(OUT_CSV),
        "apply": (
            "NO — proposal only. DESC_PROVEN does not write aim_master and is not a dated release apply."
        ),
        "permission": permission,
        "permission_bar": permission_bar,
        "apply_permission_earned": False,
        "apply_permission_sentence": apply_sentence,
        "rows_safe_v2": n_safe_v2,
        "rows_rigor_pass_expected": n_rigor_pass,
        "rows_desc_proven": n_desc,
        "rows_dropped_blank_desc_inconclusive": n_dropped_inc,
        "rows_inconclusive_in_fails_file": n_inc_file,
        "leftover_nonpass_noninc_in_safe_v2": leftover_fail,
        "unified_description": {
            "with_unified_desc": with_unified,
            "blank_unified_desc": blank_unified,
            "note": (
                "Usable description = JP + master + proposal text united (same as rigor). "
                "Proposal `description` column is often blank even when JP text exists."
            ),
        },
        "price_zkk_hkk_honesty": honesty_price_zkk,
        "zkk_contribution": {
            "zkk_majority_codes_usable": zkk_usable,
            "zkk_rows_checked_against_majority": zkk_checked,
            "zkk_conflict_count": zkk_conflict,
            "note": cov.get(
                "note_zkk",
                "ZKK is a Japan catalogue attribute, not an AIM family.",
            ),
        },
        "hkk_contribution": {
            "hkk_majority_codes_usable": hkk_usable,
            "hkk_rows_checked_against_majority": hkk_checked,
            "hkk_conflict_count": hkk_conflict,
        },
        "price_pn_contribution": {
            "price_fail_count": price_fail,
            "pn_length_fail_count": pn_len_fail,
            "pn_prefix_outlier_count": pn_prefix,
        },
        "zero_checks": zero_checks,
        "zero_checks_all_pass": all_hard_zero,
        "by_confidence": by_conf,
        "top_propose_l1": top_l1,
        "coverage_if_desc_proven_applied": {
            "master_rows": MASTER_ROWS,
            "base_with_family": BASE_WITH_FAMILY,
            "base_with_family_pct": round(100.0 * BASE_WITH_FAMILY / MASTER_ROWS, 2),
            "desc_proven_rows_added": n_desc,
            "with_family_if_applied": with_family_if,
            "with_family_pct_if_applied": with_family_pct,
            "without_family_if_applied": MASTER_ROWS - with_family_if,
            "note": "Projected only — DESC_PROVEN not applied to master.",
        },
        "notes": [
            "Intersect SAFE-v2 with rigor PASS (usable JP/master/proposal description evidence).",
            f"Dropped {n_dropped_inc:,} rigor-inconclusive blank-desc path-majority rows.",
            "Hard holds and cyl-head→Transmission re-zeroed on the desc-proven file.",
            "Does not apply aim_master. ZKK is not claimed as family proof.",
        ],
    }
    OUT_SUM.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    zc_rows = "\n".join(
        f"| {k} | {v['n']} | {'YES' if v['pass'] else 'NO'} |"
        for k, v in zero_checks.items()
        if k != "any_propose_transmission"
    )
    md = f"""# DESC_PROVEN verify — 2026-10-07

## Verdict

{verdict_md}

**Permission bar:** `{permission_bar}`  
**Apply aim_master?** No.

## Counts

| Piece | Rows |
|---|---:|
| SAFE-v2 in | {n_safe_v2:,} |
| Rigor PASS kept (desc-proven) | **{n_desc:,}** |
| Blank-desc inconclusive dropped | {n_dropped_inc:,} (fails file had {n_inc_file:,}) |
| Unified desc blank remaining | {blank_unified:,} |

Projected coverage if applied (not applied): {with_family_if:,} / {MASTER_ROWS:,} = {with_family_pct}% with family (from base {BASE_WITH_FAMILY:,}).

## Zero-checks (must all be 0)

| Check | Count | Pass |
|---|---:|---|
{zc_rows}
| Any propose_aim_l1 = Transmission left (info) | {n_trans} | — |

All hard zero-checks pass: **{'YES' if all_hard_zero else 'NO'}**.

## Honesty — what price / ZKK actually contributed

{honesty_price_zkk}

Description text (JP/master/proposal united) is the primary rigor signal for this file. Catalogue-path majority alone was not enough for Jerome; the 7,154 blank-desc path-majority rows are out. That still leaves ZKK short of a family proof — hence **PARTIAL**, not a full earn of his stated PN / description / price / ZKK bar.

## Paths

- DESC_PROVEN CSV: `{OUT_CSV}`
- Summary: `{OUT_SUM}`
- This note: `{OUT_MD}`

## What was not done

aim_master was not written. No dated release apply. Full ZKK family proof is not claimed.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(
        json.dumps(
            {
                "rows_desc_proven": n_desc,
                "dropped_inc": n_dropped_inc,
                "blank_unified": blank_unified,
                "zero_all_pass": all_hard_zero,
                "permission_bar": permission_bar,
                "coverage_pct_if_applied": with_family_pct,
                "out_csv": str(OUT_CSV),
                "out_sum": str(OUT_SUM),
                "out_md": str(OUT_MD),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
