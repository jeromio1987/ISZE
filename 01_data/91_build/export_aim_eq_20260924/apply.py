"""Write the EXPORT.XLSX classification into the AIM master, the classification
overlay, and the Power BI export pair (CSV + Excel).

What it touches, and why each one:

  aim_master_v2.csv                  the AIM spine every AIM pack reads
  aim_pn_classification_20260920.csv the overlay the Power BI export reads first
  AIM_Master_PN_Categories_*  csv    the Power BI table (CSV)
  AIM_Master_PN_Categories_*  xlsx   the same table for browsing (Excel)

Every file is backed up before it is written. Nothing else is touched, and no
shared pack is rebuilt.

Run:  python 01_data/91_build/export_aim_eq_20260924/apply.py
      python 01_data/91_build/export_aim_eq_20260924/apply.py --apply
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
DER = ROOT / "01_data" / "00_derived"
MASTER = DER / "aim_master_v2.csv"
OVERLAY = DER / "aim_pn_classification_20260920.csv"
EXPORT_CSV = DER / "AIM_Master_PN_Categories_Figkey_20260921.csv"
EXPORT_XLSX = DER / "AIM_Master_PN_Categories_Figkey_20260921.xlsx"
CLASSIFIED = OUT / "classified.csv"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
MARKER = "export_aim_eq_20260924"


def pn_key(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def is_placeholder(v: object) -> bool:
    t = str(v or "").strip().lower()
    return t in ("", "nan", "none", "null", "unknown", "unknown review")


def append_marker(series: pd.Series) -> pd.Series:
    def one(x: object) -> str:
        s = "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x).strip()
        if not s:
            return MARKER
        return s if MARKER in s else f"{s}|{MARKER}"
    return series.map(one)


def main() -> int:
    apply = "--apply" in sys.argv

    c = pd.read_csv(CLASSIFIED, dtype=str, low_memory=False)
    c["pn"] = pn_key(c["pn"])
    fill = c[c["aim_level_1"].fillna("") != ""][
        ["pn", "aim_level_1", "aim_level_2", "aim_level_3",
         "aim_source_this_pass", "aim_note"]
    ].drop_duplicates("pn")
    print(f"classification rows to apply: {len(fill)}")

    # ---- 1. the AIM spine -------------------------------------------------
    m = pd.read_csv(MASTER, dtype=str, low_memory=False)
    m["pn"] = pn_key(m["part_number"])
    before_master = int(m["aim_l1_fixed"].fillna("").map(is_placeholder).sum())

    f = fill.set_index("pn")
    hit = m["pn"].isin(f.index)
    m.loc[hit, "aim_l1_fixed"] = m.loc[hit, "pn"].map(f["aim_level_1"])
    m.loc[hit, "aim_l2_fixed"] = m.loc[hit, "pn"].map(f["aim_level_2"])
    m.loc[hit, "aim_l3"] = m.loc[hit, "pn"].map(f["aim_level_3"])
    if "aim_l1" in m.columns:
        m.loc[hit, "aim_l1"] = m.loc[hit, "pn"].map(f["aim_level_1"])
    if "aim_l2" in m.columns:
        m.loc[hit, "aim_l2"] = m.loc[hit, "pn"].map(f["aim_level_2"])
    if "has_aim" in m.columns:
        m.loc[hit, "has_aim"] = "1"
    m.loc[hit, "aim_source"] = append_marker(m.loc[hit, "aim_source"])
    m.loc[hit, "aim_changed"] = append_marker(m.loc[hit, "aim_changed"])
    m = m.drop(columns=["pn"])

    after_master = int(m["aim_l1_fixed"].fillna("").map(is_placeholder).sum())
    master_rows = int(hit.sum())
    print(f"master: rows matched={master_rows} unknown_l1 {before_master} -> {after_master}")

    # ---- 2. the classification overlay -------------------------------------
    o = pd.read_csv(OVERLAY, dtype=str, low_memory=False)
    o["pn"] = pn_key(o["part_number"])
    ohit = o["pn"].isin(f.index)
    for col, src in (
        ("aim_l1_fixed", "aim_level_1"),
        ("aim_l2_fixed", "aim_level_2"),
        ("aim_l3_fixed", "aim_level_3"),
    ):
        if col in o.columns:
            o.loc[ohit, col] = o.loc[ohit, "pn"].map(f[src])
    if "aim_source" in o.columns:
        o.loc[ohit, "aim_source"] = append_marker(o.loc[ohit, "aim_source"])
    o = o.drop(columns=["pn"])
    overlay_rows = int(ohit.sum())
    print(f"overlay: rows matched={overlay_rows}")

    if not apply:
        print("\nDRY RUN — nothing written. Re-run with --apply")
        return 0

    # ---- 3. back up then write --------------------------------------------
    backups = {}
    for p in (MASTER, OVERLAY, EXPORT_CSV, EXPORT_XLSX):
        if p.exists():
            b = p.with_name(f"{p.name}.bak_pre_{MARKER}_{STAMP}")
            shutil.copy2(p, b)
            backups[p.name] = str(b)
            print(f"backup {b.name}")

    m.to_csv(MASTER, index=False)
    o.to_csv(OVERLAY, index=False)
    print(f"written {MASTER.name}, {OVERLAY.name}")

    # ---- 4. rebuild the Power BI export pair (CSV + Excel) -----------------
    sys.path.insert(0, str(ROOT / "01_data" / "91_build"))
    import importlib
    mod = importlib.import_module("export_aim_pn_categories_figkey_xlsx")
    mod.OUT_CSV = EXPORT_CSV
    mod.OUT_XLSX = EXPORT_XLSX
    mod.SRC_CLASS = OVERLAY
    mod.main()

    summary = {
        "as_of": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "marker": MARKER,
        "classified_from": str(CLASSIFIED),
        "master_rows_matched": master_rows,
        "overlay_rows_matched": overlay_rows,
        "master_unknown_l1_before": before_master,
        "master_unknown_l1_after": after_master,
        "backups": backups,
        "exports_rebuilt": [EXPORT_CSV.name, EXPORT_XLSX.name],
    }
    (OUT / "apply_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
