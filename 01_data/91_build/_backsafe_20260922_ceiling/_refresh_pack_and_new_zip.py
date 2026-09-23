"""Refresh the BVDB pack's ceiling table + disclosure, then build a NEW hand-over zip.

WHY NOT THE PACK BUILDER: `09_meetings/_build_bvdb_pbi_pack_20260923.py` starts with
`shutil.rmtree(OUT)` and regenerates the folder from the derived CSVs. Running it would
erase the earlier session's corrections (the period-basis columns, the non-parts
disclosure, the MANIFEST notes) and the HOW_TO text. So this is a targeted refresh:
the pack folder keeps everything it has, and only the ceiling table, the MANIFEST's
row for it, and HOW_TO section 5 change.

Nothing here is destructive: the original zip and the earlier corrected zip are never
written to. A brand-new archive is created beside them.

Usage:
    python _refresh_pack_and_new_zip.py --dry-run
    python _refresh_pack_and_new_zip.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data/00_derived"
PACK = ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23"
MEET = ROOT / "09_meetings"
WALLET = DER / "wallet_waterfall.csv"
PACK_WF = PACK / "02_GPS/target_spend_waterfall.csv"
MANIFEST = PACK / "00_START_HERE/MANIFEST.csv"
HOWTO = PACK / "00_START_HERE/HOW_TO.md"
META = PACK / "00_START_HERE/_pack_meta.json"

ORIGINAL_ZIP = MEET / "BVDB_PBI_Data_Upload_2026-09-23.zip"
MISLEADING_ZIP = MEET / "BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip"
# Renamed, not deleted: it DOES contain a real fix (the part-year GPS correction) but its
# old name implied it was the fixed hand-over, which it is not. The new name says what it is.
RENAMED_ZIP = MEET / "BVDB_PBI_Data_Upload_2026-09-23_corrected_GPS-PARTIAL-YEAR_ONLY_superseded_20260922.zip"
NEW_ZIP = MEET / "BVDB_PBI_Data_Upload_2026-09-23_HANDOVER_20260922.zip"

BASIS_TEXT = (
    "Full-calendar-year target spend: trucks in service (UIO workbook) x the GPS "
    "max-spend rate per truck band. A ceiling, not a forecast."
)
AS_OF = "2026-09-22 HANOVER"
AS_OF = "2026-09-22"

FRIENDLY = {
    "theoretical_wallet_eur": "target_spend_ceiling_eur",
    "captured_total_eur": "parts_billed_total_eur",
    "captured_genuine_eur": "parts_billed_genuine_eur",
    "captured_bvp_eur": "parts_billed_bvp_eur",
    "uncaptured_eur": "gap_vs_target_eur",
    "gps_pct": "parts_billed_vs_target_pct",
}

HOWTO_ANCHOR = """Primary GPS grain: `gps_spu_by_distributor.csv`
`spend_per_unit_eur` = parts billed ÷ UIO for that year.
"""

HOWTO_ADDITION = """Primary GPS grain: `gps_spu_by_distributor.csv`
`spend_per_unit_eur` = parts billed ÷ UIO for that year.

### The target-spend table — what it is, and as of when

`02_GPS/target_spend_waterfall.csv` gives one **target spend ceiling** per distributor per year,
and the parts billed against it.

**Basis.** The ceiling is the trucks in service (UIO) for that year multiplied by the GPS
max-spend rate for each truck band (the N35 / N75 / F-Series / LCV rates in the rate card). It is
a ceiling, not a forecast: it says what the fleet could spend at full rate, and the targets are
flat across vehicle age. It is a **full calendar year** figure on every row — unlike the GPS rows
above, there is no part-year row in this file — so the eight-month caveat at the top of this
document does not apply to the ceiling itself, only to the parts billed compared against it.

**As of.** Every ceiling in this table was re-derived on **2026-09-22**. The `ceiling_as_of` and
`ceiling_basis` columns carry that per row, so a reader can tell the vintage without asking.

**What moved on 2026-09-22, and why.** Six markets — Portugal, Ireland, Germany, Belgium, Malta
and Cyprus — had their target spend overstated, because their light-truck fleet was still priced
entirely at the heavier 7.5 t band rate when a measured share of it is the 3.5 t band. Applying
that measured share, which ISZE had already corrected in its own source, moves those six ceilings
down and the network ceiling from €55,253,312 to **€54,375,729**. Parts billed did not move (it is
measured, not modelled), so the coverage percentage rises slightly. Every other market is
unchanged, Israel included.
"""


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_ceiling_table() -> tuple[pd.DataFrame, dict]:
    """Reproduce the pack's ceiling table from the rebuilt wallet file."""
    w = pd.read_csv(WALLET)
    for old, new in FRIENDLY.items():
        if old in w.columns and new not in w.columns:
            w[new] = w[old]
    # The two columns that state the basis and the date on the face of the table.
    w["ceiling_basis"] = BASIS_TEXT
    w["ceiling_as_of"] = AS_OF
    return w, {}


def update_manifest(new_wf: pd.DataFrame) -> list[str]:
    man = pd.read_csv(MANIFEST, encoding="utf-8-sig")
    changes: list[str] = []
    rel = "02_GPS/target_spend_waterfall.csv"
    i = man.index[man["file"] == rel]
    assert len(i) == 1, i
    i = i[0]
    rows, cols = len(new_wf), len(new_wf.columns)
    kb = round(PACK_WF.stat().st_size / 1024, 1)
    old = (man.at[i, "rows"], man.at[i, "cols"], man.at[i, "kb"])
    if old != (rows, cols, kb):
        changes.append(f"{rel}: rows {old[0]}->{rows} cols {old[1]}->{cols} kb {old[2]}->{kb}")
    man.at[i, "rows"] = rows
    man.at[i, "cols"] = cols
    man.at[i, "kb"] = kb
    purpose = (
        "Target spend per truck ceiling vs parts billed — use friendly columns for report labels. "
        "Full-calendar-year ceilings, all re-derived 2026-09-22; read ceiling_as_of and ceiling_basis "
        "on each row for the vintage and the basis. Not a part-year file."
    )
    if man.at[i, "purpose"] != purpose:
        changes.append(f"{rel}: purpose updated with the basis and the date")
    man.at[i, "purpose"] = purpose
    tmp = MANIFEST.with_suffix(".csv.tmp")
    man.to_csv(tmp, index=False, encoding="utf-8-sig")
    tmp.replace(MANIFEST)
    return changes


def update_howto() -> bool:
    text = HOWTO.read_text(encoding="utf-8")
    if "### The target-spend table" in text:
        return False
    if HOWTO_ANCHOR not in text:
        raise SystemExit("HOW_TO.md anchor not found - refusing to guess where to insert")
    text = text.replace(HOWTO_ANCHOR, HOWTO_ADDITION, 1)
    tmp = HOWTO.with_suffix(".md.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(HOWTO)
    return True


def update_meta(members: int, size: int) -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    meta.update({
        "as_of": AS_OF,
        "meeting": "2026-09-23",
        "folder": str(PACK),
        "zip": str(NEW_ZIP),
        "zip_kb": round(size / 1024, 1),
        "files": sum(1 for p in PACK.rglob("*") if p.is_file()),
        "archive_members": members,
        "handover_archive": [
            "This is the archive to hand over. It is a new file; no earlier archive was overwritten.",
            "Supersedes BVDB_PBI_Data_Upload_2026-09-23.zip and "
            "BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip (the latter renamed to "
            "BVDB_PBI_Data_Upload_2026-09-23_corrected_GPS-PARTIAL-YEAR_ONLY_superseded_20260922.zip, "
            "which describes what it actually contains).",
        ],
        "ceiling_correction_2026_09_22": [
            "02_GPS/target_spend_waterfall.csv rebuilt from the corrected ceiling: six markets "
            "(Portugal, Ireland, Germany, Belgium, Malta, Cyprus) re-derived with the measured "
            "3.5 t share applied. Network ceiling 55,253,312 -> 54,375,729. Parts billed unchanged.",
            "ceiling_basis and ceiling_as_of columns added so the basis and the date are on the face "
            "of the table rather than in a covering note.",
            "00_START_HERE/HOW_TO.md section 5 now states the ceiling's basis, its as-of date and "
            "what moved.",
        ],
    })
    tmp = META.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    tmp.replace(META)


def build_zip() -> tuple[int, int]:
    files = sorted(p for p in PACK.rglob("*") if p.is_file())
    tmp = NEW_ZIP.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, f.relative_to(PACK).as_posix())  # flat, matching the current archives
    tmp.replace(NEW_ZIP)
    with zipfile.ZipFile(NEW_ZIP) as zf:
        return len(zf.namelist()), NEW_ZIP.stat().st_size


def main() -> int:
    dry = "--dry-run" in sys.argv
    assert not NEW_ZIP.exists(), f"{NEW_ZIP.name} already exists - not overwriting a dated artefact"

    orig_sha = sha(ORIGINAL_ZIP)
    orig_bytes = ORIGINAL_ZIP.stat().st_size
    mis_sha = sha(MISLEADING_ZIP)
    mis_bytes = MISLEADING_ZIP.stat().st_size
    wf_before = sha(PACK_WF)

    new_wf, _ = build_ceiling_table()
    s25 = new_wf[new_wf["year"] == 2025]
    print(f"rebuilt ceiling table: {len(new_wf)} rows, {len(new_wf.columns)} columns")
    print(f"  CY2025 ceiling EUR {s25['target_spend_ceiling_eur'].sum():,.2f}  "
          f"billed EUR {s25['parts_billed_total_eur'].sum():,.2f}")
    for code in sorted(["PORTUGAL", "IRELAND", "GERMANY", "BELGIUM", "MALTA", "CYPRUS"]):
        r = s25[s25.distributor_code == code]
        print(f"    {code:9s} ceiling {float(r['target_spend_ceiling_eur'].iloc[0]):>12,.2f}  "
              f"as_of {r['ceiling_as_of'].iloc[0]}")

    if dry:
        old = pd.read_csv(PACK_WF, encoding="utf-8-sig")
        print(f"\npack table now: {len(old)} rows, {len(old.columns)} columns")
        print("would write the new table, update MANIFEST + HOW_TO, build the new zip")
        return 0

    tmp = PACK_WF.with_suffix(".csv.tmp")
    new_wf.to_csv(tmp, index=False, encoding="utf-8-sig")
    tmp.replace(PACK_WF)

    man_changes = update_manifest(new_wf)
    print("\nMANIFEST.csv:")
    for c in man_changes:
        print("   ", c)
    if not man_changes:
        print("    (already correct)")

    print("HOW_TO.md section 5 disclosure:", "added" if update_howto() else "already present")

    # Rename the misleading archive. Never delete it; the new name describes its contents.
    if MISLEADING_ZIP.exists():
        if RENAMED_ZIP.exists():
            raise SystemExit(f"{RENAMED_ZIP.name} already exists - not overwriting")
        MISLEADING_ZIP.rename(RENAMED_ZIP)
        print(f"renamed {MISLEADING_ZIP.name}\n     -> {RENAMED_ZIP.name}")
    else:
        print(f"{MISLEADING_ZIP.name} not present (already renamed?)")

    members, size = build_zip()
    update_meta(members, size)
    # meta is itself a member, so rebuild once more so the archive carries its own final meta
    members, size = build_zip()
    update_meta(members, size)
    members, size = build_zip()

    entries = {
        "new_zip": str(NEW_ZIP),
        "new_zip_bytes": size,
        "new_zip_kb": round(size / 1024, 1),
        "new_zip_sha256": sha(NEW_ZIP),
        "new_zip_members": members,
        "pack_ceiling_table_before_sha256": wf_before,
        "pack_ceiling_table_after_sha256": sha(PACK_WF),
        "original_zip": str(ORIGINAL_ZIP),
        "original_zip_untouched": sha(ORIGINAL_ZIP) == orig_sha
        and ORIGINAL_ZIP.stat().st_size == orig_bytes,
        "misleading_zip_sha256": mis_sha,
        "misleading_zip_bytes": mis_bytes,
        "renamed_to": str(RENAMED_ZIP),
        "renamed_untouched": sha(RENAMED_ZIP) == mis_sha
        and RENAMED_ZIP.stat().st_size == mis_bytes,
    }
    log = Path(__file__).resolve().parent / "_pack_zip_build_log.json"
    prev = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
    if not isinstance(prev, list):
        prev = [prev]
    prev.append(entries)
    log.write_text(json.dumps(prev, indent=2), encoding="utf-8")
    print("\n" + json.dumps(entries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
