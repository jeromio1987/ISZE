"""Confirm the dry-run legacy output is EXACTLY "current file, with the twelve rows set to their
backup values, and nothing else touched". Also count the neutral table's own version of the defect.

Nothing is written.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
BAK = ROOT / "02_dashboards" / "sales" / "_backsafe_rebase_20260923"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import pending_ruling_codes  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
TEMP = Path(sys.argv[1])
PENDING = pending_ruling_codes()
PAT = re.compile(r"(?<![A-Z0-9])(" + "|".join(map(re.escape, PENDING)) + r")(?![A-Z0-9])")

TWELVE = ["5876103260", "5878320470", "8975167220", "8978808270", "8982473951",
          "8982482712", "8983320620", "8983459492", "8983550720", "8983753330",
          "8981868281", "8983615742"]


def raw_texts(pns: set[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {p: [] for p in pns}
    for f in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
        p = DER / f
        if not p.is_file():
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            if isinstance(r, dict):
                k = n(r.get("pn"))
                if k in out:
                    out[k] += (r.get("models") or []) + (r.get("families") or [])
    x = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str, low_memory=False)
    x["g"] = x.genuine_pn.map(n)
    x["b"] = x.bvp_pn.map(n)
    for k in out:
        for r in x[(x.g == k) | (x.b == k)].itertuples():
            for c in ("vehicle_model", "registry_model"):
                v = getattr(r, c)
                if isinstance(v, str) and v.strip():
                    out[k].append(v)
    return out


def main() -> int:
    made = pd.read_csv(TEMP / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    cur = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    bak = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv.bak_pre_rebase",
                      dtype=str, low_memory=False).fillna("")
    for d in (made, cur, bak):
        d["k"] = d.pn.map(n)

    print("=" * 100)
    print("IS THE DRY-RUN LEGACY FILE = 'current file with exactly the twelve rows restored'?")
    print("=" * 100)
    expect = cur.copy()
    b = bak.set_index("k")
    tw = {n(p) for p in TWELVE}
    for i, r in expect.iterrows():
        if r.k in tw and r.k in b.index:
            expect.at[i, "bands"] = b.at[r.k, "bands"]
            expect.at[i, "band_list"] = b.at[r.k, "band_list"]
            expect.at[i, "n_bands"] = b.at[r.k, "n_bands"]
    # the free-text note differs by design; compare every data column
    cols = [c for c in cur.columns if c != "frozen_note"]
    same = (made[cols].astype(str) == expect[cols].astype(str))
    diff_rows = same[~same.all(axis=1)]
    print(f"  columns compared: {len(cols)} (frozen_note excluded, it is free text)")
    print(f"  rows differing from the expectation: {len(diff_rows)}")
    for k in diff_rows.k.tolist():
        m = made[made.k == k].iloc[0]
        e = expect[expect.k == k].iloc[0]
        print(f"      {k}:")
        for c in cols:
            if str(m[c]) != str(e[c]):
                print(f"          {c}: made {m[c]!r}  expected {e[c]!r}")
    print(f"  exact match: {len(diff_rows) == 0}")
    print()
    print(f"  rows made {len(made)}  current {len(cur)}")
    print(f"  fits one band: made {int((made.n_bands.astype(int) == 1).sum())}  "
          f"current {int((cur.n_bands.astype(int) == 1).sum())}")
    print()
    print("  the twelve, as the guard produced them:")
    for p in TWELVE:
        k = n(p)
        m = made[made.k == k].iloc[0]
        bb = bak[bak.k == k].iloc[0]
        cc = cur[cur.k == k].iloc[0]
        print(f"      {k:>12s}  backup {bb.bands:22s} current {cc.bands:22s} "
              f"made {m.bands:22s} {'OK' if m.bands == bb.bands else 'NO'}")

    print()
    print("=" * 100)
    print("THE NEUTRAL TABLE'S OWN VERSION OF THE DEFECT")
    print("=" * 100)
    app = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    app["k"] = app.pn.map(n)
    ev = raw_texts(set(app.k))
    names_pending = {k for k, t in ev.items() if any(PAT.search(s.upper()) for s in t)}
    silent = app[app.k.isin(names_pending) & (app.parked_codes.astype(str).str.strip() == "")]
    short = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}
    print(f"  rows in the neutral table whose raw evidence names a quarantined code : "
          f"{len(names_pending)}")
    print(f"  of those, parked_codes empty (not recorded as parked)                : "
          f"{len(silent)}")
    print(f"  of those, parked_codes recorded                                       : "
          f"{len(names_pending) - len(silent)}")
    print()
    print("  the rows that are silent, with the rung the quarantine would add:")
    for r in silent.itertuples():
        nmr = [c for c in PENDING if any(PAT.search(s.upper()) for s in ev[r.k])]
        extra = sorted({short.get(__import__('modules.vehicle_bands', fromlist=['band_for'])
                                 .band_for(c), '') for c in nmr} - {''})
        have = {short.get(x, x) for x in str(r.n_series_bands).split("|") if x}
        missing = [e for e in extra if e not in have]
        print(f"      {r.k:>12s} n_series {r.n_series_bands:26s} parked {r.parked_codes!r:4s} "
              f"evidence {nmr} missing {missing}")
    print()
    print(f"  NEUTRAL TABLE DEFECT COUNT: {len(silent)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
