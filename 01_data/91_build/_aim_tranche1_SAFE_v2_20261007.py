"""Build SAFE-v2 proposal from CLEAN − rigor fails − leftover cyl-head→Transmission.

Proposal / gate only. Does NOT write aim_master or cut a dated release apply.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
CLEAN = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_CLEAN_2026-10-07.csv"
)
FAILS = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_fails_20261007.csv"
RIGOR_JSON = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_20261007.json"
MASTER = ISZE / "01_data/00_derived/aim_master_v2.csv"
JP = ISZE / "01_data/00_derived/jp_codes_cache_20260920.csv"

OUT_CSV = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_SAFE_v2_2026-10-07.csv"
)
OUT_SUM = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_SAFE_v2_2026-10-07.summary.json"
)
OUT_MD = ISZE / "01_data/91_build/_aim_tranche1_SAFE_v2_verify_20261007.md"

MASTER_ROWS = 165_310
BASE_WITH_FAMILY = 21_045

# Engine / cylinder-head gasket language (JP / master / proposal desc)
CYL_HD_GASKET_RE = re.compile(
    r"GASKET;?\s*CYL|CYL\.?\s*HD|HEAD\s*GASKET|GASKET;?\s*HEAD|"
    r"HD\s*OVERHAUL|HEAD\s*OVERHAUL|"
    r"\bGASKET\b.*\bENG|\bENG\b.*\bGASKET|"
    r"CYLINDER\s*HEAD\s*GASKET|GASKET.*CYLINDER\s*HEAD",
    re.I,
)

TRANS_BAD_L1 = {"Transmission"}
# L2/L3 under Transmission that are the same leak class
TRANS_BAD_L2 = re.compile(r"bearing|seal|gasket|transmission", re.I)

# Prior Shard A / CLEAN hard holds — must stay zero in SAFE-v2
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


def is_trans_family(row) -> bool:
    l1 = clean(row.get("propose_aim_l1", ""))
    l2 = clean(row.get("propose_aim_l2", ""))
    l3 = clean(row.get("propose_aim_l3", ""))
    if l1 in TRANS_BAD_L1:
        return True
    if l1 == "Transmission" or TRANS_BAD_L2.search(l2) or TRANS_BAD_L2.search(l3):
        # only treat as Transmission-family if L1 is Transmission OR L2/L3 clearly under that leak
        if l1 in TRANS_BAD_L1:
            return True
        if l1 == "Transmission":
            return True
    return l1 in TRANS_BAD_L1


def main() -> None:
    prop = pd.read_csv(CLEAN, dtype=str, low_memory=False)
    n_clean = len(prop)
    prop["pn10"] = prop["part_number"].map(pad10)

    fails = pd.read_csv(FAILS, dtype=str, low_memory=False)
    hard_fails = fails[fails["rigor_status"].map(clean) == "fail"].copy()
    n_fail_file = len(hard_fails)
    fail_pn10 = set(hard_fails["pn10"].map(pad10))
    fail_pn_raw = set(hard_fails["part_number"].map(clean))

    # Join JP + master descriptions for residual leak scan
    am = pd.read_csv(
        MASTER,
        dtype=str,
        usecols=["part_number", "description"],
        low_memory=False,
    )
    am["pn10"] = am["part_number"].map(pad10)
    am = am.drop_duplicates("pn10", keep="first")

    jp = pd.read_csv(JP, dtype=str, low_memory=False)
    jp["pn10"] = jp["pn"].map(pad10)
    jp = jp.drop_duplicates("pn10", keep="first")

    m = prop.merge(
        am[["pn10", "description"]].rename(columns={"description": "master_desc"}),
        on="pn10",
        how="left",
    )
    m = m.merge(
        jp[["pn10", "jp_description"]],
        on="pn10",
        how="left",
    )
    m["desc_unified"] = [
        clean(a) or clean(b) or clean(c)
        for a, b, c in zip(m.get("description", ""), m["master_desc"], m["jp_description"])
    ]
    m["desc_u"] = m["desc_unified"].str.upper()

    # --- Exclusion masks ---
    excl_fail = m["pn10"].isin(fail_pn10) | m["part_number"].map(clean).isin(fail_pn_raw)

    # Path sibling that leaked: Cylinder head gasket → Transmission (any L2/L3)
    excl_path_cyl = (m["cat_path"].map(clean) == "Repair parts > Gaskets / seals > Cylinder head gasket") & (
        m["propose_aim_l1"].map(clean) == "Transmission"
    )

    # Description residual: cyl-head / head gasket nouns → Transmission (or bearings/seals/gasket L2)
    def desc_cyl_to_trans(row) -> bool:
        if not CYL_HD_GASKET_RE.search(clean(row["desc_u"])):
            return False
        l1 = clean(row["propose_aim_l1"])
        l2 = clean(row["propose_aim_l2"])
        l3 = clean(row["propose_aim_l3"])
        if l1 == "Transmission":
            return True
        # Transmission bearings/seals/gasket as L2/L3 even if L1 mislabelled
        if TRANS_BAD_L2.search(l2) and ("seal" in l2.lower() or "gasket" in l2.lower() or "bearing" in l2.lower()):
            if l1 == "Transmission" or "transmission" in l2.lower():
                return True
        if l1 == "Transmission" and TRANS_BAD_L2.search(f"{l2} {l3}"):
            return True
        return False

    excl_desc_cyl = m.apply(desc_cyl_to_trans, axis=1)

    # Extra residual beyond hard-fail PNs
    excl_extra = (excl_path_cyl | excl_desc_cyl) & ~excl_fail

    keep = ~(excl_fail | excl_path_cyl | excl_desc_cyl)
    safe = m.loc[keep].copy()

    # Drop helper cols for proposal CSV (match CLEAN columns)
    clean_cols = list(pd.read_csv(CLEAN, nrows=0).columns)
    safe_out = safe[[c for c in clean_cols if c in safe.columns]].copy()
    n_safe = len(safe_out)
    n_excl_fail = int(excl_fail.sum())
    n_excl_extra = int(excl_extra.sum())
    n_excl_path = int(excl_path_cyl.sum())
    n_excl_desc = int(excl_desc_cyl.sum())

    # --- Zero checks on SAFE-v2 (re-join desc on output) ---
    s = safe_out.copy()
    s["pn10"] = s["part_number"].map(pad10)
    s = s.merge(
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

    zero_checks: dict[str, dict] = {}

    # 1) GASKET; CYL HD / engine-gasket nouns → Transmission
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

    # 2) Prior hard holds
    for path, bad_l1, name in HARD_HOLD_PATHS:
        n = int(
            (
                (s["cat_path"].map(clean) == path)
                & (s["propose_aim_l1"].map(clean) == bad_l1)
            ).sum()
        )
        zero_checks[name] = {"n": n, "pass": n == 0, "cat_path": path, "propose_aim_l1": bad_l1}

    # 3) Any Transmission L1 left at all (CLEAN only had the 328 leak)
    n_trans = int((s["propose_aim_l1"].map(clean) == "Transmission").sum())
    zero_checks["any_propose_transmission"] = {"n": n_trans, "pass": True}  # informational

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

    # Description coverage honesty
    blank_desc = int((s["desc_unified"].map(clean) == "").sum())
    with_desc = n_safe - blank_desc
    # Rows that were pass in rigor (described + passed) vs inconclusive kept
    rigor = json.loads(RIGOR_JSON.read_text(encoding="utf-8"))
    n_pass_rigor = int(rigor.get("pass", 0))
    n_inc_rigor = int(rigor.get("inconclusive", 0))
    # SAFE-v2 ≈ pass + inconclusive (fails removed); measure from fails file
    inc_pn10 = set(fails.loc[fails["rigor_status"].map(clean) == "inconclusive", "pn10"].map(pad10))
    n_inc_in_safe = int(s["pn10"].isin(inc_pn10).sum())
    n_pass_in_safe = n_safe - n_inc_in_safe

    description_clean_only = blank_desc == 0 and n_inc_in_safe == 0
    honesty = (
        "description-clean only (every remaining row has JP/master/proposal text that passed rigor)"
        if description_clean_only
        else (
            f"still path-majority for {blank_desc:,} rows without description "
            f"({n_inc_in_safe:,} rigor-inconclusive kept); "
            f"{with_desc:,} rows have a description. "
            "ZKK is almost useless at this scale (rigor found 1 pure ZKK code at n≥20 / ≥80%), "
            "so blank-desc rows are catalogue-path proposals, not commodity-verified."
        )
    )

    coverage_added = n_safe
    with_family_if = BASE_WITH_FAMILY + coverage_added
    with_family_pct = round(100.0 * with_family_if / MASTER_ROWS, 2)

    by_conf = {k: int(v) for k, v in safe_out["confidence"].value_counts().to_dict().items()}
    top_l1 = {
        k: int(v) for k, v in safe_out["propose_aim_l1"].value_counts().head(20).to_dict().items()
    }

    # Permission honesty
    if not all_hard_zero:
        permission = "NOT_EARNED"
        verdict = (
            "SAFE-v2 still fails a hard zero-check — do not ask Jerome for apply permission."
        )
        apply_sentence = (
            "Apply permission is not earned — a teaching leak or hard hold is still present."
        )
    elif n_inc_in_safe > 0 or blank_desc > 0:
        permission = "NOT_EARNED_UNTIL_JEROME_RE_READS"
        verdict = (
            "SAFE-v2 is description-clean on the cyl-head / hard-hold leaks "
            f"(zero checks pass), but {blank_desc:,} rows still have no description "
            "and ride on catalogue path only — not apply-ready until Jerome re-reads "
            "that blank-desc tail (or cuts it)."
        )
        apply_sentence = (
            "Apply permission is not earned yet — zero-checks on description leaks pass, "
            "but the blank-description path-majority tail still needs Jerome's eyes before any apply."
        )
    else:
        permission = "EARNED_CONDITIONAL_RE_PERMISSION"
        verdict = (
            "SAFE-v2 meets the description rigor bar on remaining rows "
            "(cyl-head→Transmission and prior hard holds are zero). "
            "Conditional re-permission from Jerome is the next gate — still do not apply until he says so."
        )
        apply_sentence = (
            "Zero-checks pass and remaining rows are description-backed — "
            "Jerome's re-permission could be asked; apply is still not automatic."
        )

    excluded_reasons = [
        {
            "reason": "rigor_fail",
            "n": n_excl_fail,
            "n_expected": n_fail_file,
            "detail": (
                "Every rigor_status=fail row from "
                "_aim_tranche1_CLEAN_rigor_fails_20261007.csv "
                f"(teaching_bug + desc_hard + desc_noun + desc_stem + hkk; expected {n_fail_file})"
            ),
        },
        {
            "reason": "cyl_hd_gasket_path_to_transmission",
            "n": n_excl_path,
            "detail": (
                "cat_path = Repair parts > Gaskets / seals > Cylinder head gasket "
                "AND propose_aim_l1 = Transmission"
            ),
        },
        {
            "reason": "cyl_hd_gasket_desc_to_transmission",
            "n": n_excl_desc,
            "detail": (
                "JP/master/proposal desc matches CYL HD / HEAD GASKET / ENG gasket "
                "AND propose is Transmission (or Transmission bearings/seals/gasket)"
            ),
        },
        {
            "reason": "extra_beyond_rigor_fail_pns",
            "n": n_excl_extra,
            "detail": "Rows hit by path/desc cyl-head→Transmission rules but not already in the 406 rigor fails",
        },
    ]

    safe_out.to_csv(OUT_CSV, index=False)

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source_clean_csv": str(CLEAN),
        "rigor_fails_csv": str(FAILS),
        "rigor_json": str(RIGOR_JSON),
        "safe_v2_csv": str(OUT_CSV),
        "apply": (
            "NO — proposal only. SAFE-v2 does not write aim_master and is not a dated release apply."
        ),
        "permission": permission,
        "apply_permission_earned": False,
        "apply_permission_sentence": apply_sentence,
        "rows_clean": n_clean,
        "rows_safe_v2": n_safe,
        "rows_excluded_total": n_clean - n_safe,
        "excluded_reasons": excluded_reasons,
        "fail_leftovers_in_safe_v2": 0,
        "rigor_pass_rows_in_safe_v2": n_pass_in_safe,
        "rigor_inconclusive_rows_in_safe_v2": n_inc_in_safe,
        "description_coverage": {
            "with_description": with_desc,
            "blank_description": blank_desc,
            "blank_share": round(blank_desc / n_safe, 4) if n_safe else 0,
            "honesty": honesty,
            "zkk_note": rigor.get("coverage", {}).get("note_zkk", ""),
        },
        "zero_checks": zero_checks,
        "zero_checks_all_pass": all_hard_zero,
        "by_confidence": by_conf,
        "top_propose_l1": top_l1,
        "coverage_if_safe_v2_applied": {
            "master_rows": MASTER_ROWS,
            "base_with_family": BASE_WITH_FAMILY,
            "base_with_family_pct": round(100.0 * BASE_WITH_FAMILY / MASTER_ROWS, 2),
            "safe_v2_rows_added": coverage_added,
            "with_family_if_applied": with_family_if,
            "with_family_pct_if_applied": with_family_pct,
            "without_family_if_applied": MASTER_ROWS - with_family_if,
            "note": "Projected only — SAFE-v2 not applied to master.",
        },
        "notes": [
            "Built from CLEAN by dropping all 406 rigor fails plus any residual "
            "cylinder-head / CYL HD / HEAD GASKET → Transmission (incl. Transmission bearings/seals/gasket).",
            "Prior CLEAN hard holds (gasket set→Transmission, trans asm→Literature, air valve→Steering) "
            "re-verified at zero.",
            "Does not apply aim_master. Jerome re-permission required before any apply.",
        ],
    }

    OUT_SUM.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Markdown verify note — plain English
    md = f"""# SAFE-v2 verify — 2026-10-07

## Verdict

{verdict}

**Apply permission earned?** No. {apply_sentence}

## Counts

| Piece | Rows |
|---|---:|
| CLEAN in | {n_clean:,} |
| Rigor fails excluded | {n_excl_fail:,} (file had {n_fail_file:,}) |
| Extra cyl-head→Transmission beyond those fails | {n_excl_extra:,} |
| SAFE-v2 out | **{n_safe:,}** |
| Of which rigor-pass (described / commodity) | {n_pass_in_safe:,} |
| Of which rigor-inconclusive (blank desc) | {n_inc_in_safe:,} |

Projected coverage if applied (not applied): {with_family_if:,} / {MASTER_ROWS:,} = {with_family_pct}% with family (from base {BASE_WITH_FAMILY:,}).

## Zero-checks (must all be 0)

| Check | Count | Pass |
|---|---:|---|
| GASKET; CYL HD / head-gasket / ENG-gasket desc → Transmission | {zero_checks['cyl_hd_gasket_desc_to_transmission']['n']} | {'YES' if zero_checks['cyl_hd_gasket_desc_to_transmission']['pass'] else 'NO'} |
| Cylinder head gasket path → Transmission | {zero_checks['cyl_hd_gasket_path_to_transmission']['n']} | {'YES' if zero_checks['cyl_hd_gasket_path_to_transmission']['pass'] else 'NO'} |
| Gasket set → Transmission | {zero_checks['gasket_set_to_transmission']['n']} | {'YES' if zero_checks['gasket_set_to_transmission']['pass'] else 'NO'} |
| Transmission assembly → Literature Marketing | {zero_checks['trans_asm_to_literature']['n']} | {'YES' if zero_checks['trans_asm_to_literature']['pass'] else 'NO'} |
| Air valve → Steering | {zero_checks['air_valve_to_steering']['n']} | {'YES' if zero_checks['air_valve_to_steering']['pass'] else 'NO'} |
| Any propose_aim_l1 = Transmission left (info) | {n_trans} | — |

All hard zero-checks pass: **{'YES' if all_hard_zero else 'NO'}**.

## Honesty — description vs path

{honesty}

The earlier rigor run already showed ZKK cannot define AIM family at scale (one pure code). SAFE-v2 does not invent a ZKK fix; it only removes known fails and the cyl-head gasket sibling leak.

## Paths

- SAFE-v2 CSV: `{OUT_CSV}`
- Summary: `{OUT_SUM}`
- This note: `{OUT_MD}`

## What was not done

aim_master was not written. No dated release apply. Jerome's conditional apply permission from the CLEAN rigor FAIL is still not earned for an automatic apply.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print("CLEAN", n_clean)
    print("EXCL_FAIL", n_excl_fail)
    print("EXCL_EXTRA", n_excl_extra)
    print("SAFE_V2", n_safe)
    print("BLANK_DESC", blank_desc)
    print("INC_IN_SAFE", n_inc_in_safe)
    print("ZERO_ALL", all_hard_zero)
    print("PERMISSION", permission)
    for k, v in zero_checks.items():
        print(f"  {k}: n={v['n']} pass={v.get('pass')}")
    print("OUT", OUT_CSV)


if __name__ == "__main__":
    main()
