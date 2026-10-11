#!/usr/bin/env python3
"""
Deep QA of the PBI AIM figkey export Bart would load (release 2026-10-07)
vs the Sep-21 file he still has. Read-only. Writes JSON + MD report.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
REL = DER / "_releases"
BUILD = ROOT / "01_data" / "91_build"
OUT_JSON = BUILD / "_aim_pbi_export_deep_qa_20261011.json"
OUT_MD = BUILD / "_aim_pbi_export_deep_qa_20261011.md"

NEW_CSV = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-07.csv"
NEW_XLSX = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-07.xlsx"
NEW_META = DER / "AIM_Master_PN_Categories_Figkey_release_2026-10-07.release.json"
OLD_CSV = DER / "AIM_Master_PN_Categories_Figkey_20260921.csv"
OLD_XLSX = DER / "AIM_Master_PN_Categories_Figkey_20260921.xlsx"
CLASS_REL = REL / "aim_pn_classification_release_2026-10-07.csv"
CLASS_CHANGES = REL / "aim_pn_classification_release_2026-10-07.changes.csv"
CLASS_EQ_SKIP = REL / "aim_pn_classification_release_2026-10-07.eq_skipped.csv"
MASTER = DER / "aim_master_v2.csv"
SALES = DER / "sales_fact.parquet"
RELEASES = REL / "RELEASES.json"

RNG = np.random.default_rng(20261011)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def blank(s: pd.Series) -> pd.Series:
    return s.isna() | (s.astype(str).str.strip() == "") | (s.astype(str).str.lower() == "nan")


def aim_triple(df: pd.DataFrame) -> pd.Series:
    a1 = df["aim_level_1"].fillna("").astype(str).str.strip()
    a2 = df["aim_level_2"].fillna("").astype(str).str.strip()
    a3 = df["aim_level_3"].fillna("").astype(str).str.strip()
    return a1 + " > " + a2 + " > " + a3


def load_export(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    df["pn"] = df["part_number"].str.zfill(10)
    df["has_aim"] = ~blank(df["aim_level_1"])
    df["aim_path"] = aim_triple(df)
    try:
        df["eur"] = pd.to_numeric(df["l12m_billed_eur"], errors="coerce").fillna(0.0)
    except Exception:
        df["eur"] = 0.0
    return df


def section(rep: dict, name: str) -> dict:
    rep.setdefault("sections", {})[name] = {
        "ok": True,
        "fails": [],
        "notes": [],
        "metrics": {},
    }
    return rep["sections"][name]


def fail(sec: dict, msg: str) -> None:
    sec["ok"] = False
    sec["fails"].append(msg)


def note(sec: dict, msg: str) -> None:
    sec["notes"].append(msg)


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    report: dict = {
        "started_utc": started,
        "files": {},
        "sections": {},
        "random_samples": {},
        "verdict": "UNKNOWN",
        "better_than_sep21": None,
        "safe_to_send_bart": None,
    }

    # --- A. File identity / hash ---
    sec = section(report, "A_file_identity")
    meta = json.loads(NEW_META.read_text(encoding="utf-8"))
    h_csv = sha256(NEW_CSV)
    h_xlsx = sha256(NEW_XLSX)
    report["files"] = {
        "new_csv": str(NEW_CSV),
        "new_csv_sha256": h_csv,
        "new_csv_meta_sha256": meta.get("export_sha256"),
        "new_xlsx": str(NEW_XLSX),
        "new_xlsx_sha256": h_xlsx,
        "old_csv": str(OLD_CSV),
        "old_csv_sha256": sha256(OLD_CSV),
        "class_release_sha256": sha256(CLASS_REL),
        "class_release_meta_sha256": meta.get("release_sha256"),
        "meta": meta,
    }
    if h_csv != meta.get("export_sha256"):
        fail(sec, f"CSV hash drift vs release.json: {h_csv} != {meta.get('export_sha256')}")
    else:
        note(sec, "CSV sha256 matches release.json export_sha256")
    if sha256(CLASS_REL) != meta.get("release_sha256"):
        fail(sec, "Internal classification release hash != meta.release_sha256")
    else:
        note(sec, "Internal release sha256 matches meta")

    releases = json.loads(RELEASES.read_text(encoding="utf-8"))
    approved = [c for c in releases.get("candidates", []) if c.get("status") == "APPROVED"]
    if len(approved) != 1 or approved[0].get("release_id") != "2026-10-07":
        fail(sec, f"RELEASES.json APPROVED unexpected: {approved}")
    else:
        note(sec, "RELEASES.json APPROVED = 2026-10-07")
        if approved[0].get("sha256", "").lower() != sha256(CLASS_REL).lower():
            # register may store hash under different key
            reg_h = (approved[0].get("sha256") or approved[0].get("file_sha256") or "").lower()
            if reg_h and reg_h != sha256(CLASS_REL).lower():
                fail(sec, f"REGISTER hash mismatch: {reg_h}")
            else:
                note(sec, f"Approved register keys: {list(approved[0].keys())[:12]}")

    # --- B. Load exports ---
    sec = section(report, "B_load_compare_shape")
    new = load_export(NEW_CSV)
    old = load_export(OLD_CSV)
    sec["metrics"] = {
        "new_rows": int(len(new)),
        "old_rows": int(len(old)),
        "new_unique_pn": int(new["pn"].nunique()),
        "old_unique_pn": int(old["pn"].nunique()),
        "new_with_aim": int(new["has_aim"].sum()),
        "old_with_aim": int(old["has_aim"].sum()),
        "new_aim_unique_pn": int(new.loc[new["has_aim"], "pn"].nunique()),
        "old_aim_unique_pn": int(old.loc[old["has_aim"], "pn"].nunique()),
        "cols_equal": list(new.columns) == list(old.columns) or (
            set(c for c in new.columns if c not in ("pn", "has_aim", "aim_path", "eur"))
            == set(c for c in old.columns if c not in ("pn", "has_aim", "aim_path", "eur"))
        ),
    }
    if sec["metrics"]["new_rows"] != meta.get("rows"):
        fail(sec, f"Row count {sec['metrics']['new_rows']} != meta.rows {meta.get('rows')}")
    if sec["metrics"]["new_with_aim"] != meta.get("with_aim_level_1"):
        # allow small drift if figure export differs; flag
        note(
            sec,
            f"with_aim {sec['metrics']['new_with_aim']} vs meta {meta.get('with_aim_level_1')} "
            f"(delta {sec['metrics']['new_with_aim'] - int(meta.get('with_aim_level_1') or 0)})",
        )
    dup_new = int(new["pn"].duplicated().sum())
    dup_old = int(old["pn"].duplicated().sum())
    sec["metrics"]["dup_pn_new"] = dup_new
    sec["metrics"]["dup_pn_old"] = dup_old
    # figkey export can have multi rows per PN (figure keys) — that is expected
    note(sec, f"Duplicate PN rows new={dup_new} old={dup_old} (figure-key grain, may be >0)")

    # --- C. xlsx vs csv parity (sample + counts) ---
    sec = section(report, "C_xlsx_vs_csv")
    try:
        xdf = pd.read_excel(NEW_XLSX, dtype=str)
        for c in xdf.columns:
            xdf[c] = xdf[c].fillna("").astype(str).str.strip()
        sec["metrics"]["xlsx_rows"] = int(len(xdf))
        sec["metrics"]["xlsx_cols"] = list(xdf.columns)
        if list(xdf.columns) != [c for c in new.columns if c not in ("pn", "has_aim", "aim_path", "eur")]:
            # compare to raw csv cols
            raw_cols = list(pd.read_csv(NEW_CSV, nrows=0).columns)
            if list(xdf.columns) != raw_cols:
                fail(sec, f"xlsx cols != csv cols: {list(xdf.columns)} vs {raw_cols}")
            else:
                note(sec, "xlsx cols match csv")
        else:
            note(sec, "xlsx cols match")
        if len(xdf) != len(new):
            fail(sec, f"xlsx rows {len(xdf)} != csv rows {len(new)}")
        # full PN+AIM path set compare (memory heavy but OK)
        xdf["pn"] = xdf["part_number"].str.zfill(10)
        xdf["aim_path"] = aim_triple(xdf)
        # hash of sorted key triples
        def fingerprint(df):
            s = (df["pn"] + "|" + df["aim_path"] + "|" + df.get("figure_key", pd.Series([""] * len(df))).fillna("")).sort_values()
            return hashlib.sha256(("\n".join(s.tolist())).encode()).hexdigest()

        fp_csv = fingerprint(new)
        fp_xlsx = fingerprint(xdf)
        sec["metrics"]["fingerprint_csv"] = fp_csv
        sec["metrics"]["fingerprint_xlsx"] = fp_xlsx
        if fp_csv != fp_xlsx:
            # deeper: mismatch count
            m = new[["pn", "figure_key", "aim_path"]].merge(
                xdf[["pn", "figure_key", "aim_path"]],
                on=["pn", "figure_key"],
                how="outer",
                suffixes=("_c", "_x"),
                indicator=True,
            )
            bad = m[m["_merge"] != "both"]
            aim_diff = m[(m["_merge"] == "both") & (m["aim_path_c"] != m["aim and_path_x"] if False else m["aim_path_c"] != m["aim_path_x"])]
            sec["metrics"]["outer_mismatch_rows"] = int(len(bad))
            sec["metrics"]["aim_path_diff_rows"] = int(len(aim_diff))
            if len(bad) or len(aim_diff):
                fail(sec, f"xlsx/csv content mismatch: outer={len(bad)} aim_diff={len(aim_diff)}")
            else:
                note(sec, "fingerprint differ but join equal — check sort only")
        else:
            note(sec, "xlsx fingerprint == csv fingerprint (pn|aim|figure_key)")
        # random 400 row equality
        sample_idx = RNG.choice(len(new), size=min(400, len(new)), replace=False)
        mism = 0
        for i in sample_idx:
            r = new.iloc[int(i)]
            hit = xdf[(xdf["pn"] == r["pn"]) & (xdf["figure_key"] == r["figure_key"])]
            if hit.empty or hit.iloc[0]["aim_path"] != r["aim_path"]:
                mism += 1
        sec["metrics"]["random_400_mismatches"] = int(mism)
        if mism:
            fail(sec, f"{mism}/400 random rows xlsx!=csv")
    except Exception as e:
        fail(sec, f"xlsx read failed: {e}")

    # --- D. Sep21 vs Oct7 coverage / euro ---
    sec = section(report, "D_sep21_vs_oct7_coverage")
    # PN-level primary AIM (first nonblank, else first)
    def pn_aim(df):
        g = df.sort_values(["has_aim", "eur"], ascending=[False, False])
        return g.groupby("pn", as_index=False).first()

    new_pn = pn_aim(new)
    old_pn = pn_aim(old)
    both = new_pn.merge(old_pn, on="pn", how="outer", suffixes=("_n", "_o"), indicator=True)
    sec["metrics"]["pn_only_new"] = int((both["_merge"] == "left_only").sum())
    sec["metrics"]["pn_only_old"] = int((both["_merge"] == "right_only").sum())
    sec["metrics"]["pn_both"] = int((both["_merge"] == "both").sum())

    both_inner = both[both["_merge"] == "both"].copy()
    filled = both_inner[(~both_inner["has_aim_o"].astype(bool)) & (both_inner["has_aim_n"].astype(bool))]
    lost = both_inner[(both_inner["has_aim_o"].astype(bool)) & (~both_inner["has_aim_n"].astype(bool))]
    changed = both_inner[
        (both_inner["has_aim_o"].astype(bool))
        & (both_inner["has_aim_n"].astype(bool))
        & (both_inner["aim_path_o"] != both_inner["aim_path_n"])
    ]
    same = both_inner[
        (both_inner["has_aim_o"].astype(bool))
        & (both_inner["has_aim_n"].astype(bool))
        & (both_inner["aim_path_o"] == both_inner["aim_path_n"])
    ]
    sec["metrics"].update(
        {
            "pn_aim_filled_was_blank": int(len(filled)),
            "pn_aim_lost_was_filled": int(len(lost)),
            "pn_aim_path_changed": int(len(changed)),
            "pn_aim_path_same": int(len(same)),
            "eur_new_total": float(new["eur"].sum()),
            "eur_old_total": float(old["eur"].sum()),
            "eur_with_aim_new": float(new.loc[new["has_aim"], "eur"].sum()),
            "eur_with_aim_old": float(old.loc[old["has_aim"], "eur"].sum()),
        }
    )
    # euro coverage on unique PN max eur to avoid figure multiply
    def euro_cov(df):
        u = df.groupby("pn", as_index=False).agg(eur=("eur", "max"), has_aim=("has_aim", "max"))
        tot = float(u["eur"].sum())
        cov = float(u.loc[u["has_aim"], "eur"].sum())
        return tot, cov, (cov / tot * 100 if tot else 0)

    tot_n, cov_n, pct_n = euro_cov(new)
    tot_o, cov_o, pct_o = euro_cov(old)
    sec["metrics"]["eur_cov_pct_new_pnmax"] = round(pct_n, 3)
    sec["metrics"]["eur_cov_pct_old_pnmax"] = round(pct_o, 3)
    sec["metrics"]["eur_cov_abs_new"] = cov_n
    sec["metrics"]["eur_cov_abs_old"] = cov_o
    if pct_n + 0.05 < pct_o:
        fail(sec, f"Euro AIM coverage worse: {pct_n:.2f}% < old {pct_o:.2f}%")
    else:
        note(sec, f"Euro AIM coverage improved or held: {pct_o:.2f}% -> {pct_n:.2f}%")
    if len(lost) > 50:
        fail(sec, f"Lost AIM on {len(lost)} PNs that had AIM on Sep21")
    elif len(lost):
        note(sec, f"Lost AIM on {len(lost)} PNs (sample below)")
        sec["metrics"]["lost_aim_sample"] = lost[["pn", "description_o", "aim_path_o", "eur_o"]].head(30).to_dict("records")

    # --- E. Known remaps / hard holds on EXPORT ---
    sec = section(report, "E_hard_holds_on_export")
    desc = new["description"].fillna("").str.upper()
    path = new["aim_path"].fillna("")
    l1 = new["aim_level_1"].fillna("")

    patterns = {
        "eng_gasket_set_to_transmission": (
            desc.str.contains(r"GASKET\s*SET", regex=True)
            & desc.str.contains(r"\bENG\b|ENGINE|CYL", regex=True)
            & l1.str.contains("Transmission", case=False, na=False)
        ),
        "cyl_hd_gasket_to_transmission": (
            desc.str.contains(r"GASKET", regex=True)
            & desc.str.contains(r"CYL|HEAD|CYLINDER", regex=True)
            & l1.str.contains("Transmission", case=False, na=False)
        ),
        "any_gasket_set_to_transmission": (
            desc.str.contains(r"GASKET\s*SET", regex=True)
            & l1.str.contains("Transmission", case=False, na=False)
        ),
        "antenna_not_radio": (
            desc.str.contains(r"ANTENNA", regex=True)
            & new["has_aim"]
            & ~l1.str.contains("Radio|Audio|Cabin|Electrical|Body", case=False, na=False, regex=True)
            & ~path.str.contains("Radio", case=False, na=False)
        ),
        "evrv_not_egr": (
            desc.str.contains(r"\bEVRV\b|EGR\s*VALVE|EXHAUST\s*GAS\s*RECIRC", regex=True)
            & new["has_aim"]
            & ~path.str.contains(r"EGR|Emission|Intake", case=False, na=False, regex=True)
        ),
        "def_injector_misfiled": (
            desc.str.contains(r"DEF|UREA|ADBLUE|SCR", regex=True)
            & desc.str.contains(r"INJECT", regex=True)
            & new["has_aim"]
            & ~path.str.contains(r"Intake Exhaust Emission|Emission|DEF|Urea|SCR", case=False, na=False, regex=True)
        ),
        "trans_asm_to_literature": (
            desc.str.contains(r"TRANS|GEARBOX|AT\s*ASM|MT\s*ASM", regex=True)
            & l1.str.contains("Literature|Manual|Publication", case=False, na=False, regex=True)
        ),
        "air_valve_to_steering": (
            desc.str.contains(r"AIR\s*VALVE|VALVE;\s*AIR", regex=True)
            & l1.str.contains("Steering", case=False, na=False)
        ),
    }
    hold_counts = {}
    hold_samples = {}
    for name, mask in patterns.items():
        n = int(mask.sum())
        hold_counts[name] = n
        if n:
            hold_samples[name] = (
                new.loc[mask, ["pn", "description", "aim_path", "eur"]]
                .drop_duplicates("pn")
                .head(15)
                .to_dict("records")
            )
            # critical holds that must be 0 for eng gasket
            if name in ("eng_gasket_set_to_transmission",):
                fail(sec, f"{name} = {n} (must be 0)")
            elif name in ("cyl_hd_gasket_to_transmission", "any_gasket_set_to_transmission") and n > 0:
                # residual known outside GO — warn as fail if in CHANGED/FILLED set
                note(sec, f"{name} = {n} residual on export (inspect samples)")
            elif n > 25:
                fail(sec, f"{name} = {n} high")
            else:
                note(sec, f"{name} = {n}")
        else:
            note(sec, f"{name} = 0")
    sec["metrics"]["hold_counts"] = hold_counts
    sec["metrics"]["hold_samples"] = hold_samples

    # Oct4 remap groups from changes file if present
    if CLASS_CHANGES.exists():
        ch = pd.read_csv(CLASS_CHANGES, dtype=str, keep_default_na=False)
        sec["metrics"]["changes_rows"] = int(len(ch))
        # find group column
        gcol = None
        for c in ch.columns:
            if "group" in c.lower() or c.lower() in ("change_group", "pile", "bucket"):
                gcol = c
                break
        if gcol is None:
            # peek columns
            sec["metrics"]["changes_cols"] = list(ch.columns)[:40]
        else:
            sec["metrics"]["changes_by_group"] = Counter(ch[gcol].tolist()).most_common(20)

    # Verify specific known PNs from doublecheck
    sec2 = section(report, "E2_known_pn_spot")
    known = {
        "1878148072": "Engine",  # gasket set sample
    }
    # pull gasket/EVRV/antenna/DEF from old vs new where description matches
    for label, dmask in [
        ("gasket_set_eng", desc.str.contains(r"GASKET\s*SET", regex=True) & desc.str.contains(r"ENG|ENGINE", regex=True)),
        ("antenna", desc.str.contains(r"ANTENNA", regex=True)),
        ("evrv", desc.str.contains(r"\bEVRV\b", regex=True)),
        ("def_inj", desc.str.contains(r"INJECT", regex=True) & desc.str.contains(r"DEF|UREA|SCR", regex=True)),
    ]:
        sub = new.loc[dmask & new["has_aim"]].drop_duplicates("pn")
        l1c = Counter(sub["aim_level_1"].tolist())
        sec2["metrics"][f"{label}_n"] = int(len(sub))
        sec2["metrics"][f"{label}_l1"] = l1c.most_common(8)
        # compare old
        sub_o = old.loc[
            old["description"].fillna("").str.upper().str.contains(
                {"gasket_set_eng": r"GASKET\s*SET", "antenna": r"ANTENNA", "evrv": r"\bEVRV\b", "def_inj": r"INJECT"}[label],
                regex=True,
            )
        ]
        if label == "gasket_set_eng":
            sub_o = sub_o[sub_o["description"].fillna("").str.upper().str.contains(r"ENG|ENGINE", regex=True)]
        if label == "def_inj":
            sub_o = sub_o[sub_o["description"].fillna("").str.upper().str.contains(r"DEF|UREA|SCR", regex=True)]
        sub_o = sub_o[sub_o["has_aim"]].drop_duplicates("pn")
        sec2["metrics"][f"{label}_old_l1"] = Counter(sub_o["aim_level_1"].tolist()).most_common(8)
        # improvement: fewer Transmission for gasket
        if label == "gasket_set_eng":
            bad_n = int((sub["aim_level_1"].str.contains("Transmission", case=False, na=False)).sum())
            bad_o = int((sub_o["aim_level_1"].str.contains("Transmission", case=False, na=False)).sum())
            sec2["metrics"]["gasket_set_eng_trans_new"] = bad_n
            sec2["metrics"]["gasket_set_eng_trans_old"] = bad_o
            if bad_n > bad_o:
                fail(sec2, f"More eng gasket sets under Transmission than Sep21 ({bad_n}>{bad_o})")
            elif bad_n == 0 and bad_o > 0:
                note(sec2, f"Eng gasket sets under Transmission cleared: {bad_o} -> 0")
            else:
                note(sec2, f"Eng gasket Transmission: {bad_o} -> {bad_n}")

    for pn, expect_l1 in known.items():
        rows = new[new["pn"] == pn.zfill(10)]
        if rows.empty:
            fail(sec2, f"Known PN {pn} missing from export")
        else:
            l1v = rows.iloc[0]["aim_level_1"]
            sec2["metrics"][f"pn_{pn}"] = rows.iloc[0][["description", "aim_path"]].to_dict()
            if expect_l1.lower() not in l1v.lower():
                fail(sec2, f"PN {pn} L1={l1v} expected contains {expect_l1}")

    # --- F. Export vs internal classification release alignment ---
    sec = section(report, "F_export_vs_class_release")
    cls = pd.read_csv(CLASS_REL, dtype=str, keep_default_na=False)
    # find AIM cols
    aim_cols = [c for c in cls.columns if re.search(r"aim_l1|aim_level_1|aim_l1_fixed", c, re.I)]
    sec["metrics"]["class_cols_aimish"] = aim_cols[:20]
    sec["metrics"]["class_rows"] = int(len(cls))
    pn_col = "part_number" if "part_number" in cls.columns else ("pn" if "pn" in cls.columns else None)
    if pn_col is None:
        fail(sec, "no part_number on class release")
    else:
        cls["pn"] = cls[pn_col].astype(str).str.strip().str.zfill(10)
        # map fixed AIM
        def pick(*names):
            for n in names:
                if n in cls.columns:
                    return n
            return None

        c1 = pick("aim_l1_fixed", "aim_level_1", "aim_l1")
        c2 = pick("aim_l2_fixed", "aim_level_2", "aim_l2")
        c3 = pick("aim_l3_fixed", "aim_level_3", "aim_l3")
        sec["metrics"]["mapped_cols"] = [c1, c2, c3]
        if not c1:
            fail(sec, "cannot find AIM L1 on class release")
        else:
            cls["aim_path_c"] = (
                cls[c1].fillna("").astype(str).str.strip()
                + " > "
                + (cls[c2].fillna("").astype(str).str.strip() if c2 else "")
                + " > "
                + (cls[c3].fillna("").astype(str).str.strip() if c3 else "")
            )
            cls["has_aim_c"] = ~blank(cls[c1])
            # PN grain
            cls_pn = cls.sort_values("has_aim_c", ascending=False).groupby("pn", as_index=False).first()
            m = new_pn.merge(cls_pn[["pn", "aim_path_c", "has_aim_c"]], on="pn", how="left")
            both_aim = m[m["has_aim"] & m["has_aim_c"].fillna(False)]
            differ = both_aim[both_aim["aim_path"] != both_aim["aim_path_c"]]
            sec["metrics"]["export_vs_class_both_aim"] = int(len(both_aim))
            sec["metrics"]["export_vs_class_aim_differ"] = int(len(differ))
            if len(differ):
                # sample
                sec["metrics"]["differ_sample"] = differ[["pn", "description", "aim_path", "aim_path_c"]].head(25).to_dict("records")
                if len(differ) > 20:
                    fail(sec, f"Export AIM != class release on {len(differ)} PNs")
                else:
                    note(sec, f"Export AIM differs on {len(differ)} PNs (small)")
            else:
                note(sec, "Export PN AIM paths match class release where both filled")
            # export has AIM but class blank
            exp_only = m[m["has_aim"] & ~m["has_aim_c"].fillna(False)]
            cls_only = m[~m["has_aim"] & m["has_aim_c"].fillna(False)]
            sec["metrics"]["aim_export_not_class"] = int(len(exp_only))
            sec["metrics"]["aim_class_not_export"] = int(len(cls_only))
            if len(cls_only) > 100:
                fail(sec, f"Class has AIM but export blank on {len(cls_only)} PNs")

    # --- G. Master alignment ---
    sec = section(report, "G_master_alignment")
    if MASTER.exists():
        mast = pd.read_csv(MASTER, dtype=str, keep_default_na=False, usecols=lambda c: True)
        # find pn + aim
        pc = "part_number" if "part_number" in mast.columns else None
        if pc is None:
            for c in mast.columns:
                if "part" in c.lower() and "num" in c.lower():
                    pc = c
                    break
        a1 = next((c for c in mast.columns if c in ("aim_l1_fixed", "aim_level_1", "aim_l1")), None)
        a2 = next((c for c in mast.columns if c in ("aim_l2_fixed", "aim_level_2", "aim_l2")), None)
        a3 = next((c for c in mast.columns if c in ("aim_l3_fixed", "aim_level_3", "aim_l3")), None)
        sec["metrics"]["master_cols_used"] = [pc, a1, a2, a3]
        if pc and a1:
            mast["pn"] = mast[pc].astype(str).str.strip().str.zfill(10)
            mast["aim_path_m"] = (
                mast[a1].fillna("").astype(str).str.strip()
                + " > "
                + (mast[a2].fillna("").astype(str).str.strip() if a2 else "")
                + " > "
                + (mast[a3].fillna("").astype(str).str.strip() if a3 else "")
            )
            mast["has_aim_m"] = ~blank(mast[a1])
            mpn = mast.sort_values("has_aim_m", ascending=False).groupby("pn", as_index=False).first()
            j = new_pn.merge(mpn[["pn", "aim_path_m", "has_aim_m"]], on="pn", how="inner")
            both = j[j["has_aim"] & j["has_aim_m"]]
            diff = both[both["aim_path"] != both["aim_path_m"]]
            sec["metrics"]["master_join_pns"] = int(len(j))
            sec["metrics"]["master_both_aim_differ"] = int(len(diff))
            if len(diff):
                sec["metrics"]["master_differ_sample"] = diff[["pn", "description", "aim_path", "aim_path_m"]].head(20).to_dict("records")
                fail(sec, f"Export vs master AIM differ on {len(diff)} PNs")
            else:
                note(sec, "Export matches master AIM where both filled")
        else:
            fail(sec, "master AIM columns not found")
    else:
        fail(sec, "master missing")

    # --- H. Sales euro independent coverage ---
    sec = section(report, "H_sales_fact_euro_coverage")
    try:
        # try common column names
        sf = pd.read_parquet(SALES)
        sec["metrics"]["sales_cols"] = list(sf.columns)[:40]
        pn_s = next((c for c in sf.columns if c.lower() in ("part_number", "material", "pn", "part_no")), None)
        eur_s = next((c for c in sf.columns if c.lower() in ("net_sales_value", "net_value", "billed_eur", "sales_eur", "net_sales_eur")), None)
        date_s = next((c for c in sf.columns if c.lower() in ("billing_date", "posting_date", "invoice_date", "date")), None)
        if not pn_s or not eur_s:
            fail(sec, f"sales_fact columns not mapped pn={pn_s} eur={eur_s}")
        else:
            s = sf[[pn_s, eur_s] + ([date_s] if date_s else [])].copy()
            s["pn"] = s[pn_s].astype(str).str.strip().str.zfill(10)
            s["eur"] = pd.to_numeric(s[eur_s], errors="coerce").fillna(0.0)
            if date_s:
                s["dt"] = pd.to_datetime(s[date_s], errors="coerce")
                s = s[(s["dt"] >= "2025-01-01") & (s["dt"] <= "2026-09-30")]
            billed = s.groupby("pn", as_index=False)["eur"].sum()
            billed = billed[billed["eur"] != 0]
            jn = billed.merge(new_pn[["pn", "has_aim", "aim_path", "description"]], on="pn", how="left")
            jo = billed.merge(old_pn[["pn", "has_aim", "aim_path"]], on="pn", how="left")
            tot = float(billed["eur"].sum())
            cov_n = float(jn.loc[jn["has_aim"].fillna(False), "eur"].sum())
            cov_o = float(jo.loc[jo["has_aim"].fillna(False), "eur"].sum())
            sec["metrics"].update(
                {
                    "sales_pn_count": int(len(billed)),
                    "sales_eur_total": tot,
                    "sales_eur_aim_new": cov_n,
                    "sales_eur_aim_old": cov_o,
                    "sales_pct_aim_new": round(100 * cov_n / tot, 3) if tot else 0,
                    "sales_pct_aim_old": round(100 * cov_o / tot, 3) if tot else 0,
                    "billed_pn_missing_from_export": int(jn["has_aim"].isna().sum()),
                }
            )
            if cov_n + 1 < cov_o:
                fail(sec, "Independent sales euro AIM coverage fell vs Sep21")
            else:
                note(
                    sec,
                    f"Sales euro AIM cover {sec['metrics']['sales_pct_aim_old']}% -> {sec['metrics']['sales_pct_aim_new']}%",
                )
            # top 50 billed blank AIM on new
            blank_top = jn[~jn["has_aim"].fillna(False)].nlargest(40, "eur")
            sec["metrics"]["top_blank_aim_billed"] = blank_top[["pn", "eur", "description"]].to_dict("records")
    except Exception as e:
        fail(sec, f"sales_fact check failed: {e}")

    # --- I. Vocabulary / hierarchy sanity ---
    sec = section(report, "I_vocabulary")
    l1s = sorted(new.loc[new["has_aim"], "aim_level_1"].unique())
    l2s = sorted((new.loc[new["has_aim"], "aim_level_1"] + "|" + new.loc[new["has_aim"], "aim_level_2"]).unique())
    sec["metrics"]["l1_count"] = len(l1s)
    sec["metrics"]["l1_list"] = l1s
    sec["metrics"]["l12_count"] = len(l2s)
    # orphan L2 empty with L1
    orphan = new[new["has_aim"] & blank(new["aim_level_2"])]
    sec["metrics"]["l1_without_l2"] = int(len(orphan))
    if len(orphan) > 100:
        fail(sec, f"{len(orphan)} rows L1 without L2")
    # new L1 vs old
    old_l1 = set(old.loc[old["has_aim"], "aim_level_1"].unique())
    new_l1 = set(l1s)
    sec["metrics"]["l1_added"] = sorted(new_l1 - old_l1)
    sec["metrics"]["l1_removed"] = sorted(old_l1 - new_l1)
    if sec["metrics"]["l1_added"]:
        note(sec, f"New L1 labels vs Sep21: {sec['metrics']['l1_added']}")

    # --- J. Massive random description vs family heuristics ---
    sec = section(report, "J_random_desc_vs_family")
    # rules: if desc contains keyword, L1 should usually match family set
    rules = [
        (r"\bFILTER\b", ["Filter", "Lubricat", "Fuel", "Intake", "Engine", "Cooling", "Air"], "filter"),
        (r"\bBRAKE\b|PAD;|SHOE;", ["Brake", "Chassis", "Axle"], "brake"),
        (r"\bCLUTCH\b", ["Clutch", "Transmission", "Powertrain"], "clutch"),
        (r"\bTURBO\b", ["Engine", "Intake", "Turbo", "Emission"], "turbo"),
        (r"\bINJECTOR\b", ["Engine", "Fuel", "Intake", "Emission"], "injector"),
        (r"\bRADIATOR\b|\bCOOLANT\b", ["Cooling", "Engine"], "cooling"),
        (r"\bSTEERING\b", ["Steering"], "steering"),
        (r"\bSUSPENSION\b|\bSPRING\b|\bSHOCK\b", ["Suspension", "Chassis", "Axle", "Frame"], "suspension"),
        (r"\bBATTERY\b", ["Electrical", "Battery", "Starting"], "battery"),
        (r"\bALTERNATOR\b|\bSTARTER\b", ["Electrical", "Starting", "Charging", "Engine"], "charge_start"),
        (r"\bMIRROR\b|\bDOOR\b|\bCAB\b", ["Cab", "Body", "Cabin"], "cab"),
        (r"\bOIL\s*PUMP\b|\bWATER\s*PUMP\b", ["Engine", "Cooling", "Lubricat"], "pump"),
    ]
    filled_pns = set(filled["pn"]) if len(filled) else set()
    changed_pns = set(changed["pn"]) if len(changed) else set()
    # sample pools
    pools = {
        "filled_new": new_pn[new_pn["pn"].isin(filled_pns) & new_pn["has_aim"]],
        "changed": new_pn[new_pn["pn"].isin(changed_pns)],
        "unchanged_aim": new_pn[new_pn["pn"].isin(set(same["pn"]) if len(same) else set())],
        "top_eur_aim": new_pn[new_pn["has_aim"]].nlargest(2000, "eur"),
        "random_aim": new_pn[new_pn["has_aim"]].sample(n=min(2500, int(new_pn["has_aim"].sum())), random_state=20261011),
    }
    heuristic_hits = []
    rule_stats = {}
    for pool_name, pool in pools.items():
        if pool.empty:
            rule_stats[pool_name] = {"n": 0}
            continue
        n = min(800, len(pool))
        samp = pool.sample(n=n, random_state=abs(hash(pool_name)) % (2**31))
        bad = []
        checked = 0
        for _, row in samp.iterrows():
            d = str(row.get("description", "")).upper()
            l1v = str(row.get("aim_level_1", ""))
            pathv = str(row.get("aim_path", ""))
            for pat, ok_l1, rname in rules:
                if re.search(pat, d, re.I):
                    checked += 1
                    if not any(x.lower() in l1v.lower() or x.lower() in pathv.lower() for x in ok_l1):
                        bad.append(
                            {
                                "pool": pool_name,
                                "rule": rname,
                                "pn": row["pn"],
                                "description": row.get("description"),
                                "aim_path": pathv,
                                "eur": float(row.get("eur") or 0),
                            }
                        )
                    break
        rate = (len(bad) / checked * 100) if checked else 0
        rule_stats[pool_name] = {
            "sampled": int(n),
            "rule_checked": int(checked),
            "suspect": int(len(bad)),
            "suspect_pct_of_checked": round(rate, 2),
        }
        heuristic_hits.extend(bad[:40])
        if pool_name in ("filled_new", "changed") and rate > 15 and checked >= 50:
            fail(sec, f"{pool_name} heuristic suspects {rate:.1f}% ({len(bad)}/{checked})")
        elif rate > 25 and checked >= 80:
            fail(sec, f"{pool_name} heuristic suspects high {rate:.1f}%")
        else:
            note(sec, f"{pool_name}: suspects {len(bad)}/{checked} ({rate:.1f}%)")
    sec["metrics"]["rule_stats"] = rule_stats
    sec["metrics"]["suspect_samples"] = heuristic_hits[:80]
    report["random_samples"]["heuristic_suspects_n"] = len(heuristic_hits)

    # --- K. Random manual-style dump (200 rows) for human-readable QA ---
    sec = section(report, "K_random_dump")
    dumps = {}
    for name, pool, n in [
        ("filled_200", new_pn[new_pn["pn"].isin(filled_pns)], 200),
        ("changed_150", new_pn[new_pn["pn"].isin(changed_pns)], 150),
        ("top_eur_100", new_pn[new_pn["has_aim"]].nlargest(300, "eur"), 100),
        ("still_blank_top_eur_80", new_pn[~new_pn["has_aim"]].nlargest(200, "eur"), 80),
    ]:
        if pool.empty:
            dumps[name] = []
            continue
        take = min(n, len(pool))
        cols = (
            ["pn", "description", "aim_path", "eur", "aim_source"]
            if "aim_source" in pool.columns
            else ["pn", "description", "aim_path", "eur"]
        )
        dumps[name] = (
            pool.sample(n=take, random_state=42)
            .sort_values("eur", ascending=False)[cols]
            .to_dict("records")
        )
    # for changed, include old path
    if len(changed):
        ch_s = changed.sample(n=min(120, len(changed)), random_state=7)
        dumps["changed_with_old_120"] = ch_s[["pn", "description_n", "aim_path_o", "aim_path_n", "eur_n"]].rename(
            columns={"description_n": "description", "eur_n": "eur"}
        ).to_dict("records")
    sec["metrics"]["dump_counts"] = {k: len(v) for k, v in dumps.items()}
    report["random_samples"]["dumps"] = dumps

    # --- L. EQ skipped still absent ---
    sec = section(report, "L_eq_skipped")
    if CLASS_EQ_SKIP.exists():
        sk = pd.read_csv(CLASS_EQ_SKIP, dtype=str, keep_default_na=False)
        sec["metrics"]["eq_skipped_rows"] = int(len(sk))
        sec["metrics"]["eq_skipped_cols"] = list(sk.columns)[:20]
        pcol = next((c for c in sk.columns if "part" in c.lower()), None)
        if pcol:
            skp = sk[pcol].astype(str).str.zfill(10)
            in_new = new_pn[new_pn["pn"].isin(set(skp))]
            sec["metrics"]["skipped_present_in_export"] = int(len(in_new))
            sec["metrics"]["skipped_with_aim_in_export"] = int(in_new["has_aim"].sum())
            note(sec, f"EQ skipped {len(sk)}; in export with AIM={int(in_new['has_aim'].sum())}")
    else:
        note(sec, "no eq_skipped file")

    # --- M. Line kind / non-parts ---
    sec = section(report, "M_line_kind")
    if "line_kind" in new.columns:
        sec["metrics"]["line_kind_new"] = Counter(new["line_kind"].tolist()).most_common(20)
        sec["metrics"]["line_kind_old"] = Counter(old["line_kind"].tolist()).most_common(20)
        # parts with absurd L1
        weird = new[(new["line_kind"] == "part") & new["aim_level_1"].str.contains("freight|rebate|demurrage", case=False, na=False)]
        sec["metrics"]["part_rows_freightish_aim"] = int(len(weird))
        if len(weird):
            fail(sec, f"part rows with freightish AIM: {len(weird)}")

    # --- N. Leading zeros preserved ---
    sec = section(report, "N_leading_zeros")
    lz = new[new["part_number"].astype(str).str.match(r"^0")]
    sec["metrics"]["leading_zero_rows"] = int(len(lz))
    sec["metrics"]["leading_zero_pns"] = int(lz["pn"].nunique())
    if sec["metrics"]["leading_zero_pns"] < 1000:
        fail(sec, "too few leading-zero PNs")
    else:
        note(sec, f"leading-zero PNs={sec['metrics']['leading_zero_pns']}")

    # --- O. Recompute better-than / safe ---
    fails_all = []
    for k, v in report["sections"].items():
        if not v.get("ok", True):
            fails_all.extend([f"[{k}] {m}" for m in v.get("fails", [])])

    better = (
        report["sections"]["D_sep21_vs_oct7_coverage"]["metrics"].get("eur_cov_pct_new_pnmax", 0)
        >= report["sections"]["D_sep21_vs_oct7_coverage"]["metrics"].get("eur_cov_pct_old_pnmax", 0)
        and report["sections"]["D_sep21_vs_oct7_coverage"]["metrics"].get("pn_aim_filled_was_blank", 0) > 1000
        and report["sections"]["D_sep21_vs_oct7_coverage"]["metrics"].get("pn_aim_lost_was_filled", 0) <= 50
        and report["sections"]["E_hard_holds_on_export"]["metrics"]["hold_counts"].get("eng_gasket_set_to_transmission", 99) == 0
    )
    # hard blockers
    blockers = [f for f in fails_all if any(x in f for x in ("hash", "xlsx", "Eng gasket", "eng_gasket", "master AIM differ", "CSV hash"))]
    soft = [f for f in fails_all if f not in blockers]

    report["better_than_sep21"] = bool(better)
    report["safe_to_send_bart"] = bool(better and len(blockers) == 0)
    report["verdict"] = (
        "PASS_BETTER"
        if report["safe_to_send_bart"] and not soft
        else ("PASS_WITH_NOTES" if report["safe_to_send_bart"] else "FAIL")
    )
    report["fail_blockers"] = blockers
    report["fail_soft"] = soft
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()

    OUT_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # Markdown summary
    d = report["sections"]["D_sep21_vs_oct7_coverage"]["metrics"]
    h = report["sections"]["H_sales_fact_euro_coverage"]["metrics"]
    e = report["sections"]["E_hard_holds_on_export"]["metrics"]["hold_counts"]
    lines = [
        f"# AIM PBI export deep QA — 2026-10-11",
        "",
        f"**Verdict: {report['verdict']}**",
        f"- Better than Sep-21: **{report['better_than_sep21']}**",
        f"- Safe to send Bart (no blockers): **{report['safe_to_send_bart']}**",
        f"- Started: {report['started_utc']}",
        f"- Finished: {report['finished_utc']}",
        "",
        "## Coverage",
        f"- Rows: {d.get('old_rows') if False else report['sections']['B_load_compare_shape']['metrics']['old_rows']} → {report['sections']['B_load_compare_shape']['metrics']['new_rows']}",
        f"- PNs with AIM family: {report['sections']['B_load_compare_shape']['metrics']['old_aim_unique_pn']} → {report['sections']['B_load_compare_shape']['metrics']['new_aim_unique_pn']}",
        f"- Filled blank→AIM: {d['pn_aim_filled_was_blank']}",
        f"- Lost AIM: {d['pn_aim_lost_was_filled']}",
        f"- Path changed: {d['pn_aim_path_changed']}",
        f"- Export euro AIM cover (pn max): {d['eur_cov_pct_old_pnmax']}% → {d['eur_cov_pct_new_pnmax']}%",
        f"- Sales-fact euro AIM cover: {h.get('sales_pct_aim_old')}% → {h.get('sales_pct_aim_new')}%",
        "",
        "## Hard holds on export",
    ]
    for k, v in e.items():
        lines.append(f"- `{k}` = {v}")
    lines += ["", "## Blockers"]
    if blockers:
        lines += [f"- {b}" for b in blockers]
    else:
        lines.append("- none")
    lines += ["", "## Soft fails / notes"]
    if soft:
        lines += [f"- {b}" for b in soft]
    else:
        lines.append("- none")
    lines += ["", "## Section OK flags"]
    for k, v in report["sections"].items():
        lines.append(f"- {'PASS' if v.get('ok') else 'FAIL'} `{k}`")
        for n_ in v.get("notes", [])[:6]:
            lines.append(f"  - {n_}")
        for f_ in v.get("fails", [])[:6]:
            lines.append(f"  - FAIL: {f_}")
    lines += [
        "",
        "## Absolute paths",
        f"- {NEW_CSV}",
        f"- {NEW_XLSX}",
        f"- {OUT_JSON}",
        f"- {OUT_MD}",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "better": report["better_than_sep21"], "safe": report["safe_to_send_bart"], "blockers": blockers, "soft_n": len(soft), "out": str(OUT_MD)}, indent=2))
    return 0 if report["safe_to_send_bart"] else 2


if __name__ == "__main__":
    sys.exit(main())
