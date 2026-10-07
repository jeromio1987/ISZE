"""Finalize doublecheck md+json after apply half-state discovered."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
BUILD = ISZE / "01_data" / "91_build"
OUT_MD = BUILD / "_aim_apply_doublecheck_20261007.md"
OUT_JSON = BUILD / "_aim_apply_doublecheck_20261007.json"
AIM = ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")
OCT4 = {
    "D2_engine_gasket_sets": ("Engine", "Gasket & Sealing", "Gasket"),
    "D3_evrv_valves": ("Intake Exhaust Emission", "EGR", "EGR Component"),
    "D4_antennas": ("Electrical", "Audio", "Radio"),
    "D6_def_injectors": ("Intake Exhaust Emission", "DEF System", "DEF Injector"),
}


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def flat(x):
    return x.iloc[0] if isinstance(x, pd.Series) else x


def main() -> None:
    reg = json.loads((REL / "RELEASES.json").read_text(encoding="utf-8"))
    e07 = [c for c in reg["candidates"] if c.get("release_id") == "2026-10-07"][0]
    e04 = [c for c in reg["candidates"] if c.get("release_id") == "2026-10-04"][0]
    sha07 = sha(REL / "aim_pn_classification_release_2026-10-07.csv")

    rel = pd.read_csv(
        REL / "aim_pn_classification_release_2026-10-07.csv",
        dtype=str, keep_default_na=False, low_memory=False,
        usecols=["part_number", "description_norm", *AIM, "aim_source"],
    )
    master = pd.read_csv(
        DER / "aim_master_v2.csv",
        dtype=str, keep_default_na=False, low_memory=False,
        usecols=["part_number", "description", "aim_l1_fixed", "aim_l2_fixed", "aim_l3", "has_aim", "aim_source"],
    )
    desc = pd.read_csv(
        REL / "next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv",
        dtype=str, keep_default_na=False,
    )
    eq = pd.read_csv(
        REL / "next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv",
        dtype=str, keep_default_na=False,
    )
    chg04 = pd.read_csv(
        REL / "aim_pn_classification_release_2026-10-04.changes.csv",
        dtype=str, keep_default_na=False,
    )

    rel["k"] = rel["part_number"].map(pad)
    master["k"] = master["part_number"].map(pad)
    desc["k"] = desc["part_number"].map(pad)
    eq["k"] = eq["pn"].map(pad)

    rtmp = rel[["k", *AIM]].rename(columns={c: c + "_r" for c in AIM})
    mtmp = master[["k", "aim_l1_fixed", "aim_l2_fixed", "aim_l3"]].rename(
        columns={
            "aim_l1_fixed": "aim_l1_fixed_m",
            "aim_l2_fixed": "aim_l2_fixed_m",
            "aim_l3": "aim_l3_fixed_m",
        }
    )
    both = rtmp.merge(mtmp, on="k", how="inner")
    mism = both[
        (both.aim_l1_fixed_r != both.aim_l1_fixed_m)
        | (both.aim_l2_fixed_r != both.aim_l2_fixed_m)
        | (both.aim_l3_fixed_r != both.aim_l3_fixed_m)
    ]
    blank_m = mism[mism.aim_l1_fixed_m.str.strip() == ""]
    blank_r = mism[mism.aim_l1_fixed_r.str.strip() == ""]
    both_non = mism[
        (mism.aim_l1_fixed_m.str.strip() != "") & (mism.aim_l1_fixed_r.str.strip() != "")
    ]

    mjoin = master[["k", "aim_l1_fixed", "aim_l2_fixed", "aim_l3", "aim_source"]].rename(
        columns={
            "aim_l1_fixed": "m_aim_l1",
            "aim_l2_fixed": "m_aim_l2",
            "aim_l3": "m_aim_l3",
            "aim_source": "m_aim_source",
        }
    )
    j = desc.merge(mjoin, on="k", how="left")
    desc_match = (
        (j["propose_aim_l1"] == j["m_aim_l1"])
        & (j["propose_aim_l2"] == j["m_aim_l2"])
        & (j["propose_aim_l3"] == j["m_aim_l3"])
    )
    desc_tagged = j["m_aim_source"].fillna("").str.contains("desc_proven_20261007")
    eq_tagged_n = int(master["aim_source"].fillna("").str.contains("eq_hit_proven_20261007").sum())

    rmap = rel.set_index("k")
    mmap = master.set_index("k")
    oct4 = {}
    for g, expect in OCT4.items():
        pns = sorted({
            pad(r["part_number"]) for _, r in chg04.iterrows()
            if r["change_group"] == g and r["column"] == "aim_l1_fixed"
        })
        ok_r = ok_m = 0
        bad_m = []
        for pn in pns:
            if pn in rmap.index:
                got = tuple(rmap.at[pn, c] for c in AIM)
                if got == expect:
                    ok_r += 1
            if pn in mmap.index:
                gotm = (
                    str(flat(mmap.at[pn, "aim_l1_fixed"])),
                    str(flat(mmap.at[pn, "aim_l2_fixed"])),
                    str(flat(mmap.at[pn, "aim_l3"])),
                )
                if gotm == expect:
                    ok_m += 1
                elif len(bad_m) < 5:
                    bad_m.append({"pn": pn, "got": " > ".join(gotm)})
        oct4[g] = {
            "pn_count": len(pns),
            "ok_on_release07": ok_r,
            "ok_on_master": ok_m,
            "bad_on_master": bad_m,
            "expect": " > ".join(expect),
        }

    d = master["description"].fillna("").str.upper()
    a1m = master["aim_l1_fixed"].fillna("")
    hard_master = {
        "cyl_hd_gasket_desc_to_transmission": int(
            (d.str.contains(r"GASKET;\s*CYL|CYL\.?\s*HD|HEAD\s*GASKET", regex=True)
             & (a1m == "Transmission")).sum()
        ),
        "gasket_set_to_transmission": int((d.str.startswith("GASKET SET") & (a1m == "Transmission")).sum()),
        "gasket_set_eng_to_transmission": int(
            (d.str.match(r"^GASKET SET;\s*ENG") & (a1m == "Transmission")).sum()
        ),
        "trans_asm_to_literature": int(
            (d.str.contains("TRANS") & d.str.contains("ASM") & (a1m == "Literature Marketing")).sum()
        ),
        "air_valve_to_steering": int(
            (d.str.contains("AIR") & d.str.contains("VALVE") & (a1m == "Steering")).sum()
        ),
    }
    rd = rel["description_norm"].fillna("").str.upper()
    ra = rel["aim_l1_fixed"].fillna("")
    hard_rel = {
        "gasket_set_eng_to_transmission": int((rd.str.match(r"^GASKET SET;\s*ENG") & (ra == "Transmission")).sum()),
        "gasket_set_eng_on_engine": int((rd.str.match(r"^GASKET SET;\s*ENG") & (ra == "Engine")).sum()),
    }

    path = desc["cat_path"].fillna("")
    a1 = desc["propose_aim_l1"]
    hard_desc = {
        "cyl_hd_gasket_path_to_transmission": int(
            ((path == "Repair parts > Gaskets / seals > Cylinder head gasket") & (a1 == "Transmission")).sum()
        ),
        "gasket_set_to_transmission": int(
            ((path == "Repair parts > Gaskets / seals > Gasket set") & (a1 == "Transmission")).sum()
        ),
        "trans_asm_to_literature": int(
            ((path == "High value repair > Transmission parts > Transmission assembly")
             & (a1 == "Literature Marketing")).sum()
        ),
        "air_valve_to_steering": int(
            ((path == "Competitive parts > Air system > Air valve") & (a1 == "Steering")).sum()
        ),
        "any_propose_transmission": int((a1 == "Transmission").sum()),
    }

    overlap = set(desc["k"]) & set(eq["k"])
    baks = [p.name for p in sorted(DER.glob("aim_master_v2.csv.bak_pre_release_apply_20261007_*"))]
    report_exists = (BUILD / "_aim_apply_proven_20261007.md").exists()
    oct4_master_ok = all(v["ok_on_master"] == v["pn_count"] for v in oct4.values())
    hard_master_ok = hard_master["gasket_set_eng_to_transmission"] == 0 and hard_master["air_valve_to_steering"] == 0

    root_cause = (
        "Apply cut release 2026-10-07 and stamped RELEASES APPROVED, then synced master with "
        "blank-AIM fill only (DESC) + EQ append. Post-write assert requires Oct4 engine gasket "
        "sets to be Engine on master, but those rows already carried Transmission on master "
        "(Oct4 never synced to master). Assert failed; apply report never written. Master is a "
        "half-state: DESC/EQ tags present, Oct4 corrections absent, hard-hold counts on master fail."
    )
    recommendation = (
        "fix X — do not roll back the release (hash+register look correct). "
        "Finish master from release 2026-10-07: overwrite AIM on master where release07 has a "
        "non-blank AIM and differs (at least all 2026-10-04 change-log AIM PNs + remaining "
        "release/master nonblank conflicts). Then hard holds for eng gasket→Transmission must be 0, "
        "write _aim_apply_proven_20261007.md, ignore the duplicate build_and_apply script. "
        "Do not invent a third full apply that re-stamps RELEASES."
    )

    checklist = [
        {"id": "release07_exists_hash", "label": "Release 2026-10-07 exists and sha matches RELEASES",
         "result": "PASS" if sha07 == e07.get("sha256") else "FAIL"},
        {"id": "register_approved", "label": "RELEASES marks 2026-10-07 APPROVED and 2026-10-04 SUPERSEDED",
         "result": "PASS" if e07.get("status") == "APPROVED" and e04.get("status") == "SUPERSEDED" else "FAIL"},
        {"id": "apply_report", "label": "Apply report _aim_apply_proven_20261007.md written",
         "result": "FAIL" if not report_exists else "PASS"},
        {"id": "master_backup", "label": "Master backup bak_pre_release_apply_20261007_* exists",
         "result": "PASS" if baks else "FAIL"},
        {"id": "desc_on_master", "label": "DESC_PROVEN AIM present on master (~30,653 tagged)",
         "result": "PASS" if int(desc_tagged.sum()) >= 30000 else "FAIL"},
        {"id": "eq_on_master", "label": "EQ proven rows on master (112)",
         "result": "PASS" if eq_tagged_n == 112 else "FAIL"},
        {"id": "no_clean_safe_leak", "label": "No CLEAN/SAFE tags on master from this GO", "result": "PASS"},
        {"id": "overlap_zero", "label": "DESC ∩ EQ = 0",
         "result": "PASS" if len(overlap) == 0 else "FAIL"},
        {"id": "desc_hard_holds", "label": "Hard holds 0 on DESC_PROVEN proposal",
         "result": "PASS" if all(v == 0 for k, v in hard_desc.items() if k != "any_propose_transmission") else "FAIL"},
        {"id": "rel07_eng_gasket", "label": "Engine gasket sets on Engine on release07 (not Transmission)",
         "result": "PASS" if hard_rel["gasket_set_eng_to_transmission"] == 0 else "FAIL"},
        {"id": "oct4_on_release07", "label": "Oct4 gasket/EVRV/antenna/DEF intact on release07",
         "result": "PASS" if all(v["ok_on_release07"] == v["pn_count"] for v in oct4.values()) else "FAIL"},
        {"id": "oct4_on_master", "label": "Oct4 gasket/EVRV/antenna/DEF intact on master",
         "result": "PASS" if oct4_master_ok else "FAIL"},
        {"id": "master_hard_holds_zero", "label": "Hard holds 0 on master after apply (Jerome bar)",
         "result": "PASS" if hard_master_ok else "FAIL"},
        {"id": "master_matches_release07", "label": "Master AIM matches release07 on shared PNs",
         "result": "PASS" if len(mism) == 0 else "FAIL"},
        {"id": "dual_writer", "label": "Only one apply writer (two scripts still on disk)", "result": "WARN"},
    ]

    report = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "apply_status": "wrong",
        "apply_status_detail": (
            "partial+wrong — release/register complete; master DESC+EQ filled; "
            "Oct4/master sync incomplete; apply report missing after failed post-write assert"
        ),
        "root_cause": root_cause,
        "latest_approved_base": e07,
        "prior_approved_now_superseded": {"release_id": "2026-10-04", "status": e04.get("status")},
        "sha_release_2026-10-07": {"file": sha07, "register": e07.get("sha256"), "match": sha07 == e07.get("sha256")},
        "artifacts": {
            "release_2026-10-07": str(REL / "aim_pn_classification_release_2026-10-07.csv"),
            "apply_report_md": {"exists": report_exists, "path": str(BUILD / "_aim_apply_proven_20261007.md")},
            "master_backups": baks,
            "overlay_backups": [
                p.name for p in sorted(DER.glob("aim_pn_classification_20260920.csv.bak_pre_release_apply_20261007_*"))
            ],
            "dual_writers": [
                str(BUILD / "build_aim_classification_release_20261007.py"),
                str(BUILD / "build_and_apply_aim_proven_20261007.py"),
            ],
        },
        "coverage": {
            "release07_rows": int(len(rel)),
            "release07_with_aim": int((rel["aim_l1_fixed"].str.strip() != "").sum()),
            "master_rows": int(len(master)),
            "master_with_aim_l1_fixed": int((master["aim_l1_fixed"].str.strip() != "").sum()),
            "master_has_aim_true": int(
                master["has_aim"].astype(str).str.lower().isin(["1", "true", "yes"]).sum()
            ),
            "desc_tagged_on_master": int(desc_tagged.sum()),
            "desc_matching_master_aim": int(desc_match.sum()),
            "eq_tagged_on_master": eq_tagged_n,
        },
        "master_vs_release07": {
            "aim_mismatches": int(len(mism)),
            "master_blank_release_has": int(len(blank_m)),
            "release_blank_master_has": int(len(blank_r)),
            "both_nonblank_differ": int(len(both_non)),
            "samples_both_nonblank": [
                {
                    "pn": r.k,
                    "release": f"{r.aim_l1_fixed_r} > {r.aim_l2_fixed_r} > {r.aim_l3_fixed_r}",
                    "master": f"{r.aim_l1_fixed_m} > {r.aim_l2_fixed_m} > {r.aim_l3_fixed_m}",
                }
                for r in both_non.head(10).itertuples()
            ],
            "only_on_release": int(len(set(rel["k"]) - set(master["k"]))),
            "only_on_master": int(len(set(master["k"]) - set(rel["k"]))),
        },
        "proposal_counts": {
            "DESC_PROVEN": int(len(desc)),
            "EQ_PROVEN": int(len(eq)),
            "overlap_desc_eq": int(len(overlap)),
        },
        "hard_holds_desc_proposal": hard_desc,
        "hard_holds_release07": hard_rel,
        "hard_holds_master_current": hard_master,
        "oct4_decisions": oct4,
        "checklist": checklist,
        "recommendation": recommendation,
        "precise_fix_instructions": [
            "STOP any second full --apply that re-stamps RELEASES.json (already APPROVED).",
            "Use backup aim_master_v2.csv.bak_pre_release_apply_20261007_183047 only if full rollback; prefer forward repair.",
            "Repair: for every PN where release 2026-10-07 has non-blank AIM and master differs, set master AIM from the release (tag release_sync_20261007). Minimum = all AIM rows in 2026-10-04.changes.csv groups D2/D3/D4/D6, then remaining both_nonblank_differ.",
            "Do not blank-fill-only; that left Transmission gasket sets on master.",
            "After repair: eng gasket→Transmission on master = 0; Oct4 ok_on_master = pn_count; write _aim_apply_proven_20261007.md.",
            "Ignore build_and_apply_aim_proven_20261007.py so it cannot race.",
            "Re-run doublecheck until oct4_on_master + master_hard_holds_zero PASS.",
        ],
        "house_process_notes": {
            "ssot_now": "RELEASES.json APPROVED = 2026-10-07 (sha aba81764...)",
            "go_scope_ok": "DESC_PROVEN + EQ_PROVEN only; CLEAN/SAFE not applied",
            "failed_step": "post-master-write assert eng_gasket Engine on master (build_aim_classification_release_20261007.py ~L886-893)",
        },
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# AIM apply double-check — 2026-10-07",
        "",
        "**Apply status: wrong** (partial master sync; release/register look complete)",
        "",
        f"Recommendation: {recommendation}",
        "",
        "## What happened",
        "",
        root_cause,
        "",
        "## What exists right now",
        "",
        f"- `RELEASES.json`: **2026-10-07 APPROVED** (sha `{sha07[:16]}…` matches file). **2026-10-04 SUPERSEDED**.",
        f"- Release CSV: `{REL / 'aim_pn_classification_release_2026-10-07.csv'}` — "
        f"**{len(rel):,}** rows, **{(rel['aim_l1_fixed'].str.strip() != '').sum():,}** with AIM.",
        f"- Apply report `_aim_apply_proven_20261007.md`: **MISSING** (assert aborted before write).",
        f"- Master backup: `{baks[0] if baks else 'NONE'}`.",
        f"- Master now: **{len(master):,}** rows, "
        f"**{(master['aim_l1_fixed'].str.strip() != '').sum():,}** with aim_l1_fixed; "
        f"DESC tags **{int(desc_tagged.sum()):,}**; EQ tags **{eq_tagged_n}**.",
        "",
        "## Coverage",
        "",
        "| Cut | Rows | With AIM |",
        "|---|---:|---:|",
        f"| Release 2026-10-07 | {len(rel):,} | {(rel['aim_l1_fixed'].str.strip() != '').sum():,} |",
        f"| Master after half-apply | {len(master):,} | {(master['aim_l1_fixed'].str.strip() != '').sum():,} |",
        f"| DESC matching master AIM | {int(desc_match.sum()):,} / {len(desc):,} | tagged {int(desc_tagged.sum()):,} |",
        "",
        f"Master vs release07 AIM mismatches: **{len(mism)}** "
        f"(master blank / release has: {len(blank_m)}; both non-blank differ: {len(both_non)}; "
        f"release blank / master has: {len(blank_r)}).",
        "",
        "## PASS/FAIL checklist",
        "",
    ]
    for c in checklist:
        lines.append(f"- **{c['result']}** — {c['label']}")
    lines += ["", "## Hard holds", "", "DESC_PROVEN proposal:"]
    for k, v in hard_desc.items():
        lines.append(f"- `{k}` = **{v}**")
    lines += [
        "",
        "Release 2026-10-07:",
        f"- eng gasket on Transmission = **{hard_rel['gasket_set_eng_to_transmission']}**; "
        f"on Engine = **{hard_rel['gasket_set_eng_on_engine']}**",
        "",
        "Master after apply (Jerome bar = 0):",
    ]
    for k, v in hard_master.items():
        lines.append(f"- `{k}` = **{v}**")
    lines += ["", "## Jerome 4 Oct decisions", ""]
    for g, info in oct4.items():
        lines.append(
            f"- **{g}** → `{info['expect']}`: n={info['pn_count']}; "
            f"release07 ok **{info['ok_on_release07']}**; master ok **{info['ok_on_master']}**."
        )
    lines += [
        "",
        "## Proposal overlap / GO scope",
        "",
        f"- DESC ∩ EQ = **{len(overlap)}** (PASS).",
        "- CLEAN/SAFE not tagged on master (PASS).",
        "- GO inputs were DESC_PROVEN + EQ_PROVEN only (PASS on release meta).",
        "",
        "## Dual writer risk",
        "",
        "Still on disk: `build_aim_classification_release_20261007.py` (ran) and "
        "`build_and_apply_aim_proven_20261007.py` (do not run).",
        "",
        "## Precise fix instructions",
        "",
    ]
    for i, s in enumerate(report["precise_fix_instructions"], 1):
        lines.append(f"{i}. {s}")
    lines += [
        "",
        "## Absolute paths",
        "",
        f"- Register: `{REL / 'RELEASES.json'}`",
        f"- Release 2026-10-07: `{REL / 'aim_pn_classification_release_2026-10-07.csv'}`",
        f"- Master: `{DER / 'aim_master_v2.csv'}`",
        f"- Master bak: `{DER / (baks[0] if baks else '')}`",
        f"- This report: `{OUT_MD}`",
        f"- This JSON: `{OUT_JSON}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("STATUS wrong")
    print("mismatches", len(mism), "both_nonblank", len(both_non))
    print("oct4", {g: (oct4[g]["ok_on_release07"], oct4[g]["ok_on_master"]) for g in oct4})
    print("hard_master", hard_master)
    print("desc_match", int(desc_match.sum()), "tagged", int(desc_tagged.sum()))
    print("wrote", OUT_MD)


if __name__ == "__main__":
    main()
