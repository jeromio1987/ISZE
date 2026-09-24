"""What exactly did the repair change? Four files, three comparisons.

  A. the repaired file vs the pre-repair file just backed up  -> must be the twelve rows only
  B. the repaired file vs "pre-repair with the twelve restored" -> must be identical
  C. the repaired file vs the 297-row pre-rebase backup        -> the true movement, re-stated
  D. the twelve rows, backup vs current vs repaired

Also reports the single-band count before and after so the 180 -> 176 movement is proven, not
asserted, and lists which rows caused it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
BAK12 = DER / "_backsafe_rebase_20260923_vehbandapplic"
PREBASE = ROOT / "02_dashboards" / "sales" / "_backsafe_rebase_20260923"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import pending_ruling_codes  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
PENDING = pending_ruling_codes()
PAT = re.compile(r"(?<![A-Z0-9])(" + "|".join(map(re.escape, PENDING)) + r")(?![A-Z0-9])")

TWELVE = ["5876103260", "5878320470", "8975167220", "8978808270", "8982473951",
          "8982482712", "8983320620", "8983459492", "8983550720", "8983753330",
          "8981868281", "8983615742"]


def load(p: Path) -> pd.DataFrame:
    d = pd.read_csv(p, dtype=str, low_memory=False).fillna("")
    d["k"] = d.pn.map(n)
    return d


def main() -> int:
    now = load(DER / "tonnage_capable_part_numbers.csv")
    pre = load(BAK12 / "tonnage_capable_part_numbers.csv.bak_pre_nmr_repair")
    rebase = load(PREBASE / "tonnage_capable_part_numbers.csv.bak_pre_rebase")

    cols = [c for c in now.columns if c != "frozen_note"]
    m = pre.merge(now, on="k", suffixes=("_pre", "_now"))
    print("=" * 100)
    print("A. REPAIRED vs PRE-REPAIR  (must be the twelve rows and nothing else)")
    print("=" * 100)
    print(f"  rows pre {len(pre)}  now {len(now)}")
    changed = []
    for c in cols:
        a, b = f"{c}_pre", f"{c}_now"
        if a in m and b in m:
            d = m[m[a].astype(str) != m[b].astype(str)]
            if len(d):
                changed.append((c, len(d)))
                print(f"      column {c:26s} changed on {len(d):3d} rows")
    rows_changed = set()
    for c, _ in changed:
        d = m[m[f"{c}_pre"].astype(str) != m[f"{c}_now"].astype(str)]
        rows_changed |= set(d.k)
    print(f"  distinct part numbers touched: {len(rows_changed)}")
    twelve = {n(p) for p in TWELVE}
    print(f"  of those, the twelve named rows : {len(twelve & rows_changed)} of 12")
    print(f"  OTHER rows touched             : {sorted(rows_changed - twelve) or 'none'}")
    for k in sorted(rows_changed - twelve):
        a = pre[pre.k == k].iloc[0]
        b = now[now.k == k].iloc[0]
        print(f"      {k}")
        for c in cols:
            if str(a[c]) != str(b[c]):
                print(f"          {c}: {a[c]!r} -> {b[c]!r}")

    print()
    print("=" * 100)
    print("B. REPAIRED vs 'PRE-REPAIR WITH THE TWELVE RESTORED'  (must be identical)")
    print("=" * 100)
    expect = pre.copy()
    rb = rebase.set_index("k")
    for i, r in expect.iterrows():
        if r.k in twelve and r.k in rb.index:
            for c in ("bands", "band_list", "n_bands"):
                expect.at[i, c] = rb.at[r.k, c]
    same = (now[cols].astype(str) == expect[cols].astype(str))
    bad = same[~same.all(axis=1)]
    print(f"  rows differing: {len(bad)}   identical: {len(bad) == 0}")
    for k in bad.k.tolist()[:12]:
        a = now[now.k == k].iloc[0]
        b = expect[expect.k == k].iloc[0]
        for c in cols:
            if str(a[c]) != str(b[c]):
                print(f"      {k} {c}: repaired {a[c]!r} expected {b[c]!r}")

    print()
    print("=" * 100)
    print("C. THE SINGLE-BAND COUNT, BEFORE AND AFTER THIS REPAIR")
    print("=" * 100)
    for tag, d in (("pre-rebase (297 rows)", rebase), ("pre-repair (324 rows)", pre),
                   ("repaired (324 rows)", now)):
        print(f"  {tag:26s} rows {len(d):4d}   n_bands == 1 : "
              f"{int((d.n_bands.astype(int) == 1).sum()):4d}")
    print()
    print("  which rows moved the count:")
    for k in sorted(rows_changed):
        a = pre[pre.k == k].iloc[0]
        b = now[now.k == k].iloc[0]
        if int(a.n_bands) == 1 or int(b.n_bands) == 1:
            print(f"      {k:>12s} n_bands {a.n_bands} -> {b.n_bands}   "
                  f"bands {a.bands:22s} -> {b.bands:22s}   "
                  f"{'single count ' + str(int(b.n_bands) - int(a.n_bands)) if True else ''}")

    print()
    print("=" * 100)
    print("D. THE TWELVE, THREE WAYS")
    print("=" * 100)
    print(f"  {'pn':>12s}  {'pre-rebase backup':22s} {'pre-repair':22s} {'repaired':22s} restored")
    for p in TWELVE:
        k = n(p)
        a = rebase[rebase.k == k]
        b = pre[pre.k == k]
        c = now[now.k == k]
        av = a.bands.iloc[0] if len(a) else "(absent)"
        bv = b.bands.iloc[0] if len(b) else "(absent)"
        cv = c.bands.iloc[0] if len(c) else "(absent)"
        print(f"  {k:>12s}  {av:22s} {bv:22s} {cv:22s} {'yes' if av == cv else 'NO'}")

    print()
    print("=" * 100)
    print("E. PARKED RECORDING NOW: how many rows carry a pending code in parked_codes")
    print("=" * 100)
    print(f"  repaired file, parked_codes non-empty      : "
          f"{int((now.parked_codes.astype(str).str.strip() != '').sum())}")
    print(f"  pre-repair file, parked_codes non-empty    : "
          f"{int((pre.parked_codes.astype(str).str.strip() != '').sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
