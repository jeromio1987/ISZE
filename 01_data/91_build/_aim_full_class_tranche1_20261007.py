"""Tranche 1 toward full AIM classification — proposal only, no apply.

Jerome 2026-10-07: all parts need a full AIM family. The master has ~144k rows
without a real family. This cut proposes families for blanks where the catalogue
path already maps to one AIM family at >=90% agreement on parts that already
carry a family (n>=5 known examples).

Does not write aim_master_v2 or any release CSV. Writes a proposal + summary
under 01_data/00_derived/_releases/ for review.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
MASTER = DER / "aim_master_v2.csv"
OUT_PROP = REL / "next_release_proposal_full_class_tranche1_catmap_2026-10-07.csv"
OUT_SUM = REL / "next_release_proposal_full_class_tranche1_catmap_2026-10-07.summary.json"

MARKERS = {"", "Unknown", "Unknown Review", "nan", "None"}


def clean(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def resolved_family(r) -> str:
    for c in (clean(r.get("aim_l1_fixed")), clean(r.get("aim_l1"))):
        if c and c not in MARKERS:
            return c
    return ""


def main() -> None:
    aim = pd.read_csv(MASTER, dtype=str, low_memory=False)
    aim["family"] = [resolved_family(r) for _, r in aim.iterrows()]
    for c in ("cat_l1", "cat_l2", "cat_l3", "aim_l2", "aim_l3", "aim_l2_fixed", "aim_l3_fixed"):
        if c not in aim.columns:
            aim[c] = ""
    aim["cat_path"] = (
        aim["cat_l1"].map(clean) + " > " + aim["cat_l2"].map(clean) + " > " + aim["cat_l3"].map(clean)
    )

    known = aim[aim["family"] != ""].copy()
    # True blanks only — leave deliberate Unknown / Unknown Review for a separate clear-up
    blank = aim[
        (aim["family"] == "")
        & (~aim["aim_l1"].map(clean).isin(MARKERS - {""}))
        & (~aim["aim_l1_fixed"].map(clean).isin(MARKERS - {""}))
    ].copy()
    marked = aim[aim["aim_l1"].map(clean).isin(MARKERS - {""}) | aim["aim_l1_fixed"].map(clean).isin(MARKERS - {""})]

    # Dominant AIM L1 per catalogue path; also pick the modal L2/L3 among that L1
    rows = []
    for cat_path, g in known.groupby("cat_path"):
        if len(g) < 5:
            continue
        vc = g["family"].value_counts()
        fam = vc.index[0]
        share = float(vc.iloc[0] / len(g))
        if share < 0.90:
            continue
        sub = g[g["family"] == fam]
        l2 = clean(sub["aim_l2_fixed"].mode().iloc[0]) if len(sub["aim_l2_fixed"].mode()) else ""
        if not l2:
            l2 = clean(sub["aim_l2"].mode().iloc[0]) if len(sub["aim_l2"].mode()) else ""
        l3 = clean(sub["aim_l3"].mode().iloc[0]) if len(sub["aim_l3"].mode()) else ""
        rows.append(
            {
                "cat_path": cat_path,
                "propose_aim_l1": fam,
                "propose_aim_l2": l2,
                "propose_aim_l3": l3,
                "known_n": int(len(g)),
                "agree_share": round(share, 4),
            }
        )
    maps = pd.DataFrame(rows).set_index("cat_path")

    prop = blank[blank["cat_path"].isin(maps.index)].copy()
    prop = prop.merge(maps, left_on="cat_path", right_index=True, how="left")
    prop["method"] = "cat_path_unanimity_ge90_n5"
    prop["confidence"] = prop["agree_share"].map(
        lambda x: "HIGH" if x >= 0.95 else "MED_HIGH"
    )
    keep = [
        "part_number",
        "description",
        "cat_l1",
        "cat_l2",
        "cat_l3",
        "cat_path",
        "propose_aim_l1",
        "propose_aim_l2",
        "propose_aim_l3",
        "known_n",
        "agree_share",
        "method",
        "confidence",
        "aim_l1",
        "aim_l1_fixed",
        "l12m_billed_eur" if "l12m_billed_eur" in prop.columns else None,
    ]
    keep = [c for c in keep if c and c in prop.columns]
    out = prop[keep].sort_values(["propose_aim_l1", "part_number"])
    REL.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PROP, index=False)

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "bar": "all parts need a full AIM family (Jerome 2026-10-07)",
        "master_rows": int(len(aim)),
        "with_family": int((aim["family"] != "").sum()),
        "without_family": int((aim["family"] == "").sum()),
        "true_blank_rows": int(len(blank)),
        "unknown_marker_rows": int(len(marked)),
        "tranche1_proposed_rows": int(len(out)),
        "tranche1_share_of_true_blank": round(len(out) / max(len(blank), 1), 4),
        "distinct_cat_maps": int(len(maps)),
        "by_confidence": out["confidence"].value_counts().to_dict() if len(out) else {},
        "top_propose_l1": out["propose_aim_l1"].value_counts().head(15).to_dict() if len(out) else {},
        "proposal_csv": str(OUT_PROP),
        "apply": "NO — proposal only. Wait for Jerome OK before a dated release.",
        "still_true_blank_after_tranche1": int(len(blank) - len(out)),
        "notes": [
            "Almost all blanks already have a catalogue node; this maps catalogue path to AIM family.",
            "Remaining blanks need description rules, EQ-Hit, or hand review.",
            "Does not touch Unknown / Unknown Review — those stay a separate clear-up.",
        ],
    }
    OUT_SUM.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
