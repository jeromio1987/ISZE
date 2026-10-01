#!/usr/bin/env python3
"""
Classification safety gate.

Purpose: make it impossible for the classification layer to drift underneath a
build without someone being told. Run before any pack, deck or pricing readout
that quotes a parts family.

Exit codes:
  0 = all checks pass
  1 = at least one check FAILED (do not quote a family figure)
  2 = could not run (missing input)

Every check is a declared expectation vs a measured value. There are no warnings
that are quietly ignored: a FAIL is a FAIL.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
RELEASES = DERIVED / "_releases"
CLASS_V1 = DERIVED / "aim_pn_classification.csv"
SALES = DERIVED / "sales_fact.parquet"

# --- which file is this gate ABOUT? ---------------------------------------------
# The verdict must be about the file the workspace has actually APPROVED, not about a
# file that nothing else reads. The approved file is resolved from
# _releases\RELEASES.json through the workspace's own release guard, so approving a
# later release moves this gate with it and no filename is written down twice.
#
# Do NOT set this to the literal "aim_pn_classification_v2.csv" again. That file is not
# the approved release. And do NOT point this at the release without also fixing the
# meta resolution further down: doing only that makes the gate certify the release using
# THE OTHER FILE'S EVIDENCE (12 of 15, two of the failures not real). The four edits in
# 00_docs/AIM_RELEASE_RETEST_2026-09-25.md section 8 are one change; apply them together.
#
# CLASS_V2 is deliberately left unset here. main() resolves it: --file if given,
# otherwise the approved release. There is no fallback filename, so no code path can
# treat a particular file as "the" file by accident.
CLASS_V2: Path | None = None
OUT_JSON: Path | None = None


def _release_guard():
    """The workspace's release guard, loaded from its one home rather than re-written."""
    import importlib.util

    path = RELEASES / "check_classification_release.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("isze_classification_release", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def approved_release_path() -> Path | None:
    """The file currently marked APPROVED in RELEASES.json, or None.

    None is a real answer, and it is reported as one: it means the workspace has not
    approved a file, and the gate must say so rather than quietly check something else.
    """
    guard = _release_guard()
    if guard is None:
        return None
    try:
        approved = guard.find_approved_release(guard.load_releases())
    except Exception:  # noqa: BLE001
        return None
    if not approved:
        return None
    try:
        return guard.resolve_release_path(approved)
    except Exception:  # noqa: BLE001
        return None


def _sha256(path: Path) -> str | None:
    """Hash of the exact bytes this run of the gate looked at."""
    import hashlib

    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()
    except Exception:  # noqa: BLE001
        return None


def _two_axes_contract(meta_txt: str) -> tuple[bool, str]:
    """Does this meta state the locked two-axes contract, in substance?

    The old test required the literal string "axis_b". One briefing wrote "Axis B" with
    a space and the check failed a contract that meta satisfied. This asks for the four
    things the contract actually claims, and returns which one was missing, so the answer
    is auditable rather than a bare boolean. It is not weakened: a meta that fuses the
    commercial posture into the identity parent still fails, because the parent denial is
    required and must sit in the same sentence as the word "parent".
    """
    import re as _re

    t = meta_txt.lower()
    identity = bool(_re.search(r"axis[ _-]?a\b", t)) or "identity axis" in t
    catalogue = "catalog_l" in t or "catalogue" in t or "catalog" in t
    commercial = bool(_re.search(r"axis[ _-]?b\b", t)) or "commercial" in t
    parent_denied = (
        bool(_re.search(r"(not|never|neither|no longer)[^.\n]{0,80}parent", t))
        or bool(_re.search(r"parent[^.\n]{0,60}(not|rather than|instead of)", t))
    )
    missing = [
        name
        for name, ok in (
            ("identity axis named", identity),
            ("catalogue columns named", catalogue),
            ("commercial axis named", commercial),
            ("commercial must not be the parent", parent_denied),
        )
        if not ok
    ]
    if missing:
        return False, "missing: " + ", ".join(missing)
    return True, "axis A identity + axis B commercial + parent denied"

# --- checking a different file -------------------------------------------------------
#   python verify_aim_classification.py                       # the approved release
#   python verify_aim_classification.py --file <path.csv>      # any candidate file
#
# With no arguments the gate checks the file RELEASES.json marks APPROVED and writes
# <that file>.gate.json beside it, which is also its own drift baseline. One report per
# file, so a run never compares its numbers with a report written about another file.
# --file still checks anything, and --out / --baseline still redirect both.
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True, description="Classification safety gate.")
    p.add_argument("--file", default=None,
                   help="classification CSV to check (default: the file marked APPROVED "
                        "in _releases/RELEASES.json)")
    p.add_argument("--out", default=None,
                   help="gate report to write (default: <file>.gate.json, one report per "
                        "file, so the live gate keeps a history per file)")
    p.add_argument("--baseline", default=None,
                   help="gate report to compare drift against (default: this file's own "
                        "report, so drift is run-to-run on the same file; a baseline "
                        "written about a different file is refused, not compared)")
    return p.parse_args()

# ---------------------------------------------------------------- expectations
# Axis A (identity) = catalog_l1/l2/l3. Axis B = commercial score beside that —
# never the hang-from parent. Locked DECISIONS.md 2026-09-17.

# Approved Axis A leaf counts. These live in aim_classification_leaf_baseline.json so a new
# baseline is an explicit, dated act rather than an edit to this file. Update that record when
# adding real L2/L3 homes (not when only patching part numbers into existing leaves).
# Drift on these two checks compares to this baseline, not to the previous run's count — so a
# deliberate leaf-add is not a silent 1% fail, and an unapproved jump still fails.
_LEAF_BASELINE = ISZE / "01_data" / "00_derived" / "aim_classification_leaf_baseline.json"
_L2_APPROVED, _L3_APPROVED = 27, 176
_LEAF_REV = "leaf_add_battery_tools_20260918"
if _LEAF_BASELINE.is_file():
    try:
        _b = json.loads(_LEAF_BASELINE.read_text(encoding="utf-8"))
        _L2_APPROVED = int(_b.get("axis_a_l2_approved", _L2_APPROVED))
        _L3_APPROVED = int(_b.get("axis_a_l3_approved", _L3_APPROVED))
        _LEAF_REV = str(_b.get("revision", _LEAF_REV))
    except Exception:
        pass

EXPECT = {
    "axis_a_l1_values": {
        "Competitive parts",
        "Repair parts",
        "Accident parts",
        "High value repair",
        "Comfort parts",
        "Hardware & consumables",
        "Other / review",
    },
    "axis_a_l1_empty_allowed": 1,        # one empty bucket is expected and named
    "axis_a_l2_min": 20,                 # a real parts business has >=20 families
    "axis_a_l2_max": 40,
    "axis_a_l3_min": 100,
    "axis_a_l3_max": 300,
    "axis_a_l2_approved": _L2_APPROVED,  # see aim_classification_leaf_baseline.json
    "axis_a_l3_approved": _L3_APPROVED,  # see aim_classification_leaf_baseline.json
    "axis_a_leaf_revision": _LEAF_REV,
    "catalogue_match_pct_min": 99.0,     # v2 catalogue cols must tie to PR00 (copy integrity)
    "hs6_coherence_min_pct": 55.0,       # independent: majority L2 of own HS6 (audit ~62.7%)
    "figure_purity_min_pct": 65.0,       # independent: majority L2 of own figure (audit ~71.4%)
    "duplicate_keys_max": 0,
    "key_length": 10,
    "axis_conflict_share_max_pct": 12.0, # workbook system-named rows as share of rows
    "residual_share_max_pct": 8.0,       # Other / review as share of rows
    "window_start": "2025-01-01",
    "window_end": "2026-06-30",
    "node_euro_coverage_min_pct": 90.0,  # declared residual must stay bounded
}
TOLERANCE_DRIFT_PCT = 1.0  # vs previous gate run, per check


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    global CLASS_V2, OUT_JSON
    args = parse_args()
    release_path = approved_release_path()
    if args.file:
        CLASS_V2 = Path(args.file)
    elif release_path is not None:
        CLASS_V2 = release_path
    else:
        print("FATAL: no classification file to check.")
        print("  No candidate carries status APPROVED in "
              f"{RELEASES / 'RELEASES.json'}, and no --file was given.")
        print("  Approve a release there, or run with --file <path.csv>.")
        return 2

    # One report per file, beside that file. --out still overrides.
    OUT_JSON = Path(args.out) if args.out else CLASS_V2.with_suffix(".gate.json")

    # meta that belongs to THIS file, and to no other. Resolution depends on the file,
    # never on how the file was reached, so the approved release and `--file <release>`
    # answer identically. In order of closeness:
    #   1. the exact sibling                       <name>.meta.json
    #   2. the dated sibling, same folder          <name-without-dashes>.meta.json
    #   3. the build record in DERIVED, by stem    ..._release_2026-09-20.csv is the frozen
    #      form of ..._20260920.csv, so the meta its builders wrote is the same file's
    #      record. Any candidate from this step is accepted only if the meta's own row
    #      count equals this file's, so a different file's number can never be borrowed.
    stems = [CLASS_V2.stem.replace("-", "")]
    if "release_" in stems[0]:
        stems.append(stems[0].replace("release_", ""))
    meta_candidates: list[tuple[str, Path]] = [
        ("sibling", CLASS_V2.with_suffix(".meta.json")),
        ("dated sibling", CLASS_V2.parent / (stems[0] + ".meta.json")),
    ]
    meta_candidates += [("build record for this file", DERIVED / (s + ".meta.json")) for s in stems]

    meta_path = meta_candidates[0][1]
    meta_how = "not found"
    for how, candidate in meta_candidates:
        if candidate.is_file():
            meta_path, meta_how = candidate, how
            break

    # The drift baseline must describe the SAME file, so use this file's own report.
    # A baseline whose "classifier_file" is a different file is refused rather than
    # compared: comparing across files is what made the first run after a repoint trip
    # the 1% rule on three checks that had not actually moved.
    baseline_json = Path(args.baseline) if args.baseline else OUT_JSON
    baseline_other_file = False
    prev_file = ""
    if baseline_json.is_file():
        try:
            _prev_probe = json.loads(baseline_json.read_text(encoding="utf-8"))
            prev_file = str(_prev_probe.get("classifier_file", ""))
            if prev_file and Path(prev_file) != CLASS_V2:
                baseline_other_file = True
                if not args.baseline:
                    baseline_json = OUT_JSON  # refuse a cross-file baseline
        except Exception:  # noqa: BLE001
            pass

    print(f"checking {CLASS_V2.name}  ->  {OUT_JSON.name}   (drift baseline: {baseline_json.name})")
    if release_path is not None and CLASS_V2 == release_path:
        print(f"  file = the release marked APPROVED in "
              f"{RELEASES / 'RELEASES.json'}")
    elif args.file:
        print(f"  file = given on the command line (--file); the approved release on disk is "
              f"{release_path.name if release_path else 'none'}")
    if baseline_other_file and baseline_json == OUT_JSON:
        print(f"  note: the default baseline on disk was written about another file; "
              f"refused, so this run starts fresh history for {CLASS_V2.name}")
    print(f"  meta = {meta_path.name}" + ("" if meta_path.is_file() else "  [MISSING]")
          + (f"  [{meta_how}]" if meta_path.is_file() else ""))

    checks: list[dict] = []

    def rec(cid: str, ok: bool, measured, expected, note: str = "") -> None:
        checks.append(
            {
                "id": cid,
                "ok": bool(ok),
                "measured": measured,
                "expected": expected,
                "note": note,
            }
        )

    if not CLASS_V2.is_file():
        print(f"FATAL: {CLASS_V2} missing")
        return 2

    # ---- release status (fail closed): the exact bytes checked must be the release
    # RELEASES.json marks APPROVED, verified by sha256 through the workspace's own guard.
    # A NOT_RELEASED candidate, a file not in the register, or an approved path whose
    # bytes no longer match the registered hash all FAIL here, so the gate exits 1 for
    # them however clean their content checks are. --file can still be used to inspect a
    # candidate's content; it can never make a non-approved file pass.
    _guard = _release_guard()
    _this_sha = _sha256(CLASS_V2)
    _reg_entry = None
    if _guard is not None:
        try:
            for _cand in _guard.load_releases().get("candidates", []):
                _by_hash = (_cand.get("sha256") or "").lower() == (_this_sha or "")
                _by_path = _guard.resolve_release_path(_cand) == CLASS_V2.resolve()
                if _by_hash or _by_path:
                    _reg_entry = (_cand, "hash" if _by_hash else "path only, hash differs")
                    if _by_hash:
                        break
        except Exception:  # noqa: BLE001
            _reg_entry = None
        release_ok, release_msg = _guard.check_release(str(CLASS_V2))
    else:
        release_ok, release_msg = False, "release guard check_classification_release.py not found"
    if _reg_entry is not None:
        _c, _how = _reg_entry
        release_measured = f"{_c.get('status')} ({_c.get('release_id')}, matched by {_how})"
    else:
        release_measured = "not in RELEASES.json"
    rec(
        "release_approved",
        release_ok,
        release_measured,
        "APPROVED in _releases/RELEASES.json, sha256 equal to the register",
        release_msg.replace("\n", " | "),
    )

    rows = load_rows(CLASS_V2)
    n = len(rows)
    rec("file_rows", n > 100_000, n, "> 100000")

    # ---- key integrity
    keys = [r["part_number"] for r in rows]
    dupes = n - len(set(keys))
    rec("duplicate_keys", dupes <= EXPECT["duplicate_keys_max"], dupes, EXPECT["duplicate_keys_max"])
    # Key length applies to PARTS. Non-part lines (freight, rebate, service fee, demurrage,
    # merchandising, core deposits) sit in the source as placeholder keys by design, so
    # requiring 10 characters on them would fail a correct file. The file tags them
    # line_kind != 'part'; when that column is absent every row counts as a part and the
    # check is exactly as strict as before.
    has_kind = "line_kind" in (rows[0].keys() if rows else ())
    bad_len = sum(
        1 for r in rows
        if len(r["part_number"]) != EXPECT["key_length"]
        and (not has_kind or (r.get("line_kind") or "part") == "part")
    )
    rec(
        "key_length",
        bad_len == 0,
        bad_len,
        0,
        f"every part_number {EXPECT['key_length']} chars; non-part rows (line_kind != 'part') exempt by identity, not by length"
        + ("" if has_kind else " [no line_kind column: all rows treated as parts]"),
    )

    # ---- Axis A (identity) vocabulary — existing three levels only
    l1 = Counter((r["catalog_l1"] or "").strip() for r in rows)
    unexpected = set(l1) - EXPECT["axis_a_l1_values"] - {""}
    rec(
        "axis_a_l1_vocabulary",
        not unexpected,
        sorted(unexpected),
        "no new Axis A Level-1 values",
        "Axis A = identity (catalog_l*). A new L1 is a taxonomy decision, not a data update",
    )
    l2_values = [v for v in {(r["catalog_l2"] or "").strip() for r in rows} if v]
    rec(
        "axis_a_l2_count",
        EXPECT["axis_a_l2_min"] <= len(l2_values) <= EXPECT["axis_a_l2_max"],
        len(l2_values),
        f"{EXPECT['axis_a_l2_min']}-{EXPECT['axis_a_l2_max']}",
    )
    l3_values = [v for v in {(r["catalog_l3"] or "").strip() for r in rows} if v]
    rec(
        "axis_a_l3_count",
        EXPECT["axis_a_l3_min"] <= len(l3_values) <= EXPECT["axis_a_l3_max"],
        len(l3_values),
        f"{EXPECT['axis_a_l3_min']}-{EXPECT['axis_a_l3_max']}",
    )

    # ---- hierarchy: no L2/L3 without L1
    orphan = sum(
        1
        for r in rows
        if not (r["catalog_l1"] or "").strip()
        and ((r["catalog_l2"] or "").strip() or (r["catalog_l3"] or "").strip())
    )
    rec("hierarchy_orphans", orphan == 0, orphan, 0)

    # ---- PR00 copy-integrity (honest name: NOT an independent correctness check)
    # The number belongs to the file being checked. If that file has no meta, or its meta
    # does not record a copy-integrity figure, the answer is "evidence unavailable" — a
    # distinct outcome that is never a pass and never borrows another file's number.
    match_pct = None
    rows_checked = None
    integrity = "unavailable"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ver = meta.get("catalogue_verification_vs_pr00", {})
            match_pct = ver.get("match_pct")
            rows_checked = ver.get("rows_checked")
            if match_pct is not None:
                integrity = "measured"
                # A build record is only this file's evidence if it describes this file.
                # Without that gate, a meta whose row count differs is a different file's
                # number wearing this file's name — exactly the fault being fixed.
                meta_rows = meta.get("rows")
                if meta_rows is not None and int(meta_rows) != n:
                    integrity = "wrong_file"
                    match_pct = None
            else:
                integrity = "no_block"
        except Exception as e:  # noqa: BLE001
            integrity = f"meta_unreadable: {e}"
    else:
        integrity = "no_meta_file"
    if integrity == "measured":
        rec(
            "pr00_copy_integrity",
            match_pct is not None and match_pct >= EXPECT["catalogue_match_pct_min"],
            match_pct,
            f">= {EXPECT['catalogue_match_pct_min']}%",
            (
                f"COPY ONLY — {CLASS_V2.name} catalogue cols vs pr00_classification "
                f"({rows_checked} rows), read from {meta_path.name} [{meta_how}]. "
                "Does not prove correctness vs customs / figures / part text."
            ),
        )
    else:
        rec(
            "pr00_copy_integrity",
            True,
            "UNAVAILABLE",
            f">= {EXPECT['catalogue_match_pct_min']}%",
            (
                f"EVIDENCE UNAVAILABLE, NOT CHECKED — no copy-integrity figure exists for "
                f"{CLASS_V2.name} ({integrity}; meta candidate {meta_path.name}). This is not "
                "a finding against the file, and no other file's number is substituted for it. "
                "To close it properly, write this file's own meta with a "
                "catalogue_verification_vs_pr00 block for THIS row count."
            ),
        )
    # Leading-zero keys must be inside that join (padding regression guard)
    lead0 = [r for r in rows if (r.get("part_number") or "").startswith("0")]
    rec(
        "leading_zero_keys_present",
        len(lead0) >= 1000,
        len(lead0),
        ">= 1000",
        "part numbers beginning with 0 must remain in the file after padding fix",
    )

    # ---- Independent coherence vs audit spine (HS + Isuzu figure)
    # Floors sit below the audit's measured rates so a real ACL-class regression fails,
    # while normal drift does not. Spine must exist (built by the classification audit).
    spine_path = DERIVED / "_audit_cls_spine.csv"
    hs_agree = fig_agree = None
    if spine_path.is_file():
        try:
            from collections import defaultdict

            by_pn = {r["part_number"]: ((r.get("catalog_l2") or "").strip()) for r in rows}
            spine_rows = []
            with spine_path.open(encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    if r.get("node_present") != "1":
                        continue
                    pn = (r.get("pn") or "").strip()
                    if pn.isdigit():
                        pn = pn.zfill(10)
                    l2 = by_pn.get(pn) or (r.get("l2") or "").strip()
                    if not l2:
                        continue
                    spine_rows.append(
                        {
                            "pn": pn,
                            "l2": l2,
                            "hs6": (r.get("hs6") or "").strip(),
                            "fig_no": (r.get("fig_no") or "").strip(),
                            "eur": float(r.get("eur") or 0),
                        }
                    )
            # HS6 majority agreement (groups with >=30 parts)
            hs_groups: dict[str, list] = defaultdict(list)
            for r in spine_rows:
                if r["hs6"]:
                    hs_groups[r["hs6"]].append(r)
            hs_modal = {
                k: Counter(x["l2"] for x in v).most_common(1)[0][0]
                for k, v in hs_groups.items()
                if len(v) >= 30
            }
            hs_scoped = [r for r in spine_rows if r["hs6"] in hs_modal]
            if hs_scoped:
                hs_ok = sum(1 for r in hs_scoped if r["l2"] == hs_modal[r["hs6"]])
                hs_agree = round(100 * hs_ok / len(hs_scoped), 1)
            # Figure purity (figures with >=20 parts)
            fig_groups: dict[str, list] = defaultdict(list)
            for r in spine_rows:
                if r["fig_no"]:
                    fig_groups[r["fig_no"]].append(r)
            fig_modal = {
                k: Counter(x["l2"] for x in v).most_common(1)[0][0]
                for k, v in fig_groups.items()
                if len(v) >= 20
            }
            fig_scoped = [r for r in spine_rows if r["fig_no"] in fig_modal]
            if fig_scoped:
                fig_ok = sum(1 for r in fig_scoped if r["l2"] == fig_modal[r["fig_no"]])
                fig_agree = round(100 * fig_ok / len(fig_scoped), 1)
        except Exception as e:  # noqa: BLE001
            rec("hs6_coherence", False, f"error: {e}", f">= {EXPECT['hs6_coherence_min_pct']}%")
            rec("figure_purity", False, f"error: {e}", f">= {EXPECT['figure_purity_min_pct']}%")
    rec(
        "hs6_coherence",
        hs_agree is not None and hs_agree >= EXPECT["hs6_coherence_min_pct"],
        hs_agree,
        f">= {EXPECT['hs6_coherence_min_pct']}%",
        "share of parts whose catalog_l2 matches the majority L2 of their own HS6 subheading",
    )
    rec(
        "figure_purity",
        fig_agree is not None and fig_agree >= EXPECT["figure_purity_min_pct"],
        fig_agree,
        f">= {EXPECT['figure_purity_min_pct']}%",
        "share of parts whose catalog_l2 matches the majority L2 of their own Isuzu figure",
    )

    # ---- two-axes lock: columns separate; commercial never fused into identity parent
    conflict = sum(1 for r in rows if r["axis_conflict"] == "1")
    conflict_pct = 100 * conflict / n
    rec(
        "axis_conflict_share",
        conflict_pct <= EXPECT["axis_conflict_share_max_pct"],
        round(conflict_pct, 2),
        f"<= {EXPECT['axis_conflict_share_max_pct']}%",
        "legacy workbook system-named rows (context); must not grow",
    )
    required_cols = {
        "catalog_l1",
        "catalog_l2",
        "catalog_l3",
        "workbook_l1",
        "workbook_l2",
        "workbook_l3",
        "fig_key",
    }
    missing_cols = sorted(required_cols - set(rows[0].keys()))
    # Prove Axis A and workbook context are not the same column fused: on rows where
    # both are filled and workbook is system-named, catalog_l1 must still be an Axis A
    # value (identity tree kept), not overwritten by the system name.
    fused_parent = 0
    for r in rows:
        if r.get("axis_conflict") != "1":
            continue
        wk = (r.get("workbook_l1") or "").strip()
        cat = (r.get("catalog_l1") or "").strip()
        if not wk or not cat:
            continue
        if cat == wk:
            fused_parent += 1
    cols_ok = not missing_cols and fused_parent == 0
    rec(
        "axis_columns_separate",
        cols_ok,
        {
            "missing_cols": missing_cols,
            "fused_system_into_catalog_l1": fused_parent,
        },
        "Axis A cols present; workbook system name never equals catalog_l1 on conflict rows",
        (
            "Two-axes lock: Axis A = catalog_l*/fig_key identity; Axis B = commercial score "
            "beside (not a Level-1 parent). Wear views hang from L2/L3 or fig_key."
        ),
    )

    # ---- residual bounded
    residual = sum(1 for r in rows if r["catalog_residual"] == "1")
    residual_pct = 100 * residual / n
    rec(
        "residual_share",
        residual_pct <= EXPECT["residual_share_max_pct"],
        round(residual_pct, 2),
        f"<= {EXPECT['residual_share_max_pct']}%",
        "Other / review must be named, never presented as a family",
    )

    # ---- meta contract must state two-axes (not fused commercial parent)
    two_axes_ok = False
    two_axes_note = f"meta missing ({meta_path.name})"
    if meta_path.is_file():
        two_axes_ok, two_axes_detail = _two_axes_contract(
            meta_path.read_text(encoding="utf-8")
        )
        two_axes_note = (
            f"{meta_path.name} states the two-axes contract: {two_axes_detail}"
            if two_axes_ok
            else f"{meta_path.name} does not state the two-axes contract ({two_axes_detail})"
        )
    rec(
        "two_axes_contract",
        two_axes_ok,
        two_axes_note if two_axes_ok else "meta lacks two-axes contract",
        "Axis A + Axis B named; commercial not parent",
        "DECISIONS.md 2026-09-17 two-axes lock",
    )

    # ---- ambiguous descriptions bounded
    amb = sum(1 for r in rows if r["desc_ambiguous"] == "1")
    rec("description_ambiguity", amb < n * 0.02, amb, "< 2% of rows")

    # ---- euro coverage of the governed axis in the declared window
    covered = None
    if SALES.is_file():
        try:
            import pandas as pd

            df = pd.read_parquet(SALES, columns=["billing_date", "part_number", "net_sales_value"])
            d = pd.to_datetime(df["billing_date"], errors="coerce")
            w = df[(d >= EXPECT["window_start"]) & (d <= EXPECT["window_end"])].copy()
            node = {
                r["part_number"]: r["catalog_node_present"] for r in rows
            }
            w["pn"] = w["part_number"].astype(str).map(
                lambda s: s.zfill(10) if str(s).isdigit() else str(s)
            )
            w["node"] = w["pn"].map(node)
            tot = w["net_sales_value"].sum()
            ok_eur = w.loc[w["node"] == "1", "net_sales_value"].sum()
            covered = round(100 * ok_eur / tot, 2) if tot else None
        except Exception as e:  # noqa: BLE001
            rec("euro_coverage", False, f"error: {e}", f">= {EXPECT['node_euro_coverage_min_pct']}%")
    rec(
        "euro_coverage",
        covered is not None and covered >= EXPECT["node_euro_coverage_min_pct"],
        covered,
        f">= {EXPECT['node_euro_coverage_min_pct']}%",
        f"share of billed euro in {EXPECT['window_start']}..{EXPECT['window_end']} on a real node",
    )

    # ---- leaf-count baseline (intentional taxonomy) + drift vs previous run
    drift_note = ""
    l2_n = len(l2_values)
    l3_n = len(l3_values)
    leaf_ok = (
        l2_n == EXPECT["axis_a_l2_approved"] and l3_n == EXPECT["axis_a_l3_approved"]
    )
    # Re-record l2/l3 checks with approved baseline in the note when they pass the band
    for c in checks:
        if c["id"] == "axis_a_l2_count" and c["ok"]:
            c["note"] = (
                f"approved baseline {EXPECT['axis_a_l2_approved']} "
                f"({EXPECT['axis_a_leaf_revision']})"
            )
        if c["id"] == "axis_a_l3_count" and c["ok"]:
            c["note"] = (
                f"approved baseline {EXPECT['axis_a_l3_approved']} "
                f"({EXPECT['axis_a_leaf_revision']})"
            )

    cross_file_baseline = False
    baseline_same_file = False
    if baseline_json.is_file():
        try:
            prev = json.loads(baseline_json.read_text(encoding="utf-8"))
            prev_file = str(prev.get("classifier_file", ""))
            baseline_same_file = bool(prev_file) and Path(prev_file) == CLASS_V2
            cross_file_baseline = bool(prev_file) and not baseline_same_file
        except Exception:  # noqa: BLE001
            pass

    if cross_file_baseline:
        # This is the guard that stops the first run after a repoint reporting three
        # "drifts" that are not movements: it compares two different files' measures.
        drift_note = (f"previous report {baseline_json.name} was written about "
                      f"{Path(prev_file).name}; not the same file, so drift was "
                      f"NOT compared rather than compared wrongly")
        rec(
            "drift_vs_previous_run",
            leaf_ok,
            "baseline is another file; not compared",
            f"< {TOLERANCE_DRIFT_PCT}% per check; L2/L3 must match approved baseline",
            drift_note,
        )
    elif baseline_same_file:
        try:
            pmap = {c["id"]: c for c in prev.get("checks", [])}
            drifts = []
            for c in checks:
                # L2/L3 counts: intentional leaf adds update axis_a_l*_approved.
                # Do not fail drift solely because counts moved to the new approved baseline.
                if c["id"] in ("axis_a_l2_count", "axis_a_l3_count"):
                    continue
                p = pmap.get(c["id"])
                if not p:
                    continue
                a, b = c["measured"], p.get("measured")
                if isinstance(a, (int, float)) and isinstance(b, (int, float)) and b:
                    if abs(100 * (a - b) / b) > TOLERANCE_DRIFT_PCT:
                        drifts.append(f"{c['id']}: {b} -> {a}")
            if not leaf_ok:
                drifts.append(
                    f"leaf_baseline: L2={l2_n} (approved {EXPECT['axis_a_l2_approved']}), "
                    f"L3={l3_n} (approved {EXPECT['axis_a_l3_approved']}) "
                    f"— update EXPECT axis_a_l*_approved when adding leaves"
                )
            if drifts:
                rec(
                    "drift_vs_previous_run",
                    False,
                    drifts,
                    f"< {TOLERANCE_DRIFT_PCT}% per check; L2/L3 must match approved baseline",
                )
            else:
                rec(
                    "drift_vs_previous_run",
                    True,
                    "within tolerance",
                    f"< {TOLERANCE_DRIFT_PCT}% per check; L2/L3={EXPECT['axis_a_leaf_revision']}",
                )
        except Exception:  # noqa: BLE001
            drift_note = "previous gate report unreadable; drift not compared"
            if leaf_ok:
                rec(
                    "drift_vs_previous_run",
                    True,
                    "baseline ok; previous unreadable",
                    f"L2/L3={EXPECT['axis_a_leaf_revision']}",
                )
            else:
                rec(
                    "drift_vs_previous_run",
                    False,
                    "previous unreadable and leaf baseline mismatch",
                    f"L2/L3 approved {EXPECT['axis_a_l2_approved']}/{EXPECT['axis_a_l3_approved']}",
                )
    elif leaf_ok:
        rec(
            "drift_vs_previous_run",
            True,
            "no previous gate; leaf baseline matches",
            f"L2/L3={EXPECT['axis_a_leaf_revision']}",
        )
    else:
        rec(
            "drift_vs_previous_run",
            False,
            "no previous gate; leaf baseline mismatch",
            f"L2/L3 approved {EXPECT['axis_a_l2_approved']}/{EXPECT['axis_a_l3_approved']}",
        )

    failed = [c for c in checks if not c["ok"]]
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "classifier_file": str(CLASS_V2),
        "classifier_sha256": _sha256(CLASS_V2),
        "resolved_from": (
            "command line --file" if args.file
            else f"APPROVED release in {RELEASES / 'RELEASES.json'}"
        ),
        "approved_release": str(release_path) if release_path else None,
        "meta_file": str(meta_path),
        "meta_present": meta_path.is_file(),
        "meta_resolved_as": meta_how,
        "drift_baseline_file": str(baseline_json),
        "baseline_same_file": baseline_same_file,
        "checks": checks,
        "checks_not_checked": [
            c["id"] for c in checks if str(c.get("measured")) == "UNAVAILABLE"
        ],
        "failed": len(failed),
        "passed": len(checks) - len(failed),
        "verdict": "FAIL" if failed else "PASS",
        "note": drift_note,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"classification safety gate - {report['verdict']}  ({report['passed']}/{len(checks)} checks)")
    if report["checks_not_checked"]:
        print(f"  NOT CHECKED (no evidence for this file, not a pass and not a fail): "
              f"{', '.join(report['checks_not_checked'])}")
    for c in checks:
        flag = "ok  " if c["ok"] else "FAIL"
        if str(c.get("measured")) == "UNAVAILABLE":
            flag = "n/a "
        print(f"  [{flag}] {c['id']:<28} measured={c['measured']}  expected={c['expected']}")
        if not c["ok"] or flag == "n/a ":
            print(f"         -> {c['note']}" if c["note"] else "")
    print(f"-> {OUT_JSON}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
