"""Shard A — tranche-1 quality spot-check. Read-only on master; writes findings only."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PROP = ISZE / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_2026-10-07.csv"
MASTER = ISZE / "01_data/00_derived/aim_master_v2.csv"
JP = ISZE / "01_data/00_derived/jp_codes_cache_20260920.csv"
OUT_MD = ISZE / "01_data/91_build/_aim_tranche1_findings_20261007.md"
OUT_JSON = ISZE / "01_data/91_build/_aim_tranche1_findings_20261007.json"

MASTER_N = 165310
WITH_FAMILY = 21045
TRUE_BLANK = 140138
UNKNOWN_MARKERS = 4129


def clean(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def main() -> None:
    prop = pd.read_csv(PROP, dtype=str)
    aim = pd.read_csv(MASTER, dtype=str, usecols=["part_number", "description"], low_memory=False)
    jp = pd.read_csv(JP, dtype=str, low_memory=False)

    pn_col = "part_number" if "part_number" in jp.columns else None
    desc_col = next(
        (c for c in ("description", "description_norm", "desc") if c in jp.columns),
        None,
    )
    jmap: dict[str, str] = {}
    if pn_col and desc_col:
        for p, d in zip(jp[pn_col].map(clean), jp[desc_col].map(clean)):
            if p and d:
                jmap[p] = d
                jmap[p.lstrip("0")] = d

    mmap = {
        clean(p): clean(d)
        for p, d in zip(aim["part_number"], aim["description"])
        if clean(p)
    }

    def resolve_desc(row) -> str:
        d = clean(row.get("description"))
        if d:
            return d
        pn = clean(row.get("part_number"))
        return mmap.get(pn) or mmap.get(pn.lstrip("0")) or jmap.get(pn) or jmap.get(pn.lstrip("0")) or ""

    prop["desc"] = [resolve_desc(r) for _, r in prop.iterrows()]
    desc_filled = int((prop["desc"] != "").sum())

    # Per-path aggregates
    path_rows = []
    for cat_path, g in prop.groupby("cat_path"):
        descs = g["desc"]
        path_rows.append(
            {
                "cat_path": cat_path,
                "propose_aim_l1": g["propose_aim_l1"].iloc[0],
                "propose_aim_l2": g["propose_aim_l2"].iloc[0],
                "propose_aim_l3": g["propose_aim_l3"].iloc[0],
                "n": int(len(g)),
                "agree_share": float(g["agree_share"].iloc[0]),
                "known_n": int(float(g["known_n"].iloc[0])),
                "confidence": g["confidence"].iloc[0],
                "with_desc": int((descs != "").sum()),
                "kw_eng": int(descs.str.contains(r"\bENG\b|ENGINE|HD OVERHAUL|HEAD OVERHAUL", case=False, regex=True).sum()),
                "kw_trans": int(descs.str.contains(r"\bTRANS\b|TRANSMISSION|GEARBOX", case=False, regex=True).sum()),
                "kw_lit": int(descs.str.contains(r"\bMANUAL\b|BOOK|CATALOG|LITERATURE|HANDBOOK", case=False, regex=True).sum()),
                "kw_asm": int(descs.str.contains(r"\bASM\b|ASSEMBLY", case=False, regex=True).sum()),
                "sample_desc": "; ".join([d for d in descs.head(20).tolist() if d][:5]),
            }
        )
    paths = pd.DataFrame(path_rows).sort_values("n", ascending=False)

    flags = []
    for r in paths.itertuples(index=False):
        reasons = []
        if "Gasket set" in r.cat_path and r.propose_aim_l1 == "Transmission" and r.kw_eng > 0:
            reasons.append(
                f"engine gasket language on {r.kw_eng} rows but family=Transmission "
                "(contradicts Jerome 2026-10-04 Engine > Gasket & Sealing > Gasket for ENG gasket sets)"
            )
        if r.propose_aim_l1 == "Literature Marketing" and r.kw_asm >= r.kw_lit:
            reasons.append(
                f"assembly/hardware language ({r.kw_asm}) at least as strong as literature language ({r.kw_lit})"
            )
        if "Transmission assembly" in r.cat_path and r.propose_aim_l1 != "Transmission":
            reasons.append(f"transmission-assembly catalogue path mapped to {r.propose_aim_l1}")
        if "Air valve" in r.cat_path and r.propose_aim_l1 == "Steering":
            reasons.append("air-system valves mapped to Steering — commercially doubtful")
        if "Clutch disc" in r.cat_path and float(r.agree_share) < 0.95:
            reasons.append(f"competitive clutch disc at only {r.agree_share:.0%} agreement")
        if "Relay / solenoid / fuse" in r.cat_path and float(r.agree_share) <= 0.90:
            reasons.append(f"relay/solenoid/fuse path at floor agreement {r.agree_share:.0%}")
        if float(r.agree_share) < 0.95 and r.n >= 1000:
            reasons.append(f"large volume ({r.n:,}) below 95% agreement")
        if reasons:
            flags.append({**r._asdict(), "reasons": reasons})

    flagged_paths = {f["cat_path"] for f in flags}
    flagged_rows = int(sum(f["n"] for f in flags))
    clean_rows = int(len(prop) - flagged_rows)

    # HIGH sample from unflagged paths — keyword consistency
    noun_family = [
        (r"BUMPER|PANEL|DOOR|MIRROR|FENDER|BONNET|HOOD", "Accident & Body"),
        (r"HEADLAMP|TAIL.?LAMP|\bLAMP\b|\bBULB\b|\bLENS\b", "Lighting"),
        (r"\bSWITCH\b|\bSENSOR\b|\bRELAY\b|HARNESS|CONTROL UNIT|\bECU\b", "Electrical"),
        (r"\bBRAKE\b|CALIPER|\bPAD\b|\bDISC\b|\bDRUM\b|\bSHOE\b", "Brakes"),
        (r"\bCLUTCH\b", "Clutch"),
    ]
    safe = prop[(prop["confidence"] == "HIGH") & (~prop["cat_path"].isin(flagged_paths))].copy()
    samp = safe.sample(min(40, len(safe)), random_state=7) if len(safe) else safe
    checked = 0
    misses = []
    for _, r in samp.iterrows():
        d = r["desc"].upper()
        if not d:
            continue
        for pat, fam in noun_family:
            if re.search(pat, d):
                checked += 1
                ok = r["propose_aim_l1"] == fam
                if fam == "Accident & Body" and r["propose_aim_l1"] == "Chassis Frame":
                    ok = True  # structure/bracket adjacency
                if "BRACKET" in d or "STAY" in d:
                    ok = True
                if not ok:
                    misses.append(
                        {
                            "part_number": r["part_number"],
                            "desc": r["desc"][:60],
                            "proposed": r["propose_aim_l1"],
                            "hint": fam,
                            "cat_path": r["cat_path"],
                        }
                    )
                break

    sample_miss_rate = (len(misses) / checked) if checked else None

    # Gasket split detail
    g = prop[prop["cat_path"] == "Repair parts > Gaskets / seals > Gasket set"]
    gd = g["desc"]
    gasket_eng = int(gd.str.contains(r"ENG|ENGINE|HD OVERHAUL|HEAD", case=False, regex=True).sum())
    gasket_trans = int(gd.str.contains(r"\bTRANS\b|GEARBOX", case=False, regex=True).sum())
    gasket_other = int(len(g) - gasket_eng - gasket_trans)

    after_with = WITH_FAMILY + len(prop)
    after_without = MASTER_N - after_with
    after_true_blank = TRUE_BLANK - len(prop)

    # Coverage if ONLY clean (unflagged) rows applied
    after_with_clean = WITH_FAMILY + clean_rows
    after_without_clean = MASTER_N - after_with_clean

    top_l1 = prop["propose_aim_l1"].value_counts().head(15).to_dict()
    by_conf = prop["confidence"].value_counts().to_dict()

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "shard": "A",
        "proposal_csv": str(PROP),
        "proposed_rows": int(len(prop)),
        "by_confidence": by_conf,
        "distinct_cat_paths": int(prop["cat_path"].nunique()),
        "descriptions_filled_after_jp_enrich": desc_filled,
        "descriptions_still_blank": int(len(prop) - desc_filled),
        "top_propose_aim_l1": top_l1,
        "flagged_paths": len(flags),
        "flagged_rows": flagged_rows,
        "unflagged_clean_rows": clean_rows,
        "high_sample_checked": checked,
        "high_sample_obvious_misses": len(misses),
        "high_sample_miss_rate": sample_miss_rate,
        "high_sample_misses": misses,
        "gasket_set_rows": int(len(g)),
        "gasket_eng_keyword": gasket_eng,
        "gasket_trans_keyword": gasket_trans,
        "gasket_other_or_unmatched": gasket_other,
        "coverage_if_full_tranche1_applied": {
            "with_family": after_with,
            "with_family_pct": round(100 * after_with / MASTER_N, 2),
            "without_family": after_without,
            "true_blank_remaining": after_true_blank,
            "unknown_markers_untouched": UNKNOWN_MARKERS,
        },
        "coverage_if_only_unflagged_applied": {
            "with_family": after_with_clean,
            "with_family_pct": round(100 * after_with_clean / MASTER_N, 2),
            "without_family": after_without_clean,
            "held_back_flagged_rows": flagged_rows,
        },
        "recommendation": "NO-GO on full tranche1 as written; GO on unflagged subset after Jerome eyes the flagged paths",
        "flags": [
            {
                "cat_path": f["cat_path"],
                "propose_aim_l1": f["propose_aim_l1"],
                "n": f["n"],
                "agree_share": f["agree_share"],
                "known_n": f["known_n"],
                "confidence": f["confidence"],
                "reasons": f["reasons"],
                "sample_desc": f["sample_desc"],
            }
            for f in flags
        ],
    }

    # Markdown for Jerome / parent
    lines = []
    lines.append("# Tranche-1 AIM proposal — quality findings (2026-10-07)")
    lines.append("")
    lines.append("Shard A. Read-only check. **No release applied.**")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        "**No-go on the full 49,208-row proposal as written.** "
        f"About **{flagged_rows:,} rows ({100*flagged_rows/len(prop):.0f}%)** sit on catalogue paths that look commercially wrong or conflict with a decision you already made. "
        f"The other **{clean_rows:,} rows** look ready once you have accepted the method."
    )
    lines.append("")
    lines.append("## What the proposal is")
    lines.append("")
    lines.append(
        f"It fills true blanks where the catalogue path already points to one AIM family "
        f"on at least 90% of known examples (at least five known parts). "
        f"**{by_conf.get('HIGH', 0):,}** HIGH (≥95% agreement), **{by_conf.get('MED_HIGH', 0):,}** MED_HIGH (90–95%). "
        f"Descriptions were blank on almost every proposal row in the CSV; after joining the master and the JP cache, "
        f"**{desc_filled:,}** of {len(prop):,} have a description for review."
    )
    lines.append("")
    lines.append("## Coverage if applied (master = 165,310)")
    lines.append("")
    lines.append("| Cut | With a family | Share | Still without |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| Today | {WITH_FAMILY:,} | {100*WITH_FAMILY/MASTER_N:.1f}% | {MASTER_N-WITH_FAMILY:,} |")
    lines.append(
        f"| Full tranche 1 as written | {after_with:,} | {100*after_with/MASTER_N:.1f}% | {after_without:,} |"
    )
    lines.append(
        f"| Only unflagged rows | {after_with_clean:,} | {100*after_with_clean/MASTER_N:.1f}% | {after_without_clean:,} |"
    )
    lines.append("")
    lines.append(
        f"Unknown / Unknown Review markers (**{UNKNOWN_MARKERS:,}**) are untouched either way. "
        f"True blanks left after a full apply: about **{after_true_blank:,}**."
    )
    lines.append("")
    lines.append("## Top proposed families (volume)")
    lines.append("")
    for fam, n in top_l1.items():
        lines.append(f"- {fam}: {n:,}")
    lines.append("")
    lines.append("## Paths that need your eyes (hold these back)")
    lines.append("")
    for f in sorted(flags, key=lambda x: -x["n"]):
        lines.append(
            f"### {f['cat_path']} → {f['propose_aim_l1']} "
            f"({f['n']:,} rows, {f['agree_share']:.0%} agree on {f['known_n']} known, {f['confidence']})"
        )
        for reason in f["reasons"]:
            lines.append(f"- {reason}")
        if f["sample_desc"]:
            lines.append(f"- Examples: {f['sample_desc']}")
        lines.append("")

    lines.append("## HIGH sample on unflagged paths")
    lines.append("")
    if sample_miss_rate is None:
        lines.append("Not enough described rows in the sample to score.")
    else:
        lines.append(
            f"Keyword check on {checked} described HIGH rows from unflagged paths: "
            f"**{len(misses)} obvious mismatches** "
            f"({100*sample_miss_rate:.0f}% of those keyword-checked)."
        )
        if misses:
            lines.append("")
            for m in misses[:10]:
                lines.append(
                    f"- {m['part_number']} “{m['desc']}” → {m['proposed']} "
                    f"(description points nearer {m['hint']})"
                )
    lines.append("")
    lines.append("## Ready vs not")
    lines.append("")
    lines.append("| Bucket | Rows | Call |")
    lines.append("|---|---:|---|")
    lines.append(f"| Unflagged paths | {clean_rows:,} | Ready to approve as a first release, if you want the method |")
    lines.append(f"| Flagged paths | {flagged_rows:,} | Needs Jerome eyes — do not apply as proposed |")
    lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append(
        "1. **Do not approve the full tranche-1 file.** The gasket-set block alone (~6.5k rows) "
        "would put engine overhaul gasket sets back under Transmission, which you already corrected on 4 Oct."
    )
    lines.append(
        "2. **Approve only the unflagged subset** (or ask for a cleaned re-cut that drops the flagged paths "
        "and splits gasket sets by ENG vs TRANS in the description)."
    )
    lines.append(
        "3. Still leaves ~90k true blanks after even a full apply — that is the next work, not this check."
    )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- Proposal (unchanged): `{PROP}`")
    lines.append(f"- This note: `{OUT_MD}`")
    lines.append(f"- Machine summary: `{OUT_JSON}`")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in (
        "proposed_rows", "flagged_paths", "flagged_rows", "unflagged_clean_rows",
        "high_sample_checked", "high_sample_obvious_misses", "high_sample_miss_rate",
        "recommendation", "coverage_if_full_tranche1_applied", "coverage_if_only_unflagged_applied",
        "gasket_set_rows", "gasket_eng_keyword", "gasket_trans_keyword",
    )}, indent=2))
    print("WROTE", OUT_MD)
    print("WROTE", OUT_JSON)


if __name__ == "__main__":
    main()
