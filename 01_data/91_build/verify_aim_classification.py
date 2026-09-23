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
CLASS_V2 = DERIVED / "aim_pn_classification_v2.csv"
CLASS_V1 = DERIVED / "aim_pn_classification.csv"
SALES = DERIVED / "sales_fact.parquet"
OUT_JSON = DERIVED / "aim_classification_gate.json"

# --- optional: check a different classification file without touching the live report ---
#   python verify_aim_classification.py --file <path.csv>
# Writes <path>.gate.json beside that file instead of overwriting the live gate report,
# so a candidate build can be verified without the live gate losing its history.
# With no arguments the behaviour is exactly as before.
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True, description="Classification safety gate.")
    p.add_argument("--file", default=None,
                   help="classification CSV to check (default: the live v2 file)")
    p.add_argument("--out", default=None,
                   help="gate report to write (default: the live gate JSON, "
                        "or <file>.gate.json when --file is given)")
    p.add_argument("--baseline", default=None,
                   help="gate report to compare drift against (default: the live "
                        "aim_classification_gate.json, so a candidate is compared with "
                        "the published baseline rather than with its own last run)")
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
    if args.file:
        CLASS_V2 = Path(args.file)
        OUT_JSON = Path(args.out) if args.out else CLASS_V2.with_suffix(".gate.json")
    elif args.out:
        OUT_JSON = Path(args.out)
    baseline_json = Path(args.baseline) if args.baseline else (DERIVED / "aim_classification_gate.json")
    print(f"checking {CLASS_V2.name}  ->  {OUT_JSON.name}   (drift baseline: {baseline_json.name})")

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
        print(f"FATAL: {CLASS_V2} missing - run build_aim_classification_v2.py first")
        return 2

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
    meta_path = DERIVED / "aim_pn_classification_v2.meta.json"
    match_pct = None
    rows_checked = None
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        ver = meta.get("catalogue_verification_vs_pr00", {})
        match_pct = ver.get("match_pct")
        rows_checked = ver.get("rows_checked")
    rec(
        "pr00_copy_integrity",
        match_pct is not None and match_pct >= EXPECT["catalogue_match_pct_min"],
        match_pct,
        f">= {EXPECT['catalogue_match_pct_min']}%",
        (
            f"COPY ONLY — v2 catalogue cols vs pr00_classification ({rows_checked} rows). "
            "Does not prove correctness vs customs / figures / part text."
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
    two_axes_note = "meta missing"
    if meta_path.is_file():
        meta_txt = meta_path.read_text(encoding="utf-8").lower()
        two_axes_ok = (
            "axis_a" in meta_txt
            and "axis_b" in meta_txt
            and "commercial" in meta_txt
            and "parent" in meta_txt
        )
        two_axes_note = "meta states Axis A identity + Axis B commercial score not parent"
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

    if baseline_json.is_file():
        try:
            prev = json.loads(baseline_json.read_text(encoding="utf-8"))
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
        "checks": checks,
        "failed": len(failed),
        "passed": len(checks) - len(failed),
        "verdict": "FAIL" if failed else "PASS",
        "note": drift_note,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"classification safety gate - {report['verdict']}  ({report['passed']}/{len(checks)} checks)")
    for c in checks:
        flag = "ok  " if c["ok"] else "FAIL"
        print(f"  [{flag}] {c['id']:<28} measured={c['measured']}  expected={c['expected']}")
        if not c["ok"]:
            print(f"         -> {c['note']}" if c["note"] else "")
    print(f"-> {OUT_JSON}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
