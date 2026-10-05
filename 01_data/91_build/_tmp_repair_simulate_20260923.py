"""Simulate the guard before writing it, and count the neutral table's own defect.

The guard: a code the authored map marks `pending_ruling` contributes its interim band even when the
model string writes it glued to a suffix (`NMR-RHD`) or joined by a non-ASCII separator (`、`), which
the exact-token splitter misses. Detection is by whole-word regex over the raw evidence text, so it
does not depend on the delimiter set at all.

Nothing is written. This reports what the guard would produce, row by row.
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
from modules.vehicle_bands import (  # noqa: E402
    N_SERIES_BANDS, NOT_IN_SCOPE, UNRESOLVED, band_for, load_map, pending_ruling_codes,
)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}
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


def settled_rungs(nseries: str) -> set[str]:
    return {b for b in str(nseries).split("|") if b}


def main() -> int:
    bak = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv.bak_pre_rebase",
                      dtype=str, low_memory=False).fillna("")
    cur = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    app = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    for d in (bak, cur, app):
        d["k"] = d.pn.map(n)
    ev = raw_texts(set(bak.k) | set(cur.k) | set(app.k))
    names = {p for p, t in ev.items() if any(PAT.search(s.upper()) for s in t)}
    A = app.set_index("k")

    print("=" * 100)
    print("GUARD SIMULATION - interim band contributed for every pending code named in the raw text")
    print("=" * 100)
    print(f"  pending codes: {PENDING}  interim bands: "
          f"{ {c: SHORT.get(band_for(c), band_for(c)) for c in PENDING} }")
    print(f"  part numbers whose raw text names one: {len(names)}")
    print()
    print(f"  {'pn':>12s}  {'BACKUP (authority)':22s} {'GUARD would give':22s} {'match':6s} parked")
    bad = []
    for p in TWELVE:
        k = n(p)
        b = bak[bak.k == k]
        want = sorted({x for x in str(b.bands.iloc[0]).split("+") if x},
                      key=lambda s: ["3.5t", "5.5t", "7.5t"].index(s)) if len(b) else []
        got = settled_rungs(A.loc[k].n_series_bands) if k in A.index else set()
        for c in PENDING:
            if k in ev and any(PAT.search(s.upper()) for s in ev[k]):
                cb = band_for(c)
                if cb in N_SERIES_BANDS:
                    got.add(cb)
        got_l = sorted({SHORT[x] for x in got}, key=lambda s: ["3.5t", "5.5t", "7.5t"].index(s))
        ok = got_l == want
        if not ok:
            bad.append((k, want, got_l))
        print(f"  {k:>12s}  {'+'.join(want):22s} {'+'.join(got_l):22s} "
              f"{'yes' if ok else 'NO':6s} {A.loc[k].parked_codes if k in A.index else '-'!r}")
    print()
    print(f"  guard reproduces the backup on {len(TWELVE) - len(bad)} of {len(TWELVE)} rows")
    for k, w, g in bad:
        b = bak[bak.k == k]
        print(f"      MISMATCH {k}: backup {'+'.join(w)} vs guard {'+'.join(g)}")
        print(f"          backup exclusivity : {b.exclusivity_established.iloc[0] if len(b) else '-'!r}")
        print(f"          backup band_count  : {b.band_count.iloc[0] if len(b) else '-'}")
        if k in A.index:
            print(f"          neutral n_series   : {A.loc[k].n_series_bands!r}")
            print(f"          neutral vbands     : {A.loc[k].vehicle_bands!r}")
            print(f"          neutral codes_named: {A.loc[k].codes_named!r}")
            print(f"          neutral wildcards  : {A.loc[k].wildcards_named!r}")
        print(f"          raw strings naming a pending code:")
        for s in [t for t in ev.get(k, []) if PAT.search(t.upper())][:6]:
            print(f"              {s!r}")

    print()
    print("=" * 100)
    print("THE FLIP ROWS - why 8981868281 gained 7.5 t, and 8983615742 lost 5.5 t")
    print("=" * 100)
    for p in ("8981868281", "8983615742"):
        k = n(p)
        b = bak[bak.k == k]
        c = cur[cur.k == k]
        print(f"  {k}")
        print(f"      backup bands {b.bands.iloc[0]!r}  cat {b.category.iloc[0]!r}")
        print(f"      current bands {c.bands.iloc[0]!r}")
        if k in A.index:
            print(f"      neutral bands {A.loc[k].n_series_bands!r}  parked {A.loc[k].parked_codes!r}")
            print(f"      codes_named {A.loc[k].codes_named!r}")
        print(f"      raw strings:")
        for s in ev.get(k, [])[:8]:
            hit = PAT.findall(s.upper())
            print(f"          pending={hit}  {s[:110]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
