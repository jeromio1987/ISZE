#!/usr/bin/env python3
"""
Hotfix AIM residues Jerome asked to fix 2026-10-11, then cut release 2026-10-11.

Fixes (existing AIM leaves only — no new labels):
  1) GASKET; CYL HD under Transmission  -> Engine > Gasket & Sealing > Gasket
  2) TRANSMISSION ASM under Literature  -> Transmission > Case > Case Cover
  3) 8973586990 turbo water return      -> Intake Exhaust Emission > Turbo > Turbocharger
  4) 5873113800 turbo kit               -> Intake Exhaust Emission > Turbo > Turbocharger

Touches: classification release, live overlay, aim_master_v2, RELEASES.json.
Then run export_aim_pn_categories_figkey_xlsx.py separately.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
REL = DER / "_releases"
BUILD = ROOT / "01_data" / "91_build"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BASE_REL = REL / "aim_pn_classification_release_2026-10-07.csv"
OUT_REL = REL / "aim_pn_classification_release_2026-10-11.csv"
OUT_CHANGES = REL / "aim_pn_classification_release_2026-10-11.changes.csv"
OUT_META = REL / "aim_pn_classification_release_2026-10-11.meta.json"
RELEASES = REL / "RELEASES.json"
MASTER = DER / "aim_master_v2.csv"
LIVE = DER / "aim_pn_classification_20260920.csv"

TARGET = {
    "cyl_hd_gasket": ("Engine", "Gasket & Sealing", "Gasket"),
    "trans_asm": ("Transmission", "Case", "Case Cover"),
    "turbo_water": ("Intake Exhaust Emission", "Turbo", "Turbocharger"),
    "turbo_kit": ("Intake Exhaust Emission", "Turbo", "Turbocharger"),
}
EXTRA_PNS = {
    "8973586990": "turbo_water",
    "5873113800": "turbo_kit",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def zpn(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.zfill(10)


def backup(p: Path) -> Path:
    b = p.with_name(p.name + f".bak_pre_hotfix_20261011_{STAMP}")
    shutil.copy2(p, b)
    return b


def apply_triple(df: pd.DataFrame, mask: pd.Series, triple: tuple[str, str, str], src: str) -> int:
    n = int(mask.sum())
    if n == 0:
        return 0
    l1, l2, l3 = triple
    df.loc[mask, "aim_l1_fixed"] = l1
    df.loc[mask, "aim_l2_fixed"] = l2
    if "aim_l3_fixed" in df.columns:
        df.loc[mask, "aim_l3_fixed"] = l3
    if "aim_l3" in df.columns and "aim_l3_fixed" not in df.columns:
        df.loc[mask, "aim_l3"] = l3
    elif "aim_l3" in df.columns:
        df.loc[mask, "aim_l3"] = l3
    if "aim_source" in df.columns:
        prev = df.loc[mask, "aim_source"].fillna("").astype(str)
        df.loc[mask, "aim_source"] = prev.where(prev.str.contains("hotfix_20261011"), prev + "|hotfix_20261011")
        df.loc[mask, "aim_source"] = df.loc[mask, "aim_source"].str.replace(r"^\|", "", regex=True)
    if "has_aim" in df.columns:
        df.loc[mask, "has_aim"] = "1"
    if "aim_changed" in df.columns:
        df.loc[mask, "aim_changed"] = "1"
    return n


def select_masks(df: pd.DataFrame, desc_col: str) -> dict[str, pd.Series]:
    d = df[desc_col].fillna("").astype(str).str.upper()
    pn = zpn(df["part_number"])
    cyl = (
        d.str.contains(r"GASKET", regex=True)
        & d.str.contains(r"CYL|HEAD", regex=True)
        & ~d.str.contains(r"GASKET\s*SET", regex=True)
        & df["aim_l1_fixed"].astype(str).str.contains("Transmission", case=False, na=False)
    )
    # also catch GASKET; CYL HD even if L1 already partially fixed oddly
    cyl = cyl | (
        d.str.fullmatch(r"GASKET;\s*CYL\s*HD")
        & df["aim_l1_fixed"].astype(str).str.contains("Transmission", case=False, na=False)
    )
    lit = d.str.contains(r"TRANSMISSION\s*ASM", regex=True) & df["aim_l1_fixed"].astype(str).str.contains(
        "Literature", case=False, na=False
    )
    turbo_water = pn.eq("8973586990")
    turbo_kit = pn.eq("5873113800")
    return {
        "cyl_hd_gasket": cyl,
        "trans_asm": lit,
        "turbo_water": turbo_water,
        "turbo_kit": turbo_kit,
    }


def main() -> None:
    assert BASE_REL.exists(), BASE_REL
    backups = {
        "release_base": str(backup(BASE_REL)),
        "master": str(backup(MASTER)),
        "live": str(backup(LIVE)),
        "releases_json": str(backup(RELEASES)),
    }

    rel = pd.read_csv(BASE_REL, dtype=str, keep_default_na=False)
    for c in rel.columns:
        rel[c] = rel[c].astype(str).str.strip()
    desc_col = "description_norm" if "description_norm" in rel.columns else "description"
    masks = select_masks(rel, desc_col)

    change_rows = []
    counts = {}
    for key, mask in masks.items():
        before = rel.loc[mask, ["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]].copy()
        n = apply_triple(rel, mask, TARGET[key], key)
        counts[key] = n
        after = rel.loc[mask, ["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]]
        for pn in before["part_number"]:
            b = before[before["part_number"] == pn].iloc[0]
            a = after[after["part_number"] == pn].iloc[0]
            for col in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"):
                if b[col] != a[col]:
                    change_rows.append(
                        {
                            "part_number": str(pn).zfill(10),
                            "change_group": key,
                            "column": col,
                            "before": b[col],
                            "after": a[col],
                        }
                    )

    # zero-check: no literature left on transmission asm; no cyl hd gasket on transmission
    d = rel[desc_col].str.upper()
    assert not (
        d.str.contains(r"TRANSMISSION\s*ASM")
        & rel["aim_l1_fixed"].str.contains("Literature", case=False, na=False)
    ).any()
    assert not (
        d.str.contains(r"GASKET")
        & d.str.contains(r"CYL|HEAD")
        & ~d.str.contains(r"GASKET\s*SET")
        & rel["aim_l1_fixed"].str.contains("Transmission", case=False, na=False)
    ).any()
    for pn, key in EXTRA_PNS.items():
        row = rel[zpn(rel["part_number"]) == pn]
        assert len(row) == 1, pn
        assert tuple(row.iloc[0][["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]]) == TARGET[key]

    if OUT_REL.exists():
        backup(OUT_REL)
    rel.to_csv(OUT_REL, index=False, encoding="utf-8")
    pd.DataFrame(change_rows).to_csv(OUT_CHANGES, index=False, encoding="utf-8")
    rel_sha = sha256(OUT_REL)

    # Sync master
    master = pd.read_csv(MASTER, dtype=str, keep_default_na=False)
    for c in master.columns:
        master[c] = master[c].astype(str).str.strip()
    mp = zpn(master["part_number"])
    # map from release
    rmap = rel.copy()
    rmap["_k"] = zpn(rmap["part_number"])
    rmap = rmap.drop_duplicates("_k", keep="first").set_index("_k")
    touched = set()
    for key, mask in masks.items():
        pns = set(zpn(rel.loc[mask, "part_number"]))
        touched |= pns
        m = mp.isin(pns)
        l1, l2, l3 = TARGET[key]
        master.loc[m, "aim_l1_fixed"] = l1
        master.loc[m, "aim_l2_fixed"] = l2
        if "aim_l3" in master.columns:
            master.loc[m, "aim_l3"] = l3
        if "has_aim" in master.columns:
            master.loc[m, "has_aim"] = "1"
        if "aim_changed" in master.columns:
            master.loc[m, "aim_changed"] = "1"
        if "aim_source" in master.columns:
            prev = master.loc[m, "aim_source"].fillna("").astype(str)
            master.loc[m, "aim_source"] = prev.where(
                prev.str.contains("hotfix_20261011"), prev + "|hotfix_20261011"
            ).str.replace(r"^\|", "", regex=True)
    master.to_csv(MASTER, index=False, encoding="utf-8")

    # Sync live overlay
    live = pd.read_csv(LIVE, dtype=str, keep_default_na=False)
    for c in live.columns:
        live[c] = live[c].astype(str).str.strip()
    lp = zpn(live["part_number"])
    for key, mask in masks.items():
        pns = set(zpn(rel.loc[mask, "part_number"]))
        m = lp.isin(pns)
        apply_triple(live, m, TARGET[key], key)
    live.to_csv(LIVE, index=False, encoding="utf-8")

    # RELEASES.json — supersede 2026-10-07, approve 2026-10-11
    reg = json.loads(RELEASES.read_text(encoding="utf-8"))
    for c in reg.get("candidates", []):
        if c.get("release_id") == "2026-10-07" and c.get("status") == "APPROVED":
            c["status"] = "SUPERSEDED"
            c["superseded_by"] = "2026-10-11"
            c["superseded_on"] = "2026-10-11"
            c["superseded_note"] = (
                "Superseded when Jerome asked to hotfix cyl-head gasket / transmission-ASM / "
                "turbo water+kit residues on 2026-10-11."
            )
    # remove prior pending 2026-10-11 if any
    reg["candidates"] = [c for c in reg["candidates"] if c.get("release_id") != "2026-10-11"]
    reg["candidates"].append(
        {
            "release_id": "2026-10-11",
            "path": "aim_pn_classification_release_2026-10-11.csv",
            "sha256": rel_sha,
            "status": "APPROVED",
            "rows": int(len(rel)),
            "rows_note": "data rows, header excluded",
            "base_release": "2026-10-07",
            "source": (
                "release 2026-10-07 + hotfix: cyl-head gasket→Engine gasket; "
                "transmission ASM←Literature→Transmission Case; "
                "turbo water return + turbo kit→Turbocharger"
            ),
            "recommendation": "Jerome chat 2026-10-11: fix QA residues and new draft for Bart/PBI",
            "notes": (
                "No new AIM labels. Change log aim_pn_classification_release_2026-10-11.changes.csv. "
                f"Counts: {counts}"
            ),
            "approved_by": "Jerome",
            "approved_on": "2026-10-11",
            "approved_note": (
                "Jerome asked in chat 2026-10-11 to fix the QA residues "
                "(cyl-head gasket under Transmission, transmission ASM under Literature, "
                "turbo water return, turbo kit) and write a new Bart draft."
            ),
        }
    )
    RELEASES.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/_aim_hotfix_residues_release_20261011.py",
        "release_id": "2026-10-11",
        "status": "APPROVED",
        "base_release": "2026-10-07",
        "base_sha256": sha256(BASE_REL),
        "sha256": rel_sha,
        "rows": int(len(rel)),
        "counts": counts,
        "targets": {k: list(v) for k, v in TARGET.items()},
        "change_log": OUT_CHANGES.name,
        "change_log_rows": len(change_rows),
        "parts_touched": len(touched),
        "backups": backups,
        "zero_checks": {
            "cyl_hd_gasket_to_transmission": 0,
            "trans_asm_to_literature": 0,
            "turbo_water_not_turbo": 0,
            "turbo_kit_not_turbo": 0,
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    summary = BUILD / "_aim_hotfix_residues_release_20261011.json"
    summary.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "counts": counts, "sha256": rel_sha, "parts_touched": len(touched)}, indent=2))


if __name__ == "__main__":
    main()
