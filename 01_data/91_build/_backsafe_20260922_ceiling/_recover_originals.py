"""Recover the pre-change originals after `_take_backup.py` was re-run and overwrote them.

Background, plainly: `_take_backup.py` copies the LIVE file over `original\\`. It was
re-run after the rebuild, so for every file that had already been changed, the backup
copy became a copy of the NEW file and the pre-change bytes were lost from this folder.
`_before.json` was rewritten the same way, so it now records the post-change hash and
`restore.ps1 -Verify` reports "matches" for files it can no longer undo. That is worse
than having no backup, because it reads as if the originals were safe.

The pre-change hashes below were printed by the first backup run and are recoverable
from this session's log. This script:
  1. searches the whole workspace for a byte-identical copy of each pre-change original
  2. where one exists, restores it into .\\original\\ and rewrites the manifest entry
  3. where none exists, records the file as NOT REVERTIBLE rather than pretending

Run with --check to look without writing.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent
ORIG = HERE / "original"
MANIFEST = HERE / "_before.json"

# rel -> full sha256 of the pre-change original, from the first _take_backup run output
KNOWN: dict[str, str] = {
    "01_data/00_derived/wallet_waterfall.csv":
        None,  # full hash known from the restore round-trip; filled in below
}
PREFIXES: dict[str, str] = {
    "01_data/00_derived/wallet_waterfall.csv": "e9c13fbcde9adcdd",
    "01_data/00_derived/lost_sales_model.csv": "98422cf4e65cb4d9",
    "01_data/00_derived/lost_sales_market.csv": "880638af8e932979",
    "01_data/00_derived/lost_sales_competitor_pn.csv": "2b04fd21501a77c7",
    "01_data/00_derived/lost_sales_competitor_coverage.csv": "94d6c2d2c6214e2a",
    "01_data/00_derived/lost_sales_model.meta.json": "5e35a956dad05c44",
    "01_data/00_derived/revenue_runway.csv": "55c6d6ab93205a27",
    "01_data/00_derived/metrics_snapshot.json": "299b8eebe941c968",
    "01_data/00_derived/_verification_report.json": "d52321e411f3038d",
    "01_data/00_derived/_verification_report.md": "85cc1c3707819a2d",
    "03_analytics/Isuzu/prism/data/facts_anchor.yaml": "15d6711b2aa0b3f7",
    "03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv": "b69a060677bc82ce",
    "02_dashboards/sales/ISZE_KPI_Dashboard.html": "7f8b963269f0601c",
    "02_dashboards/ops/ISZE_OS_Console.html": "13a0a11aa2013316",
    "02_dashboards/hub/ISZE_OS_Hub.html": "37690bfe22247ddb",
    "02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html": "9986153100f255e2",
    "01_data/14_dashboards/isze_data.json": "5e15f285a82cd0f7",
    "01_data/14_dashboards/isze_data.preload.js": "5f6674da46ff8571",
    "01_data/14_dashboards/viz/risk_cockpit.json": "f024b7e4f07425a4",
    "02_dashboards/sales/risk_cockpit.data.js": "382812cca35aefe1",
    "09_meetings/Business_Performance_Review_2026/_bpr_numbers.json": "7a04b2d203227797",
    "09_meetings/Business_Performance_Review_2026/ISZE_Business_Performance_Review_2026.pptx":
        "0bc52f295c3b148a",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/target_spend_waterfall.csv":
        "a07741bc76cfb575",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md": "74c581c8ae12fcc9",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv": "cedef50c6072b42a",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip": "0fd7c705b1217016",
}
DELETE_EXTS = {".html", ".json", ".js", ".csv", ".md", ".yaml", ".pyc", ".pptx", ".zip"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def search(prefix: str, name: str) -> list[Path]:
    """Every file in the workspace whose sha256 starts with `prefix`, best copies first."""
    hits: list[Path] = []
    seen = set()
    for p in ROOT.rglob(name):
        if not p.is_file():
            continue
        rp = str(p).replace("\\", "/")
        if "_backsafe_20260922_ceiling" in rp:
            continue
        try:
            if p.stat().st_size == 0:
                continue
            h = sha(p)
        except OSError:
            continue
        if h.startswith(prefix) and rp not in seen:
            seen.add(rp)
            hits.append(p)
    # prefer archive / backup folders over live surfaces
    def rank(p: Path) -> int:
        s = str(p).replace("\\", "/")
        for i, k in enumerate(("90_archive", "15_gpt_safe", "PPT_GPT", "07_deploy", "91_build")):
            if k in s:
                return i
        return 9

    return sorted(hits, key=rank)


def main() -> int:
    check = "--check" in sys.argv
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_rel = {f["rel"]: f for f in data["files"]}
    recovered, lost = [], []

    print("looking for a byte-identical copy of each pre-change original...\n")
    for rel, prefix in PREFIXES.items():
        live = ROOT / rel
        if not live.is_file():
            continue
        live_hash = sha(live)
        if live_hash.startswith(prefix):
            print(f"UNCHANGED  {rel}  (live still matches the pre-change hash)")
            continue
        hits = search(prefix, Path(rel).name)
        tag = "RECOVER" if hits else "LOST"
        print(f"{tag:9s} {rel}")
        print(f"              wanted  {prefix}...   live now {live_hash[:16]}...")
        for h in hits[:4]:
            print(f"              candidate {h}")
        if hits:
            src = hits[0]
            dst = ORIG / rel
            if not check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                got = sha(dst)
                assert got.startswith(prefix), (got, prefix)
            rec = by_rel.get(rel)
            if rec:
                rec["sha256_before"] = sha(src) if not check else prefix + " (pending)"
                rec["sha256_at_first_backup"] = rec["sha256_before"]
                rec["recovered_from"] = str(src)
                rec["revertible"] = True
            recovered.append((rel, src))
        else:
            rec = by_rel.get(rel)
            if rec:
                rec["sha256_before"] = None
                rec["sha256_at_first_backup"] = None
                rec["revertible"] = False
                rec["not_revertible_reason"] = (
                    "the pre-change bytes were overwritten inside this backup folder and no "
                    "byte-identical copy survives in the workspace; the file can only be "
                    "reproduced by re-running its builder after restoring wallet_waterfall.csv"
                )
            lost.append(rel)

    data["recovery_run_at"] = "see _REVERTIBILITY.md"
    data["not_revertible"] = lost
    if not check:
        tmp = MANIFEST.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        tmp.replace(MANIFEST)

    print(f"\nrecovered {len(recovered)}, still lost {len(lost)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
