"""Take a byte-for-byte backup of every file this session may write.

Writes:
  .\original\<workspace-relative path>   the bytes as they are now
  .\_before.json                         sha256 + size + mtime + role per file

Safe to re-run: if a backup copy already exists and matches _before.json it is
left alone. It never touches anything outside .\original\.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
ORIG = HERE / "original"

# (relative path, group, why it is in scope)
SCOPE: list[tuple[str, str, str]] = [
    # --- prism rebuild outputs (Task 2) ---
    ("01_data/00_derived/wallet_waterfall.csv", "prism", "the locked ceiling table - rebuilt by build_wallet_waterfall.py"),
    ("01_data/00_derived/lost_sales_model.csv", "prism", "rebuilt by build_lost_sales_model.py, consumes the ceiling"),
    ("01_data/00_derived/lost_sales_market.csv", "prism", "rebuilt by build_lost_sales_model.py, per-market ceiling + cover"),
    ("01_data/00_derived/lost_sales_competitor_pn.csv", "prism", "rebuilt by build_lost_sales_model.py (collateral)"),
    ("01_data/00_derived/lost_sales_competitor_coverage.csv", "prism", "rebuilt by build_lost_sales_model.py (collateral)"),
    ("01_data/00_derived/lost_sales_model.meta.json", "prism", "rebuilt by build_lost_sales_model.py (collateral)"),
    ("01_data/00_derived/revenue_runway.csv", "prism", "backed up to prove it does NOT move (reads the ceiling)"),
    ("01_data/00_derived/metrics_snapshot.json", "prism", "rebuilt by build_metrics_snapshot.py"),
    ("01_data/00_derived/_verification_report.json", "prism", "rewritten by verify_derived_pipeline.py"),
    ("01_data/00_derived/_verification_report.md", "prism", "rewritten by verify_derived_pipeline.py"),
    # --- decision anchor (Task 2 / Task 5) ---
    ("03_analytics/Isuzu/prism/data/facts_anchor.yaml", "prism", "pins the published GPS % headline; re-based only if the drift check needs it"),
    ("03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv", "prism", "NOT to be changed - backed up so drift can be proven"),
    # --- dashboards (Task 5) ---
    ("02_dashboards/sales/ISZE_KPI_Dashboard.html", "dashboard", "reads ceiling from one file, per-market maxSpend from the other"),
    ("02_dashboards/ops/ISZE_OS_Console.html", "dashboard", "prints the network ceiling, cover and placeholder share"),
    ("02_dashboards/hub/ISZE_OS_Hub.html", "dashboard", "prints the network ceiling, cover and placeholder share"),
    ("02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html", "dashboard", "derives its headline from the ceiling at build time"),
    ("01_data/14_dashboards/isze_data.json", "dashboard", "carries addressable_gap_eur 24,727,686"),
    ("01_data/14_dashboards/isze_data.preload.js", "dashboard", "same payload as isze_data.json"),
    ("01_data/14_dashboards/viz/risk_cockpit.json", "dashboard", "carries the floored uncaptured figure"),
    ("02_dashboards/sales/risk_cockpit.data.js", "dashboard", "carries the floored uncaptured figure"),
    # --- BPR deck (Task 5) ---
    ("09_meetings/Business_Performance_Review_2026/_bpr_numbers.json", "bpr", "slide 17 numbers block"),
    ("09_meetings/Business_Performance_Review_2026/ISZE_Business_Performance_Review_2026.pptx", "bpr", "slide 17 prints the ceiling and cover"),
    # --- hand-over pack (Task 4) ---
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/target_spend_waterfall.csv", "pack", "the per-market ceiling table going to the distributor"),
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md", "pack", "carries the pack's disclosure notes"),
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv", "pack", "describes the pack contents"),
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip", "pack", "misleadingly named third copy - will be renamed, not deleted"),
    # --- internal notes (Task 5) ---
    ("00_docs/agent/STATE_PACKET.md", "notes", "carries the published-ceiling line"),
    ("DECISIONS.md", "notes", "carries the 54,323,455 sentence"),
    ("00_docs/ISZE_ROADMAP.md", "notes", "carries the 54,323,455 sentence"),
    ("01_data/90_INBOX/D08_EXECUTION_2026-09-22.md", "notes", "carries the 54,323,455 sentence"),
    # --- per-market operating dashboards (Task 5) ---
    ("09_meetings/PORTUGAL_Operating_Dashboard_2026/NUMBERS_LEDGER.json", "opdash", "wallet_cy.ceiling_eur + hero chip 3,052,087"),
    ("09_meetings/PORTUGAL_Operating_Dashboard_2026/PORTUGAL_Operating_Dashboard.html", "opdash", "prints the market's ceiling chip"),
    ("09_meetings/IRELAND_Operating_Dashboard_2026/NUMBERS_LEDGER.json", "opdash", "wallet_cy.ceiling_eur 956,313"),
    ("09_meetings/IRELAND_Operating_Dashboard_2026/IRELAND_Operating_Dashboard.html", "opdash", "prints the market's ceiling chip"),
    ("09_meetings/GERMANY_Operating_Dashboard_2026/NUMBERS_LEDGER.json", "opdash", "wallet_cy.ceiling_eur 3,808,128"),
    ("09_meetings/GERMANY_Operating_Dashboard_2026/GERMANY_Operating_Dashboard.html", "opdash", "prints the market's ceiling chip"),
    ("09_meetings/BELGIUM_Operating_Dashboard_2026/NUMBERS_LEDGER.json", "opdash", "wallet_cy.ceiling_eur 2,453,507"),
    ("09_meetings/BELGIUM_Operating_Dashboard_2026/BELGIUM_Operating_Dashboard.html", "opdash", "prints the market's ceiling chip"),
    ("09_meetings/MALTA_Operating_Dashboard_2026/NUMBERS_LEDGER.json", "opdash", "wallet_cy.ceiling_eur 378,827"),
    ("09_meetings/MALTA_Operating_Dashboard_2026/MALTA_Operating_Dashboard.html", "opdash", "prints the market's ceiling chip"),
    ("09_meetings/CYPRUS_Operating_Dashboard_2026/NUMBERS_LEDGER.json", "opdash", "wallet_cy.ceiling_eur 676,267"),
    ("09_meetings/CYPRUS_Operating_Dashboard_2026/CYPRUS_Operating_Dashboard.html", "opdash", "prints the market's ceiling chip"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    before_path = HERE / "_before.json"
    prior = {}
    if before_path.exists():
        prior = {f["rel"]: f for f in json.loads(before_path.read_text(encoding="utf-8"))["files"]}

    files = []
    missing = []
    readonly = []
    for rel, group, role in SCOPE:
        src = ROOT / rel
        if not src.exists():
            missing.append(rel)
            continue
        if src.stat().st_file_attributes & 1:  # FILE_ATTRIBUTE_READONLY
            readonly.append(rel)
        digest = sha256(src)
        dst = ORIG / rel
        prior_rec = prior.get(rel)
        if dst.exists() and sha256(dst) == digest:
            pass  # already backed up, bytes identical
        elif dst.exists() and prior_rec and prior_rec.get("sha256_before") not in (None, digest):
            # THE GUARD. A backup copy exists and it does NOT match the live file, and the
            # manifest already recorded a different pre-change hash for this path. Overwriting
            # now would replace the original with the changed file AND rewrite the manifest to
            # match, which is how a backup silently stops being a backup. Refuse.
            raise SystemExit(
                f"REFUSING to overwrite the backup copy of {rel}.\n"
                f"  backup copy   {sha256(dst)[:16]}\n"
                f"  live file     {digest[:16]}\n"
                f"  manifest says {str(prior_rec.get('sha256_before'))[:16]}\n"
                f"Re-run _recover_originals.py to re-point the manifest, or delete the backup "
                f"copy deliberately if you really mean to re-baseline it."
            )
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        st = src.stat()
        rec = {
            "rel": rel,
            "group": group,
            "role": role,
            "sha256_before": digest,
            "bytes": st.st_size,
            "mtime_before": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        }
        if rel in prior and prior[rel]["sha256_before"] == digest:
            rec["sha256_at_first_backup"] = prior[rel].get("sha256_at_first_backup", digest)
        else:
            rec["sha256_at_first_backup"] = digest
        files.append(rec)

    payload = {
        "backup_set": "ceiling-correction 2026-09-22",
        "workspace_root": str(ROOT),
        "taken_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(files),
        "files": files,
        "missing_at_backup": missing,
        "readonly_flagged": readonly,
    }
    tmp = HERE / "_before.json.tmp"
    tmp.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    tmp.replace(before_path)

    print(f"backed up {len(files)} files into {ORIG}")
    if missing:
        print("MISSING (not backed up, not in scope):")
        for m in missing:
            print("  " + m)
    if readonly:
        print("READ-ONLY flagged:")
        for r in readonly:
            print("  " + r)
    for f in files:
        print(f"  {f['sha256_before'][:16]}  {f['bytes']:>9,}  {f['rel']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
