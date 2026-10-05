# -*- coding: utf-8 -*-
"""
Add the Japan-native classification codes to the ISZE spine (aim_master_v2.csv).

Adds 8 columns, appended at the end. No existing column is touched or reordered:
    jp_zkk            sales category code          (3 char, 142 codes)
    jp_zuk            option/accessory category    (5 char, 359 codes)
    jp_hkk            warehouse route + status     (5 char, 125 codes)
    jp_eple           engineering grouping         (4 char, 662 codes)
    jp_fig_key        figure key as Japan sends it
    jp_class_new      two-letter class on the code (XC, DD, EV, ...)
    jp_class_current  same, current price list
    jp_code_source    'jp_price_cd_250912' or ''   provenance for every row

Join: spine part_number  ==  price-CD 'Pno'.
The CD's 'New Part Class' has no PN remap, so part_number is the only join key.

Safety
  * backup written before any write
  * atomic replace (write .tmp, then move)
  * gate: row count unchanged, header = old + new, no existing cell altered
  * idempotent: re-running replaces only the 8 new columns

Run: python 01_data/91_build/apply_jp_codes_to_spine_20260920.py
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CACHE = ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"
GATE = ROOT / "01_data" / "90_INBOX" / "_jp_codes_spine_gate_20260920.json"

NEW_COLS = [
    "jp_zkk", "jp_zuk", "jp_hkk", "jp_eple",
    "jp_fig_key", "jp_class_new", "jp_class_current", "jp_code_source",
]
SOURCE_TAG = "jp_price_cd_250912"
# cache column -> spine column
TAKE = {
    "jp_zkk": "zkk",
    "jp_zuk": "zuk",
    "jp_hkk": "hkk",
    "jp_eple": "eple",
    "jp_fig_key": "jp_fig_key",
    "jp_class_new": "class_new",
    "jp_class_current": "class_current",
}


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    return t[:-2] if t.endswith(".0") else t


def main() -> int:
    if not SPINE.exists() or not CACHE.exists():
        print("MISSING spine or cache", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = SPINE.with_name(f"aim_master_v2.csv.bak_pre_jpcodes_{stamp}")
    shutil.copy2(SPINE, backup)
    print(f"backup -> {backup.name}")

    # ---- japan codes ----
    jp: dict[str, dict] = {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            jp[r["pn"]] = r
    print(f"cache: {len(jp)} PNs")

    # ---- read spine ----
    with SPINE.open(encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        old_hdr = next(rd)
        old_rows = [row for row in rd]
    print(f"spine: {len(old_rows)} rows, {len(old_hdr)} cols")

    clash = [c for c in NEW_COLS if c in old_hdr]
    if clash:
        print(f"columns already present, will be replaced: {clash}")
    base_hdr = [c for c in old_hdr if c not in NEW_COLS]
    new_hdr = base_hdr + NEW_COLS
    base_idx = {c: i for i, c in enumerate(old_hdr) if c in base_hdr}

    # ---- write ----
    tmp = SPINE.with_suffix(".csv.tmp")
    matched = 0
    eur_matched = 0.0
    eur_total = 0.0
    zkk_filled = 0
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(new_hdr)
        for row in old_rows:
            pn = s(row[base_idx["part_number"]])
            try:
                eur_total += float(row[base_idx["l12m_billed_eur"]] or 0)
            except ValueError:
                pass
            j = jp.get(pn)
            add = [""] * len(NEW_COLS)
            if j:
                matched += 1
                for k, src in TAKE.items():
                    add[NEW_COLS.index(k)] = j.get(src, "")
                add[NEW_COLS.index("jp_code_source")] = SOURCE_TAG
                if j.get("zkk"):
                    zkk_filled += 1
                try:
                    eur_matched += float(row[base_idx["l12m_billed_eur"]] or 0)
                except ValueError:
                    pass
            w.writerow([row[base_idx[c]] for c in base_hdr] + add)

    # ---- verify before replacing ----
    with tmp.open(encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        new_hdr_read = next(rd)
        new_rows = [row for row in rd]

    checks = {
        "row_count_same": len(new_rows) == len(old_rows),
        "header_is_old_plus_new": new_hdr_read == new_hdr,
        "existing_columns_unchanged": all(
            all(new_rows[i][base_idx[c]] == old_rows[i][base_idx[c]] for c in base_hdr)
            for i in (0, len(old_rows) // 2, len(old_rows) - 1)
        ),
        "new_cols_present": all(c in new_hdr_read for c in NEW_COLS),
    }
    ok = all(checks.values())
    if not ok:
        print(f"GATE FAILED, spine NOT replaced: {checks}", file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return 4

    SPINE.unlink()
    tmp.replace(SPINE)
    print("spine replaced")

    gate = {
        "stamp": stamp,
        "backup": str(backup),
        "spine": str(SPINE),
        "rows": len(new_rows),
        "columns_before": len(old_hdr),
        "columns_after": len(new_hdr_read),
        "new_columns": NEW_COLS,
        "pn_matched": matched,
        "pn_matched_pct": round(100 * matched / len(old_rows), 2) if old_rows else 0.0,
        "pn_with_zkk": zkk_filled,
        "pn_with_zkk_pct": round(100 * zkk_filled / len(old_rows), 2) if old_rows else 0.0,
        "eur_matched": round(eur_matched, 2),
        "eur_total": round(eur_total, 2),
        "eur_matched_pct": round(100 * eur_matched / eur_total, 2) if eur_total else 0.0,
        "checks": checks,
        "gate_pass": ok,
    }
    GATE.write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(json.dumps(gate, indent=2))
    print(f"gate -> {GATE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
