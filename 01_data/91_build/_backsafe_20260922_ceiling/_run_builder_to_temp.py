"""Run build_wallet_waterfall.py UNMODIFIED, but write its output to a temp file.

Truncating writes fail on some files in this workspace (OSError 22), and the
builder writes with ``DataFrame.to_csv``, so:
  1. rebind the builder's module-level OUT_CSV to a temp file in the same folder
  2. run the builder entry point unchanged
  3. report the before/after diff
  4. only with --install: os.replace(tmp, real) - atomic, same filesystem

Usage:
    python _run_builder_to_temp.py            # dry run, no install
    python _run_builder_to_temp.py --install  # install after the diff prints
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics/Isuzu/prism"
TARGET = ROOT / "01_data/00_derived/wallet_waterfall.csv"
TMP = TARGET.with_name(TARGET.name + ".tmp_ceiling_20260922")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    import pandas as pd

    install = "--install" in sys.argv
    before = pd.read_csv(TARGET)

    sys.path.insert(0, str(PRISM))
    sys.path.insert(0, str(PRISM / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "_bw_under_test", PRISM / "scripts/build_wallet_waterfall.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_bw_under_test"] = mod
    spec.loader.exec_module(mod)

    assert mod.OUT_CSV == TARGET, mod.OUT_CSV
    mod.OUT_CSV = TMP
    rc = mod.main()
    print(f"builder exit {rc}; temp output -> {TMP}")

    after = pd.read_csv(TMP)
    print(f"\nrows {len(before)} -> {len(after)}")
    b25 = before[before.year == 2025]
    a25 = after[after.year == 2025]
    print(f"CY2025 ceiling  {b25.theoretical_wallet_eur.sum():,.2f} -> "
          f"{a25.theoretical_wallet_eur.sum():,.2f}  "
          f"(delta {a25.theoretical_wallet_eur.sum() - b25.theoretical_wallet_eur.sum():+,.2f})")
    print(f"CY2025 billed   {b25.captured_total_eur.sum():,.2f} -> "
          f"{a25.captured_total_eur.sum():,.2f}  "
          f"(delta {a25.captured_total_eur.sum() - b25.captured_total_eur.sum():+,.2f})")
    print(f"CY2025 cover    {b25.captured_total_eur.sum()/b25.theoretical_wallet_eur.sum()*100:.4f}% -> "
          f"{a25.captured_total_eur.sum()/a25.theoretical_wallet_eur.sum()*100:.4f}%")

    bm = {r.distributor_code: float(r.theoretical_wallet_eur) for _, r in b25.iterrows()}
    am = {r.distributor_code: float(r.theoretical_wallet_eur) for _, r in a25.iterrows()}
    print("\nper-market ceiling CY2025 (only rows that move):")
    moved = 0
    for code in sorted(set(bm) | set(am)):
        d = am.get(code, 0.0) - bm.get(code, 0.0)
        if abs(d) > 0.005:
            moved += 1
            print(f"  {code:9s} {bm.get(code, 0.0):>14,.2f} -> {am.get(code, 0.0):>14,.2f}  {d:>+12,.2f}")
    if not moved:
        print("  (none)")

    # year-by-year, for the drift check
    for y in sorted(before.year.unique()):
        b = before[before.year == y]
        a = after[after.year == y]
        print(f"  CY{y}: ceiling {b.theoretical_wallet_eur.sum():>14,.2f} -> "
              f"{a.theoretical_wallet_eur.sum():>14,.2f}")

    # column-level drift on years the change is not meant to touch
    cols = list(before.columns)
    assert cols == list(after.columns), (set(cols) ^ set(after.columns))
    print("\ncolumn set unchanged:", len(cols), "columns")
    key = lambda df: list(zip(df.year, df.distributor_code))  # noqa: E731
    print("row keys identical:", key(before) == key(after))
    if key(before) == key(after):
        for y in (2023, 2024):
            b = before[before.year == y].reset_index(drop=True)
            a = after[after.year == y].reset_index(drop=True)
            diffs = []
            for c in cols:
                for i in range(len(b)):
                    x, z = b.at[i, c], a.at[i, c]
                    if isinstance(x, float) and isinstance(z, float):
                        if abs(x - z) > 1e-9:
                            diffs.append((c, b.at[i, "distributor_code"], x, z))
                    elif str(x) != str(z):
                        diffs.append((c, b.at[i, "distributor_code"], x, z))
            print(f"  CY{y} cells that moved: {len(diffs)}")
            for d in diffs[:20]:
                print("    ", d)

    if install:
        os.replace(TMP, TARGET)
        print(f"\nINSTALLED. {TARGET.name} sha256 {sha(TARGET)}")
        receipt = HERE / "_ceiling_rebuild_receipt.json"
        receipt.write_text(json.dumps({
            "installed_at": pd.Timestamp.now().isoformat(),
            "file": str(TARGET),
            "sha256": sha(TARGET),
            "ceiling_2025_eur": round(float(a25.theoretical_wallet_eur.sum()), 2),
            "billed_2025_eur": round(float(a25.captured_total_eur.sum()), 2),
        }, indent=1), encoding="utf-8")
    else:
        print(f"\nDRY RUN - nothing installed. Temp file kept at {TMP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
