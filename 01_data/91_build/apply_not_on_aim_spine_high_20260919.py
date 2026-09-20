# -*- coding: utf-8 -*-
"""Apply ready-high Not-on-AIM residual rows to aim_master_v2 (Jerome: Apply 2026-09-19).

Medium / low / needs_eq are NOT applied.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
PRICING = ISZE / "01_data" / "01_Pricing"
MASTER = D / "aim_master_v2.csv"
WORK = D / "pricing_not_on_aim_spine_worklist_20260919.csv"
PATCH = D / "aim_gap_high_conf_patch_residual_20260919.csv"
MARKER = "gap_auto_residual_20260919"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def main() -> None:
    w = pd.read_csv(WORK, dtype=str)
    w["billed_eur"] = pd.to_numeric(w["billed_eur"], errors="coerce")
    high = w[w["work_status"] == "ready_high_apply"].copy()
    high["pn"] = high["pn"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(10)
    assert len(high) > 0, "no ready_high_apply rows"

    patch = high.rename(
        columns={
            "pn": "part_number",
            "proposed_aim_l1": "aim_l1_fixed",
            "proposed_aim_l2": "aim_l2_fixed",
            "proposed_aim_l3": "aim_l3",
        }
    )[
        [
            "part_number",
            "description",
            "billed_eur",
            "aim_l1_fixed",
            "aim_l2_fixed",
            "aim_l3",
            "method",
            "notes",
        ]
    ]
    patch.to_csv(PATCH, index=False)

    bak = D / f"aim_master_v2.csv.bak_pre_residual_high_{STAMP}"
    shutil.copy2(MASTER, bak)
    print("backup", bak)

    m = pd.read_csv(MASTER, dtype=str, low_memory=False)
    m["pn_key"] = m["part_number"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(10)
    patch["pn_key"] = patch["part_number"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(10)

    before_unknown = (
        m["aim_l1_fixed"].fillna("").isin(["", "Unknown", "Unknown Review", "Not on AIM spine"])
    ).sum()

    upd = 0
    add = 0
    for _, r in patch.iterrows():
        hit = m["pn_key"] == r["pn_key"]
        n = int(hit.sum())
        l1 = str(r["aim_l1_fixed"])
        l2 = str(r["aim_l2_fixed"])
        l3 = str(r["aim_l3"])
        if n == 0:
            row = {c: "" for c in m.columns}
            row["part_number"] = r["part_number"]
            row["pn_key"] = r["pn_key"]
            row["description"] = r.get("description") or ""
            row["aim_l1_fixed"] = l1
            row["aim_l2_fixed"] = l2
            row["aim_l3"] = l3
            if "aim_l1" in m.columns:
                row["aim_l1"] = l1
            if "aim_l2" in m.columns:
                row["aim_l2"] = l2
            if "has_aim" in m.columns:
                row["has_aim"] = "1"
            row["aim_changed"] = MARKER
            row["aim_source"] = MARKER
            m = pd.concat([m, pd.DataFrame([row])], ignore_index=True)
            add += 1
            continue
        m.loc[hit, "aim_l1_fixed"] = l1
        m.loc[hit, "aim_l2_fixed"] = l2
        m.loc[hit, "aim_l3"] = l3
        if "aim_l1" in m.columns:
            m.loc[hit, "aim_l1"] = l1
        if "aim_l2" in m.columns:
            m.loc[hit, "aim_l2"] = l2
        if "has_aim" in m.columns:
            m.loc[hit, "has_aim"] = "1"
        prev = m.loc[hit, "aim_changed"].fillna("").astype(str)
        m.loc[hit, "aim_changed"] = [
            MARKER if not x.strip() else (x if MARKER in x else f"{x}|{MARKER}")
            for x in prev
        ]
        src = m.loc[hit, "aim_source"].fillna("").astype(str)
        m.loc[hit, "aim_source"] = [
            MARKER if not x.strip() else (x if MARKER in x else f"{x}|{MARKER}")
            for x in src
        ]
        upd += n

    m = m.drop(columns=["pn_key"])
    m.to_csv(MASTER, index=False)

    after_unknown = (
        m["aim_l1_fixed"].fillna("").isin(["", "Unknown", "Unknown Review", "Not on AIM spine"])
    ).sum()

    print("patch_rows", len(patch))
    print("master_rows_updated", upd)
    print("master_rows_added", add)
    print("unknown_l1_before", int(before_unknown), "after", int(after_unknown))
    print("billed_applied", float(pd.to_numeric(patch["billed_eur"], errors="coerce").sum()))
    print("PATCH", PATCH)
    print("MASTER", MASTER)


if __name__ == "__main__":
    main()
