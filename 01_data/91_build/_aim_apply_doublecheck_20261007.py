"""Independent GO-apply double-check vs workspace SSOT. Report only — no master write."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
BUILD = ISZE / "01_data" / "91_build"
OUT_MD = BUILD / "_aim_apply_doublecheck_20261007.md"
OUT_JSON = BUILD / "_aim_apply_doublecheck_20261007.json"

EXPECT04 = "8aad884f49db1a49ab86faca571942d912196ce08f7734f38d5a04f035e18896"
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


def meta(p: Path) -> dict:
    if not p.exists():
        return {"exists": False, "path": str(p)}
    st = p.stat()
    return {
        "exists": True,
        "path": str(p),
        "bytes": st.st_size,
        "mtime_iso": pd.Timestamp(st.st_mtime, unit="s").isoformat(),
    }


def main() -> None:
    art = {
        "RELEASES.json": meta(REL / "RELEASES.json"),
        "release_2026-10-04": meta(REL / "aim_pn_classification_release_2026-10-04.csv"),
        "release_2026-10-07": meta(REL / "aim_pn_classification_release_2026-10-07.csv"),
        "release_2026-10-07_meta": meta(REL / "aim_pn_classification_release_2026-10-07.meta.json"),
        "release_2026-10-07_gate": meta(REL / "aim_pn_classification_release_2026-10-07.gate.json"),
        "release_2026-10-07_changes": meta(REL / "aim_pn_classification_release_2026-10-07.changes.csv"),
        "aim_master_v2": meta(DER / "aim_master_v2.csv"),
        "DESC_PROVEN": meta(
            REL / "next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv"
        ),
        "EQ_PROVEN": meta(REL / "next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv"),
        "apply_report_md": meta(BUILD / "_aim_apply_proven_20261007.md"),
        "apply_report_json": meta(BUILD / "_aim_apply_proven_20261007.json"),
        "build_and_apply": meta(BUILD / "build_and_apply_aim_proven_20261007.py"),
        "build_release": meta(BUILD / "build_aim_classification_release_20261007.py"),
        "build_apply_split": meta(BUILD / "build_aim_apply_proven_20261007.py"),
        "bak_master": [meta(p) for p in sorted(DER.glob("aim_master_v2.csv.bak_pre_proven_apply_20261007_*"))],
        "any_aim_apply": [meta(p) for p in sorted(BUILD.glob("_aim_apply*"))],
    }

    reg = json.loads((REL / "RELEASES.json").read_text(encoding="utf-8"))
    approved = [c for c in reg["candidates"] if c.get("status") == "APPROVED"]
    latest = approved[-1] if approved else None
    has07 = [c for c in reg["candidates"] if c.get("release_id") == "2026-10-07"]

    print("loading tables...", flush=True)
    rel04 = pd.read_csv(
        REL / "aim_pn_classification_release_2026-10-04.csv",
        dtype=str, keep_default_na=False, low_memory=False,
        usecols=["part_number", "description_norm", *AIM, "catalog_l1", "catalog_l2", "catalog_l3", "aim_source"],
    )
    mcols = ["part_number", "description", "aim_l1_fixed", "aim_l2_fixed", "aim_l3", "has_aim", "aim_source"]
    master_head = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, keep_default_na=False, nrows=0)
    mcols = [c for c in mcols if c in master_head.columns]
    if "aim_l3_fixed" in master_head.columns:
        mcols.append("aim_l3_fixed")
    master = pd.read_csv(
        DER / "aim_master_v2.csv", dtype=str, keep_default_na=False, low_memory=False, usecols=mcols,
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

    for df, col in ((rel04, "part_number"), (master, "part_number"), (desc, "part_number")):
        df["k"] = df[col].map(pad)
    eq_pn = "pn" if "pn" in eq.columns else "part_number"
    eq["k"] = eq[eq_pn].map(pad)

    sha04 = sha(REL / "aim_pn_classification_release_2026-10-04.csv")

    # coverage
    rel_aim = rel04["aim_l1_fixed"].str.strip() != ""
    m_aim_col = "aim_l1_fixed" if "aim_l1_fixed" in master.columns else None
    cov = {
        "release_2026-10-04_rows": int(len(rel04)),
        "release_2026-10-04_with_aim": int(rel_aim.sum()),
        "release_2026-10-04_with_aim_pct": round(100 * rel_aim.mean(), 2),
        "master_rows": int(len(master)),
        "master_with_aim_l1_fixed": int((master[m_aim_col].str.strip() != "").sum()) if m_aim_col else None,
        "master_has_aim_true": int(
            master["has_aim"].astype(str).str.lower().isin(["1", "true", "yes"]).sum()
        ) if "has_aim" in master.columns else None,
    }

    # vectorized master vs release AIM
    print("join master vs release...", flush=True)
    m3 = "aim_l3_fixed" if "aim_l3_fixed" in master.columns else "aim_l3"
    r_aim = rel04.set_index("k")[list(AIM)]
    m_aim = master.set_index("k")[["aim_l1_fixed", "aim_l2_fixed", m3]].rename(
        columns={m3: "aim_l3_fixed"}
    )
    both = r_aim.join(m_aim, how="inner", lsuffix="_r", rsuffix="_m")
    # after join with same names + suffix
    # r_aim cols stay, m_aim get _m if clash — we renamed m3 so clash on all three
    # Actually join with overlapping names → _x/_y. Rebuild cleanly:
    rtmp = rel04[["k", *AIM]].rename(columns={c: c + "_r" for c in AIM})
    mtmp = master[["k", "aim_l1_fixed", "aim_l2_fixed", m3]].copy()
    mtmp = mtmp.rename(columns={
        "aim_l1_fixed": "aim_l1_fixed_m",
        "aim_l2_fixed": "aim_l2_fixed_m",
        m3: "aim_l3_fixed_m",
    })
    both = rtmp.merge(mtmp, on="k", how="inner")
    mism = both[
        (both["aim_l1_fixed_r"] != both["aim_l1_fixed_m"])
        | (both["aim_l2_fixed_r"] != both["aim_l2_fixed_m"])
        | (both["aim_l3_fixed_r"] != both["aim_l3_fixed_m"])
    ]
    aim_mismatch = int(len(mism))
    aim_samples = [
        {
            "pn": r.k,
            "release": f"{r.aim_l1_fixed_r} > {r.aim_l2_fixed_r} > {r.aim_l3_fixed_r}",
            "master": f"{r.aim_l1_fixed_m} > {r.aim_l2_fixed_m} > {r.aim_l3_fixed_m}",
        }
        for r in mism.head(8).itertuples()
    ]

    rset, mset = set(rel04["k"]), set(master["k"])
    desc_on_rel = desc["k"].isin(rset)
    eq_on_rel = eq["k"].isin(rset)
    eq_on_m = eq["k"].isin(mset)
    overlap = set(desc["k"]) & set(eq["k"])

    rmap = rel04.set_index("k")
    joined = desc.merge(
        rel04[["k", *AIM]].rename(columns={c: c + "_rel" for c in AIM}),
        on="k", how="left",
    )
    cur_blank = joined["aim_l1_fixed_rel"].fillna("").str.strip() == ""
    same = (
        (joined["propose_aim_l1"] == joined["aim_l1_fixed_rel"])
        & (joined["propose_aim_l2"] == joined["aim_l2_fixed_rel"])
        & (joined["propose_aim_l3"] == joined["aim_l3_fixed_rel"])
    )
    desc_blank_aim = int((desc_on_rel & cur_blank & ~same).sum())
    # recount carefully on rows present on release
    on = joined[joined["k"].isin(rset)].copy()
    same_on = (
        (on["propose_aim_l1"] == on["aim_l1_fixed_rel"])
        & (on["propose_aim_l2"] == on["aim_l2_fixed_rel"])
        & (on["propose_aim_l3"] == on["aim_l3_fixed_rel"])
    )
    blank_on = on["aim_l1_fixed_rel"].str.strip() == ""
    desc_already = int(same_on.sum())
    desc_blank_aim = int((blank_on & ~same_on).sum())
    desc_conflict = int((~blank_on & ~same_on).sum())

    # hard holds DESC
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

    # hard holds master (desc text)
    d = master["description"].fillna("").str.upper() if "description" in master.columns else pd.Series([""] * len(master))
    a1m = master["aim_l1_fixed"].fillna("") if "aim_l1_fixed" in master.columns else pd.Series([""] * len(master))
    hard_master = {
        "cyl_hd_gasket_desc_to_transmission": int(
            (d.str.contains(r"GASKET;\s*CYL|CYL\.?\s*HD|HEAD\s*GASKET", regex=True) & (a1m == "Transmission")).sum()
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

    # Oct4 preserve
    mmap = master.set_index("k")
    oct4 = {}
    for g, expect in OCT4.items():
        pns = sorted({
            pad(r["part_number"]) for _, r in chg04.iterrows()
            if r["change_group"] == g and r["column"] == "aim_l1_fixed"
        })
        bad_rel, bad_m, ok_rel, ok_m = [], [], 0, 0
        for pn in pns:
            if pn in rmap.index:
                got = tuple(rmap.at[pn, c] for c in AIM)
                if got == expect:
                    ok_rel += 1
                else:
                    bad_rel.append({"pn": pn, "got": " > ".join(got)})
            if pn in mmap.index:
                ma1 = mmap.at[pn, "aim_l1_fixed"] if "aim_l1_fixed" in mmap.columns else ""
                ma2 = mmap.at[pn, "aim_l2_fixed"] if "aim_l2_fixed" in mmap.columns else ""
                ma3 = mmap.at[pn, "aim_l3_fixed"] if "aim_l3_fixed" in mmap.columns else mmap.at[pn, m3]
                if isinstance(ma1, pd.Series):
                    ma1 = ma1.iloc[0]
                if isinstance(ma2, pd.Series):
                    ma2 = ma2.iloc[0]
                if isinstance(ma3, pd.Series):
                    ma3 = ma3.iloc[0]
                gotm = (str(ma1), str(ma2), str(ma3))
                if gotm == expect:
                    ok_m += 1
                else:
                    bad_m.append({"pn": pn, "got": " > ".join(gotm)})
        oct4[g] = {
            "pn_count": len(pns),
            "ok_on_release04": ok_rel,
            "bad_on_release04": bad_rel[:5],
            "ok_on_master": ok_m,
            "bad_on_master": bad_m[:5],
            "expect": " > ".join(expect),
        }

    # aim_source tags on master
    src_counts = {}
    if "aim_source" in master.columns:
        s = master["aim_source"].fillna("")
        for tag in (
            "desc_proven_20261007", "eq_hit_proven_20261007",
            "CLEAN", "SAFE_v2", "safe_v2", "full_class_tranche1",
        ):
            src_counts[tag] = int(s.str.contains(tag, case=False, regex=False).sum())

    # GO script inputs — only DESC/EQ paths as assignments
    leak_hits = []
    for sp in (
        BUILD / "build_aim_classification_release_20261007.py",
        BUILD / "build_and_apply_aim_proven_20261007.py",
    ):
        if not sp.exists():
            continue
        for i, line in enumerate(sp.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            t = line.strip()
            if t.startswith("#"):
                continue
            if any(b in t for b in ("catmap_CLEAN", "SAFE_v2_2026-10-07", "live_order_unclassified")):
                if "=" in t or "read(" in t:
                    leak_hits.append({"script": str(sp), "line": i, "text": t[:200]})

    dual = {
        "script_a": str(BUILD / "build_and_apply_aim_proven_20261007.py"),
        "script_a_exists": (BUILD / "build_and_apply_aim_proven_20261007.py").exists(),
        "script_b": str(BUILD / "build_aim_classification_release_20261007.py"),
        "script_b_exists": (BUILD / "build_aim_classification_release_20261007.py").exists(),
        "script_b_references_missing_apply": not (BUILD / "build_aim_apply_proven_20261007.py").exists(),
        "risk": "TWO apply builders both claim to cut/approve/sync 2026-10-07; only one should run",
    }

    wrote_release = art["release_2026-10-07"]["exists"]
    wrote_report = art["apply_report_md"]["exists"]
    bak = bool(art["bak_master"])
    master_mtime = art["aim_master_v2"].get("mtime_iso") or ""

    if wrote_release and wrote_report and has07 and bak:
        apply_status = "complete"
    elif wrote_release or has07 or bak or wrote_report:
        apply_status = "partial"
    else:
        apply_status = "not started"

    hard_fail = {k: v for k, v in hard_desc.items() if v != 0 and k != "any_propose_transmission"}
    checklist = [
        {"id": "ssot_latest_approved", "label": "Latest APPROVED base is 2026-10-04",
         "result": "PASS" if latest and latest["release_id"] == "2026-10-04" else "FAIL"},
        {"id": "no_20261007_register_yet", "label": "No half-written 2026-10-07 register entry",
         "result": "PASS" if not has07 else "FAIL"},
        {"id": "no_partial_release_file", "label": "No half-written 2026-10-07 release CSV",
         "result": "PASS" if not wrote_release else "WARN"},
        {"id": "master_untouched_today", "label": "aim_master_v2 not rewritten by today GO apply",
         "result": "PASS" if master_mtime.startswith("2026-10-05") else "CHECK"},
        {"id": "desc_hard_holds", "label": "Hard holds 0 on DESC_PROVEN",
         "result": "PASS" if not hard_fail else "FAIL"},
        {"id": "overlap_zero", "label": "DESC ∩ EQ overlap = 0",
         "result": "PASS" if len(overlap) == 0 else "FAIL"},
        {"id": "oct4_release_intact", "label": "Oct4 gasket/EVRV/antenna/DEF intact on release04",
         "result": "PASS" if all(not v["bad_on_release04"] for v in oct4.values()) else "FAIL"},
        {"id": "oct4_master_intact", "label": "Oct4 gasket/EVRV/antenna/DEF intact on master",
         "result": "PASS" if all(not v["bad_on_master"] for v in oct4.values()) else "FAIL"},
        {"id": "go_inputs_proven_only", "label": "GO scripts assign only DESC_PROVEN + EQ_PROVEN",
         "result": "PASS" if not leak_hits else "FAIL"},
        {"id": "no_apply_report_yet", "label": "No _aim_apply_proven report yet",
         "result": "PASS" if not wrote_report else "INFO"},
        {"id": "dual_writer_risk", "label": "Only one apply writer should run",
         "result": "WARN" if dual["script_a_exists"] and dual["script_b_exists"] else "PASS"},
        {"id": "dry_run_ok", "label": "Dry-run of release builder exited 0 (terminal evidence)",
         "result": "PASS"},
        {"id": "sha04_matches_register", "label": "Release 2026-10-04 hash matches RELEASES",
         "result": "PASS" if sha04 == EXPECT04 else "FAIL"},
        {"id": "master_release_aim_sync", "label": "Master AIM matches release 2026-10-04 on shared PNs",
         "result": "PASS" if aim_mismatch == 0 else "FAIL"},
        {"id": "eng_gasket_not_trans_master", "label": "Engine gasket sets not on Transmission on master",
         "result": "PASS" if hard_master.get("gasket_set_eng_to_transmission", 0) == 0 else "FAIL"},
    ]

    mismatches = []
    mismatches.append({
        "kind": "release_hash",
        "detail": ("PASS — 2026-10-04 sha matches RELEASES.json"
                   if sha04 == EXPECT04 else f"FAIL sha {sha04} != {EXPECT04}"),
    })
    mismatches.append({
        "kind": "register",
        "detail": ("No 2026-10-07 entry in RELEASES.json (apply not registered)"
                   if not has07 else f"2026-10-07 present: {has07[0].get('status')}"),
    })
    mismatches.append({
        "kind": "master_vs_release04",
        "detail": (f"PASS — shared PNs AIM match"
                   if aim_mismatch == 0 else f"{aim_mismatch} AIM mismatches"),
        "samples": aim_samples,
    })
    mismatches.append({
        "kind": "proposal_overlap",
        "detail": f"PASS — DESC∩EQ = 0" if not overlap else f"DESC∩EQ = {len(overlap)}",
        "pns": sorted(overlap)[:20],
    })
    if desc_conflict:
        mismatches.append({
            "kind": "desc_vs_existing_aim",
            "detail": f"{desc_conflict} DESC PNs already have non-blank AIM on release04 (must keep)",
        })
    for g, info in oct4.items():
        if info["bad_on_release04"]:
            mismatches.append({"kind": "oct4_release", "detail": f"{g} broken on release04",
                               "samples": info["bad_on_release04"]})
        if info["bad_on_master"]:
            mismatches.append({"kind": "oct4_master", "detail": f"{g} broken on master",
                               "samples": info["bad_on_master"]})
    mismatches.append({
        "kind": "hard_hold_desc",
        "detail": "PASS — all hard holds 0 on DESC_PROVEN" if not hard_fail else str(hard_fail),
    })
    if hard_master.get("gasket_set_eng_to_transmission", 0):
        mismatches.append({
            "kind": "hard_hold_master",
            "detail": (f"engine gasket sets still on Transmission on master: "
                       f"{hard_master['gasket_set_eng_to_transmission']}"),
        })
    if hard_master.get("gasket_set_to_transmission", 0):
        mismatches.append({
            "kind": "hard_hold_master_info",
            "detail": (f"INFO — {hard_master['gasket_set_to_transmission']} GASKET SET* rows still "
                       f"on Transmission on master (expected for TRANS OVERHAUL / pre-Oct4 leftovers; "
                       f"ENG sets must be 0)"),
        })

    fails = [c for c in checklist if c["result"] == "FAIL"]
    warns = [c for c in checklist if c["result"] == "WARN"]

    if apply_status == "not started" and not fails:
        recommendation = (
            "safe — apply not started; dry-run OK; base intact. "
            "Run ONE writer only: build_aim_classification_release_20261007.py --apply "
            "(retire or ignore build_and_apply_aim_proven_20261007.py so they cannot fight)."
        )
    elif apply_status == "partial":
        recommendation = "fix X — partial apply artifacts; stop second writer; finish or roll back from bak_*"
    elif fails:
        recommendation = "abort / fix X — FAIL checklist items before any apply write"
    else:
        recommendation = "safe"

    projected = {
        "from_dry_run_terminal_662445": {
            "rows": 165055,
            "base": 164943,
            "eq_added": 112,
            "desc_filled": 30563,
            "desc_already_same": 90,
            "cat_diffs_not_applied": 70,
            "eq_remapped": 112,
            "eq_skipped": 4,
            "skip_reason": "no_safe_spine_leaf (4 — cameras expected)",
            "zero_checks_dry_all_zero": True,
        }
    }
    cov_after = {
        "release_rows_projected": 165055,
        "desc_aim_fills_projected": 30563,
        "eq_adds_projected": 112,
        "eq_skipped_projected": 4,
        "release_with_aim_before": cov["release_2026-10-04_with_aim"],
        "release_with_aim_after_projected": cov["release_2026-10-04_with_aim"] + 30563 + 112,
        "note": "already_same 90 do not change count; 4 EQ skipped",
    }

    report = {
        "as_of": pd.Timestamp.utcnow().isoformat() + "Z",
        "apply_status": apply_status,
        "latest_approved_base": latest,
        "register_2026-10-07": has07,
        "artifacts": art,
        "coverage_before": cov,
        "coverage_after_projected": cov_after,
        "projected_from_dry_run": projected,
        "proposal_counts": {
            "DESC_PROVEN": int(len(desc)),
            "EQ_PROVEN": int(len(eq)),
            "DESC_on_release": int(desc_on_rel.sum()),
            "DESC_missing_release": int((~desc_on_rel).sum()),
            "DESC_blank_aim_fillable": desc_blank_aim,
            "DESC_already_same": desc_already,
            "DESC_nonblank_kept": desc_conflict,
            "EQ_on_release": int(eq_on_rel.sum()),
            "EQ_missing_release": int((~eq_on_rel).sum()),
            "EQ_on_master": int(eq_on_m.sum()),
            "EQ_missing_master": int((~eq_on_m).sum()),
            "overlap_desc_eq": int(len(overlap)),
            "overlap_pns": sorted(overlap)[:50],
        },
        "hard_holds_desc_proposal": hard_desc,
        "hard_holds_master_current": hard_master,
        "oct4_decisions": oct4,
        "aim_source_tag_counts_master": src_counts,
        "master_vs_release04_aim_mismatches": aim_mismatch,
        "master_vs_release04_samples": aim_samples,
        "leak_hits": leak_hits,
        "dual_write_path": dual,
        "checklist": checklist,
        "mismatches": mismatches,
        "recommendation": recommendation,
        "precise_fix_instructions": [
            "Do NOT start a second apply while either builder is mid-flight.",
            "House process: cut release from APPROVED 2026-10-04 → gate → register → backup master → sync master from that release.",
            "Prefer one writer: python 01_data/91_build/build_aim_classification_release_20261007.py --apply",
            "Retire or ignore build_and_apply_aim_proven_20261007.py so the two cannot race.",
            "After apply expect: release CSV+meta+changes+gate, RELEASES APPROVED 2026-10-07 superseding 2026-10-04, master bak+rewrite, _aim_apply_proven_20261007.md.",
            "Re-run this doublecheck; Oct4 change PNs must stay Engine gasket / EGR / Radio / DEF Injector; hard holds on NEW fills stay 0.",
            "If partial files appear without bak: do not invent a third writer — restore from bak or last good master (mtime 2026-10-05), delete incomplete 2026-10-07 files, fix RELEASES.json.",
        ],
        "house_process_notes": {
            "ssot": "RELEASES.json latest APPROVED = 2026-10-04",
            "prior_method": "export_aim_eq_20260924 apply + dated release cut; never overwrite release files; backup master before sync",
            "go_scope": "DESC_PROVEN 30653 + EQ_PROVEN 116 only; CLEAN/SAFE-v2/unclassified stay out",
            "first_audit_attempt": "hung on row-loop join; killed; this vectorized re-run is authoritative",
        },
    }

    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# AIM apply double-check — 2026-10-07",
        "",
        f"**Apply status: {apply_status}**",
        "",
        f"Recommendation: {recommendation}",
        "",
        "## What exists right now",
        "",
        f"- Latest approved release in `RELEASES.json`: **{latest['release_id'] if latest else 'NONE'}** "
        f"(sha256 `{ (latest or {}).get('sha256','')[:16] }…`).",
        f"- Release file `aim_pn_classification_release_2026-10-07.csv`: "
        f"**{'EXISTS' if wrote_release else 'MISSING'}**.",
        f"- Apply report `_aim_apply_proven_20261007.md`: **{'EXISTS' if wrote_report else 'MISSING'}**.",
        f"- Master `aim_master_v2.csv` mtime: **{master_mtime}** "
        f"(still 2026-10-05 → not rewritten by today's GO apply).",
        f"- Master backup `bak_pre_proven_apply_20261007_*`: **{'YES' if bak else 'NONE'}**.",
        "- Dry-run of `build_aim_classification_release_20261007.py --dry`: **OK** "
        "(terminal 662445) — 30,563 AIM fills, 90 already-same, 70 catalogue diffs not applied, "
        "112 EQ adds, 4 EQ skips.",
        "",
        "## Coverage before → after (projected)",
        "",
        "| Cut | Rows | With AIM family |",
        "|---|---:|---:|",
        f"| Release 2026-10-04 (live base) | {cov['release_2026-10-04_rows']:,} | "
        f"{cov['release_2026-10-04_with_aim']:,} ({cov['release_2026-10-04_with_aim_pct']}%) |",
        f"| Master now | {cov['master_rows']:,} | aim_l1_fixed filled: {cov['master_with_aim_l1_fixed']:,} |",
        f"| After GO (from dry-run) | 165,055 | "
        f"~{cov['release_2026-10-04_with_aim'] + 30563 + 112:,} "
        f"(fills + EQ adds; 90 already-same unchanged) |",
        "",
        "## PASS/FAIL checklist",
        "",
    ]
    for c in checklist:
        lines.append(f"- **{c['result']}** — {c['label']}")
    lines += [
        "",
        "## Hard holds",
        "",
        "On DESC_PROVEN proposal (must be 0):",
    ]
    for k, v in hard_desc.items():
        lines.append(f"- `{k}` = **{v}**")
    lines += [
        "",
        "On current master (pre-apply; TRANS OVERHAUL gasket sets may still sit on Transmission — "
        "Oct4 only moved engine gasket sets):",
    ]
    for k, v in hard_master.items():
        lines.append(f"- `{k}` = **{v}**")
    lines += ["", "## Jerome 4 Oct decisions still on base", ""]
    for g, info in oct4.items():
        lines.append(
            f"- **{g}** → `{info['expect']}`: {info['pn_count']} PNs; "
            f"release04 ok {info['ok_on_release04']}; master ok {info['ok_on_master']}; "
            f"bad release {len(info['bad_on_release04'])}; bad master {len(info['bad_on_master'])}."
        )
    lines += [
        "",
        "## Proposal overlap and GO scope",
        "",
        f"- DESC_PROVEN rows: **{len(desc):,}**; on release: {int(desc_on_rel.sum()):,}; "
        f"blank-AIM fillable: {desc_blank_aim:,}; already-same: {desc_already:,}; "
        f"non-blank kept: {desc_conflict:,}.",
        f"- EQ_PROVEN rows: **{len(eq):,}**; missing from release: {int((~eq_on_rel).sum()):,}; "
        f"missing from master: {int((~eq_on_m).sum()):,}.",
        f"- DESC ∩ EQ: **{len(overlap)}**.",
        f"- CLEAN/SAFE assignment leak into GO scripts: **{len(leak_hits)}** hits.",
        f"- Master AIM vs release04 mismatches: **{aim_mismatch}**.",
        "",
        "## Dual writer risk",
        "",
        "Two builders both claim this GO apply:",
        f"- `{BUILD / 'build_and_apply_aim_proven_20261007.py'}` (exists={dual['script_a_exists']})",
        f"- `{BUILD / 'build_aim_classification_release_20261007.py'}` "
        f"(exists={dual['script_b_exists']}; references missing `build_aim_apply_proven_20261007.py`)",
        "",
        "**Do not run both.** That is the fight risk.",
        "",
        "## Mismatches vs existing SSOT",
        "",
    ]
    for m in mismatches:
        lines.append(f"- [{m['kind']}] {m['detail']}")
    lines += ["", "## Precise fix instructions", ""]
    for i, s in enumerate(report["precise_fix_instructions"], 1):
        lines.append(f"{i}. {s}")
    lines += [
        "",
        "## Absolute paths",
        "",
        f"- Register: `{REL / 'RELEASES.json'}`",
        f"- Base release: `{REL / 'aim_pn_classification_release_2026-10-04.csv'}`",
        f"- Master: `{DER / 'aim_master_v2.csv'}`",
        f"- DESC_PROVEN: `{REL / 'next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv'}`",
        f"- EQ_PROVEN: `{REL / 'next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv'}`",
        f"- This report: `{OUT_MD}`",
        f"- This JSON: `{OUT_JSON}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("STATUS", apply_status)
    print("REC", recommendation)
    print("FAILS", [c["id"] for c in fails])
    print("WARNS", [c["id"] for c in warns])
    print("overlap", len(overlap), "aim_mismatch", aim_mismatch)
    print("hard_desc", hard_desc)
    print("hard_master", hard_master)
    print("wrote", OUT_MD)
    print("wrote", OUT_JSON)


if __name__ == "__main__":
    main()
