"""Final consolidated verification (read-only where possible)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PACK = ROOT / "01_data" / "90_INBOX" / "GPT_tonnage_pack_20260920"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
BUILDER = ROOT / "03_analytics" / "Isuzu" / "prism" / "scripts" / "build_nseries_tonnage_bands.py"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


print("=== PART 1: band files vs the 18:22 backups (bytes) ===")
for n in ["series_to_tonnage.csv", "epc_decode_nseries_banded.csv",
          "nseries_tonnage_evolution.csv"]:
    now, bak = DER / n, DER / f"{n}.bak_before_order_fix_20260922"
    same = sha(now) == sha(bak)
    print(f"  {n:38s} identical-to-backup={same}")

print("\n=== PART 1: page mtime (must be 20:06:09, unchanged) ===")
print(f"  {HTML.stat().st_mtime}")

print("\n=== PART 2: the four keys in the live meta, after my re-run ===")
m = json.loads((DER / "nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))
for k in ["snapshot", "snapshot_field_meaning", "decode_snapshot", "billing_through",
          "billing_window", "generated_at"]:
    v = m.get(k)
    print(f"  {k:24s} = {str(v)[:95]}")
print(f"  tie_out.delta_eur        = {m['tie_out']['delta_eur']}")

print("\n=== PART 2: the builder lines that write them ===")
src = BUILDER.read_text(encoding="utf-8").splitlines()
for i, line in enumerate(src, 1):
    if any(t in line for t in ['"snapshot":', '"snapshot_field_meaning":', '"decode_snapshot":',
                               '"billing_through":', '"billing_window":']):
        print(f"  {i:4d}| {line.strip()}")

print("\n=== PART 2: backups present ===")
for n in ["nseries_tonnage_evolution.meta.json.bak_before_snapshot_fix_durable_20260922",
          "nseries_tonnage_evolution.meta.json.bak_before_snapshot_field_fix_20260922",
          "nseries_tonnage_evolution.meta.json.bak_before_order_fix_20260922"]:
    p = DER / n
    print(f"  {n}  bytes={p.stat().st_size}  hash={sha(p)[:16]}")

print(f"\n=== PART 2: pack file count = {len([p for p in PACK.rglob('*') if p.is_file()])}")
print(f"  pack meta == derived meta: "
      f"{sha(PACK / 'data_nseries_bands' / '12_nseries_band_evolution.meta.json') == sha(DER / 'nseries_tonnage_evolution.meta.json')}")

print("\n=== leftover temp files in the pack? ===")
leftover = [p.name for p in PACK.rglob("*") if p.is_file() and ".tmp" in p.name]
print(f"  {leftover if leftover else 'none'}")
